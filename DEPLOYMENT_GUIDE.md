# Ruby GEM Estimator - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Ruby GEM Estimator system with enhanced resolver capabilities, confidence indicators, and monitoring dashboard.

## System Requirements

### Hardware Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB minimum for application and database
- **Network**: Stable internet connection for Google AI API calls

### Software Requirements
- **Python**: 3.8 or higher
- **PostgreSQL**: 12.0 or higher
- **Operating System**: Linux, macOS, or Windows

## Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Python 3.8+ installed
- [ ] PostgreSQL database server running
- [ ] Required Python packages installed
- [ ] Environment variables configured
- [ ] Google AI API key obtained

### 2. Database Preparation
- [ ] PostgreSQL database created
- [ ] Database user with appropriate permissions
- [ ] Connection string configured
- [ ] Database schema initialized

### 3. Configuration Validation
- [ ] All configuration files present
- [ ] API keys and secrets configured
- [ ] Admin password set
- [ ] Default pricing values reviewed

## Installation Steps

### Step 1: Clone and Setup Application

```bash
# Clone the repository (if applicable)
git clone <repository-url>
cd ruby-gem-estimator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Database Setup

```sql
-- Create database
CREATE DATABASE ruby_gem_estimator;

-- Create user (optional)
CREATE USER gem_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ruby_gem_estimator TO gem_user;
```

### Step 3: Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/ruby_gem_estimator

# Google AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Application Configuration
ADMIN_PASSWORD=your_secure_admin_password
SECRET_KEY=your_secret_key_for_sessions

# Optional: Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/application.log
```

### Step 4: Initialize Database Schema

```bash
# Run database initialization
python -c "from database_config import initialize_database; initialize_database()"
```

### Step 5: Validate System

```bash
# Run comprehensive system validation
python validate_system.py

# Check validation report
cat validation_report.json
```

### Step 6: Start Application

```bash
# Start the Streamlit application
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## Configuration Management

### Default Configuration

The system includes comprehensive default configurations for:

- **Pricing**: Commodity prices per pound
- **Costs**: Flat costs for towing, lead, nut fees
- **Weights**: Fixed component weights
- **Assumptions**: Engine weight percentages, recovery factors
- **Grounding Settings**: Search parameters, confidence thresholds
- **Consensus Settings**: Agreement ratios, source weights

### Admin Configuration

Access the admin interface by:
1. Enable "Admin Mode" in the sidebar
2. Enter the admin password
3. Modify settings in the expandable admin panel
4. Save changes to persist in database

### Configuration Sections

#### Grounding Search Settings
- **Target Candidates**: Number of candidates to collect (default: 3)
- **Clustering Tolerance**: Similarity threshold for grouping (default: 0.15)
- **Confidence Threshold**: Minimum confidence for acceptance (default: 0.7)
- **Outlier Threshold**: Standard deviation threshold for outliers (default: 2.0)

#### Consensus Algorithm Settings
- **Min Agreement Ratio**: Minimum agreement for consensus (default: 0.6)
- **Preferred Sources**: List of trusted data sources
- **Source Weights**: Reliability weights for different sources

## Monitoring and Maintenance

### Health Monitoring

The system includes comprehensive monitoring capabilities:

1. **System Health Dashboard**
   - Access via monitoring_dashboard.py
   - Real-time system status
   - Performance metrics
   - Data quality indicators

2. **Database Monitoring**
   - Resolution statistics
   - Confidence score distributions
   - Performance metrics

3. **Cache Performance**
   - Hit rates and miss rates
   - Memory usage
   - Request deduplication stats

### Maintenance Tasks

#### Daily Tasks
- [ ] Check system health dashboard
- [ ] Review error logs
- [ ] Monitor API usage and costs
- [ ] Validate data quality metrics

#### Weekly Tasks
- [ ] Run database optimization
- [ ] Clear old cache entries
- [ ] Review confidence score trends
- [ ] Update pricing if needed

#### Monthly Tasks
- [ ] Full system validation
- [ ] Database backup and cleanup
- [ ] Performance optimization review
- [ ] Security updates

### Log Management

Logs are generated for:
- Resolution attempts and results
- API calls and responses
- Database operations
- System errors and warnings

Log files location:
- Application logs: `logs/application.log`
- Error logs: `logs/error.log`
- Performance logs: `logs/performance.log`

## Performance Optimization

### Database Optimization

```sql
-- Update table statistics
ANALYZE resolutions;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'resolutions';

