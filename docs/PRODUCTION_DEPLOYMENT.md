# Production Deployment Guide

## Overview
This guide provides comprehensive instructions for deploying the NLP Query Engine to production environments with security, monitoring, and scalability considerations.

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **RAM**: Minimum 8GB, Recommended 16GB+
- **CPU**: Minimum 4 cores, Recommended 8+ cores
- **Storage**: Minimum 100GB SSD, Recommended 500GB+ SSD
- **Network**: Stable internet connection with low latency

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.0+
- curl
- jq
- aws-cli (for S3 backups)

## Security Configuration

### Environment Variables
Create a secure `.env` file with the following variables:

```bash
# Database Security
POSTGRES_PASSWORD=your_very_secure_password_here
REDIS_PASSWORD=your_redis_password_here

# API Security
SECRET_KEY=your_32_character_secret_key_here
MISTRAL_API_KEY=your_mistral_api_key_here

# SSL/TLS
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# Monitoring
GRAFANA_PASSWORD=your_grafana_password_here
```

### SSL/TLS Setup
1. Obtain SSL certificates from a trusted CA
2. Place certificates in `/etc/nginx/ssl/`
3. Update nginx configuration with certificate paths
4. Enable HTTPS redirects

### Firewall Configuration
```bash
# Allow SSH
ufw allow 22

# Allow HTTP/HTTPS
ufw allow 80
ufw allow 443

# Allow internal services (optional)
ufw allow from 172.20.0.0/16

# Enable firewall
ufw enable
```

## Deployment Process

### 1. Initial Setup
```bash
# Clone repository
git clone https://github.com/your-org/nlp-query-engine.git
cd nlp-query-engine

# Set permissions
chmod +x scripts/*.sh

# Create necessary directories
mkdir -p logs backups data
```

### 2. Environment Configuration
```bash
# Copy production environment file
cp env.prod .env

# Edit environment variables
nano .env

# Set secure permissions
chmod 600 .env
```

### 3. SSL Certificate Setup
```bash
# Create SSL directory
sudo mkdir -p /etc/nginx/ssl

# Copy your SSL certificates
sudo cp your-cert.pem /etc/nginx/ssl/cert.pem
sudo cp your-key.pem /etc/nginx/ssl/key.pem

# Set secure permissions
sudo chmod 600 /etc/nginx/ssl/*
sudo chown root:root /etc/nginx/ssl/*
```

### 4. Deploy Services
```bash
# Deploy with backup
./scripts/deploy.sh --backup

# Or deploy without backup (faster)
./scripts/deploy.sh
```

### 5. Verify Deployment
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check health endpoints
curl http://localhost:8000/health
curl http://localhost/health

# Check logs
docker-compose -f docker-compose.prod.yml logs
```

## Monitoring Setup

### Prometheus Configuration
1. Access Prometheus: `http://your-domain:9090`
2. Configure data sources
3. Set up alerting rules
4. Configure notification channels

### Grafana Configuration
1. Access Grafana: `http://your-domain:3001`
2. Login with admin credentials
3. Import dashboards from `monitoring/grafana/dashboards/`
4. Configure data sources

### Log Aggregation
1. Access Kibana: `http://your-domain:5601`
2. Configure index patterns
3. Create visualizations
4. Set up alerts

## Backup and Recovery

### Automated Backups
```bash
# Add to crontab for daily backups
0 2 * * * /path/to/nlp-query-engine/scripts/backup.sh

# Manual backup
./scripts/backup.sh
```

### Backup Configuration
```bash
# S3 backup configuration
export BACKUP_S3_BUCKET=your-backup-bucket
export BACKUP_S3_ACCESS_KEY=your-access-key
export BACKUP_S3_SECRET_KEY=your-secret-key
export BACKUP_S3_REGION=us-east-1
```

### Recovery Process
```bash
# List available backups
ls -la /backups/

# Restore from backup
./scripts/restore.sh nlp_query_engine_20240101_120000.tar.gz

# Restore specific components
./scripts/restore.sh nlp_query_engine_20240101_120000.tar.gz --components postgres,redis
```

## Performance Optimization

### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_employees_department ON employees(department);
CREATE INDEX idx_employees_salary ON employees(salary);
CREATE INDEX idx_employees_hire_date ON employees(hire_date);
```

### Redis Configuration
```bash
# Optimize Redis for production
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

### Application Optimization
```bash
# Set optimal worker processes
export MAX_WORKERS=4
export WORKER_TIMEOUT=300

# Configure connection pooling
export DB_POOL_SIZE=20
export REDIS_POOL_SIZE=20
```

## Scaling Configuration

### Horizontal Scaling
```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

### Load Balancer Configuration
```nginx
# nginx-lb.conf
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

