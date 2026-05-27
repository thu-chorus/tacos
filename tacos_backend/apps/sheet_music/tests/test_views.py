import shutil
import tempfile
from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from pypdf import PdfWriter
from rest_framework.test import APIClient

from apps.sheet_music.constants import WATERMARK_CACHE_VERSION
from apps.sheet_music.models import Sheet, SheetDownloadLog, SheetDownloadTask


class SheetViewsTest(TestCase):
    def setUp(self):
        self._media_root = tempfile.mkdtemp()
        self._media_override = override_settings(MEDIA_ROOT=self._media_root)
        self._media_override.enable()
        self.addCleanup(shutil.rmtree, self._media_root, ignore_errors=True)
        self.addCleanup(self._media_override.disable)

        self.client = APIClient()
        User = get_user_model()
        self.admin = User.objects.create_user(
            user_id="admin1", password="adminpass", name="Admin", is_staff=True
        )
        res = self.client.post(
            "/api/v1/auth/login",
            {"user_id": "admin1", "password": "adminpass"},
            format="json",
        )
        self.token = res.json()["data"]["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def _upload_sheet(self):
        pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
        upload = SimpleUploadedFile(
            "test.pdf", pdf_bytes, content_type="application/pdf"
        )
        payload = {
            "title": "测试曲目",
            "lyricist": "词作者",
            "composer": "曲作者",
            "arranger": "编曲",
            "introduction": "简介",
            "original_file": upload,
        }
        res = self.client.post("/api/v1/sheets/", data=payload)
        self.assertEqual(res.status_code, 201)
        return res.json()["data"]["id"]

    def _valid_pdf_bytes(self, page_count=2):
        writer = PdfWriter()
        for _ in range(page_count):
            writer.add_blank_page(width=400, height=600)
        buffer = BytesIO()
        writer.write(buffer)
        return buffer.getvalue()

    def test_upload_and_download_pdf(self):
        sheet_id = self._upload_sheet()

        with patch("apps.sheet_music.views.generate_watermarked_pdf_task.delay"):
            res_dl = self.client.post(f"/api/v1/sheets/{sheet_id}/download/")
        self.assertEqual(res_dl.status_code, 202)
        self.assertIn("task_id", res_dl.json()["data"])
        self.assertIn("stream_url", res_dl.json()["data"])

    def test_preview_task_does_not_create_download_log(self):
        sheet_id = self._upload_sheet()

        with patch("apps.sheet_music.views.generate_watermarked_pdf_task.delay"):
            res = self.client.post(f"/api/v1/sheets/{sheet_id}/download/?preview=true")

        self.assertEqual(res.status_code, 202)
        self.assertIn("task_id", res.json()["data"])
        self.assertIn("stream_url", res.json()["data"])
        self.assertEqual(SheetDownloadLog.objects.count(), 0)

    def test_download_reuses_recent_preview_task(self):
        sheet_id = self._upload_sheet()

        with patch(
            "apps.sheet_music.views.generate_watermarked_pdf_task.delay"
        ) as delay:
            preview_res = self.client.post(
                f"/api/v1/sheets/{sheet_id}/download/?preview=true"
            )
            download_res = self.client.post(f"/api/v1/sheets/{sheet_id}/download/")

        self.assertEqual(preview_res.status_code, 202)
        self.assertEqual(download_res.status_code, 202)
        self.assertEqual(
            preview_res.json()["data"]["task_id"],
            download_res.json()["data"]["task_id"],
        )
        delay.assert_called_once()
        self.assertEqual(SheetDownloadTask.objects.count(), 1)
        self.assertEqual(SheetDownloadLog.objects.count(), 1)

    def test_status_only_returns_json_with_stream_url(self):
        sheet_id = self._upload_sheet()

        with patch("apps.sheet_music.views.generate_watermarked_pdf_task.delay"):
            preview_res = self.client.post(
                f"/api/v1/sheets/{sheet_id}/download/?preview=true"
            )

        task_id = preview_res.json()["data"]["task_id"]
        status_res = self.client.get(f"/api/v1/sheets/task/{task_id}/?status_only=true")

        self.assertEqual(status_res.status_code, 200)
        data = status_res.json()["data"]
        self.assertEqual(data["status"], "PENDING")
        self.assertIn("stream_url", data)

    def test_download_reuses_completed_cached_task(self):
        sheet_id = self._upload_sheet()
        sheet = Sheet.objects.get(public_id=sheet_id)
        cached_task = SheetDownloadTask.objects.create(
            task_id="cached-task",
            sheet=sheet,
            user=self.admin,
            status="COMPLETED",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        cached_task.result_file.save(
            f"{WATERMARK_CACHE_VERSION}_cached.pdf",
            ContentFile(self._valid_pdf_bytes()),
            save=True,
        )

        with patch(
            "apps.sheet_music.views.generate_watermarked_pdf_task.delay"
        ) as delay:
            res = self.client.post(f"/api/v1/sheets/{sheet_id}/download/")

        self.assertEqual(res.status_code, 202)
        self.assertEqual(res.json()["data"]["task_id"], cached_task.task_id)
        delay.assert_not_called()
        self.assertEqual(SheetDownloadTask.objects.count(), 1)
        self.assertEqual(SheetDownloadLog.objects.count(), 1)

    def test_stream_url_serves_completed_pdf_with_range_support(self):
        sheet_id = self._upload_sheet()
        sheet = Sheet.objects.get(public_id=sheet_id)
        cached_task = SheetDownloadTask.objects.create(
            task_id="cached-stream-task",
            sheet=sheet,
            user=self.admin,
            status="COMPLETED",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        cached_task.result_file.save(
            f"{WATERMARK_CACHE_VERSION}_stream.pdf",
            ContentFile(self._valid_pdf_bytes()),
            save=True,
        )

        res = self.client.post(f"/api/v1/sheets/{sheet_id}/download/?preview=true")
        stream_url = res.json()["data"]["stream_url"]

        stream_res = self.client.get(stream_url)
        self.assertEqual(stream_res.status_code, 200)
        self.assertEqual(stream_res["Content-Type"], "application/pdf")
        self.assertEqual(stream_res["Accept-Ranges"], "bytes")
        self.assertIn("inline", stream_res["Content-Disposition"])
        self.assertNotIn("X-Frame-Options", stream_res)

        range_res = self.client.get(stream_url, HTTP_RANGE="bytes=0-15")
        self.assertEqual(range_res.status_code, 206)
        self.assertEqual(range_res["Accept-Ranges"], "bytes")
        self.assertTrue(range_res["Content-Range"].startswith("bytes 0-15/"))

    def test_download_ignores_cached_task_from_old_watermark_version(self):
        sheet_id = self._upload_sheet()
        sheet = Sheet.objects.get(public_id=sheet_id)
        old_cached_task = SheetDownloadTask.objects.create(
            task_id="old-cached-task",
            sheet=sheet,
            user=self.admin,
            status="COMPLETED",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        old_cached_task.result_file.save(
            "old_cached.pdf",
            ContentFile(b"%PDF-1.4\n%%EOF"),
            save=True,
        )

        with patch(
            "apps.sheet_music.views.generate_watermarked_pdf_task.delay"
        ) as delay:
            res = self.client.post(f"/api/v1/sheets/{sheet_id}/download/")

        self.assertEqual(res.status_code, 202)
        self.assertNotEqual(res.json()["data"]["task_id"], old_cached_task.task_id)
        delay.assert_called_once()
        self.assertEqual(SheetDownloadTask.objects.count(), 2)
        self.assertEqual(SheetDownloadLog.objects.count(), 1)
