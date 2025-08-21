#!/usr/bin/env python3
"""
Set up vector search assets:
- Create datasets: si2a_feat (if not exists)
- Load policy sections from data/synthetic_policy_sections.csv into si2a_dim.policy_sections
- Create incident embeddings in si2a_feat.incident_text_embed
- Create policy embeddings in si2a_feat.policy_embed
- Create vector indexes with index_row_id
"""
import os
from pathlib import Path
from google.cloud import bigquery
import google.auth
from google.auth import load_credentials_from_file
import pandas as pd

PROJECT_ID = os.getenv('PROJECT_ID', 'qwiklabs-gcp-01-786e02d76fb0')
LOCATION = os.getenv('BIGQUERY_LOCATION', 'US')
DIM_DATASET = 'si2a_dim'
FEAT_DATASET = 'si2a_feat'
POLICY_CSV = Path('data') / 'synthetic_policy_sections.csv'

# Remote embedding model configuration (BigQuery model that proxies Vertex AI)
VERTEX_LOCATION = os.getenv('VERTEX_LOCATION', 'us-east4')
REMOTE_MODEL_NAME = f"{PROJECT_ID}.{FEAT_DATASET}.textembed_model"


def ensure_dataset(client: bigquery.Client, dataset_id: str) -> None:
    ds_ref = bigquery.Dataset(f"{client.project}.{dataset_id}")
    ds_ref.location = LOCATION
    try:
        client.get_dataset(ds_ref)
        print(f"✅ Dataset exists: {dataset_id}")
    except Exception:
        client.create_dataset(ds_ref)
        print(f"🆕 Created dataset: {dataset_id}")


def load_policy_sections(client: bigquery.Client) -> None:
    table_id = f"{PROJECT_ID}.{DIM_DATASET}.policy_sections"
    print("📥 Loading policy sections CSV ...")
    # The CSV has unquoted commas in section_text. Parse manually:
    rows = []
    with open(POLICY_CSV, 'r', encoding='utf-8') as f:
        header = f.readline()
        for line in f:
            parts = [p.strip() for p in line.rstrip('\n').split(',')]
            if len(parts) < 3:
                continue
            section_id = parts[0]
            section_title = parts[2]
            # section_text spans from index 3 up to the token that looks like section_number (e.g., 1.1)
            # Find the first token matching \d+(\.\d+)? and treat everything before it (from idx 3) as section_text
            idx = 3
            while idx < len(parts) and not __import__('re').match(r"^\d+(?:\.\d+)?$", parts[idx] or ''):
                idx += 1
            section_text = ','.join(parts[3:idx]).strip()
            if not section_text:
                # Fallback: join everything from 3 to end if pattern not found
                section_text = ','.join(parts[3:]).strip()
            rows.append({'section_id': section_id, 'section_title': section_title, 'section_text': section_text})
    df = pd.DataFrame(rows, columns=['section_id', 'section_title', 'section_text'])
    job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)
    load = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    load.result()
    print(f"✅ Policy sections loaded into {table_id}")


def run_query(client: bigquery.Client, sql: str):
    job = client.query(sql)
    job.result()

def create_remote_model(client: bigquery.Client) -> None:
    print("🛠️ Creating/refreshing remote embedding model ...")
    run_query(client, f"""
    CREATE OR REPLACE MODEL `{REMOTE_MODEL_NAME}`
    OPTIONS (
      MODEL_TYPE = 'VERTEX_AI',
      REMOTE_SERVICE_TYPE = 'CLOUD_AI',
      REMOTE_SERVICE_REGION = '{VERTEX_LOCATION}',
      MODEL_VERSION = 'textembedding-gecko@001'
    );
    """)
    print(f"✅ Remote model ready: {REMOTE_MODEL_NAME}")


def build_embeddings_and_indexes(client: bigquery.Client) -> None:
    # Incidents embedding table
    print("🧠 Creating incident embeddings ...")
    run_query(client, f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{FEAT_DATASET}.incident_text_embed` AS
    SELECT 
      i.incident_id,
      CONCAT(COALESCE(i.title,''), '\\n', COALESCE(i.description,''), '\\n', COALESCE(i.category,''), '\\n', COALESCE(i.root_cause,'')) AS text_corpus,
      ML.GENERATE_EMBEDDING(MODEL `{REMOTE_MODEL_NAME}`, CONCAT(COALESCE(i.title,''), '\\n', COALESCE(i.description,''), '\\n', COALESCE(i.category,''), '\\n', COALESCE(i.root_cause,''))) AS embedding
    FROM `{PROJECT_ID}.si2a_gold.incidents` i;
    """)

    # Policy embedding table
    print("🧠 Creating policy embeddings ...")
    run_query(client, f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{FEAT_DATASET}.policy_embed` AS
    SELECT 
      p.section_id,
      p.section_title,
      p.section_text,
      ML.GENERATE_EMBEDDING(MODEL `{REMOTE_MODEL_NAME}`, COALESCE(p.section_text, '')) AS embedding
    FROM `{PROJECT_ID}.{DIM_DATASET}.policy_sections` p;
    """)

    # Vector indexes (with row id)
    print("📇 Creating vector indexes ...")
    run_query(client, f"""
    CREATE VECTOR INDEX `{PROJECT_ID}.{FEAT_DATASET}.vx_incident_text`
    ON `{PROJECT_ID}.{FEAT_DATASET}.incident_text_embed`(embedding)
    OPTIONS(distance_type = 'COSINE', index_row_id = 'incident_id');
    """)

    run_query(client, f"""
    CREATE VECTOR INDEX `{PROJECT_ID}.{FEAT_DATASET}.vx_policy`
    ON `{PROJECT_ID}.{FEAT_DATASET}.policy_embed`(embedding)
    OPTIONS(distance_type = 'COSINE', index_row_id = 'section_id');
    """)


def make_client() -> bigquery.Client:
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    adc_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    creds = None
    if adc_path and os.path.exists(adc_path):
        creds, _ = load_credentials_from_file(adc_path, scopes=scopes)
    else:
        # Windows gcloud ADC default location
        appdata = os.getenv('APPDATA') or ''
        fallback = os.path.join(appdata, 'gcloud', 'application_default_credentials.json')
        if os.path.exists(fallback):
            creds, _ = load_credentials_from_file(fallback, scopes=scopes)
    return bigquery.Client(project=PROJECT_ID, credentials=creds)

if __name__ == '__main__':
    client = make_client()
    print(f"🔗 Project: {PROJECT_ID} in {LOCATION}")
    ensure_dataset(client, DIM_DATASET)
    ensure_dataset(client, FEAT_DATASET)
    create_remote_model(client)
    if POLICY_CSV.exists():
        load_policy_sections(client)
    else:
        print("⚠️ Policy CSV not found, skipping load")
    build_embeddings_and_indexes(client)
    print("🎯 Vector search assets ready.")
