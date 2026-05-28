from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TypeVar

from apps.common.sorting import pinyin_text_key

_T = TypeVar("_T")


def sheet_sort_key(sheet: Any) -> tuple[str, str, str, str]:
    """乐谱列表统一按曲名拼音、作曲、编曲、公开 ID 排序。"""
    return (
        pinyin_text_key(getattr(sheet, "title", "")),
        pinyin_text_key(getattr(sheet, "composer", "")),
        pinyin_text_key(getattr(sheet, "arranger", "")),
        str(getattr(sheet, "public_id", "") or getattr(sheet, "id", "") or ""),
    )


def sort_sheets(sheets: Iterable[_T]) -> list[_T]:
    return sorted(list(sheets), key=sheet_sort_key)
