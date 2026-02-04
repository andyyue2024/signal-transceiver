# 数据模型重构说明 - Client与User合并

## 📅 重构日期: 2026-02-04

---

## 🎯 重构目标

将 **Client（客户端）** 和 **User（用户）** 两个独立的数据模型合并为统一的 **User** 模型。

### 重构原因
1. 简化架构：一个用户既可以是管理员，也可以是API客户端
2. 减少关联复杂度：不再需要 User -> Client 的一对多关系
3. 统一认证：使用同一套用户体系进行认证和授权
4. 符合实际使用场景：大多数情况下，一个用户对应一个API客户端

---

## 📊 数据模型变更

### 变更前（旧架构）

```
User (用户)
  ├── id
  ├── username
  ├── email
  ├── hashed_password
  ├── api_key (Web UI 认证)
  └── clients[] (一对多关系)

Client (客户端)
  ├── id
  ├── name
  ├── client_key (API 认证)
  ├── client_secret
  ├── owner_id -> User
  ├── subscriptions[]
  └── data_records[]
```

### 变更后（新架构）

```
User (统一用户模型)
  ├── id
  ├── username
  ├── email
  ├── hashed_password
  ├── api_key (Web UI 认证)
  ├── client_key (API 认证)
  ├── client_secret
  ├── rate_limit
  ├── webhook_url
  ├── subscriptions[] (直接关联)
  ├── data_records[] (直接关联)
  └── permissions[] (直接关联)
```

---

## 🔄 模型文件变更

### 1. User Model (src/models/user.py)
**新增字段**:
- `client_key`: 用于API客户端认证
- `client_secret`: 客户端密钥
- `rate_limit`: API速率限制
- `webhook_url`: Webhook回调地址
- `contact_email`: 联系邮箱
- `last_access_at`: 最后API访问时间

**新增关系**:
- `subscriptions`: 直接关联到用户的订阅
- `data_records`: 用户上报的数据记录
- `permissions`: 用户权限

### 2. Subscription Model (src/models/subscription.py)
**字段变更**:
- `client_id` → `user_id`
- `ForeignKey("clients.id")` → `ForeignKey("users.id")`

**关系变更**:
- `client` → `user`

### 3. Data Model (src/models/data.py)
**字段变更**:
- `client_id` → `user_id`
- `ForeignKey("clients.id")` → `ForeignKey("users.id")`

**关系变更**:
- `client` → `user`

### 4. ClientPermission Model (src/models/permission.py)
**字段变更**:
- `client_id` → `user_id`
- `ForeignKey("clients.id")` → `ForeignKey("users.id")`

**关系变更**:
- `client` → `user`

**注**: 表名保持为 `client_permissions` 以保持向后兼容

### 5. Client Model (src/models/client.py)
**状态**: ❌ 已废弃，功能合并到 User 模型

---

## 🗄️ 数据库迁移步骤

### 方案A: 全新数据库（推荐用于开发环境）

```bash
# 1. 删除旧数据库
rm data/app.db

# 2. 重新初始化数据库
python -m src.cli db init

# 3. 初始化权限
python -m src.cli db init-permissions
```

### 方案B: 数据迁移（生产环境）

