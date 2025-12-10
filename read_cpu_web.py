#!/usr/bin/env python3
# pi_monitor_flask.py
# Single-file system monitor + OLED + fan control + Flask dashboard
# Option 1 behaviour: Manual switch allowed, but if temp > 55°C fan forced ON.

import threading
import time
import os
from flask import Flask, jsonify, request, render_template_string
import psutil
from PIL import Image, ImageDraw, ImageFont
import board
import adafruit_ssd1306
import RPi.GPIO as GPIO

# -------------------------
# CONFIG
# -------------------------
FAN_PIN = 17
TEMP_SAFE_THRESHOLD = 55.0   # °C - above this fan forced ON
OLED_WIDTH = 128
OLED_HEIGHT = 64
I2C_ADDR = 0x3C

POLL_INTERVAL = 1.0   # seconds for local monitoring
WEB_POLL_INTERVAL = 2.0  # seconds clients poll the server for updates

# -------------------------
# GLOBAL STATE (shared)
# -------------------------
state = {
    "cpu_percent": 0.0,
    "cpu_temp": None,
    "ram_used_mb": 0,
    "ram_total_mb": 0,
    "ram_percent": 0,
    "disk_used_gb": 0,
    "disk_total_gb": 0,
    "disk_percent": 0,
    "fan_actual_on": False,   # what is actually set on GPIO
    "fan_manual_state": False, # user-chosen state from web (True = ON, False = OFF)
    "fan_forced_auto": False  # whether currently forced ON due to temp
}

state_lock = threading.Lock()

# -------------------------
# HELPER: read CPU temp
# -------------------------
def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            t = int(f.read().strip()) / 1000.0
        return t
    except Exception:
        return None

# -------------------------
# GPIO & OLED SETUP
# -------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT)
GPIO.output(FAN_PIN, GPIO.LOW)

# OLED setup (same as your original code)
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, addr=I2C_ADDR)
oled.fill(0)
oled.show()
font = ImageFont.load_default()

# -------------------------
# MONITOR THREAD
# -------------------------
def monitor_loop():
    """
    Runs in a separate thread:
    - collects stats using psutil and get_cpu_temp()
    - decides fan state according to Option 1 logic:
       * If cpu_temp > TEMP_SAFE_THRESHOLD -> force fan ON (auto override)
       * Else follow manual state (from web)
    - update GPIO and OLED and state dict
    """
    while True:
        cpu = psutil.cpu_percent(interval=None)  # non-blocking
        cpu_temp = get_cpu_temp()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # convert sizes
        ram_used_mb = ram.used // (1024**2)
        ram_total_mb = ram.total // (1024**2)
        disk_used_gb = disk.used // (1024**3)
        disk_total_gb = disk.total // (1024**3)

        # Decide fan
        forced = False
        if cpu_temp is not None and cpu_temp > TEMP_SAFE_THRESHOLD:
            forced = True

        with state_lock:
            state["cpu_percent"] = round(cpu, 1)
            state["cpu_temp"] = round(cpu_temp, 1) if cpu_temp is not None else None
            state["ram_used_mb"] = ram_used_mb
            state["ram_total_mb"] = ram_total_mb
            state["ram_percent"] = ram.percent
            state["disk_used_gb"] = disk_used_gb
            state["disk_total_gb"] = disk_total_gb
            state["disk_percent"] = disk.percent
            state["fan_forced_auto"] = forced

            # actual fan: forced ON if forced else manual choice
            if forced:
                actual_on = True
            else:
                actual_on = bool(state["fan_manual_state"])

            state["fan_actual_on"] = actual_on

        # Set GPIO according to actual_on
        GPIO.output(FAN_PIN, GPIO.HIGH if actual_on else GPIO.LOW)

        # Draw to OLED (same layout you wanted)
        try:
            image = Image.new("1", (OLED_WIDTH, OLED_HEIGHT))
            draw = ImageDraw.Draw(image)

            draw.text((0, 0), f"CPU: {state['cpu_percent']}%", font=font, fill=255)
            if state["cpu_temp"] is not None:
                draw.text((0, 12), f"Temp: {state['cpu_temp']:.1f}C", font=font, fill=255)
            else:
                draw.text((0, 12), "Temp: NA", font=font, fill=255)

            draw.text((0, 24), f"RAM: {state['ram_used_mb']}/{state['ram_total_mb']}MB", font=font, fill=255)
            draw.text((0, 36), f"Disk: {state['disk_used_gb']}/{state['disk_total_gb']}GB", font=font, fill=255)

            # Fan label: show if AUTO forced
            if state["fan_actual_on"]:
                if state["fan_forced_auto"]:
                    fan_text = "FAN ON (AUTO)"
                else:
                    fan_text = "FAN ON"
            else:
                fan_text = "FAN OFF"

            draw.text((0, 48), fan_text, font=font, fill=255)

            oled.image(image)
            oled.show()
        except Exception as e:
            # don't let OLED errors kill the loop
            print("OLED update error:", e)

        # Print to terminal (clean)
        os.system("clear")
        with state_lock:
            print("======= RASPBERRY PI SYSTEM MONITOR =======")
            print(f"CPU Usage: {state['cpu_percent']}%")
            if state["cpu_temp"] is not None:
                print(f"CPU Temp: {state['cpu_temp']:.1f}°C")
            else:
                print("CPU Temp: Not Available")
            print(f"RAM: {state['ram_percent']}% ({state['ram_used_mb']} MB / {state['ram_total_mb']} MB)")
            print(f"Disk: {state['disk_percent']}% ({state['disk_used_gb']} GB / {state['disk_total_gb']} GB)")
            if state["fan_actual_on"]:
                if state["fan_forced_auto"]:
                    print("Fan: FAN ON (AUTO override)")
                else:
                    print("Fan: FAN ON (Manual)")
            else:
                print("Fan: FAN OFF (Manual)")
            print("============================================")

        # sleep for POLL_INTERVAL seconds
        time.sleep(POLL_INTERVAL)

