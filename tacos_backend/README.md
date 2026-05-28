# TaCOS 后端 (Django + DRF)

TaCOS (清华合唱队在线系统) 后端。实现身份认证 (JWT)、人事管理、谱务管理和活动管理，采用统一的 API 响应格式。

## 技术栈
- Django 4.x + Django REST Framework (DRF)
- JWT (SimpleJWT) 身份认证
- PostgreSQL (生产环境) / SQLite (开发环境)
- 密码加密: bcrypt
- Pillow 图片验证与头像处理
- Celery + Redis (异步任务处理 - PDF 水印、Excel 导出)
- Celery Beat (定时任务 - 清理过期文件、停用长期未登录在队成员、更新寿星称号)
- Gunicorn + Systemd (生产部署)

## 项目结构
```
tacos_backend/
├── manage.py
├── requirements.txt
├── .env.example
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── urls.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── development.py
│       ├── production.py
│       └── testing.py
└── apps/
    ├── common/
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── urls.py
    │   ├── views.py            # /api/v1/common/health/
    │   ├── pagination.py
    │   ├── permissions.py
    │   ├── exceptions.py
    │   ├── utils.py
    │   └── viewsets.py
    ├── authentication/
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── models.py           # 自定义用户模型 (user_id作为用户名)
    │   ├── serializers.py
    │   ├── views.py            # 登录/刷新/个人信息/登出
    │   ├── urls.py
    │   ├── utils.py            # user_id认证后端
    │   ├── tests/
    │   └── migrations/
    ├── personnel/
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── models.py           # 成员, 教师
    │   ├── serializers.py
    │   ├── views.py            # ViewSets
    │   ├── urls.py             # 路由器
    │   ├── filters.py
    │   ├── permissions.py
    │   ├── tests/
    │   └── migrations/
    ├── sheet_music/
        ├── __init__.py
        ├── apps.py
        ├── models.py           # 乐谱, 乐谱下载日志
        ├── serializers.py
        ├── views.py            # ViewSet + 下载路由
        ├── urls.py             # 路由器
        ├── utils.py
        ├── watermark.py        # PDF 水印与页面处理
        ├── tests/
        └── migrations/
    └── events/
        ├── models.py           # 活动、签到、作业
        ├── serializers.py
        ├── views.py
        ├── urls.py
        ├── tests/
        └── migrations/
```

## 统一响应格式
所有JSON接口返回:
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```
文件下载返回带水印的PDF流，内容和文件名包含学号和姓名。

## API 权限控制

系统采用严格的权限控制策略，确保数据安全：

### 权限类

1. **IsAuthenticatedReadAdminWrite** - 读需登录，写需管理员
   - 用于：系统公告 (`/api/v1/common/announcements/`)、乐谱管理 (`/api/v1/sheets/`)

2. **IsAdminOrEventAdmin** - 读需登录，写需管理员或活动管理员
   - 用于：活动管理 (`/api/v1/events/`)

3. **IsAdmin** - 所有操作需管理员
   - 用于：外请教师 (`/api/v1/instructors/`)、称号 (`/api/v1/titles/`) 等

4. **IsAdminOrSelfReadOnly** - 读需登录，创建/删除需管理员
   - 用于：队员信息 (`/api/v1/members/`)

5. **IsSelfOrAdmin** - 管理员或本人可操作
   - 用于：成员自助更新和头像维护 (`/api/v1/members/<public_id>/avatar/`)

6. **AllowAny** - 无需认证（仅特殊端点）
   - 用于：登录 (`/api/v1/auth/login/`)、token刷新、加密下载链接 (`/api/v1/common/media/`)

### 重要说明

- **除登录、token刷新和加密下载链接外，所有API端点都要求用户登录**
- 匿名用户访问任何业务API将返回 `401 Unauthorized`
- 权限不足的操作将返回 `403 Forbidden`
- 加密下载链接 (`/api/v1/common/media/`) 通过签名token验证，无需JWT认证
- 管理员手动将成员 `status` 改为 `ALUMNI` 后，系统创建 `AlumniProfile` 联系窗口。
- Celery Beat 每天会将超过 6 个月未登录的 `ACTIVE` 成员设为 `INACTIVE`，不会修改 `ALUMNI`。
- `INACTIVE` 成员登录时会被拒绝，并提示“账号已停用，请联系管理员协助处理”。
- `User.is_active` 仅作为平台级账号开关；成员生命周期状态以 `Member.status` 为准。
- 任意账号若还没有成员档案，登录后会进入首次信息完善流程；管理员权限由 `User.role` 控制。
- 成员头像上传后存储为图片文件；前端默认上传裁剪后的方形 PNG，小头像按圆形展示，点击预览原始方图。
- 校友可查看并报名显式设置 `visible_to_alumni=true` 的活动，也可查看显式校友可见的乐谱，以及校友可见活动关联的乐谱。
- 校友不能担任 `visible_to_alumni=false` 活动的活动管理员。

### 活动管理
- 创建活动 (仅管理员)
```bash
curl -s -X POST http://localhost:8000/api/v1/events/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "合唱排练",
    "introduction": "周例排练",
    "announcement": "",
    "start_date": "2025-10-01",
    "end_date": "2025-10-01",
    "visibility": "ALL",
    "visible_to_alumni": false,
    "admins": [1],
    "participants": []
  }'
