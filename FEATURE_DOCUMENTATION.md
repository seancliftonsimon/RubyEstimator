# Ruby GEM Estimator - New Features Documentation

## Overview

This document provides comprehensive documentation for all new features and configuration options added to the Ruby GEM Estimator system. These enhancements transform the system from a basic vehicle valuation tool into a sophisticated AI-powered estimation platform.

## Core Features

### 1. Grounded Search Resolution System

#### Description
The system now uses Google AI with Grounded Search to collect multiple candidate values for each vehicle specification, providing more accurate and reliable estimates.

#### How It Works
1. **Multiple Candidate Collection**: For each vehicle field (curb weight, engine material, etc.), the system queries Google AI to collect 3+ candidate values from different sources
2. **Source Reliability Scoring**: Each candidate is scored based on source reliability (KBB.com, Edmunds.com get higher scores than forums)
3. **Consensus Algorithm**: Similar values are clustered together, and the system selects the median from the largest cluster
4. **Outlier Detection**: Statistical analysis identifies and flags extreme values that deviate significantly from the consensus

#### Configuration Options
- **Target Candidates** (1-10): Number of candidates to collect per field
- **Clustering Tolerance** (0.01-1.0): How similar values must be to group together (0.15 = 15% tolerance)
- **Confidence Threshold** (0.0-1.0): Minimum confidence score for automatic acceptance
- **Outlier Threshold** (0.5-5.0): Standard deviation threshold for outlier detection

#### Benefits
- **Improved Accuracy**: Multiple sources reduce reliance on single data points
- **Quality Assessment**: Confidence scores help identify reliable vs. questionable estimates
- **Transparency**: Full source citations and resolution methods visible to users

### 2. Confidence Indicators and Data Quality

#### Description
Visual indicators throughout the interface show the reliability of each estimate, helping users make informed decisions.

#### Confidence Levels
- **High Confidence (Green)**: 80%+ confidence, multiple agreeing sources
- **Medium Confidence (Amber)**: 60-79% confidence, some source disagreement
- **Low Confidence (Red)**: <60% confidence, requires manual review

#### Visual Elements
- **Confidence Badges**: Color-coded indicators next to each resolved value
- **Warning Banners**: Prominent alerts for low-confidence estimates requiring manual review
- **Tooltips**: Hover information showing confidence scores and source counts
- **Progress Indicators**: Visual representation of data quality and agreement levels

#### Plain-English Explanations
- "High confidence - multiple reliable sources agree"
- "Medium confidence - some variation in source data"
- "Low confidence - manual verification recommended"

### 3. Provenance Tracking and Source Transparency

#### Description
Complete audit trail showing exactly how each value was determined, with clickable source citations.

#### Provenance Panel Features
- **Resolution Method**: Shows whether value came from consensus, single source, or database lookup
- **Source List**: All sources consulted with their individual confidence scores
- **Statistical Analysis**: Shows candidate values, outliers, and clustering results
- **Clickable Citations**: Direct links back to original data sources where available
- **Resolution History**: Timestamp and method for each field resolution

#### Database Storage
- All resolutions stored in `resolutions` table with complete metadata
- JSON storage of candidate values and source information
- Audit trail for configuration changes and admin actions
- Performance metrics and quality statistics

### 4. Enhanced Administrative Interface

#### Description
Comprehensive admin panel allowing real-time configuration of all system parameters without code changes.

#### New Configuration Sections

##### Grounding Search Settings
- **Target Candidates**: How many candidate values to collect
- **Clustering Tolerance**: Similarity threshold for grouping values
- **Confidence Threshold**: Minimum confidence for automatic acceptance
- **Outlier Threshold**: Statistical threshold for outlier detection
- **Nut Fee Toggle**: Apply nut fee to curb weight or ELV weight

##### Consensus Algorithm Settings
- **Min Agreement Ratio**: Minimum percentage of sources that must agree
- **Preferred Sources**: List of trusted data sources (KBB, Edmunds, etc.)
- **Source Weights**: Reliability multipliers for different source types
  - KBB.com: 1.2x weight (20% more reliable)
  - Edmunds.com: 1.2x weight
  - Manufacturer: 1.5x weight (50% more reliable)
  - Default sources: 1.0x weight

#### Real-Time Application
- All configuration changes apply immediately
- No application restart required
- Settings persisted in database
- Validation prevents invalid configurations

### 5. Production Monitoring and Performance Optimization

#### Description
Comprehensive monitoring system providing real-time insights into system health, performance, and data quality.

#### Monitoring Dashboard Features
- **System Health Overview**: Database connectivity, API status, overall system health
- **Performance Metrics**: Response times, resolution counts, API usage statistics
- **Data Quality Analysis**: Confidence score distributions, outlier detection rates
- **Resolution Statistics**: Success rates, method distribution, field-specific metrics

#### Performance Optimizations
- **Intelligent Caching**: TTL-based caching with confidence-aware expiration
  - High confidence results cached longer (48 hours)
  - Low confidence results cached shorter (12 hours)
- **Request Deduplication**: Identical searches return cached results
- **Database Optimization**: Proper indexing and query optimization
- **API Usage Optimization**: Reduced redundant calls through smart caching

#### Monitoring Alerts
- **Critical**: System down, database unreachable, API quota exceeded
- **Warning**: High low-confidence ratio (>30%), slow response times (>5s)
- **Info**: Unusual resolution patterns, high API usage

## Configuration Reference

### Default Settings

#### Pricing Configuration
```json
{
  "price_per_lb": {
    "ELV": 0.118,
    "AL_ENGINE": 0.3525,
    "FE_ENGINE": 0.2325,
    "HARNESS": 1.88,
    "AL_RIMS": 1.24,
    "CATS": 92.25,
    "TIRES": 4.5
  }
}
```

