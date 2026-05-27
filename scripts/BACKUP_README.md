# TaCOS 数据备份与恢复指南

## 📋 概述

本文档介绍如何使用TaCOS系统的备份和恢复脚本，确保数据安全和系统可恢复性。

## 🗂️ 备份内容

### 数据库文件

#### SQLite数据库（开发环境）
- **数据库文件**: `tacos_backend/db.sqlite3`
- **SQL导出**: `db_dump.sql`
- **JSON导出**: `data.json` (Django格式)

#### PostgreSQL数据库（生产环境）
- **二进制备份**: `db_backup.dump` (pg_dump custom format)
- **SQL备份**: `db_dump.sql.gz` (压缩SQL格式)
- **JSON导出**: `data.json` (Django格式)

备份脚本会自动检测当前环境的数据库类型：
- 读取 `.env.production.local` (生产环境) 或 `.env` (开发环境)
- 解析 `DATABASE_URL`：如果是 `postgres://` 开头，使用 `pg_dump` 备份
- 否则备份 SQLite 数据库文件

### 媒体文件
- **项目媒体目录**: `tacos_media/`
  - 乐谱文件
  - 作业附件
  - 活动文件
  - 提交文件
- **静态媒体目录**: `tacos_backend/static/media/`

### 配置文件
- **环境配置**: `.env`, `.env.production.local`
- **依赖配置**: `requirements.txt`
- **服务配置**: `tacos.service` (systemd, 如果存在)

## 🚀 使用方法

### 备份操作

#### 基本备份
```bash
# 执行完整备份
./scripts/backup_tacos.sh

# 备份并清理7天前的旧备份（建议手动删除备份，以保留更长时间的备份数据）
./scripts/backup_tacos.sh --cleanup

# 查看帮助信息
./scripts/backup_tacos.sh --help
```

#### 备份输出

**SQLite环境备份** (开发环境):
```
20241201_143022/
├── backup_info.txt          # 备份信息文件
├── db.sqlite3              # SQLite数据库文件
├── db_dump.sql             # SQL导出文件
├── data.json               # Django数据导出
├── media_files.tar.gz      # 媒体文件压缩包
├── .env                    # 开发环境配置
├── tacos.service           # Systemd服务配置
└── requirements.txt        # Python依赖
```

**PostgreSQL环境备份** (生产环境):
```
20241201_143022/
├── backup_info.txt          # 备份信息文件
├── db_backup.dump          # PostgreSQL二进制备份 (推荐恢复用)
├── db_dump.sql.gz          # PostgreSQL SQL备份 (可读格式)
├── data.json               # Django数据导出
├── media_files.tar.gz      # 媒体文件压缩包
├── .env.production.local   # 生产环境实际配置（包含敏感信息）
├── tacos.service           # Systemd服务配置
└── requirements.txt        # Python依赖
```

> **注意**：`.env.production.example` 是模板文件，在版本控制中，不会被备份。
> 备份脚本只备份 `.env.production.local`（实际配置）。

### PostgreSQL备份要求

#### 安装PostgreSQL客户端工具
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-client

# CentOS/RHEL
sudo yum install postgresql

# macOS
brew install postgresql
```

#### 环境配置
在 `.env.production.local` 文件中配置PostgreSQL连接：
```bash
DATABASE_URL=postgres://username:password@localhost:5432/tacos_db
```

> **文件说明**：
> - `.env.production.example` - 配置模板（提交到git）
> - `.env.production.local` - 实际配置（包含敏感信息，不提交）

格式说明：
- `username`: PostgreSQL用户名
- `password`: 数据库密码
- `localhost`: 数据库主机地址
- `5432`: PostgreSQL端口（默认5432）
- `tacos_db`: 数据库名称

**安全建议：**
```bash
chmod 600 tacos_backend/.env.production.local
```

### 恢复操作

#### 完整恢复
```bash
# 恢复所有数据
./scripts/restore_tacos.sh ./tacos_backup/20241201_143022

# 预览恢复操作（不执行实际恢复）
./scripts/restore_tacos.sh ./tacos_backup/20241201_143022 --dry-run
```

#### 选择性恢复
```bash
# 仅恢复数据库
./scripts/restore_tacos.sh ./tacos_backup/20241201_143022 --database-only

# 仅恢复媒体文件
./scripts/restore_tacos.sh ./tacos_backup/20241201_143022 --media-only

