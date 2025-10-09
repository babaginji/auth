# email_utils.py
from flask_mail import Message
from extensions import mail


def send_otp_email(user, code):
    msg = Message(
        subject="パスワード再設定コード",
        sender="your_email@example.com",
        recipients=[user.email],
        body=f"あなたの確認コードは {code} です。10分以内に入力してください。",
    )
    mail.send(msg)
