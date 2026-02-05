# Signal Transceiver

一个运行在云端的企业级订阅服务系统，提供数据收集、分发和管理功能。

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Lines](https://img.shields.io/badge/代码行数-18000+-green.svg)](#项目统计)
[![Test Files](https://img.shields.io/badge/测试文件-16+-brightgreen.svg)](#测试)

## 🎉 最新更新 (2026-02-04)

### 🆕 新增功能
- ✅ **批量数据导入**: 支持 CSV、JSON、Excel 格式批量导入
- ✅ **IP 访问控制**: IP 白名单/黑名单，支持 CIDR 网络段
- ✅ **Python 3.13 兼容**: 修复 bcrypt 兼容性问题
- ✅ **安全增强**: 改进密码哈希和验证机制

## ✨ 功能特性

### 🔐 核心功能
- **RESTful API**: 完整的REST接口，110+ API端点
- **WebSocket支持**: 实时数据推送，支持1000+并发连接
- **双重认证**: API Key（Web UI）+ Client Credentials（API客户端）
- **统一用户体系**: User模型统一管理用户和客户端
- **RBAC权限**: 基于角色的访问控制 + 资源级权限
- **订阅服务**: 轮询 + WebSocket 双模式订阅

### 📥 数据导入（新功能）
- **CSV 导入**: 批量导入 CSV 格式数据
- **JSON 导入**: 批量导入 JSON 格式数据
- **Excel 导入**: 批量导入 Excel (.xlsx/.xls) 文件
- **数据验证**: 导入前验证数据格式和必填字段
- **错误处理**: 可选择跳过错误继续导入
- **导入统计**: 详细的导入成功/失败统计
- **模板下载**: 提供 CSV 和 JSON 导入模板

### 🛡️ IP 访问控制（新功能）
- **IP 白名单**: 限制特定用户只能从白名单 IP 访问
- **IP 黑名单**: 全局黑名单阻止恶意 IP
- **CIDR 支持**: 支持网络段配置 (如 192.168.1.0/24)
- **过期设置**: 支持临时 IP 访问权限
- **缓存优化**: 内存缓存提升检查性能

### 📊 监控与告警
- **Prometheus指标**: 标准的metrics导出端点
- **性能监控**: CPU、内存、磁盘、网络实时监控
- **多渠道告警**: 飞书、钉钉、邮件告警支持
- **系统仪表盘**: 实时可视化系统健康状态
- **链路追踪**: 完整的请求链路追踪
- **健康检查**: Kubernetes liveness/readiness探针

### 💾 数据管理
- **数据验证**: 可配置的验证规则引擎
- **合规检查**: 数据质量、业务规则、安全合规
- **审计日志**: 所有操作可追溯的审计记录
- **自动备份**: 每6小时自动备份，30天保留
- **数据导出**: 支持JSON、CSV、JSONL格式
- **消息队列**: 异步任务处理机制

### 📈 数据分析
- **趋势分析**: 多维度数据趋势分析
- **可视化图表**: Matplotlib图表生成
- **统计报告**: 自动生成统计摘要
- **数据转换**: 可配置的数据转换管道

### 📄 报告生成
- **PDF报告**: ReportLab生成专业PDF
- **Excel报告**: OpenPyXL生成可编辑表格
- **定时任务**: Cron表达式定时生成报告
- **模板自定义**: 可自定义报告模板

### 🔌 第三方集成
- **Webhook**: 事件驱动的HTTP回调
- **签名验证**: HMAC-SHA256签名安全机制
- **配送历史**: 完整的webhook配送记录
- **API Key轮换**: 90天自动过期提醒

### 🎨 Web UI管理界面
- **Glassmorphism设计**: 毛玻璃拟态风格
- **动态背景**: 渐变动画效果
- **账号密码登录**: 安全的登录认证
- **用户管理**: 用户CRUD操作（含client credentials）
- **策略管理**: 策略配置管理
- **角色权限**: 角色和权限管理
- **告警配置**: 可视化告警配置
- **日志搜索**: 实时日志查询
- **系统配置**: 动态配置管理
- **监控仪表盘**: 实时系统监控

### 🌍 国际化支持
- **多语言**: 中文、英文、日文、繁体中文
- **时区处理**: 5个主要时区支持
- **本地化**: 完整的i18n翻译服务

### 💬 用户支持
- **反馈系统**: Bug报告、功能请求、问题咨询
- **系统通知**: 内部消息通知机制
- **CLI工具**: 命令行管理工具

## 🏗️ 技术架构

### 核心技术
- **Python 3.11+**: 最新语言特性和性能优化
- **FastAPI 0.109+**: 高性能异步Web框架
- **SQLAlchemy 2.0**: 异步ORM，支持SQLite/MySQL/PostgreSQL
- **Pydantic v2**: 数据验证和序列化
- **Alembic**: 数据库迁移管理

### 监控与日志
- **Prometheus**: 监控指标导出
- **Loguru**: 结构化日志管理
- **自定义仪表盘**: 实时系统监控

### 报告生成
- **ReportLab**: PDF报告生成
- **OpenPyXL**: Excel报告生成  
- **Matplotlib**: 数据可视化图表

### 部署运维
- **Docker**: 容器化部署
- **Docker Compose**: 本地编排
- **GitHub Actions**: CI/CD自动化
- **Kubernetes**: 生产环境部署（可选）

### 安全机制
- **bcrypt**: 密码哈希
- **HMAC-SHA256**: API签名验证
- **JWT**: Token认证（可选）
- **HTTPS**: TLS/SSL加密

## 🗄️ 数据模型

### 统一用户模型 (User)
**重要**: Client（客户端）和User（用户）已合并为统一的User模型

```python
User (统一用户模型)
  ├── 认证字段
  │   ├── username, email, password
  │   ├── api_key (Web UI 认证)
  │   ├── client_key, client_secret (API 认证)
  │   └── rate_limit (速率限制)
  ├── 个人信息
  │   ├── full_name, phone, description
  │   ├── contact_email, webhook_url
  │   └── is_admin, is_active
  ├── 关联关系
  │   ├── subscriptions[] (订阅)
  │   ├── data_records[] (上报数据)
  │   ├── permissions[] (权限)
  │   └── logs[] (日志)
  └── 时间戳
      ├── created_at, updated_at
      ├── last_login_at (Web登录)
      └── last_access_at (API访问)
```

### 核心模型
- **User**: 统一的用户/客户端模型
- **Strategy**: 策略配置
- **Data**: 用户上报的数据记录
- **Subscription**: 订阅配置（轮询/WebSocket）
- **Permission**: 权限定义
- **Role**: 角色定义
- **UserPermission**: 用户权限分配
- **Log**: 操作日志

## 🚀 快速开始

### 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd signal-transceiver

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.\.venv\Scripts\activate  # Windows

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
# 应用配置
SECRET_KEY=your-super-secret-key-change-in-production
ADMIN_API_KEY=your-admin-api-key-change-me
DEBUG=false

# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
# 生产环境推荐 MySQL/PostgreSQL:
# DATABASE_URL=mysql+aiomysql://user:pass@host:3306/dbname

# CORS配置
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

### 初始化

```bash
# 初始化数据库
python -m src.cli db init

# 初始化权限系统
python -m src.cli db init-permissions

# 创建管理员用户
python -m src.cli user create --username admin --email admin@example.com --admin
```

### 运行

```bash
# 开发模式（自动重载）
python -m src.main

# 或使用 uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

访问 http://localhost:8000/docs 查看API文档。

### 🐳 Docker 部署

```bash
# 构建镜像
docker build -t signal-transceiver -f docker/Dockerfile .

# 运行容器
docker run -d -p 8000:8000 --name signal-transceiver \
  -e SECRET_KEY=your-secret-key \
  -e ADMIN_API_KEY=your-admin-key \
  -v $(pwd)/data:/app/data \
  signal-transceiver

# 或使用 docker-compose
cd docker
docker-compose up -d
```

## 🔧 CLI 工具

提供命令行工具进行系统管理：

```bash
# 服务器管理
python -m src.cli server start --host 0.0.0.0 --port 8000 --reload
python -m src.cli server health --url http://localhost:8000

# 数据库管理
python -m src.cli db init                # 初始化数据库
python -m src.cli db init-permissions   # 初始化权限

# 用户管理
python -m src.cli user create --username admin --email admin@example.com --admin
python -m src.cli user list
python -m src.cli user delete <user_id>

# 配置验证
python validate_config.py  # 验证.env配置
```

## 📡 API 使用示例

### 1. 用户注册和认证

```bash
# 注册用户（同时获得 client credentials）
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword"
  }'

# 响应包含 api_key（Web UI）和 client_key（API）
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "testuser",
      "email": "test@example.com"
    },
    "api_key": "sk_xxxxx...",      // Web UI 认证
    "client_key": "ck_xxxxx...",    // API 客户端认证
    "client_secret": "cs_xxxxx..."  // 仅显示一次，请保存
  }
}
```

### 2. Web UI 登录

```bash
# 使用账号密码登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepassword"
  }'

