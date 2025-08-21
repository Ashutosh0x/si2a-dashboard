from flask import Flask, render_template, jsonify, request
from google.cloud import bigquery
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, timedelta

app = Flask(__name__)
# Helpers
def df_to_json_records(df: pd.DataFrame):
    """Convert DataFrame to JSON-serializable list of dicts.
    Ensures datetimes are ISO strings and NaNs become nulls.
    """
    if df is None or df.empty:
        return []
    try:
        # Use pandas' JSON conversion to coerce types safely
        return json.loads(df.to_json(orient='records', date_format='iso'))
    except Exception:
        # Fallback: convert datetimes to str and NaNs to None
        df = df.copy()
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str)
        df = df.where(pd.notnull(df), None)
        return df.to_dict('records')


# Configuration
PROJECT_ID = os.getenv('PROJECT_ID', 'shadow-it-incident-autopilot')
LOCATION = os.getenv('BIGQUERY_LOCATION', 'US')

# Initialize BigQuery client
try:
    client = bigquery.Client(project=PROJECT_ID)
    print(f"✅ Connected to BigQuery project: {PROJECT_ID}")
except Exception as e:
    print(f"❌ Failed to connect to BigQuery: {e}")
    client = None

# RBAC helpers
def get_user_role(req: request) -> str:
    role = (req.headers.get('X-User-Role') or req.cookies.get('user_role') or req.args.get('role') or 'viewer').strip().lower()
    if role not in {'viewer', 'analyst', 'admin'}:
        role = 'viewer'
    return role

