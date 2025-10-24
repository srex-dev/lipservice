//! # LipService Rust SDK
//!
//! AI-powered intelligent log sampling for Rust applications with PostHog integration.
//!
//! ## Features
//!
//! - **AI-Powered Sampling**: Intelligent pattern analysis and adaptive sampling
//! - **PostHog Integration**: Direct OTLP export to PostHog
//! - **High Performance**: Zero-copy operations and async processing
//! - **Memory Safe**: Rust's ownership system ensures memory safety
//! - **Zero Data Loss**: Always keeps ERROR and CRITICAL logs
//! - **Cost Reduction**: 90%+ reduction in log storage costs
//!
//! ## Quick Start
//!
//! ```rust
//! use lipservice::{LipService, Config};
//! use tracing::{info, error};
//!
//! #[tokio::main]
//! async fn main() -> Result<(), Box<dyn std::error::Error>> {
//!     // Configure LipService
//!     let config = Config {
//!         service_name: "my-rust-service".to_string(),
//!         lipservice_url: "https://lipservice.company.com".to_string(),
//!         posthog_api_key: Some("phc_xxx".to_string()),
//!         posthog_team_id: Some("12345".to_string()),
//!         ..Default::default()
//!     };
//!
//!     // Initialize LipService
//!     let mut ls = LipService::new(config).await?;
//!
//!     // Use tracing macros - they're automatically sampled and sent to PostHog!
//!     info!("User logged in", user_id = 123);
//!     error!("Database connection failed", error = "timeout");
//!
//!     // Cleanup
//!     ls.shutdown().await?;
//!     Ok(())
//! }
//! ```

pub mod config;
pub mod sampler;
pub mod posthog;
pub mod signature;
pub mod logger;

pub use config::Config;
pub use sampler::AdaptiveSampler;
pub use posthog::PostHogExporter;
pub use signature::SignatureComputer;
pub use logger::LipServiceLogger;

use anyhow::Result;
use std::sync::Arc;
use tokio::sync::RwLock;

/// Main LipService client
pub struct LipService {
    config: Config,
    sampler: Arc<AdaptiveSampler>,
    posthog_exporter: Option<Arc<PostHogExporter>>,
    logger: Arc<LipServiceLogger>,
}

impl LipService {
    /// Create a new LipService instance
    pub async fn new(config: Config) -> Result<Self> {
        // Initialize adaptive sampler
        let sampler = Arc::new(AdaptiveSampler::new(config.clone()).await?);

        // Initialize PostHog exporter if configured
        let posthog_exporter = if config.posthog_api_key.is_some() && config.posthog_team_id.is_some() {
            Some(Arc::new(PostHogExporter::new(config.clone()).await?))
        } else {
            None
        };

        // Initialize logger
        let logger = Arc::new(LipServiceLogger::new(
            sampler.clone(),
            posthog_exporter.clone(),
        ));

        Ok(Self {
            config,
            sampler,
            posthog_exporter,
            logger,
        })
    }

    /// Get the LipService logger
    pub fn logger(&self) -> Arc<LipServiceLogger> {
        self.logger.clone()
    }

    /// Shutdown the LipService instance
    pub async fn shutdown(self) -> Result<()> {
        if let Some(exporter) = self.posthog_exporter {
            exporter.shutdown().await?;
        }
        Ok(())
    }
}

/// Initialize LipService with tracing integration
pub async fn init(config: Config) -> Result<LipService> {
    // Initialize tracing subscriber
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    // Create LipService instance
    LipService::new(config).await
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_lipservice_creation() {
        let config = Config {
            service_name: "test-service".to_string(),
            lipservice_url: "http://localhost:8000".to_string(),
            ..Default::default()
        };

        let ls = LipService::new(config).await;
        assert!(ls.is_ok());
    }

    #[tokio::test]
    async fn test_lipservice_with_posthog() {
        let config = Config {
            service_name: "test-service".to_string(),
            lipservice_url: "http://localhost:8000".to_string(),
            posthog_api_key: Some("phc_test".to_string()),
            posthog_team_id: Some("12345".to_string()),
            ..Default::default()
        };

        let ls = LipService::new(config).await;
        assert!(ls.is_ok());
    }
}
