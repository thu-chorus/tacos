from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from apps.personnel.models import Member


class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(
            user_id="2021012345", password="password123", name="张三"
        )

    def test_login_and_me_and_logout(self):
        url = reverse("login")
        res = self.client.post(
            url, {"user_id": "2021012345", "password": "password123"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("data", res.json())
        token = res.json()["data"]["token"]
        refresh = res.json()["data"]["refresh_token"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        me_url = reverse("me")
        me_res = self.client.get(me_url)
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["data"]["user_id"], "2021012345")

        refresh_url = reverse("token_refresh")
        ref_res = self.client.post(refresh_url, {"refresh": refresh}, format="json")
        self.assertEqual(ref_res.status_code, 200)
        self.assertIn("data", ref_res.json())
        self.assertIn("token", ref_res.json()["data"])

        logout_url = reverse("logout")
        out_res = self.client.post(logout_url)
        self.assertEqual(out_res.status_code, 200)

    def test_first_login_requires_graduate_month(self):
        res = self.client.post(
            reverse("login"),
            {"user_id": "2021012345", "password": "password123"},
            format="json",
        )
        token = res.json()["data"]["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        payload = {
            "name": "张三",
            "gender": "男",
            "wechat_id": "wx_zhangsan",
            "voice_part": "S1",
            "tier": "二队",
            "department": "000 建筑学院",
            "class_name": "计01",
            "phone_number": "13812345678",
            "email": "zhangsan@example.com",
            "dorm": "1-101",
            "birthday": "2000-01-01",
            "hometown": "北京 北京",
            "ethnicity": "汉族",
            "political_status": "共青团员",
            "political_affiliation": "艺术团",
            "join_month": "2021-09",
            "new_password": "NewPassword123!",
            "new_password_confirm": "NewPassword123!",
        }
        response = self.client.put(reverse("first_login_setup"), payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("graduate_month", response.json()["data"])
        self.assertFalse(Member.objects.filter(user=self.user).exists())
