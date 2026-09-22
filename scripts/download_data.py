"""Download and flatten poultry disease dataset.

Pulls the dataset from Kaggle or Zenodo and flattens all upstream
train/val/test split directories into data/raw/<class>/.
"""

import os
import shutil
import sys
from pathlib import Path
from collections import defaultdict


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
TMP_DOWNLOAD_DIR = PROJECT_ROOT / "data" / "_tmp_download"
LOGS_DIR = PROJECT_ROOT / "reports"

CLASS_NAME_MAP = {
    "coccidiosis": "Coccidiosis",
    "cocci": "Coccidiosis",
    "healthy": "Healthy",
    "new castle disease": "Newcastle Disease",
    "newcastle disease": "Newcastle Disease",
    "newcastle": "Newcastle Disease",
    "ncd": "Newcastle Disease",
    "salmonella": "Salmonella",
    "salmo": "Salmonella",
}


def check_kaggle_credentials() -> bool:
    """Check whether Kaggle credentials exist on the host."""
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    has_env = "KAGGLE_USERNAME" in os.environ and "KAGGLE_KEY" in os.environ
    return kaggle_json.exists() or has_env


def download_dataset(dataset_ref: str = "efoeetienneblavo/chicken-disease-dataset") -> Path:
    """Download the dataset using the Kaggle API into a temporary directory."""
    if not check_kaggle_credentials():
        print(
            "ERROR: Kaggle credentials not found!\n"
            "Please place your Kaggle API key at ~/.kaggle/kaggle.json\n"
            "or set KAGGLE_USERNAME and KAGGLE_KEY environment variables.",
            file=sys.stderr,
        )
        sys.exit(1)

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    # Fast-path cache if already downloaded in /tmp
    cached_dir = Path("/tmp/kaggle_test2")
    if cached_dir.exists() and (cached_dir / "chicken_disease").exists():
        print(f"Using cached download from {cached_dir}...")
        return cached_dir

    TMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading dataset '{dataset_ref}' to {TMP_DOWNLOAD_DIR}...")
    api.dataset_download_files(dataset_ref, path=str(TMP_DOWNLOAD_DIR), unzip=True)
    print("Download and unzip complete.")
    return TMP_DOWNLOAD_DIR


def flatten_and_pool(download_dir: Path) -> dict:
    """Flatten upstream train/val/test folders into data/raw/<class>/."""
    # Ensure target class directories exist
    target_classes = ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]
    for cls in target_classes:
        (RAW_DIR / cls).mkdir(parents=True, exist_ok=True)

    log_counts = defaultdict(lambda: defaultdict(int))
    total_flattened = 0

    # Locate image files
    valid_exts = {".jpg", ".jpeg", ".png"}
    for root, _, files in os.walk(download_dir):
        rel_root = Path(root).relative_to(download_dir)
        parts = rel_root.parts

        # Detect upstream split folder if present
        split_name = "root"
        for p in parts:
            if p.lower() in ("train", "validation", "val", "test"):
                split_name = p.lower()
                break

        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() not in valid_exts:
                continue

            # Determine class from folder or filename
            class_name = None
            for part in reversed(parts):
                norm_part = part.lower().strip()
                if norm_part in CLASS_NAME_MAP:
                    class_name = CLASS_NAME_MAP[norm_part]
                    break

            if not class_name:
                prefix = file.split(".")[0].lower()
                class_name = CLASS_NAME_MAP.get(prefix)

            if not class_name:
                print(f"Warning: Could not identify class for {file_path}", file=sys.stderr)
                continue

            target_path = RAW_DIR / class_name / file
            if target_path.exists():
                # Avoid filename collisions across upstream splits if any
                target_path = RAW_DIR / class_name / f"{split_name}_{file}"

            shutil.copy2(file_path, target_path)
            log_counts[split_name][class_name] += 1
            total_flattened += 1

    return log_counts


def write_flattening_report(log_counts: dict) -> str:
    """Format and write the flattening log."""
    lines = []
    lines.append("=" * 60)
    lines.append("UPSTREAM DATASET FLATTENING AUDIT LOG")
    lines.append("=" * 60)
    lines.append(f"Destination: {RAW_DIR}")
    lines.append("")

    splits = sorted(log_counts.keys())
    all_classes = ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]

    for split in splits:
        lines.append(f"Upstream Split: [{split.upper()}]")
        split_total = 0
        for cls in all_classes:
            cnt = log_counts[split][cls]
            split_total += cnt
            lines.append(f"  - {cls:<20}: {cnt:>5} images")
        lines.append(f"  Total for {split}: {split_total} images\n")

    lines.append("-" * 60)
    lines.append("FINAL POOLED CLASS TOTALS IN data/raw/:")
    grand_total = 0
    for cls in all_classes:
        cls_total = sum(log_counts[s][cls] for s in splits)
        grand_total += cls_total
        lines.append(f"  - {cls:<20}: {cls_total:>5} images")
    lines.append("-" * 60)
    lines.append(f"GRAND TOTAL POOLED IMAGES: {grand_total}")
    lines.append("=" * 60)

    report_text = "\n".join(lines)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = LOGS_DIR / "flattening_log.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_text + "\n")

    return report_text


def main():
    print("Starting Phase 1 data acquisition...")
    download_dir = download_dataset()
    print("Flattening and pooling images into data/raw/...")
    log_counts = flatten_and_pool(download_dir)

    # Clean up temporary download dir
    shutil.rmtree(TMP_DOWNLOAD_DIR, ignore_errors=True)

    report_text = write_flattening_report(log_counts)
    print(report_text)


if __name__ == "__main__":
    main()
