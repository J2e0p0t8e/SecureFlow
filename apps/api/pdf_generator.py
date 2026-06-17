from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER


def generate_audit_pdf(title: str, report_text: str, audit_id: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    styles = getSampleStyleSheet()

    # Styles personnalisés
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
                                  fontSize=24, textColor=colors.HexColor('#00d4aa'),
                                  alignment=TA_CENTER, spaceAfter=0.5*cm)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                     fontSize=11, textColor=colors.grey,
                                     alignment=TA_CENTER, spaceAfter=1*cm)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                    textColor=colors.HexColor('#00d4aa'),
                                    spaceBefore=0.5*cm, spaceAfter=0.3*cm)

    story = []

    # Page de couverture
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("SecureFlow AI", title_style))
    story.append(Paragraph("Rapport d'Audit de Sécurité", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor('#00d4aa')))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"ID d'audit : <b>{audit_id}</b>", styles['Normal']))
    story.append(Spacer(1, 1*cm))

    # Contenu du rapport
    story.append(Paragraph("Résultats de l'analyse", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 0.3*cm))

    for line in report_text.split("\n"):
        if line.strip():
            story.append(Paragraph(line.replace("<", "&lt;"), styles['Normal']))
            story.append(Spacer(1, 6))

    # Pied de page
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
                                   fontSize=8, textColor=colors.grey,
                                   alignment=TA_CENTER)
    story.append(Paragraph(
        f"Généré par SecureFlow AI · Band of Agents Hackathon 2026 · {audit_id}",
        footer_style
    ))

    doc.build(story)
    return buffer.getvalue()