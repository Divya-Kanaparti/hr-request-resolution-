-- ========================================================
-- HR Request Resolution & Policy Intelligence Schema
-- Compatible with PostgreSQL 14+ and MySQL 8.0+
-- ========================================================

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    dept_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE,
    code VARCHAR(32) NOT NULL UNIQUE,
    manager_id VARCHAR(32) NULL,
    location VARCHAR(120) NOT NULL DEFAULT 'Headquarters',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Employees Table
CREATE TABLE IF NOT EXISTS employees (
    emp_id VARCHAR(32) PRIMARY KEY,
    email VARCHAR(160) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    department_id VARCHAR(32) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'EMPLOYEE',
    employment_type VARCHAR(32) NOT NULL DEFAULT 'FULL_TIME',
    hire_date DATE NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_emp_dept FOREIGN KEY (department_id) REFERENCES departments (dept_id) ON DELETE RESTRICT
);

-- 3. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    category_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE,
    code VARCHAR(32) NOT NULL UNIQUE,
    description TEXT NULL,
    default_priority VARCHAR(32) NOT NULL DEFAULT 'MEDIUM',
    is_sensitive_default BOOLEAN NOT NULL DEFAULT FALSE,
    tier VARCHAR(32) NOT NULL DEFAULT 'TIER_1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Business Calendars Table
