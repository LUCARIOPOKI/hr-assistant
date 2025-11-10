"""Text normalization utilities."""

import re
from typing import str


class TextNormalizer:
    """Normalize text for consistency."""

    @staticmethod
    def normalize_case(text: str, style: str = "preserve") -> str:
        """
        Normalize text case.

        Args:
            text: Input text
            style: 'lower', 'upper', 'title', or 'preserve'

        Returns:
            Normalized text
        """
        if style == "lower":
            return text.lower()
        elif style == "upper":
            return text.upper()
        elif style == "title":
            return text.title()
        return text

    @staticmethod
    def normalize_numbers(text: str) -> str:
        """Convert written numbers to digits."""
        number_words = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eleven': '11', 'twelve': '12',
        }
        
        for word, digit in number_words.items():
            # Replace whole words only
            text = re.sub(r'\b' + word + r'\b', digit, text, flags=re.IGNORECASE)
        
        return text

    @staticmethod
    def normalize_dates(text: str) -> str:
        """Normalize date formats to YYYY-MM-DD."""
        # DD/MM/YYYY or MM/DD/YYYY -> keep as is (ambiguous)
        # DD-MM-YYYY -> YYYY-MM-DD
        text = re.sub(
            r'(\d{2})-(\d{2})-(\d{4})',
            r'\3-\2-\1',
            text
        )
        return text

    @staticmethod
    def expand_contractions(text: str) -> str:
        """Expand common English contractions."""
        contractions = {
            "don't": "do not",
            "doesn't": "does not",
            "didn't": "did not",
            "can't": "cannot",
            "won't": "will not",
            "shouldn't": "should not",
            "wouldn't": "would not",
            "couldn't": "could not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "I'm": "I am",
            "you're": "you are",
            "he's": "he is",
            "she's": "she is",
            "it's": "it is",
            "we're": "we are",
            "they're": "they are",
            "I've": "I have",
            "you've": "you have",
            "we've": "we have",
            "they've": "they have",
            "I'll": "I will",
            "you'll": "you will",
            "he'll": "he will",
            "she'll": "she will",
            "we'll": "we will",
            "they'll": "they will",
        }
        
        for contraction, expansion in contractions.items():
            text = re.sub(r'\b' + re.escape(contraction) + r'\b', expansion, text, flags=re.IGNORECASE)
        
        return text

    @classmethod
    def normalize(
        cls,
        text: str,
        case_style: str = "preserve",
        expand_contractions: bool = False,
        normalize_numbers: bool = False,
    ) -> str:
        """
        Apply all normalization steps.

        Args:
            text: Input text
            case_style: Case normalization style
            expand_contractions: Whether to expand contractions
            normalize_numbers: Whether to normalize number words

        Returns:
            Normalized text
        """
        if expand_contractions:
            text = cls.expand_contractions(text)
        if normalize_numbers:
            text = cls.normalize_numbers(text)
        
        text = cls.normalize_case(text, case_style)
        text = cls.normalize_dates(text)
        
        return text
