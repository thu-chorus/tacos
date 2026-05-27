#!/bin/bash

# TaCOS 系统恢复脚本
# 用途: 从备份恢复数据库、媒体文件和配置文件

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

# 显示帮助信息
show_help() {
    echo "TaCOS 系统恢复脚本"
    echo ""
    echo "用法: $0 <备份目录> [选项]"
    echo ""
    echo "参数:"
    echo "  <备份目录>    备份文件夹路径 (例如: ./tacos_backup/20241201_143022)"
    echo ""
    echo "选项:"
    echo "  --database-only    仅恢复数据库"
    echo "  --media-only       仅恢复媒体文件"
    echo "  --config-only      仅恢复配置文件"
    echo "  --dry-run          预览模式，不执行实际恢复"
    echo "  --help             显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 ./tacos_backup/20241201_143022"
    echo "  $0 ./tacos_backup/20241201_143022 --database-only"
    echo "  $0 ./tacos_backup/20241201_143022 --dry-run"
}

# 检查备份目录
check_backup_dir() {
    local backup_dir="$1"

    if [ ! -d "$backup_dir" ]; then
        log_error "备份目录不存在: $backup_dir"
        exit 1
    fi

    if [ ! -f "$backup_dir/backup_info.txt" ]; then
        log_warning "备份信息文件不存在，可能不是有效的TaCOS备份"
    fi

    log_success "备份目录验证通过: $backup_dir"
}

# 显示备份信息
show_backup_info() {
    local backup_dir="$1"

    if [ -f "$backup_dir/backup_info.txt" ]; then
        log_info "备份信息:"
        cat "$backup_dir/backup_info.txt"
        echo ""
    fi
}

# 确认恢复操作
confirm_restore() {
    local backup_dir="$1"
    local mode="$2"

    echo ""
    log_warning "⚠️  警告: 此操作将覆盖当前系统数据！"
    echo ""
    log_info "恢复模式: $mode"
    log_info "备份目录: $backup_dir"
    log_info "目标目录: $BACKEND_DIR"
    echo ""

    read -p "确认要继续吗？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        exit 0
    fi
}

# 备份当前数据
backup_current_data() {
    local backup_dir="$1"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local current_backup_dir="./tacos_backup/restore_backup_$timestamp"

    log_info "备份当前数据到: $current_backup_dir"
    mkdir -p "$current_backup_dir"

    # 备份当前数据库
    if [ -f "$BACKEND_DIR/db.sqlite3" ]; then
        cp "$BACKEND_DIR/db.sqlite3" "$current_backup_dir/"
        log_success "当前数据库已备份"
    fi

    # 备份当前媒体文件
    if [ -d "$PROJECT_ROOT/tacos_media" ]; then
        tar -czf "$current_backup_dir/tacos_media_files.tar.gz" -C "$PROJECT_ROOT" tacos_media/
        log_success "当前 tacos_media 已备份"
    fi

    if [ -d "$BACKEND_DIR/static/media" ]; then
        tar -czf "$current_backup_dir/media_files.tar.gz" -C "$BACKEND_DIR/static" media/
        log_success "当前 static/media 已备份"
    fi

    # 备份当前配置文件
    cp "$BACKEND_DIR"/.env* "$current_backup_dir/" 2>/dev/null || true
    cp "$BACKEND_DIR"/requirements.txt "$current_backup_dir/" 2>/dev/null || true

    log_success "当前数据备份完成: $current_backup_dir"
}

# 检测数据库类型
detect_database_type() {
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
        log_info "目标数据库类型: PostgreSQL"

        # 解析 DATABASE_URL
        DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
        DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
        DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
        DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

        log_info "数据库信息: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
    else
        DB_TYPE="sqlite"
        log_info "目标数据库类型: SQLite"
    fi
}

