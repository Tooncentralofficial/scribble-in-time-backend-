from datetime import datetime
from django.core.cache import cache
from django.conf import settings
import json
from typing import List, Dict, Any, Optional
import uuid

class MemorySystem:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        
        # Memory type keys
        self.episodic_key = f"episodic_{self.session_id}"  # For user-specific experiences
        self.semantic_key = f"semantic_{self.session_id}"  # For general knowledge
        self.procedural_key = f"procedural_{self.session_id}"  # For task procedures
        
        # Context window for conversation history
        self.context_window = 5

    # Episodic Memory Methods
    def get_episodic_memory(self) -> List[Dict[str, str]]:
        """Retrieve episodic memory (user-specific experiences)"""
        return cache.get(self.episodic_key, [])

    def add_episodic_memory(self, role: str, content: str):
        """Add to episodic memory (user-specific experiences)"""
        current = self.get_episodic_memory()
        current.append({
            "role": role,
            "content": content,
            "timestamp": str(datetime.now())
        })
        # Keep only the most recent messages within context window
        current = current[-self.context_window:]
        # Cache for 24 hours of inactivity
        cache.set(self.episodic_key, current, timeout=86400)

    # Semantic Memory Methods
    def get_semantic_memory(self) -> Dict[str, Any]:
        """Retrieve semantic memory (general knowledge)"""
        return cache.get(self.semantic_key, {})

    def update_semantic_memory(self, key: str, value: Any):
        """Update semantic memory with new knowledge"""
        current = self.get_semantic_memory()
        current[key] = value
        # Cache for 30 days
        cache.set(self.semantic_key, current, timeout=2592000)

    # Procedural Memory Methods
    def get_procedures(self) -> List[Dict[str, Any]]:
        """Retrieve stored procedures"""
        return cache.get(self.procedural_key, [])

    def add_procedure(self, name: str, steps: List[str]):
        """Add a new procedure to memory"""
        procedures = self.get_procedures()
        procedures.append({
            "name": name,
            "steps": steps,
            "last_used": str(datetime.now())
        })
        cache.set(self.procedural_key, procedures, timeout=2592000)

    def get_conversation_context(self) -> List[Dict[str, str]]:
        """Get the conversation context with system prompt and relevant memories"""
        system_prompt = {
            "role": "system",
            "content": """You are Uche, a polite and professional customer representative assistant for Scribble in Time. 
            Follow these guidelines for every response:
            1. Be concise and answer directly to the point
            2. Keep responses to a maximum of 3 sentences
            3. Only answer questions related to Scribble in Time services
            4. If you can't answer a question or it's outside your knowledge, politely say:
               "I'll need to check on that for you. Please email us at contact.ascribbleintime@gmail.com and our team will respond as soon as possible."
            5. Always be courteous and helpful
            6. Sign off as 'Uche from Scribble in Time' at the end of each response
            
            Available memories:
            - Episodic: Previous interactions with this user
            - Semantic: General knowledge about our services
            - Procedural: How to perform common tasks"""
        }
        return [system_prompt] + self.get_episodic_memory()

    # Conversation Management
    def add_user_message(self, content: str):
        """Add a user message to episodic memory"""
        self.add_episodic_memory("user", content)

    def add_assistant_message(self, content: str):
        """Add an assistant message to episodic memory"""
        self.add_episodic_memory("assistant", content)

    def clear_session(self):
        """Clear the current session's memories"""
        cache.delete(self.episodic_key)
        cache.delete(self.semantic_key)
        cache.delete(self.procedural_key)
        
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of all memory types"""
        return {
            "episodic": {
                "count": len(self.get_episodic_memory()),
                "description": "User-specific conversation history"
            },
            "semantic": {
                "count": len(self.get_semantic_memory()),
                "description": "General knowledge and facts"
            },
            "procedural": {
                "count": len(self.get_procedures()),
                "description": "Stored procedures and workflows"
            }
        }
