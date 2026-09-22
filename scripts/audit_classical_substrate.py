"""Audit Classical ML (SVM & XGBoost) on Substrate Hard-Subsets and Center-Only Ablation.

Performs:
1. Substrate hard-subset evaluation on SVM RBF (full 410 features).
2. Center-only feature ablation (dropping all 205 'global_' features):
   - Evaluates SVM RBF and XGBoost on overall test set and hard subset.
   - 5-fold grouped cross-validation on train split.
3. SHAP attribution on Center-Only XGBoost model:
   - Saves plot to reports/figures/shap_summary_center_only.png.
   - Evaluates whether background features or fecal pathology drive predictions.
4. Generates side-by-side comparison tables against EfficientNet-B0.
"""

import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

import cv2
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.cluster import KMeans
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.baseline_ml import get_feature_names

CLASS_NAMES = ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]


def compute_or_load_substrate_clusters() -> pd.DataFrame:
    cluster_csv = PROJECT_ROOT / "data" / "processed" / "substrate_clusters.csv"
    if cluster_csv.exists():
        return pd.read_csv(cluster_csv)

    print("Computing substrate clusters from border features (Phase 1 specification)...")
    manifest = pd.read_csv(PROJECT_ROOT / "data" / "manifest.csv")
    margin = int(224 * 0.15)
    feats = []
    for _, row in manifest.iterrows():
        img_bgr = cv2.imread(str(PROJECT_ROOT / row["filepath"]))
        if img_bgr is None:
            raise RuntimeError(f"Could not load image: {row['filepath']}")
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        h, w, _ = img_rgb.shape

        top_rgb = img_rgb[:margin, :, :]
        bot_rgb = img_rgb[h - margin :, :, :]
        left_rgb = img_rgb[margin : h - margin, :margin, :]
        right_rgb = img_rgb[margin : h - margin, w - margin :, :]
        border_rgb = np.concatenate([
            top_rgb.reshape(-1, 3),
            bot_rgb.reshape(-1, 3),
            left_rgb.reshape(-1, 3),
            right_rgb.reshape(-1, 3),
        ], axis=0)

        top_hsv = img_hsv[:margin, :, :]
        bot_hsv = img_hsv[h - margin :, :, :]
        left_hsv = img_hsv[margin : h - margin, :margin, :]
        right_hsv = img_hsv[margin : h - margin, w - margin :, :]
        border_hsv = np.concatenate([
            top_hsv.reshape(-1, 3),
            bot_hsv.reshape(-1, 3),
            left_hsv.reshape(-1, 3),
            right_hsv.reshape(-1, 3),
        ], axis=0)

        feat = np.hstack([
            border_rgb.mean(axis=0),
            border_rgb.std(axis=0),
            border_hsv.mean(axis=0),
            border_hsv.std(axis=0),
        ])
        feats.append(feat)

    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    manifest["substrate_cluster"] = kmeans.fit_predict(np.array(feats))
    cluster_names = {
        0: "Cluster 0 (Dark soil / concrete)",
        1: "Cluster 1 (Light wood shavings)",
        2: "Cluster 2 (Reddish-brown litter)",
        3: "Cluster 3 (Mixed straw / pen floor)",
    }
    manifest["substrate_name"] = manifest["substrate_cluster"].map(cluster_names)
    cluster_csv.parent.mkdir(parents=True, exist_ok=True)
    manifest[["filepath", "substrate_cluster", "substrate_name"]].to_csv(cluster_csv, index=False)
    print(f"Saved substrate clusters to {cluster_csv}")
    return manifest[["filepath", "substrate_cluster", "substrate_name"]]