# 恢复SQLite数据库
restore_sqlite() {
    local backup_dir="$1"
    local db_file="$backup_dir/db.sqlite3"
    local sql_dump="$backup_dir/db_dump.sql"

    if [ -f "$db_file" ]; then
        log_info "恢复SQLite数据库..."

        # 备份当前数据库
        if [ -f "$BACKEND_DIR/db.sqlite3" ]; then
            log_info "备份当前数据库..."
            cp "$BACKEND_DIR/db.sqlite3" "$BACKEND_DIR/db.sqlite3.before_restore"
        fi

        # 复制数据库文件
        cp "$db_file" "$BACKEND_DIR/db.sqlite3"

        # 验证数据库完整性
        if sqlite3 "$BACKEND_DIR/db.sqlite3" "PRAGMA integrity_check;" > /dev/null 2>&1; then
            log_success "SQLite数据库恢复成功并通过完整性检查"
            rm "$BACKEND_DIR/db.sqlite3.before_restore"
        else
            log_error "SQLite数据库完整性检查失败"
            if [ -f "$BACKEND_DIR/db.sqlite3.before_restore" ]; then
                log_info "恢复之前的数据库..."
                mv "$BACKEND_DIR/db.sqlite3.before_restore" "$BACKEND_DIR/db.sqlite3"
            fi
            return 1
        fi
    elif [ -f "$sql_dump" ]; then
        log_info "从SQL dump恢复SQLite数据库..."

        # 备份当前数据库
        if [ -f "$BACKEND_DIR/db.sqlite3" ]; then
            log_info "备份当前数据库..."
            cp "$BACKEND_DIR/db.sqlite3" "$BACKEND_DIR/db.sqlite3.before_restore"
        fi

        # 从SQL dump恢复
        sqlite3 "$BACKEND_DIR/db.sqlite3" < "$sql_dump"

        if [ $? -eq 0 ]; then
            log_success "从SQL dump恢复成功"
        else
            log_error "从SQL dump恢复失败"
            if [ -f "$BACKEND_DIR/db.sqlite3.before_restore" ]; then
                log_info "恢复之前的数据库..."
                mv "$BACKEND_DIR/db.sqlite3.before_restore" "$BACKEND_DIR/db.sqlite3"
            fi
            return 1
        fi
    else
        log_error "未找到数据库备份文件"
        return 1
    fi
}

# 恢复PostgreSQL数据库
restore_postgresql() {
    local backup_dir="$1"
    local dump_file="$backup_dir/db_backup.dump"
    local sql_gz="$backup_dir/db_dump.sql.gz"

    # 检查pg_restore是否可用
    if ! command -v pg_restore &> /dev/null; then
        log_error "未找到pg_restore命令，请安装PostgreSQL客户端工具"
        return 1
    fi

    # 设置PGPASSWORD环境变量
    export PGPASSWORD="$DB_PASS"

    if [ -f "$dump_file" ]; then
        log_info "恢复PostgreSQL数据库 (使用pg_restore)..."
        log_info "目标数据库: $DB_NAME @ $DB_HOST:$DB_PORT (用户: $DB_USER)"

        # 询问确认
        read -p "警告：这将覆盖现有数据库内容！是否继续？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "已取消恢复操作"
            unset PGPASSWORD
            return 1
        fi

        # 使用pg_restore恢复 (custom format)
        # --clean: 恢复前先删除现有对象
        # --if-exists: 删除对象时如果不存在不报错
        # --no-owner: 不恢复对象所有权
        # --no-privileges: 不恢复权限
        pg_restore --host="$DB_HOST" --port="$DB_PORT" --username="$DB_USER" \
                  --dbname="$DB_NAME" --clean --if-exists --no-owner --no-privileges \
                  "$dump_file"

        if [ $? -eq 0 ]; then
            log_success "PostgreSQL数据库恢复成功"
        else
            log_error "PostgreSQL数据库恢复失败"
            unset PGPASSWORD
            return 1
        fi
    elif [ -f "$sql_gz" ]; then
        log_info "恢复PostgreSQL数据库 (使用SQL dump)..."
        log_info "目标数据库: $DB_NAME @ $DB_HOST:$DB_PORT (用户: $DB_USER)"

        # 询问确认
        read -p "警告：这将覆盖现有数据库内容！是否继续？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "已取消恢复操作"
            unset PGPASSWORD
            return 1
        fi

        # 解压并通过psql导入
        gunzip -c "$sql_gz" | psql --host="$DB_HOST" --port="$DB_PORT" \
                                   --username="$DB_USER" --dbname="$DB_NAME"

        if [ $? -eq 0 ]; then
            log_success "PostgreSQL数据库恢复成功"
        else
            log_error "PostgreSQL数据库恢复失败"
            unset PGPASSWORD
            return 1
        fi
    else
        log_error "未找到PostgreSQL备份文件 (db_backup.dump 或 db_dump.sql.gz)"
        unset PGPASSWORD
        return 1
    fi

    # 清除密码环境变量
    unset PGPASSWORD
}