CREATE TABLE IF NOT EXISTS business_calendars (
    calendar_id VARCHAR(32) PRIMARY KEY,
    calendar_name VARCHAR(120) NOT NULL,
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    business_hour_start INT NOT NULL DEFAULT 9,
    business_hour_end INT NOT NULL DEFAULT 17,
    work_days VARCHAR(32) NOT NULL DEFAULT '0,1,2,3,4',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Holidays Table
CREATE TABLE IF NOT EXISTS holidays (
    holiday_id VARCHAR(32) PRIMARY KEY,
    calendar_id VARCHAR(32) NOT NULL,
    name VARCHAR(120) NOT NULL,
    holiday_date DATE NOT NULL,
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_holiday_calendar FOREIGN KEY (calendar_id) REFERENCES business_calendars (calendar_id) ON DELETE CASCADE
);

-- 6. SLA Plans Table
CREATE TABLE IF NOT EXISTS sla_plans (
    plan_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    category_id VARCHAR(32) NULL,
    priority VARCHAR(32) NOT NULL,
    response_hours FLOAT NOT NULL,
    resolution_hours FLOAT NOT NULL,
    calendar_id VARCHAR(32) NOT NULL,
    allow_clarification_pause BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_plan_category FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE CASCADE,
    CONSTRAINT fk_plan_calendar FOREIGN KEY (calendar_id) REFERENCES business_calendars (calendar_id) ON DELETE RESTRICT
);

-- 7. Routing Rules Table
CREATE TABLE IF NOT EXISTS routing_rules (
    rule_id VARCHAR(32) PRIMARY KEY,
    rule_name VARCHAR(120) NOT NULL,
    description TEXT NULL,
    priority INT NOT NULL DEFAULT 100,
    condition_expression TEXT NOT NULL,
    target_category_id VARCHAR(32) NULL,
    target_tier VARCHAR(32) NOT NULL DEFAULT 'TIER_1',
    target_queue VARCHAR(64) NOT NULL,
    is_confidential_route BOOLEAN NOT NULL DEFAULT FALSE,
    auto_assign_role VARCHAR(48) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Escalation Rules Table
CREATE TABLE IF NOT EXISTS escalation_rules (
    rule_id VARCHAR(32) PRIMARY KEY,
    rule_name VARCHAR(120) NOT NULL,
    description TEXT NULL,
    priority INT NOT NULL DEFAULT 100,
    trigger_condition VARCHAR(64) NOT NULL,
    threshold_percent INT NOT NULL DEFAULT 75,
    escalate_to_role VARCHAR(48) NOT NULL,
    escalate_to_queue VARCHAR(64) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Policy Documents Table
CREATE TABLE IF NOT EXISTS policy_documents (
    policy_id VARCHAR(48) PRIMARY KEY,
    doc_code VARCHAR(48) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    category_id VARCHAR(32) NOT NULL,
    department_id VARCHAR(32) NOT NULL,
    audience VARCHAR(48) NOT NULL DEFAULT 'ALL_EMPLOYEES',
    jurisdiction VARCHAR(48) NOT NULL DEFAULT 'GLOBAL',
    owner_id VARCHAR(32) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pol_category FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_pol_dept FOREIGN KEY (department_id) REFERENCES departments (dept_id) ON DELETE RESTRICT,
    CONSTRAINT fk_pol_owner FOREIGN KEY (owner_id) REFERENCES employees (emp_id) ON DELETE RESTRICT
);

-- 10. Policy Versions Table
CREATE TABLE IF NOT EXISTS policy_versions (
    version_id VARCHAR(48) PRIMARY KEY,
    policy_id VARCHAR(48) NOT NULL,
    version_number VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,
    approved_by VARCHAR(32) NOT NULL,
    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    superseded_by_version_id VARCHAR(48) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ver_policy FOREIGN KEY (policy_id) REFERENCES policy_documents (policy_id) ON DELETE CASCADE,
    CONSTRAINT fk_ver_approver FOREIGN KEY (approved_by) REFERENCES employees (emp_id) ON DELETE RESTRICT
);

-- 11. Knowledge Articles Table
CREATE TABLE IF NOT EXISTS knowledge_articles (
    article_id VARCHAR(48) PRIMARY KEY,
    policy_version_id VARCHAR(48) NOT NULL,
    title VARCHAR(255) NOT NULL,
    section_number VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    keywords VARCHAR(255) NOT NULL,
    audience VARCHAR(48) NOT NULL DEFAULT 'ALL_EMPLOYEES',
    is_published BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_art_version FOREIGN KEY (policy_version_id) REFERENCES policy_versions (version_id) ON DELETE CASCADE
);

-- 12. Tickets Table
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id VARCHAR(48) PRIMARY KEY,
    tracking_number VARCHAR(48) NOT NULL UNIQUE,
    employee_id VARCHAR(32) NOT NULL,
    category_id VARCHAR(32) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(48) NOT NULL DEFAULT 'NEW',
    priority VARCHAR(32) NOT NULL DEFAULT 'MEDIUM',
    is_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
    confidential_assigned_to VARCHAR(32) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    CONSTRAINT fk_ticket_emp FOREIGN KEY (employee_id) REFERENCES employees (emp_id) ON DELETE RESTRICT,
    CONSTRAINT fk_ticket_cat FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_ticket_conf_agent FOREIGN KEY (confidential_assigned_to) REFERENCES employees (emp_id) ON DELETE SET NULL
);

-- 13. Ticket Participants Table
CREATE TABLE IF NOT EXISTS ticket_participants (
    participant_id VARCHAR(48) PRIMARY KEY,
    ticket_id VARCHAR(48) NOT NULL,
    employee_id VARCHAR(32) NOT NULL,
    role_in_ticket VARCHAR(48) NOT NULL DEFAULT 'COLLABORATOR',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_part_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_part_emp FOREIGN KEY (employee_id) REFERENCES employees (emp_id) ON DELETE CASCADE
);

-- 14. Assignments Table
CREATE TABLE IF NOT EXISTS assignments (
    assignment_id VARCHAR(48) PRIMARY KEY,
    ticket_id VARCHAR(48) NOT NULL,
    assigned_to_id VARCHAR(32) NOT NULL,
    assigned_by_id VARCHAR(32) NOT NULL,
    tier VARCHAR(32) NOT NULL DEFAULT 'TIER_1',
    reason VARCHAR(255) NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unassigned_at TIMESTAMP NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_asg_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_asg_to FOREIGN KEY (assigned_to_id) REFERENCES employees (emp_id) ON DELETE RESTRICT,
    CONSTRAINT fk_asg_by FOREIGN KEY (assigned_by_id) REFERENCES employees (emp_id) ON DELETE RESTRICT
);

-- 15. SLAs Table
CREATE TABLE IF NOT EXISTS slas (
    sla_id VARCHAR(48) PRIMARY KEY,
    ticket_id VARCHAR(48) NOT NULL UNIQUE,
    priority VARCHAR(32) NOT NULL,
    business_hours_limit INT NOT NULL,
    response_due_at TIMESTAMP NOT NULL,
    resolution_due_at TIMESTAMP NOT NULL,
    first_response_at TIMESTAMP NULL,
    is_response_breached BOOLEAN NOT NULL DEFAULT FALSE,
    is_resolution_breached BOOLEAN NOT NULL DEFAULT FALSE,
    calculated_business_hours FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sla_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE
);

-- 16. Messages Table
CREATE TABLE IF NOT EXISTS messages (
    message_id VARCHAR(48) PRIMARY KEY,
    ticket_id VARCHAR(48) NOT NULL,
    sender_id VARCHAR(32) NOT NULL,
    message_type VARCHAR(48) NOT NULL,
    content TEXT NOT NULL,
    citations_json TEXT NULL,
    is_internal BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_msg_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_msg_sender FOREIGN KEY (sender_id) REFERENCES employees (emp_id) ON DELETE RESTRICT
);

-- 17. Resolutions Table
CREATE TABLE IF NOT EXISTS resolutions (
    resolution_id VARCHAR(48) PRIMARY KEY,
    ticket_id VARCHAR(48) NOT NULL UNIQUE,
    resolved_by_id VARCHAR(32) NOT NULL,
    resolution_type VARCHAR(48) NOT NULL,
    resolution_notes TEXT NOT NULL,
    root_cause VARCHAR(255) NULL,
    policy_version_used_id VARCHAR(48) NULL,
    employee_rating INT NULL,
    employee_feedback TEXT NULL,
    resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_res_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_res_resolver FOREIGN KEY (resolved_by_id) REFERENCES employees (emp_id) ON DELETE RESTRICT,
    CONSTRAINT fk_res_version FOREIGN KEY (policy_version_used_id) REFERENCES policy_versions (version_id) ON DELETE SET NULL
);

-- 18. Ticket Events Table
CREATE TABLE IF NOT EXISTS ticket_events (
    event_id VARCHAR(48) PRIMARY KEY,
    ticket_id VARCHAR(48) NOT NULL,
    event_type VARCHAR(48) NOT NULL,
    previous_state VARCHAR(48) NULL,
    new_state VARCHAR(48) NOT NULL,
    actor_id VARCHAR(32) NULL,
    actor_role VARCHAR(48) NULL,
    reason TEXT NULL,
    correlation_id VARCHAR(64) NULL,
    related_policy_id VARCHAR(48) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_evt_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_evt_actor FOREIGN KEY (actor_id) REFERENCES employees (emp_id) ON DELETE SET NULL
);

-- 19. Policy Citations Table
CREATE TABLE IF NOT EXISTS policy_citations (
    citation_id VARCHAR(48) PRIMARY KEY,
    ticket_id VARCHAR(48) NOT NULL,
    message_id VARCHAR(48) NULL,
    resolution_id VARCHAR(48) NULL,
    policy_id VARCHAR(48) NOT NULL,
    policy_version_id VARCHAR(48) NOT NULL,
    article_id VARCHAR(48) NULL,
    passage_identifier VARCHAR(64) NULL,
    exact_passage TEXT NOT NULL,
    policy_effective_date DATE NOT NULL,
    decision_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cit_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_cit_msg FOREIGN KEY (message_id) REFERENCES messages (message_id) ON DELETE SET NULL,
    CONSTRAINT fk_cit_res FOREIGN KEY (resolution_id) REFERENCES resolutions (resolution_id) ON DELETE SET NULL,
    CONSTRAINT fk_cit_pol FOREIGN KEY (policy_id) REFERENCES policy_documents (policy_id) ON DELETE CASCADE,
    CONSTRAINT fk_cit_ver FOREIGN KEY (policy_version_id) REFERENCES policy_versions (version_id) ON DELETE CASCADE,
    CONSTRAINT fk_cit_art FOREIGN KEY (article_id) REFERENCES knowledge_articles (article_id) ON DELETE SET NULL
);

-- 20. Decision Traces Table
CREATE TABLE IF NOT EXISTS decision_traces (
    trace_id VARCHAR(48) PRIMARY KEY,
    ticket_id VARCHAR(48) NOT NULL,
    stage VARCHAR(64) NOT NULL,
    input_context_json TEXT NULL,
    output_decision VARCHAR(120) NOT NULL,
    rule_id_applied VARCHAR(48) NULL,
    rationale TEXT NOT NULL,
    is_automated BOOLEAN NOT NULL DEFAULT TRUE,
    actor_id VARCHAR(32) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_trace_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_trace_actor FOREIGN KEY (actor_id) REFERENCES employees (emp_id) ON DELETE SET NULL
);

-- 21. Anomaly Records Table
CREATE TABLE IF NOT EXISTS anomaly_records (
    anomaly_id VARCHAR(48) PRIMARY KEY,
    ticket_id VARCHAR(48) NOT NULL,
    anomaly_type VARCHAR(48) NOT NULL,
    severity VARCHAR(32) NOT NULL DEFAULT 'HIGH',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'DETECTED',
    ground_truth_label BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_anom_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE
);

-- 22. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id VARCHAR(48) PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    actor_id VARCHAR(32) NULL,
    target_resource VARCHAR(64) NOT NULL,
    target_id VARCHAR(48) NOT NULL,
    details TEXT NULL,
    ip_address VARCHAR(48) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 23. Evaluation Runs Table
CREATE TABLE IF NOT EXISTS evaluation_runs (
    evaluation_id VARCHAR(48) PRIMARY KEY,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dataset_profile VARCHAR(32) NOT NULL,
    seed_used INT NOT NULL DEFAULT 20261022,
    total_tickets_evaluated INT NOT NULL,
    classification_accuracy FLOAT NOT NULL,
    classification_macro_f1 FLOAT NOT NULL,
    routing_accuracy FLOAT NOT NULL,
    sensitive_routing_precision FLOAT NOT NULL,
    sensitive_routing_recall FLOAT NOT NULL,
    valid_citation_rate FLOAT NOT NULL,
    clarification_precision FLOAT NOT NULL,
    clarification_recall FLOAT NOT NULL,
    sla_calculation_accuracy FLOAT NOT NULL,
    anomaly_precision FLOAT NOT NULL,
    anomaly_recall FLOAT NOT NULL,
    anomaly_f1 FLOAT NOT NULL,
    metrics_summary_json TEXT NOT NULL,
    confusion_matrix_json TEXT NULL
);

-- 24. Dataset Manifests Table
CREATE TABLE IF NOT EXISTS dataset_manifests (
    manifest_id VARCHAR(48) PRIMARY KEY,
    profile VARCHAR(32) NOT NULL,
    seed INT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_manifest_json TEXT NOT NULL,
    overall_checksum VARCHAR(64) NOT NULL
);
