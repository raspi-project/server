import serial 
import pynmea2
import time

port = "/dev/serial0"
baud = 9600
serial_port = serial.Serial(port, baudrate = baud, timeout = 1)

print("GPS Initialized. Waiting for fix...")
print("-------------------------------------")

last_print_time = time.time()

try:
  while True:
    line = serial_port.readline().decode.('utf-8', error-'ignore')

  if "$GPGGA" in line:
    try:
      msg = pynmea2.parse(line)

      current_time = time.time()
      if current_time - last_print_time >= 2:
        if msg.lat and msg.lon:
          print(f"Time : {time.strftime('%H:%M:%S')}")
          print(f"LAtitude : {msg.latitude:.6f}")
          print(f"Longitude : {msg.longitude:.6f}")
          print(f"Satelites : {msg.num_stats}")
          print("------------------------------------------")
        else:
          print("Searching for satelites .....(NO fix) ")
        last_print_time = current_time

    except pynmea2.ParseError:
      continue
except KeyboardInterrupt:
  print("\nExiting program.")
finally:
  serial_port.close()
  
