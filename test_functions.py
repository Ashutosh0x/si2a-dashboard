#!/usr/bin/env python3
"""
Test BigQuery functions and show working capabilities
"""

import logging
from google.cloud import bigquery

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "shadow-it-incident-autopilot"

def test_functions():
    """Test BigQuery functions"""
    logger.info(f"🧪 Testing BigQuery functions in project: {PROJECT_ID}")
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Test 1: Executive Summary Generation
        logger.info("📊 Testing Executive Summary Generation...")
        query = f"""
        SELECT `si2a_fn_generate_executive_summary`('INC-2024-002') as executive_summary
        """
        
        try:
            query_job = client.query(query)
            results = query_job.result()
            
            print("\n📋 Executive Summary Generation:")
            print("=" * 80)
            for row in results:
                print(row.executive_summary)
                print()
        except Exception as e:
            logger.warning(f"⚠️ Executive summary failed: {e}")
        
        # Test 2: Incident Classification
        logger.info("🏷️ Testing Incident Classification...")
        query = f"""
        SELECT `si2a_fn_classify_incident`('User downloaded large amount of customer data to personal device') as classification
        """
        
        try:
            query_job = client.query(query)
            results = query_job.result()
            
            print("🏷️ Incident Classification:")
            print("=" * 80)
            for row in results:
                print(f"Classification: {row.classification}")
                print()
        except Exception as e:
            logger.warning(f"⚠️ Classification failed: {e}")
        
        # Test 3: Policy Compliance Check
        logger.info("✅ Testing Policy Compliance Check...")
        query = f"""
        SELECT `si2a_fn_check_policy_compliance`('INC-2024-001', 'SAAS-001') as violates
        """
        
        try:
            query_job = client.query(query)
            results = query_job.result()
            
            print("✅ Policy Compliance Check:")
            print("=" * 80)
            for row in results:
                status = "VIOLATES" if row.violates else "COMPLIES"
                print(f"Policy Compliance: {status}")
                print()
        except Exception as e:
            logger.warning(f"⚠️ Compliance check failed: {e}")
        
        # Test 4: Risk Assessment
        logger.info("⚠️ Testing Risk Assessment...")
        query = f"""
        SELECT * FROM `si2a_fn_assess_incident_risk`('INC-2024-002')
        """
        
        try:
            query_job = client.query(query)
            results = query_job.result()
            
            print("⚠️ Risk Assessment:")
            print("=" * 80)
            for row in results:
                print(f"Risk Level: {row.risk_level}")
                print(f"Adjusted Risk Score: {row.adjusted_risk_score}")
                print()
        except Exception as e:
            logger.warning(f"⚠️ Risk assessment failed: {e}")
        
        # Test 5: Root Cause Analysis
        logger.info("🔍 Testing Root Cause Analysis...")
        query = f"""
        SELECT `si2a_fn_analyze_root_cause`('INC-2024-003') as root_cause_analysis
        """
        
        try:
            query_job = client.query(query)
            results = query_job.result()
            
            print("🔍 Root Cause Analysis:")
            print("=" * 80)
            for row in results:
                print(row.root_cause_analysis)
                print()
        except Exception as e:
            logger.warning(f"⚠️ Root cause analysis failed: {e}")
        
        # Test 6: Stakeholder Communication
        logger.info("📢 Testing Stakeholder Communication...")
        query = f"""
        SELECT `si2a_fn_generate_stakeholder_communication`('INC-2024-001', 'executive') as exec_comm
        """
        
        try:
            query_job = client.query(query)
            results = query_job.result()
            
            print("📢 Stakeholder Communication (Executive):")
            print("=" * 80)
            for row in results:
                print(row.exec_comm)
                print()
        except Exception as e:
            logger.warning(f"⚠️ Communication failed: {e}")
        
        logger.info("✅ All function tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_functions()
