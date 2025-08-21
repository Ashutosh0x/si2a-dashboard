#!/usr/bin/env python3
"""
Simple authentication setup for Google Cloud
"""

import os
import subprocess
import sys
from google.cloud import bigquery
from google.auth import default

def main():
    print("🔐 Setting up Google Cloud authentication...")
    
    # Try to get default credentials
    try:
        credentials, project = default()
        print(f"✅ Authentication successful!")
        print(f"   Project: {project}")
        print(f"   Account: {credentials.service_account_email if hasattr(credentials, 'service_account_email') else 'User account'}")
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\nTo fix this, you need to:")
        print("1. Complete the gcloud setup in the other window")
        print("2. Run: gcloud auth application-default login")
        print("3. Or restart this PowerShell window after gcloud setup")
        return False

if __name__ == "__main__":
    main()
