"""ONNX Export and INT8 Quantization Pipeline (Phase 8).

Exports the trained EfficientNet-B0 checkpoint to:
1. Standard ONNX (FP32) and Dynamic Quantized INT8 ONNX.
2. Dual-output ONNX (FP32 & INT8) emitting both logits and 1280-d pooled features
   to execute disease classification and Deep Feature OOD gating in a single pass.

Audits:
- Model size reduction (MB and percentage).
- CPU latency comparison (PyTorch vs. ONNX FP32 vs. ONNX INT8).
- Prediction alignment on the held-out test set (Top-1 agreement and Logit MAE).
"""

import json
from pathlib import Path
import sys
import time
from typing import Dict, Tuple, Any

import numpy as np
import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType
import pandas as pd
from PIL import Image
import timm
import torch
import torch.nn as nn
from torchvision import transforms

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class DualOutputEfficientNet(nn.Module):
    """Wrapper that outputs both logits and penultimate pooled features."""

    def __init__(self, base_model: nn.Module):
        super().__init__()
        self.base = base_model

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        feats = self.base.forward_features(x)
        pooled = self.base.global_pool(feats)
        if hasattr(self.base, "forward_head"):
            logits = self.base.forward_head(feats)
        else:
            logits = self.base.classifier(pooled)
        return logits, pooled


def load_pytorch_model(checkpoint_path: Path) -> Tuple[nn.Module, DualOutputEfficientNet]:
    model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=4)
    state = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(state)
    model.eval()
    dual_model = DualOutputEfficientNet(model)
    dual_model.eval()
    return model, dual_model


def export_to_onnx(
    model: nn.Module,
    dual_model: DualOutputEfficientNet,
    export_dir: Path,
) -> Dict[str, Path]:
    export_dir.mkdir(parents=True, exist_ok=True)
    dummy_input = torch.randn(1, 3, 224, 224, dtype=torch.float32)

    paths = {
        "standard_fp32": export_dir / "efficientnet_b0.onnx",
        "standard_int8": export_dir / "efficientnet_b0_int8.onnx",
        "dual_fp32": export_dir / "efficientnet_b0_dual.onnx",
        "dual_int8": export_dir / "efficientnet_b0_dual_int8.onnx",
    }

    # 1. Standard FP32
    print("Exporting standard FP32 ONNX...")
    torch.onnx.export(
        model,
        dummy_input,
        str(paths["standard_fp32"]),
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch_size"}, "logits": {0: "batch_size"}},
        opset_version=17,
    )
    onnx.checker.check_model(str(paths["standard_fp32"]))

    # 2. Standard INT8
    print("Quantizing standard model to dynamic INT8...")
    quantize_dynamic(
        model_input=str(paths["standard_fp32"]),
        model_output=str(paths["standard_int8"]),
        weight_type=QuantType.QUInt8,
    )

    # 3. Dual-Output FP32
    print("Exporting dual-output FP32 ONNX...")
    torch.onnx.export(
        dual_model,
        dummy_input,
        str(paths["dual_fp32"]),
        input_names=["input"],
        output_names=["logits", "features"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "logits": {0: "batch_size"},
            "features": {0: "batch_size"},
        },
        opset_version=17,
    )
    onnx.checker.check_model(str(paths["dual_fp32"]))

    # 4. Dual-Output INT8
    print("Quantizing dual-output model to dynamic INT8...")
    quantize_dynamic(
        model_input=str(paths["dual_fp32"]),
        model_output=str(paths["dual_int8"]),
        weight_type=QuantType.QUInt8,
    )

    return paths


