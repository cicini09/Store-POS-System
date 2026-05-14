"""Email receipt utilities."""

from __future__ import annotations

import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage

from ..config import (
    EMAIL_ENABLED,
    EMAIL_LOG_PATH,
    SMTP_FROM_NAME,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_USE_SSL,
    STORE_NAME,
)


def send_receipt(order_data: dict, customer_email: str) -> bool:
    """Send a receipt email when SMTP is configured."""
    if not EMAIL_ENABLED:
        _log_email_event(order_data, customer_email, "EMAIL DISABLED", "Receipt sending is disabled.")
        return True
    if not _smtp_configured():
        _log_email_event(
            order_data,
            customer_email,
            "EMAIL FAILED",
            "SMTP is enabled but credentials are not configured in config.py or environment variables.",
        )
        return False

    message = EmailMessage()
    message["Subject"] = f"{STORE_NAME} Order Receipt #{order_data['order_id']}"
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_USERNAME}>"
    message["To"] = customer_email

    plain_body = _build_plain_body(order_data)
    message.set_content(plain_body)
    message.add_alternative(_build_html_body(order_data), subtype="html")

    try:
        context = ssl.create_default_context()
        if SMTP_USE_SSL:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as smtp:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
                smtp.send_message(message)
        _log_email_event(order_data, customer_email, "EMAIL SENT", "Receipt delivered successfully.")
        return True
    except Exception as exc:
        _log_email_event(order_data, customer_email, "EMAIL FAILED", str(exc))
        return False


def _build_plain_body(order_data: dict) -> str:
    lines = [
        f"Hello {order_data['customer_name']},",
        "",
        f"Thank you for shopping at {STORE_NAME}.",
        f"Order ID: {order_data['order_id']}",
        f"Order Date: {order_data['created_at']}",
        "",
        "Items:",
    ]
    for item in order_data["items"]:
        lines.append(
            f"- {item['product_name']} x{item['quantity']} @ PHP {item['unit_price']:,.2f}"
            f" = PHP {item['subtotal']:,.2f}"
        )
    lines.extend(
        [
            "",
            f"Total Amount: PHP {order_data['total_amount']:,.2f}",
            "",
            "We appreciate your purchase.",
        ]
    )
    return "\n".join(lines)


def _build_html_body(order_data: dict) -> str:
    rows = []
    for item in order_data["items"]:
        rows.append(
            "<tr>"
            f"<td>{item['product_name']}</td>"
            f"<td>{item['quantity']}</td>"
            f"<td>PHP {item['unit_price']:,.2f}</td>"
            f"<td>PHP {item['subtotal']:,.2f}</td>"
            "</tr>"
        )
    return f"""
    <html>
      <body style="font-family: Segoe UI, Arial, sans-serif; color: #222;">
        <h2>{STORE_NAME} Order Receipt</h2>
        <p>Hello {order_data['customer_name']},</p>
        <p>Thank you for your purchase. Here are your order details.</p>
        <p><strong>Order ID:</strong> {order_data['order_id']}<br>
        <strong>Order Date:</strong> {order_data['created_at']}</p>
        <table border="1" cellspacing="0" cellpadding="8" style="border-collapse: collapse; min-width: 420px;">
          <tr style="background-color: #dbeafe;">
            <th align="left">Product</th>
            <th align="left">Qty</th>
            <th align="left">Unit Price</th>
            <th align="left">Subtotal</th>
          </tr>
          {''.join(rows)}
        </table>
        <p style="margin-top: 16px;"><strong>Total Amount:</strong> PHP {order_data['total_amount']:,.2f}</p>
        <p>We appreciate your purchase.</p>
      </body>
    </html>
    """


def _smtp_configured() -> bool:
    placeholders = {"your-email@gmail.com", "your-app-password", ""}
    return SMTP_USERNAME not in placeholders and SMTP_PASSWORD not in placeholders


def _log_email_event(order_data: dict, customer_email: str, title: str, details: str) -> None:
    EMAIL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_entry = [
        f"[{datetime.now().isoformat(timespec='seconds')}] {title}",
        f"To: {customer_email}",
        f"Order ID: {order_data['order_id']}",
        details,
        _build_plain_body(order_data),
        "-" * 72,
        "",
    ]
    with EMAIL_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write("\n".join(log_entry))
