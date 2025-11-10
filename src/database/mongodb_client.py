"""MongoDB client for storing chunks and logs."""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime
from loguru import logger

try:
    from pymongo import MongoClient
    from pymongo.database import Database
    from pymongo.collection import Collection
    PYMONGO_AVAILABLE = True
except ImportError:
    if not TYPE_CHECKING:
        MongoClient = None  # type: ignore
        Database = None  # type: ignore
        Collection = None  # type: ignore
    PYMONGO_AVAILABLE = False

from ..config.settings import get_settings

settings = get_settings()


class MongoDBClient:
    """MongoDB client for storing document chunks and logs."""

    def __init__(self):
        self._client: Optional[Any] = None
        self._chunks_db: Optional[Any] = None
        self._logs_db: Optional[Any] = None
        self._chunks_collection: Optional[Any] = None
        self._logs_collection: Optional[Any] = None

    def connect(self):
        """Connect to MongoDB."""
        if not PYMONGO_AVAILABLE:
            logger.warning("pymongo not installed. Database features disabled.")
            return

        if not settings.mongo_db_connection_string:
            logger.warning("MongoDB connection string not configured")
            return

        try:
            self._client = MongoClient(settings.mongo_db_connection_string)
            
            # Test connection
            self._client.admin.command('ping')
            
            # Setup databases and collections
            self._chunks_db = self._client[settings.database_name]
            self._logs_db = self._client[settings.log_database_name]
            
            self._chunks_collection = self._chunks_db[settings.collection_name]
            self._logs_collection = self._logs_db[settings.log_collection_name]
            
            logger.info(f"Connected to MongoDB: {settings.database_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._client = None

    def insert_chunk(self, chunk_data: Dict[str, Any]) -> Optional[str]:
        """
        Insert a document chunk.

        Args:
            chunk_data: Chunk data to insert

        Returns:
            Inserted document ID or None
        """
        if self._chunks_collection is None:
            return None

        try:
            chunk_data['created_at'] = datetime.utcnow()
            result = self._chunks_collection.insert_one(chunk_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting chunk: {e}")
            return None

    def insert_chunks_batch(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Insert multiple chunks in batch.

        Args:
            chunks: List of chunk data

        Returns:
            Number of inserted documents
        """
        if self._chunks_collection is None:
            return 0

        try:
            for chunk in chunks:
                chunk['created_at'] = datetime.utcnow()
            
            result = self._chunks_collection.insert_many(chunks)
            return len(result.inserted_ids)
        except Exception as e:
            logger.error(f"Error inserting chunks batch: {e}")
            return 0

    def log_event(
        self,
        event_type: str,
        message: str,
        level: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log an event to the database.

        Args:
            event_type: Type of event (e.g., 'ingestion', 'query', 'error')
            message: Log message
            level: Log level (INFO, WARNING, ERROR, etc.)
            metadata: Additional metadata
        """
        if self._logs_collection is None:
            return

        try:
            log_entry = {
                'timestamp': datetime.utcnow(),
                'event_type': event_type,
                'level': level,
                'message': message,
                'metadata': metadata or {}
            }
            self._logs_collection.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Error logging event: {e}")

    def get_chunks_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document."""
        if self._chunks_collection is None:
            return []

        try:
            return list(self._chunks_collection.find({'document_id': document_id}))
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []

    def delete_chunks_by_document(self, document_id: str) -> int:
        """Delete all chunks for a document."""
        if self._chunks_collection is None:
            return 0

        try:
            result = self._chunks_collection.delete_many({'document_id': document_id})
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return 0

    def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")


# Global instance
mongodb_client = MongoDBClient()
