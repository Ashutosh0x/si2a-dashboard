#!/usr/bin/env python3
"""
Manual setup guide for SI²A BigQuery environment
This script provides step-by-step instructions for setting up the project
when gcloud CLI is not available.
"""

import os
import sys

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step_num, title, description):
    print(f"\n{step_num}. {title}")
    print(f"   {description}")

def main():
    print_header("SI²A Manual Setup Guide")
    print("Since gcloud CLI is not available, follow these manual steps:")
    
    print_step(1, "Google Cloud Console Setup", 
               "Open https://console.cloud.google.com and select project 'hackathon-e5521'")
    
    print_step(2, "Enable APIs", 
               "Go to APIs & Services > Library and enable these APIs:")
    apis = [
        "BigQuery API",
        "BigQuery Storage API", 
        "BigQuery Connection API",
        "Vertex AI API",
        "Cloud Storage API"
    ]
    for api in apis:
        print(f"   • {api}")
    
    print_step(3, "Create Datasets", 
               "In BigQuery Console, create these datasets:")
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
    for dataset in datasets:
        print(f"   • {dataset}")
    
    print_step(4, "Create Cloud Storage Bucket",
               "In Cloud Storage Console, create bucket: si2a-artifacts-{PROJECT_ID}")
    
    print_step(5, "Create BigQuery Connection",
               "In BigQuery Console > Connections, create a Cloud Resource connection named 'si2a_gcs'")
    
    print_step(6, "Run SQL Scripts",
               "Execute the SQL files in the sql/ directory in order:")
    sql_files = [
        "01_ddl_tables.sql",
        "02_embeddings_and_vector_search.sql", 
        "03_generative_ai_architect.sql",
        "04_multimodal_pioneer.sql"
    ]
    for sql_file in sql_files:
        print(f"   • {sql_file}")
    
    print_step(7, "Update Connection Reference",
               "In sql/04_multimodal_pioneer.sql, replace 'LOCATION' with your connection name")
    
    print_step(8, "Test Setup",
               "Run: python demo_si2a.py")
    
    print("\n" + "="*60)
    print("  Alternative: Quick Demo with Mock Data")
    print("="*60)
    print("If you want to see the demo working immediately, run:")
    print("python demo_si2a.py --mock")
    
    print("\n" + "="*60)
    print("  Need Help?")
    print("="*60)
    print("• Check SETUP_GUIDE.md for detailed instructions")
    print("• Review the SQL files in sql/ directory")
    print("• Look at demo_si2a.py for example usage")

if __name__ == "__main__":
    main()
