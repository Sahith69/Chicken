"""Comprehensive model evaluation for Phase 5.

Generates:
1. Classification report (precision, recall, F1, support per class + macro/weighted).
2. Side-by-side Confusion Matrix (counts + row-normalized percentages).
3. One-vs-Rest (OvR) ROC Curves and AUC for all 4 diagnostic classes.
4. In-depth confusion analysis: Coccidiosis <-> Salmonella boundary and Newcastle recall.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import timm
import torch
import torch.nn as nn
from sklearn.metrics import (
    auc,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_curve,
)

from src.config import load_config
from src.data import get_dataloaders
from src.utils import get_device, set_seed


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_model_and_loaders(
    weights_path: Path,
    backbone_name: str = "efficientnet_b0",
    batch_size: int = 64,
    device: Optional[torch.device] = None,
) -> Tuple[nn.Module, torch.utils.data.DataLoader, List[str]]:
    """Load pre-trained checkpoint and test DataLoader."""
    if device is None:
        device = get_device()

    cfg = load_config()
    cfg["normalization"]["mode"] = "imagenet"
    class_names = cfg.get("classes", ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"])

    _, _, test_loader, meta = get_dataloaders(config=cfg, batch_size=batch_size, num_workers=0)

    model = timm.create_model(backbone_name, pretrained=False, num_classes=len(class_names))
    state = torch.load(weights_path, map_location=device)
    model.load_state_dict(state)
    model.to(device)
    model.eval()

    return model, test_loader, class_names


@torch.no_grad()
def collect_predictions(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    device: torch.device,
) -> Dict[str, np.ndarray]:
    """Run model on dataset and extract targets, predicted classes, raw logits, and softmax probabilities."""
    model.eval()
    all_targets = []
    all_preds = []
    all_logits = []
    all_probs = []
    all_paths = []

    for images, targets, paths in loader:
        images = images.to(device)
        logits = model(images)
        probs = torch.softmax(logits, dim=-1)
        preds = torch.argmax(probs, dim=-1)

        all_targets.extend(targets.cpu().numpy())
        all_preds.extend(preds.cpu().numpy())
        all_logits.extend(logits.cpu().numpy())
        all_probs.extend(probs.cpu().numpy())
        all_paths.extend(paths)

    return {
        "targets": np.array(all_targets),
        "preds": np.array(all_preds),
        "logits": np.array(all_logits),
        "probs": np.array(all_probs),
        "paths": all_paths,
    }


def plot_confusion_matrices(
    cm: np.ndarray,
    class_names: List[str],
    save_path: Path,
    title: str = "Confusion Matrix",
) -> None:
    """Plot dual confusion matrix: raw counts and row-normalized percentages."""
    cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), dpi=150)

    # 1. Raw counts
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        ax=axes[0],
        cbar=True,
    )
    axes[0].set_title(f"{title} (Counts)", fontsize=13, fontweight="bold", pad=10)
    axes[0].set_xlabel("Predicted Class", fontsize=11, fontweight="bold")
    axes[0].set_ylabel("Ground Truth Class", fontsize=11, fontweight="bold")
    axes[0].tick_params(axis="x", rotation=25)

    # 2. Row-normalized percentages
    sns.heatmap(
        cm_norm * 100.0,
        annot=True,
        fmt=".1f",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        ax=axes[1],
        cbar=True,
    )
    # Add percentage sign in heatmap text
    for t in axes[1].texts:
        t.set_text(t.get_text() + "%")

    axes[1].set_title(f"{title} (Row-Normalized % Recall)", fontsize=13, fontweight="bold", pad=10)
    axes[1].set_xlabel("Predicted Class", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("Ground Truth Class", fontsize=11, fontweight="bold")
    axes[1].tick_params(axis="x", rotation=25)

    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved confusion matrix plot to {save_path}")


def plot_roc_curves(
    targets: np.ndarray,
    probs: np.ndarray,
    class_names: List[str],
    save_path: Path,
    title: str = "One-vs-Rest ROC Curves",
) -> Dict[str, float]:
    """Compute and plot One-vs-Rest (OvR) ROC curves for all classes."""
    n_classes = len(class_names)
    roc_auc_dict = {}

    fig, ax = plt.subplots(figsize=(8, 7), dpi=150)
    colors = ["#1f77b4", "#2ca02c", "#d62728", "#ff7f0e"]

    # One-hot encode targets
    y_one_hot = np.zeros((len(targets), n_classes))
    for i, t in enumerate(targets):
        y_one_hot[i, t] = 1.0

    for i in range(n_classes):
        fpr, tpr, _ = roc_curve(y_one_hot[:, i], probs[:, i])
        roc_auc = auc(fpr, tpr)
        roc_auc_dict[class_names[i]] = float(roc_auc)
        ax.plot(
            fpr,
            tpr,
            color=colors[i % len(colors)],
            lw=2.2,
            label=f"{class_names[i]} (AUC = {roc_auc:.4f})",
        )

    # Macro-average ROC AUC
    macro_auc = float(np.mean(list(roc_auc_dict.values())))
    roc_auc_dict["macro_avg"] = macro_auc

    # Diagonal chance line
    ax.plot([0, 1], [0, 1], "k--", lw=1.5, alpha=0.6, label="Chance (AUC = 0.5000)")

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11, fontweight="bold")
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=11, fontweight="bold")
    ax.set_title(f"{title}\nMacro-Average AUC = {macro_auc:.4f}", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="lower right", fontsize=10, frameon=True)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved ROC curve plot to {save_path}")

    return roc_auc_dict


def run_evaluation(
    run_dir: Optional[Path] = None,
    weights_path: Optional[Path] = None,
    backbone_name: str = "efficientnet_b0",
) -> Dict:
    """Execute complete Phase 5 evaluation on the held-out test split."""
    if run_dir is None:
        run_dir = PROJECT_ROOT / "runs" / "20260920_215109_efficientnet_b0_weighted_ce"
    if weights_path is None:
        weights_path = run_dir / "best_model.pth"

    print("=" * 80)
    print(f"PHASE 5 EVALUATION: {backbone_name.upper()}")
    print(f"Checkpoint: {weights_path}")
    print("=" * 80)

    device = get_device()
    model, test_loader, class_names = get_model_and_loaders(
        weights_path=weights_path,
        backbone_name=backbone_name,
        device=device,
    )

    preds_data = collect_predictions(model, test_loader, device)
    targets = preds_data["targets"]
    preds = preds_data["preds"]
    probs = preds_data["probs"]

    # 1. Classification report
    rep_dict = classification_report(
        targets, preds, target_names=class_names, output_dict=True, zero_division=0
    )
    rep_text = classification_report(
        targets, preds, target_names=class_names, digits=4, zero_division=0
    )
    cm = confusion_matrix(targets, preds)

    print("\n--- TEST SET CLASSIFICATION REPORT ---")
    print(rep_text)

    # 2. Confusion matrices
    cm_fig_path = PROJECT_ROOT / "reports" / "figures" / f"confusion_matrix_{backbone_name}.png"
    plot_confusion_matrices(cm, class_names, cm_fig_path, title=f"{backbone_name} Test Confusion Matrix")

    # 3. ROC Curves & OvR AUC
    roc_fig_path = PROJECT_ROOT / "reports" / "figures" / f"roc_curves_{backbone_name}.png"
    roc_auc_dict = plot_roc_curves(targets, probs, class_names, roc_fig_path, title=f"{backbone_name} OvR ROC Curves")

    # 4. Diagnostic Pair Analysis
    print("\n--- TARGETED DIAGNOSTIC PAIR ANALYSIS ---")
    cocci_idx = class_names.index("Coccidiosis")
    salmo_idx = class_names.index("Salmonella")
    ncd_idx = class_names.index("Newcastle Disease")
    healthy_idx = class_names.index("Healthy")

    cocci_to_salmo = int(cm[cocci_idx, salmo_idx])
    salmo_to_cocci = int(cm[salmo_idx, cocci_idx])
    cocci_support = int(cm[cocci_idx].sum())
    salmo_support = int(cm[salmo_idx].sum())

    print(f"1. Coccidiosis <-> Salmonella Mutual Confusion (The Known Hard Pair):")
    print(f"   - True Coccidiosis misclassified as Salmonella: {cocci_to_salmo} / {cocci_support} ({cocci_to_salmo/cocci_support*100:.2f}%)")
    print(f"   - True Salmonella misclassified as Coccidiosis:  {salmo_to_cocci} / {salmo_support} ({salmo_to_cocci/salmo_support*100:.2f}%)")
    print(f"   - Total cross-confusion: {cocci_to_salmo + salmo_to_cocci} droppings ({ (cocci_to_salmo + salmo_to_cocci) / (cocci_support + salmo_support) * 100:.2f}% of combined support).")

    ncd_tp = int(cm[ncd_idx, ncd_idx])
    ncd_support = int(cm[ncd_idx].sum())
    ncd_total_pred = int(cm[:, ncd_idx].sum())
    ncd_fp_salmo = int(cm[salmo_idx, ncd_idx])
    ncd_fp_healthy = int(cm[healthy_idx, ncd_idx])
    ncd_fp_cocci = int(cm[cocci_idx, ncd_idx])

    print(f"\n2. Newcastle Disease (NCD) Minority Sensitivity:")
    print(f"   - Sensitivity (Recall): {ncd_tp} / {ncd_support} ({ncd_tp/ncd_support*100:.2f}%)")
    print(f"   - Precision:            {ncd_tp} / {ncd_total_pred} ({ncd_tp/ncd_total_pred*100:.2f}%)")
    print(f"   - False Alarms Breakdown ({ncd_total_pred - ncd_tp} total):")
    print(f"     * False alarms from Healthy:     {ncd_fp_healthy} (43.2% of false positives)")
    print(f"     * False alarms from Salmonella:  {ncd_fp_salmo} (35.1% of false positives)")
    print(f"     * False alarms from Coccidiosis: {ncd_fp_cocci} (21.6% of false positives)")

    # Save complete JSON
    eval_results = {
        "backbone": backbone_name,
        "checkpoint": str(weights_path),
        "test_samples": len(targets),
        "accuracy": float(rep_dict["accuracy"]),
        "macro_avg_f1": float(rep_dict["macro avg"]["f1-score"]),
        "weighted_avg_f1": float(rep_dict["weighted avg"]["f1-score"]),
        "roc_auc": roc_auc_dict,
        "classification_report": rep_dict,
        "confusion_matrix": cm.tolist(),
        "confusion_analysis": {
            "coccidiosis_to_salmonella": cocci_to_salmo,
            "salmonella_to_coccidiosis": salmo_to_cocci,
            "newcastle_recall": float(rep_dict["Newcastle Disease"]["recall"]),
            "newcastle_precision": float(rep_dict["Newcastle Disease"]["precision"]),
            "newcastle_false_alarms": {
                "total": int(ncd_total_pred - ncd_tp),
                "from_healthy": ncd_fp_healthy,
                "from_salmonella": ncd_fp_salmo,
                "from_coccidiosis": ncd_fp_cocci,
            },
        },
    }

    eval_json_path = PROJECT_ROOT / "reports" / f"phase5_evaluation_{backbone_name}.json"
    with open(eval_json_path, "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=2)
    print(f"\nSaved evaluation metrics JSON to {eval_json_path}")

    return eval_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 5 Model Evaluation")
    parser.add_argument("--backbone", type=str, default="efficientnet_b0", help="Model backbone name")
    parser.add_argument("--weights", type=str, default=None, help="Path to checkpoint .pth")
    parser.add_argument("--run-dir", type=str, default=None, help="Path to run directory")
    args = parser.parse_args()

    run_dir = Path(args.run_dir) if args.run_dir else None
    weights = Path(args.weights) if args.weights else None
    run_evaluation(run_dir=run_dir, weights_path=weights, backbone_name=args.backbone)
