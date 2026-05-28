# TaCOS 资产清理工具使用指南

## 📋 概述

TaCOS 资产清理工具是一个智能的媒体文件清理脚本，能够自动识别和清理未被数据库引用的无用文件，帮助释放存储空间并保持系统整洁。

**支持的数据库**:
- **SQLite** - 开发环境（默认）
- **PostgreSQL** - 生产环境

脚本会自动检测数据库类型并使用相应的查询方式。

## 🎯 功能特性

### 数据库支持
- **自动检测**: 自动读取 `.env.production.local` 或 `.env` 配置文件
- **双数据库**: 支持 SQLite（开发）和 PostgreSQL（生产）
- **智能切换**: 根据 `DATABASE_URL` 自动选择查询方式
- **连接验证**: 检查数据库连接和必要的客户端工具

### 智能识别
- **数据库分析**: 自动分析数据库中的文件引用关系
- **结构检查**: 自动检查数据库表结构变化
- **文件扫描**: 扫描所有媒体文件
- **差异对比**: 识别未被引用的无用文件
- **安全保护**: 只删除确认无用的文件

### 多种模式
- **预览模式**: 仅显示要删除的文件，不执行删除
- **备份模式**: 删除前自动备份文件
- **强制模式**: 跳过二次确认直接删除
- **系统清理**: 同时清理.DS_Store等系统文件

### 详细统计
- **文件统计**: 显示总文件数、被引用文件数、无用文件数
- **空间统计**: 显示文件大小和可释放空间
- **进度显示**: 实时显示清理进度

## 🗂️ 支持的文件类型

### 数据库引用的文件类型
- **乐谱文件**: `sheets/` 目录下的PDF文件
- **作业附件**: `assignments/` 目录下的各种文件
- **提交文件**: `submissions/` 目录下的提交附件
- **活动图片**: `events/announcements/` 目录下的图片文件

### 可清理的文件类型
- 未被数据库引用的媒体文件
- 系统临时文件 (.DS_Store, Thumbs.db等)
- 空目录

## 🔌 数据库支持详解

### 自动检测机制

脚本会按以下顺序检测数据库配置：

1. **优先**: `.env.production.local`（生产环境，不提交到 Git）
2. **备用**: `.env`（开发环境）
3. **默认**: 如果都不存在，默认使用 SQLite

### 配置文件格式

**SQLite 配置**:
```bash
# .env
DATABASE_URL=sqlite:///db.sqlite3
```

**PostgreSQL 配置**:
```bash
# .env.production.local
DATABASE_URL=postgresql://username:password@host:port/database
# 或
DATABASE_URL=postgres://username:password@host:port/database
```

### 数据库工具要求

**SQLite**:
- 需要 `sqlite3` 命令行工具
- 数据库文件必须存在且可访问

**PostgreSQL**:
- 需要 `psql` 命令行工具
- 数据库服务器必须可连接
- 用户必须有读取权限

### 安装数据库客户端

**Ubuntu/Debian**:
```bash
# SQLite
sudo apt-get install sqlite3

# PostgreSQL
sudo apt-get install postgresql-client
```

**CentOS/RHEL**:
```bash
# SQLite
sudo yum install sqlite

# PostgreSQL
sudo yum install postgresql
```

**macOS**:
```bash
# SQLite (通常已预装)
brew install sqlite

# PostgreSQL
brew install postgresql
```

### 查询方式对比

| 特性 | SQLite | PostgreSQL |
|------|--------|------------|
| 查询工具 | `sqlite3` | `psql` |
| 表信息查询 | `sqlite_master` | `information_schema` |
| 连接方式 | 本地文件 | 网络连接 |
| 密码认证 | 不需要 | `PGPASSWORD` 环境变量 |
| 适用环境 | 开发环境 | 生产环境 |

## 🚀 使用方法

### 基本命令

