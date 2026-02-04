# Signal Transceiver

一个运行在云端的订阅服务系统，提供数据收集和分发功能。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 功能特性

### 核心功能
- **RESTful API**: 提供完整的REST接口，支持数据上报和查询
- **WebSocket支持**: 实时数据推送，支持订阅模式
- **API Key认证**: 安全的密钥认证机制
- **权限管理**: 基于角色的访问控制(RBAC)
- **订阅服务**: 支持轮询和WebSocket两种订阅方式

### 监控与告警
- **Prometheus指标**: 提供标准的Prometheus监控端点
- **性能监控**: CPU、内存、磁盘使用率实时监控
- **告警系统**: 支持飞书、钉钉告警通知
- **系统仪表盘**: 可视化系统健康状态

### 数据管理
- **数据验证**: 可配置的数据验证规则
- **合规检查**: 数据质量、业务规则、安全合规检查
- **审计日志**: 完整的操作日志和访问记录
- **数据库备份**: 自动化备份与恢复

### 报告生成
- **PDF报告**: 生成专业的PDF格式报告
- **Excel报告**: 生成可编辑的Excel报告
- **定时任务**: 自动化报告生成与发送

### 缓存与性能
- **LRU缓存**: 高性能内存缓存层
- **数据库优化**: 异步ORM和连接池

## 技术栈

- **Python 3.11+**
- **FastAPI**: 高性能异步Web框架
- **SQLAlchemy 2.0**: 异步ORM
- **SQLite/MySQL**: 数据库支持
- **Pydantic**: 数据验证
- **Prometheus**: 监控指标
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

# 使用CLI工具
python -m src.cli server start --reload
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

## CLI 工具

提供命令行工具进行系统管理：

```bash
# 服务器管理
python -m src.cli server start --host 0.0.0.0 --port 8000
python -m src.cli server health --url http://localhost:8000

# 数据库管理
python -m src.cli db init
python -m src.cli db init-permissions

# 用户管理
python -m src.cli user create --username admin --email admin@example.com --admin
python -m src.cli user list

# 数据统计
python -m src.cli data stats

# 报告生成
python -m src.cli report generate --type data --format pdf
python -m src.cli report generate --type performance --format excel

# 系统监控
python -m src.cli monitor status
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

### 监控端点

```bash
# Prometheus 指标
curl http://localhost:8000/api/v1/monitor/metrics

# 系统仪表盘
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/monitor/dashboard

# 性能数据
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/monitor/performance?minutes=60

# 下载报告
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/monitor/report/data?format=pdf -o report.pdf
```

### 合规检查

```bash
# 数据验证
curl -X POST http://localhost:8000/api/v1/compliance/validate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "signal",
    "symbol": "AAPL",
    "execute_date": "2024-02-01",
    "strategy_id": "strategy_001"
  }'

# 合规检查
curl -X POST http://localhost:8000/api/v1/compliance/check \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "signal",
    "symbol": "AAPL"
  }'
```

### 系统管理 (需要管理员权限)

```bash
# 系统统计
curl -H "X-API-Key: admin-api-key" \
  http://localhost:8000/api/v1/admin/stats

# 审计日志
curl -H "X-API-Key: admin-api-key" \
  http://localhost:8000/api/v1/admin/audit-trail?days=7

# 备份数据库
curl -X POST -H "X-API-Key: admin-api-key" \
  http://localhost:8000/api/v1/admin/backups/create

# 查看备份列表
curl -H "X-API-Key: admin-api-key" \
  http://localhost:8000/api/v1/admin/backups

# 缓存管理
curl -H "X-API-Key: admin-api-key" \
  http://localhost:8000/api/v1/admin/cache/stats

curl -X POST -H "X-API-Key: admin-api-key" \
  http://localhost:8000/api/v1/admin/cache/clear

# 调度器控制
curl -X POST -H "X-API-Key: admin-api-key" \
  http://localhost:8000/api/v1/admin/scheduler/start

curl -H "X-API-Key: admin-api-key" \
  http://localhost:8000/api/v1/admin/scheduler/status
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
pytest --cov=src --cov-report=html --cov-report=term-missing

