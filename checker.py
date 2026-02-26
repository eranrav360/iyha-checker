import os
import json
import smtplib
import subprocess
import sys
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

CHECK_URL = "https://www.iyha.org.il/be/be/pro/rooms?lang=heb&chainid=186&hotel=10210_1&in=2026-03-26&out=2026-03-27&rooms=1&ad1=2&ch1=2&inf1=0&mergeResults=false"

subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)


def check_availability():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="he-IL",
            timezone_id="Asia/Jerusalem",
            viewport={"width": 1280, "height": 800},
            extra_http_headers={"Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8"},
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

        page = context.new_page()
        api_responses = []

        def handle_response(response):
            if "rooms" in response.url and response.status == 200:
                try:
                    data = response.json()
                    print("API captured:", str(data)[:300])
                    api_responses.append(data)
                except Exception as e:
                    print(f"Failed to parse API response: {e}")

        page.on("response", handle_response)

        try:
            page.goto("https://www.iyha.org.il/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)

            page.goto(CHECK_URL, wait_until="domcontentloaded", timeout=60000)
            
            # ממתין עד שה-API response יגיע (עד 15 שניות)
            for _ in range(15):
                page.wait_for_timeout(1000)
                if api_responses:
                    break

            print(f"Page title: {page.title()}")
            print(f"API responses captured: {len(api_responses)}")

            if not api_responses:
                print("No API response captured")
                return False, []

            data = api_responses[0]
            
            # מבנה ה-JSON האמיתי: data['Obj']['RoomsList']
            obj = data.get("Obj", {})
            has_results = obj.get("HasResults", False)
            rooms_list = obj.get("RoomsList", [])

            if has_results and rooms_list:
                # חילוץ רשימת החדרים הפנויים
                rooms = []
                for room_group in rooms_list:
                    for room in room_group.get("Rooms", []):
                        if room.get("TotalAvailabilty", 0) > 0:
                            rooms.append(room)
                if rooms:
                    return True, rooms

            return False, []

        except Exception as e:
            print(f"Error: {e}")
            return None, str(e)
        finally:
            browser.close()


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
        print(f"Found {len(rooms)} room(s)!")
        send_email(
            subject='🏕️ יש חדרים פנויים באנ"א מצפה רמון!',
            body=(
                f"נמצאו {len(rooms)} חדרים פנויים!\n\n"
                f"קישור להזמנה:\n{CHECK_URL}\n\n"
                f"פרטים:\n{json.dumps(rooms, ensure_ascii=False, indent=2)}"
            ),
        )
    elif available is False:
        print("No rooms available. No email sent.")
    else:
        print(f"Check failed: {rooms}")
        send_email(
            subject="⚠️ שגיאה בבדיקת חדרים - מצפה רמון",
            body=f"הסקריפט נתקל בשגיאה:\n\n{rooms}",
        )
