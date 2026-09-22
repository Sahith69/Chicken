"""Model calibration and temperature scaling for Phase 5.

Implements:
1. Expected Calibration Error (ECE) and Maximum Calibration Error (MCE) calculation.
2. Temperature scaling optimization (fits scalar T > 0 on validation set logits via NLL).
3. Side-by-side Reliability Diagrams (pre- and post-calibration).
4. Serializing fitted T into run directory for consumption by the Streamlit application.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import timm
import torch
import torch.nn as nn
from torch.optim import LBFGS

from src.config import load_config
from src.data import get_dataloaders
from src.utils import get_device, set_seed


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ModelWithTemperature(nn.Module):
    """Decorator that wraps a model and adds a learned temperature scaling parameter."""

    def __init__(self, model: nn.Module):
        super().__init__()
        self.model = model
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, input_tensor: torch.Tensor) -> torch.Tensor:
        logits = self.model(input_tensor)
        return self.temperature_scale(logits)

    def temperature_scale(self, logits: torch.Tensor) -> torch.Tensor:
        """Expand temperature to match the size of logits and divide."""
        temperature = self.temperature.unsqueeze(1).expand(logits.size(0), logits.size(1))
        return logits / temperature

    def fit_temperature(
        self,
        val_logits: torch.Tensor,
        val_labels: torch.Tensor,
        lr: float = 0.01,
        max_iter: int = 100,
    ) -> float:
        """Fit single scalar temperature parameter T on validation logits by minimizing NLL."""
        nll_criterion = nn.CrossEntropyLoss()
        optimizer = LBFGS([self.temperature], lr=lr, max_iter=max_iter)

        def eval_loss():
            optimizer.zero_grad()
            scaled_logits = self.temperature_scale(val_logits)
            loss = nll_criterion(scaled_logits, val_labels)
            loss.backward()
            return loss

        optimizer.step(eval_loss)
        return float(self.temperature.item())


def compute_ece(
    probs: np.ndarray,
    targets: np.ndarray,
    n_bins: int = 15,
) -> Tuple[float, float, Dict]:
    """Compute Expected Calibration Error (ECE) and Maximum Calibration Error (MCE).

    Args:
        probs: Array of predicted softmax probabilities [N, C].
        targets: True integer class indices [N].
        n_bins: Number of confidence bins between 0 and 1.

    Returns:
        (ece, mce, bin_details)
    """
    confidences = np.max(probs, axis=1)
    predictions = np.argmax(probs, axis=1)
    accuracies = (predictions == targets).astype(float)

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    mce = 0.0

    bin_accs = []
    bin_confs = []
    bin_sizes = []

    n_samples = len(targets)

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        bin_size = np.sum(in_bin)

        if bin_size > 0:
            avg_acc = np.mean(accuracies[in_bin])
            avg_conf = np.mean(confidences[in_bin])
            abs_diff = np.abs(avg_acc - avg_conf)

            ece += (bin_size / n_samples) * abs_diff
            mce = max(mce, abs_diff)

            bin_accs.append(float(avg_acc))
            bin_confs.append(float(avg_conf))
            bin_sizes.append(int(bin_size))
        else:
            bin_accs.append(0.0)
            bin_confs.append((bin_lower + bin_upper) / 2.0)
            bin_sizes.append(0)

    bin_details = {
        "bin_accs": bin_accs,
        "bin_confs": bin_confs,
        "bin_sizes": bin_sizes,
        "bin_boundaries": bin_boundaries.tolist(),
    }

    return float(ece), float(mce), bin_details


def plot_reliability_diagrams(
    pre_details: Dict,
    post_details: Dict,
    pre_ece: float,
    post_ece: float,
    temperature: float,
    save_path: Path,
    model_name: str = "EfficientNet-B0",
) -> None:
    """Plot dual reliability diagrams: before and after temperature scaling."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), dpi=150)
    bin_centers = np.linspace(0.05, 0.95, 10)

    for idx, (details, ece, label, ax) in enumerate([
        (pre_details, pre_ece, f"Before Scaling (T = 1.000)", axes[0]),
        (post_details, post_ece, f"After Temperature Scaling (T = {temperature:.3f})", axes[1]),
    ]):
        accs = np.array(details["bin_accs"])
        confs = np.array(details["bin_confs"])
        sizes = np.array(details["bin_sizes"])
        valid = sizes > 0

        # Perfect calibration line
        ax.plot([0, 1], [0, 1], "k--", lw=1.5, label="Perfect Calibration")

        # Bar chart of accuracy vs confidence
        width = 1.0 / len(accs)
        boundaries = np.array(details["bin_boundaries"])
        centers = (boundaries[:-1] + boundaries[1:]) / 2.0

        ax.bar(
            centers[valid],
            accs[valid],
            width=width * 0.85,
            alpha=0.7,
            color="#1f77b4" if idx == 0 else "#2ca02c",
            edgecolor="black",
            label="Empirical Accuracy",
        )

        # Gap indicator
        gaps = np.abs(accs[valid] - confs[valid])
        ax.bar(
            centers[valid],
            gaps,
            bottom=np.minimum(accs[valid], confs[valid]),
            width=width * 0.85,
            alpha=0.3,
            color="red",
            edgecolor="darkred",
            hatch="//",
            label="Calibration Gap",
        )

        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel("Confidence", fontsize=11, fontweight="bold")
        ax.set_ylabel("Accuracy", fontsize=11, fontweight="bold")
        ax.set_title(f"{label}\nECE = {ece*100:.2f}%", fontsize=12, fontweight="bold", pad=10)
        ax.legend(loc="upper left", fontsize=10, frameon=True)
        ax.grid(alpha=0.3)

    plt.suptitle(f"{model_name} Calibration Analysis (Reliability Diagram)", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved reliability diagrams to {save_path}")


@torch.no_grad()
def extract_logits_and_targets(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    device: torch.device,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Extract all raw logits and true targets from a DataLoader."""
    model.eval()
    all_logits = []
    all_targets = []

    for images, targets, _ in loader:
        images = images.to(device)
        logits = model(images)
        all_logits.append(logits.cpu())
        all_targets.append(targets.cpu())

    return torch.cat(all_logits, dim=0), torch.cat(all_targets, dim=0)


def calibrate_and_evaluate(
    run_dir: Optional[Path] = None,
    weights_path: Optional[Path] = None,
    backbone_name: str = "efficientnet_b0",
) -> Dict:
    """Execute temperature scaling on validation set and evaluate calibration on test set."""
    if run_dir is None:
        run_dir = PROJECT_ROOT / "runs" / "20260920_215109_efficientnet_b0_weighted_ce"
    if weights_path is None:
        weights_path = run_dir / "best_model.pth"

    print("=" * 80)
    print(f"PHASE 5 CALIBRATION & TEMPERATURE SCALING: {backbone_name.upper()}")
    print(f"Run Directory: {run_dir}")
    print("=" * 80)

    device = get_device()
    cfg = load_config()
    cfg["normalization"]["mode"] = "imagenet"
    class_names = cfg.get("classes", ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"])

    train_loader, val_loader, test_loader, meta = get_dataloaders(config=cfg, batch_size=64, num_workers=0)

    # Load trained model
    model = timm.create_model(backbone_name, pretrained=False, num_classes=len(class_names))
    state = torch.load(weights_path, map_location=device)
    model.load_state_dict(state)
    model.to(device)
    model.eval()

    # 1. Extract Validation Logits and Targets
    print("Extracting validation set logits to fit temperature T...")
    val_logits, val_targets = extract_logits_and_targets(model, val_loader, device)

    # 2. Fit Temperature Scaling Parameter T
    scaled_model = ModelWithTemperature(model)
    fitted_temp = scaled_model.fit_temperature(val_logits, val_targets)
    print(f"\n[OPTIMIZATION COMPLETE] Fitted Temperature Parameter T = {fitted_temp:.4f}")

    # 3. Extract Test Set Logits and Evaluate Pre/Post Calibration
    print("\nExtracting held-out test set logits...")
    test_logits, test_targets = extract_logits_and_targets(model, test_loader, device)

    # Uncalibrated (T = 1.0)
    uncal_probs = torch.softmax(test_logits, dim=-1).numpy()
    test_targets_np = test_targets.numpy()
    pre_ece, pre_mce, pre_details = compute_ece(uncal_probs, test_targets_np, n_bins=15)

    # Calibrated (T = fitted_temp)
    cal_logits = test_logits / fitted_temp
    cal_probs = torch.softmax(cal_logits, dim=-1).numpy()
    post_ece, post_mce, post_details = compute_ece(cal_probs, test_targets_np, n_bins=15)

    # Compute NLL and Brier score
    nll_criterion = nn.CrossEntropyLoss()
    pre_nll = float(nll_criterion(test_logits, test_targets).item())
    post_nll = float(nll_criterion(cal_logits, test_targets).item())

    # One-hot targets for Brier score
    one_hot_targets = np.zeros_like(uncal_probs)
    for i, t in enumerate(test_targets_np):
        one_hot_targets[i, t] = 1.0
    pre_brier = float(np.mean(np.sum((uncal_probs - one_hot_targets) ** 2, axis=1)))
    post_brier = float(np.mean(np.sum((cal_probs - one_hot_targets) ** 2, axis=1)))

    print("\n--- CALIBRATION RESULTS ON HELD-OUT TEST SET ---")
    print(f"Fitted Temperature (T):        {fitted_temp:.4f}")
    print(f"Negative Log-Likelihood (NLL): {pre_nll:.4f} -> {post_nll:.4f} (Reduction: {pre_nll - post_nll:+.4f})")
    print(f"Brier Score:                   {pre_brier:.4f} -> {post_brier:.4f}")
    print(f"Expected Calibration Error:    {pre_ece*100:.2f}% -> {post_ece*100:.2f}% (Reduction: {(pre_ece - post_ece)*100:+.2f} pts)")
    print(f"Maximum Calibration Error:     {pre_mce*100:.2f}% -> {post_mce*100:.2f}%")

    # 4. Plot and Save Reliability Diagrams
    fig_path = PROJECT_ROOT / "reports" / "figures" / f"calibration_curves_{backbone_name}.png"
    plot_reliability_diagrams(
        pre_details=pre_details,
        post_details=post_details,
        pre_ece=pre_ece,
        post_ece=post_ece,
        temperature=fitted_temp,
        save_path=fig_path,
        model_name=backbone_name,
    )

    # 5. Save temperature.json into the model run directory
    temp_json_data = {
        "backbone": backbone_name,
        "checkpoint": str(weights_path),
        "temperature": float(fitted_temp),
        "pre_scaling": {
            "ece": float(pre_ece),
            "mce": float(pre_mce),
            "nll": float(pre_nll),
            "brier_score": float(pre_brier),
        },
        "post_scaling": {
            "ece": float(post_ece),
            "mce": float(post_mce),
            "nll": float(post_nll),
            "brier_score": float(post_brier),
        },
        "ece_reduction_percentage_points": float((pre_ece - post_ece) * 100.0),
    }

    # Save in run directory for deployment / Streamlit
    run_temp_path = run_dir / "temperature.json"
    with open(run_temp_path, "w", encoding="utf-8") as f:
        json.dump(temp_json_data, f, indent=2)
    print(f"Saved fitted temperature configuration to {run_temp_path}")

    # Also save in reports directory
    report_temp_path = PROJECT_ROOT / "reports" / f"phase5_calibration_{backbone_name}.json"
    with open(report_temp_path, "w", encoding="utf-8") as f:
        json.dump(temp_json_data, f, indent=2)
    print(f"Saved calibration report JSON to {report_temp_path}")

    return temp_json_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 5 Temperature Scaling & Calibration")
    parser.add_argument("--backbone", type=str, default="efficientnet_b0", help="Model backbone name")
    parser.add_argument("--weights", type=str, default=None, help="Path to checkpoint .pth")
    parser.add_argument("--run-dir", type=str, default=None, help="Path to run directory")
    args = parser.parse_args()

    run_dir = Path(args.run_dir) if args.run_dir else None
    weights = Path(args.weights) if args.weights else None
    calibrate_and_evaluate(run_dir=run_dir, weights_path=weights, backbone_name=args.backbone)
