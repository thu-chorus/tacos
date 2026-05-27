import re
from typing import Optional

from django.core.exceptions import ValidationError

PHONE_REGEX = re.compile(r"^1\d{10}$")


def validate_china_mainland_phone(phone: Optional[str]) -> None:
    # 允许为空；仅在有值时校验格式
    if not phone:
        return
    if not PHONE_REGEX.match(phone):
        raise ValidationError("手机号格式不正确，应为中国大陆11位手机号。")


def validate_pdf_file_extension(filename: str) -> None:
    if not filename.lower().endswith(".pdf"):
        raise ValidationError("仅支持 PDF 文件。")


def validate_email_format(email: Optional[str]) -> None:
    if not email:
        return
    if "@" not in email:
        raise ValidationError("邮箱格式不正确。")


YEAR_MONTH_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def validate_year_month(value: Optional[str]) -> None:
    """校验 YYYY-MM 年月格式，允许空值。"""
    if not value:
        return
    if not isinstance(value, str):
        raise ValidationError("入队年月格式应为 YYYY-MM。")
    if not YEAR_MONTH_REGEX.match(value):
        raise ValidationError("入队年月格式应为 YYYY-MM。")
