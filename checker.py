from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json, time

def check_availability():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://www.iyha.org.il/")
        time.sleep(2)
        driver.get(CHECK_URL)
        time.sleep(3)
        
        body = driver.find_element("tag name", "body").text
        print("Response:", body[:500])
        
        data = json.loads(body)
        
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
    finally:
        driver.quit()
        
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