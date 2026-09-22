"""Classical ML Baseline Pipeline (Phase 6).

Implements multi-colour-space, texture, and wavelet feature extraction:
- RGB, HSV, LAB colour histograms and statistical moments
- Local Binary Patterns (LBP) texture
- Gray-Level Co-occurrence Matrix (GLCM) second-order statistics
- 2D Discrete Wavelet Transform (DWT) multi-level energies
- Spatial pyramid decomposition (whole-image global + central dropping core)

Trains and evaluates:
- Random Forest
- XGBoost
- Support Vector Machine (RBF kernel)
Using 5-fold grouped cross-validation (group_id) on train and evaluating on the held-out test split.
Generates SHAP global feature attributions, confusion matrices, and latency/size benchmarks.
"""

from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import pywt
from scipy.stats import skew
import seaborn as sns
import shap
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

from src.config import load_config

CLASS_NAMES = ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]


def get_feature_names() -> List[str]:
    """Return explicit human-readable names for all 410 engineered features."""
    names = []
    regions = ["global", "center"]
    for region in regions:
        # 1. Histograms (16 bins * 3 channels * 3 spaces = 144)
        for space in ["rgb", "hsv", "lab"]:
            channels = ["r", "g", "b"] if space == "rgb" else (["h", "s", "v"] if space == "hsv" else ["l", "a", "b"])
            for ch in channels:
                for b in range(16):
                    names.append(f"{region}_{space}_{ch}_bin{b}")

        # 2. Color moments (3 channels * 3 spaces * 3 moments = 27)
        for space in ["rgb", "hsv", "lab"]:
            channels = ["r", "g", "b"] if space == "rgb" else (["h", "s", "v"] if space == "hsv" else ["l", "a", "b"])
            for ch in channels:
                names.append(f"{region}_{space}_{ch}_mean")
                names.append(f"{region}_{space}_{ch}_std")
                names.append(f"{region}_{space}_{ch}_skew")

        # 3. LBP (10 uniform bins)
        for b in range(10):
            names.append(f"{region}_lbp_bin{b}")

        # 4. GLCM (6 properties * 2 stats = 12)
        for prop in ["contrast", "dissimilarity", "homogeneity", "energy", "correlation", "ASM"]:
            names.append(f"{region}_glcm_{prop}_mean")
            names.append(f"{region}_glcm_{prop}_std")

        # 5. Wavelet energies (6 subbands * 2 stats = 12)
        for sub in ["cH2", "cV2", "cD2", "cH1", "cV1", "cD1"]:
            names.append(f"{region}_wavelet_{sub}_energy")
            names.append(f"{region}_wavelet_{sub}_std")

    return names


