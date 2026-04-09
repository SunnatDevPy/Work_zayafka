import logging
import os
import platform
import tempfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)

logger = logging.getLogger(__name__)

_MAX_IMG_BYTES = 8 * 1024 * 1024
_MAX_IMG_DIM   = 2400

# 🎨 Colors
_NAVY = colors.HexColor("#1a2f4e")
_BLUE = colors.HexColor("#2563eb")
_TEXT = colors.HexColor("#1e293b")
_MUTED = colors.HexColor("#64748b")
_BORDER = colors.HexColor("#e2e8f0")
_WHITE = colors.white
_BG = colors.HexColor("#f8fafc")


# 📸 Image optimize
def _prepare_image(path: str):
    try:
        from PIL import Image
        with Image.open(path) as im:
            im.thumbnail((_MAX_IMG_DIM, _MAX_IMG_DIM))
            im.convert("RGB").save(path, "JPEG", quality=85)
        return path
    except:
        return None


# 🔤 Fonts
def _fonts():
    if platform.system() == "Windows":
        path = Path("C:/Windows/Fonts/arial.ttf")
        bold = Path("C:/Windows/Fonts/arialbd.ttf")
    else:
        path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

    if path.exists():
        pdfmetrics.registerFont(TTFont("AppFont", str(path)))
        pdfmetrics.registerFont(TTFont("AppFontBold", str(bold)))
        return "AppFont", "AppFontBold"

    return "Helvetica", "Helvetica-Bold"


# 📝 Text
def _p(text, font, size, color=_TEXT, align=TA_LEFT):
    return Paragraph(
        text,
        ParagraphStyle(
            "x",
            fontName=font,
            fontSize=size,
            leading=size * 1.4,
            textColor=color,
            alignment=align,
            wordWrap="CJK",
        ),
    )


# 📄 Header (applicant_line — ФИО / @username / id, показывается под названием)
def _header(title, applicant_line, font, bold):
    date_cell = _p(datetime.now().strftime("%d.%m.%Y"), font, 9, _WHITE, TA_RIGHT)
    rows = [[_p(f"<b>{escape(title)}</b>", bold, 16, _WHITE), date_cell]]
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, -1), _NAVY),
        ("TEXTCOLOR", (0, 0), (-1, -1), _WHITE),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]
    if applicant_line and str(applicant_line).strip():
        rows.append(
            [
                _p(f"<b>{escape(str(applicant_line).strip())}</b>", font, 11, _WHITE, TA_LEFT),
                Spacer(1, 1),
            ]
        )
        style_cmds.append(("SPAN", (0, 1), (1, 1)))
    return Table(rows, colWidths=[350, 100], style=style_cmds)


# 📸 Photo
def _photo(path, width, max_height=8 * cm):
    if path and os.path.exists(path):
        path = _prepare_image(path)
        try:
            img = RLImage(path)
            img._restrictSize(width, max_height)
            return img
        except:
            pass
    return _p("<i>Фото нет</i>", "Helvetica", 8, _MUTED, TA_CENTER)


# 📦 Card
def _card(i, q, a, img_path, font, bold, width):
    elements = []

    elements.append(_p(f"<b>{i}. {escape(q)}</b>", bold, 10))
    elements.append(Spacer(1, 5))

    if img_path:
        elements.append(_photo(img_path, width))
        elements.append(Spacer(1, 5))

    answer = a.strip() if a else "—"
    elements.append(_p(escape(answer).replace("\n", "<br/>"), font, 9))

    return Table([[elements]], colWidths=[width],
        style=[
            ("BACKGROUND", (0,0), (-1,-1), _BG),
            ("BOX", (0,0), (-1,-1), 0.5, _BORDER),
            ("PADDING", (0,0), (-1,-1), 8),
        ]
    )


# 🧾 Main
def build_application_pdf(vacancy_title, applicant_label, items, out_path=None):
    font, bold = _fonts()

    if not out_path:
        fd, out_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=1.5*cm,
        bottomMargin=2*cm,
    )

    story = []

    # Header
    story.append(_header(vacancy_title, applicant_label, font, bold))
    story.append(Spacer(1, 10))

    # Info
    story.append(_p(f"Всего вопросов: {len(items)}", font, 8, _MUTED))
    story.append(Spacer(1, 10))

    # Cards
    for i, row in enumerate(items, 1):
        story.append(_card(
            i,
            row.get("question", ""),
            row.get("answer_text", ""),
            row.get("image_path"),
            font,
            bold,
            450
        ))
        story.append(Spacer(1, 10))

        if i % 4 == 0:
            story.append(PageBreak())

    doc.build(story)

    return out_path
def build_fake_pdf(*, out_path: str | None = None) -> str:
    items = [
        {"question": "F.I.Sh., telefon, elektron pochta",
         "answer_text": "Karimov Jamshid\n+998 90 000-00-00\njamshid@example.com",
         "image_path": None, "require_photo": False},
        {"question": "Hujjat yoki selfi rasmini yuboring",
         "answer_text": "Rasm izohi ixtiyoriy.",
         "image_path": None, "require_photo": True},
        {"question": "Qo'shimcha izohlar",
         "answer_text": "Bu namuna PDF.",
         "image_path": None, "require_photo": False},
    ]
    return build_application_pdf(
        vacancy_title="Demo: sotuv menejeri",
        applicant_label="@demo_user · Jamshid Karimov · id:123456789",
        items=items,
        out_path=out_path,
    )


def build_candidate_compact_pdf(
    vacancy_title: str,
    applicant_label: str,
    rows: list[tuple[str, str]],
    out_path: str | None = None,
    photo_path: str | None = None,
) -> str:
    font, bold = _fonts()
    if not out_path:
        fd, out_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=1.3 * cm,
        rightMargin=1.3 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
    )

    table_data = [[_p("<b>Поле</b>", bold, 8), _p("<b>Значение</b>", bold, 8)]]
    for key, value in rows:
        safe_val = escape((value or "—").replace("\n", " "))[:380]
        table_data.append([_p(f"<b>{escape(key)}</b>", bold, 7), _p(safe_val, font, 7)])

    story = [_header(vacancy_title, applicant_label, font, bold), Spacer(1, 6)]
    if photo_path and os.path.exists(photo_path):
        pic = _photo(photo_path, 4.2 * cm, max_height=5 * cm)
        story.append(
            Table(
                [[pic]],
                colWidths=[17.3 * cm],
                style=[
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                    ("BOX", (0, 0), (-1, -1), 0.4, _BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ],
            )
        )
        story.append(Spacer(1, 6))
    story.append(
        Table(
            table_data,
            colWidths=[5.3 * cm, 12.0 * cm],
            style=[
                ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf2ff")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ],
        )
    )
    doc.build(story)
    return out_path
