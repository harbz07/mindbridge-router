"""
Simple in-memory conversation store for maintaining context.
"""

from typing import Dict, List
from collections import defaultdict, deque
from app.models import ChatMessage


class ConversationMemory:
    """
    In-memory storage for conversation history.
    
    This is a basic implementation that stores conversations in memory.
    For production, this should be replaced with a persistent store
    (e.g., Redis, PostgreSQL, or Notion Memory Archive).
    """
    
    def __init__(self, max_messages_per_conversation: int = 50):
        """
        Initialize the conversation memory.
        
        Args:
            max_messages_per_conversation: Maximum number of messages to store per conversation
        """
        self.max_messages = max_messages_per_conversation
        # Store conversations as deques for efficient append/pop operations
        self._conversations: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.max_messages)
        )
    
    def add_message(self, conversation_id: str, message: ChatMessage) -> None:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            message: The message to add
        """
        self._conversations[conversation_id].append(message)
    
    def get_conversation(self, conversation_id: str) -> List[ChatMessage]:
        """
        Retrieve all messages in a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            List of messages in the conversation
        """
        return list(self._conversations.get(conversation_id, []))
    
    def clear_conversation(self, conversation_id: str) -> None:
        """
        Clear all messages in a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
    
    def get_recent_messages(
        self, 
        conversation_id: str, 
        n: int = 10
    ) -> List[ChatMessage]:
        """
        Get the n most recent messages from a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            n: Number of recent messages to retrieve
            
        Returns:
            List of recent messages
        """
        conversation = self._conversations.get(conversation_id, deque())
        # Get the last n messages
        return list(conversation)[-n:]


# Global instance
conversation_memory = ConversationMemory()
