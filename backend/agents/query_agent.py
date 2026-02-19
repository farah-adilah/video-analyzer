"""
Query Understanding Agent
Parses natural language queries and routes to appropriate agents
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
import asyncio
import re

class QueryAgent(BaseAgent):
    def __init__(self):
        super().__init__("QueryAgent")
    
    async def process(self, data: dict) -> dict:
        """
        Understand user query and determine intent
        
        Args:
            data: {
                "query": str,
                "context": dict (optional - last analysis results, etc.)
            }
        
        Returns:
            {
                "intent": str,
                "confidence": float,
                "needs_clarification": bool,
                "clarification_question": str (optional),
                "parameters": dict
            }
        """
        query = data.get("query", "").lower()
        context = data.get("context", {})
        
        self.log(f"Analyzing query: {query}")
        
        intents = {
            "confirm_yes": {
                "keywords": ["yes", "yeah", "yep", "correct", "right", "confirm", "sure", "yup"],
                "requires": [],
                "action": "confirm"
            },
            "transcribe": {
                "keywords": ["transcribe", "transcript", "what was said", "speech to text", "audio"],
                "requires": ["video"],
                "action": "transcription"
            },
            "create_ppt": {
                "keywords": ["powerpoint", "ppt", "presentation", "slides"],
                "requires": ["analysis"],
                "action": "generate_report",
                "parameters": {"format": "pptx"}
            },
            "create_pdf": {
                "keywords": ["pdf", "report", "document"],
                "requires": ["analysis"],
                "action": "generate_report",
                "parameters": {"format": "pdf"}
            },
            "detect_objects": {
                "keywords": ["objects", "what do you see", "identify", "things in",
                             "items", "shown", "show", "what is", "what are", "see",
                             "detect", "find", "visible"],
                "requires": ["video"],
                "action": "vision_analysis"
            },
            "detect_graphs": {
                "keywords": ["graph", "chart", "plot", "diagram", "visualization",
                             "bar chart", "pie chart", "line graph", "infographic"],
                "requires": ["video"],
                "action": "vision_analysis",
                "parameters": {"focus": "graphs"}
            },
            "summarize": {
                "keywords": ["summarize", "summary", "recap", "overview", "tldr"],
                "requires": [],
                "action": "summarization"
            },
            "analyze_video": {
                "keywords": ["analyze", "process", "examine"],
                "requires": ["video"],
                "action": "full_analysis"
            }
        }
        
        matched_intent = None
        max_score = 0
        matched_keywords = []
        
        query_lower = query.lower()

        if any(phrase in query_lower for phrase in ["pdf", "generate pdf", "create pdf", "make pdf", "pdf report"]):
            matched_intent = "create_pdf"
            max_score = 2
            matched_keywords = ["pdf"]
        elif any(phrase in query_lower for phrase in ["powerpoint", "ppt", "presentation", "slides"]):
            matched_intent = "create_ppt"
            max_score = 2
            matched_keywords = ["powerpoint"]
        elif any(phrase in query_lower for phrase in ["graph", "chart", "plot", "diagram", 
                                            "visualization", "bar chart", 
                                            "pie chart", "line graph", "infographic"]):
            matched_intent = "detect_graphs"
            max_score = 2
            matched_keywords = ["graph"]
        else:
            for intent_name, intent_data in intents.items():
                matches = [kw for kw in intent_data["keywords"] if kw in query_lower]
                score = len(matches)
                
                if score > max_score:
                    max_score = score
                    matched_intent = intent_name
                    matched_keywords = matches
        
        if not matched_intent or max_score == 0:
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "needs_clarification": True,
                "clarification_question": "I'm not sure what you'd like me to do. Could you clarify? For example:\n- 'Transcribe the video'\n- 'Create a PowerPoint summary'\n- 'What objects are in the video?'",
                "parameters": {}
            }
        
        intent_data = intents[matched_intent]
        # confidence = min(max_score / len(intent_data["keywords"]), 1.0)
        base_confidence = 0.6  
        bonus = min(0.1 * (max_score - 1), 0.4)
        confidence = min(base_confidence + bonus, 1.0)

        self.log(f"Matched intent: {matched_intent}, keywords: {matched_keywords}, confidence: {confidence}")

        missing_requirements = []
        for req in intent_data["requires"]:
            if req == "video":
                has_video = context.get("current_video") or context.get("has_analysis")
                if not has_video:
                    missing_requirements.append("video")
            elif req == "analysis":
                has_analysis = context.get("last_analysis_id") or context.get("has_analysis")
                if not has_analysis:
                    missing_requirements.append("analysis")
        
        if missing_requirements:
            clarification = self._generate_missing_req_question(missing_requirements)
            return {
                "intent": matched_intent,
                "confidence": confidence,
                "needs_clarification": True,
                "clarification_question": clarification,
                "parameters": intent_data.get("parameters", {})
            }
        
        if confidence < 0.4:
            return {
                "intent": matched_intent,
                "confidence": confidence,
                "needs_clarification": True,
                "clarification_question": f"Did you mean: {intent_data['action']}? Please confirm or provide more details.",
                "parameters": intent_data.get("parameters", {})
            }
        
        return {
            "intent": matched_intent,
            "confidence": confidence,
            "needs_clarification": False,
            "action": intent_data["action"],
            "parameters": intent_data.get("parameters", {})
        }
    
    def _generate_missing_req_question(self, missing: list) -> str:
        """Generate clarification question for missing requirements"""
        if "video" in missing:
            return "I need a video to analyze first. Please upload a video, then I can help you with that!"
        elif "analysis" in missing:
            return "I need to analyze a video first before I can do that. Would you like me to analyze the current video?"
        return "I need more information to proceed. Can you provide more details?"

async def test():
    agent = QueryAgent()
    
    test_queries = [
        {"query": "transcribe the video", "context": {"current_video": "test.mp4"}},
        {"query": "create a powerpoint", "context": {"last_analysis_id": "123"}},
        {"query": "what objects are in the video", "context": {}},
        {"query": "hello", "context": {}},
    ]
    
    for test in test_queries:
        result = await agent.process(test)
        print(f"\nQuery: {test['query']}")
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test())