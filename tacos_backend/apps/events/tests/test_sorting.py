from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from rest_framework.test import APIClient

from apps.events.models import (
    Assignment,
    Event,
    EventCheckinRecord,
    EventCheckinSession,
)
from apps.personnel.models import Member
from apps.sheet_music.models import Sheet

User = get_user_model()


def create_member(
    user_id: str,
    name: str,
    *,
    voice_part: str = "Other",
    tier: str = "二队",
    is_admin: bool = False,
) -> Member:
    user = User.objects.create_user(
        user_id=user_id,
        password="password123",
        name=name,
        is_staff=is_admin,
        role="Admin" if is_admin else "Member",
    )
    return Member.objects.create(
        user=user,
        name=name,
        voice_part=voice_part,
        tier=tier,
        wechat_id="wx",
        phone_number=f"138{int(user_id[-8:]):08d}",
    )


def create_sheet(title: str) -> Sheet:
    upload = SimpleUploadedFile(
        f"{title}.pdf",
        b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF",
        content_type="application/pdf",
    )
    return Sheet.objects.create(title=title, original_file=upload)


class EventSortingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.site_admin = create_member("20260001", "站点管理员", is_admin=True)
        self.event_admin = create_member(
            "20260002", "Bob", voice_part="B2", tier="二队"
        )
        self.soprano = create_member("20260003", "Alice", voice_part="S1", tier="一队")
        self.alto = create_member("20260004", "Charlie", voice_part="A1", tier="一队")
        self.event = Event.objects.create(
            name="排序测试活动",
            introduction="排序测试活动",
            start_date="2026-06-01",
            end_date="2026-06-01",
            visibility="ALL",
        )
        self.event.admins.add(self.event_admin)
        self.client.force_authenticate(user=self.site_admin.user)

    def test_event_sheets_are_sorted_in_list_and_admin_detail(self):
        bravo = create_sheet("Bravo")
        alpha = create_sheet("Alpha")
        charlie = create_sheet("Charlie")
        for sheet in (bravo, alpha, charlie):
            sheet.visible_events.add(self.event)

        response = self.client.get(f"/api/v1/events/{self.event.public_id}/sheets/")
        self.assertEqual(response.status_code, 200, response.json())
        titles = [item["title"] for item in response.json()["data"]["results"]]
        self.assertEqual(titles, ["Alpha", "Bravo", "Charlie"])

        paged_response = self.client.get(
            f"/api/v1/events/{self.event.public_id}/sheets/",
            {"page": 2, "page_size": 1},
        )
        self.assertEqual(paged_response.status_code, 200, paged_response.json())
        self.assertEqual(paged_response.json()["data"]["count"], 3)
        self.assertEqual(
            [item["title"] for item in paged_response.json()["data"]["results"]],
            ["Bravo"],
        )

        detail_response = self.client.get(
            f"/api/v1/events/{self.event.public_id}/admin-detail/"
        )
        self.assertEqual(detail_response.status_code, 200, detail_response.json())
        detail_titles = [
            item["title"] for item in detail_response.json()["data"]["sheets"]
        ]
        self.assertEqual(detail_titles, ["Alpha", "Bravo", "Charlie"])

    def test_event_member_lists_use_shared_member_order(self):
        self.event.participants.add(self.event_admin, self.alto, self.soprano)

        response = self.client.get(f"/api/v1/events/{self.event.public_id}/members/")
        self.assertEqual(response.status_code, 200, response.json())
        names = [item["name"] for item in response.json()["data"]["results"]]
        self.assertEqual(names, ["Alice", "Charlie", "Bob"])

        detail_response = self.client.get(
            f"/api/v1/events/{self.event.public_id}/admin-detail/"
        )
        participant_names = [
            item["name"]
            for item in detail_response.json()["data"]["participants_detail"]
        ]
        self.assertEqual(participant_names, ["Alice", "Charlie", "Bob"])

    def test_checkin_summary_orders_checked_and_unchecked_members(self):
        self.event.participants.add(self.event_admin, self.alto, self.soprano)
        session = EventCheckinSession.objects.create(event=self.event)
        EventCheckinRecord.objects.create(session=session, member=self.event_admin)

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(
                f"/api/v1/events/{self.event.public_id}/checkin/summary/",
                {"session_id": session.id},
            )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertLessEqual(len(ctx), 8)
        checked = [item["name"] for item in response.json()["data"]["checked"]]
        not_checked = [item["name"] for item in response.json()["data"]["not_checked"]]
        result_rows = response.json()["data"]["results"]
        self.assertEqual(checked, ["Bob"])
        self.assertEqual(not_checked, ["Alice", "Charlie"])
        self.assertEqual(
            [(item["member_name"], bool(item["checked_at"])) for item in result_rows],
            [("Alice", False), ("Charlie", False), ("Bob", True)],
        )

    def test_checkin_records_mine_filter_limits_admin_to_own_records(self):
        self.event.participants.add(self.event_admin, self.alto, self.soprano)
        session = EventCheckinSession.objects.create(event=self.event)
        EventCheckinRecord.objects.create(session=session, member=self.event_admin)
        EventCheckinRecord.objects.create(session=session, member=self.alto)

        self.client.force_authenticate(user=self.event_admin.user)
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(
                f"/api/v1/events/{self.event.public_id}/checkin/records/",
                {"mine": "true", "page_size": 10},
            )

        self.assertEqual(response.status_code, 200, response.json())
        self.assertLessEqual(len(ctx), 8)
        rows = response.json()["data"]["results"]
        self.assertEqual(response.json()["data"]["count"], 1)
        self.assertEqual([item["member_name"] for item in rows], ["Bob"])

    def test_checkin_status_includes_current_member_checked_state(self):
        self.event.participants.add(self.event_admin, self.alto)
        session = EventCheckinSession.objects.create(event=self.event, is_active=True)
        EventCheckinRecord.objects.create(session=session, member=self.event_admin)

        self.client.force_authenticate(user=self.event_admin.user)
        checked_response = self.client.get(
            f"/api/v1/events/{self.event.public_id}/checkin/status/"
        )
        self.assertEqual(checked_response.status_code, 200, checked_response.json())
        self.assertTrue(checked_response.json()["data"]["has_checked_in"])

        self.client.force_authenticate(user=self.alto.user)
        unchecked_response = self.client.get(
            f"/api/v1/events/{self.event.public_id}/checkin/status/"
        )
        self.assertEqual(unchecked_response.status_code, 200, unchecked_response.json())
        self.assertFalse(unchecked_response.json()["data"]["has_checked_in"])

    def test_assignment_include_all_submissions_are_member_sorted(self):
        self.event.participants.add(self.event_admin, self.alto, self.soprano)
        assignment = Assignment.objects.create(
            event=self.event,
            created_by=self.site_admin.user,
            title="排序作业",
            deadline=timezone.now() + timedelta(days=1),
        )

        response = self.client.get(
            f"/api/v1/events/{self.event.public_id}/assignments/{assignment.public_id}/submissions/",
            {"include_all": "1", "page_size": 10},
        )
        self.assertEqual(response.status_code, 200, response.json())
        names = [item["member_name"] for item in response.json()["data"]["results"]]
        self.assertEqual(names, ["Alice", "Charlie", "Bob"])
