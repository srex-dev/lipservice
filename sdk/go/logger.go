package lipservice

import (
	"context"
	"fmt"
	"log/slog"
	"time"
)

// LipServiceLogger provides intelligent logging with sampling and PostHog integration.
type LipServiceLogger struct {
	sampler       *AdaptiveSampler
	posthogExporter *PostHogExporter
	baseLogger    *slog.Logger
}

// NewLipServiceLogger creates a new LipService logger.
func NewLipServiceLogger(sampler *AdaptiveSampler, posthogExporter *PostHogExporter) *LipServiceLogger {
	baseLogger := slog.Default()

	return &LipServiceLogger{
		sampler:       sampler,
		posthogExporter: posthogExporter,
		baseLogger:    baseLogger,
	}
}

// Info logs an info message.
func (l *LipServiceLogger) Info(msg string, args ...interface{}) {
	l.log("INFO", msg, args...)
}

// Warn logs a warning message.
func (l *LipServiceLogger) Warn(msg string, args ...interface{}) {
	l.log("WARN", msg, args...)
}

// Error logs an error message.
func (l *LipServiceLogger) Error(msg string, args ...interface{}) {
	l.log("ERROR", msg, args...)
}

// Debug logs a debug message.
func (l *LipServiceLogger) Debug(msg string, args ...interface{}) {
	l.log("DEBUG", msg, args...)
}

// Fatal logs a fatal message.
func (l *LipServiceLogger) Fatal(msg string, args ...interface{}) {
	l.log("FATAL", msg, args...)
}

// log handles the core logging logic with sampling and PostHog export.
func (l *LipServiceLogger) log(severity, msg string, args ...interface{}) {
	// Check if we should sample this log
	if !l.sampler.ShouldSample(msg, severity) {
		return
	}

	// Log to base logger
	l.baseLogger.Info(msg, args...)

	// Export to PostHog if configured
	if l.posthogExporter != nil {
		// Convert args to attributes map
		attributes := make(map[string]interface{})
		for i := 0; i < len(args); i += 2 {
			if i+1 < len(args) {
				key, ok := args[i].(string)
				if ok {
					attributes[key] = args[i+1]
				}
			}
		}

		// Export to PostHog
		err := l.posthogExporter.ExportLog(msg, severity, time.Now(), attributes)
		if err != nil {
			// Log error but don't fail
			l.baseLogger.Error("Failed to export log to PostHog", "error", err)
		}
	}
}

// With returns a new logger with additional context.
func (l *LipServiceLogger) With(args ...interface{}) *LipServiceLogger {
	newLogger := l.baseLogger.With(args...)
	
	return &LipServiceLogger{
		sampler:       l.sampler,
		posthogExporter: l.posthogExporter,
		baseLogger:    newLogger,
	}
}

// WithContext returns a new logger with the given context.
func (l *LipServiceLogger) WithContext(ctx context.Context) *LipServiceLogger {
	newLogger := l.baseLogger.With("context", ctx)
	
	return &LipServiceLogger{
		sampler:       l.sampler,
		posthogExporter: l.posthogExporter,
		baseLogger:    newLogger,
	}
}

// Example usage and integration patterns

// ExampleHTTPHandler shows how to integrate LipService with HTTP handlers.
func ExampleHTTPHandler(ls *LipService) http.HandlerFunc {
	logger := ls.Logger()
	
	return func(w http.ResponseWriter, r *http.Request) {
		// Log request
		logger.Info("HTTP request received", 
			"method", r.Method,
			"path", r.URL.Path,
			"user_agent", r.UserAgent(),
		)
		
		// Process request
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
		
		// Log response
		logger.Info("HTTP request completed",
			"method", r.Method,
			"path", r.URL.Path,
			"status", 200,
		)
	}
}

// ExampleDatabaseOperation shows how to integrate LipService with database operations.
func ExampleDatabaseOperation(ls *LipService) error {
	logger := ls.Logger()
	
	logger.Info("Starting database operation", "operation", "user_lookup")
	
	// Simulate database operation
	time.Sleep(100 * time.Millisecond)
	
	logger.Info("Database operation completed", 
		"operation", "user_lookup",
		"duration_ms", 100,
		"rows_affected", 1,
	)
	
	return nil
}

// ExampleErrorHandling shows how to handle errors with LipService.
func ExampleErrorHandling(ls *LipService) {
	logger := ls.Logger()
	
	defer func() {
		if r := recover(); r != nil {
			logger.Error("Panic recovered", "panic", r)
		}
	}()
	
	// Simulate an error
	err := fmt.Errorf("database connection failed")
	if err != nil {
		logger.Error("Database operation failed", 
			"error", err.Error(),
			"operation", "user_creation",
		)
	}
}
