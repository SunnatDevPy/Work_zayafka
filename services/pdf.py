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
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

_MAX_IMG_BYTES = 8 * 1024 * 1024
_MAX_IMG_DIM   = 2400

# ──────────────── Color palette ────────────────
_C_PRIMARY  = colors.HexColor("#1a365d")   # deep navy
_C_ACCENT   = colors.HexColor("#2b6cb0")   # blue
_C_ACCENT2  = colors.HexColor("#3182ce")   # lighter blue
_C_BG       = colors.HexColor("#f7fafc")   # very light grey
_C_BG_CARD  = colors.HexColor("#ffffff")   # white card
_C_BORDER   = colors.HexColor("#e2e8f0")
_C_TEXT     = colors.HexColor("#2d3748")   # dark grey text
_C_MUTED    = colors.HexColor("#718096")
_C_NUM_BG   = colors.HexColor("#ebf8ff")   # light blue badge bg
_C_HEADER   = colors.HexColor("#1e3a5f")


def _prepare_image(path: str) -> str | None:
    try:
        from PIL import Image
        size = os.path.getsize(path)
        with Image.open(path) as im:
            w, h = im.size
            if w <= _MAX_IMG_DIM and h <= _MAX_IMG_DIM and size <= _MAX_IMG_BYTES:
                return path
            im.thumbnail((_MAX_IMG_DIM, _MAX_IMG_DIM), Image.LANCZOS)
            im.convert("RGB").save(path, "JPEG", quality=85)
        return path
    except Exception as exc:
        logger.warning("Rasm tayyorlashda xato: %s", exc)
        return None


def _fonts() -> tuple[str, str]:
    regular = bold = None
    candidates: list[tuple[Path, str, str]] = []
    if platform.system() == "Windows":
        d = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        candidates = [
            (d / "arial.ttf",   "AppFont",     d / "arialbd.ttf"),
            (d / "Arial.ttf",   "AppFont",     d / "Arialbd.ttf"),
        ]
    else:
        candidates = [
            (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),      "AppFont",
             Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
            (Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),                  "AppFont",
             Path("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf")),
        ]
    for reg_path, name, bold_path in candidates:
        if reg_path.is_file():
            pdfmetrics.registerFont(TTFont(name, str(reg_path)))
            regular = name
            if Path(str(bold_path)).is_file():
                pdfmetrics.registerFont(TTFont(name + "Bold", str(bold_path)))
                bold = name + "Bold"
                pdfmetrics.registerFontFamily(name, normal=name, bold=name + "Bold",
                                              italic=name, boldItalic=name + "Bold")
            else:
                bold = name
            break
    return regular or "Helvetica", bold or "Helvetica-Bold"


def _p(text: str, font: str, size: int, color=None, align=TA_LEFT, leading=None) -> Paragraph:
    return Paragraph(
        text,
        ParagraphStyle(
            "p",
            fontName=font,
            fontSize=size,
            leading=leading or size + 4,
            textColor=color or _C_TEXT,
            alignment=align,
            spaceAfter=0,
            spaceBefore=0,
        ),
    )


# ──────────────── Header block ────────────────

def _header_block(vacancy_title: str, applicant_label: str, font: str, bold: str, content_width: float) -> Table:
    date_str = datetime.now().strftime("%d.%m.%Y")

    title_row = Table(
        [[
            _p(f"<b>{escape(vacancy_title)}</b>", bold, 20, _C_BG, TA_LEFT, leading=24),
            _p(date_str, font, 9, colors.HexColor("#a0c4e8"), TA_RIGHT, leading=13),
        ]],
        colWidths=[content_width * 0.78, content_width * 0.22],
    )
    title_row.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))

    sub = _p(escape(applicant_label), font, 10, colors.HexColor("#cfe8f7"), TA_LEFT, leading=14)

    inner = Table(
        [[title_row], [Spacer(1, 0.25 * cm)], [sub]],
        colWidths=[content_width],
    )
    inner.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), _C_HEADER),
        ("LEFTPADDING",  (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING",   (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 16),
        ("LINEBELOW",    (0, -1), (-1, -1), 4, _C_ACCENT2),
    ]))
    return inner


# ──────────────── Photo block ────────────────

