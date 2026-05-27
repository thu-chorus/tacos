#!/bin/bash

# 清华合唱队在线系统后端启动脚本
#
# 此脚本处理TaCOS后端服务器的完整设置和启动

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/tacos_backend"
VENV_DIR=".venv"
PYTHON_VERSION="python3"
DJANGO_SETTINGS_MODULE="config.settings.development"
SERVER_HOST="0.0.0.0"
SERVER_PORT="8000"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION="python3"
    elif command_exists python; then
        PYTHON_VERSION="python"
    else
        print_error "Python is not installed. Please install Python 3.9+ first."
        exit 1
    fi

    PYTHON_VER=$($PYTHON_VERSION --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    REQUIRED_VER="3.9"

    if [ "$(printf '%s\n' "$REQUIRED_VER" "$PYTHON_VER" | sort -V | head -n1)" != "$REQUIRED_VER" ]; then
        print_error "Python version $PYTHON_VER is too old. Please install Python 3.9+ first."
        exit 1
    fi

    print_success "Python version check passed: $($PYTHON_VERSION --version)"
}

setup_venv() {
    print_status "Setting up virtual environment..."

    cd "$BACKEND_DIR"

    if [ ! -d "$VENV_DIR" ]; then
        print_status "Creating virtual environment..."
        $PYTHON_VERSION -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi

    print_status "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    print_status "Upgrading pip..."
    pip install --upgrade pip

    print_success "Virtual environment setup complete"
}

install_dependencies() {
    print_status "Installing Python dependencies..."

    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found in $BACKEND_DIR"
        exit 1
    fi

    pip install -r requirements.txt
    print_success "Dependencies installed successfully"
}

setup_environment() {
    print_status "Setting up environment variables..."

    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
# 清华合唱队在线系统后端环境配置

# Django 配置
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=true
DJANGO_SETTINGS_MODULE=config.settings.development

# 数据库配置
# DATABASE_URL=sqlite:///db.sqlite3

# 主机与浏览器来源
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# JWT 令牌有效期
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7

# PDF 水印字体（可选）
# WATERMARK_FONT_PATH=/System/Library/Fonts/PingFang.ttc

# Django 允许访问的主机
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
EOF
        print_success ".env file created with default values"
        print_warning "Please review and update the .env file as needed"
    else
        print_status ".env file already exists"
    fi
}

create_database() {
    print_status "Checking database file..."

    if [ ! -f "db.sqlite3" ]; then
        print_status "Creating SQLite database file..."
        touch db.sqlite3
        print_success "Database file created: db.sqlite3"
    else
        print_status "Database file already exists: db.sqlite3"
    fi
}

run_migrations() {
    print_status "Running database migrations..."

    export DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE"

    print_status "Creating migrations..."
    python manage.py makemigrations

    print_status "Applying migrations..."
    MIGRATE_ARGS=""
    if [ -f "db.sqlite3" ]; then
        print_status "Existing database detected, using --fake-initial to reconcile initial migrations"
        MIGRATE_ARGS="--fake-initial"
    fi
    python manage.py migrate $MIGRATE_ARGS

    print_success "Database migrations completed"
}

create_superuser() {
    print_status "Checking for superuser..."

    if python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('Superuser exists:', User.objects.filter(is_superuser=True).exists())" | grep -q "True"; then
        print_status "Superuser already exists"
    else
        print_warning "No superuser found. You can create one later with:"
        print_warning "python manage.py createsuperuser"
    fi
}

setup_cron_jobs() {
    print_status "Setting up cron jobs for birthday titles..."

    python manage.py crontab add

    print_success "Cron jobs installed successfully"
    print_status "Birthday titles will be updated automatically on the 1st of each month at 2:00 AM"
}

collect_static() {
    print_status "Collecting static files..."
    python manage.py collectstatic --noinput
    print_success "Static files collected"
}

health_check() {
    print_status "Running health check..."

    sleep 2

    if curl -s -f "http://localhost:$SERVER_PORT/api/v1/common/health/" > /dev/null; then
        print_success "Health check passed - server is running correctly"
    else
        print_warning "Health check failed - server may not be fully ready yet"
    fi
}

