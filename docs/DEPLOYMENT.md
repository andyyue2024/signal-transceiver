# 部署文档

## 概述

本文档介绍如何在各种环境中部署 Signal Transceiver 服务。

---

## 目录

1. [环境要求](#环境要求)
2. [本地开发部署](#本地开发部署)
3. [Docker 部署](#docker-部署)
4. [阿里云 ECS 部署](#阿里云-ecs-部署)
5. [阿里云容器服务部署](#阿里云容器服务部署)
6. [Nginx 配置](#nginx-配置)
7. [HTTPS 配置](#https-配置)
8. [监控配置](#监控配置)
9. [故障排除](#故障排除)

---

## 环境要求

- Python 3.11+
- pip 23.0+
- Docker 24.0+ (可选)
- Docker Compose 2.0+ (可选)

---

## 本地开发部署

### 1. 克隆代码

```bash
git clone <repository-url>
cd signal-transceiver
```

### 2. 创建虚拟环境

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 5. 初始化数据库

```bash
python -m src.cli db init
python -m src.cli db init-permissions
```

### 6. 启动服务

```bash
# 开发模式
python -m src.main

# 或使用 uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Docker 部署

### 1. 构建镜像

```bash
docker build -t signal-transceiver:latest -f docker/Dockerfile .
```

### 2. 运行容器

```bash
docker run -d \
  --name signal-transceiver \
  -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e ADMIN_API_KEY=your-admin-key \
  -v signal-data:/app/data \
  -v signal-logs:/app/logs \
  signal-transceiver:latest
```

### 3. 使用 Docker Compose

```bash
cd docker
docker-compose up -d
```

### 4. 查看日志

```bash
docker logs -f signal-transceiver
```

---

## 阿里云 ECS 部署

### 1. 创建 ECS 实例

- **规格**: 推荐 2核4G 以上
- **操作系统**: Ubuntu 22.04 LTS 或 CentOS 8
- **安全组**: 开放 80, 443, 8000 端口

### 2. 安装 Docker

```bash
# Ubuntu
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. 部署应用

```bash
# 克隆代码
git clone <repository-url>
cd signal-transceiver

# 配置环境变量
cp .env.example .env
vim .env

# 启动服务
cd docker
docker-compose up -d
```

### 4. 配置域名解析

在阿里云 DNS 控制台添加 A 记录指向 ECS 公网 IP。

---

## 阿里云容器服务部署

### 1. 创建容器镜像

```bash
# 登录阿里云容器镜像服务
docker login registry.cn-hangzhou.aliyuncs.com

# 构建并推送镜像
docker build -t registry.cn-hangzhou.aliyuncs.com/your-namespace/signal-transceiver:v1.0.0 -f docker/Dockerfile .
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/signal-transceiver:v1.0.0
```

### 2. 创建 Kubernetes 部署文件

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: signal-transceiver
spec:
  replicas: 2
  selector:
    matchLabels:
      app: signal-transceiver
  template:
    metadata:
      labels:
        app: signal-transceiver
    spec:
      containers:
      - name: app
        image: registry.cn-hangzhou.aliyuncs.com/your-namespace/signal-transceiver:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        - name: ADMIN_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: admin-api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: signal-transceiver
spec:
  selector:
    app: signal-transceiver
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. 部署到集群

```bash
kubectl apply -f deployment.yaml
```

---

## Nginx 配置

### 反向代理配置

```nginx
upstream signal_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://signal_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # WebSocket 支持
    location /ws/ {
        proxy_pass http://signal_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

---

## HTTPS 配置

### 使用 Let's Encrypt

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### Nginx HTTPS 配置

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # ... 其他配置
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 监控配置

### Prometheus 配置

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'signal-transceiver'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/monitor/metrics'
```

### Grafana 仪表盘

导入预配置的仪表盘或创建自定义面板。

### 阿里云监控

1. 在 ECS 控制台启用云监控
2. 配置报警规则
3. 设置通知方式（短信、邮件、钉钉）

---

## 故障排除

### 常见问题

#### 1. 数据库连接失败

```bash
# 检查数据库文件权限
ls -la data/

# 重新初始化
python -m src.cli db init
```

#### 2. 端口被占用

```bash
# 查看端口占用
lsof -i :8000

# 终止进程
kill -9 <PID>
```

#### 3. Docker 容器无法启动

```bash
# 查看容器日志
docker logs signal-transceiver

# 进入容器调试
docker exec -it signal-transceiver /bin/bash
```

#### 4. 内存不足

```bash
# 增加 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 备份与恢复

### 备份数据库

```bash
# 使用 CLI 工具
python -m src.cli db backup

# 或使用 API
curl -X POST -H "X-API-Key: admin-key" http://localhost:8000/api/v1/admin/backups/create
```

### 恢复数据库

```bash
# 使用 API
curl -X POST -H "X-API-Key: admin-key" http://localhost:8000/api/v1/admin/backups/{filename}/restore
```

### 定时备份 (Cron)

```bash
# 每天凌晨2点备份
0 2 * * * cd /path/to/signal-transceiver && python -m src.cli db backup
```

---

## 安全建议

1. **强密码**: 使用强随机密码作为 SECRET_KEY 和 ADMIN_API_KEY
2. **HTTPS**: 生产环境必须使用 HTTPS
3. **防火墙**: 只开放必要端口
4. **定期更新**: 定期更新依赖包和系统
5. **日志监控**: 监控异常登录和操作
6. **API Key 轮换**: 定期更换 API Key
