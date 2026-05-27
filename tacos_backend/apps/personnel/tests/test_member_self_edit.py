"""
测试 MemberViewSet 的成员自助编辑权限。
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient

from apps.personnel.models import Member, MemberStatus

User = get_user_model()


class MemberSelfEditPermissionTest(TestCase):
    """验证成员只能编辑自己的资料。"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            user_id="2021000001",
            password="password123",
            name="Member One",
            role="Member",
        )
        self.user2 = User.objects.create_user(
            user_id="2021000002",
            password="password123",
            name="Member Two",
            role="Member",
        )
        self.admin_user = User.objects.create_user(
            user_id="2021999999",
            password="adminpass",
            name="Admin User",
            role="Admin",
            is_staff=True,
        )

        self.member1 = Member.objects.create(
            user=self.user1,
            name="Member One",
            gender="男",
            voice_part="T1",
            department="计算机系",
            class_name="计01",
            phone_number="13800000001",
            email="member1@example.com",
            dorm="紫荆1#101",
            birthday="2000-01-01",
            hometown="北京 北京",
            ethnicity="汉族",
            political_status="团员",
            political_affiliation="计算机系团委",
            tier="一队",
            join_month="2021-09",
            graduate_month="2025-06",
        )
        self.member2 = Member.objects.create(
            user=self.user2,
            name="Member Two",
            gender="女",
            voice_part="S1",
            department="电子系",
            class_name="电01",
            phone_number="13800000002",
            email="member2@example.com",
            dorm="紫荆2#202",
            birthday="2000-02-02",
            hometown="上海 上海",
            ethnicity="汉族",
            political_status="团员",
            political_affiliation="电子系团委",
            tier="二队",
            join_month="2021-09",
            graduate_month="2025-06",
        )
        self.admin_member = Member.objects.create(
            user=self.admin_user,
            name="Admin User",
            gender="男",
            voice_part="B1",
            department="数学系",
            class_name="数01",
            phone_number="13899999999",
            email="admin@example.com",
            dorm="紫荆9#999",
            birthday="1999-09-09",
            hometown="广东 深圳",
            ethnicity="汉族",
            political_status="党员",
            political_affiliation="数学系党委",
            tier="一队",
            join_month="2019-09",
            graduate_month="2023-06",
        )

        self.client = APIClient()

    def _full_update_payload(self, member):
        birthday = member.birthday
        if birthday and hasattr(birthday, "isoformat"):
            birthday = birthday.isoformat()
        return {
            "name": member.name,
            "gender": member.gender,
            "voice_part": member.voice_part,
            "department": member.department,
            "department_other": member.department_other,
            "class_name": member.class_name,
            "wechat_id": member.wechat_id,
            "phone_number": member.phone_number,
            "email": member.email,
            "dorm": member.dorm,
            "birthday": birthday,
            "hometown": member.hometown,
            "ethnicity": member.ethnicity,
            "political_status": member.political_status,
            "political_affiliation": member.political_affiliation,
            "is_specialty": member.is_specialty,
            "is_centralized": member.is_centralized,
            "position": member.position,
            "join_month": member.join_month,
            "graduate_month": member.graduate_month,
            "tier": member.tier,
            "portfolio": member.portfolio,
        }

    def test_member_can_update_own_profile(self):
        """成员可以更新自己的资料。"""
        self.client.force_authenticate(user=self.user1)
        url = f"/api/v1/members/{self.member1.public_id}/"
        data = {"name": "Updated Name", "dorm": "紫荆1#999"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.member1.refresh_from_db()
        self.assertEqual(self.member1.name, "Updated Name")
        self.assertEqual(self.member1.dorm, "紫荆1#999")

    def test_member_can_put_own_profile_without_status(self):
        """完整更新未携带 status 时不应触发管理员状态校验。"""
        self.client.force_authenticate(user=self.user1)
        url = f"/api/v1/members/{self.member1.public_id}/"
        data = self._full_update_payload(self.member1)
        data["dorm"] = "紫荆1#888"

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, 200, response.json())
        self.member1.refresh_from_db()
        self.assertEqual(self.member1.dorm, "紫荆1#888")
        self.assertEqual(self.member1.status, MemberStatus.ACTIVE)

    def test_member_cannot_clear_graduate_month(self):
        """编辑资料时预计毕业时间仍为必填项。"""
        self.client.force_authenticate(user=self.user1)
        url = f"/api/v1/members/{self.member1.public_id}/"
        response = self.client.patch(url, {"graduate_month": ""}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("graduate_month", response.json()["data"])

    def test_member_cannot_put_own_status(self):
        """成员完整更新时也不能修改自己的状态。"""
        self.client.force_authenticate(user=self.user1)
        url = f"/api/v1/members/{self.member1.public_id}/"
        data = self._full_update_payload(self.member1)
        data["status"] = MemberStatus.ALUMNI

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.json()["data"])

    def test_member_cannot_patch_own_tier(self):
        """成员不能修改自己的梯队。"""
        self.client.force_authenticate(user=self.user1)
        url = f"/api/v1/members/{self.member1.public_id}/"

        response = self.client.patch(url, {"tier": "二队"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("tier", response.json()["data"])
        self.member1.refresh_from_db()
        self.assertEqual(self.member1.tier, "一队")

    def test_member_cannot_put_changed_own_tier(self):
        """成员完整更新时也不能修改自己的梯队。"""
        self.client.force_authenticate(user=self.user1)
        url = f"/api/v1/members/{self.member1.public_id}/"
        data = self._full_update_payload(self.member1)
        data["tier"] = "二队"

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("tier", response.json()["data"])
        self.member1.refresh_from_db()
        self.assertEqual(self.member1.tier, "一队")

    def test_member_cannot_update_others_profile(self):
        """成员不能更新他人的资料。"""
        self.client.force_authenticate(user=self.user1)
        url = f"/api/v1/members/{self.member2.public_id}/"
        data = {"name": "Hacked Name"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 403)
        self.member2.refresh_from_db()
        self.assertEqual(self.member2.name, "Member Two")

    def test_admin_can_update_any_profile(self):
        """管理员可以更新任意成员资料。"""
        self.client.force_authenticate(user=self.admin_user)
        url = f"/api/v1/members/{self.member1.public_id}/"
        data = {"dorm": "紫荆8#888"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.member1.refresh_from_db()
        self.assertEqual(self.member1.dorm, "紫荆8#888")

    def test_unauthenticated_cannot_update(self):
        """未登录用户不能更新资料。"""
        url = f"/api/v1/members/{self.member1.public_id}/"
        data = {"name": "Unauthorized"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 401)
