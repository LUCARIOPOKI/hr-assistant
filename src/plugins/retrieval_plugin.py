"""Retrieval Plugin - semantic search over company documents and knowledge base."""

from semantic_kernel.functions import kernel_function
from loguru import logger
from typing import Annotated, List, Dict, Any
from ..database.pinecone_client import pinecone_client
from ..core.semantic_kernel_setup import sk_manager


class RetrievalPlugin:
    """Plugin for semantic retrieval from vector store."""

    @kernel_function(
        name="search_documents",
        description="Search company documents and knowledge base using semantic similarity"
    )
    async def search_documents(
        self,
        query: Annotated[str, "The search query"],
        top_k: Annotated[int, "Number of results to return"] = 5
    ) -> str:
        """Perform semantic search over indexed documents."""
        logger.info(f"Document search: {query} (top_k={top_k})")
        
        try:
            # Get embedding for the query
            embedding_service = sk_manager.embedding_service
            if embedding_service is None:
                logger.warning("Embedding service not available")
                return "Document search is currently unavailable. Please contact IT support."
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_embeddings([query])
            if not query_embedding or len(query_embedding) == 0:
                return "Failed to generate query embedding."
            
            # Query Pinecone
            index = pinecone_client.get_index()
            if index is None:
                logger.warning("Pinecone index not available")
                return "Document search is currently unavailable. Knowledge base is being updated."
            
            # Perform vector search
            results = index.query(
                vector=query_embedding[0],
                top_k=top_k,
                include_metadata=True
            )
            
            if not results or not results.get('matches'):
                return "No relevant documents found for your query."
            
            # Format results
            formatted_results = []
            for match in results['matches']:
                metadata = match.get('metadata', {})
                formatted_results.append(
                    f"- {metadata.get('title', 'Untitled')} (relevance: {match['score']:.2f})\n"
                    f"  {metadata.get('text', 'No preview available')[:200]}..."
                )
            
            return "Relevant documents:\n\n" + "\n\n".join(formatted_results)
        
        except Exception as e:
            logger.error(f"Error in document search: {e}")
            return f"Search error: {str(e)}"

    @kernel_function(
        name="retrieve_context",
        description="Retrieve contextual information for answering questions"
    )
    async def retrieve_context(
        self,
        question: Annotated[str, "The question to find context for"],
        top_k: Annotated[int, "Number of context chunks"] = 3
    ) -> str:
        """Retrieve relevant context chunks for RAG."""
        logger.info(f"Retrieving context for: {question}")
        
        # Reuse search_documents for now
        return await self.search_documents(query=question, top_k=top_k)


class SummarizationPlugin:
    """Plugin for document and content summarization."""

    @kernel_function(
        name="summarize_document",
        description="Generate a summary of a document or text"
    )
    async def summarize_document(
        self,
        content: Annotated[str, "The content to summarize"],
        summary_type: Annotated[str, "Type: 'brief', 'detailed', or 'executive'"] = "brief"
    ) -> str:
        """Summarize document content."""
        logger.info(f"Summarization requested: {summary_type}")
        
        try:
            kernel = sk_manager.get_kernel()
            chat_service = sk_manager.chat_service
            
            if chat_service is None:
                return "Summarization service unavailable."
            
            # Create summarization prompt based on type
            if summary_type == "executive":
                prompt = f"""Create an executive summary (2-3 sentences) of the following content, focusing on key decisions and business impact:

{content[:4000]}"""
            elif summary_type == "detailed":
                prompt = f"""Provide a detailed summary of the following content, including main points, supporting details, and conclusions:

{content[:4000]}"""
            else:  # brief
                prompt = f"""Provide a brief summary (3-5 bullet points) of the following content:

{content[:4000]}"""
            
            # Generate summary
            result = await chat_service.complete_async(prompt)
            return str(result)
        
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return f"Failed to generate summary: {str(e)}"

    @kernel_function(
        name="extract_key_points",
        description="Extract key points and action items from text"
    )
    async def extract_key_points(
        self,
        content: Annotated[str, "The content to analyze"]
    ) -> str:
        """Extract key points and action items."""
        logger.info("Extracting key points")
        
        try:
            chat_service = sk_manager.chat_service
            if chat_service is None:
                return "Key point extraction unavailable."
            
            prompt = f"""Extract key points and action items from the following text. Format as:

KEY POINTS:
- [point 1]
- [point 2]

ACTION ITEMS:
- [action 1]
- [action 2]

Text:
{content[:4000]}"""
            
            result = await chat_service.complete_async(prompt)
            return str(result)
        
        except Exception as e:
            logger.error(f"Key point extraction error: {e}")
            return f"Failed to extract key points: {str(e)}"