# -------------------------
# FLASK APP (web UI)
# -------------------------
app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Pi Monitor Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 18px; }
    .card { border-radius:8px; padding:12px; box-shadow: 0 0 6px rgba(0,0,0,0.12); margin-bottom:12px; max-width:480px;}
    .big { font-size: 1.2rem; font-weight:600; }
    .muted { color: #666; font-size:0.9rem }
    .switch { display:inline-block; padding:6px 12px; border-radius:6px; background:#eee; cursor:pointer; }
    button { padding:8px 12px; border-radius:6px; cursor:pointer; }
  </style>
</head>
<body>
  <h2>Raspberry Pi Monitor</h2>

  <div class="card">
    <div>CPU: <span id="cpu">-</span></div>
    <div class="muted">Temperature: <span id="temp">-</span></div>
  </div>

  <div class="card">
    <div>RAM: <span id="ram">-</span></div>
    <div class="muted">Disk: <span id="disk">-</span></div>
  </div>

  <div class="card">
    <div class="big">Fan: <span id="fan_state">-</span></div>
    <div style="margin-top:8px;">
      <label>Manual Fan Control:
        <input type="checkbox" id="fan_manual_switch">
      </label>
      <button id="set_manual">Apply Manual State</button>
      <div class="muted" style="margin-top:8px;">If temp &gt; {{ threshold }}°C the fan will be forced ON automatically.</div>
    </div>
  </div>

  <script>
    const threshold = {{ threshold }};
    async function fetchStatus(){
      try{
        const res = await fetch("/status");
        const j = await res.json();
        document.getElementById("cpu").innerText = j.cpu_percent + "%";
        document.getElementById("temp").innerText = (j.cpu_temp !== null) ? j.cpu_temp + "°C" : "NA";
        document.getElementById("ram").innerText = j.ram_used_mb + "/" + j.ram_total_mb + "MB (" + j.ram_percent + "%)";
        document.getElementById("disk").innerText = j.disk_used_gb + "/" + j.disk_total_gb + "GB (" + j.disk_percent + "%)";
        document.getElementById("fan_state").innerText = j.fan_actual_on ? (j.fan_forced_auto ? "FAN ON (AUTO)" : "FAN ON (Manual)") : "FAN OFF (Manual)";
        // set checkbox to manual_state (so user sees current manual selection)
        document.getElementById("fan_manual_switch").checked = j.fan_manual_state;
      }catch(e){
        console.error("status err", e);
      }
    }

    // set manual state
    document.getElementById("set_manual").addEventListener("click", async ()=>{
      const val = document.getElementById("fan_manual_switch").checked;
      try{
        await fetch("/set_fan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ manual_state: val })
        });
        // refresh status after set
        await fetchStatus();
      }catch(e){
        console.error(e);
      }
    });

    // poll every WEB_POLL_INTERVAL seconds
    fetchStatus();
    setInterval(fetchStatus, {{ web_poll_ms }});
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    # render template with threshold and poll interval
    return render_template_string(INDEX_HTML, threshold=TEMP_SAFE_THRESHOLD, web_poll_ms=int(WEB_POLL_INTERVAL*1000))

@app.route("/status")
def status():
    with state_lock:
        return jsonify({
            "cpu_percent": state["cpu_percent"],
            "cpu_temp": state["cpu_temp"],
            "ram_used_mb": state["ram_used_mb"],
            "ram_total_mb": state["ram_total_mb"],
            "ram_percent": state["ram_percent"],
            "disk_used_gb": state["disk_used_gb"],
            "disk_total_gb": state["disk_total_gb"],
            "disk_percent": state["disk_percent"],
            "fan_actual_on": state["fan_actual_on"],
            "fan_manual_state": state["fan_manual_state"],
            "fan_forced_auto": state["fan_forced_auto"]
        })

@app.route("/set_fan", methods=["POST"])
def set_fan():
    """
    Accepts JSON: { "manual_state": true/false }
    Sets the manual state; note: AUTO override still applies when temp > threshold
    """
    data = request.get_json(force=True)
    if "manual_state" not in data:
        return jsonify({"error": "manual_state required"}), 400
    manual = bool(data["manual_state"])
    with state_lock:
        state["fan_manual_state"] = manual
        # actual will be computed by monitor thread on next loop (or we could set GPIO here too)
        # immediate apply if temperature not forcing auto:
        if not state["fan_forced_auto"]:
            state["fan_actual_on"] = manual
            GPIO.output(FAN_PIN, GPIO.HIGH if manual else GPIO.LOW)
    return jsonify({"ok": True, "fan_manual_state": state["fan_manual_state"]})

# -------------------------
# STARTUP
# -------------------------
if __name__ == "__main__":
    try:
        # start monitor thread
        mthread = threading.Thread(target=monitor_loop, daemon=True)
        mthread.start()

        # run flask (accessible on all interfaces by default, port 5000)
        # you can change host/port as needed
        app.run(host="0.0.0.0", port=5000, threaded=True)
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup GPIO on exit
        GPIO.output(FAN_PIN, GPIO.LOW)
        GPIO.cleanup()
        try:
            oled.fill(0)
            oled.show()
        except Exception:
            pass
        print("Exiting - GPIO cleaned up")
