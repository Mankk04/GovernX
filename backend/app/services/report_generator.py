"""
Compliance Report Generator (Section 10, Module 5).

Assembles a board-ready PDF using ReportLab, pulling the latest maturity
scores and top financial risks for an organization.
"""
import os
from datetime import datetime
from typing import List, Dict

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "generated_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def generate_compliance_pdf(
    org_name: str,
    org_id: str,
    maturity_scores: List[Dict],
    top_findings: List[Dict],
    total_value_at_risk: float,
) -> str:
    filename = f"governx_report_{org_id}_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], textColor=colors.HexColor("#1a3d7c"))

    doc = SimpleDocTemplate(filepath, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    story = []

    story.append(Paragraph("GovernX — NIST CSF 2.0 Compliance Report", title_style))
    story.append(Paragraph(f"Organization: {org_name}", styles["Normal"]))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph(
        f"<b>Total Value at Risk: ${total_value_at_risk:,.2f}</b>", styles["Heading2"]
    ))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Maturity Profile by NIST CSF 2.0 Function", styles["Heading2"]))
    score_table_data = [["Function", "Tier (1-4)"]] + [
        [s["function_name"], str(s["tier_level"])] for s in maturity_scores
    ]
    score_table = Table(score_table_data, colWidths=[3 * inch, 2 * inch])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3d7c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f3fa")]),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("Top Financial Risk Findings", styles["Heading2"]))
    finding_table_data = [["Resource", "Subcategory", "Severity", "Value at Risk"]] + [
        [f["resource"], f["subcategory"], f["severity"] or "-", f"${f['value_at_risk']:,.2f}"]
        for f in top_findings
    ]
    finding_table = Table(finding_table_data, colWidths=[1.8 * inch, 1.3 * inch, 1 * inch, 1.5 * inch])
    finding_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3d7c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f3fa")]),
    ]))
    story.append(finding_table)
    story.append(Spacer(1, 0.4 * inch))

    story.append(Paragraph(
        "This report was generated automatically by GovernX from live cloud "
        "configuration telemetry mapped to NIST CSF 2.0 and quantified via "
        "Monte Carlo simulation. See the GovernX Executive Dashboard for "
        "real-time data.",
        styles["Italic"],
    ))

    doc.build(story)
    return filepath
