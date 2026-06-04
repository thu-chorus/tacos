#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${TACOS_PROJECT_DIR:-/var/www/tacos}"
DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"
SKIP_GIT_SYNC=0

for arg in "$@"; do
    case "$arg" in
        --skip-git-sync)
            SKIP_GIT_SYNC=1
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            exit 2
            ;;
    esac
done

log() {
    printf '[deploy] %s\n' "$1"
}

run() {
    log "$*"
    "$@"
}

if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "Project directory is not a git repository: $PROJECT_DIR" >&2
    exit 1
fi

cd "$PROJECT_DIR"

if [ "$SKIP_GIT_SYNC" -eq 0 ]; then
    run git fetch origin main
    run git reset --hard origin/main
fi

BACKEND_DIR="$PROJECT_DIR/tacos_backend"
FRONTEND_DIR="$PROJECT_DIR/tacos_frontend"

if [ ! -x "$BACKEND_DIR/.venv/bin/python" ]; then
    run python3 -m venv "$BACKEND_DIR/.venv"
fi

run "$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt"

cd "$BACKEND_DIR"
run "$BACKEND_DIR/.venv/bin/python" manage.py migrate --noinput --settings="$DJANGO_SETTINGS_MODULE"
run "$BACKEND_DIR/.venv/bin/python" manage.py collectstatic --noinput --settings="$DJANGO_SETTINGS_MODULE"

cd "$FRONTEND_DIR"
run npm ci
run npm run build

run systemctl restart tacos
run systemctl restart tacos-celery-worker
run systemctl restart tacos-celery-beat
run systemctl reload nginx

run systemctl is-active tacos
run systemctl is-active tacos-celery-worker
run systemctl is-active tacos-celery-beat
run systemctl is-active nginx

log "Production deploy completed."
