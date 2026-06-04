# TaCOS (Tsinghua Chorus Online System)

清华合唱队在线系统 - 一套旨在提升清华大学学生艺术团合唱队内部管理效率的在线信息系统。

## 项目概述

TaCOS 是一个基于 Django + Vue.js 的现代化 Web 应用，提供人事管理、谱务管理、活动管理、签到系统和作业管理等功能。

### 核心功能

- 🔐 **用户认证系统** - 基于 JWT 的安全认证
- 👥 **人事管理** - 队员档案管理、成员头像、外请教师管理、校友状态管理
- 🤝 **校友联系窗口** - 校友维护公开联系方式，管理员控制成员状态
- 📄 **谱务管理** - 乐谱上传、下载、水印处理、校友可见范围控制
- 🗓 **活动管理** - 活动创建、报名、公告管理、校友可见活动
- ✅ **签到系统** - 密码签到、定位签到、统计记录
- 📝 **作业管理** - 作业发布、提交、批改评分
- 📱 **响应式设计** - 支持 PC 端和移动端

## 技术栈

### 后端
- **框架**: Django 4.x + Django REST Framework
- **数据库**: PostgreSQL (生产) / SQLite (开发)
- **认证**: JWT (JSON Web Token)
- **异步任务**: Celery + Redis (PDF 水印、Excel 导出)
- **定时任务**: Celery Beat (定期清理、长期未登录停用、自动更新寿星称号)
- **文件处理**: Pillow (图片验证、头像处理)
- **部署**: Systemd + Nginx + Gunicorn

### 前端
- **框架**: Vue.js 3.x
- **状态管理**: Vuex 4.x
- **路由**: Vue Router 4.x
- **UI框架**: Element Plus + shadcn-vue + Tailwind CSS
- **构建工具**: Vite
- **HTTP客户端**: Axios

## 快速开始

### 环境要求

- **后端**: Python 3.9+, Redis (消息队列), PostgreSQL 13+ (生产环境) / SQLite (开发环境)
- **前端**: Node.js 20+, npm 9+
- **系统**: Linux, macOS, Windows (WSL)

### 启动脚本

项目提供了便捷的启动脚本来快速启动开发环境：

**启动后端：**

开发环境需要启动 **3 个服务**（分别在 3 个终端中）：

```bash
# Terminal 1: Django 服务器
./scripts/start_backend.sh

# Terminal 2: Celery Worker (异步任务处理)
./scripts/start_backend.sh --celery

# Terminal 3: Celery Beat (定时任务调度)
./scripts/start_backend.sh --celery-beat
```

**注意**：启动前请确保 **Redis** 服务已运行：
- **macOS**: `brew services start redis`
- **Linux**: `sudo systemctl start redis`
- **Windows**: 使用 WSL 或 Docker 运行 Redis

脚本会自动完成：
- Python 环境检测和虚拟环境创建
- 依赖包安装
- 数据库迁移
- 启动对应的服务（Django / Celery Worker / Celery Beat）

**为什么需要这些服务？**
- **Django**: Web API 服务器，处理 HTTP 请求
- **Celery Worker**: 异步处理耗时任务（PDF 水印生成、Excel 导出）
- **Celery Beat**: 定时执行任务（每小时清理过期文件、每天停用超过 6 个月未登录的在队成员、每月更新寿星称号）
- **Redis**: 消息队列，连接 Django 和 Celery

**启动前端：**
```bash
./scripts/start_frontend.sh
```

脚本会自动完成：
- Node.js 环境检测
- 依赖包安装
- 环境变量配置
- 启动 Vite 开发服务器

**首次启动后端后，需要创建超级用户：**
```bash
cd tacos_backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python manage.py createsuperuser
```

然后访问 Django Admin 后台进行用户管理。管理员账号仍然需要成员档案；若只在
Django Admin 创建了用户，首次登录后会进入个人信息完善流程。

详细的脚本使用说明请参考 [scripts/README.md](scripts/README.md)。

## 成员与校友管理

