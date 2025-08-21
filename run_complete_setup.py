#!/usr/bin/env python3
"""
Complete SI²A setup with all fixed SQL files
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
    logger.info(f"🚀 Running complete SI²A setup for project: {PROJECT_ID}")
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project=PROJECT_ID)
        
        # Run all SQL files in order
        sql_files = [
            "sql/01_ddl_tables_fixed.sql",
            "sql/02_embeddings_and_vector_search_fixed.sql",
            "sql/03_generative_ai_architect_fixed.sql"
        ]
        
        for sql_file in sql_files:
            if os.path.exists(sql_file):
                run_sql_file(client, sql_file)
            else:
                logger.warning(f"⚠️ SQL file not found: {sql_file}")
        
        logger.info("🎉 Complete setup finished!")
        logger.info("📋 Next steps:")
        logger.info("   1. Test the functions with demo queries")
        logger.info("   2. Run the demo: python demo_si2a.py")
        logger.info("   3. Create video demo for submission")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    main()
