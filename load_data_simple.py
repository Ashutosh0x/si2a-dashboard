#!/usr/bin/env python3
"""
Simple Data Loading for SI²A - Load synthetic data into BigQuery
"""

import logging
import os
import pandas as pd
from google.cloud import bigquery
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("PROJECT_ID", "shadow-it-incident-autopilot")

def ensure_datasets_and_tables():
    """Ensure required datasets and minimal tables exist in the target project."""
    client = bigquery.Client(project=PROJECT_ID)

    # Ensure datasets
    for ds in ["si2a_gold", "si2a_dim", "si2a_marts"]:
        ref = bigquery.Dataset(f"{PROJECT_ID}.{ds}")
        try:
            client.get_dataset(ref)
        except Exception:
            client.create_dataset(ref, exists_ok=True)

    # Ensure tables with minimal schema used by this loader
    tables = {
        f"{PROJECT_ID}.si2a_gold.incidents": [
            bigquery.SchemaField("incident_id", "STRING"),
            bigquery.SchemaField("title", "STRING"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("severity", "STRING"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("updated_at", "TIMESTAMP"),
            bigquery.SchemaField("assigned_to", "STRING"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("root_cause", "STRING"),
            bigquery.SchemaField("resolution", "STRING"),
            bigquery.SchemaField("resolution_time_hours", "FLOAT"),
            bigquery.SchemaField("affected_users", "INT64"),
            bigquery.SchemaField("affected_systems", "STRING", mode="REPEATED"),
            bigquery.SchemaField("tags", "STRING", mode="REPEATED"),
            bigquery.SchemaField("business_impact", "STRING"),
            bigquery.SchemaField("risk_score", "FLOAT"),
        ],
        f"{PROJECT_ID}.si2a_dim.policy_sections": [
            bigquery.SchemaField("section_id", "STRING"),
            bigquery.SchemaField("policy_id", "STRING"),
            bigquery.SchemaField("section_title", "STRING"),
            bigquery.SchemaField("section_text", "STRING"),
            bigquery.SchemaField("effective_date", "DATE"),
            bigquery.SchemaField("expiry_date", "DATE"),
        ],
        f"{PROJECT_ID}.si2a_marts.incident_daily": [
            bigquery.SchemaField("date", "DATE"),
            bigquery.SchemaField("total_incidents", "INT64"),
            bigquery.SchemaField("high_severity_incidents", "INT64"),
            bigquery.SchemaField("medium_severity_incidents", "INT64"),
            bigquery.SchemaField("low_severity_incidents", "INT64"),
            bigquery.SchemaField("avg_resolution_time_hours", "FLOAT"),
        ],
    }

    for table_id, schema in tables.items():
        try:
            client.get_table(table_id)
        except Exception:
            client.create_table(bigquery.Table(table_id, schema=schema), exists_ok=True)

def load_incidents_data():
    """Load incidents data with proper CSV handling"""
    logger.info("📊 Loading synthetic incidents data...")
    try:
        # Read CSV with proper handling
        df = pd.read_csv('data/synthetic_incidents.csv', quotechar='"', escapechar='\\')
        
        # Convert string arrays to actual arrays
        df['affected_systems'] = df['affected_systems'].str.split(';')
        df['tags'] = df['tags'].str.split(';')
        df['artifacts'] = df['artifacts'].str.split(';')
        
        # Convert timestamps
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['updated_at'] = pd.to_datetime(df['updated_at'])
        
        # Load to BigQuery
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.si2a_gold.incidents"
        
        # Clear existing data
        client.query(f"DELETE FROM `{table_id}` WHERE TRUE").result()
        
        # Load new data
        job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND)
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"✅ Loaded {len(df)} incidents successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to load incidents: {e}")
        return False

def load_policy_sections_data():
    """Load policy sections data"""
    logger.info("📜 Loading synthetic policy sections data...")
    try:
        df = pd.read_csv('data/synthetic_policy_sections.csv', quotechar='"', escapechar='\\')
        
        # Convert timestamps
        df['effective_date'] = pd.to_datetime(df['effective_date'])
        df['expiry_date'] = pd.to_datetime(df['expiry_date'])
        
        # Load to BigQuery
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.si2a_dim.policy_sections"
        
        # Clear existing data
        client.query(f"DELETE FROM `{table_id}` WHERE TRUE").result()
        
        # Load new data
        job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND)
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"✅ Loaded {len(df)} policy sections successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to load policy sections: {e}")
        return False

