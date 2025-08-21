#!/usr/bin/env python3
"""
Deployment script for SI²A Dashboard to Google Cloud App Run
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🚀 {description}...")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"   ✅ {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"   ❌ {description} failed")
        print(f"   Error: {e.stderr}")
        return None

def check_prerequisites():
    """Check if required tools are available"""
    print("🔍 Checking prerequisites...")
    
    # Check gcloud CLI
    try:
        result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Google Cloud CLI (gcloud) is available")
        else:
            print("   ❌ Google Cloud CLI (gcloud) not found")
            return False
    except FileNotFoundError:
        print("   ❌ Google Cloud CLI (gcloud) not found")
        return False
    
    # Check Docker
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Docker is available")
        else:
            print("   ❌ Docker not found")
            return False
    except FileNotFoundError:
        print("   ❌ Docker not found")
        return False
    
    return True

def get_project_config():
    """Get project configuration from environment or user input"""
    print("\n⚙️  Project Configuration")
    
    # Get project ID
    project_id = os.getenv('PROJECT_ID')
    if not project_id:
        project_id = input("Enter your Google Cloud Project ID: ").strip()
        if not project_id:
            print("❌ Project ID is required")
            sys.exit(1)
    
    # Get region
    region = os.getenv('REGION', 'us-central1')
    print(f"   Project ID: {project_id}")
    print(f"   Region: {region}")
    
    return project_id, region

def build_and_deploy(project_id, region):
    """Build and deploy the application to Cloud Run"""
    print(f"\n🚀 Building and deploying to Cloud Run...")
    
    # Set project
    if not run_command(f"gcloud config set project {project_id}", "Setting Google Cloud project"):
        return False
    
    # Build and deploy
    deploy_command = f"""
    gcloud run deploy si2a-dashboard \\
        --source . \\
        --platform managed \\
        --region {region} \\
        --allow-unauthenticated \\
        --memory 2Gi \\
        --cpu 2 \\
        --timeout 300 \\
        --set-env-vars PROJECT_ID={project_id}
    """
    
    if not run_command(deploy_command, "Deploying to Cloud Run"):
        return False
    
    return True

def get_service_url(project_id, region):
    """Get the deployed service URL"""
    print(f"\n🔗 Getting service URL...")
    
    command = f"gcloud run services describe si2a-dashboard --region={region} --format='value(status.url)'"
    result = run_command(command, "Getting service URL")
    
    if result and result.stdout:
        service_url = result.stdout.strip()
        print(f"   🌐 Your dashboard is available at: {service_url}")
        return service_url
    else:
        print("   ❌ Failed to get service URL")
        return None

def main():
    """Main deployment function"""
    print("🚀 SI²A Dashboard - Google Cloud App Run Deployment")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install:")
        print("   - Google Cloud CLI (gcloud)")
        print("   - Docker")
        sys.exit(1)
    
    # Get configuration
    project_id, region = get_project_config()
    
    # Check if user is authenticated
    print(f"\n🔐 Checking authentication...")
    auth_result = run_command("gcloud auth list --filter=status:ACTIVE --format='value(account)'", "Checking authentication")
    
    if not auth_result or not auth_result.stdout.strip():
        print("   ❌ Not authenticated. Please run: gcloud auth login")
        sys.exit(1)
    
    print(f"   ✅ Authenticated as: {auth_result.stdout.strip()}")
    
    # Build and deploy
    if not build_and_deploy(project_id, region):
        print("\n❌ Deployment failed")
        sys.exit(1)
    
    # Get service URL
    service_url = get_service_url(project_id, region)
    
    if service_url:
        print(f"\n🎉 Deployment completed successfully!")
        print(f"   Dashboard URL: {service_url}")
        print(f"\n📋 Next steps:")
        print(f"   1. Open the dashboard URL in your browser")
        print(f"   2. Test all features and functionality")
        print(f"   3. Monitor logs: gcloud logs tail --service=si2a-dashboard --region={region}")
        print(f"   4. Update service: gcloud run services update si2a-dashboard --region={region}")
    else:
        print("\n⚠️  Deployment may have succeeded but couldn't get service URL")
        print("   Check the Cloud Run console for your service")

if __name__ == "__main__":
    main()
