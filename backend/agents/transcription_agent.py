"""
Transcription Agent
Coordinates audio extraction and transcription
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
from mcp_servers.transcription_server.server import TranscriptionServer
from utils.video_processor import VideoProcessor
import asyncio

class TranscriptionAgent(BaseAgent):
    def __init__(self):
        super().__init__("TranscriptionAgent")
        self.transcription_server = TranscriptionServer()
        self.video_processor = VideoProcessor()
    
    async def process(self, data: dict) -> dict:
        """
        Process video for transcription
        
        Args:
            data: Dictionary with 'video_path' key
            
        Returns:
            Dictionary with transcription results
        """
        video_path = data.get('video_path')
        if not video_path:
            return {"error": "No video_path provided"}
        
        self.log(f"Processing video: {video_path}")
        
        self.log("Extracting audio...")
        audio_path = self.video_processor.extract_audio(video_path)
        
        if not audio_path:
            return {"error": "Failed to extract audio"}
        
        self.log("Transcribing audio...")
        transcription_result = await self.transcription_server.transcribe_audio(audio_path)
        
        try:
            os.remove(audio_path)
            self.log("Cleaned up audio file")
        except:
            pass
        
        result = {
            "agent": self.name,
            "transcription": transcription_result.get("text", ""),
            "language": transcription_result.get("language", "unknown"),
            "error": transcription_result.get("error")
        }
        
        self.log("Transcription complete!")
        return result

# Test
async def test():
    agent = TranscriptionAgent()
    print("TranscriptionAgent ready!")

if __name__ == "__main__":
    asyncio.run(test())