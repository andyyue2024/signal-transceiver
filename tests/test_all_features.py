#!/usr/bin/env python
"""
完整功能测试脚本
测试所有核心功能，包括管理后台登录认证
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试统计
stats = {"total": 0, "passed": 0, "failed": 0, "errors": []}

def test(name, condition, details=""):
    """测试函数"""
    stats["total"] += 1
    if condition:
        print(f"✅ {name}")
        if details:
            print(f"   {details}")
        stats["passed"] += 1
        return True
    else:
        print(f"❌ {name}")
        if details:
            print(f"   {details}")
        stats["failed"] += 1
        stats["errors"].append(name)
        return False

print("=" * 80)
print("🧪 Signal Transceiver - 完整功能测试")
print("=" * 80)

# 1. 基础模块测试
print("\n📦 1. 基础模块导入测试")
print("-" * 80)

try:
    from src.core.security import (
        get_password_hash, verify_password,
        generate_api_key, generate_client_credentials
    )
    test("安全模块导入", True)
except Exception as e:
    test("安全模块导入", False, f"错误: {e}")

try:
    from src.services.auth_service import AuthService
    test("认证服务导入", True)
except Exception as e:
    test("认证服务导入", False, f"错误: {e}")

try:
    from src.services.import_service import DataImportService
    test("数据导入服务导入", True)
except Exception as e:
    test("数据导入服务导入", False, f"错误: {e}")

try:
    from src.core.ip_control import IPAccessControl
    test("IP访问控制导入", True)
except Exception as e:
    test("IP访问控制导入", False, f"错误: {e}")

# 2. 功能测试
print("\n🔧 2. 核心功能测试")
print("-" * 80)

# 密码哈希测试
try:
    from src.core.security import get_password_hash, verify_password
    pwd = "test123"
    hashed = get_password_hash(pwd)
    verified = verify_password(pwd, hashed)
    test("密码哈希和验证", verified, "bcrypt 正常工作")
except Exception as e:
    test("密码哈希和验证", False, f"错误: {e}")

# API Key 生成测试
try:
    from src.core.security import generate_api_key
    api_key, hashed_key = generate_api_key()
    test("API Key 生成",
         api_key.startswith("sk_") and len(api_key) > 32,
         f"生成: {api_key[:20]}...")
except Exception as e:
    test("API Key 生成", False, f"错误: {e}")

# 客户端凭证生成测试
try:
    from src.core.security import generate_client_credentials
    ck, cs, hs = generate_client_credentials()
    test("客户端凭证生成",
         ck.startswith("ck_") and cs.startswith("cs_"),
         f"CK: {ck[:15]}..., CS: {cs[:15]}...")
except Exception as e:
    test("客户端凭证生成", False, f"错误: {e}")

# 3. 数据库和认证测试
print("\n🗄️ 3. 数据库和认证测试")
print("-" * 80)

async def test_database_auth():
    """测试数据库和认证"""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from sqlalchemy.pool import StaticPool
        from src.config.database import Base
        from src.services.auth_service import AuthService
        from src.schemas.user import UserCreate

        # 创建测试数据库
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

            # 测试用户注册
            user_data = UserCreate(
                username="testuser",
                email="test@example.com",
                password="test123",
                full_name="Test User"
            )

            user, api_key = await auth_service.register_user(user_data)
            test("用户注册",
                 user.username == "testuser" and user.client_key is not None,
                 f"用户ID: {user.id}, 已生成 client_key")

            # 测试用户认证
            auth_user = await auth_service.authenticate_user("testuser", "test123")
            test("用户认证", auth_user.id == user.id, "认证成功")

            # 测试错误密码
            try:
                await auth_service.authenticate_user("testuser", "wrongpass")
                test("错误密码拒绝", False, "应该抛出异常")
            except:
                test("错误密码拒绝", True, "正确拒绝错误密码")

            # 测试管理员用户
            admin_data = UserCreate(
                username="admin",
                email="admin@example.com",
                password="admin123",
                full_name="管理员"
            )
            admin_user, admin_key = await auth_service.register_user(admin_data)

            # 手动设置为管理员
            admin_user.is_admin = True
            await session.commit()
            await session.refresh(admin_user)

            test("管理员用户创建",
                 admin_user.is_admin == True,
                 f"管理员: {admin_user.username}")

        await engine.dispose()

    except Exception as e:
        test("数据库和认证测试", False, f"错误: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_database_auth())

# 4. IP访问控制测试
print("\n🛡️ 4. IP 访问控制测试")
print("-" * 80)

try:
    from src.core.ip_control import IPAccessControl
    ip_control = IPAccessControl()

    # IPv4 验证
    test("IPv4 地址验证",
         ip_control.is_valid_ip("192.168.1.1"),
         "192.168.1.1 是有效的 IPv4")

    # IPv6 验证
    test("IPv6 地址验证",
         ip_control.is_valid_ip("2001:db8::1"),
         "2001:db8::1 是有效的 IPv6")

    # 无效IP
    test("无效IP拒绝",
         not ip_control.is_valid_ip("invalid"),
         "正确拒绝无效IP")

    # 网络段检查
    test("CIDR 网络段检查",
         ip_control.is_in_network("192.168.1.10", "192.168.1.0/24"),
         "192.168.1.10 在 192.168.1.0/24 网段内")

except Exception as e:
    test("IP访问控制测试", False, f"错误: {e}")

# 5. 缓存系统测试
print("\n💾 5. 缓存系统测试")
print("-" * 80)

try:
    from src.core.cache import CacheManager
    cache = CacheManager.get_instance()

    # 设置和获取
    cache.set("test_key", "test_value")
    value = cache.get("test_key")
    test("缓存设置和获取", value == "test_value", "值匹配")

    # 删除
    cache.delete("test_key")
    value = cache.get("test_key")
    test("缓存删除", value is None, "缓存已清除")

    # LRU 测试
    for i in range(1050):  # 超过默认容量1000
        cache.set(f"key_{i}", f"value_{i}")

    test("LRU 缓存淘汰",
         cache.get("key_0") is None,
         "早期键已被淘汰")

except Exception as e:
    test("缓存系统测试", False, f"错误: {e}")

# 6. 文件存在性检查
print("\n📁 6. 关键文件检查")
print("-" * 80)

files = [
    ("主程序", "src/main.py"),
    ("管理后台登录", "src/web/admin_login.py"),
    ("管理后台界面", "src/web/admin_ui.py"),
    ("数据导入服务", "src/services/import_service.py"),
    ("导入API", "src/api/v1/import.py"),
    ("IP控制", "src/core/ip_control.py"),
    ("初始化管理员脚本", "init_admin.py"),
    ("Docker配置", "docker/Dockerfile"),
    ("快速启动指南", "QUICKSTART.md"),
]

for name, path in files:
    test(name, os.path.exists(path), path)

# 7. Web UI 功能检查
print("\n🖥️ 7. Web UI 功能检查")
print("-" * 80)

# 检查 admin_login.py 中的关键功能
try:
    with open("web/admin_login.py", "r", encoding="utf-8") as f:
        content = f.read()
        test("登录页面存在", "/admin/login" in content)
        test("退出登录功能", "/admin/logout" in content)
        test("LocalStorage 会话", "localStorage" in content)
        test("登录表单", "handleLogin" in content)
except Exception as e:
    test("Web UI 功能检查", False, f"错误: {e}")

# 检查 admin_ui.py 中的会话验证
try:
    with open("web/admin_ui.py", "r", encoding="utf-8") as f:
        content = f.read()
        test("强制登录检查", "checkAuth" in content and "window.location.href = '/admin/login'" in content)
        test("退出登录按钮", "handleLogout" in content)
        test("用户信息显示", "userInfo" in content)
        test("会话保护", "localStorage.getItem('adminApiKey')" in content)
except Exception as e:
    test("会话验证检查", False, f"错误: {e}")

# 最终统计
print("\n" + "=" * 80)
print("📊 测试结果统计")
print("=" * 80)
print(f"总测试数: {stats['total']}")
print(f"✅ 通过: {stats['passed']} ({stats['passed']/stats['total']*100:.1f}%)")
print(f"❌ 失败: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")

if stats["failed"] > 0:
    print("\n❌ 失败的测试:")
    for error in stats["errors"]:
        print(f"   - {error}")

print("\n" + "=" * 80)
if stats["failed"] == 0:
    print("🎉 所有测试通过！")
    print("\n✅ 项目功能完整性确认:")
    print("   1. ✅ 基础模块全部正常")
    print("   2. ✅ 核心功能运行正常")
    print("   3. ✅ 数据库和认证工作正常")
    print("   4. ✅ 安全功能实现完整")
    print("   5. ✅ 管理后台登录认证完善")
    print("   6. ✅ 会话管理和退出登录正常")
    print("   7. ✅ 所有关键文件存在")
    print("\n🚀 系统已就绪，可以部署使用！")
    sys.exit(0)
else:
    print(f"⚠️ 有 {stats['failed']} 个测试失败，请检查！")
    sys.exit(1)
