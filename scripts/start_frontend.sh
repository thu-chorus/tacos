#!/bin/bash

# 清华合唱队在线系统 - 前端启动脚本
#
# 此脚本用于启动 TaCOS 前端开发服务器
# 支持环境检查、依赖安装、环境变量配置等功能

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

# 显示帮助信息
show_help() {
    echo "TaCOS Frontend Startup Script"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示此帮助信息"
    echo "  -p, --port PORT         指定端口号 (默认: 3000)"
    echo "  -b, --backend-url URL   指定后端API地址 (默认: http://localhost:8000)"
    echo "  -i, --install           强制重新安装依赖"
    echo "  -s, --skip-check        跳过环境检查"
    echo "  -d, --dev               开发模式 (默认)"
    echo "  -p, --prod              生产模式预览"
    echo "  --build                 构建生产版本"
    echo "  --clean                 清理 node_modules 和重新安装"
    echo ""
    echo "示例:"
    echo "  $0                      # 使用默认设置启动开发服务器"
    echo "  $0 -p 3001             # 在端口 3001 启动"
    echo "  $0 -b http://api.example.com  # 指定后端地址"
    echo "  $0 --build             # 构建生产版本"
    echo "  $0 --clean             # 清理并重新安装依赖"
}

# 默认配置
DEFAULT_PORT=3000
DEFAULT_BACKEND_URL="http://localhost:8000"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/tacos_frontend"
FORCE_INSTALL=false
SKIP_CHECK=false
MODE="dev"
BUILD_MODE=false
CLEAN_MODE=false
CUSTOM_PORT=""
CUSTOM_BACKEND_URL=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--port)
            CUSTOM_PORT="$2"
            shift 2
            ;;
        -b|--backend-url)
            CUSTOM_BACKEND_URL="$2"
            shift 2
            ;;
        -i|--install)
            FORCE_INSTALL=true
            shift
            ;;
        -s|--skip-check)
            SKIP_CHECK=true
            shift
            ;;
        -d|--dev)
            MODE="dev"
            shift
            ;;
        --prod)
            MODE="prod"
            shift
            ;;
        --build)
            BUILD_MODE=true
            shift
            ;;
        --clean)
            CLEAN_MODE=true
            shift
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查是否在正确的目录
if [[ ! -d "$FRONTEND_DIR" ]]; then
    log_error "未找到前端目录: $FRONTEND_DIR"
    log_error "请确保在 TaCOS 项目根目录下运行此脚本: ./scripts/start_frontend.sh"
    exit 1
fi

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 进入前端目录
cd "$FRONTEND_DIR"

# 环境检查函数
check_environment() {
    log_info "检查开发环境..."

    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        log_error "请安装 Node.js >= 20.0.0"
        log_error "下载地址: https://nodejs.org/"
        exit 1
    fi

    NODE_VERSION=$(node --version | sed 's/v//')
    REQUIRED_VERSION="20.0.0"

    if ! node -e "process.exit(require('semver').gte('$NODE_VERSION', '$REQUIRED_VERSION') ? 0 : 1)" 2>/dev/null; then
        log_warning "Node.js 版本过低: $NODE_VERSION"
        log_warning "推荐版本: >= $REQUIRED_VERSION"
        log_warning "当前版本可能无法正常运行，建议升级"
    else
        log_success "Node.js 版本检查通过: $NODE_VERSION"
    fi

    # 检查 npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装"
        exit 1
    fi

    NPM_VERSION=$(npm --version)
    log_success "npm 版本: $NPM_VERSION"

    # 检查端口是否被占用
    PORT=${CUSTOM_PORT:-$DEFAULT_PORT}
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "端口 $PORT 已被占用"
        log_warning "请使用 -p 参数指定其他端口，或停止占用该端口的进程"
        if [[ "$MODE" == "dev" ]]; then
            log_info "尝试使用端口 $((PORT + 1))..."
            PORT=$((PORT + 1))
        fi
    fi
}

