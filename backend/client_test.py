"""
gRPC Client for testing
Can be called from Tauri or used standalone
"""
import grpc
import sys
import json
import os
from grpc_service import video_analyzer_pb2
from grpc_service import video_analyzer_pb2_grpc

def analyze_video(video_path: str):
    """
    Analyze video via gRPC
    
    Args:
        video_path: Path to video file
    """
    options = [
        ('grpc.max_send_message_length', 100 * 1024 * 1024),
        ('grpc.max_receive_message_length', 100 * 1024 * 1024),  
    ]
    channel = grpc.insecure_channel('localhost:50051', options=options)
    stub = video_analyzer_pb2_grpc.VideoAnalyzerStub(channel)
    
    try:
        with open(video_path, 'rb') as f:
            video_data = f.read()
    except FileNotFoundError:
        print(json.dumps({"error": f"File not found: {video_path}"}))
        return
    
    request = video_analyzer_pb2.VideoRequest(
        video_data=video_data,
        video_name=video_path.split('\\')[-1].split('/')[-1],
        analysis_types=["transcription", "vision"]
    )
    
    result_data = None
    try:
        for update in stub.AnalyzeVideo(request):            
            if update.result_json:
                result_data = json.loads(update.result_json)
                
    except grpc.RpcError as e:
        print(json.dumps({"error": str(e)}))
        return
    if result_data:
        print(json.dumps(result_data))
    else:
        print(json.dumps({"error": "No results received"}))
    
def generate_report(analysis_id: str, format: str = "pptx"):
    """
    Generate report via gRPC
    
    Args:
        analysis_id: ID of the analysis
        format: 'pptx' or 'pdf'
        
    Returns:
        Filepath of generated report
    """
    channel = grpc.insecure_channel('localhost:50051')
    stub = video_analyzer_pb2_grpc.VideoAnalyzerStub(channel)
    
    request = video_analyzer_pb2.ReportRequest(
        analysis_id=analysis_id,
        format=format
    )
    
    try:
        response = stub.GenerateReport(request)
        
        if response.filename == "error.txt":
            return json.dumps({"error": "Failed to generate report"})
        
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, response.filename)
        
        with open(output_path, 'wb') as f:
            f.write(response.report_data)
        
        return json.dumps({
            "success": True,
            "filepath": output_path,
            "filename": response.filename
        })
        
    except grpc.RpcError as e:
        return json.dumps({"error": str(e)})

def send_chat_message(query: str, conversation_id: str = None, context: dict = None):
    """
    Send chat message via gRPC
    
    Args:
        query: User's message
        conversation_id: Optional conversation ID
        context: Optional context dict
        
    Returns:
        JSON string with response
    """
    channel = grpc.insecure_channel('localhost:50051')
    stub = video_analyzer_pb2_grpc.VideoAnalyzerStub(channel)
    
    request = video_analyzer_pb2.ChatMessage(
        query=query,
        conversation_id=conversation_id or "",
        context_json=json.dumps(context or {})
    )
    
    try:
        response = stub.SendChatMessage(request)
        
        result = {
            "message": response.message,
            "type": response.type,
            "action": response.action
        }
        
        if response.data_json:
            result["data"] = json.loads(response.data_json)
        
        return json.dumps(result)
        
    except grpc.RpcError as e:
        return json.dumps({"error": str(e)})

def get_conversation_history(conversation_id: str):
    """Get conversation history"""
    channel = grpc.insecure_channel('localhost:50051')
    stub = video_analyzer_pb2_grpc.VideoAnalyzerStub(channel)
    
    request = video_analyzer_pb2.ConversationHistoryRequest(
        conversation_id=conversation_id
    )
    
    try:
        response = stub.GetConversationHistory(request)
        return response.messages_json
        
    except grpc.RpcError as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    if len(sys.argv) < 2:
        import sys
        sys.stderr.write("Usage:\n")
        sys.stderr.write("  Analyze: python client_test.py <video_path>\n")
        sys.stderr.write("  Report:  python client_test.py --report <analysis_id> [format]\n")
        sys.stderr.write("  Chat:    python client_test.py --chat <message> [conversation_id]\n")
        sys.stderr.write("  History: python client_test.py --history <conversation_id>\n")
        sys.exit(1)

    if sys.argv[1] == "--report":
        if len(sys.argv) < 3:
            sys.stderr.write("Error: analysis_id required\n")
            sys.exit(1)
        
        analysis_id = sys.argv[2]
        format = sys.argv[3] if len(sys.argv) > 3 else "pptx"
        result = generate_report(analysis_id, format)
        print(result)

    elif sys.argv[1] == "--chat":
        if len(sys.argv) < 3:
            sys.stderr.write("Error: message required\n")
            sys.exit(1)
        
        message = sys.argv[2]
        conversation_id = sys.argv[3] if len(sys.argv) > 3 else None
        result = send_chat_message(message, conversation_id)
        print(result)
        
    elif sys.argv[1] == "--history":
        if len(sys.argv) < 3:
            sys.stderr.write("Error: conversation_id required\n")
            sys.exit(1)
        
        conversation_id = sys.argv[2]
        result = get_conversation_history(conversation_id)
        print(result)
        
    else:
        video_path = sys.argv[1]
        analyze_video(video_path)