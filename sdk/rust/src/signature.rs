//! Signature computation module
//! 
//! This module provides efficient signature computation for log pattern analysis.

use md5::{Digest, Md5};
use regex::Regex;
use std::collections::HashMap;

/// Signature computer for log pattern analysis
pub struct SignatureComputer {
    patterns: Vec<(Regex, String)>,
}

impl SignatureComputer {
    /// Create a new signature computer
    pub fn new() -> Self {
        let patterns = vec![
            (Regex::new(r"\b\d+\b").unwrap(), "N".to_string()),
            (Regex::new(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}").unwrap(), "UUID".to_string()),
            (Regex::new(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}").unwrap(), "TIMESTAMP".to_string()),
            (Regex::new(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b").unwrap(), "IP".to_string()),
            (Regex::new(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b").unwrap(), "EMAIL".to_string()),
            (Regex::new(r"https?://[^\s]+").unwrap(), "URL".to_string()),
        ];

        Self { patterns }
    }

    /// Compute signature for a log message
    pub fn compute_signature(&self, message: &str) -> String {
        let mut normalized = message.to_lowercase().trim().to_string();

        // Apply pattern replacements
        for (pattern, replacement) in &self.patterns {
            normalized = pattern.replace_all(&normalized, replacement).to_string();
        }

        // Compute MD5 hash
        let mut hasher = Md5::new();
        hasher.update(normalized.as_bytes());
        let result = hasher.finalize();
        format!("{:x}", result)
    }
}

impl Default for SignatureComputer {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_signature_computation() {
        let computer = SignatureComputer::new();
        
        let sig1 = computer.compute_signature("User 123 logged in");
        let sig2 = computer.compute_signature("User 456 logged in");
        
        // Different user IDs should produce different signatures
        assert_ne!(sig1, sig2);
        
        // Same message should produce same signature
        let sig3 = computer.compute_signature("User 123 logged in");
        assert_eq!(sig1, sig3);
    }

    #[test]
    fn test_pattern_normalization() {
        let computer = SignatureComputer::new();
        
        let sig1 = computer.compute_signature("User 123 logged in from IP 192.168.1.1");
        let sig2 = computer.compute_signature("User 456 logged in from IP 10.0.0.1");
        
        // Different user IDs and IPs should produce different signatures
        assert_ne!(sig1, sig2);
        
        // But same pattern should produce same signature
        let sig3 = computer.compute_signature("User 789 logged in from IP 192.168.1.2");
        let sig4 = computer.compute_signature("User 101112 logged in from IP 10.0.0.2");
        
        // Should be the same pattern
        assert_eq!(sig3, sig4);
    }

    #[test]
    fn test_uuid_normalization() {
        let computer = SignatureComputer::new();
        
        let sig1 = computer.compute_signature("Request 550e8400-e29b-41d4-a716-446655440000 processed");
        let sig2 = computer.compute_signature("Request 6ba7b810-9dad-11d1-80b4-00c04fd430c8 processed");
        
        // Different UUIDs should produce same signature (normalized)
        assert_eq!(sig1, sig2);
    }

    #[test]
    fn test_timestamp_normalization() {
        let computer = SignatureComputer::new();
        
        let sig1 = computer.compute_signature("Log entry at 2023-01-01T12:00:00");
        let sig2 = computer.compute_signature("Log entry at 2023-12-31T23:59:59");
        
        // Different timestamps should produce same signature (normalized)
        assert_eq!(sig1, sig2);
    }
}
