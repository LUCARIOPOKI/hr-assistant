"""Metadata extraction utilities."""

import re
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger


class MetadataExtractor:
    """Extract metadata from document text."""

    @staticmethod
    def extract_title(text: str) -> Optional[str]:
        """Extract document title from text."""
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line) < 200:  # Reasonable title length
                # Remove common prefixes
                line = re.sub(r'^(title:|subject:)', '', line, flags=re.IGNORECASE).strip()
                if line:
                    return line
        return None

    @staticmethod
    def extract_dates(text: str) -> Dict[str, Optional[str]]:
        """Extract dates from document text."""
        dates = {
            'effective_date': None,
            'revision_date': None,
            'expiry_date': None,
        }

        # Common date patterns
        patterns = [
            (r'effective\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'effective_date'),
            (r'revision\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'revision_date'),
            (r'expiry\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'expiry_date'),
            (r'last\s+updated[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'revision_date'),
        ]

        for pattern, key in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dates[key] = match.group(1)

        return dates

    @staticmethod
    def extract_policy_number(text: str) -> Optional[str]:
        """Extract policy/document number."""
        patterns = [
            r'policy\s+(?:number|#|no\.?)[:\s]+([A-Z0-9-]+)',
            r'document\s+(?:number|#|no\.?)[:\s]+([A-Z0-9-]+)',
            r'ref\s*(?:erence)?[:\s]+([A-Z0-9-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def extract_department(text: str) -> Optional[str]:
        """Extract department/owner information."""
        patterns = [
            r'department[:\s]+([A-Za-z\s&-]+?)(?:\n|$)',
            r'owner[:\s]+([A-Za-z\s&-]+?)(?:\n|$)',
            r'responsible[:\s]+([A-Za-z\s&-]+?)(?:\n|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dept = match.group(1).strip()
                if len(dept) < 100:  # Sanity check
                    return dept
        return None

    @classmethod
    def extract_all(cls, text: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract all metadata from document text.

        Args:
            text: Document text
            filename: Optional filename for additional context

        Returns:
            Dict of extracted metadata
        """
        metadata = {
            'title': cls.extract_title(text) or (filename if filename else 'Untitled'),
            'policy_number': cls.extract_policy_number(text),
            'department': cls.extract_department(text),
            'extracted_at': datetime.utcnow().isoformat(),
        }

        # Add dates
        dates = cls.extract_dates(text)
        metadata.update(dates)

        # Extract document type hint from text
        text_lower = text.lower()[:500]  # Check first 500 chars
        if 'policy' in text_lower:
            metadata['document_type'] = 'policy'
        elif 'procedure' in text_lower:
            metadata['document_type'] = 'procedure'
        elif 'guideline' in text_lower:
            metadata['document_type'] = 'guideline'
        elif 'handbook' in text_lower or 'manual' in text_lower:
            metadata['document_type'] = 'handbook'
        else:
            metadata['document_type'] = 'document'

        logger.debug(f"Extracted metadata: {metadata}")
        return metadata
