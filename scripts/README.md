# TaCOS 脚本工具集

本目录包含 TaCOS 项目的所有辅助脚本和相关文档。所有脚本都应该从项目根目录运行。

## 📁 目录结构

```
scripts/
├── README.md                       # 本文件：脚本使用总览
├── BACKUP_README.md                # 备份恢复详细指南
├── ASSET_CLEANUP_README.md         # 资源清理详细指南
├── FORMATTING_GUIDE.md             # 代码格式化详细指南
├── backup_tacos.sh                 # 备份脚本
├── restore_tacos.sh                # 恢复脚本
├── cleanup_unused_assets.sh        # 资源清理脚本
├── format_code.sh                  # 代码格式化脚本
├── start_backend.sh                # 后端启动脚本
└── start_frontend.sh               # 前端启动脚本
```

## 📖 文档指南

- **[BACKUP_README.md](BACKUP_README.md)** - 详细的备份与恢复操作指南
- **[ASSET_CLEANUP_README.md](ASSET_CLEANUP_README.md)** - 媒体资源清理完整说明
- **[FORMATTING_GUIDE.md](FORMATTING_GUIDE.md)** - 代码格式化工具配置和使用

## 📁 脚本列表

### 🚀 启动脚本

#### `start_backend.sh`
启动后端开发服务器（Django / Celery Worker / Celery Beat）

**功能：**
- 自动检测并安装 Python 环境
- 创建虚拟环境
- 安装依赖包
- 执行数据库迁移
- 启动对应的服务（Django / Celery Worker / Celery Beat）

**使用方法：**
```bash
# 启动 Django 开发服务器（完整启动，包括环境设置）
./scripts/start_backend.sh

# 启动 Celery Worker（异步任务处理）
./scripts/start_backend.sh --celery

# 启动 Celery Beat（定时任务调度）
./scripts/start_backend.sh --celery-beat

# 仅设置环境（不启动服务）
./scripts/start_backend.sh --setup-only

# 跳过设置直接启动
./scripts/start_backend.sh --skip-setup

# 显示帮助
./scripts/start_backend.sh --help
```

**开发环境完整启动流程：**

开发环境需要启动 **3 个服务**（分别在 3 个终端中）：

```bash
# Terminal 1: 启动 Django 服务器
./scripts/start_backend.sh

# Terminal 2: 启动 Celery Worker（处理异步任务）
./scripts/start_backend.sh --celery

# Terminal 3: 启动 Celery Beat（定时任务调度）
./scripts/start_backend.sh --celery-beat
```

**注意事项：**
- 首次运行会自动创建虚拟环境并安装依赖
- 默认使用 SQLite 数据库（开发环境）
- **启动 Celery 前需要先启动 Redis 服务**：
  - macOS: `brew services start redis`
  - Linux: `sudo systemctl start redis`
- Django 服务器默认运行在 `http://localhost:8000`

**为什么需要这些服务？**
- **Django**: Web API 服务器，处理 HTTP 请求
- **Celery Worker**: 异步处理耗时任务（PDF 水印生成、Excel 导出）
- **Celery Beat**: 定时执行任务（每小时清理过期文件、每天停用超过 6 个月未登录的在队成员、每月更新寿星称号）
- **Redis**: 消息队列，连接 Django 和 Celery

#### `start_frontend.sh`
启动前端开发服务器

**功能：**
- 检测 Node.js 和 npm 环境
- 安装前端依赖
- 配置环境变量
- 启动 Vite 开发服务器

**使用方法：**
```bash
# 默认启动
./scripts/start_frontend.sh

# 指定端口
./scripts/start_frontend.sh -p 3001

# 指定后端 API 地址
./scripts/start_frontend.sh -b http://api.example.com

# 强制重新安装依赖
./scripts/start_frontend.sh -i

# 清理并重新安装
./scripts/start_frontend.sh --clean

# 构建生产版本
./scripts/start_frontend.sh --build

# 显示帮助
./scripts/start_frontend.sh --help
```

