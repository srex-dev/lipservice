/**
 * Pattern signature generation for log messages
 */

import * as crypto from 'crypto';

/**
 * Generate a signature for a log message by normalizing variables
 */
export function computeSignature(message: string): string {
  if (!message || typeof message !== 'string') {
    return '';
  }

  // Normalize the message by replacing common variable patterns
  let normalized = message
    // Replace UUIDs (8-4-4-4-12 format)
    .replace(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, 'UUID')
    // Replace UUIDs (32 hex chars)
    .replace(/[0-9a-f]{32}/gi, 'UUID')
    // Replace numbers (including decimals)
    .replace(/\b\d+\.?\d*\b/g, 'N')
    // Replace timestamps (ISO format)
    .replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?/g, 'TIMESTAMP')
    // Replace IP addresses
    .replace(/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, 'IP')
    // Replace email addresses
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, 'EMAIL')
    // Replace URLs
    .replace(/https?:\/\/[^\s]+/g, 'URL')
    // Replace file paths
    .replace(/[A-Za-z]:\\[^\\]+/g, 'PATH')
    .replace(/\/[^\/]+/g, 'PATH')
    // Replace common ID patterns
    .replace(/\b(id|ID|Id)\s*[:=]\s*\w+/gi, '$1:ID')
    // Replace session IDs
    .replace(/\b(session|Session)\s*[:=]\s*\w+/gi, '$1:SESSION')
    // Replace user IDs
    .replace(/\b(user|User)\s*[:=]\s*\w+/gi, '$1:USER')
    // Replace request IDs
    .replace(/\b(request|Request)\s*[:=]\s*\w+/gi, '$1:REQUEST')
    // Replace trace IDs
    .replace(/\b(trace|Trace)\s*[:=]\s*\w+/gi, '$1:TRACE')
    // Replace span IDs
    .replace(/\b(span|Span)\s*[:=]\s*\w+/gi, '$1:SPAN')
    // Replace common variable patterns
    .replace(/\$\{[^}]+\}/g, 'VAR')
    .replace(/\{\w+\}/g, 'VAR')
    // Replace quoted strings that look like IDs
    .replace(/"[A-Za-z0-9_-]{8,}"/g, '"ID"')
    .replace(/'[A-Za-z0-9_-]{8,}'/g, "'ID'")
    // Replace common hash patterns
    .replace(/\b[a-f0-9]{40,}\b/g, 'HASH')
    // Replace common token patterns
    .replace(/\b[A-Za-z0-9_-]{20,}\b/g, 'TOKEN')
    // Clean up extra spaces
    .replace(/\s+/g, ' ')
    .trim();

  // Generate MD5 hash of normalized message
  return crypto.createHash('md5').update(normalized).digest('hex');
}

/**
 * Extract error type from log message
 */
export function extractErrorType(message: string): string | null {
  if (!message || typeof message !== 'string') {
    return null;
  }

  // Common error patterns
  const errorPatterns = [
    /Error:\s*(\w+)/i,
    /Exception:\s*(\w+)/i,
    /(\w+Error)/i,
    /(\w+Exception)/i,
    /(\w+Timeout)/i,
    /(\w+Failed)/i,
    /(\w+Rejected)/i,
    /(\w+Denied)/i,
    /(\w+NotFound)/i,
    /(\w+Unauthorized)/i,
    /(\w+Forbidden)/i,
    /(\w+Conflict)/i,
    /(\w+BadRequest)/i,
    /(\w+InternalError)/i,
    /(\w+ServiceUnavailable)/i,
  ];

  for (const pattern of errorPatterns) {
    const match = message.match(pattern);
    if (match) {
      return match[1];
    }
  }

  return null;
}

/**
 * Check if a message looks like an error
 */
export function isErrorMessage(message: string): boolean {
  if (!message || typeof message !== 'string') {
    return false;
  }

  const errorKeywords = [
    'error', 'exception', 'failed', 'failure', 'timeout',
    'rejected', 'denied', 'unauthorized', 'forbidden',
    'not found', 'notfound', 'conflict', 'bad request',
    'internal error', 'service unavailable', 'crashed',
    'panic', 'fatal', 'critical', 'emergency'
  ];

  const lowerMessage = message.toLowerCase();
  return errorKeywords.some(keyword => lowerMessage.includes(keyword));
}
