"""Token counting using tiktoken (OpenAI cl100k_base encoding).

Based on analyze_markdown_notes.py from muse-v1.
"""
from typing import Optional


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken (cl100k_base).

    Falls back to word count * 1.3 if tiktoken unavailable.

    Args:
        text: Text to count tokens for

    Returns:
        Token count
    """
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except (ImportError, Exception):
        # Fallback: word count * 1.3 (82.6% accuracy)
        return int(len(text.split()) * 1.3)


def format_size(bytes_size: int) -> str:
    """Convert bytes to human-readable format.

    Args:
        bytes_size: File size in bytes

    Returns:
        Formatted string like "1.5 KB" or "23.4 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"
