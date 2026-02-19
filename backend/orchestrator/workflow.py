"""
Workflow Orchestrator
Coordinates all agents and manages the video analysis pipeline
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.transcription_agent import TranscriptionAgent
from agents.vision_agent import VisionAgent
from agents.generation_agent import GenerationAgent
from agents.summarization_agent import SummarizationAgent
from utils.video_processor import VideoProcessor
import asyncio
from datetime import datetime
import json
from agents.query_agent import QueryAgent
from conversation_manager import conversation_manager

class VideoAnalysisOrchestrator:
    def __init__(self):
        self.transcription_agent = TranscriptionAgent()
        self.vision_agent = VisionAgent()
        self.generation_agent = GenerationAgent()
        self.summarization_agent = SummarizationAgent()
        self.video_processor = VideoProcessor()
        self.query_agent = QueryAgent()
        print("[Orchestrator] Initialized all agents")
    
    async def analyze_video(self, video_path: str, video_name: str = None, 
                           progress_callback=None) -> dict:
        """
        Analyze a video file
        
        Args:
            video_path: Path to video file
            video_name: Display name for video
            progress_callback: Optional async callback(stage, progress, message)
            
        Returns:
            Complete analysis results
        """
        if video_name is None:
            video_name = os.path.basename(video_path)
        
        print(f"[Orchestrator] Starting analysis: {video_name}")
        
        results = {
            "video_name": video_name,
            "video_path": video_path,
            "timestamp": datetime.now().isoformat(),
            "status": "processing"
        }
        
        try:
            video_info = self.video_processor.get_video_info(video_path)
            results["video_info"] = video_info
            print(f"[Orchestrator] Video info: {video_info}")
        except Exception as e:
            print(f"[Orchestrator] Error getting video info: {e}")
        
        if progress_callback:
            await progress_callback("transcription", 0, "Starting transcription...")
        
        try:
            print("[Orchestrator] Stage 1: Transcription")
            transcription_result = await self.transcription_agent.process({
                "video_path": video_path
            })
            results["transcription"] = transcription_result
            
            if progress_callback:
                await progress_callback("transcription", 100, "Transcription complete")
        except Exception as e:
            print(f"[Orchestrator] Transcription error: {e}")
            results["transcription"] = {"error": str(e)}
        
        if progress_callback:
            await progress_callback("vision", 0, "Starting visual analysis...")
        
        try:
            print("[Orchestrator] Stage 2: Vision Analysis")
            vision_result = await self.vision_agent.process({
                "video_path": video_path,
                "frame_interval": 5
            })
            results["vision"] = vision_result
            
            if progress_callback:
                await progress_callback("vision", 100, "Visual analysis complete")
        except Exception as e:
            print(f"[Orchestrator] Vision analysis error: {e}")
            results["vision"] = {"error": str(e)}

        if progress_callback:
            await progress_callback("summarization", 0, "Generating AI summary...")

        try:
            print("[Orchestrator] Stage 3: AI Summarization")
            summary_result = await self.summarization_agent.process(results)
            results["ai_summary"] = summary_result.get("summary", "")
            
            if progress_callback:
                await progress_callback("summarization", 100, "AI summary complete")
        except Exception as e:
            print(f"[Orchestrator] Summarization error: {e}")
            results["ai_summary"] = "Error generating summary"
                
        results["status"] = "complete"
        print(f"[Orchestrator] Analysis complete!")

        conversation_manager.update_context("last_analysis", results)
        conversation_manager.update_context("video_path", video_path)
        conversation_manager.update_context("video_name", video_name)
        
        return results
    
    async def generate_report(self, analysis_data: dict, format: str = "pptx", 
                            output_path: str = None) -> dict:
        """
        Generate a report from analysis data
        
        Args:
            analysis_data: Results from analyze_video()
            format: 'pptx' or 'pdf'
            output_path: Where to save the report
            
        Returns:
            Generation results
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"report_{timestamp}.{format}"
        
        print(f"[Orchestrator] Generating {format.upper()} report...")
        
        report_data = {
            "video_name": analysis_data.get("video_name", "Unknown"),
            "video_info": analysis_data.get("video_info", {}),
            "vision": analysis_data.get("vision", {}),
            "transcription": analysis_data.get("transcription", {}).get("transcription", ""),
            "captions": [c['caption'] for c in analysis_data.get("vision", {}).get("captions", [])],
            # "summary": analysis_data.get("vision", {}).get("summary", ""),
            "ai_summary": analysis_data.get("ai_summary", ""),
            "summary": analysis_data.get("ai_summary", ""),
            "timestamp": analysis_data.get("timestamp", ""),
        }
        
        result = await self.generation_agent.process({
            "analysis_data": report_data,
            "format": format,
            "output_path": output_path
        })
        
        return result
    
    async def handle_query(self, query: str, context: dict = None) -> dict:
        """
        Handle natural language query
        
        Args:
            query: User's natural language query
            context: Current context (video, analysis results, etc.)
        
        Returns:
            Response dictionary with action to take
        """
        print(f"[Orchestrator] Processing query: {query}")
        
        if not context:
            context = {}
        
        stored_video = conversation_manager.get_context("current_video")
        stored_analysis = conversation_manager.get_context("last_analysis_id")
        
        if stored_video and not context.get("current_video"):
            context["current_video"] = stored_video
        if stored_analysis and not context.get("last_analysis_id"):
            context["last_analysis_id"] = stored_analysis
        
        if query.startswith("__CONTEXT_UPDATE__:"):
            try:
                import json
                context_str = query.replace("__CONTEXT_UPDATE__:", "")
                new_context = json.loads(context_str)
                
                for key, value in new_context.items():
                    conversation_manager.update_context(key, value)
                
                print(f"[Orchestrator] Context updated: {new_context}")
                return {
                    "type": "response",
                    "message": "Context updated"
                }
            except Exception as e:
                print(f"[Orchestrator] Error updating context: {e}")
        
        conversation_manager.add_message("user", query)
        
        intent_result = await self.query_agent.process({
            "query": query,
            "context": context
        })
        
        conversation_manager.add_message("user", query)
        
        intent_result = await self.query_agent.process({
            "query": query,
            "context": context or conversation_manager.current_context
        })
        
        print(f"[Orchestrator] Intent: {intent_result}")
        print(f"[Orchestrator] Context: {context}")

        if intent_result.get("needs_clarification"):
            response = {
                "type": "clarification",
                "message": intent_result["clarification_question"]
            }
            conversation_manager.add_message("assistant", response["message"])
            return response
        
        action = intent_result.get("action")
        intent = intent_result.get("intent")

        conversation_manager.update_context("last_query_intent", intent)
        conversation_manager.update_context("last_query_action", action)
        
        if action == "confirm":
            last_messages = conversation_manager.get_conversation_history()
            if len(last_messages) >= 2:
                last_assistant_msg = None
                for msg in reversed(last_messages):
                    if msg["role"] == "assistant":
                        last_assistant_msg = msg["content"]
                        break
                
                if last_assistant_msg and "vision" in last_assistant_msg.lower():
                    return {
                        "type": "action_required",
                        "action": "analyze_video",
                        "message": "Great! I'll analyze the video and identify objects for you."
                    }
            
            return {
                "type": "response",
                "message": "What would you like me to do? Please specify: transcribe, analyze objects, or create a report."
            }

        if action == "transcription":
            if context.get("last_analysis_id"):
                from storage import storage
                analysis_data = storage.get_analysis(context["last_analysis_id"])
                
                if analysis_data and "transcription" in analysis_data:
                    trans = analysis_data["transcription"]
                    
                    if isinstance(trans, dict):
                        trans_text = trans.get("transcription", "").strip()
                        trans_error = trans.get("error")
                    else:
                        trans_text = str(trans).strip()
                        trans_error = None
                    
                    if trans_error:
                        msg = f"⚠️ Transcription error: {trans_error}"
                    elif not trans_text:
                        msg = "🔇 No speech detected in this video. The video may be silent or contain only background noise/music."
                    else:
                        msg = f"🎤 Here's the transcription:\n\n{trans_text}"
                    
                    response = {
                        "type": "response",
                        "message": msg
                    }
                    conversation_manager.add_message("assistant", response["message"])
                    return response
            response = {
                "type": "action_required",
                "action": "analyze_video",
                "focus": "transcription",
                "message": "Here's the transcription:"
            }
            conversation_manager.add_message("assistant", response["message"])
            return response
        
        elif action == "vision_analysis":
            response = {
                "type": "action_required",
                "action": "analyze_video",
                "focus": "objects",
                "message": "Here are the objects I found in the video:"
            }
            conversation_manager.add_message("assistant", response["message"])
            return response
        
        elif action == "full_analysis":
            response = {
                "type": "action_required",
                "action": "analyze_video",
                "focus": "all",
                "message": "Starting full video analysis..."
            }
            conversation_manager.add_message("assistant", response["message"])
            return response
        
        elif action == "generate_report":
            format_type = intent_result.get("parameters", {}).get("format", "pptx")

            print(f"[Orchestrator] ========== REPORT DEBUG ==========")
            print(f"[Orchestrator] Intent result: {intent_result}")
            print(f"[Orchestrator] Parameters: {intent_result.get('parameters', {})}")
            print(f"[Orchestrator] Format type: {format_type}")
            print(f"[Orchestrator] =====================================")
            
            response = {
                "type": "action_required",
                "action": "generate_report",
                "focus": "all",
                "format": format_type,
                "message": f"I'll generate a {format_type.upper()} report for you."
            }
            conversation_manager.add_message("assistant", response["message"])
            return response
        

        elif action == "summarization":
            if context.get("last_analysis_id"):
                from storage import storage
                analysis_data = storage.get_analysis(context["last_analysis_id"])
                
                if analysis_data and analysis_data.get("ai_summary"):
                    summary = analysis_data["ai_summary"]
                    summary = summary.replace("Based on the video analysis data, the summary is:", "").strip()
                    response = {
                        "type": "response",
                        "message": f"📝 Summary:\n\n{summary}"
                    }
                    conversation_manager.add_message("assistant", response["message"])
                    return response
            
            history = conversation_manager.get_conversation_history()
            summary = self._summarize_conversation(history)
            response =  {
                "type": "response",
                "message": summary
            }
            conversation_manager.add_message("assistant", response["message"])
            return response

        elif action == "graph_analysis":
            if context.get("last_analysis_id"):
                from storage import storage
                analysis_data = storage.get_analysis(context["last_analysis_id"])
                
                if analysis_data and analysis_data.get("vision", {}).get("captions"):
                    captions = analysis_data["vision"]["captions"]
                    
                    graph_keywords = ["graph", "chart", "plot", "diagram", 
                                    "bar", "pie", "line", "data", "statistics"]
                    
                    found_graphs = []
                    for cap in captions:
                        caption_text = cap.get("caption", "").lower()
                        if any(kw in caption_text for kw in graph_keywords):
                            found_graphs.append(cap)
                    
                    if found_graphs:
                        graph_descriptions = "\n".join([
                            f"• Frame at {g.get('timestamp', 0)}s: {g.get('caption', '')}"
                            for g in found_graphs
                        ])
                        response = {
                            "type": "response",
                            "message": f"Yes! I found graphs/charts in the video:\n\n{graph_descriptions}"
                        }
                    else:
                        response = {
                            "type": "response",
                            "message": "I analyzed the video frames and did not detect any graphs, charts, or diagrams. The video appears to contain: " + 
                                    ", ".join([c.get("caption", "") for c in captions[:3] if c.get("caption")])
                        }
                    
                    conversation_manager.add_message("assistant", response["message"])
                    return response
            
            response = {
                "type": "action_required",
                "action": "analyze_video",
                "focus": "graphs",
                "message": "Let me analyze the video to check for graphs..."
            }
            conversation_manager.add_message("assistant", response["message"])
            return response
        
        response = {
            "type": "response",
            "message": "I'm not sure how to help with that. Could you rephrase your request?"
        }
        conversation_manager.add_message("assistant", response["message"])
        return response

    def _summarize_conversation(self, history: list) -> str:
        """Summarize conversation history"""
        if not history:
            return "We haven't discussed anything yet!"
        
        summary_parts = [f"Conversation Summary ({len(history)} messages):"]
        
        for i, msg in enumerate(history[-10:], 1):
            role = "You" if msg["role"] == "user" else "Me"
            content = msg["content"][:100]
            summary_parts.append(f"{i}. {role}: {content}...")
        
        return "\n".join(summary_parts)

async def test():
    orchestrator = VideoAnalysisOrchestrator()
    print("Orchestrator ready!")
    
    # To test with actual video:
    # result = await orchestrator.analyze_video("test.mp4")
    # print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(test())