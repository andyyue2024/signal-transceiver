"""
演示场景：
- 用户A（数据提供者）：创建策略S，每日北京时间5:00上报数据
- 用户B（数据订阅者）：订阅策略S，每日北京时间5:01拉取数据

运行方式：
    python src/demo_run1.py

说明：
    此脚本会模拟整个流程，包括：
    1. 创建用户A和用户B
    2. 用户A创建策略
    3. 用户B订阅策略
    4. 模拟定时任务（用户A上报，用户B拉取）
"""
import asyncio
import sys
import os
import io
from datetime import datetime, timezone, timedelta
from typing import Optional

# 设置控制台输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)


def format_time(dt: datetime) -> str:
    """格式化时间显示"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class DemoScenario:
    """演示场景类"""

    def __init__(self):
        self.user_a = None  # 数据提供者
        self.user_b = None  # 数据订阅者
        self.strategy = None  # 策略
        self.subscription = None  # 订阅
        self.user_a_api_key = None
        self.user_b_api_key = None
        self.user_a_client_key = None
        self.user_a_client_secret = None
        self.user_b_client_key = None
        self.user_b_client_secret = None

    async def setup(self):
        """初始化数据库和创建演示数据"""
        from src.config.database import init_db, async_session_maker
        from src.models.user import User
        from src.models.strategy import Strategy
        from src.models.subscription import Subscription
        from src.core.security import (
            get_password_hash, generate_api_key, generate_client_credentials
        )
        from sqlalchemy import select

        print("\n" + "=" * 60)
        print("🚀 初始化演示环境")
        print("=" * 60)

        # 初始化数据库
        await init_db()
        print("✅ 数据库初始化完成")

        async with async_session_maker() as session:
            # ========================================
            # 1. 创建用户A（数据提供者）
            # ========================================
            print("\n📦 创建用户A（数据提供者）...")

            # 检查用户A是否存在
            result = await session.execute(
                select(User).where(User.username == "provider_a")
            )
            self.user_a = result.scalar_one_or_none()

            if not self.user_a:
                api_key_a, hashed_key_a = generate_api_key()
                client_key_a, client_secret_a, hashed_secret_a = generate_client_credentials()

                self.user_a = User(
                    username="provider_a",
                    email="provider_a@example.com",
                    hashed_password=get_password_hash("password123"),
                    api_key=hashed_key_a,
                    client_key=client_key_a,
                    client_secret=hashed_secret_a,
                    full_name="数据提供者A",
                    description="负责每日上报策略数据",
                    is_active=True,
                    is_admin=False
                )
                session.add(self.user_a)
                await session.flush()

                self.user_a_api_key = api_key_a
                self.user_a_client_key = client_key_a
                self.user_a_client_secret = client_secret_a

                print(f"   ✅ 用户A创建成功: {self.user_a.username}")
                print(f"   📧 邮箱: {self.user_a.email}")
                print(f"   🔑 Client Key: {client_key_a}")
            else:
                print(f"   ℹ️ 用户A已存在: {self.user_a.username}")
                # 为已存在用户生成新凭据用于演示
                api_key_a, hashed_key_a = generate_api_key()
                self.user_a.api_key = hashed_key_a
                self.user_a_api_key = api_key_a
                self.user_a_client_key = self.user_a.client_key
                self.user_a_client_secret = "（使用已有密钥）"

            # ========================================
            # 2. 创建用户B（数据订阅者）
            # ========================================
            print("\n📦 创建用户B（数据订阅者）...")

            result = await session.execute(
                select(User).where(User.username == "subscriber_b")
            )
            self.user_b = result.scalar_one_or_none()

            if not self.user_b:
                api_key_b, hashed_key_b = generate_api_key()
                client_key_b, client_secret_b, hashed_secret_b = generate_client_credentials()

                self.user_b = User(
                    username="subscriber_b",
                    email="subscriber_b@example.com",
                    hashed_password=get_password_hash("password123"),
                    api_key=hashed_key_b,
                    client_key=client_key_b,
                    client_secret=hashed_secret_b,
                    full_name="数据订阅者B",
                    description="订阅策略数据，每日拉取",
                    is_active=True,
                    is_admin=False
                )
                session.add(self.user_b)
                await session.flush()

                self.user_b_api_key = api_key_b
                self.user_b_client_key = client_key_b
                self.user_b_client_secret = client_secret_b

                print(f"   ✅ 用户B创建成功: {self.user_b.username}")
                print(f"   📧 邮箱: {self.user_b.email}")
                print(f"   🔑 Client Key: {client_key_b}")
            else:
                print(f"   ℹ️ 用户B已存在: {self.user_b.username}")
                api_key_b, hashed_key_b = generate_api_key()
                self.user_b.api_key = hashed_key_b
                self.user_b_api_key = api_key_b
                self.user_b_client_key = self.user_b.client_key
                self.user_b_client_secret = "（使用已有密钥）"

            # ========================================
            # 3. 用户A创建策略S
            # ========================================
            print("\n📊 用户A创建策略S...")

            result = await session.execute(
                select(Strategy).where(Strategy.strategy_id == "strategy_s_demo")
            )
            self.strategy = result.scalar_one_or_none()

            if not self.strategy:
                self.strategy = Strategy(
                    strategy_id="strategy_s_demo",
                    name="每日交易策略S",
                    description="用户A的每日交易信号策略，每天北京时间5:00发布",
                    type="trading",
                    category="daily",
                    config={
                        "update_time": "05:00",
                        "timezone": "Asia/Shanghai",
                        "frequency": "daily"
                    },
                    parameters={
                        "symbols": ["AAPL", "GOOGL", "MSFT"],
                        "signal_types": ["buy", "sell", "hold"]
                    },
                    is_active=True,
                    priority=10,
                    version="1.0.0"
                )
                session.add(self.strategy)
                await session.flush()
                print(f"   ✅ 策略创建成功: {self.strategy.name}")
            else:
                print(f"   ℹ️ 策略已存在: {self.strategy.name}")

            print(f"   📋 策略ID: {self.strategy.strategy_id}")
            print(f"   📝 描述: {self.strategy.description}")

            # ========================================
            # 4. 用户B订阅策略S
            # ========================================
            print("\n🔔 用户B订阅策略S...")

            result = await session.execute(
                select(Subscription).where(
                    Subscription.user_id == self.user_b.id,
                    Subscription.strategy_id == self.strategy.id
                )
            )
            self.subscription = result.scalar_one_or_none()

            if not self.subscription:
                self.subscription = Subscription(
                    name=f"订阅-{self.strategy.name}",
                    description=f"用户B订阅用户A的策略：{self.strategy.name}",
                    subscription_type="polling",  # 轮询方式
                    user_id=self.user_b.id,
                    strategy_id=self.strategy.id,
                    filters={
                        "symbols": ["AAPL", "GOOGL"],  # 只关注部分股票
                        "signal_types": ["buy", "sell"]  # 只关注买卖信号
                    },
                    webhook_url=None,  # 可设置webhook通知
                    notification_enabled=True,
                    is_active=True
                )
                session.add(self.subscription)
                await session.flush()
                print(f"   ✅ 订阅创建成功: {self.subscription.name}")
            else:
                print(f"   ℹ️ 订阅已存在: {self.subscription.name}")

            print(f"   📋 订阅类型: {self.subscription.subscription_type}")
            print(f"   🔍 过滤条件: {self.subscription.filters}")

            await session.commit()

        print("\n✅ 演示环境初始化完成！")

    async def user_a_report_data(self, execute_date: Optional[datetime] = None):
        """
        用户A上报数据
        模拟每日北京时间5:00执行
        """
        from src.config.database import async_session_maker
        from src.models.data import Data
        from sqlalchemy import select
        import random

        if execute_date is None:
            execute_date = beijing_now()

        print("\n" + "-" * 60)
        print(f"📤 [用户A] 上报数据 - 北京时间: {format_time(execute_date)}")
        print("-" * 60)

        async with async_session_maker() as session:
            # 模拟生成交易信号数据
            symbols = ["AAPL", "GOOGL", "MSFT"]
            signals = ["buy", "sell", "hold"]

            data_records = []
            for symbol in symbols:
                signal = random.choice(signals)
                confidence = round(random.uniform(0.6, 0.95), 2)

                data = Data(
                    type="trading_signal",
                    symbol=symbol,
                    execute_date=execute_date.date(),
                    description=f"{symbol} {signal.upper()} 信号 (置信度: {confidence})",
                    payload={
                        "signal": signal,
                        "confidence": confidence,
                        "price_target": round(random.uniform(100, 500), 2),
                        "stop_loss": round(random.uniform(90, 450), 2),
                    },
                    extra_metadata={
                        "generated_at": format_time(execute_date),
                        "model_version": "v2.1",
                        "provider": "provider_a"
                    },
                    source="strategy_s_demo",
                    strategy_id=self.strategy.id,
                    user_id=self.user_a.id,
                    status="published",
                    processed=False
                )
                data_records.append(data)
                session.add(data)

            await session.commit()

            print(f"   ✅ 成功上报 {len(data_records)} 条数据:")
            for record in data_records:
                print(f"      📊 {record.symbol}: {record.payload['signal'].upper()} "
                      f"(置信度: {record.payload['confidence']})")

            return data_records

    async def user_b_fetch_data(self, since_date: Optional[datetime] = None):
        """
        用户B拉取数据
        模拟每日北京时间5:01执行
        """
        from src.config.database import async_session_maker
        from src.models.data import Data
        from src.models.subscription import Subscription
        from sqlalchemy import select, and_

        fetch_time = beijing_now()
        if since_date is None:
            since_date = fetch_time - timedelta(days=1)

        print("\n" + "-" * 60)
        print(f"📥 [用户B] 拉取数据 - 北京时间: {format_time(fetch_time)}")
        print("-" * 60)

        async with async_session_maker() as session:
            # 获取订阅信息
            result = await session.execute(
                select(Subscription).where(Subscription.id == self.subscription.id)
            )
            subscription = result.scalar_one()

            # 构建查询 - 根据订阅的过滤条件
            query = select(Data).where(
                and_(
                    Data.strategy_id == subscription.strategy_id,
                    Data.status == "published",
                    Data.created_at >= since_date.replace(tzinfo=None)
                )
            )

            # 应用过滤条件
            filters = subscription.filters or {}

            result = await session.execute(query.order_by(Data.created_at.desc()))
            all_data = result.scalars().all()

            # 在Python中应用过滤（也可以在SQL中实现）
            filtered_data = []
            filter_symbols = filters.get("symbols", [])
            filter_signals = filters.get("signal_types", [])

            for data in all_data:
                # 符号过滤
                if filter_symbols and data.symbol not in filter_symbols:
                    continue
                # 信号类型过滤
                if filter_signals and data.payload:
                    if data.payload.get("signal") not in filter_signals:
                        continue
                filtered_data.append(data)

            # 更新订阅的最后拉取时间
            subscription.last_notified_at = fetch_time.replace(tzinfo=None)
            if filtered_data:
                subscription.last_data_id = filtered_data[0].id
            await session.commit()

            print(f"   📋 订阅: {subscription.name}")
            print(f"   🔍 过滤条件: symbols={filter_symbols}, signals={filter_signals}")
            print(f"   📊 获取到 {len(filtered_data)} 条数据 (过滤前: {len(all_data)} 条):")

            for data in filtered_data:
                signal = data.payload.get("signal", "unknown") if data.payload else "unknown"
                confidence = data.payload.get("confidence", 0) if data.payload else 0
                print(f"      📈 [{data.execute_date}] {data.symbol}: {signal.upper()} "
                      f"(置信度: {confidence})")

            return filtered_data

    async def simulate_daily_workflow(self, days: int = 3):
        """
        模拟多天的工作流程
        """
        print("\n" + "=" * 60)
        print("🔄 开始模拟每日工作流程")
        print("=" * 60)

        base_date = beijing_now().replace(hour=5, minute=0, second=0, microsecond=0)

        for day in range(days):
            current_date = base_date + timedelta(days=day)

            print(f"\n{'=' * 60}")
            print(f"📅 第 {day + 1} 天 - {current_date.strftime('%Y-%m-%d')}")
            print("=" * 60)

            # 5:00 - 用户A上报数据
            report_time = current_date
            print(f"\n⏰ 北京时间 05:00 - 用户A上报数据")
            await self.user_a_report_data(report_time)

            # 模拟1分钟延迟
            await asyncio.sleep(0.5)  # 实际演示中缩短等待时间

            # 5:01 - 用户B拉取数据
            fetch_time = current_date + timedelta(minutes=1)
            print(f"\n⏰ 北京时间 05:01 - 用户B拉取数据")
            await self.user_b_fetch_data(current_date - timedelta(hours=1))

            if day < days - 1:
                print("\n💤 等待下一天...")
                await asyncio.sleep(1)  # 演示中缩短等待

    async def show_summary(self):
        """显示演示摘要"""
        from src.config.database import async_session_maker
        from src.models.data import Data
        from src.models.subscription import Subscription
        from sqlalchemy import select, func

        print("\n" + "=" * 60)
        print("📊 演示摘要")
        print("=" * 60)

        async with async_session_maker() as session:
            # 统计用户A上报的数据
            result = await session.execute(
                select(func.count(Data.id)).where(Data.user_id == self.user_a.id)
            )
            user_a_data_count = result.scalar()

            # 统计策略S的数据
            result = await session.execute(
                select(func.count(Data.id)).where(Data.strategy_id == self.strategy.id)
            )
            strategy_data_count = result.scalar()

            # 获取订阅信息
            result = await session.execute(
                select(Subscription).where(Subscription.id == self.subscription.id)
            )
            subscription = result.scalar_one()

            print(f"""
