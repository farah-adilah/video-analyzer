import { useState, useEffect } from 'react';
import VideoUpload from './components/VideoUpload';
import ChatInterface from './components/ChatInterface';
import videoAnalyzerService from './services/videoAnalyzerService';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    { type: 'assistant', content: 'Welcome to Video AI Analyzer! Upload an MP4 video to get started.' }
  ]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentVideo, setCurrentVideo] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [reportFormat, setReportFormat] = useState('pptx');
  const [conversationId, setConversationId] = useState(
    () => new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
  );
  const [chatInput, setChatInput] = useState('');

  // Load conversation history on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        const historyStr = await invoke('get_conversation_history', {
          conversationId: conversationId
        });
        
        const history = JSON.parse(historyStr);
        
        if (history && history.length > 0) {
          const loadedMessages = history.map(msg => ({
            type: msg.role === 'user' ? 'user' : 'assistant',
            content: msg.content
          }));
          
          setMessages([
            { type: 'assistant', content: '🎥 Welcome back! Previous conversation loaded.' },
            ...loadedMessages
          ]);
        }
      } catch (error) {
        console.log("No previous conversation found");
      }
    };
    
    loadHistory();
  }, []);

  const handleVideoSelect = async (file) => {
    setCurrentVideo(file);
    setMessages(prev => [...prev, 
      { type: 'user', content: `Selected video: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`}
    ]);

    setMessages(prev => [...prev, 
      { type: 'progress', content: '🔄 Connecting to backend...', progress: 10 }
    ]);

    // Simulate analysis (we'll connect to backend later)
    setIsAnalyzing(true);
    
    try {
      // await videoAnalyzerService.analyzeVideo(file, (update) => {
      await videoAnalyzerService.analyzeVideo(file, async (update) => {  // ← Add async here
        // Add progress message
        // setMessages(prev => [...prev, 
        //   { 
        //     type: 'progress', 
        //     content: update.message,
        //     progress: update.progress,
        //     stage: update.stage
        //   }
        // ]);

        if (update.stage !== 'complete') {
          // Replace progress message (not add new one)
          setMessages(prev => {
            const nonProgress = prev.filter(msg => msg.type !== 'progress');
            return [
              ...nonProgress,
              { 
                type: 'progress', 
                content: '🔄 Analyzing video...',
                progress: update.progress,
                stage: update.stage
              }
            ];
          });
        }

        if (update.stage === 'complete' && update.result) {
          setMessages(prev => prev.filter(msg => msg.type !== 'progress'));
          setAnalysisResults(update.result);

          const contextUpdate = {
            current_video: file.name,
            last_analysis_id: update.result.analysis_id,
            has_analysis: true
          };
          // Store that we have an analyzed video
          // const contextUpdate = {
          //   current_video: file.name,
          //   last_analysis_id: update.result.analysis_id,
          //   has_analysis: true
          // };
          
          // Update via chat to save context
          try {
            const { invoke } = await import('@tauri-apps/api/core');
            await invoke('send_chat_message', {
              message: `__CONTEXT_UPDATE__:${JSON.stringify(contextUpdate)}`,
              conversationId: conversationId,
              contextJson: JSON.stringify(contextUpdate)
            });
          } catch (error) {
            console.log("Context update failed:", error);
          }
                    
          // Display results
          const videoInfo = update.result.video_info;
          const transcription = update.result.transcription;
          const vision = update.result.vision;
          
          // let resultMessage = '✅ **Analysis Complete!**\n\n';
          
          // // Video info
          // if (videoInfo) {
          //   resultMessage += `📊 **Video Info:**\n`;
          //   resultMessage += `- Resolution: ${videoInfo.width}x${videoInfo.height}\n`;
          //   resultMessage += `- Duration: ${videoInfo.duration.toFixed(1)}s\n`;
          //   resultMessage += `- FPS: ${videoInfo.fps}\n\n`;
          // }
          
          // // Transcription
          // if (transcription && !transcription.error) {
          //   resultMessage += `🎤 **Transcription:**\n${transcription.transcription}\n\n`;
          // } else if (transcription && transcription.error) {
          //   resultMessage += `⚠️ **Transcription:** ${transcription.error}\n\n`;
          // }
          
          // // Vision analysis
          // if (vision && vision.captions) {
          //   resultMessage += `🎬 **Visual Analysis:**\n`;
          //   resultMessage += `- Analyzed ${vision.analyzed_frames} frames \n\n`;
          //   resultMessage += `**Key Scenes:**\n`;

          //   vision.captions.forEach((cap, idx) => {
          //     if (cap.caption) {
          //       resultMessage += `${idx + 1}. ${cap.caption} (${cap.timestamp}s)\n`;
          //     }
          //   });
          // }
          
          // setMessages(prev => [...prev, 
          //   { type: 'assistant', content: resultMessage }
          // ]);

          const resultContent = (
            <div className="analysis-results">
              <h3>✅ Analysis Complete!</h3>

              {update.result.ai_summary && (
                <div className="result-section">
                  <h4>Summary:</h4>
                  <p className="ai-summary">
                    {update.result.ai_summary
                      .replace(/Based on the video analysis data.*?follows:/gi, '')
                      .replace(/Video duration:.*?\n/gi, '')
                      .replace(/Resolution:.*?\n/gi, '')
                      .replace(/Narration:.*?\n/gi, '')
                      .trim()}
                  </p>
                </div>
              )}
              
              {videoInfo && (
                <div className="result-section">
                  <h4>Video Info:</h4>
                  <ul>
                    <li>Resolution: {videoInfo.width}x{videoInfo.height}</li>
                    <li>Duration: {videoInfo.duration.toFixed(1)}s</li>
                    <li>FPS: {videoInfo.fps}</li>
                  </ul>
                </div>
              )}
              
              {transcription && (
                <div className="result-section">
                  <h4>Transcription:</h4>
                  {transcription.error ? (
                    <p className="error-text">⚠️ {transcription.error}</p>
                  ) : transcription.transcription && transcription.transcription.trim() ? (
                    <p className="transcription-text">{transcription.transcription}</p>
                  ) : (
                    <p className="no-content-text">
                      🔇 No speech detected in this video. The video may be silent 
                      or contain only background noise/music.
                    </p>
                  )}
                </div>
              )}
              
              {/* {vision && vision.captions && vision.captions.length > 0 && (
                <div className="result-section">
                  <h4>🎬 Visual Analysis:</h4>
                  <p>Analyzed {vision.analyzed_frames} frames</p>
                  <div className="key-scenes">
                    <strong>Key Scenes:</strong>
                    <ol>
                      {vision.captions.map((cap, idx) => (
                        cap.caption && (
                          <li key={idx}>
                            {cap.caption} <span className="timestamp">({cap.timestamp}s)</span>
                          </li>
                        )
                      ))}
                    </ol>
                  </div>
                </div>
              )} */}
            </div>
          );
          setMessages(prev => [...prev,
            { type: 'assistant', content: resultContent, isJSX: true }
          ]);
        } else if (update.stage === 'error') {
          setMessages(prev => [...prev, 
            { type: 'error', content: `❌ ${update.message}` }
          ]);
        }
      });



    } catch (error) {
      setMessages(prev => [...prev, 
        { type: 'error', content: `❌ Error: ${error.message}` }
      ]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleDownloadReport = async (formatOverride = null) => {
    if (!analysisResults) {
      alert('No analysis results available yet!');
      return;
    }

    const analysisId = analysisResults.analysis_id;
    if (!analysisId) {
      setMessages(prev => [...prev, 
        { 
          type: 'error', 
          content: `No analysis ID found!` 
        }
      ]);
      return;
    }

    const format = formatOverride || reportFormat;

    setMessages(prev => [...prev, 
      { type: 'assistant', content: `📄 Generating ${reportFormat.toUpperCase()} report...`}
    ]);
    
    try {
      // Import Tauri API
      const { invoke } = await import('@tauri-apps/api/core');
      
      // Call Tauri command
      const resultStr = await invoke('generate_report', {
        analysisId: analysisId,
        // format: reportFormat
        format: format
      });
      
      const result = JSON.parse(resultStr);
      
      if (result.success) {
        setMessages(prev => [...prev, 
          { 
            type: 'assistant', 
            content: `✅ ${reportFormat.toUpperCase()} generated successfully!\n\nFile: ${result.filename}\nLocation: backend/output/${result.filename}\n\n📂 Open the backend/output folder to view your report!` 
          }
        ]);
      } else {
        setMessages(prev => [...prev, 
          { type: 'error', content: `❌ ${result.error}` }
        ]);
      }
      
    } catch (error) {
      setMessages(prev => [...prev, 
        { type: 'error', content: `❌ Error: ${error}` }
      ]);
    }
  };

  // Add this useEffect near the top with other useEffects
  const [pendingReportGeneration, setPendingReportGeneration] = useState(false);

  useEffect(() => {
    if (pendingReportGeneration && reportFormat) {
      setPendingReportGeneration(false);
      handleDownloadReport();
    }
  }, [reportFormat, pendingReportGeneration]);

  const handleChatMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMessage = chatInput;
    setChatInput('');
    
    // Add user message to UI
    setMessages(prev => [...prev, 
      { type: 'user', content: userMessage }
    ]);
    
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      
      // Prepare context
      const context = {
        current_video: currentVideo?.name,
        last_analysis_id: analysisResults?.analysis_id
      };
      
      // Send to backend
      const resultStr = await invoke('send_chat_message', {
        message: userMessage,
        conversationId: conversationId,
        contextJson: JSON.stringify(context)
      });
      
      const result = JSON.parse(resultStr);
      
      // Handle response
      if (result.type === 'clarification') {
        // Bot is asking for clarification
        setMessages(prev => [...prev, 
          { type: 'assistant', content: result.message }
        ]);
      } else if (result.type === 'action_required') {

        // Bot needs to perform an action
        // setMessages(prev => [...prev, 
        //   { type: 'assistant', content: result.message }
        // ]);
        
        let focus = 'all';
          try {
            if (result.data && result.data.focus) {
              // const data = JSON.parse(result.data_json);
              // focus = data.focus || 'all';
              focus = result.data.focus;
            }
            else if (result.data_json){
              const data = JSON.parse(result.data_json);
              focus = data.focus || 'all';
            }
            else if (result.focus) {
              focus = result.focus;
            }
          } catch {
            focus = 'all';
          }

          console.log('[Chat] Action:', result.action, 'Focus:', focus); // Debug log

        // Trigger action
        // if (result.action === 'analyze_video' && currentVideo) {
        //   handleVideoSelect(currentVideo);
        // } else if (result.action === 'generate_report') {
        //   const format = result.format || 'pptx';
        //   setReportFormat(format);
        //   setTimeout(() => handleDownloadReport(), 500);
        // }

        if (result.action === 'analyze_video' && currentVideo) {
          // Store what user asked for
          // const focus = result.focus || 'all';

          // If we already have analysis results, use them!
          if (analysisResults) {
            showFocusedResults(analysisResults, focus, result.message);
          } else {
            // Only re-analyze if no results exist
            await analyzeVideoWithFocus(currentVideo, focus);
          }
          
        } else if (result.action === 'generate_report') {

          // const format = result.format || 'pptx';

          let format = 'pptx'; // default
  
          // Check result.data first (most reliable)
          if (result.data && result.data.format && result.data.format !== '') {
            format = result.data.format;
          }
          // Then check data_json
          // else if (result.data_json) {
          //   try {
          //     const data = JSON.parse(result.data_json);
          //     if (data.format && data.format !== '') {
          //       format = data.format;
          //     }
          //   } catch {}
          // }
          
          // Also check message for clues (backup)
          else if (result.message && result.message.toLowerCase().includes('pdf')) {
              format = 'pdf';
          } else if (result.message && 
                    (result.message.toLowerCase().includes('powerpoint') || 
                      result.message.toLowerCase().includes('pptx'))) {
            format = 'pptx';
          }
          setReportFormat(format);
          // setTimeout(() => handleDownloadReport(), 500);
          // handleDownloadReport(format);
          setPendingReportGeneration(true);

        }
      } else {
        // Regular response
        setMessages(prev => [...prev, 
          { type: 'assistant', content: result.message }
        ]);
      }
      
    } catch (error) {
      setMessages(prev => [...prev, 
        { type: 'error', content: `❌ Error: ${error}` }
      ]);
    }
  };

  const showFocusedResults = (results, focus, prefixMessage = null) => {
    const vision = results.vision;
    const transcription = results.transcription;
    const videoInfo = results.video_info;
    
    let resultContent;
    
    if (focus === 'objects' || focus === 'vision') {
      // Show ONLY objects/captions
      resultContent = (
        <div className="analysis-results">
          {prefixMessage && <p>{prefixMessage}</p>}
          {vision && vision.captions && vision.captions.length > 0 ? (
            <div className="result-section">
              <ul>
                {vision.captions.map((cap, idx) => (
                  cap.caption && (
                    <li key={idx}>
                      <strong>Scene {idx + 1}:</strong> {cap.caption}
                      <span className="timestamp"> (at {cap.timestamp}s)</span>
                    </li>
                  )
                ))}
              </ul>
            </div>
          ) : (
            <p>No objects detected in the video.</p>
          )}
        </div>
      );
    } else if (focus === 'transcription') {
      // Show ONLY transcription
      resultContent = (
        <div className="analysis-results">
          {/* <h3>🎤 Transcription:</h3> */}
          {prefixMessage && <p>{prefixMessage}</p>}
          
          {/* {transcription && (
            <div className="result-section">
              {transcription.error ? (
                <p className="error-text">⚠️ {transcription.error}</p>
              ) : (
                <p className="transcription-text">{transcription.transcription}</p>
              )}
            </div>
          )}
        </div> */}
          {transcription ? (
            <div className="result-section">
              {transcription.error ? (
                <p className="error-text">⚠️ {transcription.error}</p>
              ) : transcription.transcription && transcription.transcription.trim().length > 0 ? (
                <p className="transcription-text">{transcription.transcription}</p>
              ) : (
                // ← THIS HANDLES EMPTY TRANSCRIPTION
                <p className="no-content-text">
                  🔇 No speech detected in this video. The video may be 
                  silent or contain only background noise/music.
                </p>
              )}
            </div>
          ) : (
            <p className="no-content-text">
              🔇 No speech detected in this video. The video may be 
              silent or contain only background noise/music.
            </p>
          )}
        </div>
      );
    } else if (focus === 'summary') {
      // Show ONLY summary
      resultContent = (
        <div className="analysis-results">
          {/* <h3>📝 Summary:</h3> */}
          {prefixMessage && <p>{prefixMessage}</p>}
          
          {results.ai_summary ? (
            <div className="result-section">
              <p className="ai-summary">
                {results.ai_summary
                  .replace(/Based on the video analysis data.*?follows:/gi, '')
                  .replace(/Video duration:.*?\n/gi, '')
                  .replace(/Resolution:.*?\n/gi, '')
                  .replace(/Narration:.*?\n/gi, '')
                  .trim()}
              </p>
            </div>
          ) : (
            <p>No summary available.</p>
          )}
        </div>
      );
    } else if (focus === 'video_info') {
      // Show ONLY video info
      resultContent = (
        <div className="analysis-results">
          {/* <h3>📊 Video Info:</h3> */}
          {prefixMessage && <p>{prefixMessage}</p>}
          
          {videoInfo && (
            <div className="result-section">
              <ul>
                <li>Resolution: {videoInfo.width}x{videoInfo.height}</li>
                <li>Duration: {videoInfo.duration.toFixed(1)}s</li>
                <li>FPS: {videoInfo.fps}</li>
              </ul>
            </div>
          )}
        </div>
      );
    } else if (focus === 'graphs') {
        resultContent = (
          <div className="analysis-results">
            {prefixMessage && <p>{prefixMessage}</p>}
            {vision && vision.captions ? (
              (() => {
                const graphKeywords = ['graph', 'chart', 'plot', 'diagram', 'bar', 'pie'];
                const graphScenes = vision.captions.filter(cap => 
                  cap.caption && graphKeywords.some(kw => 
                    cap.caption.toLowerCase().includes(kw)
                  )
                );
                
                return graphScenes.length > 0 ? (
                  <div className="result-section">
                    <p>Found potential graphs/charts:</p>
                    <ul>
                      {graphScenes.map((cap, idx) => (
                        <li key={idx}>
                          {cap.caption}
                          <span className="timestamp"> (at {cap.timestamp}s)</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p>No graphs or charts detected in this video.</p>
                );
              })()
            ) : (
              <p>No visual analysis available.</p>
            )}
          </div>
        );
      } else {
      // Show all (default) - only called when explicitly needed
      resultContent = (
        <div className="analysis-results">
          {/* <h3>✅ Analysis Results:</h3> */}
          {prefixMessage && <p>{prefixMessage}</p>}
          
          {results.ai_summary && (
            <div className="result-section">
              <h4>📝 Summary:</h4>
              <p className="ai-summary">
                {results.ai_summary
                  .replace(/Based on the video analysis data.*?follows:/gi, '')
                  .trim()}
              </p>
            </div>
          )}
          
          {videoInfo && (
            <div className="result-section">
              <h4>📊 Video Info:</h4>
              <ul>
                <li>Resolution: {videoInfo.width}x{videoInfo.height}</li>
                <li>Duration: {videoInfo.duration.toFixed(1)}s</li>
                <li>FPS: {videoInfo.fps}</li>
              </ul>
            </div>
          )}
          
          {transcription && (
            <div className="result-section">
              <h4>🎤 Transcription:</h4>
              {transcription.error ? (
                <p className="error-text">⚠️ {transcription.error}</p>
              ) : (
                <p className="transcription-text">{transcription.transcription}</p>
              )}
            </div>
          )}
          
          {vision && vision.captions && (
            <div className="result-section">
              <h4>🔍 Objects:</h4>
              <ul>
                {vision.captions.map((cap, idx) => (
                  cap.caption && (
                    <li key={idx}>
                      Scene {idx + 1}: {cap.caption}
                      <span className="timestamp"> (at {cap.timestamp}s)</span>
                    </li>
                  )
                ))}
              </ul>
            </div>
          )}
        </div>
      );
    }
    
    setMessages(prev => [...prev, 
      { type: 'assistant', content: resultContent, isJSX: true }
    ]);
  };

  const analyzeVideoWithFocus = async (file, focus) => {
    setIsAnalyzing(true);
    
    try {
      await videoAnalyzerService.analyzeVideo(file, async (update) => {
        if (update.stage === 'complete' && update.result) {
          setAnalysisResults(update.result);
          
          // Update context
          const contextUpdate = {
            current_video: file.name,
            last_analysis_id: update.result.analysis_id,
            has_analysis: true
          };
          
          try {
            const { invoke } = await import('@tauri-apps/api/core');
            await invoke('send_chat_message', {
              message: `__CONTEXT_UPDATE__:${JSON.stringify(contextUpdate)}`,
              conversationId: conversationId,
              contextJson: JSON.stringify(contextUpdate)
            });
          } catch (error) {
            console.log("Context update failed:", error);
          }
          
          // ========== DISPLAY FOCUSED RESULTS ==========
          const videoInfo = update.result.video_info;
          const transcription = update.result.transcription;
          const vision = update.result.vision;
          
          let resultContent;
          
          if (focus === 'objects' || focus === 'vision') {
            // Show only objects
            resultContent = (
              <div className="analysis-results">
                <h3>🔍 Objects Found in Video:</h3>
                
                {vision && vision.captions && vision.captions.length > 0 && (
                  <div className="result-section">
                    <ul>
                      {vision.captions.map((cap, idx) => (
                        cap.caption && (
                          <li key={idx}>
                            <strong>Frame {idx + 1}:</strong> {cap.caption} <span className="timestamp">(at {cap.timestamp}s)</span>
                          </li>
                        )
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          } else if (focus === 'transcription') {
            // Show only transcription
            resultContent = (
              <div className="analysis-results">
                <h3>📝 Transcription:</h3>
                
                {transcription && (
                  <div className="result-section">
                    {transcription.error ? (
                      <p className="error-text">⚠️ {transcription.error}</p>
                    ) : (
                      <p className="transcription-text">{transcription.transcription}</p>
                    )}
                  </div>
                )}
              </div>
            );
          } else {
            // Show all (default)
            resultContent = (
              <div className="analysis-results">
                <h3>✅ Analysis Complete!</h3>
                
                {update.result.ai_summary && (
                  <div className="result-section">
                    <h4>📝 Summary:</h4>
                    <p className="ai-summary">
                      {update.result.ai_summary
                        .replace(/Based on the video analysis data.*?follows:/gi, '')
                        .replace(/Video duration:.*?\n/gi, '')
                        .replace(/Resolution:.*?\n/gi, '')
                        .replace(/Narration:.*?\n/gi, '')
                        .trim()}
                    </p>
                  </div>
                )}
                
                {videoInfo && (
                  <div className="result-section">
                    <h4>📊 Video Info:</h4>
                    <ul>
                      <li>Resolution: {videoInfo.width}x{videoInfo.height}</li>
                      <li>Duration: {videoInfo.duration.toFixed(1)}s</li>
                      <li>FPS: {videoInfo.fps}</li>
                    </ul>
                  </div>
                )}
                
                {transcription && (
                  <div className="result-section">
                    <h4>🎤 Transcription:</h4>
                    {transcription.error ? (
                      <p className="error-text">⚠️ {transcription.error}</p>
                    ) : (
                      <p className="transcription-text">{transcription.transcription}</p>
                    )}
                  </div>
                )}
                
                {vision && vision.captions && vision.captions.length > 0 && (
                  <div className="result-section">
                    <h4>🎬 Visual Analysis:</h4>
                    <p>Analyzed {vision.analyzed_frames} frames</p>
                  </div>
                )}
              </div>
            );
          }
          // =============================================
          
          setMessages(prev => [...prev, 
            { type: 'assistant', content: resultContent, isJSX: true }
          ]);
        }
      });
    } catch (error) {
      setMessages(prev => [...prev, 
        { type: 'error', content: `❌ Error: ${error.message}` }
      ]);
    } finally {
      setIsAnalyzing(false);
    }
  };


  return (
    <div className="app">
      <header className="app-header">
        <h1>🎥 Video AI Analyzer</h1>
        <p>Analyze short videos with local AI models</p>
      </header>

      <main className="app-main">
        <VideoUpload onVideoSelect={handleVideoSelect} />
        <ChatInterface 
          messages={messages} 
          isAnalyzing={isAnalyzing}
        />
        
        <div className="chat-input-container">
          <input
            type="text"
            className="chat-input"
            placeholder="Ask me anything... e.g., 'Transcribe the video' or 'Create a PowerPoint summary'"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleChatMessage()}
            disabled={isAnalyzing}
          />
          <button 
            className="send-button"
            onClick={handleChatMessage}
            disabled={isAnalyzing || !chatInput.trim()}
          >
            Send
          </button>
        </div>

        {analysisResults && !isAnalyzing && (
          <div className="actions">
            <div className="report-format">
              <label>
                <input 
                  type="radio" 
                  value="pptx" 
                  checked={reportFormat === 'pptx'}
                  onChange={(e) => setReportFormat(e.target.value)}
                />
                PowerPoint (.pptx)
              </label>
              <label>
                <input 
                  type="radio" 
                  value="pdf" 
                  checked={reportFormat === 'pdf'}
                  onChange={(e) => setReportFormat(e.target.value)}
                />
                PDF (.pdf)
              </label>
            </div>
            <button 
              className="action-button"
              onClick={() => handleDownloadReport()}
            >
              📄 Generate {reportFormat.toUpperCase()} Report
            </button>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>
          Powered by Local AI • No Cloud Required • 
          Backend: {isAnalyzing ? '🟢 Processing' : '⚪ Ready'}
        </p>
      </footer>
    </div>
  );
}

export default App;