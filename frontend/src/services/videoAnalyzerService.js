/**
 * Video Analyzer Service
 * Works in both browser and Tauri desktop app
 */

class VideoAnalyzerService {
  constructor() {
    this.httpServerUrl = 'http://localhost:5000';
    this.isTauri = false;
    this.tauriInvoke = null;
    
    // Detect if running in Tauri
    this.checkTauriEnvironment();
  }

  async checkTauriEnvironment() {
    try {
      // Try to import Tauri API
      const tauri = await import('@tauri-apps/api/core');
      this.isTauri = true;
      this.tauriInvoke = tauri.invoke;
      console.log('[Service] Running in Tauri desktop app');
    } catch {
      this.isTauri = false;
      console.log('[Service] Running in browser');
    }
  }

  /**
   * Analyze video - uses Tauri if available, otherwise HTTP
   */
  async analyzeVideo(file, onProgress) {
    try {
      console.log('[Service] Starting analysis:', file.name);
      
      if (this.isTauri && this.tauriInvoke) {
        // Use Tauri invoke (desktop app)
        return await this.analyzeViaTauri(file, onProgress);
      } else {
        // Use HTTP (browser)
        return await this.analyzeViaHTTP(file, onProgress);
      }
      
    } catch (error) {
      console.error('[Service] Error:', error);
      
      onProgress({
        stage: 'error',
        progress: 0,
        message: error.message || 'Unknown error'
      });
      
      throw error;
    }
  }

  /**
   * Analyze via Tauri invoke (desktop app)
   */
  async analyzeViaTauri(file, onProgress) {
    onProgress({
      stage: 'starting',
      progress: 10,
      message: 'Reading video file...'
    });

    // Read file as array buffer
    const arrayBuffer = await file.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);
    const videoData = Array.from(uint8Array);

    onProgress({
      stage: 'uploading',
      progress: 30,
      message: 'Sending to backend...'
    });

    // Call Tauri command
    const resultStr = await this.tauriInvoke('analyze_video_grpc', {
      videoData: videoData,
      videoName: file.name
    });

    // Parse result
    const result = JSON.parse(resultStr);

    onProgress({
      stage: 'complete',
      progress: 100,
      message: 'Analysis complete!',
      result: result
    });

    return {
      success: true,
      data: result
    };
  }

  /**
   * Analyze via HTTP (browser)
   */
  async analyzeViaHTTP(file, onProgress) {
    onProgress({
      stage: 'starting',
      progress: 10,
      message: 'Uploading video to backend...'
    });

    // Create form data
    const formData = new FormData();
    formData.append('video', file);

    onProgress({
      stage: 'uploading',
      progress: 30,
      message: 'Analyzing video...'
    });

    // Call HTTP server
    const response = await fetch(`${this.httpServerUrl}/analyze`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    onProgress({
      stage: 'complete',
      progress: 100,
      message: 'Analysis complete!',
      result: result
    });

    return {
      success: true,
      data: result
    };
  }

  /**
   * Check if HTTP backend is running
   */
  async checkHealth() {
    try {
      const response = await fetch(`${this.httpServerUrl}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }
}

export default new VideoAnalyzerService();