"""Report generation in PDF (ReportLab) and Excel (XlsxWriter)."""
from __future__ import annotations

import io

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def build_pdf_report(
    title: str, summary: str, quality: dict, insights: list[dict]
) -> bytes:
    """Render an executive PDF report and return its bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=title)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Executive Summary", styles["Heading2"]))
    story.append(Paragraph(summary, styles["BodyText"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Data Quality Overview", styles["Heading2"]))
    metrics = [
        ["Metric", "Value"],
        ["Quality Score", f"{quality.get('quality_score', 0)}/100"],
        ["Total Rows", quality.get("total_rows", 0)],
        ["Total Columns", quality.get("total_columns", 0)],
        ["Missing Values", quality.get("total_missing", 0)],
        ["Duplicate Rows", quality.get("duplicate_rows", 0)],
    ]
    table = Table(metrics, colWidths=[8 * cm, 6 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2ff")]),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Key Insights", styles["Heading2"]))
    for ins in insights:
        story.append(
            Paragraph(
                f"<b>[{ins['severity'].upper()}] {ins['title']}</b>: {ins['detail']}",
                styles["BodyText"],
            )
        )
        story.append(Spacer(1, 0.15 * cm))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def build_excel_report(
    title: str, summary: str, quality: dict, insights: list[dict], df: pd.DataFrame
) -> bytes:
    """Render a multi-sheet Excel workbook and return its bytes."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        wb = writer.book
        header_fmt = wb.add_format(
            {"bold": True, "bg_color": "#4f46e5", "font_color": "white"}
        )

        overview = pd.DataFrame(
            {
                "Metric": [
                    "Title", "Quality Score", "Total Rows",
                    "Total Columns", "Missing Values", "Duplicate Rows",
                ],
                "Value": [
                    title,
                    quality.get("quality_score", 0),
                    quality.get("total_rows", 0),
                    quality.get("total_columns", 0),
                    quality.get("total_missing", 0),
                    quality.get("duplicate_rows", 0),
                ],
            }
        )
        overview.to_excel(writer, sheet_name="Overview", index=False)

        pd.DataFrame({"Executive Summary": [summary]}).to_excel(
            writer, sheet_name="Summary", index=False
        )

        if insights:
            pd.DataFrame(insights).to_excel(
                writer, sheet_name="Insights", index=False
            )

        cols = pd.DataFrame(quality.get("columns", []))
        if not cols.empty:
            cols.to_excel(writer, sheet_name="Column Profiles", index=False)

        df.head(1000).to_excel(writer, sheet_name="Data Sample", index=False)

        for sheet in writer.sheets.values():
            sheet.set_row(0, None, header_fmt)
            sheet.set_column(0, 20, 22)

    buffer.seek(0)
    return buffer.getvalue()
