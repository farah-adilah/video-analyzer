"""
Video processing utilities
Handles video frame extraction and audio extraction
"""
import cv2
import os
import subprocess
from pathlib import Path

class VideoProcessor:
    def __init__(self):
        pass
    
    def extract_audio(self, video_path: str, output_path: str = None) -> str:
        """
        Extract audio from video file
        
        Args:
            video_path: Path to video file
            output_path: Optional output path for audio file
            
        Returns:
            Path to extracted audio file
        """
        if output_path is None:
            output_path = video_path.replace('.mp4', '.wav')
        
        try:
            command = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # Audio codec
                '-ar', '16000',  # Sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite
                output_path
            ]
            
            subprocess.run(command, check=True, capture_output=True)
            print(f"Audio extracted to: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e}")
            return None
        except FileNotFoundError:
            print("ffmpeg not found. Please install ffmpeg.")
            return None
    
    def extract_frames(self, video_path: str, output_dir: str = None, 
                      frame_rate: int = 1) -> list:
        """
        Extract frames from video
        
        Args:
            video_path: Path to video file
            output_dir: Directory to save frames
            frame_rate: Extract 1 frame every N seconds
            
        Returns:
            List of frame file paths
        """
        if output_dir is None:
            output_dir = "temp_frames"
        
        os.makedirs(output_dir, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * frame_rate)
        
        frame_count = 0
        extracted_frames = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                frame_path = os.path.join(output_dir, f"frame_{frame_count:06d}.jpg")
                cv2.imwrite(frame_path, frame)
                extracted_frames.append(frame_path)
                print(f"Extracted frame: {frame_path}")
            
            frame_count += 1
        
        cap.release()
        print(f"Extracted {len(extracted_frames)} frames")
        return extracted_frames
    
    def get_video_info(self, video_path: str) -> dict:
        """Get video metadata"""
        cap = cv2.VideoCapture(video_path)
        
        info = {
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
        }
        
        cap.release()
        return info

if __name__ == "__main__":
    processor = VideoProcessor()
    print("VideoProcessor initialized successfully!")