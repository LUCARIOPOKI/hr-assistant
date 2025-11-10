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
            # For SK v1.x, we'll use the chat service directly
            # Construct messages if system prompt is provided
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            result = await self._chat_service.complete_async(
                prompt=full_prompt,
                settings=self._get_completion_settings(temperature, max_tokens),
            )
            
            return str(result)
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
            # Convert messages to a prompt format
            prompt = self._format_chat_messages(messages)
            result = await self._chat_service.complete_async(
                prompt=prompt,
                settings=self._get_completion_settings(temperature, max_tokens),
            )
            return str(result)
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            raise

    def _format_chat_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages into a single prompt."""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role.upper()}: {content}")
        return "\n\n".join(formatted)

    def _get_completion_settings(self, temperature: float, max_tokens: int) -> Any:
        """Create completion settings object."""
        # This is a simplified version; adjust based on SK version
        try:
            from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
            return OpenAIChatPromptExecutionSettings(
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except ImportError:
            # Fallback for different SK versions
            return None


# Global instance
llm_service = LLMService()