```

- 列出活动 (筛选 + 搜索)
```bash
curl -s 'http://localhost:8000/api/v1/events/?page=1&page_size=20&only_participated=true&search=排练'
```

- 参加活动 (成员)
```bash
curl -s -X POST http://localhost:8000/api/v1/events/1/join/ \
  -H "Authorization: Bearer <token>"
```

### 活动签到
- 活跃签到会话状态
```bash
curl -s -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/events/1/checkin/status/
```

- 列出签到会话 (成员/管理员)
```bash
curl -s -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/events/1/checkin/sessions/
```

- 创建签到会话 (管理员)
```bash
curl -s -X POST -H "Authorization: Bearer <token>" \
  -H 'Content-Type: application/json' \
  -d '{"name":"晚到签到","type":"PASSWORD","password":"1234"}' \
  http://localhost:8000/api/v1/events/1/checkin/start/
```

- 开始/停止签到会话 (管理员)
```bash
curl -s -X POST -H "Authorization: Bearer <token>" \
  -H 'Content-Type: application/json' \
  -d '{"session_id":2}' \
  http://localhost:8000/api/v1/events/1/checkin/begin/

curl -s -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/events/1/checkin/stop/
```

- 提交签到 (成员)
```bash
# 密码模式
curl -s -X POST -H "Authorization: Bearer <token>" \
  -H 'Content-Type: application/json' \
  -d '{"password":"1234"}' \
  http://localhost:8000/api/v1/events/1/checkin/submit/

# 位置模式
curl -s -X POST -H "Authorization: Bearer <token>" \
  -H 'Content-Type: application/json' \
  -d '{"lat":40.0, "lng":116.3}' \
  http://localhost:8000/api/v1/events/1/checkin/submit/
```

- 签到记录和统计
```bash
curl -s -H "Authorization: Bearer <token>" \
  'http://localhost:8000/api/v1/events/1/checkin/records/?page=1&page_size=20'

curl -s -H "Authorization: Bearer <token>" \
  'http://localhost:8000/api/v1/events/1/checkin/summary/?session_id=2'
```

### 作业管理
- 列出作业 (成员/管理员)
```bash
curl -s -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/events/1/assignments/
```

- 创建作业 (管理员)
```bash
curl -s -X POST -H "Authorization: Bearer <token>" \
  -H 'Content-Type: application/json' \
  -d '{"title":"第一次作业","description":"请完成","deadline":"2025-10-05T12:00:00Z"}' \
  http://localhost:8000/api/v1/events/1/assignments/create/