# 仅恢复配置文件
./scripts/restore_tacos.sh ./tacos_backup/20241201_143022 --config-only
```

## ⚠️ 重要注意事项

### 备份前检查
1. 确保在TaCOS项目根目录下运行脚本
2. 检查数据库连接配置（SQLite文件或PostgreSQL连接）
3. 确认有足够的磁盘空间
4. 对于PostgreSQL，确保安装了 `pg_dump` 命令

### 恢复前准备
1. **停止所有相关服务**
   - SQLite: 停止Django开发服务器
   - PostgreSQL: 停止systemd服务 `sudo systemctl stop tacos`
2. **备份当前数据**（脚本会自动备份SQLite）
3. **确认恢复模式**（完整恢复/选择性恢复）
4. **验证备份文件完整性**
5. **确认数据库类型匹配**
   - PostgreSQL恢复需要 `pg_restore` 或 `psql` 命令
   - 恢复会覆盖现有数据库内容（会有确认提示）

### PostgreSQL恢复注意事项
1. **数据库必须已存在**
   - 恢复脚本不会创建数据库
   - 需要提前创建目标数据库：`CREATE DATABASE tacos_db;`
2. **用户权限**
   - 确保PostgreSQL用户有足够权限
   - 建议使用数据库所有者账户恢复
3. **备份格式**
   - `.dump` 文件：使用 `pg_restore` 恢复（推荐）
   - `.sql.gz` 文件：使用 `psql` 恢复
4. **恢复选项**
   - `--clean`: 恢复前删除现有对象
   - `--if-exists`: 安全删除（对象不存在时不报错）
   - `--no-owner`: 不恢复对象所有权
   - `--no-privileges`: 不恢复访问权限

### 安全建议
1. 定期执行备份（建议每日）
2. 测试恢复流程
3. 异地存储备份文件
4. 加密敏感备份文件
5. 妥善保管 `.env` 文件中的数据库密码
6. PostgreSQL生产环境使用强密码

## 🔧 高级用法

### 自动化备份
创建定时任务（crontab）：
```bash
# 每日凌晨2点执行备份
0 2 * * * /path/to/tacos/scripts/backup_tacos.sh --cleanup

# 每周日凌晨3点执行完整备份
0 3 * * 0 /path/to/tacos/scripts/backup_tacos.sh
```

### 远程备份
```bash
# 备份到远程服务器
./scripts/backup_tacos.sh
rsync -av ./tacos_backup/ user@remote-server:/backup/tacos/

# 从远程恢复
rsync -av user@remote-server:/backup/tacos/20241201_143022/ ./temp_restore/
./scripts/restore_tacos.sh ./temp_restore/20241201_143022
```

### 数据库迁移
```bash
# 从SQLite迁移到PostgreSQL
# 1. 备份SQLite数据库
./scripts/backup_tacos.sh

# 2. 创建PostgreSQL数据库
psql -U postgres
CREATE DATABASE tacos_db OWNER your_user;
\q

# 3. 修改 .env.production.local 配置使用 PostgreSQL
# DATABASE_URL=postgres://your_user:password@localhost:5432/tacos_db

# 4. 运行Django迁移
cd tacos_backend
source .venv/bin/activate
python manage.py migrate
python manage.py loaddata backup_dir/data.json
```

## 🐛 故障排除

### 常见问题

#### 1. 权限错误
```bash
# 设置脚本执行权限
chmod +x scripts/backup_tacos.sh scripts/restore_tacos.sh
```

#### 2. PostgreSQL连接失败
```bash
# 检查PostgreSQL服务状态
sudo systemctl status postgresql

# 检查连接参数
psql -h localhost -p 5432 -U username -d tacos_db

# 常见原因：
# - 密码错误：检查 .env.production.local 中的 DATABASE_URL
# - 主机无法访问：检查pg_hba.conf配置
# - 数据库不存在：需要先创建数据库
```

#### 3. pg_dump/pg_restore未找到
```bash
# Ubuntu/Debian安装
sudo apt-get install postgresql-client

# 验证安装
pg_dump --version
pg_restore --version
```

#### 4. 数据库锁定（SQLite）
```bash
# 停止Django服务
# 或使用SQLite的WAL模式
```

#### 5. 磁盘空间不足
```bash
# 检查可用空间
df -h
# 清理旧备份
./scripts/backup_tacos.sh --cleanup
```

#### 6. PostgreSQL恢复失败
```bash
# 检查备份文件完整性
pg_restore --list db_backup.dump

# 使用预览模式检查
./scripts/restore_tacos.sh backup_dir --dry-run

# 手动恢复测试
export PGPASSWORD='your_password'
pg_restore -h localhost -U username -d tacos_db --clean --if-exists db_backup.dump
```

#### 7. 权限不足错误
```bash
# PostgreSQL恢复时如果遇到权限错误
# 使用--no-owner和--no-privileges选项（脚本已自动使用）
pg_restore -h localhost -U username -d tacos_db --no-owner --no-privileges db_backup.dump
```

### 日志分析
脚本会输出详细的日志信息：
- `[INFO]` - 一般信息
- `[SUCCESS]` - 成功操作
- `[WARNING]` - 警告信息
- `[ERROR]` - 错误信息

## 📊 备份策略建议

### 开发环境
- **频率**: 每日备份
- **保留**: 7天
- **存储**: 本地磁盘

### 生产环境
- **频率**: 每日备份 + 实时复制
- **保留**: 30天
- **存储**: 本地 + 云存储
- **验证**: 每周测试恢复

### 紧急恢复
- **RTO**: 恢复时间目标 < 1小时
- **RPO**: 恢复点目标 < 24小时
- **测试**: 每月演练
