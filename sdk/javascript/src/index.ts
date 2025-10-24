/**
 * LipService JavaScript/TypeScript SDK
 * 
 * AI-powered intelligent log sampling with PostHog integration
 */

export { configureAdaptiveLogging, getLogger } from './config';
export { LipServiceClient } from './client';
export { LipServiceHandler } from './handler';
export { AdaptiveSampler } from './sampler';
export { PostHogConfig, PostHogHandler, PostHogOTLPExporter, createPostHogHandler } from './posthog';
export { LogContext, SamplingPolicy, PatternStats, SDKConfig } from './models';

// Version
export const VERSION = '0.2.0';
