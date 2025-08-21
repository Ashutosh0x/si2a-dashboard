#!/usr/bin/env python3
"""
Test script to check BigQuery connection and table existence
"""

from google.cloud import bigquery
import sys

def test_bigquery():
    try:
        # Initialize client
        client = bigquery.Client(project='shadow-it-incident-autopilot')
        print("✅ Connected to BigQuery project: shadow-it-incident-autopilot")
        
        # Check if incidents table exists
        try:
            query = "SELECT COUNT(*) as count FROM `shadow-it-incident-autopilot.si2a_gold.incidents`"
            result = client.query(query).result()
            count = result.to_dataframe()['count'].iloc[0]
            print(f"✅ Found {count} incidents in the table")
            return True
        except Exception as e:
            print(f"❌ Incidents table not found or accessible: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to BigQuery: {e}")
        return False

if __name__ == "__main__":
    success = test_bigquery()
    sys.exit(0 if success else 1)
