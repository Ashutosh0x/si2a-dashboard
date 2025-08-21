#!/usr/bin/env python3
"""
Test BigQuery tables and show sample data
"""

import logging
from google.cloud import bigquery

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "shadow-it-incident-autopilot"

def test_tables():
    """Test if tables exist and show sample data"""
    logger.info(f"🔍 Testing BigQuery tables in project: {PROJECT_ID}")
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Test incidents table
        logger.info("📊 Testing incidents table...")
        query = f"""
        SELECT 
            incident_id,
            title,
            severity,
            status,
            created_at,
            affected_users,
            risk_score
        FROM `{PROJECT_ID}.si2a_gold.incidents`
        ORDER BY created_at DESC
        LIMIT 5
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        print("\n📋 Sample Incidents:")
        print("=" * 80)
        for row in results:
            print(f"• {row.incident_id}: {row.title}")
            print(f"  Severity: {row.severity} | Status: {row.status} | Users: {row.affected_users}")
            print(f"  Risk Score: {row.risk_score} | Created: {row.created_at}")
            print()
        
        # Test policy sections table
        logger.info("📋 Testing policy sections table...")
        query = f"""
        SELECT 
            section_id,
            section_title,
            category,
            compliance_level
        FROM `{PROJECT_ID}.si2a_dim.policy_sections`
        LIMIT 5
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        print("📜 Sample Policy Sections:")
        print("=" * 80)
        for row in results:
            print(f"• {row.section_id}: {row.section_title}")
            print(f"  Category: {row.category} | Compliance: {row.compliance_level}")
            print()
        
        # Test daily metrics table
        logger.info("📈 Testing daily metrics table...")
        query = f"""
        SELECT 
            date,
            total_incidents,
            high_severity_incidents,
            avg_resolution_time_hours
        FROM `{PROJECT_ID}.si2a_marts.incident_daily`
        ORDER BY date DESC
        LIMIT 5
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        print("📊 Sample Daily Metrics:")
        print("=" * 80)
        for row in results:
            print(f"• {row.date}: {row.total_incidents} incidents")
            print(f"  High Severity: {row.high_severity_incidents} | Avg Resolution: {row.avg_resolution_time_hours:.1f} hours")
            print()
        
        logger.info("✅ All tables tested successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_tables()