def extract_features_single(img_rel_path: str) -> np.ndarray:
    """Extract engineered features from a single image."""
    full_path = str(PROJECT_ROOT / img_rel_path)
    img_bgr = cv2.imread(full_path)
    if img_bgr is None:
        return np.zeros(410, dtype=np.float32)

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)

    h, w, _ = img_rgb.shape
    cy_start, cy_end = int(h * 0.2), int(h * 0.8)
    cx_start, cx_end = int(w * 0.2), int(w * 0.8)

    regions = [
        (img_rgb, hsv, lab),
        (img_rgb[cy_start:cy_end, cx_start:cx_end], hsv[cy_start:cy_end, cx_start:cx_end], lab[cy_start:cy_end, cx_start:cx_end]),
    ]

    feats = []
    for r_rgb, r_hsv, r_lab in regions:
        # 1. Color Histograms
        for c in range(3):
            h_c, _ = np.histogram(r_rgb[:, :, c], bins=16, range=(0, 256), density=True)
            feats.extend(h_c)
        for c in range(3):
            rng = (0, 180) if c == 0 else (0, 256)
            h_c, _ = np.histogram(r_hsv[:, :, c], bins=16, range=rng, density=True)
            feats.extend(h_c)
        for c in range(3):
            h_c, _ = np.histogram(r_lab[:, :, c], bins=16, range=(0, 256), density=True)
            feats.extend(h_c)

        # 2. Color Moments
        for arr in [r_rgb, r_hsv, r_lab]:
            for c in range(3):
                ch = arr[:, :, c].astype(np.float32)
                feats.append(float(np.mean(ch)))
                feats.append(float(np.std(ch)))
                feats.append(float(skew(ch.ravel())))

        # 3. LBP Texture
        gray = cv2.cvtColor(r_rgb, cv2.COLOR_RGB2GRAY)
        lbp = local_binary_pattern(gray, P=8, R=1, method="uniform")
        lbp_h, _ = np.histogram(lbp.ravel(), bins=10, range=(0, 10), density=True)
        feats.extend(lbp_h)

        # 4. GLCM Stats
        gray_q = (gray // 16).astype(np.uint8)
        glcm = graycomatrix(gray_q, distances=[1, 3], angles=[0, np.pi/4, np.pi/2, 3*np.pi/4], levels=16, symmetric=True, normed=True)
        for prop in ["contrast", "dissimilarity", "homogeneity", "energy", "correlation", "ASM"]:
            vals = graycoprops(glcm, prop)
            feats.append(float(vals.mean()))
            feats.append(float(vals.std()))

        # 5. Wavelet Energies
        coeffs = pywt.wavedec2(gray, "haar", level=2)
        _, (cH2, cV2, cD2), (cH1, cV1, cD1) = coeffs
        for sub in [cH2, cV2, cD2, cH1, cV1, cD1]:
            feats.append(float(np.mean(sub**2)))
            feats.append(float(np.std(sub)))

    arr = np.array(feats, dtype=np.float32)
    return np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)


