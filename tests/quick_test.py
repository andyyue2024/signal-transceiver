"""Quick test to verify bcrypt fix and basic functionality"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.security import get_password_hash, verify_password, generate_client_credentials

async def test_security():
    print("Testing security module...")

    # Test password hashing
    password = "test123"
    hashed = get_password_hash(password)
    print(f"✓ Password hashed: {hashed[:50]}...")

    # Test password verification
    assert verify_password(password, hashed), "Password verification failed"
    print("✓ Password verification works")

    # Test client credentials
    client_key, client_secret, hashed_secret = generate_client_credentials()
    print(f"✓ Client key: {client_key}")
    print(f"✓ Client secret: {client_secret[:20]}...")

    print("\n✅ All security tests passed!")

async def test_auth_service():
    print("\nTesting auth service...")
    from src.config.database import get_db, init_db
    from src.services.auth_service import AuthService
    from src.schemas.user import UserCreate
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy.pool import StaticPool
    from src.config.database import Base

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
            username="testuser",
            email="test@example.com",
            password="testpass123",
            full_name="Test User"
        )

        user, api_key = await auth_service.register_user(user_data)
        print(f"✓ User registered: {user.username}")
        print(f"✓ API key generated: {api_key[:20]}...")
        print(f"✓ Client key: {user.client_key}")

        # Test authentication
        auth_user = await auth_service.authenticate_user("testuser", "testpass123")
        print(f"✓ User authenticated: {auth_user.username}")

        print("\n✅ All auth service tests passed!")

if __name__ == "__main__":
    asyncio.run(test_security())
    asyncio.run(test_auth_service())
    print("\n🎉 All tests completed successfully!")
