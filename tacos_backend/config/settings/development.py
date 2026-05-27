from .base import *  # noqa

DEBUG = True

# SQLite 已由 base 配置

# 开发环境允许本地主机访问
ALLOWED_HOSTS = ALLOWED_HOSTS + ["localhost", "127.0.0.1"]
