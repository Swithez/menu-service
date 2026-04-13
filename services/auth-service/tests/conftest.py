"""
Shared test fixtures for auth-service.

Uses SQLite in-memory for isolation — no real PostgreSQL required.
Session-scoped engine seeds permissions + admin role + admin user once.
Each test gets a function-scoped session that rolls back after the test.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_session
from app.main import app
from app.models.auth import Permission, Role, RolePermission, User
from app.permissions import ADMIN_PERMISSIONS, ALL_PERMISSIONS
from app.services.auth_service import hash_password

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "testpass123"


# ── Engine (session-scoped) ───────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create tables once per test session and seed baseline data."""
    eng = create_async_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed: permissions → admin role → admin user (committed, visible to all tests)
    factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        for p in ALL_PERMISSIONS:
            s.add(Permission(code=p.code, description=p.description, group=p.group))
        await s.flush()

        admin_role = Role(name="admin", description="Full access", is_system=True)
        s.add(admin_role)
        await s.flush()

        for code in ADMIN_PERMISSIONS:
            s.add(RolePermission(role_id=admin_role.id, permission_code=code))
        await s.flush()

        s.add(
            User(
                email=ADMIN_EMAIL,
                full_name="Test Admin",
                hashed_password=hash_password(ADMIN_PASSWORD),
                role_id=admin_role.id,
                is_active=True,
            )
        )
        await s.commit()

    yield eng
    await eng.dispose()


# ── Per-test session (function-scoped, rolls back) ────────────────────────────

@pytest_asyncio.fixture()
async def session(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
        await sess.rollback()


# ── Unauthenticated HTTP client ───────────────────────────────────────────────

@pytest_asyncio.fixture()
async def client(session):
    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Admin token (session-scoped, obtained once) ───────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def admin_token(engine):
    """Login once and reuse the token for all authenticated tests."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override():
        async with factory() as s:
            yield s

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        token = resp.json()["access_token"]
    app.dependency_overrides.clear()
    return token


# ── Authenticated HTTP client (admin) ─────────────────────────────────────────

@pytest_asyncio.fixture()
async def admin_client(session, admin_token):
    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {admin_token}"},
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
