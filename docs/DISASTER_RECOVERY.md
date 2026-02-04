# 灾难恢复计划

## 概述

本文档定义了 Signal Transceiver 服务的灾难恢复策略和程序，确保在发生系统故障时能够快速恢复服务。

---

## 1. 恢复目标

### 1.1 恢复时间目标 (RTO)

| 优先级 | 服务类型 | RTO |
|--------|---------|-----|
| P0 | 核心API服务 | < 15分钟 |
| P1 | 数据订阅服务 | < 30分钟 |
| P2 | 监控告警 | < 1小时 |
| P3 | 报告生成 | < 4小时 |

### 1.2 恢复点目标 (RPO)

| 数据类型 | RPO | 备份频率 |
|---------|-----|---------|
| 用户数据 | < 1小时 | 每小时 |
| 业务数据 | < 6小时 | 每6小时 |
| 日志数据 | < 24小时 | 每日 |
| 配置数据 | 实时 | Git版本控制 |

---

## 2. 备份策略

### 2.1 自动备份

系统内置定时备份任务：

```python
# 每6小时自动备份
scheduler.add_task(
    task_id="database_backup",
    name="数据库备份",
    func=task_backup_database,
    interval_seconds=21600
)
```

### 2.2 手动备份

```bash
# CLI 命令
python -m src.cli db backup

# API 调用
curl -X POST -H "X-API-Key: admin-key" \
  http://localhost:8000/api/v1/admin/backups/create
```

### 2.3 备份存储

| 存储位置 | 保留时间 | 说明 |
|---------|---------|------|
| 本地 /app/backups | 7天 | 快速恢复 |
| 阿里云 OSS | 30天 | 异地备份 |
| 跨区域备份 | 90天 | 灾难恢复 |

---

## 3. 故障场景与恢复程序

### 3.1 场景一：应用服务崩溃

**症状**: 服务无响应，健康检查失败

**恢复步骤**:

1. 检查容器状态
```bash
docker ps -a | grep signal-transceiver
```

2. 查看日志定位问题
```bash
docker logs signal-transceiver --tail 100
```

3. 重启服务
```bash
docker-compose restart app
```

4. 验证恢复
```bash
curl http://localhost:8000/health
```

**预计恢复时间**: 5-10分钟

---

### 3.2 场景二：数据库损坏

**症状**: 数据库查询失败，数据不一致

**恢复步骤**:

1. 停止服务
```bash
docker-compose stop app
```

2. 备份当前数据库（即使损坏）
```bash
cp data/app.db data/app.db.corrupted
```

3. 从最近备份恢复
```bash
# 使用 API
curl -X POST -H "X-API-Key: admin-key" \
  http://localhost:8000/api/v1/admin/backups/app_full_20240201_120000.db.gz/restore

# 或手动恢复
gunzip -c backups/app_full_20240201_120000.db.gz > data/app.db
```

4. 重启服务
```bash
docker-compose start app
```

5. 验证数据完整性
```bash
python -m src.cli db verify
```

**预计恢复时间**: 15-30分钟

---

### 3.3 场景三：服务器硬件故障

**症状**: 服务器完全不可用

**恢复步骤**:

1. 在备用服务器部署新实例
```bash
# 在备用服务器上
git clone <repository-url>
cd signal-transceiver
docker-compose up -d
```

2. 从异地备份恢复数据
```bash
# 从 OSS 下载最新备份
aliyun oss cp oss://bucket/backups/latest.db.gz ./backups/

# 恢复数据库
gunzip -c backups/latest.db.gz > data/app.db
```

3. 更新 DNS 解析
```bash
# 将域名指向新服务器 IP
```

4. 验证服务正常

**预计恢复时间**: 30-60分钟

---

### 3.4 场景四：区域级故障

**症状**: 整个数据中心/区域不可用

**恢复步骤**:

1. 激活跨区域灾备环境
2. 从跨区域备份恢复数据
3. 更新 DNS 或负载均衡配置
4. 通知用户服务迁移信息

**预计恢复时间**: 1-4小时

---

### 3.5 场景五：安全事件（数据泄露）

**症状**: 发现未授权访问

**响应步骤**:

1. 隔离受影响系统
```bash
# 临时禁用外部访问
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

2. 保留证据
```bash
# 备份日志
cp -r logs/ logs_backup_$(date +%Y%m%d)/
```

3. 分析入侵途径
4. 轮换所有密钥
```bash
# 重新生成管理员密钥
python -m src.cli user regenerate-key admin
```

5. 修复漏洞
6. 通知受影响用户
7. 向监管机构报告

---

## 4. 恢复验证

### 4.1 验证检查清单

- [ ] 服务健康检查通过
- [ ] 用户可正常登录
- [ ] 数据上报功能正常
- [ ] 订阅推送正常
- [ ] WebSocket 连接正常
- [ ] 定时任务运行正常
- [ ] 监控告警正常

### 4.2 验证脚本

```bash
#!/bin/bash
# recovery_verify.sh

echo "验证服务恢复..."

# 健康检查
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✓ 健康检查通过"
else
    echo "✗ 健康检查失败"
    exit 1
fi

# API 测试
if curl -s -H "X-API-Key: $ADMIN_KEY" http://localhost:8000/api/v1/admin/stats | grep -q "success"; then
    echo "✓ API 正常"
else
    echo "✗ API 异常"
    exit 1
fi

echo "恢复验证完成"
```

---

## 5. 演练计划

### 5.1 演练频率

| 场景类型 | 演练频率 |
|---------|---------|
| 服务重启 | 每月 |
| 数据库恢复 | 每季度 |
| 完整灾难恢复 | 每年 |

### 5.2 演练记录

每次演练需记录：

- 演练日期和时间
- 参与人员
- 演练场景
- 实际恢复时间
- 发现的问题
- 改进措施

---

## 6. 联系人

### 6.1 应急响应团队

| 角色 | 姓名 | 联系方式 | 职责 |
|------|------|---------|------|
| 应急负责人 | [姓名] | [电话] | 总体协调 |
| 技术负责人 | [姓名] | [电话] | 技术恢复 |
| 运维工程师 | [姓名] | [电话] | 执行恢复 |
| 安全负责人 | [姓名] | [电话] | 安全评估 |

### 6.2 外部支持

- 阿里云技术支持: 95187
- 域名服务商: [联系方式]

---

## 7. 文档维护

- **责任人**: 运维团队
- **审核周期**: 每半年
- **上次审核**: 2024-02-01
- **下次审核**: 2024-08-01