# 恢复数据库
restore_database() {
    local backup_dir="$1"
    local dry_run="$2"

    log_info "恢复数据库..."

    # 检测数据库类型
    detect_database_type

    if [ "$dry_run" = "true" ]; then
        log_info "[预览] 将恢复数据库文件 (类型: $DB_TYPE)"
        return 0
    fi

    # 停止可能运行的服务
    log_info "停止相关服务..."
    if systemctl is-active --quiet tacos 2>/dev/null; then
        log_info "停止 systemd 服务..."
        sudo systemctl stop tacos
    fi

    # 根据数据库类型恢复
    if [ "$DB_TYPE" = "sqlite" ]; then
        restore_sqlite "$backup_dir"
    elif [ "$DB_TYPE" = "postgresql" ]; then
        restore_postgresql "$backup_dir"
    fi

    # 如果存在JSON数据文件，提供从JSON恢复的选项
    if [ -f "$backup_dir/data.json" ]; then
        log_info "发现JSON数据文件，可选择从JSON恢复"
        log_warning "注意: JSON恢复将排除contenttypes和permissions（这些会自动生成）"
        read -p "是否从JSON文件恢复数据？这将清空现有数据 (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd "$BACKEND_DIR"
            if [ -d ".venv" ]; then
                source .venv/bin/activate
            fi

            # 如果是SQLite，删除数据库文件重新创建
            if [ "$DB_TYPE" = "sqlite" ]; then
                log_info "删除现有SQLite数据库..."
                rm -f db.sqlite3

                log_info "运行数据库迁移..."
                python manage.py migrate --noinput

                # 从JSON恢复（排除自动生成的表）
                log_info "从JSON文件导入数据（排除contenttypes和permissions）..."
                python manage.py loaddata "$backup_dir/data.json" \
                    --exclude contenttypes \
                    --exclude auth.Permission
            else
                # 清空 PostgreSQL 数据库
                log_info "清空PostgreSQL数据库..."
                python manage.py flush --noinput --settings=config.settings.production

                # 从JSON恢复（排除自动生成的表）
                log_info "从JSON文件导入数据（排除contenttypes和permissions）..."
                python manage.py loaddata "$backup_dir/data.json" \
                    --exclude contenttypes \
                    --exclude auth.Permission \
                    --settings=config.settings.production
            fi

            if [ $? -eq 0 ]; then
                log_success "JSON数据导入成功"
            else
                log_error "JSON数据导入失败"
            fi

            if [ -d ".venv" ]; then
                deactivate
            fi
            cd "$PROJECT_ROOT"
            log_success "从JSON数据恢复完成"
        fi
    fi
}

