#!/usr/bin/env python
"""
综合功能测试脚本
测试所有核心功能和新增功能
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from src.config.database import Base

# 测试结果统计
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}


def test_passed(test_name):
    """标记测试通过"""
    print(f"✅ {test_name}")
    test_results["passed"] += 1


def test_failed(test_name, error):
    """标记测试失败"""
    print(f"❌ {test_name}: {error}")
    test_results["failed"] += 1
    test_results["errors"].append({
        "test": test_name,
        "error": str(error)
    })


async def test_security():
    """测试安全模块"""
    print("\n🔐 测试安全模块...")

    try:
        from src.core.security import (
            get_password_hash, verify_password,
            generate_api_key, generate_client_credentials
        )

        # 测试密码哈希
        password = "test123"
        hashed = get_password_hash(password)
        assert hashed, "密码哈希失败"
        test_passed("密码哈希")

        # 测试密码验证
        assert verify_password(password, hashed), "密码验证失败"
        test_passed("密码验证")

        # 测试错误密码
        assert not verify_password("wrong", hashed), "错误密码验证应该失败"
        test_passed("错误密码验证")

        # 测试 API Key 生成
        api_key, hashed_key = generate_api_key()
        assert api_key.startswith("sk_"), "API Key 格式错误"
        assert len(api_key) > 32, "API Key 长度不足"
        test_passed("API Key 生成")

        # 测试客户端凭证生成
        client_key, client_secret, hashed_secret = generate_client_credentials()
        assert client_key.startswith("ck_"), "Client Key 格式错误"
        assert client_secret.startswith("cs_"), "Client Secret 格式错误"
        test_passed("客户端凭证生成")

    except Exception as e:
        test_failed("安全模块", e)


async def test_auth_service():
    """测试认证服务"""
    print("\n👤 测试认证服务...")

    try:
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
                password="testpass123",
                full_name="Test User"
            )

            user, api_key = await auth_service.register_user(user_data)
            assert user.username == "testuser", "用户名不匹配"
            assert user.client_key, "client_key 未生成"
            assert api_key, "API key 未返回"
            test_passed("用户注册")

            # 测试用户认证
            auth_user = await auth_service.authenticate_user("testuser", "testpass123")
            assert auth_user.id == user.id, "认证用户不匹配"
            test_passed("用户认证")

            # 测试错误密码
            try:
                await auth_service.authenticate_user("testuser", "wrongpass")
                test_failed("错误密码认证", "应该抛出异常")
            except Exception:
                test_passed("错误密码认证拒绝")

            # 测试 API Key 重新生成
            new_api_key = await auth_service.regenerate_api_key(user.id)
            assert new_api_key, "新 API key 未生成"
            assert new_api_key != api_key, "新旧 API key 相同"
            test_passed("API Key 重新生成")

    except Exception as e:
        test_failed("认证服务", e)


async def test_data_import_service():
    """测试数据导入服务"""
    print("\n📥 测试数据导入服务...")

    try:
        from src.services.import_service import DataImportService
        from src.models.strategy import Strategy
        from src.models.user import User
        from src.core.security import generate_api_key, generate_client_credentials, get_password_hash

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
            # 创建测试用户
            api_key, hashed_key = generate_api_key()
            client_key, client_secret, hashed_secret = generate_client_credentials()

            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("password123"),
                api_key=hashed_key,
                client_key=client_key,
                client_secret=hashed_secret,
                is_active=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            # 创建测试策略
            strategy = Strategy(
                name="Test Strategy",
                description="Test",
                type="trading",
                user_id=user.id,
                is_active=True
            )
            session.add(strategy)
            await session.commit()
            await session.refresh(strategy)

            # 测试 CSV 导入
            csv_content = f"""type,strategy_id,symbol,execute_date,description,metadata
