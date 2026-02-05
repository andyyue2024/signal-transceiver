# 数据库关系图 (ERD) - Signal Transceiver

## 表关系概览

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    数据库关系图                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

                                      ┌──────────────────┐
                                      │    Permission    │
                                      │──────────────────│
                                      │ id (PK)          │
                                      │ name             │
                                      │ code             │
                                      │ description      │
                                      │ category         │
                                      │ resource         │
                                      │ action           │
                                      │ is_active        │
                                      │ created_at       │
                                      │ updated_at       │
                                      └────────┬─────────┘
                                               │
                                               │ M:N
                                               ▼
   ┌──────────────────────────────────────────────────────────────────────────────────────┐
   │                                  role_permissions                                     │
   │                                (关联表/Association Table)                             │
   │                              role_id (FK) ◄──── permission_id (FK)                   │
   └──────────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               │ M:N
                                               ▼
                                      ┌──────────────────┐
                                      │      Role        │
                                      │──────────────────│
                                      │ id (PK)          │
                                      │ name             │
                                      │ code             │
                                      │ description      │
                                      │ level            │
                                      │ is_active        │
                                      │ is_default       │
                                      │ created_at       │
                                      │ updated_at       │
                                      └────────┬─────────┘
                                               │
                                               │ 1:N
                                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                           │
│     ┌──────────────────┐                ┌──────────────────┐                              │
│     │ ClientPermission │◄───────────────│      User        │                              │
│     │──────────────────│       1:N      │──────────────────│                              │
│     │ id (PK)          │                │ id (PK)          │                              │
│     │ user_id (FK)     │────────────────│ username         │                              │
│     │ role_id (FK)     │                │ email            │                              │
│     │ is_active        │                │ hashed_password  │                              │
│     │ expires_at       │                │ api_key          │                              │
│     │ created_at       │                │ api_key_expires  │                              │
│     │ updated_at       │                │ client_key       │                              │
│     └──────────────────┘                │ client_secret    │                              │
│                                         │ is_active        │                              │
│                                         │ is_admin         │                              │
│                                         │ full_name        │                              │
│                                         │ phone            │                              │
│                                         │ description      │                              │
│                                         │ webhook_url      │                              │
│                                         │ rate_limit       │                              │
│                                         │ created_at       │                              │
│                                         │ updated_at       │                              │
│                                         │ last_login_at    │                              │
│                                         │ last_access_at   │                              │
│                                         └────────┬─────────┘                              │
│                                                  │                                        │
│           ┌──────────────────────────────────────┼───────────────────────────────┐        │
│           │                                      │                               │        │
│           │ 1:N                                  │ 1:N                           │ 1:N    │
│           ▼                                      ▼                               ▼        │
│  ┌──────────────────┐                   ┌──────────────────┐              ┌──────────────┐│
│  │   Subscription   │                   │       Data       │              │     Log      ││
│  │──────────────────│                   │──────────────────│              │──────────────││
│  │ id (PK)          │                   │ id (PK)          │              │ id (PK)      ││
│  │ name             │                   │ type             │              │ log_type     ││
│  │ description      │                   │ symbol           │              │ action       ││
│  │ subscription_type│                   │ execute_date     │              │ resource     ││
│  │ user_id (FK)     │                   │ description      │              │ resource_id  ││
│  │ strategy_id (FK) │                   │ payload (JSON)   │              │ method       ││
│  │ filters (JSON)   │                   │ metadata (JSON)  │              │ path         ││
│  │ webhook_url      │                   │ source           │              │ ip_address   ││
│  │ notification_en  │                   │ strategy_id (FK) │              │ user_agent   ││
│  │ is_active        │                   │ user_id (FK)     │              │ user_id (FK) ││
│  │ last_data_id     │                   │ status           │              │ client_id    ││
│  │ last_notified_at │                   │ processed        │              │ message      ││
│  │ created_at       │                   │ created_at       │              │ details(JSON)││
│  │ updated_at       │                   │ updated_at       │              │ status_code  ││
│  │ expires_at       │                   └────────┬─────────┘              │ response_time││
│  └────────┬─────────┘                            │                        │ level        ││
│           │                                      │                        │ created_at   ││
│           │ N:1                                  │ N:1                    └──────────────┘│
│           └──────────────────────────────────────┤                                        │
│                                                  │                                        │
│                                                  ▼                                        │
│                                         ┌──────────────────┐                              │
│                                         │    Strategy      │                              │
│                                         │──────────────────│                              │
│                                         │ id (PK)          │                              │
│                                         │ strategy_id      │                              │
│                                         │ name             │                              │
│                                         │ description      │                              │
│                                         │ type             │                              │
│                                         │ category         │                              │
│                                         │ config (JSON)    │                              │
│                                         │ parameters(JSON) │                              │
│                                         │ is_active        │                              │
│                                         │ priority         │                              │
│                                         │ version          │                              │
│                                         │ created_at       │                              │
│                                         │ updated_at       │                              │
│                                         └──────────────────┘                              │
│                                                                                           │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

