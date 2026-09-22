"""Build data/manifest.csv with image metadata and checksums."""

import hashlib
import os
from pathlib import Path
import pandas as pd
from PIL import Image
from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.csv"


def compute_md5(filepath: Path, chunk_size: int = 65536) -> str:
    """Compute MD5 checksum for a file."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_manifest(raw_dir: Path = RAW_DIR, output_path: Path = MANIFEST_PATH) -> pd.DataFrame:
    """Scan raw image files and construct manifest CSV."""
    records = []
    valid_exts = {".jpg", ".jpeg", ".png"}

    image_paths = sorted([
        p for p in raw_dir.glob("**/*")
        if p.is_file() and p.suffix.lower() in valid_exts and not p.name.startswith(".")
    ])

    print(f"Building manifest for {len(image_paths)} images in {raw_dir}...")

    for path in tqdm(image_paths, desc="Processing images"):
        label = path.parent.name
        filesize = path.stat().st_size
        md5 = compute_md5(path)

        try:
            with Image.open(path) as img:
                width, height = img.size
        except Exception as e:
            print(f"Warning: Corrupt or unreadable image {path}: {e}")
            width, height = None, None

        rel_path = path.relative_to(PROJECT_ROOT).as_posix()
        records.append({
            "filepath": rel_path,
            "label": label,
            "width": width,
            "height": height,
            "filesize": filesize,
            "md5": md5,
        })

    df = pd.DataFrame(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Manifest successfully created at {output_path} with {len(df)} rows.")
    return df


if __name__ == "__main__":
    build_manifest()
