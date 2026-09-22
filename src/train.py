"""Training script with AdamW, Cosine LR, Early Stopping, and metric logging."""

import argparse
import json
import shutil
import time
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from tqdm import tqdm

from src.config import load_config
from src.data import get_dataloaders
from src.losses import get_loss_fn
from src.model import build_model
from src.utils import get_device, get_run_dir, set_seed


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def train_epoch(
    model: torch.nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> Dict[str, float]:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    all_preds = []
    all_targets = []

    for images, targets, _ in loader:
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)

        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, targets)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * len(targets)
        preds = torch.argmax(logits, dim=-1)
        all_preds.extend(preds.cpu().numpy())
        all_targets.extend(targets.cpu().numpy())

    n_samples = len(all_targets)
    epoch_loss = total_loss / n_samples
    acc = np.mean(np.array(all_preds) == np.array(all_targets))
    macro_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)

    return {"loss": epoch_loss, "accuracy": float(acc), "macro_f1": float(macro_f1)}


@torch.no_grad()
def evaluate_epoch(
    model: torch.nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: torch.nn.Module,
    device: torch.device,
) -> Dict:
    """Evaluate model on a dataset."""
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_targets = []

    for images, targets, _ in loader:
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)

        logits = model(images)
        loss = criterion(logits, targets)

        total_loss += loss.item() * len(targets)
        preds = torch.argmax(logits, dim=-1)
        all_preds.extend(preds.cpu().numpy())
        all_targets.extend(targets.cpu().numpy())

    n_samples = len(all_targets)
    epoch_loss = total_loss / n_samples
    acc = np.mean(np.array(all_preds) == np.array(all_targets))
    macro_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    per_class_f1 = f1_score(all_targets, all_preds, average=None, zero_division=0)

    return {
        "loss": epoch_loss,
        "accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "per_class_f1": [float(f) for f in per_class_f1],
        "targets": all_targets,
        "preds": all_preds,
    }


