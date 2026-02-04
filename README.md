# Signal Transceiver

一个运行在云端的订阅服务系统，提供数据收集和分发功能。

## 功能特性

- **RESTful API**: 提供完整的REST接口，支持数据上报和查询
- **WebSocket支持**: 实时数据推送，支持订阅模式
- **API Key认证**: 安全的密钥认证机制
- **权限管理**: 基于角色的访问控制(RBAC)
- **订阅服务**: 支持轮询和WebSocket两种订阅方式
- **日志记录**: 完整的操作日志和访问日志

## 技术栈

- **Python 3.11+**
- **FastAPI**: 高性能异步Web框架
- **SQLAlchemy 2.0**: 异步ORM
- **SQLite/MySQL**: 数据库支持
- **Pydantic**: 数据验证
- **Loguru**: 日志管理
- **Docker**: 容器化部署

## 快速开始

### 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd signal-transceiver

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置

复制环境配置文件并修改：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置必要的配置项：

```env
SECRET_KEY=your-super-secret-key
ADMIN_API_KEY=your-admin-api-key
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
```

### 运行

```bash
# 开发模式
python -m src.main

# 或使用 uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看API文档。

### Docker 部署

```bash
# 构建镜像
docker build -t signal-transceiver -f docker/Dockerfile .

# 运行容器
docker run -d -p 8000:8000 --name signal-transceiver \
  -e SECRET_KEY=your-secret-key \
  -e ADMIN_API_KEY=your-admin-key \
  signal-transceiver

# 或使用 docker-compose
cd docker
docker-compose up -d
```

## API 使用指南

### 认证

系统支持两种认证方式：

1. **用户API Key**: 用于用户管理操作
   - 请求头: `X-API-Key: your-api-key`

2. **客户端凭证**: 用于数据上报和订阅
   - 请求头: `X-Client-Key: your-client-key`
   - 请求头: `X-Client-Secret: your-client-secret`

### 用户注册

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword"
  }'
```

### 创建客户端

```bash
curl -X POST http://localhost:8000/api/v1/clients \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Application",
    "description": "Test client"
  }'
```

### 上报数据

```bash
curl -X POST http://localhost:8000/api/v1/data \
  -H "X-Client-Key: your-client-key" \
  -H "X-Client-Secret: your-client-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "signal",
    "symbol": "AAPL",
    "execute_date": "2024-02-01",
    "strategy_id": "strategy_001",
    "description": "Buy signal"
  }'
```

### 创建订阅

```bash
curl -X POST http://localhost:8000/api/v1/subscriptions \
  -H "X-Client-Key: your-client-key" \
  -H "X-Client-Secret: your-client-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Subscription",
    "subscription_type": "polling",
    "strategy_id": "strategy_001"
  }'
```

### WebSocket 连接

```javascript
const ws = new WebSocket(
  'ws://localhost:8000/ws/subscribe?client_key=xxx&client_secret=xxx'
);

ws.onopen = () => {
  // 订阅
  ws.send(JSON.stringify({
    action: 'subscribe',
    subscription_id: 1
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit -v

# 运行集成测试
pytest tests/integration -v

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 项目结构

```
signal-transceiver/
├── src/
│   ├── main.py              # 应用入口
│   ├── config/              # 配置管理
│   │   ├── settings.py      # 应用设置
│   │   └── database.py      # 数据库配置
│   ├── models/              # ORM模型
│   │   ├── user.py          # 用户模型
│   │   ├── client.py        # 客户端模型
│   │   ├── data.py          # 数据模型
│   │   ├── strategy.py      # 策略模型
│   │   ├── subscription.py  # 订阅模型
│   │   ├── permission.py    # 权限模型
│   │   └── log.py           # 日志模型
│   ├── schemas/             # Pydantic模式
│   ├── api/                 # API路由
│   │   ├── v1/              # v1版本API
│   │   └── websocket.py     # WebSocket
│   ├── services/            # 业务逻辑
│   ├── core/                # 核心组件
│   │   ├── security.py      # 安全工具
│   │   ├── dependencies.py  # 依赖注入
│   │   ├── exceptions.py    # 异常定义
│   │   └── middleware.py    # 中间件
│   └── utils/               # 工具函数
├── tests/                   # 测试文件
│   ├── unit/                # 单元测试
│   └── integration/         # 集成测试
├── docker/                  # Docker配置
├── requirements.txt         # 依赖列表
└── README.md
```

## 数据库模型

- **User**: 用户信息和API密钥
- **Client**: 客户端应用信息
- **Strategy**: 策略配置
- **Data**: 上报的数据记录
- **Subscription**: 订阅信息
- **Permission/Role**: 权限和角色
- **Log**: 操作日志

## 部署到阿里云

### 使用 ECS

1. 创建 ECS 实例（推荐 2核4G 以上）
2. 安装 Docker 和 Docker Compose
3. 上传代码或克隆仓库
4. 配置环境变量
5. 运行 `docker-compose up -d`

### 使用容器服务 ACK

1. 创建 Kubernetes 集群
2. 构建并推送镜像到阿里云容器镜像服务
3. 部署 Deployment 和 Service
4. 配置 Ingress 和 HTTPS

### 安全建议

- 使用 HTTPS（配置 SSL 证书）
- 设置强密码和定期轮换 API Key
- 配置安全组只开放必要端口
- 启用阿里云 WAF 防护
- 使用 RAM 角色管理权限

## License

MIT License
