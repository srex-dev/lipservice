/**
 * PostHog OTLP exporter for LipService JavaScript SDK
 */

import axios, { AxiosInstance } from 'axios';
import { LogContext } from './models';

export interface PostHogConfig {
  apiKey: string;
  teamId: string;
  endpoint: string;
  timeout: number;
  batchSize: number;
  flushInterval: number;
  maxRetries: number;
}

export interface LogRecord {
  timeUnixNano: number;
  severityText: string;
  severityNumber: number;
  body: string;
  attributes: Record<string, string>;
}

export class PostHogOTLPExporter {
  private config: PostHogConfig;
  private client: AxiosInstance;
  private batch: LogRecord[] = [];
  private isRunning: boolean = false;
  private flushTimer?: NodeJS.Timeout;

  constructor(config: PostHogConfig) {
    this.config = config;
    this.client = axios.create({
      baseURL: config.endpoint.replace(/\/$/, ''),
      headers: {
        'Content-Type': 'application/x-protobuf',
        'Authorization': `Bearer ${config.apiKey}`,
        'X-PostHog-Team-Id': config.teamId,
      },
      timeout: config.timeout,
    });
  }

  /**
   * Start the exporter
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      return;
    }

    this.isRunning = true;
    
    // Start flush timer
    this.flushTimer = setInterval(() => {
      this.flushBatch().catch(console.error);
    }, this.config.flushInterval);

    console.info('PostHogOTLPExporter started');
  }

  /**
   * Stop the exporter
   */
  async stop(): Promise<void> {
    if (!this.isRunning) {
      return;
    }

    this.isRunning = false;

    // Clear timer
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = undefined;
    }

    // Flush remaining logs
    if (this.batch.length > 0) {
      await this.flushBatch();
    }

    console.info('PostHogOTLPExporter stopped');
  }

  /**
   * Export a log record
   */
  async exportLog(
    message: string,
    severity: string,
    timestamp: Date,
    context?: LogContext,
    attributes: Record<string, any> = {}
  ): Promise<void> {
    const logRecord = this.createLogRecord(message, severity, timestamp, context, attributes);
    
    this.batch.push(logRecord);

    // Flush if batch is full
    if (this.batch.length >= this.config.batchSize) {
      await this.flushBatch();
    }
  }

  /**
   * Create a log record
   */
  private createLogRecord(
    message: string,
    severity: string,
    timestamp: Date,
    context?: LogContext,
    attributes: Record<string, any> = {}
  ): LogRecord {
    const timestampNano = timestamp.getTime() * 1_000_000;
    const severityNumber = this.getSeverityNumber(severity);

    const recordAttributes: Record<string, string> = {
      severity_text: severity,
      severity_number: severityNumber.toString(),
    };

    // Add context attributes
    if (context) {
      if (context.userId) recordAttributes['context.user_id'] = context.userId;
      if (context.requestId) recordAttributes['context.request_id'] = context.requestId;
      if (context.traceId) recordAttributes['context.trace_id'] = context.traceId;
      if (context.spanId) recordAttributes['context.span_id'] = context.spanId;
      
      if (context.customFields) {
        Object.entries(context.customFields).forEach(([key, value]) => {
          recordAttributes[`context.${key}`] = String(value);
        });
      }
    }

    // Add additional attributes
    Object.entries(attributes).forEach(([key, value]) => {
      recordAttributes[key] = String(value);
    });

    return {
      timeUnixNano: timestampNano,
      severityText: severity,
      severityNumber,
      body: message,
      attributes: recordAttributes,
    };
  }

  /**
   * Get severity number for OTLP
   */
  private getSeverityNumber(severity: string): number {
    const severityMap: Record<string, number> = {
      'TRACE': 1,
      'DEBUG': 5,
      'INFO': 9,
      'WARN': 13,
      'WARNING': 13,
      'ERROR': 17,
      'FATAL': 21,
      'CRITICAL': 21,
    };
    
    return severityMap[severity.toUpperCase()] || 9; // Default to INFO
  }

  /**
   * Flush the current batch
   */
  private async flushBatch(): Promise<void> {
    if (this.batch.length === 0) {
      return;
    }

    const batchToSend = [...this.batch];
    this.batch = [];

    // Create OTLP request (simplified JSON format for now)
    const request = this.createOTLPRequest(batchToSend);

    // Send with retries
    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      try {
        await this.client.post('/api/v1/otlp/v1/logs', request);
        console.info(`Logs exported: ${batchToSend.length} records`);
        return;
      } catch (error: any) {
        const status = error.response?.status;
        
        if (status && [429, 502, 503, 504].includes(status)) {
          // Retryable error
          if (attempt < this.config.maxRetries) {
            const waitTime = Math.pow(2, attempt) * 1000; // Exponential backoff
            console.warn(`Export retry ${attempt + 1}/${this.config.maxRetries}, waiting ${waitTime}ms`);
            await new Promise(resolve => setTimeout(resolve, waitTime));
            continue;
          }
        }
        
        console.error(`Export failed: ${error.message}`);
        break;
      }
    }
  }

  /**
   * Create OTLP request (simplified JSON format)
   */
  private createOTLPRequest(logRecords: LogRecord[]): any {
    return {
      resourceLogs: [{
        resource: {
          attributes: [
            { key: 'service.name', value: { stringValue: 'lipservice-sdk' } },
            { key: 'service.version', value: { stringValue: '0.2.0' } },
          ],
        },
        scopeLogs: [{
          scope: {
            name: 'lipservice',
            version: '0.2.0',
          },
          logRecords: logRecords.map(record => ({
            timeUnixNano: record.timeUnixNano,
            severityText: record.severityText,
            severityNumber: record.severityNumber,
            body: { stringValue: record.body },
            attributes: Object.entries(record.attributes).map(([key, value]) => ({
              key,
              value: { stringValue: value },
            })),
          })),
        }],
      }],
    };
  }
}

/**
 * Create a PostHog handler
 */
export function createPostHogHandler(config: PostHogConfig): PostHogHandler {
  return new PostHogHandler(config);
}

/**
 * PostHog logging handler
 */
export class PostHogHandler {
  private exporter: PostHogOTLPExporter;
  private isStarted: boolean = false;

  constructor(private config: PostHogConfig) {
    this.exporter = new PostHogOTLPExporter(config);
  }

  /**
   * Handle a log record
   */
  async handleLog(
    message: string,
    severity: string,
    timestamp: Date,
    context?: LogContext,
    attributes: Record<string, any> = {}
  ): Promise<void> {
    // Start exporter if not started
    if (!this.isStarted) {
      await this.exporter.start();
      this.isStarted = true;
    }

    await this.exporter.exportLog(message, severity, timestamp, context, attributes);
  }

  /**
   * Close the handler
   */
  async close(): Promise<void> {
    if (this.isStarted) {
      await this.exporter.stop();
      this.isStarted = false;
    }
  }
}