def benchmark_latency(
    torch_model: nn.Module,
    onnx_fp32_path: Path,
    onnx_int8_path: Path,
    num_warmup: int = 15,
    num_iterations: int = 100,
) -> Dict[str, Dict[str, float]]:
    dummy = torch.randn(1, 3, 224, 224, dtype=torch.float32)
    dummy_np = dummy.numpy()

    # PyTorch CPU
    for _ in range(num_warmup):
        with torch.no_grad():
            _ = torch_model(dummy)
    t0 = time.perf_counter()
    for _ in range(num_iterations):
        with torch.no_grad():
            _ = torch_model(dummy)
    torch_latency = (time.perf_counter() - t0) / num_iterations * 1000.0

    # ONNX FP32
    session_fp32 = ort.InferenceSession(str(onnx_fp32_path), providers=["CPUExecutionProvider"])
    for _ in range(num_warmup):
        _ = session_fp32.run(["logits"], {"input": dummy_np})
    t0 = time.perf_counter()
    for _ in range(num_iterations):
        _ = session_fp32.run(["logits"], {"input": dummy_np})
    onnx_fp32_latency = (time.perf_counter() - t0) / num_iterations * 1000.0

    # ONNX INT8
    session_int8 = ort.InferenceSession(str(onnx_int8_path), providers=["CPUExecutionProvider"])
    for _ in range(num_warmup):
        _ = session_int8.run(["logits"], {"input": dummy_np})
    t0 = time.perf_counter()
    for _ in range(num_iterations):
        _ = session_int8.run(["logits"], {"input": dummy_np})
    onnx_int8_latency = (time.perf_counter() - t0) / num_iterations * 1000.0

    return {
        "pytorch_fp32": {
            "mean_ms": torch_latency,
            "throughput_fps": 1000.0 / torch_latency,
        },
        "onnx_fp32": {
            "mean_ms": onnx_fp32_latency,
            "throughput_fps": 1000.0 / onnx_fp32_latency,
            "speedup_vs_pytorch": torch_latency / onnx_fp32_latency,
        },
        "onnx_int8": {
            "mean_ms": onnx_int8_latency,
            "throughput_fps": 1000.0 / onnx_int8_latency,
            "speedup_vs_pytorch": torch_latency / onnx_int8_latency,
        },
    }


def verify_test_alignment(
    torch_model: nn.Module,
    onnx_fp32_path: Path,
    onnx_int8_path: Path,
    test_csv: Path,
    sample_n: int = 100,
) -> Dict[str, Any]:
    test_df = pd.read_csv(test_csv)
    if len(test_df) > sample_n:
        test_df = test_df.sample(sample_n, random_state=42).reset_index(drop=True)

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    session_fp32 = ort.InferenceSession(str(onnx_fp32_path), providers=["CPUExecutionProvider"])
    session_int8 = ort.InferenceSession(str(onnx_int8_path), providers=["CPUExecutionProvider"])

    tensors = []
    for _, row in test_df.iterrows():
        p = PROJECT_ROOT / row["filepath"]
        with Image.open(p) as img:
            tensors.append(transform(img.convert("RGB")))
    batch = torch.stack(tensors)  # (N, 3, 224, 224)
    batch_np = batch.numpy()

    with torch.no_grad():
        torch_logits = torch_model(batch).numpy()

    fp32_logits = session_fp32.run(["logits"], {"input": batch_np})[0]
    int8_logits = session_int8.run(["logits"], {"input": batch_np})[0]

    torch_preds = np.argmax(torch_logits, axis=1)
    fp32_preds = np.argmax(fp32_logits, axis=1)
    int8_preds = np.argmax(int8_logits, axis=1)

    fp32_agreement = float(np.mean(torch_preds == fp32_preds))
    int8_agreement = float(np.mean(torch_preds == int8_preds))

    fp32_mae = float(np.mean(np.abs(torch_logits - fp32_logits)))
    int8_mae = float(np.mean(np.abs(torch_logits - int8_logits)))

    return {
        "sample_size": len(test_df),
        "onnx_fp32": {
            "top1_agreement_with_pytorch": fp32_agreement,
            "logit_mean_absolute_error": fp32_mae,
        },
        "onnx_int8": {
            "top1_agreement_with_pytorch": int8_agreement,
            "logit_mean_absolute_error": int8_mae,
        },
    }


