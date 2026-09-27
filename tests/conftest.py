"""
SIH 26090: Pytest Test Configuration & Shared Fixtures
Configures in-memory SQLite database, FastAPI dependency overrides,
and pre-seeded authenticated user fixtures for Phase 2 tests.
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_async_db
import backend.app.models  # Register all models on Base.metadata
from backend.app.main import app
from backend.app.core.security import hash_password, create_access_token
from backend.app.models.auth import User, Role
from backend.app.models.craft import CraftCategory, Craft
from backend.app.models.artisan import ArtisanProfile
from backend.app.models.buyer import BuyerProfile

# In-memory SQLite async engine with StaticPool for test isolation and persistence across session calls
test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    future=True,
    echo=False
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


@pytest_asyncio.fixture(autouse=True)
async def init_db():
    """Initializes tables before each test and drops them afterwards."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a transactional database session for tests."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provides an AsyncClient connected to the FastAPI application with mocked DB."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_async_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_craft(db_session: AsyncSession) -> Craft:
    """Seeds a craft category and craft record for artisan profile and passport linkage."""
    cat = CraftCategory(name="Handloom Textiles", description="Traditional handlooms")
    db_session.add(cat)
    await db_session.flush()

    craft = Craft(
        category_id=cat.id,
        name="Chanderi Silk Saree",
        gi_tag_number="GI-007",
        has_gi_tag=True,
        origin_state="Madhya Pradesh",
        origin_district="Ashoknagar",
        cultural_heritage_description="Traditional sheer weave with zari border.",
        traditional_raw_materials=["Silk", "Cotton", "Zari"]
    )
    db_session.add(craft)
    await db_session.commit()
    await db_session.refresh(craft)
    return craft


@pytest_asyncio.fixture
async def artisan_user(db_session: AsyncSession) -> User:
    """Creates a seeded active artisan user."""
    user = User(
        phone_number="+919876543201",
        email="artisan1@test.in",
        password_hash=hash_password("ArtisanPass123!"),
        role="artisan",
        preferred_language="hi",
        is_active=True,
        is_verified=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
def artisan_token(artisan_user: User) -> str:
    """Generates a valid JWT access token for the artisan user."""
    return create_access_token(user_id=artisan_user.id, role=artisan_user.role)


@pytest_asyncio.fixture
def artisan_headers(artisan_token: str) -> dict:
    """Authorization headers for the artisan user."""
    return {"Authorization": f"Bearer {artisan_token}"}


@pytest_asyncio.fixture
async def other_artisan_user(db_session: AsyncSession) -> User:
    """Creates a second active artisan user for cross-user permission / IDOR tests."""
    user = User(
        phone_number="+919876543202",
        email="artisan2@test.in",
        password_hash=hash_password("ArtisanPass123!"),
        role="artisan",
        preferred_language="en",
        is_active=True,
        is_verified=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
def other_artisan_token(other_artisan_user: User) -> str:
    """Generates a valid JWT access token for the second artisan user."""
    return create_access_token(user_id=other_artisan_user.id, role=other_artisan_user.role)


@pytest_asyncio.fixture
def other_artisan_headers(other_artisan_token: str) -> dict:
    """Authorization headers for the second artisan user."""
    return {"Authorization": f"Bearer {other_artisan_token}"}


@pytest_asyncio.fixture
async def buyer_user(db_session: AsyncSession) -> User:
    """Creates a seeded active buyer user."""
    user = User(
        phone_number="+919876543203",
        email="buyer1@test.in",
        password_hash=hash_password("BuyerPass123!"),
        role="buyer",
        preferred_language="en",
        is_active=True,
        is_verified=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
def buyer_token(buyer_user: User) -> str:
    """Generates a valid JWT access token for the buyer user."""
    return create_access_token(user_id=buyer_user.id, role=buyer_user.role)


@pytest_asyncio.fixture
def buyer_headers(buyer_token: str) -> dict:
    """Authorization headers for the buyer user."""
    return {"Authorization": f"Bearer {buyer_token}"}


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Creates a seeded active admin user."""
    user = User(
        phone_number="+919876543204",
        email="admin@test.gov.in",
        password_hash=hash_password("AdminPass123!"),
        role="admin",
        preferred_language="en",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
def admin_token(admin_user: User) -> str:
    """Generates a valid JWT access token for the admin user."""
    return create_access_token(user_id=admin_user.id, role=admin_user.role)


@pytest_asyncio.fixture
def admin_headers(admin_token: str) -> dict:
    """Authorization headers for the admin user."""
    return {"Authorization": f"Bearer {admin_token}"}
