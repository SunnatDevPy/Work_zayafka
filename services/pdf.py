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

# ── Palette ──────────────────────────────────────────────────────────
_NAVY      = colors.HexColor("#1a2f4e")
_BLUE      = colors.HexColor("#2563eb")
_BLUE_SOFT = colors.HexColor("#3b82f6")
_BLUE_PALE = colors.HexColor("#eff6ff")
_BLUE_LINE = colors.HexColor("#bfdbfe")
_TEXT      = colors.HexColor("#1e293b")
_MUTED     = colors.HexColor("#64748b")
_BORDER    = colors.HexColor("#e2e8f0")
_WHITE     = colors.white
_GREY_BG   = colors.HexColor("#f8fafc")


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
    candidates: list[tuple[Path, str, Path]] = []
    if platform.system() == "Windows":
        d = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        candidates = [
            (d / "arial.ttf",  "AppFont", d / "arialbd.ttf"),
            (d / "Arial.ttf",  "AppFont", d / "Arialbd.ttf"),
        ]
    else:
        candidates = [
            (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
             "AppFont",
             Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
            (Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
             "AppFont",
             Path("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf")),
        ]
    for reg_path, name, bold_path in candidates:
        if reg_path.is_file():
            pdfmetrics.registerFont(TTFont(name, str(reg_path)))
            if Path(str(bold_path)).is_file():
                pdfmetrics.registerFont(TTFont(name + "Bold", str(bold_path)))
                pdfmetrics.registerFontFamily(
                    name, normal=name, bold=name + "Bold",
                    italic=name, boldItalic=name + "Bold",
                )
                return name, name + "Bold"
            return name, name
    return "Helvetica", "Helvetica-Bold"


def _p(text: str, font: str, size: float, color=None,
       align=TA_LEFT, leading: float | None = None) -> Paragraph:
    return Paragraph(
        text,
        ParagraphStyle(
            "x",
            fontName=font,
            fontSize=size,
            leading=leading or (size * 1.35),
            textColor=color or _TEXT,
            alignment=align,
            spaceAfter=0,
            spaceBefore=0,
        ),
    )


# ── Header ───────────────────────────────────────────────────────────

def _header_block(vacancy_title: str, applicant_label: str,
                  font: str, bold: str, content_width: float) -> Table:
    date_str = datetime.now().strftime("%d.%m.%Y")

    top_row = Table(
        [[
            _p(f"<b>{escape(vacancy_title)}</b>", bold, 16, _WHITE, TA_LEFT, leading=20),
            _p(date_str, font, 8, colors.HexColor("#93c5fd"), TA_RIGHT, leading=12),
        ]],
        colWidths=[content_width * 0.80, content_width * 0.20],
    )
    top_row.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    sub = _p(escape(applicant_label), font, 8,
             colors.HexColor("#bfdbfe"), TA_LEFT, leading=11)

    inner = Table(
        [[top_row], [Spacer(1, 0.15 * cm)], [sub]],
        colWidths=[content_width],
    )
    inner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _NAVY),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LINEBELOW",     (0, -1), (-1, -1), 3, _BLUE_SOFT),
    ]))
    return inner


# ── Photo block ──────────────────────────────────────────────────────

def _photo_block(image_path: str | None, font: str, inner_width: float) -> list:
    if image_path and os.path.isfile(image_path):
        usable = _prepare_image(image_path)
        if usable:
            try:
                max_w = min(inner_width, 10 * cm)
                img = RLImage(usable, width=max_w)
                t = Table([[img]], colWidths=[inner_width])
                t.setStyle(TableStyle([
                    ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                    ("BACKGROUND",    (0, 0), (-1, -1), _WHITE),
                    ("BOX",           (0, 0), (-1, -1), 0.5, _BORDER),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
                    ("TOPPADDING",    (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                return [t]
            except Exception as exc:
                logger.warning("PDF rasm yuklashda xato: %s", exc)

    ph = _p("[ rasm yuborilmadi ]", font, 8, _MUTED, TA_CENTER)
    t = Table([[ph]], colWidths=[inner_width])
    t.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND",    (0, 0), (-1, -1), _GREY_BG),
        ("BOX",           (0, 0), (-1, -1), 0.4, _BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [t]


# ── Question card ────────────────────────────────────────────────────

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
    inner_w = content_width - 22   # card left padding (10) + accent bar (4) + right (8)
    ans_w   = inner_w - 16         # answer box inner padding

    # ── Number + question ──
    num = _p(f"<b>{index}</b>", bold, 8, _BLUE, TA_CENTER, leading=10)
    num_cell = Table([[num]], colWidths=[0.7 * cm])
    num_cell.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _BLUE_PALE),
        ("BOX",           (0, 0), (-1, -1), 0.5, _BLUE_LINE),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))

    q_text = _p(f"<b>{escape(question)}</b>", bold, 9, _TEXT, TA_LEFT, leading=12)
    q_row = Table(
        [[num_cell, q_text]],
        colWidths=[0.7 * cm, inner_w - 0.7 * cm - 4],
    )
    q_row.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 1), (0, 1),   4),
    ]))

    rows: list = [[q_row]]

    # ── Photo (above answer) ──
    if require_photo:
        rows.append([Spacer(1, 0.15 * cm)])
        for bit in _photo_block(image_path, font, inner_w):
            rows.append([bit])

    # ── Answer ──
    rows.append([Spacer(1, 0.12 * cm)])

    ans_txt = (answer_text or "").strip() or "—"
    ans_p = _p(
        escape(ans_txt).replace("\n", "<br/>"),
        font, 9, _TEXT if ans_txt != "—" else _MUTED,
        TA_LEFT, leading=12,
    )
    ans_box = Table([[ans_p]], colWidths=[ans_w])
    ans_box.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _WHITE),
        ("BOX",           (0, 0), (-1, -1), 0.4, _BORDER),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    rows.append([ans_box])

    card = Table(rows, colWidths=[inner_w])
    card.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _WHITE),
        ("BOX",           (0, 0), (-1, -1), 0.5, _BORDER),
        ("LINEBEFORE",    (0, 0), (0, -1),  3, _BLUE),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return card


# ── Footer ───────────────────────────────────────────────────────────

def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(_MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        A4[0] / 2,
        0.9 * cm,
        f"Telegram bot orqali to'ldirildi  •  {datetime.now().strftime('%d.%m.%Y %H:%M')}",
    )
    canvas.setStrokeColor(_BORDER)
    canvas.setLineWidth(0.4)
    canvas.line(2 * cm, 1.1 * cm, A4[0] - 2 * cm, 1.1 * cm)
    canvas.restoreState()


# ── Main builder ─────────────────────────────────────────────────────

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

    content_w = A4[0] - 3.6 * cm  # left 1.8 + right 1.8

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.8 * cm,
    )
    story: list = []

    story.append(_header_block(vacancy_title, applicant_label, font, bold, content_w))
    story.append(Spacer(1, 0.35 * cm))

    hint = _p(
        f"Jami {len(items)} ta savol  •  Anketa Telegram bot orqali to'ldirildi",
        font, 7.5, _MUTED, TA_LEFT, leading=10,
    )
    story.append(hint)
    story.append(Spacer(1, 0.25 * cm))

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
        story.append(Spacer(1, 0.22 * cm))

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
