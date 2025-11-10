"""Text cleaning utilities."""

import re


class TextCleaner:
    """Clean and normalize document text."""

    @staticmethod
    def remove_extra_whitespace(text: str) -> str:
        """Remove extra whitespace and normalize line breaks."""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\n+', '\n\n', text)
        # Remove trailing/leading whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines)

    @staticmethod
    def remove_special_characters(text: str, keep_punctuation: bool = True) -> str:
        """Remove special characters while preserving readable text."""
        if keep_punctuation:
            # Keep alphanumeric, spaces, and basic punctuation
            text = re.sub(r'[^\w\s.,!?;:()\-\'\"]+', ' ', text)
        else:
            # Keep only alphanumeric and spaces
            text = re.sub(r'[^\w\s]+', ' ', text)
        return text

    @staticmethod
    def remove_urls(text: str) -> str:
        """Remove URLs from text."""
        return re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

    @staticmethod
    def remove_emails(text: str) -> str:
        """Remove email addresses from text."""
        return re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)

    @staticmethod
    def fix_encoding_issues(text: str) -> str:
        """Fix common encoding issues."""
        # Replace common encoding artifacts
        replacements = {
            'â€™': "'",
            'â€œ': '"',
            'â€': '"',
            'â€"': '—',
            'â€"': '–',
            'Ã©': 'é',
            'Ã¨': 'è',
            'Ã ': 'à',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    @classmethod
    def clean(
        cls,
        text: str,
        remove_urls: bool = True,
        remove_emails: bool = False,
        fix_encoding: bool = True,
    ) -> str:
        """
        Clean text with all available methods.

        Args:
            text: Text to clean
            remove_urls: Whether to remove URLs
            remove_emails: Whether to remove email addresses
            fix_encoding: Whether to fix encoding issues

        Returns:
            Cleaned text
        """
        if fix_encoding:
            text = cls.fix_encoding_issues(text)
        if remove_urls:
            text = cls.remove_urls(text)
        if remove_emails:
            text = cls.remove_emails(text)
        
        text = cls.remove_extra_whitespace(text)
        return text.strip()
