"""
Pytest Test Fixtures and In-Memory Database Configuration
Provides an isolated, fast in-memory SQLite database and authenticated TestClients for all test suites.
"""
import pytest
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.employee import Employee, RoleEnum, EmploymentTypeEnum, EmployeeStatusEnum
from app.models.department import Department
from app.models.category import Category, PriorityEnum, TierEnum
from app.models.policy import PolicyDocument, PolicyVersion, KnowledgeArticle, AudienceEnum, PolicyStatusEnum
from app.core.security import get_password_hash, create_access_token

# Test database: In-memory SQLite with StaticPool so all connections share the memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    """Provide a clean transaction-isolated database session for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Seed baseline fixtures
    seed_test_database(session)
    
    yield session
    session.close()

def seed_test_database(db):
    """Seed minimal test baseline records."""
    # Departments
    hr_dept = Department(dept_id="DEP-001", name="Human Resources", code="HR", location="HQ")
    eng_dept = Department(dept_id="DEP-002", name="Engineering", code="ENG", location="B4")
    ops_dept = Department(dept_id="DEP-006", name="Operations & IT", code="OPS", location="HQ")
    db.add_all([hr_dept, eng_dept, ops_dept])
    db.commit()

    # Users
    pwd_hash = get_password_hash("Password123!")
    emp_user = Employee(
        emp_id="EMP-TEST-01",
        email="employee@company.com",
        password_hash=pwd_hash,
        full_name="Standard Employee",
        department_id="DEP-002",
        role=RoleEnum.EMPLOYEE,
        employment_type=EmploymentTypeEnum.FULL_TIME,
        hire_date=date(2023, 1, 1),
        is_active=True
    )
    agent_user = Employee(
        emp_id="EMP-TEST-02",
        email="agent@company.com",
        password_hash=pwd_hash,
        full_name="HR Agent",
        department_id="DEP-001",
        role=RoleEnum.HR_AGENT,
        employment_type=EmploymentTypeEnum.FULL_TIME,
        hire_date=date(2022, 1, 1),
        is_active=True
    )
    mgr_user = Employee(
        emp_id="EMP-TEST-03",
        email="manager@company.com",
        password_hash=pwd_hash,
        full_name="HR Manager",
        department_id="DEP-001",
        role=RoleEnum.HR_MANAGER,
        employment_type=EmploymentTypeEnum.FULL_TIME,
        hire_date=date(2021, 1, 1),
        is_active=True
    )
    comp_user = Employee(
        emp_id="EMP-TEST-04",
        email="compliance@company.com",
        password_hash=pwd_hash,
        full_name="Compliance Officer",
        department_id="DEP-001",
        role=RoleEnum.COMPLIANCE_OFFICER,
        employment_type=EmploymentTypeEnum.FULL_TIME,
        hire_date=date(2021, 1, 1),
        is_active=True
    )
    it_user = Employee(
        emp_id="EMP-TEST-05",
        email="it.partner@company.com",
        password_hash=pwd_hash,
        full_name="IT Operations Partner",
        department_id="DEP-006",
        role=RoleEnum.IT_OPERATIONS_PARTNER,
        employment_type=EmploymentTypeEnum.FULL_TIME,
        hire_date=date(2021, 1, 1),
        is_active=True
    )
    db.add_all([emp_user, agent_user, mgr_user, comp_user, it_user])
    db.commit()

    # Categories
    cat_ben = Category(category_id="CAT-001", name="Benefits", code="BEN", default_priority=PriorityEnum.MEDIUM, is_sensitive_default=False, tier=TierEnum.TIER_1)
    cat_lev = Category(category_id="CAT-002", name="Leave", code="LEV", default_priority=PriorityEnum.MEDIUM, is_sensitive_default=False, tier=TierEnum.TIER_1)
    cat_pay = Category(category_id="CAT-003", name="Payroll", code="PAY", default_priority=PriorityEnum.HIGH, is_sensitive_default=False, tier=TierEnum.TIER_2)
    cat_cmp = Category(category_id="CAT-007", name="Compliance & Ethics", code="CMP", default_priority=PriorityEnum.URGENT, is_sensitive_default=True, tier=TierEnum.TIER_3)
    db.add_all([cat_ben, cat_lev, cat_pay, cat_cmp])
    db.commit()

    # Policy and Versions
    pdoc = PolicyDocument(
        policy_id="POL-001",
        doc_code="POL-BEN-01",
        title="Health and Dental Benefits",
        category_id="CAT-001",
        department_id="DEP-001",
        audience=AudienceEnum.ALL_EMPLOYEES,
        owner_id="EMP-TEST-03"
    )
    db.add(pdoc)
    db.commit()

    # Active version
    pver_active = PolicyVersion(
        version_id="VER-001-2",
        policy_id="POL-001",
        version_number="2.0",
        status=PolicyStatusEnum.ACTIVE,
        effective_from=date(2025, 1, 1),
        effective_to=None,
        summary="Current active medical benefits",
        content="Standard comprehensive health benefits cover 80% of in-network dental care.",
        approved_by="EMP-TEST-03",
        approved_at=datetime.utcnow()
    )
    # Superseded version
    pver_old = PolicyVersion(
        version_id="VER-001-1",
        policy_id="POL-001",
        version_number="1.0",
        status=PolicyStatusEnum.SUPERSEDED,
        effective_from=date(2023, 1, 1),
        effective_to=date(2024, 12, 31),
        summary="Legacy medical benefits",
        content="Legacy dental was capped at $500 per year.",
        approved_by="EMP-TEST-03",
        approved_at=datetime(2023, 1, 1)
    )
    db.add_all([pver_active, pver_old])
    db.commit()

    art1 = KnowledgeArticle(
        article_id="ART-001",
        policy_version_id="VER-001-2",
        title="Dental Coverage In-Network Guidelines",
        section_number="Sec 2.1",
        content="Under active policy, in-network preventive and diagnostic dental care is covered at 100%, and basic restorations at 80%.",
        keywords="dental, health, teeth, cleaning, in-network",
        audience=AudienceEnum.ALL_EMPLOYEES,
        is_published=True
    )
    db.add(art1)
    db.commit()

@pytest.fixture(scope="function")
def client(db):
    """FastAPI test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def employee_token():
    return create_access_token({"sub": "EMP-TEST-01", "role": "EMPLOYEE"})

@pytest.fixture
def agent_token():
    return create_access_token({"sub": "EMP-TEST-02", "role": "HR_AGENT"})

@pytest.fixture
def manager_token():
    return create_access_token({"sub": "EMP-TEST-03", "role": "HR_MANAGER"})

@pytest.fixture
def compliance_token():
    return create_access_token({"sub": "EMP-TEST-04", "role": "COMPLIANCE_OFFICER"})

@pytest.fixture
def it_operations_token():
    return create_access_token({"sub": "EMP-TEST-05", "role": "IT_OPERATIONS_PARTNER"})

