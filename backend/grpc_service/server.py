"""
gRPC Server
Connects frontend (Tauri/React) with backend (Python agents)
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import storage as storage_module
storage = storage_module.storage

import grpc.aio
from concurrent import futures
import asyncio
import json
import tempfile
from datetime import datetime
from conversation_manager import conversation_manager

try:
    from . import video_analyzer_pb2
    from . import video_analyzer_pb2_grpc
except ImportError:
    try:
        import video_analyzer_pb2
        import video_analyzer_pb2_grpc
    except ImportError:
        print("ERROR: Protobuf files not found!")
        print("Make sure you're running from the backend directory!")
        print("Run: cd backend && python grpc_service/server.py")
        sys.exit(1)

from orchestrator.workflow import VideoAnalysisOrchestrator

class VideoAnalyzerService(video_analyzer_pb2_grpc.VideoAnalyzerServicer):
    def __init__(self):
        self.orchestrator = VideoAnalysisOrchestrator()
        print("[gRPC Server] Initialized")
    
    async def AnalyzeVideo(self, request, context):
        """
        Analyze video and stream progress updates
        """
        print(f"[gRPC Server] Received video: {request.video_name}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            temp_video.write(request.video_data)
            video_path = temp_video.name
        
        print(f"[gRPC Server] Video saved to: {video_path}")
        
        async def progress_callback(stage, progress, message):
            print(f"[gRPC Server] Progress: {stage} - {progress}% - {message}")
            return video_analyzer_pb2.AnalysisUpdate(
                stage=stage,
                progress=progress,
                message=message,
                result_json=""
            )
        
        try:
            yield video_analyzer_pb2.AnalysisUpdate(
                stage="starting",
                progress=0,
                message="Starting video analysis...",
                result_json=""
            )
            
            results = await self.orchestrator.analyze_video(
                video_path=video_path,
                video_name=request.video_name,
                # progress_callback=progress_callback
            )
            
            analysis_id = storage_module.storage.save_analysis(results)
            results["analysis_id"] = analysis_id

            print(f"[gRPC Server] Analysis saved with ID: {analysis_id}")

            conversation_manager.update_context("current_video", request.video_name)
            conversation_manager.update_context("last_analysis_id", analysis_id)
            conversation_manager.update_context("has_analysis", True)
            print(f"[gRPC Server] Context updated for conversation")

            yield video_analyzer_pb2.AnalysisUpdate(
                stage="complete",
                progress=100,
                message="Analysis complete!",
                result_json=json.dumps(results)
            )
            
        except Exception as e:
            print(f"[gRPC Server] Error: {e}")
            yield video_analyzer_pb2.AnalysisUpdate(
                stage="error",
                progress=0,
                message=f"Error: {str(e)}",
                result_json=""
            )
        
        finally:
            try:
                os.unlink(video_path)
                print(f"[gRPC Server] Cleaned up temp file")
            except:
                pass
    
    async def GenerateReport(self, request, context):
        """
        Generate PDF or PowerPoint report
        """
        print(f"[gRPC Server] Generating {request.format} report for: {request.analysis_id}")
        
        analysis_data = storage.get_analysis(request.analysis_id)

        if not analysis_data:
            return video_analyzer_pb2.ReportResponse(
                report_data=b"",
                filename="error.txt"
            )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.{request.format}"
        output_path = os.path.join("output", filename)
        
        os.makedirs("output", exist_ok=True)
        
        try:
            report_result = await self.orchestrator.generate_report(
                analysis_data=analysis_data,
                format=request.format,
                output_path=output_path
            )
            
            if report_result.get("success"):
                print(f"[gRPC Server] Report generated: {output_path}")
                
                with open(output_path, 'rb') as f:
                    report_data = f.read()
                
                return video_analyzer_pb2.ReportResponse(
                    report_data=report_data,
                    filename=filename
                )
            else:
                print(f"[gRPC Server] Report generation failed: {report_result.get('error')}")
                return video_analyzer_pb2.ReportResponse(
                    report_data=b"",
                    filename="error.txt"
                )
                
        except Exception as e:
            print(f"[gRPC Server] Error generating report: {e}")
            return video_analyzer_pb2.ReportResponse(
                report_data=b"",
                filename="error.txt"
            )
        
    async def SendChatMessage(self, request, context):
        """
        Handle chat message from user
        """
        print(f"[gRPC Server] Received chat: {request.query}")
        
        user_context = {}
        if request.context_json:
            try:
                user_context = json.loads(request.context_json)
                print(f"[gRPC Server] Received context: {user_context}")
            except:
                pass
        
        if request.conversation_id:
            conversation_manager.current_conversation = request.conversation_id
        else:
            conversation_manager.start_conversation()
        
        stored_video = conversation_manager.get_context("current_video")
        stored_analysis = conversation_manager.get_context("last_analysis_id")
        
        if stored_video:
            user_context["current_video"] = stored_video
        if stored_analysis:
            user_context["last_analysis_id"] = stored_analysis
        
        print(f"[gRPC Server] Merged context: {user_context}")

        try:
            response = await self.orchestrator.handle_query(request.query, user_context)
            
            data = {
                "focus": response.get("focus", "all"),
                "format": response.get("format", ""),
            }

            return video_analyzer_pb2.ChatResponse(
                message=response.get("message", ""),
                type=response.get("type", "response"),
                action=response.get("action", ""),
                data_json=json.dumps(data)
            )
            
        except Exception as e:
            print(f"[gRPC Server] Chat error: {e}")
            import traceback
            traceback.print_exc()
            return video_analyzer_pb2.ChatResponse(
                message=f"Sorry, I encountered an error: {str(e)}",
                type="error",
                action="",
                data_json="{}"
            )

    async def GetConversationHistory(self, request, context):
        """
        Get conversation history
        """
        print(f"[gRPC Server] Getting conversation: {request.conversation_id}")
        
        try:
            messages = conversation_manager.get_conversation_history(request.conversation_id)
            
            return video_analyzer_pb2.ConversationHistoryResponse(
                messages_json=json.dumps(messages)
            )
            
        except Exception as e:
            print(f"[gRPC Server] Error getting history: {e}")
            return video_analyzer_pb2.ConversationHistoryResponse(
                messages_json="[]"
            )

async def serve(port=50051):
    """Start the gRPC server"""
    options = [
        ('grpc.max_send_message_length', 100 * 1024 * 1024),
        ('grpc.max_receive_message_length', 100 * 1024 * 1024), 
    ]
    server = grpc.aio.server(
        options=options
    )
    video_analyzer_pb2_grpc.add_VideoAnalyzerServicer_to_server(
        VideoAnalyzerService(), server
    )
    server.add_insecure_port(f'[::]:{port}')
    await server.start()
    print(f"[gRPC Server] Started on port {port}")
    print("[gRPC Server] Ready to accept connections...")
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[gRPC Server] Shutting down...")
        server.stop(0)

if __name__ == '__main__':
    print("=" * 60)
    print("Video AI Analyzer - gRPC Server")
    print("=" * 60)
    asyncio.run(serve())