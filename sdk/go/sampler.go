package lipservice

import (
	"context"
	"crypto/md5"
	"fmt"
	"net/http"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"go.opentelemetry.io/otel/log"
	"go.opentelemetry.io/otel/sdk/log"
)

// Config holds the configuration for LipService.
type Config struct {
	// ServiceName is the name of the service using LipService
	ServiceName string

	// LipServiceURL is the URL of the LipService backend
	LipServiceURL string

	// APIKey is the API key for LipService (optional)
	APIKey string

	// PostHogAPIKey is the PostHog API key for direct integration
	PostHogAPIKey string

	// PostHogTeamID is the PostHog team ID
	PostHogTeamID string

	// PostHogEndpoint is the PostHog endpoint (defaults to https://app.posthog.com)
	PostHogEndpoint string

	// BatchSize is the number of logs to batch before sending
	BatchSize int

	// FlushInterval is the interval between batch flushes
	FlushInterval time.Duration

	// MaxRetries is the maximum number of retry attempts
	MaxRetries int

	// Timeout is the timeout for HTTP requests
	Timeout time.Duration
}

// DefaultConfig returns a default configuration.
func DefaultConfig() Config {
	return Config{
		PostHogEndpoint: "https://app.posthog.com",
		BatchSize:       100,
		FlushInterval:   5 * time.Second,
		MaxRetries:      3,
		Timeout:         10 * time.Second,
	}
}

// LipService is the main LipService client.
type LipService struct {
	config        Config
	sampler       *AdaptiveSampler
	posthogExporter *PostHogExporter
	logger        *LipServiceLogger
	ctx           context.Context
	cancel        context.CancelFunc
	wg            sync.WaitGroup
}

// New creates a new LipService instance.
func New(config Config) (*LipService, error) {
	// Set defaults
	if config.PostHogEndpoint == "" {
		config.PostHogEndpoint = "https://app.posthog.com"
	}
	if config.BatchSize == 0 {
		config.BatchSize = 100
	}
	if config.FlushInterval == 0 {
		config.FlushInterval = 5 * time.Second
	}
	if config.MaxRetries == 0 {
		config.MaxRetries = 3
	}
	if config.Timeout == 0 {
		config.Timeout = 10 * time.Second
	}

	ctx, cancel := context.WithCancel(context.Background())

	ls := &LipService{
		config: config,
		ctx:    ctx,
		cancel: cancel,
	}

	// Initialize components
	if err := ls.initialize(); err != nil {
		cancel()
		return nil, err
	}

	return ls, nil
}

// initialize sets up the LipService components.
func (ls *LipService) initialize() error {
	// Initialize adaptive sampler
	sampler, err := NewAdaptiveSampler(ls.config)
	if err != nil {
		return fmt.Errorf("failed to create adaptive sampler: %w", err)
	}
	ls.sampler = sampler

	// Initialize PostHog exporter if configured
	if ls.config.PostHogAPIKey != "" && ls.config.PostHogTeamID != "" {
		exporter, err := NewPostHogExporter(ls.config)
		if err != nil {
			return fmt.Errorf("failed to create PostHog exporter: %w", err)
		}
		ls.posthogExporter = exporter
	}

	// Initialize logger
	ls.logger = NewLipServiceLogger(ls.sampler, ls.posthogExporter)

	return nil
}

// Logger returns the LipService logger.
func (ls *LipService) Logger() *LipServiceLogger {
	return ls.logger
}

// Close shuts down the LipService instance.
func (ls *LipService) Close() error {
	ls.cancel()
	ls.wg.Wait()

	if ls.posthogExporter != nil {
		return ls.posthogExporter.Close()
	}

	return nil
}

// AdaptiveSampler handles intelligent log sampling.
type AdaptiveSampler struct {
	config        Config
	client        *http.Client
	policy        *SamplingPolicy
	patternStats  map[string]*PatternStats
	mu            sync.RWMutex
	lastPolicyUpdate time.Time
}

