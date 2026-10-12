"""Optional email delivery via SendGrid, with optional PDF attachment."""
import base64
import os
import re
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition


def send_travel_email(body: str, recipient: str, subject: str, attachment_bytes: bytes = None,
                      attachment_name: str = "travel_plan.pdf") -> str:
    api_key = os.getenv("SENDGRID_API_KEY", "").strip()
    sender = os.getenv("FROM_EMAIL", "").strip()
    if not api_key:
        return "Email not sent: SENDGRID_API_KEY is not configured."
    if not sender:
        return "Email not sent: FROM_EMAIL is not configured."
    if not recipient.strip() or not subject.strip() or not body.strip():
        return "Email not sent: recipient, subject, and travel results are required."
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", recipient.strip()):
        return "Email not sent: please enter a valid recipient email address."
    try:
        message = Mail(from_email=sender, to_emails=recipient.strip(), subject=subject.strip(),
                       plain_text_content=body)
        if attachment_bytes:
            encoded = base64.b64encode(attachment_bytes).decode("ascii")
            message.attachment = Attachment(
                FileContent(encoded), FileName(attachment_name), FileType("application/pdf"),
                Disposition("attachment")
            )
        response = SendGridAPIClient(api_key).send(message)
        if 200 <= response.status_code < 300:
            return f"Email accepted by SendGrid (HTTP {response.status_code}). This does not guarantee inbox delivery."
        return f"SendGrid returned HTTP {response.status_code}. Check sender verification and API permissions."
    except Exception as exc:
        # Do not expose credentials; error text may contain request details, so keep message concise.
        return f"Email error: {type(exc).__name__}. Check SendGrid configuration and logs."
