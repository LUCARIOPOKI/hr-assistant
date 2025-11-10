"""Embedding service for generating text embeddings using Azure OpenAI."""

from typing import List
from loguru import logger
from ..config.settings import get_settings
from ..core.semantic_kernel_setup import sk_manager

settings = get_settings()


class EmbeddingService:
    """Service for generating embeddings using Azure OpenAI."""

    def __init__(self):
        self._embedding_service = None

    async def initialize(self):
        """Initialize the embedding service."""
        kernel = sk_manager.get_kernel()
        self._embedding_service = sk_manager.embedding_service
        logger.info("Embedding service initialized")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not self._embedding_service:
            await self.initialize()

        try:
            # Semantic Kernel v1.x embedding generation
            result = await self._embedding_service.generate_embeddings([text])
            embedding = result[0]  # Get first embedding
            return embedding if isinstance(embedding, list) else embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not self._embedding_service:
            await self.initialize()

        try:
            results = await self._embedding_service.generate_embeddings(texts)
            return [emb if isinstance(emb, list) else emb.tolist() for emb in results]
        except Exception as e:
            logger.error(f"Error generating embeddings batch: {e}")
            raise


# Global instance
embedding_service = EmbeddingService()
