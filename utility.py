"""
Utility functions for Rubel AI Chat Application.

This module contains various utility functions used throughout the application,
including text processing and other helper functions.
"""

import re

def clean_response(text: str) -> str:
    """
    Remove parenthetical remarks from the response text.

    This function cleans up AI-generated responses by removing any text
    enclosed in parentheses, which are typically used for internal notes
    or meta-comments that shouldn't be displayed to users.

    Args:
        text (str): The raw response text from the AI

    Returns:
        str: The cleaned response text with parentheticals removed

    Example:
        >>> clean_response("Hello world (internal note) how are you?")
        'Hello world how are you?'
    """
    # Remove anything in parentheses, square brackets, or angle brackets
    # Examples removed: (internal note), [Pausing, eyes narrowing], <stage direction>
    cleaned = re.sub(r"\([^)]*\)", "", text)        # ( ... )
    cleaned = re.sub(r"\[[^\]]*\]", "", cleaned)   # [ ... ]
    cleaned = re.sub(r"<[^>]*>", "", cleaned)         # < ... >
    # Remove extra whitespace that might result from removals
    cleaned = ' '.join(cleaned.split())
    return cleaned