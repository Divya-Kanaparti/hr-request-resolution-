-- ============================================================
-- HR Request Resolution System
-- MySQL schema + demo data (single file)
-- Separate database: hr_request_resolution_demo
-- Compatible with the supplied SQLAlchemy models.
--
-- DEMO LOGIN PASSWORD FOR ALL ACCOUNTS: Password123!
-- This file stores the synthetic demo password as plain text.
-- The supplied security.py explicitly supports this fallback
-- for synthetic seeds. Replace with bcrypt hashes for production.
--
-- WARNING: This script DROPS and recreates the 13 application
-- tables below. Run only when you are happy to reset their data.
-- ============================================================

CREATE DATABASE IF NOT EXISTS hr_request_resolution_demo
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hr_request_resolution_demo;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS anomaly_records;
DROP TABLE IF EXISTS audit_events; -- remove legacy table from the older schema
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

-- 1. Departments
CREATE TABLE departments (
    dept_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE,
    code VARCHAR(32) NOT NULL UNIQUE,
    manager_id VARCHAR(32) NULL,
    location VARCHAR(120) NOT NULL DEFAULT 'Headquarters',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dept_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Employees
CREATE TABLE employees (
    emp_id VARCHAR(32) PRIMARY KEY,
    email VARCHAR(160) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    department_id VARCHAR(32) NOT NULL,
    role ENUM('EMPLOYEE','HR_AGENT','HR_MANAGER','ADMIN','COMPLIANCE_OFFICER') NOT NULL DEFAULT 'EMPLOYEE',
    employment_type ENUM('FULL_TIME','PART_TIME','CONTRACT','INTERN') NOT NULL DEFAULT 'FULL_TIME',
    hire_date DATE NOT NULL,
    status ENUM('ACTIVE','ON_LEAVE','SUSPENDED','TERMINATED') NOT NULL DEFAULT 'ACTIVE',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_emp_email (email),
    INDEX idx_emp_role (role),
    INDEX idx_emp_dept (department_id),
    CONSTRAINT fk_emp_dept FOREIGN KEY (department_id) REFERENCES departments(dept_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE departments
  ADD CONSTRAINT fk_dept_manager FOREIGN KEY (manager_id)
  REFERENCES employees(emp_id) ON DELETE SET NULL;

-- 3. Categories
CREATE TABLE categories (
    category_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(32) NOT NULL UNIQUE,
    description TEXT NULL,
    default_priority ENUM('LOW','MEDIUM','HIGH','URGENT') NOT NULL DEFAULT 'MEDIUM',
    is_sensitive_default BOOLEAN NOT NULL DEFAULT FALSE,
    tier ENUM('TIER_1','TIER_2','TIER_3') NOT NULL DEFAULT 'TIER_1',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cat_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Policy documents
CREATE TABLE policy_documents (
    policy_id VARCHAR(32) PRIMARY KEY,
    doc_code VARCHAR(40) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    category_id VARCHAR(32) NOT NULL,
    department_id VARCHAR(32) NOT NULL,
    audience ENUM('ALL_EMPLOYEES','MANAGERS_ONLY','FULL_TIME_ONLY','CONTRACTORS','HR_ONLY') NOT NULL DEFAULT 'ALL_EMPLOYEES',
    owner_id VARCHAR(32) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_policy_code (doc_code),
    INDEX idx_policy_cat (category_id),
    CONSTRAINT fk_pol_cat FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_pol_dept FOREIGN KEY (department_id) REFERENCES departments(dept_id) ON DELETE RESTRICT,
    CONSTRAINT fk_pol_owner FOREIGN KEY (owner_id) REFERENCES employees(emp_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Policy versions
CREATE TABLE policy_versions (
    version_id VARCHAR(32) PRIMARY KEY,
    policy_id VARCHAR(32) NOT NULL,
    version_number VARCHAR(16) NOT NULL,
    status ENUM('DRAFT','ACTIVE','ARCHIVED','SUPERSEDED') NOT NULL DEFAULT 'DRAFT',
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,
    changelog TEXT NULL,
    approved_by VARCHAR(32) NULL,
    approved_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_policy_version (policy_id,version_number),
    INDEX idx_pver_status (status),
    INDEX idx_pver_effective (effective_from,effective_to),
    CONSTRAINT fk_pver_policy FOREIGN KEY (policy_id) REFERENCES policy_documents(policy_id) ON DELETE CASCADE,
    CONSTRAINT fk_pver_approver FOREIGN KEY (approved_by) REFERENCES employees(emp_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Knowledge articles
CREATE TABLE knowledge_articles (
    article_id VARCHAR(32) PRIMARY KEY,
    policy_version_id VARCHAR(32) NOT NULL,
    title VARCHAR(220) NOT NULL,
    section_number VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    keywords VARCHAR(500) NULL,
    audience ENUM('ALL_EMPLOYEES','MANAGERS_ONLY','FULL_TIME_ONLY','CONTRACTORS','HR_ONLY') NOT NULL DEFAULT 'ALL_EMPLOYEES',
    is_published BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_kart_pver (policy_version_id),
    INDEX idx_kart_section (section_number),
    CONSTRAINT fk_kart_pver FOREIGN KEY (policy_version_id) REFERENCES policy_versions(version_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Tickets
CREATE TABLE tickets (
    ticket_id VARCHAR(32) PRIMARY KEY,
    tracking_number VARCHAR(48) NOT NULL UNIQUE,
    employee_id VARCHAR(32) NOT NULL,
    category_id VARCHAR(32) NOT NULL,
    title VARCHAR(220) NOT NULL,
    description TEXT NOT NULL,
    status ENUM('NEW','CLARIFICATION_NEEDED','IN_PROGRESS','ESCALATED','RESOLVED','CLOSED') NOT NULL DEFAULT 'NEW',
    priority ENUM('LOW','MEDIUM','HIGH','URGENT') NOT NULL DEFAULT 'MEDIUM',
    is_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
    confidential_assigned_to VARCHAR(32) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL,
    INDEX idx_tck_tracking (tracking_number),
    INDEX idx_tck_emp (employee_id),
    INDEX idx_tck_cat (category_id),
    INDEX idx_tck_status (status),
    INDEX idx_tck_priority (priority),
    INDEX idx_tck_sensitive (is_sensitive),
    CONSTRAINT fk_tck_emp FOREIGN KEY (employee_id) REFERENCES employees(emp_id) ON DELETE RESTRICT,
    CONSTRAINT fk_tck_cat FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_tck_confidential FOREIGN KEY (confidential_assigned_to) REFERENCES employees(emp_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Assignments
CREATE TABLE assignments (
    assignment_id VARCHAR(32) PRIMARY KEY,
    ticket_id VARCHAR(32) NOT NULL,
    assigned_to_id VARCHAR(32) NOT NULL,
    assigned_by_id VARCHAR(32) NOT NULL,
    tier ENUM('TIER_1','TIER_2','TIER_3') NOT NULL DEFAULT 'TIER_1',
    reason VARCHAR(255) NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    unassigned_at DATETIME NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_asg_ticket (ticket_id),
    INDEX idx_asg_agent (assigned_to_id),
    INDEX idx_asg_active (is_active),
    CONSTRAINT fk_asg_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_asg_target FOREIGN KEY (assigned_to_id) REFERENCES employees(emp_id) ON DELETE RESTRICT,
    CONSTRAINT fk_asg_actor FOREIGN KEY (assigned_by_id) REFERENCES employees(emp_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. SLAs
CREATE TABLE slas (
    sla_id VARCHAR(32) PRIMARY KEY,
    ticket_id VARCHAR(32) NOT NULL UNIQUE,
    priority ENUM('LOW','MEDIUM','HIGH','URGENT') NOT NULL DEFAULT 'MEDIUM',
    business_hours_limit INT NOT NULL DEFAULT 24,
    response_due_at DATETIME NOT NULL,
    resolution_due_at DATETIME NOT NULL,
    first_response_at DATETIME NULL,
    is_response_breached BOOLEAN NOT NULL DEFAULT FALSE,
    is_resolution_breached BOOLEAN NOT NULL DEFAULT FALSE,
    calculated_business_hours DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sla_due (resolution_due_at),
    INDEX idx_sla_breached (is_resolution_breached),
    CONSTRAINT fk_sla_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Messages
CREATE TABLE messages (
    message_id VARCHAR(32) PRIMARY KEY,
    ticket_id VARCHAR(32) NOT NULL,
    sender_id VARCHAR(32) NOT NULL,
    message_type ENUM('EMPLOYEE_NOTE','AGENT_REPLY','INTERNAL_NOTE','SYSTEM_EVENT','CLARIFICATION_PROMPT') NOT NULL,
    content TEXT NOT NULL,
    citations_json JSON NULL,
    is_internal BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_msg_ticket (ticket_id),
    INDEX idx_msg_sender (sender_id),
    INDEX idx_msg_type (message_type),
    CONSTRAINT fk_msg_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_msg_sender FOREIGN KEY (sender_id) REFERENCES employees(emp_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Resolutions
CREATE TABLE resolutions (
    resolution_id VARCHAR(32) PRIMARY KEY,
    ticket_id VARCHAR(32) NOT NULL UNIQUE,
    resolved_by_id VARCHAR(32) NOT NULL,
    resolution_type ENUM('POLICY_EXPLANATION','MANUAL_CORRECTION','ESCALATION_RESOLVED','POLICY_EXCEPTION','DUPLICATE','WITHDRAWN') NOT NULL DEFAULT 'POLICY_EXPLANATION',
    resolution_notes TEXT NOT NULL,
    root_cause VARCHAR(255) NULL,
    policy_version_used_id VARCHAR(32) NULL,
    employee_rating INT NULL,
    employee_feedback TEXT NULL,
    resolved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_res_ticket (ticket_id),
    INDEX idx_res_actor (resolved_by_id),
    CONSTRAINT fk_res_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    CONSTRAINT fk_res_actor FOREIGN KEY (resolved_by_id) REFERENCES employees(emp_id) ON DELETE RESTRICT,
    CONSTRAINT fk_res_pver FOREIGN KEY (policy_version_used_id) REFERENCES policy_versions(version_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Audit logs
CREATE TABLE audit_logs (
    audit_id VARCHAR(32) PRIMARY KEY,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(32) NOT NULL,
    action VARCHAR(64) NOT NULL,
    actor_id VARCHAR(32) NULL,
    details_json JSON NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_entity (entity_type,entity_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_created (created_at),
    CONSTRAINT fk_audit_actor FOREIGN KEY (actor_id) REFERENCES employees(emp_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Anomaly records
CREATE TABLE anomaly_records (
    anomaly_id VARCHAR(32) PRIMARY KEY,
    ticket_id VARCHAR(32) NOT NULL,
    anomaly_type ENUM('OBSOLETE_POLICY_CITATION','SENSITIVE_GENERAL_QUEUE','INCORRECT_SLA_CALCULATION','UNSUPPORTED_POLICY_CLAIM') NOT NULL,
    severity ENUM('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL DEFAULT 'HIGH',
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL,
    status ENUM('DETECTED','INVESTIGATING','RESOLVED','FALSE_POSITIVE') NOT NULL DEFAULT 'DETECTED',
    ground_truth_label BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX idx_anom_ticket (ticket_id),
    INDEX idx_anom_type (anomaly_type),
    INDEX idx_anom_status (status),
    CONSTRAINT fk_anom_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- DEMO DATA
-- All demo accounts use Password123! (synthetic plain-text seed;
-- security.py's documented fallback accepts this for demo seeds).
-- ============================================================

-- Departments first; manager_id is updated after employee inserts.
INSERT INTO departments (dept_id,name,code,manager_id,location) VALUES
('DEPT-HR','Human Resources','HR',NULL,'Hyderabad'),
('DEPT-IT','Information Technology','IT',NULL,'Hyderabad'),
('DEPT-FIN','Finance','FIN',NULL,'Hyderabad'),
('DEPT-OPS','Operations','OPS',NULL,'Hyderabad');

-- Employees: one account for each application role.
INSERT INTO employees
(emp_id,email,password_hash,full_name,department_id,role,employment_type,hire_date,status,is_active)
VALUES
('EMP-1001','john.doe@company.com','Password123!','John Doe','DEPT-IT','EMPLOYEE','FULL_TIME','2024-06-10','ACTIVE',TRUE),
('EMP-1002','sarah.agent@company.com','Password123!','Sarah Agent','DEPT-HR','HR_AGENT','FULL_TIME','2023-03-15','ACTIVE',TRUE),
('EMP-1003','emily.manager@company.com','Password123!','Emily Manager','DEPT-HR','HR_MANAGER','FULL_TIME','2022-01-10','ACTIVE',TRUE),
('EMP-1004','rachel.compliance@company.com','Password123!','Rachel Compliance','DEPT-HR','COMPLIANCE_OFFICER','FULL_TIME','2021-09-01','ACTIVE',TRUE),
('EMP-1005','admin@company.com','Password123!','System Administrator','DEPT-IT','ADMIN','FULL_TIME','2021-01-01','ACTIVE',TRUE);

UPDATE departments SET manager_id='EMP-1003' WHERE dept_id='DEPT-HR';
UPDATE departments SET manager_id='EMP-1005' WHERE dept_id='DEPT-IT';

-- Categories
INSERT INTO categories
(category_id,name,code,description,default_priority,is_sensitive_default,tier)
VALUES
('CAT-LEAVE','Leave and Attendance','LEAVE','Leave balances, leave requests and attendance corrections.','MEDIUM',FALSE,'TIER_1'),
('CAT-PAY','Payroll and Compensation','PAYROLL','Salary, payslip, deductions and compensation queries.','HIGH',FALSE,'TIER_2'),
('CAT-BEN','Benefits and Insurance','BENEFITS','Employee benefits, insurance and reimbursements.','MEDIUM',FALSE,'TIER_1'),
('CAT-ER','Employee Relations','EMP-REL','Confidential employee relations and grievance matters.','URGENT',TRUE,'TIER_3');

-- Policy documents
INSERT INTO policy_documents
(policy_id,doc_code,title,category_id,department_id,audience,owner_id)
VALUES
('POL-LEAVE','HR-POL-001','Leave and Attendance Policy','CAT-LEAVE','DEPT-HR','ALL_EMPLOYEES','EMP-1003'),
('POL-PAY','HR-POL-002','Payroll and Payslip Policy','CAT-PAY','DEPT-HR','ALL_EMPLOYEES','EMP-1003'),
('POL-BEN','HR-POL-003','Employee Benefits Policy','CAT-BEN','DEPT-HR','ALL_EMPLOYEES','EMP-1003'),
('POL-ER','HR-POL-004','Employee Relations and Confidentiality Policy','CAT-ER','DEPT-HR','HR_ONLY','EMP-1004');

-- Versioned policies
INSERT INTO policy_versions
(version_id,policy_id,version_number,status,effective_from,effective_to,summary,content,changelog,approved_by,approved_at)
VALUES
('PVER-LEAVE-1','POL-LEAVE','1.0','ACTIVE','2025-01-01',NULL,
 'Explains leave request submission, approval and balance queries.',
 'Employees should submit planned leave through the HR portal. Managers review requests based on team coverage. Leave balances are maintained by HR and should be checked in the employee portal.',
 'Initial published version.','EMP-1003',NOW()),
('PVER-PAY-1','POL-PAY','1.0','ACTIVE','2025-01-01',NULL,
 'Explains payslip access and payroll query handling.',
 'Payslips are available through the employee payroll portal. Employees should raise a payroll ticket with the relevant pay period and a description of the discrepancy. HR and Payroll will review supporting records.',
 'Initial published version.','EMP-1003',NOW()),
('PVER-BEN-1','POL-BEN','1.0','ACTIVE','2025-01-01',NULL,
 'Explains benefits and insurance support.',
 'Employees can review current benefits in the benefits portal. Reimbursement requests must include the required receipts and supporting documents. HR Benefits will review eligibility under the applicable plan.',
 'Initial published version.','EMP-1003',NOW()),
('PVER-ER-1','POL-ER','1.0','ACTIVE','2025-01-01',NULL,
 'Defines confidential handling of employee relations cases.',
 'Employee relations matters must be handled only by authorized HR or Compliance personnel. Do not disclose case details in general queues or to unauthorized employees. Escalate sensitive allegations to the designated confidential handler.',
 'Initial published version.','EMP-1004',NOW());

-- Knowledge articles
INSERT INTO knowledge_articles
(article_id,policy_version_id,title,section_number,content,keywords,audience,is_published)
VALUES
('ART-LEAVE-1','PVER-LEAVE-1','How to request leave','1.1','Submit planned leave through the HR portal and monitor the manager approval status.','leave,request,approval','ALL_EMPLOYEES',TRUE),
('ART-PAY-1','PVER-PAY-1','How to report a payslip issue','2.1','Open a payroll ticket and include the affected pay period and a clear description. Do not include passwords.','payroll,payslip,salary','ALL_EMPLOYEES',TRUE),
('ART-BEN-1','PVER-BEN-1','Benefits and reimbursement checklist','3.1','Review plan eligibility and attach receipts or other required supporting documents.','benefits,insurance,reimbursement','ALL_EMPLOYEES',TRUE),
('ART-ER-1','PVER-ER-1','Confidential employee relations handling','4.1','Restrict case details to authorized HR and Compliance users and use confidential assignment.','confidential,grievance,employee relations','HR_ONLY',TRUE);

-- Tickets
INSERT INTO tickets
(ticket_id,tracking_number,employee_id,category_id,title,description,status,priority,is_sensitive,confidential_assigned_to,resolved_at)
VALUES
('TCK-1001','HR-2026-1001','EMP-1001','CAT-LEAVE','Leave balance clarification','Please clarify my current annual leave balance.','NEW','MEDIUM',FALSE,NULL,NULL),
('TCK-1002','HR-2026-1002','EMP-1001','CAT-PAY','Payslip deduction query','There is an unexpected deduction on my latest payslip. Please review.','IN_PROGRESS','HIGH',FALSE,NULL,NULL),
('TCK-1003','HR-2026-1003','EMP-1001','CAT-BEN','Medical reimbursement status','Please provide an update on my submitted reimbursement.','RESOLVED','MEDIUM',FALSE,NULL,NOW()),
('TCK-1004','HR-2026-1004','EMP-1001','CAT-ER','Confidential workplace concern','I need to report a sensitive workplace concern for confidential review.','ESCALATED','URGENT',TRUE,'EMP-1004',NULL),
('TCK-1005','HR-2026-1005','EMP-1001','CAT-LEAVE','Leave request process','How do I submit a planned leave request?','CLOSED','LOW',FALSE,NULL,NOW());

-- Assignments
INSERT INTO assignments
(assignment_id,ticket_id,assigned_to_id,assigned_by_id,tier,reason,is_active)
VALUES
('ASN-1001','TCK-1002','EMP-1002','EMP-1003','TIER_2','Payroll-related review',TRUE),
('ASN-1002','TCK-1003','EMP-1002','EMP-1003','TIER_1','Benefits support',FALSE),
('ASN-1003','TCK-1004','EMP-1004','EMP-1003','TIER_3','Sensitive case routed to Compliance',TRUE),
('ASN-1004','TCK-1005','EMP-1002','EMP-1003','TIER_1','Routine leave policy question',FALSE);

-- SLAs: timestamps are relative to execution time for usable demo records.
INSERT INTO slas
(sla_id,ticket_id,priority,business_hours_limit,response_due_at,resolution_due_at,first_response_at,is_response_breached,is_resolution_breached,calculated_business_hours)
VALUES
('SLA-1001','TCK-1001','MEDIUM',24,DATE_ADD(NOW(),INTERVAL 4 HOUR),DATE_ADD(NOW(),INTERVAL 24 HOUR),NULL,FALSE,FALSE,0.00),
('SLA-1002','TCK-1002','HIGH',12,DATE_ADD(NOW(),INTERVAL 2 HOUR),DATE_ADD(NOW(),INTERVAL 12 HOUR),NOW(),FALSE,FALSE,1.00),
('SLA-1003','TCK-1003','MEDIUM',24,DATE_SUB(NOW(),INTERVAL 2 DAY),DATE_SUB(NOW(),INTERVAL 1 DAY),DATE_SUB(NOW(),INTERVAL 3 DAY),TRUE,FALSE,18.00),
('SLA-1004','TCK-1004','URGENT',4,DATE_ADD(NOW(),INTERVAL 1 HOUR),DATE_ADD(NOW(),INTERVAL 4 HOUR),NULL,FALSE,FALSE,0.00),
('SLA-1005','TCK-1005','LOW',48,DATE_SUB(NOW(),INTERVAL 4 DAY),DATE_SUB(NOW(),INTERVAL 2 DAY),DATE_SUB(NOW(),INTERVAL 4 DAY),FALSE,FALSE,8.00);

-- Messages
INSERT INTO messages
(message_id,ticket_id,sender_id,message_type,content,citations_json,is_internal)
VALUES
('MSG-1001','TCK-1001','EMP-1001','EMPLOYEE_NOTE','Please confirm my available annual leave balance.',NULL,FALSE),
('MSG-1002','TCK-1002','EMP-1002','AGENT_REPLY','We are reviewing the deduction against the payroll record.',NULL,FALSE),
('MSG-1003','TCK-1003','EMP-1002','AGENT_REPLY','Your reimbursement query has been reviewed under the benefits policy.','[{"policy":"HR-POL-003","version":"1.0"}]',FALSE),
('MSG-1004','TCK-1004','EMP-1004','INTERNAL_NOTE','Confidential case received. Access restricted to Compliance.',NULL,TRUE),
('MSG-1005','TCK-1005','EMP-1002','AGENT_REPLY','Submit planned leave through the HR portal and monitor manager approval.','[{"policy":"HR-POL-001","version":"1.0"}]',FALSE);

-- Resolutions
INSERT INTO resolutions
(resolution_id,ticket_id,resolved_by_id,resolution_type,resolution_notes,root_cause,policy_version_used_id,employee_rating,employee_feedback)
VALUES
('RES-1001','TCK-1003','EMP-1002','POLICY_EXPLANATION','Provided the employee with the benefits review process and required documentation checklist.','Benefits status clarification','PVER-BEN-1',5,'Clear explanation provided.'),
('RES-1002','TCK-1005','EMP-1002','POLICY_EXPLANATION','Explained the leave submission and manager approval process.','Routine policy question','PVER-LEAVE-1',5,'Helpful response.');

-- Audit events
INSERT INTO audit_logs
(audit_id,entity_type,entity_id,action,actor_id,details_json)
VALUES
('AUD-1001','EMPLOYEE','EMP-1001','DEMO_ACCOUNT_CREATED','EMP-1005','{"source":"demo_seed"}'),
('AUD-1002','TICKET','TCK-1002','TICKET_ASSIGNED','EMP-1003','{"assigned_to":"EMP-1002","tier":"TIER_2"}'),
('AUD-1003','TICKET','TCK-1003','TICKET_RESOLVED','EMP-1002','{"resolution_id":"RES-1001"}'),
('AUD-1004','TICKET','TCK-1004','SENSITIVE_CASE_ROUTED','EMP-1003','{"assigned_to":"EMP-1004","confidential":true}'),
('AUD-1005','POLICY','POL-LEAVE','POLICY_VERSION_APPROVED','EMP-1003','{"version":"1.0"}');

-- Labeled anomaly examples for the anomaly dashboard.
INSERT INTO anomaly_records
(anomaly_id,ticket_id,anomaly_type,severity,description,status,ground_truth_label)
VALUES
('ANOM-1001','TCK-1003','OBSOLETE_POLICY_CITATION','MEDIUM','Synthetic demo anomaly: a sample response references an older policy version.','DETECTED',TRUE),
('ANOM-1002','TCK-1004','SENSITIVE_GENERAL_QUEUE','CRITICAL','Synthetic demo anomaly: sensitive case routing must remain restricted.','INVESTIGATING',TRUE),
('ANOM-1003','TCK-1002','INCORRECT_SLA_CALCULATION','HIGH','Synthetic demo anomaly: review the sample SLA calculation against business hours.','DETECTED',TRUE),
('ANOM-1004','TCK-1001','UNSUPPORTED_POLICY_CLAIM','MEDIUM','Synthetic demo anomaly: validate policy support before issuing a definitive claim.','DETECTED',TRUE);

-- ============================================================
-- VERIFICATION
-- ============================================================
SELECT 'departments' AS table_name, COUNT(*) AS row_count FROM departments
UNION ALL SELECT 'employees', COUNT(*) FROM employees
UNION ALL SELECT 'categories', COUNT(*) FROM categories
UNION ALL SELECT 'policy_documents', COUNT(*) FROM policy_documents
UNION ALL SELECT 'policy_versions', COUNT(*) FROM policy_versions
UNION ALL SELECT 'knowledge_articles', COUNT(*) FROM knowledge_articles
UNION ALL SELECT 'tickets', COUNT(*) FROM tickets
UNION ALL SELECT 'assignments', COUNT(*) FROM assignments
UNION ALL SELECT 'slas', COUNT(*) FROM slas
UNION ALL SELECT 'messages', COUNT(*) FROM messages
UNION ALL SELECT 'resolutions', COUNT(*) FROM resolutions
UNION ALL SELECT 'audit_logs', COUNT(*) FROM audit_logs
UNION ALL SELECT 'anomaly_records', COUNT(*) FROM anomaly_records;

SELECT emp_id,email,role,is_active FROM employees ORDER BY emp_id;
