#!/usr/bin/env python3
"""
Setup BigQuery for local SI²A demo:
- Creates dataset `si2a_gold` (US)
- Loads `data/synthetic_incidents_clean.csv` into `si2a_gold.incidents_raw` with correct columns
- Creates or replaces TABLE `si2a_gold.incidents` with proper types and parsed arrays
"""
import os
from pathlib import Path
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = os.getenv('PROJECT_ID', 'shadow-it-incident-autopilot')
DATASET_ID = 'si2a_gold'
LOCATION = os.getenv('BIGQUERY_LOCATION', 'US')
# Use the normalized CSV that avoids comma-induced misalignment and uses semicolon-delimited lists
CSV_PATH = Path('data') / 'synthetic_incidents_fixed.csv'

EXPECTED_COLUMNS = [
    'incident_id','title','description','severity','status','created_at','updated_at',
    'assigned_to','category','root_cause','resolution','resolution_time_hours','affected_users',
    'affected_systems','tags','artifacts','business_impact','risk_score','created_by','last_modified_by'
]

def ensure_dataset(client: bigquery.Client, dataset_id: str) -> None:
    dataset_ref = bigquery.Dataset(f"{client.project}.{dataset_id}")
    dataset_ref.location = LOCATION
    try:
        client.get_dataset(dataset_ref)
        print(f"✅ Dataset exists: {dataset_id}")
    except Exception:
        client.create_dataset(dataset_ref)
        print(f"🆕 Created dataset: {dataset_id}")

def load_csv_to_raw(client: bigquery.Client) -> str:
    table_id = f"{PROJECT_ID}.{DATASET_ID}.incidents_raw"

    # Read CSV with pandas to ensure correct column names and quoting handling
    print("📥 Reading CSV with pandas ...")
    df = pd.read_csv(
        CSV_PATH,
        dtype=str,
        keep_default_na=False,
        engine='python'
    )

    # Ensure expected columns exist and in order
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise RuntimeError(f"CSV missing expected columns: {missing}")
    df = df[EXPECTED_COLUMNS]

    # Upload dataframe, truncate if table exists
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    print(f"📤 Loading DataFrame to {table_id} ...")
    load_job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    load_job.result()
    table = client.get_table(table_id)
    print(f"✅ Loaded {table.num_rows} rows into {table_id}")
    return table_id

TABLE_SQL = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.incidents` AS
SELECT
  SAFE_CAST(incident_id AS STRING) AS incident_id,
  SAFE_CAST(title AS STRING) AS title,
  SAFE_CAST(description AS STRING) AS description,
  SAFE_CAST(severity AS STRING) AS severity,
  SAFE_CAST(status AS STRING) AS status,
  SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', created_at) AS created_at,
  SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', updated_at) AS updated_at,
  SAFE_CAST(assigned_to AS STRING) AS assigned_to,
  SAFE_CAST(category AS STRING) AS category,
  SAFE_CAST(root_cause AS STRING) AS root_cause,
  SAFE_CAST(resolution AS STRING) AS resolution,
  SAFE_CAST(resolution_time_hours AS FLOAT64) AS resolution_time_hours,
  SAFE_CAST(affected_users AS INT64) AS affected_users,
  -- Parse semicolon-delimited lists into arrays, trim whitespace
  ARRAY(SELECT TRIM(part) FROM UNNEST(SPLIT(IFNULL(affected_systems, ''), ';')) AS part WHERE TRIM(part) != '') AS affected_systems,
  ARRAY(SELECT TRIM(part) FROM UNNEST(SPLIT(IFNULL(tags, ''), ';')) AS part WHERE TRIM(part) != '') AS tags,
  ARRAY(SELECT TRIM(part) FROM UNNEST(SPLIT(IFNULL(artifacts, ''), ';')) AS part WHERE TRIM(part) != '') AS artifacts,
  SAFE_CAST(business_impact AS STRING) AS business_impact,
  SAFE_CAST(risk_score AS FLOAT64) AS risk_score,
  SAFE_CAST(created_by AS STRING) AS created_by,
  SAFE_CAST(last_modified_by AS STRING) AS last_modified_by
FROM `{PROJECT_ID}.{DATASET_ID}.incidents_raw`;
"""

def create_typed_table(client: bigquery.Client) -> None:
    print("🧱 Creating typed table si2a_gold.incidents ...")
    client.query(TABLE_SQL).result()
    print("✅ Table created: si2a_gold.incidents")

if __name__ == '__main__':
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV not found: {CSV_PATH}")
    client = bigquery.Client(project=PROJECT_ID)
    print(f"🔗 Using project: {PROJECT_ID} in {LOCATION}")
    ensure_dataset(client, DATASET_ID)
    load_csv_to_raw(client)
    create_typed_table(client)
    print("🎉 BigQuery local demo setup complete.")