# 恢复媒体文件
restore_media() {
    local backup_dir="$1"
    local dry_run="$2"

    log_info "恢复媒体文件..."

    if [ "$dry_run" = "true" ]; then
        log_info "[预览] 将恢复媒体文件"
        return 0
    fi

    local media_restored=false

    # 恢复 tacos_media 目录
    if [ -f "$backup_dir/tacos_media_files.tar.gz" ]; then
        log_info "恢复 tacos_media 目录..."
        tar -xzf "$backup_dir/tacos_media_files.tar.gz" -C "$PROJECT_ROOT/"
        chmod -R 755 "$PROJECT_ROOT/tacos_media/"
        log_success "tacos_media 目录已恢复"
        media_restored=true
    fi

    # 恢复 static/media 目录
    if [ -f "$backup_dir/media_files.tar.gz" ]; then
        log_info "恢复 static/media 目录..."
        mkdir -p "$BACKEND_DIR/static"
        tar -xzf "$backup_dir/media_files.tar.gz" -C "$BACKEND_DIR/static/"
        chmod -R 755 "$BACKEND_DIR/static/media/"
        log_success "static/media 目录已恢复"
        media_restored=true
    fi

    if [ "$media_restored" = false ]; then
        log_warning "备份中未找到媒体文件"
    fi
}

# 恢复配置文件
restore_configs() {
    local backup_dir="$1"
    local dry_run="$2"

    log_info "恢复配置文件..."

    if [ "$dry_run" = "true" ]; then
        log_info "[预览] 将恢复配置文件"
        return 0
    fi

    # 恢复环境配置文件
    if [ -f "$backup_dir/.env" ]; then
        cp "$backup_dir/.env" "$BACKEND_DIR/.env"
        log_success "开发环境配置已恢复"
    fi

    if [ -f "$backup_dir/.env.production.local" ]; then
        cp "$backup_dir/.env.production.local" "$BACKEND_DIR/.env.production.local"
        log_success "生产环境配置已恢复 (.env.production.local)"
    fi

    # 恢复requirements.txt
    if [ -f "$backup_dir/requirements.txt" ]; then
        cp "$backup_dir/requirements.txt" "$BACKEND_DIR/requirements.txt"
        log_success "Python依赖配置已恢复"
    fi

    # 恢复systemd服务配置（需要sudo权限）
    if [ -f "$backup_dir/tacos.service" ]; then
        log_info "发现systemd服务配置备份"
        read -p "是否恢复systemd服务配置？(需要sudo权限) (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo cp "$backup_dir/tacos.service" "/etc/systemd/system/tacos.service"
            sudo systemctl daemon-reload
            log_success "systemd服务配置已恢复"
        fi
    fi
}

# 验证恢复结果
verify_restore() {
    local backup_dir="$1"
    local mode="$2"

    log_info "验证恢复结果..."

    local errors=0

    # 验证数据库
    if [[ "$mode" == *"database"* ]] || [[ "$mode" == "all" ]]; then
        # 检测数据库类型
        detect_database_type

        if [ "$DB_TYPE" = "sqlite" ]; then
            # SQLite 数据库验证
            if [ -f "$BACKEND_DIR/db.sqlite3" ]; then
                if command -v sqlite3 &> /dev/null; then
                    if sqlite3 "$BACKEND_DIR/db.sqlite3" "PRAGMA integrity_check;" | grep -q "ok"; then
                        log_success "SQLite数据库恢复验证通过"
                    else
                        log_error "SQLite数据库恢复验证失败"
                        ((errors++))
                    fi
                else
                    log_warning "未安装sqlite3命令，跳过数据库完整性检查"
                fi
            else
                log_error "SQLite数据库文件不存在"
                ((errors++))
            fi
        elif [ "$DB_TYPE" = "postgresql" ]; then
            # PostgreSQL 数据库验证
            if command -v psql &> /dev/null; then
                export PGPASSWORD="$DB_PASS"
                if psql --host="$DB_HOST" --port="$DB_PORT" --username="$DB_USER" \
                       --dbname="$DB_NAME" --command="SELECT 1;" > /dev/null 2>&1; then
                    log_success "PostgreSQL数据库连接验证通过"
                else
                    log_error "PostgreSQL数据库连接验证失败"
                    ((errors++))
                fi
                unset PGPASSWORD
            else
                log_warning "未安装psql命令，跳过数据库连接检查"
            fi
        fi
    fi

    # 验证媒体文件
    if [[ "$mode" == *"media"* ]] || [[ "$mode" == "all" ]]; then
        local media_verified=false
        if [ -d "$PROJECT_ROOT/tacos_media" ]; then
            log_success "tacos_media 目录恢复验证通过"
            media_verified=true
        fi
        if [ -d "$BACKEND_DIR/static/media" ]; then
            log_success "static/media 目录恢复验证通过"
            media_verified=true
        fi
        if [ "$media_verified" = false ]; then
            log_error "媒体文件目录不存在"
            ((errors++))
        fi
    fi

    # 验证配置文件
    if [[ "$mode" == *"config"* ]] || [[ "$mode" == "all" ]]; then
        if [ -f "$BACKEND_DIR/.env" ] || [ -f "$BACKEND_DIR/.env.production.local" ]; then
            log_success "配置文件恢复验证通过"
        else
            log_warning "未找到环境配置文件"
        fi
    fi

    if [ $errors -eq 0 ]; then
        log_success "恢复验证完成，无错误"
        return 0
    else
        log_error "恢复验证发现 $errors 个错误"
        return 1
    fi
}

