"""
Monitoring dashboard for Ruby GEM Estimator system health and performance.

This module provides real-time monitoring capabilities including:
- System performance metrics
- Resolution quality statistics  
- Cache performance monitoring
- Database health indicators
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

from resolver import create_monitoring_dashboard_data, get_system_metrics
from database_config import create_database_engine, get_datetime_interval_query
from sqlalchemy import text


def render_monitoring_dashboard():
    """Render the complete monitoring dashboard."""
    st.title("🔍 System Monitoring Dashboard")
    st.markdown("Real-time monitoring of Ruby GEM Estimator system performance and data quality")
    
    # Get dashboard data
    dashboard_data = create_monitoring_dashboard_data()
    
    if "error" in dashboard_data:
        st.error(f"Unable to load monitoring data: {dashboard_data['error']}")
        return
    
    # Knowledge base statistics (all-time)
    render_knowledge_base_stats()
    
    # System health overview
    render_health_overview(dashboard_data)
    
    # Performance metrics
    render_performance_metrics(dashboard_data)
    
    # Resolution quality analysis
    render_quality_analysis(dashboard_data)
    
    # Detailed statistics
    render_detailed_statistics(dashboard_data)


def render_knowledge_base_stats():
    """Render all-time knowledge base statistics."""
    st.header("📚 Knowledge Base Statistics (All Time)")
    
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Get all-time statistics
            stats_query = text("""
                SELECT 
                    COUNT(*) as total_resolutions,
                    COUNT(DISTINCT vehicle_key) as unique_vehicles,
                    COUNT(DISTINCT field_name) as unique_fields,
                    AVG(confidence_score) as avg_confidence,
                    COUNT(CASE WHEN confidence_score >= 0.7 THEN 1 END) as high_confidence_count,
                    MIN(created_at) as first_resolution,
                    MAX(created_at) as last_resolution
                FROM resolutions
            """)
            
            stats_result = conn.execute(stats_query).fetchone()
            
            if stats_result and stats_result[0] > 0:
                total_resolutions = stats_result[0]
                unique_vehicles = stats_result[1]
                unique_fields = stats_result[2]
                avg_confidence = stats_result[3]
                high_confidence_count = stats_result[4]
                first_resolution = stats_result[5]
                last_resolution = stats_result[6]
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric(
                        "Total Resolutions",
                        f"{total_resolutions:,}",
                        help="Total number of resolutions stored in the knowledge base"
                    )
                
                with col2:
                    st.metric(
                        "Unique Vehicles",
                        f"{unique_vehicles:,}",
                        help="Number of unique vehicles in the knowledge base"
                    )
                
                with col3:
                    st.metric(
                        "Unique Fields",
                        f"{unique_fields}",
                        help="Number of unique fields resolved"
                    )
                
                with col4:
                    cache_hit_potential = (high_confidence_count / total_resolutions * 100) if total_resolutions > 0 else 0
                    st.metric(
                        "Cache Quality",
                        f"{cache_hit_potential:.1f}%",
                        help="Percentage of high-confidence resolutions (usable for caching)"
                    )
                
                with col5:
                    if first_resolution and last_resolution:
                        days_active = (last_resolution - first_resolution).days
                        st.metric(
                            "Days Active",
                            f"{days_active}",
                            help="Number of days the knowledge base has been collecting data"
                        )
                    else:
                        st.metric("Days Active", "N/A")
                
                # Knowledge base growth visualization
                st.subheader("📈 Knowledge Base Growth Over Time")
                
                growth_query = text("""
                    SELECT 
                        DATE_TRUNC('day', created_at) as day,
                        COUNT(*) as daily_resolutions,
                        COUNT(DISTINCT vehicle_key) as daily_vehicles
                    FROM resolutions
                    GROUP BY DATE_TRUNC('day', created_at)
                    ORDER BY day
                """)
                
                growth_results = conn.execute(growth_query).fetchall()
                
                if growth_results:
                    growth_df = pd.DataFrame(growth_results, columns=["Day", "Daily Resolutions", "Daily Vehicles"])
                    growth_df["Day"] = pd.to_datetime(growth_df["Day"])
                    
                    # Calculate cumulative totals
                    growth_df["Cumulative Resolutions"] = growth_df["Daily Resolutions"].cumsum()
                    growth_df["Cumulative Vehicles"] = growth_df["Daily Vehicles"].cumsum()
                    
                    # Create dual-axis chart
                    fig = go.Figure()
                    
                    # Add cumulative resolutions
                    fig.add_trace(go.Scatter(
                        x=growth_df["Day"],
                        y=growth_df["Cumulative Resolutions"],
                        name="Total Resolutions",
                        mode="lines",
                        line=dict(color="#3b82f6", width=3),
                        fill='tozeroy'
                    ))
                    
                    # Add cumulative vehicles
                    fig.add_trace(go.Scatter(
                        x=growth_df["Day"],
                        y=growth_df["Cumulative Vehicles"],
                        name="Total Vehicles",
                        mode="lines",
                        line=dict(color="#22c55e", width=3),
                        yaxis="y2"
                    ))
                    
                    # Update layout
                    fig.update_layout(
                        title="Cumulative Knowledge Base Growth",
                        xaxis_title="Date",
                        yaxis=dict(title="Total Resolutions", side="left"),
                        yaxis2=dict(title="Total Vehicles", side="right", overlaying="y"),
                        hovermode="x unified",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # API call reduction metrics
                    st.subheader("💰 API Cost Reduction")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Estimate potential API calls saved
                        potential_calls_saved = total_resolutions - unique_vehicles * unique_fields
                        if potential_calls_saved < 0:
                            potential_calls_saved = 0
                        st.metric(
                            "Potential API Calls Saved",
                            f"{potential_calls_saved:,}",
                            help="Estimated API calls avoided by using cached data"
                        )
                    
                    with col2:
                        # Calculate cache efficiency
                        if total_resolutions > 0:
                            cache_efficiency = (potential_calls_saved / total_resolutions * 100)
                            st.metric(
                                "Cache Efficiency",
                                f"{cache_efficiency:.1f}%",
                                help="Percentage of resolutions that could be served from cache"
                            )
                        else:
                            st.metric("Cache Efficiency", "N/A")
                    
                    with col3:
                        # Average resolutions per vehicle
                        avg_resolutions_per_vehicle = total_resolutions / unique_vehicles if unique_vehicles > 0 else 0
                        st.metric(
                            "Avg Resolutions/Vehicle",
                            f"{avg_resolutions_per_vehicle:.1f}",
                            help="Average number of field resolutions per vehicle"
                        )
            else:
                st.info("No resolution data available yet. The knowledge base will grow as vehicles are resolved.")
                
    except Exception as e:
        st.error(f"Error loading knowledge base statistics: {e}")


def render_health_overview(dashboard_data: Dict[str, Any]):
    """Render system health overview section."""
    st.header("🏥 System Health Overview")
    
    health = dashboard_data.get("health_indicators", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = health.get("system_status", "unknown")
        status_color = "🟢" if status == "operational" else "🔴"
        st.metric(
            "System Status",
            f"{status_color} {status.title()}",
            help="Overall system operational status"
        )
    
    with col2:
        db_connected = health.get("database_connected", False)
        db_status = "🟢 Connected" if db_connected else "🔴 Disconnected"
        st.metric(
            "Database",
            db_status,
            help="Database connection status"
        )
    
    with col3:
        avg_confidence = dashboard_data.get("resolution_stats", {}).get("average_confidence", 0)
        confidence_healthy = health.get("average_confidence_healthy", False)
        confidence_color = "🟢" if confidence_healthy else "🟡" if avg_confidence > 0.5 else "🔴"
        st.metric(
            "Data Quality",
            f"{confidence_color} {avg_confidence:.1%}",
            help="Average confidence score of recent resolutions"
        )
    
    with col4:
        low_confidence_ratio = health.get("low_confidence_ratio", 0)
        ratio_color = "🟢" if low_confidence_ratio < 0.2 else "🟡" if low_confidence_ratio < 0.4 else "🔴"
        st.metric(
            "Low Confidence Ratio",
            f"{ratio_color} {low_confidence_ratio:.1%}",
            help="Percentage of resolutions with confidence < 60%"
        )


def render_performance_metrics(dashboard_data: Dict[str, Any]):
    """Render performance metrics section."""
    st.header("📊 Performance Metrics")
    
    stats = dashboard_data.get("resolution_stats", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Resolution Volume (24h)")
        
        # Create metrics display
        metrics_data = {
            "Metric": ["Total Resolutions", "Unique Vehicles", "Unique Fields", "High Confidence", "Low Confidence"],
            "Value": [
                stats.get("total_resolutions", 0),
                stats.get("unique_vehicles", 0),
                stats.get("unique_fields", 0),
                stats.get("high_confidence_count", 0),
                stats.get("low_confidence_count", 0)
            ]
        }
        
        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(metrics_df, use_container_width=True)
    
    with col2:
        st.subheader("Resolution Methods")
        
        method_dist = dashboard_data.get("method_distribution", {})
        if method_dist:
            # Create pie chart for method distribution
            fig = px.pie(
                values=list(method_dist.values()),
                names=list(method_dist.keys()),
                title="Resolution Method Distribution"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No resolution method data available")


def render_quality_analysis(dashboard_data: Dict[str, Any]):
    """Render data quality analysis section."""
    st.header("🎯 Data Quality Analysis")
    
    confidence_dist = dashboard_data.get("confidence_distribution", {})
    
    if confidence_dist:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Confidence Level Distribution")
            
            # Create bar chart for confidence distribution
            confidence_df = pd.DataFrame([
                {"Level": level.title(), "Count": count}
                for level, count in confidence_dist.items()
            ])
            
            fig = px.bar(
                confidence_df,
                x="Level",
                y="Count",
                color="Level",
                color_discrete_map={
                    "High": "#22c55e",
                    "Medium": "#f59e0b", 
                    "Low": "#ef4444"
                },
                title="Resolution Confidence Levels"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Quality Recommendations")
            
            total_resolutions = sum(confidence_dist.values())
            if total_resolutions > 0:
                high_ratio = confidence_dist.get("high", 0) / total_resolutions
                low_ratio = confidence_dist.get("low", 0) / total_resolutions
                
                if high_ratio >= 0.7:
                    st.success("✅ Excellent data quality - most resolutions have high confidence")
                elif high_ratio >= 0.5:
                    st.info("ℹ️ Good data quality - consider improving source diversity")
                else:
                    st.warning("⚠️ Data quality needs attention - many low confidence resolutions")
                
                if low_ratio >= 0.3:
                    st.error("🚨 High number of low confidence resolutions - review data sources")
                
                # Specific recommendations
                st.markdown("**Recommendations:**")
                if low_ratio > 0.2:
                    st.markdown("- Review and improve data source quality")
                    st.markdown("- Consider manual verification for critical vehicles")
                if confidence_dist.get("medium", 0) > confidence_dist.get("high", 0):
                    st.markdown("- Increase target candidates for better consensus")
                    st.markdown("- Add more reliable data sources")
            else:
                st.info("No resolution data available for analysis")
    else:
        st.info("No confidence distribution data available")


def render_detailed_statistics(dashboard_data: Dict[str, Any]):
    """Render detailed statistics section."""
    st.header("📈 Detailed Statistics")
    
    # Time-based analysis
    render_time_based_analysis()
    
    # Field-specific analysis
    render_field_analysis()
    
    # Vehicle-specific analysis
    render_vehicle_analysis()


def render_time_based_analysis():
    """Render time-based resolution analysis with time range selector."""
    st.subheader("⏰ Time-Based Analysis")
    
    # Time range selector
    time_range = st.selectbox(
        "Select Time Range",
        options=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
        index=0,
        key="time_based_range"
    )
    
    # Map selection to hours
    time_range_map = {
        "Last 24 Hours": 24,
        "Last 7 Days": 168,
        "Last 30 Days": 720,
        "All Time": None
    }
    
    hours = time_range_map[time_range]
    
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Build query based on time range
            if hours is not None:
                datetime_condition = get_datetime_interval_query(hours)
                where_clause = f"WHERE created_at > {datetime_condition}"
                time_label = time_range
            else:
                where_clause = ""
                time_label = "All Time"
            
            # Determine grouping based on time range
            if hours == 24:
                time_trunc = "hour"
                time_format = "Hour"
            else:
                time_trunc = "day"
                time_format = "Day"
            
            hourly_query = text(f"""
                SELECT 
                    DATE_TRUNC('{time_trunc}', created_at) as time_period,
                    COUNT(*) as resolution_count,
                    AVG(confidence_score) as avg_confidence
                FROM resolutions 
                {where_clause}
                GROUP BY DATE_TRUNC('{time_trunc}', created_at)
                ORDER BY time_period
            """)
            
            hourly_results = conn.execute(hourly_query).fetchall()
            
            if hourly_results:
                hourly_df = pd.DataFrame(hourly_results, columns=[time_format, "Resolutions", "Avg Confidence"])
                hourly_df[time_format] = pd.to_datetime(hourly_df[time_format])
                
                # Create dual-axis chart
                fig = go.Figure()
                
                # Add resolution count bars
                fig.add_trace(go.Bar(
                    x=hourly_df[time_format],
                    y=hourly_df["Resolutions"],
                    name="Resolution Count",
                    yaxis="y",
                    marker_color="#3b82f6"
                ))
                
                # Add confidence line
                fig.add_trace(go.Scatter(
                    x=hourly_df[time_format],
                    y=hourly_df["Avg Confidence"],
                    name="Avg Confidence",
                    yaxis="y2",
                    mode="lines+markers",
                    line=dict(color="#ef4444", width=3)
                ))
                
                # Update layout for dual axis
                fig.update_layout(
                    title=f"Resolution Activity ({time_label})",
                    xaxis_title=time_format,
                    yaxis=dict(title="Resolution Count", side="left"),
                    yaxis2=dict(title="Average Confidence", side="right", overlaying="y", range=[0, 1]),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No data available for {time_label}")
                
    except Exception as e:
        st.error(f"Error loading time-based analysis: {e}")


def render_field_analysis():
    """Render field-specific analysis with time range selector."""
    st.subheader("🔧 Field-Specific Analysis")
    
    # Time range selector
    time_range = st.selectbox(
        "Select Time Range",
        options=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
        index=0,
        key="field_analysis_range"
    )
    
    # Map selection to hours
    time_range_map = {
        "Last 24 Hours": 24,
        "Last 7 Days": 168,
        "Last 30 Days": 720,
        "All Time": None
    }
    
    hours = time_range_map[time_range]
    
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Build query based on time range
            if hours is not None:
                datetime_condition = get_datetime_interval_query(hours)
                where_clause = f"WHERE created_at > {datetime_condition}"
            else:
                where_clause = ""
            
            field_query = text(f"""
                SELECT 
                    field_name,
                    COUNT(*) as resolution_count,
                    AVG(confidence_score) as avg_confidence,
                    MIN(confidence_score) as min_confidence,
                    MAX(confidence_score) as max_confidence,
                    COUNT(CASE WHEN confidence_score < 0.6 THEN 1 END) as low_confidence_count
                FROM resolutions 
                {where_clause}
                GROUP BY field_name
                ORDER BY resolution_count DESC
            """)
            
            field_results = conn.execute(field_query).fetchall()
            
            if field_results:
                field_df = pd.DataFrame(field_results, columns=[
                    "Field", "Count", "Avg Confidence", "Min Confidence", 
                    "Max Confidence", "Low Confidence Count"
                ])
                
                # Format confidence columns as percentages
                for col in ["Avg Confidence", "Min Confidence", "Max Confidence"]:
                    field_df[col] = field_df[col].apply(lambda x: f"{x:.1%}")
                
                st.dataframe(field_df, use_container_width=True)
                
                # Highlight fields needing attention
                low_confidence_fields = [
                    row["Field"] for _, row in field_df.iterrows() 
                    if row["Low Confidence Count"] > 0
                ]
                
                if low_confidence_fields:
                    st.warning(f"⚠️ Fields with low confidence resolutions: {', '.join(low_confidence_fields)}")
            else:
                st.info(f"No field-specific data available for {time_range}")
                
    except Exception as e:
        st.error(f"Error loading field analysis: {e}")


def render_vehicle_analysis():
    """Render vehicle-specific analysis with time range selector."""
    st.subheader("🚗 Vehicle Analysis")
    
    # Time range selector
    time_range = st.selectbox(
        "Select Time Range",
        options=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
        index=1,  # Default to 7 days
        key="vehicle_analysis_range"
    )
    
    # Map selection to hours
    time_range_map = {
        "Last 24 Hours": 24,
        "Last 7 Days": 168,
        "Last 30 Days": 720,
        "All Time": None
    }
    
    hours = time_range_map[time_range]
    
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Build query based on time range
            if hours is not None:
                datetime_condition = get_datetime_interval_query(hours)
                where_clause = f"WHERE created_at > {datetime_condition}"
            else:
                where_clause = ""
            
            vehicle_query = text(f"""
                SELECT 
                    vehicle_key,
                    COUNT(*) as resolution_count,
                    AVG(confidence_score) as avg_confidence,
                    COUNT(DISTINCT field_name) as fields_resolved
                FROM resolutions 
                {where_clause}
                GROUP BY vehicle_key
                ORDER BY resolution_count DESC
                LIMIT 10
            """)
            
            vehicle_results = conn.execute(vehicle_query).fetchall()
            
            if vehicle_results:
                vehicle_df = pd.DataFrame(vehicle_results, columns=[
                    "Vehicle", "Resolutions", "Avg Confidence", "Fields Resolved"
                ])
                
                # Format confidence as percentage
                vehicle_df["Avg Confidence"] = vehicle_df["Avg Confidence"].apply(lambda x: f"{x:.1%}")
                
                st.dataframe(vehicle_df, use_container_width=True)
            else:
                st.info(f"No vehicle-specific data available for {time_range}")
                
    except Exception as e:
        st.error(f"Error loading vehicle analysis: {e}")


def render_system_alerts():
    """Render system alerts and warnings."""
    st.header("🚨 System Alerts")
    
    dashboard_data = create_monitoring_dashboard_data()
    
    alerts = []
    
    # Check for system health issues
    health = dashboard_data.get("health_indicators", {})
    
    if not health.get("database_connected", True):
        alerts.append({
            "level": "error",
            "message": "Database connection lost",
            "action": "Check database server status and connection settings"
        })
    
    if not health.get("average_confidence_healthy", True):
        avg_confidence = dashboard_data.get("resolution_stats", {}).get("average_confidence", 0)
        alerts.append({
            "level": "warning", 
            "message": f"Low average confidence score: {avg_confidence:.1%}",
            "action": "Review data sources and consider improving source quality"
        })
    
    low_confidence_ratio = health.get("low_confidence_ratio", 0)
    if low_confidence_ratio > 0.3:
        alerts.append({
            "level": "warning",
            "message": f"High ratio of low confidence resolutions: {low_confidence_ratio:.1%}",
            "action": "Investigate data quality issues and consider manual verification"
        })
    
    # Display alerts
    if alerts:
        for alert in alerts:
            if alert["level"] == "error":
                st.error(f"🚨 **{alert['message']}**\n\n*Action:* {alert['action']}")
            elif alert["level"] == "warning":
                st.warning(f"⚠️ **{alert['message']}**\n\n*Action:* {alert['action']}")
    else:
        st.success("✅ No system alerts - all systems operating normally")


if __name__ == "__main__":
    # For testing the dashboard independently
    render_monitoring_dashboard()