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

    def send_alert(self, subject, body, recipient):
        if not recipient:
            return False
        try:
            self._load_config()
            msg = MIMEMultipart()
            msg['From'] = self.address
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.address, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {e}")
            return False
