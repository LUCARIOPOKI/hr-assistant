"""Retrieval plugin for RAG-based document retrieval."""

from semantic_kernel.functions import kernel_function
from loguru import logger
from typing import Annotated, List, Dict, Any
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.services.vector_store_service import vector_store_service
from src.config.prompts import RAG_RESPONSE_TEMPLATE


class RetrievalPlugin:
    """Plugin for retrieving relevant documents from vector store."""

    def __init__(self):
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure vector store is initialized."""
        if not self._initialized:
            await vector_store_service.initialize()
            self._initialized = True

    @kernel_function(
        name="retrieve_documents",
        description="Retrieve relevant documents from the knowledge base based on a query"
    )
    async def retrieve_documents(
        self,
        query: Annotated[str, "The search query to find relevant documents"],
        top_k: Annotated[int, "Number of documents to retrieve"] = 5,
    ) -> str:
        """
        Retrieve relevant documents from vector store.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            Formatted string of retrieved documents
        """
        await self._ensure_initialized()
        
        logger.info(f"Retrieving documents for query: {query} (top_k={top_k})")
        
        try:
            # Search vector store
            results = await vector_store_service.search(
                query=query,
                top_k=top_k,
                namespace="hr_policies"
            )
            
            if not results:
                return "No relevant documents found in the knowledge base."
            
            # Format results
            formatted_docs = []
            for i, result in enumerate(results, 1):
                score = result.get('score', 0)
                text = result.get('text', '')
                metadata = result.get('metadata', {})
                
                doc_info = f"[Document {i}] (Relevance: {score:.2f})\n"
                if metadata.get('filename'):
                    doc_info += f"Source: {metadata['filename']}\n"
                if metadata.get('title'):
                    doc_info += f"Title: {metadata['title']}\n"
                doc_info += f"Content:\n{text}\n"
                
                formatted_docs.append(doc_info)
            
            result_text = "\n---\n".join(formatted_docs)
            logger.info(f"Retrieved {len(results)} documents")
            
            return result_text
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return f"Error retrieving documents: {str(e)}"

    @kernel_function(
        name="retrieve_and_answer",
        description="Retrieve relevant documents and generate an answer based on them"
    )
    async def retrieve_and_answer(
        self,
        question: Annotated[str, "The question to answer using retrieved documents"],
        top_k: Annotated[int, "Number of documents to retrieve"] = 3,
    ) -> str:
        """
        Retrieve documents and provide context for answering a question.

        Args:
            question: The question to answer
            top_k: Number of documents to retrieve

        Returns:
            Context string with retrieved documents formatted for LLM
        """
        await self._ensure_initialized()
        
        logger.info(f"RAG query: {question}")
        
        try:
            # Retrieve documents
            results = await vector_store_service.search(
                query=question,
                top_k=top_k,
                namespace="hr_policies"
            )
            
            if not results:
                context = "No relevant policy documents found."
            else:
                # Format context for LLM
                context_parts = []
                for result in results:
                    text = result.get('text', '')
                    metadata = result.get('metadata', {})
                    source = metadata.get('filename', 'Unknown source')
                    context_parts.append(f"[From {source}]\n{text}")
                
                context = "\n\n".join(context_parts)
            
            # Format using template
            formatted_prompt = RAG_RESPONSE_TEMPLATE.format(
                context=context,
                question=question
            )
            
            return formatted_prompt
            
        except Exception as e:
            logger.error(f"Error in retrieve_and_answer: {e}")
            return f"I encountered an error while searching the knowledge base: {str(e)}"
