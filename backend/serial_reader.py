import serial
import threading
import time
import re
import requests

SERIAL_PORT = "/dev/cu.usbserial-3110"      # ← change to your port
BAUD_RATE   = 115200
PATIENT_ID  = "P001"      # ← change to your actual patient ID
POST_URL    = "http://127.0.0.1:8000/vitals"

latest_bpm = 0
sensor_status = "waiting"   # "ok" | "no_finger" | "calculating" | "disconnected"

def parse_and_post(line):
    global latest_bpm, sensor_status

    if "No finger detected" in line:
        sensor_status = "no_finger"
        latest_bpm = 0
        return

    if "Too much pressure" in line:
        sensor_status = "too_much_pressure"
        return

    if "Heart Rate:" in line:
        if "calculating" in line:
            sensor_status = "calculating"
            return

        match = re.search(r"Heart Rate:\s*(\d+)\s*BPM", line)
        if match:
            bpm = int(match.group(1))
            if bpm > 0:
                latest_bpm    = bpm
                sensor_status = "ok"

                # POST to your existing /vitals endpoint
                payload = {
                    "patient_id": PATIENT_ID,
                    "bpm":        bpm,
                    "spo2":       98,    # placeholder until you add SpO2
                    "ax": 0, "ay": 0, "az": 1,   # neutral motion
                    "gx": 0, "gy": 0, "gz": 0
                }
                try:
                    requests.post(POST_URL, json=payload, timeout=2)
                except Exception as e:
                    print(f"[POST error] {e}")

def read_serial():
    global sensor_status
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
            print(f"[Serial] Connected on {SERIAL_PORT}")
            sensor_status = "connected"
            while True:
                raw  = ser.readline()
                line = raw.decode("utf-8", errors="ignore").strip()
                if line:
                    parse_and_post(line)
        except serial.SerialException as e:
            print(f"[Serial] {e} — retrying in 3s...")
            sensor_status = "disconnected"
            time.sleep(3)

def start_serial_thread():
    t = threading.Thread(target=read_serial, daemon=True)
    t.start()