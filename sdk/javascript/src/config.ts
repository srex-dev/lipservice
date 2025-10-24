/**
 * Configuration and setup for LipService JavaScript SDK
 */

import { LipServiceClient } from './client';
import { AdaptiveSampler } from './sampler';
import { PostHogHandler, createPostHogHandler, PostHogConfig } from './posthog';
import { SDKConfig, LogContext } from './models';

// Global state
let globalSampler: AdaptiveSampler | null = null;
let globalClient: LipServiceClient | null = null;
let globalConfig: SDKConfig | null = null;
let posthogHandler: PostHogHandler | null = null;

/**
 * Configure LipService adaptive logging
 */
export async function configureAdaptiveLogging(config: {
  serviceName: string;
  lipserviceUrl: string;
  apiKey?: string;
  policyRefreshInterval?: number;
  patternReportInterval?: number;
  useStructlog?: boolean;
  // PostHog integration
  posthogApiKey?: string;
  posthogTeamId?: string;
  posthogEndpoint?: string;
  posthogTimeout?: number;
  posthogBatchSize?: number;
  posthogFlushInterval?: number;
  posthogMaxRetries?: number;
}): Promise<void> {
  // Create SDK configuration
  globalConfig = {
    serviceName: config.serviceName,
    lipserviceUrl: config.lipserviceUrl,
    apiKey: config.apiKey,
    policyRefreshInterval: config.policyRefreshInterval || 300000, // 5 minutes
    patternReportInterval: config.patternReportInterval || 600000, // 10 minutes
    enablePatternDetection: true,
    enablePolicySampling: true,
    fallbackSampleRate: 1.0,
    maxPatternCacheSize: 10000,
  };

  // Create client
  globalClient = new LipServiceClient(
    config.lipserviceUrl,
    config.serviceName,
    config.apiKey
  );

  // Create sampler
  globalSampler = new AdaptiveSampler(
    globalClient,
    globalConfig.policyRefreshInterval,
    globalConfig.patternReportInterval
  );

  // Start sampler
  await globalSampler.start();

  // Create PostHog handler if configured
  if (config.posthogApiKey && config.posthogTeamId) {
    const posthogConfig: PostHogConfig = {
      apiKey: config.posthogApiKey,
      teamId: config.posthogTeamId,
      endpoint: config.posthogEndpoint || 'https://app.posthog.com',
      timeout: config.posthogTimeout || 10000,
      batchSize: config.posthogBatchSize || 100,
      flushInterval: config.posthogFlushInterval || 5000,
      maxRetries: config.posthogMaxRetries || 3,
    };

    posthogHandler = createPostHogHandler(posthogConfig);
    console.info(`PostHog handler created for team ${config.posthogTeamId}`);
  }

  console.info(`LipService configured for service: ${config.serviceName}`);
}

/**
 * Get a logger instance
 */
export function getLogger(name?: string): Logger {
  return new Logger(name);
}

/**
 * Logger class with intelligent sampling
 */
export class Logger {
  constructor(private name?: string) {}

  /**
   * Log an info message
   */
  async info(message: string, context?: LogContext, attributes: Record<string, any> = {}): Promise<void> {
    await this.log('INFO', message, context, attributes);
  }

  /**
   * Log a warning message
   */
  async warn(message: string, context?: LogContext, attributes: Record<string, any> = {}): Promise<void> {
    await this.log('WARNING', message, context, attributes);
  }

  /**
   * Log an error message
   */
  async error(message: string, context?: LogContext, attributes: Record<string, any> = {}): Promise<void> {
    await this.log('ERROR', message, context, attributes);
  }

  /**
   * Log a debug message
   */
  async debug(message: string, context?: LogContext, attributes: Record<string, any> = {}): Promise<void> {
    await this.log('DEBUG', message, context, attributes);
  }

  /**
   * Log a message with intelligent sampling
   */
  private async log(
    severity: string,
    message: string,
    context?: LogContext,
    attributes: Record<string, any> = {}
  ): Promise<void> {
    if (!globalSampler) {
      console.warn('LipService not configured. Call configureAdaptiveLogging() first.');
      return;
    }

    // Make sampling decision
    const decision = globalSampler.shouldSample(message, severity);

    // Add metadata to attributes
    const logAttributes = {
      ...attributes,
      lipservice_signature: decision.signature,
      lipservice_sampled: decision.shouldSample,
      lipservice_rate: decision.rate,
      lipservice_reason: decision.reason,
      logger_name: this.name || 'unknown',
    };

    // Send to PostHog if configured and sampled
    if (posthogHandler && decision.shouldSample) {
      try {
        await posthogHandler.handleLog(
          message,
          severity,
          new Date(),
          context,
          logAttributes
        );
      } catch (error) {
        console.error('PostHog export failed:', error);
      }
    }

    // Also log to console for development
    if (process.env.NODE_ENV === 'development' || !posthogHandler) {
      const timestamp = new Date().toISOString();
      const logMessage = `[${timestamp}] ${severity} ${this.name ? `[${this.name}]` : ''} ${message}`;
      
      if (decision.shouldSample) {
        console.log(logMessage, logAttributes);
      } else {
        console.debug(`[SAMPLED OUT] ${logMessage}`, logAttributes);
      }
    }
  }
}

/**
 * Get the global sampler instance
 */
export function getSampler(): AdaptiveSampler | null {
  return globalSampler;
}

/**
 * Get the global client instance
 */
export function getClient(): LipServiceClient | null {
  return globalClient;
}

/**
 * Get the global configuration
 */
export function getConfig(): SDKConfig | null {
  return globalConfig;
}

/**
 * Shutdown LipService gracefully
 */
export async function shutdown(): Promise<void> {
  if (globalSampler) {
    await globalSampler.stop();
    globalSampler = null;
  }

  if (globalClient) {
    await globalClient.close();
    globalClient = null;
  }

  if (posthogHandler) {
    await posthogHandler.close();
    posthogHandler = null;
  }

  globalConfig = null;
  console.info('LipService shutdown complete');
}
