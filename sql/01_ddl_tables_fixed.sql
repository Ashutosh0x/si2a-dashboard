-- SI²A: Shadow IT Incident Autopilot - Database Schema (Fixed)
-- This file creates all tables needed for the BigQuery AI-powered security incident triage system

-- =============================================================================
-- RAW LAYER (Bronze) - Raw data ingestion
-- =============================================================================

-- CASB/SaaS security events from various sources
CREATE OR REPLACE TABLE `${PROJECT_ID}.si2a_raw.events_casb` (
  event_id STRING,
  timestamp TIMESTAMP,
  user_email STRING,
  application STRING,
  event_type STRING,
  severity STRING,
  ip_address STRING,
  user_agent STRING,
  raw_data JSON,
  source_system STRING,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Support tickets and emails
CREATE OR REPLACE TABLE `${PROJECT_ID}.si2a_raw.support_emails` (
  email_id STRING,
  timestamp TIMESTAMP,
  from_email STRING,
  to_email STRING,
  subject STRING,
  body STRING,
  headers JSON,
  attachments ARRAY<STRING>,
  priority STRING,
  category STRING,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Policy documents and compliance requirements
CREATE OR REPLACE TABLE `${PROJECT_ID}.si2a_raw.policy_documents` (
  policy_id STRING,
  policy_name STRING,
  version STRING,
  effective_date DATE,
  content STRING,
  category STRING,
  owner STRING,
  status STRING,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- FEATURE LAYER (Silver) - Processed features and embeddings
-- =============================================================================

-- Text embeddings for incidents
CREATE OR REPLACE TABLE `${PROJECT_ID}.si2a_feat.incident_text_embed` (
  incident_id STRING,
  embedding ARRAY<FLOAT64>,
  text_content STRING,
  embedding_model STRING DEFAULT 'bqml.textembedding.gecko',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Text embeddings for policy sections
CREATE OR REPLACE TABLE `${PROJECT_ID}.si2a_feat.policy_embed` (
  policy_section_id STRING,
  embedding ARRAY<FLOAT64>,
  section_text STRING,
  policy_id STRING,
  section_title STRING,
  embedding_model STRING DEFAULT 'bqml.textembedding.gecko',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- GOLD LAYER (Business Logic) - Enriched, business-ready data
-- =============================================================================

-- Enriched incidents with all related data
CREATE OR REPLACE TABLE `${PROJECT_ID}.si2a_gold.incidents` (
  incident_id STRING,
  title STRING,
  description STRING,
  severity STRING,
  status STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  assigned_to STRING,
  category STRING,
  root_cause STRING,
  resolution STRING,
  resolution_time_hours FLOAT64,
  affected_users INT64,
  affected_systems ARRAY<STRING>,
  related_incidents ARRAY<STRING>,
  policy_violations ARRAY<STRING>,
  artifacts ARRAY<STRING>, -- GCS URIs
  tags ARRAY<STRING>,
  business_impact STRING,
  risk_score FLOAT64,
  created_by STRING,
  last_modified_by STRING
);

-- Policy sections for compliance checking
CREATE OR REPLACE TABLE `${PROJECT_ID}.si2a_dim.policy_sections` (
  section_id STRING,
  policy_id STRING,
  section_title STRING,
  section_text STRING,
  section_number STRING,
  category STRING,
  compliance_level STRING, -- required, recommended, optional
  effective_date DATE,
  expiry_date DATE,
  owner STRING,
  status STRING,
  version STRING
);

-- Daily incident metrics for forecasting
CREATE OR REPLACE TABLE `${PROJECT_ID}.si2a_marts.incident_daily` (
  date DATE,
  total_incidents INT64,
  high_severity_incidents INT64,
  medium_severity_incidents INT64,
  low_severity_incidents INT64,
  avg_resolution_time_hours FLOAT64,
  incidents_by_category STRUCT<
    security_breach INT64,
    policy_violation INT64,
    system_outage INT64,
    data_leak INT64,
    unauthorized_access INT64
  >,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- SAMPLE DATA INSERTION
-- =============================================================================

-- Insert sample policy sections
INSERT INTO `${PROJECT_ID}.si2a_dim.policy_sections` (section_id, policy_id, section_title, section_text, section_number, category, compliance_level, effective_date, owner, status, version)
VALUES
  ('MFA-001', 'MFA-POLICY', 'Multi-Factor Authentication Requirements', 'All users must enable MFA for accessing corporate resources. MFA must be enabled within 24 hours of account creation. Failure to enable MFA will result in account suspension.', '1.1', 'Authentication', 'required', DATE '2024-01-01', 'Security Team', 'active', '1.0'),
  ('MFA-002', 'MFA-POLICY', 'MFA Exemptions', 'MFA exemptions may be granted for service accounts and emergency access scenarios. All exemptions must be documented and reviewed quarterly.', '1.2', 'Authentication', 'required', DATE '2024-01-01', 'Security Team', 'active', '1.0'),
  ('SAAS-001', 'SAAS-POLICY', 'SaaS Application Approval', 'All new SaaS applications must be approved by the IT security team before procurement. Applications must meet security requirements including SSO integration and data encryption.', '2.1', 'Application Security', 'required', DATE '2024-01-01', 'IT Team', 'active', '1.0'),
  ('SAAS-002', 'SAAS-POLICY', 'Shadow IT Reporting', 'Employees must report any unauthorized SaaS applications they discover. Failure to report may result in disciplinary action.', '2.2', 'Application Security', 'required', DATE '2024-01-01', 'IT Team', 'active', '1.0'),
  ('DATA-001', 'DATA-POLICY', 'Data Classification', 'All corporate data must be classified as public, internal, confidential, or restricted. Data handling procedures vary by classification level.', '3.1', 'Data Protection', 'required', DATE '2024-01-01', 'Legal Team', 'active', '1.0');

-- Insert sample incidents
INSERT INTO `${PROJECT_ID}.si2a_gold.incidents` (incident_id, title, description, severity, status, created_at, assigned_to, category, root_cause, resolution, resolution_time_hours, affected_users, affected_systems, tags, business_impact, risk_score)
VALUES
  ('INC-2024-001', 'Unauthorized SaaS Application Detected', 'CASB detected user john.doe@company.com accessing unauthorized project management tool "TrelloClone" without approval. User has been accessing the application for 3 weeks.', 'medium', 'resolved', TIMESTAMP '2024-01-15 09:30:00', 'security-analyst-1', 'shadow_it', 'User bypassed approval process', 'Application access blocked, user educated on policy, formal warning issued', 4.5, 1, ['TrelloClone'], ['shadow_it', 'policy_violation'], 'Low - single user, no data loss', 0.6),
  ('INC-2024-002', 'MFA Bypass Attempt Detected', 'Multiple failed MFA attempts detected for user jane.smith@company.com from suspicious IP address 192.168.1.100. Account shows signs of potential compromise.', 'high', 'investigating', TIMESTAMP '2024-01-16 14:20:00', 'security-analyst-2', 'authentication', 'Potential credential stuffing attack', 'Account temporarily locked, user contacted, investigation ongoing', 2.0, 1, ['Active Directory', 'Email System'], ['mfa_bypass', 'potential_breach'], 'High - potential account compromise', 0.9),
  ('INC-2024-003', 'Data Exfiltration Attempt', 'Large volume of data download detected from user mike.wilson@company.com. User downloaded 2GB of customer data to personal device.', 'high', 'resolved', TIMESTAMP '2024-01-17 11:15:00', 'security-analyst-1', 'data_leak', 'User violated data handling policy', 'Data access revoked, incident reported to management, disciplinary action taken', 6.0, 1, ['CRM System', 'File Server'], ['data_leak', 'policy_violation'], 'High - potential data breach', 0.8),
  ('INC-2024-004', 'Suspicious Login Pattern', 'User sarah.jones@company.com logged in from 5 different countries within 24 hours. Travel policy indicates user should only be in US.', 'medium', 'resolved', TIMESTAMP '2024-01-18 08:45:00', 'security-analyst-3', 'authentication', 'VPN usage or account compromise', 'User confirmed legitimate travel, VPN usage documented', 1.5, 1, ['VPN System'], ['suspicious_activity'], 'Medium - resolved quickly', 0.4),
  ('INC-2024-005', 'Unapproved Cloud Storage Usage', 'CASB detected team using unapproved cloud storage service "CloudSync" for sharing sensitive project documents.', 'medium', 'investigating', TIMESTAMP '2024-01-19 16:30:00', 'security-analyst-2', 'shadow_it', 'Team seeking alternative to approved tools', 'Investigation ongoing, team contacted for explanation', 3.0, 5, ['CloudSync'], ['shadow_it', 'team_violation'], 'Medium - team-wide policy violation', 0.7);

-- Insert sample daily metrics
INSERT INTO `${PROJECT_ID}.si2a_marts.incident_daily` (date, total_incidents, high_severity_incidents, medium_severity_incidents, low_severity_incidents, avg_resolution_time_hours, incidents_by_category)
VALUES
  (DATE '2024-01-15', 1, 0, 1, 0, 4.5, STRUCT(0, 1, 0, 0, 0)),
  (DATE '2024-01-16', 1, 1, 0, 0, 2.0, STRUCT(0, 0, 0, 0, 1)),
  (DATE '2024-01-17', 1, 1, 0, 0, 6.0, STRUCT(0, 0, 0, 1, 0)),
  (DATE '2024-01-18', 1, 0, 1, 0, 1.5, STRUCT(0, 0, 0, 0, 1)),
  (DATE '2024-01-19', 1, 0, 1, 0, 3.0, STRUCT(0, 1, 0, 0, 0));

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- View for active incidents
CREATE OR REPLACE VIEW `${PROJECT_ID}.si2a_vw_active_incidents` AS
SELECT 
  incident_id,
  title,
  severity,
  status,
  created_at,
  assigned_to,
  category,
  business_impact,
  risk_score
FROM `${PROJECT_ID}.si2a_gold.incidents`
WHERE status IN ('new', 'investigating', 'in_progress')
ORDER BY created_at DESC;

-- View for incident metrics
CREATE OR REPLACE VIEW `${PROJECT_ID}.si2a_vw_incident_metrics` AS
SELECT 
  DATE(created_at) as incident_date,
  COUNT(*) as total_incidents,
  COUNTIF(severity = 'high') as high_severity,
  COUNTIF(severity = 'medium') as medium_severity,
  COUNTIF(severity = 'low') as low_severity,
  AVG(resolution_time_hours) as avg_resolution_time,
  COUNTIF(status = 'resolved') as resolved_incidents
FROM `${PROJECT_ID}.si2a_gold.incidents`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY DATE(created_at)
ORDER BY incident_date DESC;
