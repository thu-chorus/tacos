from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient

from apps.personnel.models import Member


class EventViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.admin = User.objects.create_user(
            user_id="admin1",
            password="adminpass",
            name="Admin",
            is_staff=True,
            role="Admin",
        )
        self.user = User.objects.create_user(
            user_id="u1001", password="pass1001", name="User"
        )
        self.member = Member.objects.create(
            user=self.user,
            name="User",
            gender="男",
            voice_part="Other",
            wechat_id="wx",
            department="",
            class_name="",
            phone_number="13800000000",
            email="",
            dorm="",
            hometown="",
            ethnicity="",
            political_status="",
            political_affiliation="",
            is_specialty=False,
            is_centralized=False,
            position="",
            join_month="",
            tier="二队",
            portfolio="",
        )

    def auth(self, user_id: str, password: str):
        res = self.client.post(
            "/api/v1/auth/login",
            {"user_id": user_id, "password": password},
            format="json",
        )
        token = res.json()["data"]["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_admin_create_and_public_list(self):
        self.auth("admin1", "adminpass")
        payload = {
            "name": "招新说明会",
            "introduction": "欢迎参加",
            "start_date": "2025-10-01",
            "end_date": "2025-10-02",
            "is_public": True,
            "admins": [self.member.id],
            "participants": [],
        }
        res = self.client.post("/api/v1/events/", payload, format="json")
        self.assertEqual(res.status_code, 201)
        eid = res.json()["data"]["id"]

        self.client.credentials()
        res_list = self.client.get("/api/v1/events/")
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(any(e["id"] == eid for e in res_list.json()["data"]["results"]))

    def test_join_public_event(self):
        self.auth("admin1", "adminpass")
        payload = {
            "name": "开放排练",
            "introduction": "来一起唱",
            "start_date": "2025-10-10",
            "end_date": "2025-10-10",
            "is_public": True,
            "admins": [self.member.id],
            "participants": [],
        }
        res = self.client.post("/api/v1/events/", payload, format="json")
        eid = res.json()["data"]["id"]

        self.auth("u1001", "pass1001")
        res_join = self.client.post(f"/api/v1/events/{eid}/join/")
        self.assertEqual(res_join.status_code, 200)
