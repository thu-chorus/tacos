"""
测试生日称号自动更新功能
"""

from datetime import date
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.authentication.models import User
from apps.personnel.models import Member, MemberTitle, Title
from apps.personnel.tasks import update_birthday_title_for_month


class BirthdayTitlesTestCase(TestCase):
    """测试生日称号功能"""

    def setUp(self):
        """创建测试数据"""
        # 创建"本月寿星"称号
        self.birthday_title = Title.objects.create(
            name="本月寿星",
            description="生日在本月的队员",
            appearance={"bg_color": "#ff6b6b", "text_color": "#ffffff"},
        )

        # 创建其他称号
        self.other_title = Title.objects.create(
            name="优秀队员",
            description="表现优秀的队员",
            appearance={"bg_color": "#4ecdc4", "text_color": "#ffffff"},
        )

        # 创建用户和队员
        current_month = timezone.now().month
        next_month = (current_month % 12) + 1

        # 本月生日的队员
        self.user1 = User.objects.create_user(user_id="2021001", password="test123")
        self.member1 = Member.objects.create(
            user=self.user1, name="张三", birthday=date(2000, current_month, 15)
        )

        self.user2 = User.objects.create_user(user_id="2021002", password="test123")
        self.member2 = Member.objects.create(
            user=self.user2, name="李四", birthday=date(1999, current_month, 25)
        )

        # 下月生日的队员
        self.user3 = User.objects.create_user(user_id="2021003", password="test123")
        self.member3 = Member.objects.create(
            user=self.user3, name="王五", birthday=date(2001, next_month, 10)
        )

        # 没有生日信息的队员
        self.user4 = User.objects.create_user(user_id="2021004", password="test123")
        self.member4 = Member.objects.create(
            user=self.user4, name="赵六", birthday=None
        )

    def test_update_current_month_birthday_titles(self):
        """测试更新本月生日称号"""
        current_month = timezone.now().month

        # 执行更新
        update_birthday_title_for_month(current_month, "本月寿星")

        # 检查结果
        birthday_members = MemberTitle.objects.filter(title=self.birthday_title)
        self.assertEqual(birthday_members.count(), 2)

        member_ids = set(mt.member.user.user_id for mt in birthday_members)
        self.assertIn("2021001", member_ids)
        self.assertIn("2021002", member_ids)
        self.assertNotIn("2021003", member_ids)
        self.assertNotIn("2021004", member_ids)

    def test_clear_existing_titles_before_update(self):
        """测试更新前清空现有称号授予"""
        current_month = timezone.now().month

        # 先给一些队员授予"本月寿星"称号
        MemberTitle.objects.create(
            member=self.member3,  # 下月生日的队员
            title=self.birthday_title,
            awarded_at=timezone.localdate(),
        )
        MemberTitle.objects.create(
            member=self.member4,  # 没有生日的队员
            title=self.birthday_title,
            awarded_at=timezone.localdate(),
        )

        # 确认有2个现有的授予
        self.assertEqual(
            MemberTitle.objects.filter(title=self.birthday_title).count(), 2
        )

        # 执行更新
        update_birthday_title_for_month(current_month, "本月寿星")

        # 检查结果：应该只有本月生日的队员有称号
        birthday_members = MemberTitle.objects.filter(title=self.birthday_title)
        self.assertEqual(birthday_members.count(), 2)

        member_ids = set(mt.member.user.user_id for mt in birthday_members)
        self.assertIn("2021001", member_ids)
        self.assertIn("2021002", member_ids)

    def test_management_command(self):
        """测试管理命令"""
        current_month = timezone.now().month

        # 捕获命令输出
        out = StringIO()
        call_command(
            "update_birthday_titles",
            title_name="本月寿星",
            month=current_month,
            stdout=out,
        )

        # 检查输出
        output = out.getvalue()
        self.assertIn("找到 2 名", output)
        self.assertIn("成功为 2 名队员授予", output)

        # 检查数据库
        birthday_members = MemberTitle.objects.filter(title=self.birthday_title)
        self.assertEqual(birthday_members.count(), 2)

    def test_management_command_dry_run(self):
        """测试管理命令的试运行模式"""
        current_month = timezone.now().month

        # 先给一些队员授予称号
        MemberTitle.objects.create(
            member=self.member1,
            title=self.birthday_title,
            awarded_at=timezone.localdate(),
        )

        # 执行试运行
        out = StringIO()
        call_command(
            "update_birthday_titles",
            title_name="本月寿星",
            month=current_month,
            dry_run=True,
            stdout=out,
        )

        # 检查输出
        output = out.getvalue()
        self.assertIn("[试运行]", output)

        # 数据库应该没有变化
        self.assertEqual(
            MemberTitle.objects.filter(title=self.birthday_title).count(), 1
        )

    def test_nonexistent_title(self):
        """测试不存在的称号"""
        current_month = timezone.now().month

        with self.assertRaises(Exception):
            update_birthday_title_for_month(current_month, "不存在的称号")

    def test_invalid_month(self):
        """测试无效的月份"""
        with self.assertRaises(ValueError):
            update_birthday_title_for_month(13, "本月寿星")

        with self.assertRaises(ValueError):
            update_birthday_title_for_month(0, "本月寿星")

    def test_no_birthday_members(self):
        """测试没有生日队员的月份"""
        # 选择一个没有队员生日的月份
        current_month = timezone.now().month
        empty_month = (current_month + 6) % 12 + 1  # 半年后的月份

        # 执行更新
        update_birthday_title_for_month(empty_month, "本月寿星")

        # 应该没有队员被授予称号
        birthday_members = MemberTitle.objects.filter(title=self.birthday_title)
        self.assertEqual(birthday_members.count(), 0)

    def test_preserve_other_titles(self):
        """测试更新生日称号时不影响其他称号"""
        current_month = timezone.now().month

        # 给队员授予其他称号
        MemberTitle.objects.create(
            member=self.member1, title=self.other_title, awarded_at=timezone.localdate()
        )
        MemberTitle.objects.create(
            member=self.member2, title=self.other_title, awarded_at=timezone.localdate()
        )

        # 执行生日称号更新
        update_birthday_title_for_month(current_month, "本月寿星")

        # 检查其他称号没有被影响
        other_title_members = MemberTitle.objects.filter(title=self.other_title)
        self.assertEqual(other_title_members.count(), 2)

        # 检查生日称号正确授予
        birthday_members = MemberTitle.objects.filter(title=self.birthday_title)
        self.assertEqual(birthday_members.count(), 2)
