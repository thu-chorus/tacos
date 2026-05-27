from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient

from apps.events.models import Event, EventVisibility
from apps.personnel.models import Member, MemberStatus

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


def create_event(name: str, admin: Member, **kwargs) -> Event:
    event = Event.objects.create(
        name=name,
        introduction=name,
        start_date="2026-01-01",
        end_date="2026-01-01",
        **kwargs,
    )
    event.admins.add(admin)
    return event


class AlumniEventVisibilityTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_member = create_member("admin", "Admin")
        self.admin_member.user.role = "Admin"
        self.admin_member.user.is_staff = True
        self.admin_member.user.save(update_fields=["role", "is_staff"])
        self.active_member = create_member("20210001", "Active")
        self.alumni_member = create_member(
            "20190001", "Alumni", status=MemberStatus.ALUMNI
        )

        self.public_event = create_event(
            "Public",
            self.admin_member,
            visibility=EventVisibility.ALL,
            visible_to_alumni=False,
        )
        self.alumni_event = create_event(
            "Alumni",
            self.admin_member,
            visibility=EventVisibility.PARTIAL,
            visible_to_alumni=True,
        )
        self.hidden_event = create_event(
            "Hidden",
            self.admin_member,
            visibility=EventVisibility.PARTIAL,
            visible_to_alumni=False,
        )

    def _listed_event_ids(self):
        response = self.client.get("/api/v1/events/")
        self.assertEqual(response.status_code, 200)
        return {item["id"] for item in response.json()["data"]["results"]}

    def test_alumni_only_sees_alumni_visible_events(self):
        self.client.force_authenticate(user=self.alumni_member.user)
        ids = self._listed_event_ids()
        self.assertIn(self.alumni_event.public_id, ids)
        self.assertNotIn(self.public_event.public_id, ids)
        self.assertNotIn(self.hidden_event.public_id, ids)

    def test_active_member_keeps_existing_visibility_rules(self):
        self.client.force_authenticate(user=self.active_member.user)
        ids = self._listed_event_ids()
        self.assertIn(self.public_event.public_id, ids)
        self.assertNotIn(self.alumni_event.public_id, ids)
        self.assertNotIn(self.hidden_event.public_id, ids)

    def test_alumni_can_join_alumni_visible_event(self):
        self.client.force_authenticate(user=self.alumni_member.user)
        response = self.client.post(
            f"/api/v1/events/{self.alumni_event.public_id}/join/"
        )
        self.assertEqual(response.status_code, 200)
        self.alumni_event.refresh_from_db()
        self.assertTrue(
            self.alumni_event.participants.filter(pk=self.alumni_member.pk).exists()
        )

    def test_alumni_admin_requires_alumni_visible_event_on_create(self):
        self.client.force_authenticate(user=self.admin_member.user)
        response = self.client.post(
            "/api/v1/events/",
            {
                "name": "Invisible",
                "introduction": "Invisible",
                "start_date": "2026-02-01",
                "end_date": "2026-02-01",
                "visibility": EventVisibility.PARTIAL,
                "visible_to_alumni": False,
                "admins": [self.alumni_member.public_id],
                "participants": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("校友不能担任校友不可见活动的管理员", str(response.data))

    def test_alumni_admin_requires_alumni_visible_event_on_update(self):
        self.alumni_event.admins.add(self.alumni_member)
        self.client.force_authenticate(user=self.admin_member.user)
        response = self.client.put(
            f"/api/v1/events/{self.alumni_event.public_id}/",
            {
                "name": self.alumni_event.name,
                "introduction": self.alumni_event.introduction,
                "start_date": str(self.alumni_event.start_date),
                "end_date": str(self.alumni_event.end_date),
                "visibility": self.alumni_event.visibility,
                "visible_to_alumni": False,
                "admins": [
                    self.admin_member.public_id,
                    self.alumni_member.public_id,
                ],
                "participants": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("校友不能担任校友不可见活动的管理员", str(response.data))
