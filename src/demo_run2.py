"""
演示场景（API远程调用版）：
- 用户A（数据提供者）：创建策略S，每日北京时间5:00通过API远程上报数据
- 用户B（数据订阅者）：订阅策略S，每日北京时间5:01通过API远程拉取数据

运行方式：
    1. 首先启动服务器: python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
    2. 然后运行演示: python src/demo_run2.py

说明：
    此脚本通过 HTTP API 模拟远程调用流程
"""
import asyncio
import sys
import os
import io
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

# 设置控制台输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# API 基础配置
BASE_URL = "http://127.0.0.1:8000"
API_V1 = f"{BASE_URL}/api/v1"

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)


def format_time(dt: datetime) -> str:
    """格式化时间显示"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class APIClient:
    """API 客户端封装"""

    def __init__(self, base_url: str = API_V1):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.api_key: Optional[str] = None
        self.client_key: Optional[str] = None
        self.client_secret: Optional[str] = None

    async def close(self):
        await self.client.aclose()

    def set_credentials(self, api_key: str = None, client_key: str = None, client_secret: str = None):
        """设置认证凭据"""
        self.api_key = api_key
        self.client_key = client_key
        self.client_secret = client_secret

    def _get_headers(self, use_client_key: bool = False) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if use_client_key and self.client_key and self.client_secret:
            headers["X-Client-Key"] = self.client_key
            headers["X-Client-Secret"] = self.client_secret
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        try:
            response = await self.client.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "message": f"HTTP {response.status_code}: {response.text[:200]}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def register(self, username: str, email: str, password: str,
                      full_name: str = None) -> Dict[str, Any]:
        """用户注册"""
        data = {
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name
        }
        try:
            response = await self.client.post(
                f"{self.base_url}/auth/register",
                json=data
            )
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return {"success": False, "message": f"HTTP {response.status_code}: {response.text[:200]}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def create_strategy(self, strategy_id: str, name: str, description: str,
                             strategy_type: str = "trading", category: str = "daily",
                             config: Dict = None, parameters: Dict = None) -> Dict[str, Any]:
        """创建策略"""
        data = {
            "strategy_id": strategy_id,
            "name": name,
            "description": description,
            "type": strategy_type,
            "category": category,
            "config": config or {},
            "parameters": parameters or {},
            "is_active": True
        }
        try:
            response = await self.client.post(
                f"{self.base_url}/strategies",
                headers=self._get_headers(),
                json=data
            )
            if response.status_code in [200, 201]:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}: {response.text[:200]}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def get_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """获取策略"""
        try:
            response = await self.client.get(
                f"{self.base_url}/strategies/{strategy_id}",
                headers=self._get_headers()
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def list_strategies(self) -> Dict[str, Any]:
        """列出所有策略"""
        try:
            response = await self.client.get(
                f"{self.base_url}/strategies",
                headers=self._get_headers()
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def upload_data(self, data_type: str, symbol: str, execute_date: str,
                         description: str, payload: Dict, strategy_id: str,
                         metadata: Dict = None) -> Dict[str, Any]:
        """上报数据 (使用 Client Key 认证)"""
        data = {
            "type": data_type,
            "symbol": symbol,
            "execute_date": execute_date,
            "description": description,
            "payload": payload,
            "metadata": metadata or {},
            "strategy_id": strategy_id
        }
        try:
            response = await self.client.post(
                f"{self.base_url}/data",
                headers=self._get_headers(use_client_key=True),
                json=data
            )
            if response.status_code in [200, 201]:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}: {response.text[:200]}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def create_subscription(self, name: str, strategy_id: str,
                                  subscription_type: str = "polling",
                                  filters: Dict = None,
                                  description: str = None) -> Dict[str, Any]:
        """创建订阅"""
        data = {
            "name": name,
            "strategy_id": strategy_id,
            "subscription_type": subscription_type,
            "filters": filters or {},
            "description": description,
            "is_active": True
        }
        try:
            response = await self.client.post(
                f"{self.base_url}/subscriptions",
                headers=self._get_headers(use_client_key=True),
                json=data
            )
            if response.status_code in [200, 201]:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}: {response.text[:200]}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def get_subscription_data(self, subscription_id: int) -> Dict[str, Any]:
        """获取订阅数据 (拉取)"""
        try:
            response = await self.client.get(
                f"{self.base_url}/subscriptions/{subscription_id}/data",
                headers=self._get_headers(use_client_key=True)
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def poll_subscription(self, subscription_id: int,
                                since: str = None) -> Dict[str, Any]:
        """轮询订阅数据"""
        params = {}
        if since:
            params["since"] = since
        try:
            response = await self.client.get(
                f"{self.base_url}/subscriptions/{subscription_id}/poll",
                headers=self._get_headers(use_client_key=True),
                params=params
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def list_data(self, strategy_id: str = None,
                       since_date: str = None) -> Dict[str, Any]:
        """列出数据"""
        params = {}
        if strategy_id:
            params["strategy_id"] = strategy_id
        if since_date:
            params["since_date"] = since_date
        try:
            response = await self.client.get(
                f"{self.base_url}/data",
                headers=self._get_headers(use_client_key=True),
                params=params
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}


class RemoteDemoScenario:
    """远程 API 演示场景"""

    def __init__(self):
        self.admin_client = APIClient()  # 管理员客户端（用于创建策略）
        self.user_a_client = APIClient()  # 用户A客户端
        self.user_b_client = APIClient()  # 用户B客户端
        self.strategy_id = "strategy_s_remote"
        self.subscription_id: Optional[int] = None

        # 管理员凭据（从 admin_credentials.txt 获取或使用默认）
        self.admin_credentials = {
            "username": "admin",
            "password": "admin123"
        }

        # 用户凭据
        self.user_a_credentials = {
            "username": "remote_provider_a",
            "email": "remote_provider_a@example.com",
            "password": "password123",
            "full_name": "远程数据提供者A"
        }
        self.user_b_credentials = {
            "username": "remote_subscriber_b",
            "email": "remote_subscriber_b@example.com",
            "password": "password123",
            "full_name": "远程数据订阅者B"
        }

    async def check_server(self) -> bool:
        """检查服务器是否运行"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{BASE_URL}/health", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    print(f"   服务器状态: {data.get('status', 'unknown')}")
                    print(f"   版本: {data.get('version', 'unknown')}")
                    return True
        except Exception as e:
            print(f"   ❌ 无法连接服务器: {e}")
            return False
        return False

    async def setup_users(self):
        """设置用户（注册或登录）"""
        print("\n" + "=" * 60)
        print("👤 设置用户账号")
        print("=" * 60)

        # ========== 管理员登录 ==========
        print("\n📦 登录管理员账号（用于创建策略）...")
        result = await self.admin_client.login(
            self.admin_credentials["username"],
            self.admin_credentials["password"]
        )

        if result.get("success"):
            print(f"   ✅ 管理员登录成功")
            user_data = result.get("data", {})
            self.admin_client.set_credentials(
                api_key=user_data.get("api_key")
            )
        else:
            print(f"   ❌ 管理员登录失败: {result.get('message', result)}")
            print("   ℹ️ 请确保已运行 python src/init_db.py 初始化数据库")
            return False

        # ========== 用户A ==========
        print("\n📦 设置用户A（数据提供者）...")

        # 尝试登录
        result = await self.user_a_client.login(
            self.user_a_credentials["username"],
            self.user_a_credentials["password"]
        )

        if result.get("success"):
            print(f"   ✅ 用户A登录成功: {self.user_a_credentials['username']}")
            user_data = result.get("data", {})
            user_info = user_data.get("user", {})
            self.user_a_client.set_credentials(
                api_key=user_data.get("api_key"),
                client_key=user_info.get("client_key"),
                client_secret=user_info.get("client_secret")
            )
            print(f"   🔑 API Key: {user_data.get('api_key', 'N/A')[:30]}...")
        else:
            # 尝试注册
            print("   ℹ️ 用户A不存在，正在注册...")
            result = await self.user_a_client.register(
                self.user_a_credentials["username"],
                self.user_a_credentials["email"],
                self.user_a_credentials["password"],
                self.user_a_credentials["full_name"]
            )

            if result.get("success"):
                print(f"   ✅ 用户A注册成功")
                user_data = result.get("data", {})
                self.user_a_client.set_credentials(
                    api_key=user_data.get("api_key"),
                    client_key=user_data.get("client_key"),
                    client_secret=user_data.get("client_secret")
                )
                print(f"   🔑 API Key: {user_data.get('api_key', 'N/A')[:30]}...")
                print(f"   🔑 Client Key: {user_data.get('client_key', 'N/A')}")
            else:
                print(f"   ❌ 用户A注册失败: {result.get('message', result)}")
                return False

        # ========== 用户B ==========
        print("\n📦 设置用户B（数据订阅者）...")

        result = await self.user_b_client.login(
            self.user_b_credentials["username"],
            self.user_b_credentials["password"]
        )

        if result.get("success"):
            print(f"   ✅ 用户B登录成功: {self.user_b_credentials['username']}")
            user_data = result.get("data", {})
            user_info = user_data.get("user", {})
            self.user_b_client.set_credentials(
                api_key=user_data.get("api_key"),
                client_key=user_info.get("client_key"),
                client_secret=user_info.get("client_secret")
            )
            print(f"   🔑 API Key: {user_data.get('api_key', 'N/A')[:30]}...")
        else:
            print("   ℹ️ 用户B不存在，正在注册...")
            result = await self.user_b_client.register(
                self.user_b_credentials["username"],
                self.user_b_credentials["email"],
                self.user_b_credentials["password"],
                self.user_b_credentials["full_name"]
            )

            if result.get("success"):
                print(f"   ✅ 用户B注册成功")
                user_data = result.get("data", {})
                self.user_b_client.set_credentials(
                    api_key=user_data.get("api_key"),
                    client_key=user_data.get("client_key"),
                    client_secret=user_data.get("client_secret")
                )
                print(f"   🔑 API Key: {user_data.get('api_key', 'N/A')[:30]}...")
                print(f"   🔑 Client Key: {user_data.get('client_key', 'N/A')}")
            else:
                print(f"   ❌ 用户B注册失败: {result.get('message', result)}")
                return False

        return True

    async def setup_strategy(self):
        """管理员创建策略（创建策略需要管理员权限）"""
        print("\n" + "=" * 60)
        print("📊 管理员创建策略S")
        print("=" * 60)

        # 先检查策略是否存在
        result = await self.admin_client.get_strategy(self.strategy_id)

        if result.get("success"):
            print(f"   ℹ️ 策略已存在: {self.strategy_id}")
            return True

        # 使用管理员账号创建新策略
        result = await self.admin_client.create_strategy(
            strategy_id=self.strategy_id,
            name="远程每日交易策略S",
            description="用户A的远程策略，每天北京时间5:00通过API发布数据",
            strategy_type="trading",
            category="daily",
            config={
                "update_time": "05:00",
                "timezone": "Asia/Shanghai",
                "frequency": "daily",
                "delivery_method": "API"
            },
            parameters={
                "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
                "signal_types": ["buy", "sell", "hold"]
            }
        )

        if result.get("success"):
            print(f"   ✅ 策略创建成功: {self.strategy_id}")
            strategy_data = result.get("data", {})
            print(f"   📋 策略名称: {strategy_data.get('name', 'N/A')}")
            print(f"   📝 描述: {strategy_data.get('description', 'N/A')}")
            return True
        else:
            print(f"   ❌ 策略创建失败: {result.get('message', result)}")
            return False

    async def setup_subscription(self):
        """用户B订阅策略"""
        print("\n" + "=" * 60)
        print("🔔 用户B订阅策略S")
        print("=" * 60)

        result = await self.user_b_client.create_subscription(
            name=f"订阅-{self.strategy_id}",
            strategy_id=self.strategy_id,
            subscription_type="polling",
            filters={
                "symbols": ["AAPL", "GOOGL", "TSLA"],  # 只关注部分股票
                "signal_types": ["buy", "sell"]  # 只关注买卖信号
            },
            description="用户B通过API轮询获取策略数据"
        )

        if result.get("success"):
            sub_data = result.get("data", {})
            self.subscription_id = sub_data.get("id")
            print(f"   ✅ 订阅创建成功: ID={self.subscription_id}")
            print(f"   📋 订阅名称: {sub_data.get('name', 'N/A')}")
            print(f"   🔍 过滤条件: {sub_data.get('filters', {})}")
            return True
        else:
            # 可能已存在，尝试获取
            print(f"   ⚠️ 订阅创建返回: {result.get('message', result)}")
            # 假设订阅ID为1（实际应该从列表API获取）
            self.subscription_id = 1
            return True

    async def user_a_report_data(self, execute_date: datetime = None):
        """
        用户A通过API远程上报数据
        模拟每日北京时间5:00执行
        """
        import random

        if execute_date is None:
            execute_date = beijing_now()

        print("\n" + "-" * 60)
        print(f"📤 [用户A] 远程API上报数据")
        print(f"   ⏰ 北京时间: {format_time(execute_date)}")
        print(f"   🌐 API端点: POST {API_V1}/data/")
        print("-" * 60)

        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        signals = ["buy", "sell", "hold"]

        uploaded_count = 0
        for symbol in symbols:
            signal = random.choice(signals)
            confidence = round(random.uniform(0.6, 0.95), 2)

            result = await self.user_a_client.upload_data(
                data_type="trading_signal",
                symbol=symbol,
                execute_date=execute_date.strftime("%Y-%m-%d"),
                description=f"{symbol} {signal.upper()} 信号 (置信度: {confidence})",
                payload={
                    "signal": signal,
                    "confidence": confidence,
                    "price_target": round(random.uniform(100, 500), 2),
                    "stop_loss": round(random.uniform(90, 450), 2),
                    "timestamp": format_time(execute_date)
                },
                strategy_id=self.strategy_id,
                metadata={
                    "generated_at": format_time(execute_date),
                    "model_version": "v2.1",
                    "provider": "remote_provider_a",
                    "delivery_method": "HTTP_API"
                }
            )

            if result.get("success"):
                uploaded_count += 1
                print(f"   ✅ {symbol}: {signal.upper()} (置信度: {confidence})")
            else:
                print(f"   ❌ {symbol}: 上传失败 - {result.get('message', result)}")

        print(f"\n   📊 成功上报 {uploaded_count}/{len(symbols)} 条数据")
        return uploaded_count

    async def user_b_fetch_data(self, since_date: datetime = None):
        """
        用户B通过API远程拉取数据
        模拟每日北京时间5:01执行
        """
        fetch_time = beijing_now()

        print("\n" + "-" * 60)
        print(f"📥 [用户B] 远程API拉取数据")
        print(f"   ⏰ 北京时间: {format_time(fetch_time)}")
        print(f"   🌐 API端点: GET {API_V1}/subscriptions/{self.subscription_id}/poll")
        print("-" * 60)

        # 方式1: 通过订阅轮询
        if self.subscription_id:
            since_str = since_date.strftime("%Y-%m-%dT%H:%M:%S") if since_date else None
            result = await self.user_b_client.poll_subscription(
                self.subscription_id,
                since=since_str
            )

            if result.get("success"):
                data_list = result.get("data", [])
                print(f"   📋 订阅ID: {self.subscription_id}")
                print(f"   📊 获取到 {len(data_list)} 条数据:")

                for item in data_list:
                    symbol = item.get("symbol", "N/A")
                    payload = item.get("payload", {})
                    signal = payload.get("signal", "unknown")
                    confidence = payload.get("confidence", 0)
                    print(f"      📈 [{item.get('execute_date')}] {symbol}: "
                          f"{signal.upper()} (置信度: {confidence})")

                return data_list
            else:
                print(f"   ⚠️ 轮询返回: {result.get('message', result)}")

        # 方式2: 直接查询数据列表
        print("\n   🔄 尝试直接查询数据列表...")
        result = await self.user_b_client.list_data(
            strategy_id=self.strategy_id,
            since_date=since_date.strftime("%Y-%m-%d") if since_date else None
        )

        if result.get("success"):
            data_list = result.get("data", {}).get("items", [])
            print(f"   📊 查询到 {len(data_list)} 条数据:")

            for item in data_list[:5]:  # 只显示前5条
                symbol = item.get("symbol", "N/A")
                payload = item.get("payload", {})
                signal = payload.get("signal", "unknown") if payload else "unknown"
                confidence = payload.get("confidence", 0) if payload else 0
                print(f"      📈 [{item.get('execute_date')}] {symbol}: "
                      f"{signal.upper()} (置信度: {confidence})")

            if len(data_list) > 5:
                print(f"      ... 还有 {len(data_list) - 5} 条数据")

            return data_list
        else:
            print(f"   ❌ 查询失败: {result.get('message', result)}")
            return []

    async def simulate_daily_workflow(self, days: int = 3):
        """模拟多天的远程API工作流程"""
        print("\n" + "=" * 60)
        print("🔄 开始模拟每日远程API工作流程")
        print("=" * 60)

        base_date = beijing_now().replace(hour=5, minute=0, second=0, microsecond=0)

        for day in range(days):
            current_date = base_date + timedelta(days=day)

            print(f"\n{'=' * 60}")
            print(f"📅 第 {day + 1} 天 - {current_date.strftime('%Y-%m-%d')}")
            print("=" * 60)

            # 5:00 - 用户A通过API上报数据
            print(f"\n⏰ 模拟北京时间 05:00 - 用户A远程上报数据")
            await self.user_a_report_data(current_date)

            # 模拟1分钟延迟
            await asyncio.sleep(1)

            # 5:01 - 用户B通过API拉取数据
            print(f"\n⏰ 模拟北京时间 05:01 - 用户B远程拉取数据")
            await self.user_b_fetch_data(current_date - timedelta(hours=1))

            if day < days - 1:
                print("\n💤 等待下一天模拟...")
                await asyncio.sleep(2)

    async def show_api_examples(self):
        """显示API调用示例"""
        print("\n" + "=" * 60)
        print("📚 API 调用示例 (cURL)")
        print("=" * 60)

        print(f"""
┌─────────────────────────────────────────────────────────────┐
│                    1. 用户登录                               │
└─────────────────────────────────────────────────────────────┘
curl -X POST "{API_V1}/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{{"username": "provider_a", "password": "password123"}}'

┌─────────────────────────────────────────────────────────────┐
│                    2. 上报数据 (用户A)                        │
└─────────────────────────────────────────────────────────────┘
curl -X POST "{API_V1}/data/" \\
  -H "Content-Type: application/json" \\
  -H "X-Client-Key: YOUR_CLIENT_KEY" \\
  -H "X-Client-Secret: YOUR_CLIENT_SECRET" \\
  -d '{{
    "type": "trading_signal",
    "symbol": "AAPL",
    "execute_date": "2026-02-05",
    "description": "AAPL BUY signal",
    "payload": {{"signal": "buy", "confidence": 0.85}},
    "strategy_id": "{self.strategy_id}"
  }}'

┌─────────────────────────────────────────────────────────────┐
│                    3. 创建订阅 (用户B)                        │
└─────────────────────────────────────────────────────────────┘
curl -X POST "{API_V1}/subscriptions/" \\
  -H "Content-Type: application/json" \\
  -H "X-Client-Key: YOUR_CLIENT_KEY" \\
  -H "X-Client-Secret: YOUR_CLIENT_SECRET" \\
  -d '{{
    "name": "My Subscription",
    "strategy_id": "{self.strategy_id}",
    "subscription_type": "polling",
    "filters": {{"symbols": ["AAPL", "GOOGL"]}}
  }}'

┌─────────────────────────────────────────────────────────────┐
│                    4. 拉取数据 (用户B)                        │
└─────────────────────────────────────────────────────────────┘
curl -X GET "{API_V1}/subscriptions/1/poll?since=2026-02-05T00:00:00" \\
  -H "X-Client-Key: YOUR_CLIENT_KEY" \\
  -H "X-Client-Secret: YOUR_CLIENT_SECRET"

# 或直接查询数据列表
curl -X GET "{API_V1}/data/?strategy_id={self.strategy_id}" \\
  -H "X-Client-Key: YOUR_CLIENT_KEY" \\
  -H "X-Client-Secret: YOUR_CLIENT_SECRET"
""")

    async def cleanup(self):
        """清理资源"""
        await self.admin_client.close()
        await self.user_a_client.close()
        await self.user_b_client.close()


