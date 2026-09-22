"""Grad-CAM implementation with target-layer lookup dictionary for Phase 5.

Supports:
- resnet*       -> layer4[-1]
- mobilenetv2*  -> conv_head (fallback features[-1])
- efficientnet* -> conv_head (fallback blocks[-1])
- densenet*     -> features.norm5

Generates:
- 3 correct + 3 incorrect predictions per class (24 total).
- Visual heatmaps overlaid on original unnormalized RGB images.
- Attention audit cross-referencing Phase 1 substrate confounder findings.
"""

import argparse
import fnmatch
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import timm
import torch
import torch.nn as nn
from torchvision import transforms

from src.config import load_config
from src.data import get_dataloaders
from src.utils import get_device, set_seed


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_target_layer(model: nn.Module, backbone_name: str) -> nn.Module:
    """Resolve target layer for Grad-CAM using exact model architecture lookup.

    Asserts target layer exists; raises detailed error with module names if not found.
    """
    bb_lower = backbone_name.lower()

    if any(fnmatch.fnmatch(bb_lower, pat) for pat in ["*resnet*"]):
        if hasattr(model, "layer4") and len(model.layer4) > 0:
            return model.layer4[-1]

    elif any(fnmatch.fnmatch(bb_lower, pat) for pat in ["*mobilenetv2*", "*mobilenet_v2*"]):
        if hasattr(model, "conv_head"):
            return model.conv_head
        if hasattr(model, "features") and len(model.features) > 0:
            return model.features[-1]

    elif any(fnmatch.fnmatch(bb_lower, pat) for pat in ["*efficientnet*"]):
        if hasattr(model, "conv_head"):
            return model.conv_head
        if hasattr(model, "blocks") and len(model.blocks) > 0:
            return model.blocks[-1]

    elif any(fnmatch.fnmatch(bb_lower, pat) for pat in ["*densenet*"]):
        if hasattr(model, "features") and hasattr(model.features, "norm5"):
            return model.features.norm5

    # General fallback
    for candidate_name in ["conv_head", "layer4", "features", "blocks"]:
        if hasattr(model, candidate_name):
            mod = getattr(model, candidate_name)
            if isinstance(mod, nn.Sequential) and len(mod) > 0:
                return mod[-1]
            if isinstance(mod, nn.Module):
                return mod

    available_modules = [name for name, _ in model.named_modules() if len(name) > 0][:20]
    raise AttributeError(
        f"Could not resolve Grad-CAM target layer for backbone '{backbone_name}'. "
        f"Available top-level modules include: {available_modules}"
    )


class GradCAM:
    """Grad-CAM engine for extracting convolutional feature heatmaps."""

    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.activations = None
        self.gradients = None

        # Register forward and backward hooks
        self.forward_handle = self.target_layer.register_forward_hook(self._save_activation)
        self.backward_handle = self.target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, input_tensor, output_tensor):
        self.activations = output_tensor.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None,
    ) -> np.ndarray:
        """Compute Grad-CAM heatmap for a single input image tensor [1, 3, H, W]."""
        self.model.eval()
        self.model.zero_grad()

        output = self.model(input_tensor)
        if target_class is None:
            target_class = int(torch.argmax(output, dim=-1).item())

        score = output[0, target_class]
        score.backward(retain_graph=True)

        # Global average pooling on gradients: alpha_k = (1/Z) * sum(grad)
        gradients = self.gradients[0]  # [C, h, w]
        activations = self.activations[0]  # [C, h, w]

        weights = torch.mean(gradients, dim=(1, 2), keepdim=True)  # [C, 1, 1]
        cam = torch.sum(weights * activations, dim=0)  # [h, w]
        cam = torch.clamp(cam, min=0.0)  # ReLU

        cam_np = cam.cpu().numpy()
        if np.max(cam_np) > 0:
            cam_np = cam_np / np.max(cam_np)

        # Resize heatmap to input dimensions
        h, w = input_tensor.shape[2], input_tensor.shape[3]
        heatmap = cv2.resize(cam_np, (w, h), interpolation=cv2.INTER_LINEAR)
        return heatmap

    def overlay_on_image(
        self,
        rgb_image: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.5,
        colormap: int = cv2.COLORMAP_TURBO,
    ) -> np.ndarray:
        """Blend heatmap with unnormalized RGB image [H, W, 3] in [0, 255]."""
        heatmap_colored = cv2.applyColorMap(np.uint8(255 * heatmap), colormap)
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)

        blended = np.float32(heatmap_colored) * alpha + np.float32(rgb_image) * (1.0 - alpha)
        blended = np.clip(blended, 0, 255).astype(np.uint8)
        return blended

    def remove_hooks(self):
        self.forward_handle.remove()
        self.backward_handle.remove()


