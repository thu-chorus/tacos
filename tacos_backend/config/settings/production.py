import os
from pathlib import Path

import environ

# 导入 base 设置
from .base import *  # noqa

# 重新初始化 environ，专门为生产环境读取 .env.production.local
BASE_DIR = Path(__file__).resolve().parents[2]

# 生产环境配置：直接读取 .env.production.local 文件
production_env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "change-me"),
    ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    ACCESS_TOKEN_LIFETIME_MINUTES=(int, 1440),  # 默认1天（1440分钟）
    REFRESH_TOKEN_LIFETIME_DAYS=(int, 10),  # 默认10天
    WATERMARK_FONT_PATH=(str, ""),
)

# 读取生产环境配置文件
env_file = BASE_DIR / ".env.production.local"
if env_file.exists():
    environ.Env.read_env(str(env_file))
else:
    # 如果文件不存在，发出警告
    import warnings

    warnings.warn(
        f"Production environment file not found: {env_file}\n"
        "Please create .env.production.local based on .env.production.example",
        RuntimeWarning,
    )

DEBUG = False

# 生产环境安全加固
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True

# 数据库配置：优先使用 django-environ 提供的 DATABASE_URL
if production_env("DATABASE_URL", default=None):
    DATABASES = {
        "default": production_env.db(),
    }

# CORS 和主机名配置来自 base 中的环境变量
