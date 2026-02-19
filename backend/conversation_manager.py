"""
Conversation Manager
Handles chat history, context, and natural language queries
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class ConversationManager:
    def __init__(self):
        self.conversations_dir = "conversations"
        os.makedirs(self.conversations_dir, exist_ok=True)
        self.current_conversation = None
        self.current_context = {}
    
    def start_conversation(self, conversation_id: str = None) -> str:
        """Start a new conversation or resume existing one"""
        if conversation_id is None:
            conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.current_conversation = conversation_id
        
        conversation = self.load_conversation(conversation_id)
        if conversation:
            print(f"[ConversationManager] Resumed conversation: {conversation_id}")
        else:
            conversation = {
                "id": conversation_id,
                "created_at": datetime.now().isoformat(),
                "messages": [],
                "context": {}
            }
            self.save_conversation(conversation)
            print(f"[ConversationManager] Started new conversation: {conversation_id}")
        
        return conversation_id
    
    def add_message(self, role: str, content: str, metadata: dict = None):
        """Add a message to current conversation"""
        if not self.current_conversation:
            self.start_conversation()
        
        conversation = self.load_conversation(self.current_conversation)
        
        if conversation is None:
            self.start_conversation(self.current_conversation)
            conversation = self.load_conversation(self.current_conversation)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        conversation["messages"].append(message)
        self.save_conversation(conversation)
    
    def get_conversation_history(self, conversation_id: str = None) -> List[Dict]:
        """Get all messages from a conversation"""
        conv_id = conversation_id or self.current_conversation
        conversation = self.load_conversation(conv_id)
        return conversation["messages"] if conversation else []
    
    def update_context(self, key: str, value: any):
        """Update conversation context (e.g., last analyzed video)"""
        if not self.current_conversation:
            self.start_conversation()
        
        conversation = self.load_conversation(self.current_conversation)
        conversation["context"][key] = value
        self.save_conversation(conversation)
        self.current_context[key] = value
    
    def get_context(self, key: str) -> Optional[any]:
        """Get value from conversation context"""
        if not self.current_conversation:
            return None
        
        if key in self.current_context:
            return self.current_context[key]
        
        conversation = self.load_conversation(self.current_conversation)
        return conversation.get("context", {}).get(key)
    
    def save_conversation(self, conversation: dict):
        """Save conversation to file"""
        filepath = os.path.join(
            self.conversations_dir, 
            f"{conversation['id']}.json"
        )
        with open(filepath, 'w') as f:
            json.dump(conversation, f, indent=2)

    def load_conversation(self, conversation_id: str) -> Optional[dict]:
        if not conversation_id:
            return None

        filepath = os.path.join(self.conversations_dir, f"{conversation_id}.json")

        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print("[ConversationManager] Failed to load:", e)
            return None

    
    def list_conversations(self) -> List[str]:
        """List all conversation IDs"""
        files = os.listdir(self.conversations_dir)
        return [f.replace('.json', '') for f in files if f.endswith('.json')]

    def update_analysis_context(self, video_name: str, analysis_id: str):
        """Update context with analysis information"""
        self.update_context("current_video", video_name)
        self.update_context("last_analysis_id", analysis_id)
        self.update_context("has_analysis", True)
        print(f"[ConversationManager] Context updated: video={video_name}, analysis={analysis_id}")

conversation_manager = ConversationManager()