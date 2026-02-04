#!/usr/bin/env python
"""
测试管理员登录API修复
验证登录后返回 api_key
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_admin_login_api():
    """测试管理员登录API"""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy.pool import StaticPool
    from src.config.database import Base
    from src.services.auth_service import AuthService
    from src.schemas.user import UserCreate
    from src.schemas.auth import LoginRequest
    from src.api.v1.auth import login

    print("=" * 70)
    print("🧪 测试管理员登录 API - 验证返回 api_key")
    print("=" * 70)

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
            # 1. 创建管理员用户
            print("\n📝 步骤 1: 创建管理员用户...")
            auth_service = AuthService(session)

            admin_data = UserCreate(
                username="admin",
                email="admin@example.com",
                password="admin123",
                full_name="管理员"
            )

            admin_user, original_api_key = await auth_service.register_user(admin_data)

            # 设置为管理员
            admin_user.is_admin = True
            await session.commit()
            await session.refresh(admin_user)

            print(f"✅ 管理员创建成功")
            print(f"   用户名: {admin_user.username}")
            print(f"   User ID: {admin_user.id}")
            print(f"   原始 API Key: {original_api_key[:20]}...")
            print(f"   存储的 API Key (hashed): {admin_user.api_key[:20]}...")

            # 2. 测试登录API
            print("\n🔐 步骤 2: 测试登录 API...")

            # 创建新的session用于登录测试
            async with session_maker() as login_session:
                login_request = LoginRequest(
                    username="admin",
                    password="admin123"
                )

                # 调用登录API
                response = await login(login_request, login_session)

                print(f"✅ 登录 API 调用成功")
                print(f"   Success: {response.success}")
                print(f"   Message: {response.message}")

                # 3. 验证返回数据
                print("\n✅ 步骤 3: 验证返回数据...")

                if not response.data:
                    print("❌ 失败: response.data 为空")
                    return False

                print(f"   返回数据键: {list(response.data.keys())}")

                # 检查是否包含 api_key
                if 'api_key' not in response.data:
                    print("❌ 失败: 返回数据中没有 'api_key'")
                    print(f"   实际返回: {response.data}")
                    return False

                returned_api_key = response.data['api_key']
                print(f"✅ 返回的 API Key: {returned_api_key[:20]}...")

                # 验证返回的是存储的API Key
                if returned_api_key == admin_user.api_key:
                    print(f"✅ API Key 正确: 返回的是数据库中存储的 API Key")
                else:
                    print(f"⚠️  注意: 返回的 API Key 与存储的不完全匹配")
                    print(f"   期望: {admin_user.api_key[:20]}...")
                    print(f"   实际: {returned_api_key[:20]}...")

                # 检查用户信息
                if 'user' in response.data:
                    user_data = response.data['user']
                    print(f"✅ 包含用户信息")
                    print(f"   用户名: {user_data.get('username')}")
                    print(f"   邮箱: {user_data.get('email')}")
                    print(f"   是否管理员: {user_data.get('is_admin')}")

                print("\n" + "=" * 70)
                print("🎉 所有测试通过！登录 API 正确返回 api_key")
                print("=" * 70)
                print("\n💡 前端应该能够:")
                print("   1. 接收到 response.data.api_key")
                print("   2. 保存到 localStorage")
                print("   3. 用于后续 API 请求")

                return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    result = asyncio.run(test_admin_login_api())

    if result:
        print("\n✅ 修复验证成功！")
        print("\n🚀 现在可以:")
        print("   1. 重启应用: python src/main.py")
        print("   2. 访问: http://localhost:8000/admin/login")
        print("   3. 登录: admin / admin123")
        print("   4. 应该能正常跳转到管理界面")
    else:
        print("\n❌ 修复验证失败，请检查问题")

    sys.exit(0 if result else 1)
