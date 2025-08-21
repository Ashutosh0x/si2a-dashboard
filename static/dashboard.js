// SI²A Dashboard JavaScript
class SI2ADashboard {
    constructor() {
        this.incidents = [];
        this.metrics = {};
        this.charts = {};
        this.role = 'viewer';
        this.capabilities = ['read'];
        this.activeFilters = { severity: null };
        this.init();
    }
    
    async loadRBAC() {
        try {
            const response = await fetch('/api/rbac/me', { credentials: 'same-origin' });
            const data = await response.json();
            if (data && !data.error) {
                this.role = data.role || 'viewer';
                this.capabilities = data.capabilities || ['read'];
                const badge = document.getElementById('role-badge');
                if (badge) badge.textContent = (this.role || 'viewer').toUpperCase();
                const disableIfNo = (cap, el) => {
                    if (!el) return;
                    const has = (this.capabilities || []).includes(cap) || this.role === 'admin';
                    el.disabled = !has;
                    if (!has) el.title = 'Requires analyst role';
                };
                disableIfNo('write_evidence', document.getElementById('add-evidence-btn'));
                disableIfNo('feedback', document.getElementById('submit-feedback-btn'));
            }
        } catch (e) {
            console.warn('RBAC load failed', e);
        }
    }

    async init() {
        console.log('🚀 Initializing SI²A Dashboard...');
        
        try {
            // Check health status
            await this.checkHealth();
            await this.loadRBAC();
            
            // Load initial data
            await this.loadMetrics();
            await this.loadIncidents();
            await this.loadCharts();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Auto-refresh every 30 seconds
            setInterval(() => this.refreshData(), 30000);
            
            console.log('✅ Dashboard initialized successfully');
        } catch (error) {
            console.error('❌ Dashboard initialization failed:', error);
            this.showError('Failed to initialize dashboard. Please check your connection.');
        }
    }
    
    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            if (data.status === 'healthy') {
                console.log('✅ BigQuery connection healthy');
                this.showSuccess('Connected to BigQuery successfully');
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('❌ Health check failed:', error);
            this.showError('BigQuery connection failed. Some features may not work.');
        }
    }
    
    async loadMetrics() {
        try {
            const response = await fetch('/api/metrics');
            this.metrics = await response.json();
            
            this.updateMetricsDisplay();
            console.log('✅ Metrics loaded successfully');
        } catch (error) {
            console.error('❌ Failed to load metrics:', error);
            this.showError('Failed to load metrics data');
        }
    }
    
    async loadIncidents() {
        try {
            const response = await fetch('/api/incidents');
            this.incidents = await response.json();
            
            this.updateIncidentsTable();
            this.populateIncidentSelectors();
            console.log('✅ Incidents loaded successfully');
        } catch (error) {
            console.error('❌ Failed to load incidents:', error);
            this.showError('Failed to load incidents data');
        }
    }
    
    async loadCharts() {
        try {
            // Load severity distribution chart
            await this.createSeverityChart();
            
            // Load risk distribution chart
            await this.createRiskChart();
            
            // Load resolution time chart
            await this.createResolutionChart();
            
            // Load trends chart
            await this.createTrendsChart();
            
            // Load forecast and anomaly charts
            await this.createForecastChart();
            await this.createAnomalyChart();
            
            console.log('✅ Charts loaded successfully');
        } catch (error) {
            console.error('❌ Failed to load charts:', error);
            this.showError('Failed to load chart data');
        }
    }
    
    updateMetricsDisplay() {
        // Update metric cards
        const openIncidents = this.incidents.filter(i => (i.status || '').toLowerCase() === 'open' || (i.status || '').toLowerCase() === 'investigating').length;
        
        document.getElementById('open-incidents-count').textContent = openIncidents;
        const mttrEl = document.getElementById('avg-mttr');
        const riskEl = document.getElementById('avg-risk-score');
        const mttr = this.metrics.avg_mttr || 0;
        const risk = this.metrics.avg_risk_score || 0;
        mttrEl.textContent = (mttr).toFixed(1);
        riskEl.textContent = (risk).toFixed(2);
        // Risk color coding
        riskEl.style.color = this.getRiskColor(risk);
        document.getElementById('total-incidents').textContent = this.metrics.total_incidents || this.incidents.length;
    }
    
    updateIncidentsTable() {
        const tableContainer = document.getElementById('incidents-table');
        
        if (this.incidents.length === 0) {
            tableContainer.innerHTML = '<p>No incidents found.</p>';
            return;
        }
        
        const recentIncidents = this.incidents.slice(0, 10); // Show last 10
        
        let tableHTML = `
            <table class="si2a-table" id="incidents-table-el">
                <thead>
                    <tr>
                        <th data-key="incident_id">ID</th>
                        <th data-key="title">Title</th>
                        <th data-key="severity">Severity</th>
                        <th data-key="status">Status</th>
                        <th data-key="risk_score">Risk</th>
                        <th data-key="created_at">Created</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        recentIncidents.forEach(incident => {
            const sev = (incident.severity || '').toLowerCase();
            const sevClass = sev ? `badge-${sev}` : 'badge';
            const statusIndicator = this.getStatusIndicator(incident.status);
            const risk = typeof incident.risk_score === 'number' ? incident.risk_score : (parseFloat(incident.risk_score) || 0);
            const riskClass = risk >= 0.8 ? 'risk-crit' : risk >= 0.6 ? 'risk-high' : risk >= 0.4 ? 'risk-med' : risk >= 0.2 ? 'risk-low' : 'risk-min';
            
            tableHTML += `
                <tr>
                    <td style="font-family: monospace;">${incident.incident_id}</td>
                    <td>${incident.title}</td>
                    <td>
                        <span class="badge ${sevClass}">${incident.severity || 'N/A'}</span>
                    </td>
                    <td>
                        ${statusIndicator} ${(incident.status || '').toString()}
                    </td>
                    <td>
                        <span class="risk-pill ${riskClass}">${isNaN(risk) ? 'N/A' : risk.toFixed(2)}</span>
                    </td>
                    <td>
                        ${incident.created_at ? new Date(incident.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                </tr>
            `;
        });
        
        tableHTML += '</tbody></table>';
        tableContainer.innerHTML = tableHTML;

        // Simple sorting by clicking headers
        const headers = document.querySelectorAll('#incidents-table-el thead th');
        headers.forEach(h => {
            h.addEventListener('click', () => {
                const key = h.getAttribute('data-key');
                if (!key) return;
                const sorted = [...this.incidents].sort((a,b) => {
                    const av = (a[key] ?? '').toString();
                    const bv = (b[key] ?? '').toString();
                    if (!isNaN(av) && !isNaN(bv)) return parseFloat(av) - parseFloat(bv);
                    return av.localeCompare(bv);
                });
                const original = this.incidents;
                this.incidents = sorted;
                this.updateIncidentsTable();
                this.incidents = original;
            });
        });
    }
    
    populateIncidentSelectors() {
        const selectors = ['incident-selector', 'compliance-incident-selector', 'evidence-incident-selector', 'feedback-incident-selector'];
        
        selectors.forEach(selectorId => {
            const selector = document.getElementById(selectorId);
            if (selector) {
                // Clear existing options
                selector.innerHTML = '<option>Select Incident...</option>';
                
                // Add incident options
                this.incidents.forEach(incident => {
                    const option = document.createElement('option');
                    option.value = incident.incident_id;
                    option.textContent = `${incident.incident_id}: ${incident.title}`;
                    selector.appendChild(option);
                });
            }
        });
    }

    async loadEvidence() {
        const selector = document.getElementById('evidence-incident-selector');
        const incidentId = selector ? selector.value : '';
        if (!incidentId || incidentId === 'Select Incident...') {
            this.showError('Select an incident to load evidence');
            return;
        }
        try {
            const response = await fetch(`/api/evidence/${encodeURIComponent(incidentId)}`);
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            const list = document.getElementById('evidence-list');
            if (!list) return;
            if (!data.evidence || data.evidence.length === 0) {
                list.innerHTML = '<p>No evidence yet.</p>';
                return;
            }
            list.innerHTML = data.evidence.map(ev => `
                <div class=\"similar-item\">\n                    <h4>${(ev.object_type || 'object').toUpperCase()} — ${ev.object_uri}</h4>\n                    <p>${ev.description || ''}</p>\n                    <p><strong>Tags:</strong> ${(ev.tags || []).join(', ')}</p>\n                    <p><small>By ${ev.uploader || 'unknown'} at ${ev.created_at || ''}</small></p>\n                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load evidence:', error);
            this.showError('Failed to load evidence');
        }
    }

    async addEvidence() {
        if (!(this.capabilities.includes('write_evidence') || this.role === 'admin')) {
            this.showError('Insufficient role to add evidence');
            return;
        }
        const incidentId = document.getElementById('evidence-incident-selector')?.value;
        const uri = document.getElementById('evidence-uri')?.value?.trim();
        const type = document.getElementById('evidence-type')?.value?.trim() || 'generic';
        const desc = document.getElementById('evidence-description')?.value?.trim() || '';
        const tags = (document.getElementById('evidence-tags')?.value || '').split(',').map(t => t.trim()).filter(Boolean);
        if (!incidentId || incidentId === 'Select Incident...') {
            this.showError('Select an incident first');
            return;
        }
        if (!uri) {
            this.showError('Provide an object URI');
            return;
        }
        try {
            const response = await fetch(`/api/evidence/${encodeURIComponent(incidentId)}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ object_uri: uri, object_type: type, description: desc, tags })
            });
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            this.showSuccess('Evidence added');
            await this.loadEvidence();
        } catch (error) {
            console.error('Failed to add evidence:', error);
            this.showError('Failed to add evidence');
        }
    }

    async submitFeedback() {
        if (!(this.capabilities.includes('feedback') || this.role === 'admin')) {
            this.showError('Insufficient role to submit feedback');
            return;
        }
        const incidentId = document.getElementById('feedback-incident-selector')?.value;
        if (!incidentId || incidentId === 'Select Incident...') {
            this.showError('Select an incident first');
            return;
        }
        const qual = parseInt(document.getElementById('fb-quality')?.value || '3', 10);
        const acc = parseInt(document.getElementById('fb-accuracy')?.value || '3', 10);
        const use = parseInt(document.getElementById('fb-usefulness')?.value || '3', 10);
        const text = document.getElementById('fb-text')?.value || '';
        try {
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ incident_id: incidentId, generation_type: 'executive_summary', quality_rating: qual, accuracy_rating: acc, usefulness_rating: use, feedback_text: text })
            });
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            this.showSuccess('Feedback submitted');
        } catch (error) {
            console.error('Failed to submit feedback:', error);
            this.showError('Failed to submit feedback');
        }
    }
    
    async createSeverityChart() {
        try {
            const response = await fetch('/api/charts/severity-distribution');
            const data = await response.json();
            
            // Color palette to match the provided image (teal, blue, indigo, pink, orange, yellow)
            const imagePalette = ['#14B8A6', '#3B82F6', '#6366F1', '#EC4899', '#F59E0B', '#FBBF24'];

            const n = data.counts.length;
            const baseColors = Array.from({length: n}, (_, i) => imagePalette[i % imagePalette.length]);
            const basePull = Array.from({length: n}, () => 0);
            const baseOpacity = Array.from({length: n}, () => 0.9);

            const chartData = [{
                values: data.counts,
                labels: data.labels,
                type: 'pie',
                hole: 0.6,
                sort: false,
                direction: 'clockwise',
                rotation: -90,
                textinfo: 'percent',
                textposition: 'inside',
                insidetextorientation: 'radial',
                textfont: {color: '#e5e7eb', size: 12},
                marker: {
                    colors: baseColors,
                    line: {color: 'rgba(255,255,255,0.08)', width: 2}
                },
                pull: basePull,
                opacity: 1,
                hovertemplate: '%{label}<br>%{value} incidents • %{percent}<extra></extra>'
            }];

            const total = data.counts.reduce((a,b)=>a+b,0);
            const layout = {
                title: 'Incident Severity Distribution',
                height: 400,
                margin: { t: 40, b: 20, l: 20, r: 20 },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                annotations: [
                    {text: `${total}<br><span style="font-size:12px;color:#9ca3af">Incidents</span>`,
                     showarrow: false, font: {size: 18, color: '#9ca3af'}, x: 0.5, y: 0.5}
                ]
            };

            const config = {responsive: true, displaylogo: false, scrollZoom: false};
            const el = document.getElementById('severity-chart');
            await Plotly.newPlot(el, chartData, layout, config);

            const highlight = (idx) => {
                const pull = basePull.slice();
                pull[idx] = 0.08; // emphasize selected slice without changing color
                Plotly.restyle(el, {'pull':[pull], 'opacity':[1]});
            };

            const resetHighlight = () => {
                Plotly.restyle(el, {'pull':[basePull], 'opacity':[1]});
            };

            el.on('plotly_hover', (ev) => {
                if (!ev || !ev.points || !ev.points.length) return;
                highlight(ev.points[0].pointNumber);
            });
            el.on('plotly_unhover', () => resetHighlight());
            el.on('plotly_click', (ev) => {
                if (!ev || !ev.points || !ev.points.length) return;
                const label = ev.points[0].label.toLowerCase();
                this.activeFilters.severity = label;
                this.applyFilters();
            });
        } catch (error) {
            console.error('Failed to create severity chart:', error);
            document.getElementById('severity-chart').innerHTML = '<p class="error">Failed to load chart</p>';
        }
    }
    
    async createRiskChart() {
        try {
            const response = await fetch('/api/charts/risk-distribution');
            const data = await response.json();
            
            const chartData = [{
                x: data.labels,
                y: data.counts,
                type: 'bar',
                marker: {
                    color: data.counts.map(count => this.getRiskColor(count / Math.max(...data.counts)))
                }
            }];
            
            const layout = {
                title: 'Risk Score Distribution',
                height: 400,
                margin: { t: 50, b: 100, l: 50, r: 50 },
                xaxis: { tickangle: -45 },
                hovermode: 'closest'
            };
            
            Plotly.newPlot('risk-distribution', chartData, layout, {responsive: true, displaylogo: false});
        } catch (error) {
            console.error('Failed to create risk chart:', error);
            document.getElementById('risk-distribution').innerHTML = '<p class="error">Failed to load chart</p>';
        }
    }
    
    async createResolutionChart() {
        try {
            const response = await fetch('/api/charts/severity-distribution');
            const data = await response.json();
            
            const chartData = [{
                x: data.labels,
                y: data.avg_resolution_times,
                type: 'bar',
                marker: {
                    color: data.avg_resolution_times.map(time => this.getResolutionColor(time))
                },
                hovertemplate: '%{x}: %{y:.1f} hours<extra></extra>'
            }];
            
            const layout = {
                title: 'Average Resolution Time by Severity',
                height: 400,
                margin: { t: 50, b: 50, l: 50, r: 50 },
                yaxis: { title: 'Hours' }
            };
            
            Plotly.newPlot('resolution-chart', chartData, layout, {responsive: true, displaylogo: false});
        } catch (error) {
            console.error('Failed to create resolution chart:', error);
            document.getElementById('resolution-chart').innerHTML = '<p class="error">Failed to load chart</p>';
        }
    }
    
    async createTrendsChart() {
        try {
            const response = await fetch('/api/trends');
            const data = await response.json();
            
            const chartData = [{
                x: data.trends.map(t => t.date),
                y: data.trends.map(t => t.incident_count),
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Daily Incidents',
                line: { color: '#667eea', width: 3 },
                marker: { size: 6 }
            }];
            
            const layout = {
                title: 'Daily Incident Trends (Last 30 Days)',
                height: 400,
                margin: { t: 50, b: 50, l: 50, r: 50 },
                xaxis: { title: 'Date' },
                yaxis: { title: 'Incident Count' }
            };
            
            Plotly.newPlot('trends-chart', chartData, layout);
        } catch (error) {
            console.error('Failed to create trends chart:', error);
            document.getElementById('trends-chart').innerHTML = '<p class="error">Failed to load chart</p>';
        }
    }
    
    async createForecastChart() {
        try {
            const response = await fetch('/api/forecast/incidents?days=14');
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            const historyX = (data.history || []).map(d => d.date);
            const historyY = (data.history || []).map(d => d.incident_count);
            const forecastX = (data.forecast || []).map(d => d.date);
            const forecastY = (data.forecast || []).map(d => d.predicted_incidents);
            const chartData = [
                { x: historyX, y: historyY, type: 'scatter', mode: 'lines', name: 'History', line: { color: '#60a5fa', width: 3 } },
                { x: forecastX, y: forecastY, type: 'scatter', mode: 'lines', name: 'Forecast', line: { color: '#10b981', width: 3, dash: 'dash' } }
            ];
            const layout = { title: 'Incident Forecast (next 14 days)', height: 400, margin: { t: 50, b: 50, l: 50, r: 50 } };
            Plotly.newPlot('forecast-chart', chartData, layout, {responsive: true, displaylogo: false});
        } catch (error) {
            console.error('Failed to create forecast chart:', error);
            const el = document.getElementById('forecast-chart');
            if (el) el.innerHTML = '<p class="error">Failed to load forecast</p>';
        }
    }
    
    async createAnomalyChart() {
        try {
            const response = await fetch('/api/anomalies/incidents');
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            const seriesX = (data.series || []).map(d => d.date);
            const seriesY = (data.series || []).map(d => d.incident_count);
            const anom = data.anomalies || [];
            const anomX = anom.map(d => d.date);
            const anomY = anom.map(d => d.incident_count);
            const chartData = [
                { x: seriesX, y: seriesY, type: 'scatter', mode: 'lines+markers', name: 'Incidents', line: { color: '#6366f1', width: 3 } },
                { x: anomX, y: anomY, type: 'scatter', mode: 'markers', name: 'Anomalies', marker: { color: '#ef4444', size: 10, symbol: 'diamond' } }
            ];
            const layout = { title: 'Anomaly Detection (z-score ≥ 2)', height: 400, margin: { t: 50, b: 50, l: 50, r: 50 } };
            Plotly.newPlot('anomaly-chart', chartData, layout, {responsive: true, displaylogo: false});
        } catch (error) {
            console.error('Failed to create anomaly chart:', error);
            const el = document.getElementById('anomaly-chart');
            if (el) el.innerHTML = '<p class="error">Failed to load anomalies</p>';
        }
    }
    
    async generateSummary() {
        const incidentId = document.getElementById('incident-selector').value;
        if (!incidentId || incidentId === 'Select Incident...') {
            this.showError('Please select an incident first');
            return;
        }
        
        try {
            const response = await fetch(`/api/ai-summary/${incidentId}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            document.getElementById('summary-output').innerHTML = `
                <div class="ai-summary">
                    <strong>AI-Generated Executive Summary:</strong><br><br>
                    ${data.summary}
                </div>
            `;
            
            this.showSuccess('Executive summary generated successfully');
        } catch (error) {
            console.error('Failed to generate summary:', error);
            this.showError('Failed to generate executive summary');
        }
    }
    
    async findSimilar() {
        const queryText = document.getElementById('query-input').value.trim();
        if (!queryText) {
            this.showError('Please enter a description to search for');
            return;
        }
        
        try {
            const response = await fetch(`/api/similar-incidents?query=${encodeURIComponent(queryText)}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            let resultsHTML = '';
            if (data.results && data.results.length > 0) {
                resultsHTML = '<h4>Similar Incidents Found:</h4>';
                data.results.forEach(result => {
                    resultsHTML += `
                        <div class="similar-item">
                            <h4>${result.incident_id}: ${result.title}</h4>
                            <p><strong>Severity:</strong> ${result.severity} | 
                               <strong>Risk Score:</strong> ${result.risk_score?.toFixed(2) || 'N/A'}</p>
                            <p><strong>Similarity Score:</strong> <span class="similarity-score">${result.similarity_score?.toFixed(2) || 'N/A'}</span></p>
                            <p><em>${result.description}</em></p>
                        </div>
                    `;
                });
            } else {
                resultsHTML = '<p>No similar incidents found.</p>';
            }
            
            document.getElementById('similar-results').innerHTML = resultsHTML;
            this.showSuccess('Similar incidents search completed');
        } catch (error) {
            console.error('Failed to find similar incidents:', error);
            this.showError('Failed to search for similar incidents');
        }
    }
    
    async checkCompliance() {
        const incidentId = document.getElementById('compliance-incident-selector').value;
        if (!incidentId || incidentId === 'Select Incident...') {
            this.showError('Please select an incident first');
            return;
        }
        
        try {
            const response = await fetch(`/api/compliance-check/${incidentId}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            document.getElementById('compliance-output').innerHTML = `
                <div class="success">
                    <h4>Compliance Assessment:</h4>
                    <p><strong>Applicable Policy:</strong> ${data.applicable_policy}</p>
                    <p><strong>Assessment:</strong> ${data.compliance_assessment}</p>
                    <p><strong>Severity:</strong> ${data.severity}</p>
                    <p><strong>Tags:</strong> ${data.tags.join(', ') || 'None'}</p>
                </div>
            `;
            
            this.showSuccess('Compliance check completed');
        } catch (error) {
            console.error('Failed to check compliance:', error);
            this.showError('Failed to check policy compliance');
        }
    }
    
    async loadTrends() {
        try {
            const response = await fetch('/api/trends');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            const trendsOutput = document.getElementById('trends-output');
            
            if (data.trends && data.trends.length > 0) {
                const avgIncidents = (data.trends.reduce((sum, t) => sum + t.incident_count, 0) / data.trends.length).toFixed(1);
                const avgRisk = (data.trends.reduce((sum, t) => sum + t.avg_risk_score, 0) / data.trends.length).toFixed(2);
                
                trendsOutput.innerHTML = `
                    <div class="success">
                        <h4>Risk Trend Analysis (Last 30 Days):</h4>
                        <p><strong>Average Daily Incidents:</strong> ${avgIncidents}</p>
                        <p><strong>Average Risk Score:</strong> ${avgRisk}</p>
                        <p><strong>Trend Period:</strong> ${data.trends.length} days</p>
                    </div>
                `;
            } else {
                trendsOutput.innerHTML = '<p>No trend data available.</p>';
            }
            
            this.showSuccess('Risk trends loaded successfully');
        } catch (error) {
            console.error('Failed to load trends:', error);
            this.showError('Failed to load risk trends');
        }
    }
    
    async refreshData() {
        console.log('🔄 Refreshing dashboard data...');
        await this.loadMetrics();
        await this.loadIncidents();
        this.updateMetricsDisplay();
        this.updateIncidentsTable();
    }
    
    setupEventListeners() {
        // Reset filters button
        const resetBtn = document.getElementById('reset-filters');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.activeFilters = { severity: null };
                this.renderFiltered();
                const label = document.getElementById('active-filter-label');
                if (label) label.textContent = '';
            });
        }
        // Dark mode toggle
        const toggleDark = document.getElementById('toggle-dark');
        if (toggleDark) {
            toggleDark.addEventListener('click', () => {
                document.body.classList.toggle('dark');
            });
        }
        // Quick severity chips
        document.querySelectorAll('.severity-chip').forEach(btn => {
            btn.addEventListener('click', () => {
                const sev = btn.getAttribute('data-sev');
                this.activeFilters.severity = sev;
                const lbl = document.getElementById('table-filter-label');
                if (lbl) lbl.textContent = `Filtering severity: ${sev}`;
                this.renderFiltered();
            });
        });
        console.log('✅ Event listeners configured');
        // Role select
        const roleSel = document.getElementById('role-select');
        if (roleSel) {
            roleSel.addEventListener('change', async () => {
                const v = roleSel.value;
                document.cookie = `user_role=${v}; path=/; max-age=864000`;
                await this.loadRBAC();
            });
        }
        // Evidence actions
        const loadEvBtn = document.getElementById('load-evidence-btn');
        if (loadEvBtn) loadEvBtn.addEventListener('click', () => this.loadEvidence());
        const addEvBtn = document.getElementById('add-evidence-btn');
        if (addEvBtn) addEvBtn.addEventListener('click', () => this.addEvidence());
        // Feedback action
        const fbBtn = document.getElementById('submit-feedback-btn');
        if (fbBtn) fbBtn.addEventListener('click', () => this.submitFeedback());
    }
    
    // Utility methods
    applyFilters() {
        const label = document.getElementById('active-filter-label');
        if (this.activeFilters.severity && label) {
            label.textContent = `Filtering severity: ${this.activeFilters.severity}`;
        }
        this.renderFiltered();
    }

    renderFiltered() {
        // Filter incidents table and metrics based on active filters
        let filtered = [...this.incidents];
        if (this.activeFilters.severity) {
            filtered = filtered.filter(i => (i.severity || '').toLowerCase() === this.activeFilters.severity);
        }
        // Re-render incidents subset
        const original = this.incidents;
        this.incidents = filtered;
        this.updateIncidentsTable();
        // Restore for future operations but keep UI filtered label
        this.incidents = original;
    }
    getSeverityColor(severity) {
        const colors = {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        };
        return colors[severity?.toLowerCase()] || '#6c757d';
    }
    
    getRiskColor(riskScore) {
        if (riskScore >= 0.8) return '#dc3545';
        if (riskScore >= 0.6) return '#fd7e14';
        if (riskScore >= 0.4) return '#ffc107';
        if (riskScore >= 0.2) return '#28a745';
        return '#6c757d';
    }
    
    getResolutionColor(hours) {
        if (hours >= 8) return '#dc3545';
        if (hours >= 6) return '#fd7e14';
        if (hours >= 4) return '#ffc107';
        if (hours >= 2) return '#28a745';
        return '#6c757d';
    }
    
    getStatusIndicator(status) {
        const indicators = {
            'open': '<span class="status-indicator status-open"></span>',
            'resolved': '<span class="status-indicator status-resolved"></span>',
            'in-progress': '<span class="status-indicator status-in-progress"></span>'
        };
        return indicators[status?.toLowerCase()] || '<span class="status-indicator status-open"></span>';
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = type;
        notification.textContent = message;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '1000';
        notification.style.minWidth = '300px';
        notification.style.maxWidth = '500px';
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Global functions for HTML buttons
function generateSummary() {
    if (window.dashboard) {
        window.dashboard.generateSummary();
    }
}

function findSimilar() {
    if (window.dashboard) {
        window.dashboard.findSimilar();
    }
}

function checkCompliance() {
    if (window.dashboard) {
        window.dashboard.checkCompliance();
    }
}

function loadTrends() {
    if (window.dashboard) {
        window.dashboard.loadTrends();
    }
}

function loadEvidence() {
    if (window.dashboard) {
        window.dashboard.loadEvidence();
    }
}

function addEvidence() {
    if (window.dashboard) {
        window.dashboard.addEvidence();
    }
}

function submitFeedback() {
    if (window.dashboard) {
        window.dashboard.submitFeedback();
    }
}

function setRole(role) {
    document.cookie = `user_role=${role}; path=/; max-age=864000`;
    if (window.dashboard) {
        window.dashboard.loadRBAC();
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 SI²A Dashboard Loading...');
    window.dashboard = new SI2ADashboard();
});
