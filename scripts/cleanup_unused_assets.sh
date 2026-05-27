#!/bin/bash

# TaCOS 资产清理脚本
# 用途: 检测和清理无用的资产文件（未被数据库引用的文件）

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_highlight() {
    echo -e "${CYAN}[HIGHLIGHT]${NC} $1"
}

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/tacos_backend"
# 支持多个媒体目录位置
MEDIA_DIRS=(
    "$PROJECT_ROOT/tacos_media"
    "$BACKEND_DIR/static/media"
)
DB_FILE="$BACKEND_DIR/db.sqlite3"

# 数据库类型和配置
DB_TYPE=""  # sqlite 或 postgresql
DB_NAME=""
DB_USER=""
DB_PASSWORD=""
DB_HOST=""
DB_PORT=""

# 临时文件
TEMP_DIR="/tmp/tacos_cleanup_$$"
REFERENCED_FILES="$TEMP_DIR/referenced_files.txt"
ALL_FILES="$TEMP_DIR/all_files.txt"
UNUSED_FILES="$TEMP_DIR/unused_files.txt"

# 显示帮助信息
show_help() {
    echo "TaCOS 资产清理脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --dry-run          预览模式，仅显示要删除的文件，不执行删除"
    echo "  --force            强制模式，跳过二次确认"
    echo "  --backup           删除前备份文件到备份目录"
    echo "  --cleanup-ds       同时清理 .DS_Store 文件"
    echo "  --help             显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --dry-run        # 预览要删除的文件"
    echo "  $0 --backup         # 备份后删除无用文件"
    echo "  $0 --force          # 强制删除（跳过确认）"
    echo "  $0 --cleanup-ds     # 同时清理系统文件"
}

