-- ========================================================
-- HR Request Resolution System - Native MySQL Seed Script
-- Can be executed directly in MySQL CLI, Workbench, or phpMyAdmin
-- ========================================================

USE hr_request_resolution;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Departments
INSERT INTO departments (dept_id, name, code, manager_id, location, created_at) VALUES
('DEP-001', 'Human Resources', 'HR', NULL, 'Corporate Tower A', NOW()),
('DEP-002', 'Engineering', 'ENG', NULL, 'Building 4, Tech Campus', NOW()),
('DEP-003', 'Sales & Marketing', 'MKT', NULL, 'Corporate Tower B', NOW()),
('DEP-004', 'Finance & Accounting', 'FIN', NULL, 'Corporate Tower A', NOW()),
('DEP-005', 'Legal & Compliance', 'LGL', NULL, 'Corporate Tower A', NOW()),
('DEP-006', 'Operations & IT', 'OPS', NULL, 'Building 2, Tech Campus', NOW())
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 2. Employees (Password for all accounts: Password123!)
-- Bcrypt hash for 'Password123!': $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW
INSERT INTO employees (emp_id, email, password_hash, full_name, department_id, role, employment_type, hire_date, status, is_active, created_at) VALUES
('EMP-0001', 'admin@company.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'System Administrator', 'DEP-006', 'ADMIN', 'FULL_TIME', '2021-01-10', 'ACTIVE', 1, NOW()),
('EMP-0002', 'emily.manager@company.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Emily Watson', 'DEP-001', 'HR_MANAGER', 'FULL_TIME', '2021-03-15', 'ACTIVE', 1, NOW()),
('EMP-0003', 'sarah.agent@company.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Sarah Jenkins', 'DEP-001', 'HR_AGENT', 'FULL_TIME', '2022-02-01', 'ACTIVE', 1, NOW()),
('EMP-0004', 'rachel.compliance@company.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Rachel Vance', 'DEP-005', 'COMPLIANCE_OFFICER', 'FULL_TIME', '2021-06-10', 'ACTIVE', 1, NOW()),
('EMP-0005', 'john.doe@company.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'John Doe', 'DEP-002', 'EMPLOYEE', 'FULL_TIME', '2022-05-18', 'ACTIVE', 1, NOW()),
('EMP-0006', 'alice.smith@company.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Alice Smith', 'DEP-002', 'EMPLOYEE', 'FULL_TIME', '2022-08-01', 'ACTIVE', 1, NOW()),
('EMP-0007', 'bob.martin@company.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Bob Martin', 'DEP-004', 'EMPLOYEE', 'FULL_TIME', '2023-02-15', 'ACTIVE', 1, NOW())
ON DUPLICATE KEY UPDATE email=VALUES(email);

-- Update Department Managers
UPDATE departments SET manager_id = 'EMP-0002' WHERE dept_id = 'DEP-001';
UPDATE departments SET manager_id = 'EMP-0001' WHERE dept_id = 'DEP-006';
UPDATE departments SET manager_id = 'EMP-0004' WHERE dept_id = 'DEP-005';

-- 3. Categories
INSERT INTO categories (category_id, name, code, description, default_priority, is_sensitive_default, tier, created_at) VALUES
('CAT-001', 'Benefits', 'BEN', 'Health insurance, 401k, HSA/FSA, wellness perks', 'MEDIUM', 0, 'TIER_1', NOW()),
('CAT-002', 'Leave & Time Off', 'LEV', 'PTO, sick leave, maternity/paternity, bereavement', 'MEDIUM', 0, 'TIER_1', NOW()),
('CAT-003', 'Payroll & Compensation', 'PAY', 'Direct deposit, paycheck disputes, bonuses, tax withholding', 'HIGH', 0, 'TIER_2', NOW()),
('CAT-004', 'Onboarding & Offboarding', 'ONB', 'Equipment requisition, new hire paperwork, exit processing', 'MEDIUM', 0, 'TIER_1', NOW()),
('CAT-005', 'Workplace Relations', 'REL', 'Manager conflict, performance plans, team dynamics', 'HIGH', 0, 'TIER_2', NOW()),
('CAT-006', 'Health & Safety', 'SAF', 'Ergonomics, workplace injury, safety hazards', 'HIGH', 0, 'TIER_2', NOW()),
('CAT-007', 'Compliance & Ethics', 'CMP', 'Harassment, discrimination, whistleblowing, code of conduct', 'URGENT', 1, 'TIER_3', NOW())
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 4. Policy Documents
INSERT INTO policy_documents (policy_id, doc_code, title, category_id, department_id, audience, owner_id, created_at) VALUES
('POL-001', 'POL-BEN-01', 'Comprehensive Employee Health & Retirement Benefits', 'CAT-001', 'DEP-001', 'ALL_EMPLOYEES', 'EMP-0002', NOW()),
('POL-002', 'POL-LEV-01', 'Paid Time Off and Leave Administration Policy', 'CAT-002', 'DEP-001', 'ALL_EMPLOYEES', 'EMP-0002', NOW()),
('POL-003', 'POL-PAY-01', 'Payroll Discrepancy, Overtime, and Direct Deposit Policy', 'CAT-003', 'DEP-004', 'ALL_EMPLOYEES', 'EMP-0002', NOW()),
('POL-004', 'POL-CMP-01', 'Anti-Harassment, Discrimination, and Whistleblower Protection', 'CAT-007', 'DEP-005', 'ALL_EMPLOYEES', 'EMP-0004', NOW())
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- 5. Policy Versions
INSERT INTO policy_versions (version_id, policy_id, version_number, status, effective_from, effective_to, summary, content, changelog, approved_by, approved_at, created_at) VALUES
('VER-001-1', 'POL-001', '1.0', 'SUPERSEDED', '2023-01-01', '2024-12-31', 'Legacy initial health benefits summary.', 'Historical policy. Superseded on 2025-01-01.', 'Initial version', 'EMP-0002', NOW(), NOW()),
('VER-001-2', 'POL-001', '2.0', 'ACTIVE', '2025-01-01', NULL, 'Covers medical, dental, vision insurance coverage, 401(k) matching up to 4%, and HSA contributions.', 'All full-time employees are eligible for company-sponsored medical, dental, and vision insurance starting on the first day of the calendar month following their start date. The company matches 100% of the first 3% of 401(k) contributions and 50% of the next 2%, resulting in up to 4% total company match.', 'Annual benefits update', 'EMP-0002', NOW(), NOW()),
('VER-002-2', 'POL-002', '2.0', 'ACTIVE', '2025-01-01', NULL, 'Details annual PTO accruals, sick leave, parental leave (16 weeks paid), and rollover rules (maximum 40 hours).', 'Standard full-time staff accrue 15 days of PTO annually during their first two years, increasing to 20 days starting year three. Up to 40 hours of unused accrued PTO can roll over into the subsequent calendar year.', 'Updated rollover policy', 'EMP-0002', NOW(), NOW()),
('VER-003-2', 'POL-003', '1.2', 'ACTIVE', '2024-06-01', NULL, 'Establishes bi-weekly pay schedules, direct deposit setup, and correction SLAs for payroll errors.', 'Paychecks are deposited bi-weekly on alternating Fridays. Any discrepancies reported in writing to HR within 5 business days will be investigated and corrected on an off-cycle run within 48 business hours if the discrepancy exceeds $100.', 'Direct deposit cutoff rules added', 'EMP-0002', NOW(), NOW()),
('VER-004-2', 'POL-004', '2.0', 'ACTIVE', '2024-01-01', NULL, 'Strict zero-tolerance policy regarding workplace harassment, discriminatory behavior, retaliation, and whistleblower protections.', 'The company maintains zero tolerance for harassment, retaliation, or illegal discrimination based on protected characteristics. All reports are treated as strictly confidential, routed solely to designated compliance officers and investigated promptly.', 'Updated compliance reporting', 'EMP-0004', NOW(), NOW())
ON DUPLICATE KEY UPDATE summary=VALUES(summary);

-- 6. Knowledge Articles (150 articles are generated in generator/generate_data.py; here are baseline core ones)
INSERT INTO knowledge_articles (article_id, policy_version_id, title, section_number, content, keywords, audience, is_published, created_at) VALUES
('ART-0001', 'VER-001-2', 'Health & Dental Eligibility and Enrollment', 'Sec 2.1', 'Full-time employees can enroll within 30 calendar days of joining. Coverage commences on the first of the subsequent month. Dependents including spouse and children under age 26 may be added.', 'health insurance, dental, vision, open enrollment, dependents', 'ALL_EMPLOYEES', 1, NOW()),
('ART-0002', 'VER-001-2', '401(k) Retirement Plan & Corporate Matching', 'Sec 4.2', 'Employees are automatically enrolled at a 4% deferral rate after 60 days of service. The company matches up to 4% total with immediate 100% vesting of matching contributions.', '401k, retirement, matching, vesting, pension', 'ALL_EMPLOYEES', 1, NOW()),
('ART-0003', 'VER-002-2', 'PTO Accrual Schedule and Maximum Rollover', 'Sec 1.3', 'PTO accrues bi-weekly on pay dates. Rollover is capped at 40 hours as of December 31st each year. Any hours exceeding 40 that remain unspent are forfeited unless approved in writing by HR.', 'pto, vacation, rollover, accrual, carryover', 'ALL_EMPLOYEES', 1, NOW()),
('ART-0004', 'VER-002-2', 'Paid Parental Leave Policy', 'Sec 3.0', 'Birth, adoptive, and foster parents are eligible for 16 consecutive weeks of 100% paid parental leave, provided they have completed at least 6 months of continuous full-time employment.', 'parental leave, maternity, paternity, birth, adoption', 'ALL_EMPLOYEES', 1, NOW()),
('ART-0005', 'VER-003-2', 'Reporting and Resolving Paycheck Discrepancies', 'Sec 2.4', 'If you observe a mistake in your gross pay, tax deduction, or reimbursement, submit an HR request specifying the pay period and discrepancy amount. Discrepancies over $100 are rectified via an immediate off-cycle deposit within 48 business hours.', 'payroll, paycheck, deduction, missing pay, off-cycle', 'ALL_EMPLOYEES', 1, NOW()),
('ART-0006', 'VER-004-2', 'Confidential Reporting and Non-Retaliation Guarantee', 'Sec 1.1', 'Employees may report concerns without fear of retaliation. All sensitive harassment and ethics reports are routed exclusively to authorized Compliance and HR Directors. Retaliation against any employee reporting in good faith is grounds for immediate termination.', 'harassment, discrimination, retaliation, whistleblower, ethics, complaint', 'ALL_EMPLOYEES', 1, NOW())
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- 7. Sample Core Tickets
INSERT INTO tickets (ticket_id, tracking_number, employee_id, category_id, title, description, status, priority, is_sensitive, confidential_assigned_to, created_at, updated_at, resolved_at) VALUES
('TCK-00001', 'REQ-2026-0001', 'EMP-0005', 'CAT-001', 'Dental insurance coverage for spouse', 'I got married last week and would like to add my spouse to our dental and vision plan.', 'RESOLVED', 'MEDIUM', 0, NULL, DATE_SUB(NOW(), INTERVAL 2 DAY), NOW(), DATE_SUB(NOW(), INTERVAL 1 DAY)),
('TCK-00002', 'REQ-2026-0002', 'EMP-0006', 'CAT-002', 'Unused PTO carryover question', 'How many hours of unused accrued vacation can I roll over into the next calendar year?', 'RESOLVED', 'MEDIUM', 0, NULL, DATE_SUB(NOW(), INTERVAL 1 DAY), NOW(), NOW()),
('TCK-00003', 'REQ-2026-0003', 'EMP-0007', 'CAT-003', 'Missing overtime compensation on pay stub', 'My paycheck dated March 15 did not include the 12 overtime hours approved by my supervisor.', 'IN_PROGRESS', 'HIGH', 0, NULL, NOW(), NOW(), NULL),
('TCK-00004', 'REQ-2026-0004', 'EMP-0005', 'CAT-007', 'Confidential report of workplace harassment', 'Reporting repeated offensive remarks and hostile comments made by a senior colleague.', 'NEW', 'URGENT', 1, 'EMP-0004', NOW(), NOW(), NULL)
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- 8. Core Assignments
INSERT INTO assignments (assignment_id, ticket_id, assigned_to_id, assigned_by_id, tier, reason, assigned_at, unassigned_at, is_active) VALUES
('ASG-00001', 'TCK-00001', 'EMP-0003', 'EMP-0002', 'TIER_1', 'Automated system triage', DATE_SUB(NOW(), INTERVAL 2 DAY), NULL, 1),
('ASG-00002', 'TCK-00002', 'EMP-0003', 'EMP-0002', 'TIER_1', 'Automated system triage', DATE_SUB(NOW(), INTERVAL 1 DAY), NULL, 1),
('ASG-00003', 'TCK-00003', 'EMP-0003', 'EMP-0002', 'TIER_2', 'Payroll investigation', NOW(), NULL, 1),
('ASG-00004', 'TCK-00004', 'EMP-0004', 'EMP-0002', 'TIER_3', 'Confidential compliance routing', NOW(), NULL, 1)
ON DUPLICATE KEY UPDATE reason=VALUES(reason);

-- 9. Core SLAs
INSERT INTO slas (sla_id, ticket_id, priority, business_hours_limit, response_due_at, resolution_due_at, first_response_at, is_response_breached, is_resolution_breached, calculated_business_hours, created_at) VALUES
('SLA-00001', 'TCK-00001', 'MEDIUM', 24, DATE_ADD(NOW(), INTERVAL 4 HOUR), DATE_ADD(NOW(), INTERVAL 24 HOUR), DATE_SUB(NOW(), INTERVAL 2 DAY), 0, 0, 8.50, DATE_SUB(NOW(), INTERVAL 2 DAY)),
('SLA-00002', 'TCK-00002', 'MEDIUM', 24, DATE_ADD(NOW(), INTERVAL 4 HOUR), DATE_ADD(NOW(), INTERVAL 24 HOUR), DATE_SUB(NOW(), INTERVAL 1 DAY), 0, 0, 4.00, DATE_SUB(NOW(), INTERVAL 1 DAY)),
('SLA-00003', 'TCK-00003', 'HIGH', 8, DATE_ADD(NOW(), INTERVAL 2 HOUR), DATE_ADD(NOW(), INTERVAL 8 HOUR), NULL, 0, 0, 1.20, NOW()),
('SLA-00004', 'TCK-00004', 'URGENT', 4, DATE_ADD(NOW(), INTERVAL 1 HOUR), DATE_ADD(NOW(), INTERVAL 4 HOUR), NULL, 0, 0, 0.50, NOW())
ON DUPLICATE KEY UPDATE priority=VALUES(priority);

-- 10. Core Messages
INSERT INTO messages (message_id, ticket_id, sender_id, message_type, content, citations_json, is_internal, created_at) VALUES
('MSG-000001', 'TCK-00001', 'EMP-0005', 'EMPLOYEE_NOTE', 'I got married last week and would like to add my spouse to our dental and vision plan.', '[]', 0, DATE_SUB(NOW(), INTERVAL 2 DAY)),
('MSG-000002', 'TCK-00001', 'EMP-0003', 'AGENT_REPLY', 'Congratulations! Per policy POL-BEN-01 Sec 2.1, you have 30 days to add dependents after a qualifying life event.', '[]', 0, DATE_SUB(NOW(), INTERVAL 1 DAY)),
('MSG-000003', 'TCK-00002', 'EMP-0006', 'EMPLOYEE_NOTE', 'How many hours of unused accrued vacation can I roll over into the next calendar year?', '[]', 0, DATE_SUB(NOW(), INTERVAL 1 DAY)),
('MSG-000004', 'TCK-00002', 'EMP-0003', 'AGENT_REPLY', 'Under policy POL-LEV-01 Sec 1.3, you can roll over up to 40 hours of unused accrued PTO into the next calendar year.', '[]', 0, NOW()),
('MSG-000005', 'TCK-00004', 'EMP-0005', 'EMPLOYEE_NOTE', 'Reporting repeated offensive remarks and hostile comments made by a senior colleague.', '[]', 0, NOW())
ON DUPLICATE KEY UPDATE content=VALUES(content);

-- 11. Core Resolutions
INSERT INTO resolutions (resolution_id, ticket_id, resolved_by_id, resolution_type, resolution_notes, root_cause, policy_version_used_id, employee_rating, employee_feedback, resolved_at) VALUES
('RES-00001', 'TCK-00001', 'EMP-0003', 'POLICY_EXPLANATION', 'Provided qualifying life event enrollment form and verified dependent documentation requirements.', 'Marriage qualifying life event enrollment', 'VER-001-2', 5, 'Very helpful and quick response!', DATE_SUB(NOW(), INTERVAL 1 DAY)),
('RES-00002', 'TCK-00002', 'EMP-0003', 'POLICY_EXPLANATION', 'Explained 40-hour maximum carryover cap per POL-LEV-01 Section 1.3.', 'PTO policy clarification', 'VER-002-2', 5, 'Clear policy explanation, thank you.', NOW())
ON DUPLICATE KEY UPDATE resolution_notes=VALUES(resolution_notes);

SET FOREIGN_KEY_CHECKS = 1;

