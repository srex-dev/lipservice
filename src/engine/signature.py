import hashlib
import re


def compute_signature(message: str) -> str:
    """
    Generate a normalized signature for log message clustering.
    
    Similar messages (differing only in variables) get the same signature.
    This enables pattern detection and frequency analysis.
    
    Normalization rules:
    - Numbers replaced with 'N'
    - UUIDs replaced with 'UUID'
    - Dates replaced with 'DATE'
    - Timestamps replaced with 'TIME'
    - IPs replaced with 'IP'
    - Case insensitive
    
    Args:
        message: Raw log message
        
    Returns:
        MD5 hash of normalized message (32 chars)
        
    Examples:
        >>> compute_signature("User 123 logged in")
        'a1b2c3...'
        >>> compute_signature("User 456 logged in")
        'a1b2c3...'  # Same signature - same pattern
    """
    if not message:
        return hashlib.md5(b"empty").hexdigest()

    normalized = message.lower().strip()

    # Remove numbers
    normalized = re.sub(r"\d+", "N", normalized)

    # Remove UUIDs (various formats)
    normalized = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "UUID", normalized)
    normalized = re.sub(r"\b[0-9a-f]{32}\b", "UUID", normalized)

    # Remove ISO dates (YYYY-MM-DD)
    normalized = re.sub(r"\d{4}-\d{2}-\d{2}", "DATE", normalized)

    # Remove times (HH:MM:SS)
    normalized = re.sub(r"\d{2}:\d{2}:\d{2}", "TIME", normalized)

    # Remove IP addresses
    normalized = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "IP", normalized)

    # Remove file paths
    normalized = re.sub(r"[a-z]:\\[^\s]+", "PATH", normalized)
    normalized = re.sub(r"/[^\s]+/[^\s]+", "PATH", normalized)

    # Collapse multiple spaces
    normalized = re.sub(r"\s+", " ", normalized)

    return hashlib.md5(normalized.encode()).hexdigest()


def extract_error_type(message: str) -> str | None:
    """
    Extract error/exception type from log message.
    
    Args:
        message: Log message possibly containing error info
        
    Returns:
        Error type if found, else None
        
    Examples:
        >>> extract_error_type("ValueError: Invalid input")
        'ValueError'
        >>> extract_error_type("Exception in handler: TypeError")
        'TypeError'
    """
    error_patterns = [
        r"(\w+Error):",
        r"(\w+Exception):",
        r"Exception:\s+(\w+)",
        r"Error:\s+(\w+)",
    ]

    for pattern in error_patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1)

    return None


def compute_signature_with_context(message: str, severity: str | None = None, error_type: str | None = None) -> str:
    """
    Generate signature with additional context.
    
    Includes severity and error type in signature to avoid grouping
    different severities or error types together.
    
    Args:
        message: Log message
        severity: Log severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        error_type: Exception type if applicable
        
    Returns:
        MD5 hash of normalized message with context
    """
    base_sig = compute_signature(message)

    context_parts = [base_sig]
    if severity:
        context_parts.append(severity.upper())
    if error_type:
        context_parts.append(error_type)

    combined = ":".join(context_parts)
    return hashlib.md5(combined.encode()).hexdigest()