```

- 上传作业附件 (管理员)
```bash
curl -s -X POST -H "Authorization: Bearer <token>" \
  -F 'file=@/path/to/guide.txt' \
  http://localhost:8000/api/v1/events/1/assignments/2/attachments/
```

- 提交作业 (成员; 文本 + 文件)
```bash
curl -s -X POST -H "Authorization: Bearer <token>" \
  -F 'text=完成了' \
  -F 'files=@/path/to/answer.txt' \
  http://localhost:8000/api/v1/events/1/assignments/2/submit/
```

- 列出提交 (管理员; 筛选: 姓名, 学号, 声部)
```bash
curl -s -H "Authorization: Bearer <token>" \
  'http://localhost:8000/api/v1/events/1/assignments/2/submissions/?name=张'
```

- 我的提交 (成员)
```bash
curl -s -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/events/1/assignments/2/my-submission/
```

- 评分提交 (管理员)
```bash
curl -s -X POST -H "Authorization: Bearer <token>" \
  -H 'Content-Type: application/json' \
  -d '{"submission_id":5, "graded_score":95, "graded_comment":"很好"}' \
  http://localhost:8000/api/v1/events/1/assignments/2/grade/
```

## 快速开始

### 开发环境 (SQLite)

1) **克隆仓库**
```bash
git clone <repository-url>
cd tacos/tacos_backend
```

2) **创建并激活虚拟环境**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3) **安装依赖**
```bash
pip install -U pip
pip install -r requirements.txt
```

4) **配置环境变量**
```bash
cp .env.example .env
```
编辑 `.env` 文件，设置开发环境配置：
```bash
DJANGO_SETTINGS_MODULE=config.settings.development
DEBUG=True
SECRET_KEY=your-dev-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

5) **数据库迁移**
```bash
python manage.py makemigrations
python manage.py migrate
```

6) **创建超级用户 (可选)**
```bash
python manage.py createsuperuser
```

7) **启动 Redis (异步任务消息队列)**
```bash
# macOS (使用 Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# 验证 Redis 运行
redis-cli ping  # 应返回 PONG
```

8) **启动 Celery Worker (处理异步任务)**

在新的终端窗口中：
```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动 Celery worker
celery -A config worker -l info

# 可选：启动 Celery Beat (定时任务调度)
# 在另一个终端窗口中
celery -A config beat -l info
```

9) **运行开发服务器**
```bash
python manage.py runserver 0.0.0.0:8000
```

10) **访问应用**
- API健康检查: http://localhost:8000/api/v1/common/health/
- 管理后台: http://localhost:8000/admin/

### 生产环境部署

> **📚 完整部署指南**: 请参考项目根目录的 [SYSTEMD_DEPLOYMENT.md](../SYSTEMD_DEPLOYMENT.md) 获取详细的生产环境部署步骤，包括：
> - Django (Gunicorn) 服务配置
> - Celery Worker 和 Beat 服务配置
> - Redis 消息队列配置
> - PostgreSQL 数据库配置
> - Nginx 反向代理配置

**生产环境需要运行的服务：**
1. **Redis** - Celery 消息队列
2. **Django (Gunicorn)** - Web 应用服务器
3. **Celery Worker** - 异步任务处理
4. **Celery Beat** - 定时任务调度
5. **Nginx** - 反向代理
6. **PostgreSQL** - 数据库（推荐）

#### 快速部署命令

