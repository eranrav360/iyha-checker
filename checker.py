import requests
import smtplib
from email.mime.text import MIMEText
import os

CHECK_URL = "https://www.iyha.org.il/be/be/pro/rooms?lang=heb&chainid=186&hotel=10210_1&in=2026-03-26&out=2026-03-27&rooms=1&ad1=2&ch1=2&inf1=0&mergeResults=false"

def check_availability():
    session = requests.Session()
    
    # קודם "ביקור" בעמוד הראשי כדי לקבל cookies
    session.get("https://www.iyha.org.il/", headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    })
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8",
        "Referer": "https://www.iyha.org.il/",
        "Origin": "https://www.iyha.org.il",
    }
    
    try:
        resp = session.get(CHECK_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        print("Response:", data)
        
        if isinstance(data, list) and len(data) > 0:
            return True, data
        if isinstance(data, dict):
            rooms = data.get("rooms") or data.get("data") or data.get("results") or []
            if rooms:
                return True, rooms
        return False, []
    except Exception as e:
        print(f"Error checking availability: {e}")
        return None, str(e)

def send_email(available_rooms):
    sender = os.environ["GMAIL_USER"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ["NOTIFY_EMAIL"]
    
    msg = MIMEText(
        f"נמצאו חדרים פנויים באכסניית מצפה רמון!\n\n"
        f"קישור להזמנה:\n{CHECK_URL}\n\n"
        f"פרטים: {available_rooms}",
        "plain",
        "utf-8"
    )
    msg["Subject"] = "🏕️ יש חדרים פנויים באנ\"א מצפה רמון!"
    msg["From"] = sender
    msg["To"] = recipient
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, recipient, msg.as_string())
    print("Email sent!")

if __name__ == "__main__":
    available, rooms = check_availability()
    if available:
        print(f"Found rooms: {rooms}")
        send_email(rooms)
    elif available is False:
        print("No rooms available.")
        send_email("אין חדרים פנויים כרגע — אבל הסקריפט עובד!")  # זמני לבדיקה
    else:
        print("Check failed.")
        send_email(f"שגיאה בבדיקה: {rooms}")  # זמני לבדיקה