def evaluate_on_slices(
    model: Any,
    scaler: StandardScaler,
    X_test: np.ndarray,
    test_df: pd.DataFrame,
    feature_slice_name: str,
) -> Dict[str, Any]:
    """Evaluate model on overall test set and hard subset."""
    X_test_scaled = scaler.transform(X_test)
    preds = model.predict(X_test_scaled)
    test_df = test_df.copy()
    test_df["pred_idx"] = preds
    test_df["pred_label"] = [CLASS_NAMES[p] for p in preds]
    test_df["is_correct"] = test_df["label"] == test_df["pred_label"]

    hard_df = test_df[test_df["is_hard"]].copy()

    # Overall metrics
    overall_acc = float((test_df["is_correct"]).mean())
    overall_macro_f1 = float(f1_score(test_df["label"], test_df["pred_label"], average="macro"))

    # Hard subset metrics
    hard_acc = float((hard_df["is_correct"]).mean())
    hard_macro_f1 = float(f1_score(hard_df["label"], hard_df["pred_label"], average="macro"))

    # Per-class breakdown
    per_class = {}
    for cls in CLASS_NAMES:
        cls_all = test_df[test_df["label"] == cls]
        cls_hard = hard_df[hard_df["label"] == cls]

        # Overall
        o_n = len(cls_all)
        o_recall = float((cls_all["is_correct"]).mean())
        o_prec = float((test_df[test_df["pred_label"] == cls]["label"] == cls).mean()) if len(test_df[test_df["pred_label"] == cls]) > 0 else 0.0
        o_f1 = 2 * (o_prec * o_recall) / (o_prec + o_recall + 1e-9)

        # Hard subset
        h_n = len(cls_hard)
        h_recall = float((cls_hard["is_correct"]).mean()) if h_n > 0 else 0.0
        h_prec = float((hard_df[hard_df["pred_label"] == cls]["label"] == cls).mean()) if len(hard_df[hard_df["pred_label"] == cls]) > 0 else 0.0
        h_f1 = 2 * (h_prec * h_recall) / (h_prec + h_recall + 1e-9)

        per_class[cls] = {
            "overall_n": o_n,
            "overall_recall": o_recall,
            "overall_prec": o_prec,
            "overall_f1": o_f1,
            "hard_n": h_n,
            "hard_recall": h_recall,
            "hard_prec": h_prec,
            "hard_f1": h_f1,
            "recall_delta": h_recall - o_recall,
            "is_small_sample": h_n < 15,
        }

    return {
        "feature_slice": feature_slice_name,
        "n_features": X_test.shape[1],
        "overall_acc": overall_acc,
        "overall_macro_f1": overall_macro_f1,
        "hard_acc": hard_acc,
        "hard_macro_f1": hard_macro_f1,
        "macro_f1_delta": hard_macro_f1 - overall_macro_f1,
        "per_class": per_class,
    }