```bash
# 1. 安装系统依赖
sudo apt update
sudo apt install python3 python3-venv python3-pip postgresql nginx

# 2. 创建数据库
sudo -u postgres psql
CREATE DATABASE tacos_db;
CREATE USER tacos_user WITH PASSWORD 'your_secure_password';
\c tacos_db
GRANT ALL PRIVILEGES ON DATABASE tacos_db TO tacos_user;
GRANT CREATE ON SCHEMA public TO tacos_user;
\q


# 3. 部署应用
sudo mkdir -p /var/www/tacos
sudo chown $USER:$USER /var/www/tacos
cd /var/www/tacos
git clone <repository-url> .
cd tacos_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.production.example .env.production.local
nano .env.production.local  # 编辑配置

# 5. 数据库迁移
python manage.py migrate --settings=config.settings.production
python manage.py collectstatic --noinput --settings=config.settings.production
python manage.py createsuperuser --settings=config.settings.production

# 6. 配置并启动 Systemd 服务
sudo cp /var/www/tacos/tacos.service.example /etc/systemd/system/tacos.service
sudo nano /etc/systemd/system/tacos.service  # 确认路径配置
sudo systemctl daemon-reload
sudo systemctl start tacos
sudo systemctl enable tacos

# 7. 配置 Nginx
sudo nano /etc/nginx/sites-available/tacos  # 参考 SYSTEMD_DEPLOYMENT.md
sudo ln -s /etc/nginx/sites-available/tacos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 8. 配置 SSL
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

#### 重要配置文件

**`.env.production.local` 示例**:
```bash
SECRET_KEY=your-production-secret-key-here
DEBUG=false
DJANGO_SETTINGS_MODULE=config.settings.production
DATABASE_URL=postgres://tacos_user:password@localhost:5432/tacos_db
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

**生成安全的 SECRET_KEY**:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### 验证部署

```bash
# 检查服务状态
sudo systemctl status tacos

# 检查日志
sudo journalctl -u tacos -f

# 测试 API
curl http://localhost/api/v1/common/health/
```

#### 更多信息

详细的部署步骤、配置说明、故障排除等，请查看：
- **[SYSTEMD_DEPLOYMENT.md](../SYSTEMD_DEPLOYMENT.md)** - 完整的 Systemd 部署指南
- **[tacos.service.example](../tacos.service.example)** - Systemd 服务配置模板

## 本地开发指南

### 代码格式化

项目使用 `black` 和 `isort` 进行代码格式化：

```bash
# 使用项目根目录的格式化脚本
cd /path/to/tacos
./scripts/format_code.sh  # Linux/Mac
```

手动格式化：
```bash
cd tacos_backend
black .
isort .
```

### 运行测试

使用测试设置配置：
```bash
export DJANGO_SETTINGS_MODULE=config.settings.testing

python manage.py test -v 2
```

运行特定测试：
```bash
# 测试特定应用
python manage.py test apps.authentication -v 2

# 测试特定文件
python manage.py test apps.personnel.tests.test_birthday_titles -v 2
```

## API使用文档

基础URL: `http://localhost:8000/api/v1`

### 身份认证
- 登录
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"2021012345","password":"password123"}'
```
响应包含 `data.token` 和 `data.refresh_token`。

- 刷新令牌
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh":"<refresh_token>"}'
```

- 当前用户
```bash
curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

- 登出 (无状态)
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <token>"
```

### 人事管理
- 创建成员 (仅管理员)
```bash
curl -s -X POST http://localhost:8000/api/v1/members/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <token>" \
  -d '{
    "user_id":"2021012345",
    "name":"张三",
    "gender":"男",
    "voice_part":"T1",
    "department":"计算机系",
    "class_name":"计15",
    "phone_number":"13812345678",
    "email":"zhangsan@example.com",
    "dorm":"1-101",
    "birthday":"2000-01-01",
    "hometown":"北京",
    "ethnicity":"汉族",
    "political_status":"共青团员",
    "political_affiliation":"艺术团",
    "is_specialty":false,
    "is_centralized":false,
    "position":"队员",
    "join_month":"2021-09",
    "tier":"二队",
    "portfolio":"档案"
  }'
```

