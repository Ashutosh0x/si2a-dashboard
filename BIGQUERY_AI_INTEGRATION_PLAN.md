# 🚀 BigQuery AI Integration & Dashboard Plan for SI²A

## 📋 Executive Summary

This document outlines how BigQuery AI capabilities are integrated into the Shadow IT Incident Autopilot (SI²A) project, how to demonstrate results in Jupyter notebooks, and how to create a deployable dashboard for Google Cloud App Run.

## 🎯 BigQuery AI Integration Strategy

### 1. **AI Architect Approach** 🧠
**BigQuery AI Features Used:**
- `AI.GENERATE`: Executive summaries, incident analysis
- `AI.GENERATE_TABLE`: Remediation playbooks, action plans
- `AI.GENERATE_BOOL`: Policy compliance checks
- `AI.FORECAST`: Incident volume prediction, risk trends

**Implementation Examples:**
```sql
-- Executive Summary Generation
SELECT AI.GENERATE(
  'vertex-ai',
  STRUCT(
    'Summarize this security incident in 5 bullet points' AS prompt,
    TO_JSON_STRING((SELECT AS STRUCT * FROM incidents WHERE incident_id = @id)) AS input_json
  )
) AS executive_summary;

-- Remediation Playbook Generation
SELECT * FROM AI.GENERATE_TABLE(
  'vertex-ai',
  'Generate a remediation plan with columns: step, owner, eta_hours, priority',
  (SELECT * FROM incidents WHERE incident_id = @id)
);

-- Policy Compliance Check
SELECT AI.GENERATE_BOOL(
  'vertex-ai',
  'Does this incident violate the MFA policy?',
  CONCAT(incident_description, '\nPolicy: ', policy_text)
) AS policy_violation;
```

### 2. **Semantic Detective Approach** 🔍
**BigQuery AI Features Used:**
- `ML.GENERATE_EMBEDDING`: Text vectorization for incidents and policies
- `CREATE VECTOR INDEX`: Performance optimization for similarity search
- `VECTOR_SEARCH`: Semantic similarity queries

**Implementation Examples:**
```sql
-- Create embeddings for incident text
CREATE OR REPLACE TABLE incident_embeddings AS
SELECT 
  incident_id,
  ML.GENERATE_EMBEDDING(
    MODEL `bqml.textembedding.gecko`,
    CONCAT(title, ' ', description, ' ', root_cause)
  ) AS embedding
FROM incidents;

-- Create vector index for performance
CREATE OR REPLACE VECTOR INDEX incident_vector_index
ON incident_embeddings(embedding)
OPTIONS (distance_type = 'COSINE');

-- Semantic similarity search
SELECT 
  i.incident_id,
  i.title,
  vs.distance AS similarity_score
FROM VECTOR_SEARCH(
  TABLE incident_embeddings,
  (SELECT ML.GENERATE_EMBEDDING(MODEL `bqml.textembedding.gecko`, @query_text) AS embedding),
  top_k => 5
) AS vs
JOIN incidents i ON vs.neighbor_id = i.incident_id
ORDER BY vs.distance ASC;
```

### 3. **Multimodal Pioneer Approach** 🖼️
**BigQuery AI Features Used:**
- `Object Tables`: Interface to Cloud Storage files
- `ObjectRef`: Reference unstructured data in AI operations
- Multimodal data processing (images, PDFs, documents)

**Implementation Examples:**
```sql
-- Create Object Table for artifacts
CREATE OR REPLACE EXTERNAL TABLE artifacts
WITH CONNECTION `LOCATION.gcs_connection`
OPTIONS (
  object_metadata = 'SIMPLE',
  uris = ['gs://si2a-artifacts/**/*']
);

-- Analyze security screenshots
SELECT AI.GENERATE(
  'vertex-ai',
  STRUCT(
    'Analyze this security screenshot and identify security risks' AS prompt,
    ObjectRef(image_uri) AS input_json
  )
) AS image_analysis;

-- Correlate visual evidence with incidents
SELECT 
  i.incident_id,
  i.title,
  a.object_name,
  a.content_type,
  AI.GENERATE(
    'vertex-ai',
    'Summarize the security implications of this evidence',
    ObjectRef(a.object_uri)
  ) AS evidence_summary
FROM incidents i
JOIN artifacts a ON i.incident_id = a.incident_id;
```

