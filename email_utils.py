# email_utils.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_otp_email(user, code):
    message = Mail(
        from_email="icomunication.pass@gmail.com",
        to_emails=user.email,
        subject="パスワードリセットコード",
        plain_text_content=f"あなたの確認コードは {code} です。",
    )
    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(response.status_code, response.body, response.headers)  # ← ここで確認
    except Exception as e:
        print(e)
