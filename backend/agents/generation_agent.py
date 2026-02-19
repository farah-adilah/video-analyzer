"""
Generation Agent
Coordinates report generation (PDF/PowerPoint)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
from mcp_servers.generation_server.server import GenerationServer
import asyncio

class GenerationAgent(BaseAgent):
    def __init__(self):
        super().__init__("GenerationAgent")
        self.generation_server = GenerationServer()
    
    async def process(self, data: dict) -> dict:
        """
        Generate reports from analysis data
        
        Args:
            data: Dictionary with 'analysis_data', 'format', 'output_path'
            
        Returns:
            Dictionary with generation results
        """
        analysis_data = data.get('analysis_data', {})
        report_format = data.get('format', 'pptx')
        output_path = data.get('output_path', f'output.{report_format}')
        
        self.log(f"Generating {report_format.upper()} report...")
        
        if report_format == 'pptx':
            result = await self.generation_server.generate_pptx(analysis_data, output_path)
        elif report_format == 'pdf':
            result = await self.generation_server.generate_pdf(analysis_data, output_path)
        else:
            return {"error": f"Unsupported format: {report_format}"}
        
        if result.get('success'):
            self.log(f"Report generated: {output_path}")
        else:
            self.log(f"Failed to generate report: {result.get('error')}")
        
        return {
            "agent": self.name,
            "format": report_format,
            "output_path": output_path,
            "success": result.get('success', False),
            "error": result.get('error')
        }

# Test
async def test():
    agent = GenerationAgent()
    test_data = {
        "analysis_data": {
            "video_name": "test.mp4",
            "transcription": "This is a test",
            "captions": ["Scene 1", "Scene 2"]
        },
        "format": "pptx",
        "output_path": "test_report.pptx"
    }
    result = await agent.process(test_data)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test())