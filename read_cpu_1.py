import psutil
import os
import time
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import board
import RPi.GPIO as GPIO

# -------------------------
# CPU TEMPERATURE FUNCTION
# -------------------------
def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000
        return temp
    except:
        return None

# -------------------------
# GPIO SETUP FOR FAN (DC MOTOR)
# -------------------------
FAN_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT)
GPIO.output(FAN_PIN, GPIO.LOW)

# -------------------------
# OLED CONFIG
# -------------------------
WIDTH = 128
HEIGHT = 64

i2c = board.I2C()  # SDA=2, SCL=3
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C)

oled.fill(0)
oled.show()

font = ImageFont.load_default()

# -------------------------
# MAIN LOOP
# -------------------------
while True:
    os.system("clear")
    
    # Collect system stats
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    cpu_temp = get_cpu_temp()

    # FAN CONTROL
    if cpu_temp is not None and cpu_temp > 55:
        GPIO.output(FAN_PIN, GPIO.HIGH)
        fan_state = "FAN ON"
    else:
        GPIO.output(FAN_PIN, GPIO.LOW)
        fan_state = "FAN OFF"

    # Print to Terminal
    print("======= RASPBERRY PI SYSTEM MONITOR =======")
    print(f"CPU Usage: {cpu}%")
    
    if cpu_temp is not None:
        print(f"CPU Temp: {cpu_temp:.1f}°C")
    else:
        print("CPU Temp: Not Available")

    print(f"RAM: {ram.percent}% ({ram.used//(1024**2)} MB / {ram.total//(1024**2)} MB)")
    print(f"Disk: {disk.percent}% ({disk.used//(1024**3)} GB / {disk.total//(1024**3)} GB)")
    print(f"Fan: {fan_state}")
    print("============================================")

    # Draw on OLED
    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    draw.text((0, 0),  f"CPU: {cpu}%", font=font, fill=255)

    if cpu_temp is not None:
        draw.text((0, 12), f"Temp: {cpu_temp:.1f}C", font=font, fill=255)
    else:
        draw.text((0, 12), "Temp: NA", font=font, fill=255)

    draw.text((0, 24), f"RAM: {ram.used//(1024**2)}/{ram.total//(1024**2)}MB", font=font, fill=255)
    draw.text((0, 36), f"Disk: {disk.used//(1024**3)}/{disk.total//(1024**3)}GB", font=font, fill=255)

    draw.text((0, 48), fan_state, font=font, fill=255)

    oled.image(image)
    oled.show()

    time.sleep(1)
