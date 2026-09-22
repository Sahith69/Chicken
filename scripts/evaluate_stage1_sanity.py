"""Sanity check: evaluate Stage-1-only (frozen backbone) ResNet50 on the test set."""

import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, f1_score
from torch.utils.data import DataLoader
import timm

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.data import get_dataloaders
from src.losses import get_loss_fn
from src.utils import get_device, set_seed


def evaluate_stage1():
    set_seed(42)
    device = torch.device("cpu")
    torch.set_num_threads(8)

    cfg = load_config()
    # Force imagenet normalization
    cfg["normalization"]["mode"] = "imagenet"

    train_loader, val_loader, test_loader, meta = get_dataloaders(config=cfg, batch_size=64, num_workers=2)
    class_names = cfg.get("classes")

    print("Loading pretrained resnet50...")
    model = timm.create_model("resnet50", pretrained=True, num_classes=4)
    model.eval()

    # Extract features from frozen backbone
    # In Stage 1, all backbone layers were frozen
    # Let's extract global pooling features (2048-d)
    feature_extractor = timm.create_model("resnet50", pretrained=True, num_classes=0).eval()

    print("Extracting frozen features for Train set...")
    t0 = time.time()
    train_feats, train_labels = [], []
    with torch.no_grad():
        for images, targets, _ in train_loader:
            feats = feature_extractor(images)
            train_feats.append(feats)
            train_labels.append(targets)
    X_train = torch.cat(train_feats, dim=0)
    y_train = torch.cat(train_labels, dim=0)
    print(f"Train features shape: {X_train.shape} (took {time.time()-t0:.1f}s)")

    print("Extracting frozen features for Val set...")
    val_feats, val_labels = [], []
    with torch.no_grad():
        for images, targets, _ in val_loader:
            feats = feature_extractor(images)
            val_feats.append(feats)
            val_labels.append(targets)
    X_val = torch.cat(val_feats, dim=0)
    y_val = torch.cat(val_labels, dim=0)

    print("Extracting frozen features for Test set...")
    test_feats, test_labels = [], []
    with torch.no_grad():
        for images, targets, _ in test_loader:
            feats = feature_extractor(images)
            test_feats.append(feats)
            test_labels.append(targets)
    X_test = torch.cat(test_feats, dim=0)
    y_test = torch.cat(test_labels, dim=0)
    print(f"Test features shape: {X_test.shape}")

    # Train linear head for 5 epochs with AdamW lr=1e-3 (identical to Stage 1)
    class_counts = [int((y_train == i).sum()) for i in range(len(class_names))]
    loss_fn = get_loss_fn({"loss": {"type": "weighted_ce"}}, class_counts=class_counts, device=device)

    head = nn.Linear(2048, len(class_names))
    optimizer = torch.optim.AdamW(head.parameters(), lr=1e-3, weight_decay=1e-4)

    dataset_train = torch.utils.data.TensorDataset(X_train, y_train)
    loader_train = DataLoader(dataset_train, batch_size=64, shuffle=True)

    print("\nTraining Stage 1 Linear Head on frozen features for 5 epochs...")
    best_val_f1 = 0.0
    best_head_state = None

    for ep in range(1, 6):
        head.train()
        for batch_x, batch_y in loader_train:
            optimizer.zero_grad()
            out = head(batch_x)
            loss = loss_fn(out, batch_y)
            loss.backward()
            optimizer.step()

        # Val evaluation
        head.eval()
        with torch.no_grad():
            val_out = head(X_val)
            val_preds = val_out.argmax(dim=-1).numpy()
            val_f1 = f1_score(y_val.numpy(), val_preds, average="macro")

        print(f"Stage 1 Ep {ep}: Val Macro-F1 = {val_f1:.4f}")
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_head_state = head.state_dict().copy()

    # Evaluate on Test Set
    head.load_state_dict(best_head_state)
    head.eval()
    with torch.no_grad():
        test_out = head(X_test)
        test_preds = test_out.argmax(dim=-1).numpy()
        test_f1 = f1_score(y_test.numpy(), test_preds, average="macro")
        test_acc = (test_preds == y_test.numpy()).mean()

    rep = classification_report(y_test.numpy(), test_preds, target_names=class_names, digits=4)
    print("\n" + "=" * 60)
    print("STAGE-1-ONLY (FROZEN BACKBONE) TEST EVALUATION")
    print("=" * 60)
    print(f"Test Accuracy: {test_acc*100:.2f}%")
    print(f"Test Macro-F1: {test_f1:.4f}")
    print("\nClassification Report:")
    print(rep)


if __name__ == "__main__":
    evaluate_stage1()
