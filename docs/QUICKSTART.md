# 快速启动指南

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd signal-transceiver

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库初始化

```bash
# 初始化数据库
alembic upgrade head

# 或者直接运行应用（会自动创建表）
python src/main.py
```

### 3. 运行应用

```bash
# 开发模式
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 或使用内置脚本
python src/main.py
```

### 4. 访问应用

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- 管理后台: http://localhost:8000/admin/login

## 📋 功能测试清单

### ✅ 基础功能测试

1. **健康检查**
```bash
curl http://localhost:8000/health
```

2. **用户注册**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

3. **用户登录**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

4. **创建策略**（需要 API Key）
```bash
curl -X POST http://localhost:8000/api/v1/strategies \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "name": "Test Strategy",
    "description": "测试策略",
    "type": "trading"
  }'
```

5. **上报数据**（需要 API Key）
```bash
curl -X POST http://localhost:8000/api/v1/data \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "type": "signal",
    "strategy_id": 1,
    "symbol": "AAPL",
    "description": "买入信号",
    "metadata": {"price": 150.0}
  }'
```

6. **创建订阅**
```bash
curl -X POST http://localhost:8000/api/v1/subscriptions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "name": "我的订阅",
    "type": "polling",
    "filters": {"strategy_ids": [1]}
  }'
```

7. **获取订阅数据**
```bash
curl http://localhost:8000/api/v1/subscriptions/1/data \
  -H "X-API-Key: YOUR_API_KEY"
```

### 🆕 新功能测试

8. **CSV 数据导入**
```bash
# 创建测试 CSV 文件
echo "type,strategy_id,symbol,execute_date,description,metadata
signal,1,AAPL,2024-01-01,Buy signal,{\"price\": 150.0}
data,1,GOOGL,2024-01-02,Market data,{\"volume\": 1000000}" > test_import.csv

# 导入数据
curl -X POST http://localhost:8000/api/v1/import/csv \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@test_import.csv" \
  -F "skip_errors=true"
```

9. **JSON 数据导入**
```bash
curl -X POST http://localhost:8000/api/v1/import/json \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '[
    {
      "type": "signal",
      "strategy_id": 1,
      "symbol": "MSFT",
      "execute_date": "2024-01-03",
      "description": "Sell signal",
      "metadata": {"price": 300.0}
    }
  ]'
```

10. **下载导入模板**
```bash
# CSV 模板
curl http://localhost:8000/api/v1/import/template/csv -o import_template.csv

# JSON 模板
curl http://localhost:8000/api/v1/import/template/json -o import_template.json
```

## 🧪 运行测试

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行单元测试
```bash
pytest tests/unit/ -v
```

### 运行集成测试
```bash
pytest tests/integration/ -v
```

### 运行综合功能测试
```bash
python comprehensive_test.py
```

### 测试覆盖率
```bash
pytest tests/ --cov=src --cov-report=html
# 查看报告: open htmlcov/index.html
```

## 🐳 Docker 部署

### 构建镜像
```bash
docker build -t signal-transceiver:latest -f docker/Dockerfile .
```

### 运行容器
```bash
docker run -d \
  --name signal-transceiver \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e DEBUG=false \
  signal-transceiver:latest
```

### 使用 Docker Compose
```bash
cd docker
docker-compose up -d
```

## 📊 监控和维护

### 查看系统状态
```bash
curl http://localhost:8000/api/v1/system/health
```

### 查看 Prometheus 指标
```bash
curl http://localhost:8000/api/v1/system/metrics
```

### 数据库备份
```bash
curl -X POST http://localhost:8000/api/v1/system/backup \
  -H "X-API-Key: ADMIN_API_KEY" \
  -d '{"compressed": true}'
```

### 查看日志
```bash
# 实时日志
tail -f logs/app.log

# 搜索日志
curl http://localhost:8000/api/v1/logs/search?level=ERROR \
  -H "X-API-Key: YOUR_API_KEY"
```

## 🔧 常见问题

### 1. 端口被占用
```bash
# 查找占用端口的进程
# Windows
netstat -ano | findstr :8000
# Linux
lsof -i :8000

# 使用其他端口
uvicorn src.main:app --port 8080
```

### 2. 数据库锁定
```bash
# 删除数据库文件重新初始化
rm data/app.db
python src/main.py
```

### 3. 依赖安装失败
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. bcrypt 安装问题（Windows）
```bash
# 安装 Visual C++ 构建工具
# 或使用预编译轮子
pip install bcrypt --only-binary :all:
```

## 📚 更多文档

- [API 文档](API.md)
- [部署文档](DEPLOYMENT.md)
- [功能特性](../features.txt)
- [完成报告](COMPLETION_REPORT.md)
- [增强计划](ENHANCEMENT_PLAN.md)

## 🎯 生产环境配置

### 环境变量
```bash
# .env 文件
DEBUG=false
SECRET_KEY=your-production-secret-key-change-this
DATABASE_URL=sqlite+aiosqlite:///data/app.db
LOG_LEVEL=INFO
ADMIN_API_KEY=your-admin-api-key

# CORS（如果需要）
CORS_ORIGINS=["https://yourdomain.com"]
```

### Nginx 配置
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Systemd 服务
```ini
# /etc/systemd/system/signal-transceiver.service
[Unit]
Description=Signal Transceiver API Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/signal-transceiver
Environment="PATH=/opt/signal-transceiver/.venv/bin"
ExecStart=/opt/signal-transceiver/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl enable signal-transceiver
sudo systemctl start signal-transceiver
sudo systemctl status signal-transceiver
```

## 🎉 完成！

现在你的 Signal Transceiver 应用已经准备就绪！

访问 http://localhost:8000/docs 查看完整的 API 文档。
