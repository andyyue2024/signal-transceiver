# API 文档

## 概述

Signal Transceiver 是一个订阅服务系统，提供数据收集和分发功能。

**基础URL**: `http://localhost:8000`

**API版本**: v1

**认证方式**: API Key / Client Credentials

---

## 认证

### 用户认证

使用 `X-API-Key` 请求头进行用户级别认证：

```http
X-API-Key: sk_your_api_key_here
```

### 客户端认证

使用客户端密钥对进行客户端级别认证：

```http
X-Client-Key: ck_your_client_key
X-Client-Secret: cs_your_client_secret
```

---

## 端点列表

### 1. 认证 API

#### 1.1 用户注册

```http
POST /api/v1/auth/register
```

**请求体**:
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "securepassword"
}
```

**响应**:
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user": {
      "id": 1,
      "username": "testuser",
      "email": "test@example.com"
    },
    "api_key": "sk_xxxxx..."
  }
}
```

#### 1.2 用户登录

```http
POST /api/v1/auth/login
```

**请求体**:
```json
{
  "username": "testuser",
  "password": "securepassword"
}
```

#### 1.3 获取当前用户

```http
GET /api/v1/auth/me
```

**请求头**: `X-API-Key: your-api-key`

---

### 2. 数据 API

#### 2.1 上报数据

```http
POST /api/v1/data
```

**请求头**: 客户端认证

**请求体**:
```json
{
  "type": "signal",
  "symbol": "AAPL",
  "execute_date": "2024-02-01",
  "strategy_id": 1,
  "description": "Buy signal",
  "payload": {}
}
```

#### 2.2 批量上报

```http
POST /api/v1/data/batch
```

**请求体**:
```json
{
  "items": [
    {
      "type": "signal",
      "symbol": "AAPL",
      "execute_date": "2024-02-01",
      "strategy_id": 1
    }
  ]
}
```

#### 2.3 查询数据

```http
GET /api/v1/data?strategy_id=1&symbol=AAPL&start_date=2024-01-01&end_date=2024-02-01
```

**查询参数**:
- `strategy_id` (int): 策略ID
- `symbol` (string): 交易标的
- `type` (string): 数据类型
- `start_date` (date): 开始日期
- `end_date` (date): 结束日期
- `limit` (int): 返回数量限制
- `offset` (int): 偏移量

#### 2.4 获取单条数据

```http
GET /api/v1/data/{id}
```

#### 2.5 更新数据

```http
PUT /api/v1/data/{id}
```

#### 2.6 删除数据

```http
DELETE /api/v1/data/{id}
```

---

### 3. 订阅 API

#### 3.1 创建订阅

```http
POST /api/v1/subscriptions
```

**请求体**:
```json
{
  "name": "My Subscription",
  "subscription_type": "polling",
  "strategy_id": 1,
  "filters": {
    "symbol": "AAPL"
  }
}
```

**订阅类型**:
- `polling`: 轮询订阅
- `websocket`: WebSocket实时订阅

#### 3.2 获取订阅列表

```http
GET /api/v1/subscriptions
```

#### 3.3 获取订阅数据

```http
GET /api/v1/subscriptions/{id}/data?since=2024-02-01T00:00:00Z
```

#### 3.4 更新订阅

```http
PUT /api/v1/subscriptions/{id}
```

#### 3.5 删除订阅

```http
DELETE /api/v1/subscriptions/{id}
```

---

### 4. 客户端 API

#### 4.1 创建客户端

```http
POST /api/v1/clients
```

**请求头**: 用户认证

**请求体**:
```json
{
  "name": "My Application",
  "description": "Test client"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "My Application",
    "client_key": "ck_xxxxx",
    "client_secret": "cs_xxxxx"
  }
}
```

#### 4.2 获取客户端列表

```http
GET /api/v1/clients
```

#### 4.3 更新客户端

```http
PUT /api/v1/clients/{id}
```

#### 4.4 重新生成密钥

```http
POST /api/v1/clients/{id}/regenerate-secret
```