def plot_and_save_curves(history: Dict, save_path: Path):
    """Plot training and validation loss and macro-F1 curves."""
    epochs = range(1, len(history["train_loss"]) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=150)

    # Loss curve
    axes[0].plot(epochs, history["train_loss"], "o-", label="Train Loss", color="#1f77b4", lw=2)
    axes[0].plot(epochs, history["val_loss"], "s-", label="Val Loss", color="#ff7f0e", lw=2)
    axes[0].set_title("Loss Curves", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Epoch", fontsize=10, fontweight="bold")
    axes[0].set_ylabel("Loss", fontsize=10, fontweight="bold")
    axes[0].legend(frameon=True)
    axes[0].grid(True, linestyle="--", alpha=0.6)

    # Macro-F1 curve
    axes[1].plot(epochs, history["train_f1"], "o-", label="Train Macro-F1", color="#2ca02c", lw=2)
    axes[1].plot(epochs, history["val_f1"], "s-", label="Val Macro-F1", color="#d62728", lw=2)
    best_idx = np.argmax(history["val_f1"])
    best_f1 = history["val_f1"][best_idx]
    axes[1].axvline(best_idx + 1, color="gray", linestyle=":", label=f"Best Ep {best_idx+1} ({best_f1:.3f})")
    axes[1].set_title("Macro-F1 Curves", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Epoch", fontsize=10, fontweight="bold")
    axes[1].set_ylabel("Macro-F1", fontsize=10, fontweight="bold")
    axes[1].legend(frameon=True)
    axes[1].grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path)
    plt.close(fig)


def train(config_path: str = "config.yaml", patience: int = 6):
    """Main training routine."""
    cfg = load_config(config_path)
    seed = cfg.get("seed", 42)
    set_seed(seed)

    device = get_device()
    torch.set_num_threads(8)
    print(f"Executing on compute device: {device} (threads={torch.get_num_threads()})")

    # Timestamped run directory
    backbone_name = cfg.get("backbone", "scratch_cnn")
    run_dir = get_run_dir(base_dir=PROJECT_ROOT / cfg["paths"]["runs_dir"], name=backbone_name)
    print(f"Run directory created: {run_dir}")

    # Copy config to run directory
    shutil.copy2(PROJECT_ROOT / config_path, run_dir / "config.yaml")

    # Data loaders
    train_loader, val_loader, test_loader, meta = get_dataloaders(config=cfg, num_workers=2)
    class_names = cfg.get("classes", ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"])

    # Compute training class counts for balanced loss weighting
    train_df = pd.read_csv(PROJECT_ROOT / cfg["paths"]["train_split"])
    class_counts = [int((train_df["label"] == cls).sum()) for cls in class_names]
    print(f"Training Class Counts: {dict(zip(class_names, class_counts))}")

    criterion = get_loss_fn(cfg, class_counts=class_counts, device=device)
    print(f"Loss criterion configured: {criterion.__class__.__name__}")

    model = build_model(cfg, num_classes=len(class_names))
    model = model.to(device)

    # Optimizer and Cosine Scheduler
    lr = float(cfg.get("lr", 1e-3))
    epochs = int(cfg.get("epochs", 20))
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    history = {
        "train_loss": [],
        "train_acc": [],
        "train_f1": [],
        "val_loss": [],
        "val_acc": [],
        "val_f1": [],
        "lr": [],
    }

    best_val_f1 = -1.0
    best_epoch = -1
    best_weights_path = run_dir / "best_model.pth"
    patience_counter = 0

    print(f"\nBeginning training for {epochs} epochs (Early stopping patience={patience})...")
    start_time = time.time()

    for epoch in range(1, epochs + 1):
        ep_start = time.time()
        current_lr = scheduler.get_last_lr()[0]

        train_res = train_epoch(model, train_loader, criterion, optimizer, device)
        val_res = evaluate_epoch(model, val_loader, criterion, device)
        scheduler.step()

        history["train_loss"].append(train_res["loss"])
        history["train_acc"].append(train_res["accuracy"])
        history["train_f1"].append(train_res["macro_f1"])
        history["val_loss"].append(val_res["loss"])
        history["val_acc"].append(val_res["accuracy"])
        history["val_f1"].append(val_res["macro_f1"])
        history["lr"].append(current_lr)

        ep_duration = time.time() - ep_start
        val_f1 = val_res["macro_f1"]

        # Checkpoint if best
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch
            torch.save(model.state_dict(), best_weights_path)
            patience_counter = 0
            improved_flag = " [*BEST]"
        else:
            patience_counter += 1
            improved_flag = ""

        print(
            f"Epoch [{epoch:02d}/{epochs:02d}] ({ep_duration:.1f}s) | "
            f"Train Loss: {train_res['loss']:.4f}, F1: {train_res['macro_f1']:.4f} | "
            f"Val Loss: {val_res['loss']:.4f}, F1: {val_f1:.4f}{improved_flag} | "
            f"LR: {current_lr:.6f}"
        )

        if patience_counter >= patience:
            print(f"\nEarly stopping triggered after {patience} epochs without improvement.")
            break

    total_duration = time.time() - start_time
    print(f"\nTraining completed in {total_duration/60:.2f} minutes.")
    print(f"Best Validation Macro-F1: {best_val_f1:.4f} at Epoch {best_epoch}")

    # Plot and save curves
    curve_path = run_dir / "training_curves.png"
    plot_and_save_curves(history, curve_path)
    shutil.copy2(curve_path, PROJECT_ROOT / "reports" / "figures" / "baseline_training_curves.png")

    # Load best model for evaluation on test set
    print("\nLoading best model checkpoint for final Test set evaluation...")
    model.load_state_dict(torch.load(best_weights_path, map_location=device))
    test_res = evaluate_epoch(model, test_loader, criterion, device)

    # Classification report
    report_dict = classification_report(
        test_res["targets"],
        test_res["preds"],
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    report_text = classification_report(
        test_res["targets"],
        test_res["preds"],
        target_names=class_names,
        digits=4,
        zero_division=0,
    )
    cm = confusion_matrix(test_res["targets"], test_res["preds"])

    print("\n" + "=" * 60)
    print("TEST SET CLASSIFICATION REPORT (Baseline Scratch CNN)")
    print("=" * 60)
    print(report_text)
    print("Confusion Matrix:")
    print(cm)
    print("=" * 60)

    # Dump complete metrics to JSON
    metrics_payload = {
        "model_name": backbone_name,
        "seed": seed,
        "total_train_time_sec": total_duration,
        "best_epoch": best_epoch,
        "best_val_macro_f1": float(best_val_f1),
        "test_metrics": {
            "loss": float(test_res["loss"]),
            "accuracy": float(test_res["accuracy"]),
            "macro_f1": float(test_res["macro_f1"]),
            "classification_report": report_dict,
            "confusion_matrix": cm.tolist(),
        },
        "history": history,
    }

    with open(run_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    # Check suspicious performance flag
    if test_res["macro_f1"] >= 0.95:
        print(
            f"\n[WARNING] Test Macro-F1 is suspiciously high ({test_res['macro_f1']:.4f} >= 0.95) "
            "for a from-scratch baseline! Investigate potential leakage before proceeding."
        )

    return {
        "run_dir": str(run_dir),
        "best_val_macro_f1": float(best_val_f1),
        "best_epoch": best_epoch,
        "test_macro_f1": float(test_res["macro_f1"]),
        "report_dict": report_dict,
        "report_text": report_text,
    }


if __name__ == "__main__":
    train()
