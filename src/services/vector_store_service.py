"""Vector store service for managing embeddings in Pinecone."""

from typing import List, Dict, Any, Optional
from loguru import logger
from ..database.pinecone_client import pinecone_client
from ..services.embedding_service import embedding_service


class VectorStoreService:
    """Service for managing vector embeddings in Pinecone."""

    def __init__(self):
        self._index = None

    async def initialize(self):
        """Initialize the vector store."""
        self._index = pinecone_client.get_index()
        if self._index is None:
            logger.warning("Pinecone index not available")
        else:
            logger.info("Vector store service initialized")

    async def upsert_documents(
        self,
        documents: List[Dict[str, Any]],
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upsert document embeddings into Pinecone.

        Args:
            documents: List of dicts with 'id', 'text', and 'metadata'
            namespace: Optional namespace for organization

        Returns:
            Upsert result statistics
        """
        if self._index is None:
            await self.initialize()
            if self._index is None:
                raise RuntimeError("Vector store not available")

        try:
            # Generate embeddings for all documents
            texts = [doc["text"] for doc in documents]
            embeddings = await embedding_service.generate_embeddings_batch(texts)

            # Prepare vectors for upsert
            vectors = []
            for doc, embedding in zip(documents, embeddings):
                vectors.append({
                    "id": doc["id"],
                    "values": embedding,
                    "metadata": doc.get("metadata", {}),
                })

            # Upsert to Pinecone
            result = self._index.upsert(vectors=vectors, namespace=namespace or "")
            logger.info(f"Upserted {len(vectors)} vectors to Pinecone")
            return {"upserted_count": len(vectors), "result": result}

        except Exception as e:
            logger.error(f"Error upserting documents: {e}")
            raise

    async def search(
        self,
        query: str,
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query: Query text
            top_k: Number of results to return
            namespace: Optional namespace to search
            filter: Optional metadata filter

        Returns:
            List of matching documents with scores and metadata
        """
        if self._index is None:
            await self.initialize()
            if self._index is None:
                return []

        try:
            # Generate query embedding
            query_embedding = await embedding_service.generate_embedding(query)

            # Search Pinecone
            results = self._index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=namespace or "",
                filter=filter,
                include_metadata=True,
            )

            # Format results
            matches = []
            for match in results.get("matches", []):
                matches.append({
                    "id": match["id"],
                    "score": match["score"],
                    "metadata": match.get("metadata", {}),
                    "text": match.get("metadata", {}).get("text", ""),
                })

            logger.info(f"Found {len(matches)} matches for query")
            return matches

        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

    async def delete_by_ids(
        self,
        ids: List[str],
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete vectors by IDs."""
        if self._index is None:
            await self.initialize()
            if self._index is None:
                raise RuntimeError("Vector store not available")

        try:
            result = self._index.delete(ids=ids, namespace=namespace or "")
            logger.info(f"Deleted {len(ids)} vectors from Pinecone")
            return {"deleted_count": len(ids), "result": result}
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            raise

    async def delete_namespace(self, namespace: str) -> Dict[str, Any]:
        """Delete all vectors in a namespace."""
        if self._index is None:
            await self.initialize()
            if self._index is None:
                raise RuntimeError("Vector store not available")

        try:
            result = self._index.delete(delete_all=True, namespace=namespace)
            logger.info(f"Deleted all vectors in namespace '{namespace}'")
            return {"result": result}
        except Exception as e:
            logger.error(f"Error deleting namespace: {e}")
            raise


# Global instance
vector_store_service = VectorStoreService()
