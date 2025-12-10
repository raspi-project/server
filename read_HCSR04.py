
import time
import RPi.GPIO as GPIO
import smtplib
from email.mime.text import MIMEText

TRIG = 26
ECHO = 19
ALERT_PIN = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(ALERT_PIN, GPIO.OUT)

GPIO.output(TRIG, False)
time.sleep(2)

DIST_LIMIT = 20  # cm

EMAIL_USER = "yourgmail@gmail.com"
EMAIL_PASS = "your_app_password"  # 16 digit one
EMAIL_TO = "receiver@gmail.com"

def send_email_alert(distance):
    subject = "Ultrasonic Alert - Object Detected"
    body = f"Warning! Object detected at {distance} cm from your Raspberry Pi."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
        server.quit()
        print("Email Alert Sent!")
    except Exception as e:
        print("Error sending email:", e)

def get_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # speed of sound
    distance = round(distance, 2)
    return distance


print("Ultrasonic Distance Alert System Started...")

try:
    while True:
        dist = get_distance()
        print(f"Distance: {dist} cm")

        last_alert_time = 0

        if dist < DIST_LIMIT:
            if time.time() - last_alert_time > 30:
                send_email_alert(dist)
                last_alert_time = time.time()
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    GPIO.cleanup()




