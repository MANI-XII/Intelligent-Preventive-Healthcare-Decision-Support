from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas


PAGE_WIDTH, PAGE_HEIGHT = letter
LEFT_MARGIN = 54
RIGHT_MARGIN = 54
TOP_MARGIN = 54
BOTTOM_MARGIN = 54
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

TITLE_COLOR = colors.HexColor("#0F766E")
ACCENT_COLOR = colors.HexColor("#14B8A6")
TEXT_DARK = colors.HexColor("#0F172A")
TEXT_MUTED = colors.HexColor("#475569")
CARD_BG = colors.HexColor("#F8FAFC")
CARD_BORDER = colors.HexColor("#CBD5E1")
GOOD_COLOR = colors.HexColor("#15803D")
WARNING_COLOR = colors.HexColor("#B45309")
HIGH_COLOR = colors.HexColor("#B91C1C")


def _draw_watermark(c: canvas.Canvas, width: float, height: float) -> None:
    """Draw a subtle healthcare-themed watermark in the page background."""
    c.saveState()
    if hasattr(c, "setFillAlpha"):
        c.setFillAlpha(0.08)
    c.translate(width - 150, height - 170)
    c.setStrokeColor(ACCENT_COLOR)
    c.setFillColor(ACCENT_COLOR)
    c.setLineWidth(10)
    c.circle(0, 0, 44, stroke=1, fill=0)
    c.roundRect(-10, -34, 20, 68, 4, stroke=0, fill=1)
    c.roundRect(-34, -10, 68, 20, 4, stroke=0, fill=1)
    c.restoreState()


