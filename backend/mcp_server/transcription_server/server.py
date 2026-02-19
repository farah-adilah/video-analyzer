"""
Transcription MCP Server
Handles audio-to-text conversion using Whisper
"""
import asyncio
import os

class TranscriptionServer:
    def __init__(self):
        self.name = "transcription-server"
        self.model = None
        print(f"[{self.name}] Initialized")
    
    def load_model(self):
        """Load Whisper model (lazy loading)"""
        if self.model is None:
            try:
                import whisper
                print(f"[{self.name}] Loading Whisper base model...")
                self.model = whisper.load_model("base")
                print(f"[{self.name}] Whisper Model loaded!")
            except ImportError:
                print(f"[{self.name}] ERROR: whisper not installed!")
                print(f"[{self.name}] Run: pip install openai-whisper")
                self.model = None
            except Exception as e:
                print(f"[{self.name}] Error loading model: {e}")
                self.model = None

    async def transcribe_audio(self, audio_path: str) -> dict:
        """
        Transcribe audio file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with transcription results
        """
        print(f"[{self.name}] Transcribing: {audio_path}")
        
        if not os.path.exists(audio_path):
            return {
                "text": "",
                "error": f"Audio file not found: {audio_path}"
            }
        
        self.load_model()
        
        if self.model is None:
            return {
                "text": "",
                "error": "Whisper model not available. Please install: pip install openai-whisper"
            }

        try:
            print(f"[{self.name}] Running Whisper inference...")
            result = self.model.transcribe(audio_path, fp16=False)

            print(f"[{self.name}] Transcription complete!")
            print(f"[{self.name}] Text: {result['text'][:100]}...") 

            return {
                "text": result["text"],
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", [])
            }
        except Exception as e:
            print(f"[{self.name}] Error during transcription: {e}")
            return {
                "text": "",
                "error": str(e)
            }

async def test():
    server = TranscriptionServer()
    print("TranscriptionServer ready!")

if __name__ == "__main__":
    print("Testing Transcription Server...")
    asyncio.run(test())