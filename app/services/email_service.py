import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

class EmailService:
    def __init__(self):
        self.address = None
        self.password = None
        self.server = None
        self.port = None

    def _load_config(self):
        self.address = current_app.config['EMAIL_ADDRESS']
        self.password = current_app.config['EMAIL_PASSWORD']
        self.server = current_app.config['SMTP_SERVER']
        self.port = current_app.config['SMTP_PORT']

    # الأنماط: 'info' برتقالي | 'threshold' أحمر (تجاوز عتبة) | 'security' أحمر أمني
    STYLES = {
        'info': {'color': '#ff8c42', 'icon': '🔔', 'bg': 'rgba(255, 140, 66, 0.08)'},
        'threshold': {'color': '#ef4444', 'icon': '⚠️', 'bg': 'rgba(239, 68, 68, 0.08)'},
        'security': {'color': '#ef4444', 'icon': '🛡️', 'bg': 'rgba(239, 68, 68, 0.12)'}
    }

    def send_alert(self, subject, body, recipient, style='info'):
        if not recipient:
            return False
        try:
            self._load_config()
            msg = MIMEMultipart('alternative')
            msg['From'] = self.address
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            msg.attach(MIMEText(self._render_html(subject, body, style), 'html', 'utf-8'))

            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.address, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {e}")
            return False

    def _render_html(self, subject, body, style='info'):
        st = self.STYLES.get(style, self.STYLES['info'])
        color, icon, bg = st['color'], st['icon'], st['bg']
        rtl = 'dir="rtl" style="direction:rtl; text-align:right;"'

        rows = ''
        for ln in body.split('\n'):
            ln = ln.strip()
            if not ln:
                continue
            if '：' in ln or ': ' in ln:
                label, val = ln.split('：' if '：' in ln else ': ', 1)
                rows += f"""
                <tr>
                  <td {rtl} style="padding:10px 20px; border-bottom:1px solid #f1f5f9; color:#64748b; font-size:13px; font-weight:700; white-space:nowrap; width:35%;">{label}</td>
                  <td {rtl} style="padding:10px 20px; border-bottom:1px solid #f1f5f9; color:#1e293b; font-size:15px; font-weight:700;">{val}</td>
                </tr>"""
            else:
                rows += f"""
                <tr>
                  <td {rtl} colspan="2" style="padding:14px 20px 6px; color:{color}; font-size:15px; font-weight:800;">{ln}</td>
                </tr>"""

        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<body style="margin:0; padding:0; background:#f1f5f9; font-family:'Segoe UI',Tahoma,Arial,sans-serif;">
  <div dir="rtl" style="direction:rtl; text-align:right; max-width:560px; margin:24px auto; background:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 6px 24px rgba(0,0,0,0.10);">
    <div style="background:linear-gradient(135deg, {color}, #8b5cf6); padding:28px; text-align:center;">
      <div style="font-size:44px; line-height:1;">{icon}</div>
      <h1 {rtl} style="color:#ffffff; margin:10px 0 0; font-size:21px; font-weight:800;">{subject}</h1>
    </div>
    <table dir="rtl" cellpadding="0" cellspacing="0" style="width:100%; border-collapse:collapse; direction:rtl;">{rows}</table>
    <div {rtl} style="margin:16px 20px 20px; padding:14px; background:{bg}; border-radius:10px; border-right:4px solid {color}; text-align:center;">
      <span style="color:{color}; font-weight:800; font-size:14px;">⚠️ يرجى مراجعة النظام واتخاذ الإجراء اللازم في أقرب وقت</span>
    </div>
  </div>
</body>
</html>"""
