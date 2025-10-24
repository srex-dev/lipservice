use crate::config::Config;
use anyhow::Result;
use dashmap::DashMap;
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tokio::time::interval;
use tracing::{debug, error, info, warn};

/// Adaptive sampler that handles intelligent log sampling
pub struct AdaptiveSampler {
    config: Config,
    policy: Arc<RwLock<Option<SamplingPolicy>>>,
    pattern_stats: Arc<DashMap<String, PatternStats>>,
    signature_computer: Arc<SignatureComputer>,
    last_policy_update: Arc<RwLock<Instant>>,
}

/// Sampling policy from LipService backend
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SamplingPolicy {
    pub policy_id: String,
    pub sampling_rate: f64,
    pub patterns: Vec<String>,
    pub max_logs_per_minute: u32,
    pub severity_rates: std::collections::HashMap<String, f64>,
}

/// Pattern statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PatternStats {
    pub count: u64,
    pub last_seen: SystemTime,
    pub signature: String,
    pub sampling_rate: f64,
}

/// Signature computer for log pattern analysis
pub struct SignatureComputer {
    patterns: Vec<(regex::Regex, String)>,
}

impl SignatureComputer {
    pub fn new() -> Self {
        let patterns = vec![
            (regex::Regex::new(r"\b\d+\b").unwrap(), "N".to_string()),
            (regex::Regex::new(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}").unwrap(), "UUID".to_string()),
            (regex::Regex::new(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}").unwrap(), "TIMESTAMP".to_string()),
            (regex::Regex::new(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b").unwrap(), "IP".to_string()),
            (regex::Regex::new(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b").unwrap(), "EMAIL".to_string()),
            (regex::Regex::new(r"https?://[^\s]+").unwrap(), "URL".to_string()),
        ];

        Self { patterns }
    }

    pub fn compute_signature(&self, message: &str) -> String {
        let mut normalized = message.to_lowercase().trim().to_string();

        // Apply pattern replacements
        for (pattern, replacement) in &self.patterns {
            normalized = pattern.replace_all(&normalized, replacement).to_string();
        }

        // Compute MD5 hash
        let digest = md5::compute(normalized.as_bytes());
        format!("{:x}", digest)
    }
}

impl AdaptiveSampler {
    /// Create a new adaptive sampler
    pub async fn new(config: Config) -> Result<Self> {
        let sampler = Self {
            config: config.clone(),
            policy: Arc::new(RwLock::new(None)),
            pattern_stats: Arc::new(DashMap::new()),
            signature_computer: Arc::new(SignatureComputer::new()),
            last_policy_update: Arc::new(RwLock::new(Instant::now())),
        };

        // Start background tasks
        sampler.start_background_tasks().await;

        Ok(sampler)
    }

    /// Determine if a log should be sampled
    pub fn should_sample(&self, message: &str, severity: &str) -> bool {
        // Always sample errors and critical logs
        if matches!(severity.to_uppercase().as_str(), "ERROR" | "CRITICAL" | "FATAL") {
            return true;
        }

        // Compute signature
        let signature = self.signature_computer.compute_signature(message);

        // Update pattern stats
        if let Some(mut stats) = self.pattern_stats.get_mut(&signature) {
            stats.count += 1;
            stats.last_seen = SystemTime::now();
            return self.decide_sampling(stats.sampling_rate);
        }

        // Default sampling rate
        self.decide_sampling(0.1) // 10% default
    }

    /// Make a sampling decision based on rate
    fn decide_sampling(&self, rate: f64) -> bool {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let mut hasher = DefaultHasher::new();
        SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos().hash(&mut hasher);
        let hash = hasher.finish();
        
        (hash % 10000) < (rate * 10000.0) as u64
    }

    /// Start background tasks for policy refresh and pattern reporting
    async fn start_background_tasks(&self) {
        let policy_refresh_interval = self.config.policy_refresh_interval;
        let pattern_report_interval = self.config.pattern_report_interval;
        let policy = Arc::clone(&self.policy);
        let pattern_stats = Arc::clone(&self.pattern_stats);
        let last_policy_update = Arc::clone(&self.last_policy_update);

        // Policy refresh task
        tokio::spawn(async move {
            let mut interval = interval(policy_refresh_interval);
            loop {
                interval.tick().await;
                Self::refresh_policy(&policy, &last_policy_update).await;
            }
        });

        // Pattern reporting task
        tokio::spawn(async move {
            let mut interval = interval(pattern_report_interval);
            loop {
                interval.tick().await;
                Self::report_patterns(&pattern_stats).await;
            }
        });
    }

    /// Refresh the sampling policy
    async fn refresh_policy(
        policy: &Arc<RwLock<Option<SamplingPolicy>>>,
        last_update: &Arc<RwLock<Instant>>,
    ) {
        debug!("Refreshing sampling policy");

        // For now, use a default policy
        // In a real implementation, this would fetch from LipService backend
        let new_policy = SamplingPolicy {
            policy_id: "default".to_string(),
            sampling_rate: 0.1,
            patterns: vec!["error".to_string(), "warning".to_string()],
            max_logs_per_minute: 1000,
            severity_rates: std::collections::HashMap::from([
                ("ERROR".to_string(), 1.0),
                ("WARNING".to_string(), 0.5),
                ("INFO".to_string(), 0.1),
                ("DEBUG".to_string(), 0.05),
            ]),
        };

        {
            let mut policy_guard = policy.write();
            *policy_guard = Some(new_policy);
        }

        {
            let mut last_update_guard = last_update.write();
            *last_update_guard = Instant::now();
        }

        info!("Sampling policy refreshed");
    }

    /// Report pattern statistics
    async fn report_patterns(pattern_stats: &Arc<DashMap<String, PatternStats>>) {
        let count = pattern_stats.len();
        debug!("Reporting {} patterns", count);

        // In a real implementation, this would send stats to LipService backend
        // For now, just log the count
        info!("Pattern statistics reported", pattern_count = count);
    }

    /// Get current policy
    pub fn get_policy(&self) -> Option<SamplingPolicy> {
        self.policy.read().clone()
    }

    /// Get pattern statistics
    pub fn get_pattern_stats(&self) -> Vec<PatternStats> {
        self.pattern_stats.iter().map(|entry| entry.value().clone()).collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_adaptive_sampler_creation() {
        let config = Config::default();
        let sampler = AdaptiveSampler::new(config).await;
        assert!(sampler.is_ok());
    }

    #[tokio::test]
    async fn test_error_sampling() {
        let config = Config::default();
        let sampler = AdaptiveSampler::new(config).await.unwrap();

        // Error logs should always be sampled
        assert!(sampler.should_sample("Database connection failed", "ERROR"));
        assert!(sampler.should_sample("System critical error", "CRITICAL"));
        assert!(sampler.should_sample("Fatal system error", "FATAL"));
    }

    #[tokio::test]
    async fn test_signature_computation() {
        let computer = SignatureComputer::new();
        
        let sig1 = computer.compute_signature("User 123 logged in");
        let sig2 = computer.compute_signature("User 456 logged in");
        
        // Different user IDs should produce different signatures
        assert_ne!(sig1, sig2);
        
        // Same message should produce same signature
        let sig3 = computer.compute_signature("User 123 logged in");
        assert_eq!(sig1, sig3);
    }

    #[tokio::test]
    async fn test_pattern_normalization() {
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
}
