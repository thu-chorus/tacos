import os
import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from PIL import Image
from rest_framework.test import APIClient

from apps.authentication.models import UserRole
from apps.personnel.models import Member

User = get_user_model()


def build_avatar_upload(
    name: str = "avatar.png", content_type: str = "image/png"
) -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (16, 16), color=(154, 86, 181)).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


class MemberAvatarApiTest(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)
        self.addCleanup(self.media_override.disable)

        self.user1 = User.objects.create_user(
            user_id="2021000001",
            password="password123",
            name="Member One",
            role=UserRole.MEMBER,
        )
        self.user2 = User.objects.create_user(
            user_id="2021000002",
            password="password123",
            name="Member Two",
            role=UserRole.MEMBER,
        )
        self.admin_user = User.objects.create_user(
            user_id="2021999999",
            password="adminpass",
            name="Admin User",
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.member1 = Member.objects.create(
            user=self.user1,
            name="Member One",
            voice_part="T1",
            tier="一队",
            graduate_month="2025-06",
        )
        self.member2 = Member.objects.create(
            user=self.user2,
            name="Member Two",
            voice_part="S1",
            tier="二队",
            graduate_month="2025-06",
        )
        self.client = APIClient()

    def avatar_url(self, member: Member) -> str:
        return f"/api/v1/members/{member.public_id}/avatar/"

    def test_member_can_upload_own_avatar(self):
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            self.avatar_url(self.member1),
            {"avatar": build_avatar_upload()},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200, response.json())
        data = response.json()["data"]
        self.assertIn("/api/v1/common/media/", data["avatar"])
        self.member1.refresh_from_db()
        self.assertTrue(self.member1.avatar.name.startswith("members/avatars/"))
        self.assertTrue(
            os.path.exists(os.path.join(self.media_root, self.member1.avatar.name))
        )

    def test_member_can_delete_own_avatar(self):
        self.client.force_authenticate(user=self.user1)
        upload_response = self.client.post(
            self.avatar_url(self.member1),
            {"avatar": build_avatar_upload()},
            format="multipart",
        )
        self.assertEqual(upload_response.status_code, 200, upload_response.json())
        self.member1.refresh_from_db()
        old_name = self.member1.avatar.name
        old_path = os.path.join(self.media_root, old_name)
        self.assertTrue(os.path.exists(old_path))

        response = self.client.delete(self.avatar_url(self.member1))

        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["data"]["avatar"], "")
        self.member1.refresh_from_db()
        self.assertFalse(self.member1.avatar)
        self.assertFalse(os.path.exists(old_path))

    def test_member_cannot_upload_other_avatar(self):
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            self.avatar_url(self.member2),
            {"avatar": build_avatar_upload()},
            format="multipart",
        )

        self.assertEqual(response.status_code, 403)
        self.member2.refresh_from_db()
        self.assertFalse(self.member2.avatar)

    def test_admin_can_upload_member_avatar(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            self.avatar_url(self.member1),
            {"avatar": build_avatar_upload()},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200, response.json())
        self.member1.refresh_from_db()
        self.assertTrue(self.member1.avatar)

    def test_invalid_avatar_is_rejected(self):
        self.client.force_authenticate(user=self.user1)
        upload = SimpleUploadedFile(
            "avatar.png", b"not an image", content_type="image/png"
        )

        response = self.client.post(
            self.avatar_url(self.member1), {"avatar": upload}, format="multipart"
        )

        self.assertEqual(response.status_code, 422)
        self.member1.refresh_from_db()
        self.assertFalse(self.member1.avatar)
