package lipservice

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"go.opentelemetry.io/otel/log"
	"go.opentelemetry.io/otel/sdk/log"
	"go.opentelemetry.io/proto/otlp/collector/logs/v1"
	"go.opentelemetry.io/proto/otlp/common/v1"
	"go.opentelemetry.io/proto/otlp/logs/v1"
	"go.opentelemetry.io/proto/otlp/resource/v1"
	"google.golang.org/protobuf/proto"
)

// PostHogExporter handles OTLP export to PostHog.
type PostHogExporter struct {
	config     Config
	client     *http.Client
	batch      []*logs.LogRecord
	mu         sync.Mutex
	ctx        context.Context
	cancel     context.CancelFunc
	wg         sync.WaitGroup
}

// NewPostHogExporter creates a new PostHog exporter.
func NewPostHogExporter(config Config) (*PostHogExporter, error) {
	ctx, cancel := context.WithCancel(context.Background())

	exporter := &PostHogExporter{
		config: config,
		client: &http.Client{
			Timeout: config.Timeout,
		},
		batch:  make([]*logs.LogRecord, 0, config.BatchSize),
		ctx:    ctx,
		cancel: cancel,
	}

	// Start background flush task
	exporter.wg.Add(1)
	go exporter.flushLoop()

	return exporter, nil
}

// ExportLog exports a log to PostHog.
func (e *PostHogExporter) ExportLog(message, severity string, timestamp time.Time, attributes map[string]interface{}) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	// Create log record
	logRecord := e.createLogRecord(message, severity, timestamp, attributes)
	e.batch = append(e.batch, logRecord)

	// Flush if batch is full
	if len(e.batch) >= e.config.BatchSize {
		return e.flushBatch()
	}

	return nil
}

// createLogRecord creates an OTLP LogRecord.
func (e *PostHogExporter) createLogRecord(message, severity string, timestamp time.Time, attributes map[string]interface{}) *logs.LogRecord {
	// Convert timestamp to nanoseconds
	timestampNs := uint64(timestamp.UnixNano())

	// Create attributes
	otlpAttributes := make([]*common.KeyValue, 0, len(attributes)+2)

	// Add severity
	otlpAttributes = append(otlpAttributes, &common.KeyValue{
		Key: "severity_text",
		Value: &common.AnyValue{
			Value: &common.AnyValue_StringValue{
				StringValue: severity,
			},
		},
	})

	// Add severity number
	severityNumber := e.getSeverityNumber(severity)
	otlpAttributes = append(otlpAttributes, &common.KeyValue{
		Key: "severity_number",
		Value: &common.AnyValue{
			Value: &common.AnyValue_IntValue{
				IntValue: int64(severityNumber),
			},
		},
	})

	// Add custom attributes
	for key, value := range attributes {
		otlpAttributes = append(otlpAttributes, &common.KeyValue{
			Key: key,
			Value: &common.AnyValue{
				Value: &common.AnyValue_StringValue{
					StringValue: fmt.Sprintf("%v", value),
				},
			},
		})
	}

	return &logs.LogRecord{
		TimeUnixNano:   timestampNs,
		SeverityText:   severity,
		SeverityNumber: logs.SeverityNumber(severityNumber),
		Body: &common.AnyValue{
			Value: &common.AnyValue_StringValue{
				StringValue: message,
			},
		},
		Attributes: otlpAttributes,
	}
}

// getSeverityNumber converts severity string to OTLP severity number.
func (e *PostHogExporter) getSeverityNumber(severity string) logs.SeverityNumber {
	switch severity {
	case "TRACE":
		return logs.SeverityNumber_SEVERITY_NUMBER_TRACE
	case "DEBUG":
		return logs.SeverityNumber_SEVERITY_NUMBER_DEBUG
	case "INFO":
		return logs.SeverityNumber_SEVERITY_NUMBER_INFO
	case "WARN", "WARNING":
		return logs.SeverityNumber_SEVERITY_NUMBER_WARN
	case "ERROR":
		return logs.SeverityNumber_SEVERITY_NUMBER_ERROR
	case "FATAL", "CRITICAL":
		return logs.SeverityNumber_SEVERITY_NUMBER_FATAL
	default:
		return logs.SeverityNumber_SEVERITY_NUMBER_INFO
	}
}

