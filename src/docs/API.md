# Signal Transceiver API 文档

## 概述

Signal Transceiver 是一个订阅服务系统，提供以下功能：

1. 数据接收服务 - 客户端上报数据
2. 订阅服务 - 其他客户端获取数据
3. 权限管理 - 不同客户端的访问权限控制

## 基础URL

```
开发环境: http://localhost:8000
生产环境: https://your-domain.com
```

## 认证方式

### 用户 API Key

用于用户账户相关操作（创建客户端、管理策略等）。

```http
X-API-Key: sk_your_api_key_here
```

### 客户端凭证

用于数据上报和订阅操作。

```http
X-Client-Key: ck_your_client_key_here
X-Client-Secret: cs_your_client_secret_here
```

## API 端点

### 认证

#### 注册用户

```http
POST /api/v1/auth/register
```

请求体:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string (可选)"
}
```

响应:
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user": { ... },
    "api_key": "sk_xxx...",
    "note": "Save this API key securely."
  }
}
```

#### 用户登录

```http
POST /api/v1/auth/login
```

请求体:
```json
{
  "username": "string",
  "password": "string"
}
```

#### 获取当前用户

```http
GET /api/v1/auth/me
```

### 客户端管理

#### 创建客户端

```http
POST /api/v1/clients
```

请求体:
```json
{
  "name": "string",
  "description": "string (可选)",
  "contact_email": "string (可选)",
  "rate_limit": 100
}
```

响应:
```json
{
  "id": 1,
  "name": "My Client",
  "client_key": "ck_xxx...",
  "client_secret": "cs_xxx...",
  ...
}
```

#### 列出客户端

```http
GET /api/v1/clients
```

#### 重新生成凭证

```http
POST /api/v1/clients/{client_id}/regenerate-credentials
```

### 数据管理

#### 上报数据

```http
POST /api/v1/data
```

请求体:
```json
{
  "type": "signal",
  "symbol": "AAPL",
  "execute_date": "2024-02-01",
  "strategy_id": "strategy_001",
  "description": "Buy signal",
  "payload": {
    "action": "buy",
    "quantity": 100
  }
}
```

#### 批量上报

```http
POST /api/v1/data/batch
```

请求体:
```json
{
  "items": [
    { "type": "...", "symbol": "...", ... },
    { "type": "...", "symbol": "...", ... }
  ]
}
```

#### 查询数据

```http
GET /api/v1/data
```

查询参数:
- `type`: 数据类型
- `symbol`: 交易标的
- `strategy_id`: 策略ID
- `start_date`: 开始日期
- `end_date`: 结束日期
- `limit`: 返回数量
- `offset`: 偏移量

### 订阅管理

#### 创建订阅

```http
POST /api/v1/subscriptions
```

请求体:
```json
{
  "name": "My Subscription",
  "subscription_type": "polling",
  "strategy_id": "strategy_001",
  "filters": {
    "type": "signal",
    "symbol": "AAPL"
  }
}
```

#### 获取订阅数据（轮询）

```http
GET /api/v1/subscriptions/{subscription_id}/data
```

响应:
```json
{
  "subscription_id": 1,
  "data": [...],
  "last_id": 100,
  "has_more": false
}
```

### 策略管理

#### 创建策略（需要管理员权限）

```http
POST /api/v1/strategies
```

请求体:
```json
{
  "strategy_id": "strategy_001",
  "name": "My Strategy",
  "type": "default",
  "description": "策略描述"
}
```

#### 列出策略

```http
GET /api/v1/strategies
```

### 管理员接口

#### 初始化权限

```http
POST /api/v1/admin/init-permissions
```

#### 分配角色

```http
POST /api/v1/admin/clients/{client_id}/roles/{role_code}
```

## WebSocket API

### 连接

```
ws://localhost:8000/ws/subscribe?client_key=xxx&client_secret=xxx
```

### 消息格式

#### 订阅

客户端发送:
```json
{"action": "subscribe", "subscription_id": 1}
```

服务端响应:
```json
{"type": "subscribed", "subscription_id": 1}
```

#### 取消订阅

客户端发送:
```json
{"action": "unsubscribe", "subscription_id": 1}
```

#### 接收数据

服务端推送:
```json
{
  "type": "data",
  "subscription_id": 1,
  "data": [...],
  "has_more": false
}
```

#### 心跳

客户端发送:
```json
{"action": "ping"}
```

服务端响应:
```json
{"type": "pong"}
```

## 错误响应

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "details": {}
}
```

### 错误代码

| 代码 | HTTP状态码 | 描述 |
|------|-----------|------|
| AUTH_ERROR | 401 | 认证失败 |
| FORBIDDEN | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| VALIDATION_ERROR | 422 | 验证错误 |
| RATE_LIMIT | 429 | 请求限流 |
| INTERNAL_ERROR | 500 | 服务器错误 |

## 限流

默认限制: 100 请求/分钟

响应头:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
```
