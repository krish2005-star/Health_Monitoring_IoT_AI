import numpy as np
import shap
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import io
import pickle
import os

from tensorflow.keras.models import load_model

# ============================================================
# GLOBALS
# ============================================================

model = None
scaler = None
explainer = None
background_data = None

# ============================================================
# FALLBACK IMAGE
# ============================================================

def _shap_unavailable_image(message: str) -> bytes:
    fig, ax = plt.subplots(figsize=(7, 2), facecolor='#0f172a')

    ax.text(
        0.5,
        0.5,
        message,
        ha='center',
        va='center',
        color='white',
        fontsize=11
    )

    ax.axis('off')

    buf = io.BytesIO()

    plt.savefig(
        buf,
        format='png',
        dpi=120,
        bbox_inches='tight',
        facecolor='#0f172a'
    )

    plt.close()

    buf.seek(0)

    return buf.read()

# ============================================================
# LOAD MODEL + SHAP
# ============================================================

def load_shap():

    global model
    global scaler
    global explainer
    global background_data

    try:

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        model_path = os.path.join(BASE_DIR, 'saved', 'lstm_model.keras')
        scaler_path = os.path.join(BASE_DIR, 'saved', 'scaler.pkl')

        model_path = os.path.abspath(model_path)
        scaler_path = os.path.abspath(scaler_path)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Missing model: {model_path}")

        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Missing scaler: {scaler_path}")

        # ----------------------------------------------------
        # LOAD MODEL
        # ----------------------------------------------------

        model = load_model(model_path)

        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)

        # ----------------------------------------------------
        # IMPORTANT:
        # USE REALISTIC BACKGROUND DATA
        # ----------------------------------------------------
        # Replace this later with real NORMAL training sequences
        # shape => (num_samples, 30)
        # ----------------------------------------------------

        background_data = np.random.normal(
            loc=70,
            scale=5,
            size=(20, 30)
        ).astype(np.float32)

        # scale background data
        background_data = scaler.transform(
            background_data.reshape(-1, 1)
        ).reshape(20, 30)

        # ----------------------------------------------------
        # MODEL PREDICTION FUNCTION
        # ----------------------------------------------------

        def model_predict(x):

            x_reshaped = x.reshape(-1, 30, 1)

            pred = model.predict(x_reshaped, verbose=0)

            # reconstruction error
            error = np.mean(
                np.abs(pred - x_reshaped),
                axis=(1, 2)
            )

            return error

        # ----------------------------------------------------
        # SHAP EXPLAINER
        # ----------------------------------------------------

        explainer = shap.KernelExplainer(
            model_predict,
            background_data
        )

        print("SHAP explainer loaded successfully")

    except Exception as e:

        explainer = None

        print(f"SHAP loading failed: {e}")

# ============================================================
# CLASSIFY ANOMALY TYPE
# ============================================================

def classify_anomaly(sequence):

    seq = np.array(sequence[-30:])

    max_hr = np.max(seq)
    min_hr = np.min(seq)

    delta = max_hr - min_hr

    std_dev = np.std(seq)

    if max_hr > 130 and delta > 40:
        return "Sudden Heart-Rate Spike Detected"

    elif std_dev > 18:
        return "High Heart-Rate Variability Detected"

    elif min_hr < 45:
        return "Abnormally Low Heart Rate Detected"

    else:
        return "Physiological Anomaly Detected"

# ============================================================
# GENERATE NATURAL LANGUAGE EXPLANATION
# ============================================================

def generate_explanation(sequence):

    seq = np.array(sequence[-30:])

    current_hr = seq[-1]
    max_hr = np.max(seq)
    min_hr = np.min(seq)

    avg_hr = np.mean(seq)

    delta = max_hr - min_hr

    std_dev = np.std(seq)

    explanation = (
        f"Heart rate changed from "
        f"{min_hr:.0f} BPM to {max_hr:.0f} BPM "
        f"(variation: {delta:.0f} BPM). "
        f"Average HR: {avg_hr:.1f} BPM. "
        f"Current HR: {current_hr:.0f} BPM. "
        f"Variability score: {std_dev:.1f}."
    )

    return explanation

