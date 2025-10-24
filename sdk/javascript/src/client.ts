/**
 * LipService API client for fetching policies and reporting patterns
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { SamplingPolicy, PatternStats } from './models';

export class LipServiceClient {
  private client: AxiosInstance;
  private serviceName: string;

  constructor(
    baseUrl: string,
    serviceName: string,
    apiKey?: string,
    timeout: number = 10000
  ) {
    this.serviceName = serviceName;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (apiKey) {
      headers['Authorization'] = `Bearer ${apiKey}`;
    }

    this.client = axios.create({
      baseURL: baseUrl.replace(/\/$/, ''),
      headers,
      timeout,
    });
  }

  /**
   * Fetch active sampling policy for this service
   */
  async getActivePolicy(): Promise<SamplingPolicy | null> {
    try {
      const response: AxiosResponse = await this.client.get(
        `/api/v1/policies/${this.serviceName}`
      );

      const data = response.data;

      return {
        version: data.version,
        globalRate: data.global_rate,
        severityRates: data.severity_rates || {},
        patternRates: data.pattern_rates || {},
        anomalyBoost: data.anomaly_boost || 2.0,
        reasoning: data.reasoning,
        createdAt: data.created_at ? new Date(data.created_at) : undefined,
      };
    } catch (error: any) {
      if (error.response?.status === 404) {
        console.info(`No policy found for service: ${this.serviceName}`);
        return null;
      }
      
      console.error(`Policy fetch failed for service ${this.serviceName}:`, error.message);
      return null;
    }
  }

  /**
   * Report pattern statistics to LipService
   */
  async reportPatterns(patterns: PatternStats[]): Promise<boolean> {
    if (!patterns || patterns.length === 0) {
      return true;
    }

    try {
      const payload = {
        service_name: this.serviceName,
        patterns: patterns.map(p => ({
          signature: p.signature,
          message_sample: p.messageSample,
          count: p.count,
          severity_distribution: p.severityDistribution,
          first_seen: p.firstSeen.toISOString(),
          last_seen: p.lastSeen.toISOString(),
        })),
      };

      await this.client.post('/api/v1/patterns/stats', payload);
      
      console.info(`Patterns reported for service ${this.serviceName}: ${patterns.length} patterns`);
      return true;
    } catch (error: any) {
      console.error(`Pattern report failed for service ${this.serviceName}:`, error.message);
      return false;
    }
  }

  /**
   * Close the HTTP client
   */
  async close(): Promise<void> {
    // Axios doesn't have a close method, but we can clear the instance
    this.client = axios.create();
  }
}
