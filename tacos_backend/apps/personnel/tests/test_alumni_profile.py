from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient

from apps.personnel.models import AlumniProfile, Member, MemberStatus

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


class AlumniProfileTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            user_id="admin",
            password="password123",
            name="Admin",
            role="Admin",
            is_staff=True,
        )
        self.active_member = create_member("20210001", "Active")
        self.alumni_member = create_member(
            "20190001", "Alumni", status=MemberStatus.ALUMNI
        )

    def test_admin_status_change_creates_alumni_profile(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            f"/api/v1/members/{self.active_member.public_id}/",
            {"status": MemberStatus.ALUMNI},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.active_member.refresh_from_db()
        self.assertEqual(self.active_member.status, MemberStatus.ALUMNI)
        self.assertTrue(
            AlumniProfile.objects.filter(member=self.active_member).exists()
        )

    def test_member_cannot_change_own_status(self):
        self.client.force_authenticate(user=self.active_member.user)
        response = self.client.patch(
            f"/api/v1/members/{self.active_member.public_id}/",
            {"status": MemberStatus.ALUMNI},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.active_member.refresh_from_db()
        self.assertEqual(self.active_member.status, MemberStatus.ACTIVE)

    def test_alumni_can_manage_own_contact_window(self):
        self.client.force_authenticate(user=self.alumni_member.user)
        response = self.client.get("/api/v1/alumni-profiles/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"]["member_public_id"], self.alumni_member.public_id
        )

        response = self.client.patch(
            "/api/v1/alumni-profiles/me/",
            {
                "current_city": "Shanghai",
                "industry": "Technology",
                "company": "Example Co.",
                "job_title": "Product Manager",
                "graduation_month": "2023-06",
                "bio": "Building music tools.",
                "contact_note": "Email preferred",
                "allow_contact": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        profile = AlumniProfile.objects.get(member=self.alumni_member)
        self.assertEqual(profile.current_city, "Shanghai")
        self.assertEqual(profile.industry, "Technology")
        self.assertEqual(profile.company, "Example Co.")
        self.assertEqual(profile.job_title, "Product Manager")
        self.assertEqual(profile.graduation_month, "2023-06")
        self.assertEqual(profile.bio, "Building music tools.")

    def test_alumni_graduation_month_is_required(self):
        self.client.force_authenticate(user=self.alumni_member.user)
        response = self.client.patch(
            "/api/v1/alumni-profiles/me/",
            {
                "graduation_month": "",
                "current_city": "Shanghai",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("graduation_month", response.json()["data"])

    def test_alumni_profile_rejects_non_profile_fields(self):
        self.client.force_authenticate(user=self.alumni_member.user)
        response = self.client.patch(
            "/api/v1/alumni-profiles/me/",
            {
                "wechat_id": "member_wx",
                "phone_number": "13800000001",
                "email": "member@example.com",
                "graduate_month": "2024-06",
                "graduation_month": "2023-06",
                "unexpected_field": "ignored",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        errors = response.json()["data"]
        self.assertIn("wechat_id", errors)
        self.assertIn("phone_number", errors)
        self.assertIn("email", errors)
        self.assertIn("graduate_month", errors)
        self.assertIn("unexpected_field", errors)
        self.assertNotIn("graduation_month", errors)

    def test_active_member_cannot_use_alumni_contact_window(self):
        self.client.force_authenticate(user=self.active_member.user)
        response = self.client.get("/api/v1/alumni-profiles/me/")
        self.assertEqual(response.status_code, 403)

    def test_hidden_member_fields_do_not_hide_distinct_alumni_profile(self):
        self.alumni_member.email = "private@example.com"
        self.alumni_member.phone_number = "13800000002"
        self.alumni_member.graduate_month = "2023-06"
        self.alumni_member.is_specialty = True
        self.alumni_member.is_centralized = True
        self.alumni_member.hidden_fields = [
            "email",
            "phone_number",
            "graduate_month",
            "is_specialty",
            "is_centralized",
        ]
        self.alumni_member.save(
            update_fields=[
                "email",
                "phone_number",
                "graduate_month",
                "is_specialty",
                "is_centralized",
                "hidden_fields",
            ]
        )
        AlumniProfile.objects.update_or_create(
            member=self.alumni_member,
            defaults={
                "current_city": "Shanghai",
                "industry": "Technology",
                "graduation_month": "2023-06",
                "allow_contact": True,
            },
        )

        self.client.force_authenticate(user=self.active_member.user)
        response = self.client.get(f"/api/v1/members/{self.alumni_member.public_id}/")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIsNone(data["email"])
        self.assertIsNone(data["phone_number"])
        self.assertIsNone(data["graduate_month"])
        self.assertIsNone(data["is_specialty"])
        self.assertIsNone(data["is_centralized"])
        self.assertNotIn("hidden_fields", data)
        self.assertEqual(data["alumni_profile"]["current_city"], "Shanghai")
        self.assertEqual(data["alumni_profile"]["industry"], "Technology")
        self.assertEqual(data["alumni_profile"]["graduation_month"], "2023-06")
