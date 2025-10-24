/**
 * Logging handler for integrating with existing logging libraries
 */

import { AdaptiveSampler } from './sampler';
import { LogContext } from './models';

export interface LogRecord {
  level: string;
  message: string;
  timestamp: Date;
  context?: LogContext;
  attributes?: Record<string, any>;
}

export class LipServiceHandler {
  constructor(
    private sampler: AdaptiveSampler,
    private downstreamHandler?: (record: LogRecord) => void
  ) {}

  /**
   * Handle a log record with intelligent sampling
   */
  handle(record: LogRecord): void {
    try {
      // Make sampling decision
      const decision = this.sampler.shouldSample(record.message, record.level);

      // Add metadata to record
      const enhancedRecord: LogRecord = {
        ...record,
        attributes: {
          ...record.attributes,
          lipservice_signature: decision.signature,
          lipservice_sampled: decision.shouldSample,
          lipservice_rate: decision.rate,
          lipservice_reason: decision.reason,
        },
      };

      // Forward to downstream handler if sampled
      if (decision.shouldSample && this.downstreamHandler) {
        this.downstreamHandler(enhancedRecord);
      }
    } catch (error) {
      console.error('LipServiceHandler error:', error);
    }
  }
}

/**
 * Winston transport for LipService
 */
export class LipServiceWinstonTransport {
  private handler: LipServiceHandler;

  constructor(sampler: AdaptiveSampler) {
    this.handler = new LipServiceHandler(sampler);
  }

  log(info: any, callback: () => void): void {
    const record: LogRecord = {
      level: info.level,
      message: info.message,
      timestamp: new Date(info.timestamp || Date.now()),
      context: info.context,
      attributes: info.meta || {},
    };

    this.handler.handle(record);
    callback();
  }
}

/**
 * Pino transport for LipService
 */
export class LipServicePinoTransport {
  private handler: LipServiceHandler;

  constructor(sampler: AdaptiveSampler) {
    this.handler = new LipServiceHandler(sampler);
  }

  write(log: any): void {
    const record: LogRecord = {
      level: log.level >= 50 ? 'ERROR' : log.level >= 40 ? 'WARN' : log.level >= 30 ? 'INFO' : 'DEBUG',
      message: log.msg || log.message || '',
      timestamp: new Date(log.time),
      context: log.context,
      attributes: log,
    };

    this.handler.handle(record);
  }
}

/**
 * Console transport for LipService
 */
export class LipServiceConsoleTransport {
  private handler: LipServiceHandler;
  private originalConsole: {
    log: typeof console.log;
    warn: typeof console.warn;
    error: typeof console.error;
    debug: typeof console.debug;
  };

  constructor(sampler: AdaptiveSampler) {
    this.handler = new LipServiceHandler(sampler);
    this.originalConsole = {
      log: console.log,
      warn: console.warn,
      error: console.error,
      debug: console.debug,
    };
  }

  /**
   * Install console interceptors
   */
  install(): void {
    console.log = (...args: any[]) => {
      this.handleLog('INFO', args);
    };

    console.warn = (...args: any[]) => {
      this.handleLog('WARNING', args);
    };

    console.error = (...args: any[]) => {
      this.handleLog('ERROR', args);
    };

    console.debug = (...args: any[]) => {
      this.handleLog('DEBUG', args);
    };
  }

  /**
   * Uninstall console interceptors
   */
  uninstall(): void {
    console.log = this.originalConsole.log;
    console.warn = this.originalConsole.warn;
    console.error = this.originalConsole.error;
    console.debug = this.originalConsole.debug;
  }

  private handleLog(level: string, args: any[]): void {
    const message = args.map(arg => 
      typeof arg === 'string' ? arg : JSON.stringify(arg)
    ).join(' ');

    const record: LogRecord = {
      level,
      message,
      timestamp: new Date(),
      attributes: { args },
    };

    this.handler.handle(record);
  }
}
