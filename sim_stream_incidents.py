#!/usr/bin/env python3
"""
Hybrid streaming generator (Option C)
- Reads 10–20 seed incidents from si2a_gold.incidents
- Mutates fields (severity, risk_score, timestamps, users) to produce realistic variety
- Appends new rows into si2a_gold.incidents in batches, on an interval

Usage:
  PROJECT_ID=your-project BIGQUERY_LOCATION=US python sim_stream_incidents.py --batch-size 5 --interval 10 --iterations 3
"""
import os
import random
import string
import time
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Any

import pandas as pd
from google.cloud import bigquery


PROJECT_ID = os.getenv("PROJECT_ID", "qwiklabs-gcp-01-786e02d76fb0")
LOCATION = os.getenv("BIGQUERY_LOCATION", "US")
DATASET = os.getenv("DATASET", "si2a_gold")
TABLE = f"{PROJECT_ID}.{DATASET}.incidents"


def random_id() -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"INC-{ts}-{suffix}"


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def choose_severity(seed: str) -> str:
    sev_order = ["low", "medium", "high", "critical"]
    weights = {
        "low": [0.7, 0.2, 0.1, 0.0],
        "medium": [0.2, 0.5, 0.25, 0.05],
        "high": [0.05, 0.25, 0.5, 0.2],
        "critical": [0.0, 0.1, 0.3, 0.6],
    }
    seed = (seed or "medium").lower()
    probs = weights.get(seed, [0.2, 0.5, 0.25, 0.05])
    return random.choices(sev_order, probs, k=1)[0]


def mutate_row(row: Dict[str, Any]) -> Dict[str, Any]:
    mutated = dict(row)

    # New identity
    mutated["incident_id"] = random_id()

    # Time: within last 72 hours
    now = datetime.utcnow()
    delta_minutes = random.randint(5, 72 * 60)
    created = now - timedelta(minutes=delta_minutes)
    mutated["created_at"] = created.isoformat()

    # Severity and risk
    base_sev = str(row.get("severity") or "medium")
    new_sev = choose_severity(base_sev)
    mutated["severity"] = new_sev

    base_risk = row.get("risk_score")
    try:
        base_risk = float(base_risk) if base_risk is not None else 0.5
    except Exception:
        base_risk = 0.5
    jitter = random.uniform(-0.15, 0.15)
    mutated["risk_score"] = round(clamp(base_risk + jitter), 2)

    # Users
    au = row.get("affected_users") or 1
    try:
        au = int(au)
    except Exception:
        au = 1
    mutated["affected_users"] = max(1, int(au + random.randint(-1, 5)))

    # Status progression
    mutated["status"] = random.choice(["investigating", "in-progress", "resolved"]) if new_sev != "low" else random.choice(["resolved", "investigating"]) 

    # Assigned_to rotation
    assignees = [
        "security-analyst-1",
        "security-analyst-2",
        "security-analyst-3",
        "incident-responder-1",
    ]
    mutated["assigned_to"] = random.choice(assignees)

    # Resolution time approx by severity
    sev_to_hours = {"low": (0.5, 2), "medium": (1, 6), "high": (2, 12), "critical": (4, 24)}
    lo, hi = sev_to_hours.get(new_sev, (1, 6))
    mutated["resolution_time_hours"] = round(random.uniform(lo, hi), 1)

    # Title suffix to avoid exact duplicates
    mutated["title"] = f"{row.get('title','Incident')} (sim)"

    return mutated


def fetch_seed(client: bigquery.Client, limit: int = 20) -> List[Dict[str, Any]]:
    sql = f"""
    SELECT 
      incident_id, title, description, severity, status, created_at, assigned_to, category,
      root_cause, resolution, resolution_time_hours, affected_users, affected_systems, tags,
      business_impact, risk_score
    FROM `{TABLE}`
    ORDER BY created_at DESC
    LIMIT {limit}
    """
    df = client.query(sql).to_dataframe()
    return df.to_dict("records")


def insert_rows(client: bigquery.Client, rows: List[Dict[str, Any]]):
    def sanitize(v):
        if isinstance(v, np.generic):
            return v.item()
        if isinstance(v, (np.ndarray,)):
            return [sanitize(x) for x in v.tolist()]
        if isinstance(v, list):
            return [sanitize(x) for x in v]
        if isinstance(v, dict):
            return {k: sanitize(val) for k, val in v.items()}
        return v

    sanitized = []
    for r in rows:
        s = {k: sanitize(v) for k, v in r.items()}
        # Ensure timestamp string with Z
        if isinstance(s.get("created_at"), str) and not s["created_at"].endswith("Z"):
            s["created_at"] = s["created_at"].split(".")[0] + "Z"
        sanitized.append(s)

    table = client.get_table(TABLE)
    errors = client.insert_rows_json(table, sanitized)
    if errors:
        raise RuntimeError(f"Errors inserting rows: {errors}")


def main(batch_size: int, interval_s: int, iterations: int):
    client = bigquery.Client(project=PROJECT_ID)
    print(f"🔗 Streaming to: {TABLE}")
    seeds = fetch_seed(client)
    if not seeds:
        raise SystemExit("No seed incidents found. Load seeds first.")

    for it in range(iterations):
        batch: List[Dict[str, Any]] = []
        for _ in range(batch_size):
            base = random.choice(seeds)
            batch.append(mutate_row(base))
        insert_rows(client, batch)
        print(f"✅ Iter {it+1}: inserted {len(batch)} rows")
        if it < iterations - 1:
            time.sleep(interval_s)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch-size", type=int, default=5)
    p.add_argument("--interval", type=int, default=10, help="seconds between batches")
    p.add_argument("--iterations", type=int, default=3)
    args = p.parse_args()
    main(args.batch_size, args.interval, args.iterations)


