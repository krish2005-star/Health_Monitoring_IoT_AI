import os
import pickle
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    LSTM, Dense, RepeatVector,
    TimeDistributed, Dropout
)
from tensorflow.keras.callbacks import EarlyStopping

SEQ_LEN = 60  # increased from 30 — more context = better detection


def load_mitdb_bpm():
    try:
        import wfdb
    except Exception:
        return np.array([])

    records = [
        '100','101','102','103','104','105',
        '106','107','108','109','111','112',
        '113','114','115','116','117','118',
        '119','121','122','123','124','200',
        '201','202','203','205','207','208',
        '209','210','212','213','214','215',
        '217','219','220','221','222','223',
        '228','230','231','232','233','234'
    ]

    all_bpm = []

    for rec in records:
        try:
            ann = wfdb.rdann(f'./ml/data/{rec}', 'atr')

            # keep only normal beats (N)
            normal_idx     = [i for i, s in enumerate(ann.symbol) if s == 'N']
            normal_samples = ann.sample[normal_idx]

            # convert RR intervals to BPM
            for i in range(1, len(normal_samples)):
                interval_sec = (normal_samples[i] - normal_samples[i-1]) / 360.0
                if 0.3 < interval_sec < 1.5:  # valid: 40-200 BPM
                    bpm = 60.0 / interval_sec
                    all_bpm.append(bpm)

            print(f"Record {rec}: {len(normal_samples)} normal beats")

        except Exception as e:
            print(f"Skip {rec}: {e}")

    print(f"\nTotal BPM values extracted: {len(all_bpm)}")
    return np.array(all_bpm)


def create_sequences(data, seq_len):
    sequences = []
    for i in range(len(data) - seq_len):
        sequences.append(data[i:i + seq_len])
    return np.array(sequences)


def train():
    print("Loading MIT-BIH BPM data...")
    raw = load_mitdb_bpm()

    # fallback to synthetic if no data found
    if raw.size == 0:
        print("No MIT-BIH data — generating synthetic BPM data...")
        n   = 5000
        t   = np.linspace(0, 200, n)
        raw = (72 + 6 * np.sin(2 * np.pi * 0.03 * t)
               + np.random.normal(0, 1.5, size=n)).astype(float)

    print(f"BPM range: {raw.min():.1f} - {raw.max():.1f}")
    print(f"BPM mean:  {raw.mean():.1f}")

    # normalize to 0-1
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(raw.reshape(-1, 1)).flatten()

    # create sequences
    X = create_sequences(scaled, SEQ_LEN)

    if X.size == 0:
        raise RuntimeError("No sequences created.")

    # Method 4 — use 30,000 sequences (was 10,000)
    if len(X) > 30000:
        idx = np.random.choice(len(X), 30000, replace=False)
        X   = X[idx]
        print(f"Subsampled to 30,000 sequences")

    X = X.reshape((X.shape[0], X.shape[1], 1))
    print(f"Training on {len(X)} sequences of length {SEQ_LEN}...")

    # Method 3 — deeper model with tanh + dropout
    model = Sequential([
        LSTM(128, activation='tanh',
             input_shape=(SEQ_LEN, 1),
             return_sequences=True),
        Dropout(0.2),
        LSTM(64, activation='tanh',
             return_sequences=False),
        RepeatVector(SEQ_LEN),
        LSTM(64, activation='tanh',
             return_sequences=True),
        Dropout(0.2),
        LSTM(128, activation='tanh',
             return_sequences=True),
        TimeDistributed(Dense(1))
    ])

    model.compile(optimizer='adam', loss='mse')
    model.summary()

    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=3,
        restore_best_weights=True
    )

    history = model.fit(
        X, X,
        epochs=10,
        batch_size=256,
        validation_split=0.1,
        callbacks=[early_stop],
        verbose=1
    )

    # save directory
    os.makedirs('./ml/saved', exist_ok=True)

    # save loss curve
    plt.figure(figsize=(8, 5))
    plt.plot(history.history['loss'],     label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('MSE Loss')
    plt.title('LSTM Autoencoder — Training vs Validation Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('./ml/saved/loss_curve.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Loss curve saved: ./ml/saved/loss_curve.png")

    # save model + scaler
    model.save('./ml/saved/lstm_model.keras')
    with open('./ml/saved/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)

    # Method 1 — threshold at 85th percentile (better balance)
    print("\nCalculating threshold on full dataset...")
    all_X = create_sequences(scaled, SEQ_LEN)
    all_X = all_X.reshape((all_X.shape[0], all_X.shape[1], 1))

    preds  = model.predict(all_X, batch_size=512, verbose=1)
    errors = np.mean(np.abs(preds - all_X), axis=(1, 2))

    threshold = np.percentile(errors, 85)  # was 95, then 80
    np.save('./ml/saved/threshold.npy', threshold)

    print(f"\n{'='*45}")
    print(f"Training complete!")
    print(f"Anomaly threshold (85th percentile): {threshold:.6f}")
    print(f"Error mean:  {errors.mean():.6f}")
    print(f"Error std:   {errors.std():.6f}")
    print(f"Error min:   {errors.min():.6f}")
    print(f"Error max:   {errors.max():.6f}")
    print(f"{'='*45}")
    print(f"\nSaved files:")
    print(f"  ./ml/saved/lstm_model.keras")
    print(f"  ./ml/saved/scaler.pkl")
    print(f"  ./ml/saved/threshold.npy")
    print(f"  ./ml/saved/loss_curve.png")


if __name__ == "__main__":
    train()