### Auto-scaling
```bash
# Configure auto-scaling
export AUTO_SCALE_ENABLED=true
export MIN_INSTANCES=1
export MAX_INSTANCES=10
export SCALE_UP_THRESHOLD=80
export SCALE_DOWN_THRESHOLD=20
```

## Security Hardening

### Container Security
```bash
# Run containers as non-root
docker-compose -f docker-compose.prod.yml up -d

# Enable security options
security_opt:
  - no-new-privileges:true
```

### Network Security
```bash
# Create isolated network
docker network create --driver bridge nlp-network

# Configure firewall rules
ufw allow from 172.20.0.0/16 to any port 5432
ufw allow from 172.20.0.0/16 to any port 6379
```

### Data Encryption
```bash
# Enable database encryption
export POSTGRES_ENCRYPTION=true

# Enable Redis encryption
export REDIS_ENCRYPTION=true

# Enable ChromaDB encryption
export CHROMA_ENCRYPTION=true
```

## Maintenance Procedures

### Regular Maintenance
```bash
# Weekly maintenance tasks
./scripts/maintenance.sh --weekly

# Monthly maintenance tasks
./scripts/maintenance.sh --monthly

# Database maintenance
./scripts/db-maintenance.sh
```

### Log Rotation
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/nlp-query-engine

# Log rotation configuration
/var/log/nlp-query-engine/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
```

### Health Monitoring
```bash
# Set up health monitoring
./scripts/health-monitor.sh --daemon

# Configure alerts
./scripts/configure-alerts.sh
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs service-name

# Check resource usage
docker stats

# Check disk space
df -h
```

#### Database Connection Issues
```bash
# Test database connection
docker exec nlp-query-postgres-prod psql -U postgres -c "SELECT 1;"

# Check database logs
docker logs nlp-query-postgres-prod
```

#### Performance Issues
```bash
# Check system resources
htop
iostat -x 1
netstat -tulpn

# Check application metrics
curl http://localhost:9090/metrics
```

### Log Analysis
```bash
# View application logs
tail -f logs/backend.log

# Search for errors
grep -i error logs/*.log

# Analyze performance
grep "slow query" logs/*.log
```

## Disaster Recovery

### Recovery Procedures
1. **Database Recovery**: Use PostgreSQL backups
2. **Application Recovery**: Redeploy from source
3. **Data Recovery**: Restore from ChromaDB backups
4. **Configuration Recovery**: Restore from configuration backups

### Recovery Time Objectives
- **RTO**: 4 hours maximum
- **RPO**: 1 hour maximum
- **Backup Frequency**: Daily
- **Retention Period**: 30 days

### Testing Recovery
```bash
# Test backup integrity
./scripts/test-backup.sh

# Test recovery procedures
./scripts/test-recovery.sh

# Simulate disaster scenarios
./scripts/disaster-test.sh
```

## Support and Maintenance

### Monitoring Alerts
- **CPU Usage**: > 80% for 5 minutes
- **Memory Usage**: > 90% for 5 minutes
- **Disk Space**: > 85% for 5 minutes
- **Database Connections**: > 80% for 5 minutes
- **Error Rate**: > 5% for 5 minutes

### Maintenance Windows
- **Weekly**: Sunday 2:00 AM - 4:00 AM
- **Monthly**: First Sunday 2:00 AM - 6:00 AM
- **Emergency**: As needed

### Contact Information
- **Technical Support**: support@your-domain.com
- **Emergency Contact**: +1-555-0123
- **Documentation**: https://docs.your-domain.com

## Compliance and Security

### Security Standards
- **Encryption**: AES-256 for data at rest
- **Transport**: TLS 1.3 for data in transit
- **Authentication**: Multi-factor authentication
- **Access Control**: Role-based access control
- **Audit Logging**: Comprehensive audit trails

### Compliance Requirements
- **GDPR**: Data protection and privacy
- **SOC 2**: Security and availability
- **ISO 27001**: Information security management
- **HIPAA**: Healthcare data protection (if applicable)

### Security Monitoring
- **Intrusion Detection**: Real-time monitoring
- **Vulnerability Scanning**: Weekly scans
- **Penetration Testing**: Quarterly tests
- **Security Audits**: Annual audits

## Performance Benchmarks

### Expected Performance
- **Response Time**: < 2 seconds average
- **Throughput**: 100+ requests per second
- **Concurrent Users**: 50+ simultaneous users
- **Database Queries**: < 1 second average
- **Document Processing**: < 3 seconds per document

### Scaling Limits
- **Maximum Users**: 1000+ concurrent
- **Maximum Documents**: 1M+ documents
- **Maximum Queries**: 10K+ queries per hour
- **Maximum Storage**: 10TB+ total storage

## Conclusion

This production deployment guide provides comprehensive instructions for deploying and maintaining the NLP Query Engine in production environments. Follow these procedures carefully to ensure a secure, scalable, and reliable deployment.

For additional support or questions, please refer to the troubleshooting section or contact the technical support team.

