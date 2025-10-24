/**
 * Adaptive sampler for intelligent log sampling
 */

import { LipServiceClient } from './client';
import { SamplingPolicy, PatternStats, SamplingDecision } from './models';
import { computeSignature } from './signature';

export class AdaptiveSampler {
  private client: LipServiceClient;
  private policy: SamplingPolicy | null = null;
  private patternCache: Map<string, PatternStats> = new Map();
  private policyRefreshInterval: number;
  private patternReportInterval: number;
  private isRunning: boolean = false;
  private refreshTimer?: NodeJS.Timeout;
  private reportTimer?: NodeJS.Timeout;

  constructor(
    client: LipServiceClient,
    policyRefreshInterval: number = 300000, // 5 minutes
    patternReportInterval: number = 600000  // 10 minutes
  ) {
    this.client = client;
    this.policyRefreshInterval = policyRefreshInterval;
    this.patternReportInterval = patternReportInterval;
  }

  /**
   * Start the sampler background tasks
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      return;
    }

    this.isRunning = true;
    
    // Initial policy fetch
    await this.refreshPolicy();
    
    // Start background timers
    this.refreshTimer = setInterval(() => {
      this.refreshPolicy().catch(console.error);
    }, this.policyRefreshInterval);

    this.reportTimer = setInterval(() => {
      this.reportPatterns().catch(console.error);
    }, this.patternReportInterval);

    console.info('AdaptiveSampler started');
  }

  /**
   * Stop the sampler
   */
  async stop(): Promise<void> {
    if (!this.isRunning) {
      return;
    }

    this.isRunning = false;

    // Clear timers
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = undefined;
    }

    if (this.reportTimer) {
      clearInterval(this.reportTimer);
      this.reportTimer = undefined;
    }

    // Final pattern report
    await this.reportPatterns();

    console.info('AdaptiveSampler stopped');
  }

  /**
   * Make a sampling decision for a log message
   */
  shouldSample(message: string, severity: string): SamplingDecision {
    // Always sample ERROR and CRITICAL logs
    if (severity.toUpperCase() === 'ERROR' || severity.toUpperCase() === 'CRITICAL') {
      return {
        shouldSample: true,
        signature: computeSignature(message),
        rate: 1.0,
        reason: 'Error/Critical logs always sampled',
      };
    }

    // Generate signature
    const signature = computeSignature(message);

    // Update pattern cache
    this.updatePatternCache(signature, message, severity);

    // Get sampling rate
    const rate = this.getSamplingRate(severity, signature);

    // Make sampling decision
    const shouldSample = Math.random() < rate;

    return {
      shouldSample,
      signature,
      rate,
      reason: `Sampling rate: ${(rate * 100).toFixed(1)}%`,
    };
  }

  /**
   * Get sampling statistics
   */
  getStats(): Record<string, any> {
    return {
      policyVersion: this.policy?.version || 0,
      patternsTracked: this.patternCache.size,
      isRunning: this.isRunning,
      policyRefreshInterval: this.policyRefreshInterval,
      patternReportInterval: this.patternReportInterval,
    };
  }

  /**
   * Refresh the sampling policy
   */
  async refreshPolicy(): Promise<void> {
    try {
      const newPolicy = await this.client.getActivePolicy();
      if (newPolicy) {
        this.policy = newPolicy;
        console.info(`Policy refreshed: version ${newPolicy.version}`);
      }
    } catch (error) {
      console.error('Policy refresh failed:', error);
    }
  }

  /**
   * Report pattern statistics
   */
  async reportPatterns(): Promise<void> {
    if (this.patternCache.size === 0) {
      return;
    }

    try {
      const patterns = Array.from(this.patternCache.values());
      await this.client.reportPatterns(patterns);
      
      // Clear cache after successful report
      this.patternCache.clear();
    } catch (error) {
      console.error('Pattern report failed:', error);
    }
  }

  /**
   * Get sampling rate for severity and pattern
   */
  private getSamplingRate(severity: string, signature: string): number {
    if (!this.policy) {
      return 1.0; // Default to 100% if no policy
    }

    // Check pattern-specific rate first
    const patternRate = this.policy.patternRates[signature];
    if (patternRate !== undefined) {
      return patternRate;
    }

    // Check severity-specific rate
    const severityRate = this.policy.severityRates[severity.toUpperCase()];
    if (severityRate !== undefined) {
      return severityRate;
    }

    // Fall back to global rate
    return this.policy.globalRate;
  }

  /**
   * Update pattern cache with new log entry
   */
  private updatePatternCache(signature: string, message: string, severity: string): void {
    const existing = this.patternCache.get(signature);
    
    if (existing) {
      existing.count++;
      existing.severityDistribution[severity] = (existing.severityDistribution[severity] || 0) + 1;
      existing.lastSeen = new Date();
    } else {
      this.patternCache.set(signature, {
        signature,
        messageSample: message.substring(0, 200), // Truncate long messages
        count: 1,
        severityDistribution: { [severity]: 1 },
        firstSeen: new Date(),
        lastSeen: new Date(),
      });
    }
  }
}
