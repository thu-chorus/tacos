from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient

from apps.authentication.models import UserRole


class SystemAnnouncementsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.admin = User.objects.create_user(
            user_id="admin1", password="adminpass", name="Admin", role=UserRole.ADMIN
        )
        self.user = User.objects.create_user(
            user_id="20210001", password="userpass", name="Alice"
        )

        res = self.client.post(
            "/api/v1/auth/login",
            {"user_id": "admin1", "password": "adminpass"},
            format="json",
        )
        self.admin_token = res.json()["data"]["token"]
        res2 = self.client.post(
            "/api/v1/auth/login",
            {"user_id": "20210001", "password": "userpass"},
            format="json",
        )
        self.user_token = res2.json()["data"]["token"]

    def test_public_list_and_admin_crud(self):
        list_res = self.client.get("/api/v1/common/announcements/")
        self.assertEqual(list_res.status_code, 200)
        self.assertIn("data", list_res.json())

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        payload = {
            "publish_time": timezone.now().isoformat(),
            "content": "普通用户不应能创建公告",
        }
        bad_create = self.client.post(
            "/api/v1/common/announcements/", payload, format="json"
        )
        self.assertIn(bad_create.status_code, (401, 403))

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        create_res = self.client.post(
            "/api/v1/common/announcements/",
            {"publish_time": timezone.now().isoformat(), "content": "系统维护公告"},
            format="json",
        )
        self.assertEqual(create_res.status_code, 201)
        ann_id = create_res.json()["data"]["id"]

        list_res2 = self.client.get("/api/v1/common/announcements/?page_size=1")
        self.assertEqual(list_res2.status_code, 200)
        self.assertGreaterEqual(list_res2.json()["data"]["count"], 1)

        update_res = self.client.put(
            f"/api/v1/common/announcements/{ann_id}/",
            {
                "publish_time": timezone.now().isoformat(),
                "content": "系统维护公告（已更新）",
            },
            format="json",
        )
        self.assertEqual(update_res.status_code, 200)

        del_res = self.client.delete(f"/api/v1/common/announcements/{ann_id}/")
        self.assertIn(del_res.status_code, (200, 204))
