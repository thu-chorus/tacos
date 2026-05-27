from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from rest_framework.test import APIClient

from apps.events.models import Event, EventVisibility
from apps.personnel.models import Member, MemberStatus
from apps.sheet_music.models import Sheet

User = get_user_model()


def create_member(user_id: str, name: str, status: str = MemberStatus.ACTIVE) -> Member:
    user = User.objects.create_user(user_id=user_id, password="password123", name=name)
    return Member.objects.create(
        user=user,
        name=name,
        gender="",
        voice_part="Other",
        wechat_id="wx",
        department="",
        class_name="",
        phone_number="13800000000",
        email="",
        tier="二队",
        status=status,
    )


def create_sheet(title: str, **kwargs) -> Sheet:
    upload = SimpleUploadedFile(
        f"{title}.pdf",
        b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF",
        content_type="application/pdf",
    )
    return Sheet.objects.create(title=title, original_file=upload, **kwargs)


class AlumniSheetVisibilityTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_member = create_member("admin", "Admin")
        self.active_member = create_member("20210001", "Active")
        self.alumni_member = create_member(
            "20190001", "Alumni", status=MemberStatus.ALUMNI
        )

        self.alumni_event = Event.objects.create(
            name="Alumni Event",
            introduction="Alumni Event",
            start_date="2026-01-01",
            end_date="2026-01-01",
            visibility=EventVisibility.PARTIAL,
            visible_to_alumni=True,
        )
        self.alumni_event.admins.add(self.admin_member)

        self.active_sheet = create_sheet("Active", visible_to_all=True)
        self.alumni_sheet = create_sheet(
            "Alumni", visible_to_all=False, visible_to_alumni=True
        )
        self.event_sheet = create_sheet("Event", visible_to_all=False)
        self.event_sheet.visible_events.add(self.alumni_event)
        self.hidden_sheet = create_sheet("Hidden", visible_to_all=False)

    def _listed_sheet_ids(self):
        response = self.client.get("/api/v1/sheets/")
        self.assertEqual(response.status_code, 200)
        return {item["id"] for item in response.json()["data"]["results"]}

    def test_alumni_sees_alumni_visible_and_alumni_event_sheets(self):
        self.client.force_authenticate(user=self.alumni_member.user)
        ids = self._listed_sheet_ids()
        self.assertIn(self.alumni_sheet.public_id, ids)
        self.assertIn(self.event_sheet.public_id, ids)
        self.assertNotIn(self.active_sheet.public_id, ids)
        self.assertNotIn(self.hidden_sheet.public_id, ids)

    def test_active_member_keeps_existing_sheet_visibility(self):
        self.client.force_authenticate(user=self.active_member.user)
        ids = self._listed_sheet_ids()
        self.assertIn(self.active_sheet.public_id, ids)
        self.assertNotIn(self.alumni_sheet.public_id, ids)
        self.assertNotIn(self.event_sheet.public_id, ids)
        self.assertNotIn(self.hidden_sheet.public_id, ids)

    def test_event_sheet_endpoint_respects_alumni_visibility(self):
        self.client.force_authenticate(user=self.alumni_member.user)
        response = self.client.get(
            f"/api/v1/events/{self.alumni_event.public_id}/sheets/"
        )
        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.json()["data"]["results"]}
        self.assertIn(self.event_sheet.public_id, ids)
