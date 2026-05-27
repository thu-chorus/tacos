#!/usr/bin/env python3
"""
Django 管理命令入口。

默认使用开发环境配置，可通过 DJANGO_SETTINGS_MODULE 覆盖。
"""
import os
import sys


def main() -> None:
    """使用当前环境配置运行管理命令。"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable? Did you forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
