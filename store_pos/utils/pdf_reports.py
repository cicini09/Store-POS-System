"""PDF export helpers using ReportLab."""

from __future__ import annotations

from datetime import datetime

from ..config import REPORTS_DIR, STORE_NAME


def generate_inventory_pdf(rows) -> str:
    """Generate and return the path to the inventory report PDF."""
    filename = REPORTS_DIR / f"products_report_{_timestamp()}.pdf"
    data = [["Product", "Category", "Price", "On Hand", "Units Sold"]]
    for row in rows:
        data.append([row[0], row[1], f"PHP {row[2]:,.2f}", str(row[3]), str(row[4])])
    _build_pdf(filename, f"{STORE_NAME} Products Report", data)
    return str(filename)


def generate_orders_pdf(rows) -> str:
    """Generate and return the path to the orders report PDF."""
    filename = REPORTS_DIR / f"orders_report_{_timestamp()}.pdf"
    data = [["Order ID", "Customer", "Email", "Date", "Total", "Email Sent"]]
    total_amount = 0.0
    for row in rows:
        total_amount += float(row[4])
        data.append([str(row[0]), row[1], row[2], row[3], f"PHP {row[4]:,.2f}", row[5]])
    data.append(["", "", "", "Grand Total", f"PHP {total_amount:,.2f}", ""])
    _build_pdf(filename, f"{STORE_NAME} Orders Report", data)
    return str(filename)


def _build_pdf(path, title: str, table_data: list[list[str]]) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError(
            "ReportLab is not installed. Run 'pip install -r requirements.txt' to enable PDF exports."
        ) from exc

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(path), pagesize=A4)
    styles = getSampleStyleSheet()

    title_paragraph = Paragraph(title, styles["Heading1"])
    timestamp = Paragraph(
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Normal"],
    )
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A56A0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ("ALIGN", (2, 1), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ]
        )
    )

    document.build([title_paragraph, Spacer(1, 10), timestamp, Spacer(1, 12), table])


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