# 主函数
main() {
    local backup_dir=""
    local mode="all"
    local dry_run="false"

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --database-only)
                mode="database"
                shift
                ;;
            --media-only)
                mode="media"
                shift
                ;;
            --config-only)
                mode="config"
                shift
                ;;
            --dry-run)
                dry_run="true"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            -*)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
            *)
                if [ -z "$backup_dir" ]; then
                    backup_dir="$1"
                else
                    log_error "只能指定一个备份目录"
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # 检查参数
    if [ -z "$backup_dir" ]; then
        log_error "请指定备份目录"
        show_help
        exit 1
    fi

    # 转换为绝对路径
    backup_dir="$(cd "$backup_dir" 2>/dev/null && pwd)" || {
        log_error "无法访问备份目录: $1"
        exit 1
    }
    log_info "使用备份目录: $backup_dir"

    # 检查是否在正确的目录
    if [ ! -d "tacos_backend" ]; then
        log_error "请在TaCOS项目根目录下运行此脚本"
        log_error "或者使用: cd /path/to/tacos && ./scripts/restore_tacos.sh <backup_dir>"
        exit 1
    fi

    # 检查备份目录
    check_backup_dir "$backup_dir"

    # 显示备份信息
    show_backup_info "$backup_dir"

    # 确认操作
    if [ "$dry_run" != "true" ]; then
        confirm_restore "$backup_dir" "$mode"

        # 备份当前数据
        backup_current_data "$backup_dir"
    fi

    # 执行恢复
    case $mode in
        "database")
            restore_database "$backup_dir" "$dry_run"
            ;;
        "media")
            restore_media "$backup_dir" "$dry_run"
            ;;
        "config")
            restore_configs "$backup_dir" "$dry_run"
            ;;
        "all")
            restore_database "$backup_dir" "$dry_run"
            restore_media "$backup_dir" "$dry_run"
            restore_configs "$backup_dir" "$dry_run"
            ;;
    esac

    # 验证恢复结果
    if [ "$dry_run" != "true" ]; then
        if verify_restore "$backup_dir" "$mode"; then
            log_success "🎉 TaCOS系统恢复成功完成！"
            echo ""

            # 检查并重启服务
            if systemctl list-unit-files tacos.service &>/dev/null; then
                log_info "重启 tacos 服务..."
                sudo systemctl restart tacos
                sleep 2
                if systemctl is-active --quiet tacos; then
                    log_success "tacos 服务已成功重启"
                else
                    log_error "tacos 服务启动失败，请检查日志: sudo journalctl -u tacos -n 50"
                fi
            else
                log_info "未检测到 systemd 服务，请手动启动应用:"
                log_info "  cd tacos_backend && source .venv/bin/activate"
                log_info "  python manage.py runserver"
            fi
        else
            log_error "恢复过程中出现错误，请检查日志"
            exit 1
        fi
    else
        log_info "预览模式完成，未执行实际恢复操作"
    fi
}

# 执行主函数
main "$@"