# 检测数据库类型
detect_database_type() {
    log_info "检测数据库类型..."

    # 优先检查 .env.production.local（生产环境）
    local env_file=""
    if [ -f "$BACKEND_DIR/.env.production.local" ]; then
        env_file="$BACKEND_DIR/.env.production.local"
        log_info "使用配置文件: .env.production.local"
    elif [ -f "$BACKEND_DIR/.env" ]; then
        env_file="$BACKEND_DIR/.env"
        log_info "使用配置文件: .env"
    else
        log_warning "未找到环境配置文件，默认使用 SQLite"
        DB_TYPE="sqlite"
        return 0
    fi

    # 读取 DATABASE_URL
    local database_url=$(grep "^DATABASE_URL=" "$env_file" | cut -d'=' -f2- | tr -d '"' | tr -d "'")

    if [ -z "$database_url" ]; then
        log_warning "未找到 DATABASE_URL 配置，默认使用 SQLite"
        DB_TYPE="sqlite"
        return 0
    fi

    # 解析数据库类型
    if [[ $database_url == postgres://* ]] || [[ $database_url == postgresql://* ]]; then
        DB_TYPE="postgresql"
        log_info "检测到 PostgreSQL 数据库"

        # 解析 PostgreSQL 连接信息
        # 格式: postgresql://user:password@host:port/database
        local url_pattern="postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)"
        if [[ $database_url =~ $url_pattern ]]; then
            DB_USER="${BASH_REMATCH[1]}"
            DB_PASSWORD="${BASH_REMATCH[2]}"
            DB_HOST="${BASH_REMATCH[3]}"
            DB_PORT="${BASH_REMATCH[4]}"
            DB_NAME="${BASH_REMATCH[5]}"
        else
            # 尝试 postgres:// 前缀
            url_pattern="postgres://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)"
            if [[ $database_url =~ $url_pattern ]]; then
                DB_USER="${BASH_REMATCH[1]}"
                DB_PASSWORD="${BASH_REMATCH[2]}"
                DB_HOST="${BASH_REMATCH[3]}"
                DB_PORT="${BASH_REMATCH[4]}"
                DB_NAME="${BASH_REMATCH[5]}"
            else
                log_error "无法解析 PostgreSQL 连接字符串"
                exit 1
            fi
        fi

        log_info "数据库: $DB_NAME @ $DB_HOST:$DB_PORT"
    else
        DB_TYPE="sqlite"
        log_info "检测到 SQLite 数据库"
    fi
}

# 检查环境
check_environment() {
    log_info "检查环境..."

    # 检查是否在正确的目录
    if [ ! -d "tacos_backend" ]; then
        log_error "请在TaCOS项目根目录下运行此脚本"
        log_error "或者使用: cd /path/to/tacos && ./scripts/cleanup_unused_assets.sh"
        exit 1
    fi

    # 检测数据库类型
    detect_database_type

    # 根据数据库类型检查相应的工具
    if [ "$DB_TYPE" = "postgresql" ]; then
        if ! command -v psql &> /dev/null; then
            log_error "psql 命令未找到，请安装 PostgreSQL 客户端"
            log_error "Ubuntu/Debian: sudo apt-get install postgresql-client"
            log_error "CentOS/RHEL: sudo yum install postgresql"
            log_error "macOS: brew install postgresql"
            exit 1
        fi
        log_success "PostgreSQL 客户端检查通过"
    else
        # 检查数据库文件
        if [ ! -f "$DB_FILE" ]; then
            log_error "数据库文件不存在: $DB_FILE"
            exit 1
        fi

        # 检查sqlite3命令
        if ! command -v sqlite3 &> /dev/null; then
            log_error "sqlite3 命令未找到，请安装 sqlite3"
            exit 1
        fi
        log_success "SQLite 检查通过"
    fi

    # 检查媒体目录
    local media_found=false
    for media_dir in "${MEDIA_DIRS[@]}"; do
        if [ -d "$media_dir" ]; then
            media_found=true
            log_info "找到媒体目录: $media_dir"
        fi
    done

    if [ "$media_found" = false ]; then
        log_error "未找到任何媒体目录"
        exit 1
    fi

    # 创建临时目录
    mkdir -p "$TEMP_DIR"

    log_success "环境检查完成"
}

# 执行数据库查询的通用函数
execute_query() {
    local query="$1"

    if [ "$DB_TYPE" = "postgresql" ]; then
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "$query" 2>/dev/null || true
    else
        sqlite3 "$DB_FILE" "$query" 2>/dev/null || true
    fi
}

# 检查数据库表结构
check_database_structure() {
    log_info "检查数据库表结构..."

    # 获取所有包含文件字段的表（排除索引）
    local file_tables=""
    if [ "$DB_TYPE" = "postgresql" ]; then
        file_tables=$(execute_query "
            SELECT DISTINCT table_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND (column_name LIKE '%file%' OR column_name LIKE '%image%')
            AND table_name NOT LIKE '%_idx_%' AND table_name NOT LIKE '%_index%'
            ORDER BY table_name;
        ")
    else
        file_tables=$(execute_query "
            SELECT DISTINCT name FROM sqlite_master
            WHERE type='table' AND (sql LIKE '%file%' OR sql LIKE '%image%')
            AND name NOT LIKE '%_idx_%' AND name NOT LIKE '%_index%'
            ORDER BY name;
        ")
    fi

    # 预期的文件相关表（这些表已在 get_referenced_files() 函数中被处理）
    local expected_tables=("assignment_attachments" "assignment_submission_attachments" "event_announcement_images" "sheets")

    log_info "数据库中发现的文件相关表:"
    if [ -n "$file_tables" ]; then
        echo "$file_tables" | while read -r table; do
            echo "  - $table"
        done
    else
        log_warning "未发现任何文件相关表"
    fi

    # 检查是否有未预期的表
    local unexpected_tables=()
    if [ -n "$file_tables" ]; then
        while IFS= read -r table; do
            # 去除可能的空格
            table=$(echo "$table" | tr -d '[:space:]')
            if [ -z "$table" ]; then
                continue
            fi

            local is_expected=0
            for expected in "${expected_tables[@]}"; do
                if [ "$table" = "$expected" ]; then
                    is_expected=1
                    break
                fi
            done
            if [ $is_expected -eq 0 ]; then
                unexpected_tables+=("$table")
            fi
        done <<< "$file_tables"
    fi

    # 检查是否有缺失的预期表
    local missing_tables=()
    for expected in "${expected_tables[@]}"; do
        local found=0
        if [ -n "$file_tables" ]; then
            while IFS= read -r table; do
                # 去除可能的空格
                table=$(echo "$table" | tr -d '[:space:]')
                if [ "$table" = "$expected" ]; then
                    found=1
                    break
                fi
            done <<< "$file_tables"
        fi
        if [ $found -eq 0 ]; then
            missing_tables+=("$expected")
        fi
    done

    # 显示检查结果
    if [ ${#unexpected_tables[@]} -gt 0 ]; then
        echo ""
        log_warning "⚠️  发现未预期的文件相关表:"
        for table in "${unexpected_tables[@]}"; do
            echo "  - $table"
        done
        echo ""
        log_error "数据库结构已发生变化！"
        log_error "请更新 cleanup_assets.sh 脚本以包含这些新表:"
        for table in "${unexpected_tables[@]}"; do
            echo "  - 需要在 get_referenced_files() 函数中添加对 $table 表的处理"
        done
        echo ""
        log_warning "建议:"
        echo "  1. 检查这些表的字段结构"
        echo "  2. 确定哪些字段存储文件路径"
        echo "  3. 在脚本中添加相应的SQL查询"
        echo "  4. 更新 expected_tables 数组"
        echo ""
        read -p "是否继续执行清理？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "操作已取消，请先更新脚本"
            exit 1
        fi
    fi

    if [ ${#missing_tables[@]} -gt 0 ]; then
        echo ""
        log_warning "⚠️  预期的文件相关表未找到:"
        for table in "${missing_tables[@]}"; do
            echo "  - $table"
        done
        echo ""
        log_warning "这些表可能已被删除或重命名"
    fi

    if [ ${#unexpected_tables[@]} -eq 0 ] && [ ${#missing_tables[@]} -eq 0 ]; then
        log_success "数据库表结构检查通过，所有预期的文件相关表都存在"
    fi

    echo ""
}

# 从数据库获取被引用的文件
get_referenced_files() {
    log_info "分析数据库中的文件引用..."

    # 清空引用文件列表
    > "$REFERENCED_FILES"

    # 从各个表中提取文件路径
    log_info "提取乐谱文件引用..."
    execute_query "SELECT original_file FROM sheets WHERE original_file IS NOT NULL AND original_file != '';" >> "$REFERENCED_FILES"

    log_info "提取作业附件引用..."
    execute_query "SELECT file FROM assignment_attachments WHERE file IS NOT NULL AND file != '';" >> "$REFERENCED_FILES"

    log_info "提取作业提交附件引用..."
    execute_query "SELECT file FROM assignment_submission_attachments WHERE file IS NOT NULL AND file != '';" >> "$REFERENCED_FILES"

    log_info "提取活动公告图片引用..."
    execute_query "SELECT image FROM event_announcement_images WHERE image IS NOT NULL AND image != '';" >> "$REFERENCED_FILES"

    # 去重并排序
    sort -u "$REFERENCED_FILES" > "$REFERENCED_FILES.tmp" && mv "$REFERENCED_FILES.tmp" "$REFERENCED_FILES"

    local referenced_count=$(wc -l < "$REFERENCED_FILES")
    log_success "找到 $referenced_count 个被引用的文件"

    # 显示被引用的文件（前10个）
    if [ $referenced_count -gt 0 ]; then
        log_info "被引用的文件示例:"
        head -10 "$REFERENCED_FILES" | while read -r file; do
            echo "  - $file"
        done
        if [ $referenced_count -gt 10 ]; then
            echo "  ... 还有 $((referenced_count - 10)) 个文件"
        fi
    fi
}

# 获取所有媒体文件
get_all_media_files() {
    log_info "扫描媒体目录中的所有文件..."

    # 清空文件列表
    > "$ALL_FILES"

    # 从所有媒体目录获取文件
    for media_dir in "${MEDIA_DIRS[@]}"; do
        if [ -d "$media_dir" ]; then
            log_info "扫描目录: $media_dir"
            # 获取相对于媒体根目录的路径
            find "$media_dir" -type f | while read -r file; do
                # 提取相对路径（去除媒体根目录前缀）
                echo "$file" | sed "s|^$media_dir/||" >> "$ALL_FILES"
            done
        fi
    done

    # 去重并排序
    sort -u "$ALL_FILES" > "$ALL_FILES.tmp" && mv "$ALL_FILES.tmp" "$ALL_FILES"

    local total_count=$(wc -l < "$ALL_FILES")
    log_success "找到 $total_count 个媒体文件"
}

# 识别无用文件
identify_unused_files() {
    log_info "识别无用文件..."

    # 找出不在引用列表中的文件
    comm -23 "$ALL_FILES" "$REFERENCED_FILES" > "$UNUSED_FILES.tmp"

    # 过滤掉需要保留的文件（Git 相关文件等）
    local exclude_patterns=(".gitignore" ".gitkeep" ".DS_Store" "Thumbs.db" "desktop.ini")

    > "$UNUSED_FILES"
    while IFS= read -r file; do
        local should_exclude=0
        local basename=$(basename "$file")

        for pattern in "${exclude_patterns[@]}"; do
            if [ "$basename" = "$pattern" ]; then
                should_exclude=1
                break
            fi
        done

        if [ $should_exclude -eq 0 ]; then
            echo "$file" >> "$UNUSED_FILES"
        fi
    done < "$UNUSED_FILES.tmp"

    rm -f "$UNUSED_FILES.tmp"

    local unused_count=$(wc -l < "$UNUSED_FILES")
    log_success "识别出 $unused_count 个无用文件（已过滤 Git 和系统文件）"

    if [ $unused_count -gt 0 ]; then
        log_info "无用文件示例:"
        head -10 "$UNUSED_FILES" | while read -r file; do
            echo "  - $file"
        done
        if [ $unused_count -gt 10 ]; then
            echo "  ... 还有 $((unused_count - 10)) 个文件"
        fi
    fi
}

# 格式化字节数
format_bytes() {
    local bytes=$1
    if [ $bytes -eq 0 ]; then
        echo "0 B"
    elif [ $bytes -lt 1024 ]; then
        echo "${bytes} B"
    elif [ $bytes -lt 1048576 ]; then
        echo "$((bytes / 1024)) KB"
    elif [ $bytes -lt 1073741824 ]; then
        echo "$((bytes / 1048576)) MB"
    else
        echo "$((bytes / 1073741824)) GB"
    fi
}

# 计算文件大小
calculate_file_sizes() {
    local file_list="$1"
    local total_size=0
    local file_count=0

    while IFS= read -r file; do
        local found=false
        # 在所有媒体目录中查找文件
        for media_dir in "${MEDIA_DIRS[@]}"; do
            if [ -f "$media_dir/$file" ]; then
                local size=$(stat -f%z "$media_dir/$file" 2>/dev/null || stat -c%s "$media_dir/$file" 2>/dev/null || echo 0)
                total_size=$((total_size + size))
                file_count=$((file_count + 1))
                found=true
                break
            fi
        done
    done < "$file_list"

    echo "$file_count:$total_size"
}

# 显示统计信息
show_statistics() {
    log_highlight "=== 文件统计信息 ==="

    # 被引用文件统计
    local referenced_stats=$(calculate_file_sizes "$REFERENCED_FILES")
    local referenced_count=$(echo "$referenced_stats" | cut -d: -f1)
    local referenced_size=$(echo "$referenced_stats" | cut -d: -f2)

    # 无用文件统计
    local unused_stats=$(calculate_file_sizes "$UNUSED_FILES")
    local unused_count=$(echo "$unused_stats" | cut -d: -f1)
    local unused_size=$(echo "$unused_stats" | cut -d: -f2)

    # 总文件统计
    local total_stats=$(calculate_file_sizes "$ALL_FILES")
    local total_count=$(echo "$total_stats" | cut -d: -f1)
    local total_size=$(echo "$total_stats" | cut -d: -f2)

    echo "总文件数: $total_count"
    echo "被引用文件: $referenced_count"
    echo "无用文件: $unused_count"
    echo ""
    echo "总大小: $(format_bytes $total_size)"
    echo "被引用文件大小: $(format_bytes $referenced_size)"
    echo "无用文件大小: $(format_bytes $unused_size)"
    echo ""

    if [ $unused_count -gt 0 ]; then
        local saved_percent=$((unused_size * 100 / total_size))
        echo "可释放空间: $(format_bytes $unused_size) ($saved_percent%)"
    fi
}

# 备份无用文件
backup_unused_files() {
    local backup_dir="./tacos_backup/unused_files_$(date +%Y%m%d_%H%M%S)"

    log_info "备份无用文件到: $backup_dir"
    mkdir -p "$backup_dir"

    local backup_count=0
    while IFS= read -r file; do
        # 在所有媒体目录中查找文件
        for media_dir in "${MEDIA_DIRS[@]}"; do
            if [ -f "$media_dir/$file" ]; then
                local dir_path=$(dirname "$file")
                mkdir -p "$backup_dir/$dir_path"
                cp "$media_dir/$file" "$backup_dir/$file"
                backup_count=$((backup_count + 1))
                break
            fi
        done
    done < "$UNUSED_FILES"

    log_success "已备份 $backup_count 个文件到 $backup_dir"
}

# 删除无用文件
delete_unused_files() {
    local dry_run="$1"
    local force="$2"
    local backup="$3"

    local unused_count=$(wc -l < "$UNUSED_FILES")

    if [ $unused_count -eq 0 ]; then
        log_success "没有发现无用文件，无需清理"
        return 0
    fi

    if [ "$dry_run" = "true" ]; then
        log_highlight "=== 预览模式 - 以下文件将被删除 ==="
        cat "$UNUSED_FILES"
        echo ""
        log_info "预览完成，未执行实际删除操作"
        return 0
    fi

    # 备份文件（如果需要）
    if [ "$backup" = "true" ]; then
        backup_unused_files
    fi

    # 确认删除
    if [ "$force" != "true" ]; then
        echo ""
        log_warning "⚠️  即将删除 $unused_count 个无用文件！"
        echo ""
        log_info "要删除的文件列表:"
        head -20 "$UNUSED_FILES" | while read -r file; do
            echo "  - $file"
        done
        if [ $unused_count -gt 20 ]; then
            echo "  ... 还有 $((unused_count - 20)) 个文件"
        fi
        echo ""

        read -p "确认要删除这些文件吗？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "操作已取消"
            return 0
        fi
    fi

    # 执行删除
    log_info "开始删除无用文件..."
    local deleted_count=0
    local error_count=0

    while IFS= read -r file; do
        local deleted=false
        # 在所有媒体目录中查找并删除文件
        for media_dir in "${MEDIA_DIRS[@]}"; do
            if [ -f "$media_dir/$file" ]; then
                if rm "$media_dir/$file" 2>/dev/null; then
                    deleted_count=$((deleted_count + 1))
                    if [ $((deleted_count % 10)) -eq 0 ]; then
                        log_info "已删除 $deleted_count 个文件..."
                    fi
                    deleted=true
                else
                    log_error "删除失败: $file"
                    error_count=$((error_count + 1))
                fi
                break
            fi
        done
    done < "$UNUSED_FILES"

    echo ""
    if [ $error_count -eq 0 ]; then
        log_success "成功删除 $deleted_count 个无用文件"
    else
        log_warning "删除了 $deleted_count 个文件，$error_count 个文件删除失败"
    fi
}

# 清理空目录
cleanup_empty_directories() {
    log_info "清理空目录..."

    local cleaned_count=0
    # 从所有媒体目录清理空目录
    for media_dir in "${MEDIA_DIRS[@]}"; do
        if [ -d "$media_dir" ]; then
            # 从最深层的目录开始清理
            local count=$(find "$media_dir" -type d -empty -delete 2>/dev/null | wc -l)
            cleaned_count=$((cleaned_count + count))
        fi
    done

    if [ $cleaned_count -gt 0 ]; then
        log_success "清理了 $cleaned_count 个空目录"
    else
        log_info "没有发现空目录"
    fi
}

# 清理系统文件
cleanup_system_files() {
    log_info "清理系统文件..."

    local system_files=(".DS_Store" "Thumbs.db" "desktop.ini")
    local cleaned_count=0

    for media_dir in "${MEDIA_DIRS[@]}"; do
        if [ -d "$media_dir" ]; then
            for pattern in "${system_files[@]}"; do
                local count=$(find "$media_dir" -name "$pattern" -type f -delete 2>/dev/null | wc -l)
                cleaned_count=$((cleaned_count + count))
            done
        fi
    done

    if [ $cleaned_count -gt 0 ]; then
        log_success "清理了 $cleaned_count 个系统文件"
    else
        log_info "没有发现系统文件"
    fi
}

# 清理临时文件
cleanup_temp_files() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
        log_info "清理临时文件完成"
    fi
}

# 主函数
main() {
    local dry_run="false"
    local force="false"
    local backup="false"
    local cleanup_ds="false"

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run="true"
                shift
                ;;
            --force)
                force="true"
                shift
                ;;
            --backup)
                backup="true"
                shift
                ;;
            --cleanup-ds)
                cleanup_ds="true"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 设置退出时清理临时文件
    trap cleanup_temp_files EXIT

    log_highlight "=== TaCOS 资产清理工具 ==="
    log_info "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"

    # 执行清理流程
    check_environment
    check_database_structure
    get_referenced_files
    get_all_media_files
    identify_unused_files
    show_statistics

    # 删除无用文件
    delete_unused_files "$dry_run" "$force" "$backup"

    # 清理空目录
    cleanup_empty_directories

    # 清理系统文件（如果需要）
    if [ "$cleanup_ds" = "true" ]; then
        cleanup_system_files
    fi

    log_success "🎉 资产清理完成！"
    log_info "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
}

# 执行主函数
main "$@"
