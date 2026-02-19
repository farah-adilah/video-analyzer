"""
Summarization Agent
Uses local LLM to generate intelligent summaries
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
import asyncio

class SummarizationAgent(BaseAgent):
    def __init__(self):
        super().__init__("SummarizationAgent")
        self.model = None
        self.tokenizer = None
    
    def load_model(self):
        """Load TinyLlama model for summarization"""
        if self.model is None:
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                
                self.log("Loading TinyLlama model for summarization...")
                self.log("This may take 5-10 minutes on first run (downloading ~2GB)...")
                
                # model_name = "microsoft/Phi-3-mini-4k-instruct"
                model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True
                )
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32,  # for CPU
                    device_map="cpu",
                    trust_remote_code=True
                    # low_cpu_mem_usage=True,
                    # device_map=None
                )
                
                self.log("Model loaded successfully!")
                
            except Exception as e:
                self.log(f"Error loading model: {e}")
                self.model = None
    
    async def process(self, data: dict) -> dict:
        """
        Generate summary from analysis data
        
        Args:
            data: Dictionary with analysis results
            
        Returns:
            Dictionary with summary
        """
        self.log("Generating AI summary...")
        
        self.load_model()
        
        if self.model is None:
            return {
                "agent": self.name,
                "summary": "AI model not available. Using basic summary.",
                "error": "Model not loaded"
            }
        
        context = self._prepare_context(data)
        
        try:
            summary = await self._generate_summary(context)
            self.log(f"Summary generated: {summary[:100]}...")
            
            return {
                "agent": self.name,
                "summary": summary
            }
            
        except Exception as e:
            self.log(f"Error generating summary: {e}")
            return {
                "agent": self.name,
                "summary": "Error generating summary",
                "error": str(e)
            }
    
    def _prepare_context(self, data: dict) -> str:
        """Prepare context string from analysis data"""
        context_parts = []
        
        if 'transcription' in data:
            trans = data['transcription']
            if isinstance(trans, dict) and trans.get('transcription'):
                context_parts.append(f"Narration: {trans['transcription']}")
            elif isinstance(trans, str):
                context_parts.append(f"Narration: {trans}")
        
        if 'vision' in data:
            vision = data['vision']
            if vision.get('captions'):
                scenes = []
                for cap in vision['captions']:
                    if cap.get('caption'):
                        scenes.append(f"{cap['caption']} at {cap.get('timestamp', 0)}s")
                if scenes:
                    context_parts.append(f"Visual scenes: {'; '.join(scenes)}")
        
        return "\n".join(context_parts)

    async def _generate_summary(self, context: str) -> str:
        """Generate summary using the LLM"""
        
        prompt = f"""<|system|>
                You are a helpful assistant that creates concise video summaries.</s>
                <|user|>
                Based on this video analysis data, write a 2-3 sentence summary:

                {context}

                Provide ONLY the summary, nothing else.</s>
                <|assistant|>
                """

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            self.log("Running LLM inference (this may take 10-30 seconds)...")
            
            outputs = self.model.generate(
                inputs.input_ids,
                max_new_tokens=100,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            if "<|assistant|>" in full_response:
                summary = full_response.split("<|assistant|>")[-1].strip()
            else:
                summary = full_response.replace(prompt, "").strip()
            
            summary = summary.replace("</s>", "").strip()
            summary = summary.replace("Based on the video analysis data, a concise 2-3 sentence summary of the video content is as follows:", "").strip()
            summary = summary.replace("Based on this video analysis data, write a 2-3 sentence summary:", "").strip()
            
            lines = summary.split('\n')
            clean_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith("Video duration:") or line.startswith("Resolution:") or line.startswith("Narration:"):
                    continue
                if line:
                    clean_lines.append(line)
            
            summary = ' '.join(clean_lines)
            
            if len(summary) < 20:
                return "Summary generation incomplete. Please try again."
            
            return summary
            
        except Exception as e:
            self.log(f"Error in LLM inference: {e}")
            return f"Error generating summary: {str(e)}"

async def test():
    agent = SummarizationAgent()
    
    test_data = {
        "video_info": {"duration": 5.7, "width": 1920, "height": 1080},
        "transcription": {"transcription": "Welcome to our park tour. Today we'll show you the beautiful scenery."},
        "vision": {
            "captions": [
                {"caption": "a park with trees and cars", "timestamp": 0},
                {"caption": "a park bench under a tree", "timestamp": 5}
            ]
        }
    }
    
    result = await agent.process(test_data)
    print(f"Summary: {result.get('summary')}")

if __name__ == "__main__":
    asyncio.run(test())