from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.core.locale import pdf_decision_label, pdf_message, pdf_report_name
from apps.core.markdown_lite import is_markdown_heading, is_skippable_markdown_line, markdown_to_reportlab

# Identité visuelle SecureFlow
BRAND_PRIMARY = colors.HexColor("#7C3AED")  # violet
BRAND_ACCENT = colors.HexColor("#3B82F6")  # bleu
INK = colors.HexColor("#1E293B")
MUTED = colors.HexColor("#64748B")
HAIRLINE = colors.HexColor("#E2E8F0")
SUMMARY_BG = colors.HexColor("#F5F3FF")


def _score_color(score: int | float | None) -> colors.Color:
    if score is None:
        return colors.HexColor("#64748B")
    value = float(score)
    if value >= 80:
        return colors.HexColor("#10B981")
    if value >= 60:
        return colors.HexColor("#F59E0B")
    return colors.HexColor("#EF4444")


def _decision_color(decision: str) -> colors.Color:
    mapping = {
        "CRITIQUE": colors.HexColor("#EF4444"),
        "CORRIGER": colors.HexColor("#F97316"),
        "SURVEILLER": colors.HexColor("#EAB308"),
        "PROPRE": colors.HexColor("#10B981"),
    }
    return mapping.get((decision or "").upper(), colors.HexColor("#64748B"))


def _decision_badge(decision: str, label: str | None = None) -> Table:
    """Pastille colorée pour le verdict."""
    text = label or decision or "N/A"
    color = _decision_color(decision)
    style = ParagraphStyle(
        "Badge",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.white,
        alignment=TA_CENTER,
    )
    badge = Table(
        [[Paragraph(text.upper(), style)]],
        colWidths=[5.5 * cm],
        rowHeights=[0.85 * cm],
    )
    badge.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ]
        )
    )
    return badge


def _score_bar(security_score: int | float | None, *, label: str, na_text: str) -> Table:
    """Barre de score /100 colorée."""
    bar_width = 14 * cm
    fill_ratio = min(max(float(security_score or 0) / 100.0, 0.0), 1.0)
    score_display = f"{int(security_score)}/100" if security_score is not None else "N/A"
    head_style = ParagraphStyle(
        "ScoreHead", fontName="Helvetica-Bold", fontSize=13, leading=18, textColor=INK
    )
    track = Table(
        [[""]],
        colWidths=[bar_width],
        rowHeights=[0.5 * cm],
        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), HAIRLINE)]),
    )
    if fill_ratio > 0:
        fill = Table(
            [[""]],
            colWidths=[bar_width * fill_ratio],
            rowHeights=[0.5 * cm],
            style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), _score_color(security_score))]),
        )
        bar_cell: Any = fill
    else:
        bar_cell = Paragraph(na_text, head_style)
    return Table(
        [
            [Paragraph(f"<b>{label}</b> : {score_display}", head_style)],
            [bar_cell if fill_ratio > 0 else track],
        ],
        colWidths=[bar_width],
    )


def _summary_flowables(summary: dict[str, Any] | None) -> list:
    """Encadré « Résumé exécutif » clair et textuel (PDF)."""
    if not summary:
        return []

    title_style = ParagraphStyle(
        "SumTitle", fontName="Helvetica-Bold", fontSize=15, leading=20, textColor=BRAND_PRIMARY
    )
    line_style = ParagraphStyle("SumLine", fontName="Helvetica", fontSize=12, leading=17, textColor=INK)
    label_style = ParagraphStyle(
        "SumLabel", fontName="Helvetica-Bold", fontSize=12, leading=17, textColor=MUTED
    )
    bullet_style = ParagraphStyle(
        "SumBullet", fontName="Helvetica", fontSize=12, leading=17, textColor=INK, leftIndent=10
    )

    inner: list = [Paragraph(summary["title"], title_style), Spacer(1, 0.25 * cm)]

    meta = Table(
        [
            [Paragraph(summary["verdict_label"], label_style), Paragraph(summary["verdict"], line_style)],
            [Paragraph(summary["score_label"], label_style), Paragraph(summary["score"], line_style)],
            [Paragraph(summary["agents_label"], label_style), Paragraph(str(summary["agents"]), line_style)],
            [Paragraph(summary["project_label"], label_style), Paragraph(str(summary["project"]), line_style)],
        ],
        colWidths=[4 * cm, 9.5 * cm],
    )
    meta.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    inner.append(meta)
    inner.append(Spacer(1, 0.25 * cm))

    inner.append(Paragraph(summary["takeaways_label"], label_style))
    for point in summary["takeaways"]:
        inner.append(Paragraph(f"• {point}", bullet_style))
    inner.append(Spacer(1, 0.2 * cm))
    inner.append(
        Paragraph(f"<b>{summary['recommendation_label']} :</b> {summary['recommendation']}", line_style)
    )

    box = Table([[inner]], colWidths=[14.5 * cm])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SUMMARY_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, HAIRLINE),
                ("LINEBEFORE", (0, 0), (0, -1), 3, BRAND_PRIMARY),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return [box]