注意: 新创建的成员默认对非管理员/非本人查看者隐藏以下字段: 家乡、民族、政治面貌、政治归属。

- 列出成员 (筛选 + 分页)
```bash
curl -s 'http://localhost:8000/api/v1/members/?page=1&page_size=20&voice_part=T1&status=ACTIVE&search=张'
```

- 上传本人头像或管理员维护队员头像
```bash
curl -s -X POST http://localhost:8000/api/v1/members/<public_id>/avatar/ \
  -H "Authorization: Bearer <token>" \
  -F 'avatar=@/path/to/avatar.png;type=image/png'
```

头像仅支持 JPG、PNG、WebP，大小不超过 2 MB。前端会上传方形裁剪图，头像缩略展示由前端按圆形裁切；删除头像使用 `DELETE /api/v1/members/<public_id>/avatar/`。

- 当前校友维护校友信息
```bash
curl -s -X PATCH http://localhost:8000/api/v1/alumni-profiles/me/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <token>" \
  -d '{"current_city":"Shanghai","industry":"Technology","company":"Example Co.","job_title":"Product Manager","graduation_month":"2023-06","bio":"Building music tools.","allow_contact":true}'
```

- 教师管理 (仅管理员)
```bash
curl -s -X POST http://localhost:8000/api/v1/instructors/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <token>" \
  -d '{"instructor_id":"110101199001011234","name":"李老师","phone_number":"13912345678"}'
```

### 乐谱管理
- 上传PDF (管理员/员工令牌)
```bash
curl -s -X POST http://localhost:8000/api/v1/sheets/ \
  -H "Authorization: Bearer <token>" \
  -F 'title=青春舞曲' \
  -F 'lyricist=王洛宾' \
  -F 'composer=王洛宾' \
  -F 'arranger=张某某' \
  -F 'introduction=经典新疆民歌' \
  -F 'visible_to_alumni=false' \
  -F 'original_file=@/path/to/file.pdf;type=application/pdf'
```

- 列出/筛选
```bash
curl -s 'http://localhost:8000/api/v1/sheets/?page=1&page_size=20&composer=王洛宾'
```

- 下载带用户信息水印和文件名的乐谱 (异步处理)

**步骤1：发起下载任务**
```bash
curl -X POST http://localhost:8000/api/v1/sheets/<sheet_id>/download/ \
  -H "Authorization: Bearer <token>"
```
返回：
```json
{
  "code": 202,
  "message": "任务已创建",
  "data": {
    "task_id": "uuid-here",
    "status": "PENDING",
    "created_at": "2025-10-28T10:00:00Z",
    "expires_at": "2025-10-28T11:00:00Z",
    "stream_url": "/api/v1/sheets/task/uuid-here/stream/?token=..."
  }
}
```

**步骤2：轮询任务状态并获取文件**
```bash
# 轮询直到状态为 COMPLETED，然后获取文件
curl -L -o out.pdf \
  -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/sheets/task/<task_id>/
```

任务处理中返回 JSON：
```json
{
  "code": 200,
  "message": "任务处理中",
  "data": {
    "task_id": "uuid-here",
    "status": "PROCESSING"
  }
}
```

任务完成后返回 PDF 文件流（带水印）。

PDF包含一个非常浅的对角线水印"清华合唱-姓名-学号"，文件名格式为`标题_<student_id>_<name>.pdf`。

**预览模式**：添加 `?preview=true` 参数，Content-Disposition 设置为 inline：
```bash
curl -L \
  -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/sheets/task/<task_id>/?preview=true"
```

**详情页完整预览**：前端使用 `?status_only=true` 轮询任务状态；任务完成后使用
响应中的 `stream_url` 作为 PDF 查看器地址，避免先把完整 PDF 下载成 Axios blob，
并支持浏览器 Range 加载。

可选: 如果中文字符渲染不正确，设置操作系统字体文件路径:
```bash
export WATERMARK_FONT_PATH=/System/Library/Fonts/PingFang.ttc
```

