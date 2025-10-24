use serde::{Deserialize, Serialize};
use std::time::Duration;

/// Configuration for LipService
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// Name of the service using LipService
    pub service_name: String,
    
    /// URL of the LipService backend
    pub lipservice_url: String,
    
    /// API key for LipService (optional)
    pub api_key: Option<String>,
    
    /// PostHog API key for direct integration
    pub posthog_api_key: Option<String>,
    
    /// PostHog team ID
    pub posthog_team_id: Option<String>,
    
    /// PostHog endpoint (defaults to https://app.posthog.com)
    pub posthog_endpoint: String,
    
    /// Batch size for exports
    pub batch_size: usize,
    
    /// Flush interval between batch exports
    pub flush_interval: Duration,
    
    /// Maximum number of retry attempts
    pub max_retries: u32,
    
    /// Request timeout
    pub timeout: Duration,
    
    /// Policy refresh interval
    pub policy_refresh_interval: Duration,
    
    /// Pattern report interval
    pub pattern_report_interval: Duration,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            service_name: "lipservice-service".to_string(),
            lipservice_url: "http://localhost:8000".to_string(),
            api_key: None,
            posthog_api_key: None,
            posthog_team_id: None,
            posthog_endpoint: "https://app.posthog.com".to_string(),
            batch_size: 100,
            flush_interval: Duration::from_secs(5),
            max_retries: 3,
            timeout: Duration::from_secs(10),
            policy_refresh_interval: Duration::from_secs(300), // 5 minutes
            pattern_report_interval: Duration::from_secs(600), // 10 minutes
        }
    }
}

impl Config {
    /// Create a new config with required fields
    pub fn new(service_name: String, lipservice_url: String) -> Self {
        Self {
            service_name,
            lipservice_url,
            ..Default::default()
        }
    }

    /// Set PostHog credentials
    pub fn with_posthog(mut self, api_key: String, team_id: String) -> Self {
        self.posthog_api_key = Some(api_key);
        self.posthog_team_id = Some(team_id);
        self
    }

    /// Set custom PostHog endpoint
    pub fn with_posthog_endpoint(mut self, endpoint: String) -> Self {
        self.posthog_endpoint = endpoint;
        self
    }

    /// Set batch size
    pub fn with_batch_size(mut self, batch_size: usize) -> Self {
        self.batch_size = batch_size;
        self
    }

    /// Set flush interval
    pub fn with_flush_interval(mut self, interval: Duration) -> Self {
        self.flush_interval = interval;
        self
    }

    /// Set timeout
    pub fn with_timeout(mut self, timeout: Duration) -> Self {
        self.timeout = timeout;
        self
    }

    /// Set max retries
    pub fn with_max_retries(mut self, max_retries: u32) -> Self {
        self.max_retries = max_retries;
        self
    }

    /// Validate the configuration
    pub fn validate(&self) -> Result<(), String> {
        if self.service_name.is_empty() {
            return Err("service_name cannot be empty".to_string());
        }
        
        if self.lipservice_url.is_empty() {
            return Err("lipservice_url cannot be empty".to_string());
        }
        
        if self.batch_size == 0 {
            return Err("batch_size must be greater than 0".to_string());
        }
        
        if self.max_retries > 10 {
            return Err("max_retries cannot exceed 10".to_string());
        }
        
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert_eq!(config.service_name, "lipservice-service");
        assert_eq!(config.lipservice_url, "http://localhost:8000");
        assert_eq!(config.posthog_endpoint, "https://app.posthog.com");
        assert_eq!(config.batch_size, 100);
        assert_eq!(config.max_retries, 3);
    }

    #[test]
    fn test_config_builder() {
        let config = Config::new("test-service".to_string(), "http://localhost:8000".to_string())
            .with_posthog("phc_test".to_string(), "12345".to_string())
            .with_batch_size(50)
            .with_timeout(Duration::from_secs(5));

        assert_eq!(config.service_name, "test-service");
        assert_eq!(config.posthog_api_key, Some("phc_test".to_string()));
        assert_eq!(config.posthog_team_id, Some("12345".to_string()));
        assert_eq!(config.batch_size, 50);
        assert_eq!(config.timeout, Duration::from_secs(5));
    }

    #[test]
    fn test_config_validation() {
        let mut config = Config::default();
        assert!(config.validate().is_ok());

        config.service_name = "".to_string();
        assert!(config.validate().is_err());

        config.service_name = "test".to_string();
        config.batch_size = 0;
        assert!(config.validate().is_err());

        config.batch_size = 100;
        config.max_retries = 11;
        assert!(config.validate().is_err());
    }
}