def require_role(allowed_roles):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            role = get_user_role(request)
            if role not in allowed_roles:
                return jsonify({'error': 'forbidden', 'message': 'Insufficient role', 'role': role}), 403
            return fn(*args, **kwargs)
        # Preserve function name for Flask
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    if client is None:
        return jsonify({'status': 'error', 'message': 'BigQuery client not available'}), 500
    
    try:
        # Test BigQuery connection
        client.query("SELECT 1").result()
        return jsonify({'status': 'healthy', 'project': PROJECT_ID, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/rbac/me')
def whoami():
    """Return current role and allowed actions."""
    role = get_user_role(request)
    capabilities = {
        'viewer': ['read'],
        'analyst': ['read', 'write_evidence', 'generate_playbook', 'feedback'],
        'admin': ['read', 'write_evidence', 'generate_playbook', 'feedback', 'admin']
    }
    return jsonify({'role': role, 'capabilities': capabilities.get(role, ['read'])})

@app.route('/api/incidents')
def get_incidents():
    """Get incidents data for dashboard"""
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    
    try:
        query = f"""
        SELECT 
            incident_id,
            title,
            description,
            severity,
            status,
            created_at,
            assigned_to,
            category,
            root_cause,
            resolution,
            resolution_time_hours,
            affected_users,
            affected_systems,
            tags,
            business_impact,
            risk_score
        FROM `{PROJECT_ID}.si2a_gold.incidents`
        ORDER BY created_at DESC
        LIMIT 100
        """
        
        df = client.query(query).to_dataframe()
        
        return jsonify(df_to_json_records(df))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics')
def get_metrics():
    """Get aggregated metrics for dashboard"""
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    
    try:
        query = f"""
        SELECT 
            severity,
            COUNT(*) as count,
            AVG(resolution_time_hours) as avg_resolution_time,
            AVG(risk_score) as avg_risk_score,
            SUM(affected_users) as total_affected_users
        FROM `{PROJECT_ID}.si2a_gold.incidents`
        GROUP BY severity
        ORDER BY 
            CASE severity 
                WHEN 'critical' THEN 1 
                WHEN 'high' THEN 2 
                WHEN 'medium' THEN 3 
                WHEN 'low' THEN 4 
                ELSE 5 
            END
        """
        
        df = client.query(query).to_dataframe()
        
        # Calculate additional metrics
        total_incidents = df['count'].sum()
        avg_mttr = df['avg_resolution_time'].mean()
        avg_risk = df['avg_risk_score'].mean()
        
        metrics = {
            'total_incidents': int(total_incidents),
            'avg_mttr': float(avg_mttr) if not pd.isna(avg_mttr) else 0.0,
            'avg_risk_score': float(avg_risk) if not pd.isna(avg_risk) else 0.0,
            'severity_breakdown': df_to_json_records(df)
        }
        
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-summary/<incident_id>')
def generate_ai_summary(incident_id):
    """Generate AI summary for an incident"""
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    
    try:
        # Fetch incident details
        query = f"""
        SELECT 
            incident_id,
            title,
            description,
            severity,
            status,
            business_impact,
            resolution_time_hours,
            affected_users,
            risk_score,
            category,
            created_at,
            root_cause,
            resolution,
            tags
        FROM `{PROJECT_ID}.si2a_gold.incidents`
        WHERE incident_id = '{incident_id}'
        """

        df = client.query(query).to_dataframe()

        if df.empty:
            return jsonify({'error': 'Incident not found'}), 404

        row = df.iloc[0].to_dict()

        def val(key, default="N/A"):
            v = row.get(key)
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return default
            return v

        title = str(val('title', 'Untitled Incident'))
        description = str(val('description', ''))
        severity = str(val('severity', 'unknown')).lower()
        status = str(val('status', 'unknown')).title()
        category = str(val('category', 'general'))
        business_impact = str(val('business_impact', 'Not specified'))
        root_cause = str(val('root_cause', 'Undetermined'))
        resolution = str(val('resolution', 'In progress'))
        created_at = val('created_at', '')
        created_str = str(created_at)[:19] if created_at else 'N/A'

        # Numbers and bands
        try:
            risk_score_float = float(val('risk_score', 0.0))
        except Exception:
            risk_score_float = 0.0
        risk_band = (
            'Very High' if risk_score_float >= 0.9 else
            'High' if risk_score_float >= 0.7 else
            'Moderate' if risk_score_float >= 0.5 else
            'Low'
        )

        try:
            affected_users_int = int(val('affected_users', 0))
        except Exception:
            affected_users_int = 0

        try:
            rt_hours_float = float(val('resolution_time_hours', 0))
        except Exception:
            rt_hours_float = 0.0

        tags_val = row.get('tags')
        if isinstance(tags_val, list):
            tags_list = tags_val
        else:
            tags_list = []

        # Severity guidance
        severity_text = {
            'critical': 'Critical – immediate containment and executive comms required',
            'high': 'High – rapid response, escalate to senior on-call',
            'medium': 'Medium – standard response within 24–48h',
            'low': 'Low – monitor and document'
        }.get(severity, 'Standard response')

        # Suggested actions
        suggestions = []
        if severity in ('critical', 'high'):
            suggestions.append('Initiate incident command and page senior on-call')
            suggestions.append('Contain blast radius and revoke suspicious access')
        if 'authentication' in category or 'mfa' in description.lower() or ('mfa' in [t.lower() for t in tags_list]):
            suggestions.append('Force password reset; enforce MFA re-verification for affected users')
        if any(k in category for k in ['data_leak', 'credential', 'insider', 'third_party']):
            suggestions.append('Start data exposure assessment and legal/compliance review')
        suggestions.append('Document findings and schedule post-incident review within 72 hours')

        summary_lines = [
            f"EXECUTIVE SUMMARY — {incident_id}",
            "",
            f"Title: {title}",
            f"Severity: {severity.title()} ({severity_text})",
            f"Status: {status}",
            f"Category: {category}",
            f"Created: {created_str}",
            f"Affected Users: {affected_users_int}",
            f"Estimated Resolution Time: {rt_hours_float} hours",
            f"Risk: {risk_score_float:.2f} ({risk_band})",
            f"Business Impact: {business_impact}",
        ]

        if description:
            summary_lines += ["", "Context:", f"- {description}"]
        if root_cause and root_cause != 'Undetermined':
            summary_lines += ["", "Likely Root Cause:", f"- {root_cause}"]
        if resolution and resolution != 'In progress':
            summary_lines += ["", "Actions Taken:", f"- {resolution}"]

        summary_lines += [
            "",
            "Recommended Next Actions:",
        ] + [f"- {s}" for s in suggestions]

        summary = "\n".join(summary_lines)

        return jsonify({
            'incident_id': incident_id,
            'summary': summary,
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/similar-incidents')
def find_similar_incidents():
    """Find semantically similar incidents using embeddings (fallback to keyword if error)."""
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    
    query_text = request.args.get('query', '')
    if not query_text:
        return jsonify({'error': 'Query text is required'}), 400
    
    try:
        # Semantic approach: embed query and incidents, compute cosine distance
        sql = f"""
        DECLARE top_k INT64 DEFAULT 5;
        WITH q AS (
          SELECT ML.GENERATE_EMBEDDING(MODEL `bqml.textembedding.gecko@001`, @qtxt) AS emb
        ),
        inc AS (
          SELECT 
            incident_id,
            title,
            description,
            severity,
            IFNULL(risk_score, 0.0) AS risk_score,
            ML.GENERATE_EMBEDDING(
              MODEL `bqml.textembedding.gecko@001`,
              CONCAT(COALESCE(title,''), '\\n', COALESCE(description,''), '\\n', COALESCE(category,''), '\\n', COALESCE(root_cause,''))
            ) AS emb
          FROM `{PROJECT_ID}.si2a_gold.incidents`
        )
        SELECT 
          inc.incident_id,
          inc.title,
          inc.description,
          inc.severity,
          inc.risk_score,
          1.0 - VECTOR_DISTANCE(inc.emb, (SELECT emb FROM q), 'COSINE') AS similarity_score
        FROM inc
        ORDER BY similarity_score DESC
        LIMIT top_k;
        """

        from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter
        job = client.query(
            sql,
            job_config=QueryJobConfig(query_parameters=[ScalarQueryParameter('qtxt', 'STRING', query_text)])
        )
        df = job.to_dataframe()
        
        if df.empty:
            return jsonify({'message': 'No similar incidents found', 'results': []})
        
        return jsonify({
            'query': query_text,
            'results': df.to_dict('records')
        })
    except Exception as e:
        # Fallback: keyword search
        try:
            query = f"""
            SELECT 
                incident_id,
                title,
                description,
                severity,
                risk_score,
                CASE 
                    WHEN LOWER(title) LIKE '%{query_text.lower()}%' OR 
                         LOWER(description) LIKE '%{query_text.lower()}%' THEN 0.9
                    ELSE 0.3
                END AS similarity_score
            FROM `{PROJECT_ID}.si2a_gold.incidents`
            WHERE LOWER(title) LIKE '%{query_text.lower()}%' 
               OR LOWER(description) LIKE '%{query_text.lower()}%'
            ORDER BY similarity_score DESC
            LIMIT 5
            """
            df = client.query(query).to_dataframe()
            return jsonify({'query': query_text, 'results': df.to_dict('records'), 'fallback': True})
        except Exception as ex:
            return jsonify({'error': str(ex)}), 500

@app.route('/api/policy-match')
def policy_match():
    """Return top policy sections relevant to a query using embeddings."""
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    query_text = request.args.get('query', '')
    if not query_text:
        return jsonify({'error': 'Query text is required'}), 400
    try:
        sql = f"""
        WITH q AS (
          SELECT ML.GENERATE_EMBEDDING(MODEL `bqml.textembedding.gecko@001`, @qtxt) AS emb
        ),
        pol AS (
          SELECT 
            section_id,
            section_title,
            section_text,
            ML.GENERATE_EMBEDDING(MODEL `bqml.textembedding.gecko@001`, COALESCE(section_text,'')) AS emb
          FROM `{PROJECT_ID}.si2a_dim.policy_sections`
        )
        SELECT 
          section_id,
          section_title,
          section_text,
          1.0 - VECTOR_DISTANCE(pol.emb, (SELECT emb FROM q), 'COSINE') AS similarity_score
        FROM pol
        ORDER BY similarity_score DESC
        LIMIT 5;
        """
        from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter
        job = client.query(
            sql,
            job_config=QueryJobConfig(query_parameters=[ScalarQueryParameter('qtxt', 'STRING', query_text)])
        )
        df = job.to_dataframe()
        return jsonify({'query': query_text, 'results': df.to_dict('records')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/playbook/<incident_id>', methods=['POST'])
def generate_playbook(incident_id):
    """Generate a structured remediation playbook for an incident.
    Primary: AI.GENERATE_TABLE via Vertex provider in BigQuery.
    Fallback: Deterministic template based on severity/category.
    """
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500

    try:
        sql = f"""
        SELECT * FROM AI.GENERATE_TABLE(
          'vertex-ai',
          '''
          You are an experienced incident responder. From the provided incident context,
          produce a concise remediation plan with columns:
          step STRING, owner STRING, eta_hours INT64, priority STRING, tooling STRING.
          Constraints:
          - 5 to 7 steps maximum
          - owner are role names (e.g., IR Lead, IAM Admin, SecOps)
          - priority is one of [P1, P2, P3]
          - tooling references internal/common tools (e.g., SIEM, EDR, IAM, DLP)
          Keep steps atomic and outcome‑oriented.
          ''',
          (
            SELECT AS STRUCT
              incident_id, title, description, severity, status, category, tags,
              root_cause, resolution, business_impact, affected_users, risk_score
            FROM `{PROJECT_ID}.si2a_gold.incidents`
            WHERE incident_id = @iid
          )
        );
        """
        from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter
        job = client.query(
            sql,
            job_config=QueryJobConfig(query_parameters=[ScalarQueryParameter('iid', 'STRING', incident_id)])
        )
        df = job.to_dataframe()
        if df.empty:
            raise RuntimeError('Empty playbook from AI')
        # Normalize columns
        cols = ['step', 'owner', 'eta_hours', 'priority', 'tooling']
        for c in cols:
            if c not in df.columns:
                df[c] = ''
        df = df[cols]
        return jsonify({'incident_id': incident_id, 'playbook': df.to_dict('records'), 'provider': 'vertex-ai'})
    except Exception:
        # Fallback template
        try:
            info = client.query(
                f"""
                SELECT severity, category, COALESCE(tags, []) AS tags
                FROM `{PROJECT_ID}.si2a_gold.incidents` WHERE incident_id = '{incident_id}'
                """
            ).to_dataframe()
            sev = (info.iloc[0]['severity'] if not info.empty else 'medium') if 'severity' in info.columns else 'medium'
            category = (info.iloc[0]['category'] if not info.empty else 'general') if 'category' in info.columns else 'general'
        except Exception:
            sev, category = 'medium', 'general'

        base = [
            {'step': 'Establish incident channel and assign roles', 'owner': 'IR Lead', 'eta_hours': 1, 'priority': 'P1', 'tooling': 'Chat/ITSM'},
            {'step': 'Contain affected accounts/systems', 'owner': 'SecOps', 'eta_hours': 2, 'priority': 'P1', 'tooling': 'EDR/IAM'},
            {'step': 'Collect evidence and snapshot logs', 'owner': 'SecOps', 'eta_hours': 2, 'priority': 'P2', 'tooling': 'SIEM/EDR'},
            {'step': 'Root cause analysis and scope', 'owner': 'IR Lead', 'eta_hours': 4, 'priority': 'P2', 'tooling': 'SIEM'},
            {'step': 'Remediate misconfigurations/rotate secrets', 'owner': 'IAM Admin', 'eta_hours': 3, 'priority': 'P2', 'tooling': 'IAM/Secrets'},
            {'step': 'User comms and awareness', 'owner': 'IT Comms', 'eta_hours': 2, 'priority': 'P3', 'tooling': 'Email/LMS'},
            {'step': 'Post‑incident review and lessons learned', 'owner': 'IR Lead', 'eta_hours': 2, 'priority': 'P3', 'tooling': 'Docs/ITSM'}
        ]
        if isinstance(sev, str) and sev.lower() == 'critical':
            base[1]['eta_hours'] = 1
            base[1]['priority'] = 'P1'
        if isinstance(category, str) and 'authentication' in category:
            base.insert(1, {'step': 'Force password reset & MFA re‑verification', 'owner': 'IAM Admin', 'eta_hours': 1, 'priority': 'P1', 'tooling': 'IAM'})
        playbook = base[:7]
        return jsonify({'incident_id': incident_id, 'playbook': playbook, 'provider': 'fallback'})

@app.route('/api/trends')
def get_trends():
    """Get incident trends over time"""
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    
    try:
        # Get daily incident counts for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        query = f"""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as incident_count,
            AVG(risk_score) as avg_risk_score,
            AVG(resolution_time_hours) as avg_resolution_time
        FROM `{PROJECT_ID}.si2a_gold.incidents`
        WHERE created_at >= TIMESTAMP('{start_date.strftime('%Y-%m-%d')}')
        GROUP BY DATE(created_at)
        ORDER BY date
        """
        
        df = client.query(query).to_dataframe()
        
        if df.empty:
            # Return mock data if no real data
            mock_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') 
                         for i in range(31)]
            mock_data = [
                {
                    'date': date,
                    'incident_count': max(0, int(5 + (i % 7) * 2)),
                    'avg_risk_score': 0.5 + (i % 5) * 0.1,
                    'avg_resolution_time': 4 + (i % 8) * 2
                }
                for i, date in enumerate(mock_dates)
            ]
            return jsonify({'trends': mock_data})
        
        return jsonify({'trends': df_to_json_records(df)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/anomalies/incidents')
def anomalies_incidents():
    """Detect anomalies in daily incident counts using simple z-score method."""
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        query = f"""
        SELECT 
            DATE(created_at) AS date,
            COUNT(*) AS incident_count
        FROM `{PROJECT_ID}.si2a_gold.incidents`
        WHERE created_at >= TIMESTAMP('{start_date.strftime('%Y-%m-%d')}')
        GROUP BY date
        ORDER BY date
        """
        df = client.query(query).to_dataframe()
        if df.empty:
            return jsonify({'series': [], 'anomalies': []})
        # Fill missing dates
        df['date'] = pd.to_datetime(df['date'])
        full_idx = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
        s = df.set_index('date')['incident_count'].reindex(full_idx).fillna(0)
        mean = float(s.mean())
        std = float(s.std()) or 1.0
        zscores = (s - mean) / std
        anomalies = [
            {'date': d.strftime('%Y-%m-%d'), 'incident_count': int(s.loc[d]), 'zscore': float(zscores.loc[d])}
            for d in s.index if abs(float(zscores.loc[d])) >= 2.0
        ]
        series = [
            {'date': d.strftime('%Y-%m-%d'), 'incident_count': int(s.loc[d])}
            for d in s.index
        ]
        return jsonify({'series': series, 'anomalies': anomalies, 'mean': mean, 'std': std})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecast/incidents')
def forecast_incidents():
    """Forecast daily incident counts using simple linear trend; fallback to naive."""
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    try:
        horizon_days = int(request.args.get('days', '14'))
        horizon_days = max(1, min(horizon_days, 60))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        query = f"""
        SELECT 
            DATE(created_at) AS date,
            COUNT(*) AS incident_count
        FROM `{PROJECT_ID}.si2a_gold.incidents`
        WHERE created_at >= TIMESTAMP('{start_date.strftime('%Y-%m-%d')}')
        GROUP BY date
        ORDER BY date
        """
        df = client.query(query).to_dataframe()
        if df.empty:
            # simple flat forecast
            base = 5
            forecast = [
                {'date': (end_date + timedelta(days=i+1)).strftime('%Y-%m-%d'), 'predicted_incidents': base}
                for i in range(horizon_days)
            ]
            return jsonify({'history': [], 'forecast': forecast, 'method': 'naive'})
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        # Build numeric time index
        df['t'] = range(len(df))
        y = df['incident_count'].astype(float)
        t = df['t'].astype(float)
        # Simple OLS slope/intercept without numpy
        y_last = float(y.iloc[-1])
        n = float(len(t))
        sum_t = float(t.sum())
        sum_y = float(y.sum())
        sum_tt = float((t * t).sum())
        sum_ty = float((t * y).sum())
        denom = (n * sum_tt - sum_t * sum_t)
        if denom == 0:
            slope = 0.0
            intercept = sum_y / n if n else y_last
            method = 'naive_last'
        else:
            slope = (n * sum_ty - sum_t * sum_y) / denom
            intercept = (sum_y - slope * sum_t) / n
            method = 'linear_trend'
        start_t = int(df['t'].iloc[-1])
        forecast = []
        for i in range(1, horizon_days + 1):
            ti = start_t + i
            pred = max(0.0, slope * ti + intercept)
            forecast.append({'date': (df['date'].iloc[-1] + timedelta(days=i)).strftime('%Y-%m-%d'), 'predicted_incidents': float(round(pred, 2))})
        history = [{'date': d.strftime('%Y-%m-%d'), 'incident_count': int(c)} for d, c in zip(df['date'], df['incident_count'])]
        return jsonify({'history': history, 'forecast': forecast, 'method': method})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evidence/<incident_id>', methods=['GET', 'POST'])
def evidence_endpoint(incident_id):
    """List or add evidence object references for an incident.
    Expects table: {PROJECT_ID}.si2a_evidence.object_references
    Schema suggestion: evidence_id STRING, incident_id STRING, object_uri STRING, object_type STRING, description STRING, tags ARRAY<STRING>, uploader STRING, created_at TIMESTAMP
    """
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    table_fqn = f"{PROJECT_ID}.si2a_evidence.object_references"
    try:
        if request.method == 'GET':
            query = f"""
            SELECT evidence_id, incident_id, object_uri, object_type, description, tags, uploader, created_at
            FROM `{table_fqn}`
            WHERE incident_id = @iid
            ORDER BY created_at DESC
            LIMIT 100
            """
            from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter
            job = client.query(query, job_config=QueryJobConfig(query_parameters=[ScalarQueryParameter('iid', 'STRING', incident_id)]))
            df = job.to_dataframe()
            return jsonify({'incident_id': incident_id, 'evidence': df_to_json_records(df)})
        else:
            # POST
            role = get_user_role(request)
            if role not in {'analyst', 'admin'}:
                return jsonify({'error': 'forbidden', 'message': 'Insufficient role', 'role': role}), 403
            payload = request.get_json(force=True) or {}
            from uuid import uuid4
            evidence_id = payload.get('evidence_id') or str(uuid4())
            object_uri = payload.get('object_uri') or ''
            object_type = (payload.get('object_type') or 'generic').lower()
            description = payload.get('description') or ''
            tags = payload.get('tags') or []
            uploader = payload.get('uploader') or 'web-user'
            row = {
                'evidence_id': evidence_id,
                'incident_id': incident_id,
                'object_uri': object_uri,
                'object_type': object_type,
                'description': description,
                'tags': tags,
                'uploader': uploader,
                'created_at': datetime.utcnow().isoformat()
            }
            errors = client.insert_rows_json(table_fqn, [row])
            if errors:
                return jsonify({'error': 'insert_failed', 'details': errors}), 500
            return jsonify({'status': 'ok', 'evidence_id': evidence_id})
    except Exception as e:
        # Fallback: if table missing, return mock on GET
        if request.method == 'GET':
            mock = [
                {'evidence_id': 'mock-1', 'incident_id': incident_id, 'object_uri': 'gs://bucket/logs/incident.log', 'object_type': 'log', 'description': 'System log snapshot', 'tags': ['log', 'forensics'], 'uploader': 'system', 'created_at': datetime.utcnow().isoformat()}
            ]
            return jsonify({'incident_id': incident_id, 'evidence': mock, 'mock': True})
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Record user feedback about AI generations or workflows."""
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    try:
        payload = request.get_json(force=True) or {}
        incident_id = payload.get('incident_id') or ''
        generation_type = payload.get('generation_type') or 'executive_summary'
        reviewer = payload.get('reviewer') or 'anonymous'
        def clamp_int(v, lo=1, hi=5):
            try:
                iv = int(v)
            except Exception:
                iv = lo
            return max(lo, min(hi, iv))
        row = {
            'feedback_id': payload.get('feedback_id') or f"fb-{int(datetime.utcnow().timestamp())}",
            'incident_id': incident_id,
            'generation_type': generation_type,
            'quality_rating': clamp_int(payload.get('quality_rating', 3)),
            'accuracy_rating': clamp_int(payload.get('accuracy_rating', 3)),
            'usefulness_rating': clamp_int(payload.get('usefulness_rating', 3)),
            'feedback_text': payload.get('feedback_text') or '',
            'reviewer': reviewer,
            'feedback_timestamp': datetime.utcnow().isoformat()
        }
        table_fqn = f"{PROJECT_ID}.si2a_feedback.ai_generation_feedback"
        errors = client.insert_rows_json(table_fqn, [row])
        if errors:
            return jsonify({'error': 'insert_failed', 'details': errors}), 500
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compliance-check/<incident_id>')
def check_compliance(incident_id):
    """Check policy compliance for an incident"""
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    
    try:
        query = f"""
        SELECT 
            i.incident_id,
            i.title,
            i.description,
            i.severity,
            i.tags,
            CASE 
                WHEN 'mfa' IN UNNEST(i.tags) OR LOWER(i.description) LIKE '%mfa%' THEN 'MFA Policy'
                WHEN 'saas' IN UNNEST(i.tags) OR LOWER(i.description) LIKE '%saas%' THEN 'SaaS Usage Policy'
                WHEN 'access' IN UNNEST(i.tags) OR LOWER(i.description) LIKE '%access%' THEN 'Access Control Policy'
                ELSE 'General Security Policy'
            END AS applicable_policy,
            CASE 
                WHEN i.severity = 'critical' THEN 'High Risk - Immediate Action Required'
                WHEN i.severity = 'high' THEN 'High Risk - Escalate to Senior Team'
                WHEN i.severity = 'medium' THEN 'Medium Risk - Standard Response'
                WHEN i.severity = 'low' THEN 'Low Risk - Monitor and Document'
                ELSE 'Minimal Risk - Routine Handling'
            END AS compliance_assessment
        FROM `{PROJECT_ID}.si2a_gold.incidents` i
        WHERE i.incident_id = '{incident_id}'
        """
        
        df = client.query(query).to_dataframe()
        
        if df.empty:
            return jsonify({'error': 'Incident not found'}), 404
        
        result = df.iloc[0]
        
        return jsonify({
            'incident_id': incident_id,
            'applicable_policy': result['applicable_policy'],
            'compliance_assessment': result['compliance_assessment'],
            'severity': result['severity'],
            'tags': result['tags'] if isinstance(result['tags'], list) else [],
            'checked_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/severity-distribution')
def get_severity_chart():
    """Get data for severity distribution chart"""
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    
    try:
        query = f"""
        SELECT 
            severity,
            COUNT(*) as count,
            AVG(resolution_time_hours) as avg_resolution_time
        FROM `{PROJECT_ID}.si2a_gold.incidents`
        GROUP BY severity
        ORDER BY 
            CASE severity 
                WHEN 'critical' THEN 1 
                WHEN 'high' THEN 2 
                WHEN 'medium' THEN 3 
                WHEN 'low' THEN 4 
                ELSE 5 
            END
        """
        
        df = client.query(query).to_dataframe()
        
        if df.empty:
            # Return mock data
            return jsonify({
                'labels': ['Critical', 'High', 'Medium', 'Low'],
                'counts': [5, 12, 18, 25],
                'avg_resolution_times': [8.5, 6.2, 4.1, 2.8]
            })
        
        return jsonify({
            'labels': df['severity'].str.title().tolist(),
            'counts': df['count'].tolist(),
            'avg_resolution_times': df['avg_resolution_time'].round(1).tolist()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/risk-distribution')
def get_risk_chart():
    """Get data for risk distribution chart"""
    if client is None:
        return jsonify({'error': 'BigQuery client not available'}), 500
    
    try:
        query = f"""
        SELECT 
            CASE 
                WHEN risk_score >= 0.8 THEN 'Critical (0.8-1.0)'
                WHEN risk_score >= 0.6 THEN 'High (0.6-0.79)'
                WHEN risk_score >= 0.4 THEN 'Medium (0.4-0.59)'
                WHEN risk_score >= 0.2 THEN 'Low (0.2-0.39)'
                ELSE 'Minimal (0.0-0.19)'
            END AS risk_category,
            COUNT(*) as count
        FROM `{PROJECT_ID}.si2a_gold.incidents`
        GROUP BY risk_category
        ORDER BY risk_category
        """
        
        df = client.query(query).to_dataframe()
        
        if df.empty:
            # Return mock data
            return jsonify({
                'labels': ['Critical (0.8-1.0)', 'High (0.6-0.79)', 'Medium (0.4-0.59)', 'Low (0.2-0.39)', 'Minimal (0.0-0.19)'],
                'counts': [8, 15, 22, 12, 3]
            })
        
        return jsonify({
            'labels': df['risk_category'].tolist(),
            'counts': df['count'].tolist()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
