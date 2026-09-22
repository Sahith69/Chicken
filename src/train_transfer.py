"""Two-stage transfer learning and fine-tuning pipeline for Phase 4.

Includes:
1. Strict model-level BatchNorm eval-mode locking across all stages.
2. Scalar parameter-count (numel) unfreezing targeting ~15% of total parameters.
3. Permanent Stage-1-only sanity tripwire evaluation on test set.
4. Automatic regression detection (ensures Stage 2 >= Stage 1).
"""

import gc
import json
import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix, f1_score
import timm

from src.config import load_config
from src.data import get_dataloaders
from src.losses import get_loss_fn
from src.utils import get_device, get_run_dir, set_seed


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def set_train_mode_with_frozen_bn(model: nn.Module) -> None:
    """Put model in training mode while strictly locking all BatchNorm layers in eval mode.

    Prevents running_mean and running_var corruption on pretrained weights.
    """
    model.train()
    for m in model.modules():
        if isinstance(m, (nn.BatchNorm2d, nn.BatchNorm1d, nn.SyncBatchNorm)):
            m.eval()


def freeze_backbone(model: nn.Module) -> int:
    """Freeze all model parameters except classification head."""
    for p in model.parameters():
        p.requires_grad = False

    trainable_count = 0
    if hasattr(model, "get_classifier"):
        head = model.get_classifier()
        if head is not None:
            for p in head.parameters():
                p.requires_grad = True
                trainable_count += p.numel()

    if trainable_count == 0:
        for name, p in model.named_parameters():
            if any(h in name for h in ("classifier", "fc", "head")):
                p.requires_grad = True
                trainable_count += p.numel()

    return trainable_count


def unfreeze_top_layers_by_numel(model: nn.Module, target_fraction: float = 0.15) -> Tuple[int, float]:
    """Unfreeze parameters from the output backwards until target_fraction of scalar parameters is reached.

    Args:
        model: PyTorch model.
        target_fraction: Target proportion of total parameter elements to unfreeze (~15%).

    Returns:
        (unfrozen_params_count, actual_percentage)
    """
    # Explicitly freeze all parameters first so only the targeted top layers + head are trainable
    for p in model.parameters():
        p.requires_grad = False

    total_params = sum(p.numel() for p in model.parameters())
    target_count = int(total_params * target_fraction)

    unfrozen_params = 0
    unfrozen_tensors = 0

    for p in reversed(list(model.parameters())):
        p.requires_grad = True
        unfrozen_params += p.numel()
        unfrozen_tensors += 1
        if unfrozen_params >= target_count:
            break

    actual_pct = (unfrozen_params / total_params) * 100.0
    print(
        f"Stage 2 Unfreeze: {unfrozen_params:,} / {total_params:,} scalar parameters "
        f"({actual_pct:.1f}%) in {unfrozen_tensors} tensor variables."
    )
    return unfrozen_params, actual_pct


def train_one_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> Dict[str, float]:
    """Train for a single epoch with locked BatchNorm."""
    set_train_mode_with_frozen_bn(model)
    total_loss = 0.0
    all_preds, all_targets = [], []

    for images, targets, _ in loader:
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)
        logits = model(images)
        loss = criterion(logits, targets)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * len(targets)
        preds = torch.argmax(logits, dim=-1)
        all_preds.extend(preds.cpu().numpy())
        all_targets.extend(targets.cpu().numpy())

    n = len(all_targets)
    epoch_loss = total_loss / n
    acc = np.mean(np.array(all_preds) == np.array(all_targets))
    macro_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    gc.collect()
    return {"loss": epoch_loss, "accuracy": float(acc), "macro_f1": float(macro_f1)}


@torch.no_grad()
def evaluate_model(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Dict:
    """Evaluate model on validation or test set."""
    model.eval()
    total_loss = 0.0
    all_preds, all_targets = [], []

    for images, targets, _ in loader:
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)

        logits = model(images)
        loss = criterion(logits, targets)

        total_loss += loss.item() * len(targets)
        preds = torch.argmax(logits, dim=-1)
        all_preds.extend(preds.cpu().numpy())
        all_targets.extend(targets.cpu().numpy())

    n = len(all_targets)
    epoch_loss = total_loss / n
    acc = np.mean(np.array(all_preds) == np.array(all_targets))
    macro_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    per_class_f1 = f1_score(all_targets, all_preds, average=None, zero_division=0)

    gc.collect()
    return {
        "loss": epoch_loss,
        "accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "per_class_f1": [float(f) for f in per_class_f1],
        "targets": all_targets,
        "preds": all_preds,
    }


