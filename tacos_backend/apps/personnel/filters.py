from django.db.models import Q

import django_filters

from .models import Instructor, Member


class MemberFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    # 支持学号模糊查询（user.user_id）
    user_id = django_filters.CharFilter(
        field_name="user__user_id", lookup_expr="icontains"
    )
    # 支持生日月份查询（1-12）
    birthday_month = django_filters.NumberFilter(method="filter_birthday_month")
    # 院系：支持 icontains；并兼容“其他 + department_other”
    department = django_filters.CharFilter(method="filter_department")
    department__icontains = django_filters.CharFilter(method="filter_department")

    class Meta:
        model = Member
        fields = {
            "voice_part": ["exact"],
            "tier": ["exact"],
            "status": ["exact"],
            "join_month": ["exact", "icontains"],
            "graduate_month": ["exact", "icontains"],
            "name": ["exact", "icontains"],
            "department": ["exact", "icontains"],
        }

    def filter_search(self, queryset, name, value):  # type: ignore[override]
        return queryset.filter(
            Q(name__icontains=value) | Q(user__user_id__icontains=value)
        )

    def filter_birthday_month(self, queryset, name, value):  # type: ignore[override]
        """按生日月份筛选成员（1-12）。"""
        if value and 1 <= value <= 12:
            return queryset.filter(birthday__month=value)
        return queryset

    def filter_department(self, queryset, name, value):  # type: ignore[override]
        """由于院系导入字段有奇怪的格式问题，需要专门写一个更鲁棒的院系筛选函数
        支持院系过滤：
        - 普通院系：匹配 department exact/icontains
        - 当 value 为“其他”或包含“其他”时，匹配 Q(department='其他') | Q(department_other__icontains=value_without_prefix)
        - 当使用参数 `department` 时，执行院系代码+院系名称匹配；
        - 当使用参数 `department__icontains` 时，执行院系名称模糊匹配并保留“其他”兼容逻辑。
        """
        if not value:
            return queryset
        s = str(value).strip()

        # 模糊匹配及兼容逻辑：department__icontains
        parts = s.split(" ", 1)
        code = parts[0] if len(parts) > 1 and parts[0].isdigit() else ""
        name_part = parts[1] if len(parts) > 1 and parts[0].isdigit() else s

        conditions = Q(department__icontains=s)
        # 额外按名称部分匹配（去掉代码）
        if name == "department":
            # 严格匹配
            conditions = Q(department__icontains=code) & Q(
                department__icontains=name_part
            )
        elif name_part and name_part != s:
            # 模糊匹配
            conditions = conditions | Q(department__icontains=name_part)

        # 处理“其他”逻辑
        if "其他" in s:
            # 当只选择“其他”，匹配 department='其他'
            conditions = conditions | Q(department="其他")
            # 若包含额外名称，则同时匹配 department_other
            extra = name_part if name_part and name_part != s else ""
            if extra:
                conditions = conditions | Q(department_other__icontains=extra)

        return queryset.filter(conditions)


class InstructorFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Instructor
        fields = {
            "name": ["exact", "icontains"],
            "is_external": ["exact"],
        }

    def filter_search(self, queryset, name, value):  # type: ignore[override]
        return queryset.filter(name__icontains=value)