def _append_report_lines(story: list, report_text: str, *, heading_style, body_style) -> None:
    for line in (report_text or "").split("\n"):
        stripped = line.strip()
        if not stripped or is_skippable_markdown_line(stripped):
            continue
        converted = markdown_to_reportlab(line)
        if not converted:
            continue
        style = heading_style if is_markdown_heading(stripped) else body_style
        story.append(Paragraph(converted, style))
        story.append(Spacer(1, 6))


def _disagreement_flowables(disagreement: dict[str, Any] | None) -> list:
    """Encadré « Désaccord détecté » (PDF)."""
    if not disagreement:
        return []
    warn = colors.HexColor("#F97316")
    title_style = ParagraphStyle(
        "DisTitle", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=warn
    )
    line_style = ParagraphStyle("DisLine", fontName="Helvetica", fontSize=12, leading=17, textColor=INK)
    label_style = ParagraphStyle(
        "DisLabel", fontName="Helvetica-Bold", fontSize=12, leading=17, textColor=MUTED
    )

    inner: list = [Paragraph(f"⚠ {disagreement['title']}", title_style), Spacer(1, 0.2 * cm)]
    rows = [
        [Paragraph(str(agent), label_style), Paragraph(str(val), line_style)]
        for agent, val in disagreement["rows"]
    ]
    if disagreement.get("spread"):
        rows.append(
            [Paragraph(disagreement["spread_label"], label_style), Paragraph(disagreement["spread"], line_style)]
        )
    table = Table(rows, colWidths=[5 * cm, 8.5 * cm])
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    inner.append(table)
    inner.append(Spacer(1, 0.15 * cm))
    inner.append(Paragraph(disagreement["note"], line_style))

    box = Table([[inner]], colWidths=[14.5 * cm])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF7ED")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FED7AA")),
                ("LINEBEFORE", (0, 0), (0, -1), 3, warn),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return [box]