// SamplingPolicy represents a sampling policy from LipService backend.
type SamplingPolicy struct {
	PolicyID        string            `json:"policy_id"`
	SamplingRate    float64           `json:"sampling_rate"`
	Patterns        []string          `json:"patterns"`
	MaxLogsPerMinute int              `json:"max_logs_per_minute"`
	SeverityRates   map[string]float64 `json:"severity_rates"`
}

// PatternStats tracks statistics for log patterns.
type PatternStats struct {
	Count       int       `json:"count"`
	LastSeen    time.Time `json:"last_seen"`
	Signature   string    `json:"signature"`
	SamplingRate float64  `json:"sampling_rate"`
}

// NewAdaptiveSampler creates a new adaptive sampler.
func NewAdaptiveSampler(config Config) (*AdaptiveSampler, error) {
	client := &http.Client{
		Timeout: config.Timeout,
	}

	sampler := &AdaptiveSampler{
		config:       config,
		client:       client,
		patternStats: make(map[string]*PatternStats),
	}

	// Start background tasks
	go sampler.policyRefreshLoop()
	go sampler.patternReportLoop()

	return sampler, nil
}

// ShouldSample determines if a log should be sampled.
func (s *AdaptiveSampler) ShouldSample(message, severity string) bool {
	s.mu.RLock()
	defer s.mu.RUnlock()

	// Always sample errors and critical logs
	if severity == "ERROR" || severity == "CRITICAL" || severity == "FATAL" {
		return true
	}

	// Compute signature
	signature := computeSignature(message)

	// Check pattern stats
	if stats, exists := s.patternStats[signature]; exists {
		stats.Count++
		stats.LastSeen = time.Now()
		return s.decideSampling(stats.SamplingRate)
	}

	// Default sampling rate
	return s.decideSampling(0.1) // 10% default
}

// decideSampling makes a sampling decision based on rate.
func (s *AdaptiveSampler) decideSampling(rate float64) bool {
	// Simple random sampling
	return time.Now().UnixNano()%10000 < int64(rate*10000)
}

// policyRefreshLoop refreshes the sampling policy periodically.
func (s *AdaptiveSampler) policyRefreshLoop() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			s.refreshPolicy()
		}
	}
}

// patternReportLoop reports pattern statistics periodically.
func (s *AdaptiveSampler) patternReportLoop() {
	ticker := time.NewTicker(10 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			s.reportPatterns()
		}
	}
}

// refreshPolicy fetches the latest sampling policy.
func (s *AdaptiveSampler) refreshPolicy() {
	// Implementation would fetch policy from LipService backend
	// For now, use a default policy
	s.mu.Lock()
	defer s.mu.Unlock()

	s.policy = &SamplingPolicy{
		PolicyID:        "default",
		SamplingRate:    0.1,
		Patterns:        []string{"error", "warning"},
		MaxLogsPerMinute: 1000,
		SeverityRates: map[string]float64{
			"ERROR":   1.0,
			"WARNING": 0.5,
			"INFO":    0.1,
			"DEBUG":   0.05,
		},
	}
	s.lastPolicyUpdate = time.Now()
}

// reportPatterns reports pattern statistics to LipService backend.
func (s *AdaptiveSampler) reportPatterns() {
	s.mu.RLock()
	defer s.mu.RUnlock()

	// Implementation would send pattern stats to LipService backend
	// For now, just log the stats
	fmt.Printf("Reporting %d patterns\n", len(s.patternStats))
}

// computeSignature computes a signature for a log message.
func computeSignature(message string) string {
	// Normalize the message
	normalized := strings.ToLower(strings.TrimSpace(message))

	// Replace common patterns
	patterns := map[string]string{
		`\b\d+\b`:                    "N",
		`[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`: "UUID",
		`\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}`:                        "TIMESTAMP",
		`\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b`:                            "IP",
		`\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`:           "EMAIL",
		`https?://[^\s]+`:                                               "URL",
	}

	for pattern, replacement := range patterns {
		re := regexp.MustCompile(pattern)
		normalized = re.ReplaceAllString(normalized, replacement)
	}

	// Compute MD5 hash
	hash := md5.Sum([]byte(normalized))
	return fmt.Sprintf("%x", hash)
}
