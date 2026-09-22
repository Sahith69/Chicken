"""Utility functions for seeding, device selection, logging, and metrics."""

import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import numpy as np
import torch


def set_seed(seed: int = 42) -> None:
    """Set random seed across all libraries for deterministic execution.

    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def get_device() -> torch.device:
    """Detect and return the preferred available compute device.

    Priority: CUDA -> MPS -> CPU.

    Returns:
        torch.device instance.
    """
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def get_run_dir(base_dir: str | Path = "runs", name: str | None = None) -> Path:
    """Create and return a timestamped run directory for logging experiments.

    Args:
        base_dir: Base directory for storing experiment runs.
        name: Optional run name suffix.

    Returns:
        Path to the created run directory.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{timestamp}_{name}" if name else timestamp
    run_dir = Path(base_dir) / folder_name
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_metrics(metrics: Dict[str, Any], filepath: str | Path) -> None:
    """Serialize and save metrics dictionary to a JSON file.

    Args:
        metrics: Dictionary containing scalar or structured metrics.
        filepath: Destination path for the JSON file.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)
