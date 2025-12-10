import time
import RPi.GPIO as GPIO

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

        if dist < DIST_LIMIT:
            print("⚠ ALERT! Object too close!")
            GPIO.output(ALERT_PIN, True)
        else:
            GPIO.output(ALERT_PIN, False)

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    GPIO.cleanup()