---

### 5. 策略 API

#### 5.1 创建策略

```http
POST /api/v1/strategies
```

**请求体**:
```json
{
  "strategy_id": "strategy_001",
  "name": "Alpha Strategy",
  "description": "Description of the strategy"
}
```

#### 5.2 获取策略列表

```http
GET /api/v1/strategies
```

#### 5.3 获取策略详情

```http
GET /api/v1/strategies/{id}
```

---

### 6. 监控 API

#### 6.1 健康检查

```http
GET /health
```

#### 6.2 Prometheus指标

```http
GET /api/v1/monitor/metrics
```

#### 6.3 系统仪表盘

```http
GET /api/v1/monitor/dashboard
```

**请求头**: 用户认证

#### 6.4 性能数据

```http
GET /api/v1/monitor/performance?minutes=60
```

---

### 7. 合规检查 API

#### 7.1 数据验证

```http
POST /api/v1/compliance/validate
```

**请求体**:
```json
{
  "type": "signal",
  "symbol": "AAPL",
  "execute_date": "2024-02-01",
  "strategy_id": "strategy_001"
}
```

#### 7.2 合规检查

```http
POST /api/v1/compliance/check
```

#### 7.3 获取合规规则

```http
GET /api/v1/compliance/rules
```

---

### 8. 系统管理 API (需要管理员权限)

#### 8.1 系统统计

```http
GET /api/v1/admin/stats
```

#### 8.2 审计日志

```http
GET /api/v1/admin/audit-trail?days=7
```

#### 8.3 创建备份

```http
POST /api/v1/admin/backups/create
```

#### 8.4 备份列表

```http
GET /api/v1/admin/backups
```

#### 8.5 调度器状态

```http
GET /api/v1/admin/scheduler/status
```

#### 8.6 缓存统计

```http
GET /api/v1/admin/cache/stats
```

---

### 9. WebSocket API

#### 9.1 连接订阅

```
ws://localhost:8000/ws/subscribe?client_key=xxx&client_secret=xxx
```

#### 9.2 订阅消息

```json
{
  "action": "subscribe",
  "subscription_id": 1
}
```

#### 9.3 心跳

```json
{
  "action": "ping"
}
```

---

## 错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|-----------|------|
| AUTH_ERROR | 401 | 认证失败 |
| FORBIDDEN | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源未找到 |
| VALIDATION_ERROR | 422 | 验证错误 |
| CONFLICT | 409 | 资源冲突 |
| RATE_LIMIT | 429 | 请求过于频繁 |
| DB_ERROR | 500 | 数据库错误 |

---

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

### 错误响应

```json
{
  "success": false,
  "message": "Error message",
  "error_code": "ERROR_CODE",
  "details": {}
}
```

---

## 分页

支持分页的端点使用以下查询参数：

- `limit` (int, default=20): 每页数量
- `offset` (int, default=0): 偏移量

响应格式：

```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 100,
    "limit": 20,
    "offset": 0
  }
}
```

---

## 速率限制

- 默认: 100 请求/分钟
- 超出限制返回 429 状态码

---

## 10. 数据分析 API

#### 10.1 获取数据趋势

```http
GET /api/v1/analytics/data/trends?days=30&strategy_id=1
```

**查询参数**:
- `days` (int): 分析天数 (1-365)
- `strategy_id` (int): 策略ID过滤
- `data_type` (string): 数据类型过滤

**响应**:
```json
{
  "success": true,
  "data": {
    "total_records": 1000,
    "period": {"start": "2024-01-01", "end": "2024-01-31", "days": 30},
    "trends": [{"date": "2024-01-01", "count": 50}],
    "by_type": {"signal": 500, "order": 500},
    "by_symbol": {"AAPL": 200, "GOOGL": 150},
    "summary": {
      "average_daily": 33.3,
      "growth_rate_percent": 15.5
    }
  }
}
```

#### 10.2 获取图表数据

```http
GET /api/v1/analytics/data/chart?days=30&chart_type=line
```

