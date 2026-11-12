# Enterprise HR Request Resolution System

A production-grade, full-stack Human Resources Request Resolution and Policy Intelligence platform engineered with **FastAPI**, **SQLAlchemy**, **MySQL**, **Vanilla JavaScript**, **Role-Based Access Control (RBAC)**, **Deterministic Business-Hours SLA Monitoring**, and **RAG-powered Policy Question Answering with Exact Citations**.

---

## 1. Project Overview

Modern corporate HR departments face severe friction with ambiguous requests, missed SLA deadlines due to inaccurate business-hours calculations, confidential routing leaks, and outdated policy guidance. 

This system resolves those operational challenges by providing:
1. **Automated Request Triage & AI Classification**: Automatically categorizes inquiries (Benefits, Leave, Payroll, Onboarding, Relations, Compliance) and detects sensitivity or ambiguity.
2. **Deterministic Business-Hours SLA Engine**: Accurately tracks response and resolution deadlines strictly within corporate working hours (09:00 - 17:00, Mon-Fri, excluding holidays).
3. **Policy-Backed RAG with Verbatim Citations**: Answers employee inquiries strictly using verified active corporate policy versions, citing the document code, version number, section, and exact quote.
4. **Confidential Case Routing**: Protects sensitive cases (harassment, whistleblowing, medical disclosures, grievances) by routing exclusively to designated HR directors and compliance officers.
5. **Continuous Anomaly Detection Radar**: Scans for obsolete policy citations, exposed sensitive cases, SLA calculation discrepancies, and unsupported policy claims.

---

## 2. Technology Stack

| Layer | Technologies Selected |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Backend** | Python 3.10+, FastAPI, SQLAlchemy 2.0 ORM, Pydantic v2 |
| **Database** | MySQL 8.0+ (InnoDB engine, utf8mb4 collation) |
| **AI & RAG** | Gemini 1.5 Flash API (Configurable) + Sentence-Transformers + Deterministic Semantic Search |
| **Data Generation** | Python, Pandas, NumPy, Faker, Standard CSV/JSON (Deterministic seed `20261022`) |
| **Authentication** | JWT (JSON Web Tokens), PBKDF2/Bcrypt hashing, Role-Based Access Control (RBAC) |
| **Documentation & Testing** | Interactive Swagger UI (`/docs`), Pytest |

---

## 3. Project Directory Structure