-- Clean up old low-confidence records
DELETE FROM resolutions 
WHERE created_at < NOW() - INTERVAL '30 days'
AND confidence_score < 0.5;
```

### Cache Optimization

- Monitor cache hit rates
- Adjust TTL based on confidence scores
- Clear cache periodically to prevent memory issues
- Use request deduplication for identical searches

### API Optimization

- Monitor Google AI API usage
- Implement rate limiting if needed
- Use request caching to reduce API calls
- Batch requests when possible

## Security Considerations

### Access Control
- Admin interface protected by password
- Database credentials secured
- API keys stored in environment variables
- Session management for admin access

### Data Protection
- No personal information stored
- Vehicle specifications only
- Secure database connections
- Regular security updates

### API Security
- API keys rotated regularly
- Rate limiting implemented
- Request validation
- Error handling without information disclosure

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database status
sudo systemctl status postgresql

# Test connection
python -c "from database_config import test_database_connection; print(test_database_connection())"
```

#### API Issues
```bash
# Test API key
python -c "import os; print('API Key:', 'Valid' if os.getenv('GEMINI_API_KEY') else 'Missing')"
```

#### Performance Issues
```bash
# Run performance validation
python validate_system.py

# Check system resources
htop
df -h
```

### Error Resolution

#### Low Confidence Scores
- Review data sources
- Adjust clustering tolerance
- Increase target candidates
- Manual verification for critical vehicles

#### Cache Issues
- Clear Streamlit cache: `streamlit cache clear`
- Monitor memory usage
- Restart application if needed

#### Database Performance
- Run VACUUM and ANALYZE
- Check index usage
- Monitor query performance
- Consider partitioning for large datasets

## Backup and Recovery

### Database Backup
```bash
# Create backup
pg_dump ruby_gem_estimator > backup_$(date +%Y%m%d).sql

# Restore backup
psql ruby_gem_estimator < backup_20241022.sql
```

### Configuration Backup
```bash
# Export configuration
python -c "from database_config import get_app_config; import json; print(json.dumps(get_app_config(), indent=2))" > config_backup.json
```

### Application Backup
```bash
# Create application backup
tar -czf app_backup_$(date +%Y%m%d).tar.gz *.py *.md requirements.txt .env
```

## Scaling Considerations

### Horizontal Scaling
- Multiple application instances behind load balancer
- Shared database and cache
- Session affinity for admin interface

### Vertical Scaling
- Increase server resources
- Optimize database configuration
- Tune application parameters

### Performance Monitoring
- Monitor response times
- Track API usage
- Database performance metrics
- Memory and CPU usage

## Support and Maintenance

### Contact Information
- System Administrator: [admin@company.com]
- Technical Support: [support@company.com]
- Emergency Contact: [emergency@company.com]

### Documentation
- System Requirements: See requirements.md
- API Documentation: See resolver.py docstrings
- UI Components: See confidence_ui.py
- Database Schema: See database_config.py

### Version Control
- Current Version: 2.0.0
- Last Updated: October 2024
- Next Review: January 2025

## Deployment Checklist

### Pre-Deployment
- [ ] System validation passed
- [ ] Database initialized
- [ ] Configuration reviewed
- [ ] Backup created
- [ ] Monitoring configured

### Deployment
- [ ] Application deployed
- [ ] Database migrated
- [ ] Configuration applied
- [ ] Services started
- [ ] Health checks passed

### Post-Deployment
- [ ] System monitoring active
- [ ] Performance baseline established
- [ ] User access verified
- [ ] Documentation updated
- [ ] Team notified

## Rollback Procedures

### Application Rollback
1. Stop current application
2. Restore previous version
3. Restart services
4. Verify functionality

### Database Rollback
1. Stop application
2. Restore database backup
3. Update configuration if needed
4. Restart application

### Configuration Rollback
1. Access admin interface
2. Restore previous configuration
3. Save changes
4. Verify system operation

---

**Note**: This deployment guide should be customized based on your specific infrastructure and requirements. Always test deployment procedures in a staging environment before production deployment.