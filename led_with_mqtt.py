import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

# ---------------- GPIO ----------------
LED_PIN = 26
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, False)

# ---------------- MQTT ----------------
BROKER = "YOUR_HIVEMQ_HOST"
PORT = 8883
USERNAME = "YOUR_USERNAME"
PASSWORD = "YOUR_PASSWORD"

TOPIC_CONTROL = "umesh/led/control"
TOPIC_STATUS  = "umesh/led/status"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe(TOPIC_CONTROL)
    else:
        print("Connection failed")

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print("Received:", message)

    if message == "ON":
        GPIO.output(LED_PIN, True)
        client.publish(TOPIC_STATUS, "ON")

    elif message == "OFF":
        GPIO.output(LED_PIN, False)
        client.publish(TOPIC_STATUS, "OFF")

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()

client.on_connect = on_connect
client.on_message = on_message

print("Connecting to broker...")
client.connect(BROKER, PORT, 60)
client.loop_forever()
