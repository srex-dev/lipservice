# 🚀 LipService Production Deployment Guide

**Version:** 1.0  
**Date:** October 24, 2025  
**Status:** ✅ **PRODUCTION READY**

---

## 🎯 Overview

This guide provides comprehensive instructions for deploying LipService to production environments with high availability, security, and performance.

---

## 📋 Prerequisites

### System Requirements
- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 8GB+ (16GB+ recommended)
- **Storage**: 100GB+ SSD (500GB+ recommended)
- **Network**: 1Gbps+ bandwidth
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+

### Software Requirements
- **Python**: 3.11+
- **PostgreSQL**: 13+
- **Redis**: 6+
- **Docker**: 20.10+
- **Kubernetes**: 1.24+ (optional)
- **Nginx**: 1.18+ (optional)

### External Services
- **PostHog**: Cloud or self-hosted instance
- **OpenAI API**: For AI-powered sampling (optional)
- **Monitoring**: Prometheus + Grafana (recommended)

---

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   LipService    │    │   PostHog       │
│   (Nginx)       │───▶│   Backend      │───▶│   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   Database      │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Redis Cache   │
                       └─────────────────┘
```

---

## 🔧 Installation Methods

### Method 1: Docker Compose (Recommended for Small-Medium Deployments)

#### 1. Clone Repository
```bash
git clone https://github.com/srex-dev/lipservice.git
cd lipservice
```

#### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

#### 3. Start Services
```bash
docker-compose up -d
```

#### 4. Initialize Database
```bash
docker-compose exec backend alembic upgrade head
```

#### 5. Verify Installation
```bash
curl http://localhost:8000/health
```

### Method 2: Kubernetes (Recommended for Large Deployments)

#### 1. Create Namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: lipservice
```

#### 2. Deploy PostgreSQL
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: lipservice
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:13
        env:
        - name: POSTGRES_DB
          value: lipservice
        - name: POSTGRES_USER
          value: lipservice
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

#### 3. Deploy Redis
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: lipservice
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:6-alpine
        ports:
        - containerPort: 6379
```

#### 4. Deploy LipService Backend
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lipservice-backend
  namespace: lipservice
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lipservice-backend
  template:
    metadata:
      labels:
        app: lipservice-backend
    spec:
      containers:
      - name: backend
        image: lipservice/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: POSTHOG_API_KEY
          valueFrom:
            secretKeyRef:
              name: posthog-secret
              key: api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 5. Deploy Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: lipservice-service
  namespace: lipservice
spec:
  selector:
    app: lipservice-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Method 3: Manual Installation

#### 1. Install Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-pip postgresql-13 redis-server nginx

# CentOS/RHEL
sudo yum install python311 python311-pip postgresql13-server redis nginx
```

#### 2. Setup Database
```bash
sudo -u postgres createdb lipservice
sudo -u postgres createuser lipservice
sudo -u postgres psql -c "ALTER USER lipservice PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE lipservice TO lipservice;"
```

#### 3. Install LipService
```bash
git clone https://github.com/srex-dev/lipservice.git
cd lipservice
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Configure Environment
```bash
export DATABASE_URL="postgresql://lipservice:your_password@localhost/lipservice"
export REDIS_URL="redis://localhost:6379"
export POSTHOG_API_KEY="your_posthog_api_key"
export SECRET_KEY="your_secret_key"
```

#### 5. Initialize Database
```bash
alembic upgrade head
```

#### 6. Start Services
```bash
# Start Redis
sudo systemctl start redis

# Start LipService
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## 🔐 Security Configuration

### 1. SSL/TLS Setup

#### Using Let's Encrypt
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Using Custom Certificates
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Firewall Configuration

#### UFW (Ubuntu)
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### Firewalld (CentOS/RHEL)
```bash
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 3. Database Security

#### PostgreSQL Configuration
```postgresql
# /etc/postgresql/13/main/postgresql.conf
listen_addresses = 'localhost'
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'