```bash
# 预览要删除的文件（推荐首次使用）
./scripts/cleanup_unused_assets.sh --dry-run

# 备份后删除无用文件
./scripts/cleanup_unused_assets.sh --backup

# 强制删除（跳过确认）
./scripts/cleanup_unused_assets.sh --force

# 同时清理系统文件
./scripts/cleanup_unused_assets.sh --cleanup-ds

# 查看帮助信息
./scripts/cleanup_unused_assets.sh --help
```

### 组合使用

```bash
# 预览 + 系统文件清理
./scripts/cleanup_unused_assets.sh --dry-run --cleanup-ds

# 备份 + 系统文件清理
./scripts/cleanup_unused_assets.sh --backup --cleanup-ds

# 强制 + 系统文件清理
./scripts/cleanup_unused_assets.sh --force --cleanup-ds
```

## 📊 输出示例

### 预览模式输出
```
[HIGHLIGHT] === TaCOS 资产清理工具 ===
[INFO] 开始时间: 2024-12-01 14:30:06
[INFO] 检查环境...
[INFO] 检测数据库类型...
[INFO] 使用配置文件: .env.production.local
[INFO] 检测到 PostgreSQL 数据库
[INFO] 数据库: tacos_db @ localhost:5432
[SUCCESS] PostgreSQL 客户端检查通过
[INFO] 找到媒体目录: /path/to/tacos_media
[SUCCESS] 环境检查完成
[INFO] 检查数据库表结构...
[INFO] 数据库中发现的文件相关表:
  - assignment_attachments
  - assignment_submission_attachments
  - event_announcement_images
  - sheets
[SUCCESS] 数据库表结构检查通过，所有预期的文件相关表都存在

[INFO] 分析数据库中的文件引用...
[INFO] 提取乐谱文件引用...
[INFO] 提取作业附件引用...
[INFO] 提取作业提交附件引用...
[INFO] 提取活动公告图片引用...
[SUCCESS] 找到 4 个被引用的文件
[INFO] 扫描媒体目录中的所有文件...
[SUCCESS] 找到 16 个媒体文件
[INFO] 识别无用文件...
[SUCCESS] 识别出 12 个无用文件

[HIGHLIGHT] === 文件统计信息 ===
总文件数: 16
被引用文件: 4
无用文件: 12

总大小: 23 MB
被引用文件大小: 6 MB
无用文件大小: 17 MB

可释放空间: 17 MB (72%)

[HIGHLIGHT] === 预览模式 - 以下文件将被删除 ===
.DS_Store
assignments/1/old_file.pdf
sheets/unused_sheet.pdf
...
```

### 实际删除输出
```
[INFO] 开始删除无用文件...
[INFO] 已删除 10 个文件...
[SUCCESS] 成功删除 12 个无用文件
[SUCCESS] 清理了 3 个空目录
[SUCCESS] 🎉 资产清理完成！
```

## 🔍 数据库结构检查

### 自动检查功能
脚本会自动检查数据库中的文件相关表结构，确保与预期一致：

**预期的文件相关表**:
- `sheets` - 乐谱文件表
- `assignment_attachments` - 作业附件表
- `assignment_submission_attachments` - 作业提交附件表
- `event_announcement_images` - 活动公告图片表

### 结构变化警告
如果发现未预期的文件相关表，脚本会：
1. 显示警告信息
2. 列出新发现的表
3. 提供更新建议
4. 询问是否继续执行

### 警告示例
```
[WARNING] ⚠️  发现未预期的文件相关表:
  - new_file_table

[ERROR] 数据库结构已发生变化！
[ERROR] 请更新 cleanup_assets.sh 脚本以包含这些新表:
  - 需要在 get_referenced_files() 函数中添加对 new_file_table 表的处理

[WARNING] 建议:
  1. 检查这些表的字段结构
  2. 确定哪些字段存储文件路径
  3. 在脚本中添加相应的SQL查询
  4. 更新 expected_tables 数组
```

## ⚠️ 重要注意事项

### 使用前准备
1. **备份数据**: 建议先执行完整备份（可使用 `backup_tacos.sh`）
2. **停止服务**: 清理前停止相关服务
3. **预览模式**: 首次使用务必使用 `--dry-run` 预览
4. **结构检查**: 注意数据库结构变化警告
5. **环境配置**: 确保数据库配置文件存在（`.env.production.local` 或 `.env`）

