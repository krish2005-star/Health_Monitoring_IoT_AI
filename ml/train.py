import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping
import pickle, os

SEQ_LEN = 30  # look at last 30 readings

def load_mitdb_bpm():
    try:
        import wfdb
    except Exception:
        # wfdb not installed — caller should handle fallback
        return np.array([])

    records = ['100','101','102','103','104','105']
    all_signals = []
    for rec in records:
        try:
            record = wfdb.rdrecord(f'./ml/data/{rec}')
            signal = record.p_signal[:, 0]
            # sample every 100 points to simulate 1/sec readings
            signal = signal[::100]
            all_signals.extend(signal.tolist())
        except Exception:
            # missing files or read error -> skip
            continue
    return np.array(all_signals)

def create_sequences(data, seq_len):
    sequences = []
    for i in range(len(data) - seq_len):
        sequences.append(data[i:i+seq_len])
    return np.array(sequences)

def train():
    print("Loading data...")
    raw = load_mitdb_bpm()

    # If no real data was loaded (common in a fresh workspace), synthesize a plausible BPM signal
    if raw.size == 0:
        print("No MIT‑BIH data found — generating synthetic BPM signal for local training.")
        # generate ~5000 samples (~1 sample/sec -> ~1.5 hours) with slow baseline oscillation
        n = 5000
        t = np.linspace(0, 200, n)
        base = 72 + 6 * np.sin(2 * np.pi * 0.03 * t)  # slow breathing/variation
        noise = np.random.normal(0, 1.5, size=n)
        raw = (base + noise).astype(float)
        # insert occasional tachycardia spikes for variety
        rng = np.random.default_rng(12345)
        for _ in range(30):
            i = int(rng.integers(0, n))
            raw[i:i+3] += rng.integers(20, 60)

    # ensure we have enough samples for at least one sequence
    if len(raw) <= SEQ_LEN:
        needed = SEQ_LEN + 50
        print(f"Data too short ({len(raw)} samples). Extending synthetic data to {needed} samples.")
        t = np.linspace(0, 50, needed)
        raw = (70 + 4 * np.sin(2 * np.pi * 0.05 * t) + np.random.normal(0, 1.2, size=needed)).astype(float)

    # normalize
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(raw.reshape(-1,1)).flatten()

    # create sequences
    X = create_sequences(scaled, SEQ_LEN)
    if X.size == 0:
        raise RuntimeError("No sequences could be created for training. Check data and SEQ_LEN.")
    X = X.reshape((X.shape[0], X.shape[1], 1))

    print(f"Training on {len(X)} sequences...")

    # LSTM autoencoder — learns to reconstruct normal sequences
    # high reconstruction error = anomaly
    model = Sequential([
        LSTM(64, activation='relu', input_shape=(SEQ_LEN, 1), return_sequences=False),
        RepeatVector(SEQ_LEN),
        LSTM(64, activation='relu', return_sequences=True),
        TimeDistributed(Dense(1))
    ])
    model.compile(optimizer='adam', loss='mse')

    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    model.fit(X, X,
              epochs=2,
              batch_size=32,
              validation_split=0.1,
              callbacks=[early_stop],
              verbose=1)

    os.makedirs('./ml/saved', exist_ok=True)
    model.save('./ml/saved/lstm_model.keras')
    with open('./ml/saved/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)

    # calculate threshold from training data
    preds = model.predict(X)
    errors = np.mean(np.abs(preds - X), axis=(1,2))
    threshold = np.percentile(errors, 95)  # top 5% = anomaly
    np.save('./ml/saved/threshold.npy', threshold)

    print(f"Training complete. Anomaly threshold: {threshold:.4f}")

if __name__ == "__main__":
    train()