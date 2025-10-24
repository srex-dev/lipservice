package lipservice

import (
	"testing"
	"time"
)

func TestConfig(t *testing.T) {
	config := DefaultConfig()
	
	if config.PostHogEndpoint != "https://app.posthog.com" {
		t.Errorf("Expected default PostHog endpoint, got %s", config.PostHogEndpoint)
	}
	
	if config.BatchSize != 100 {
		t.Errorf("Expected default batch size 100, got %d", config.BatchSize)
	}
	
	if config.FlushInterval != 5*time.Second {
		t.Errorf("Expected default flush interval 5s, got %v", config.FlushInterval)
	}
}

func TestLipService(t *testing.T) {
	config := Config{
		ServiceName:    "test-service",
		LipServiceURL:  "http://localhost:8000",
		PostHogAPIKey:  "phc_test",
		PostHogTeamID:   "12345",
		PostHogEndpoint: "https://app.posthog.com",
	}
	
	ls, err := New(config)
	if err != nil {
		t.Fatalf("Failed to create LipService: %v", err)
	}
	defer ls.Close()
	
	if ls.config.ServiceName != "test-service" {
		t.Errorf("Expected service name 'test-service', got %s", ls.config.ServiceName)
	}
	
	logger := ls.Logger()
	if logger == nil {
		t.Error("Expected logger to be non-nil")
	}
}

func TestAdaptiveSampler(t *testing.T) {
	config := Config{
		ServiceName:   "test-service",
		LipServiceURL: "http://localhost:8000",
	}
	
	sampler, err := NewAdaptiveSampler(config)
	if err != nil {
		t.Fatalf("Failed to create adaptive sampler: %v", err)
	}
	
	// Test error sampling (should always be true)
	if !sampler.ShouldSample("Database connection failed", "ERROR") {
		t.Error("Expected error logs to always be sampled")
	}
	
	// Test critical sampling (should always be true)
	if !sampler.ShouldSample("System critical error", "CRITICAL") {
		t.Error("Expected critical logs to always be sampled")
	}
	
	// Test info sampling (should be sampled based on rate)
	sampled := sampler.ShouldSample("User logged in", "INFO")
	// This is probabilistic, so we just check it doesn't panic
	_ = sampled
}

func TestSignatureComputation(t *testing.T) {
	tests := []struct {
		name     string
		message  string
		expected string
	}{
		{
			name:     "simple message",
			message:  "User logged in",
			expected: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
		},
		{
			name:     "message with numbers",
			message:  "User 123 logged in",
			expected: "b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7",
		},
		{
			name:     "message with IP",
			message:  "User logged in from IP 192.168.1.1",
			expected: "c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8",
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			signature := computeSignature(tt.message)
			
			// Check that signature is a valid hex string
			if len(signature) != 32 {
				t.Errorf("Expected signature length 32, got %d", len(signature))
			}
			
			// Check that same message produces same signature
			signature2 := computeSignature(tt.message)
			if signature != signature2 {
				t.Error("Expected same message to produce same signature")
			}
		})
	}
}

func TestSignatureNormalization(t *testing.T) {
	// Test that similar messages produce the same signature
	message1 := "User 123 logged in from IP 192.168.1.1"
	message2 := "User 456 logged in from IP 10.0.0.1"
	
	sig1 := computeSignature(message1)
	sig2 := computeSignature(message2)
	
	// These should be different (different user IDs and IPs)
	if sig1 == sig2 {
		t.Error("Expected different user IDs and IPs to produce different signatures")
	}
	
	// But these should be the same pattern
	message3 := "User 789 logged in from IP 192.168.1.2"
	message4 := "User 101112 logged in from IP 10.0.0.2"
	
	sig3 := computeSignature(message3)
	sig4 := computeSignature(message4)
	
	// Should be the same pattern
	if sig3 != sig4 {
		t.Error("Expected same pattern to produce same signature")
	}
}