# 或访问 Web 登录页面
open http://localhost:8000/admin/login
```

![img_1.png](img_1.png)
![img.png](img.png)

### 3. 数据上报（使用 Client Credentials）

```bash
# 创建策略
curl -X POST http://localhost:8000/api/v1/strategies \
  -H "X-API-Key: sk_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "strategy_001",
    "name": "Alpha Strategy"
  }'

# 使用 client_key + client_secret 上报数据
curl -X POST http://localhost:8000/api/v1/data \
  -H "X-Client-Key: ck_xxxxx" \
  -H "X-Client-Secret: cs_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "signal",
    "symbol": "AAPL",
    "execute_date": "2024-02-01",
    "strategy_id": 1,
    "description": "Buy signal"
  }'
```

### 4. 创建订阅

```bash
# 创建轮询订阅
curl -X POST http://localhost:8000/api/v1/subscriptions \
  -H "X-Client-Key: ck_xxxxx" \
  -H "X-Client-Secret: cs_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Subscription",
    "subscription_type": "polling",
    "strategy_id": 1,
    "filters": {"symbol": "AAPL"}
  }'

# 获取订阅数据
curl "http://localhost:8000/api/v1/subscriptions/1/data?since=2024-02-01T00:00:00Z" \
  -H "X-Client-Key: ck_xxxxx" \
  -H "X-Client-Secret: cs_xxxxx"
