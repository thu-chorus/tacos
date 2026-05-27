from __future__ import annotations

import os
from io import BytesIO
from typing import Iterable, Optional

from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

try:  # 可选支持 Django settings
    from django.conf import settings  # type: ignore
except Exception:  # pragma: no cover
    settings = None  # type: ignore


def _try_register_ttc_font(font_name: str, ttc_path: str) -> Optional[str]:
    """尝试通过 0..9 子字体索引注册 TTC 字体。

    成功时返回已注册字体名，否则返回 None。
    """
    for idx in range(0, 10):
        try:
            pdfmetrics.registerFont(TTFont(font_name, ttc_path, subfontIndex=idx))
            return font_name
        except Exception:
            continue
    return None


def _register_font_if_provided(font_path: Optional[str]) -> str:
    """注册可用的 TTF/TTC 中文字体，并返回使用的字体名。"""
    if "WatermarkFont" in pdfmetrics.getRegisteredFontNames():
        return "WatermarkFont"

    if font_path and os.path.exists(font_path):
        try:
            if font_path.lower().endswith(".ttc"):
                name = _try_register_ttc_font("WatermarkFont", font_path)
                if name:
                    return name
            else:
                pdfmetrics.registerFont(TTFont("WatermarkFont", font_path))
                return "WatermarkFont"
        except Exception:
            pass

    # 回退到内置 CID 字体（不需要外部文件，但不嵌入字体）
    for cid_name in ("STSong-Light", "MSung-Light", "HeiseiKakuGo-W5"):
        try:
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont

            pdfmetrics.registerFont(UnicodeCIDFont(cid_name))
            return cid_name
        except Exception:
            continue

    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Songti.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc",
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            if path.lower().endswith(".ttc"):
                name = _try_register_ttc_font("WatermarkFont", path)
                if name:
                    return name
            else:
                pdfmetrics.registerFont(TTFont("WatermarkFont", path))
                return "WatermarkFont"
        except Exception:
            continue

    return "Helvetica-Bold"


def _build_overlay(
    width: float,
    height: float,
    text_lines: Iterable[str],
    *,
    font_path: Optional[str] = None,
    font_size: int = 0,
    light_gray: float = 0.88,
    opacity: float = 0.08,
) -> BytesIO:
    """创建只包含一条浅色斜向水印的单页 PDF 覆盖层。

    返回已定位到起始位置的 BytesIO。
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(width, height))

    font_name = _register_font_if_provided(font_path)
    c.setFillColor(Color(light_gray, light_gray, light_gray))
    try:  # 部分环境不支持透明度，不可用时忽略
        c.setFillAlpha(opacity)  # type: ignore[attr-defined]
    except Exception:
        pass
    fs = font_size if font_size and font_size > 0 else max(48, min(width, height) / 8.0)
    c.setFont(font_name, fs)

    c.saveState()
    c.translate(width / 2.0, height / 2.0)
    c.rotate(45)
    offset = 0
    for line in text_lines:
        c.drawCentredString(0, offset, line)
        offset -= fs + 6
    c.restoreState()

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def _box_values(box) -> tuple[float, float, float, float]:
    return (
        float(box.left),
        float(box.bottom),
        float(box.right),
        float(box.top),
    )


def _boxes_differ(box, reference, tolerance: float = 0.01) -> bool:
    return any(
        abs(value - ref_value) > tolerance
        for value, ref_value in zip(_box_values(box), _box_values(reference))
    )


def _effective_visible_box(page):
    """返回 PDF 裁剪或修边后用户最可能看到的页面区域。"""
    media_box = page.mediabox
    crop_box = page.cropbox
    if _boxes_differ(crop_box, media_box):
        return crop_box

    if "/TrimBox" in page:
        trim_box = page.trimbox
        if _boxes_differ(trim_box, media_box):
            return trim_box

    return crop_box


def add_text_watermark_to_pdf(
    src_pdf_bytes: bytes,
    text: str,
    *,
    font_path: Optional[str] = None,
    font_size: int = 46,
    light_gray: float = 0.88,
    opacity: float = 0.2,
) -> bytes:
    """为源 PDF 的每一页嵌入文字水印。

    参数：
        src_pdf_bytes: 原始 PDF 字节。
        text: 水印文本，可用 "\n" 分隔多行。

    返回：
        包含水印的新 PDF 字节。
    """
    reader = PdfReader(BytesIO(src_pdf_bytes))
    writer = PdfWriter()

    lines = [line for line in str(text).split("\n") if line.strip()]
    if not lines:
        lines = [text]

    if font_path is None and settings is not None:  # type: ignore[truthy-function]
        font_path = getattr(settings, "WATERMARK_FONT_PATH", None)  # type: ignore[attr-defined]

    overlay_cache = {}
    for page in reader.pages:
        writer.add_page(page)
        out_page = writer.pages[-1]
        if out_page.rotation:
            out_page.transfer_rotation_to_content()

        visible_box = _effective_visible_box(out_page)
        width = float(visible_box.width)
        height = float(visible_box.height)
        overlay_key = (width, height)
        overlay_reader = overlay_cache.get(overlay_key)
        if overlay_reader is None:
            overlay_buf = _build_overlay(
                width,
                height,
                lines,
                font_path=font_path,
                font_size=font_size,
                light_gray=light_gray,
                opacity=opacity,
            )
            overlay_reader = PdfReader(overlay_buf)
            overlay_cache[overlay_key] = overlay_reader
        overlay_page = overlay_reader.pages[0]

        out_page.merge_transformed_page(
            overlay_page,
            Transformation().translate(
                tx=float(visible_box.left),
                ty=float(visible_box.bottom),
            ),
        )

    out_buf = BytesIO()
    writer.write(out_buf)
    out_buf.seek(0)
    return out_buf.getvalue()
