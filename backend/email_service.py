import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


async def send_email(to: str, subject: str, html_body: str) -> bool:
    """发送 HTML 邮件到指定收件人，成功返回 True。"""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.error("SMTP 未配置，跳过发送")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_FROM or SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            use_tls=SMTP_USE_TLS,
        )
        logger.info("邮件已发送至 %s", to)
        return True
    except Exception:
        logger.exception("邮件发送失败 -> %s", to)
        return False


def markdown_to_html(md_text: str) -> str:
    """将 Agent 返回的 Markdown 转为简单 HTML 邮件正文。"""
    try:
        import markdown
        body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    except ImportError:
        body = f"<pre>{md_text}</pre>"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:'Microsoft YaHei',sans-serif;padding:24px;color:#2d3436;">
  <h2 style="color:#ff4757;">🔥 小红书热点日报</h2>
  {body}
  <hr style="border:none;border-top:1px solid #e8e8e8;margin-top:24px;">
  <p style="font-size:12px;color:#b2bec3;">此邮件由小红书热点 Agent 自动发送</p>
</body></html>"""