# ============================================================
# MAIN SHAP PLOT FUNCTION
# ============================================================

def get_shap_plot(sequence: list) -> bytes:

    if explainer is None:
        return _shap_unavailable_image(
            "SHAP unavailable: model not loaded"
        )

    if not sequence or len(sequence) < 30:
        return _shap_unavailable_image(
            "Need at least 30 readings"
        )

    try:

        # ----------------------------------------------------
        # PREPARE INPUT
        # ----------------------------------------------------

        seq = np.array(sequence[-30:]).reshape(-1, 1)

        scaled = scaler.transform(seq).flatten()

        X = scaled.reshape(1, 30).astype(np.float32)

        # ----------------------------------------------------
        # SHAP VALUES
        # ----------------------------------------------------

        shap_vals = explainer.shap_values(
            X,
            nsamples=100
        )

        vals = shap_vals[0]

        # ----------------------------------------------------
        # TOP FEATURES
        # ----------------------------------------------------

        top_idx = np.argsort(np.abs(vals))[-10:][::-1]

        labels = [
            f"t-{30-i} ({sequence[-30:][i]:.0f} BPM)"
            for i in top_idx
        ]

        heights = vals[top_idx]

        # ----------------------------------------------------
        # COLORS
        # ----------------------------------------------------
        # RED => increases anomaly
        # GREEN => reduces anomaly
        # ----------------------------------------------------

        colors = [
            '#ef4444' if v > 0 else '#10b981'
            for v in heights
        ]

        # ----------------------------------------------------
        # ANOMALY ANALYSIS
        # ----------------------------------------------------

        anomaly_title = classify_anomaly(sequence)

        explanation = generate_explanation(sequence)

        max_change = np.max(
            np.abs(np.diff(sequence[-30:]))
        )

        # ----------------------------------------------------
        # PLOT
        # ----------------------------------------------------

        fig, ax = plt.subplots(
            figsize=(10, 5),
            facecolor='#111827'
        )

        ax.set_facecolor('#111827')

        # horizontal bars
        ax.barh(
            labels,
            heights,
            color=colors
        )

        # ----------------------------------------------------
        # STYLING
        # ----------------------------------------------------

        ax.tick_params(
            colors='white',
            labelsize=9
        )

        ax.set_xlabel(
            'SHAP Contribution',
            color='white',
            fontsize=10
        )

        ax.set_title(
            anomaly_title,
            color='white',
            fontsize=13,
            pad=15
        )

        # spines
        for spine in ax.spines.values():
            spine.set_edgecolor('#374151')

        # grid
        ax.grid(
            color='#374151',
            linestyle='--',
            linewidth=0.5,
            alpha=0.5
        )

        # ----------------------------------------------------
        # EXTRA METRICS
        # ----------------------------------------------------

        ax.text(
            0.01,
            1.08,
            f"Maximum Instant HR Change: {max_change:.1f} BPM",
            transform=ax.transAxes,
            color='#facc15',
            fontsize=9
        )

        # ----------------------------------------------------
        # NATURAL LANGUAGE EXPLANATION
        # ----------------------------------------------------

        fig.text(
            0.02,
            -0.03,
            explanation,
            color='white',
            fontsize=9
        )

        # ----------------------------------------------------
        # LEGEND
        # ----------------------------------------------------

        from matplotlib.patches import Patch

        legend_elements = [
            Patch(
                facecolor='#ef4444',
                label='Increased anomaly score'
            ),
            Patch(
                facecolor='#10b981',
                label='Reduced anomaly score'
            )
        ]

        ax.legend(
            handles=legend_elements,
            facecolor='#111827',
            edgecolor='#374151',
            labelcolor='white',
            fontsize=8,
            loc='lower right'
        )

        plt.tight_layout()

        # ----------------------------------------------------
        # SAVE IMAGE
        # ----------------------------------------------------

        buf = io.BytesIO()

        plt.savefig(
            buf,
            format='png',
            dpi=120,
            bbox_inches='tight',
            facecolor='#111827'
        )

        plt.close()

        buf.seek(0)

        return buf.read()

    except Exception as e:

        return _shap_unavailable_image(
            f"SHAP generation failed: {e}"
        )