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


def _shap_unavailable_image(message: str) -> bytes:
    """Return a small PNG with a helpful message when SHAP is unavailable."""
    fig, ax = plt.subplots(figsize=(6, 1.5), facecolor='#0f172a')
    ax.text(0.5, 0.5, message, ha='center', va='center', color='white', fontsize=10)
    ax.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='#0f172a')
    plt.close()
    buf.seek(0)
    return buf.read()


def load_shap():
    global model, scaler, explainer
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        model_path = os.path.join(BASE_DIR, 'saved', 'lstm_model.keras')
        scaler_path = os.path.join(BASE_DIR, 'saved', 'scaler.pkl')

        model_path = os.path.abspath(model_path)
        scaler_path = os.path.abspath(scaler_path)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Missing: {model_path}")

        model = load_model(model_path)
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)

        # use KernelExplainer — works with any model
        # background = small sample of normal sequences
        bg = np.random.randn(20, 30).astype(np.float32)

        def model_predict(x):
            """returns reconstruction error per sample"""
            x_reshaped = x.reshape(-1, 30, 1)
            pred = model.predict(x_reshaped, verbose=0)
            error = np.mean(np.abs(pred - x_reshaped), axis=(1, 2))
            return error

        explainer = shap.KernelExplainer(model_predict, bg)
        print("SHAP explainer ready (KernelExplainer)")

    except Exception as e:
        explainer = None
        print(f"SHAP load failed: {e}")


def get_shap_plot(sequence: list) -> bytes:
    if explainer is None:
        return _shap_unavailable_image("SHAP unavailable: model or artifacts missing")
    if not sequence or len(sequence) < 30:
        return _shap_unavailable_image("Not enough data (need 30 readings)")

    seq    = np.array(sequence[-30:]).reshape(-1, 1)
    scaled = scaler.transform(seq).flatten()
    X      = scaled.reshape(1, 30).astype(np.float32)

    try:
        shap_vals = explainer.shap_values(X, nsamples=50)
        vals      = np.abs(shap_vals[0])

        top_idx = np.argsort(vals)[-10:][::-1]
        labels  = [f"t-{30-i}" for i in top_idx]
        heights = vals[top_idx]

        fig, ax = plt.subplots(figsize=(8, 3), facecolor='#111827')
        ax.barh(labels, heights, color='#3b82f6')
        ax.set_facecolor('#111827')
        ax.tick_params(colors='white', labelsize=9)
        ax.set_xlabel('SHAP importance', color='white', fontsize=9)
        ax.set_title('Which readings caused this anomaly?',
                     color='white', fontsize=10)
        for spine in ax.spines.values():
            spine.set_edgecolor('#374151')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100,
                    bbox_inches='tight', facecolor='#111827')
        plt.close()
        buf.seek(0)
        return buf.read()

    except Exception as e:
        return _shap_unavailable_image(f"SHAP error: {e}")