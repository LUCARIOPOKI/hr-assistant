"""Retrieval plugin for RAG-based document retrieval with agentic capabilities."""

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
    """Plugin for retrieving relevant documents from vector store with agentic tools."""

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

    @kernel_function(
        name="search_policy_documents",
        description="Search HR policy documents by topic or keyword. Use this to find specific policies."
    )
    async def search_policy_documents(
        self,
        query: Annotated[str, "The policy topic or keyword to search for (e.g., 'vacation', 'sick leave', 'remote work')"],
        top_k: Annotated[int, "Number of policy documents to retrieve"] = 3,
    ) -> str:
        """
        Search for specific policy documents.
        
        This is a tool for the agent to find HR policies on specific topics.
        """
        await self._ensure_initialized()
        logger.info(f"[Agent Tool] Searching policies for: {query}")
        
        try:
            results = await vector_store_service.search(
                query=query,
                top_k=top_k,
                namespace="hr_policies"
            )
            
            if not results:
                return f"No policies found for '{query}'."
            
            # Format for agent consumption
            policy_texts = []
            for i, result in enumerate(results, 1):
                text = result.get('text', '')
                score = result.get('score', 0)
                source = result.get('metadata', {}).get('filename', 'Unknown')
                policy_texts.append(f"Policy {i} (relevance: {score:.2f}, source: {source}):\n{text}")
            
            return "\n\n".join(policy_texts)
            
        except Exception as e:
            logger.error(f"Error searching policies: {e}")
            return f"Error searching policies: {str(e)}"

    @kernel_function(
        name="get_document_details",
        description="Get detailed information about a specific document by searching for its exact title or identifier"
    )
    async def get_document_details(
        self,
        document_identifier: Annotated[str, "The document title, filename, or identifier to retrieve"],
    ) -> str:
        """
        Get full details of a specific document.
        
        Use this when you need complete information from a specific document.
        """
        await self._ensure_initialized()
        logger.info(f"[Agent Tool] Getting document details: {document_identifier}")
        
        try:
            results = await vector_store_service.search(
                query=document_identifier,
                top_k=5,
                namespace="hr_policies"
            )
            
            if not results:
                return f"Document '{document_identifier}' not found."
            
            # Combine chunks from same document
            doc_chunks = {}
            for result in results:
                filename = result.get('metadata', {}).get('filename', 'Unknown')
                text = result.get('text', '')
                
                if filename not in doc_chunks:
                    doc_chunks[filename] = []
                doc_chunks[filename].append(text)
            
            # Format document details
            details = []
            for filename, chunks in doc_chunks.items():
                combined = "\n\n".join(chunks)
                details.append(f"Document: {filename}\n\nContent:\n{combined}")
            
            return "\n\n---\n\n".join(details)
            
        except Exception as e:
            logger.error(f"Error getting document details: {e}")
            return f"Error retrieving document: {str(e)}"

    @kernel_function(
        name="search_related_topics",
        description="Find policy documents related to multiple topics. Use when you need to understand connections between different policies."
    )
    async def search_related_topics(
        self,
        topic1: Annotated[str, "First topic to search"],
        topic2: Annotated[str, "Second topic to search"],
    ) -> str:
        """
        Search for documents that relate to multiple topics.
        
        Use this to find connections between different policy areas.
        """
        await self._ensure_initialized()
        logger.info(f"[Agent Tool] Searching related topics: {topic1} and {topic2}")
        
        try:
            # Search with combined query
            combined_query = f"{topic1} {topic2} related policy"
            results = await vector_store_service.search(
                query=combined_query,
                top_k=5,
                namespace="hr_policies"
            )
            
            if not results:
                return f"No policies found relating '{topic1}' and '{topic2}'."
            
            # Format results highlighting connections
            related_policies = []
            for i, result in enumerate(results, 1):
                text = result.get('text', '')
                score = result.get('score', 0)
                source = result.get('metadata', {}).get('filename', 'Unknown')
                
                # Check if both topics are mentioned
                mentions_both = (topic1.lower() in text.lower() and topic2.lower() in text.lower())
                relevance = "BOTH TOPICS" if mentions_both else "RELATED"
                
                related_policies.append(
                    f"Policy {i} ({relevance}, relevance: {score:.2f}):\n"
                    f"Source: {source}\n"
                    f"Content: {text}"
                )
            
            return "\n\n".join(related_policies)
            
        except Exception as e:
            logger.error(f"Error searching related topics: {e}")
            return f"Error finding related policies: {str(e)}"

    @kernel_function(
        name="list_available_policies",
        description="List all available policy categories and documents in the knowledge base"
    )
    async def list_available_policies(self) -> str:
        """
        List what policy documents are available.
        
        Use this when you need to know what information is in the knowledge base.
        """
        await self._ensure_initialized()
        logger.info("[Agent Tool] Listing available policies")
        
        try:
            # Get a broad sample of documents
            results = await vector_store_service.search(
                query="HR policy employee handbook benefits procedures",
                top_k=10,
                namespace="hr_policies"
            )
            
            if not results:
                return "No policy documents found in the knowledge base."
            
            # Extract unique document names and topics
            documents = set()
            for result in results:
                filename = result.get('metadata', {}).get('filename', '')
                title = result.get('metadata', {}).get('title', '')
                if filename:
                    documents.add(filename)
                if title:
                    documents.add(title)
            
            doc_list = "\n".join([f"- {doc}" for doc in sorted(documents)])
            
            return f"Available policy documents:\n{doc_list}\n\nYou can search these documents for specific information."
            
        except Exception as e:
            logger.error(f"Error listing policies: {e}")
            return f"Error listing policies: {str(e)}"
