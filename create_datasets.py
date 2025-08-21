#!/usr/bin/env python3
"""
Create required BigQuery datasets and evidence table for SI²A.
"""

import os
from google.cloud import bigquery

PROJECT_ID = os.getenv("PROJECT_ID", "shadow-it-incident-autopilot")
LOCATION = os.getenv("BIGQUERY_LOCATION", "US")

def ensure_dataset(client: bigquery.Client, dataset_id: str) -> None:
    ds_ref = bigquery.Dataset(f"{PROJECT_ID}.{dataset_id}")
    ds_ref.location = LOCATION
    try:
        client.get_dataset(ds_ref)
    except Exception:
        client.create_dataset(ds_ref, exists_ok=True)

def ensure_evidence_table(client: bigquery.Client) -> None:
    table_id = f"{PROJECT_ID}.si2a_evidence.object_references"
    schema = [
        bigquery.SchemaField("evidence_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("incident_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("object_uri", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("object_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("description", "STRING"),
        bigquery.SchemaField("tags", "STRING", mode="REPEATED"),
        bigquery.SchemaField("uploader", "STRING"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table, exists_ok=True)

def main():
    print(f"Using project: {PROJECT_ID} location: {LOCATION}")
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    datasets = [
        "si2a_raw",
        "si2a_feat",
        "si2a_gold",
        "si2a_dim",
        "si2a_marts",
        "si2a_feedback",
        "si2a_evidence",
    ]
    for ds in datasets:
        ensure_dataset(client, ds)
        print(f"Dataset ensured: {ds}")
    ensure_evidence_table(client)
    print("Evidence table ensured.")

if __name__ == "__main__":
    main()


