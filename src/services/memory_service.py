"""Memory service for managing conversation history."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger


class MemoryService:
    """Service for managing conversation memory and history."""

    def __init__(self):
        # In-memory storage for now; can be replaced with Redis or DB
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}

    def create_session(self, session_id: str, user_id: str, metadata: Optional[Dict[str, Any]] = None):
        """Create a new conversation session."""
        if session_id not in self._conversations:
            self._conversations[session_id] = []
            logger.info(f"Created conversation session: {session_id} for user: {user_id}")

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Add a message to the conversation history.

        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        if session_id not in self._conversations:
            self._conversations[session_id] = []

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        self._conversations[session_id].append(message)
        logger.debug(f"Added {role} message to session {session_id}")

    def get_conversation(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages to return

        Returns:
            List of messages
        """
        messages = self._conversations.get(session_id, [])
        if limit:
            return messages[-limit:]
        return messages

    def get_formatted_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> str:
        """
        Get formatted conversation history as a string.

        Args:
            session_id: Session identifier
            limit: Optional limit on messages

        Returns:
            Formatted conversation string
        """
        messages = self.get_conversation(session_id, limit)
        formatted = []
        for msg in messages:
            role = msg["role"].upper()
            content = msg["content"]
            formatted.append(f"{role}: {content}")
        return "\n\n".join(formatted)

    def clear_session(self, session_id: str):
        """Clear conversation history for a session."""
        if session_id in self._conversations:
            del self._conversations[session_id]
            logger.info(f"Cleared session: {session_id}")

    def get_context_for_llm(
        self,
        session_id: str,
        max_messages: int = 10,
    ) -> List[Dict[str, str]]:
        """
        Get conversation context formatted for LLM.

        Args:
            session_id: Session identifier
            max_messages: Maximum number of recent messages

        Returns:
            List of message dicts with role and content
        """
        messages = self.get_conversation(session_id, limit=max_messages)
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]


# Global instance
memory_service = MemoryService()