# /etc/postgresql/13/main/pg_hba.conf
local   all             all                                     peer
host    all             all             127.0.0.1/32            md5
hostssl all             all             127.0.0.1/32            md5
```

---

## 📊 Monitoring & Observability

### 1. Prometheus Configuration

#### prometheus.yml
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'lipservice'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
    scrape_interval: 5s
```

### 2. Grafana Dashboards

#### Key Metrics to Monitor
- **Request Rate**: Requests per second
- **Response Time**: P50, P95, P99 latencies
- **Error Rate**: 4xx and 5xx error rates
- **Database Connections**: Active connections
- **Memory Usage**: RAM utilization
- **CPU Usage**: CPU utilization
- **Disk Usage**: Storage utilization

### 3. Alerting Rules

#### Prometheus Alert Rules
```yaml
groups:
- name: lipservice
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
```

---

## 🔄 Backup & Recovery

### 1. Database Backup

#### Automated Backup Script
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/lipservice"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="lipservice"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h localhost -U lipservice $DB_NAME > $BACKUP_DIR/lipservice_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/lipservice_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "lipservice_*.sql.gz" -mtime +30 -delete

echo "Backup completed: lipservice_$DATE.sql.gz"
```

#### Cron Job
```bash
# Add to crontab
0 2 * * * /path/to/backup.sh
```

### 2. Configuration Backup

#### Backup Script
```bash
#!/bin/bash
# config_backup.sh

CONFIG_DIR="/etc/lipservice"
BACKUP_DIR="/backups/config"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/lipservice_config_$DATE.tar.gz $CONFIG_DIR

# Keep only last 7 days
find $BACKUP_DIR -name "lipservice_config_*.tar.gz" -mtime +7 -delete
```

---

## 🚀 Performance Optimization

### 1. Database Optimization

#### PostgreSQL Tuning
```postgresql
# postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

#### Index Optimization
```sql
-- Create indexes for common queries
CREATE INDEX idx_logs_service_timestamp ON log_entries(service_id, timestamp);
CREATE INDEX idx_logs_level ON log_entries(level);
CREATE INDEX idx_patterns_signature ON pattern_stats(signature);
CREATE INDEX idx_policies_service ON sampling_policies(service_id);
```

### 2. Application Optimization

#### Gunicorn Configuration
```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
keepalive = 2
timeout = 30
```

#### Redis Optimization
```redis
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U lipservice -d lipservice

# Check logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

#### 2. High Memory Usage
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Check for memory leaks
python -m memory_profiler your_script.py
```

#### 3. Slow Response Times
```bash
# Check database performance
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Check slow queries
sudo -u postgres psql -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Log Analysis

#### Application Logs
```bash
# Check application logs
tail -f /var/log/lipservice/app.log

# Check error logs
grep "ERROR" /var/log/lipservice/app.log | tail -20
```

#### System Logs
```bash
# Check system logs
sudo journalctl -u lipservice -f

# Check nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 📞 Support & Maintenance

### Support Channels
- **Documentation**: https://docs.lipservice.com
- **GitHub Issues**: https://github.com/srex-dev/lipservice/issues
- **Discord**: https://discord.gg/lipservice
- **Email**: support@lipservice.com

### Maintenance Schedule
- **Daily**: Monitor system health and logs
- **Weekly**: Review performance metrics and alerts
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and update backup procedures

---

## ✅ Production Checklist

### Pre-Deployment
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Backup procedures tested
- [ ] Monitoring configured
- [ ] SSL certificates installed
- [ ] Firewall configured
- [ ] Database optimized
- [ ] Documentation updated

### Post-Deployment
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Backup jobs running
- [ ] Performance metrics baseline
- [ ] Security scanning completed
- [ ] Team training completed
- [ ] Support procedures documented

---

**Deployment Status**: ✅ **PRODUCTION READY**  
**Last Updated**: October 24, 2025  
**Next Review**: January 24, 2026
