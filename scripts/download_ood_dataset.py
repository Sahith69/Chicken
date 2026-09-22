"""Download a curated realistic Out-Of-Distribution (OOD) benchmark dataset.

Collects ~300 realistic farm, household, and non-faecal images across 6 diverse categories:
1. shoes_boots (~50 images) - direct test for the 'shoe' failure mode
2. hands_gloves (~50 images) - human handlers / hands in farm settings
3. feed_troughs_buckets (~50 images) - feeding equipment, waterers, buckets
4. grass_foliage (~50 images) - lawn, pastures, outdoor vegetation
5. empty_floors (~50 images) - bare concrete, clean wood floor, tiles (clean background without feces)
6. household_objects (~50 images) - domestic tools, cups, plastic containers, vehicles

Saves images to data/ood/<category>/ and writes data/ood/manifest.csv.
"""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import urllib.parse
import urllib.request
import cv2
import numpy as np
import pandas as pd
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OOD_DIR = PROJECT_ROOT / "data" / "ood"

CATEGORIES = {
    "shoes_boots": [
        "leather work boot", "running shoe sneaker", "rubber boot wellington",
        "hiking boot shoe", "farmer boot shoe"
    ],
    "hands_gloves": [
        "human hand skin", "work gloves leather", "rubber latex gloves",
        "holding hand fingers", "gardening gloves"
    ],
    "feed_troughs_buckets": [
        "chicken feeder poultry", "plastic bucket farm", "livestock trough water",
        "feeding bucket animal", "poultry waterer drinker"
    ],
    "grass_foliage": [
        "green grass lawn", "pasture grass close up", "leaves foliage green",
        "clover lawn garden", "hay straw pasture"
    ],
    "empty_floors": [
        "concrete floor texture", "wooden floor boards", "ceramic tile floor",
        "gravel pebble ground", "clean soil earth ground"
    ],
    "household_objects": [
        "ceramic coffee mug", "plastic water bottle", "metal wrench tool",
        "cardboard box brown", "bicycle wheel tire"
    ],
}


def query_wikimedia_images(query: str, limit: int = 20) -> list[str]:
    """Query Wikimedia Commons API for image URLs matching query."""
    url = (
        "https://commons.wikimedia.org/w/api.php?"
        "action=query&generator=search&gsrnamespace=6&"
        f"gsrsearch={urllib.parse.quote(query)}&gsrlimit={limit}&"
        "prop=imageinfo&iiprop=url&format=json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "PoultryOODResearch/1.0 (academic research)"})
    urls = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            pages = data.get("query", {}).get("pages", {})
            for p in pages.values():
                info = p.get("imageinfo")
                if info and len(info) > 0:
                    img_url = info[0].get("url")
                    if img_url and any(img_url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                        urls.append(img_url)
    except Exception as e:
        print(f"Query error for '{query}': {e}")
    return urls


def download_and_process_image(url: str, save_path: Path) -> bool:
    """Download image, convert to 224x224 RGB JPEG."""
    if save_path.exists() and save_path.stat().st_size > 1000:
        return True
    req = urllib.request.Request(url, headers={"User-Agent": "PoultryOODResearch/1.0 (academic research)"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            img_bytes = resp.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            return False
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        # Center crop to square, then resize to 224x224
        h, w, _ = img_rgb.shape
        min_dim = min(h, w)
        sy = (h - min_dim) // 2
        sx = (w - min_dim) // 2
        cropped = img_rgb[sy : sy + min_dim, sx : sx + min_dim]
        resized = cv2.resize(cropped, (224, 224), interpolation=cv2.INTER_AREA)

        save_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(resized).save(save_path, "JPEG", quality=92)
        return True
    except Exception:
        return False


def main():
    print("=" * 80)
    print("DOWNLOADING CURATED REALISTIC OUT-OF-DISTRIBUTION (OOD) BENCHMARK")
    print("=" * 80)

    records = []
    target_per_category = 50

    for category, queries in CATEGORIES.items():
        cat_dir = OOD_DIR / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nProcessing category: '{category}' (target: {target_per_category} images)...")

        candidate_urls = []
        for q in queries:
            urls = query_wikimedia_images(q, limit=25)
            candidate_urls.extend(urls)

        # Deduplicate URLs
        candidate_urls = list(dict.fromkeys(candidate_urls))
        print(f"  Found {len(candidate_urls)} candidate image URLs for '{category}'.")

        saved_count = 0
        for i, url in enumerate(candidate_urls):
            if saved_count >= target_per_category:
                break
            filename = f"ood_{category}_{saved_count:03d}.jpg"
            save_path = cat_dir / filename
            success = download_and_process_image(url, save_path)
            if success:
                records.append({
                    "filepath": str(save_path.relative_to(PROJECT_ROOT)),
                    "category": category,
                    "source_url": url,
                })
                saved_count += 1

        print(f"  Successfully downloaded and formatted: {saved_count} images in '{category}'.")

    # Save manifest
    manifest_df = pd.DataFrame(records)
    manifest_path = OOD_DIR / "manifest.csv"
    manifest_df.to_csv(manifest_path, index=False)
    print(f"\nSaved OOD manifest to {manifest_path} (Total: {len(manifest_df)} OOD images across {len(CATEGORIES)} categories).")


if __name__ == "__main__":
    main()