## 管理后台

访问 `http://localhost:8000/admin/` 使用超级用户账号登录。

## 环境变量配置

### 开发环境 (.env)
本地开发请从模板创建 `.env`，该文件不会提交到版本控制。

```bash
DJANGO_SETTINGS_MODULE=config.settings.development
DEBUG=True
SECRET_KEY=your-dev-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000
ACCESS_TOKEN_LIFETIME_MINUTES=1440  # 1天
REFRESH_TOKEN_LIFETIME_DAYS=10      # 10天
```

### 生产环境 (.env.production.local)
生产环境请从 `.env.production.example` 创建 `.env.production.local`，该文件不会提交到版本控制。

```bash
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://tacos_user:password@localhost:5432/tacos_db
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
ACCESS_TOKEN_LIFETIME_MINUTES=1440  # 1天
REFRESH_TOKEN_LIFETIME_DAYS=10      # 10天
WATERMARK_FONT_PATH=/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc
```

**注意**:
- 生产环境使用双重读取策略：
  1. systemd service 通过 `EnvironmentFile` 读取并注入环境变量
  2. Django `production.py` 也会读取作为后备
- systemd 注入的环境变量优先级更高

### 环境变量说明
- `SECRET_KEY`: Django密钥，生产环境必须设置强密钥
- `DEBUG`: 开发环境为 true，生产环境必须为 false
- `DJANGO_SETTINGS_MODULE`: 配置文件路径
- `ALLOWED_HOSTS`: 允许访问的主机列表（逗号分隔）
- `DATABASE_URL`: PostgreSQL连接字符串（生产环境）
- `CORS_ALLOWED_ORIGINS`: CORS允许的源列表（逗号分隔）
- `CSRF_TRUSTED_ORIGINS`: CSRF可信源列表（逗号分隔）
- `ACCESS_TOKEN_LIFETIME_MINUTES`: JWT访问令牌有效期（分钟），默认1440（1天）
- `REFRESH_TOKEN_LIFETIME_DAYS`: JWT刷新令牌有效期（天），默认10天
- `WATERMARK_FONT_PATH`: 水印字体路径（可选）

### JWT滑动刷新机制
系统启用了JWT滑动刷新（ROTATE_REFRESH_TOKENS），工作原理如下：
1. **Access Token** 有效期1天：用于日常API请求认证
2. **Refresh Token** 有效期10天：用于刷新过期的Access Token
3. **滑动刷新**：每次使用Refresh Token刷新时，会生成新的Refresh Token
4. **活跃续期**：只要用户在10天内有活动（触发Token刷新），登录状态就会持续延长

前端在Access Token过期（收到401响应）时，会自动使用Refresh Token刷新，对用户无感知。

## 注意事项

- **数据验证**: 输入验证遵循开发文档规则（手机号必须是中国大陆11位数字，仅支持PDF上传等）
- **分页**: 默认每页20条记录，使用 `page` 和 `page_size` 查询参数控制
- **身份认证**: 受保护的接口必须在请求头中包含 `Authorization: Bearer <token>`
- **文件上传**: 最大文件大小限制为20MB（可在Nginx配置中调整）
- **时区**: 服务器时区设置为 `Asia/Shanghai`

## 公共模块: 系统公告

接口端点 (基础路径: `/api/v1/common/announcements/`):
- `GET /` 公开列表带分页 (无需认证)
- `POST /` 创建 (仅管理员/员工)
- `PUT /{id}/` 更新 (仅管理员/员工)
- `DELETE /{id}/` 删除 (仅管理员/员工)

请求载荷:
```json
{
  "publish_time": "2025-09-25T12:00:00Z",
  "content": "系统维护公告"
}
```

响应格式遵循统一格式。

## 生日称号功能使用指南

### 1. 创建"本月寿星"称号

