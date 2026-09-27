import numpy as np
import shap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, pickle, os
from tensorflow.keras.models import load_model

model     = None
scaler    = None
explainer = None
SEQ_LEN   = 30


def _message_image(message: str) -> bytes:
    fig, ax = plt.subplots(figsize=(7, 1.5), facecolor='#0f172a')
    ax.text(0.5, 0.5, message,
            ha='center', va='center',
            color='#94a3b8', fontsize=10)
    ax.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100,
                bbox_inches='tight', facecolor='#0f172a')
    plt.close()
    buf.seek(0)
    return buf.read()


def _model_predict(x_flat):
    """
    Wrapper for SHAP KernelExplainer.
    Input:  (n, SEQ_LEN) flat array
    Output: (n,) reconstruction error per sample
    """
    x = x_flat.reshape(-1, SEQ_LEN, 1)
    pred  = model.predict(x, verbose=0)
    error = np.mean(np.abs(pred - x), axis=(1, 2))
    return error


def load_shap():
    global model, scaler, explainer

    try:
        BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
        model_path  = os.path.join(BASE_DIR, 'saved', 'lstm_model.keras')
        scaler_path = os.path.join(BASE_DIR, 'saved', 'scaler.pkl')

        if not os.path.exists(model_path):
            print(f"SHAP: model not found at {model_path}")
            return

        if not os.path.exists(scaler_path):
            print(f"SHAP: scaler not found at {scaler_path}")
            return

        model = load_model(model_path)

        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)

        # Background = realistic normalized BPM sequences
        # Normal BPM (60-90) normalizes to roughly 0.3-0.7
        bg = np.random.uniform(0.3, 0.7,
                               size=(50, SEQ_LEN)).astype(np.float32)

        explainer = shap.KernelExplainer(_model_predict, bg)
        print("SHAP explainer ready (KernelExplainer)")

    except Exception as e:
        model     = None
        explainer = None
        print(f"SHAP load failed: {e}")


load_shap()


def get_shap_plot(sequence: list) -> bytes:
    """
    Generate SHAP bar chart for the last SEQ_LEN BPM readings.
    Returns PNG bytes.
    """
    print(f"SHAP requested — sequence length: {len(sequence)}")

    if explainer is None:
        return _message_image(
            "SHAP unavailable — model not loaded. "
            "Run: python -m ml.train")

    if not sequence or len(sequence) < SEQ_LEN:
        return _message_image(
            f"Need {SEQ_LEN} readings for SHAP "
            f"(have {len(sequence)}). Keep monitoring...")

    # Prepare input
    recent = sequence[-SEQ_LEN:]
    seq    = np.array(recent).reshape(-1, 1)

    try:
        scaled = scaler.transform(seq).flatten()
    except Exception as e:
        return _message_image(f"Scaler error: {e}")

    X = scaled.reshape(1, SEQ_LEN).astype(np.float32)

    try:
        # nsamples=100 gives good accuracy vs speed tradeoff
        shap_vals = explainer.shap_values(X, nsamples=100)
        vals      = np.abs(shap_vals[0])  # shape: (SEQ_LEN,)

        # Top 10 most important timesteps
        top_n   = 10
        top_idx = np.argsort(vals)[-top_n:][::-1]

        # Human-readable labels: "2s ago (148 BPM)"
        labels      = []
        heights     = vals[top_idx]
        actual_bpms = []

        for idx in top_idx:
            secs_ago = SEQ_LEN - idx
            bpm_val  = recent[idx]
            labels.append(f"{secs_ago}s ago")
            actual_bpms.append(bpm_val)

        # Build chart
        fig, ax = plt.subplots(figsize=(9, 4), facecolor='#111827')

        colors = []
        for bpm_val in actual_bpms:
            if bpm_val > 120 or bpm_val < 45:
                colors.append('#ef4444')   # red — critical
            elif bpm_val > 100 or bpm_val < 55:
                colors.append('#f97316')   # orange — warning
            else:
                colors.append('#3b82f6')   # blue — normal

        bars = ax.barh(labels, heights, color=colors)

        # Add BPM annotation on each bar
        for bar, bpm_val in zip(bars, actual_bpms):
            ax.text(
                bar.get_width() + max(heights) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f'  {bpm_val:.0f} BPM',
                va='center',
                color='#e2e8f0',
                fontsize=9,
                fontweight='bold'
            )

        # Styling
        ax.set_facecolor('#111827')
        ax.set_xlim(0, max(heights) * 1.35)
        ax.tick_params(colors='white', labelsize=9)
        ax.set_xlabel('Contribution to anomaly score →',
                      color='#94a3b8', fontsize=9)
        ax.set_title(
            'SHAP — Which readings triggered this alert?',
            color='white', fontsize=11, pad=12, fontweight='bold')

        for spine in ax.spines.values():
            spine.set_edgecolor('#374151')

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#ef4444', label='Critical BPM'),
            Patch(facecolor='#f97316', label='Warning BPM'),
            Patch(facecolor='#3b82f6', label='Normal BPM'),
        ]
        ax.legend(handles=legend_elements,
                  loc='lower right',
                  facecolor='#1f2937',
                  labelcolor='white',
                  fontsize=8,
                  framealpha=0.8)

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120,
                    bbox_inches='tight', facecolor='#111827')
        plt.close()
        buf.seek(0)
        return buf.read()

    except Exception as e:
        print(f"SHAP compute error: {e}")
        return _message_image(f"SHAP compute error: {str(e)[:80]}")