**注意事项：**
- 需要 Node.js >= 20.0.0
- 默认运行在 `http://localhost:3000`
- 可以自定义后端 API 地址

### 💾 备份与恢复

#### `backup_tacos.sh`
备份系统数据（支持SQLite和PostgreSQL）

**功能：**
- **自动检测数据库类型**（SQLite/PostgreSQL）
- **SQLite备份**：数据库文件 + SQL导出
- **PostgreSQL备份**：pg_dump二进制格式 + 压缩SQL
- 导出Django JSON格式数据
- 备份媒体文件（支持多个位置）
- 备份配置文件（`.env`、`.env.production.local`、systemd 服务等）
- 生成备份信息文件
- 验证备份完整性

**使用方法：**
```bash
# 执行备份（自动检测数据库类型）
./scripts/backup_tacos.sh

# 备份并清理7天前的旧备份
./scripts/backup_tacos.sh --cleanup

# 显示帮助
./scripts/backup_tacos.sh --help
```

**备份内容：**

*SQLite环境（开发）：*
- 数据库文件：`db.sqlite3`
- SQL 导出：`db_dump.sql`
- JSON 数据：`data.json`

*PostgreSQL环境（生产）：*
- 二进制备份：`db_backup.dump` (pg_dump custom format)
- SQL 备份：`db_dump.sql.gz` (压缩SQL)
- JSON 数据：`data.json`

*通用：*
- 媒体文件：`tacos_media_files.tar.gz`, `media_files.tar.gz`
- 配置文件：`.env`, `.env.production.local`, `requirements.txt`, `tacos.service`
- 备份信息：`backup_info.txt`

**备份位置：**
```
./tacos_backup/YYYYMMDD_HHMMSS/
```

**PostgreSQL要求：**
- 需要安装 `pg_dump` 命令
- 在 `.env.production.local` 中配置 `DATABASE_URL=postgres://user:pass@host:port/dbname`

#### `restore_tacos.sh`
从备份恢复系统（支持SQLite和PostgreSQL）

**功能：**
- **自动检测数据库类型**
- **SQLite恢复**：文件复制 + 完整性检查
- **PostgreSQL恢复**：pg_restore或psql恢复
- 恢复数据库
- 恢复媒体文件
- 恢复配置文件
- 恢复 systemd 服务配置
- 验证恢复结果
- 自动备份当前数据

**使用方法：**
```bash
# 完整恢复
./scripts/restore_tacos.sh ./tacos_backup/20241024_120000

# 仅恢复数据库
./scripts/restore_tacos.sh ./tacos_backup/20241024_120000 --database-only

# 仅恢复媒体文件
./scripts/restore_tacos.sh ./tacos_backup/20241024_120000 --media-only

# 仅恢复配置
./scripts/restore_tacos.sh ./tacos_backup/20241024_120000 --config-only

# 预览模式（不执行实际恢复）
./scripts/restore_tacos.sh ./tacos_backup/20241024_120000 --dry-run

# 显示帮助
./scripts/restore_tacos.sh --help
```

**注意事项：**
- 恢复前会自动停止相关服务
- SQLite：自动备份当前数据库
- PostgreSQL：需要确认才会覆盖数据
- PostgreSQL需要 `pg_restore` 或 `psql` 命令
- 数据库必须已存在（PostgreSQL）
- 恢复后建议重启相关服务

**PostgreSQL恢复格式：**
- 优先使用 `db_backup.dump` (pg_restore)
- 备选使用 `db_dump.sql.gz` (psql)

### 🧹 资源清理

#### `cleanup_unused_assets.sh`
清理无用的媒体文件

**功能：**
- 扫描数据库中的文件引用
- 识别未被引用的媒体文件
- 支持多个媒体目录
- 计算可释放空间
- 可选备份无用文件
- 清理空目录和系统文件