在称号管理页面创建一个名为"本月寿星"的称号：

```json
{
  "name": "本月寿星",
  "description": "生日在本月的队员",
  "appearance": {
    "bg_color": "#ff6b6b",
    "text_color": "#ffffff",
    "icon": {
      "name": "birthday-cake",
      "set": "ep",
      "color": "#ffffff",
      "size_px": 14
    }
  }
}
```

### 2. 配置队员生日信息

确保队员档案中包含生日信息（birthday字段）。

### 3. 部署定时任务

生产环境通过 Celery Beat 执行每月更新任务。请确保 Redis、Celery Worker 和 Celery Beat 已启动。

开发启动脚本仍会安装兼容的 django-crontab 任务；如果生产环境已经运行 Celery Beat，不需要再单独安装 crontab。

### 4. 手动触发更新

**前端界面**:
在称号管理页面点击"更新本月寿星"按钮

**API调用**:
```bash
curl -X POST http://localhost:8000/api/v1/titles/update-birthday-titles/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**管理命令**:
```bash
python manage.py update_birthday_titles
```

### 详细功能

#### 自动执行
- 时间：Celery Beat 每月1号 00:00
- 操作：清空现有"本月寿星"称号，重新授予给本月生日的队员
- 日志：查看 Celery Worker 和 Celery Beat 日志

#### 手动触发
- 前端：称号管理页面的"更新本月寿星"按钮
- API：`POST /api/v1/titles/update-birthday-titles/`
- 命令：`python manage.py update_birthday_titles`

#### 试运行模式
```bash
python manage.py update_birthday_titles --dry-run
```

### 故障排除

#### 常见问题

1. **称号不存在**
   - 解决：在称号管理中创建"本月寿星"称号

2. **Celery Beat 任务不执行**
   - 检查：`systemctl status tacos-celery-beat`
   - 验证：`systemctl status tacos-celery-worker`
   - 日志：`journalctl -u tacos-celery-beat -u tacos-celery-worker -f`

3. **前端按钮不可用**
   - 确认：已创建"本月寿星"称号
   - 检查：用户是否有管理员权限

4. **没有队员被授予称号**
   - 验证：队员是否有生日信息
   - 检查：生日月份是否正确

#### 测试验证

```bash
# 运行测试
python manage.py test apps.personnel.tests.test_birthday_titles

# 试运行检查
python manage.py update_birthday_titles --dry-run

# 查看当前月份生日的队员
python manage.py shell
>>> from apps.personnel.models import Member
>>> from django.utils import timezone
>>> Member.objects.filter(birthday__month=timezone.now().month, birthday__isnull=False)
```

### 扩展开发

#### 添加其他生日相关称号

1. 修改 `tacos_backend/config/celery.py` 中的 Beat 配置：
```python
app.conf.beat_schedule["update-quarterly-birthday-title"] = {
    "task": "apps.personnel.tasks.update_quarterly_birthday_title",
    "schedule": crontab(minute=0, hour=3, day_of_month=1, month_of_year="1,4,7,10"),
}
```

2. 实现对应的任务函数：
```python
def update_quarterly_birthday_title():
    current_month = timezone.now().month
    quarter_months = {1: [1,2,3], 4: [4,5,6], 7: [7,8,9], 10: [10,11,12]}
    # 实现季度生日逻辑
```

### 添加生日提醒功能

```python
app.conf.beat_schedule["send-birthday-notifications"] = {
    "task": "apps.personnel.tasks.send_birthday_notifications",
    "schedule": crontab(minute=0, hour=9),
}
```

## 监控和维护

### 定期检查
- 每月检查 Celery Beat 执行日志
- 验证称号授予是否正确
- 确认队员生日信息完整性

### 性能优化
- 大量数据时使用bulk_create
- 定期清理无用的称号授予记录
- 监控数据库性能

### 安全考虑
- API接口仅限管理员访问
- 重要操作前备份数据
- 记录详细的操作日志

## 故障排查

### 开发环境常见问题

#### 数据库迁移失败
```bash
# 删除迁移文件和数据库重新开始
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

