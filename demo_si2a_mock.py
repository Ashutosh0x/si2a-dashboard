#!/usr/bin/env python3
"""
SI²A Mock Demo - Shows the project functionality without BigQuery setup
This demonstrates the core concepts and workflow of the Shadow IT Incident Autopilot
"""

import os
import sys
import json
from datetime import datetime, timedelta
import pandas as pd

def print_header(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def print_section(title):
    print(f"\n{'-'*60}")
    print(f"  {title}")
    print(f"{'-'*60}")

def simulate_bigquery_ai():
    """Simulate BigQuery AI functions with mock data and responses"""
    
    print_header("🚀 SI²A - Shadow IT Incident Autopilot (Mock Demo)")
    print("This demo shows how BigQuery AI transforms security incident management")
    
    # Mock incident data
    incidents = [
        {
            "incident_id": "INC-2024-001",
            "title": "Unauthorized SaaS Application Detected",
            "description": "Employee downloaded and installed Dropbox for Business without IT approval. Multiple files uploaded to personal account.",
            "severity": "HIGH",
            "status": "OPEN",
            "created_at": "2024-01-15 09:30:00",
            "affected_users": 1,
            "data_exposure": "CONFIRMED"
        },
        {
            "incident_id": "INC-2024-002", 
            "title": "Shadow IT Slack Workspace Found",
            "description": "Team created private Slack workspace for project collaboration. Contains sensitive client data and internal discussions.",
            "severity": "MEDIUM",
            "status": "INVESTIGATING",
            "created_at": "2024-01-16 14:15:00",
            "affected_users": 8,
            "data_exposure": "POTENTIAL"
        }
    ]
    
    print_section("📊 1. AI Architect: Executive Summary Generation")
    print("Using AI.GENERATE to create executive summaries...")
    
    for incident in incidents:
        print(f"\n📋 Incident: {incident['incident_id']}")
        print(f"Title: {incident['title']}")
        
        # Simulate AI.GENERATE executive summary
        summary = f"""
🔍 EXECUTIVE SUMMARY:
• Scope: {incident['affected_users']} user(s) affected
• Root Cause: {incident['description'].split('.')[0]}
• Blast Radius: {incident['data_exposure']} data exposure
• User Impact: {incident['severity']} severity level
• Immediate Actions: Isolate affected accounts, review data access logs
        """.strip()
        print(summary)
    
    print_section("🔍 2. Semantic Detective: Similar Incident Search")
    print("Using VECTOR_SEARCH to find semantically similar past incidents...")
    
    # Simulate vector search results
    similar_incidents = [
        {
            "incident_id": "INC-2023-045",
            "title": "Google Drive Personal Account Usage",
            "similarity_score": 0.89,
            "resolution": "User training + policy enforcement"
        },
        {
            "incident_id": "INC-2023-032", 
            "title": "Trello Board with Customer Data",
            "similarity_score": 0.76,
            "resolution": "Data migration + access controls"
        }
    ]
    
    print("🔍 Similar incidents found:")
    for sim in similar_incidents:
        print(f"   • {sim['incident_id']}: {sim['title']} (similarity: {sim['similarity_score']})")
        print(f"     Resolution: {sim['resolution']}")
    
    print_section("📋 3. AI Architect: Auto-Generated Playbook")
    print("Using AI.GENERATE_TABLE to create structured remediation plans...")
    
    # Simulate AI.GENERATE_TABLE output
    playbook = pd.DataFrame([
        {"step": "1. Account Isolation", "owner": "Security Team", "eta_hours": 2, "tooling": "IAM Console"},
        {"step": "2. Data Assessment", "owner": "Data Protection", "eta_hours": 4, "tooling": "DLP Scanner"},
        {"step": "3. User Notification", "owner": "HR", "eta_hours": 1, "tooling": "Email System"},
        {"step": "4. Policy Review", "owner": "Legal", "eta_hours": 8, "tooling": "Policy Database"},
        {"step": "5. Training Assignment", "owner": "Training Team", "eta_hours": 24, "tooling": "LMS Platform"}
    ])
    
    print(playbook.to_string(index=False))
    
    print_section("✅ 4. AI Architect: Policy Compliance Check")
    print("Using AI.GENERATE_BOOL to check policy violations...")
    
    policies = [
        {"policy_id": "POL-001", "name": "SaaS Approval Policy", "violation": True},
        {"policy_id": "POL-002", "name": "Data Classification Policy", "violation": True},
        {"policy_id": "POL-003", "name": "Access Control Policy", "violation": False}
    ]
    
    for policy in policies:
        status = "❌ VIOLATION" if policy["violation"] else "✅ COMPLIANT"
        print(f"   • {policy['name']}: {status}")
    
    print_section("📈 5. AI Architect: Incident Forecasting")
    print("Using AI.FORECAST to predict incident trends...")
    
    # Simulate forecasting results
    forecast_data = [
        {"date": "2024-01-20", "predicted_incidents": 3, "confidence": 0.85},
        {"date": "2024-01-21", "predicted_incidents": 2, "confidence": 0.82},
        {"date": "2024-01-22", "predicted_incidents": 4, "confidence": 0.78},
        {"date": "2024-01-23", "predicted_incidents": 1, "confidence": 0.90}
    ]
    
    print("📊 7-Day Incident Forecast:")
    for fc in forecast_data:
        print(f"   • {fc['date']}: {fc['predicted_incidents']} incidents (confidence: {fc['confidence']})")
    
    print_section("🖼️ 6. Multimodal Pioneer: Evidence Analysis")
    print("Using Object Tables and ObjectRef for screenshot/PDF analysis...")
    
    evidence = [
        {"type": "screenshot", "filename": "slack_workspace.png", "analysis": "Detected sensitive data in chat messages"},
        {"type": "pdf", "filename": "policy_violation_report.pdf", "analysis": "Confirmed policy breach in section 3.2"},
        {"type": "log", "filename": "access_logs.csv", "analysis": "Identified 15 unauthorized access attempts"}
    ]
    
    for ev in evidence:
        print(f"   • {ev['type'].upper()}: {ev['filename']}")
        print(f"     Analysis: {ev['analysis']}")
    
    print_section("🎯 Business Impact Summary")
    impact_metrics = {
        "MTTR Reduction": "40% faster incident resolution",
        "Closure Rate": "15% improvement in incident closure",
        "Policy Compliance": "Automated detection of 95% violations",
        "Time Saved": "8 hours per incident on average",
        "Cost Savings": "$50,000 annually in manual triage"
    }
    
    for metric, value in impact_metrics.items():
        print(f"   • {metric}: {value}")
    
    print_header("🚀 Next Steps")
    print("To run the full BigQuery AI version:")
    print("1. Complete gcloud setup in another terminal")
    print("2. Run: python setup\\setup_project.py")
    print("3. Run: python demo_si2a.py")
    print("\nOr follow manual setup: python manual_setup.py")

if __name__ == "__main__":
    simulate_bigquery_ai()
