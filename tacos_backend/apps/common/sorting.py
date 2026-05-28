from __future__ import annotations


def pinyin_text_key(value: object) -> str:
    """将中文文本转换为适合排序的拼音键。"""
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        from pypinyin import Style, lazy_pinyin  # type: ignore

        return "".join(lazy_pinyin(text, style=Style.NORMAL, errors="default")).lower()
    except Exception:
        return text.lower()
