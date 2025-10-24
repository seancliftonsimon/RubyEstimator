# Ruby GEM Estimator - Deployment Checklist & Rollback Procedures

## Pre-Deployment Checklist

### System Validation ✅
- [ ] Run comprehensive system validation: `python validate_system.py`
- [ ] Run end-to-end validation: `python end_to_end_validation.py`
- [ ] Verify all validation reports show "PASS" or "READY" status
- [ ] Review and address any warnings in validation reports
- [ ] Confirm all test vehicles process correctly with expected accuracy

### Database Preparation ✅
- [ ] PostgreSQL server running and accessible
- [ ] Database created with proper permissions
- [ ] Connection string configured and tested
- [ ] Resolutions table created with proper indexes
- [ ] App_config table initialized with default settings
- [ ] Database backup created before deployment

### Configuration Validation ✅
- [ ] All environment variables set (DATABASE_URL, GEMINI_API_KEY, ADMIN_PASSWORD)
- [ ] Default configuration values reviewed and approved
- [ ] Admin password set and documented securely
- [ ] Google AI API key valid and quota sufficient
- [ ] Grounding and consensus settings appropriate for production

### Application Dependencies ✅
- [ ] Python 3.8+ installed on target system
- [ ] All required packages installed: `pip install -r requirements.txt`
- [ ] Virtual environment configured if applicable
- [ ] System resources adequate (4GB+ RAM, 2+ CPU cores)
- [ ] Network connectivity to Google AI API confirmed

### Security Validation ✅
- [ ] Admin password meets security requirements
- [ ] Database credentials secured
- [ ] API keys stored securely (environment variables or secrets)
- [ ] No sensitive information in code or logs
- [ ] Access controls configured appropriately

## Deployment Steps

### Step 1: Environment Setup
```bash
# Create deployment directory
mkdir -p /opt/ruby-gem-estimator
cd /opt/ruby-gem-estimator

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration Deployment
```bash
# Copy application files
cp *.py /opt/ruby-gem-estimator/
cp *.md /opt/ruby-gem-estimator/
cp requirements.txt /opt/ruby-gem-estimator/

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/ruby_gem_estimator"
export GEMINI_API_KEY="your_api_key_here"
export ADMIN_PASSWORD="your_secure_password"

# Or create .env file
cat > .env << EOF
DATABASE_URL=postgresql://user:pass@localhost:5432/ruby_gem_estimator
GEMINI_API_KEY=your_api_key_here
ADMIN_PASSWORD=your_secure_password
EOF
```

### Step 3: Database Initialization
```bash
# Initialize database schema
python -c "from resolver import create_resolutions_table; create_resolutions_table()"

# Verify database connectivity
python -c "from database_config import test_database_connection; print(test_database_connection())"
```

### Step 4: System Validation
```bash
# Run final pre-deployment validation
python validate_system.py
python end_to_end_validation.py

# Check validation results
cat validation_report.json
cat end_to_end_validation_report.json
```

### Step 5: Application Startup
```bash
# Start application
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Or use systemd service (recommended for production)
sudo systemctl start ruby-gem-estimator
sudo systemctl enable ruby-gem-estimator
```

## Post-Deployment Validation

### Immediate Checks (0-15 minutes)
- [ ] Application starts without errors
- [ ] Web interface accessible at configured URL
- [ ] Database connection successful
- [ ] Admin interface accessible with correct password
- [ ] Test vehicle processing works correctly
- [ ] Confidence indicators display properly
- [ ] Provenance panels show source information

### Short-term Monitoring (15 minutes - 2 hours)
- [ ] Process multiple test vehicles successfully
- [ ] Monitor system resource usage (CPU, memory, disk)
- [ ] Check application logs for errors or warnings
- [ ] Verify Google AI API calls working correctly
- [ ] Test admin configuration changes apply correctly
- [ ] Confirm resolution caching working properly

### Extended Validation (2-24 hours)
- [ ] Monitor system performance under normal load
- [ ] Review resolution quality metrics
- [ ] Check database performance and growth
- [ ] Validate monitoring dashboard functionality
- [ ] Confirm no memory leaks or resource issues
- [ ] Test system recovery after restart

## Rollback Procedures

### Immediate Rollback (Critical Issues)

#### Application Rollback
```bash
# Stop current application
sudo systemctl stop ruby-gem-estimator
# or
pkill -f "streamlit run app.py"

