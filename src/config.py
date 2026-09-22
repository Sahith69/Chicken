"""Configuration loader and schema validation."""

import os
from pathlib import Path
from typing import Any, Dict
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Dict containing configuration parameters.
    """
    path = Path(config_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    validate_config(config)
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """Validate that required keys are present in config."""
    required_top_keys = [
        "paths",
        "seed",
        "image_size",
        "batch_size",
        "epochs",
        "lr",
        "backbone",
        "classes",
        "loss",
        "sampler",
        "normalization",
        "dedup",
    ]
    missing = [k for k in required_top_keys if k not in config]
    if missing:
        raise ValueError(f"Missing required configuration keys: {missing}")

    if config["loss"].get("type") not in ("weighted_ce", "focal"):
        raise ValueError(
            f"Invalid loss type: {config['loss'].get('type')}. Expected 'weighted_ce' or 'focal'."
        )

    if config["normalization"].get("mode") not in ("imagenet", "dataset"):
        raise ValueError(
            f"Invalid normalization mode: {config['normalization'].get('mode')}. "
            "Expected 'imagenet' or 'dataset'."
        )