def create_sample_daily_metrics():
    """Create sample daily metrics directly in BigQuery"""
    logger.info("📈 Creating sample daily metrics...")
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Create sample daily metrics SQL
        sql = f"""
        INSERT INTO `{PROJECT_ID}.si2a_marts.incident_daily`
        (date, total_incidents, high_severity_incidents, medium_severity_incidents, low_severity_incidents, avg_resolution_time_hours)
        VALUES
        ('2024-01-15', 1, 0, 1, 0, 4.5),
        ('2024-01-16', 1, 1, 0, 0, 2.0),
        ('2024-01-17', 2, 0, 1, 1, 3.2),
        ('2024-01-18', 0, 0, 0, 0, 0.0),
        ('2024-01-19', 1, 0, 0, 1, 1.5),
        ('2024-01-20', 2, 1, 1, 0, 5.8),
        ('2024-01-21', 1, 0, 1, 0, 2.3),
        ('2024-01-22', 3, 1, 1, 1, 4.1),
        ('2024-01-23', 1, 0, 0, 1, 1.8),
        ('2024-01-24', 2, 0, 2, 0, 3.7)
        """
        
        # Clear existing data first
        client.query(f"DELETE FROM `{PROJECT_ID}.si2a_marts.incident_daily` WHERE TRUE").result()
        
        # Insert new data
        client.query(sql).result()
        
        logger.info("✅ Created sample daily metrics successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create daily metrics: {e}")
        return False

def verify_data_loading():
    """Verify that data was loaded successfully"""
    logger.info("🔍 Verifying data loading...")
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Check incidents
        incidents_query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.si2a_gold.incidents`"
        incidents_result = client.query(incidents_query).result()
        incidents_count = list(incidents_result)[0].count
        
        # Check policy sections
        policy_query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.si2a_dim.policy_sections`"
        policy_result = client.query(policy_query).result()
        policy_count = list(policy_result)[0].count
        
        # Check daily metrics
        metrics_query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.si2a_marts.incident_daily`"
        metrics_result = client.query(metrics_query).result()
        metrics_count = list(metrics_result)[0].count
        
        logger.info(f"📊 Data Verification Results:")
        logger.info(f"   • Incidents: {incidents_count}")
        logger.info(f"   • Policy Sections: {policy_count}")
        logger.info(f"   • Daily Metrics: {metrics_count}")
        
        if incidents_count > 0 and policy_count > 0 and metrics_count > 0:
            logger.info("✅ All data loaded successfully!")
            return True
        else:
            logger.warning("⚠️ Some data may not have loaded properly")
            return False
            
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def main():
    """Main function to load all data"""
    logger.info(f"🚀 Loading synthetic data for project: {PROJECT_ID}")

    # Ensure datasets/tables exist for the target project
    ensure_datasets_and_tables()
    
    success_count = 0
    
    # Load incidents
    if load_incidents_data():
        success_count += 1
    
    # Load policy sections
    if load_policy_sections_data():
        success_count += 1
    
    # Create daily metrics
    if create_sample_daily_metrics():
        success_count += 1
    
    # Verify loading
    if verify_data_loading():
        success_count += 1
    
    logger.info(f"🎉 Data loading completed! {success_count}/4 steps successful")
    
    if success_count == 4:
        logger.info("✅ All data loaded successfully! Ready to run enhanced demo.")
    else:
        logger.warning("⚠️ Some data loading steps failed. Check logs above.")

if __name__ == "__main__":
    main()