#### 10.3 获取分析摘要

```http
GET /api/v1/analytics/summary?days=7
```

---

## 11. Webhook API

#### 11.1 注册 Webhook

```http
POST /api/v1/webhooks
```

**请求体**:
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["data.created", "subscription.activated"],
  "headers": {"Authorization": "Bearer token"}
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "wh_abc123",
    "url": "https://your-server.com/webhook",
    "secret": "your-webhook-secret",
    "events": ["data.created", "subscription.activated"],
    "enabled": true
  }
}
```

#### 11.2 列出 Webhook

```http
GET /api/v1/webhooks
```

#### 11.3 更新 Webhook

```http
PATCH /api/v1/webhooks/{webhook_id}
```

#### 11.4 删除 Webhook

```http
DELETE /api/v1/webhooks/{webhook_id}
```

#### 11.5 测试 Webhook

```http
POST /api/v1/webhooks/{webhook_id}/test
```

#### 11.6 查看配送历史

```http
GET /api/v1/webhooks/{webhook_id}/deliveries?status=delivered&limit=50
```

#### 11.7 可用事件类型

```http
GET /api/v1/webhooks/events
```

**事件类型**:
- `data.created` - 数据创建
- `data.updated` - 数据更新
- `data.deleted` - 数据删除
- `subscription.created` - 订阅创建
- `subscription.activated` - 订阅激活
- `client.created` - 客户端创建
- `system.alert` - 系统告警
- `system.backup_completed` - 备份完成

---

## Webhook 签名验证

Webhook 请求包含签名头用于验证:

```http
X-Webhook-Signature: sha256=abc123...
X-Webhook-Timestamp: 1704067200
X-Webhook-Event: data.created
```

验证示例 (Python):
```python
import hmac
import hashlib