# Restore previous version
cd /opt/ruby-gem-estimator
git checkout previous-stable-tag
# or
cp -r /backup/ruby-gem-estimator-previous/* .

# Restart application
sudo systemctl start ruby-gem-estimator
# or
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
```

#### Database Rollback
```bash
# Stop application first
sudo systemctl stop ruby-gem-estimator

# Restore database backup
psql ruby_gem_estimator < /backup/database_backup_pre_deployment.sql

# Restart application
sudo systemctl start ruby-gem-estimator
```

### Partial Rollback (Configuration Issues)

#### Configuration Rollback
```bash
# Access admin interface
# Navigate to admin settings
# Restore previous configuration values from backup

# Or restore via database
python -c "
from database_config import upsert_app_config
import json
with open('/backup/config_backup.json') as f:
    config = json.load(f)
    for section, values in config.items():
        upsert_app_config(section, values, 'Rollback', 'admin')
"
```

#### Feature Rollback
```bash
# Disable new features via admin interface
# Set grounding_settings.target_candidates = 1 (disables consensus)
# Set confidence_threshold = 0.0 (disables confidence filtering)
# This maintains backward compatibility while disabling new features
```

## Monitoring and Alerting

### Key Metrics to Monitor
- **System Health**: Application uptime, response times
- **Database Performance**: Connection count, query performance
- **Resolution Quality**: Average confidence scores, error rates
- **API Usage**: Google AI API calls, quota usage, error rates
- **Resource Usage**: CPU, memory, disk space

### Alert Thresholds
- **Critical**: Application down, database unreachable, API quota exceeded
- **Warning**: Low confidence scores >30%, high response times >5s
- **Info**: High API usage, unusual resolution patterns

### Monitoring Commands
```bash
# Check application status
sudo systemctl status ruby-gem-estimator

# Monitor logs
tail -f /var/log/ruby-gem-estimator/application.log

# Check database connections
psql ruby_gem_estimator -c "SELECT count(*) FROM pg_stat_activity;"

# Monitor system resources
htop
df -h
```

## Emergency Contacts

### Technical Contacts
- **System Administrator**: [admin@company.com] - Primary contact for system issues
- **Database Administrator**: [dba@company.com] - Database-related issues
- **Development Team**: [dev@company.com] - Application bugs or feature issues

### Escalation Procedures
1. **Level 1** (0-30 minutes): System administrator attempts resolution
2. **Level 2** (30-60 minutes): Engage database administrator if DB issues
3. **Level 3** (60+ minutes): Engage development team and consider rollback

## Documentation Updates

### Post-Deployment Documentation
- [ ] Update system documentation with actual deployment configuration
- [ ] Document any deployment-specific customizations
- [ ] Update monitoring and alerting procedures
- [ ] Record lessons learned and improvements for next deployment
- [ ] Update emergency contact information

### Version Control
- [ ] Tag successful deployment in version control
- [ ] Document configuration changes
- [ ] Update changelog with deployment notes
- [ ] Archive deployment artifacts

## Success Criteria

### Deployment Considered Successful When:
- [ ] All validation checks pass
- [ ] System processes test vehicles with >90% accuracy
- [ ] Average confidence scores >70%
- [ ] Response times <3 seconds for typical requests
- [ ] No critical errors in first 24 hours
- [ ] Admin interface fully functional
- [ ] Monitoring dashboard operational

### Go/No-Go Decision Points
- **GO**: All critical checks pass, minor warnings acceptable
- **NO-GO**: Any critical validation failures, database issues, or API problems
- **CONDITIONAL GO**: Minor issues that can be addressed post-deployment

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Validated By**: _______________  
**Approved By**: _______________