```
hr-request-resolution/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI entrypoint, CORS, static file mounting
│   │   ├── core/
│   │   │   ├── config.py              # Environment configuration & pydantic settings
│   │   │   ├── security.py            # Bcrypt hashing & JWT token issuance/decoding
│   │   │   ├── rbac.py                # Role checking & sensitive ticket privacy
│   │   │   └── business_hours.py      # Deterministic 09:00 - 17:00 Mon-Fri SLA engine
│   │   ├── database/
│   │   │   ├── base.py                # Declarative Base
│   │   │   └── session.py             # SQLAlchemy engine & session factory
│   │   ├── models/                    # All 11 entities + Audit & Anomaly models
│   │   │   ├── employee.py
│   │   │   ├── department.py
│   │   │   ├── category.py
│   │   │   ├── policy.py              # PolicyDocument, PolicyVersion, KnowledgeArticle
│   │   │   ├── ticket.py
│   │   │   ├── assignment.py
│   │   │   ├── sla.py
│   │   │   ├── message.py
│   │   │   ├── resolution.py
│   │   │   ├── audit.py               # Immutable audit log
│   │   │   └── anomaly.py             # Anomaly tracking model
│   │   ├── schemas/                   # Pydantic request & response models
│   │   ├── services/                  # Business logic (RAG, SLA, Triage, Anomaly Radar)
│   │   └── routes/                    # Modular API routers for all resources
│   ├── tests/                         # Pytest test suite (Auth, SLA, Tickets, RAG, etc.)
│   └── requirements.txt
├── database/
│   ├── schema.sql                     # Complete MySQL schema DDL
│   ├── init_db.py                     # Schema initialization script
│   └── seed.py                        # Base master data & demo users seed script
├── generator/
│   ├── generate_data.py               # Synthetic generator (starter & full profiles)
│   ├── validation.py                  # Foreign key, checksum, and duplicate checks
│   └── ground_truth.py                # Ground truth exporter & summary utility
├── data/
│   ├── starter/                       # Quick testing dataset (250 tickets, 150 articles)
│   ├── full/                          # Production synthetic dataset (5,000 tickets, 20,000 messages)
│   └── ground_truth/                  # ground_truth.csv and ground_truth.json
├── frontend/
│   ├── index.html                     # Public portal landing page
│   ├── login.html                     # 1-Click Demo Sign In and registration
│   ├── dashboard.html                 # Main role-aware KPI & SLA dashboard
│   ├── tickets.html                   # Ticket workflow, AI precheck, detail, chat, modals
│   ├── policies.html                  # Versioned policy explorer & AI Assistant (RAG)
│   ├── analytics.html                 # KPIs, Category trends, Agent workload & Anomaly Radar
│   ├── css/style.css                  # Enterprise corporate stylesheet
│   └── js/
│       ├── api.js                     # Centralized API fetcher & toast notifications
│       ├── auth.js                    # Auth token handling & role UI visibility
│       ├── dashboard.js               # KPI calculations & recent tickets table
│       ├── tickets.js                 # Ticket submission, triage, messaging & resolution
│       ├── policies.js                # Policy explorer & RAG citations chat
│       └── analytics.js               # SLA charts, agent workload & anomaly resolution
├── docs/
│   ├── architecture.md                # System design, SLA formula, RAG sequence
│   ├── data_dictionary.md             # Complete database schema reference
│   ├── api_documentation.md           # Endpoints, schemas, and samples
│   └── validation_report.md           # Synthetic data metrics, SHA256 checksums
├── .env.example                       # Template configuration
├── requirements.txt
└── README.md
```

---

## 4. Setup and Execution Instructions (Windows PowerShell)

Follow these exact steps in **Windows PowerShell** to configure and run the application locally.

### Step 1: Open PowerShell and Navigate to Project Directory
```powershell
cd hr-request-resolution
```

### Step 2: Create and Activate Python Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

### Step 3: Install Required Python Packages
```powershell
pip install -r requirements.txt
```

---

### Step 4: Configure MySQL Database

1. Ensure MySQL Server is running locally.
2. Open your MySQL client or PowerShell and create the database:
```sql
CREATE DATABASE IF NOT EXISTS hr_request_resolution
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

3. Create your `.env` configuration file from `.env.example`:
```powershell
Copy-Item .env.example .env
```

4. Edit `.env` with your MySQL credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YourMySQLPasswordHere
DB_NAME=hr_request_resolution
DATABASE_URL=mysql+pymysql://root:YourMySQLPasswordHere@localhost:3306/hr_request_resolution
```
*(Optional: If you have a Gemini API key, add `GEMINI_API_KEY=your_key_here`. If left blank, the system automatically uses its built-in deterministic RAG semantic engine!)*

---

### Step 5: Initialize Schema and Seed Base Data

Initialize the MySQL database tables:
```powershell
# Option A: Run automated initializer
python database/init_db.py

# Option B: Or execute schema.sql directly via MySQL CLI
Get-Content database/schema.sql | mysql -u root -p hr_request_resolution
```

Seed the default corporate departments, categories, policies, and demo accounts:
```powershell
python database/seed.py
```

---

### Step 6: Generate Synthetic Data & Ground Truth

Generate synthetic records using fixed seed `20261022`:

```powershell
# Generate Starter Profile (250 tickets, 1,000 messages, 150 policy articles)
python generator/generate_data.py --profile starter

# Generate Full Enterprise Profile (5,000 tickets, 20,000 messages, 150 policy articles)
python generator/generate_data.py --profile full

# Run synthetic data integrity validation
python generator/validation.py starter
python generator/validation.py full

# Inspect Ground Truth Summary
python generator/ground_truth.py
```

