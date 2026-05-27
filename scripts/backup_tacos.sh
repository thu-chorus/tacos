#!/bin/bash

# TaCOS 系统备份脚本
# 用途: 备份数据库、媒体文件和配置文件

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/tacos_backend"

# 获取当前时间戳
DATETIME=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$PROJECT_ROOT/tacos_backup/$DATETIME"

# 检测数据库类型
detect_database_type() {
    log_info "检测数据库类型..."

    # 读取环境变量
    # 生产环境: .env.production.local (包含敏感信息)
    # 开发环境: .env
    if [ -f "$BACKEND_DIR/.env.production.local" ]; then
        source "$BACKEND_DIR/.env.production.local"
        log_info "读取配置: .env.production.local"
    elif [ -f "$BACKEND_DIR/.env" ]; then
        source "$BACKEND_DIR/.env"
        log_info "读取配置: .env"
    fi

    # 检查是否配置了 PostgreSQL
    if [ ! -z "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgres* ]]; then
        DB_TYPE="postgresql"
        log_info "检测到 PostgreSQL 数据库"

        # 解析 DATABASE_URL
        # 格式: postgres://user:password@host:port/dbname
        DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
        DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
        DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
        DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

        log_info "数据库信息: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
    elif [ -f "$BACKEND_DIR/db.sqlite3" ]; then
        DB_TYPE="sqlite"
        log_info "检测到 SQLite 数据库"
    else
        log_error "未检测到任何数据库配置"
        exit 1
    fi
}

# 检查必要文件是否存在
check_files() {
    log_info "检查必要文件..."

    # 检测数据库类型
    detect_database_type

    if [ "$DB_TYPE" = "sqlite" ]; then
        if [ ! -f "$BACKEND_DIR/db.sqlite3" ]; then
            log_error "SQLite数据库文件不存在: $BACKEND_DIR/db.sqlite3"
            exit 1
        fi
    elif [ "$DB_TYPE" = "postgresql" ]; then
        # 检查 pg_dump 是否可用
        if ! command -v pg_dump &> /dev/null; then
            log_error "pg_dump 命令未找到，请安装 PostgreSQL 客户端工具"
            exit 1
        fi
    fi

    log_success "文件检查完成"
}

# 备份数据库
backup_database() {
    log_info "备份数据库..."

    if [ "$DB_TYPE" = "sqlite" ]; then
        backup_sqlite
    elif [ "$DB_TYPE" = "postgresql" ]; then
        backup_postgresql
    fi
}

# 备份 SQLite 数据库
backup_sqlite() {
    log_info "备份 SQLite 数据库..."

    # 方法1: 直接复制SQLite文件
    cp "$BACKEND_DIR/db.sqlite3" "$BACKUP_DIR/db.sqlite3"
    log_success "SQLite数据库文件已备份"

    # 方法2: 导出为SQL格式
    if command -v sqlite3 &> /dev/null; then
        sqlite3 "$BACKEND_DIR/db.sqlite3" .dump > "$BACKUP_DIR/db_dump.sql"
        log_success "数据库SQL导出完成"
    else
        log_warning "sqlite3命令未找到，跳过SQL导出"
    fi

    # 方法3: 使用Django dumpdata命令导出JSON
    backup_django_data
}

# 备份 PostgreSQL 数据库
backup_postgresql() {
    log_info "备份 PostgreSQL 数据库..."

    # 设置 PostgreSQL 密码环境变量
    export PGPASSWORD="$DB_PASS"

    # 方法1: 使用 pg_dump 导出自定义格式（推荐，支持并行恢复）
    log_info "使用 pg_dump 导出自定义格式..."
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -F c -f "$BACKUP_DIR/db_backup.dump" 2>&1 || {
        log_error "pg_dump 自定义格式导出失败"
        unset PGPASSWORD
        exit 1
    }
    log_success "PostgreSQL 数据库自定义格式已备份 (db_backup.dump)"

    # 方法2: 导出为纯SQL格式（便于查看和手动恢复）
    log_info "导出纯SQL格式..."
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -f "$BACKUP_DIR/db_dump.sql" 2>&1 || {
        log_warning "SQL格式导出失败"
    }
    if [ -f "$BACKUP_DIR/db_dump.sql" ]; then
        # 压缩SQL文件以节省空间
        gzip "$BACKUP_DIR/db_dump.sql"
        log_success "PostgreSQL SQL导出完成并已压缩 (db_dump.sql.gz)"
    fi

    # 清除密码环境变量
    unset PGPASSWORD

    # 方法3: 使用Django dumpdata命令导出JSON
    backup_django_data
}

# 使用 Django dumpdata 导出数据
backup_django_data() {
    log_info "使用 Django dumpdata 导出 JSON 数据..."

    if [ -f "$BACKEND_DIR/manage.py" ]; then
        cd "$BACKEND_DIR"
        if [ -d ".venv" ]; then
            source .venv/bin/activate
        fi

        # 设置正确的 Django 设置模块
        if [ "$DB_TYPE" = "postgresql" ]; then
            export DJANGO_SETTINGS_MODULE=config.settings.production
        else
            export DJANGO_SETTINGS_MODULE=config.settings.development
        fi

        python manage.py dumpdata --settings=config.settings.production --indent 2 > "$BACKUP_DIR/data.json" 2>/dev/null || {
            log_warning "Django dumpdata 失败，可能是环境问题"
        }

        if [ -d ".venv" ]; then
            deactivate
        fi
        cd "$PROJECT_ROOT"

        if [ -f "$BACKUP_DIR/data.json" ]; then
            log_success "Django JSON 数据导出完成"
        fi
    fi
}

# 备份媒体文件
backup_media() {
    log_info "备份媒体文件..."

    # 检查媒体文件目录（支持多个可能的位置）
    MEDIA_PATHS=(
        "$PROJECT_ROOT/tacos_media"
        "$BACKEND_DIR/static/media"
    )

    local media_backed_up=false

    for media_path in "${MEDIA_PATHS[@]}"; do
        if [ -d "$media_path" ]; then
            log_info "找到媒体目录: $media_path"

            # 获取目录名
            local dir_name=$(basename "$media_path")
            local parent_dir=$(dirname "$media_path")

            # 使用tar压缩备份媒体文件
            tar -czf "$BACKUP_DIR/${dir_name}_files.tar.gz" -C "$parent_dir" "$dir_name/"
            log_success "媒体文件已压缩备份: ${dir_name}_files.tar.gz"

            # 计算媒体文件大小
            MEDIA_SIZE=$(du -sh "$media_path" | cut -f1)
            log_info "媒体文件大小: $MEDIA_SIZE"

            media_backed_up=true
        fi
    done

    if [ "$media_backed_up" = false ]; then
        log_warning "未找到媒体文件目录，跳过备份"
    fi
}

# 备份配置文件
backup_configs() {
    log_info "备份配置文件..."

    # 备份环境配置文件
    if [ -f "$BACKEND_DIR/.env" ]; then
        cp "$BACKEND_DIR/.env" "$BACKUP_DIR/.env"
        log_success "开发环境配置已备份"
    fi

    # 注意：不备份 .env.production.example（这是模板文件，应该在版本控制中）
    # 只备份 .env.production.local（包含实际的敏感配置）
    if [ -f "$BACKEND_DIR/.env.production.local" ]; then
        cp "$BACKEND_DIR/.env.production.local" "$BACKUP_DIR/.env.production.local"
        log_success "生产环境配置已备份 (.env.production.local)"
    fi

    # 备份requirements.txt
    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        cp "$BACKEND_DIR/requirements.txt" "$BACKUP_DIR/requirements.txt"
        log_success "Python依赖配置已备份"
    fi

    # 备份systemd服务配置（如果存在）
    if [ -f "/etc/systemd/system/tacos.service" ]; then
        sudo cp "/etc/systemd/system/tacos.service" "$BACKUP_DIR/tacos.service" 2>/dev/null || \
            log_warning "无法备份systemd服务配置（需要sudo权限）"
    fi
}

# 生成备份信息文件
generate_backup_info() {
    log_info "生成备份信息..."

    cat > "$BACKUP_DIR/backup_info.txt" << EOF
TaCOS 系统备份信息
==================

备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份目录: $BACKUP_DIR
数据库类型: $DB_TYPE
项目版本: $(git describe --tags 2>/dev/null || echo "未知")
Git提交: $(git rev-parse HEAD 2>/dev/null || echo "未知")

文件清单:
---------
EOF

    # 列出备份文件
    find "$BACKUP_DIR" -type f -exec basename {} \; | sort >> "$BACKUP_DIR/backup_info.txt"

    # 添加文件大小信息
    echo "" >> "$BACKUP_DIR/backup_info.txt"
    echo "文件大小:" >> "$BACKUP_DIR/backup_info.txt"
    du -sh "$BACKUP_DIR"/* >> "$BACKUP_DIR/backup_info.txt"

    log_success "备份信息文件已生成"
}

# 验证备份完整性
verify_backup() {
    log_info "验证备份完整性..."

    # 检查关键文件是否存在
    local missing_files=()

    # 根据数据库类型检查不同的备份文件
    if [ "$DB_TYPE" = "sqlite" ]; then
        if [ ! -f "$BACKUP_DIR/db.sqlite3" ]; then
            missing_files+=("db.sqlite3")
        fi
    elif [ "$DB_TYPE" = "postgresql" ]; then
        if [ ! -f "$BACKUP_DIR/db_backup.dump" ] && [ ! -f "$BACKUP_DIR/db_dump.sql.gz" ]; then
            missing_files+=("PostgreSQL备份文件")
        fi
    fi

    # 检查是否有任何媒体文件备份
    local has_media_backup=false
    if [ -f "$BACKUP_DIR/media_files.tar.gz" ] || [ -f "$BACKUP_DIR/tacos_media_files.tar.gz" ]; then
        has_media_backup=true
    fi

    if [ "$has_media_backup" = false ] && ([ -d "$BACKEND_DIR/static/media" ] || [ -d "$PROJECT_ROOT/tacos_media" ]); then
        missing_files+=("media_files")
    fi

    if [ ${#missing_files[@]} -eq 0 ]; then
        log_success "备份完整性验证通过"
    else
        log_error "备份不完整，缺少文件: ${missing_files[*]}"
        return 1
    fi

    # 验证数据库完整性
    if [ "$DB_TYPE" = "sqlite" ]; then
        if command -v sqlite3 &> /dev/null && [ -f "$BACKUP_DIR/db.sqlite3" ]; then
            if sqlite3 "$BACKUP_DIR/db.sqlite3" "PRAGMA integrity_check;" | grep -q "ok"; then
                log_success "SQLite 数据库完整性验证通过"
            else
                log_error "SQLite 数据库完整性验证失败"
                return 1
            fi
        fi
    elif [ "$DB_TYPE" = "postgresql" ]; then
        # PostgreSQL 备份文件存在即可，实际完整性需要在恢复时验证
        if [ -f "$BACKUP_DIR/db_backup.dump" ]; then
            local size=$(stat -f%z "$BACKUP_DIR/db_backup.dump" 2>/dev/null || stat -c%s "$BACKUP_DIR/db_backup.dump" 2>/dev/null)
            if [ $size -gt 0 ]; then
                log_success "PostgreSQL 备份文件验证通过 ($(numfmt --to=iec-i --suffix=B $size 2>/dev/null || echo "${size} bytes"))"
            else
                log_error "PostgreSQL 备份文件为空"
                return 1
            fi
        fi
    fi
}

# 清理旧备份（可选）
cleanup_old_backups() {
    if [ "$1" = "--cleanup" ]; then
        log_info "清理7天前的旧备份..."
        find ./tacos_backup -type d -name "20*" -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
        log_success "旧备份清理完成"
    fi
}

# 主函数
main() {
    # 检查是否在正确的目录
    if [ ! -d "tacos_backend" ]; then
        log_error "请在TaCOS项目根目录下运行此脚本"
        log_error "当前目录: $(pwd)"
        log_error "或者使用: cd /path/to/tacos && ./scripts/backup_tacos.sh"
        exit 1
    fi

    log_info "开始 TaCOS 系统备份..."
    log_info "备份时间: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "备份目录: $BACKUP_DIR"

    # 创建备份目录
    mkdir -p "$BACKUP_DIR"
    log_success "创建备份目录: $BACKUP_DIR"

    # 执行备份流程
    check_files
    backup_database
    backup_media
    backup_configs
    generate_backup_info

    # 验证备份
    if verify_backup; then
        log_success "备份完成！"
        log_info "备份位置: $BACKUP_DIR"
        log_info "备份大小: $(du -sh "$BACKUP_DIR" | cut -f1)"

        # 显示备份内容
        echo ""
        log_info "备份内容:"
        ls -la "$BACKUP_DIR"

        # 清理旧备份
        cleanup_old_backups "$1"

        echo ""
        log_success "🎉 TaCOS系统备份成功完成！"
    else
        log_error "备份验证失败，请检查备份文件"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "TaCOS 系统备份脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --cleanup    清理7天前的旧备份"
    echo "  --help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                # 执行备份"
    echo "  $0 --cleanup      # 执行备份并清理旧备份"
}

# 处理命令行参数
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        main "$1"
        ;;
esac
