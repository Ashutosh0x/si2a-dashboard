#!/usr/bin/env python3
"""
Load synthetic data into BigQuery tables for SI²A
"""

import logging
import pandas as pd
from google.cloud import bigquery
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os
PROJECT_ID = os.getenv("PROJECT_ID", "shadow-it-incident-autopilot")

def load_incidents_data():
    """Load synthetic incidents data"""
    logger.info("📊 Loading synthetic incidents data...")
    
    try:
        # Read CSV file
        df = pd.read_csv('data/synthetic_incidents.csv')
        
        # Convert string arrays to proper format
        df['affected_systems'] = df['affected_systems'].apply(eval)
        df['tags'] = df['tags'].apply(eval)
        df['artifacts'] = df['artifacts'].apply(eval)
        
        # Convert timestamps
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['updated_at'] = pd.to_datetime(df['updated_at'])
        
        # Load to BigQuery
        client = bigquery.Client(project=PROJECT_ID)
        
        # Clear existing data
        client.query(f"DELETE FROM `{PROJECT_ID}.si2a_gold.incidents` WHERE TRUE").result()
        
        # Load new data
        table_id = f"{PROJECT_ID}.si2a_gold.incidents"
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"✅ Loaded {len(df)} incidents successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to load incidents: {e}")

def load_daily_metrics_data():
    """Load synthetic daily metrics data"""
    logger.info("📈 Loading synthetic daily metrics data...")
    
    try:
        # Read CSV file
        df = pd.read_csv('data/synthetic_daily_metrics.csv')
        
        # Convert date
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Load to BigQuery
        client = bigquery.Client(project=PROJECT_ID)
        
        # Clear existing data
        client.query(f"DELETE FROM `{PROJECT_ID}.si2a_marts.incident_daily` WHERE TRUE").result()
        
        # Load new data
        table_id = f"{PROJECT_ID}.si2a_marts.incident_daily"
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"✅ Loaded {len(df)} daily metrics successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to load daily metrics: {e}")

def load_policy_sections_data():
    """Load synthetic policy sections data"""
    logger.info("📜 Loading synthetic policy sections data...")
    
    try:
        # Read CSV file
        df = pd.read_csv('data/synthetic_policy_sections.csv')
        
        # Convert dates
        df['effective_date'] = pd.to_datetime(df['effective_date']).dt.date
        df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
        
        # Load to BigQuery
        client = bigquery.Client(project=PROJECT_ID)
        
        # Clear existing data
        client.query(f"DELETE FROM `{PROJECT_ID}.si2a_dim.policy_sections` WHERE TRUE").result()
        
        # Load new data
        table_id = f"{PROJECT_ID}.si2a_dim.policy_sections"
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"✅ Loaded {len(df)} policy sections successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to load policy sections: {e}")

def verify_data_loading():
    """Verify that data was loaded correctly"""
    logger.info("🔍 Verifying data loading...")
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Check incidents
        query = f"""
        SELECT COUNT(*) as incident_count, 
               COUNT(DISTINCT category) as category_count,
               AVG(risk_score) as avg_risk_score
        FROM `{PROJECT_ID}.si2a_gold.incidents`
        """
        
        result = client.query(query).result()
        for row in result:
            logger.info(f"📊 Incidents: {row.incident_count} total, {row.category_count} categories, avg risk: {row.avg_risk_score:.2f}")
        
        # Check daily metrics
        query = f"""
        SELECT COUNT(*) as days_count,
               AVG(total_incidents) as avg_daily_incidents,
               MAX(total_incidents) as max_daily_incidents
        FROM `{PROJECT_ID}.si2a_marts.incident_daily`
        """
        
        result = client.query(query).result()
        for row in result:
            logger.info(f"📈 Daily Metrics: {row.days_count} days, avg: {row.avg_daily_incidents:.1f} incidents/day, max: {row.max_daily_incidents}")
        
        # Check policy sections
        query = f"""
        SELECT COUNT(*) as policy_count,
               COUNT(DISTINCT category) as category_count
        FROM `{PROJECT_ID}.si2a_dim.policy_sections`
        """
        
        result = client.query(query).result()
        for row in result:
            logger.info(f"📜 Policy Sections: {row.policy_count} total, {row.category_count} categories")
        
        logger.info("✅ Data verification completed!")
        
    except Exception as e:
        logger.error(f"❌ Data verification failed: {e}")

def main():
    """Main function"""
    logger.info(f"🚀 Loading synthetic data for SI²A project: {PROJECT_ID}")
    
    # Load all data
    load_incidents_data()
    load_daily_metrics_data()
    load_policy_sections_data()
    
    # Verify loading
    verify_data_loading()
    
    logger.info("🎉 Synthetic data loading completed!")
    logger.info("📋 Next steps:")
    logger.info("   1. Run: python demo_si2a_simple.py")
    logger.info("   2. Test forecasting capabilities")
    logger.info("   3. Test semantic search")
    logger.info("   4. Create video demo")

if __name__ == "__main__":
    main()