# 只运行特定测试
pytest tests/unit/test_security.py -v
pytest tests/unit/test_new_features.py -v
```

## 项目结构

```
signal-transceiver/
├── src/
│   ├── main.py              # 应用入口
│   ├── cli.py               # 命令行工具
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
│   │   │   ├── auth.py      # 认证API
│   │   │   ├── data.py      # 数据API
│   │   │   ├── subscription.py  # 订阅API
│   │   │   ├── client.py    # 客户端API
│   │   │   ├── strategy.py  # 策略API
│   │   │   ├── admin.py     # 管理API
│   │   │   ├── system.py    # 系统API
│   │   │   └── compliance.py # 合规API
│   │   └── websocket.py     # WebSocket
│   ├── services/            # 业务逻辑
│   │   ├── auth_service.py
│   │   ├── data_service.py
│   │   ├── subscription_service.py
│   │   ├── audit_service.py  # 审计服务
│   │   └── backup_service.py # 备份服务
│   ├── core/                # 核心组件
│   │   ├── security.py      # 安全工具
│   │   ├── dependencies.py  # 依赖注入
│   │   ├── exceptions.py    # 异常定义
│   │   ├── middleware.py    # 中间件
│   │   ├── scheduler.py     # 定时任务
│   │   ├── cache.py         # 缓存层
│   │   ├── validation.py    # 数据验证
│   │   ├── compliance.py    # 合规检查
│   │   └── resource_access.py # 资源权限
│   ├── monitor/             # 监控模块
│   │   ├── metrics.py       # Prometheus指标
│   │   ├── alerts.py        # 告警系统
│   │   ├── performance.py   # 性能监控
│   │   ├── dashboard.py     # 仪表盘
│   │   ├── feishu_enhanced.py # 飞书通知
│   │   └── dingtalk.py      # 钉钉通知
│   ├── report/              # 报告生成
│   │   └── generator.py     # PDF/Excel报告
│   ├── web/                 # Web模块
│   │   └── api.py           # 监控API
│   └── utils/               # 工具函数
├── tests/                   # 测试文件
│   ├── unit/                # 单元测试
│   │   ├── test_auth.py
│   │   ├── test_security.py
│   │   ├── test_exceptions.py
│   │   ├── test_new_features.py
│   │   └── test_backup.py
│   └── integration/         # 集成测试
│       └── test_api_flow.py
├── alembic/                 # 数据库迁移
├── docker/                  # Docker配置
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
├── .github/workflows/       # GitHub Actions
│   ├── ci.yml
│   └── release.yml
├── requirements.txt         # 依赖列表
└── README.md
```

## 数据库模型

| 模型 | 说明 |
|------|------|
| **User** | 用户信息和API密钥 |
| **Client** | 客户端应用信息 |
| **Strategy** | 策略配置 |
| **Data** | 上报的数据记录 |
| **Subscription** | 订阅信息 |
| **Permission** | 权限定义 |
| **Role** | 角色定义 |
| **Log** | 操作日志 |

## 定时任务

系统内置以下定时任务：

| 任务 | 执行周期 | 说明 |
|------|----------|------|
| cleanup_logs | 每24小时 | 清理7天以前的日志 |
| daily_report | 每24小时 | 生成并发送每日报告 |
| health_check | 每5分钟 | 检查系统状态，触发告警 |
| database_backup | 每6小时 | 自动备份SQLite数据库 |

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

### CI/CD 部署

项目已配置 GitHub Actions 工作流：

- **ci.yml**: 代码检查、测试、构建Docker镜像
- **release.yml**: 版本发布和镜像推送

### 安全建议

- 使用 HTTPS（配置 SSL 证书）
- 设置强密码和定期轮换 API Key
- 配置安全组只开放必要端口（80, 443, 8000）
- 启用阿里云 WAF 防护
- 使用 RAM 角色管理权限
- 配置阿里云 SLS 日志服务
- 设置云监控告警规则

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| SECRET_KEY | 加密密钥 | 必需 |
| ADMIN_API_KEY | 管理员API密钥 | 必需 |
| DATABASE_URL | 数据库连接URL | sqlite+aiosqlite:///./data/app.db |
| DEBUG | 调试模式 | false |
| LOG_LEVEL | 日志级别 | INFO |
| CORS_ORIGINS | CORS允许的源 | ["*"] |

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
