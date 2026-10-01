"""Multimodal Dataset & Synthetic Clinical Metadata Generator for Poultry Diagnostics.

Combines fecal image samples with realistic flock-level epidemiological indicators:
- 24h Mortality Count (birds)
- Water Consumption Drop (%)
- Feed Intake Reduction (%)
- Flock Age (weeks)
- Coop Ambient Temperature (°C)
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset
from torchvision import transforms

CLASSES = ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]
CLASS_TO_IDX = {cls_name: i for i, cls_name in enumerate(CLASSES)}


def generate_clinical_metadata(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Generates realistic clinical metadata features aligned with veterinary pathology standards."""
    rng = np.random.default_rng(seed)
    n = len(df)
    
    mortality = np.zeros(n, dtype=np.float32)
    water_drop = np.zeros(n, dtype=np.float32)
    feed_drop = np.zeros(n, dtype=np.float32)
    flock_age = np.zeros(n, dtype=np.float32)
    coop_temp = np.zeros(n, dtype=np.float32)

    for i, row in enumerate(df.itertuples()):
        cls = row.label
        if cls == "Newcastle Disease":
            # Acute viral outbreak: severe mortality spike, massive water/feed drop
            mortality[i] = rng.negative_binomial(n=3, p=0.2) + 2  # Mean ~12 deaths
            water_drop[i] = np.clip(rng.normal(35.0, 7.0), 10.0, 50.0)
            feed_drop[i] = np.clip(rng.normal(40.0, 8.0), 15.0, 50.0)
            flock_age[i] = rng.integers(4, 52)
            coop_temp[i] = rng.normal(28.0, 3.0)

        elif cls == "Salmonella":
            # Septicemic bacterial enteritis: moderate chick mortality, severe water drop
            mortality[i] = rng.negative_binomial(n=2, p=0.3) + 1  # Mean ~5.6 deaths
            water_drop[i] = np.clip(rng.normal(25.0, 6.0), 5.0, 45.0)
            feed_drop[i] = np.clip(rng.normal(20.0, 5.0), 5.0, 40.0)
            flock_age[i] = rng.integers(1, 16)  # Younger birds
            coop_temp[i] = rng.normal(29.0, 2.5)

        elif cls == "Coccidiosis":
            # Parasitic mucosal shedding: low mortality, high feed intake drop
            mortality[i] = rng.poisson(lam=1.5)  # Mean ~1.5 deaths
            water_drop[i] = np.clip(rng.normal(15.0, 4.0), 2.0, 30.0)
            feed_drop[i] = np.clip(rng.normal(30.0, 6.0), 8.0, 48.0)
            flock_age[i] = rng.integers(3, 12)  # 3-12 week growers
            coop_temp[i] = rng.normal(27.0, 3.0)

        else:  # Healthy
            # Baseline normal flock state
            mortality[i] = rng.choice([0, 0, 0, 0, 1], p=[0.85, 0.10, 0.03, 0.01, 0.01])
            water_drop[i] = np.clip(rng.normal(1.5, 1.0), 0.0, 5.0)
            feed_drop[i] = np.clip(rng.normal(1.5, 1.0), 0.0, 5.0)
            flock_age[i] = rng.integers(2, 60)
            coop_temp[i] = rng.normal(25.0, 2.0)

    df_meta = df.copy()
    df_meta["mortality_24h"] = np.round(mortality, 1)
    df_meta["water_drop_pct"] = np.round(water_drop, 1)
    df_meta["feed_drop_pct"] = np.round(feed_drop, 1)
    df_meta["flock_age_weeks"] = np.round(flock_age, 1)
    df_meta["coop_temp_c"] = np.round(coop_temp, 1)
    return df_meta


def compute_metadata_scaler_params(df_train: pd.DataFrame) -> dict:
    """Computes mean and std normalization parameters for metadata features."""
    cols = ["mortality_24h", "water_drop_pct", "feed_drop_pct", "flock_age_weeks", "coop_temp_c"]
    means = df_train[cols].mean().to_dict()
    stds = df_train[cols].std().replace(0, 1.0).to_dict()
    return {"mean": means, "std": stds, "feature_names": cols}


class MultimodalPoultryDataset(Dataset):
    """PyTorch Dataset returning Image Tensor, Standardized Metadata Tensor, and Class Label."""

    def __init__(self, df: pd.DataFrame, root_dir: Path, scaler_params: dict, is_train: bool = True):
        self.df = df
        self.root_dir = Path(root_dir)
        self.scaler = scaler_params
        self.feature_cols = self.scaler["feature_names"]

        if is_train:
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomVerticalFlip(p=0.5),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
        else:
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = self.root_dir / row["filepath"]
        
        # Fallback if path is relative
        if not img_path.exists():
            img_path = self.root_dir / "data" / row["filepath"]

        image = Image.open(img_path).convert("RGB")
        img_tensor = self.transform(image)

        # Standardize metadata features
        meta_vals = []
        for col in self.feature_cols:
            val = float(row[col])
            m = self.scaler["mean"][col]
            s = self.scaler["std"][col]
            meta_vals.append((val - m) / s)
            
        meta_tensor = torch.tensor(meta_vals, dtype=torch.float32)
        label_idx = CLASS_TO_IDX[row["label"]]
        
        return img_tensor, meta_tensor, torch.tensor(label_idx, dtype=torch.long)
