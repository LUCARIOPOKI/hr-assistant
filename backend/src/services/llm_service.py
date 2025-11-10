"""LLM service for text generation using Azure OpenAI with agentic capabilities."""

from typing import Optional, List, Dict, Any
from loguru import logger
from ..config.settings import get_settings
from ..core.semantic_kernel_setup import sk_manager

settings = get_settings()


class LLMService:
    """Service for text generation using Azure OpenAI with agent support."""

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

    async def agent_execute(
        self,
        query: str,
        system_prompt: str,
        max_iterations: int = 5,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """
        Execute query using agentic approach with auto function calling.
        
        The agent will autonomously plan, call tools, and reason about the answer.
        
        Args:
            query: User question
            system_prompt: System context for the agent
            max_iterations: Maximum tool calling iterations
            temperature: Sampling temperature
            max_tokens: Maximum tokens per generation
            
        Returns:
            Dict with:
                - answer: Final response
                - tool_calls: List of tool calls made
                - iterations: Number of iterations
                - agent_plan: Agent's reasoning (if available)
        """
        if not self._chat_service:
            await self.initialize()
            
        try:
            from semantic_kernel.contents import ChatHistory
            from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
            from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
            
            kernel = sk_manager.get_kernel()
            
            # Create chat history with system prompt
            chat_history = ChatHistory()
            chat_history.add_system_message(system_prompt)
            chat_history.add_user_message(query)
            
            # Track agent activity
            tool_calls = []
            iterations = 0
            
            # Create settings with auto function calling
            execution_settings = AzureChatPromptExecutionSettings(
                temperature=temperature,
                max_tokens=max_tokens,
                function_choice_behavior=FunctionChoiceBehavior.Auto(
                    auto_invoke=True,
                    filters={"excluded_plugins": []}  # Allow all plugins
                )
            )
            
            logger.info(f"[Agent] Starting execution for query: {query[:100]}...")
            
            # Iteratively call the agent until complete or max iterations
            for iteration in range(max_iterations):
                iterations += 1
                logger.info(f"[Agent] Iteration {iterations}/{max_iterations}")
                
                try:
                    # Get response with auto function calling
                    response = await self._chat_service.get_chat_message_contents(
                        chat_history=chat_history,
                        settings=execution_settings,
                        kernel=kernel,
                    )
                    
                    if not response or len(response) == 0:
                        logger.warning("[Agent] Empty response received")
                        break
                    
                    # Get the response message
                    message = response[0]
                    
                    # Add assistant response to history
                    chat_history.add_assistant_message(str(message.content))
                    
                    # Check for function calls in metadata
                    if hasattr(message, 'function_call') and message.function_call:
                        # Function was called
                        func_call = message.function_call
                        tool_calls.append({
                            "tool_name": func_call.name,
                            "arguments": func_call.arguments if hasattr(func_call, 'arguments') else {},
                            "iteration": iterations
                        })
                        logger.info(f"[Agent] Tool called: {func_call.name}")
                        
                    # Check if we have a final answer (no more function calls)
                    elif message.content and not (hasattr(message, 'function_call') and message.function_call):
                        # Agent has provided final answer
                        logger.info("[Agent] Final answer received")
                        return {
                            "answer": str(message.content),
                            "tool_calls": tool_calls,
                            "iterations": iterations,
                            "agent_plan": f"Completed in {iterations} iteration(s) with {len(tool_calls)} tool call(s)"
                        }
                    
                except Exception as iter_error:
                    logger.error(f"[Agent] Error in iteration {iterations}: {iter_error}")
                    # Continue to next iteration unless it's the last one
                    if iteration == max_iterations - 1:
                        raise
                    continue
            
            # Max iterations reached - extract best answer from history
            logger.warning(f"[Agent] Max iterations ({max_iterations}) reached")
            
            # Get last assistant message as answer
            last_assistant_msg = ""
            for msg in reversed(chat_history.messages):
                if msg.role == "assistant":
                    last_assistant_msg = str(msg.content)
                    break
            
            return {
                "answer": last_assistant_msg or "I reached my thinking limit. Please try asking a more specific question.",
                "tool_calls": tool_calls,
                "iterations": iterations,
                "agent_plan": f"Reached max iterations ({max_iterations}) with {len(tool_calls)} tool call(s)"
            }
            
        except Exception as e:
            logger.error(f"[Agent] Error in agent execution: {e}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "tool_calls": [],
                "iterations": 0,
                "agent_plan": "Error during execution"
            }

# Global instance
llm_service = LLMService()