TaCOS 的成员档案统一承载在队成员、校友和停用成员的生命周期信息：

- 成员状态支持 `ACTIVE`、`ALUMNI`、`INACTIVE`，管理员可手动维护。
- `Member.status` 是成员在队、校友、停用状态的来源，`User.is_active` 仅作为平台级账号开关。
- 队员列表会明确显示状态，并按在队、校友、停用优先排序。
- 成员切换为 `ALUMNI` 后自动创建校友信息档案。
- 管理员创建成员时预计毕业时间可暂空，用户首次登录完善信息时必须填写。
- 任意账号若还没有成员档案，登录后会进入首次信息完善流程；管理员权限由 `User.role` 控制。
- 校友可在个人主页维护当前城市、行业、单位、职位、毕业时间、简介、备注和是否开放联系，其中毕业时间必填；微信、电话、邮箱沿用成员档案字段。
- 活动和乐谱均支持 `visible_to_alumni`，校友只看到显式面向校友开放的内容，并可报名校友可见活动。
- 校友只能担任校友可见活动的活动管理员。
- 与活动关联且活动已开放给校友的乐谱，也会对校友可见。
- Celery Beat 每天将超过 6 个月未登录的 `ACTIVE` 成员设为 `INACTIVE`，不会修改 `ALUMNI`。
- `INACTIVE` 成员登录时会被拒绝，并提示“账号已停用，请联系管理员协助处理”。
- 成员可上传本人头像，管理员可维护任意成员头像；前端保存方形裁剪图，小头像按圆形展示，点击头像时预览方图。

当前系统不包含导师制、校友活动组织或自动毕业状态转换。

## 日常维护

项目提供了完善的维护脚本和文档，主要包括定期备份和资源清理：

### 备份与恢复
- **备份脚本**: `./scripts/backup_tacos.sh` - 支持 SQLite（开发）和 PostgreSQL（生产）自动检测
- **恢复脚本**: `./scripts/restore_tacos.sh` - 自动选择对应的恢复方式
- **详细文档**: [scripts/BACKUP_README.md](scripts/BACKUP_README.md)

### 资源清理
- **清理脚本**: `./scripts/cleanup_unused_assets.sh` - 清理无用的媒体文件
- **详细文档**: [scripts/ASSET_CLEANUP_README.md](scripts/ASSET_CLEANUP_README.md)

### 代码格式化
- **格式化脚本**: `./scripts/format_code.sh` - 统一 Python 和 JavaScript/Vue 代码风格
- **详细文档**: [scripts/FORMATTING_GUIDE.md](scripts/FORMATTING_GUIDE.md)

更多信息请参考 [scripts/README.md](scripts/README.md)。

## 访问地址

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000/api/v1
- **Django Admin**: http://localhost:8000/admin

## 项目结构

