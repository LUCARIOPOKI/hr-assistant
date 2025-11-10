from loguru import logger
from typing import Optional
from ..config.settings import get_settings

try:
    from pinecone import Pinecone, ServerlessSpec
except ImportError:  # fallback if package not yet installed or version mismatch
    Pinecone = None  # type: ignore
    ServerlessSpec = None  # type: ignore

settings = get_settings()


class PineconeClient:
    """Wrapper for Pinecone index management."""

    def __init__(self):
        self._pc: Optional[object] = None
        self._index_name = settings.pinecone_index_name

    def _ensure_client(self):
        if self._pc is None:
            if not settings.pinecone_api_key:
                logger.warning("Pinecone API key missing; retrieval disabled")
                return None
            try:
                self._pc = Pinecone(api_key=settings.pinecone_api_key)
            except Exception as e:
                logger.error(f"Failed to create Pinecone client: {e}")
                self._pc = None
        return self._pc

    def initialize_index(self):
        pc = self._ensure_client()
        if pc is None:
            return
        try:
            existing = [idx.name for idx in pc.list_indexes()]  # type: ignore[attr-defined]
            if self._index_name not in existing:
                logger.info(f"Creating Pinecone index '{self._index_name}'")
                spec = ServerlessSpec(cloud="aws", region="us-east-1") if ServerlessSpec else None
                pc.create_index(
                    name=self._index_name,
                    dimension=settings.pinecone_dimension,
                    metric=settings.pinecone_metric,
                    spec=spec,
                )
            else:
                logger.info(f"Pinecone index '{self._index_name}' already exists")
        except Exception as e:
            logger.error(f"Error ensuring Pinecone index: {e}")

    def get_index(self):
        pc = self._ensure_client()
        if pc is None:
            return None
        try:
            return pc.Index(self._index_name)  # type: ignore[attr-defined]
        except Exception as e:
            logger.error(f"Failed to get Pinecone index: {e}")
            return None


pinecone_client = PineconeClient()
