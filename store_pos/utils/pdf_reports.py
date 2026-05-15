"""PDF export helpers using ReportLab — polished, branded reports."""

from __future__ import annotations

from datetime import datetime

from ..config import REPORTS_DIR, STORE_NAME


def generate_inventory_pdf(rows) -> str:
    """Generate a polished inventory report PDF with summary statistics."""
    filename = REPORTS_DIR / f"products_report_{_timestamp()}.pdf"

    # Compute summary stats
    total_products = len(rows)
    total_stock = sum(int(row[3]) for row in rows)
    total_sold = sum(int(row[4]) for row in rows)
    total_value = sum(float(row[2]) * int(row[3]) for row in rows)
    categories = len(set(row[1] for row in rows if row[1]))

    summary = [
        ("Total Products", str(total_products)),
        ("Categories", str(categories)),
        ("Total Stock On Hand", f"{total_stock:,}"),
        ("Total Units Sold", f"{total_sold:,}"),
        ("Inventory Value", f"PHP {total_value:,.2f}"),
    ]

    data = [["#", "Product", "Category", "Unit Price", "On Hand", "Units Sold", "Stock Value"]]
    for idx, row in enumerate(rows, 1):
        stock_val = float(row[2]) * int(row[3])
        data.append([
            str(idx),
            row[0],
            row[1] or "Uncategorized",
            f"PHP {row[2]:,.2f}",
            str(row[3]),
            str(row[4]),
            f"PHP {stock_val:,.2f}",
        ])
    # Totals row
    data.append(["", "", "TOTALS", f"—", str(total_stock), str(total_sold), f"PHP {total_value:,.2f}"])

    col_widths = [30, 160, 100, 90, 70, 80, 100]
    _build_pdf(
        filename,
        f"{STORE_NAME} — Products Inventory Report",
        data,
        summary=summary,
        col_widths=col_widths,
        has_totals_row=True,
    )
    return str(filename)


def generate_orders_pdf(rows) -> str:
    """Generate a polished orders report PDF with summary statistics."""
    filename = REPORTS_DIR / f"orders_report_{_timestamp()}.pdf"

    # Compute summary stats
    total_orders = len(rows)
    total_revenue = sum(float(row[5]) for row in rows)
    total_units = sum(int(row[8]) for row in rows)
    receipts_sent = sum(1 for row in rows if row[6] == "Sent")
    unique_customers = len(set(row[1] for row in rows))

    summary = [
        ("Total Orders", str(total_orders)),
        ("Unique Customers", str(unique_customers)),
        ("Total Units Sold", f"{total_units:,}"),
        ("Total Revenue", f"PHP {total_revenue:,.2f}"),
        ("Receipts Sent", f"{receipts_sent}/{total_orders}"),
    ]

    data = [["#", "Order ID", "Customer", "Items", "Units", "Total", "Date", "Receipt"]]
    for idx, row in enumerate(rows, 1):
        data.append([
            str(idx),
            str(row[0]),
            row[1],
            row[9][:40] + ("..." if len(row[9]) > 40 else ""),
            str(row[8]),
            f"PHP {row[5]:,.2f}",
            row[4],
            row[6],
        ])
    # Grand total row
    data.append(["", "", "", "", str(total_units), f"PHP {total_revenue:,.2f}", "GRAND TOTAL", ""])

    col_widths = [25, 55, 120, 180, 45, 90, 130, 55]
    _build_pdf(
        filename,
        f"{STORE_NAME} — Orders Report",
        data,
        summary=summary,
        col_widths=col_widths,
        has_totals_row=True,
    )
    return str(filename)


def _build_pdf(
    path,
    title: str,
    table_data: list[list[str]],
    summary: list[tuple[str, str]] | None = None,
    col_widths: list[int] | None = None,
    has_totals_row: bool = False,
) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exc:
        raise RuntimeError(
            "ReportLab is not installed. Run 'pip install -r requirements.txt' to enable PDF exports."
        ) from exc

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Colors
    primary = colors.HexColor("#1E40AF")
    primary_light = colors.HexColor("#DBEAFE")
    dark_text = colors.HexColor("#1E293B")
    muted_text = colors.HexColor("#64748B")
    border_color = colors.HexColor("#CBD5E1")
    row_alt = colors.HexColor("#F8FAFC")
    white = colors.white

    page_size = landscape(A4)
    document = SimpleDocTemplate(
        str(path),
        pagesize=page_size,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # --- Report Header ---
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=dark_text,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=muted_text,
        spaceAfter=6,
    )

    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} &bull; {STORE_NAME}",
        subtitle_style,
    ))
    elements.append(Spacer(1, 6))

    # --- Separator line ---
    separator_data = [["" for _ in range(5)]]
    separator = Table(separator_data, colWidths=[page_size[0] - 40 * mm])
    separator.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 1, border_color),
        ("TOPPADDING", (0, 0), (-1, 0), 0),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
    ]))
    elements.append(separator)
    elements.append(Spacer(1, 10))

    # --- Summary Statistics ---
    if summary:
        summary_data = [[label for label, _ in summary], [value for _, value in summary]]
        summary_table = Table(summary_data, colWidths=[130] * len(summary))
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_light),
            ("TEXTCOLOR", (0, 0), (-1, 0), muted_text),
            ("TEXTCOLOR", (0, 1), (-1, 1), dark_text),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, 1), 11),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("TOPPADDING", (0, 1), (-1, 1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
            ("BOX", (0, 0), (-1, -1), 0.5, border_color),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, border_color),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 16))

    # --- Main Data Table ---
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_commands = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), primary),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        # Body rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("TEXTCOLOR", (0, 1), (-1, -1), dark_text),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.4, border_color),
        # Alternating row backgrounds
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, row_alt]),
        # Alignment
        ("ALIGN", (0, 0), (0, -1), "CENTER"),  # Row number column centered
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    # Style the totals row distinctly
    if has_totals_row:
        last_row = len(table_data) - 1
        style_commands.extend([
            ("BACKGROUND", (0, last_row), (-1, last_row), primary_light),
            ("FONTNAME", (0, last_row), (-1, last_row), "Helvetica-Bold"),
            ("FONTSIZE", (0, last_row), (-1, last_row), 9),
            ("TEXTCOLOR", (0, last_row), (-1, last_row), primary),
            ("LINEABOVE", (0, last_row), (-1, last_row), 1.2, primary),
            ("TOPPADDING", (0, last_row), (-1, last_row), 10),
            ("BOTTOMPADDING", (0, last_row), (-1, last_row), 10),
        ])

    table.setStyle(TableStyle(style_commands))
    elements.append(table)

    # --- Footer note ---
    elements.append(Spacer(1, 16))
    footer_style = ParagraphStyle(
        "FooterNote",
        parent=styles["Normal"],
        fontSize=8,
        textColor=muted_text,
        alignment=1,  # center
    )
    elements.append(Paragraph(
        f"— End of Report — | {STORE_NAME} Point of Sale System | Page generated automatically",
        footer_style,
    ))

    document.build(elements)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