#### 依赖安装失败
```bash
# 更新pip并重新安装
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### 生产环境故障排查

生产环境的详细故障排查步骤，请参考 [SYSTEMD_DEPLOYMENT.md](../SYSTEMD_DEPLOYMENT.md#故障排查)，包括：

- **服务启动失败** - 检查日志、权限、配置
- **Unix Socket 问题** - Socket 文件、权限、连接
- **数据库连接问题** - PostgreSQL 配置、连接字符串
- **静态文件 404** - collectstatic、Nginx 配置
- **CORS/CSRF 错误** - 域名配置、Nginx headers
- **权限问题** - 文件权限、用户组设置

#### 快速诊断命令

```bash
# 检查服务状态
sudo systemctl status tacos

# 查看最近日志
sudo journalctl -u tacos -n 100 --no-pager

# 检查 Socket 文件
ls -l /run/gunicorn/tacos.sock

# 测试 API 连接
curl http://localhost/api/v1/common/health/

# 检查 Nginx 配置
sudo nginx -t
```

## 快速启动脚本

项目根目录提供了便捷的启动脚本：

### 后端快速启动（开发环境）
```bash
./scripts/start_backend.sh

```

### 前端快速启动（开发环境）
```bash
./scripts/start_frontend.sh

```

## 备份与恢复

项目提供了备份和恢复脚本（Linux/Mac）：

### 备份
```bash
# 备份数据库和媒体文件
./scripts/backup_tacos.sh

# 备份文件保存在项目根目录，格式：tacos_backup/YYYYMMDD_HHMMSS/
```

### 恢复
```bash
# 从备份文件恢复
./scripts/restore_tacos.sh tacos_backup/20250101_120000
```

## 相关文档

### 项目文档
- **[README.md](../README.md)** - 项目总览和快速开始
- **[DEVELOP_DOCUMENT.md](../DEVELOP_DOCUMENT.md)** - 详细开发文档和API设计

### 部署文档
- **[SYSTEMD_DEPLOYMENT.md](../SYSTEMD_DEPLOYMENT.md)** - 📚 **生产环境部署完整指南**
  - Systemd 服务配置详解
  - Unix Socket 配置和验证
  - Nginx 反向代理配置
  - PostgreSQL 数据库配置
  - SSL 证书配置
  - 详细故障排查步骤
- **[tacos.service.example](../tacos.service.example)** - Systemd 服务配置模板

### 运维文档
- **[BACKUP_README.md](../scripts/BACKUP_README.md)** - 备份恢复完整指南
- **[ASSET_CLEANUP_README.md](../scripts/ASSET_CLEANUP_README.md)** - 媒体文件清理工具
- **[FORMATTING_GUIDE.md](../scripts/FORMATTING_GUIDE.md)** - 代码格式化指南

## 技术支持

### 日志查看

**开发环境**:
```bash
# Django 开发服务器输出直接在终端显示
python manage.py runserver
```

**生产环境**:
```bash
# Systemd 服务日志
sudo journalctl -u tacos -f

# Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# Nginx 访问日志
sudo tail -f /var/log/nginx/access.log
```

### 获取帮助

1. **查看文档** - 先查阅相关文档（见上方"相关文档"）
2. **检查日志** - 使用上述命令查看详细错误信息
3. **故障排查** - 参考 [SYSTEMD_DEPLOYMENT.md](../SYSTEMD_DEPLOYMENT.md#故障排查)
4. **环境验证** - 确认环境变量配置正确（`printenv`）

## 贡献指南

1. 代码格式化：提交前运行 `./scripts/format_code.sh`
2. 运行测试：确保所有测试通过
3. 遵循项目代码规范
4. 提交前检查没有语法错误
