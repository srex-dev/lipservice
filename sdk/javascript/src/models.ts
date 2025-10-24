/**
 * Data models for LipService SDK
 */

export interface SamplingPolicy {
  version: number;
  globalRate: number;
  severityRates: Record<string, number>;
  patternRates: Record<string, number>;
  anomalyBoost: number;
  reasoning?: string;
  createdAt?: Date;
}

export interface PatternStats {
  signature: string;
  messageSample: string;
  count: number;
  severityDistribution: Record<string, number>;
  firstSeen: Date;
  lastSeen: Date;
}

export interface LogContext {
  userId?: string;
  requestId?: string;
  traceId?: string;
  spanId?: string;
  customFields?: Record<string, any>;
}

export interface SDKConfig {
  serviceName: string;
  lipserviceUrl: string;
  apiKey?: string;
  policyRefreshInterval: number;
  patternReportInterval: number;
  enablePatternDetection: boolean;
  enablePolicySampling: boolean;
  fallbackSampleRate: number;
  maxPatternCacheSize: number;
}

export interface PostHogConfig {
  apiKey: string;
  teamId: string;
  endpoint: string;
  timeout: number;
  batchSize: number;
  flushInterval: number;
  maxRetries: number;
}

export interface SamplingDecision {
  shouldSample: boolean;
  signature: string;
  rate: number;
  reason: string;
}
