"""
Pattern signature generation for log messages.

This module generates semantic signatures from log messages by normalizing
variable content (IDs, timestamps, numbers) so similar messages produce
the same signature.
"""

import hashlib
import re


def compute_signature(message: str) -> str:
    """
    Generate a semantic signature for a log message.

    Similar messages (e.g., differing only by IDs, numbers, timestamps)
    will produce the same signature.

    Args:
        message: The raw log message string

    Returns:
        Hexadecimal string representing the log signature

    Examples:
        >>> compute_signature("User 123 logged in")
        'a1b2c3d4...'
        >>> compute_signature("User 456 logged in")
        'a1b2c3d4...'  # Same signature!
    """
    # Normalize the message
    normalized = message

    # Replace numbers with placeholder
    normalized = re.sub(r"\b\d+\b", "N", normalized)

    # Replace UUIDs
    normalized = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "UUID", normalized, flags=re.IGNORECASE)

    # Replace hex IDs
    normalized = re.sub(r"\b[a-f0-9]{32,}\b", "HEXID", normalized, flags=re.IGNORECASE)

    # Replace ISO timestamps
    normalized = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", "TIMESTAMP", normalized)

    # Replace dates
    normalized = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "DATE", normalized)

    # Replace times
    normalized = re.sub(r"\b\d{2}:\d{2}:\d{2}\b", "TIME", normalized)

    # Replace IP addresses
    normalized = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "IP", normalized)

    # Replace email addresses
    normalized = re.sub(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", "EMAIL", normalized)

    # Replace URLs
    normalized = re.sub(r"https?://[^\s]+", "URL", normalized)

    # Collapse multiple spaces
    normalized = re.sub(r"\s+", " ", normalized)

    # Trim
    normalized = normalized.strip()

    # Generate MD5 hash
    return hashlib.md5(normalized.encode()).hexdigest()

