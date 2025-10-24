"""Tests for pattern signature generation."""

from lipservice.signature import compute_signature


def test_compute_signature_normalizes_numbers():
    """Test that numbers are normalized to 'N'."""
    sig1 = compute_signature("User 123 logged in")
    sig2 = compute_signature("User 456 logged in")
    assert sig1 == sig2


def test_compute_signature_normalizes_uuids():
    """Test that UUIDs are normalized."""
    sig1 = compute_signature("Request a1b2c3d4-1234-5678-9abc-123456789012 processed")
    sig2 = compute_signature("Request f9e8d7c6-5678-1234-5678-987654321098 processed")
    assert sig1 == sig2


def test_compute_signature_normalizes_timestamps():
    """Test that timestamps are normalized."""
    sig1 = compute_signature("Event at 2025-01-09T10:30:00")
    sig2 = compute_signature("Event at 2025-01-10T15:45:30")
    assert sig1 == sig2


def test_compute_signature_normalizes_dates():
    """Test that dates are normalized."""
    sig1 = compute_signature("Report for 2025-01-09")
    sig2 = compute_signature("Report for 2025-01-10")
    assert sig1 == sig2


def test_compute_signature_normalizes_times():
    """Test that times are normalized."""
    sig1 = compute_signature("Job started at 10:30:45")
    sig2 = compute_signature("Job started at 15:20:10")
    assert sig1 == sig2


def test_compute_signature_normalizes_ips():
    """Test that IP addresses are normalized."""
    sig1 = compute_signature("Connection from 192.168.1.1")
    sig2 = compute_signature("Connection from 10.0.0.5")
    assert sig1 == sig2


def test_compute_signature_normalizes_emails():
    """Test that emails are normalized."""
    sig1 = compute_signature("Email sent to john@example.com")
    sig2 = compute_signature("Email sent to jane@company.org")
    assert sig1 == sig2


def test_compute_signature_normalizes_urls():
    """Test that URLs are normalized."""
    sig1 = compute_signature("Downloaded from https://example.com/file.pdf")
    sig2 = compute_signature("Downloaded from http://another.com/document.doc")
    assert sig1 == sig2


def test_compute_signature_different_messages():
    """Test that different messages produce different signatures."""
    sig1 = compute_signature("User logged in")
    sig2 = compute_signature("User logged out")
    assert sig1 != sig2


def test_compute_signature_returns_hex_string():
    """Test that signature is a hex string (MD5)."""
    sig = compute_signature("Test message")
    assert len(sig) == 32  # MD5 produces 32-char hex
    assert all(c in "0123456789abcdef" for c in sig)


def test_compute_signature_handles_empty_string():
    """Test handling of empty string."""
    sig = compute_signature("")
    assert isinstance(sig, str)
    assert len(sig) == 32