## 📊 Jupyter Notebook Results Demonstration

### **Notebook Structure:**
```
notebooks/
├── 01_bigquery_ai_demo.ipynb          # Main demo notebook
├── 02_ai_architect_demo.ipynb         # Generative AI capabilities
├── 03_semantic_detective_demo.ipynb   # Vector search demo
├── 04_multimodal_pioneer_demo.ipynb   # Object tables demo
└── 05_business_impact_demo.ipynb      # Analytics and forecasting
```

### **Key Notebook Features:**
1. **Interactive BigQuery Queries**: Live data from BigQuery tables
2. **Real-time AI Results**: Demonstrate AI.GENERATE, VECTOR_SEARCH in action
3. **Data Visualization**: Matplotlib, Seaborn, and Plotly charts
4. **Business Metrics**: MTTR reduction, risk trends, compliance scores
5. **Export Capabilities**: Save results as CSV, generate reports

### **Sample Notebook Cell:**
```python
# Demonstrate AI Architect capabilities
def demo_executive_summary():
    query = """
    SELECT 
        incident_id,
        title,
        AI.GENERATE(
            'vertex-ai',
            STRUCT(
                'Create an executive summary for this incident' AS prompt,
                TO_JSON_STRING((SELECT AS STRUCT * FROM incidents WHERE incident_id = @id)) AS input_json
            )
        ) AS ai_summary
    FROM incidents
    WHERE incident_id = 'INC-2024-001'
    """
    
    df = client.query(query).to_dataframe()
    return df

# Run demo and display results
results = demo_executive_summary()
print("🤖 AI-Generated Executive Summary:")
print(results['ai_summary'].iloc[0])
```

## 🎨 Dashboard Creation for Google Cloud App Run

### **Dashboard Architecture:**
```
Frontend (HTML/CSS/JavaScript)
    ↓
Flask Backend (Python)
    ↓
BigQuery Client (Google Cloud)
    ↓
BigQuery AI Functions
```

### **Dashboard Components:**

#### 1. **Real-time Incident Overview**
- Live incident count by severity
- Current open incidents
- Recent incident timeline
- Risk score distribution

#### 2. **AI-Powered Analytics**
- Executive summary generator
- Similar incident finder
- Policy compliance checker
- Risk trend forecasting

#### 3. **Interactive Visualizations**
- Incident severity pie chart
- Resolution time trends
- Risk score histograms
- Affected systems breakdown

#### 4. **Business Impact Metrics**
- MTTR reduction tracking
- Cost savings calculator
- Compliance score trends
- Resource utilization

### **Dashboard Implementation:**

