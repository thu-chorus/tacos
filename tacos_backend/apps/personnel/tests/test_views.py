from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from apps.authentication.models import UserRole
from apps.personnel.models import Member, MemberStatus


class PersonnelViewsTest(TestCase):
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

    def test_member_create_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        payload = {
            "user_id": "20210001",
            "name": "李华",
            "gender": "女",
            "voice_part": "S1",
            "department": "000 建筑学院",
            "class_name": "计15",
            "phone_number": "13812345678",
            "email": "alice@example.com",
            "dorm": "1-101",
            "birthday": "2000-01-01",
            "hometown": "北京",
            "ethnicity": "汉族",
            "political_status": "共青团员",
            "political_affiliation": "艺术团",
            "is_specialty": False,
            "is_centralized": False,
            "position": "队员",
            "graduate_month": "2025-06",
            "tier": "二队",
            "portfolio": "档案",
        }
        res = self.client.post("/api/v1/members/", payload, format="json")
        self.assertEqual(res.status_code, 201)

        res_list = self.client.get("/api/v1/members/?voice_part=S1")
        self.assertEqual(res_list.status_code, 200)
        self.assertGreaterEqual(res_list.json()["data"]["count"], 1)

    def test_admin_member_create_allows_missing_graduate_month(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        payload = {
            "user_id": "20210001",
            "name": "李华",
            "gender": "女",
            "voice_part": "S1",
            "department": "000 建筑学院",
            "class_name": "计15",
            "phone_number": "13812345678",
            "email": "alice@example.com",
            "dorm": "1-101",
            "birthday": "2000-01-01",
            "hometown": "北京",
            "ethnicity": "汉族",
            "political_status": "共青团员",
            "political_affiliation": "艺术团",
            "is_specialty": False,
            "is_centralized": False,
            "position": "队员",
            "tier": "二队",
            "portfolio": "档案",
        }

        res = self.client.post("/api/v1/members/", payload, format="json")

        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["data"]["graduate_month"], "")

    def test_member_list_orders_by_status_first(self):
        User = get_user_model()
        active_user = User.objects.create_user(
            user_id="20230001", password="pass", name="Active"
        )
        alumni_user = User.objects.create_user(
            user_id="20190001", password="pass", name="Alumni"
        )
        inactive_user = User.objects.create_user(
            user_id="20180001", password="pass", name="Inactive"
        )
        Member.objects.create(
            user=active_user,
            name="Active",
            voice_part="B2",
            wechat_id="wx",
            phone_number="13812345001",
            tier="二队",
            status=MemberStatus.ACTIVE,
        )
        Member.objects.create(
            user=alumni_user,
            name="Alumni",
            voice_part="S1",
            wechat_id="wx",
            phone_number="13812345002",
            tier="一队",
            status=MemberStatus.ALUMNI,
        )
        Member.objects.create(
            user=inactive_user,
            name="Inactive",
            voice_part="S1",
            wechat_id="wx",
            phone_number="13812345003",
            tier="一队",
            status=MemberStatus.INACTIVE,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.get("/api/v1/members/?page_size=10")
        self.assertEqual(response.status_code, 200)
        statuses = [item["status"] for item in response.json()["data"]["results"][:3]]
        self.assertEqual(
            statuses,
            [MemberStatus.ACTIVE, MemberStatus.ALUMNI, MemberStatus.INACTIVE],
        )

    def test_member_bulk_template_and_import(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        tpl_res = self.client.get("/api/v1/members/bulk-template/")
        self.assertEqual(tpl_res.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            tpl_res.headers.get("Content-Type", ""),
        )

        csv_content = (
            "user_id,name,gender,wechat_id,voice_part,department,class_name,phone_number,email,dorm,birthday,hometown,ethnicity,political_status,political_affiliation,is_specialty,is_centralized,position,join_month,graduate_month,tier,portfolio\n"
            "20220002,Bob,男,wx_bob,T1,CS,计16,13812345679,bob@example.com,1-102,2001-02-02,北京,汉族,共青团员,艺术团,否,否,队员,2022-09,2026-06,二队,档案\n"
            "20220003,,男,wx_empty,T2,CS,计16,13812345670,empty@example.com,1-103,2001-03-03,北京,汉族,共青团员,艺术团,否,否,队员,2022-09,2026-06,二队,档案\n"
        ).encode("utf-8")
        upload = SimpleUploadedFile("members.csv", csv_content, content_type="text/csv")
        import_res = self.client.post("/api/v1/members/bulk-import/", {"file": upload})
        self.assertEqual(import_res.status_code, 200)
        data = (
            import_res.json()["data"]
            if "data" in import_res.json()
            else import_res.json()
        )
        self.assertEqual(data.get("success"), 1)
        self.assertEqual(data.get("failed"), 1)

    def test_instructor_admin_only(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        res_bad = self.client.post(
            "/api/v1/instructors/",
            {
                "instructor_id": "110101199001011234",
                "name": "李老师",
                "phone_number": "13912345678",
            },
            format="json",
        )
        self.assertIn(res_bad.status_code, (401, 403))

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        res_ok = self.client.post(
            "/api/v1/instructors/",
            {
                "instructor_id": "110101199001011234",
                "name": "李老师",
                "phone_number": "13912345678",
            },
            format="json",
        )
        self.assertEqual(res_ok.status_code, 201)