```sql
-- Step 1: 为 users 表添加新字段
ALTER TABLE users ADD COLUMN client_key VARCHAR(64) UNIQUE NOT NULL DEFAULT '';
ALTER TABLE users ADD COLUMN client_secret VARCHAR(128) NOT NULL DEFAULT '';
ALTER TABLE users ADD COLUMN rate_limit INTEGER DEFAULT 100;
ALTER TABLE users ADD COLUMN webhook_url VARCHAR(500);
ALTER TABLE users ADD COLUMN contact_email VARCHAR(255);
ALTER TABLE users ADD COLUMN last_access_at DATETIME;

-- Step 2: 迁移 clients 表数据到 users 表
UPDATE users u
SET 
    client_key = (SELECT c.client_key FROM clients c WHERE c.owner_id = u.id LIMIT 1),
    client_secret = (SELECT c.client_secret FROM clients c WHERE c.owner_id = u.id LIMIT 1),
    rate_limit = (SELECT c.rate_limit FROM clients c WHERE c.owner_id = u.id LIMIT 1),
    webhook_url = (SELECT c.webhook_url FROM clients c WHERE c.owner_id = u.id LIMIT 1),
    contact_email = (SELECT c.contact_email FROM clients c WHERE c.owner_id = u.id LIMIT 1),
    last_access_at = (SELECT c.last_access_at FROM clients c WHERE c.owner_id = u.id LIMIT 1);

-- Step 3: 更新 subscriptions 表
ALTER TABLE subscriptions ADD COLUMN user_id INTEGER;
UPDATE subscriptions SET user_id = (SELECT owner_id FROM clients WHERE id = client_id);
ALTER TABLE subscriptions DROP COLUMN client_id;

-- Step 4: 更新 data 表
ALTER TABLE data ADD COLUMN user_id INTEGER;
UPDATE data SET user_id = (SELECT owner_id FROM clients WHERE id = client_id);
ALTER TABLE data DROP COLUMN client_id;

-- Step 5: 更新 client_permissions 表
ALTER TABLE client_permissions ADD COLUMN user_id INTEGER;
UPDATE client_permissions SET user_id = (SELECT owner_id FROM clients WHERE id = client_id);
ALTER TABLE client_permissions DROP COLUMN client_id;

-- Step 6: 删除 clients 表（可选，建议先备份）
-- DROP TABLE clients;
```

---

## 🔧 代码变更影响

### API 端点变更

**之前**:
```python
# 客户端管理
POST /api/v1/clients
GET /api/v1/clients
GET /api/v1/clients/{id}
```

**现在**:
```python
# 用户即客户端，API端点保持兼容
POST /api/v1/clients -> 创建用户（同时生成client_key）
GET /api/v1/clients -> 获取用户列表
GET /api/v1/clients/{id} -> 获取用户详情
```

### 认证方式

**保持不变**:
- Web UI 登录: 使用 `username + password`，返回 `api_key`
- API 客户端: 使用 `client_key + client_secret` 认证

---

## ✅ 兼容性处理

### 1. API 兼容
- `/api/v1/clients/*` 端点继续可用，内部映射到User操作
- 响应格式保持一致，使用 `client_key` 和 `client_secret` 字段名

### 2. Schema 兼容
- ClientResponse schema 继续存在，作为 UserResponse 的别名
- 旧的 API 调用不受影响

### 3. Service 兼容
- ClientService 保留，内部调用 User 模型
- 确保平滑过渡

---

## 📝 更新清单

### 已更新的文件
- ✅ `src/models/user.py` - 合并 Client 功能
- ✅ `src/models/subscription.py` - 更新为 user_id
- ✅ `src/models/data.py` - 更新为 user_id
- ✅ `src/models/permission.py` - ClientPermission 更新为 user_id
- ✅ `src/models/__init__.py` - 移除 Client 导出

### 需要更新的文件
- ⏳ `src/services/client_service.py` - 适配新User模型
- ⏳ `src/services/auth_service.py` - 生成client credentials
- ⏳ `src/api/v1/client.py` - 更新API端点
- ⏳ `src/api/v1/subscription.py` - 使用user_id
- ⏳ `src/api/v1/data.py` - 使用user_id
- ⏳ `src/core/dependencies.py` - 更新认证逻辑
- ⏳ `src/schemas/client.py` - 更新schema
- ⏳ 测试文件更新

---

## 🧪 测试计划

### 单元测试
```bash
# 测试用户模型
pytest tests/unit/test_user_model.py -v

# 测试认证
pytest tests/unit/test_auth.py -v

# 测试订阅
pytest tests/unit/test_subscription.py -v
```

### 集成测试
```bash
# 完整工作流测试
pytest tests/integration/ -v
```

---

## 🎯 features.txt 更新

```text
修改前：
- 核心API (认证、数据、订阅、客户端、策略) ✓
- /api/v1/clients/* - 客户端

修改后：
- 核心API (认证、数据、订阅、用户、策略) ✓
- /api/v1/clients/* - 用户（兼容客户端API）
```

---

## 📚 参考文档

- User Model: `src/models/user.py`
- Migration Script: 本文档 SQL 部分
- API Documentation: `docs/API.md` (需更新)

---

**重构负责人**: AI Assistant  
**审核状态**: 待测试  
**上线时间**: TBD
