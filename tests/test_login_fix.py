#!/usr/bin/env python
"""
快速测试登录功能
验证 timezone 导入问题是否已修复
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_login():
    """测试登录功能"""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy.pool import StaticPool
    from src.config.database import Base
    from src.services.auth_service import AuthService
    from src.schemas.user import UserCreate

    print("=" * 60)
    print("🧪 测试登录功能 - 验证 timezone 导入修复")
    print("=" * 60)

    # 创建测试数据库
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_maker() as session:
            auth_service = AuthService(session)

            # 创建测试用户
            print("\n📝 创建测试用户...")
            user_data = UserCreate(
                username="testuser",
                email="test@example.com",
                password="test123",
                full_name="Test User"
            )

            user, api_key = await auth_service.register_user(user_data)
            print(f"✅ 用户注册成功: {user.username}")
            print(f"   User ID: {user.id}")
            print(f"   API Key: {api_key[:20]}...")
            print(f"   Client Key: {user.client_key}")

            # 测试登录（这会触发 timezone 的使用）
            print("\n🔐 测试用户登录...")
            auth_user = await auth_service.authenticate_user("testuser", "test123")
            print(f"✅ 用户登录成功: {auth_user.username}")
            print(f"   Last Login: {auth_user.last_login_at}")

            # 验证 last_login_at 已设置
            if auth_user.last_login_at:
                print(f"✅ last_login_at 已正确设置")
                print(f"   类型: {type(auth_user.last_login_at)}")
                print(f"   时区: {auth_user.last_login_at.tzinfo}")
            else:
                print(f"❌ last_login_at 未设置")
                return False

            print("\n" + "=" * 60)
            print("🎉 所有测试通过！timezone 导入问题已修复！")
            print("=" * 60)
            return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    result = asyncio.run(test_login())
    sys.exit(0 if result else 1)