#### **Flask Application (app.py):**
```python
from flask import Flask, render_template, jsonify
from google.cloud import bigquery
import plotly.express as px
import plotly.graph_objects as go
import json

app = Flask(__name__)
client = bigquery.Client(project=PROJECT_ID)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/incidents')
def get_incidents():
    query = """
    SELECT * FROM `si2a_gold.incidents`
    ORDER BY created_at DESC
    LIMIT 100
    """
    df = client.query(query).to_dataframe()
    return jsonify(df.to_dict('records'))

@app.route('/api/ai-summary/<incident_id>')
def generate_ai_summary(incident_id):
    query = f"""
    SELECT AI.GENERATE(
        'vertex-ai',
        STRUCT(
            'Summarize this incident for executives' AS prompt,
            TO_JSON_STRING((SELECT AS STRUCT * FROM si2a_gold.incidents WHERE incident_id = '{incident_id}')) AS input_json
        )
    ) AS summary
    """
    result = client.query(query).to_dataframe()
    return jsonify({'summary': result['summary'].iloc[0]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

#### **HTML Template (templates/dashboard.html):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>SI²A Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="dashboard">
        <h1>🚀 SI²A - Shadow IT Incident Autopilot</h1>
        
        <!-- Real-time Metrics -->
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Open Incidents</h3>
                <div id="open-incidents-count">Loading...</div>
            </div>
            <div class="metric-card">
                <h3>Average MTTR</h3>
                <div id="avg-mttr">Loading...</div>
            </div>
            <div class="metric-card">
                <h3>Risk Score</h3>
                <div id="avg-risk-score">Loading...</div>
            </div>
        </div>
        
        <!-- AI-Powered Features -->
        <div class="ai-features">
            <h2>🤖 AI-Powered Analysis</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>Executive Summary Generator</h3>
                    <select id="incident-selector">
                        <option>Select Incident...</option>
                    </select>
                    <button onclick="generateSummary()">Generate Summary</button>
                    <div id="summary-output"></div>
                </div>
                
                <div class="feature-card">
                    <h3>Similar Incident Finder</h3>
                    <input type="text" id="query-input" placeholder="Describe the incident...">
                    <button onclick="findSimilar()">Find Similar</button>
                    <div id="similar-results"></div>
                </div>
            </div>
        </div>
        
        <!-- Interactive Charts -->
        <div class="charts-section">
            <h2>📊 Analytics Dashboard</h2>
            <div class="chart-grid">
                <div id="severity-chart"></div>
                <div id="trend-chart"></div>
                <div id="risk-distribution"></div>
            </div>
        </div>
    </div>
    
    <script src="/static/dashboard.js"></script>
</body>
</html>
```

#### **JavaScript (static/dashboard.js):**
```javascript
// Dashboard functionality
class SI2ADashboard {
    constructor() {
        this.init();
    }
    
    async init() {
        await this.loadMetrics();
        await this.loadCharts();
        this.setupEventListeners();
    }
    
    async loadMetrics() {
        try {
            const response = await fetch('/api/incidents');
            const incidents = await response.json();
            
            // Update metrics
            document.getElementById('open-incidents-count').textContent = 
                incidents.filter(i => i.status === 'open').length;
            
            const avgMTTR = incidents.reduce((sum, i) => sum + i.resolution_time_hours, 0) / incidents.length;
            document.getElementById('avg-mttr').textContent = `${avgMTTR.toFixed(1)} hours`;
            
            const avgRisk = incidents.reduce((sum, i) => sum + i.risk_score, 0) / incidents.length;
            document.getElementById('avg-risk-score').textContent = avgRisk.toFixed(2);
            
            // Populate incident selector
            const selector = document.getElementById('incident-selector');
            incidents.forEach(incident => {
                const option = document.createElement('option');
                option.value = incident.incident_id;
                option.textContent = `${incident.incident_id}: ${incident.title}`;
                selector.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading metrics:', error);
        }
    }
    
    async generateSummary(incidentId) {
        try {
            const response = await fetch(`/api/ai-summary/${incidentId}`);
            const data = await response.json();
            
            document.getElementById('summary-output').innerHTML = 
                `<div class="ai-summary">${data.summary}</div>`;
        } catch (error) {
            console.error('Error generating summary:', error);
        }
    }
    
    async loadCharts() {
        // Create Plotly charts
        this.createSeverityChart();
        this.createTrendChart();
        this.createRiskDistribution();
    }
    
    createSeverityChart() {
        const data = [{
            values: [20, 30, 25, 25],
            labels: ['Critical', 'High', 'Medium', 'Low'],
            type: 'pie',
            marker: {colors: ['#ff4444', '#ff8800', '#ffcc00', '#88cc00']}
        }];
        
        const layout = {title: 'Incident Severity Distribution'};
        Plotly.newPlot('severity-chart', data, layout);
    }
    
    // Additional chart methods...
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    new SI2ADashboard();
});

// Global functions for HTML buttons
function generateSummary() {
    const incidentId = document.getElementById('incident-selector').value;
    if (incidentId) {
        window.dashboard.generateSummary(incidentId);
    }
}
```

