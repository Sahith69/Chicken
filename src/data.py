"""Dataset, data loaders, and augmentation pipeline for Poultry Disease Detection."""

import random
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
import torchvision.transforms as transforms

from src.config import load_config
from src.utils import set_seed


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Standard ImageNet statistics
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class RandomRotationReflect:
    """Random rotation with reflect padding to avoid black border artifacts."""

    def __init__(self, degrees: float = 20.0):
        self.degrees = degrees

    def __call__(self, img: Image.Image) -> Image.Image:
        angle = random.uniform(-self.degrees, self.degrees)
        arr = np.array(img)
        h, w = arr.shape[:2]
        center = (w / 2.0, h / 2.0)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(arr, M, (w, h), borderMode=cv2.BORDER_REFLECT)
        return Image.fromarray(rotated)


class PoultryDataset(Dataset):
    """PyTorch Dataset for chicken faecal images."""

    def __init__(
        self,
        data: Union[str, Path, pd.DataFrame],
        transform: Optional[transforms.Compose] = None,
        class_to_idx: Optional[Dict[str, int]] = None,
        root_dir: Path = PROJECT_ROOT,
    ):
        if isinstance(data, (str, Path)):
            self.df = pd.read_csv(root_dir / data if not Path(data).is_absolute() else data)
        else:
            self.df = data.copy().reset_index(drop=True)

        self.root_dir = Path(root_dir)
        self.transform = transform

        if class_to_idx is None:
            classes = sorted(self.df["label"].unique())
            self.class_to_idx = {cls: idx for idx, cls in enumerate(classes)}
        else:
            self.class_to_idx = class_to_idx

        self.idx_to_class = {idx: cls for cls, idx in self.class_to_idx.items()}

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, str]:
        row = self.df.iloc[idx]
        rel_path = row["filepath"]
        full_path = self.root_dir / rel_path
        label_name = row["label"]
        label_idx = self.class_to_idx[label_name]

        with Image.open(full_path) as img:
            image = img.convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label_idx, rel_path


def get_transforms(
    config: Dict,
    split: str = "train",
) -> Tuple[transforms.Compose, Tuple[list, list]]:
    """Build transforms for train or val/test splits.

    - Train transforms: resize 224, random flips (H+V), rotation ±20° with reflect padding,
      mild brightness/contrast (saturation/hue strictly 0.0 to preserve diagnostic colour).
      No MixUp, no CutMix.
    - Val/Test transforms: resize 224 + normalize only.
    """
    image_size = config.get("image_size", 224)
    norm_cfg = config.get("normalization", {})
    mode = norm_cfg.get("mode", "imagenet")

    if mode == "dataset" and norm_cfg.get("dataset_mean") and norm_cfg.get("dataset_std"):
        mean = norm_cfg["dataset_mean"]
        std = norm_cfg["dataset_std"]
    else:
        mean = IMAGENET_MEAN
        std = IMAGENET_STD

    if split == "train":
        transform_list = [
            transforms.Resize((image_size, image_size)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
            RandomRotationReflect(degrees=20.0),
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.0, hue=0.0),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ]
    else:
        transform_list = [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ]

    return transforms.Compose(transform_list), (mean, std)


def get_dataloaders(
    config: Optional[Dict] = None,
    batch_size: Optional[int] = None,
    num_workers: int = 2,
) -> Tuple[DataLoader, DataLoader, DataLoader, Dict]:
    """Create train, validation, and test DataLoaders."""
    if config is None:
        config = load_config()

    set_seed(config.get("seed", 42))
    bs = batch_size or config.get("batch_size", 32)

    class_names = config.get("classes", ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"])
    class_to_idx = {cls: idx for idx, cls in enumerate(class_names)}

    train_tf, norm_stats = get_transforms(config, split="train")
    eval_tf, _ = get_transforms(config, split="val")

    train_path = PROJECT_ROOT / config["paths"]["train_split"]
    val_path = PROJECT_ROOT / config["paths"]["val_split"]
    test_path = PROJECT_ROOT / config["paths"]["test_split"]

    train_dataset = PoultryDataset(train_path, transform=train_tf, class_to_idx=class_to_idx)
    val_dataset = PoultryDataset(val_path, transform=eval_tf, class_to_idx=class_to_idx)
    test_dataset = PoultryDataset(test_path, transform=eval_tf, class_to_idx=class_to_idx)

    # Sampler configuration
    weighted_sampler = config.get("sampler", {}).get("weighted", False)
    if weighted_sampler:
        train_df = train_dataset.df
        class_counts = train_df["label"].value_counts()
        class_weights = {cls: 1.0 / count for cls, count in class_counts.items()}
        sample_weights = [class_weights[label] for label in train_df["label"]]
        sampler = WeightedRandomSampler(
            weights=torch.as_tensor(sample_weights, dtype=torch.double),
            num_samples=len(sample_weights),
            replacement=True,
        )
        shuffle = False
    else:
        sampler = None
        shuffle = True

    pin_memory = torch.cuda.is_available()
    train_loader = DataLoader(
        train_dataset,
        batch_size=bs,
        shuffle=shuffle,
        sampler=sampler,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=bs,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=bs,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
    )

    metadata = {
        "class_to_idx": class_to_idx,
        "idx_to_class": {v: k for k, v in class_to_idx.items()},
        "norm_mean": norm_stats[0],
        "norm_std": norm_stats[1],
        "train_size": len(train_dataset),
        "val_size": len(val_dataset),
        "test_size": len(test_dataset),
        "weighted_sampler_enabled": weighted_sampler,
    }

    return train_loader, val_loader, test_loader, metadata


def render_batch_preview(
    output_path: Path = PROJECT_ROOT / "reports" / "figures" / "batch_preview.png",
    n_images: int = 16,
):
    """Render one augmented batch to verify data transformations."""
    config = load_config()
    train_loader, _, _, meta = get_dataloaders(config=config, batch_size=n_images, num_workers=0)

    images, labels, _ = next(iter(train_loader))
    idx_to_class = meta["idx_to_class"]
    mean = np.array(meta["norm_mean"])
    std = np.array(meta["norm_std"])

    n_rows = 4
    n_cols = n_images // n_rows
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 4 * n_rows), dpi=150)

    for i in range(n_images):
        ax = axes[i // n_cols, i % n_cols]
        # Un-normalize image tensor back to [0, 1]
        img_np = images[i].permute(1, 2, 0).cpu().numpy()
        img_np = (img_np * std) + mean
        img_np = np.clip(img_np, 0.0, 1.0)

        label_name = idx_to_class[labels[i].item()]
        ax.imshow(img_np)
        ax.set_title(f"{label_name}", fontsize=11, fontweight="bold")
        ax.axis("off")

    plt.suptitle(
        "Augmented Training Batch Preview\n"
        "(Rotations ±20° with reflect padding, H/V flips, mild brightness/contrast)",
        fontsize=14,
        fontweight="bold",
        y=0.99,
    )
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    print(f"Batch preview saved successfully to {output_path}")


if __name__ == "__main__":
    render_batch_preview()