// flushLoop periodically flushes the batch.
func (e *PostHogExporter) flushLoop() {
	defer e.wg.Done()

	ticker := time.NewTicker(e.config.FlushInterval)
	defer ticker.Stop()

	for {
		select {
		case <-e.ctx.Done():
			// Flush remaining logs before exiting
			e.mu.Lock()
			if len(e.batch) > 0 {
				e.flushBatch()
			}
			e.mu.Unlock()
			return
		case <-ticker.C:
			e.mu.Lock()
			if len(e.batch) > 0 {
				e.flushBatch()
			}
			e.mu.Unlock()
		}
	}
}

// flushBatch flushes the current batch to PostHog.
func (e *PostHogExporter) flushBatch() error {
	if len(e.batch) == 0 {
		return nil
	}

	// Create OTLP request
	request := e.createOTLPRequest(e.batch)

	// Serialize request
	data, err := proto.Marshal(request)
	if err != nil {
		return fmt.Errorf("failed to marshal OTLP request: %w", err)
	}

	// Send request with retries
	for attempt := 0; attempt <= e.config.MaxRetries; attempt++ {
		err := e.sendRequest(data)
		if err == nil {
			break
		}

		if attempt < e.config.MaxRetries {
			// Exponential backoff
			waitTime := time.Duration(1<<uint(attempt)) * time.Second
			time.Sleep(waitTime)
		}
	}

	// Clear batch
	e.batch = e.batch[:0]

	return err
}

// createOTLPRequest creates an OTLP ExportLogsServiceRequest.
func (e *PostHogExporter) createOTLPRequest(logRecords []*logs.LogRecord) *collector.ExportLogsServiceRequest {
	// Create resource
	resource := &resource.Resource{
		Attributes: []*common.KeyValue{
			{
				Key: "service.name",
				Value: &common.AnyValue{
					Value: &common.AnyValue_StringValue{
						StringValue: e.config.ServiceName,
					},
				},
			},
			{
				Key: "service.version",
				Value: &common.AnyValue{
					Value: &common.AnyValue_StringValue{
						StringValue: "0.2.0",
					},
				},
			},
		},
	}

	// Create scope
	scope := &common.InstrumentationScope{
		Name:    "lipservice-go",
		Version: "0.2.0",
	}

	// Create scope logs
	scopeLogs := &logs.ScopeLogs{
		Scope:      scope,
		LogRecords: logRecords,
	}

	// Create resource logs
	resourceLogs := &logs.ResourceLogs{
		Resource:   resource,
		ScopeLogs:  []*logs.ScopeLogs{scopeLogs},
	}

	return &collector.ExportLogsServiceRequest{
		ResourceLogs: []*logs.ResourceLogs{resourceLogs},
	}
}

// sendRequest sends the OTLP request to PostHog.
func (e *PostHogExporter) sendRequest(data []byte) error {
	url := fmt.Sprintf("%s/api/v1/otlp/v1/logs", e.config.PostHogEndpoint)

	req, err := http.NewRequestWithContext(e.ctx, "POST", url, bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	req.Header.Set("Content-Type", "application/x-protobuf")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", e.config.PostHogAPIKey))
	req.Header.Set("X-PostHog-Team-Id", e.config.PostHogTeamID)

	// Send request
	resp, err := e.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("PostHog returned status %d", resp.StatusCode)
	}

	return nil
}

// Close shuts down the exporter.
func (e *PostHogExporter) Close() error {
	e.cancel()
	e.wg.Wait()
	return nil
}