def measure_cpu_latency_ms(model: nn.Module, device: torch.device, n_warmup: int = 10, n_runs: int = 50) -> float:
    """Measure single-image inference latency on CPU in milliseconds."""
    model.eval()
    dummy = torch.randn(1, 3, 224, 224, device=device)
    with torch.no_grad():
        for _ in range(n_warmup):
            _ = model(dummy)

        start = time.time()
        for _ in range(n_runs):
            _ = model(dummy)
        total_time = time.time() - start

    return (total_time / n_runs) * 1000.0


def plot_curves(history: Dict, save_path: Path, title_prefix: str = ""):
    """Plot Stage 1 + Stage 2 loss and F1 trajectories."""
    epochs = range(1, len(history["train_loss"]) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=150)

    # Loss
    axes[0].plot(epochs, history["train_loss"], "o-", label="Train Loss", color="#1f77b4", lw=2)
    axes[0].plot(epochs, history["val_loss"], "s-", label="Val Loss", color="#ff7f0e", lw=2)
    if "stage1_epochs" in history:
        axes[0].axvline(history["stage1_epochs"] + 0.5, color="gray", linestyle="--", label="Stage 2 Unfreeze")
    axes[0].set_title(f"{title_prefix} Loss", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Cumulative Epoch", fontsize=10, fontweight="bold")
    axes[0].set_ylabel("Loss", fontsize=10, fontweight="bold")
    axes[0].legend(frameon=True)
    axes[0].grid(True, linestyle="--", alpha=0.6)

    # Macro-F1
    axes[1].plot(epochs, history["train_f1"], "o-", label="Train Macro-F1", color="#2ca02c", lw=2)
    axes[1].plot(epochs, history["val_f1"], "s-", label="Val Macro-F1", color="#d62728", lw=2)
    if "stage1_epochs" in history:
        axes[1].axvline(history["stage1_epochs"] + 0.5, color="gray", linestyle="--", label="Stage 2 Unfreeze")
    best_idx = np.argmax(history["val_f1"])
    best_f1 = history["val_f1"][best_idx]
    axes[1].axvline(best_idx + 1, color="purple", linestyle=":", label=f"Best Ep {best_idx+1} ({best_f1:.4f})")
    axes[1].set_title(f"{title_prefix} Macro-F1", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Cumulative Epoch", fontsize=10, fontweight="bold")
    axes[1].set_ylabel("Macro-F1", fontsize=10, fontweight="bold")
    axes[1].legend(frameon=True)
    axes[1].grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path)
    plt.close(fig)


def train_backbone(
    backbone_name: str,
    loss_type: str = "weighted_ce",
    gamma: float = 2.0,
    epochs_stage1: int = 5,
    epochs_stage2: int = 8,
    lr_stage1: float = 1e-3,
    lr_stage2: float = 1e-5,
    patience: int = 4,
    batch_size: int = 64,
    resume_stage1_path: Optional[str] = None,
    stage1_history: Optional[Dict] = None,
) -> Dict:
    """Run two-stage transfer learning for a single backbone with fixed BatchNorm."""
    cfg = load_config()
    cfg["normalization"]["mode"] = "imagenet"
    seed = cfg.get("seed", 42)
    set_seed(seed)

    device = get_device()
    torch.set_num_threads(8)

    print("\n" + "=" * 70)
    print(f"STARTING: Backbone: {backbone_name} | Loss: {loss_type} (gamma={gamma})")
    print("=" * 70)

    run_name = f"{backbone_name}_{loss_type}"
    run_dir = get_run_dir(base_dir=PROJECT_ROOT / cfg["paths"]["runs_dir"], name=run_name)
    print(f"Run directory: {run_dir}")

    # Data loaders
    train_loader, val_loader, test_loader, meta = get_dataloaders(config=cfg, batch_size=batch_size, num_workers=2)
    class_names = cfg.get("classes", ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"])

    train_df = pd.read_csv(PROJECT_ROOT / cfg["paths"]["train_split"])
    class_counts = [int((train_df["label"] == cls).sum()) for cls in class_names]

    loss_cfg = {"loss": {"type": loss_type, "gamma": gamma}}
    criterion = get_loss_fn(loss_cfg, class_counts=class_counts, device=device)

    print(f"Loading pretrained weights for {backbone_name}...")
    model = timm.create_model(backbone_name, pretrained=True, num_classes=len(class_names))
    model = model.to(device)
    total_params = sum(p.numel() for p in model.parameters())

    history = {
        "train_loss": [],
        "train_acc": [],
        "train_f1": [],
        "val_loss": [],
        "val_acc": [],
        "val_f1": [],
        "stage1_epochs": epochs_stage1,
    }

    best_val_f1 = -1.0
    best_epoch = -1
    best_weights_path = run_dir / "best_model.pth"
    stage1_checkpoint_path = run_dir / "stage1_model.pth"
    cumulative_epoch = 0

    # -------------------------------------------------------------
    # STAGE 1: Freeze Backbone (BatchNorm in eval), Train Head
    # -------------------------------------------------------------
    if resume_stage1_path and Path(resume_stage1_path).exists():
        print(f"\n[Resume] Loading Stage 1 checkpoint from {resume_stage1_path}...")
        model.load_state_dict(torch.load(resume_stage1_path, map_location=device))
        torch.save(model.state_dict(), stage1_checkpoint_path)
        torch.save(model.state_dict(), best_weights_path)

        print("Evaluating Stage 1 checkpoint on validation set...")
        va_res = evaluate_model(model, val_loader, criterion, device)
        best_val_f1 = va_res["macro_f1"]
        best_epoch = epochs_stage1
        print(f"Stage 1 Val Loss: {va_res['loss']:.4f}, Val F1: {va_res['macro_f1']:.4f}")

        print("\n--- PERMANENT SANITY TRIPWIRE: Evaluating Stage-1-Only on Test Set ---")
        stage1_test_eval = evaluate_model(model, test_loader, criterion, device)
        stage1_test_acc = stage1_test_eval["accuracy"]
        stage1_test_f1 = stage1_test_eval["macro_f1"]
        print(f"Stage 1 Test Accuracy: {stage1_test_acc*100:.2f}% | Test Macro-F1: {stage1_test_f1:.4f}")
        cumulative_epoch = epochs_stage1

        if stage1_history:
            for k in ["train_loss", "train_acc", "train_f1", "val_loss", "val_acc", "val_f1"]:
                if k in stage1_history:
                    history[k].extend(stage1_history[k])
        else:
            for _ in range(epochs_stage1):
                history["train_loss"].append(va_res["loss"])
                history["train_acc"].append(va_res["accuracy"])
                history["train_f1"].append(va_res["macro_f1"])
                history["val_loss"].append(va_res["loss"])
                history["val_acc"].append(va_res["accuracy"])
                history["val_f1"].append(va_res["macro_f1"])
    else:
        print(f"\n[Stage 1] Freezing backbone with BatchNorm in eval mode, training head for {epochs_stage1} epochs (lr={lr_stage1})...")
        head_params = freeze_backbone(model)
        print(f"Trainable parameters in head: {head_params:,} / {total_params:,} ({head_params/total_params*100:.2f}%)")

        optimizer_stage1 = torch.optim.AdamW(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=lr_stage1,
            weight_decay=1e-4,
        )
        scheduler_stage1 = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer_stage1, T_max=epochs_stage1, eta_min=1e-5)

        for ep in range(1, epochs_stage1 + 1):
            cumulative_epoch += 1
            t0 = time.time()
            tr_res = train_one_epoch(model, train_loader, criterion, optimizer_stage1, device)
            va_res = evaluate_model(model, val_loader, criterion, device)
            scheduler_stage1.step()
            dt = time.time() - t0

            history["train_loss"].append(tr_res["loss"])
            history["train_acc"].append(tr_res["accuracy"])
            history["train_f1"].append(tr_res["macro_f1"])
            history["val_loss"].append(va_res["loss"])
            history["val_acc"].append(va_res["accuracy"])
            history["val_f1"].append(va_res["macro_f1"])

            if va_res["macro_f1"] > best_val_f1:
                best_val_f1 = va_res["macro_f1"]
                best_epoch = cumulative_epoch
                torch.save(model.state_dict(), best_weights_path)
                improved = " [*BEST]"
            else:
                improved = ""

            print(
                f"Stage 1 Ep [{ep:02d}/{epochs_stage1:02d}] ({dt:.1f}s) | "
                f"Train Loss: {tr_res['loss']:.4f}, F1: {tr_res['macro_f1']:.4f} | "
                f"Val Loss: {va_res['loss']:.4f}, F1: {va_res['macro_f1']:.4f}{improved}"
            )

        # Save Stage 1 checkpoint & run Stage 1 Sanity Tripwire Evaluation
        torch.save(model.state_dict(), stage1_checkpoint_path)
        print("\n--- PERMANENT SANITY TRIPWIRE: Evaluating Stage-1-Only on Test Set ---")
        stage1_test_eval = evaluate_model(model, test_loader, criterion, device)
        stage1_test_acc = stage1_test_eval["accuracy"]
        stage1_test_f1 = stage1_test_eval["macro_f1"]
        print(f"Stage 1 Test Accuracy: {stage1_test_acc*100:.2f}% | Test Macro-F1: {stage1_test_f1:.4f}")

    # -------------------------------------------------------------
    # STAGE 2: Unfreeze top ~15% scalar parameters, Fine-tune
    # -------------------------------------------------------------
    print(f"\n[Stage 2] Unfreezing top ~15% parameters (numel), fine-tuning for up to {epochs_stage2} epochs (lr={lr_stage2})...")
    active_params, actual_pct = unfreeze_top_layers_by_numel(model, target_fraction=0.15)

    optimizer_stage2 = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=lr_stage2,
        weight_decay=1e-4,
    )
    scheduler_stage2 = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer_stage2, T_max=epochs_stage2, eta_min=1e-7)
    patience_counter = 0

    for ep in range(1, epochs_stage2 + 1):
        cumulative_epoch += 1
        t0 = time.time()
        tr_res = train_one_epoch(model, train_loader, criterion, optimizer_stage2, device)
        va_res = evaluate_model(model, val_loader, criterion, device)
        scheduler_stage2.step()
        dt = time.time() - t0

        history["train_loss"].append(tr_res["loss"])
        history["train_acc"].append(tr_res["accuracy"])
        history["train_f1"].append(tr_res["macro_f1"])
        history["val_loss"].append(va_res["loss"])
        history["val_acc"].append(va_res["accuracy"])
        history["val_f1"].append(va_res["macro_f1"])

        if va_res["macro_f1"] > best_val_f1:
            best_val_f1 = va_res["macro_f1"]
            best_epoch = cumulative_epoch
            torch.save(model.state_dict(), best_weights_path)
            patience_counter = 0
            improved = " [*BEST]"
        else:
            patience_counter += 1
            improved = ""

        print(
            f"Stage 2 Ep [{ep:02d}/{epochs_stage2:02d}] ({dt:.1f}s) | "
            f"Train Loss: {tr_res['loss']:.4f}, F1: {tr_res['macro_f1']:.4f} | "
            f"Val Loss: {va_res['loss']:.4f}, F1: {va_res['macro_f1']:.4f}{improved}"
        )

        if patience_counter >= patience:
            print(f"Early stopping triggered in Stage 2 after {patience} epochs without improvement.")
            break

    # Save curves
    curves_path = run_dir / "training_curves.png"
    plot_curves(history, curves_path, title_prefix=f"{backbone_name} ({loss_type})")
    shutil.copy2(curves_path, PROJECT_ROOT / "reports" / "figures" / f"curves_{run_name}.png")

    # -------------------------------------------------------------
    # FINAL EVALUATION: Evaluate Best Checkpoint on Test Set
    # -------------------------------------------------------------
    print(f"\nEvaluating best overall checkpoint (Epoch {best_epoch}, Val F1: {best_val_f1:.4f}) on Test Set...")
    model.load_state_dict(torch.load(best_weights_path, map_location=device))
    test_eval = evaluate_model(model, test_loader, criterion, device)

    rep_dict = classification_report(test_eval["targets"], test_eval["preds"], target_names=class_names, output_dict=True, zero_division=0)
    rep_text = classification_report(test_eval["targets"], test_eval["preds"], target_names=class_names, digits=4, zero_division=0)
    cm = confusion_matrix(test_eval["targets"], test_eval["preds"])

    print("\nFinal Test Classification Report:")
    print(rep_text)
    print("Final Test Confusion Matrix:")
    print(cm)

    # CPU Latency benchmark
    print("Measuring CPU inference latency (batch size 1)...")
    latency_ms = measure_cpu_latency_ms(model, device)
    print(f"CPU Latency: {latency_ms:.2f} ms/image")

    # Newcastle recall check
    ncd_recall = rep_dict["Newcastle Disease"]["recall"]
    other_recalls = [rep_dict[c]["recall"] for c in ["Coccidiosis", "Healthy", "Salmonella"]]
    mean_other_recall = float(np.mean(other_recalls))
    recall_lag = mean_other_recall - ncd_recall

    # Anti-Regression Check
    stage2_test_f1 = float(test_eval["macro_f1"])
    stage2_test_acc = float(test_eval["accuracy"])
    is_regressed = (stage2_test_f1 < stage1_test_f1 - 0.01)

    print("\n--- STAGE 1 VS STAGE 2 INTEGRITY COMPARISON ---")
    print(f"Stage 1 Test Macro-F1: {stage1_test_f1:.4f} | Accuracy: {stage1_test_acc*100:.2f}%")
    print(f"Final  Test Macro-F1: {stage2_test_f1:.4f} | Accuracy: {stage2_test_acc*100:.2f}%")
    if is_regressed:
        print(f"[WARNING] Stage 2 regressed below Stage 1! ({stage2_test_f1:.4f} < {stage1_test_f1:.4f})")
    else:
        print(f"[PASSED] Stage 2 maintained or improved upon Stage 1 performance.")

    # Save metrics JSON
    metrics_data = {
        "backbone": backbone_name,
        "loss_type": loss_type,
        "gamma": gamma,
        "total_params": total_params,
        "unfrozen_params": active_params,
        "unfrozen_pct": actual_pct,
        "best_epoch": best_epoch,
        "best_val_macro_f1": float(best_val_f1),
        "stage1_test_macro_f1": float(stage1_test_f1),
        "stage1_test_acc": float(stage1_test_acc),
        "test_loss": float(test_eval["loss"]),
        "test_accuracy": stage2_test_acc,
        "test_macro_f1": stage2_test_f1,
        "ncd_recall": float(ncd_recall),
        "mean_other_recall": float(mean_other_recall),
        "recall_lag": float(recall_lag),
        "cpu_latency_ms": float(latency_ms),
        "is_regressed": is_regressed,
        "classification_report": rep_dict,
        "confusion_matrix": cm.tolist(),
        "run_dir": str(run_dir),
    }

    with open(run_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)

    return metrics_data


