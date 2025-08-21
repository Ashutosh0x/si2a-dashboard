#!/usr/bin/env python3
"""
SI²A BigQuery Setup Script
Automates the creation of BigQuery datasets, tables, and AI functions
"""

import os
import sys
import logging
from google.cloud import bigquery
from google.cloud import storage
from google.auth import default

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "shadow-it-incident-autopilot"  # Updated project ID
LOCATION = "US"

def create_datasets(client):
    """Create all required datasets"""
    datasets = [
        "si2a",
        "si2a_raw", 
        "si2a_feat",
        "si2a_gold",
        "si2a_dim",
        "si2a_marts",
        "si2a_analysis",
        "si2a_logs",
        "si2a_notifications",
        "si2a_feedback"
    ]
    
    for dataset_id in datasets:
        dataset_ref = client.dataset(dataset_id)
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = LOCATION
        
        try:
            dataset = client.create_dataset(dataset, exists_ok=True)
            logger.info(f"✅ Dataset {dataset_id} created/verified")
        except Exception as e:
            logger.error(f"❌ Failed to create dataset {dataset_id}: {e}")

def create_gcs_bucket():
    """Create Cloud Storage bucket for artifacts"""
    bucket_name = f"si2a-artifacts-{PROJECT_ID}"
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        if not bucket.exists():
            bucket = storage_client.create_bucket(bucket, location=LOCATION)
            logger.info(f"✅ GCS bucket {bucket_name} created")
        else:
            logger.info(f"✅ GCS bucket {bucket_name} already exists")
            
    except Exception as e:
        logger.error(f"❌ Failed to create GCS bucket: {e}")

def execute_sql_file(client, file_path):
    """Execute SQL file"""
    try:
        with open(file_path, 'r') as f:
            sql = f.read()
        
        # Replace placeholders
        sql = sql.replace('${PROJECT_ID}', PROJECT_ID)
        sql = sql.replace('${LOCATION}', LOCATION)
        
        query_job = client.query(sql)
        query_job.result()  # Wait for completion
        
        logger.info(f"✅ Executed {file_path}")
        
    except Exception as e:
        logger.error(f"❌ Failed to execute {file_path}: {e}")

def main():
    """Main setup function"""
    logger.info(f"🚀 Setting up SI²A for project: {PROJECT_ID}")
    logger.info(f"📍 Location: {LOCATION}")
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project=PROJECT_ID)
        
        # Create datasets
        logger.info("📊 Creating datasets...")
        create_datasets(client)
        
        # Create GCS bucket
        logger.info("🪣 Creating Cloud Storage bucket...")
        create_gcs_bucket()
        
        # Execute SQL files in order
        sql_files = [
            "sql/01_ddl_tables.sql",
            "sql/02_embeddings_and_vector_search.sql",
            "sql/03_generative_ai_architect.sql",
            "sql/04_multimodal_pioneer.sql"
        ]
        
        logger.info("🔧 Executing SQL setup files...")
        for sql_file in sql_files:
            if os.path.exists(sql_file):
                execute_sql_file(client, sql_file)
            else:
                logger.warning(f"⚠️ SQL file not found: {sql_file}")
        
        logger.info("🎉 SI²A setup completed successfully!")
        logger.info("📋 Next steps:")
        logger.info("   1. Create BigQuery connection: bq mk --connection --connection_type=CLOUD_RESOURCE --project_id=${PROJECT_ID} --location=${LOCATION} si2a_gcs")
        logger.info("   2. Update sql/04_multimodal_pioneer.sql with connection name")
        logger.info("   3. Run demo: python demo_si2a.py")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
