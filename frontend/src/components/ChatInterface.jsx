import { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';

function ChatInterface({ messages, onAnalyze, isAnalyzing }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="chat-interface">
      <div className="messages-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}`}>
            <div className="message-content">
              {msg.type === 'user' && <strong>You:</strong>}
              {msg.type === 'assistant' && <strong>AI:</strong>}
              {msg.type === 'progress' && <strong>Progress:</strong>}

              {msg.isJSX ? (
                msg.content
              ) : (
                <p>{msg.content}</p>
              )}

              {msg.progress !== undefined && (
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${msg.progress}%` }}
                  ></div>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      {isAnalyzing && (
        <div className="analyzing-indicator">
          <div className="spinner"></div>
          <span>Analyzing video...</span>
        </div>
      )}
    </div>
  );
}

export default ChatInterface;