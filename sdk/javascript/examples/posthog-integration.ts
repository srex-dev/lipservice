/**
 * PostHog integration example for LipService JavaScript SDK
 */

import { configureAdaptiveLogging, getLogger } from '../src/config';

async function basicPosthogIntegration() {
  console.log('=== Basic PostHog Integration ===');
  
  // One-line configuration with PostHog
  await configureAdaptiveLogging({
    serviceName: 'my-api',
    lipserviceUrl: 'https://lipservice.company.com',
    posthogApiKey: 'phc_xxx',  // Your PostHog API key
    posthogTeamId: '12345',    // Your PostHog team ID
  });
  
  // Get logger and start logging
  const logger = getLogger('example');
  
  // These logs will be intelligently sampled and sent to PostHog
  await logger.info('user_login', { userId: 123, action: 'login' });
  await logger.info('user_login', { userId: 456, action: 'login' }); // Same pattern, sampled together
  await logger.warn('rate_limit_exceeded', { userId: 123, limit: 100 });
  await logger.error('payment_failed', { userId: 123, amount: 99.99 }); // Always kept!
  await logger.debug('cache_hit', { key: 'user:123' }); // Sampled at low rate
  
  console.log('✅ Logs sent to PostHog with intelligent sampling!');
}

async function advancedPosthogIntegration() {
  console.log('\n=== Advanced PostHog Integration ===');
  
  // Advanced configuration
  await configureAdaptiveLogging({
    serviceName: 'ecommerce-api',
    lipserviceUrl: 'https://lipservice.company.com',
    posthogApiKey: 'phc_xxx',
    posthogTeamId: '12345',
    posthogEndpoint: 'https://app.posthog.com', // PostHog Cloud
    policyRefreshInterval: 300000, // Refresh policies every 5 minutes
    patternReportInterval: 600000, // Report patterns every 10 minutes
    posthogBatchSize: 50, // Smaller batches
    posthogFlushInterval: 3000, // Flush every 3 seconds
  });
  
  // Get structured logger
  const logger = getLogger('ecommerce');
  
  // Simulate different types of logs
  const logScenarios = [
    // High-frequency INFO logs (will be heavily sampled)
    { event: 'user_action', context: { userId: 123, action: 'page_view', page: '/products' } },
    { event: 'user_action', context: { userId: 124, action: 'page_view', page: '/products' } },
    { event: 'user_action', context: { userId: 125, action: 'page_view', page: '/products' } },
    
    // WARNING logs (moderate sampling)
    { event: 'rate_limit_warning', context: { userId: 123, limit: 100, current: 95 } },
    { event: 'slow_query', context: { query: 'SELECT * FROM users', duration: 2.5 } },
    
    // ERROR logs (always kept at 100%)
    { event: 'payment_error', context: { userId: 123, error: 'insufficient_funds', amount: 99.99 } },
    { event: 'database_error', context: { error: 'connection_timeout', retryCount: 3 } },
    
    // DEBUG logs (minimal sampling)
    { event: 'cache_debug', context: { key: 'user:123', hit: true } },
    { event: 'performance_debug', context: { function: 'process_order', duration: 0.1 } },
  ];
  
  // Log all scenarios
  for (const scenario of logScenarios) {
    await logger.info(scenario.event, scenario.context);
    await new Promise(resolve => setTimeout(resolve, 100)); // Small delay between logs
  }
  
  console.log('✅ Advanced logging with PostHog integration complete!');
}

async function selfHostedPosthogIntegration() {
  console.log('\n=== Self-Hosted PostHog Integration ===');
  
  // Configuration for self-hosted PostHog
  await configureAdaptiveLogging({
    serviceName: 'internal-api',
    lipserviceUrl: 'https://lipservice.company.com',
    posthogApiKey: 'phc_xxx',
    posthogTeamId: '67890',
    posthogEndpoint: 'https://posthog.company.com', // Self-hosted endpoint
  });
  
  const logger = getLogger('internal');
  
  // Log to self-hosted PostHog
  await logger.info('deployment_started', { version: '1.2.3', environment: 'production' });
  await logger.info('health_check', { service: 'api', status: 'healthy' });
  await logger.warn('high_memory_usage', { service: 'api', usagePercent: 85 });
  await logger.error('service_unavailable', { service: 'database', error: 'connection_failed' });
  
  console.log('✅ Logs sent to self-hosted PostHog!');
}