async def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║         Signal Transceiver - 远程 API 演示场景                    ║
║                                                                  ║
║  场景说明:                                                        ║
║  - 用户A: 数据提供者，每日北京时间 05:00 通过 API 远程上报数据      ║
║  - 用户B: 数据订阅者，每日北京时间 05:01 通过 API 远程拉取数据      ║
║                                                                  ║
║  前置条件: 服务器必须正在运行                                       ║
║  启动命令: uvicorn src.main:app --host 0.0.0.0 --port 8000       ║
╚══════════════════════════════════════════════════════════════════╝
""")

    demo = RemoteDemoScenario()

    try:
        # 1. 检查服务器
        print("\n" + "=" * 60)
        print("🔍 检查服务器状态")
        print("=" * 60)

        if not await demo.check_server():
            print("\n" + "=" * 60)
            print("❌ 服务器未运行！请先启动服务器:")
            print("   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000")
            print("=" * 60)
            return 1

        print("   ✅ 服务器运行正常")

        # 2. 设置用户
        if not await demo.setup_users():
            print("❌ 用户设置失败")
            return 1

        # 3. 创建策略
        if not await demo.setup_strategy():
            print("❌ 策略创建失败")
            return 1

        # 4. 创建订阅
        if not await demo.setup_subscription():
            print("❌ 订阅创建失败")
            return 1

        # 5. 模拟3天的工作流程
        await demo.simulate_daily_workflow(days=3)

        # 6. 显示API调用示例
        await demo.show_api_examples()

        print("\n" + "=" * 60)
        print("✅ 远程API演示完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await demo.cleanup()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
