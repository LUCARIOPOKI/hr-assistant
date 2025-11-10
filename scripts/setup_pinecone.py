"""
Script to set up Pinecone index for the application.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger
from src.database.pinecone_client import pinecone_client
from src.config.settings import get_settings

settings = get_settings()


def setup_pinecone():
    """Set up Pinecone index."""
    try:
        logger.info("Setting up Pinecone index...")
        logger.info(f"Index name: {settings.pinecone_index_name}")
        logger.info(f"Dimension: {settings.embedding_dimension}")
        logger.info(f"Environment: {settings.pinecone_environment}")
        
        # Initialize index
        pinecone_client.initialize_index()
        
        # Get stats
        stats = pinecone_client.get_index_stats()
        logger.info(f"Index stats: {stats}")
        
        logger.info("✓ Pinecone setup complete!")
        
    except Exception as e:
        logger.error(f"✗ Error setting up Pinecone: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_pinecone()