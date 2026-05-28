import numpy as np
import pickle
from collections import defaultdict
from tensorflow.keras.models import load_model
import shap

# in-memory buffer — stores last 30 readings per patient
patient_buffers = defaultdict(list)

model    = None
scaler   = None
threshold = None

def load_artifacts():
    global model, scaler, threshold
    try:
        model     = load_model('./ml/saved/lstm_model.keras')
        with open('./ml/saved/scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        threshold = float(np.load('./ml/saved/threshold.npy'))
        print(f"ML model loaded. Threshold: {threshold:.4f}")
    except Exception as e:
        print(f"Model not found, using rule-based fallback: {e}")

load_artifacts()

def get_anomaly_score(patient_id: str, bpm: float, spo2: float) -> tuple[float, str]:
    # add to buffer
    patient_buffers[patient_id].append(bpm)

    # keep only last 30
    if len(patient_buffers[patient_id]) > 30:
        patient_buffers[patient_id].pop(0)

    buf = patient_buffers[patient_id]

    # not enough data yet — use simple rules
    if len(buf) < 30 or model is None:
        return rule_based_score(bpm, spo2)

    # normalize sequence
    seq = np.array(buf).reshape(-1, 1)
    seq_scaled = scaler.transform(seq).flatten()
    X = seq_scaled.reshape(1, 30, 1)

    # reconstruct and measure error
    pred = model.predict(X, verbose=0)
    error = float(np.mean(np.abs(pred - X)))

    # normalize score to 0-1
    score = min(error / (threshold * 2), 1.0)

    reason = build_reason(patient_id, bpm, spo2, score, buf)
    return score, reason

def rule_based_score(bpm: float, spo2: float) -> tuple[float, str]:
    if bpm > 130 or bpm < 45:
        return 0.9, f"BPM {bpm} is critically abnormal"
    if spo2 < 90:
        return 0.95, f"SpO2 {spo2}% is dangerously low"
    if spo2 < 94:
        return 0.7, f"SpO2 {spo2}% is below safe threshold"
    return 0.1, "Vitals within normal range"

def build_reason(patient_id, bpm, spo2, score, buf) -> str:
    avg = np.mean(buf[:-1])  # average of previous readings
    diff = abs(bpm - avg)

    if spo2 < 94:
        return f"SpO2 dropped to {spo2}% (below safe 94% threshold)"
    if bpm > avg + 30:
        return f"BPM spiked to {bpm} (patient avg: {avg:.0f}, jump of +{diff:.0f})"
    if bpm < avg - 20:
        return f"BPM dropped to {bpm} (patient avg: {avg:.0f}, drop of -{diff:.0f})"
    if score > 0.75:
        return f"Abnormal heart rate pattern detected (anomaly score: {score:.2f})"
    return f"Vitals normal (score: {score:.2f})"

def classify_activity(bpm: float) -> str:
    if bpm < 60:  return "sleeping"
    if bpm < 75:  return "resting"
    if bpm < 100: return "active"
    return "exercising"