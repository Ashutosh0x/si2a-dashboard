#!/usr/bin/env python3
"""
Create BigQuery connections for Vertex AI and Cloud Storage
"""

import logging
from google.cloud import bigquery

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "shadow-it-incident-autopilot"
LOCATION = "US"

def create_vertex_ai_connection():
    """Create BigQuery connection to Vertex AI"""
    logger.info("🔗 Creating Vertex AI connection...")
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Create connection configuration
        connection_config = {
            "connection_type": "CLOUD_RESOURCE",
            "cloud_resource": {
                "service_account_id": f"{PROJECT_ID}@appspot.gserviceaccount.com"
            }
        }
        
        # Create connection
        connection = client.create_connection(
            connection_id="vertex_ai_connection",
            location=LOCATION,
            connection_config=connection_config
        )
        
        logger.info(f"✅ Vertex AI connection created: {connection.name}")
        return connection
        
    except Exception as e:
        logger.error(f"❌ Failed to create Vertex AI connection: {e}")
        return None

def create_gcs_connection():
    """Create BigQuery connection to Cloud Storage"""
    logger.info("🔗 Creating Cloud Storage connection...")
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Create connection configuration
        connection_config = {
            "connection_type": "CLOUD_RESOURCE",
            "cloud_resource": {
                "service_account_id": f"{PROJECT_ID}@appspot.gserviceaccount.com"
            }
        }
        
        # Create connection
        connection = client.create_connection(
            connection_id="si2a_gcs",
            location=LOCATION,
            connection_config=connection_config
        )
        
        logger.info(f"✅ Cloud Storage connection created: {connection.name}")
        return connection
        
    except Exception as e:
        logger.error(f"❌ Failed to create Cloud Storage connection: {e}")
        return None

def main():
    """Main function"""
    logger.info(f"🚀 Creating BigQuery connections for project: {PROJECT_ID}")
    
    # Create connections
    vertex_connection = create_vertex_ai_connection()
    gcs_connection = create_gcs_connection()
    
    if vertex_connection and gcs_connection:
        logger.info("🎉 All connections created successfully!")
        logger.info("📋 Next steps:")
        logger.info("   1. Update SQL files to use connection names")
        logger.info("   2. Create embeddings and vector indexes")
        logger.info("   3. Set up Object Tables")
        logger.info("   4. Run the demo")
    else:
        logger.error("❌ Some connections failed to create")

if __name__ == "__main__":
    main()
