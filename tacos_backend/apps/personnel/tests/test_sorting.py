from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient

from apps.personnel.models import AlumniProfile, Instructor, Member, MemberStatus

User = get_user_model()


def create_member(
    user_id: str,
    name: str,
    *,
    voice_part: str = "Other",
    tier: str = "二队",
    status: str = MemberStatus.ACTIVE,
) -> Member:
    user = User.objects.create_user(user_id=user_id, password="password123", name=name)
    return Member.objects.create(
        user=user,
        name=name,
        voice_part=voice_part,
        tier=tier,
        status=status,
        wechat_id="wx",
        phone_number=f"138{int(user_id[-8:]):08d}",
    )


class InstructorSortingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            user_id="admin-sort",
            password="password123",
            name="Admin",
            is_staff=True,
            role="Admin",
        )
        self.client.force_authenticate(user=self.admin)

    def test_instructors_are_sorted_by_name_then_id(self):
        Instructor.objects.create(
            instructor_id="110101199001011235",
            name="Bravo",
            phone_number="13900000002",
        )
        Instructor.objects.create(
            instructor_id="110101199001011234",
            name="Alpha",
            phone_number="13900000001",
        )
        Instructor.objects.create(
            instructor_id="110101199001011236",
            name="Alpha",
            phone_number="13900000003",
        )

        response = self.client.get("/api/v1/instructors/", {"page_size": 10})
        self.assertEqual(response.status_code, 200, response.json())
        results = response.json()["data"]["results"]
        self.assertEqual(
            [(item["name"], item["instructor_id"]) for item in results],
            [
                ("Alpha", "110101199001011234"),
                ("Alpha", "110101199001011236"),
                ("Bravo", "110101199001011235"),
            ],
        )

    def test_alumni_profiles_use_member_sort_order(self):
        bob = create_member(
            "20262001",
            "Bob",
            voice_part="B2",
            tier="二队",
            status=MemberStatus.ALUMNI,
        )
        alice = create_member(
            "20262002",
            "Alice",
            voice_part="S1",
            tier="一队",
            status=MemberStatus.ALUMNI,
        )
        charlie = create_member(
            "20262003",
            "Charlie",
            voice_part="A1",
            tier="一队",
            status=MemberStatus.ALUMNI,
        )
        for member in (bob, charlie, alice):
            AlumniProfile.objects.get_or_create(member=member)

        response = self.client.get("/api/v1/alumni-profiles/", {"page_size": 10})
        self.assertEqual(response.status_code, 200, response.json())
        names = [item["member_name"] for item in response.json()["data"]["results"]]
        self.assertEqual(names, ["Alice", "Charlie", "Bob"])