#### Grounding Settings
```json
{
  "grounding_settings": {
    "target_candidates": 3,
    "clustering_tolerance": 0.15,
    "confidence_threshold": 0.7,
    "outlier_threshold": 2.0,
    "nut_fee_applies_to": "curb_weight"
  }
}
```

#### Consensus Settings
```json
{
  "consensus_settings": {
    "min_agreement_ratio": 0.6,
    "preferred_sources": ["kbb.com", "edmunds.com", "manufacturer"],
    "source_weights": {
      "kbb.com": 1.2,
      "edmunds.com": 1.2,
      "manufacturer": 1.5,
      "default": 1.0
    }
  }
}
```

### Environment Variables
- **DATABASE_URL**: PostgreSQL connection string
- **GEMINI_API_KEY**: Google AI API key for grounded search
- **ADMIN_PASSWORD**: Password for admin interface access
- **LOG_LEVEL**: Logging verbosity (INFO, DEBUG, WARNING, ERROR)

## User Interface Enhancements

### Enhanced Results Display
- **Confidence Badges**: Color-coded indicators next to each value
- **Interactive Tooltips**: Hover for detailed confidence and source information
- **Warning Banners**: Prominent alerts for values requiring manual review
- **Provenance Panels**: Expandable sections showing resolution details

### Improved Styling
- **Ruby/Teal Color Scheme**: Professional appearance with brand colors
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Accessibility**: Proper contrast ratios and screen reader support
- **Loading Indicators**: Visual feedback during resolution processes

### Enhanced Data Presentation
- **Inline Confidence**: Confidence indicators integrated into results tables
- **Visual Highlighting**: Low-confidence values highlighted for attention
- **Source Citations**: Clickable links to original data sources
- **Statistical Summaries**: Agreement levels and data quality metrics

## API and Integration

### Google AI Integration
- **Grounded Search**: Uses Google's grounded search for source citations
- **Rate Limiting**: Intelligent rate limiting to stay within API quotas
- **Error Handling**: Graceful fallback when API is unavailable
- **Request Optimization**: Caching and deduplication reduce API calls

### Database Schema Extensions
```sql
-- New resolutions table for provenance tracking
CREATE TABLE resolutions (
    id SERIAL PRIMARY KEY,
    vehicle_key VARCHAR(100) NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    final_value FLOAT,
    confidence_score FLOAT,
    method VARCHAR(50),
    candidates_json JSONB,
    warnings_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vehicle_key, field_name)
);
```

### Performance Characteristics
- **Single Resolution**: <1 second typical response time
- **Batch Processing**: <2 seconds for 5 vehicles
- **Cache Hit Rate**: ~60% reduction in API calls
- **Database Queries**: Optimized with proper indexing

## Troubleshooting Guide

### Common Issues and Solutions

#### Low Confidence Scores
**Symptoms**: Many estimates showing red confidence badges
**Causes**: Poor source quality, high data variability, insufficient candidates
**Solutions**:
- Increase target candidates to 5-7
- Adjust clustering tolerance to 0.20-0.25
- Review and improve preferred sources list
- Consider manual verification for critical vehicles

#### Slow Performance
**Symptoms**: Long response times, timeouts
**Causes**: API rate limits, database performance, network issues
**Solutions**:
- Check Google AI API quota and usage
- Monitor database connection pool
- Review cache hit rates and optimize TTL settings
- Consider increasing clustering tolerance to reduce processing

#### API Issues
**Symptoms**: "No candidates found" errors, API failures
**Causes**: Invalid API key, quota exceeded, network connectivity
**Solutions**:
- Verify GEMINI_API_KEY environment variable
- Check API quota in Google Cloud Console
- Test network connectivity to Google AI services
- Review API usage patterns and implement rate limiting

#### Database Connectivity
**Symptoms**: Configuration changes not persisting, resolution history missing
**Causes**: Database connection issues, permission problems
**Solutions**:
- Test database connection: `python -c "from database_config import test_database_connection; print(test_database_connection())"`
- Verify DATABASE_URL environment variable
- Check PostgreSQL server status and permissions
- Review database logs for connection errors

## Best Practices

### Configuration Management
- **Start Conservative**: Begin with default settings and adjust based on results
- **Monitor Quality**: Watch confidence score distributions and adjust thresholds
- **Test Changes**: Use admin interface to test configuration changes with known vehicles
- **Document Changes**: Keep record of configuration modifications and reasons

### Data Quality Management
- **Regular Review**: Monitor low-confidence resolutions and investigate patterns
- **Source Validation**: Periodically review and update preferred sources list
- **Manual Verification**: Establish process for verifying critical or unusual vehicles
- **Quality Metrics**: Track confidence score trends and resolution accuracy

### Performance Optimization
- **Cache Management**: Monitor cache hit rates and adjust TTL settings
- **API Usage**: Track API calls and implement usage alerts
- **Database Maintenance**: Regular VACUUM and ANALYZE operations
- **Resource Monitoring**: Monitor CPU, memory, and disk usage patterns

## Future Enhancements

### Planned Improvements
- **Machine Learning**: Train models on resolution history for better predictions
- **Advanced Analytics**: Trend analysis and predictive insights
- **Mobile App**: Native mobile application for field use
- **Batch Processing**: Bulk vehicle processing capabilities
- **Additional APIs**: Integration with more data sources beyond Google AI

### Scalability Considerations
- **Horizontal Scaling**: Load balancer with multiple application instances
- **Database Scaling**: Read replicas and query optimization
- **Distributed Caching**: Redis or Memcached for multi-instance deployments
- **API Management**: Advanced rate limiting and quota management

---

**Last Updated**: October 2024  
**Version**: 2.0.0  
**Next Review**: January 2025