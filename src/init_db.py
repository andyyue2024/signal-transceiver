#!/usr/bin/env python
"""
数据库初始化脚本
创建初始化数据，覆盖所有数据表
"""
import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config.database import Base
from src.config.settings import settings
from src.core.security import (
    get_password_hash, generate_api_key, generate_client_credentials
)

# 导入所有模型
from src.models.user import User
from src.models.strategy import Strategy
from src.models.data import Data
from src.models.subscription import Subscription
from src.models.permission import Permission, Role, UserPermission
from src.models.log import Log


async def init_database():
    """初始化数据库和所有表的数据"""
    print("=" * 80)
    print("🚀 Signal Transceiver - 数据库初始化")
    print("=" * 80)

    # 创建数据库引擎
    engine = create_async_engine(settings.database_url, echo=False)

    # 创建所有表
    print("\n📋 创建数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        try:
            # ============================================
            # 1. 创建用户 (User)
            # ============================================
            print("\n👤 创建用户...")
            users = []

            # 管理员用户
            admin_api_key, admin_hashed_key = generate_api_key()
            admin_ck, admin_cs, admin_hashed_cs = generate_client_credentials()
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                api_key=admin_hashed_key,
                client_key=admin_ck,
                client_secret=admin_hashed_cs,
                is_active=True,
                is_admin=True,
                full_name="系统管理员",
                phone="13800000001",
                description="系统内置管理员账号",
                rate_limit=1000,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            users.append(admin)

            # 普通用户1 - 交易员
            user1_api_key, user1_hashed_key = generate_api_key()
            user1_ck, user1_cs, user1_hashed_cs = generate_client_credentials()
            user1 = User(
                username="trader1",
                email="trader1@example.com",
                hashed_password=get_password_hash("trader123"),
                api_key=user1_hashed_key,
                client_key=user1_ck,
                client_secret=user1_hashed_cs,
                is_active=True,
                is_admin=False,
                full_name="张三",
                phone="13800000002",
                description="量化交易员",
                webhook_url="https://webhook.example.com/trader1",
                rate_limit=100,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            users.append(user1)

            # 普通用户2 - 分析师
            user2_api_key, user2_hashed_key = generate_api_key()
            user2_ck, user2_cs, user2_hashed_cs = generate_client_credentials()
            user2 = User(
                username="analyst1",
                email="analyst1@example.com",
                hashed_password=get_password_hash("analyst123"),
                api_key=user2_hashed_key,
                client_key=user2_ck,
                client_secret=user2_hashed_cs,
                is_active=True,
                is_admin=False,
                full_name="李四",
                phone="13800000003",
                description="数据分析师",
                rate_limit=200,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            users.append(user2)

            # 普通用户3 - 订阅者
            user3_api_key, user3_hashed_key = generate_api_key()
            user3_ck, user3_cs, user3_hashed_cs = generate_client_credentials()
            user3 = User(
                username="subscriber1",
                email="subscriber1@example.com",
                hashed_password=get_password_hash("subscriber123"),
                api_key=user3_hashed_key,
                client_key=user3_ck,
                client_secret=user3_hashed_cs,
                is_active=True,
                is_admin=False,
                full_name="王五",
                phone="13800000004",
                description="信号订阅用户",
                rate_limit=50,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            users.append(user3)

            # 禁用用户
            user4_api_key, user4_hashed_key = generate_api_key()
            user4_ck, user4_cs, user4_hashed_cs = generate_client_credentials()
            user4 = User(
                username="disabled_user",
                email="disabled@example.com",
                hashed_password=get_password_hash("disabled123"),
                api_key=user4_hashed_key,
                client_key=user4_ck,
                client_secret=user4_hashed_cs,
                is_active=False,
                is_admin=False,
                full_name="已禁用用户",
                description="此账号已被禁用",
                rate_limit=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            users.append(user4)

            for user in users:
                session.add(user)
            await session.flush()
            print(f"✅ 创建了 {len(users)} 个用户")

            # ============================================
            # 2. 创建策略 (Strategy)
            # ============================================
            print("\n📊 创建策略...")
            strategies = [
                Strategy(
                    strategy_id="STR-TREND-001",
                    name="趋势跟踪策略",
                    description="基于移动平均线的趋势跟踪策略，适用于趋势明显的市场",
                    type="trend",
                    category="quantitative",
                    is_active=True,
                    config={"ma_period": 20, "threshold": 0.02},
                    version="1.0.0",
                    priority=10,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                Strategy(
                    strategy_id="STR-MEAN-002",
                    name="均值回归策略",
                    description="基于布林带的均值回归策略，适用于震荡市场",
                    type="mean_reversion",
                    category="quantitative",
                    is_active=True,
                    config={"bb_period": 20, "bb_std": 2},
                    version="1.0.0",
                    priority=8,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                Strategy(
                    strategy_id="STR-MOM-003",
                    name="动量策略",
                    description="基于RSI和MACD的动量策略",
                    type="momentum",
                    category="technical",
                    is_active=True,
                    config={"rsi_period": 14, "macd_fast": 12, "macd_slow": 26},
                    version="1.2.0",
                    priority=7,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                Strategy(
                    strategy_id="STR-ARB-004",
                    name="套利策略",
                    description="跨市场套利策略",
                    type="arbitrage",
                    category="quantitative",
                    is_active=True,
                    config={"spread_threshold": 0.005},
                    version="2.0.0",
                    priority=9,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                Strategy(
                    strategy_id="STR-TEST-005",
                    name="测试策略（已停用）",
                    description="用于测试的策略，当前已停用",
                    type="test",
                    category="development",
                    is_active=False,
                    config={"test_mode": True},
                    version="0.1.0",
                    priority=0,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
            ]

            for strategy in strategies:
                session.add(strategy)
            await session.flush()
            print(f"✅ 创建了 {len(strategies)} 个策略")

            # ============================================
            # 3. 创建数据记录 (Data)
            # ============================================
            print("\n📈 创建数据记录...")
            data_records = []
            symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "JPM"]
            data_types = ["signal", "alert", "notification", "report"]

            for i, symbol in enumerate(symbols):
                for j, dtype in enumerate(data_types[:2]):  # signal 和 alert
                    strategy = strategies[i % len(strategies)]
                    user = users[1 + (i % 3)]  # trader1, analyst1, subscriber1

                    data = Data(
                        type=dtype,
                        strategy_id=strategy.id,
                        symbol=symbol,
                        execute_date=datetime.now(timezone.utc).date() - timedelta(days=i),
                        description=f"{symbol} {dtype.upper()} - 策略: {strategy.name}",
                        extra_metadata={
                            "price": 100 + i * 10 + j,
                            "volume": 1000000 + i * 100000,
                            "action": "buy" if (i + j) % 2 == 0 else "sell",
                            "confidence": 0.8 + (i % 3) * 0.05
                        },
                        user_id=user.id,
                        created_at=datetime.now(timezone.utc) - timedelta(hours=i * 2),
                    )
                    data_records.append(data)

            # 添加一些最近的数据
            recent_data = [
                Data(
                    type="signal",
                    strategy_id=strategies[0].id,
                    symbol="BTC",
                    execute_date=datetime.now(timezone.utc).date(),
                    description="比特币买入信号",
                    extra_metadata={"price": 45000, "action": "buy", "confidence": 0.92},
                    user_id=user1.id,
                    created_at=datetime.now(timezone.utc),
                ),
                Data(
                    type="alert",
                    strategy_id=strategies[1].id,
                    symbol="ETH",
                    execute_date=datetime.now(timezone.utc).date(),
                    description="以太坊价格警报",
                    extra_metadata={"price": 2500, "threshold": 2400, "type": "above"},
                    user_id=user1.id,
                    created_at=datetime.now(timezone.utc),
                ),
                Data(
                    type="report",
                    strategy_id=strategies[2].id,
                    symbol="PORTFOLIO",
                    execute_date=datetime.now(timezone.utc).date(),
                    description="每日组合报告",
                    extra_metadata={"total_value": 1000000, "daily_pnl": 5000, "positions": 15},
                    user_id=user2.id,
                    created_at=datetime.now(timezone.utc),
                ),
            ]
            data_records.extend(recent_data)

            for data in data_records:
                session.add(data)
            await session.flush()
            print(f"✅ 创建了 {len(data_records)} 条数据记录")

            # ============================================
            # 4. 创建订阅 (Subscription)
            # ============================================
            print("\n📬 创建订阅...")
            subscriptions = [
                Subscription(
                    name="趋势信号订阅",
                    user_id=user3.id,
                    strategy_id=strategies[0].id,
                    subscription_type="polling",
                    filters={"symbols": ["AAPL", "GOOGL", "MSFT"]},
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                Subscription(
                    name="动量策略实时推送",
                    user_id=user3.id,
                    strategy_id=strategies[2].id,
                    subscription_type="websocket",
                    filters={"min_confidence": 0.8},
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                Subscription(
                    name="全策略订阅",
                    user_id=user2.id,
                    strategy_id=None,
                    subscription_type="webhook",
                    webhook_url="https://webhook.example.com/analyst1/all",
                    filters={},
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                Subscription(
                    name="套利信号订阅",
                    user_id=user1.id,
                    strategy_id=strategies[3].id,
                    subscription_type="polling",
                    filters={"data_type": "signal"},
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                Subscription(
                    name="已暂停订阅",
                    user_id=user3.id,
                    strategy_id=strategies[1].id,
                    subscription_type="polling",
                    filters={},
                    is_active=False,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
            ]

            for sub in subscriptions:
                session.add(sub)
            await session.flush()
            print(f"✅ 创建了 {len(subscriptions)} 个订阅")

            # ============================================
            # 5. 创建权限 (Permission)
            # ============================================
            print("\n🔐 创建权限...")
            permissions = [
                # 数据权限
                Permission(name="创建数据", code="data:create", description="创建数据", resource="data", action="create"),
                Permission(name="读取数据", code="data:read", description="读取数据", resource="data", action="read"),
                Permission(name="更新数据", code="data:update", description="更新数据", resource="data", action="update"),
                Permission(name="删除数据", code="data:delete", description="删除数据", resource="data", action="delete"),
                # 策略权限
                Permission(name="创建策略", code="strategy:create", description="创建策略", resource="strategy", action="create"),
                Permission(name="读取策略", code="strategy:read", description="读取策略", resource="strategy", action="read"),
                Permission(name="更新策略", code="strategy:update", description="更新策略", resource="strategy", action="update"),
                Permission(name="删除策略", code="strategy:delete", description="删除策略", resource="strategy", action="delete"),
                # 订阅权限
                Permission(name="创建订阅", code="subscription:create", description="创建订阅", resource="subscription", action="create"),
                Permission(name="读取订阅", code="subscription:read", description="读取订阅", resource="subscription", action="read"),
                Permission(name="更新订阅", code="subscription:update", description="更新订阅", resource="subscription", action="update"),
                Permission(name="删除订阅", code="subscription:delete", description="删除订阅", resource="subscription", action="delete"),
                # 用户权限
                Permission(name="创建用户", code="user:create", description="创建用户", resource="user", action="create"),
                Permission(name="读取用户", code="user:read", description="读取用户", resource="user", action="read"),
                Permission(name="更新用户", code="user:update", description="更新用户", resource="user", action="update"),
                Permission(name="删除用户", code="user:delete", description="删除用户", resource="user", action="delete"),
                # 系统权限
                Permission(name="系统管理", code="system:admin", description="系统管理", resource="system", action="admin"),
                Permission(name="系统备份", code="system:backup", description="系统备份", resource="system", action="backup"),
                Permission(name="查看日志", code="system:logs", description="查看日志", resource="system", action="logs"),
                Permission(name="系统配置", code="system:config", description="系统配置", resource="system", action="config"),
            ]

            for perm in permissions:
                session.add(perm)
            await session.flush()
            print(f"✅ 创建了 {len(permissions)} 个权限")

            # ============================================
            # 6. 创建角色 (Role)
            # ============================================
            print("\n👑 创建角色...")

            # 管理员角色 - 所有权限
            admin_role = Role(
                name="管理员",
                code="admin",
                description="系统管理员，拥有所有权限",
                level=100,
                is_active=True,
                is_default=False,
                created_at=datetime.now(timezone.utc)
            )
            admin_role.permissions = permissions  # 所有权限
            session.add(admin_role)

            # 交易员角色 - 数据和策略权限
            trader_perms = [p for p in permissions if p.resource in ("data", "strategy", "subscription")]
            trader_role = Role(
                name="交易员",
                code="trader",
                description="量化交易员，可管理数据和策略",
                level=50,
                is_active=True,
                is_default=False,
                created_at=datetime.now(timezone.utc)
            )
            trader_role.permissions = trader_perms
            session.add(trader_role)

            # 分析师角色 - 只读权限
            analyst_perms = [p for p in permissions if p.action == "read"]
            analyst_role = Role(
                name="分析师",
                code="analyst",
                description="数据分析师，只读权限",
                level=30,
                is_active=True,
                is_default=False,
                created_at=datetime.now(timezone.utc)
            )
            analyst_role.permissions = analyst_perms
            session.add(analyst_role)

            # 订阅者角色 - 订阅相关权限
            subscriber_perms = [p for p in permissions if p.resource in ("subscription", "data") and p.action in ("read", "create")]
            subscriber_role = Role(
                name="订阅者",
                code="subscriber",
                description="信号订阅用户",
                level=10,
                is_active=True,
                is_default=True,  # 默认角色
                created_at=datetime.now(timezone.utc)
            )
            subscriber_role.permissions = subscriber_perms
            session.add(subscriber_role)

            await session.flush()
            roles = [admin_role, trader_role, analyst_role, subscriber_role]
            print(f"✅ 创建了 {len(roles)} 个角色")

            # ============================================
            # 7. 创建用户角色关联 (UserPermission)
            # ============================================
            print("\n🔑 创建用户角色关联...")
            user_permissions = [
                # admin 用户 - 管理员角色
                UserPermission(
                    user_id=admin.id,
                    role_id=admin_role.id,
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                ),
                # trader1 - 交易员角色
                UserPermission(
                    user_id=user1.id,
                    role_id=trader_role.id,
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                ),
                # analyst1 - 分析师角色
                UserPermission(
                    user_id=user2.id,
                    role_id=analyst_role.id,
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                ),
                # subscriber1 - 订阅者角色
                UserPermission(
                    user_id=user3.id,
                    role_id=subscriber_role.id,
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                ),
                # disabled_user - 订阅者角色（但账号已禁用）
                UserPermission(
                    user_id=user4.id,
                    role_id=subscriber_role.id,
                    is_active=False,
                    created_at=datetime.now(timezone.utc)
                ),
            ]

            for up in user_permissions:
                session.add(up)
            await session.flush()
            print(f"✅ 创建了 {len(user_permissions)} 个用户角色关联")

            # ============================================
            # 8. 创建日志 (Log)
            # ============================================
            print("\n📝 创建日志...")
            logs = [
                Log(
                    log_type="operation",
                    action="system_start",
                    level="INFO",
                    message="系统启动",
                    resource="system",
                    user_id=None,
                    ip_address="127.0.0.1",
                    created_at=datetime.now(timezone.utc) - timedelta(hours=24)
                ),
                Log(
                    log_type="access",
                    action="login",
                    level="INFO",
                    message="管理员登录成功",
                    resource="auth",
                    user_id=admin.id,
                    ip_address="192.168.1.100",
                    details={"username": "admin", "method": "password"},
                    created_at=datetime.now(timezone.utc) - timedelta(hours=23)
                ),
                Log(
                    log_type="operation",
                    action="register",
                    level="INFO",
                    message="用户注册成功",
                    resource="user",
                    user_id=user1.id,
                    ip_address="192.168.1.101",
                    details={"username": "trader1"},
                    created_at=datetime.now(timezone.utc) - timedelta(hours=22)
                ),
                Log(
                    log_type="operation",
                    action="create",
                    level="INFO",
                    message="创建新策略: 趋势跟踪策略",
                    resource="strategy",
                    resource_id=strategies[0].id,
                    user_id=user1.id,
                    ip_address="192.168.1.101",
                    details={"strategy_name": "趋势跟踪策略"},
                    created_at=datetime.now(timezone.utc) - timedelta(hours=20)
                ),
                Log(
                    log_type="operation",
                    action="upload",
                    level="INFO",
                    message="数据上传成功",
                    resource="data",
                    user_id=user1.id,
                    ip_address="192.168.1.101",
                    details={"count": 10, "type": "signal"},
                    created_at=datetime.now(timezone.utc) - timedelta(hours=18)
                ),
                Log(
                    log_type="security",
                    action="rate_limit",
                    level="WARNING",
                    message="API 速率限制警告",
                    resource="rate_limiter",
                    user_id=user2.id,
                    ip_address="192.168.1.102",
                    details={"current_rate": 95, "limit": 100},
                    created_at=datetime.now(timezone.utc) - timedelta(hours=12)
                ),
                Log(
                    log_type="operation",
                    action="create",
                    level="INFO",
                    message="创建新订阅",
                    resource="subscription",
                    user_id=user3.id,
                    ip_address="192.168.1.103",
                    details={"subscription_name": "趋势信号订阅"},
                    created_at=datetime.now(timezone.utc) - timedelta(hours=10)
                ),
                Log(
                    log_type="error",
                    action="webhook_send",
                    level="ERROR",
                    message="Webhook 发送失败",
                    resource="webhook",
                    user_id=user1.id,
                    ip_address="192.168.1.101",
                    details={"url": "https://webhook.example.com/trader1", "error": "Connection timeout"},
                    created_at=datetime.now(timezone.utc) - timedelta(hours=6)
                ),
                Log(
                    log_type="operation",
                    action="backup",
                    level="INFO",
                    message="数据库备份完成",
                    resource="backup",
                    user_id=admin.id,
                    ip_address="127.0.0.1",
                    details={"file": "backup_20260204.db", "size": "15MB"},
                    created_at=datetime.now(timezone.utc) - timedelta(hours=3)
                ),
                Log(
                    log_type="operation",
                    action="health_check",
                    level="INFO",
                    message="系统健康检查通过",
                    resource="health",
                    user_id=None,
                    ip_address="127.0.0.1",
                    details={"cpu": 25, "memory": 45, "disk": 60},
                    created_at=datetime.now(timezone.utc) - timedelta(hours=1)
                ),
                Log(
                    log_type="access",
                    action="login",
                    level="INFO",
                    message="用户登录成功",
                    resource="auth",
                    user_id=user1.id,
                    ip_address="192.168.1.101",
                    details={"username": "trader1", "method": "api_key"},
                    created_at=datetime.now(timezone.utc)
                ),
            ]

            for log in logs:
                session.add(log)
            await session.flush()
            print(f"✅ 创建了 {len(logs)} 条日志")

            # 提交所有更改
            await session.commit()

            # ============================================
            # 输出汇总
            # ============================================
            print("\n" + "=" * 80)
            print("📊 初始化数据汇总")
            print("=" * 80)
            print(f"""
数据表                  | 记录数
------------------------|--------
用户 (User)             | {len(users)}
策略 (Strategy)         | {len(strategies)}
数据 (Data)             | {len(data_records)}
订阅 (Subscription)     | {len(subscriptions)}
权限 (Permission)       | {len(permissions)}
角色 (Role)             | {len(roles)}
用户角色 (UserPermission) | {len(user_permissions)}
日志 (Log)              | {len(logs)}
------------------------|--------
总计                    | {len(users) + len(strategies) + len(data_records) + len(subscriptions) + len(permissions) + len(roles) + len(user_permissions) + len(logs)}
""")

            print("=" * 80)
            print("👤 用户账号信息")
            print("=" * 80)
            print(f"""
用户名          | 密码         | 角色      | API Key (首次显示)
----------------|--------------|-----------|-------------------
admin           | admin123     | 管理员    | {admin_api_key[:30]}...
trader1         | trader123    | 交易员    | {user1_api_key[:30]}...
analyst1        | analyst123   | 分析师    | {user2_api_key[:30]}...
subscriber1     | subscriber123| 订阅者    | {user3_api_key[:30]}...
disabled_user   | disabled123  | 已禁用    | {user4_api_key[:30]}...
""")

            # 保存凭证到文件
            creds_file = os.path.join(os.path.dirname(__file__), ".", "init_credentials.txt")
            with open(creds_file, "w", encoding="utf-8") as f:
                f.write("Signal Transceiver - 初始化凭证\n")
                f.write("=" * 80 + "\n")
                f.write(f"生成时间: {datetime.now(timezone.utc).isoformat()}\n\n")
                f.write("用户凭证:\n")
                f.write("-" * 80 + "\n")
                f.write(f"admin:\n  密码: admin123\n  API Key: {admin_api_key}\n  Client Key: {admin_ck}\n  Client Secret: {admin_cs}\n\n")
                f.write(f"trader1:\n  密码: trader123\n  API Key: {user1_api_key}\n  Client Key: {user1_ck}\n  Client Secret: {user1_cs}\n\n")
                f.write(f"analyst1:\n  密码: analyst123\n  API Key: {user2_api_key}\n  Client Key: {user2_ck}\n  Client Secret: {user2_cs}\n\n")
                f.write(f"subscriber1:\n  密码: subscriber123\n  API Key: {user3_api_key}\n  Client Key: {user3_ck}\n  Client Secret: {user3_cs}\n\n")
                f.write(f"disabled_user:\n  密码: disabled123\n  API Key: {user4_api_key}\n  Client Key: {user4_ck}\n  Client Secret: {user4_cs}\n\n")
                f.write("\n⚠️ 警告: 请妥善保管此文件，并在生产环境中删除！\n")

            print(f"\n💾 凭证已保存到: {creds_file}")

            print("\n" + "=" * 80)
            print("🎉 数据库初始化完成！")
            print("=" * 80)
            print("""
✅ 可以使用以下命令启动应用:
   python src/main.py

✅ 访问管理后台:
   http://localhost:8000/admin/login
   用户名: admin
   密码: admin123

✅ API 文档:
   http://localhost:8000/docs
""")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(init_database())
    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        sys.exit(1)
