# 🎙️ LipService JavaScript/TypeScript SDK

> **Reduce logging costs by 50-80% with AI-powered intelligent sampling + PostHog integration**

[![npm](https://img.shields.io/npm/v/@lipservice/sdk)](https://www.npmjs.com/package/@lipservice/sdk)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-16.0+-green)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 🌟 What is LipService SDK?

LipService SDK enables **intelligent, AI-powered log sampling** in your JavaScript/TypeScript applications with **built-in PostHog integration**. It automatically:

- ✅ **Keeps 100% of errors and critical logs** (never lose important data)
- ✅ **Samples repetitive logs at 1-20%** (reduce noise and cost)
- ✅ **Boosts sampling during anomalies** (catch issues early)
- ✅ **Adapts policies automatically** (AI learns your patterns)
- ✅ **Reduces log costs by 50-80%** (while maintaining observability)
- ✅ **Direct PostHog integration** (one-line setup with OTLP)

---

## 🚀 Quick Start

### Installation

```bash
npm install @lipservice/sdk
# or
yarn add @lipservice/sdk
# or
pnpm add @lipservice/sdk
```

### Basic Usage

```typescript
import { configureAdaptiveLogging, getLogger } from '@lipservice/sdk';

// One-line configuration
await configureAdaptiveLogging({
  serviceName: 'my-api',
  lipserviceUrl: 'https://lipservice.company.com'
});

// Use logging as normal - AI handles sampling!
const logger = getLogger('my-module');

await logger.info('user_login', { user_id: 123 }); // Sampled intelligently
await logger.error('payment_failed', { amount: 99.99 }); // Always kept (100%)
```

### PostHog Integration (NEW!)

```typescript
import { configureAdaptiveLogging, getLogger } from '@lipservice/sdk';

// One-line PostHog integration
await configureAdaptiveLogging({
  serviceName: 'my-api',
  lipserviceUrl: 'https://lipservice.company.com',
  posthogApiKey: 'phc_xxx',  // Your PostHog API key
  posthogTeamId: '12345',    // Your PostHog team ID
});

// Logs are intelligently sampled AND sent to PostHog automatically!
const logger = getLogger('my-module');
await logger.info('user_login', { user_id: 123 }); // Sampled + sent to PostHog
await logger.error('payment_failed', { amount: 99.99 }); // Always kept + sent to PostHog
```

**That's it!** Your logs are now intelligently sampled and sent directly to PostHog.

---

## 📖 How It Works

```
Your Application
      ↓
   LipService SDK
   ├── Detect patterns in logs
   ├── Fetch AI sampling policy
   ├── Make sampling decisions
   └── Send sampled logs
      ↓
   PostHog / Log Storage
   (50-80% reduced volume!)
```

### Example: Before vs After

**Without LipService:**
```
1,000,000 logs/day → PostHog → $500/month
```

**With LipService:**
```
1,000,000 logs/day
   ↓ AI sampling (DEBUG: 5%, INFO: 20%, ERROR: 100%)
200,000 logs/day → PostHog → $100/month

💰 Savings: $400/month (80% reduction)
```

---

## 🎯 Features

### 1. **Pattern Detection**
Automatically identifies similar log messages:
```typescript
await logger.info('User 123 logged in');  // Pattern: "User N logged in"
await logger.info('User 456 logged in');  // Same pattern!
```

### 2. **Severity-Based Sampling**
Different rates for different log levels:
- `DEBUG`: 5% (minimal noise)
- `INFO`: 20% (relevant signals)
- `WARNING`: 50% (potential issues)
- `ERROR`: 100% (never miss)
- `CRITICAL`: 100% (always capture)

### 3. **AI Policy Generation**
LipService analyzes your logs and generates intelligent policies:
```json
{
  "global_rate": 0.3,
  "severity_rates": {
    "DEBUG": 0.05,
    "INFO": 0.2,
    "ERROR": 1.0
  },
  "pattern_rates": {
    "abc123": 0.01  // Noisy pattern sampled at 1%
  },
  "anomaly_boost": 3.0  // 3x sampling during anomalies
}
```

### 4. **Automatic Policy Updates**
Policies refresh every 5 minutes, adapting to your application's behavior.

### 5. **Pattern Reporting**
SDK reports pattern statistics back to LipService for continuous improvement.

---

## 🎯 PostHog Integration

### Why PostHog + LipService?

- **PostHog provides:** Log storage, querying, and UI
- **LipService adds:** AI-powered intelligent sampling
- **Together:** 50-80% cost reduction with zero data loss

### PostHog Cloud Integration

```typescript
import { configureAdaptiveLogging, getLogger } from '@lipservice/sdk';

await configureAdaptiveLogging({
  serviceName: 'my-api',
  lipserviceUrl: 'https://lipservice.company.com',
  posthogApiKey: 'phc_xxx',  // From PostHog settings
  posthogTeamId: '12345',    // From PostHog settings
});

const logger = getLogger('my-module');
await logger.info('user_action', { user_id: 123, action: 'login' });
```

### Self-Hosted PostHog Integration

```typescript
await configureAdaptiveLogging({
  serviceName: 'my-api',
  lipserviceUrl: 'https://lipservice.company.com',
  posthogApiKey: 'phc_xxx',
  posthogTeamId: '12345',
  posthogEndpoint: 'https://posthog.company.com',  // Your self-hosted URL
});
```

### PostHog Features

- ✅ **OTLP Protocol:** Uses OpenTelemetry standard
- ✅ **Batch Export:** Efficient log batching
- ✅ **Retry Logic:** Handles network issues gracefully
- ✅ **Authentication:** JWT-based auth with PostHog
- ✅ **Team Isolation:** Proper team ID handling
- ✅ **Error Handling:** Graceful degradation

---

## 🔧 Framework Integrations

### Express.js

```typescript
import express from 'express';
import { configureAdaptiveLogging, getLogger } from '@lipservice/sdk';

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
```

### Next.js

```typescript
// pages/api/hello.ts
import { configureAdaptiveLogging, getLogger } from '@lipservice/sdk';

await configureAdaptiveLogging({
  serviceName: 'nextjs-app',
  lipserviceUrl: 'https://lipservice.company.com',
  posthogApiKey: 'phc_xxx',
  posthogTeamId: '12345',
});

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const logger = getLogger('api');
  await logger.info('api_request', { method: req.method, url: req.url });
  res.status(200).json({ message: 'Hello World' });
}
```

### Winston Integration

```typescript
import winston from 'winston';
import { LipServiceWinstonTransport, getSampler } from '@lipservice/sdk';

const logger = winston.createLogger({
  transports: [
    new LipServiceWinstonTransport(getSampler()),
    new winston.transports.Console(),
  ],
});
```

### Pino Integration

```typescript
import pino from 'pino';
import { LipServicePinoTransport, getSampler } from '@lipservice/sdk';

const logger = pino({
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: true,
    },
  },
});

// Add LipService transport
logger.addTransport(new LipServicePinoTransport(getSampler()));
```

---

## 📚 Advanced Usage

### Custom Context

```typescript
import { LogContext } from '@lipservice/sdk';

const context: LogContext = {
  userId: '123',
  requestId: 'req-456',
  traceId: 'trace-789',
  spanId: 'span-101',
  customFields: {
    environment: 'production',
    version: '1.2.3',
  },
};

await logger.info('user_action', context, { action: 'login' });
```

### Manual Sampler Control

```typescript
import { getSampler } from '@lipservice/sdk';

const sampler = getSampler();

// Get sampling statistics
const stats = sampler?.getStats();
console.log(`Policy version: ${stats?.policyVersion}`);
console.log(`Patterns tracked: ${stats?.patternsTracked}`);

// Force policy refresh
await sampler?.refreshPolicy();

// Force pattern report
await sampler?.reportPatterns();
```

### Graceful Shutdown

```typescript
import { shutdown } from '@lipservice/sdk';

// In your shutdown handler
process.on('SIGINT', async () => {
  await shutdown(); // Reports final patterns
  process.exit(0);
});
```

---

## 🔐 Configuration Options

```typescript
await configureAdaptiveLogging({
  serviceName: 'my-api',                    // Required: Service identifier
  lipserviceUrl: 'https://...',             // Required: LipService API URL
  apiKey: 'optional-key',                    // Optional: API key for auth
  policyRefreshInterval: 300000,            // Milliseconds between policy updates
  patternReportInterval: 600000,            // Milliseconds between pattern reports
  useStructlog: true,                       // Use structured logging (default: true)
  // PostHog integration
  posthogApiKey: 'phc_xxx',                 // PostHog API key
  posthogTeamId: '12345',                   // PostHog team ID
  posthogEndpoint: 'https://app.posthog.com', // PostHog endpoint
  posthogTimeout: 10000,                    // Request timeout
  posthogBatchSize: 100,                    // Batch size
  posthogFlushInterval: 5000,               // Flush interval
  posthogMaxRetries: 3,                     // Max retries
});
```

---

## 🧪 Testing

### Unit Tests

```bash
npm test
```

### With Coverage

```bash
npm run test:coverage
```

---

## 📊 Cost Savings Calculator

Estimate your savings:

| Log Volume/Day | Without LipService | With LipService | Savings |
|----------------|-------------------|----------------|---------|
| 100K logs      | $50/month         | $10/month      | **$40 (80%)** |
| 1M logs        | $500/month        | $100/month     | **$400 (80%)** |
| 10M logs       | $5,000/month      | $1,000/month   | **$4,000 (80%)** |

*Assuming typical log distribution (40% DEBUG, 40% INFO, 15% WARN, 5% ERROR)*

---

## 🔍 FAQ

### Q: Will I lose error logs?
**A: No!** ERROR and CRITICAL logs are ALWAYS sampled at 100%.

### Q: How does pattern detection work?
**A:** We normalize messages by replacing variables (IDs, timestamps, numbers) with placeholders, so similar messages get the same signature.

### Q: What if LipService API is down?
**A:** SDK falls back to 100% sampling (configurable) to ensure no data loss.

### Q: Does this work with existing logging setup?
**A:** Yes! LipService integrates with Winston, Pino, and console logging.

### Q: How often do policies update?
**A:** Every 5 minutes by default (configurable).

---

## 🤝 Support

- **Documentation:** https://github.com/srex-dev/lipservice
- **Issues:** https://github.com/srex-dev/lipservice/issues
- **Discord:** https://discord.gg/lipservice

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built to complement [PostHog](https://posthog.com)'s logging infrastructure with AI-powered cost optimization.

---

**Start saving on logging costs today!** 🚀

```bash
npm install @lipservice/sdk
```
