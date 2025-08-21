#!/usr/bin/env python3
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = 'shadow-it-incident-autopilot'
TABLE = f"`{PROJECT_ID}.si2a_gold.incidents`"

c = bigquery.Client(project=PROJECT_ID)
print("Connected to BigQuery")

print("/api/incidents -> top 3 rows")
q_inc = f"""
SELECT incident_id,title,description,severity,status,created_at,assigned_to,category,root_cause,resolution,
       resolution_time_hours,affected_users,affected_systems,tags,business_impact,risk_score
FROM {TABLE}
ORDER BY created_at DESC
LIMIT 3
"""
df_inc = c.query(q_inc).to_dataframe()
print(df_inc.dtypes)
print(df_inc.head(3))

print("/api/metrics")
q_met = f"""
SELECT severity,
       COUNT(*) as count,
       AVG(resolution_time_hours) as avg_resolution_time,
       AVG(risk_score) as avg_risk_score,
       SUM(affected_users) as total_affected_users
FROM {TABLE}
GROUP BY severity
ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 ELSE 5 END
"""
df_met = c.query(q_met).to_dataframe()
print(df_met)
print({
    'total_incidents': int(df_met['count'].sum()),
    'avg_mttr': float(df_met['avg_resolution_time'].mean()) if not pd.isna(df_met['avg_resolution_time'].mean()) else 0.0,
    'avg_risk_score': float(df_met['avg_risk_score'].mean()) if not pd.isna(df_met['avg_risk_score'].mean()) else 0.0,
})

print("/api/charts/risk-distribution")
q_risk = f"""
SELECT CASE 
         WHEN risk_score >= 0.8 THEN 'Critical (0.8-1.0)'
         WHEN risk_score >= 0.6 THEN 'High (0.6-0.79)'
         WHEN risk_score >= 0.4 THEN 'Medium (0.4-0.59)'
         WHEN risk_score >= 0.2 THEN 'Low (0.2-0.39)'
         ELSE 'Minimal (0.0-0.19)'
       END AS risk_category,
       COUNT(*) as count
FROM {TABLE}
GROUP BY risk_category
ORDER BY risk_category
"""
print(c.query(q_risk).to_dataframe())

print("/api/trends")
q_trend = f"""
SELECT DATE(created_at) as date,
       COUNT(*) as incident_count,
       AVG(risk_score) as avg_risk_score,
       AVG(resolution_time_hours) as avg_resolution_time
FROM {TABLE}
GROUP BY date
ORDER BY date
"""
print(c.query(q_trend).to_dataframe().tail(5))