signal,{strategy.id},AAPL,2024-01-01,Buy signal,"{{\\"price\\": 150.0}}"
data,{strategy.id},GOOGL,2024-01-02,Market data,"{{\\"volume\\": 1000000}}"
"""

            import_service = DataImportService(session)
            result = await import_service.import_from_csv(csv_content, user.id)

            assert result.total == 2, f"总数应为2，实际为{result.total}"
            assert result.success == 2, f"成功数应为2，实际为{result.success}"
            assert result.failed == 0, f"失败数应为0，实际为{result.failed}"
            test_passed("CSV 数据导入")

            # 测试 JSON 导入
            json_data = [
                {
                    "type": "signal",
                    "strategy_id": strategy.id,
                    "symbol": "MSFT",
                    "execute_date": "2024-01-03",
                    "description": "Sell signal",
                    "metadata": {"price": 300.0}
                }
            ]

            result = await import_service.import_from_json(json_data, user.id)
            assert result.success == 1, "JSON 导入失败"
            test_passed("JSON 数据导入")

            # 测试数据验证
            validation_result = await import_service.validate_import_data([
                {"type": "signal", "strategy_id": 1, "symbol": "TEST"}
            ])
            assert validation_result["is_valid"], "验证应该通过"
            test_passed("数据验证")

    except Exception as e:
        test_failed("数据导入服务", e)


async def test_ip_control():
    """测试 IP 访问控制"""
    print("\n🛡️ 测试 IP 访问控制...")

    try:
        from src.core.ip_control import IPAccessControl

        ip_control = IPAccessControl()

        # 测试 IP 格式验证
        assert ip_control.is_valid_ip("192.168.1.1"), "有效 IP 验证失败"
        assert ip_control.is_valid_ip("2001:db8::1"), "有效 IPv6 验证失败"
        assert not ip_control.is_valid_ip("invalid"), "无效 IP 应该验证失败"
        test_passed("IP 格式验证")

        # 测试网络段检查
        assert ip_control.is_in_network("192.168.1.10", "192.168.1.0/24"), "网络段检查失败"
        assert not ip_control.is_in_network("192.168.2.10", "192.168.1.0/24"), "网络段检查应该失败"
        test_passed("网络段检查")

    except Exception as e:
        test_failed("IP 访问控制", e)


async def test_cache_system():
    """测试缓存系统"""
    print("\n💾 测试缓存系统...")

    try:
        from src.core.cache import CacheManager

        cache = CacheManager.get_instance()

        # 测试缓存设置和获取
        cache.set("test_key", "test_value", ttl=60)
        value = cache.get("test_key")
        assert value == "test_value", "缓存值不匹配"
        test_passed("缓存设置和获取")

        # 测试缓存删除
        cache.delete("test_key")
        value = cache.get("test_key")
        assert value is None, "缓存应该被删除"
        test_passed("缓存删除")

        # 测试 LRU 淘汰
        for i in range(1100):  # 超过默认容量 1000
            cache.set(f"key_{i}", f"value_{i}")

        # 早期的键应该被淘汰
        assert cache.get("key_0") is None, "LRU 淘汰未生效"
        test_passed("LRU 缓存淘汰")

    except Exception as e:
        test_failed("缓存系统", e)


async def test_scheduler():
    """测试调度器"""
    print("\n⏰ 测试调度器...")

    try:
        from src.core.scheduler import scheduler

        task_executed = {"count": 0}

        def test_task():
            task_executed["count"] += 1

        # 添加任务
        scheduler.add_task(
            task_id="test_task",
            func=test_task,
            trigger="interval",
            seconds=1
        )

        # 检查任务状态
        status = scheduler.get_status()
        assert "test_task" in [task["id"] for task in status["tasks"]], "任务未添加"
        test_passed("调度器任务添加")

        # 移除任务
        scheduler.remove_task("test_task")
        status = scheduler.get_status()
        assert "test_task" not in [task["id"] for task in status["tasks"]], "任务未移除"
        test_passed("调度器任务移除")

    except Exception as e:
        test_failed("调度器", e)


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 开始综合功能测试")
    print("=" * 60)

    await test_security()
    await test_auth_service()
    await test_data_import_service()
    await test_ip_control()
    await test_cache_system()
    await test_scheduler()

    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"✅ 通过: {test_results['passed']}")
    print(f"❌ 失败: {test_results['failed']}")

    if test_results['failed'] > 0:
        print("\n失败详情:")
        for error in test_results['errors']:
            print(f"  - {error['test']}: {error['error']}")

    success_rate = (test_results['passed'] / (test_results['passed'] + test_results['failed']) * 100) if (test_results['passed'] + test_results['failed']) > 0 else 0
    print(f"\n成功率: {success_rate:.1f}%")

    if test_results['failed'] == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️ 有 {test_results['failed']} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
