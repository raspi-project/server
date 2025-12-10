import psutil
import os
import time
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import board

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
    # Terminal Clear
    os.system("clear")
    
    # Collect system stats
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    cpu_temp = get_cpu_temp()

    # ---------------------------
    # Print to Terminal
    # ---------------------------
    print("======= RASPBERRY PI SYSTEM MONITOR =======")
    print(f"CPU Usage: {cpu}%")
    if cpu_temp is not None:
        print(f"CPU Temperature: {cpu_temp:.1f}°C")
    else:
        print("CPU Temperature: Not Available")
    print(f"RAM Usage: {ram.percent}% ({ram.used//(1024**2)} MB / {ram.total//(1024**2)} MB)")
    print(f"Disk Usage: {disk.percent}% ({disk.used//(1024**3)} GB / {disk.total//(1024**3)} GB)")
    print("============================================")

    # ---------------------------
    # Draw on OLED
    # ---------------------------
    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    draw.text((0, 0),  f"CPU: {cpu}%", font=font, fill=255)
    
    if cpu_temp is not None:
        draw.text((0, 12), f"Temp: {cpu_temp:.1f}C", font=font, fill=255)
    else:
        draw.text((0, 12), f"Temp: NA", font=font, fill=255)

    draw.text((0, 24), f"RAM: {ram.percent}%", font=font, fill=255)
    draw.text((0, 36), f"Disk: {disk.percent}%", font=font, fill=255)
    draw.text((0, 48), "UMESH's PI", font=font, fill=255)

    oled.image(image)
    oled.show()

    time.sleep(1)