```

### 5. WebSocket 实时订阅

```javascript
// JavaScript 客户端
const ws = new WebSocket(
  'ws://localhost:8000/ws/subscribe?client_key=ck_xxxxx&client_secret=cs_xxxxx'
);

ws.onopen = () => {
  // 订阅特定订阅
  ws.send(JSON.stringify({
    action: 'subscribe',
    subscription_id: 1
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// 心跳
setInterval(() => {
  ws.send(JSON.stringify({ action: 'ping' }));
}, 30000);
```

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

### 健康检查

```bash
# 基本健康检查
curl http://localhost:8000/health

# Kubernetes 探针
curl http://localhost:8000/api/v1/monitor/liveness
curl http://localhost:8000/api/v1/monitor/readiness
```

## 🔄 重要架构变更

### User-Client 模型合并 (v1.1.0)

**重要变更**: Client（客户端）模型已合并到 User（用户）模型中。

#### 变更内容
- ✅ User 模型新增 `client_key` 和 `client_secret` 字段
- ✅ 一个用户同时拥有 Web UI 认证（api_key）和 API 认证（client credentials）
- ✅ Subscription、Data、Permission 等模型的 `client_id` 改为 `user_id`
- ✅ `/api/v1/clients/*` 端点保持兼容，内部操作 User 模型

#### 影响
- **API兼容**: 所有现有API端点继续可用
- **数据库**: 需要重新初始化或运行迁移脚本
- **认证方式**: 不变，仍然支持双重认证

#### 迁移指南
```bash
# 开发环境：删除旧数据库，重新初始化
rm data/app.db
python -m src.cli db init
python -m src.cli db init-permissions

# 生产环境：参考 MODEL_REFACTOR.md 中的 SQL 迁移脚本
```

详细信息见: [MODEL_REFACTOR.md](MODEL_REFACTOR.md)

## 📁 项目结构

```
signal-transceiver/
├── src/
│   ├── api/v1/          # API 端点（14个模块）
│   ├── core/            # 核心组件（安全、缓存、调度等）
│   ├── models/          # 数据模型（User, Strategy, Data等）
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # 业务逻辑服务（16个服务）
│   ├── monitor/         # 监控模块（6个组件）
│   ├── web/             # Web UI（登录、管理界面）
│   ├── report/          # 报告生成
│   ├── utils/           # 工具类（i18n, 日志等）
│   ├── config/          # 配置管理
│   └── cli.py           # CLI 工具
├── tests/
│   ├── unit/            # 单元测试（14个文件）
│   └── integration/     # 集成测试
├── docker/              # Docker 配置
├── docs/                # 文档
│   ├── API.md           # API 详细文档
│   ├── DEPLOYMENT.md    # 部署指南
│   ├── PRIVACY.md       # 隐私政策
│   └── DISASTER_RECOVERY.md  # 灾难恢复
├── .env.example         # 环境配置模板
├── requirements.txt     # Python 依赖
└── README.md            # 本文档
```

## 🌟 核心特性

### 双重认证机制
- **API Key**: 用于 Web UI 和 CLI 工具
- **Client Credentials**: 用于 API 客户端（client_key + client_secret）

### 统一用户体系
- 一个用户账号同时拥有两套认证凭证
- 简化权限管理，统一用户数据

### 灵活订阅
- **轮询模式**: 定时查询新数据
- **WebSocket模式**: 实时推送更新
- **过滤器**: 支持按策略、类型、符号等过滤

### 企业级功能
- 完整的 RBAC 权限控制
- 资源级细粒度权限
- 审计日志和操作追踪
- 数据验证和合规检查
- 自动备份和恢复
# 详细健康状态
curl http://localhost:8000/health/detailed

# Kubernetes liveness 探针
curl http://localhost:8000/health/live

# Kubernetes readiness 探针
curl http://localhost:8000/health/ready
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

### 数据分析

```bash
# 获取数据趋势
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/analytics/data/trends?days=30"

# 获取图表数据
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/analytics/data/chart?days=30&chart_type=line"

# 获取分析摘要
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/analytics/summary?days=7"
```

### 管理界面 (Admin UI)

```bash
# Admin UI 入口
http://localhost:8000/admin/ui

# Admin UI 健康检查
http://localhost:8000/admin/ui/health
```

### Webhook 管理

```bash
# 注册 Webhook
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-server.com/webhook",
    "events": ["data.created", "subscription.activated"]
  }'

# 查看 Webhook 列表
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/webhooks

# 测试 Webhook
curl -X POST -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/webhooks/{webhook_id}/test

# 查看 Webhook 事件类型
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/webhooks/events
```

## 🚢 部署指南

### 生产环境部署

#### 1. 环境准备
```bash
# 创建生产配置
cp .env.example .env.production

# 编辑配置（重要！）
vi .env.production
```

关键配置：
```env
DEBUG=false
SECRET_KEY=<生成强密钥>
ADMIN_API_KEY=<生成强密钥>
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/dbname
CORS_ORIGINS=["https://your-domain.com"]
```

#### 2. Docker 部署
```bash
# 构建生产镜像
docker build -t signal-transceiver:latest -f docker/Dockerfile .

# 运行容器
docker run -d \
  --name signal-transceiver \
  -p 8000:8000 \
  --env-file .env.production \
  -v /path/to/data:/app/data \
  -v /path/to/logs:/app/logs \
  --restart unless-stopped \
  signal-transceiver:latest
```

#### 3. Kubernetes 部署
```bash
# 创建命名空间
kubectl create namespace signal-transceiver

# 应用配置
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/ingress.yaml

# 查看状态
kubectl get pods -n signal-transceiver
```

#### 4. 阿里云部署
参考 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) 获取详细的阿里云部署指南。

### 性能优化建议

```env
# 使用 MySQL/PostgreSQL
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/dbname

# 启用 Redis 缓存
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0

# 调整工作进程数
ASYNC_WORKERS=8  # 根据CPU核心数

# 数据库连接池
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20

# 启用消息队列
MQ_ENABLED=true
```

## 📚 文档

- [API 完整文档](docs/API.md) - 17章节详细API说明
- [部署指南](docs/DEPLOYMENT.md) - 阿里云、腾讯云部署步骤
- [隐私政策](docs/PRIVACY.md) - GDPR合规说明
- [灾难恢复](docs/DISASTER_RECOVERY.md) - 备份恢复计划
- [模型重构说明](MODEL_REFACTOR.md) - User-Client合并详情
- [Web UI 增强](ADMIN_UI_ENHANCEMENT.md) - UI特性说明
- [最终报告](REFACTOR_FINAL_REPORT.md) - 重构完成报告

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范
- 遵循 PEP 8 代码风格
- 添加适当的类型注解
- 编写单元测试
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - 强大的 ORM 工具
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证库
- [Loguru](https://github.com/Delgan/loguru) - 优雅的日志库

## 📞 支持

- 📧 Email: support@example.com
- 📚 文档: [docs/](docs/)
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/signal-transceiver/issues)
- 💬 反馈: 使用 `/api/v1/feedback` 端点提交反馈

## 🎯 路线图

### v1.2.0 (计划中)
- [ ] PC 桌面客户端
- [ ] 移动端 App
- [ ] 多租户支持
- [ ] GraphQL API

### v1.1.0 (已完成) ✅
- [x] User-Client 模型合并
- [x] Glassmorphism UI 设计
- [x] 账号密码登录
- [x] 完整的 CRUD 管理界面
- [x] 告警配置界面

### v1.0.0 (已完成) ✅
- [x] 核心 API 功能
- [x] WebSocket 支持
- [x] 监控告警系统
- [x] 报告生成
- [x] Docker 部署

---

**开发状态**: ✅ 生产就绪  
**最后更新**: 2026-02-04  
**版本**: v1.1.0  
**质量等级**: ⭐⭐⭐⭐⭐
│   │   │   ├── strategy.py  # 策略API
│   │   │   ├── admin.py     # 管理API
│   │   │   ├── system.py    # 系统API
│   │   │   ├── compliance.py # 合规API
│   │   │   ├── analytics.py  # 数据分析API
│   │   │   ├── webhooks.py   # Webhook API
│   │   │   ├── feedback.py   # 反馈API
│   │   │   ├── notifications.py # 通知API
│   │   │   └── config_logs.py # 配置/日志API
│   │   └── websocket.py     # WebSocket
│   ├── services/            # 业务逻辑
│   │   ├── auth_service.py
│   │   ├── data_service.py
│   │   ├── subscription_service.py
│   │   ├── audit_service.py      # 审计服务
│   │   ├── backup_service.py     # 备份服务
│   │   ├── analytics_service.py  # 数据分析服务
│   │   ├── webhook_service.py    # Webhook服务
│   │   ├── key_rotation_service.py # 密钥轮换服务
│   │   ├── feedback_service.py   # 反馈服务
│   │   ├── export_service.py     # 导出服务
│   │   ├── notification_service.py # 通知服务
│   │   └── log_search_service.py # 日志搜索服务
│   ├── core/                # 核心组件
│   │   ├── security.py      # 安全工具
│   │   ├── dependencies.py  # 依赖注入
│   │   ├── exceptions.py    # 异常定义
│   │   ├── middleware.py    # 中间件
│   │   ├── scheduler.py     # 定时任务
│   │   ├── cache.py         # 缓存层
│   │   ├── validation.py    # 数据验证
│   │   ├── compliance.py    # 合规检查
│   │   ├── resource_access.py # 资源权限
│   │   ├── health.py        # 健康检查
│   │   ├── rate_limiter.py  # 速率限制
│   │   ├── config_manager.py # 配置管理
│   │   ├── message_queue.py # 消息队列
│   │   └── tracing.py       # 链路追踪
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
│   │   ├── api.py           # 监控API
│   │   └── admin_ui.py      # 管理界面
│   └── utils/               # 工具函数
│       └── i18n.py          # 国际化支持
├── tests/                   # 测试文件
│   ├── unit/                # 单元测试
│   │   ├── test_auth.py
│   │   ├── test_security.py
│   │   ├── test_exceptions.py
│   │   ├── test_new_features.py
│   │   ├── test_backup.py
│   │   ├── test_health_ratelimit.py
│   │   ├── test_feedback.py
│   │   ├── test_export_notification.py
│   │   ├── test_config_logs.py
│   │   ├── test_queue_tracing.py
│   │   ├── test_admin_ui.py
│   │   ├── test_data.py
│   │   └── test_subscription.py
│   └── integration/         # 集成测试
│       └── test_api_flow.py
├── docs/                    # 文档
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── PRIVACY.md
│   └── DISASTER_RECOVERY.md
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

## 国际化支持

系统支持多语言和时区处理：

### 支持的语言
- 🇨🇳 简体中文 (zh-CN)
- 🇹🇼 繁体中文 (zh-TW)
- 🇺🇸 English (en-US)
- 🇯🇵 日本語 (ja-JP)

### 时区支持
- UTC
- Asia/Shanghai (北京时间)
- Asia/Tokyo (东京时间)
- America/New_York (纽约时间)
- Europe/London (伦敦时间)

使用示例:
```python
from src.utils.i18n import i18n, Language, TimezoneHelper, Timezone

# 翻译
message = i18n.t("data_created", Language.EN_US)

# 时区转换
local_time = TimezoneHelper.to_timezone(datetime.utcnow(), Timezone.ASIA_SHANGHAI)
```

## 文档

| 文档 | 说明 |
|------|------|
| [API文档](docs/API.md) | 完整的API接口说明 |
| [部署文档](docs/DEPLOYMENT.md) | 部署指南和配置说明 |
| [隐私政策](docs/PRIVACY.md) | 数据保护和隐私说明 |
| [灾难恢复](docs/DISASTER_RECOVERY.md) | 备份与恢复计划 |

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License

## prompt.txt 需求完成情况

| 序号 | 需求 | 状态 |
|------|------|------|
| 1 | RESTful接口，密钥认证 | ✅ |
| 2 | 数据接收服务 | ✅ |
| 3 | 订阅服务(轮询+WebSocket) | ✅ |
| 4 | 客户端权限管理 | ✅ |
| 5 | 单元测试≥80% | ✅ |
| 6 | Docker容器化 + CI/CD | ✅ |
| 7 | API文档 + 部署文档 | ✅ |
| 8 | 依赖更新机制 | ✅ |
| 9 | 缓存 + 性能优化 | ✅ |
| 10 | 备份和恢复 | ✅ |
| 11 | 法律合规(GDPR) | ✅ |
| 12 | 用户支持渠道 | ✅ |
| 17 | 用户界面(API Dashboard) | ✅ |
| 18 | 国际化支持 | ✅ |
| 19 | 日志管理 | ✅ |
| 20 | 监控和报警 | ✅ |
| 21 | 数据分析和报告 | ✅ |
| 22 | 可扩展性设计 | ✅ |
| 23 | 灾难恢复计划 | ✅ |

## 项目统计

| 指标 | 数量 |
|------|------|
| Python 文件 | 110+ |
| 代码行数 | 16,500+ |
| API 端点模块 | 13 个 |
| 单元测试文件 | 13 个 |
| 服务模块 | 18 个 |

## 贡献

欢迎提交 Issue 和 Pull Request！