```
TaCOS/
├── tacos_backend/              # Django 后端应用
│   ├── apps/                   # 应用模块
│   │   ├── authentication/     # 认证模块
│   │   ├── personnel/          # 人事管理
│   │   ├── sheet_music/        # 谱务管理
│   │   ├── events/             # 活动管理
│   │   └── common/             # 公共模块
│   ├── config/                 # 项目配置
│   │   ├── settings/           # 环境配置
│   │   │   ├── base.py         # 基础配置
│   │   │   ├── development.py  # 开发环境配置
│   │   │   ├── production.py   # 生产环境配置
│   │   │   └── testing.py      # 测试环境配置
│   │   ├── urls.py             # URL 路由
│   │   └── wsgi.py             # WSGI 配置
│   ├── static/                 # 静态文件目录
│   ├── .env.example            # 开发环境配置模板
│   ├── .env.production.example # 生产环境配置模板
│   ├── manage.py               # Django 管理脚本
│   ├── requirements.txt        # Python 依赖
│   └── pyproject.toml          # Python 项目配置
├── tacos_frontend/             # Vue.js 前端应用
│   ├── src/                    # 源代码
│   │   ├── views/              # 页面组件
│   │   ├── components/         # 公共组件
│   │   ├── api/                # API 接口
│   │   ├── store/              # 状态管理
│   │   ├── router/             # 路由配置
│   │   ├── utils/              # 工具函数
│   │   └── assets/             # 静态资源
│   ├── public/                 # 公共资源
│   ├── .env.example            # 前端环境配置模板
│   ├── package.json            # 项目依赖
│   ├── vite.config.js          # Vite 配置
│   └── tailwind.config.js      # Tailwind 配置
├── tacos_media/                # 媒体文件目录（不提交）
│   ├── events/                 # 活动相关媒体
│   ├── members/                # 成员头像
│   ├── sheets/                 # 乐谱文件
│   └── assignments/            # 作业附件
├── scripts/                    # 辅助脚本和文档
│   ├── README.md               # 脚本使用总览
│   ├── start_backend.sh        # 后端启动脚本
│   ├── start_frontend.sh       # 前端启动脚本
│   ├── backup_tacos.sh         # 系统备份脚本
│   ├── restore_tacos.sh        # 系统恢复脚本
│   ├── cleanup_unused_assets.sh # 媒体资源清理脚本
│   ├── format_code.sh          # 代码格式化脚本
│   ├── BACKUP_README.md        # 备份恢复详细指南
│   ├── ASSET_CLEANUP_README.md # 资源清理详细指南
│   └── FORMATTING_GUIDE.md     # 代码格式化详细指南
├── .gitignore                  # Git 忽略配置
├── AGENTS.md                   # Agent 工作流说明
├── LICENSE                     # Apache 2.0 许可证
├── README.md                   # 项目说明（本文件）
├── SECURITY.md                 # 安全漏洞报告政策
├── SYSTEMD_DEPLOYMENT.md       # 生产环境部署指南
└── tacos.service.example       # Systemd 服务配置模板
```

## 文档索引

### 核心文档
- **[项目主文档](README.md)** - 本文件：项目概览和快速开始
- **[后端文档](tacos_backend/README.md)** - 后端 API 详细文档和开发指南
- **[开发文档](DEVELOP_DOCUMENT.md)** - 详细的开发规范和贡献指南

### 部署文档
- **[部署文档](SYSTEMD_DEPLOYMENT.md)** - 生产环境 Systemd 部署完整指南

### 脚本文档
- **[脚本总览](scripts/README.md)** - 所有脚本的使用说明和快速参考
- **[备份恢复指南](scripts/BACKUP_README.md)** - 备份恢复脚本详细使用指南
- **[资源清理指南](scripts/ASSET_CLEANUP_README.md)** - 媒体资源清理详细说明
- **[代码格式化指南](scripts/FORMATTING_GUIDE.md)** - 代码格式化工具配置和使用

## 测试

### 后端测试

```bash
cd tacos_backend
python manage.py test --settings=config.settings.testing
```

### 前端测试

```bash
cd tacos_frontend
npm run test:unit
npm run test:e2e
```

## 许可证

Copyright © 2026 Tsinghua Chorus.

本项目采用 Apache 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 更新日志

### v2.3.1 (2026-06-04)

修复列表分页状态被筛选监听误重置的问题，避免队员、乐谱和活动列表翻页卡在第一页。

### v2.3.0 (2026-06-04)

优化页面加载、缓存复用和列表交互体验，增加活动队员导出与成员头像轻量预览，并修复活动管理员管理、活动乐谱排序和乐谱上传取消操作等问题。

### v2.2.0 (2026-05-28)

增加长期未登录成员自动停用、停用成员登录拦截、成员头像上传裁剪与预览，并补齐管理员账号也需要成员档案的首次信息完善流程。

### v2.1.0 (2026-05-27)

增加校友联系窗口、校友可见活动和乐谱范围控制，并优化完整乐谱预览、水印处理和相关权限规则。

### v2.0.0 (2026-01-04)

重构前端交互与移动端体验，增加链接分享和快速签到等功能。

### v1.0.0 (2025-10-26)

发布基础的人事管理、谱务管理、活动管理、签到系统和作业管理能力。
