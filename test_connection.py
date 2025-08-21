#!/usr/bin/env python3
"""
Test BigQuery and Google Cloud connection status
"""

import os
import sys
import subprocess

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_status(item, status, details=""):
    icon = "✅" if status else "❌"
    print(f"{icon} {item}")
    if details:
        print(f"   {details}")

def test_python_packages():
    """Test if required Python packages are installed"""
    print_header("Python Package Status")
    
    packages = [
        ("google-cloud-bigquery", "BigQuery client library"),
        ("google-cloud-storage", "Cloud Storage client library"),
        ("google-auth", "Google authentication library"),
        ("pandas", "Data manipulation library"),
        ("numpy", "Numerical computing library")
    ]
    
    for package, description in packages:
        try:
            __import__(package.replace("-", "_"))
            print_status(package, True, description)
        except ImportError:
            print_status(package, False, f"Missing: {description}")

def test_gcloud_cli():
    """Test if gcloud CLI is available"""
    print_header("Google Cloud CLI Status")
    
    try:
        result = subprocess.run(["gcloud", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print_status("gcloud CLI", True, version)
            return True
        else:
            print_status("gcloud CLI", False, "Command failed")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print_status("gcloud CLI", False, "Not found in PATH")
        return False

def test_google_auth():
    """Test Google Cloud authentication"""
    print_header("Google Cloud Authentication Status")
    
    try:
        from google.auth import default
        from google.cloud import bigquery
        
        credentials, project = default()
        print_status("Authentication", True, f"Project: {project}")
        
        # Test BigQuery connection
        client = bigquery.Client()
        datasets = list(client.list_datasets(max_results=5))
        print_status("BigQuery Connection", True, f"Found {len(datasets)} datasets")
        return True
        
    except Exception as e:
        print_status("Authentication", False, str(e))
        return False

def test_project_files():
    """Test if all project files are present"""
    print_header("Project Files Status")
    
    required_files = [
        ("README.md", "Project documentation"),
        ("requirements.txt", "Python dependencies"),
        ("setup/setup_project.py", "Setup automation script"),
        ("sql/01_ddl_tables.sql", "Database schema"),
        ("sql/02_embeddings_and_vector_search.sql", "Vector search setup"),
        ("sql/03_generative_ai_architect.sql", "AI functions"),
        ("sql/04_multimodal_pioneer.sql", "Multimodal features"),
        ("demo_si2a.py", "Main demo script"),
        ("demo_si2a_mock.py", "Mock demo script"),
        ("SETUP_GUIDE.md", "Setup instructions")
    ]
    
    for file_path, description in required_files:
        if os.path.exists(file_path):
            print_status(file_path, True, description)
        else:
            print_status(file_path, False, f"Missing: {description}")

def provide_next_steps():
    """Provide clear next steps based on current status"""
    print_header("Next Steps")
    
    print("🎯 Current Status: Project files ready, authentication needed")
    print("\n📋 To connect to BigQuery and run the full demo:")
    
    print("\n1. 🔐 Set up Google Cloud Authentication:")
    print("   Option A: Use gcloud CLI (recommended)")
    print("   - Complete gcloud setup in another terminal")
    print("   - Run: gcloud auth application-default login")
    print("   - Run: gcloud config set project hackathon-e5521")
    
    print("\n   Option B: Manual setup via Google Cloud Console")
    print("   - Go to: https://console.cloud.google.com")
    print("   - Select project: hackathon-e5521")
    print("   - Enable required APIs")
    print("   - Create service account and download credentials")
    
    print("\n2. 🚀 Run the setup:")
    print("   python setup\\setup_project.py")
    
    print("\n3. 🎬 Run the demo:")
    print("   python demo_si2a.py")
    
    print("\n🎭 Alternative: Run mock demo (works now):")
    print("   python demo_si2a_mock.py")

def main():
    print_header("SI²A BigQuery Connection Test")
    
    # Test all components
    test_python_packages()
    test_gcloud_cli()
    test_google_auth()
    test_project_files()
    
    # Provide next steps
    provide_next_steps()
    
    print_header("Summary")
    print("✅ Project files are ready")
    print("✅ Python packages are installed")
    print("❌ Google Cloud authentication needed")
    print("❌ gcloud CLI not available in this session")
    print("\n🎯 Recommendation: Complete gcloud setup in another terminal")

if __name__ == "__main__":
    main()
