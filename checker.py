import os
import json
import smtplib
import requests
from email.mime.text import MIMEText

CHECK_URL = "https://www.iyha.org.il/be/be/pro/rooms?lang=heb&chainid=186&hotel=10210_1&in=2026-03-26&out=2026-03-27&rooms=1&ad1=2&ch1=2&inf1=0&mergeResults=false"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.iyha.org.il/",
}

def check_availability():
    try:
        response = requests.get(CHECK_URL, headers=HEADERS, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response (first 500 chars): {response.text[:500]}")

        data = response.json()

        # המבנה יכול להיות רשימה ישירה או dict עם מפתח
        rooms = []
        if isinstance(data, list):
            rooms = data
        elif isinstance(data, dict):
            rooms = (
                data.get("rooms")
                or data.get("data")
                or data.get("results")
                or []
            )

        if rooms:
            print(f"Found {len(rooms)} room(s)!")
            return True, rooms
        else:
            print("No rooms found in response.")
            return False, []

    except Exception as e:
        print(f"Error checking availability: {e}")
        return None, str(e)


def send_email(subject, body):
    sender = os.environ["GMAIL_USER"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ["NOTIFY_EMAIL"]

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, recipient, msg.as_string())
    print("Email sent!")


if __name__ == "__main__":
    available, rooms = check_availability()

    if available is True:
        print(f"Found rooms: {rooms}")
        send_email(
            subject="🏕️ יש חדרים פנויים באנ\"א מצפה רמון!",
            body=(
                f"נמצאו חדרים פנויים באכסניית מצפה רמון!\n\n"
                f"קישור להזמנה:\n{CHECK_URL}\n\n"
                f"פרטים:\n{json.dumps(rooms, ensure_ascii=False, indent=2)}"
            ),
        )
    elif available is False:
        print("No rooms available. No email sent.")
        # אין אימייל — אין חדרים, אין צורך להודיע
    else:
        # שגיאה אמיתית — שווה לדעת
        print(f"Check failed: {rooms}")
        send_email(
            subject="⚠️ שגיאה בבדיקת חדרים - מצפה רמון",
            body=f"הסקריפט נתקל בשגיאה:\n\n{rooms}",
        )