def load_or_extract_features(cache_path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load cached features or extract from data splits."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        print(f"Loading cached classical features from {cache_path}...")
        data = np.load(cache_path)
        return data["X_train"], data["y_train"], data["groups_train"], data["X_test"], data["y_test"]

    print("Extracting classical features via multiprocessing...")
    train_df = pd.read_csv(PROJECT_ROOT / "data" / "splits" / "train.csv")
    test_df = pd.read_csv(PROJECT_ROOT / "data" / "splits" / "test.csv")

    cls2idx = {c: i for i, c in enumerate(CLASS_NAMES)}
    y_train = np.array([cls2idx[l] for l in train_df["label"]], dtype=np.int64)
    y_test = np.array([cls2idx[l] for l in test_df["label"]], dtype=np.int64)
    groups_train = train_df["group_id"].to_numpy()

    workers = os.cpu_count() or 4
    with ProcessPoolExecutor(max_workers=workers) as ex:
        X_train = list(ex.map(extract_features_single, train_df["filepath"].tolist()))
        X_test = list(ex.map(extract_features_single, test_df["filepath"].tolist()))

    X_train = np.array(X_train, dtype=np.float32)
    X_test = np.array(X_test, dtype=np.float32)

    np.savez_compressed(
        cache_path,
        X_train=X_train,
        y_train=y_train,
        groups_train=groups_train,
        X_test=X_test,
        y_test=y_test,
    )
    print(f"Extracted and saved: X_train={X_train.shape}, X_test={X_test.shape}")
    return X_train, y_train, groups_train, X_test, y_test


def run_grouped_cv(
    models: Dict[str, Any],
    X_train_scaled: np.ndarray,
    y_train: np.ndarray,
    groups: np.ndarray,
    n_splits: int = 5,
) -> Dict[str, Dict[str, Any]]:
    """Run 5-fold grouped cross validation reusing group_id."""
    gkf = GroupKFold(n_splits=n_splits)
    cv_results = {}

    for name, model in models.items():
        fold_f1s = []
        fold_accs = []
        for fold, (trn_idx, val_idx) in enumerate(gkf.split(X_train_scaled, y_train, groups=groups)):
            X_tr, y_tr = X_train_scaled[trn_idx], y_train[trn_idx]
            X_va, y_va = X_train_scaled[val_idx], y_train[val_idx]
            model.fit(X_tr, y_tr)
            preds = model.predict(X_va)
            fold_f1s.append(float(f1_score(y_va, preds, average="macro")))
            fold_accs.append(float((y_va == preds).mean()))

        cv_results[name] = {
            "mean_macro_f1": float(np.mean(fold_f1s)),
            "std_macro_f1": float(np.std(fold_f1s)),
            "mean_accuracy": float(np.mean(fold_accs)),
            "std_accuracy": float(np.std(fold_accs)),
            "fold_f1s": fold_f1s,
        }
        print(f"[{name}] 5-Fold Grouped CV Macro-F1: {cv_results[name]['mean_macro_f1']:.4f} (+/- {cv_results[name]['std_macro_f1']:.4f})")

    return cv_results


def evaluate_test_split(
    models: Dict[str, Any],
    X_train_scaled: np.ndarray,
    y_train: np.ndarray,
    X_test_scaled: np.ndarray,
    y_test: np.ndarray,
    model_save_dir: Path,
) -> Dict[str, Dict[str, Any]]:
    """Fit on train and evaluate on held-out test split."""
    model_save_dir.mkdir(parents=True, exist_ok=True)
    test_results = {}

    for name, model in models.items():
        t0 = time.time()
        model.fit(X_train_scaled, y_train)
        fit_time = time.time() - t0

        # Save model checkpoint
        ckpt_path = model_save_dir / f"{name.lower()}.joblib"
        joblib.dump(model, ckpt_path)
        size_mb = ckpt_path.stat().st_size / (1024 * 1024)

        # Measure pure prediction latency
        t_infer0 = time.time()
        preds = model.predict(X_test_scaled)
        t_infer = time.time() - t_infer0
        infer_latency_ms = (t_infer / len(X_test_scaled)) * 1000

        acc = float((y_test == preds).mean())
        macro_f1 = float(f1_score(y_test, preds, average="macro"))

        precisions, recalls, f1s, supports = precision_recall_fscore_support(y_test, preds, average=None)
        per_class = {}
        for i, cls in enumerate(CLASS_NAMES):
            per_class[cls] = {
                "precision": float(precisions[i]),
                "recall": float(recalls[i]),
                "f1": float(f1s[i]),
                "support": int(supports[i]),
            }

        cm = confusion_matrix(y_test, preds).tolist()

        test_results[name] = {
            "accuracy": acc,
            "macro_f1": macro_f1,
            "fit_time_sec": fit_time,
            "model_size_mb": size_mb,
            "classifier_latency_ms": infer_latency_ms,
            "checkpoint_path": str(ckpt_path.relative_to(PROJECT_ROOT)),
            "per_class": per_class,
            "confusion_matrix": cm,
            "predictions": preds,
        }
        print(f"\n[{name}] Test Set: Acc = {acc*100:.2f}%, Macro-F1 = {macro_f1:.4f}, Model Size = {size_mb:.2f} MB, Classifier Latency = {infer_latency_ms:.3f} ms/img")

    return test_results


def benchmark_end_to_end_latency(model: Any, scaler: StandardScaler, n_samples: int = 100) -> float:
    """Benchmark end-to-end CPU latency: image read + feature extraction + scaling + inference."""
    test_df = pd.read_csv(PROJECT_ROOT / "data" / "splits" / "test.csv")
    sample_paths = test_df["filepath"].head(n_samples).tolist()

    # Warmup
    _ = model.predict(scaler.transform([extract_features_single(sample_paths[0])]))

    t0 = time.time()
    for p in sample_paths:
        feat = extract_features_single(p)
        scaled_feat = scaler.transform([feat])
        _ = model.predict(scaled_feat)
    total_time = time.time() - t0
    return (total_time / n_samples) * 1000


def generate_shap_analysis(
    xgb_model: XGBClassifier,
    X_test_scaled: np.ndarray,
    feature_names: List[str],
    output_fig_path: Path,
    max_display: int = 15,
) -> List[Dict[str, Any]]:
    """Compute TreeExplainer SHAP attributions and save summary plot."""
    print("Computing SHAP attributions for XGBoost...")
    explainer = shap.TreeExplainer(xgb_model)
    # Use 200 representative test samples for fast, clean SHAP visualization
    subset_indices = np.linspace(0, len(X_test_scaled) - 1, 200, dtype=int)
    X_sub = X_test_scaled[subset_indices]

    shap_values = explainer.shap_values(X_sub)

    # Compute global importance (mean absolute SHAP value across all classes and samples)
    if isinstance(shap_values, list):
        # Multi-class list of arrays [n_samples, n_features]
        global_importance = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
    elif len(shap_values.shape) == 3:
        # Array of shape [n_samples, n_features, n_classes]
        global_importance = np.mean(np.abs(shap_values), axis=(0, 2))
    else:
        global_importance = np.mean(np.abs(shap_values), axis=0)

    top_indices = np.argsort(global_importance)[::-1][:max_display]
    top_features = [
        {"feature": feature_names[i], "mean_abs_shap": float(global_importance[i]), "rank": r + 1}
        for r, i in enumerate(top_indices)
    ]

    # Plot summary bar chart
    fig, ax = plt.subplots(figsize=(10, 7), dpi=150)
    y_pos = np.arange(len(top_indices))
    ax.barh(y_pos, [global_importance[i] for i in reversed(top_indices)], color="#1976d2", edgecolor="#0d47a1")
    ax.set_yticks(y_pos)
    ax.set_yticklabels([feature_names[i] for i in reversed(top_indices)], fontsize=9, fontweight="bold")
    ax.set_xlabel("Mean |SHAP Value| (Impact on Model Output Magnitude)", fontsize=10, fontweight="bold")
    ax.set_title("SHAP Global Feature Importance (XGBoost Classical Baseline)", fontsize=12, fontweight="bold", pad=10)
    plt.tight_layout()

    output_fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_fig_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved SHAP plot to {output_fig_path}")

    return top_features


def plot_classical_confusion_matrix(cm: List[List[int]], output_path: Path):
    """Plot dual raw and normalized confusion matrix for the best classical model."""
    cm_arr = np.array(cm)
    cm_norm = cm_arr.astype("float") / cm_arr.sum(axis=1)[:, np.newaxis]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=150)

    sns.heatmap(cm_arr, annot=True, fmt="d", cmap="Blues", xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, ax=axes[0])
    axes[0].set_title("Test Confusion Matrix (Raw Counts) — SVM RBF", fontsize=11, fontweight="bold")
    axes[0].set_ylabel("True Disease Label", fontsize=10, fontweight="bold")
    axes[0].set_xlabel("Predicted Disease Label", fontsize=10, fontweight="bold")

    sns.heatmap(cm_norm, annot=True, fmt=".2%", cmap="Blues", xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, ax=axes[1])
    axes[1].set_title("Test Confusion Matrix (Normalized Recall) — SVM RBF", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("True Disease Label", fontsize=10, fontweight="bold")
    axes[1].set_xlabel("Predicted Disease Label", fontsize=10, fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved confusion matrix to {output_path}")


def main():
    print("=" * 80)
    print("PHASE 6: CLASSICAL MACHINE LEARNING BASELINE PIPELINE")
    print("=" * 80)

    # 1. Feature Extraction & Caching
    cache_path = PROJECT_ROOT / "data" / "processed" / "classical_features.npz"
    X_train, y_train, groups_train, X_test, y_test = load_or_extract_features(cache_path)
    feature_names = get_feature_names()

    # 2. Scaling strictly on train split
    print("\nFitting StandardScaler strictly on training set (dataset normalization)...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    scaler_path = PROJECT_ROOT / "runs" / "classical" / "scaler.joblib"
    scaler_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, scaler_path)

    # 3. Model Definitions
    cv_models = {
        "RandomForest": RandomForestClassifier(n_estimators=200, max_depth=16, random_state=42, n_jobs=-1),
        "XGBoost": XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1, eval_metric="mlogloss"),
        "SVM_RBF": SVC(C=5.0, kernel="rbf", gamma="scale", random_state=42),
    }

    # 4. 5-Fold Grouped Cross-Validation
    print("\n--- 1. Running 5-Fold Grouped Cross-Validation on Train Split ---")
    cv_results = run_grouped_cv(cv_models, X_train_scaled, y_train, groups=groups_train)

    # 5. Held-Out Test Split Evaluation
    print("\n--- 2. Training Final Models & Evaluating Held-Out Test Set ---")
    eval_models = {
        "RandomForest": RandomForestClassifier(n_estimators=200, max_depth=16, random_state=42, n_jobs=-1),
        "XGBoost": XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1, eval_metric="mlogloss"),
        "SVM_RBF": SVC(C=5.0, kernel="rbf", gamma="scale", random_state=42),
    }
    model_dir = PROJECT_ROOT / "runs" / "classical"
    test_results = evaluate_test_split(eval_models, X_train_scaled, y_train, X_test_scaled, y_test, model_dir)

    # 6. End-to-End Latency Benchmark (Image Read + Feature Extraction + Scaling + Model Prediction)
    print("\n--- 3. Benchmarking End-to-End Latency ---")
    best_classical_name = "SVM_RBF" if test_results["SVM_RBF"]["macro_f1"] >= test_results["XGBoost"]["macro_f1"] else "XGBoost"
    best_model = eval_models[best_classical_name]
    e2e_latency = benchmark_end_to_end_latency(best_model, scaler, n_samples=100)
    print(f"End-to-End CPU Latency ({best_classical_name}): {e2e_latency:.2f} ms/image (incl. feature extraction)")

    # 7. SHAP Global Feature Attributions
    print("\n--- 4. Computing SHAP Global Feature Importance ---")
    shap_fig_path = PROJECT_ROOT / "reports" / "figures" / "shap_summary_classical.png"
    top_features = generate_shap_analysis(eval_models["XGBoost"], X_test_scaled, feature_names, shap_fig_path)

    # 8. Plot Best Classical Confusion Matrix
    cm_fig_path = PROJECT_ROOT / "reports" / "figures" / "confusion_matrix_classical_best.png"
    plot_classical_confusion_matrix(test_results["SVM_RBF"]["confusion_matrix"], cm_fig_path)

    # 9. Feature Selection Ablation (PCA & XGBoost top features)
    print("\n--- 5. Feature Selection Ablations ---")
    pca = PCA(n_components=0.95, random_state=42)
    X_tr_pca = pca.fit_transform(X_train_scaled)
    X_te_pca = pca.transform(X_test_scaled)
    svm_pca = SVC(C=5.0, kernel="rbf", gamma="scale", random_state=42).fit(X_tr_pca, y_train)
    pca_macro_f1 = float(f1_score(y_test, svm_pca.predict(X_te_pca), average="macro"))
    pca_acc = float((y_test == svm_pca.predict(X_te_pca)).mean())
    print(f"SVM + PCA 95% ({X_tr_pca.shape[1]} components): Acc = {pca_acc*100:.2f}%, Macro-F1 = {pca_macro_f1:.4f}")

    # 10. Compile JSON Summary
    # Remove numpy array predictions for JSON serialization
    for k in test_results:
        if "predictions" in test_results[k]:
            del test_results[k]["predictions"]

    benchmark_summary = {
        "dataset": {
            "n_features": X_train.shape[1],
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        },
        "grouped_cv": cv_results,
        "test_results": test_results,
        "feature_selection_ablation": {
            "pca_95_components": int(X_tr_pca.shape[1]),
            "pca_test_acc": pca_acc,
            "pca_test_macro_f1": pca_macro_f1,
        },
        "end_to_end_latency_ms": e2e_latency,
        "top_shap_features": top_features,
    }

    summary_path = PROJECT_ROOT / "reports" / "phase6_classical_benchmark.json"
    with open(summary_path, "w") as f:
        json.dump(benchmark_summary, f, indent=2)
    print(f"\nSaved complete benchmark summary to {summary_path}")


if __name__ == "__main__":
    main()
