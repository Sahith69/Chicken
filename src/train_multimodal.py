"""Training & Evaluation Engine for Multimodal Vision + Clinical Metadata Fusion Network."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from src.multimodal_data import (
    generate_clinical_metadata,
    compute_metadata_scaler_params,
    MultimodalPoultryDataset,
    CLASSES,
)
from src.multimodal_model import MultimodalPoultryNet
from src.utils import set_seed, get_device

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_training_and_evaluation(epochs: int = 5, batch_size: int = 32, lr: float = 5e-4):
    set_seed(42)
    device = get_device()
    print(f"Using device: {device}")

    # 1. Load splits
    train_csv = PROJECT_ROOT / "data" / "splits" / "train.csv"
    val_csv = PROJECT_ROOT / "data" / "splits" / "val.csv"
    test_csv = PROJECT_ROOT / "data" / "splits" / "test.csv"

    df_train_raw = pd.read_csv(train_csv)
    df_val_raw = pd.read_csv(val_csv)
    df_test_raw = pd.read_csv(test_csv)

    print(f"Loaded raw splits: train={len(df_train_raw)}, val={len(df_val_raw)}, test={len(df_test_raw)}")

    # 2. Generate clinical metadata
    df_train = generate_clinical_metadata(df_train_raw, seed=42)
    df_val = generate_clinical_metadata(df_val_raw, seed=142)
    df_test = generate_clinical_metadata(df_test_raw, seed=242)

    scaler_params = compute_metadata_scaler_params(df_train)

    # Save scaler params & metadata config to runs/multimodal/
    run_dir = PROJECT_ROOT / "runs" / "multimodal"
    run_dir.mkdir(parents=True, exist_ok=True)
    with open(run_dir / "meta_scaler.json", "w") as f:
        json.dump(scaler_params, f, indent=2)

    # 3. Datasets & Loaders
    train_dataset = MultimodalPoultryDataset(df_train, PROJECT_ROOT, scaler_params, is_train=True)
    val_dataset = MultimodalPoultryDataset(df_val, PROJECT_ROOT, scaler_params, is_train=False)
    test_dataset = MultimodalPoultryDataset(df_test, PROJECT_ROOT, scaler_params, is_train=False)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)

    # 4. Model, Loss, Optimizer
    model = MultimodalPoultryNet(num_classes=4, meta_dim=5, embed_dim=64).to(device)

    # Compute class weights for cross-entropy
    class_counts = df_train["label"].value_counts()
    total_samples = len(df_train)
    weights = [total_samples / (4 * class_counts[cls]) for cls in CLASSES]
    class_weights_t = torch.tensor(weights, dtype=torch.float32).to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights_t)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # 5. Training loop
    best_val_f1 = 0.0
    best_model_path = run_dir / "best_multimodal_model.pth"

    print("\nStarting Multimodal Network Training...")
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for images, metadata, labels in train_loader:
            images = images.to(device)
            metadata = metadata.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            logits, _ = model(images, metadata)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * len(labels)

        scheduler.step()
        train_loss /= len(train_dataset)

        # Validation
        model.eval()
        val_preds = []
        val_targets = []
        with torch.no_grad():
            for images, metadata, labels in val_loader:
                images = images.to(device)
                metadata = metadata.to(device)
                logits, _ = model(images, metadata)
                preds = logits.argmax(dim=1).cpu().numpy()
                val_preds.extend(preds)
                val_targets.extend(labels.numpy())

        val_acc = accuracy_score(val_targets, val_preds)
        val_f1 = f1_score(val_targets, val_preds, average="macro")

        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | Val Acc: {val_acc*100:.2f}% | Val Macro-F1: {val_f1:.4f}")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save(model.state_dict(), best_model_path)

    # 6. Evaluation on Test Set
    print("\nEvaluating Best Multimodal Model on Test Set...")
    model.load_state_dict(torch.load(best_model_path, map_location=device))
    model.eval()

    test_preds = []
    test_targets = []
    gate_values = []

    with torch.no_grad():
        for images, metadata, labels in test_loader:
            images = images.to(device)
            metadata = metadata.to(device)
            logits, g = model(images, metadata)
            preds = logits.argmax(dim=1).cpu().numpy()
            test_preds.extend(preds)
            test_targets.extend(labels.numpy())
            gate_values.extend(g.cpu().numpy().flatten())

    test_acc = accuracy_score(test_targets, test_preds)
    test_macro_f1 = f1_score(test_targets, test_preds, average="macro")
    test_report = classification_report(test_targets, test_preds, target_names=CLASSES, output_dict=True)
    conf_mat = confusion_matrix(test_targets, test_preds).tolist()
    avg_gate = float(np.mean(gate_values))

    print("\n" + "=" * 80)
    print(f"MULTIMODAL FUSION NETWORK TEST ACCURACY: {test_acc * 100:.2f}%")
    print(f"MULTIMODAL FUSION NETWORK TEST MACRO-F1: {test_macro_f1:.4f}")
    print(f"AVERAGE METADATA GATING WEIGHT: {avg_gate:.4f}")
    print("=" * 80)
    print(classification_report(test_targets, test_preds, target_names=CLASSES))

    # Save benchmark report to reports/phase9_multimodal_benchmark.json
    report_data = {
        "model_name": "MultimodalPoultryNet (EfficientNet-B0 + Clinical Gated Fusion)",
        "test_samples": len(df_test),
        "test_accuracy": float(test_acc),
        "test_macro_f1": float(test_macro_f1),
        "average_gating_weight": avg_gate,
        "classification_report": test_report,
        "confusion_matrix": conf_mat,
        "comparison_vs_image_only": {
            "image_only_accuracy": 0.8941273779983457,
            "image_only_macro_f1": 0.8714376545199868,
            "accuracy_improvement_pct": float((test_acc - 0.8941273779983457) * 100),
            "macro_f1_improvement": float(test_macro_f1 - 0.8714376545199868),
        },
    }

    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / "phase9_multimodal_benchmark.json", "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"Benchmark results saved to {reports_dir / 'phase9_multimodal_benchmark.json'}")


if __name__ == "__main__":
    run_training_and_evaluation()