## 表关系详细说明

### 1. User (用户表) - 核心表
| 关系类型 | 关联表 | 关系说明 |
|---------|--------|---------|
| 1:N | Subscription | 一个用户可以有多个订阅 |
| 1:N | Data | 一个用户可以上报多条数据 |
| 1:N | ClientPermission | 一个用户可以有多个权限分配 |
| 1:N | Log | 一个用户可以有多条日志记录 |

### 2. Strategy (策略表)
| 关系类型 | 关联表 | 关系说明 |
|---------|--------|---------|
| 1:N | Data | 一个策略对应多条数据记录 |
| 1:N | Subscription | 一个策略可以被多个用户订阅 |

### 3. Subscription (订阅表)
| 关系类型 | 关联表 | 外键 | 关系说明 |
|---------|--------|-----|---------|
| N:1 | User | user_id | 多个订阅属于一个用户 |
| N:1 | Strategy | strategy_id (可空) | 订阅可关联到特定策略 |

### 4. Data (数据表)
| 关系类型 | 关联表 | 外键 | 关系说明 |
|---------|--------|-----|---------|
| N:1 | User | user_id | 数据由用户上报 |
| N:1 | Strategy | strategy_id | 数据关联到策略 |

### 5. Log (日志表)
| 关系类型 | 关联表 | 外键 | 关系说明 |
|---------|--------|-----|---------|
| N:1 | User | user_id (可空) | 日志可关联到用户 |

### 6. Permission (权限表) & Role (角色表)
| 关系类型 | 关联表 | 关系说明 |
|---------|--------|---------|
| M:N | Role ↔ Permission | 通过 role_permissions 关联表实现多对多 |
| 1:N | Role → ClientPermission | 一个角色可分配给多个用户权限记录 |

### 7. ClientPermission (用户权限分配表)
| 关系类型 | 关联表 | 外键 | 关系说明 |
|---------|--------|-----|---------|
| N:1 | User | user_id | 权限分配给用户 |
| N:1 | Role | role_id | 分配特定角色 |

## 外键约束汇总

```
subscriptions.user_id      → users.id
subscriptions.strategy_id  → strategies.id (可空)
data.user_id               → users.id
data.strategy_id           → strategies.id
logs.user_id               → users.id (可空)
client_permissions.user_id → users.id
client_permissions.role_id → roles.id
role_permissions.role_id   → roles.id
role_permissions.perm_id   → permissions.id
```

## 数据模型说明

### User 模型
统一的用户模型，合并了原有的 User 和 Client 功能：
- 支持管理员登录 (is_admin)
- 支持 API Key 认证 (api_key)
- 支持客户端凭据认证 (client_key, client_secret)
- 支持速率限制 (rate_limit)

### Strategy 模型
策略管理：
- 支持版本控制 (version)
- 支持优先级排序 (priority)
- 支持 JSON 配置 (config, parameters)

### Data 模型
数据上报：
- 支持多种数据类型 (type)
- 支持 JSON 扩展字段 (payload, metadata)
- 支持状态追踪 (status, processed)

### Subscription 模型
订阅管理：
- 支持轮询和 WebSocket 两种方式 (subscription_type)
- 支持 JSON 过滤条件 (filters)
- 支持 Webhook 通知 (webhook_url)

### Permission & Role 模型
RBAC 权限控制：
- 支持资源级权限 (resource, action)
- 支持角色级别 (level)
- 支持多对多角色-权限关联
