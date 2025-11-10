"""Text splitting utilities for chunking documents."""

from typing import List, Dict, Any
import re
from loguru import logger


class TextSplitter:
    """Split text into chunks for embedding."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n",
    ):
        """
        Initialize text splitter.

        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            separator: Primary separator for splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        # First try to split by separator
        parts = text.split(self.separator)
        
        chunks = []
        current_chunk = ""

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # If adding this part would exceed chunk size
            if len(current_chunk) + len(part) + len(self.separator) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = overlap_text + part
                else:
                    # Part is larger than chunk size, split it
                    sub_chunks = self._split_large_part(part)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
            else:
                # Add part to current chunk
                if current_chunk:
                    current_chunk += self.separator + part
                else:
                    current_chunk = part

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks

    def _get_overlap(self, text: str) -> str:
        """Get overlap text from the end of a chunk."""
        if len(text) <= self.chunk_overlap:
            return text
        return text[-self.chunk_overlap:]

    def _split_large_part(self, text: str) -> List[str]:
        """Split a large text part that exceeds chunk size."""
        chunks = []
        sentences = re.split(r'[.!?]+\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    overlap = self._get_overlap(current_chunk)
                    current_chunk = overlap + sentence
                else:
                    # Sentence itself is too long, split by words
                    word_chunks = self._split_by_words(sentence)
                    chunks.extend(word_chunks)
                    current_chunk = ""
            else:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_words(self, text: str) -> List[str]:
        """Split text by words when sentences are too long."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > self.chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    # Keep last few words for overlap
                    overlap_words = int(self.chunk_overlap / 10)  # Rough estimate
                    current_chunk = current_chunk[-overlap_words:] + [word]
                    current_length = sum(len(w) + 1 for w in current_chunk)
                else:
                    # Single word is too long, just add it
                    chunks.append(word)
                    current_chunk = []
                    current_length = 0
            else:
                current_chunk.append(word)
                current_length += word_length

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def split_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Split multiple documents into chunks.

        Args:
            documents: List of document dicts with 'content' and 'metadata'

        Returns:
            List of chunk dicts with text and metadata
        """
        all_chunks = []
        
        for doc in documents:
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            chunks = self.split_text(content)
            
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = i
                chunk_metadata['total_chunks'] = len(chunks)
                
                all_chunks.append({
                    'text': chunk,
                    'metadata': chunk_metadata,
                })

        logger.info(f"Split {len(documents)} documents into {len(all_chunks)} total chunks")
        return all_chunks
