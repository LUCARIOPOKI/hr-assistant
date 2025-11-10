"""Document loader for various file formats."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None


class DocumentLoader:
    """Load documents from various file formats."""

    @staticmethod
    def load_pdf(file_path: str) -> str:
        """Load text from a PDF file."""
        if PyPDF2 is None:
            raise ImportError("PyPDF2 not installed. Install with: pip install PyPDF2")

        try:
            text = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            
            full_text = "\n\n".join(text)
            logger.info(f"Loaded PDF: {file_path} ({len(text)} pages)")
            return full_text
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            raise

    @staticmethod
    def load_docx(file_path: str) -> str:
        """Load text from a DOCX file."""
        if Document is None:
            raise ImportError("python-docx not installed. Install with: pip install python-docx")

        try:
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            
            full_text = "\n\n".join(text)
            logger.info(f"Loaded DOCX: {file_path} ({len(text)} paragraphs)")
            return full_text
        except Exception as e:
            logger.error(f"Error loading DOCX {file_path}: {e}")
            raise

    @staticmethod
    def load_txt(file_path: str) -> str:
        """Load text from a TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            logger.info(f"Loaded TXT: {file_path}")
            return text
        except Exception as e:
            logger.error(f"Error loading TXT {file_path}: {e}")
            raise

    @staticmethod
    def load_markdown(file_path: str) -> str:
        """Load text from a Markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            logger.info(f"Loaded Markdown: {file_path}")
            return text
        except Exception as e:
            logger.error(f"Error loading Markdown {file_path}: {e}")
            raise

    @classmethod
    def load_document(cls, file_path: str) -> Dict[str, Any]:
        """
        Load a document and return its content with metadata.

        Args:
            file_path: Path to the document

        Returns:
            Dict with 'content', 'metadata', and 'file_path'
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = file_path.suffix.lower()
        
        # Load based on file type
        if extension == '.pdf':
            content = cls.load_pdf(str(file_path))
        elif extension in ['.docx', '.doc']:
            content = cls.load_docx(str(file_path))
        elif extension in ['.txt', '.text']:
            content = cls.load_txt(str(file_path))
        elif extension in ['.md', '.markdown']:
            content = cls.load_markdown(str(file_path))
        else:
            raise ValueError(f"Unsupported file format: {extension}")

        # Extract metadata
        metadata = {
            'filename': file_path.name,
            'file_type': extension[1:],  # Remove the dot
            'file_size': file_path.stat().st_size,
            'file_path': str(file_path.absolute()),
        }

        return {
            'content': content,
            'metadata': metadata,
            'file_path': str(file_path),
        }

    @classmethod
    def load_directory(cls, directory_path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Load all documents from a directory.

        Args:
            directory_path: Path to the directory
            recursive: Whether to search subdirectories

        Returns:
            List of document dicts
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        supported_extensions = {'.pdf', '.docx', '.doc', '.txt', '.text', '.md', '.markdown'}
        documents = []

        pattern = '**/*' if recursive else '*'
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    doc = cls.load_document(str(file_path))
                    documents.append(doc)
                except Exception as e:
                    logger.warning(f"Skipping {file_path}: {e}")

        logger.info(f"Loaded {len(documents)} documents from {directory}")
        return documents
