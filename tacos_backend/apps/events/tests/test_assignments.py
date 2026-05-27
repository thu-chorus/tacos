from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient

from apps.personnel.models import Member


class AssignmentViewsTest(TestCase):
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

    def _create_event(self) -> int:
        self.auth("admin1", "adminpass")
        payload = {
            "name": "测试活动",
            "introduction": "介绍",
            "announcement": "",
            "start_date": "2025-10-01",
            "end_date": "2025-10-02",
            "visibility": "ALL",
            "admins": [self.member.id],
            "participants": [],
        }
        res = self.client.post("/api/v1/events/", payload, format="json")
        self.assertEqual(res.status_code, 201)
        return res.json()["data"]["id"]

    def test_assignment_flow_create_submit_grade(self):
        eid = self._create_event()

        deadline = (
            (timezone.now() + timedelta(days=1)).isoformat().replace("+00:00", "Z")
        )
        res_create = self.client.post(
            f"/api/v1/events/{eid}/assignments/create/",
            {
                "title": "第一次作业",
                "description": "请按要求完成",
                "deadline": deadline,
            },
            format="json",
        )
        self.assertEqual(res_create.status_code, 201)
        aid = res_create.json()["data"]["id"]

        file = SimpleUploadedFile("guide.txt", b"guide", content_type="text/plain")
        res_up = self.client.post(
            f"/api/v1/events/{eid}/assignments/{aid}/attachments/", {"file": file}
        )
        self.assertEqual(res_up.status_code, 201)

        self.auth("u1001", "pass1001")
        res_list = self.client.get(f"/api/v1/events/{eid}/assignments/")
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(any(a["id"] == aid for a in res_list.json()["data"]["results"]))
        res_detail = self.client.get(f"/api/v1/events/{eid}/assignments/{aid}/")
        self.assertEqual(res_detail.status_code, 200)

        upload = SimpleUploadedFile(
            "answer.txt", b"my answer", content_type="text/plain"
        )
        res_submit = self.client.post(
            f"/api/v1/events/{eid}/assignments/{aid}/submit/",
            {"text": "完成了", "files": [upload]},
        )
        self.assertIn(res_submit.status_code, (200, 201))
        sub_id = res_submit.json()["data"]["id"]

        self.auth("admin1", "adminpass")
        res_subs = self.client.get(
            f"/api/v1/events/{eid}/assignments/{aid}/submissions/", {"name": "User"}
        )
        self.assertEqual(res_subs.status_code, 200)
        self.assertGreaterEqual(res_subs.json()["data"]["count"], 1)

        res_grade = self.client.post(
            f"/api/v1/events/{eid}/assignments/{aid}/grade/",
            {"submission_id": sub_id, "graded_score": 95, "graded_comment": "很好"},
            format="json",
        )
        self.assertEqual(res_grade.status_code, 200)
        self.assertEqual(res_grade.json()["data"]["graded_score"], "95")

    def test_cannot_submit_after_deadline(self):
        eid = self._create_event()
        past = (timezone.now() - timedelta(days=1)).isoformat().replace("+00:00", "Z")
        res_create = self.client.post(
            f"/api/v1/events/{eid}/assignments/create/",
            {
                "title": "过期作业",
                "description": "已经过期",
                "deadline": past,
            },
            format="json",
        )
        aid = res_create.json()["data"]["id"]

        self.auth("u1001", "pass1001")
        res_submit = self.client.post(
            f"/api/v1/events/{eid}/assignments/{aid}/submit/", {"text": "补交"}
        )
        self.assertEqual(res_submit.status_code, 403)

    def test_my_submission_isolated(self):
        eid = self._create_event()
        deadline = (
            (timezone.now() + timedelta(days=1)).isoformat().replace("+00:00", "Z")
        )
        res_create = self.client.post(
            f"/api/v1/events/{eid}/assignments/create/",
            {
                "title": "隔离测试",
                "description": "",
                "deadline": deadline,
            },
            format="json",
        )
        aid = res_create.json()["data"]["id"]

        User = get_user_model()
        user2 = User.objects.create_user(
            user_id="u2002", password="pass2002", name="User2"
        )
        member2 = Member.objects.create(
            user=user2,
            name="User2",
            gender="男",
            voice_part="Other",
            wechat_id="w2",
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

        from apps.events.models import Event

        ev = Event.objects.get(pk=eid)
        ev.participants.add(self.member)
        ev.participants.add(member2)

        self.auth("u1001", "pass1001")
        self.client.post(
            f"/api/v1/events/{eid}/assignments/{aid}/submit/", {"text": "me"}
        )
        self.auth("u2002", "pass2002")
        self.client.post(
            f"/api/v1/events/{eid}/assignments/{aid}/submit/", {"text": "other"}
        )

        self.auth("u1001", "pass1001")
        res_my = self.client.get(
            f"/api/v1/events/{eid}/assignments/{aid}/my-submission/"
        )
        self.assertEqual(res_my.status_code, 200)
        self.assertEqual(res_my.json()["data"]["submission"]["text"], "me")
