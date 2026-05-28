from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TypeVar

from apps.common.sorting import pinyin_text_key

from .models import MemberStatus

_T = TypeVar("_T")

STATUS_RANK = {
    MemberStatus.ACTIVE: 0,
    MemberStatus.ALUMNI: 1,
    MemberStatus.INACTIVE: 2,
}
TIER_RANK = {"一队": 0, "二队": 1}
VOICE_PART_RANK = {
    "S1": 0,
    "S2": 1,
    "A1": 2,
    "A2": 3,
    "T1": 4,
    "T2": 5,
    "B1": 6,
    "B2": 7,
    "Other": 8,
}


def member_sort_key(member: Any) -> tuple[int, int, int, str, str]:
    """成员列表统一排序：状态、梯队、声部、姓名拼音、学号。"""
    user = getattr(member, "user", None)
    return (
        STATUS_RANK.get(getattr(member, "status", ""), 99),
        TIER_RANK.get(getattr(member, "tier", ""), 99),
        VOICE_PART_RANK.get(getattr(member, "voice_part", ""), 99),
        pinyin_text_key(getattr(member, "name", "")),
        str(getattr(user, "user_id", "") or ""),
    )


def sort_members(members: Iterable[_T]) -> list[_T]:
    return sorted(list(members), key=member_sort_key)


def instructor_sort_key(instructor: Any) -> tuple[str, str]:
    """教师列表统一按姓名拼音、教师 ID 排序。"""
    return (
        pinyin_text_key(getattr(instructor, "name", "")),
        str(getattr(instructor, "instructor_id", "") or ""),
    )


def sort_instructors(instructors: Iterable[_T]) -> list[_T]:
    return sorted(list(instructors), key=instructor_sort_key)
