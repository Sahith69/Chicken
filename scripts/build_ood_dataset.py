"""Build curated 300-image Out-Of-Distribution (OOD) benchmark dataset.

Constructs 300 diverse out-of-domain images across 4 distinct categories (75 images each):
1. shoes_boots (75 images) - leather boots, work boots, sneakers, loafers, sandals (the primary 'shoe' failure case)
2. hands_skin (75 images) - human hands, fingers, skin, handler gestures
3. domestic_objects (75 images) - ceramic mugs, cups, domestic containers
4. clean_soils (75 images) - bare unsoiled earth, clay, red earth, alluvial soil (empty pen floors with zero feces)

Saves all images as 224x224 RGB JPEG into data/ood/<category>/ and writes data/ood/manifest.csv.
"""

from pathlib import Path
import random
import cv2
import numpy as np
import pandas as pd
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OOD_DIR = PROJECT_ROOT / "data" / "ood"


def format_and_save(src_path: Path, dst_path: Path) -> bool:
    try:
        img_bgr = cv2.imread(str(src_path))
        if img_bgr is None:
            return False
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w, _ = img_rgb.shape
        min_dim = min(h, w)
        sy = (h - min_dim) // 2
        sx = (w - min_dim) // 2
        cropped = img_rgb[sy : sy + min_dim, sx : sx + min_dim]
        resized = cv2.resize(cropped, (224, 224), interpolation=cv2.INTER_AREA)

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(resized).save(dst_path, "JPEG", quality=92)
        return True
    except Exception:
        return False


def main():
    random.seed(42)
    OOD_DIR.mkdir(parents=True, exist_ok=True)
    records = []

    # 1. Shoes & Boots (75 images)
    shoe_dir = Path("/tmp/kaggle_shoe/shoeTypeClassifierDataset")
    shoe_files = [p for p in shoe_dir.rglob("*.jpg") if p.is_file()]
    random.shuffle(shoe_files)
    print(f"Found {len(shoe_files)} shoe candidates. Selecting 75...")
    target_shoe = OOD_DIR / "shoes_boots"
    target_shoe.mkdir(exist_ok=True)
    count = 0
    for p in shoe_files:
        if count >= 75:
            break
        dst = target_shoe / f"shoe_{count:03d}.jpg"
        if format_and_save(p, dst):
            records.append({
                "filepath": str(dst.relative_to(PROJECT_ROOT)),
                "category": "shoes_boots",
                "source_file": p.name,
            })
            count += 1
    print(f"  Formatted {count} shoes/boots.")

    # 2. Hands & Skin (75 images)
    hand_dir = Path("/tmp/kaggle_hands")
    hand_files = [p for p in hand_dir.rglob("*.jpg") if p.is_file()]
    random.shuffle(hand_files)
    print(f"Found {len(hand_files)} hand candidates. Selecting 75...")
    target_hand = OOD_DIR / "hands_skin"
    target_hand.mkdir(exist_ok=True)
    count = 0
    for p in hand_files:
        if count >= 75:
            break
        dst = target_hand / f"hand_{count:03d}.jpg"
        if format_and_save(p, dst):
            records.append({
                "filepath": str(dst.relative_to(PROJECT_ROOT)),
                "category": "hands_skin",
                "source_file": p.name,
            })
            count += 1
    print(f"  Formatted {count} hands.")

    # 3. Domestic Objects / Mugs (75 images)
    mug_dir = Path("/tmp/kaggle_mugs")
    mug_files = [p for p in mug_dir.rglob("*.jpg") if p.is_file()]
    random.shuffle(mug_files)
    print(f"Found {len(mug_files)} mug candidates. Selecting 75...")
    target_mug = OOD_DIR / "domestic_objects"
    target_mug.mkdir(exist_ok=True)
    count = 0
    for p in mug_files:
        if count >= 75:
            break
        dst = target_mug / f"object_{count:03d}.jpg"
        if format_and_save(p, dst):
            records.append({
                "filepath": str(dst.relative_to(PROJECT_ROOT)),
                "category": "domestic_objects",
                "source_file": p.name,
            })
            count += 1
    print(f"  Formatted {count} domestic objects.")

    # 4. Clean Soils / Empty Ground (75 images)
    soil_dir = Path("/tmp/kaggle_soils")
    soil_files = [p for p in soil_dir.rglob("*.jpg") if p.is_file()]
    random.shuffle(soil_files)
    print(f"Found {len(soil_files)} soil candidates. Selecting 75...")
    target_soil = OOD_DIR / "clean_soils"
    target_soil.mkdir(exist_ok=True)
    count = 0
    for p in soil_files:
        if count >= 75:
            break
        dst = target_soil / f"soil_{count:03d}.jpg"
        if format_and_save(p, dst):
            records.append({
                "filepath": str(dst.relative_to(PROJECT_ROOT)),
                "category": "clean_soils",
                "source_file": p.name,
            })
            count += 1
    print(f"  Formatted {count} clean soils.")

    # Save manifest
    manifest_df = pd.DataFrame(records)
    manifest_path = OOD_DIR / "manifest.csv"
    manifest_df.to_csv(manifest_path, index=False)
    print(f"\nOOD Benchmark Dataset successfully generated at {OOD_DIR}!")
    print(f"Total: {len(manifest_df)} images across {manifest_df['category'].nunique()} categories.")
    print(manifest_df["category"].value_counts().to_string())


if __name__ == "__main__":
    main()