def verify_signature(payload: str, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## 12. 用户反馈 API

#### 12.1 提交反馈

```http
POST /api/v1/feedback
```

**请求体**:
```json
{
  "title": "功能建议",
  "description": "希望添加更多图表类型",
  "type": "feature_request",
  "priority": "medium",
  "tags": ["chart", "enhancement"]
}
```

**反馈类型**:
- `bug` - Bug报告
- `feature_request` - 功能请求
- `question` - 问题咨询
- `improvement` - 改进建议
- `other` - 其他

**优先级**:
- `low`, `medium`, `high`, `critical`

#### 12.2 查看反馈列表

```http
GET /api/v1/feedback?status=open&type=bug&limit=50
```

#### 12.3 获取反馈详情

```http
GET /api/v1/feedback/{feedback_id}
```

#### 12.4 获取反馈统计

```http
GET /api/v1/feedback/stats
```

#### 12.5 获取反馈类型

```http
GET /api/v1/feedback/types
```

---

---

## 13. 系统通知 API

#### 13.1 创建通知

```http
POST /api/v1/notifications
```

**请求体**:
```json
{
  "title": "系统维护通知",
  "message": "系统将在今晚进行维护",
  "type": "info",
  "user_id": 1
}
```

**通知类型**: `info`, `success`, `warning`, `error`

#### 13.2 获取通知列表

```http
GET /api/v1/notifications?user_id=1&unread_only=true
```

#### 13.3 标记为已读

```http
POST /api/v1/notifications/{notification_id}/read
```

#### 13.4 标记全部为已读

```http
POST /api/v1/notifications/read-all
```

#### 13.5 获取未读数量

```http
GET /api/v1/notifications/unread-count
```

---

## 14. 数据导出 API

#### 14.1 导出数据

```http
GET /api/v1/export/data?format=json&limit=1000
```

**支持格式**:
- `json` - JSON格式
- `csv` - CSV格式
- `jsonl` - JSON Lines格式

#### 14.2 导出订阅数据

```http
GET /api/v1/export/subscriptions/{subscription_id}?format=csv
```

---

## 15. 配置管理 API (需要管理员权限)

#### 15.1 获取所有配置

```http
GET /api/v1/config
```

#### 15.2 获取单个配置

```http
GET /api/v1/config/{key}
```

#### 15.3 更新配置

```http
PUT /api/v1/config/{key}
```

**请求体**:
```json
{
  "value": "new_value"
}
```

#### 15.4 删除配置

```http
DELETE /api/v1/config/{key}
```

---

## 16. 日志搜索 API (需要管理员权限)

#### 16.1 搜索日志

```http
GET /api/v1/logs?level=ERROR&hours=24&limit=100
```

**查询参数**:
- `level` - 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `hours` - 最近多少小时
- `keyword` - 关键词搜索
- `source` - 日志来源
- `limit` - 返回数量

#### 16.2 获取日志统计

```http
GET /api/v1/logs/stats
```

---

## 17. 数据转换管道 API

#### 17.1 列出转换管道

```http
GET /api/v1/transform/pipelines
```

#### 17.2 预览转换

```http
POST /api/v1/transform/preview
```

**请求体**:
```json
{
  "pipeline": "normalize_symbol",
  "payload": {
    "symbol": "  aapl  ",
    "type": "signal"
  }
}
```

或使用自定义步骤:
```json
{
  "steps": [
    {"type": "trim", "field": "symbol"},
    {"type": "upper", "field": "symbol"}
  ],
  "payload": {
    "symbol": "  aapl  "
  }
}
```

---

## 速率限制详情

默认限制: **100 请求/分钟**

响应头:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1704067260
```

超出限制时返回:
```json
{
  "success": false,
  "message": "Rate limit exceeded",
  "error_code": "RATE_LIMIT",
  "details": {
    "retry_after": 60
  }
}
```

---

## 错误处理最佳实践

1. **检查 success 字段**
   ```python
   if response.get("success"):
       data = response.get("data")
   else:
       error = response.get("error_code")
   ```

2. **实现重试机制** (针对 429, 500, 503)
   ```python
   import time
   from requests import Session

   def retry_request(url, max_retries=3):
       for i in range(max_retries):
           response = session.get(url)
           if response.status_code < 500:
               return response
           time.sleep(2 ** i)  # 指数退避
   ```

3. **处理分页**
   ```python
   def get_all_data(endpoint):
       offset = 0
       all_items = []
       while True:
           response = client.get(f"{endpoint}?limit=100&offset={offset}")
           items = response["data"]["items"]
           all_items.extend(items)
           if len(items) < 100:
               break
           offset += 100
       return all_items
   ```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.3.0 | 2024-02-04 | 添加通知、导出、配置、日志、转换管道API |
| 1.2.0 | 2024-02-04 | 添加用户反馈API |
| 1.1.0 | 2024-02-04 | 添加数据分析和Webhook API |
| 1.0.0 | 2024-02-01 | 初始版本 |

---

## 附录

### A. 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| SECRET_KEY | 加密密钥 | 必需 |
| ADMIN_API_KEY | 管理员API密钥 | 必需 |
| DATABASE_URL | 数据库连接URL | sqlite+aiosqlite:///./data/app.db |
| DEBUG | 调试模式 | false |
| LOG_LEVEL | 日志级别 | INFO |

### B. 支持的数据类型

- `signal` - 交易信号
- `order` - 订单
- `execution` - 执行记录
- `position` - 持仓
- `custom` - 自定义类型

### C. 订阅过滤器

订阅可以使用以下过滤器:
```json
{
  "filters": {
    "type": "signal",
    "symbol": "AAPL",
    "strategy_id": "strategy_001",
    "tags": ["important"]
  }
}
```

### D. Webhook 载荷示例

```json
{
  "event": "data.created",
  "timestamp": "2024-02-04T12:00:00Z",
  "data": {
    "id": 123,
    "type": "signal",
    "symbol": "AAPL",
    "strategy_id": "strategy_001"
  }
}
```

### E. 联系支持

- 📧 Email: support@example.com
- 📚 文档: https://docs.example.com
- 🐛 问题反馈: https://github.com/example/signal-transceiver/issues