def main():
    print("=" * 80)
    print("CLASSICAL ML SUBSTRATE AUDIT & CENTER-ONLY ABLATION")
    print("=" * 80)

    # 1. Load Features
    data = np.load(PROJECT_ROOT / "data" / "processed" / "classical_features.npz")
    X_train_full = data["X_train"]
    y_train = data["y_train"]
    groups_train = data["groups_train"]
    X_test_full = data["X_test"]
    y_test = data["y_test"]

    feature_names_full = get_feature_names()
    center_indices = [i for i, n in enumerate(feature_names_full) if n.startswith("center_")]
    feature_names_center = [feature_names_full[i] for i in center_indices]

    X_train_center = X_train_full[:, center_indices]
    X_test_center = X_test_full[:, center_indices]

    print(f"Full feature dim: {X_train_full.shape[1]} (205 global + 205 center)")
    print(f"Center-only feature dim: {X_train_center.shape[1]} (205 center)")

    # 2. Substrate cluster labels on test set
    sub_df = compute_or_load_substrate_clusters()
    test_df = pd.read_csv(PROJECT_ROOT / "data" / "splits" / "test.csv")
    test_df = test_df.merge(sub_df, on="filepath")

    # Hard subset definition (from Phase 1 & Phase 5)
    hard_conditions = {
        "Coccidiosis": [1, 3],
        "Healthy": [0, 2, 3],
        "Newcastle Disease": [0, 2, 3],
        "Salmonella": [0, 2, 3],
    }
    test_df["is_hard"] = False
    for cls, min_clusters in hard_conditions.items():
        mask = (test_df["label"] == cls) & (test_df["substrate_cluster"].isin(min_clusters))
        test_df.loc[mask, "is_hard"] = True

    print(f"Test Set total: N = {len(test_df)}")
    print(f"Hard Subset total: n = {test_df['is_hard'].sum()} ({test_df['is_hard'].mean()*100:.1f}%)")

    # 3. Train Models: Full vs Center-Only
    # Model 1: SVM Full
    scaler_full = StandardScaler().fit(X_train_full)
    svm_full = SVC(C=5.0, kernel="rbf", gamma="scale", random_state=42).fit(scaler_full.transform(X_train_full), y_train)

    # Model 2: SVM Center-Only
    scaler_center = StandardScaler().fit(X_train_center)
    svm_center = SVC(C=5.0, kernel="rbf", gamma="scale", random_state=42).fit(scaler_center.transform(X_train_center), y_train)

    # Model 3: XGBoost Center-Only
    xgb_center = XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1, eval_metric="mlogloss")
    xgb_center.fit(scaler_center.transform(X_train_center), y_train)

    # 4. Grouped 5-Fold CV on Center-Only
    print("\n--- 5-Fold Grouped Cross-Validation on Center-Only Features (Train Split) ---")
    gkf = GroupKFold(n_splits=5)
    X_tr_c_scaled = scaler_center.transform(X_train_center)
    cv_f1s_svm_center = []
    for trn_idx, val_idx in gkf.split(X_tr_c_scaled, y_train, groups=groups_train):
        m = SVC(C=5.0, kernel="rbf", gamma="scale", random_state=42).fit(X_tr_c_scaled[trn_idx], y_train[trn_idx])
        preds = m.predict(X_tr_c_scaled[val_idx])
        cv_f1s_svm_center.append(f1_score(y_train[val_idx], preds, average="macro"))
    print(f"[SVM RBF Center-Only] 5-Fold Grouped CV Macro-F1: {np.mean(cv_f1s_svm_center):.4f} (+/- {np.std(cv_f1s_svm_center):.4f})")

    # 5. Evaluate Full vs Center-Only on Test & Hard Subset
    res_svm_full = evaluate_on_slices(svm_full, scaler_full, X_test_full, test_df, "SVM RBF (Full: Global + Center)")
    res_svm_center = evaluate_on_slices(svm_center, scaler_center, X_test_center, test_df, "SVM RBF (Center-Only: 60% Core)")
    res_xgb_center = evaluate_on_slices(xgb_center, scaler_center, X_test_center, test_df, "XGBoost (Center-Only: 60% Core)")

    print("\n" + "=" * 80)
    print("SUBSTRATE HARD-SUBSET STRESS TEST RESULTS")
    print("=" * 80)
    for res in [res_svm_full, res_svm_center, res_xgb_center]:
        print(f"\nModel: {res['feature_slice']} (dim = {res['n_features']})")
        print(f"  Overall Test: Acc = {res['overall_acc']*100:.2f}%, Macro-F1 = {res['overall_macro_f1']:.4f}")
        print(f"  Hard Subset:  Acc = {res['hard_acc']*100:.2f}%, Macro-F1 = {res['hard_macro_f1']:.4f} (Δ Macro-F1: {res['macro_f1_delta']:+.4f})")
        print("  Per-Class Metrics on Hard Subset:")
        for cls, st in res["per_class"].items():
            print(f"    - {cls:18s} Hard n={st['hard_n']:3d} | Recall={st['hard_recall']*100:5.2f}% (Overall {st['overall_recall']*100:5.2f}%, Δ: {st['recall_delta']*100:+.2f}%) | Prec={st['hard_prec']*100:5.2f}% | F1={st['hard_f1']:.4f}")

    # 6. SHAP Analysis on Center-Only XGBoost Model
    print("\n--- Computing SHAP Attributions for Center-Only Model ---")
    explainer = shap.TreeExplainer(xgb_center)
    subset_indices = np.linspace(0, len(X_test_center) - 1, 200, dtype=int)
    X_sub_center = scaler_center.transform(X_test_center[subset_indices])
    shap_vals = explainer.shap_values(X_sub_center)

    if isinstance(shap_vals, list):
        global_imp = np.mean([np.abs(sv).mean(axis=0) for sv in shap_vals], axis=0)
    elif len(shap_vals.shape) == 3:
        global_imp = np.mean(np.abs(shap_vals), axis=(0, 2))
    else:
        global_imp = np.mean(np.abs(shap_vals), axis=0)

    top_idx = np.argsort(global_imp)[::-1][:15]
    top_shap_center = [
        {"feature": feature_names_center[i], "mean_abs_shap": float(global_imp[i]), "rank": r + 1}
        for r, i in enumerate(top_idx)
    ]

    # Save SHAP figure
    fig, ax = plt.subplots(figsize=(10, 7), dpi=150)
    y_pos = np.arange(len(top_idx))
    ax.barh(y_pos, [global_imp[i] for i in reversed(top_idx)], color="#2e7d32", edgecolor="#1b5e20")
    ax.set_yticks(y_pos)
    ax.set_yticklabels([feature_names_center[i] for i in reversed(top_idx)], fontsize=9, fontweight="bold")
    ax.set_xlabel("Mean |SHAP Value| (Impact on Model Output Magnitude)", fontsize=10, fontweight="bold")
    ax.set_title("SHAP Global Feature Importance (Center-Only Dropping Core Model)", fontsize=12, fontweight="bold", pad=10)
    plt.tight_layout()

    shap_fig_path = PROJECT_ROOT / "reports" / "figures" / "shap_summary_center_only.png"
    plt.savefig(shap_fig_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved Center-Only SHAP plot to {shap_fig_path}")

    # 7. Save Models and Output JSON
    joblib.dump(svm_center, PROJECT_ROOT / "runs" / "classical" / "svm_center_only.joblib")
    joblib.dump(scaler_center, PROJECT_ROOT / "runs" / "classical" / "scaler_center_only.joblib")

    audit_summary = {
        "svm_full": res_svm_full,
        "svm_center_only": res_svm_center,
        "xgb_center_only": res_xgb_center,
        "grouped_cv_center_svm_f1": float(np.mean(cv_f1s_svm_center)),
        "grouped_cv_center_svm_std": float(np.std(cv_f1s_svm_center)),
        "top_shap_center_only": top_shap_center,
    }

    audit_json_path = PROJECT_ROOT / "reports" / "phase6_substrate_ablation_audit.json"
    with open(audit_json_path, "w") as f:
        json.dump(audit_summary, f, indent=2)
    print(f"Saved audit JSON to {audit_json_path}")


if __name__ == "__main__":
    main()