### 安全建议
1. **预览确认**: 删除前仔细检查预览列表
2. **备份重要文件**: 使用`--backup`选项备份
3. **分批清理**: 大量文件建议分批处理
4. **定期清理**: 建议定期执行清理

### 注意事项
1. 脚本只清理媒体目录中的文件
2. 不会删除数据库记录
3. 被数据库引用的文件不会被删除
4. 系统文件(.DS_Store等)需要`--cleanup-ds`选项

## 🔧 高级用法

### 自动化清理
创建定时任务（crontab）：
```bash
# 每周日凌晨2点执行清理
0 2 * * 0 /path/to/tacos/scripts/cleanup_unused_assets.sh --backup --cleanup-ds

# 每月1号执行深度清理
0 3 1 * * /path/to/tacos/scripts/cleanup_unused_assets.sh --force --cleanup-ds
```

### 自定义清理
```bash
# 仅清理系统文件
./scripts/cleanup_unused_assets.sh --dry-run --cleanup-ds

# 备份后清理（推荐生产环境）
./scripts/cleanup_unused_assets.sh --backup --cleanup-ds
```

## 🐛 故障排除

### 常见问题

#### 1. 权限错误
```bash
# 设置执行权限
chmod +x cleanup_assets.sh
```

#### 2. 数据库连接失败

**SQLite 环境**:
```bash
# 检查数据库文件是否存在
ls -la tacos_backend/db.sqlite3

# 检查数据库权限
sqlite3 tacos_backend/db.sqlite3 "SELECT 1;"
```

**PostgreSQL 环境**:
```bash
# 检查 psql 是否安装
which psql

# 测试数据库连接
psql -h localhost -p 5432 -U tacos_user -d tacos_db -c "SELECT 1;"

# 检查配置文件
cat tacos_backend/.env.production.local | grep DATABASE_URL
```

#### 3. 媒体目录不存在
```bash
# 检查媒体目录
ls -la tacos_backend/tacos_backend/static/media/
```

#### 4. 文件删除失败
- 检查文件权限
- 确认文件未被其他程序占用
- 检查磁盘空间

#### 5. 数据库结构变化警告
```
[ERROR] 数据库结构已发生变化！
```
**解决方案**:
1. 检查新发现的表结构
2. 确定文件字段名称
3. 更新脚本中的SQL查询
4. 更新expected_tables数组

**示例更新**:
```bash
# 在get_referenced_files()函数中添加
sqlite3 "$DB_FILE" "SELECT new_file_field FROM new_file_table WHERE new_file_field IS NOT NULL AND new_file_field != '';" >> "$REFERENCED_FILES" 2>/dev/null || true

# 在expected_tables数组中添加
local expected_tables=("assignment_attachments" "assignment_submission_attachments" "event_announcement_images" "sheets" "new_file_table")
```

### 日志分析
脚本会输出详细的日志信息：
- `[INFO]` - 一般信息
- `[SUCCESS]` - 成功操作
- `[WARNING]` - 警告信息
- `[ERROR]` - 错误信息
- `[HIGHLIGHT]` - 重要信息

## 📈 性能优化

### 大文件处理
- 脚本会自动分批处理大量文件
- 每10个文件显示一次进度
- 支持中断和恢复

### 内存使用
- 使用临时文件处理，内存占用低
- 自动清理临时文件
- 支持处理数万个文件

## 🔒 安全特性

### 数据保护
- 只删除确认无用的文件
- 支持备份模式
- 二次确认机制

### 权限控制
- 检查文件权限
- 验证数据库完整性
- 错误处理和回滚

## 📚 相关文档

- [备份恢复指南](BACKUP_README.md) - 包含 SQLite 和 PostgreSQL 备份说明
- [代码格式化指南](FORMATTING_GUIDE.md) - 代码格式化工具使用
- [脚本总览](README.md) - 所有脚本的使用说明
