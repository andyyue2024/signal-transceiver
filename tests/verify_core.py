"""
Simple test script to verify core functionality.
Run with: python tests/verify_core.py
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all core modules can be imported."""
    print("Testing imports...")

    try:
        from src.models.user import User
        print("  ✓ User model")
    except Exception as e:
        print(f"  ✗ User model: {e}")
        return False

    try:
        from src.models.data import Data
        print("  ✓ Data model")
    except Exception as e:
        print(f"  ✗ Data model: {e}")
        return False

    try:
        from src.models.strategy import Strategy
        print("  ✓ Strategy model")
    except Exception as e:
        print(f"  ✗ Strategy model: {e}")
        return False

    try:
        from src.models.subscription import Subscription
        print("  ✓ Subscription model")
    except Exception as e:
        print(f"  ✗ Subscription model: {e}")
        return False

    try:
        from src.models.permission import Permission, Role, UserPermission
        print("  ✓ Permission models")
    except Exception as e:
        print(f"  ✗ Permission models: {e}")
        return False

    try:
        from src.models.log import Log
        print("  ✓ Log model")
    except Exception as e:
        print(f"  ✗ Log model: {e}")
        return False

    try:
        from src.services.auth_service import AuthService
        print("  ✓ AuthService")
    except Exception as e:
        print(f"  ✗ AuthService: {e}")
        return False

    try:
        from src.api.v1.system import router as system_router
        print("  ✓ System API router")
    except Exception as e:
        print(f"  ✗ System API router: {e}")
        return False

    try:
        from src.core.security import get_password_hash, verify_password, generate_api_key
        print("  ✓ Security module")
    except Exception as e:
        print(f"  ✗ Security module: {e}")
        return False

    print("\n✅ All imports successful!")
    return True


def test_security():
    """Test security functions."""
    print("\nTesting security functions...")

    from src.core.security import get_password_hash, verify_password, generate_api_key, generate_client_credentials

    # Test password hashing
    password = "test_password_123"
    hashed = get_password_hash(password)
    print(f"  ✓ Password hashed: {hashed[:30]}...")

    # Test password verification
    if verify_password(password, hashed):
        print("  ✓ Password verification: correct password accepted")
    else:
        print("  ✗ Password verification failed")
        return False

    if not verify_password("wrong_password", hashed):
        print("  ✓ Password verification: wrong password rejected")
    else:
        print("  ✗ Wrong password was accepted!")
        return False

    # Test API key generation
    api_key, hashed_key = generate_api_key()
    print(f"  ✓ API key generated: {api_key[:20]}...")

    # Test client credentials
    client_key, client_secret, hashed_secret = generate_client_credentials()
    print(f"  ✓ Client key: {client_key}")
    print(f"  ✓ Client secret: {client_secret[:20]}...")

    print("\n✅ All security tests passed!")
    return True


async def test_database():
    """Test database connection and models."""
    print("\nTesting database...")

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy.pool import StaticPool
    from src.config.database import Base
    from src.models.user import User
    from src.models.strategy import Strategy
    from src.core.security import get_password_hash, generate_api_key, generate_client_credentials

    # Create in-memory test database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  ✓ Database tables created")

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        # Create test user
        api_key, hashed_key = generate_api_key()
        client_key, client_secret, hashed_secret = generate_client_credentials()

        user = User(
            username="test_user",
            email="test@example.com",
            hashed_password=get_password_hash("test123"),
            api_key=hashed_key,
            client_key=client_key,
            client_secret=hashed_secret,
            is_active=True,
            is_admin=False
        )
        session.add(user)
        await session.commit()
        print("  ✓ User created")

        # Create test strategy
        strategy = Strategy(
            strategy_id="test_strategy_001",
            name="Test Strategy",
            description="A test strategy",
            type="default",
            is_active=True
        )
        session.add(strategy)
        await session.commit()
        print("  ✓ Strategy created")

        # Query user
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "test_user"))
        found_user = result.scalar_one_or_none()
        if found_user:
            print(f"  ✓ User queried: {found_user.username}")
        else:
            print("  ✗ User query failed")
            return False

        # Query strategy
        result = await session.execute(select(Strategy).where(Strategy.strategy_id == "test_strategy_001"))
        found_strategy = result.scalar_one_or_none()
        if found_strategy:
            print(f"  ✓ Strategy queried: {found_strategy.name}")
        else:
            print("  ✗ Strategy query failed")
            return False

    print("\n✅ All database tests passed!")
    return True


async def test_auth_service():
    """Test authentication service."""
    print("\nTesting AuthService...")

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy.pool import StaticPool
    from src.config.database import Base
    from src.services.auth_service import AuthService
    from src.schemas.user import UserCreate

    # Create in-memory test database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        auth_service = AuthService(session)

        # Test user registration
        user_data = UserCreate(
            username="auth_test_user",
            email="auth_test@example.com",
            password="secure_password_123"
        )

        user, api_key = await auth_service.register_user(user_data)
        print(f"  ✓ User registered: {user.username}")
        print(f"  ✓ API key returned: {api_key[:20]}...")

        # Test authentication
        authenticated_user = await auth_service.authenticate_user("auth_test_user", "secure_password_123")
        print(f"  ✓ User authenticated: {authenticated_user.username}")

        # Test wrong password
        try:
            await auth_service.authenticate_user("auth_test_user", "wrong_password")
            print("  ✗ Wrong password was accepted!")
            return False
        except Exception:
            print("  ✓ Wrong password rejected")

        # Test API key regeneration
        new_api_key = await auth_service.regenerate_api_key(user.id)
        print(f"  ✓ API key regenerated: {new_api_key[:20]}...")

    print("\n✅ All AuthService tests passed!")
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Signal Transceiver - Core Functionality Tests")
    print("=" * 60)

    all_passed = True

    # Test imports
    if not test_imports():
        all_passed = False

    # Test security
    if not test_security():
        all_passed = False

    # Test database
    if not await test_database():
        all_passed = False

    # Test auth service
    if not await test_auth_service():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