def _draw_header(c: canvas.Canvas, user_id: str, generated_at: datetime) -> float:
    c.setFillColor(colors.white)
    c.roundRect(LEFT_MARGIN, PAGE_HEIGHT - 155, CONTENT_WIDTH, 105, 18, stroke=0, fill=1)

    c.setFillColor(TITLE_COLOR)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 88, "Preventive Health Report")

    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 11)
    c.drawCentredString(
        PAGE_WIDTH / 2,
        PAGE_HEIGHT - 107,
        "Personalized summary of risk levels, health signals, and next steps",
    )

    meta_y = PAGE_HEIGHT - 137
    c.setFillColor(TEXT_DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(LEFT_MARGIN + 20, meta_y, "PATIENT")
    c.drawString(PAGE_WIDTH / 2 + 10, meta_y, "GENERATED")

    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(LEFT_MARGIN + 20, meta_y - 15, user_id)
    c.drawString(
        PAGE_WIDTH / 2 + 10,
        meta_y - 15,
        generated_at.strftime("%d %b %Y, %I:%M %p UTC"),
    )
    return PAGE_HEIGHT - 180


def _draw_section_title(c: canvas.Canvas, y: float, title: str) -> float:
    c.setFillColor(TEXT_DARK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(LEFT_MARGIN, y, title)
    c.setStrokeColor(CARD_BORDER)
    c.setLineWidth(1)
    c.line(LEFT_MARGIN, y - 8, PAGE_WIDTH - RIGHT_MARGIN, y - 8)
    return y - 24


def _risk_color(label: str) -> colors.Color:
    lower = (label or "").strip().lower()
    if any(word in lower for word in ["low", "good", "normal"]):
        return GOOD_COLOR
    if any(word in lower for word in ["moderate", "warning", "elevated"]):
        return WARNING_COLOR
    return HIGH_COLOR


def _draw_metric_card(
    c: canvas.Canvas,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    value: str,
    tone: colors.Color | None = None,
) -> None:
    c.setFillColor(CARD_BG)
    c.setStrokeColor(CARD_BORDER)
    c.roundRect(x, y - height, width, height, 14, stroke=1, fill=1)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(x + 14, y - 20, title.upper())

    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(tone or TEXT_DARK)
    c.drawString(x + 14, y - 44, value)


def _draw_detail_rows(c: canvas.Canvas, y: float, rows: list[tuple[str, str]]) -> float:
    row_height = 28
    box_height = row_height * len(rows) + 12
    c.setFillColor(colors.white)
    c.setStrokeColor(CARD_BORDER)
    c.roundRect(LEFT_MARGIN, y - box_height, CONTENT_WIDTH, box_height, 14, stroke=1, fill=1)

    current_y = y - 22
    for idx, (label, value) in enumerate(rows):
        if idx:
            c.setStrokeColor(colors.HexColor("#E2E8F0"))
            c.line(LEFT_MARGIN + 16, current_y + 8, PAGE_WIDTH - RIGHT_MARGIN - 16, current_y + 8)
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(TEXT_DARK)
        c.drawString(LEFT_MARGIN + 18, current_y - 2, label)
        c.setFont("Helvetica", 11)
        c.setFillColor(TEXT_MUTED)
        c.drawRightString(PAGE_WIDTH - RIGHT_MARGIN - 18, current_y - 2, value)
        current_y -= row_height
    return y - box_height - 18


def _draw_recommendations(c: canvas.Canvas, y: float, recommendations: list[str]) -> float:
    c.setFillColor(colors.white)
    c.setStrokeColor(CARD_BORDER)
    c.roundRect(LEFT_MARGIN, y - 130, CONTENT_WIDTH, 130, 14, stroke=1, fill=1)

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEXT_DARK)
    c.drawString(LEFT_MARGIN + 18, y - 22, "Recommended next steps")

    c.setFont("Helvetica", 10.5)
    c.setFillColor(TEXT_MUTED)
    current_y = y - 44
    items = recommendations or ["No recommendations available."]

    for item in items[:4]:
        wrapped = simpleSplit(item, "Helvetica", 10.5, CONTENT_WIDTH - 48)
        for line_index, line in enumerate(wrapped):
            prefix = "• " if line_index == 0 else "  "
            c.drawString(LEFT_MARGIN + 18, current_y, f"{prefix}{line}")
            current_y -= 14
            if current_y < y - 112:
                break
        if current_y < y - 112:
            break
        current_y -= 4

    return y - 148


def render_preventive_report_pdf(
    *,
    user_id: str,
    generated_at: datetime,
    prediction: dict,
) -> bytes:
    """Generate a polished single-page preventive health PDF report."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    c.setFillColor(colors.HexColor("#ECFEFF"))
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    _draw_watermark(c, PAGE_WIDTH, PAGE_HEIGHT)

    y = _draw_header(c, user_id, generated_at)

    diabetes_risk = prediction.get("diabetes_risk_prob", prediction.get("diabetes_risk")) or 0
    diabetes_level = prediction.get("risk_level", prediction.get("diabetes_risk_level")) or "Unknown"
    heart_level = prediction.get("heart_risk", prediction.get("heart_risk_level")) or "Unknown"
    bmi_status = prediction.get("bmi_status", prediction.get("rule_based", {}).get("bmi_status")) or "Unknown"
    overall_score = prediction.get("overall_health_score")
    overall_score_text = "N/A" if overall_score is None else str(overall_score)

    y = _draw_section_title(c, y, "Report Summary")

    card_gap = 12
    card_width = (CONTENT_WIDTH - card_gap) / 2
    top_row_y = y
    _draw_metric_card(
        c,
        x=LEFT_MARGIN,
        y=top_row_y,
        width=card_width,
        height=64,
        title="Diabetes Risk",
        value=f"{float(diabetes_risk) * 100:.0f}%",
        tone=_risk_color(diabetes_level),
    )
    _draw_metric_card(
        c,
        x=LEFT_MARGIN + card_width + card_gap,
        y=top_row_y,
        width=card_width,
        height=64,
        title="Overall Health Score",
        value=overall_score_text,
        tone=TITLE_COLOR,
    )

    second_row_y = top_row_y - 78
    _draw_metric_card(
        c,
        x=LEFT_MARGIN,
        y=second_row_y,
        width=card_width,
        height=64,
        title="Diabetes Risk Level",
        value=diabetes_level,
        tone=_risk_color(diabetes_level),
    )
    _draw_metric_card(
        c,
        x=LEFT_MARGIN + card_width + card_gap,
        y=second_row_y,
        width=card_width,
        height=64,
        title="Heart Risk Level",
        value=heart_level,
        tone=_risk_color(heart_level),
    )

    y = second_row_y - 84
    detail_rows = [
        ("Body Mass Index Status", str(bmi_status)),
        ("Report Type", "Preventive risk assessment"),
        ("Prepared For", user_id),
        ("Generated On", generated_at.strftime("%d %b %Y at %I:%M %p UTC")),
    ]
    y = _draw_detail_rows(c, y, detail_rows)

    y = _draw_section_title(c, y, "Recommendations")
    _draw_recommendations(c, y, prediction.get("recommendations", []) or [])

    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT_MUTED)
    c.drawCentredString(
        PAGE_WIDTH / 2,
        BOTTOM_MARGIN - 8,
        "This report is intended for wellness support and should not replace professional medical advice.",
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
