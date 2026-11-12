-- ========================================================
-- HR Request Resolution System - MySQL Database Schema
-- Version: 1.0.0
-- ========================================================

CREATE DATABASE IF NOT EXISTS hr_request_resolution
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE hr_request_resolution;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS anomaly_records;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS resolutions;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS slas;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS knowledge_articles;
DROP TABLE IF EXISTS policy_versions;
DROP TABLE IF EXISTS policy_documents;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

SET FOREIGN_KEY_CHECKS = 1;

-- 1. Departments Table
CREATE TABLE departments (
    dept_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE,
    code VARCHAR(32) NOT NULL UNIQUE,
    manager_id VARCHAR(32) NULL,
    location VARCHAR(120) NOT NULL DEFAULT 'Headquarters',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dept_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Employees Table
CREATE TABLE employees (
    emp_id VARCHAR(32) PRIMARY KEY,
    email VARCHAR(160) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    department_id VARCHAR(32) NOT NULL,
    role ENUM('EMPLOYEE', 'HR_AGENT', 'HR_MANAGER', 'ADMIN', 'COMPLIANCE_OFFICER') NOT NULL DEFAULT 'EMPLOYEE',
    employment_type ENUM('FULL_TIME', 'PART_TIME', 'CONTRACT', 'INTERN') NOT NULL DEFAULT 'FULL_TIME',
    hire_date DATE NOT NULL,
    status ENUM('ACTIVE', 'ON_LEAVE', 'SUSPENDED', 'TERMINATED') NOT NULL DEFAULT 'ACTIVE',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_emp_email (email),
    INDEX idx_emp_role (role),
    INDEX idx_emp_dept (department_id),
    CONSTRAINT fk_emp_dept FOREIGN KEY (department_id) REFERENCES departments (dept_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add manager FK to departments now that employees exists
ALTER TABLE departments
    ADD CONSTRAINT fk_dept_manager FOREIGN KEY (manager_id) REFERENCES employees (emp_id) ON DELETE SET NULL;

-- 3. Categories Table
CREATE TABLE categories (
    category_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(32) NOT NULL UNIQUE,
    description TEXT NULL,
    default_priority ENUM('LOW', 'MEDIUM', 'HIGH', 'URGENT') NOT NULL DEFAULT 'MEDIUM',
    is_sensitive_default BOOLEAN NOT NULL DEFAULT FALSE,
    tier ENUM('TIER_1', 'TIER_2', 'TIER_3') NOT NULL DEFAULT 'TIER_1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cat_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Policy Documents Table
CREATE TABLE policy_documents (
    policy_id VARCHAR(32) PRIMARY KEY,
    doc_code VARCHAR(40) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    category_id VARCHAR(32) NOT NULL,
    department_id VARCHAR(32) NOT NULL,
    audience ENUM('ALL_EMPLOYEES', 'MANAGERS_ONLY', 'FULL_TIME_ONLY', 'CONTRACTORS', 'HR_ONLY') NOT NULL DEFAULT 'ALL_EMPLOYEES',
    owner_id VARCHAR(32) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_policy_code (doc_code),
    INDEX idx_policy_cat (category_id),
    CONSTRAINT fk_pol_cat FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_pol_dept FOREIGN KEY (department_id) REFERENCES departments (dept_id) ON DELETE RESTRICT,
    CONSTRAINT fk_pol_owner FOREIGN KEY (owner_id) REFERENCES employees (emp_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Policy Versions Table
CREATE TABLE policy_versions (
    version_id VARCHAR(32) PRIMARY KEY,
    policy_id VARCHAR(32) NOT NULL,
    version_number VARCHAR(16) NOT NULL,
    status ENUM('DRAFT', 'ACTIVE', 'ARCHIVED', 'SUPERSEDED') NOT NULL DEFAULT 'DRAFT',
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    summary TEXT NOT NULL,
    content MEDIUMTEXT NOT NULL,
    changelog TEXT NULL,
    approved_by VARCHAR(32) NULL,
    approved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_policy_version (policy_id, version_number),
    INDEX idx_pver_status (status),
    INDEX idx_pver_effective (effective_from, effective_to),
    CONSTRAINT fk_pver_policy FOREIGN KEY (policy_id) REFERENCES policy_documents (policy_id) ON DELETE CASCADE,
    CONSTRAINT fk_pver_approver FOREIGN KEY (approved_by) REFERENCES employees (emp_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Knowledge Articles Table
CREATE TABLE knowledge_articles (
    article_id VARCHAR(32) PRIMARY KEY,
    policy_version_id VARCHAR(32) NOT NULL,
    title VARCHAR(220) NOT NULL,
    section_number VARCHAR(32) NOT NULL,
    content MEDIUMTEXT NOT NULL,
    keywords VARCHAR(500) NULL,
    audience ENUM('ALL_EMPLOYEES', 'MANAGERS_ONLY', 'FULL_TIME_ONLY', 'CONTRACTORS', 'HR_ONLY') NOT NULL DEFAULT 'ALL_EMPLOYEES',
    is_published BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_kart_pver (policy_version_id),
    INDEX idx_kart_section (section_number),
    CONSTRAINT fk_kart_pver FOREIGN KEY (policy_version_id) REFERENCES policy_versions (version_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Tickets Table
CREATE TABLE tickets (
    ticket_id VARCHAR(32) PRIMARY KEY,
    tracking_number VARCHAR(48) NOT NULL UNIQUE,
    employee_id VARCHAR(32) NOT NULL,
    category_id VARCHAR(32) NOT NULL,
    title VARCHAR(220) NOT NULL,
    description MEDIUMTEXT NOT NULL,
    status ENUM('NEW', 'CLARIFICATION_NEEDED', 'IN_PROGRESS', 'ESCALATED', 'RESOLVED', 'CLOSED') NOT NULL DEFAULT 'NEW',
    priority ENUM('LOW', 'MEDIUM', 'HIGH', 'URGENT') NOT NULL DEFAULT 'MEDIUM',
    is_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
    confidential_assigned_to VARCHAR(32) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    INDEX idx_tck_tracking (tracking_number),
    INDEX idx_tck_emp (employee_id),
    INDEX idx_tck_cat (category_id),
    INDEX idx_tck_status (status),
    INDEX idx_tck_priority (priority),
    INDEX idx_tck_sensitive (is_sensitive),
    CONSTRAINT fk_tck_emp FOREIGN KEY (employee_id) REFERENCES employees (emp_id) ON DELETE RESTRICT,
    CONSTRAINT fk_tck_cat FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_tck_confidential FOREIGN KEY (confidential_assigned_to) REFERENCES employees (emp_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Assignments Table
CREATE TABLE assignments (
    assignment_id VARCHAR(32) PRIMARY KEY,
    ticket_id VARCHAR(32) NOT NULL,
    assigned_to_id VARCHAR(32) NOT NULL,
    assigned_by_id VARCHAR(32) NOT NULL,
    tier ENUM('TIER_1', 'TIER_2', 'TIER_3') NOT NULL DEFAULT 'TIER_1',
    reason VARCHAR(255) NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unassigned_at TIMESTAMP NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_asg_ticket (ticket_id),
    INDEX idx_asg_agent (assigned_to_id),
    INDEX idx_asg_active (is_active),
    CONSTRAINT fk_asg_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_asg_target FOREIGN KEY (assigned_to_id) REFERENCES employees (emp_id) ON DELETE RESTRICT,
    CONSTRAINT fk_asg_actor FOREIGN KEY (assigned_by_id) REFERENCES employees (emp_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. SLAs Table
CREATE TABLE slas (
    sla_id VARCHAR(32) PRIMARY KEY,
    ticket_id VARCHAR(32) NOT NULL UNIQUE,
    priority ENUM('LOW', 'MEDIUM', 'HIGH', 'URGENT') NOT NULL DEFAULT 'MEDIUM',
    business_hours_limit INT NOT NULL DEFAULT 24,
    response_due_at TIMESTAMP NOT NULL,
    resolution_due_at TIMESTAMP NOT NULL,
    first_response_at TIMESTAMP NULL,
    is_response_breached BOOLEAN NOT NULL DEFAULT FALSE,
    is_resolution_breached BOOLEAN NOT NULL DEFAULT FALSE,
    calculated_business_hours DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sla_due (resolution_due_at),
    INDEX idx_sla_breached (is_resolution_breached),
    CONSTRAINT fk_sla_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Messages Table
CREATE TABLE messages (
    message_id VARCHAR(32) PRIMARY KEY,
    ticket_id VARCHAR(32) NOT NULL,
    sender_id VARCHAR(32) NOT NULL,
    message_type ENUM('EMPLOYEE_NOTE', 'AGENT_REPLY', 'INTERNAL_NOTE', 'SYSTEM_EVENT', 'CLARIFICATION_PROMPT') NOT NULL,
    content MEDIUMTEXT NOT NULL,
    citations_json JSON NULL,
    is_internal BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_msg_ticket (ticket_id),
    INDEX idx_msg_sender (sender_id),
    INDEX idx_msg_type (message_type),
    CONSTRAINT fk_msg_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_msg_sender FOREIGN KEY (sender_id) REFERENCES employees (emp_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Resolutions Table
CREATE TABLE resolutions (
    resolution_id VARCHAR(32) PRIMARY KEY,
    ticket_id VARCHAR(32) NOT NULL UNIQUE,
    resolved_by_id VARCHAR(32) NOT NULL,
    resolution_type ENUM('POLICY_EXPLANATION', 'MANUAL_CORRECTION', 'ESCALATION_RESOLVED', 'POLICY_EXCEPTION', 'DUPLICATE', 'WITHDRAWN') NOT NULL DEFAULT 'POLICY_EXPLANATION',
    resolution_notes MEDIUMTEXT NOT NULL,
    root_cause VARCHAR(255) NULL,
    policy_version_used_id VARCHAR(32) NULL,
    employee_rating TINYINT NULL,
    employee_feedback TEXT NULL,
    resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_res_ticket (ticket_id),
    INDEX idx_res_actor (resolved_by_id),
    CONSTRAINT fk_res_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_res_actor FOREIGN KEY (resolved_by_id) REFERENCES employees (emp_id) ON DELETE RESTRICT,
    CONSTRAINT fk_res_pver FOREIGN KEY (policy_version_used_id) REFERENCES policy_versions (version_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Audit Logs Table (Immutable Event History)
CREATE TABLE audit_logs (
    audit_id VARCHAR(32) PRIMARY KEY,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(32) NOT NULL,
    action VARCHAR(64) NOT NULL,
    actor_id VARCHAR(32) NULL,
    details_json JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_entity (entity_type, entity_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_created (created_at),
    CONSTRAINT fk_audit_actor FOREIGN KEY (actor_id) REFERENCES employees (emp_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Anomaly Records Table (Labeled Injected & Detected Anomalies)
CREATE TABLE anomaly_records (
    anomaly_id VARCHAR(32) PRIMARY KEY,
    ticket_id VARCHAR(32) NOT NULL,
    anomaly_type ENUM('OBSOLETE_POLICY_CITATION', 'SENSITIVE_GENERAL_QUEUE', 'INCORRECT_SLA_CALCULATION', 'UNSUPPORTED_POLICY_CLAIM') NOT NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'HIGH',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL,
    status ENUM('DETECTED', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE') NOT NULL DEFAULT 'DETECTED',
    ground_truth_label BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_anom_ticket (ticket_id),
    INDEX idx_anom_type (anomaly_type),
    INDEX idx_anom_status (status),
    CONSTRAINT fk_anom_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