def main():
    checkpoint_path = PROJECT_ROOT / "runs" / "20260920_215109_efficientnet_b0_weighted_ce" / "best_model.pth"
    export_dir = PROJECT_ROOT / "runs" / "export"
    test_csv = PROJECT_ROOT / "data" / "splits" / "test.csv"
    report_json = PROJECT_ROOT / "reports" / "phase8_export_benchmark.json"

    print("=" * 80)
    print("PHASE 8: ONNX EXPORT & DYNAMIC INT8 QUANTIZATION BENCHMARK")
    print("=" * 80)

    torch_model, dual_model = load_pytorch_model(checkpoint_path)
    paths = export_to_onnx(torch_model, dual_model, export_dir)

    # Size comparison
    pth_size_mb = checkpoint_path.stat().st_size / (1024 * 1024)
    fp32_size_mb = paths["standard_fp32"].stat().st_size / (1024 * 1024)
    int8_size_mb = paths["standard_int8"].stat().st_size / (1024 * 1024)
    dual_fp32_mb = paths["dual_fp32"].stat().st_size / (1024 * 1024)
    dual_int8_mb = paths["dual_int8"].stat().st_size / (1024 * 1024)

    print("\n--- File Size Comparison ---")
    print(f"PyTorch Checkpoint (.pth) : {pth_size_mb:.2f} MB")
    print(f"ONNX FP32 Standard         : {fp32_size_mb:.2f} MB")
    print(f"ONNX INT8 Quantized        : {int8_size_mb:.2f} MB ({(1 - int8_size_mb / pth_size_mb)*100:.1f}% reduction)")
    print(f"ONNX Dual-Output INT8      : {dual_int8_mb:.2f} MB")

    print("\n--- Benchmarking CPU Latency (100 runs) ---")
    latency_results = benchmark_latency(
        torch_model,
        paths["standard_fp32"],
        paths["standard_int8"],
    )
    print(f"PyTorch FP32 : {latency_results['pytorch_fp32']['mean_ms']:.2f} ms/img ({latency_results['pytorch_fp32']['throughput_fps']:.1f} FPS)")
    print(f"ONNX FP32    : {latency_results['onnx_fp32']['mean_ms']:.2f} ms/img ({latency_results['onnx_fp32']['throughput_fps']:.1f} FPS, {latency_results['onnx_fp32']['speedup_vs_pytorch']:.2f}x speedup)")
    print(f"ONNX INT8    : {latency_results['onnx_int8']['mean_ms']:.2f} ms/img ({latency_results['onnx_int8']['throughput_fps']:.1f} FPS, {latency_results['onnx_int8']['speedup_vs_pytorch']:.2f}x speedup)")

    print("\n--- Verifying Prediction Fidelity on Held-Out Test Set ---")
    alignment_results = verify_test_alignment(
        torch_model,
        paths["standard_fp32"],
        paths["standard_int8"],
        test_csv,
        sample_n=200,
    )
    print(f"ONNX FP32 Agreement: {alignment_results['onnx_fp32']['top1_agreement_with_pytorch']*100:.2f}% (MAE: {alignment_results['onnx_fp32']['logit_mean_absolute_error']:.4f})")
    print(f"ONNX INT8 Agreement: {alignment_results['onnx_int8']['top1_agreement_with_pytorch']*100:.2f}% (MAE: {alignment_results['onnx_int8']['logit_mean_absolute_error']:.4f})")

    results = {
        "file_sizes_mb": {
            "pytorch_pth": pth_size_mb,
            "onnx_fp32": fp32_size_mb,
            "onnx_int8": int8_size_mb,
            "onnx_dual_fp32": dual_fp32_mb,
            "onnx_dual_int8": dual_int8_mb,
            "compression_ratio": pth_size_mb / int8_size_mb,
            "size_reduction_pct": (1 - int8_size_mb / pth_size_mb) * 100,
        },
        "latency_benchmark": latency_results,
        "prediction_fidelity": alignment_results,
        "model_paths": {k: str(v.relative_to(PROJECT_ROOT)) for k, v in paths.items()},
    }

    with open(report_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved export benchmark report to {report_json}")


if __name__ == "__main__":
    main()
