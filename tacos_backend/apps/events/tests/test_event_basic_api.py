from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient

from apps.events.models import Event
from apps.personnel.models import Member


class EventBasicApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.site_admin = User.objects.create_user(
            user_id="admin001",
            password="AdminPass123",
            name="Site Admin",
            is_staff=True,
            role="Admin",
        )
        self.user1 = User.objects.create_user(
            user_id="m10001", password="Pass1001", name="Member1"
        )
        self.user2 = User.objects.create_user(
            user_id="m10002", password="Pass1002", name="Member2"
        )
        self.member1 = Member.objects.create(
            user=self.user1,
            name="Member1",
            gender="男",
            voice_part="Other",
            wechat_id="wx1",
            department="",
            class_name="",
            phone_number="13800000001",
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
        self.member2 = Member.objects.create(
            user=self.user2,
            name="Member2",
            gender="男",
            voice_part="Other",
            wechat_id="wx2",
            department="",
            class_name="",
            phone_number="13800000002",
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

        self._auth("admin001", "AdminPass123")
        payload = {
            "name": "排练活动",
            "introduction": "周五晚排练",
            "announcement": "",
            "start_date": "2025-11-10",
            "end_date": "2025-11-10",
            "visibility": "ALL",
            "admins": [self.member1.public_id],
            "participants": [],
        }
        resp = self.client.post("/api/v1/events/", payload, format="json")
        self.assertEqual(resp.status_code, 201, resp.json())
        self.event_id = resp.json()["data"]["id"]
        self.client.credentials()  # 清空认证

    def _auth(self, user_id: str, password: str):
        res = self.client.post(
            "/api/v1/auth/login",
            {"user_id": user_id, "password": password},
            format="json",
        )
        self.assertEqual(res.status_code, 200, getattr(res, "content", None))
        token = res.json()["data"]["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_relation_not_member_member_admin(self):
        self._auth("m10002", "Pass1002")
        res_detail = self.client.get(f"/api/v1/events/{self.event_id}/")
        self.assertEqual(res_detail.status_code, 200, res_detail.json())
        data = res_detail.json()["data"]
        self.assertEqual(data.get("relation"), "not_member")
        self.assertEqual(data.get("is_participant"), False)
        self.assertIn("name", data)
        self.assertNotIn("participants_detail", data)
        self.assertNotIn("sheets", data)

        res_join = self.client.post(f"/api/v1/events/{self.event_id}/join/")
        self.assertEqual(res_join.status_code, 200, res_join.json())
        res_detail2 = self.client.get(f"/api/v1/events/{self.event_id}/")
        self.assertEqual(res_detail2.status_code, 200, res_detail2.json())
        self.assertEqual(res_detail2.json()["data"].get("relation"), "member")
        self.assertEqual(res_detail2.json()["data"].get("is_participant"), True)

        self._auth("admin001", "AdminPass123")
        ev = Event.objects.get(public_id=self.event_id)
        ev.admins.add(self.member2)
        self._auth("m10002", "Pass1002")
        res_detail3 = self.client.get(f"/api/v1/events/{self.event_id}/")
        self.assertEqual(res_detail3.status_code, 200, res_detail3.json())
        self.assertEqual(res_detail3.json()["data"].get("relation"), "event_admin")
        self.assertEqual(res_detail3.json()["data"].get("is_participant"), True)

    def test_is_participant_for_admin_only(self):
        """活动管理员未加入参与者列表时可自行报名。"""
        self._auth("m10001", "Pass1001")
        res_detail = self.client.get(f"/api/v1/events/{self.event_id}/")
        self.assertEqual(res_detail.status_code, 200, res_detail.json())
        data = res_detail.json()["data"]
        self.assertEqual(data.get("relation"), "event_admin")
        self.assertEqual(data.get("is_participant"), False)

        res_join = self.client.post(f"/api/v1/events/{self.event_id}/join/")
        self.assertEqual(res_join.status_code, 200, res_join.json())
        res_detail_after_join = self.client.get(f"/api/v1/events/{self.event_id}/")
        self.assertEqual(res_detail_after_join.status_code, 200)
        data_after_join = res_detail_after_join.json()["data"]
        self.assertEqual(data_after_join.get("relation"), "event_admin")
        self.assertEqual(data_after_join.get("is_participant"), True)

    def test_event_admin_can_manage_without_joining(self):
        """活动管理员不在参与者列表中时仍可管理活动。"""
        self._auth("m10001", "Pass1001")
        event = Event.objects.get(public_id=self.event_id)
        self.assertFalse(event.participants.filter(pk=self.member1.pk).exists())

        detail_response = self.client.get(f"/api/v1/events/{self.event_id}/")
        self.assertEqual(detail_response.status_code, 200, detail_response.json())
        detail = detail_response.json()["data"]
        self.assertEqual(detail.get("relation"), "event_admin")
        self.assertEqual(detail.get("is_participant"), False)

        admin_response = self.client.get(
            f"/api/v1/events/{self.event_id}/admin-detail/"
        )
        self.assertEqual(admin_response.status_code, 200, admin_response.json())

        sessions_response = self.client.get(
            f"/api/v1/events/{self.event_id}/checkin/sessions/"
        )
        self.assertEqual(sessions_response.status_code, 200, sessions_response.json())

        create_session_response = self.client.post(
            f"/api/v1/events/{self.event_id}/checkin/start/",
            {"name": "排练签到", "type": "NONE"},
            format="json",
        )
        self.assertEqual(
            create_session_response.status_code,
            201,
            create_session_response.json(),
        )

        create_assignment_response = self.client.post(
            f"/api/v1/events/{self.event_id}/assignments/create/",
            {
                "title": "录音作业",
                "description": "",
                "deadline": (timezone.now() + timedelta(days=1)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(
            create_assignment_response.status_code,
            201,
            create_assignment_response.json(),
        )

        assignments_response = self.client.get(
            f"/api/v1/events/{self.event_id}/assignments/"
        )
        self.assertEqual(
            assignments_response.status_code, 200, assignments_response.json()
        )
        self.assertEqual(assignments_response.json()["data"]["count"], 1)

        members_response = self.client.get(f"/api/v1/events/{self.event_id}/members/")
        self.assertEqual(members_response.status_code, 200, members_response.json())

        event.refresh_from_db()
        self.assertFalse(event.participants.filter(pk=self.member1.pk).exists())
