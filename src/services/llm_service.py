"""LLM service for text generation using Azure OpenAI."""

from typing import Optional, List, Dict, Any
from loguru import logger
from ..config.settings import get_settings
from ..core.semantic_kernel_setup import sk_manager

settings = get_settings()


class LLMService:
    """Service for text generation using Azure OpenAI."""

    def __init__(self):
        self._chat_service = None

    async def initialize(self):
        """Initialize the LLM service."""
        kernel = sk_manager.get_kernel()
        self._chat_service = sk_manager.chat_service
        logger.info("LLM service initialized")

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate a text response.

        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        if not self._chat_service:
            await self.initialize()

        try:
            from semantic_kernel.contents import ChatHistory
            from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
            
            # Create chat history
            chat_history = ChatHistory()
            
            if system_prompt:
                chat_history.add_system_message(system_prompt)
            
            chat_history.add_user_message(prompt)
            
            # Create settings
            settings = AzureChatPromptExecutionSettings(
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Get completion using get_chat_message_contents
            response = await self._chat_service.get_chat_message_contents(
                chat_history=chat_history,
                settings=settings,
            )
            
            # Extract text from response
            if response and len(response) > 0:
                return str(response[0].content)
            else:
                return ""
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate a response from a chat conversation.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response
        """
        if not self._chat_service:
            await self.initialize()

        try:
            from semantic_kernel.contents import ChatHistory
            from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
            
            # Create chat history from messages
            chat_history = ChatHistory()
            
            for msg in messages:
                role = msg.get("role", "user").lower()
                content = msg.get("content", "")
                
                if role == "system":
                    chat_history.add_system_message(content)
                elif role == "assistant":
                    chat_history.add_assistant_message(content)
                else:
                    chat_history.add_user_message(content)
            
            # Create settings
            settings = AzureChatPromptExecutionSettings(
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Get completion
            response = await self._chat_service.get_chat_message_contents(
                chat_history=chat_history,
                settings=settings,
            )
            
            if response and len(response) > 0:
                return str(response[0].content)
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            raise

# Global instance
llm_service = LLMService()