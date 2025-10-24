# 🚀 LipService Beta User Onboarding Guide

**Welcome to the LipService Beta Testing Program!**

This guide will help you get started with LipService SDK and integrate it into your application to achieve 50-80% cost reduction on your PostHog logging costs.

---

## 🎯 What is LipService?

LipService is an AI-powered intelligent log sampling system that:
- ✅ **Reduces logging costs by 50-80%** while maintaining observability
- ✅ **Keeps 100% of ERROR and CRITICAL logs** (never lose important data)
- ✅ **Uses AI to intelligently sample** repetitive logs at 1-20%
- ✅ **Integrates seamlessly with PostHog** via OTLP protocol
- ✅ **Works with your existing logging** setup (no changes required)

---

## 📋 Pre-Flight Checklist

Before starting, please verify:

- [ ] **Python 3.11+** installed
- [ ] **PostHog account** with API key and team ID
- [ ] **Application using Python logging** (Django, FastAPI, Flask, etc.)
- [ ] **Current log volume** > 1,000 logs/day
- [ ] **PostHog costs** > $50/month
- [ ] **Technical team** available for integration

---

## 🚀 Quick Start (5 minutes)

### Step 1: Install LipService SDK

```bash
pip install lipservice-sdk
```

### Step 2: Configure LipService

```python
from lipservice import configure_adaptive_logging, get_logger

# One-line configuration with PostHog integration
await configure_adaptive_logging(
    service_name='your-app-name',
    lipservice_url='https://lipservice.company.com',  # Beta backend URL
    posthog_api_key='phc_your_api_key',               # Your PostHog API key
    posthog_team_id='your_team_id',                  # Your PostHog team ID
)

# Get logger and start logging
logger = get_logger('your-module')
await logger.info('User logged in', {'user_id': 123})  # Sampled + sent to PostHog!
```

### Step 3: Test Integration

```python
# Test different log levels
await logger.info('Application started', {'version': '1.0.0'})
await logger.warn('High memory usage', {'usage': 85})
await logger.error('Database connection failed', {'error': 'timeout'})  # Always kept!
await logger.debug('Cache hit', {'key': 'user:123'})  # Sampled at low rate
```

**That's it!** Your logs are now intelligently sampled and sent to PostHog.

---

## 🔧 Framework-Specific Integration

### Django Integration

```python
# settings.py
import asyncio
from lipservice import configure_adaptive_logging

# Configure LipService
asyncio.run(configure_adaptive_logging(
    service_name='django-app',
    lipservice_url='https://lipservice.company.com',
    posthog_api_key='phc_your_api_key',
    posthog_team_id='your_team_id',
))

# views.py
from lipservice import get_logger

logger = get_logger('django.views')

def my_view(request):
    logger.info('View accessed', {'user': request.user.id})
    return HttpResponse('Hello World')
```

### FastAPI Integration

```python
# main.py
from fastapi import FastAPI
from lipservice import configure_adaptive_logging, get_logger
import asyncio

app = FastAPI()

# Configure LipService
asyncio.run(configure_adaptive_logging(
    service_name='fastapi-app',
    lipservice_url='https://lipservice.company.com',
    posthog_api_key='phc_your_api_key',
    posthog_team_id='your_team_id',
))

logger = get_logger('fastapi.app')

@app.get("/")
async def root():
    logger.info('API endpoint hit', {'endpoint': '/'})
    return {"message": "Hello World"}
```

### Flask Integration

```python
# app.py
from flask import Flask
from lipservice import configure_adaptive_logging, get_logger
import asyncio

app = Flask(__name__)

# Configure LipService
asyncio.run(configure_adaptive_logging(
    service_name='flask-app',
    lipservice_url='https://lipservice.company.com',
    posthog_api_key='phc_your_api_key',
    posthog_team_id='your_team_id',
))

logger = get_logger('flask.app')

@app.route('/')
def hello():
    logger.info('Route accessed', {'route': '/'})
    return 'Hello World!'
```

---

## 📊 Monitoring Your Integration

### PostHog Dashboard

1. **Log in to PostHog** and navigate to your project
2. **Check the Logs section** to see sampled logs
3. **Monitor log volume** reduction over time
4. **Verify ERROR logs** are still at 100%

### LipService Dashboard

1. **Access the beta dashboard** at `https://lipservice.company.com/dashboard`
2. **View cost savings** in real-time
3. **Monitor sampling policies** and AI decisions
4. **Track performance metrics**

### Key Metrics to Monitor

- **Log Volume Reduction**: Should see 50-80% reduction
- **Cost Savings**: Monitor PostHog billing for savings
- **Error Rate**: Should remain 0% (no data loss)
- **Performance**: Should maintain or improve response times

---

## 🛠️ Configuration Options

### Basic Configuration

```python
await configure_adaptive_logging(
    service_name='your-app',                    # Required: Your app name
    lipservice_url='https://lipservice.company.com',  # Required: Beta backend URL
    posthog_api_key='phc_your_api_key',         # Required: PostHog API key
    posthog_team_id='your_team_id',            # Required: PostHog team ID
)
```

### Advanced Configuration

```python
await configure_adaptive_logging(
    service_name='your-app',
    lipservice_url='https://lipservice.company.com',
    posthog_api_key='phc_your_api_key',
    posthog_team_id='your_team_id',
    
    # Policy and pattern settings
    policy_refresh_interval=300,               # Refresh policies every 5 minutes
    pattern_report_interval=600,               # Report patterns every 10 minutes
    
    # PostHog settings
    posthog_endpoint='https://app.posthog.com', # PostHog endpoint
    posthog_batch_size=100,                    # Batch size for efficiency
    posthog_flush_interval=5000,               # Flush every 5 seconds
    
    # Sampling settings
    fallback_sample_rate=1.0,                  # Fallback rate if no policy
    max_pattern_cache_size=10000,              # Max patterns to track
)
```

