#!/usr/bin/env python3
"""
Run SQL setup files using BigQuery client
"""

import os
import logging
from google.cloud import bigquery

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("PROJECT_ID", "shadow-it-incident-autopilot")
LOCATION = os.getenv("BIGQUERY_LOCATION", "US")

def run_sql_file(client, file_path):
    """Execute SQL file"""
    logger.info(f"Executing {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Replace placeholders
        sql = sql.replace('${PROJECT_ID}', PROJECT_ID)
        sql = sql.replace('${LOCATION}', LOCATION)
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        for i, statement in enumerate(statements):
            if statement:
                try:
                    query_job = client.query(statement)
                    query_job.result()  # Wait for completion
                    logger.info(f"✅ Statement {i+1} executed successfully")
                except Exception as e:
                    logger.warning(f"⚠️ Statement {i+1} failed: {e}")
                    # Continue with next statement
        
        logger.info(f"✅ Completed {file_path}")
        
    except Exception as e:
        logger.error(f"❌ Failed to execute {file_path}: {e}")

def main():
    """Main function"""
    logger.info(f"🚀 Running SQL setup for project: {PROJECT_ID}")
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project=PROJECT_ID)
        
        # Run the fixed DDL file
        run_sql_file(client, "sql/01_ddl_tables_fixed.sql")
        
        logger.info("🎉 SQL setup completed!")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    main()
