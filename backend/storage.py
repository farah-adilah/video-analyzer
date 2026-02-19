"""
Simple storage for analysis results
In production, you'd use a database
"""
import json
import os
from datetime import datetime

class AnalysisStorage:
    def __init__(self):
        self.storage_dir = "storage"
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def save_analysis(self, analysis_data: dict) -> str:
        """
        Save analysis results
        Returns: analysis_id
        """
        analysis_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        analysis_data["analysis_id"] = analysis_id
        
        filepath = os.path.join(self.storage_dir, f"{analysis_id}.json")
        with open(filepath, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"[Storage] Saved analysis: {analysis_id}")
        return analysis_id
    
    def get_analysis(self, analysis_id: str) -> dict:
        """Retrieve analysis by ID"""
        filepath = os.path.join(self.storage_dir, f"{analysis_id}.json")
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)

storage = AnalysisStorage()