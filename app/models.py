from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal


# Enums for type safety
class ReportType(str, Enum):
    INDUSTRY = "industry"
    COMPANY = "company"


class UserRole(str, Enum):
    ADMIN = "admin"
    OFFICIAL = "official"
    VIEWER = "viewer"


class InteractionType(str, Enum):
    QUESTION = "question"
    SUMMARY = "summary"
    ANALYSIS = "analysis"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=100, unique=True)
    email: str = Field(max_length=255, unique=True, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    full_name: str = Field(max_length=200)
    role: UserRole = Field(default=UserRole.OFFICIAL)
    is_active: bool = Field(default=True)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)

    # Relationships
    report_interactions: List["ReportInteraction"] = Relationship(back_populates="user")
    search_history: List["SearchHistory"] = Relationship(back_populates="user")


class APICredentials(SQLModel, table=True):
    __tablename__ = "api_credentials"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    service_name: str = Field(max_length=100)  # e.g., "ibisworld", "anthropic"
    api_key: str = Field(max_length=500)  # Encrypted storage
    api_secret: Optional[str] = Field(default=None, max_length=500)
    base_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_user_id: int = Field(foreign_key="users.id")


class IBISWorldReport(SQLModel, table=True):
    __tablename__ = "ibisworld_reports"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: str = Field(max_length=100, unique=True)  # IBISWorld report ID
    title: str = Field(max_length=500)
    report_type: ReportType
    industry_code: Optional[str] = Field(default=None, max_length=50)
    company_name: Optional[str] = Field(default=None, max_length=300)
    description: str = Field(default="", max_length=2000)
    publication_date: Optional[datetime] = Field(default=None)
    report_url: Optional[str] = Field(default=None, max_length=1000)

    # Report metadata
    page_count: Optional[int] = Field(default=None)
    report_size_mb: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10)
    tags: List[str] = Field(default=[], sa_column=Column(JSON))

    # Caching information
    is_cached: bool = Field(default=False)
    cache_expiry: Optional[datetime] = Field(default=None)
    last_accessed: Optional[datetime] = Field(default=None)
    access_count: int = Field(default=0)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    interactions: List["ReportInteraction"] = Relationship(back_populates="report")
    search_results: List["SearchResult"] = Relationship(back_populates="report")


class ReportInteraction(SQLModel, table=True):
    __tablename__ = "report_interactions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    report_id: int = Field(foreign_key="ibisworld_reports.id")

    interaction_type: InteractionType
    question: Optional[str] = Field(default=None, max_length=1000)
    response: str = Field(max_length=10000)

    # Claude API interaction details
    claude_model: str = Field(max_length=100, default="claude-3-sonnet-20240229")
    tokens_used: Optional[int] = Field(default=None)
    response_time_ms: Optional[int] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="report_interactions")
    report: IBISWorldReport = Relationship(back_populates="interactions")


class SearchHistory(SQLModel, table=True):
    __tablename__ = "search_history"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    search_query: str = Field(max_length=500)
    search_filters: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    results_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="search_history")
    search_results: List["SearchResult"] = Relationship(back_populates="search_history")


class SearchResult(SQLModel, table=True):
    __tablename__ = "search_results"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    search_history_id: int = Field(foreign_key="search_history.id")
    report_id: int = Field(foreign_key="ibisworld_reports.id")
    relevance_score: Optional[Decimal] = Field(default=None, decimal_places=4, max_digits=10)
    result_rank: int = Field(default=0)

    # Relationships
    search_history: SearchHistory = Relationship(back_populates="search_results")
    report: IBISWorldReport = Relationship(back_populates="search_results")


class ReportCache(SQLModel, table=True):
    __tablename__ = "report_cache"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    cache_key: str = Field(max_length=255, unique=True)
    cache_type: str = Field(max_length=50)  # "report_list", "report_content", "search_results"
    cache_data: Dict[str, Any] = Field(sa_column=Column(JSON))
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    hit_count: int = Field(default=0)
    last_hit: Optional[datetime] = Field(default=None)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    action: str = Field(max_length=100)  # "login", "report_access", "api_call", etc.
    resource_type: Optional[str] = Field(default=None, max_length=100)
    resource_id: Optional[str] = Field(default=None, max_length=255)
    details: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    username: str = Field(max_length=100)
    email: str = Field(max_length=255)
    full_name: str = Field(max_length=200)
    password: str = Field(min_length=8, max_length=255)
    role: UserRole = Field(default=UserRole.OFFICIAL)


class UserUpdate(SQLModel, table=False):
    full_name: Optional[str] = Field(default=None, max_length=200)
    email: Optional[str] = Field(default=None, max_length=255)
    role: Optional[UserRole] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class UserLogin(SQLModel, table=False):
    username: str = Field(max_length=100)
    password: str = Field(max_length=255)


class ReportSearch(SQLModel, table=False):
    query: str = Field(max_length=500)
    report_type: Optional[ReportType] = Field(default=None)
    industry_codes: List[str] = Field(default=[])
    publication_date_from: Optional[datetime] = Field(default=None)
    publication_date_to: Optional[datetime] = Field(default=None)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ReportInteractionCreate(SQLModel, table=False):
    report_id: int
    interaction_type: InteractionType
    question: Optional[str] = Field(default=None, max_length=1000)


class APICredentialsCreate(SQLModel, table=False):
    service_name: str = Field(max_length=100)
    api_key: str = Field(max_length=500)
    api_secret: Optional[str] = Field(default=None, max_length=500)
    base_url: Optional[str] = Field(default=None, max_length=500)


class APICredentialsUpdate(SQLModel, table=False):
    api_key: Optional[str] = Field(default=None, max_length=500)
    api_secret: Optional[str] = Field(default=None, max_length=500)
    base_url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)


class ReportSummary(SQLModel, table=False):
    id: int
    report_id: str
    title: str
    report_type: ReportType
    industry_code: Optional[str] = None
    company_name: Optional[str] = None
    publication_date: Optional[str] = None  # ISO format
    last_accessed: Optional[str] = None  # ISO format
    access_count: int
    is_cached: bool


class InteractionHistory(SQLModel, table=False):
    interactions: List[Dict[str, Any]] = Field(default=[])
    total_count: int
    user_name: str
    report_title: str
