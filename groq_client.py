"""
Groq API client module for Rubel AI Chat Application.

This module handles all interactions with the Groq LLM API including:
- Sending chat completion requests
- Managing conversation context
- Processing API responses
"""

from typing import List, Dict, Any, Optional
from config import groq_client

def get_groq_response(messages: List[Dict[str, Any]]) -> Optional[str]:
    """
    Get a response from the Groq LLM API.

    This function sends a conversation context to the Groq API and returns
    the AI-generated response. It uses the llama-3.3-70b-versatile model
    for generating responses.

    Args:
        messages (List[Dict[str, str]]): A list of message dictionaries containing
            the conversation history. Each dict should have 'role' and 'content' keys.

    Returns:
        str: The AI-generated response text

    Raises:
        Exception: If the API call fails or the client is not initialized

    Example:
        >>> messages = [
        ...     {"role": "system", "content": "You are a helpful assistant."},
        ...     {"role": "user", "content": "Hello!"}
        ... ]
        >>> response = get_groq_response(messages)
        >>> print(response)
    """
    if not groq_client:
        raise Exception("Groq client not initialized. Check GROQ_API_KEY.")

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    return response.choices[0].message.content