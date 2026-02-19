"""
Test the complete backend pipeline
"""
import asyncio
from orchestrator.workflow import VideoAnalysisOrchestrator
import json

async def progress_callback(stage, progress, message):
    print(f"[Progress] {stage}: {progress}% - {message}")

async def main():
    print("=" * 60)
    print("Testing Video Analysis Backend")
    print("=" * 60)
    
    orchestrator = VideoAnalysisOrchestrator()
    
    video_path = r"D:\Users\User\ProjectVSCode\video-analyzer\backend\sample_video.mp4"
    
    print(f"\nAnalyzing video: {video_path}\n")
    
    results = await orchestrator.analyze_video(
        video_path=video_path,
        video_name="Test Video",
        progress_callback=progress_callback
    )
    
    print("\n" + "=" * 60)
    print("Analysis Results:")
    print("=" * 60)
    print(json.dumps(results, indent=2))
    
    print("\n" + "=" * 60)
    print("Generating PowerPoint Report...")
    print("=" * 60)
    
    report_result = await orchestrator.generate_report(
        analysis_data=results,
        format="pptx",
        output_path="output/test_report.pptx"
    )
    
    print(f"\nReport generation result: {report_result}")

if __name__ == "__main__":
    asyncio.run(main())