## 🚀 Google Cloud App Run Deployment

### **Deployment Files:**

#### **requirements.txt:**
```
flask>=2.0.0
gunicorn>=20.0.0
google-cloud-bigquery>=3.11.0
google-cloud-storage>=2.0.0
pandas>=1.5.0
plotly>=5.0.0
python-dotenv>=0.19.0
```

#### **Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
```

#### **.dockerignore:**
```
.venv/
__pycache__/
*.pyc
.git/
*.ipynb
data/
sql/
setup/
```

### **Deployment Commands:**
```bash
# 1. Build and deploy to Cloud Run
gcloud run deploy si2a-dashboard \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300

# 2. Set environment variables
gcloud run services update si2a-dashboard \
  --region us-central1 \
  --set-env-vars PROJECT_ID=your-project-id

# 3. Get the service URL
gcloud run services describe si2a-dashboard \
  --region us-central1 \
  --format='value(status.url)'
```

### **Environment Configuration:**
```bash
# Set in Cloud Run
PROJECT_ID=shadow-it-incident-autopilot
GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
BIGQUERY_LOCATION=US
```

## 📈 Expected Results & Business Impact

### **Technical Metrics:**
- **Query Performance**: Vector search < 100ms response time
- **AI Generation**: Executive summaries in < 5 seconds
- **Dashboard Load**: Full page load < 3 seconds
- **Scalability**: Handle 1000+ concurrent users

### **Business Metrics:**
- **MTTR Reduction**: 40% faster incident resolution
- **Policy Compliance**: 95% automated compliance checking
- **Resource Efficiency**: 60% reduction in manual triage
- **Risk Detection**: 80% faster threat identification

### **User Experience:**
- **Security Analysts**: One-click incident analysis
- **Managers**: Real-time executive summaries
- **Compliance Teams**: Automated policy checking
- **Operations**: Predictive incident forecasting

## 🔧 Implementation Timeline

### **Week 1: Core Integration**
- [ ] BigQuery AI functions implementation
- [ ] Vector search and embeddings setup
- [ ] Object tables configuration
- [ ] Basic API endpoints

### **Week 2: Dashboard Development**
- [ ] Flask application structure
- [ ] Frontend templates and styling
- [ ] Interactive charts and visualizations
- [ ] Real-time data integration

### **Week 3: Testing & Optimization**
- [ ] Performance testing
- [ ] Error handling and logging
- [ ] Security and authentication
- [ ] Load testing and scaling

### **Week 4: Deployment & Launch**
- [ ] Cloud Run deployment
- [ ] Production environment setup
- [ ] Monitoring and alerting
- [ ] Documentation and training

## 🎯 Success Criteria

1. **Technical Excellence**: All BigQuery AI features working correctly
2. **Performance**: Dashboard responds within 3 seconds
3. **Scalability**: Handles production load
4. **User Adoption**: Security teams actively using the system
5. **Business Impact**: Measurable reduction in incident MTTR

## 🚨 Risk Mitigation

1. **BigQuery Quotas**: Monitor usage and implement rate limiting
2. **AI Model Costs**: Set budget alerts and optimize prompts
3. **Data Privacy**: Implement proper access controls
4. **Performance**: Use caching and query optimization
5. **Security**: Regular security audits and updates

---

This plan provides a comprehensive roadmap for integrating BigQuery AI into the SI²A project, creating an interactive Jupyter notebook demonstration, and deploying a production-ready dashboard on Google Cloud App Run.
