# SI²A Setup Guide for Windows 🚀

This guide will walk you through setting up and running the SI²A (Shadow IT Incident Autopilot) project on Windows.

## Prerequisites

- **Python 3.8+** (you have 3.8.10 ✅)
- **Google Cloud Project** with billing enabled
- **Windows PowerShell** or **Command Prompt**

## Step 1: Install Google Cloud SDK

### Option A: Download and Install (Recommended)
1. Go to: https://cloud.google.com/sdk/docs/install#windows
2. Download `GoogleCloudSDKInstaller.exe`
3. Run as Administrator
4. Follow the installation wizard
5. **Restart PowerShell** after installation

### Option B: Verify Installation
After installation, open a new PowerShell window and run:
```powershell
gcloud --version
```

## Step 2: Set Up Your Environment

### 2.1 Set Environment Variables
```powershell
$env:PROJECT_ID = "your-gcp-project-id"  # Replace with your actual project ID
$env:LOCATION = "US"  # Keep consistent across all services
```

### 2.2 Authenticate with Google Cloud
```powershell
gcloud auth login
gcloud auth application-default login
```

### 2.3 Enable Required APIs
```powershell
gcloud services enable bigquery.googleapis.com
gcloud services enable bigquerystorage.googleapis.com
gcloud services enable bigqueryconnection.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

## Step 3: Set Up Python Environment

### 3.1 Create Virtual Environment (Already Done ✅)
```powershell
python -m venv .venv
```

### 3.2 Activate Virtual Environment (Already Done ✅)
```powershell
.\.venv\Scripts\Activate.ps1
```

### 3.3 Install Dependencies (Already Done ✅)
```powershell
pip install google-cloud-bigquery google-cloud-storage pandas
```

## Step 4: Run Project Setup

### 4.1 Run the Setup Script
```powershell
python setup\setup_project.py
```

This will:
- Create BigQuery datasets (`si2a`, `si2a_raw`, `si2a_feat`, etc.)
- Create GCS buckets for artifacts and policy documents
- Execute SQL scripts to create tables and functions
- Load sample data

### 4.2 Handle Setup Warnings
If you see warnings about "WITH CONNECTION `LOCATION`", that's expected. We'll fix this in the next step.

## Step 5: Create BigQuery Connection (for Object Tables)

### 5.1 Create Cloud Resource Connection
```powershell
bq mk --connection --connection_type=CLOUD_RESOURCE --project_id=$env:PROJECT_ID --location=$env:LOCATION si2a_gcs
```

### 5.2 Fix SQL Connection References
Edit `sql/04_multimodal_pioneer.sql` and replace:
- `WITH CONNECTION \`LOCATION\`` → `WITH CONNECTION \`${LOCATION}.si2a_gcs\``

### 5.3 Re-run Object Table Creation
```powershell
# Run just the object table statements
bq query --use_legacy_sql=false --project_id=$env:PROJECT_ID < sql/04_multimodal_pioneer.sql
```

## Step 6: Run the Demo

### Option A: Using the Batch File (Easiest)
```powershell
# Set your project ID first
$env:PROJECT_ID = "your-gcp-project-id"
.\run_demo.bat
```

### Option B: Using PowerShell Directly
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Set project ID
$env:PROJECT_ID = "your-gcp-project-id"

# Run demo
python demo_si2a.py
```

## Step 7: Optional - Upload Sample Files for Multimodal Analysis

### 7.1 Upload Sample Files
```powershell
# Replace with actual files you have
gsutil cp sample_screenshot.png gs://$env:PROJECT_ID-si2a-artifacts/
gsutil cp sample_security_policy.pdf gs://$env:PROJECT_ID-si2a-policy-docs/
```

### 7.2 Test Multimodal Functions
The demo will automatically test multimodal analysis if files are available.

## Troubleshooting

### Common Issues

#### 1. "gcloud not recognized"
- **Solution**: Install Google Cloud SDK (Step 1)
- **Verify**: `gcloud --version`

#### 2. "Authentication failed"
- **Solution**: Run `gcloud auth application-default login`
- **Verify**: `gcloud auth list`

#### 3. "API not enabled"
- **Solution**: Enable APIs (Step 2.3)
- **Verify**: `gcloud services list --enabled`

#### 4. "Project not found"
- **Solution**: Check your PROJECT_ID is correct
- **Verify**: `gcloud config get-value project`

#### 5. "Permission denied"
- **Solution**: Ensure your account has BigQuery Admin and Storage Admin roles
- **Verify**: Go to IAM & Admin in Google Cloud Console

#### 6. "WITH CONNECTION errors"
- **Solution**: Create BigQuery connection (Step 5)
- **Verify**: `bq ls --connections`

### Getting Help

1. **Check the logs**: Look for specific error messages
2. **Verify permissions**: Ensure your account has the right roles
3. **Check quotas**: Some APIs have usage limits
4. **Review setup**: Make sure all steps were completed

## What the Demo Shows

The demo will demonstrate:

1. **📊 Sample Data**: View incident records
2. **🔍 Similar Incidents**: Vector search for past similar cases
3. **📋 Relevant Policies**: Find applicable policy sections
4. **📝 Executive Summary**: AI-generated business summary
5. **🛠️ Remediation Playbook**: Structured action plan
6. **✅ Compliance Check**: Policy violation detection
7. **📈 Forecasting**: Predict future incident trends

## Next Steps

After running the demo successfully:

1. **Customize**: Modify the SQL functions for your specific needs
2. **Scale**: Add more data and tune the models
3. **Integrate**: Connect to your actual security tools
4. **Deploy**: Set up automated pipelines
5. **Monitor**: Track performance and costs

## Cost Considerations

- **Embeddings**: ~$0.0001 per 1K tokens
- **AI Generation**: ~$0.001 per 1K tokens
- **Storage**: Standard BigQuery pricing
- **Estimated monthly cost**: $50-100 for 1000 incidents

---

**🎉 You're ready to run SI²A! Follow the steps above and enjoy your AI-powered security incident automation!**
