// Package lipservice provides intelligent log sampling for Go applications.
//
// LipService is an AI-powered logging system that reduces log storage costs
// by 90%+ through intelligent sampling while maintaining full observability.
//
// Features:
//   - AI-powered pattern analysis
//   - Adaptive sampling policies
//   - PostHog OTLP integration
//   - High-performance signature computation
//   - Memory-efficient batch processing
//
// Example usage:
//
//	package main
//
//	import (
//		"context"
//		"log"
//		"time"
//
//		"github.com/srex-dev/lipservice-go"
//	)
//
//	func main() {
//		// Configure LipService
//		config := lipservice.Config{
//			ServiceName: "my-go-service",
//			LipServiceURL: "https://lipservice.company.com",
//			PostHogAPIKey: "phc_xxx",
//			PostHogTeamID: "12345",
//		}
//
//		// Initialize LipService
//		ls, err := lipservice.New(config)
//		if err != nil {
//			log.Fatal(err)
//		}
//		defer ls.Close()
//
//		// Use LipService logger
//		logger := ls.Logger()
//		logger.Info("User logged in", "user_id", 123)
//		logger.Error("Database connection failed", "error", "timeout")
//	}
package lipservice
