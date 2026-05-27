import hashlib
import hmac
import os
import secrets
import string
import time
from typing import Any, Dict, Optional

from django.conf import settings


def envelope_ok(
    data: Optional[Dict[str, Any]] = None, message: str = "success"
) -> Dict[str, Any]:
    if data is None:
        data = {}
    return {"code": 200, "message": message, "data": data}


def envelope_error(
    code: int, message: str, data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if data is None:
        data = {}
    return {"code": code, "message": message, "data": data}


# ============
# ============

_PUBLIC_ID_ALPHABET = string.ascii_lowercase + string.digits


def generate_public_id(prefix: str = "", length: int = 12) -> str:
    """生成固定长度且 URL 安全的随机 public_id。

    - 使用小写字母和数字，便于阅读和放入 URL
    - 可提供单字符前缀区分类型，例如 m、e、s
    - 默认长度包含前缀长度
    """
    if not isinstance(prefix, str):
        prefix = ""
    prefix = prefix[:1]
    n = max(1, int(length) - len(prefix))
    body = "".join(secrets.choice(_PUBLIC_ID_ALPHABET) for _ in range(n))
    return f"{prefix}{body}"


def ensure_unique_public_id(
    model_cls, field: str = "public_id", prefix: str = "", length: int = 12
) -> str:
    """为指定模型生成唯一 public_id。

    会重复生成新 ID，直到数据库中不存在冲突。
    """
    for _ in range(50):
        candidate = generate_public_id(prefix=prefix, length=length)
        exists = model_cls.objects.filter(**{field: candidate}).exists()  # type: ignore[attr-defined]
        if not exists:
            return candidate
    return ensure_unique_public_id(
        model_cls, field=field, prefix=prefix, length=length + 2
    )


# =========================
# =========================


def _sign_payload(payload: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def generate_signed_token(
    path: str, expires_in_seconds: int = 300, subject: Optional[str] = None
) -> str:
    """为文件路径生成短期有效的签名令牌。

    带主体绑定的令牌格式为 "exp:sub:signature"。

    subject 应为已登录用户的稳定标识，例如 user_id。
    """
    exp = int(time.time()) + int(expires_in_seconds)
    sub = (subject or "").strip()
    secret = getattr(settings, "SECRET_KEY", "change-me")
    if not sub:
        sub = "anonymous"
    base = f"{path}:{exp}:{sub}"
    sig = _sign_payload(base, secret)
    return f"{exp}:{sub}:{sig}"


def verify_signed_token(path: str, token: str) -> bool:
    """校验 generate_signed_token 生成的签名令牌。

    仅接受绑定 subject 的未过期令牌（exp:sub:sig）。
    """
    try:
        parts = str(token or "").split(":", 2)
        if len(parts) != 3:
            return False
        exp_str, sub, sig = parts
        exp = int(exp_str)
        sub = (sub or "").strip()
        if not sub:
            return False
    except Exception:
        return False
    if exp < int(time.time()):
        return False
    secret = getattr(settings, "SECRET_KEY", "change-me")
    expected = _sign_payload(f"{path}:{exp}:{sub}", secret)
    return hmac.compare_digest(expected, sig)
