"""
Vision Agent
Coordinates frame extraction and visual analysis
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
from mcp_servers.vision_server.server import VisionServer
from utils.video_processor import VideoProcessor
import asyncio
import shutil

class VisionAgent(BaseAgent):
    def __init__(self):
        super().__init__("VisionAgent")
        self.vision_server = VisionServer()
        self.video_processor = VideoProcessor()
    
    async def process(self, data: dict) -> dict:
        """
        Process video for visual analysis
        
        Args:
            data: Dictionary with 'video_path' and optional 'frame_interval'
            
        Returns:
            Dictionary with visual analysis results
        """
        video_path = data.get('video_path')
        frame_interval = data.get('frame_interval', 5)
        if not video_path:
            return {"error": "No video_path provided"}
        
        self.log(f"Processing video: {video_path}")
        
        self.log(f"Extracting frames (1 per {frame_interval}s)...")
        temp_dir = "temp_frames"
        frame_paths = self.video_processor.extract_frames(
            video_path, 
            output_dir=temp_dir,
            frame_rate=frame_interval
        )
        
        if not frame_paths:
            return {"error": "Failed to extract frames"}
        
        self.log(f"Extracted {len(frame_paths)} frames")
        
        self.log("Analyzing frames...")
        captions = []
        
        for i, frame_path in enumerate(frame_paths[:10]):  # Limit to first 10 frames
            self.log(f"Analyzing frame {i+1}/{min(len(frame_paths), 10)}...")
            result = await self.vision_server.caption_image(frame_path)
            if 'caption' in result:
                captions.append({
                    "frame": i+1,
                    "caption": result['caption'],
                    "timestamp": i * frame_interval
                })
        
        try:
            shutil.rmtree(temp_dir)
            self.log("Cleaned up frame files")
        except:
            pass
        
        result = {
            "agent": self.name,
            "total_frames": len(frame_paths),
            "analyzed_frames": len(captions),
            "captions": captions,
            "summary": self._generate_summary(captions)
        }
        
        self.log("Visual analysis complete!")
        return result
    
    def _generate_summary(self, captions: list) -> str:
        """Generate a summary of the visual content"""
        if not captions:
            return "No visual content analyzed"
        
        caption_texts = [c['caption'] for c in captions]
        return f"The video contains {len(captions)} key scenes. " + " ".join(caption_texts[:3])

async def test():
    agent = VisionAgent()
    print("VisionAgent ready!")

if __name__ == "__main__":
    asyncio.run(test())