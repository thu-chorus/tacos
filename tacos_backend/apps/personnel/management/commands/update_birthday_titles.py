"""
管理命令：更新本月寿星称号
自动清空"本月寿星"称号的现有授予，并根据生日月份重新授予给对应的队员。
"""

import logging
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.personnel.models import Member, MemberTitle, Title

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "更新本月寿星称号，清空现有授予并重新分配给本月生日的队员"

    def add_arguments(self, parser):
        parser.add_argument(
            "--title-name",
            type=str,
            default="本月寿星",
            help="称号名称（默认：本月寿星）",
        )
        parser.add_argument(
            "--month", type=int, help="指定月份（1-12），不指定则使用当前月份"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="试运行模式，不实际修改数据"
        )

    def handle(self, *args, **options):
        title_name = options["title_name"]
        target_month = options.get("month")
        dry_run = options["dry_run"]

        if target_month is None:
            target_month = timezone.localdate().month

        if not (1 <= target_month <= 12):
            raise CommandError("月份必须在1-12之间")

        self.stdout.write(f"开始更新称号 '{title_name}' 的授予情况...")
        self.stdout.write(f"目标月份: {target_month}月")

        if dry_run:
            self.stdout.write(self.style.WARNING("**试运行模式，不会实际修改数据**"))

        try:
            # 查找称号（支持包含匹配）
            matching_titles = Title.objects.filter(name__icontains=title_name)

            if not matching_titles.exists():
                raise CommandError(f"未找到包含 '{title_name}' 的称号")

            # 优先选择完全匹配的称号，否则选择第一个匹配的
            title = None
            for t in matching_titles:
                if t.name == title_name:
                    title = t
                    break

            if title is None:
                title = matching_titles.first()

            self.stdout.write(f"找到称号: {title.name} (ID: {title.id})")

            # 如果有多个匹配，显示所有匹配的称号
            if matching_titles.count() > 1:
                self.stdout.write(
                    self.style.WARNING(
                        f"找到 {matching_titles.count()} 个包含 '{title_name}' 的称号，使用: {title.name}"
                    )
                )
                for t in matching_titles:
                    self.stdout.write(f"  - {t.name} (ID: {t.id})")

            # 查找本月生日的队员
            birthday_members = Member.objects.filter(
                birthday__month=target_month, birthday__isnull=False
            ).select_related("user")

            member_count = birthday_members.count()
            self.stdout.write(f"找到 {member_count} 名 {target_month}月 生日的队员")

            if member_count == 0:
                self.stdout.write(
                    self.style.WARNING(f"没有找到 {target_month}月 生日的队员")
                )

            # 显示详细信息
            for member in birthday_members:
                user_id = getattr(member.user, "user_id", "N/A")
                birthday_str = (
                    member.birthday.strftime("%m-%d") if member.birthday else "N/A"
                )
                self.stdout.write(f"  - {user_id} {member.name} (生日: {birthday_str})")

            if not dry_run:
                with transaction.atomic():
                    # 清空现有的称号授予
                    existing_count = MemberTitle.objects.filter(title=title).count()
                    if existing_count > 0:
                        MemberTitle.objects.filter(title=title).delete()
                        self.stdout.write(f"已清空 {existing_count} 个现有的称号授予")
                    else:
                        self.stdout.write("没有现有的称号授予需要清空")

                    # 为本月生日的队员授予称号
                    new_titles = []
                    today = timezone.localdate()

                    for member in birthday_members:
                        new_titles.append(
                            MemberTitle(member=member, title=title, awarded_at=today)
                        )

                    if new_titles:
                        MemberTitle.objects.bulk_create(new_titles)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"成功为 {len(new_titles)} 名队员授予 '{title_name}' 称号"
                            )
                        )
                    else:
                        self.stdout.write("没有队员需要授予称号")
            else:
                # 试运行模式的输出
                existing_count = MemberTitle.objects.filter(title=title).count()
                self.stdout.write(f"[试运行] 将清空 {existing_count} 个现有的称号授予")
                self.stdout.write(f"[试运行] 将为 {member_count} 名队员授予称号")

            self.stdout.write(self.style.SUCCESS("操作完成"))

        except Exception as e:
            logger.error(f"更新本月寿星称号时发生错误: {e}")
            raise CommandError(f"操作失败: {e}")