# 安装依赖函数
install_dependencies() {
    if [[ "$CLEAN_MODE" == true ]]; then
        log_info "清理 node_modules..."
        rm -rf node_modules package-lock.json
        log_success "清理完成"
    fi

    if [[ ! -d "node_modules" ]] || [[ "$FORCE_INSTALL" == true ]] || [[ "$CLEAN_MODE" == true ]]; then
        log_info "安装依赖包..."
        npm install
        log_success "依赖安装完成"
    else
        log_info "依赖已存在，跳过安装"
        log_info "如需重新安装，请使用 -i 或 --clean 参数"
    fi
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."

    BACKEND_URL=${CUSTOM_BACKEND_URL:-$DEFAULT_BACKEND_URL}

    # 创建开发环境 .env.local 文件
    cat > .env.local << EOF
# 此文件由 start_frontend.sh 自动生成，用于开发环境

# API 基础地址
VITE_API_BASE_URL=$BACKEND_URL/api/v1

# 开发模式配置
VITE_DEBUG=true
VITE_DEV_MODE=true

# 应用配置
VITE_APP_TITLE=TaCOS - 清华合唱队在线系统
VITE_APP_VERSION=2.4.0

# 生成时间
VITE_BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

    log_success "开发环境配置完成"
    log_info "API 地址: $BACKEND_URL/api/v1"
}

# 构建生产版本
build_production() {
    log_info "构建生产版本..."

    # 创建本地生产构建配置
    cat > .env.production.local << EOF
VITE_API_BASE_URL=/api/v1
VITE_DEBUG=false
VITE_DEV_MODE=false
VITE_APP_TITLE=TaCOS - 清华合唱队在线系统
VITE_APP_VERSION=2.4.0
VITE_BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

    npm run build
    log_success "生产版本构建完成"
    log_info "构建文件位于: dist/"
}

# 启动开发服务器
start_dev_server() {
    log_info "启动开发服务器..."

    PORT=${CUSTOM_PORT:-$DEFAULT_PORT}

    # 更新 vite.config.js 中的端口配置（如果需要）
    if [[ "$CUSTOM_PORT" != "" ]]; then
        log_info "使用自定义端口: $PORT"
    fi

    log_success "前端开发服务器启动中..."
    log_info "访问地址: http://localhost:$PORT"
    log_info "后端API: ${CUSTOM_BACKEND_URL:-$DEFAULT_BACKEND_URL}/api/v1"
    log_info "按 Ctrl+C 停止服务器"
    echo ""

    # 启动开发服务器
    npm run serve -- --port $PORT
}

# 启动生产预览
start_prod_preview() {
    log_info "启动生产版本预览..."

    if [[ ! -d "dist" ]]; then
        log_warning "未找到构建文件，正在构建..."
        build_production
    fi

    PORT=${CUSTOM_PORT:-$DEFAULT_PORT}

    log_success "生产版本预览启动中..."
    log_info "访问地址: http://localhost:$PORT"
    log_info "按 Ctrl+C 停止服务器"
    echo ""

    npm run preview -- --port $PORT
}

# 主函数
main() {
    echo "=========================================="
    echo "  TaCOS Frontend Startup Script"
    echo "  清华合唱队在线系统 - 前端启动脚本"
    echo "=========================================="
    echo ""

    # 环境检查
    if [[ "$SKIP_CHECK" == false ]]; then
        check_environment
        echo ""
    fi

    # 安装依赖
    install_dependencies
    echo ""

    # 根据模式执行不同操作
    case $MODE in
        "dev")
            if [[ "$BUILD_MODE" == true ]]; then
                build_production
            else
                setup_environment
                start_dev_server
            fi
            ;;
        "prod")
            if [[ "$BUILD_MODE" == true ]]; then
                build_production
            else
                start_prod_preview
            fi
            ;;
        *)
            log_error "未知模式: $MODE"
            exit 1
            ;;
    esac
}

# 信号处理
trap 'echo ""; log_info "正在停止服务器..."; exit 0' INT TERM

# 执行主函数
main "$@"
