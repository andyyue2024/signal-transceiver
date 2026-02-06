# API 权限检查实现说明

## 概述

项目中的 API 接口实现了基于角色的访问控制 (RBAC)。权限检查通过 `src/core/dependencies.py` 中的依赖注入实现。

## 认证方式

系统支持两种认证方式：

1. **API Key 认证** - 通过 `X-API-Key` 请求头
2. **Client Key/Secret 认证** - 通过 `X-Client-Key` 和 `X-Client-Secret` 请求头

## 权限依赖函数

| 函数 | 说明 |
|------|------|
| `get_current_user` | 基础认证，验证用户身份 |
| `get_admin_user` | 要求管理员权限 |
| `get_client_from_key` | 通过 Client 凭证认证 |
| `require_permissions(*permissions)` | 要求特定权限码 |

## 权限码定义

| 权限码 | 说明 |
|--------|------|
| `data:read` | 读取数据 |
| `data:create` | 创建数据 |
| `data:update` | 更新数据 |
| `data:delete` | 删除数据 |
| `subscription:read` | 读取订阅 |
| `subscription:create` | 创建订阅 |
| `subscription:update` | 更新订阅 |
| `subscription:delete` | 删除订阅 |
| `strategy:read` | 读取策略 |
| `strategy:create` | 创建策略 |
| `admin:access` | 管理员访问 |

## API 权限配置

### 数据 API (`/api/v1/data`)
- `POST /data` - 需要 `data:create`
- `POST /data/batch` - 需要 `data:create`
- `GET /data` - 需要 `data:read`
- `GET /data/{id}` - 需要 `data:read`
- `PUT /data/{id}` - 需要 `data:update`
- `DELETE /data/{id}` - 需要 `data:delete`

### 订阅 API (`/api/v1/subscriptions`)
- `POST /subscriptions` - 需要 `subscription:create`
- `GET /subscriptions` - 需要 `subscription:read`
- `GET /subscriptions/{id}` - 需要 `subscription:read`
- `PUT /subscriptions/{id}` - 需要 `subscription:update`
- `DELETE /subscriptions/{id}` - 需要 `subscription:delete`
- `GET /subscriptions/{id}/data` - 需要 `subscription:read`
- `POST /subscriptions/{id}/activate` - 需要 `subscription:update`
- `POST /subscriptions/{id}/deactivate` - 需要 `subscription:update`

### 策略 API (`/api/v1/strategies`)
- `POST /strategies` - 需要 `strategy:create`
- `GET /strategies` - 需要 `strategy:read`
- `GET /strategies/{id}` - 需要 `strategy:read`
- `PUT /strategies/{id}` - 需要 `strategy:create`
- `DELETE /strategies/{id}` - 需要 `strategy:create`

### 客户端管理 API (`/api/v1/clients`)
- 所有接口需要管理员权限 (`get_admin_user`)

### 分析 API (`/api/v1/analytics`)
- `GET /analytics/data/trends` - 需要 `data:read`
- `GET /analytics/data/chart` - 需要 `data:read`
- `GET /analytics/subscriptions` - 需要 `subscription:read`
- `GET /analytics/clients` - 需要 `admin:access`
- `GET /analytics/summary` - 需要 `data:read`

### Webhook API (`/api/v1/webhooks`)
- `POST /webhooks` - 需要 `subscription:create`
- `GET /webhooks` - 需要 `subscription:read`
- `GET /webhooks/{id}` - 需要 `subscription:read`
- `PATCH /webhooks/{id}` - 需要 `subscription:update`
- `DELETE /webhooks/{id}` - 需要 `subscription:delete`

### 合规 API (`/api/v1/compliance`)
- `POST /compliance/validate` - 需要 `data:read`
- `POST /compliance/check` - 需要 `data:read`
- `GET /compliance/rules` - 需要 `data:read`

### 系统管理 API (`/api/v1/admin`)
- 所有接口需要管理员权限 (`get_admin_user`)

### 反馈 API (`/api/v1/feedback`)
- 所有接口需要基础认证 (`get_current_user`)

### 通知 API (`/api/v1/notifications`)
- 所有接口需要基础认证 (`get_current_user`)

## 默认角色

| 角色 | 权限 |
|------|------|
| Reader | `data:read`, `subscription:read`, `strategy:read` |
| Writer | `data:read`, `data:create`, `subscription:read`, `subscription:create`, `subscription:update`, `strategy:read` |
| Admin | 所有权限 |

## 使用示例

```python
from src.core.dependencies import require_permissions

@router.get("/data")
async def list_data(
    user: User = Depends(require_permissions("data:read")),
    db: AsyncSession = Depends(get_db)
):
    # 只有拥有 data:read 权限的用户才能访问
    ...
```

## 注意事项

1. 管理员用户 (`is_admin=True`) 自动拥有所有权限
2. 使用系统 Admin API Key 的请求自动获得管理员权限
3. 权限通过角色分配给用户，用户可以拥有多个角色