def _photo_block(image_path: str | None, font: str, content_width: float) -> list:
    inner_w = max(content_width - 24, 6 * cm)

    if image_path and os.path.isfile(image_path):
        usable = _prepare_image(image_path)
        if usable:
            try:
                img = RLImage(usable, width=min(inner_w, 13 * cm))
                t = Table([[img]], colWidths=[content_width - 24])
                t.setStyle(TableStyle([
                    ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                    ("BACKGROUND",   (0, 0), (-1, -1), colors.white),
                    ("BOX",          (0, 0), (-1, -1), 0.5, _C_BORDER),
                    ("LEFTPADDING",  (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING",   (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
                ]))
                return [t]
            except Exception as exc:
                logger.warning("PDF rasm yuklashda xato: %s", exc)

    # Placeholder
    ph = _p("[ Rasm yuborilmadi ]", font, 10, _C_MUTED, TA_CENTER, leading=13)
    t = Table([[Spacer(1, 0.3 * cm)], [ph], [Spacer(1, 0.3 * cm)]], colWidths=[content_width - 24])
    t.setStyle(TableStyle([
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND",  (0, 0), (-1, -1), _C_BG),
        ("BOX",         (0, 0), (-1, -1), 0.5, _C_BORDER),
    ]))
    return [t]


# ──────────────── Question card ────────────────

def _question_card(
    index: int,
    question: str,
    answer_text: str | None,
    image_path: str | None,
    require_photo: bool,
    font: str,
    bold: str,
    content_width: float,
) -> Table:

    # ── Number badge + question text ──
    num_cell  = _p(f"<b>{index}</b>", bold, 13, _C_ACCENT, TA_CENTER, leading=17)
    q_cell    = _p(escape(question), font, 11, _C_TEXT, TA_LEFT, leading=15)
    num_w     = 0.9 * cm
    q_header  = Table([[num_cell, q_cell]], colWidths=[num_w, content_width - 28 - num_w])
    q_header.setStyle(TableStyle([
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND",     (0, 0), (0, 0),  _C_NUM_BG),
        ("BOX",            (0, 0), (0, 0),  0.5, _C_ACCENT),
        ("LEFTPADDING",    (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 4),
        ("TOPPADDING",     (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
    ]))

    rows: list = [[q_header], [Spacer(1, 0.2 * cm)]]

    # ── Photo FIRST (above answer) ──
    if require_photo:
        label = _p("<b>Rasm</b>", bold, 9, _C_ACCENT, TA_LEFT)
        rows.append([label])
        rows.append([Spacer(1, 0.08 * cm)])
        for bit in _photo_block(image_path, font, content_width - 28):
            rows.append([bit])
        rows.append([Spacer(1, 0.18 * cm)])

    # ── Answer text ──
    ans_label = _p("<b>Javob</b>", bold, 9, _C_ACCENT, TA_LEFT)
    if answer_text and answer_text.strip():
        ans_body = _p(
            escape(answer_text).replace("\n", "<br/>"),
            font, 10, _C_TEXT, TA_LEFT, leading=14,
        )
        ans_inner = Table([[ans_body]], colWidths=[content_width - 52])
        ans_inner.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), colors.white),
            ("BOX",          (0, 0), (-1, -1), 0.5, _C_BORDER),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING",   (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ]))
    else:
        ans_body = _p("—", font, 10, _C_MUTED, TA_LEFT)
        ans_inner = Table([[ans_body]], colWidths=[content_width - 52])
        ans_inner.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), colors.white),
            ("BOX",          (0, 0), (-1, -1), 0.5, _C_BORDER),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING",   (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ]))

    rows.append([ans_label])
    rows.append([Spacer(1, 0.06 * cm)])
    rows.append([ans_inner])

    card = Table(rows, colWidths=[content_width - 24])
    card.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), _C_BG_CARD),
        ("BOX",          (0, 0), (-1, -1), 0.75, _C_BORDER),
        ("LINEBEFORE",   (0, 0), (0, -1),  4,    _C_ACCENT),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
    ]))
    return card


# ──────────────── Footer canvas ────────────────

def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(_C_MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawCentredString(
        A4[0] / 2,
        1.1 * cm,
        f"Telegram bot orqali to'ldirildi  •  {datetime.now().strftime('%d.%m.%Y %H:%M')}",
    )
    canvas.setStrokeColor(_C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.35 * cm, A4[0] - 2 * cm, 1.35 * cm)
    canvas.restoreState()


# ──────────────── Main builder ────────────────

def build_application_pdf(
    *,
    vacancy_title: str,
    applicant_label: str,
    items: list[dict],
    out_path: str | None = None,
) -> str:
    font, bold = _fonts()

    if out_path is None:
        fd, out_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

    content_w = A4[0] - 4 * cm

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.4 * cm,
        bottomMargin=2 * cm,
    )
    story: list = []

    # Header
    story.append(_header_block(vacancy_title, applicant_label, font, bold, content_w))
    story.append(Spacer(1, 0.5 * cm))

    # Hint
    hint = _p(
        "Anketa Telegram-bot orqali to'ldirildi. Quyida har bir savol bo'yicha javoblar.",
        font, 8, _C_MUTED, TA_LEFT, leading=11,
    )
    story.append(hint)
    story.append(Spacer(1, 0.4 * cm))

    # Question cards
    for i, row in enumerate(items, start=1):
        card = _question_card(
            index=i,
            question=row.get("question") or "",
            answer_text=row.get("answer_text"),
            image_path=row.get("image_path"),
            require_photo=bool(row.get("require_photo")),
            font=font,
            bold=bold,
            content_width=content_w,
        )
        story.append(KeepTogether([card]))
        story.append(Spacer(1, 0.4 * cm))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
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