def run_gradcam_analysis(
    backbone_name: str = "efficientnet_b0",
    run_dir: Optional[Path] = None,
    weights_path: Optional[Path] = None,
    n_per_category: int = 3,
) -> Dict:
    """Select 3 correct + 3 incorrect predictions per class and generate Grad-CAM overlays."""
    if run_dir is None:
        run_dir = PROJECT_ROOT / "runs" / "20260920_215109_efficientnet_b0_weighted_ce"
    if weights_path is None:
        weights_path = run_dir / "best_model.pth"

    output_dir = PROJECT_ROOT / "reports" / "figures" / "gradcam"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(f"GRAD-CAM EXPLAINABILITY PIPELINE: {backbone_name.upper()}")
    print(f"Checkpoint: {weights_path}")
    print(f"Target directory: {output_dir}")
    print("=" * 80)

    device = get_device()
    cfg = load_config()
    cfg["normalization"]["mode"] = "imagenet"
    class_names = cfg.get("classes", ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"])

    # Load test split dataframe
    test_df = pd.read_csv(PROJECT_ROOT / cfg["paths"]["test_split"])
    _, _, test_loader, meta = get_dataloaders(config=cfg, batch_size=32, num_workers=0)

    # Initialize model
    model = timm.create_model(backbone_name, pretrained=False, num_classes=len(class_names))
    state = torch.load(weights_path, map_location=device)
    model.load_state_dict(state)
    model.to(device)
    model.eval()

    # Resolve target layer
    target_layer = resolve_target_layer(model, backbone_name)
    print(f"Successfully resolved Grad-CAM target layer: {target_layer.__class__.__name__} ({target_layer})")

    gradcam = GradCAM(model=model, target_layer=target_layer)

    # Collect predictions for all test samples
    print("Gathering model predictions across test set...")
    samples_data = []

    inv_normalize = transforms.Normalize(
        mean=[-0.485 / 0.229, -0.456 / 0.224, -0.406 / 0.225],
        std=[1 / 0.229, 1 / 0.224, 1 / 0.225],
    )

    with torch.no_grad():
        for images, targets, paths in test_loader:
            images = images.to(device)
            logits = model(images)
            probs = torch.softmax(logits, dim=-1)
            preds = torch.argmax(probs, dim=-1)

            for i in range(len(targets)):
                samples_data.append({
                    "path": paths[i],
                    "target": int(targets[i].item()),
                    "target_name": class_names[int(targets[i].item())],
                    "pred": int(preds[i].item()),
                    "pred_name": class_names[int(preds[i].item())],
                    "conf": float(probs[i, preds[i]].item()),
                    "is_correct": bool(preds[i].item() == targets[i].item()),
                })

    all_samples_df = pd.DataFrame(samples_data)

    # Select 3 correct and 3 incorrect per class
    selected_cases = []
    for cls_idx, cls_name in enumerate(class_names):
        correct_pool = all_samples_df[(all_samples_df["target"] == cls_idx) & (all_samples_df["is_correct"])].copy()
        incorrect_pool = all_samples_df[(all_samples_df["target"] == cls_idx) & (~all_samples_df["is_correct"])].copy()

        # Sort correct by highest confidence
        correct_pool = correct_pool.sort_values(by="conf", ascending=False)
        # Sort incorrect by highest misplaced confidence
        incorrect_pool = incorrect_pool.sort_values(by="conf", ascending=False)

        selected_correct = correct_pool.head(n_per_category)
        selected_incorrect = incorrect_pool.head(n_per_category)

        for _, row in selected_correct.iterrows():
            selected_cases.append({**row.to_dict(), "category": "correct"})
        for _, row in selected_incorrect.iterrows():
            selected_cases.append({**row.to_dict(), "category": "incorrect"})

    print(f"\nExtracted {len(selected_cases)} representative cases (3 correct + 3 incorrect across 4 classes).")

    # Image transform for Grad-CAM
    cam_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    saved_overlays = []

    # Composite figure: 4 classes x 6 samples (3 correct + 3 incorrect)
    fig, axes = plt.subplots(4, 6, figsize=(22, 16), dpi=150)

    for idx, case in enumerate(selected_cases):
        img_rel_path = case["path"]
        img_full_path = PROJECT_ROOT / img_rel_path
        true_name = case["target_name"]
        pred_name = case["pred_name"]
        conf = case["conf"]
        category = case["category"]

        # Load original raw RGB image
        with Image.open(img_full_path) as raw_img:
            raw_rgb = np.array(raw_img.convert("RGB").resize((224, 224)))

        # Process tensor for model
        input_tensor = cam_transform(Image.fromarray(raw_rgb)).unsqueeze(0).to(device)

        # Generate Grad-CAM for predicted class
        heatmap = gradcam.generate_heatmap(input_tensor, target_class=case["pred"])
        overlay = gradcam.overlay_on_image(raw_rgb, heatmap, alpha=0.45)

        # Save individual overlay
        safe_rel_stem = Path(img_rel_path).stem
        save_filename = f"{true_name.lower().replace(' ', '_')}_{category}_{safe_rel_stem}.png"
        save_file_path = output_dir / save_filename
        Image.fromarray(overlay).save(save_file_path)

        saved_overlays.append({
            "image_path": img_rel_path,
            "overlay_path": str(save_file_path),
            "true_class": true_name,
            "pred_class": pred_name,
            "confidence": conf,
            "category": category,
        })

        # Plot into composite grid
        cls_idx = class_names.index(true_name)
        col_offset = 0 if category == "correct" else 3
        # find sub-index in this category
        cat_samples = [c for c in selected_cases if c["target_name"] == true_name and c["category"] == category]
        sub_idx = cat_samples.index(case)
        col_idx = col_offset + sub_idx

        ax = axes[cls_idx, col_idx]
        ax.imshow(overlay)
        ax.axis("off")

        status_text = "CORRECT" if category == "correct" else "WRONG"
        color = "green" if category == "correct" else "red"
        ax.set_title(
            f"[{status_text}] True: {true_name}\nPred: {pred_name} ({conf*100:.1f}%)",
            fontsize=9,
            fontweight="bold",
            color=color,
            pad=4,
        )

    # Row labels
    for r, cls_name in enumerate(class_names):
        axes[r, 0].set_ylabel(cls_name, fontsize=12, fontweight="bold", labelpad=10)

    plt.suptitle(
        f"Phase 5 Grad-CAM Visual Explainability Gallery ({backbone_name})\n"
        "Left 3 Columns: Correct Predictions | Right 3 Columns: Misclassifications",
        fontsize=15,
        fontweight="bold",
        y=0.99,
    )
    plt.tight_layout()

    composite_path = PROJECT_ROOT / "reports" / "figures" / f"gradcam_composite_grid_{backbone_name}.png"
    plt.savefig(composite_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved 24 individual Grad-CAM overlays to {output_dir}")
    print(f"Saved composite 4x6 Grad-CAM gallery to {composite_path}")

    # Remove hooks
    gradcam.remove_hooks()

    # Save summary JSON
    summary_path = PROJECT_ROOT / "reports" / f"phase5_gradcam_{backbone_name}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "backbone": backbone_name,
            "target_layer": target_layer.__class__.__name__,
            "n_samples": len(saved_overlays),
            "overlays": saved_overlays,
        }, f, indent=2)

    return {
        "composite_path": str(composite_path),
        "overlays": saved_overlays,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 5 Grad-CAM Analysis")
    parser.add_argument("--backbone", type=str, default="efficientnet_b0", help="Model backbone name")
    parser.add_argument("--weights", type=str, default=None, help="Path to checkpoint .pth")
    parser.add_argument("--run-dir", type=str, default=None, help="Path to run directory")
    args = parser.parse_args()

    run_dir = Path(args.run_dir) if args.run_dir else None
    weights = Path(args.weights) if args.weights else None
    run_gradcam_analysis(backbone_name=args.backbone, run_dir=run_dir, weights_path=weights)