---

### Step 7: Run Backend API Server

Start the FastAPI application on port 8000:
```powershell
uvicorn app.main:app --reload --port 8000 --app-dir backend
```
The backend is now live at:
- **API Base**: `http://localhost:8000/api/v1`
- **Interactive Swagger UI**: `http://localhost:8000/docs`

---

### Step 8: Access the Frontend Web Application

The frontend and backend can be started independently.

**Option 1: Run the Frontend Separately (Recommended)**

Open a new terminal in the project root and run:

```powershell
python -m http.server 3000 --directory frontend
```

Open your browser and visit:

`http://localhost:3000/`

**Option 2: Access Through the Backend**

If the backend is configured to serve the frontend, visit:

`http://localhost:8000/`

**Important:** Start the backend separately in another terminal:

```powershell
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

The frontend communicates with the backend API running on port `8000`.


## 5. Demo Login Credentials

The system provides 1-click quick-fill buttons on `login.html`:

| Role | Email | Password | Primary Capabilities |
| :--- | :--- | :--- | :--- |
| **Standard Employee** | `john.doe@company.com` | `Password123!` | Submit requests, AI classification preview, view own tickets, rate service, ask policy RAG |
| **HR Agent** | `sarah.agent@company.com` | `Password123!` | General triage queue, respond to tickets, post internal notes, resolve requests with citations |
| **HR Manager** | `emily.manager@company.com` | `Password123!` | All agent actions, confidential/sensitive cases, escalation handling, author policy versions |
| **Compliance Officer** | `rachel.compliance@company.com` | `Password123!` | Confidential harassment/ethics cases, run Anomaly Radar scan, resolve anomalies, audit logs |
| **System Admin** | `admin@company.com` | `Password123!` | Full unrestricted administrative access across all modules |

---

## 6. Testing via Swagger UI (`/docs`)

1. Open `http://localhost:8000/docs` in your browser.
2. Click the green **Authorize** button at the top right.
3. In the OAuth2 form, enter:
   - **username**: `sarah.agent@company.com`
   - **password**: `Password123!`
4. Click **Authorize** then **Close**.
5. Test key endpoints:
   - `GET /api/v1/tickets`: Returns tickets.
   - `POST /api/v1/rag/ask`: Submit query `{"query": "How many hours of PTO can roll over?"}` and view verbatim citations.
   - `POST /api/v1/anomalies/scan`: Triggers live detection of injected anomalies.
   - `GET /api/v1/analytics/summary`: Returns top-level KPI metrics.

---

## 7. Running Automated Test Suite (Pytest)

Run the full automated pytest suite:
```powershell
pytest backend/tests -v
```

The test suite validates:
- **Authentication & RBAC**: Token decoding, password verification, forbidden route protection.
- **Ticket Submission**: Auto-classification, ambiguity detection, priority assignment.
- **Sensitive Case Isolation**: Confidential tickets hidden from regular agents.
- **Business-Hours SLA Engine**: Correct calculation across weekends and overnight.
- **Policy Version Control**: Superseding previous active versions.
- **RAG & Citations**: Exact citation matching and graceful fallback for unknown queries.
- **Ticket Resolution & Rating**: Completing tickets and recording employee star ratings.
- **Anomaly Detection**: Detecting all 4 anomaly types and resolving them.
- **Foreign Key Integrity**: Cascades and referential validity.

---

## 8. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `Can't connect to MySQL server on 'localhost'` | MySQL is not started or port differs | Start MySQL service in Windows Services (`services.msc`) or XAMPP/WAMP. Verify credentials in `.env`. |
| `Access Denied for user 'root'@'localhost'` | Wrong database password in `.env` | Update `DB_PASSWORD` in `.env` to match your local MySQL root password. |
| `Network Error: Is backend running on localhost:8000?` | Backend not running | Start backend via `uvicorn app.main:app --reload --port 8000 --app-dir backend`. |
| `Execution of scripts is disabled on this system` | PowerShell execution policy | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once. |

