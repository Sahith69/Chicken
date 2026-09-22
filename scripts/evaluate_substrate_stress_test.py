"""Substrate Stress-Test Evaluation for EfficientNet-B0.

Evaluates performance on minority substrate clusters (hard subsets) vs overall test set,
and generates Grad-CAM overlays for hard-subset images to assess spatial attention.
"""

import json
from pathlib import Path
import sys
import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sklearn.cluster import KMeans
from sklearn.metrics import classification_report, f1_score, precision_recall_fscore_support
import timm
import torch
from torchvision import transforms

from src.config import load_config
from src.data import get_dataloaders
from src.gradcam import GradCAM, resolve_target_layer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "reports" / "figures" / "gradcam" / "hard_subset"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def compute_border_features(manifest_path: Path, margin_frac: float = 0.15) -> np.ndarray:
    manifest = pd.read_csv(manifest_path)
    margin = int(224 * margin_frac)
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
    return np.array(feats)


def main():
    print("1. Extracting border features and clustering substrates...")
    manifest_path = PROJECT_ROOT / "data" / "manifest.csv"
    manifest = pd.read_csv(manifest_path)
    feats = compute_border_features(manifest_path)

    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    manifest["substrate_cluster"] = kmeans.fit_predict(feats)

    cluster_names = {
        0: "Cluster 0 (Dark soil / concrete)",
        1: "Cluster 1 (Light wood shavings)",
        2: "Cluster 2 (Reddish-brown litter)",
        3: "Cluster 3 (Mixed straw / pen floor)",
    }
    manifest["substrate_name"] = manifest["substrate_cluster"].map(cluster_names)

    test_df = pd.read_csv(PROJECT_ROOT / "data" / "splits" / "test.csv")
    test_df = test_df.merge(manifest[["filepath", "substrate_cluster", "substrate_name"]], on="filepath")

    # 2. Model inference
    print("2. Loading EfficientNet-B0 and evaluating on test set...")
    cfg = load_config()
    cfg["normalization"]["mode"] = "imagenet"
    _, _, test_loader, meta = get_dataloaders(config=cfg, batch_size=64, num_workers=0)
    class_names = cfg["classes"]

    model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=4)
    checkpoint_path = PROJECT_ROOT / "runs" / "20260920_215109_efficientnet_b0_weighted_ce" / "best_model.pth"
    state = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(state)
    model.eval()

    all_preds = []
    all_probs = []
    with torch.no_grad():
        for images, _, _ in test_loader:
            out = model(images)
            probs = torch.softmax(out, dim=-1)
            preds = torch.argmax(probs, dim=-1)
            all_preds.extend(preds.numpy())
            all_probs.extend(probs.numpy())

    test_df["pred"] = all_preds
    test_df["pred_label"] = [class_names[p] for p in all_preds]
    test_df["conf"] = [all_probs[i][all_preds[i]] for i in range(len(all_preds))]
    test_df["is_correct"] = test_df["label"] == test_df["pred_label"]

    # 3. Define Hard Subsets
    # Coccidiosis: majority = 0, 2 (71.3%); hard = 1, 3
    # Healthy: majority = 1 (86.5%); hard = 0, 2, 3
    # Newcastle: majority = 1 (59.6%); hard = 0, 2, 3
    # Salmonella: majority = 1 (56.4%); hard = 0, 2, 3
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

    hard_df = test_df[test_df["is_hard"]].copy()

    # Overall Metrics
    overall_acc = float((test_df["label"] == test_df["pred_label"]).mean())
    overall_macro_f1 = float(f1_score(test_df["label"], test_df["pred_label"], average="macro"))

    # Hard Subset Metrics
    hard_acc = float((hard_df["label"] == hard_df["pred_label"]).mean())
    hard_macro_f1 = float(f1_score(hard_df["label"], hard_df["pred_label"], average="macro"))

    print("\n" + "=" * 80)
    print("SUBSTRATE STRESS-TEST SUMMARY")
    print("=" * 80)
    print(f"Overall Test Set:  n = {len(test_df)}, Acc = {overall_acc*100:.2f}%, Macro-F1 = {overall_macro_f1:.4f}")
    print(f"Hard Subset:       n = {len(hard_df)} ({len(hard_df)/len(test_df)*100:.1f}%), Acc = {hard_acc*100:.2f}%, Macro-F1 = {hard_macro_f1:.4f}")
    print("=" * 80)

    # Per-Class Breakdown
    per_class_stats = {}
    for cls in class_names:
        cls_all = test_df[test_df["label"] == cls]
        cls_hard = hard_df[hard_df["label"] == cls]

        # Overall per-class
        overall_n = len(cls_all)
        overall_recall = float((cls_all["pred_label"] == cls).mean())
        # precision requires all predictions of cls
        overall_prec = float((test_df[test_df["pred_label"] == cls]["label"] == cls).mean()) if len(test_df[test_df["pred_label"] == cls]) > 0 else 0.0
        overall_f1 = 2 * (overall_prec * overall_recall) / (overall_prec + overall_recall + 1e-9)

        # Hard subset per-class
        hard_n = len(cls_hard)
        hard_recall = float((cls_hard["pred_label"] == cls).mean()) if hard_n > 0 else 0.0
        hard_prec = float((hard_df[hard_df["pred_label"] == cls]["label"] == cls).mean()) if len(hard_df[hard_df["pred_label"] == cls]) > 0 else 0.0
        hard_f1 = 2 * (hard_prec * hard_recall) / (hard_prec + hard_recall + 1e-9)

        # Breakdown across each minority cluster
        cluster_breakdown = {}
        for c in hard_conditions[cls]:
            c_subset = cls_hard[cls_hard["substrate_cluster"] == c]
            cn = len(c_subset)
            cr = float((c_subset["pred_label"] == cls).mean()) if cn > 0 else 0.0
            cluster_breakdown[c] = {
                "cluster_name": cluster_names[c],
                "n": cn,
                "recall": cr,
                "is_small_sample": cn < 15,
            }

        per_class_stats[cls] = {
            "overall_n": overall_n,
            "overall_recall": overall_recall,
            "overall_precision": overall_prec,
            "overall_f1": overall_f1,
            "hard_n": hard_n,
            "hard_recall": hard_recall,
            "hard_precision": hard_prec,
            "hard_f1": hard_f1,
            "recall_delta": hard_recall - overall_recall,
            "is_indicative_only": hard_n < 15,
            "cluster_breakdown": cluster_breakdown,
        }

        print(f"\nClass: {cls}")
        print(f"  Overall:  n = {overall_n:4d}, Recall = {overall_recall*100:5.2f}%, Precision = {overall_prec*100:5.2f}%, F1 = {overall_f1:.4f}")
        indicative_flag = " [INDICATIVE ONLY: n < 15]" if hard_n < 15 else ""
        print(f"  Hard Sub: n = {hard_n:4d}{indicative_flag}, Recall = {hard_recall*100:5.2f}%, Precision = {hard_prec*100:5.2f}%, F1 = {hard_f1:.4f} (Recall Δ: {(hard_recall-overall_recall)*100:+.2f}%)")
        print("  Minority Cluster Breakdown:")
        for c, c_info in cluster_breakdown.items():
            s_flag = " (n < 15: INDICATIVE ONLY)" if c_info["is_small_sample"] else ""
            print(f"    - {c_info['cluster_name']}: n = {c_info['n']:2d}{s_flag}, Recall = {c_info['recall']*100:5.2f}%")

    # 4. Grad-CAM Analysis on Hard Subsets
    print("\n4. Generating Grad-CAM overlays for Hard-Subset exemplars...")
    target_layer = resolve_target_layer(model, "efficientnet_b0")
    gradcam = GradCAM(model=model, target_layer=target_layer)

    cam_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # Select 16 exemplars (2 correct, 2 incorrect per class from hard_df)
    # If a class has fewer than 2 incorrect in hard_df, take as many as possible
    selected_exemplars = []
    for cls in class_names:
        cls_df = hard_df[hard_df["label"] == cls]
        corr = cls_df[cls_df["is_correct"]].head(2)
        incorr = cls_df[~cls_df["is_correct"]].head(2)
        selected_exemplars.extend(corr.to_dict("records"))
        selected_exemplars.extend(incorr.to_dict("records"))

    fig, axes = plt.subplots(4, 4, figsize=(18, 16), dpi=150)
    all_hard_center_energies = []
    exemplar_records = []

    for idx, row in enumerate(selected_exemplars):
        img_path = PROJECT_ROOT / row["filepath"]
        with Image.open(img_path) as raw_img:
            raw_rgb = np.array(raw_img.convert("RGB").resize((224, 224)))

        inp = cam_transform(Image.fromarray(raw_rgb)).unsqueeze(0)
        heatmap = gradcam.generate_heatmap(inp, target_class=row["pred"])
        overlay = gradcam.overlay_on_image(raw_rgb, heatmap, alpha=0.45)

        # Central 70% vs 15% outer border energy
        h, w = heatmap.shape
        by, bx = int(h * 0.15), int(w * 0.15)
        c_mask = np.zeros((h, w), dtype=bool)
        c_mask[by:h-by, bx:w-bx] = True
        c_energy = float(np.sum(heatmap[c_mask]) / (np.sum(heatmap) + 1e-6))
        all_hard_center_energies.append(c_energy)

        # Save individual overlay
        status_str = "correct" if row["is_correct"] else "incorrect"
        stem = Path(row["filepath"]).stem
        fn = f"hard_{row['label'].lower().replace(' ', '_')}_{status_str}_{stem}.png"
        Image.fromarray(overlay).save(OUTPUT_DIR / fn)

        r_idx = class_names.index(row["label"])
        # Find column in row for this class
        cls_items = [e for e in selected_exemplars if e["label"] == row["label"]]
        c_idx = cls_items.index(row)

        if r_idx < 4 and c_idx < 4:
            ax = axes[r_idx, c_idx]
            ax.imshow(overlay)
            ax.axis("off")
            status_title = "CORRECT" if row["is_correct"] else "WRONG"
            title_color = "#2e7d32" if row["is_correct"] else "#c62828"
            ax.set_title(
                f"[{status_title}] Pred: {row['pred_label']} ({row['conf']*100:.1f}%)\n"
                f"True: {row['label']}\n"
                f"{row['substrate_name'].split('(')[0].strip()}\n"
                f"Central Energy: {c_energy*100:.1f}%",
                fontsize=8,
                fontweight="bold",
                color=title_color,
                pad=4,
            )

        exemplar_records.append({
            "filepath": row["filepath"],
            "filename": fn,
            "label": row["label"],
            "pred": row["pred_label"],
            "conf": float(row["conf"]),
            "is_correct": bool(row["is_correct"]),
            "substrate_cluster": int(row["substrate_cluster"]),
            "substrate_name": row["substrate_name"],
            "central_energy": c_energy,
        })

    for r_idx, cls in enumerate(class_names):
        axes[r_idx, 0].set_ylabel(cls, fontsize=11, fontweight="bold")

    plt.suptitle(
        "Grad-CAM Attention on Hard Substrate Subsets (EfficientNet-B0)\n"
        "Visualizing spatial focus for droppings resting on atypical/minority pen substrates",
        fontsize=13,
        fontweight="bold",
        y=0.99,
    )
    plt.tight_layout()
    gallery_path = PROJECT_ROOT / "reports" / "figures" / "gradcam_hard_subset_gallery.png"
    plt.savefig(gallery_path, bbox_inches="tight")
    plt.close(fig)
    gradcam.remove_hooks()

    mean_hard_energy = float(np.mean(all_hard_center_energies))
    print(f"\nHard Subset Grad-CAM Gallery saved: {gallery_path}")
    print(f"Mean Central Energy on Hard Subset: {mean_hard_energy*100:.2f}%")

    # Save complete results to JSON
    output_summary = {
        "overall": {
            "n": len(test_df),
            "accuracy": overall_acc,
            "macro_f1": overall_macro_f1,
        },
        "hard_subset": {
            "n": len(hard_df),
            "pct_of_test": len(hard_df) / len(test_df),
            "accuracy": hard_acc,
            "macro_f1": hard_macro_f1,
            "mean_central_energy": mean_hard_energy,
        },
        "per_class": per_class_stats,
        "exemplars": exemplar_records,
    }

    report_json_path = PROJECT_ROOT / "reports" / "phase5_substrate_stress_test.json"
    with open(report_json_path, "w") as f:
        json.dump(output_summary, f, indent=2)
    print(f"Saved JSON summary: {report_json_path}")


if __name__ == "__main__":
    main()
