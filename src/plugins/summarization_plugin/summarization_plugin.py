"""Summarization plugin for generating document summaries."""

from semantic_kernel.functions import kernel_function
from loguru import logger
from typing import Annotated
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.services.llm_service import llm_service
from src.config.prompts import POLICY_SUMMARY_TEMPLATE


class SummarizationPlugin:
    """Plugin for generating summaries of HR documents and policies."""

    def __init__(self):
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure LLM service is initialized."""
        if not self._initialized:
            await llm_service.initialize()
            self._initialized = True

    @kernel_function(
        name="summarize_document",
        description="Generate a summary of a document or policy"
    )
    async def summarize_document(
        self,
        document: Annotated[str, "The document text to summarize"],
        summary_type: Annotated[str, "Type of summary: 'brief', 'comprehensive', or 'executive'"] = "comprehensive",
    ) -> str:
        """
        Generate a summary of a document.

        Args:
            document: Document text to summarize
            summary_type: Type of summary to generate

        Returns:
            Generated summary
        """
        await self._ensure_initialized()
        
        logger.info(f"Generating {summary_type} summary for document")
        
        try:
            # Prepare prompt based on summary type
            if summary_type == "brief":
                prompt = f"Provide a brief 2-3 sentence summary of this HR document:\n\n{document}"
            elif summary_type == "executive":
                prompt = f"Provide an executive summary highlighting key decisions, policies, and action items from this document:\n\n{document}"
            else:  # comprehensive
                prompt = f"Provide a comprehensive summary covering all major points, policies, and requirements from this document:\n\n{document}"
            
            # Generate summary
            summary = await llm_service.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1000
            )
            
            logger.info("Summary generated successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Error generating summary: {str(e)}"

    @kernel_function(
        name="summarize_for_audience",
        description="Generate a summary tailored for a specific audience"
    )
    async def summarize_for_audience(
        self,
        document: Annotated[str, "The document text to summarize"],
        audience: Annotated[str, "Target audience: 'employee', 'manager', 'executive', or 'new_hire'"] = "employee",
    ) -> str:
        """
        Generate an audience-specific summary.

        Args:
            document: Document text
            audience: Target audience

        Returns:
            Tailored summary
        """
        await self._ensure_initialized()
        
        logger.info(f"Generating summary for audience: {audience}")
        
        try:
            # Use template with audience
            prompt = POLICY_SUMMARY_TEMPLATE.format(
                document=document,
                audience=audience,
                summary_type="clear and actionable"
            )
            
            summary = await llm_service.generate_response(
                prompt=prompt,
                temperature=0.4,
                max_tokens=1200
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating audience-specific summary: {e}")
            return f"Error generating summary: {str(e)}"

    @kernel_function(
        name="extract_key_points",
        description="Extract key points and action items from a document"
    )
    async def extract_key_points(
        self,
        document: Annotated[str, "The document text to analyze"]
    ) -> str:
        """
        Extract key points and action items.

        Args:
            document: Document text

        Returns:
            List of key points
        """
        await self._ensure_initialized()
        
        logger.info("Extracting key points from document")
        
        try:
            prompt = f"""Extract the key points, policies, and action items from this HR document.
Format as a bulleted list with categories:

Key Policies:
- [policy points]

Requirements:
- [requirement points]

Action Items:
- [action items]

Document:
{document}"""
            
            key_points = await llm_service.generate_response(
                prompt=prompt,
                temperature=0.2,
                max_tokens=800
            )
            
            return key_points
            
        except Exception as e:
            logger.error(f"Error extracting key points: {e}")
            return f"Error extracting key points: {str(e)}"
