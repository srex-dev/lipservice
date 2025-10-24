/**
 * Test suite for LipService JavaScript SDK
 */

import { configureAdaptiveLogging, getLogger, shutdown } from '../src/config';
import { LipServiceClient } from '../src/client';
import { AdaptiveSampler } from '../src/sampler';
import { PostHogOTLPExporter, PostHogHandler, createPostHogHandler } from '../src/posthog';
import { computeSignature, extractErrorType, isErrorMessage } from '../src/signature';
import { LipServiceHandler, LipServiceWinstonTransport, LipServicePinoTransport } from '../src/handler';

describe('LipService SDK', () => {
  beforeEach(async () => {
    // Clean up after each test
    await shutdown();
  });

  describe('Signature Generation', () => {
    test('should normalize UUIDs', () => {
      const message = 'User 123e4567-e89b-12d3-a456-426614174000 logged in';
      const signature = computeSignature(message);
      expect(signature).toBe(computeSignature('User UUID logged in'));
    });

    test('should normalize numbers', () => {
      const message = 'Processing request 12345 with amount 99.99';
      const signature = computeSignature(message);
      expect(signature).toBe(computeSignature('Processing request N with amount N'));
    });

    test('should normalize timestamps', () => {
      const message = 'Request at 2023-12-01T10:30:00Z completed';
      const signature = computeSignature(message);
      expect(signature).toBe(computeSignature('Request at TIMESTAMP completed'));
    });

    test('should normalize IP addresses', () => {
      const message = 'Request from 192.168.1.1 processed';
      const signature = computeSignature(message);
      expect(signature).toBe(computeSignature('Request from IP processed'));
    });

    test('should normalize email addresses', () => {
      const message = 'Email sent to user@example.com';
      const signature = computeSignature(message);
      expect(signature).toBe(computeSignature('Email sent to EMAIL'));
    });

    test('should normalize URLs', () => {
      const message = 'Request to https://api.example.com/v1/users';
      const signature = computeSignature(message);
      expect(signature).toBe(computeSignature('Request to URL'));
    });

    test('should normalize file paths', () => {
      const message = 'File /home/user/data.txt processed';
      const signature = computeSignature(message);
      expect(signature).toBe(computeSignature('File PATH processed'));
    });

    test('should normalize common ID patterns', () => {
      const message = 'User ID: abc123def456 processed';
      const signature = computeSignature(message);
      expect(signature).toBe(computeSignature('User ID: ID processed'));
    });

    test('should handle empty message', () => {
      const signature = computeSignature('');
      expect(signature).toBe('');
    });

    test('should handle null message', () => {
      const signature = computeSignature(null as any);
      expect(signature).toBe('');
    });
  });

  describe('Error Detection', () => {
    test('should detect error types', () => {
      expect(extractErrorType('Error: ConnectionTimeout')).toBe('ConnectionTimeout');
      expect(extractErrorType('Exception: DatabaseError')).toBe('DatabaseError');
      expect(extractErrorType('PaymentError occurred')).toBe('PaymentError');
      expect(extractErrorType('RequestTimeout')).toBe('RequestTimeout');
      expect(extractErrorType('AccessDenied')).toBe('AccessDenied');
    });

    test('should detect error messages', () => {
      expect(isErrorMessage('Database connection failed')).toBe(true);
      expect(isErrorMessage('User authentication error')).toBe(true);
      expect(isErrorMessage('Service timeout occurred')).toBe(true);
      expect(isErrorMessage('Access denied for user')).toBe(true);
      expect(isErrorMessage('System crashed unexpectedly')).toBe(true);
      expect(isErrorMessage('User logged in successfully')).toBe(false);
      expect(isErrorMessage('Cache hit')).toBe(false);
    });

    test('should handle case insensitive detection', () => {
      expect(isErrorMessage('ERROR: Something went wrong')).toBe(true);
      expect(isErrorMessage('Exception occurred')).toBe(true);
      expect(isErrorMessage('FATAL: System failure')).toBe(true);
    });
  });

  describe('LipService Client', () => {
    test('should create client with correct configuration', () => {
      const client = new LipServiceClient('https://api.example.com', 'test-service', 'test-key');
      expect(client).toBeDefined();
    });

    test('should handle policy fetch failure gracefully', async () => {
      const client = new LipServiceClient('https://invalid-url', 'test-service');
      const policy = await client.getActivePolicy();
      expect(policy).toBeNull();
    });

    test('should handle pattern report failure gracefully', async () => {
      const client = new LipServiceClient('https://invalid-url', 'test-service');
      const result = await client.reportPatterns([]);
      expect(result).toBe(false);
    });
  });

  describe('Adaptive Sampler', () => {
    test('should always sample error logs', () => {
      const client = new LipServiceClient('https://api.example.com', 'test-service');
      const sampler = new AdaptiveSampler(client);
      
      const decision = sampler.shouldSample('Database error occurred', 'ERROR');
      expect(decision.shouldSample).toBe(true);
      expect(decision.rate).toBe(1.0);
      expect(decision.reason).toBe('Error/Critical logs always sampled');
    });

    test('should always sample critical logs', () => {
      const client = new LipServiceClient('https://api.example.com', 'test-service');
      const sampler = new AdaptiveSampler(client);
      
      const decision = sampler.shouldSample('System going down', 'CRITICAL');
      expect(decision.shouldSample).toBe(true);
      expect(decision.rate).toBe(1.0);
    });

    test('should generate consistent signatures', () => {
      const client = new LipServiceClient('https://api.example.com', 'test-service');
      const sampler = new AdaptiveSampler(client);
      
      const decision1 = sampler.shouldSample('User 123 logged in', 'INFO');
      const decision2 = sampler.shouldSample('User 456 logged in', 'INFO');
      
      expect(decision1.signature).toBe(decision2.signature);
    });

    test('should track pattern statistics', () => {
      const client = new LipServiceClient('https://api.example.com', 'test-service');
      const sampler = new AdaptiveSampler(client);
      
      // Generate some logs
      sampler.shouldSample('User 123 logged in', 'INFO');
      sampler.shouldSample('User 456 logged in', 'INFO');
      sampler.shouldSample('User 789 logged in', 'INFO');
      
      const stats = sampler.getStats();
      expect(stats.patternsTracked).toBe(1); // Same pattern
    });

    test('should start and stop correctly', async () => {
      const client = new LipServiceClient('https://api.example.com', 'test-service');
      const sampler = new AdaptiveSampler(client);
      
      await sampler.start();
      expect(sampler.getStats().isRunning).toBe(true);
      
      await sampler.stop();
      expect(sampler.getStats().isRunning).toBe(false);
    });
  });

  describe('PostHog OTLP Exporter', () => {
    test('should create exporter with correct configuration', () => {
      const config = {
        apiKey: 'test-key',
        teamId: 'test-team',
        endpoint: 'https://app.posthog.com',
        timeout: 10000,
        batchSize: 100,
        flushInterval: 5000,
        maxRetries: 3,
      };
      
      const exporter = new PostHogOTLPExporter(config);
      expect(exporter).toBeDefined();
    });

    test('should map severity levels correctly', () => {
      const config = {
        apiKey: 'test-key',
        teamId: 'test-team',
        endpoint: 'https://app.posthog.com',
        timeout: 10000,
        batchSize: 100,
        flushInterval: 5000,
        maxRetries: 3,
      };
      
      const exporter = new PostHogOTLPExporter(config);
      
      // Test severity mapping (using private method via any)
      const severityNumber = (exporter as any).getSeverityNumber('ERROR');
      expect(severityNumber).toBe(17);
      
      const debugNumber = (exporter as any).getSeverityNumber('DEBUG');
      expect(debugNumber).toBe(5);
      
      const infoNumber = (exporter as any).getSeverityNumber('INFO');
      expect(infoNumber).toBe(9);
    });

    test('should start and stop correctly', async () => {
      const config = {
        apiKey: 'test-key',
        teamId: 'test-team',
        endpoint: 'https://app.posthog.com',
        timeout: 10000,
        batchSize: 100,
        flushInterval: 5000,
        maxRetries: 3,
      };
      
      const exporter = new PostHogOTLPExporter(config);
      
      await exporter.start();
      await exporter.stop();
      
      // Should not throw
      expect(true).toBe(true);
    });
  });

  describe('PostHog Handler', () => {
    test('should create handler with correct configuration', () => {
      const config = {
        apiKey: 'test-key',
        teamId: 'test-team',
        endpoint: 'https://app.posthog.com',
        timeout: 10000,
        batchSize: 100,
        flushInterval: 5000,
        maxRetries: 3,
      };
      
      const handler = createPostHogHandler(config);
      expect(handler).toBeDefined();
    });

    test('should handle log records', async () => {
      const config = {
        apiKey: 'test-key',
        teamId: 'test-team',
        endpoint: 'https://app.posthog.com',
        timeout: 10000,
        batchSize: 100,
        flushInterval: 5000,
        maxRetries: 3,
      };
      
      const handler = createPostHogHandler(config);
      
      // Should not throw
      await handler.handleLog('Test message', 'INFO', new Date());
      await handler.close();
      
      expect(true).toBe(true);
    });
  });

  describe('Logging Handler', () => {
    test('should create handler with sampler', () => {
      const client = new LipServiceClient('https://api.example.com', 'test-service');
      const sampler = new AdaptiveSampler(client);
      const handler = new LipServiceHandler(sampler);
      
      expect(handler).toBeDefined();
    });

    test('should handle log records', () => {
      const client = new LipServiceClient('https://api.example.com', 'test-service');
      const sampler = new AdaptiveSampler(client);
      const handler = new LipServiceHandler(sampler);
      
      const record = {
        level: 'INFO',
        message: 'Test message',
        timestamp: new Date(),
        attributes: { test: 'value' },
      };
      
      // Should not throw
      handler.handle(record);
      expect(true).toBe(true);
    });
  });

  describe('Winston Transport', () => {
    test('should create Winston transport', () => {
      const client = new LipServiceClient('https://api.example.com', 'test-service');
      const sampler = new AdaptiveSampler(client);
      const transport = new LipServiceWinstonTransport(sampler);
      
      expect(transport).toBeDefined();
    });

    test('should handle Winston log info', () => {
      const client = new LipServiceClient('https://api.example.com', 'test-service');
      const sampler = new AdaptiveSampler(client);
      const transport = new LipServiceWinstonTransport(sampler);
      
      const info = {
        level: 'info',
        message: 'Test message',
        timestamp: new Date().toISOString(),
        meta: { test: 'value' },
      };
      
      // Should not throw
      transport.log(info, () => {});
      expect(true).toBe(true);
    });
  });

  describe('Pino Transport', () => {
    test('should create Pino transport', () => {
      const client = new LipServiceClient('https://api.example.com', 'test-service');
      const sampler = new AdaptiveSampler(client);
      const transport = new LipServicePinoTransport(sampler);
      
      expect(transport).toBeDefined();
    });

    test('should handle Pino log', () => {
      const client = new LipServiceClient('https://api.example.com', 'test-service');
      const sampler = new AdaptiveSampler(client);
      const transport = new LipServicePinoTransport(sampler);
      
      const log = {
        level: 30, // INFO level
        msg: 'Test message',
        time: Date.now(),
        test: 'value',
      };
      
      // Should not throw
      transport.write(log);
      expect(true).toBe(true);
    });
  });

  describe('SDK Configuration', () => {
    test('should configure SDK without PostHog', async () => {
      await configureAdaptiveLogging({
        serviceName: 'test-service',
        lipserviceUrl: 'https://api.example.com',
      });
      
      const logger = getLogger('test');
      expect(logger).toBeDefined();
    });

    test('should configure SDK with PostHog', async () => {
      await configureAdaptiveLogging({
        serviceName: 'test-service',
        lipserviceUrl: 'https://api.example.com',
        posthogApiKey: 'test-key',
        posthogTeamId: 'test-team',
      });
      
      const logger = getLogger('test');
      expect(logger).toBeDefined();
    });

    test('should handle logging without configuration', async () => {
      const logger = getLogger('test');
      
      // Should not throw, but should warn
      await logger.info('Test message');
      expect(true).toBe(true);
    });
  });

  describe('Logger', () => {
    test('should create logger with name', () => {
      const logger = getLogger('test-module');
      expect(logger).toBeDefined();
    });

    test('should handle different log levels', async () => {
      const logger = getLogger('test');
      
      // Should not throw
      await logger.info('Info message');
      await logger.warn('Warning message');
      await logger.error('Error message');
      await logger.debug('Debug message');
      
      expect(true).toBe(true);
    });

    test('should handle context and attributes', async () => {
      const logger = getLogger('test');
      
      const context = {
        userId: '123',
        requestId: 'req-456',
        customFields: { environment: 'test' },
      };
      
      const attributes = { action: 'login', timestamp: Date.now() };
      
      // Should not throw
      await logger.info('User action', context, attributes);
      expect(true).toBe(true);
    });
  });

  describe('Integration Tests', () => {
    test('should handle full logging flow', async () => {
      await configureAdaptiveLogging({
        serviceName: 'integration-test',
        lipserviceUrl: 'https://api.example.com',
        posthogApiKey: 'test-key',
        posthogTeamId: 'test-team',
      });
      
      const logger = getLogger('integration');
      
      // Generate various log types
      await logger.info('User 123 logged in', { userId: '123' });
      await logger.info('User 456 logged in', { userId: '456' }); // Same pattern
      await logger.warn('High memory usage', { usage: 85 });
      await logger.error('Database connection failed', { error: 'timeout' });
      await logger.debug('Cache hit', { key: 'user:123' });
      
      expect(true).toBe(true);
    });

    test('should handle shutdown gracefully', async () => {
      await configureAdaptiveLogging({
        serviceName: 'shutdown-test',
        lipserviceUrl: 'https://api.example.com',
      });
      
      const logger = getLogger('shutdown');
      await logger.info('Before shutdown');
      
      await shutdown();
      
      // Should not throw after shutdown
      await logger.info('After shutdown');
      expect(true).toBe(true);
    });
  });
});