┌─────────────────────────────────────────────────────────┐
│                      用户信息                            │
├─────────────────────────────────────────────────────────┤
│ 用户A (数据提供者)                                       │
│   - 用户名: {self.user_a.username:<20}                  │
│   - 上报数据总数: {user_a_data_count:<10}               │
│                                                         │
│ 用户B (数据订阅者)                                       │
│   - 用户名: {self.user_b.username:<20}                  │
│   - 订阅策略: {self.strategy.name:<20}                  │
├─────────────────────────────────────────────────────────┤
│                      策略信息                            │
├─────────────────────────────────────────────────────────┤
│ 策略S                                                   │
│   - 策略ID: {self.strategy.strategy_id:<20}             │
│   - 数据总数: {strategy_data_count:<10}                 │
├─────────────────────────────────────────────────────────┤
│                      订阅信息                            │
├─────────────────────────────────────────────────────────┤
│ 订阅详情                                                │
│   - 订阅类型: {subscription.subscription_type:<15}      │
│   - 最后拉取: {format_time(subscription.last_notified_at) if subscription.last_notified_at else 'N/A':<20}│
│   - 状态: {'活跃' if subscription.is_active else '停用':<10}│
└─────────────────────────────────────────────────────────┘
""")

    def print_credentials(self):
        """打印凭据信息"""
        print("\n" + "=" * 60)
        print("🔐 API 凭据信息（用于测试）")
        print("=" * 60)
        print(f"""
用户A (数据提供者):
  - API Key: {self.user_a_api_key}
  - Client Key: {self.user_a_client_key}
  - Client Secret: {self.user_a_client_secret}

用户B (数据订阅者):
  - API Key: {self.user_b_api_key}
  - Client Key: {self.user_b_client_key}
  - Client Secret: {self.user_b_client_secret}
""")


async def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Signal Transceiver - 演示场景                       ║
║                                                              ║
║  场景说明:                                                    ║
║  - 用户A: 数据提供者，每日北京时间 05:00 上报策略数据          ║
║  - 用户B: 数据订阅者，每日北京时间 05:01 拉取订阅数据          ║
╚══════════════════════════════════════════════════════════════╝
""")

    demo = DemoScenario()

    try:
        # 1. 初始化环境
        await demo.setup()

        # 2. 打印凭据
        demo.print_credentials()

        # 3. 模拟3天的工作流程
        await demo.simulate_daily_workflow(days=3)

        # 4. 显示摘要
        await demo.show_summary()

        print("\n" + "=" * 60)
        print("✅ 演示完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
