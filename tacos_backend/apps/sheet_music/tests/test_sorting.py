from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from rest_framework.test import APIClient

from apps.events.models import Event
from apps.personnel.models import Member
from apps.sheet_music.models import Sheet

User = get_user_model()


def create_member(
    user_id: str,
    name: str,
    *,
    voice_part: str = "Other",
    tier: str = "二队",
) -> Member:
    user = User.objects.create_user(user_id=user_id, password="password123", name=name)
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


class SheetSortingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_member = create_member("20261001", "站点管理员")
        self.admin_member.user.is_staff = True
        self.admin_member.user.role = "Admin"
        self.admin_member.user.save(update_fields=["is_staff", "role"])
        self.client.force_authenticate(user=self.admin_member.user)

    def test_sheet_list_is_sorted_by_title(self):
        create_sheet("Bravo")
        create_sheet("Alpha")
        create_sheet("Charlie")

        response = self.client.get("/api/v1/sheets/", {"page_size": 10})
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(
            [item["title"] for item in response.json()["data"]["results"]],
            ["Alpha", "Bravo", "Charlie"],
        )

    def test_sheet_detail_orders_visible_events_and_members(self):
        sheet = create_sheet("排序乐谱")
        later_event = Event.objects.create(
            name="Later",
            introduction="Later",
            start_date="2026-08-01",
            end_date="2026-08-01",
            visibility="ALL",
        )
        earlier_event = Event.objects.create(
            name="Earlier",
            introduction="Earlier",
            start_date="2026-07-01",
            end_date="2026-07-01",
            visibility="ALL",
        )
        for event in (earlier_event, later_event):
            event.admins.add(self.admin_member)
            sheet.visible_events.add(event)

        bob = create_member("20261002", "Bob", voice_part="B2", tier="二队")
        alice = create_member("20261003", "Alice", voice_part="S1", tier="一队")
        charlie = create_member("20261004", "Charlie", voice_part="A1", tier="一队")
        sheet.visible_members.add(bob, charlie, alice)

        response = self.client.get(f"/api/v1/sheets/{sheet.public_id}/")
        self.assertEqual(response.status_code, 200, response.json())
        data = response.json()["data"]
        self.assertEqual(
            [item["name"] for item in data["visible_events"]],
            ["Later", "Earlier"],
        )
        self.assertEqual(
            [item["name"] for item in data["visible_members"]],
            ["Alice", "Charlie", "Bob"],
        )

    def test_sheet_list_prefetches_visibility_details(self):
        event = Event.objects.create(
            name="可见活动",
            introduction="排练",
            start_date="2026-08-01",
            end_date="2026-08-01",
            visibility="ALL",
        )
        event.admins.add(self.admin_member)
        member = create_member("20261011", "Visible", voice_part="S1", tier="一队")
        for index in range(5):
            sheet = create_sheet(f"ListSheet{index}")
            sheet.visible_events.add(event)
            sheet.visible_members.add(member)

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/v1/sheets/", {"page_size": 10})

        self.assertEqual(response.status_code, 200, response.json())
        self.assertLessEqual(len(ctx), 5)
