from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient

from apps.authentication.models import UserRole
from apps.common.models import SystemStats
from apps.personnel.models import Member


class MemberStatsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.admin = User.objects.create_user(
            user_id="admin1", password="adminpass", name="Admin", role=UserRole.ADMIN
        )
        res = self.client.post(
            "/api/v1/auth/login",
            {"user_id": "admin1", "password": "adminpass"},
            format="json",
        )
        self.token = res.json()["data"]["token"]

    def auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_stats_endpoint_and_signals(self):
        stats = SystemStats.get_solo()
        initial = stats.total_members

        User = get_user_model()
        u = User.objects.create_user(user_id="20200001", password="x", name="A")
        Member.objects.create(user=u, name="A")

        stats.refresh_from_db()
        self.assertEqual(stats.total_members, initial + 1)

        self.auth()
        r = self.client.get("/api/v1/members/stats/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"]["total_members"], stats.total_members)

        Member.objects.filter(user=u).delete()
        stats.refresh_from_db()
        self.assertEqual(stats.total_members, initial)
