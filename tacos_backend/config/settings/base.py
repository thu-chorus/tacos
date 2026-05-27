import os
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "change-me"),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1", "0.0.0.0"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000", "http://127.0.0.1:3000"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    ACCESS_TOKEN_LIFETIME_MINUTES=(int, 1440),  # 默认1天（1440分钟）
    REFRESH_TOKEN_LIFETIME_DAYS=(int, 10),  # 默认10天
    WATERMARK_FONT_PATH=(str, ""),  # PDF 水印可选中文字体路径
)

# 读取 .env 文件（主要用于开发环境）
# 生产环境会在 production.py 中单独读取 .env.production.local
env_file = BASE_DIR / ".env"
if (
    env_file.exists()
    and not os.environ.get("DJANGO_READ_DOTENV", "").lower() == "false"
):
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])  # type: ignore

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "django_crontab",
    "django_celery_results",
    # 'drf_spectacular',  # 需要时再启用
    "apps.common",
    "apps.authentication",
    "apps.personnel",
    "apps.sheet_music",
    "apps.events",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# TEMPLATES 配置用于指定 Django 模板引擎相关设置。
# 主要作用：告诉 Django 如何查找和渲染 HTML 模板（例如后台管理、前端渲染页面等）。
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",  # 指定模板引擎
        "DIRS": [BASE_DIR / "templates"],  # 项目模板目录，一般用于存放通用页面模板
        "APP_DIRS": True,  # 启用自动查找各 app 下的 templates 目录
        "OPTIONS": {
            "context_processors": [  # 模板上下文处理器，自动传递常用变量
                "django.template.context_processors.debug",  # 调试相关上下文变量
                "django.template.context_processors.request",  # request对象
                "django.contrib.auth.context_processors.auth",  # 用户认证相关变量
                "django.contrib.messages.context_processors.messages",  # 消息提示
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "authentication.User"

AUTHENTICATION_BACKENDS = [
    "apps.authentication.utils.UserIdBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# 优先使用 bcrypt 哈希器
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
# 将媒体文件移出 static，避免静态服务直接公开访问
MEDIA_URL = "/media/"  # 仅用于构造 URL，不直接托管
MEDIA_ROOT = BASE_DIR.parent / "tacos_media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 默认初始密码
DEFAULT_INITIAL_PASSWORD = "ChangeMe123!"

# 定时任务配置
CRONJOBS = [
    # 每月1号凌晨2点更新本月寿星称号
    (
        "0 2 1 * *",
        "apps.personnel.tasks.update_monthly_birthday_title",
        ">> /tmp/tacos_cron.log 2>&1",
    ),
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsSetPagination",
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])  # type: ignore
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("ACCESS_TOKEN_LIFETIME_MINUTES", default=1440)  # 默认1天
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.int("REFRESH_TOKEN_LIFETIME_DAYS", default=10)  # 默认10天
    ),
    # 滑动刷新：每次使用 refresh token 刷新时，生成新的 refresh token
    # 这样只要用户在10天内有活动，登录状态就会一直延续
    "ROTATE_REFRESH_TOKENS": True,
    # 刷新后旧的 refresh token 立即失效（需要配合 token blacklist，但这里简化处理）
    "BLACKLIST_AFTER_ROTATION": False,
    # 更新用户最后登录时间
    "UPDATE_LAST_LOGIN": True,
}

# 可选：设置系统中文字体路径用于渲染水印
WATERMARK_FONT_PATH = env("WATERMARK_FONT_PATH") or None

# ==================== Celery 配置 ====================
# 异步任务处理配置
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TIME_LIMIT = 300  # 5 分钟硬限制
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 分钟软限制
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_RESULT_EXTENDED = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True  # 启动时重试消息队列连接