start_server() {
    print_status "Starting Django development server..."
    print_status "Server will be available at: http://localhost:$SERVER_PORT"
    print_status "API base URL: http://localhost:$SERVER_PORT/api/v1"
    print_status "Admin interface: http://localhost:$SERVER_PORT/admin/"
    print_status ""
    print_status "Press Ctrl+C to stop the server"
    print_status "=========================================="

    export DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE"

    python manage.py runserver "$SERVER_HOST:$SERVER_PORT"
}

start_celery_worker() {
    print_status "Starting Celery worker..."
    print_status "Press Ctrl+C to stop the worker"
    print_status "=========================================="

    export DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE"

    celery -A config worker -l info
}

start_celery_beat() {
    print_status "Starting Celery beat (periodic task scheduler)..."
    print_status "Press Ctrl+C to stop the scheduler"
    print_status "=========================================="

    export DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE"

    celery -A config beat -l info
}

check_redis() {
    print_status "Checking Redis connection..."
    if command_exists redis-cli; then
        if redis-cli ping >/dev/null 2>&1; then
            print_success "Redis is running"
            return 0
        else
            print_warning "Redis is not running. Please start Redis:"
            print_warning "  macOS: brew services start redis"
            print_warning "  Linux: sudo systemctl start redis"
            return 1
        fi
    else
        print_warning "redis-cli not found. Cannot check Redis status."
        print_warning "Please ensure Redis is installed and running."
        return 1
    fi
}

show_usage() {
    echo "TaCOS Backend Server Startup Script"
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --setup-only    Only setup environment, don't start server"
    echo "  --skip-setup    Skip setup, start server directly"
    echo "  --celery        Start Celery worker instead of Django server"
    echo "  --celery-beat   Start Celery beat scheduler instead of Django server"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0
    echo "  $0 --setup-only
    echo "  $0 --skip-setup
    echo "  $0 --celery
    echo "  $0 --celery-beat
    echo ""
    echo "For development with async tasks, run in separate terminals:"
    echo "  Terminal 1: $0
    echo "  Terminal 2: $0 --celery
    echo "  Terminal 3: $0 --celery-beat
    echo ""
    echo "Note: Redis must be running for Celery to work properly."
}

main() {
    echo "=========================================="
    echo "TaCOS Backend Server Startup Script"
    echo "清华合唱队在线系统后端启动脚本"
    echo "=========================================="

    SETUP_ONLY=false
    SKIP_SETUP=false
    START_CELERY=false
    START_CELERY_BEAT=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --setup-only)
                SETUP_ONLY=true
                shift
                ;;
            --skip-setup)
                SKIP_SETUP=true
                shift
                ;;
            --celery)
                START_CELERY=true
                shift
                ;;
            --celery-beat)
                START_CELERY_BEAT=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    if [ ! -d "$BACKEND_DIR" ]; then
        print_error "Backend directory '$BACKEND_DIR' not found."
        print_error "Please run this script from the TaCOS project root: ./scripts/start_backend.sh"
        exit 1
    fi

    # 切换到项目根目录
    cd "$PROJECT_ROOT"

    if [ "$SKIP_SETUP" = false ]; then
        print_status "Starting setup phase..."

        check_python_version
        setup_venv
        install_dependencies
        setup_environment
        create_database
        run_migrations
        create_superuser
        setup_cron_jobs
        collect_static

        if [ "$START_CELERY" = true ] || [ "$START_CELERY_BEAT" = true ]; then
            check_redis
        fi

        print_success "Setup phase completed successfully!"
        echo ""
    fi

    if [ "$SETUP_ONLY" = true ]; then
        print_success "Setup completed. You can now start the server with: $0 --skip-setup"
        exit 0
    fi

    if [ "$START_CELERY" = true ]; then
        print_status "Starting Celery worker..."
        check_redis
        start_celery_worker
    elif [ "$START_CELERY_BEAT" = true ]; then
        print_status "Starting Celery beat scheduler..."
        check_redis
        start_celery_beat
    else
        print_status "Starting Django development server..."
        start_server
    fi
}

trap 'echo ""; print_status "Server stopped by user"; exit 0' INT

main "$@"