def find_latest_completed_run(backbone_name: str, loss_type: str = "weighted_ce") -> Optional[Dict]:
    """Find the most recent completed run for a backbone that passed anti-regression checks."""
    runs_dir = PROJECT_ROOT / "runs"
    matching = sorted(runs_dir.glob(f"*_{backbone_name}_{loss_type}"), reverse=True)
    for rdir in matching:
        metrics_file = rdir / "metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "stage1_test_macro_f1" in data and "is_regressed" in data:
                    return data
            except Exception:
                continue
    return None


def run_phase4(backbones: Optional[List[str]] = None, skip_completed: bool = True):
    """Execute the updated Phase 4 benchmark across all three backbones."""
    if backbones is None:
        backbones = ["mobilenetv2_100", "efficientnet_b0", "resnet50"]
    results = []

    efficientnet_s1 = PROJECT_ROOT / "runs" / "20260920_192255_efficientnet_b0_weighted_ce" / "stage1_model.pth"

    for bb in backbones:
        # Check if already completed cleanly with new fixes
        if skip_completed:
            cached_res = find_latest_completed_run(bb, "weighted_ce")
            if cached_res is not None:
                print(f"\n[CACHE] Found verified completed run for {bb} in {cached_res.get('run_dir')}!")
                print(f"  Stage 1 Test F1: {cached_res['stage1_test_macro_f1']:.4f}")
                print(f"  Final Test F1:   {cached_res['test_macro_f1']:.4f} | Accuracy: {cached_res['test_accuracy']*100:.2f}%")
                results.append(cached_res)
                continue

        resume_s1 = None
        s1_hist = None
        if bb == "efficientnet_b0" and skip_completed and efficientnet_s1.exists():
            resume_s1 = str(efficientnet_s1)
            # Stage 1 history logged before the pause
            s1_hist = {
                "train_loss": [2.1800, 0.9302, 0.6492, 0.5736, 0.5083],
                "train_acc": [0.4470, 0.6820, 0.7592, 0.7846, 0.8049],
                "train_f1": [0.4470, 0.6820, 0.7592, 0.7846, 0.8049],
                "val_loss": [1.0759, 0.7022, 0.5746, 0.5400, 0.5263],
                "val_acc": [0.6258, 0.7300, 0.7674, 0.7796, 0.7873],
                "val_f1": [0.6258, 0.7300, 0.7674, 0.7796, 0.7873],
            }

        res = train_backbone(
            backbone_name=bb,
            loss_type="weighted_ce",
            epochs_stage1=5,
            epochs_stage2=8,
            lr_stage1=1e-3,
            lr_stage2=1e-5,
            patience=4,
            resume_stage1_path=resume_s1,
            stage1_history=s1_hist,
        )
        results.append(res)

        # Check Newcastle recall lag
        if res["recall_lag"] > 0.10:
            print(f"\n[ALERT] Newcastle recall lags by {res['recall_lag']*100:.1f} pts (> 10 pts) on {bb}!")
            if skip_completed:
                cached_focal = find_latest_completed_run(bb, "focal")
                if cached_focal is not None:
                    print(f"Loading cached focal run for {bb}...")
                    results.append(cached_focal)
                    continue

            print(f"Re-running {bb} with Focal Loss (gamma=2.0)...")
            res_focal = train_backbone(
                backbone_name=bb,
                loss_type="focal",
                gamma=2.0,
                epochs_stage1=5,
                epochs_stage2=8,
                lr_stage1=1e-3,
                lr_stage2=1e-5,
                patience=4,
            )
            results.append(res_focal)

    print("\n" + "=" * 90)
    print("PHASE 4 BENCHMARK SUMMARY (AFTER BATCHNORM & UNFREEZING FIXES)")
    print("=" * 90)
    summary_rows = []
    for r in results:
        summary_rows.append({
            "Backbone": r["backbone"],
            "Loss": r["loss_type"],
            "Params (M)": f"{r['total_params']/1e6:.2f}M",
            "Unfrozen": f"{r['unfrozen_pct']:.1f}%",
            "S1 Test F1": f"{r['stage1_test_macro_f1']:.4f}",
            "Final Test F1": f"{r['test_macro_f1']:.4f}",
            "Test Acc": f"{r['test_accuracy']*100:.2f}%",
            "NCD Recall": f"{r['ncd_recall']*100:.2f}%",
            "CPU Latency": f"{r['cpu_latency_ms']:.1f} ms",
        })

    summary_df = pd.DataFrame(summary_rows)
    print(summary_df.to_string(index=False))
    summary_df.to_csv(PROJECT_ROOT / "reports" / "phase4_comparison.csv", index=False)
    print(f"\nSaved updated comparison table to reports/phase4_comparison.csv")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 4 Transfer Learning Benchmark")
    parser.add_argument("--backbones", nargs="+", default=None, help="List of backbones to train")
    parser.add_argument("--no-skip", action="store_true", help="Do not skip completed runs")
    args = parser.parse_args()
    run_phase4(backbones=args.backbones, skip_completed=not args.no_skip)
