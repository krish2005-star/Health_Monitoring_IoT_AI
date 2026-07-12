import serial
import threading
import time
import re
import requests

# ==========================
# CONFIG
# ==========================

SERIAL_PORT = "/dev/cu.wchusbserial1130"
BAUD_RATE = 115200

PATIENT_ID = "P001"
POST_URL = "http://127.0.0.1:8000/vitals"

# ==========================
# GLOBAL STATE
# ==========================

latest_bpm = 0
sensor_status = "waiting"

last_sent_bpm = None
last_sent_time = 0

last_no_finger_time = 0

# ==========================
# PARSE SERIAL + POST
# ==========================

# def parse_and_post(line):
#     global latest_bpm
#     global sensor_status
#     global last_sent_bpm
#     global last_sent_time

#     if not line:
#         return

#     # -------------------------
#     # No finger detected
#     # -------------------------
#     if "No finger?" in line:

#         sensor_status = "no_finger"
#         latest_bpm = 0

#         print("[Sensor] No finger detected")

#         payload = {
#             "patient_id": PATIENT_ID,
#             "bpm": 0,
#             "spo2": 0,
#             "ax": 0,
#             "ay": 0,
#             "az": 1,
#             "gx": 0,
#             "gy": 0,
#             "gz": 0,
#         }

#         try:
#             requests.post(
#                 POST_URL,
#                 json=payload,
#                 timeout=5
#             )
#         except Exception as e:
#             print("[POST ERROR]", e)

#         return

#     # -------------------------
#     # Extract Avg BPM
#     # -------------------------
#     match = re.search(r"Avg BPM=(\d+)", line)

#     if not match:
#         return

#     bpm = int(match.group(1))

#     # Ignore invalid BPM
#     if bpm < 20 or bpm > 220:
#         print(f"[Ignored BPM] {bpm}")
#         return

#     # -------------------------
#     # Prevent sending duplicates
#     # but refresh every 2 seconds
#     # -------------------------

#     current_time = time.time()

#     if (
#         bpm == last_sent_bpm
#         and current_time - last_sent_time < 2
#     ):
#         return

#     last_sent_bpm = bpm
#     last_sent_time = current_time

#     latest_bpm = bpm
#     sensor_status = "ok"

#     payload = {
#         "patient_id": PATIENT_ID,
#         "bpm": bpm,
#         "spo2": 98,
#         "ax": 0,
#         "ay": 0,
#         "az": 1,
#         "gx": 0,
#         "gy": 0,
#         "gz": 0,
#     }

#     try:

#         response = requests.post(
#             POST_URL,
#             json=payload,
#             timeout=10
#         )

#         print(
#             f"[POST] BPM={bpm} "
#             f"→ {response.status_code}"
#         )

#     except Exception as e:
#         print("[POST ERROR]", e)

def post_payload(payload):
    try:
        response = requests.post(
            POST_URL,
            json=payload,
            timeout=3
        )

        print(
            f"[POST] BPM={payload['bpm']} -> {response.status_code}"
        )

    except Exception as e:
        print("[POST ERROR]", e)


def parse_and_post(line):

    global latest_bpm
    global sensor_status
    global last_sent_bpm
    global last_sent_time
    global last_no_finger_time

    if not line:
        return

    print("BACKEND SERIAL:", line)

    current_time = time.time()

    # ------------------------
    # No finger
    # ------------------------

    if "NO_FINGER" in line:

        sensor_status = "no_finger"
        latest_bpm = 0

        # Only send once every 3 seconds
        if current_time - last_no_finger_time < 3:
            return

        last_no_finger_time = current_time

        payload = {
            "patient_id": PATIENT_ID,
            "bpm": 0,
            "spo2": 0,
            "ax": 0,
            "ay": 0,
            "az": 1,
            "gx": 0,
            "gy": 0,
            "gz": 0,
        }

        post_payload(payload)

        return

    # ------------------------
    # Extract BPM
    # ------------------------

    match = re.search(r"BPM=([\d.]+)", line)

    if not match:
        return

    bpm = float(match.group(1))

    if bpm < 20 or bpm > 220:
        return

    # Don't send identical BPM within 2 sec
    if (
        bpm == last_sent_bpm
        and current_time - last_sent_time < 2
    ):
        return

    last_sent_bpm = bpm
    last_sent_time = current_time

    latest_bpm = bpm
    sensor_status = "ok"

    payload = {
        "patient_id": PATIENT_ID,
        "bpm": bpm,
        "spo2": 98,
        "ax": 0,
        "ay": 0,
        "az": 1,
        "gx": 0,
        "gy": 0,
        "gz": 0,
    }

    post_payload(payload)

# ==========================
# SERIAL READER
# ==========================

def read_serial():
    global sensor_status

    while True:

        try:

            print(
                f"[Serial] Connecting to {SERIAL_PORT}..."
            )

            ser = serial.Serial(
                SERIAL_PORT,
                BAUD_RATE,
                timeout=1
            )

            # ESP8266 resets after opening serial
            time.sleep(3)

            ser.reset_input_buffer()

            print(
                f"[Serial] Connected on {SERIAL_PORT}"
            )

            sensor_status = "connected"

            while True:

                raw = ser.readline()

                if not raw:
                    continue

                try:
                    line = raw.decode(
                        "utf-8",
                        errors="ignore"
                    ).strip()

                except Exception:
                    continue

                if not line:
                    continue

                parse_and_post(line)

        except serial.SerialException as e:

            sensor_status = "disconnected"

            print("[Serial Error]", e)

            print(
                "[Serial] Reconnecting in 3 seconds..."
            )

            time.sleep(3)


# ==========================
# START THREAD
# ==========================

def start_serial_thread():

    t = threading.Thread(
        target=read_serial,
        daemon=True
    )

    t.start()

    print("[Serial Thread Started]")