import os
import pickle
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping

SEQ_LEN = 30  # look at last 30 readings


def load_mitdb_bpm():
    try:
        import wfdb
    except Exception:
        return np.array([])

    records = ['100', '101', '102', '103', '104', '105']
    all_signals = []

    for rec in records:
        try:
            record = wfdb.rdrecord(f'./ml/data/{rec}')
            signal = record.p_signal[:, 0]

            # sample every 100 points to simulate ~1 reading/sec
            signal = signal[::100]

            all_signals.extend(signal.tolist())

        except Exception as e:
            print(f"Skipping record {rec}: {e}")
            continue

    return np.array(all_signals)


def create_sequences(data, seq_len):
    sequences = []

    for i in range(len(data) - seq_len):
        sequences.append(data[i:i + seq_len])

    return np.array(sequences)


def train():
    print("Loading data...")

    raw = load_mitdb_bpm()

    # Fallback to synthetic data if MIT-BIH files are unavailable
    if raw.size == 0:
        print("No MIT-BIH data found.")
        print("Generating synthetic BPM data...")

        n = 5000
        t = np.linspace(0, 200, n)

        base = 72 + 6 * np.sin(2 * np.pi * 0.03 * t)
        noise = np.random.normal(0, 1.5, size=n)

        raw = (base + noise).astype(float)

        rng = np.random.default_rng(12345)

        # occasional spikes
        for _ in range(30):
            idx = int(rng.integers(0, n))
            raw[idx:idx + 3] += rng.integers(20, 60)

    # Ensure enough samples
    if len(raw) <= SEQ_LEN:
        needed = SEQ_LEN + 50

        print(
            f"Data too short ({len(raw)} samples). "
            f"Extending to {needed} samples."
        )

        t = np.linspace(0, 50, needed)

        raw = (
            70
            + 4 * np.sin(2 * np.pi * 0.05 * t)
            + np.random.normal(0, 1.2, size=needed)
        ).astype(float)

    # Normalize
    scaler = MinMaxScaler()

    scaled = scaler.fit_transform(
        raw.reshape(-1, 1)
    ).flatten()

    # Create sequences
    X = create_sequences(scaled, SEQ_LEN)

    if X.size == 0:
        raise RuntimeError(
            "No sequences could be created. "
            "Check data and SEQ_LEN."
        )

    X = X.reshape((X.shape[0], X.shape[1], 1))

    print(f"Training on {len(X)} sequences...")

    # LSTM Autoencoder
    model = Sequential([
        LSTM(
            64,
            activation='relu',
            input_shape=(SEQ_LEN, 1),
            return_sequences=False
        ),
        RepeatVector(SEQ_LEN),
        LSTM(
            64,
            activation='relu',
            return_sequences=True
        ),
        TimeDistributed(Dense(1))
    ])

    model.compile(
        optimizer='adam',
        loss='mse'
    )

    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True
    )

    # Train model
    history = model.fit(
        X,
        X,
        epochs=20,
        batch_size=32,
        validation_split=0.1,
        callbacks=[early_stop],
        verbose=1
    )

    # Create save directory
    os.makedirs('./ml/saved', exist_ok=True)

    # Save loss curve
    plt.figure(figsize=(8, 5))

    plt.plot(
        history.history['loss'],
        label='Training Loss'
    )

    plt.plot(
        history.history['val_loss'],
        label='Validation Loss'
    )

    plt.xlabel('Epoch')
    plt.ylabel('MSE Loss')
    plt.title('Training vs Validation Loss')
    plt.legend()

    plt.savefig(
        './ml/saved/loss_curve.png',
        dpi=150,
        bbox_inches='tight'
    )

    plt.close()

    print("Loss curve saved to:")
    print("./ml/saved/loss_curve.png")

    # Save model
    model.save('./ml/saved/lstm_model.keras')

    # Save scaler
    with open('./ml/saved/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)

    # Calculate anomaly threshold
    preds = model.predict(X)

    errors = np.mean(
        np.abs(preds - X),
        axis=(1, 2)
    )

    threshold = np.percentile(
        errors,
        95
    )

    np.save(
        './ml/saved/threshold.npy',
        threshold
    )

    print(
        f"Training complete.\n"
        f"Anomaly threshold = {threshold:.6f}"
    )


if __name__ == "__main__":
    train()