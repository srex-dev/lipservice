import pytest

from src.engine.signature import compute_signature, compute_signature_with_context, extract_error_type


@pytest.mark.parametrize(
    "message1,message2",
    [
        ("User 123 logged in", "User 456 logged in"),
        ("Payment $99.99 processed", "Payment $49.99 processed"),
        ("Error on line 42", "Error on line 100"),
        ("Request from 192.168.1.1", "Request from 10.0.0.1"),
        (
            "File saved: C:\\Users\\test\\file.txt",
            "File saved: C:\\Users\\admin\\document.txt",
        ),
    ],
)
def test_similar_messages_produce_same_signature(message1, message2):
    sig1 = compute_signature(message1)
    sig2 = compute_signature(message2)
    assert sig1 == sig2


@pytest.mark.parametrize(
    "message1,message2",
    [
        ("User logged in", "User logged out"),
        ("Payment processed", "Payment failed"),
        ("File saved", "File deleted"),
    ],
)
def test_different_messages_produce_different_signatures(message1, message2):
    sig1 = compute_signature(message1)
    sig2 = compute_signature(message2)
    assert sig1 != sig2


@pytest.mark.parametrize(
    "message,expected_pattern",
    [
        ("User 123 logged in", "user n logged in"),
        ("Error: File not found at /var/log/app.log", "error: file not found at path"),
        ("2024-01-15 10:30:00 - Request started", "date time - request started"),
        ("UUID: 550e8400-e29b-41d4-a716-446655440000", "uuid: uuid"),
        ("Connection from 192.168.1.100:8080", "connection from ip:n"),
    ],
)
def test_normalization_patterns(message, expected_pattern):
    sig = compute_signature(message)
    assert sig == compute_signature(expected_pattern)


def test_empty_message_returns_consistent_hash():
    sig1 = compute_signature("")
    sig2 = compute_signature("")
    assert sig1 == sig2
    assert len(sig1) == 32


def test_signature_is_md5_hash():
    sig = compute_signature("Test message")
    assert len(sig) == 32
    assert all(c in "0123456789abcdef" for c in sig)


@pytest.mark.parametrize(
    "message,expected_error",
    [
        ("ValueError: Invalid input", "ValueError"),
        ("TypeError: cannot convert", "TypeError"),
        ("Exception: RuntimeError occurred", "RuntimeError"),
        ("Error: KeyError in handler", "KeyError"),
        ("Normal log message", None),
    ],
)
def test_extract_error_type(message, expected_error):
    error = extract_error_type(message)
    assert error == expected_error


def test_signature_with_context_includes_severity():
    msg = "User logged in"

    sig_info = compute_signature_with_context(msg, severity="INFO")
    sig_error = compute_signature_with_context(msg, severity="ERROR")

    assert sig_info != sig_error


def test_signature_with_context_includes_error_type():
    msg = "Operation failed"

    sig_value_error = compute_signature_with_context(msg, error_type="ValueError")
    sig_type_error = compute_signature_with_context(msg, error_type="TypeError")

    assert sig_value_error != sig_type_error


def test_case_insensitive_normalization():
    sig_lower = compute_signature("user logged in")
    sig_upper = compute_signature("USER LOGGED IN")
    sig_mixed = compute_signature("User Logged In")

    assert sig_lower == sig_upper == sig_mixed


def test_whitespace_normalization():
    sig1 = compute_signature("User  logged    in")
    sig2 = compute_signature("User logged in")

    assert sig1 == sig2