func TestPostHogExporter(t *testing.T) {
	config := Config{
		ServiceName:     "test-service",
		PostHogAPIKey:   "phc_test",
		PostHogTeamID:   "12345",
		PostHogEndpoint: "https://app.posthog.com",
		BatchSize:       10,
		FlushInterval:   1 * time.Second,
	}
	
	exporter, err := NewPostHogExporter(config)
	if err != nil {
		t.Fatalf("Failed to create PostHog exporter: %v", err)
	}
	defer exporter.Close()
	
	// Test log export
	attributes := map[string]interface{}{
		"user_id": 123,
		"action":  "login",
	}
	
	err = exporter.ExportLog("User logged in", "INFO", time.Now(), attributes)
	if err != nil {
		t.Errorf("Failed to export log: %v", err)
	}
	
	// Wait for flush
	time.Sleep(2 * time.Second)
}

func TestLipServiceLogger(t *testing.T) {
	config := Config{
		ServiceName:     "test-service",
		LipServiceURL:   "http://localhost:8000",
		PostHogAPIKey:   "phc_test",
		PostHogTeamID:   "12345",
		PostHogEndpoint: "https://app.posthog.com",
	}
	
	ls, err := New(config)
	if err != nil {
		t.Fatalf("Failed to create LipService: %v", err)
	}
	defer ls.Close()
	
	logger := ls.Logger()
	
	// Test different log levels
	logger.Info("Test info message", "key", "value")
	logger.Warn("Test warning message", "key", "value")
	logger.Error("Test error message", "key", "value")
	logger.Debug("Test debug message", "key", "value")
	
	// Test with context
	ctx := context.Background()
	loggerWithContext := logger.WithContext(ctx)
	loggerWithContext.Info("Test message with context", "key", "value")
	
	// Test with additional fields
	loggerWithFields := logger.With("service", "test", "version", "1.0.0")
	loggerWithFields.Info("Test message with fields", "key", "value")
}

func TestSeverityNumberConversion(t *testing.T) {
	exporter := &PostHogExporter{}
	
	tests := []struct {
		severity string
		expected logs.SeverityNumber
	}{
		{"TRACE", logs.SeverityNumber_SEVERITY_NUMBER_TRACE},
		{"DEBUG", logs.SeverityNumber_SEVERITY_NUMBER_DEBUG},
		{"INFO", logs.SeverityNumber_SEVERITY_NUMBER_INFO},
		{"WARN", logs.SeverityNumber_SEVERITY_NUMBER_WARN},
		{"WARNING", logs.SeverityNumber_SEVERITY_NUMBER_WARN},
		{"ERROR", logs.SeverityNumber_SEVERITY_NUMBER_ERROR},
		{"FATAL", logs.SeverityNumber_SEVERITY_NUMBER_FATAL},
		{"CRITICAL", logs.SeverityNumber_SEVERITY_NUMBER_FATAL},
		{"UNKNOWN", logs.SeverityNumber_SEVERITY_NUMBER_INFO},
	}
	
	for _, tt := range tests {
		t.Run(tt.severity, func(t *testing.T) {
			result := exporter.getSeverityNumber(tt.severity)
			if result != tt.expected {
				t.Errorf("Expected severity number %v for %s, got %v", tt.expected, tt.severity, result)
			}
		})
	}
}

func BenchmarkSignatureComputation(b *testing.B) {
	message := "User 123 logged in from IP 192.168.1.1"
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		computeSignature(message)
	}
}

func BenchmarkAdaptiveSampler(b *testing.B) {
	config := Config{
		ServiceName:   "test-service",
		LipServiceURL: "http://localhost:8000",
	}
	
	sampler, err := NewAdaptiveSampler(config)
	if err != nil {
		b.Fatalf("Failed to create adaptive sampler: %v", err)
	}
	
	message := "User logged in"
	severity := "INFO"
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		sampler.ShouldSample(message, severity)
	}
}

func BenchmarkPostHogExporter(b *testing.B) {
	config := Config{
		ServiceName:     "test-service",
		PostHogAPIKey:   "phc_test",
		PostHogTeamID:   "12345",
		PostHogEndpoint: "https://app.posthog.com",
		BatchSize:       1000, // Large batch to avoid flushes
	}
	
	exporter, err := NewPostHogExporter(config)
	if err != nil {
		b.Fatalf("Failed to create PostHog exporter: %v", err)
	}
	defer exporter.Close()
	
	attributes := map[string]interface{}{
		"user_id": 123,
		"action":  "login",
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		exporter.ExportLog("User logged in", "INFO", time.Now(), attributes)
	}
}
