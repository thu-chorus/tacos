# TaCOS 生产环境部署指南

> 本文档介绍如何使用 systemd 在 Linux 服务器上部署 TaCOS 完整系统。

## 📋 目录

- [服务架构](#服务架构)
- [快速部署步骤](#快速部署步骤)
- [环境变量配置](#环境变量配置)
- [Django 服务部署](#django-服务部署)
- [Celery 服务部署](#celery-服务部署)
- [Nginx 配置](#nginx-配置)
- [服务管理](#服务管理)
- [故障排查](#故障排查)

## 服务架构

```
┌─────────────┐
│   Nginx     │  反向代理 + 静态文件
└──────┬──────┘
       │
┌──────▼──────┐
│  Gunicorn   │  Django 应用
│  (tacos)    │
└──────┬──────┘
       │
       ├─────► PostgreSQL (数据库)
       │
       └─────► Redis ◄────┬─── Celery Worker (异步任务)
                          └─── Celery Beat (定时任务)
```

**需要运行的服务：**

| 服务 | 作用 | 服务名 |
|------|------|--------|
| Redis | 消息队列 | `redis` |
| Django (Gunicorn) | Web应用 | `tacos` |
| Celery Worker | 异步任务（PDF水印、Excel导出） | `tacos-celery-worker` |
| Celery Beat | 定时任务（清理、长期未登录停用、更新寿星） | `tacos-celery-beat` |
| Nginx | 反向代理 | `nginx` |
| PostgreSQL | 数据库（推荐） | `postgresql` |

## 快速部署步骤

### 1. 安装依赖

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-venv python3-pip git nginx redis-server postgresql postgresql-contrib fonts-noto-cjk -y
```

### 2. 准备项目

```bash
# 部署项目到 /var/www/tacos
cd /var/www/tacos/tacos_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 3. 配置环境变量

```bash
cd /var/www/tacos/tacos_backend
cp .env.production.example .env.production.local
nano .env.production.local
```

修改以下关键配置：
- `SECRET_KEY` - 使用 `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` 生成
- `DEBUG=false`
- `ALLOWED_HOSTS` - 你的域名
- `DATABASE_URL` - PostgreSQL连接
- `CELERY_BROKER_URL=redis://localhost:6379/0`
- `WATERMARK_FONT_PATH=/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc`

### 4. 初始化数据库

```bash
source .venv/bin/activate
python manage.py migrate --settings=config.settings.production
python manage.py createsuperuser --settings=config.settings.production
python manage.py collectstatic --noinput --settings=config.settings.production
```

### 5. 设置权限

```bash
sudo mkdir -p /var/log/tacos /var/www/tacos/tacos_media
sudo chown -R www-data:www-data /var/log/tacos /var/www/tacos/tacos_media /var/www/tacos/tacos_backend
sudo chmod 600 /var/www/tacos/tacos_backend/.env.production.local
```

### 6. 安装 systemd 服务

```bash
# 复制服务文件
sudo cp /var/www/tacos/tacos.service.example /etc/systemd/system/tacos.service
sudo cp /var/www/tacos/tacos-celery-worker.service.example /etc/systemd/system/tacos-celery-worker.service
sudo cp /var/www/tacos/tacos-celery-beat.service.example /etc/systemd/system/tacos-celery-beat.service

# 根据实际路径编辑（如果不是 /var/www/tacos）
sudo nano /etc/systemd/system/tacos.service
sudo nano /etc/systemd/system/tacos-celery-worker.service
sudo nano /etc/systemd/system/tacos-celery-beat.service
```

### 7. 启动所有服务

```bash
sudo systemctl daemon-reload
sudo systemctl start redis tacos tacos-celery-worker tacos-celery-beat
sudo systemctl enable redis tacos tacos-celery-worker tacos-celery-beat
```

### 8. 验证部署

```bash
# 检查所有服务状态
sudo systemctl status redis tacos tacos-celery-worker tacos-celery-beat

# 查看日志
sudo journalctl -u tacos -u tacos-celery-worker -u tacos-celery-beat -f
```

## 环境变量配置

### 配置文件

| 文件 | 用途 | 提交到Git |
|------|------|----------|
| `.env.example` | 开发环境模板 | 是 |
| `.env` | 开发环境实际配置 | **否** |
| `.env.production.example` | 生产环境模板 | 是 |
| `.env.production.local` | 生产环境实际配置 | **否** |

### 完整配置示例

```bash
# Django
SECRET_KEY=生成的强随机密钥
DEBUG=false
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_SETTINGS_MODULE=config.settings.production

# Database
DATABASE_URL=postgres://tacos_user:password@localhost:5432/tacos_db

# CORS/CSRF
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# JWT
ACCESS_TOKEN_LIFETIME_MINUTES=1440
REFRESH_TOKEN_LIFETIME_DAYS=10

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# Watermark
WATERMARK_FONT_PATH=/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc
```

## Django 服务部署

### service 文件要点

项目提供了 `tacos.service.example` 模板，主要配置项：

```ini
[Service]
User=www-data
WorkingDirectory=/var/www/tacos/tacos_backend
EnvironmentFile=/var/www/tacos/tacos_backend/.env.production.local

ExecStart=/var/www/tacos/tacos_backend/.venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/gunicorn/tacos.sock \
    --timeout 120 \
    --access-logfile /var/log/tacos/access.log \
    --error-logfile /var/log/tacos/error.log \
    config.wsgi:application

RuntimeDirectory=gunicorn
ReadWritePaths=/var/www/tacos/tacos_backend /var/www/tacos/tacos_media /var/log/tacos
```

**关键点：**
- 使用 Unix Socket (`/run/gunicorn/tacos.sock`) 而非 TCP 端口
- `EnvironmentFile` 读取 `.env.production.local`
- `RuntimeDirectory` 自动创建 `/run/gunicorn/` 目录

### 验证部署

```bash
# 检查服务状态
sudo systemctl status tacos

# 检查 socket 文件
ls -l /run/gunicorn/tacos.sock

# 测试连接
curl --unix-socket /run/gunicorn/tacos.sock http://localhost/api/v1/common/health/

# 查看日志
sudo tail -f /var/log/tacos/error.log
```

## Celery 服务部署

### 为什么需要 Celery？

**异步任务：**
- 🎼 PDF 乐谱水印生成（耗时操作，不阻塞用户）
- 📊 Excel 导出（作业记录、队员信息）

**定时任务：**
- ⏰ 每小时清理过期的下载/导出任务
- 👤 每天停用超过 6 个月未登录的在队成员
- 🎂 每月1号自动更新"本月寿星"称号

### 安装 Redis

```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
redis-cli ping  # 应返回 PONG
```

**可选：设置 Redis 密码**

```bash
sudo nano /etc/redis/redis.conf
# 添加: requirepass your_password

sudo systemctl restart redis

# 更新 .env.production.local
CELERY_BROKER_URL=redis://:your_password@localhost:6379/0
```

### 部署 Celery Worker 和 Beat

使用项目提供的模板：

```bash
sudo cp /var/www/tacos/tacos-celery-worker.service.example /etc/systemd/system/tacos-celery-worker.service
sudo cp /var/www/tacos/tacos-celery-beat.service.example /etc/systemd/system/tacos-celery-beat.service

sudo systemctl daemon-reload
sudo systemctl start tacos-celery-worker tacos-celery-beat
sudo systemctl enable tacos-celery-worker tacos-celery-beat
```

### 验证 Celery

```bash
# 检查服务
sudo systemctl status tacos-celery-worker tacos-celery-beat

# 查看日志
sudo tail -f /var/log/tacos/celery-worker.log
sudo tail -f /var/log/tacos/celery-beat.log

# 通过 Django Shell 测试
cd /var/www/tacos/tacos_backend && source .venv/bin/activate
python manage.py shell --settings=config.settings.production

# 在 shell 中：
from config.celery import debug_task
result = debug_task.delay()
print(f"Task ID: {result.id}, Status: {result.status}")
```

## Nginx 配置

### 配置文件示例

```nginx
upstream tacos_backend {
    server unix:/run/gunicorn/tacos.sock fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/tacos/tacos_backend/static/;
    }

    location /media/ {
        alias /var/www/tacos/tacos_media/;
    }

    location /api/ {
        proxy_pass http://tacos_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        proxy_pass http://tacos_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /var/www/tacos/tacos_frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

### 部署 Nginx

```bash
sudo nano /etc/nginx/sites-available/tacos
# 粘贴上面的配置

sudo ln -s /etc/nginx/sites-available/tacos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 配置 HTTPS（使用 Let's Encrypt）
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## 服务管理

### 常用命令

```bash
# 查看所有服务状态
sudo systemctl status redis tacos tacos-celery-worker tacos-celery-beat nginx

# 重启所有服务
sudo systemctl restart tacos tacos-celery-worker tacos-celery-beat

# 查看实时日志
sudo journalctl -u tacos -u tacos-celery-worker -u tacos-celery-beat -f

# 查看应用日志
sudo tail -f /var/log/tacos/error.log
sudo tail -f /var/log/tacos/celery-worker.log
```

### 更新部署

```bash
cd /var/www/tacos
git pull origin main

cd tacos_backend
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --settings=config.settings.production
python manage.py collectstatic --noinput --settings=config.settings.production

sudo systemctl restart tacos tacos-celery-worker tacos-celery-beat
```

### 修改环境变量后

```bash
sudo nano /var/www/tacos/tacos_backend/.env.production.local
# 修改配置

sudo systemctl restart tacos tacos-celery-worker tacos-celery-beat
sudo systemctl status tacos tacos-celery-worker tacos-celery-beat
```

## 故障排查

### Django 服务无法启动

```bash
# 查看详细错误
sudo journalctl -u tacos -xe

# 检查 socket 文件
ls -l /run/gunicorn/tacos.sock

# 检查权限
ps aux | grep gunicorn
ls -la /run/gunicorn/

# 手动测试
cd /var/www/tacos/tacos_backend
source .venv/bin/activate
gunicorn --bind unix:/tmp/test.sock config.wsgi:application
```

### Celery Worker 连接失败

```bash
# 检查 Redis
redis-cli ping

# 检查环境变量
sudo cat /var/www/tacos/tacos_backend/.env.production.local | grep CELERY_BROKER_URL

# 查看详细日志
sudo journalctl -u tacos-celery-worker -xe
sudo tail -100 /var/log/tacos/celery-worker.log

# 手动测试
cd /var/www/tacos/tacos_backend && source .venv/bin/activate
celery -A config worker -l debug
```

### 定时任务不执行

```bash
# 检查 Beat 服务
sudo systemctl status tacos-celery-beat
sudo journalctl -u tacos-celery-beat -f

# 检查 schedule 文件权限
ls -l /var/www/tacos/tacos_backend/celerybeat-schedule
sudo chown www-data:www-data /var/www/tacos/tacos_backend/celerybeat-schedule

# 查看即将执行的任务
cd /var/www/tacos/tacos_backend && source .venv/bin/activate
celery -A config inspect scheduled
```

### 权限问题

```bash
sudo chown -R www-data:www-data /var/www/tacos/tacos_backend
sudo chown -R www-data:www-data /var/www/tacos/tacos_media
sudo chown -R www-data:www-data /var/log/tacos
sudo chmod 600 /var/www/tacos/tacos_backend/.env.production.local
```

### Nginx 502 Bad Gateway

```bash
# 检查 Gunicorn 服务
sudo systemctl status tacos

# 检查 socket 权限
ls -l /run/gunicorn/tacos.sock
sudo -u www-data test -r /run/gunicorn/tacos.sock && echo "OK" || echo "Permission Denied"

# 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

## 性能优化

### Gunicorn Workers

根据 CPU 核心数调整：`workers = (2 * CPU核心数) + 1`

```bash
sudo nano /etc/systemd/system/tacos.service
# 修改 --workers 参数

sudo systemctl daemon-reload
sudo systemctl restart tacos
```

### Celery Workers

```bash
sudo nano /etc/systemd/system/tacos-celery-worker.service
# 添加 --concurrency=4

sudo systemctl daemon-reload
sudo systemctl restart tacos-celery-worker
```

### 日志轮转

```bash
sudo nano /etc/logrotate.d/tacos

# 添加：
/var/log/tacos/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload tacos tacos-celery-worker tacos-celery-beat >/dev/null 2>&1 || true
    endscript
}
```

## 安全检查清单

- [ ] `DEBUG=false`
- [ ] 强随机 `SECRET_KEY`
- [ ] `ALLOWED_HOSTS` 仅包含实际域名
- [ ] 使用 HTTPS
- [ ] Redis 设置密码（推荐）
- [ ] PostgreSQL 强密码
- [ ] `.env.production.local` 权限为 600
- [ ] 定期备份数据库
- [ ] 配置防火墙

## 完整启动顺序

```bash
# 1. 基础服务
sudo systemctl start redis postgresql

# 2. Django
sudo systemctl start tacos

# 3. Celery
sudo systemctl start tacos-celery-worker tacos-celery-beat

# 4. Nginx
sudo systemctl start nginx

# 验证
sudo systemctl status redis tacos tacos-celery-worker tacos-celery-beat nginx
```

部署完成后，请通过健康检查、服务状态和日志确认系统正常运行。