---

## 🔍 Testing Your Integration

### Test Scenarios

1. **Basic Logging Test**
   ```python
   logger = get_logger('test')
   await logger.info('Test message', {'test': True})
   ```

2. **High Volume Test**
   ```python
   for i in range(1000):
       await logger.info(f'High volume test {i}', {'iteration': i})
   ```

3. **Error Logging Test**
   ```python
   await logger.error('Test error', {'error': 'test'})  # Should always be kept
   ```

4. **Pattern Detection Test**
   ```python
   # These should be detected as the same pattern
   await logger.info('User 123 logged in', {'user_id': 123})
   await logger.info('User 456 logged in', {'user_id': 456})
   ```

### Validation Checklist

- [ ] **Logs appear in PostHog** within 5 minutes
- [ ] **ERROR logs are kept at 100%** (no sampling)
- [ ] **INFO logs are sampled** (reduced volume)
- [ ] **Pattern detection works** (similar messages grouped)
- [ ] **Performance is maintained** (no latency increase)
- [ ] **Cost savings visible** in PostHog billing

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Logs not appearing in PostHog
**Symptoms**: Logs not visible in PostHog dashboard
**Solutions**:
- Check PostHog API key and team ID
- Verify network connectivity
- Check PostHog endpoint URL
- Review error logs for authentication issues

#### 2. High memory usage
**Symptoms**: Application memory usage increases
**Solutions**:
- Reduce `max_pattern_cache_size`
- Increase `pattern_report_interval`
- Check for memory leaks in your application

#### 3. Performance degradation
**Symptoms**: Application response times increase
**Solutions**:
- Increase `posthog_batch_size`
- Increase `posthog_flush_interval`
- Check network latency to PostHog

#### 4. Configuration errors
**Symptoms**: SDK fails to start or configure
**Solutions**:
- Verify all required parameters
- Check parameter types and values
- Review error messages in logs

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

await configure_adaptive_logging(
    service_name='your-app',
    lipservice_url='https://lipservice.company.com',
    posthog_api_key='phc_your_api_key',
    posthog_team_id='your_team_id',
    # ... other settings
)
```

---

## 📞 Support and Help

### Beta Support Channels

1. **Slack**: `#lipservice-beta` for real-time support
2. **Email**: `beta-support@lipservice.com` for formal support
3. **GitHub Issues**: For bug reports and feature requests
4. **Video Calls**: Weekly check-ins and troubleshooting

### Support Response Times

- **Critical Issues**: 2 hours
- **High Priority**: 4 hours
- **Medium Priority**: 24 hours
- **Low Priority**: 72 hours

### Emergency Contacts

- **Critical Issues**: +1-XXX-XXX-XXXX
- **24/7 Support**: support@lipservice.com
- **Escalation**: escalation@lipservice.com

---

## 📊 Beta Testing Requirements

### What We Need From You

1. **Weekly Check-ins**: 30-minute weekly calls
2. **Feedback Surveys**: Weekly feedback collection
3. **Issue Reporting**: Report bugs and issues promptly
4. **Performance Data**: Share performance metrics
5. **Cost Savings Data**: Track and report cost savings

### What You Get

1. **Free Usage**: 6 months free LipService usage
2. **Priority Support**: Dedicated support channel
3. **Early Access**: Access to new features
4. **Cost Savings**: Immediate 50-80% cost reduction
5. **Influence**: Direct input on product development

---

## 📈 Success Metrics

### Key Performance Indicators

- **Cost Savings**: Target 50-80% reduction
- **Performance**: Maintain <100ms latency impact
- **Reliability**: 99.9% uptime
- **User Satisfaction**: 8+ rating (out of 10)

### Monitoring Dashboard

Access your personalized dashboard at:
`https://lipservice.company.com/dashboard/your-team-id`

Track:
- Real-time cost savings
- Log volume reduction
- Performance metrics
- Sampling decisions
- Error rates

---

## 🎯 Next Steps

### Week 1: Basic Integration
- [ ] Install and configure LipService SDK
- [ ] Integrate with your application
- [ ] Test basic logging functionality
- [ ] Verify PostHog integration

### Week 2: Production Testing
- [ ] Deploy to staging environment
- [ ] Run load tests
- [ ] Monitor performance impact
- [ ] Validate cost savings

### Week 3: Production Deployment
- [ ] Deploy to production
- [ ] Monitor for 48 hours
- [ ] Collect baseline metrics
- [ ] Report initial results

### Week 4+: Ongoing Monitoring
- [ ] Weekly check-ins
- [ ] Performance monitoring
- [ ] Cost savings tracking
- [ ] Feedback collection

---

## 🎉 Welcome to the Beta Program!

Thank you for participating in the LipService Beta Testing Program. We're excited to work with you to validate our AI-powered intelligent log sampling solution.

**Remember**: You're not just testing a product - you're helping shape the future of intelligent logging and cost optimization.

Let's make logging smarter together! 🚀

---

**Need Help?** Contact us at `beta-support@lipservice.com` or join our Slack workspace at `#lipservice-beta`.

**Beta Program Duration**: 7 weeks  
**Next Check-in**: [Schedule will be sent separately]  
**Support**: Available 24/7 for critical issues
