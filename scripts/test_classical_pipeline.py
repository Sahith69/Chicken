"""Test Classical ML Pipeline on Chicken Droppings Dataset.
Extracts multi-colour-space features (RGB/HSV/LAB histograms, LBP, GLCM, wavelets),
runs 5-fold GroupKFold cross-validation on train, and evaluates on held-out test split.
"""

import os
from pathlib import Path
import time
from concurrent.futures import ProcessPoolExecutor
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import pywt
from scipy.stats import skew
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def extract_features_single(img_path_str: str) -> np.ndarray:
    full_path = str(PROJECT_ROOT / img_path_str)
    img_bgr = cv2.imread(full_path)
    if img_bgr is None:
        return np.zeros(350, dtype=np.float32)

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)

    h, w, _ = img_rgb.shape
    # Center crop (central 60% of image where dropping is located)
    cy_start, cy_end = int(h * 0.2), int(h * 0.8)
    cx_start, cx_end = int(w * 0.2), int(w * 0.8)

    regions = [
        # (name, rgb, hsv, lab)
        ("global", img_rgb, hsv, lab),
        ("center", img_rgb[cy_start:cy_end, cx_start:cx_end], hsv[cy_start:cy_end, cx_start:cx_end], lab[cy_start:cy_end, cx_start:cx_end]),
    ]

    feats = []
    for _, r_rgb, r_hsv, r_lab in regions:
        # 1. Histograms: RGB, HSV, LAB (16 bins each = 16 * 9 = 144 per region)
        for c in range(3):
            hist, _ = np.histogram(r_rgb[:, :, c], bins=16, range=(0, 256), density=True)
            feats.extend(hist)
        for c in range(3):
            # HSV range: H is 0-180 in OpenCV, S, V are 0-256
            rng = (0, 180) if c == 0 else (0, 256)
            hist, _ = np.histogram(r_hsv[:, :, c], bins=16, range=rng, density=True)
            feats.extend(hist)
        for c in range(3):
            hist, _ = np.histogram(r_lab[:, :, c], bins=16, range=(0, 256), density=True)
            feats.extend(hist)

        # 2. Color moments: mean, std, skew for each channel (3 * 3 * 3 = 27 per region)
        for arr in [r_rgb, r_hsv, r_lab]:
            for c in range(3):
                ch = arr[:, :, c].astype(np.float32)
                feats.append(float(np.mean(ch)))
                feats.append(float(np.std(ch)))
                feats.append(float(skew(ch.ravel())))

        # 3. Grayscale Texture: LBP (10 uniform bins per region)
        gray = cv2.cvtColor(r_rgb, cv2.COLOR_RGB2GRAY)
        lbp = local_binary_pattern(gray, P=8, R=1, method="uniform")
        lbp_hist, _ = np.histogram(lbp.ravel(), bins=10, range=(0, 10), density=True)
        feats.extend(lbp_hist)

        # 4. GLCM stats (quantize to 16 levels: contrast, dissimilarity, homogeneity, energy, correlation, ASM)
        gray_q = (gray // 16).astype(np.uint8)
        glcm = graycomatrix(gray_q, distances=[1, 3], angles=[0, np.pi/4, np.pi/2, 3*np.pi/4], levels=16, symmetric=True, normed=True)
        for prop in ["contrast", "dissimilarity", "homogeneity", "energy", "correlation", "ASM"]:
            vals = graycoprops(glcm, prop)
            feats.append(float(vals.mean()))
            feats.append(float(vals.std()))

        # 5. Wavelet energies: Haar 2-level decomposition (6 sub-bands * 2 stats = 12 per region)
        coeffs = pywt.wavedec2(gray, "haar", level=2)
        _, (cH2, cV2, cD2), (cH1, cV1, cD1) = coeffs
        for sub in [cH2, cV2, cD2, cH1, cV1, cD1]:
            feats.append(float(np.mean(sub**2)))
            feats.append(float(np.std(sub)))

    return np.array(feats, dtype=np.float32)


def main():
    train_df = pd.read_csv(PROJECT_ROOT / "data" / "splits" / "train.csv")
    test_df = pd.read_csv(PROJECT_ROOT / "data" / "splits" / "test.csv")

    cache_file = PROJECT_ROOT / "data" / "processed" / "classical_features.npz"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    if cache_file.exists():
        print(f"Loading cached features from {cache_file}...")
        data = np.load(cache_file)
        X_train = data["X_train"]
        y_train = data["y_train"]
        groups_train = data["groups_train"]
        X_test = data["X_test"]
        y_test = data["y_test"]
    else:
        print("Extracting features using multiprocessing...")
        t0 = time.time()
        with ProcessPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
            X_train = list(executor.map(extract_features_single, train_df["filepath"].tolist()))
            X_test = list(executor.map(extract_features_single, test_df["filepath"].tolist()))
        X_train = np.array(X_train, dtype=np.float32)
        X_test = np.array(X_test, dtype=np.float32)

        class_names = ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]
        cls2idx = {c: i for i, c in enumerate(class_names)}
        y_train = np.array([cls2idx[l] for l in train_df["label"]], dtype=np.int64)
        y_test = np.array([cls2idx[l] for l in test_df["label"]], dtype=np.int64)
        groups_train = train_df["group_id"].to_numpy()

        np.savez_compressed(cache_file, X_train=X_train, y_train=y_train, groups_train=groups_train, X_test=X_test, y_test=y_test)
        print(f"Extracted and cached {len(X_train)} train and {len(X_test)} test features in {time.time()-t0:.1f}s. Feature dim: {X_train.shape[1]}")

    print(f"Features shape: X_train = {X_train.shape}, X_test = {X_test.shape}")

    # Standardize
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 5-fold GroupKFold
    gkf = GroupKFold(n_splits=5)
    class_names = ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]

    models = {
        "RandomForest": RandomForestClassifier(n_estimators=200, max_depth=16, random_state=42, n_jobs=-1),
        "XGBoost": XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1, eval_metric="mlogloss"),
        "SVM_RBF": SVC(C=5.0, kernel="rbf", gamma="scale", random_state=42, probability=True),
    }

    print("\n--- 5-Fold Grouped Cross-Validation on Train Split ---")
    for name, model in models.items():
        val_f1s = []
        for fold, (trn_idx, val_idx) in enumerate(gkf.split(X_train_scaled, y_train, groups=groups_train)):
            X_tr, y_tr = X_train_scaled[trn_idx], y_train[trn_idx]
            X_va, y_va = X_train_scaled[val_idx], y_train[val_idx]
            model.fit(X_tr, y_tr)
            preds = model.predict(X_va)
            f1 = f1_score(y_va, preds, average="macro")
            val_f1s.append(f1)
        print(f"[{name}] 5-Fold Grouped CV Macro-F1: {np.mean(val_f1s):.4f} (+/- {np.std(val_f1s):.4f})")

    print("\n--- Held-out Test Set Evaluation ---")
    for name, model in models.items():
        # Fit on entire train split
        t_start = time.time()
        model.fit(X_train_scaled, y_train)
        fit_time = time.time() - t_start

        # Inference speed test
        t_infer = time.time()
        test_preds = model.predict(X_test_scaled)
        total_infer_time = time.time() - t_infer
        per_img_ms = (total_infer_time / len(X_test_scaled)) * 1000

        acc = (y_test == test_preds).mean()
        macro_f1 = f1_score(y_test, test_preds, average="macro")
        print(f"\n[{name}]")
        print(f"  Accuracy:  {acc*100:.2f}%")
        print(f"  Macro-F1:  {macro_f1:.4f}")
        print(f"  Fit Time:  {fit_time:.2f}s")
        print(f"  Inference: {per_img_ms:.3f} ms/image")
        print(classification_report(y_test, test_preds, target_names=class_names, digits=4))


if __name__ == "__main__":
    main()
