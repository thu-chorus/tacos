from io import BytesIO
from unittest.mock import patch

from django.test import SimpleTestCase

from pypdf import PdfReader, PdfWriter

from apps.sheet_music import watermark


class WatermarkPdfGeometryTest(SimpleTestCase):
    def _write_pdf(self, writer):
        buffer = BytesIO()
        writer.write(buffer)
        return buffer.getvalue()

    def test_watermark_uses_crop_box_for_trimmed_pages(self):
        writer = PdfWriter()
        page = writer.add_blank_page(width=500, height=700)
        page.cropbox.lower_left = (50, 100)
        page.cropbox.upper_right = (350, 600)

        with patch(
            "apps.sheet_music.watermark._build_overlay",
            wraps=watermark._build_overlay,
        ) as build_overlay:
            output = watermark.add_text_watermark_to_pdf(
                self._write_pdf(writer),
                "Test",
                font_size=24,
            )

        self.assertEqual(build_overlay.call_count, 1)
        width, height = build_overlay.call_args.args[:2]
        self.assertAlmostEqual(width, 300)
        self.assertAlmostEqual(height, 500)

        result_page = PdfReader(BytesIO(output)).pages[0]
        self.assertEqual(result_page.rotation, 0)
        self.assertAlmostEqual(float(result_page.cropbox.left), 50)
        self.assertAlmostEqual(float(result_page.cropbox.bottom), 100)

    def test_watermark_normalizes_rotated_page_before_overlay(self):
        writer = PdfWriter()
        page = writer.add_blank_page(width=400, height=600)
        page.cropbox.lower_left = (50, 100)
        page.cropbox.upper_right = (350, 500)
        page.rotate(90)

        with patch(
            "apps.sheet_music.watermark._build_overlay",
            wraps=watermark._build_overlay,
        ) as build_overlay:
            output = watermark.add_text_watermark_to_pdf(
                self._write_pdf(writer),
                "Test",
                font_size=24,
            )

        self.assertEqual(build_overlay.call_count, 1)
        width, height = build_overlay.call_args.args[:2]
        self.assertAlmostEqual(width, 400)
        self.assertAlmostEqual(height, 300)

        result_page = PdfReader(BytesIO(output)).pages[0]
        self.assertEqual(result_page.rotation, 0)
        self.assertAlmostEqual(float(result_page.cropbox.width), 400)
        self.assertAlmostEqual(float(result_page.cropbox.height), 300)

    def test_watermark_uses_trim_box_when_crop_box_is_default(self):
        writer = PdfWriter()
        page = writer.add_blank_page(width=400, height=600)
        page.trimbox.lower_left = (25, 50)
        page.trimbox.upper_right = (375, 550)

        with patch(
            "apps.sheet_music.watermark._build_overlay",
            wraps=watermark._build_overlay,
        ) as build_overlay:
            output = watermark.add_text_watermark_to_pdf(
                self._write_pdf(writer),
                "Test",
                font_size=24,
            )

        self.assertEqual(build_overlay.call_count, 1)
        width, height = build_overlay.call_args.args[:2]
        self.assertAlmostEqual(width, 350)
        self.assertAlmostEqual(height, 500)

        result_page = PdfReader(BytesIO(output)).pages[0]
        self.assertEqual(result_page.rotation, 0)
        self.assertAlmostEqual(float(result_page.trimbox.left), 25)
        self.assertAlmostEqual(float(result_page.trimbox.bottom), 50)