**使用方法：**
```bash
# 预览模式（不执行删除）
./scripts/cleanup_unused_assets.sh --dry-run

# 备份后删除
./scripts/cleanup_unused_assets.sh --backup

# 强制删除（跳过确认）
./scripts/cleanup_unused_assets.sh --force

# 同时清理系统文件
./scripts/cleanup_unused_assets.sh --cleanup-ds

# 显示帮助
./scripts/cleanup_unused_assets.sh --help
```

**检查的数据库表：**
- `sheets` - 乐谱文件
- `assignment_attachments` - 作业附件
- `assignment_submission_attachments` - 作业提交附件
- `event_announcement_images` - 活动公告图片

**注意事项：**
- 建议先使用 `--dry-run` 预览
- 删除前会自动生成文件列表
- 使用 `--backup` 选项可以在删除前备份文件

### 🎨 代码格式化

#### `format_code.sh`
格式化项目代码

**功能：**
- 使用 `black` 格式化 Python 代码
- 使用 `isort` 排序 Python 导入
- 使用 `prettier` 格式化前端代码
- 自动安装缺失的工具

**使用方法：**
```bash
# 格式化所有代码
./scripts/format_code.sh
```

**格式化内容：**
- 后端：所有 `.py` 文件
- 前端：`.js`, `.vue`, `.css`, `.html`, `.json`, `.md` 文件

**注意事项：**
- 提交代码前建议运行此脚本
- 会自动跳过虚拟环境和 node_modules

## 🔧 常见问题

### Q: 脚本提示"请在项目根目录运行"？
**A:** 确保你在 TaCOS 项目根目录（包含 `tacos_backend` 和 `tacos_frontend` 的目录）运行脚本：
```bash
cd /path/to/tacos
./scripts/script_name.sh
```

### Q: 权限不足无法执行脚本？
**A:** 给脚本添加执行权限：
```bash
chmod +x scripts/*.sh
```

### Q: Windows 下如何运行这些脚本？
**A:**
1. 使用 Git Bash 或 WSL
2. 或者参考脚本内容手动执行相应命令

### Q: 备份文件保存在哪里？
**A:** 备份文件保存在项目根目录的 `tacos_backup` 目录下，按时间戳组织。

### Q: 如何定期自动备份？
**A:** 可以使用 crontab 设置定时任务：
```bash
# 每天凌晨2点自动备份
0 2 * * * cd /path/to/tacos && ./scripts/backup_tacos.sh --cleanup
```

## 📚 相关文档

- [项目主 README](../README.md)
- [后端 README](../tacos_backend/README.md)
- [备份说明文档](BACKUP_README.md)
- [资源清理说明](ASSET_CLEANUP_README.md)
- [代码格式化指南](FORMATTING_GUIDE.md)
- [系统部署文档](../SYSTEMD_DEPLOYMENT.md)

## 💡 最佳实践

1. **开发环境启动：**
   ```bash
   # 首次启动
   ./scripts/start_backend.sh
   ./scripts/start_frontend.sh

   # 后续启动（跳过环境设置）
   ./scripts/start_backend.sh --skip-setup
   ./scripts/start_frontend.sh -s
   ```

2. **定期维护：**
   ```bash
   # 每周备份一次
   ./scripts/backup_tacos.sh --cleanup

   # 每月清理一次无用文件
   ./scripts/cleanup_unused_assets.sh --dry-run  # 先预览
   ./scripts/cleanup_unused_assets.sh --backup   # 确认后执行
   ```

3. **代码提交前：**
   ```bash
   # 格式化代码
   ./scripts/format_code.sh

   # 运行测试
   cd tacos_backend
   python manage.py test
   ```

4. **部署到生产：**
   ```bash
   # 备份现有数据
   ./scripts/backup_tacos.sh

   # 更新代码后恢复数据（如需要）
   ./scripts/restore_tacos.sh ./tacos_backup/YYYYMMDD_HHMMSS
   ```
