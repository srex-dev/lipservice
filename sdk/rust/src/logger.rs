//! Logger module for LipService integration
//! 
//! This module provides the main logging interface for LipService.

use crate::sampler::AdaptiveSampler;
use crate::posthog::PostHogExporter;
use std::sync::Arc;
use tracing::{debug, error, info, warn};

/// LipService logger that integrates with tracing
pub struct LipServiceLogger {
    sampler: Arc<AdaptiveSampler>,
    posthog_exporter: Option<Arc<PostHogExporter>>,
}

impl LipServiceLogger {
    /// Create a new LipService logger
    pub fn new(
        sampler: Arc<AdaptiveSampler>,
        posthog_exporter: Option<Arc<PostHogExporter>>,
    ) -> Self {
        Self {
            sampler,
            posthog_exporter,
        }
    }

    /// Log an info message
    pub fn info(&self, message: &str) {
        self.log("INFO", message, &[]);
    }

    /// Log a warning message
    pub fn warn(&self, message: &str) {
        self.log("WARN", message, &[]);
    }

    /// Log an error message
    pub fn error(&self, message: &str) {
        self.log("ERROR", message, &[]);
    }

    /// Log a debug message
    pub fn debug(&self, message: &str) {
        self.log("DEBUG", message, &[]);
    }

    /// Log a fatal message
    pub fn fatal(&self, message: &str) {
        self.log("FATAL", message, &[]);
    }

    /// Core logging method
    fn log(&self, severity: &str, message: &str, _attributes: &[(&str, &str)]) {
        // Check if we should sample this log
        if !self.sampler.should_sample(message, severity) {
            return;
        }

        // Log to tracing
        match severity {
            "INFO" => info!("{}", message),
            "WARN" => warn!("{}", message),
            "ERROR" => error!("{}", message),
            "DEBUG" => debug!("{}", message),
            "FATAL" => error!("{}", message),
            _ => info!("{}", message),
        }

        // Export to PostHog if configured
        if let Some(exporter) = &self.posthog_exporter {
            if let Err(e) = exporter.export_log(message, severity, std::time::SystemTime::now(), vec![]) {
                error!("Failed to export log to PostHog: {}", e);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::Config;

    #[tokio::test]
    async fn test_logger_creation() {
        let config = Config::default();
        let sampler = Arc::new(AdaptiveSampler::new(config).await.unwrap());
        let logger = LipServiceLogger::new(sampler, None);

        // Test that logger can be created
        assert!(true); // Placeholder test
    }

    #[tokio::test]
    async fn test_logger_methods() {
        let config = Config::default();
        let sampler = Arc::new(AdaptiveSampler::new(config).await.unwrap());
        let logger = LipServiceLogger::new(sampler, None);

        // Test all logging methods
        logger.info("Test info message");
        logger.warn("Test warning message");
        logger.error("Test error message");
        logger.debug("Test debug message");
        logger.fatal("Test fatal message");

        // Test should not panic
        assert!(true);
    }
}
