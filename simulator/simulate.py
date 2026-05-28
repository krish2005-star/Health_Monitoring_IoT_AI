import requests
import time
import random
import math

BASE_URL = "http://localhost:8000"

def get_all_patients():
    """fetch live patient list from DB every time"""
    try:
        res = requests.get(f"{BASE_URL}/admin/patients-simple")
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return []

def generate_vitals(base_bpm, cycle):
    """generate realistic vitals with natural variation"""
    # natural sine wave variation ±5 BPM
    natural = base_bpm + 5 * math.sin(cycle * 0.3)
    bpm  = natural + random.uniform(-3, 3)
    spo2 = random.uniform(96, 100)
    # simulate activity states
    if random.random() < 0.03:   # 3% chance spike (emergency)
        bpm = base_bpm + random.randint(50, 80)
        spo2 = random.uniform(85, 93)
    return round(bpm, 1), round(spo2, 1)

def generate_motion():
    """generate realistic accelerometer + gyro data"""
    # normal movement
    ax = round(random.uniform(-0.3, 0.3), 3)
    ay = round(random.uniform(-0.3, 0.3), 3)
    az = round(random.uniform(0.8, 1.2), 3)   # gravity ~1g
    gx = round(random.uniform(-5, 5), 3)
    gy = round(random.uniform(-5, 5), 3)
    gz = round(random.uniform(-5, 5), 3)

    # 2% chance of fall (sudden jolt)
    if random.random() < 0.02:
        ax = round(random.uniform(2.5, 4.0), 3)
        ay = round(random.uniform(2.5, 4.0), 3)
        az = round(random.uniform(-0.5, 0.5), 3)
        print("  ⚠ FALL SIMULATED")

    return ax, ay, az, gx, gy, gz

def simulate():
    cycle = 0
    print("Simulator started — auto-fetching patients from DB...")

    while True:
        # re-fetch patient list every 10 cycles
        # so new registrations are picked up automatically
        if cycle % 10 == 0:
            patients = get_all_patients()
            if not patients:
                print("No patients in DB yet. Waiting...")
                time.sleep(3)
                cycle += 1
                continue
            print(f"Monitoring {len(patients)} patient(s): "
                  f"{[p['id'] for p in patients]}")

        for p in patients:
            pid      = p["id"]
            base_bpm = p.get("base_bpm", 72)

            bpm, spo2           = generate_vitals(base_bpm, cycle)
            ax, ay, az, gx, gy, gz = generate_motion()

            payload = {
                "patient_id": pid,
                "bpm":        bpm,
                "spo2":       spo2,
                "ax": ax, "ay": ay, "az": az,
                "gx": gx, "gy": gy, "gz": gz,
            }

            try:
                res = requests.post(f"{BASE_URL}/vitals", json=payload)
                data = res.json()
                score    = data.get("anomaly_score", 0)
                activity = data.get("activity", "unknown")
                fall     = data.get("fall_detected", False)
                print(f"{pid} | BPM:{bpm:5.1f} SpO2:{spo2:.1f}% "
                      f"score:{score:.2f} {activity}"
                      f"{' *** FALL ***' if fall else ''}")
            except Exception as e:
                print(f"Error for {pid}: {e}")

        time.sleep(1)
        cycle += 1

if __name__ == "__main__":
    simulate()