def generate_audit_pdf(
    title: str,
    report_text: str,
    audit_id: str,
    *,
    decision: str | None = None,
    decision_label: str | None = None,
    security_score: int | float | None = None,
    summary: dict[str, Any] | None = None,
    meta_rows: list[tuple[str, str]] | None = None,
    disagreement: dict[str, Any] | None = None,
    locale: str = "fr",
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title=f"SecureFlow — {audit_id}",
    )
    styles = getSampleStyleSheet()
    en = locale == "en"

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=30,
        leading=36,
        textColor=BRAND_PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=0.2 * cm,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=14,
        leading=19,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=0.6 * cm,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=15,
        leading=20,
        textColor=BRAND_PRIMARY,
        spaceBefore=0.5 * cm,
        spaceAfter=0.25 * cm,
    )
    body_style = ParagraphStyle(
        "AuditBody", parent=styles["Normal"], fontSize=12, leading=17, textColor=INK
    )
    meta_label_style = ParagraphStyle(
        "MetaLabel", fontName="Helvetica-Bold", fontSize=11, leading=16, textColor=MUTED
    )
    meta_value_style = ParagraphStyle(
        "MetaValue", fontName="Helvetica", fontSize=11, leading=16, textColor=INK
    )

    story: list = []
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("SecureFlow AI", title_style))
    story.append(Paragraph(title, subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT))
    story.append(Spacer(1, 0.4 * cm))

    rows = [(f"ID {'audit' if en else 'audit'}", audit_id)]
    rows.extend(meta_rows or [])
    meta_table = Table(
        [[Paragraph(k, meta_label_style), Paragraph(str(v), meta_value_style)] for k, v in rows],
        colWidths=[3.6 * cm, 10.9 * cm],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 0.35 * cm))

    if decision:
        story.append(_decision_badge(decision, decision_label))
        story.append(Spacer(1, 0.35 * cm))
    if security_score is not None:
        story.append(
            _score_bar(
                security_score,
                label="Security score" if en else "Score de sécurité",
                na_text="N/A",
            )
        )
        story.append(Spacer(1, 0.4 * cm))

    # Résumé exécutif en tête pour une lecture immédiate
    summary_box = _summary_flowables(summary)
    if summary_box:
        story.extend(summary_box)
        story.append(Spacer(1, 0.6 * cm))

    disagreement_box = _disagreement_flowables(disagreement)
    if disagreement_box:
        story.extend(disagreement_box)
        story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Detailed results" if en else "Résultats détaillés", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HAIRLINE))
    story.append(Spacer(1, 0.25 * cm))
    _append_report_lines(story, report_text, heading_style=heading_style, body_style=body_style)

    # Rappel du résumé en fin de document
    if summary_box:
        story.append(Spacer(1, 0.6 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HAIRLINE))
        story.append(Spacer(1, 0.3 * cm))
        story.extend(_summary_flowables(summary))

    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HAIRLINE))
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=MUTED,
        alignment=TA_CENTER,
    )
    story.append(
        Paragraph(
            f"Généré par SecureFlow AI · Band of Agents Hackathon 2026 · {audit_id}",
            footer_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()


def generate_mode_c_pdf(
    *,
    audit_id: str,
    decision: str,
    security_score: int | float | None,
    report_text: str,
    metrics_text: str,
    session_date: str,
    locale: str = "fr",
    ingestion: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
    disagreement: dict[str, Any] | None = None,
) -> bytes:
    """PDF professionnel Mode C — page de couverture, jauge score, rapport structuré."""
    lang = locale or "fr"
    report_name = pdf_report_name(audit_id, lang)
    decision_display = pdf_decision_label(decision, lang)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"SecureFlow — {audit_id}",
    )
    styles = getSampleStyleSheet()

    brand = BRAND_PRIMARY
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=34,
        leading=40,
        textColor=brand,
        alignment=TA_CENTER,
        spaceAfter=0.4 * cm,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontSize=16,
        leading=22,
        textColor=colors.HexColor("#475569"),
        alignment=TA_CENTER,
        spaceAfter=0.8 * cm,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=17,
        leading=22,
        textColor=brand,
        spaceBefore=0.6 * cm,
        spaceAfter=0.25 * cm,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#334155"),
        alignment=TA_LEFT,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=12,
        leading=17,
        textColor=colors.HexColor("#1e293b"),
    )

    story: list = []
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph("SecureFlow AI", title_style))
    story.append(Paragraph(pdf_message("subtitle", lang), subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=brand))
    story.append(Spacer(1, 0.6 * cm))

    score_display = f"{int(security_score)}/100" if security_score is not None else "N/A"
    score_bar_width = 14 * cm
    fill_ratio = min(max(float(security_score or 0) / 100.0, 0.0), 1.0)
    score_label = pdf_message("security_score", lang)
    score_table = Table(
        [
            [Paragraph(f"<b>{score_label}</b> : {score_display}", meta_style)],
            [
                Table(
                    [[""]],
                    colWidths=[score_bar_width * fill_ratio],
                    rowHeights=[0.55 * cm],
                    style=TableStyle(
                        [("BACKGROUND", (0, 0), (-1, -1), _score_color(security_score))]
                    ),
                )
                if fill_ratio > 0
                else Paragraph(pdf_message("score_not_calculated", lang), meta_style)
            ],
        ],
        colWidths=[score_bar_width],
    )
    story.append(score_table)
    story.append(Spacer(1, 0.5 * cm))

    decision_style = ParagraphStyle(
        "Decision",
        parent=meta_style,
        textColor=_decision_color(decision),
        fontSize=15,
        leading=20,
    )
    meta_rows = [
        [pdf_message("field_report", lang), report_name],
        [pdf_message("field_id", lang), audit_id],
        [pdf_message("field_date", lang), session_date],
        [pdf_message("field_decision", lang), decision_display],
    ]

    meta_table = Table(meta_rows, colWidths=[3.2 * cm, 11 * cm])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 13),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#64748B")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 0.3 * cm))
    final_decision = pdf_message("final_decision", lang)
    story.append(
        Paragraph(f"<b>{final_decision} :</b> {decision_display}", decision_style)
    )
    story.append(Spacer(1, 0.6 * cm))

    summary_box = _summary_flowables(summary)
    if summary_box:
        story.extend(summary_box)
        story.append(Spacer(1, 0.6 * cm))

    disagreement_box = _disagreement_flowables(disagreement)
    if disagreement_box:
        story.extend(disagreement_box)
        story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph(pdf_message("professional_report", lang), section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1")))
    story.append(Spacer(1, 0.2 * cm))
    _append_report_lines(story, report_text, heading_style=section_style, body_style=body_style)

    if metrics_text.strip():
        story.append(Paragraph(pdf_message("metrics_appendix", lang), section_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1")))
        story.append(Spacer(1, 0.2 * cm))
        _append_report_lines(story, metrics_text, heading_style=section_style, body_style=body_style)

    if summary_box:
        story.append(Spacer(1, 0.8 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HAIRLINE))
        story.append(Spacer(1, 0.3 * cm))
        story.extend(_summary_flowables(summary))

    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    footer_style = ParagraphStyle(
        "FooterC",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    story.append(
        Paragraph(
            pdf_message("footer_confidential", lang, audit_id=audit_id),
            footer_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()
