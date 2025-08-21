#!/usr/bin/env python3
"""
Seed minimal data into BigQuery for SI²A charts to render.
Creates table `si2a_gold.incidents` if missing and inserts one row.
"""

import os
from google.cloud import bigquery

PROJECT_ID = os.getenv("PROJECT_ID")
if not PROJECT_ID:
    raise SystemExit("PROJECT_ID env var required")

client = bigquery.Client(project=PROJECT_ID)

create_sql = f"""
CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.si2a_gold.incidents` (
  incident_id STRING,
  title STRING,
  description STRING,
  severity STRING,
  status STRING,
  created_at TIMESTAMP,
  assigned_to STRING,
  category STRING,
  root_cause STRING,
  resolution STRING,
  resolution_time_hours FLOAT64,
  affected_users INT64,
  affected_systems ARRAY<STRING>,
  tags ARRAY<STRING>,
  business_impact STRING,
  risk_score FLOAT64
)
"""

insert_sql = f"""
INSERT INTO `{PROJECT_ID}.si2a_gold.incidents`
(incident_id,title,description,severity,status,created_at,assigned_to,category,root_cause,resolution,resolution_time_hours,affected_users,affected_systems,tags,business_impact,risk_score)
VALUES ('INC-BOOT-001','Bootstrap Incident','Seed row','medium','resolved',CURRENT_TIMESTAMP(),'analyst','general','N/A','N/A',2.5,1,['sys'],['seed'],'Low impact',0.5)
"""

client.query(create_sql).result()
client.query(insert_sql).result()
print("Seeded incidents table with 1 row")


