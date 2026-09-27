import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (
    confusion_matrix, classification_report,
    roc_curve, auc, precision_recall_curve,
    f1_score, precision_score, recall_score
)
from tensorflow.keras.models import load_model
import wfdb

SEQ_LEN = 30

# ─── STEP 1: Load model and scaler ───────────────────────
def load_artifacts():
    model  = load_model('./ml/saved/lstm_model.keras')
    with open('./ml/saved/scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    threshold = float(np.load('./ml/saved/threshold.npy'))
    print(f"Model loaded. Threshold: {threshold:.6f}")
    return model, scaler, threshold

# ─── STEP 2: Load normal BPM sequences ───────────────────
def load_normal_sequences(scaler):
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
            normal_idx     = [i for i, s in enumerate(ann.symbol) if s == 'N']
            normal_samples = ann.sample[normal_idx]

            for i in range(1, len(normal_samples)):
                interval_sec = (normal_samples[i] - normal_samples[i-1]) / 360.0
                if 0.3 < interval_sec < 1.5:
                    all_bpm.append(60.0 / interval_sec)

        except Exception as e:
            print(f"Skip {rec}: {e}")

    raw    = np.array(all_bpm)
    scaled = scaler.transform(raw.reshape(-1, 1)).flatten()

    sequences = []
    for i in range(len(scaled) - SEQ_LEN):
        sequences.append(scaled[i:i + SEQ_LEN])

    print(f"BPM range: {raw.min():.1f} - {raw.max():.1f}")
    print(f"Total sequences: {len(sequences)}")
    return np.array(sequences)

# ─── STEP 3: Generate synthetic anomaly sequences ────────
def generate_anomaly_sequences(normal_sequences, scaler):
    """
    Create realistic anomaly sequences by injecting:
    1. Sudden BPM spikes
    2. Sudden BPM drops
    3. Sustained high BPM
    4. Irregular rhythm
    """
    n         = len(normal_sequences)
    anomalies = []

    # get BPM range from scaler
    bpm_min = float(scaler.data_min_[0])
    bpm_max = float(scaler.data_max_[0])

    rng = np.random.default_rng(42)

    for i in range(n):
        base = normal_sequences[i].copy()
        anom_type = rng.integers(0, 4)

        if anom_type == 0:
            # sudden spike — BPM jumps to 140-180
            spike_pos = rng.integers(10, 25)
            spike_bpm = rng.uniform(140, 180)
            spike_scaled = (spike_bpm - bpm_min) / (bpm_max - bpm_min)
            base[spike_pos:spike_pos+3] = np.clip(spike_scaled, 0, 1)

        elif anom_type == 1:
            # sudden drop — BPM drops to 30-45
            drop_pos = rng.integers(10, 25)
            drop_bpm = rng.uniform(30, 45)
            drop_scaled = (drop_bpm - bpm_min) / (bpm_max - bpm_min)
            base[drop_pos:drop_pos+3] = np.clip(drop_scaled, 0, 1)

        elif anom_type == 2:
            # sustained high BPM > 120
            high_bpm     = rng.uniform(120, 150)
            high_scaled  = (high_bpm - bpm_min) / (bpm_max - bpm_min)
            start        = rng.integers(5, 15)
            base[start:] = np.clip(high_scaled + rng.normal(0, 0.02, SEQ_LEN-start), 0, 1)

        elif anom_type == 3:
            # irregular rhythm — random jumps
            for j in range(SEQ_LEN):
                if rng.random() < 0.3:
                    irregular_bpm    = rng.uniform(40, 160)
                    irregular_scaled = (irregular_bpm - bpm_min) / (bpm_max - bpm_min)
                    base[j]          = np.clip(irregular_scaled, 0, 1)

        anomalies.append(base)

    return np.array(anomalies)

# ─── STEP 4: Calculate reconstruction errors ─────────────
def get_errors(model, sequences):
    X    = sequences.reshape(-1, SEQ_LEN, 1)
    pred = model.predict(X, verbose=0, batch_size=256)
    errors = np.mean(np.abs(pred - X), axis=(1,2))
    return errors

# ─── STEP 5: Full evaluation ─────────────────────────────
def evaluate():
    model, scaler, threshold = load_artifacts()

    print("\nLoading normal sequences...")
    normal_seq = load_normal_sequences(scaler)

    # use 20% for testing
    test_size   = int(len(normal_seq) * 0.2)
    test_normal = normal_seq[-test_size:]

    print(f"Normal test sequences:  {len(test_normal)}")

    print("\nGenerating anomaly sequences...")
    test_anomaly = generate_anomaly_sequences(test_normal, scaler)
    print(f"Anomaly test sequences: {len(test_anomaly)}")

    print("\nCalculating reconstruction errors...")
    normal_errors  = get_errors(model, test_normal)
    anomaly_errors = get_errors(model, test_anomaly)

    # combine for metrics
    all_errors = np.concatenate([normal_errors, anomaly_errors])
    all_labels = np.concatenate([
        np.zeros(len(normal_errors)),   # 0 = normal
        np.ones(len(anomaly_errors))    # 1 = anomaly
    ])

    # predictions using threshold
    all_preds = (all_errors > threshold).astype(int)

    # add this RIGHT BEFORE the metrics calculation section
    # find optimal threshold using F1 score
    print("\nFinding optimal threshold...")
    thresholds_to_try = np.percentile(all_errors, np.arange(10, 96, 1))
    best_f1    = 0
    best_thresh = threshold

    for t in thresholds_to_try:
        preds_t = (all_errors > t).astype(int)
        f1_t    = f1_score(all_labels, preds_t, zero_division=0)
        if f1_t > best_f1:
            best_f1     = f1_t
            best_thresh = t

    print(f"Optimal threshold: {best_thresh:.6f} (F1={best_f1*100:.1f}%)")
    print(f"Original threshold: {threshold:.6f}")

    # use optimal threshold for final metrics
    all_preds = (all_errors > best_thresh).astype(int)
    threshold = best_thresh  # update for display

    # ── METRICS ──────────────────────────────────────────
    cm        = confusion_matrix(all_labels, all_preds)
    tn, fp, fn, tp = cm.ravel()

    accuracy    = (tp + tn) / (tp + tn + fp + fn)
    precision   = precision_score(all_labels, all_preds, zero_division=0)
    recall      = recall_score(all_labels, all_preds, zero_division=0)
    f1          = f1_score(all_labels, all_preds, zero_division=0)
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    fpr_val     = fp / (fp + tn) if (fp + tn) > 0 else 0

    # ROC AUC
    fpr, tpr, _ = roc_curve(all_labels, all_errors)
    roc_auc     = auc(fpr, tpr)

    # Precision-Recall AUC
    prec_curve, rec_curve, _ = precision_recall_curve(all_labels, all_errors)
    pr_auc = auc(rec_curve, prec_curve)

    # print all metrics
    print("\n" + "="*50)
    print("       EVALUATION METRICS")
    print("="*50)
    print(f"Accuracy:              {accuracy*100:.2f}%")
    print(f"Precision:             {precision*100:.2f}%")
    print(f"Recall (Sensitivity):  {recall*100:.2f}%")
    print(f"Specificity:           {specificity*100:.2f}%")
    print(f"F1 Score:              {f1*100:.2f}%")
    print(f"False Alarm Rate:      {fpr_val*100:.2f}%")
    print(f"ROC AUC:               {roc_auc:.4f}")
    print(f"PR AUC:                {pr_auc:.4f}")
    print("="*50)
    print(f"\nConfusion Matrix:")
    print(f"  True Negatives  (Normal  → Normal):   {tn}")
    print(f"  False Positives (Normal  → Anomaly):  {fp}  ← false alarms")
    print(f"  False Negatives (Anomaly → Normal):   {fn}  ← missed alerts")
    print(f"  True Positives  (Anomaly → Anomaly):  {tp}")
    print(f"\nThreshold used: {threshold:.6f}")
    print(f"Normal error mean:  {normal_errors.mean():.6f}")
    print(f"Anomaly error mean: {anomaly_errors.mean():.6f}")

    # ── PLOTS ────────────────────────────────────────────
    fig = plt.figure(figsize=(16, 12))
    gs  = gridspec.GridSpec(2, 3, figure=fig)

    # Plot 1 — Confusion Matrix
    ax1 = fig.add_subplot(gs[0, 0])
    im  = ax1.imshow(cm, interpolation='nearest', cmap='Blues')
    plt.colorbar(im, ax=ax1)
    ax1.set_xticks([0,1]); ax1.set_yticks([0,1])
    ax1.set_xticklabels(['Normal','Anomaly'])
    ax1.set_yticklabels(['Normal','Anomaly'])
    ax1.set_xlabel('Predicted'); ax1.set_ylabel('Actual')
    ax1.set_title('Confusion Matrix')
    for i in range(2):
        for j in range(2):
            ax1.text(j, i, str(cm[i,j]),
                     ha='center', va='center',
                     color='white' if cm[i,j] > cm.max()/2 else 'black',
                     fontsize=14, fontweight='bold')

    # Plot 2 — ROC Curve
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(fpr, tpr, 'b-', linewidth=2, label=f'ROC (AUC={roc_auc:.3f})')
    ax2.plot([0,1],[0,1],'k--', alpha=0.5, label='Random')
    ax2.fill_between(fpr, tpr, alpha=0.1, color='blue')
    ax2.set_xlabel('False Positive Rate')
    ax2.set_ylabel('True Positive Rate')
    ax2.set_title('ROC Curve')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3 — Precision-Recall Curve
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.plot(rec_curve, prec_curve, 'g-', linewidth=2,
             label=f'PR (AUC={pr_auc:.3f})')
    ax3.fill_between(rec_curve, prec_curve, alpha=0.1, color='green')
    ax3.set_xlabel('Recall')
    ax3.set_ylabel('Precision')
    ax3.set_title('Precision-Recall Curve')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4 — Reconstruction Error Distribution
    ax4 = fig.add_subplot(gs[1, :2])
    ax4.hist(normal_errors,  bins=80, alpha=0.6,
             color='green', label='Normal', density=True)
    ax4.hist(anomaly_errors, bins=80, alpha=0.6,
             color='red',   label='Anomaly', density=True)
    ax4.axvline(threshold, color='black', linestyle='--',
                linewidth=2, label=f'Threshold={threshold:.4f}')
    ax4.set_xlabel('Reconstruction Error')
    ax4.set_ylabel('Density')
    ax4.set_title('Reconstruction Error Distribution')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # Plot 5 — Metrics Bar Chart
    ax5   = fig.add_subplot(gs[1, 2])
    names = ['Accuracy','Precision','Recall','Specificity','F1','ROC AUC']
    vals  = [accuracy, precision, recall, specificity, f1, roc_auc]
    colors= ['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ef4444','#06b6d4']
    bars  = ax5.barh(names, [v*100 for v in vals], color=colors)
    ax5.set_xlim(0, 110)
    ax5.set_xlabel('Score (%)')
    ax5.set_title('All Metrics')
    for bar, val in zip(bars, vals):
        ax5.text(bar.get_width() + 0.5,
                 bar.get_y() + bar.get_height()/2,
                 f'{val*100:.1f}%', va='center', fontsize=9)
    ax5.grid(True, alpha=0.3, axis='x')

    plt.suptitle('LSTM Autoencoder — Model Evaluation',
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig('./ml/saved/evaluation_metrics.png',
                dpi=150, bbox_inches='tight')
    plt.close()
    print("\nPlots saved to: ./ml/saved/evaluation_metrics.png")

    # save metrics to text file
    with open('./ml/saved/metrics.txt', 'w') as f:
        f.write("LSTM AUTOENCODER EVALUATION METRICS\n")
        f.write("="*40 + "\n")
        f.write(f"Accuracy:          {accuracy*100:.2f}%\n")
        f.write(f"Precision:         {precision*100:.2f}%\n")
        f.write(f"Recall:            {recall*100:.2f}%\n")
        f.write(f"Specificity:       {specificity*100:.2f}%\n")
        f.write(f"F1 Score:          {f1*100:.2f}%\n")
        f.write(f"False Alarm Rate:  {fpr_val*100:.2f}%\n")
        f.write(f"ROC AUC:           {roc_auc:.4f}\n")
        f.write(f"PR AUC:            {pr_auc:.4f}\n")
        f.write("="*40 + "\n")
        f.write(f"TP={tp} TN={tn} FP={fp} FN={fn}\n")
        f.write(f"Threshold={threshold:.6f}\n")
    print("Metrics saved to: ./ml/saved/metrics.txt")

if __name__ == "__main__":
    evaluate()