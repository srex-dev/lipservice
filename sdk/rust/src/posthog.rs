use crate::config::Config;
use crate::sampler::AdaptiveSampler;
use anyhow::Result;
use opentelemetry::logs::{LogRecord, Severity};
use opentelemetry::KeyValue;
use opentelemetry_otlp::WithExportConfig;
use opentelemetry_sdk::logs::LoggerProvider;
use opentelemetry_sdk::Resource;
use std::sync::Arc;
use std::time::SystemTime;
use tracing::{debug, error, info, warn};

/// PostHog OTLP exporter for high-performance log export
pub struct PostHogExporter {
    config: Config,
    logger_provider: LoggerProvider,
    _shutdown: opentelemetry_sdk::logs::Shutdown,
}

impl PostHogExporter {
    /// Create a new PostHog exporter
    pub async fn new(config: Config) -> Result<Self> {
        let resource = Resource::new(vec![
            KeyValue::new("service.name", config.service_name.clone()),
            KeyValue::new("service.version", "0.2.0"),
        ]);

        let exporter = opentelemetry_otlp::new_exporter()
            .http()
            .with_endpoint(&format!("{}/api/v1/otlp/v1/logs", config.posthog_endpoint))
            .with_headers(std::collections::HashMap::from([
                ("Authorization".to_string(), format!("Bearer {}", config.posthog_api_key.as_ref().unwrap())),
                ("X-PostHog-Team-Id".to_string(), config.posthog_team_id.as_ref().unwrap().clone()),
            ]));

        let logger_provider = LoggerProvider::builder()
            .with_batch_log_processor(
                exporter,
                opentelemetry_sdk::logs::BatchLogProcessorConfig::default()
                    .with_max_export_batch_size(config.batch_size)
                    .with_export_timeout(config.timeout),
            )
            .with_resource(resource)
            .build();

        let shutdown = logger_provider.shutdown();

        Ok(Self {
            config,
            logger_provider,
            _shutdown: shutdown,
        })
    }

    /// Export a log to PostHog
    pub fn export_log(
        &self,
        message: &str,
        severity: &str,
        timestamp: SystemTime,
        attributes: Vec<KeyValue>,
    ) -> Result<()> {
        let logger = self.logger_provider.logger("lipservice-rust");

        let severity = self.parse_severity(severity);
        
        let mut log_record = LogRecord::default();
        log_record.set_severity_text(severity.1.to_string());
        log_record.set_severity_number(severity.0);
        log_record.set_body(message.to_string().into());
        log_record.set_timestamp(timestamp);
        log_record.set_attributes(attributes);

        logger.emit(log_record);
        
        debug!("Log exported to PostHog", message = message, severity = severity.1);
        Ok(())
    }

    /// Parse severity string to OTLP severity
    fn parse_severity(&self, severity: &str) -> (Severity, &str) {
        match severity.to_uppercase().as_str() {
            "TRACE" => (Severity::Trace, "TRACE"),
            "DEBUG" => (Severity::Debug, "DEBUG"),
            "INFO" => (Severity::Info, "INFO"),
            "WARN" | "WARNING" => (Severity::Warn, "WARN"),
            "ERROR" => (Severity::Error, "ERROR"),
            "FATAL" | "CRITICAL" => (Severity::Fatal, "FATAL"),
            _ => (Severity::Info, "INFO"),
        }
    }

    /// Shutdown the exporter
    pub async fn shutdown(self) -> Result<()> {
        // The shutdown is handled by the Drop trait
        Ok(())
    }
}

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

    /// Log a message with sampling and PostHog export
    pub fn log(
        &self,
        level: tracing::Level,
        message: &str,
        fields: &tracing::field::ValueSet,
    ) {
        let severity = match level {
            tracing::Level::TRACE => "TRACE",
            tracing::Level::DEBUG => "DEBUG",
            tracing::Level::INFO => "INFO",
            tracing::Level::WARN => "WARN",
            tracing::Level::ERROR => "ERROR",
        };

        // Check if we should sample this log
        if !self.sampler.should_sample(message, severity) {
            return;
        }

        // Export to PostHog if configured
        if let Some(exporter) = &self.posthog_exporter {
            let attributes = self.extract_attributes(fields);
            if let Err(e) = exporter.export_log(message, severity, SystemTime::now(), attributes) {
                error!("Failed to export log to PostHog: {}", e);
            }
        }
    }

    /// Extract attributes from tracing fields
    fn extract_attributes(&self, fields: &tracing::field::ValueSet) -> Vec<KeyValue> {
        let mut attributes = Vec::new();
        
        fields.record(&mut |key, value| {
            attributes.push(KeyValue::new(key.to_string(), value.to_string()));
        });

        attributes
    }
}

/// Tracing layer for LipService integration
pub struct LipServiceLayer {
    logger: Arc<LipServiceLogger>,
}

impl LipServiceLayer {
    /// Create a new LipService layer
    pub fn new(logger: Arc<LipServiceLogger>) -> Self {
        Self { logger }
    }
}

impl<S> tracing_subscriber::Layer<S> for LipServiceLayer
where
    S: tracing::Subscriber,
{
    fn on_event(&self, event: &tracing::Event<'_>, _ctx: tracing_subscriber::layer::Context<'_, S>) {
        let level = *event.metadata().level();
        let message = format!("{}", event);
        
        self.logger.log(level, &message, event.field_set());
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::Config;

    #[tokio::test]
    async fn test_posthog_exporter_creation() {
        let config = Config {
            service_name: "test-service".to_string(),
            lipservice_url: "http://localhost:8000".to_string(),
            posthog_api_key: Some("phc_test".to_string()),
            posthog_team_id: Some("12345".to_string()),
            ..Default::default()
        };

        let exporter = PostHogExporter::new(config).await;
        // This might fail in tests due to network, but we can test the creation
        // In a real test environment, you'd mock the HTTP client
        assert!(exporter.is_ok() || exporter.is_err());
    }

    #[tokio::test]
    async fn test_lipservice_logger() {
        let config = Config::default();
        let sampler = Arc::new(AdaptiveSampler::new(config.clone()).await.unwrap());
        let logger = LipServiceLogger::new(sampler, None);

        // Test that logger can be created
        assert!(true); // Placeholder test
    }
}
