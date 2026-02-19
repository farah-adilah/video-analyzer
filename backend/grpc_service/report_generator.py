"""
Report generation service
"""
import os
from datetime import datetime
from orchestrator.workflow import VideoAnalysisOrchestrator

class ReportGenerator:
    def __init__(self):
        self.orchestrator = VideoAnalysisOrchestrator()
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def generate_report(self, analysis_data: dict, format: str = "pptx") -> dict:
        """
        Generate report from analysis data
        
        Returns:
            {
                "success": True,
                "filepath": "output/report_20260215_143000.pptx",
                "filename": "report_20260215_143000.pptx"
            }
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.{format}"
        filepath = os.path.join(self.output_dir, filename)
        
        result = await self.orchestrator.generate_report(
            analysis_data=analysis_data,
            format=format,
            output_path=filepath
        )
        
        if result.get("success"):
            return {
                "success": True,
                "filepath": filepath,
                "filename": filename
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error")
            }