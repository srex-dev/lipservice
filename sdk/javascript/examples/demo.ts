/**
 * Simple demo script for LipService JavaScript SDK
 */

import { configureAdaptiveLogging, getLogger, shutdown } from './src/config';

async function demo() {
  console.log('🎙️ LipService JavaScript SDK Demo');
  console.log('=====================================\n');

  try {
    // Configure LipService with PostHog integration
    console.log('📡 Configuring LipService...');
    await configureAdaptiveLogging({
      serviceName: 'demo-app',
      lipserviceUrl: 'http://localhost:8000', // Replace with your LipService backend URL
      posthogApiKey: process.env.POSTHOG_API_KEY || 'phc_test_api_key',
      posthogTeamId: process.env.POSTHOG_TEAM_ID || '12345',
      posthogEndpoint: process.env.POSTHOG_ENDPOINT || 'http://localhost:8000/api/v1/otlp/v1/logs',
      policyRefreshInterval: 10000, // 10 seconds for demo
      patternReportInterval: 20000,  // 20 seconds for demo
    });

    console.log('✅ LipService configured successfully!\n');

    // Get logger
    const logger = getLogger('demo');

    // Log various types of messages
    console.log('📝 Logging sample messages...\n');

    // High-frequency INFO logs (will be sampled)
    await logger.info('User logged in', { userId: 'user-123', sessionId: 'sess-abc' });
    await logger.info('User logged in', { userId: 'user-456', sessionId: 'sess-def' });
    await logger.info('User logged in', { userId: 'user-789', sessionId: 'sess-ghi' });

    // WARNING logs (moderate sampling)
    await logger.warn('High CPU usage detected', { cpuPercent: 85, threshold: 80 });
    await logger.warn('Memory usage high', { memoryPercent: 90, threshold: 85 });

    // ERROR logs (always kept at 100%)
    await logger.error('Database connection failed', { 
      dbHost: 'localhost', 
      port: 5432, 
      errorCode: 500 
    });
    await logger.error('Payment processing failed', { 
      userId: 'user-123', 
      amount: 99.99, 
      error: 'insufficient_funds' 
    });

    // DEBUG logs (minimal sampling)
    await logger.debug('Cache hit for user data', { userId: 'user-123', cacheKey: 'user:123' });
    await logger.debug('Background task completed', { taskId: 'task-789', duration: 0.1 });

    console.log('✅ Sample messages logged!\n');

    // Simulate some activity over time
    console.log('⏰ Simulating activity over time...');
    for (let i = 0; i < 5; i++) {
      await logger.info('Heartbeat signal', { iteration: i, timestamp: new Date().toISOString() });
      await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
    }

    console.log('✅ Activity simulation complete!\n');

    // Log a critical message
    await logger.error('System going down for maintenance', { 
      reason: 'urgent_patch', 
      estimatedDowntime: '5 minutes' 
    });

    console.log('🎉 Demo completed successfully!\n');

    console.log('📊 What happened:');
    console.log('• INFO logs were intelligently sampled (same patterns grouped)');
    console.log('• WARNING logs were moderately sampled');
    console.log('• ERROR logs were kept at 100% (never lose important data)');
    console.log('• DEBUG logs were minimally sampled');
    console.log('• All sampled logs were sent to PostHog via OTLP');
    console.log('• Pattern statistics were reported to LipService\n');

    console.log('💰 Expected cost savings: 50-80% reduction in log storage costs!');

  } catch (error) {
    console.error('❌ Demo failed:', error);
    console.log('\n💡 Make sure you have:');
    console.log('1. LipService backend running on http://localhost:8000');
    console.log('2. PostHog API key and team ID configured');
    console.log('3. Required dependencies installed: npm install');
  } finally {
    // Graceful shutdown
    console.log('\n🛑 Shutting down LipService...');
    await shutdown();
    console.log('✅ Shutdown complete!');
  }
}

// Run demo if this file is executed directly
if (require.main === module) {
  demo().catch(console.error);
}

export { demo };