async function costSavingsDemonstration() {
  console.log('\n=== Cost Savings Demonstration ===');
  
  await configureAdaptiveLogging({
    serviceName: 'high-volume-api',
    lipserviceUrl: 'https://lipservice.company.com',
    posthogApiKey: 'phc_xxx',
    posthogTeamId: '12345',
  });
  
  const logger = getLogger('high-volume');
  
  // Simulate high-volume logging
  console.log('Simulating high-volume logging...');
  
  // Generate 1000 logs with different patterns
  for (let i = 0; i < 1000; i++) {
    if (i % 10 === 0) {
      // ERROR logs (always kept)
      await logger.error('critical_error', { errorId: i, message: 'Something went wrong' });
    } else if (i % 5 === 0) {
      // WARNING logs (moderate sampling)
      await logger.warn('performance_warning', { requestId: i, duration: 2.5 });
    } else {
      // INFO logs (heavy sampling)
      await logger.info('request_processed', { requestId: i, userId: i % 100 });
    }
  }
  
  console.log('✅ Generated 1000 logs with intelligent sampling!');
  console.log('📊 Expected cost reduction: 50-80%');
  console.log('🛡️ All ERROR logs preserved (100%)');
}

async function frameworkIntegrationExamples() {
  console.log('\n=== Framework Integration Examples ===');
  
  // Express.js example
  console.log('Express.js Integration:');
  console.log(`
  const express = require('express');
  const { configureAdaptiveLogging, getLogger } = require('@lipservice/sdk');
  
  const app = express();
  
  // Configure LipService with PostHog
  await configureAdaptiveLogging({
    serviceName: 'express-app',
    lipserviceUrl: 'https://lipservice.company.com',
    posthogApiKey: 'phc_xxx',
    posthogTeamId: '12345',
  });
  
  app.get('/', async (req, res) => {
    const logger = getLogger('api');
    await logger.info('endpoint_hit', { endpoint: '/', method: 'GET' });
    res.json({ message: 'Hello World' });
  });
  `);
  
  // Next.js example
  console.log('\nNext.js Integration:');
  console.log(`
  // pages/api/hello.js
  import { configureAdaptiveLogging, getLogger } from '@lipservice/sdk';
  
  await configureAdaptiveLogging({
    serviceName: 'nextjs-app',
    lipserviceUrl: 'https://lipservice.company.com',
    posthogApiKey: 'phc_xxx',
    posthogTeamId: '12345',
  });
  
  export default async function handler(req, res) {
    const logger = getLogger('api');
    await logger.info('api_request', { method: req.method, url: req.url });
    res.status(200).json({ message: 'Hello World' });
  }
  `);
  
  // Winston integration
  console.log('\nWinston Integration:');
  console.log(`
  const winston = require('winston');
  const { LipServiceWinstonTransport, getSampler } = require('@lipservice/sdk');
  
  const logger = winston.createLogger({
    transports: [
      new LipServiceWinstonTransport(getSampler()),
      new winston.transports.Console(),
    ],
  });
  `);
}

async function main() {
  console.log('🎙️ LipService + PostHog Integration Examples');
  console.log('='.repeat(50));
  
  try {
    // Run synchronous examples
    await basicPosthogIntegration();
    await advancedPosthogIntegration();
    await selfHostedPosthogIntegration();
    await costSavingsDemonstration();
    await frameworkIntegrationExamples();
    
    console.log('\n🎉 All PostHog integration examples completed!');
    console.log('\nKey Benefits:');
    console.log('✅ 50-80% cost reduction on log storage');
    console.log('✅ Zero data loss (ERROR logs always kept)');
    console.log('✅ One-line PostHog integration');
    console.log('✅ Intelligent pattern-based sampling');
    console.log('✅ Real-time policy updates');
    console.log('✅ Works with PostHog Cloud and self-hosted');
    
  } catch (error) {
    console.error('❌ Demo failed:', error);
    console.log('💡 Make sure you have the required dependencies installed:');
    console.log('   npm install @lipservice/sdk');
  }
}

if (require.main === module) {
  main().catch(console.error);
}

export {
  basicPosthogIntegration,
  advancedPosthogIntegration,
  selfHostedPosthogIntegration,
  costSavingsDemonstration,
  frameworkIntegrationExamples,
};
