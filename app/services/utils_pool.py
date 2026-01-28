import bcrypt
import base64
import secrets
import string
import os
import smtplib
from email.message import EmailMessage


class PasswordUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return base64.b64encode(hashed_password).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password_str: str) -> bool:
        hashed_password = base64.b64decode(hashed_password_str.encode('utf-8'))
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

    @staticmethod
    def generate_temporary_password(length: int = 10) -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def send_email(to_email: str, subject: str, body: str) -> bool:

        smtp_host = os.getenv('SMTP_HOST')
        smtp_port = int(os.getenv('SMTP_PORT', '0')) if os.getenv('SMTP_PORT') else None
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('FROM_EMAIL', smtp_user)

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = from_email or 'no-reply@example.com'
        msg['To'] = to_email
        msg.set_content(body)

        # If SMTP not configured, just log and return True
        if not smtp_host or not smtp_port or not smtp_user or not smtp_pass:
            print('SMTP not fully configured; email content:')
            print('To:', to_email)
            print('Subject:', subject)
            print('Body:', body)
            return True

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return True
        except Exception as e:
            print('Failed to send email:', e)
            return False
