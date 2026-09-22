"""Prepare sample gallery images for Streamlit app (Phase 8).

Selects:
- 2 Coccidiosis test images
- 2 Healthy test images (including 1 on hard non-wood substrate)
- 2 Newcastle test images
- 2 Salmonella test images
- 3 OOD distractor images (boot, hand, clean soil)

Copies them into app/samples/ with a manifest app/samples/manifest.json.
"""

import json
from pathlib import Path
import shutil
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = PROJECT_ROOT / "app" / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

test_df = pd.read_csv(PROJECT_ROOT / "data" / "splits" / "test.csv")
ood_df = pd.read_csv(PROJECT_ROOT / "data" / "ood" / "manifest.csv")

samples = [
    # Coccidiosis
    {
        "id": "cocci_01",
        "name": "Coccidiosis (Bloody Mucus, Wood Shavings)",
        "category": "Coccidiosis",
        "is_ood": False,
        "source": "data/raw/Coccidiosis/cocci.1002.jpg",
        "description": "Characteristic frank crimson blood and mucosal shedding on wood shavings bedding.",
    },
    {
        "id": "cocci_02",
        "name": "Coccidiosis (Mucoid Red Core, Straw Floor)",
        "category": "Coccidiosis",
        "is_ood": False,
        "source": "data/raw/Coccidiosis/cocci.1067.jpg",
        "description": "Mucoid hemorrhage on pen straw (Phase 5 hard minority subset sample).",
    },
    # Healthy
    {
        "id": "healthy_01",
        "name": "Healthy (Normal Cecal Dropping, Wood Shavings)",
        "category": "Healthy",
        "is_ood": False,
        "source": "data/raw/Healthy/healthy.1000.jpg",
        "description": "Typical normal brown stool capped with white uric acid on wood shavings.",
    },
    {
        "id": "healthy_02",
        "name": "Healthy (Normal Dropping, Mixed Soil Bedding)",
        "category": "Healthy",
        "is_ood": False,
        "source": "data/raw/Healthy/healthy.1037.jpg",
        "description": "Normal dropping on darker bedding — surfaces the substrate confounder limitation.",
    },
    # Newcastle Disease
    {
        "id": "newcastle_01",
        "name": "Newcastle Disease (Emerald Green Watery Diarrhea)",
        "category": "Newcastle Disease",
        "is_ood": False,
        "source": "data/raw/Newcastle Disease/ncd.100.jpg",
        "description": "Classic watery emerald-green diarrhea indicative of paramyxovirus enteritis.",
    },
    {
        "id": "newcastle_02",
        "name": "Newcastle Disease (Bile-Stained Mucoid Dropping)",
        "category": "Newcastle Disease",
        "is_ood": False,
        "source": "data/raw/Newcastle Disease/ncd.106.jpg",
        "description": "Whitish-green mucoid stool with watery perimeter.",
    },
    # Salmonella
    {
        "id": "salmonella_01",
        "name": "Salmonella (Sulfur-Yellow Chalky Urate)",
        "category": "Salmonella",
        "is_ood": False,
        "source": "data/raw/Salmonella/salmo.1001.jpg",
        "description": "Pasty sulfur-yellow stool characteristic of pullorum/gallinarum infection.",
    },
    {
        "id": "salmonella_02",
        "name": "Salmonella (Yellowish-Green Watery Stool)",
        "category": "Salmonella",
        "is_ood": False,
        "source": "data/raw/Salmonella/salmo.1026.jpg",
        "description": "Sulfur-yellow watery diarrhea on pen floor.",
    },
    # Out of Distribution Distractors
    {
        "id": "ood_boot_01",
        "name": "Distractor: Rubber Gumboot (Non-Fecal)",
        "category": "Out-of-Distribution",
        "is_ood": True,
        "source": "data/ood/shoes_boots/shoe_000.jpg",
        "description": "Real farm work boot in pen. Must be rejected by OOD gate without disease prediction.",
    },
    {
        "id": "ood_hand_01",
        "name": "Distractor: Human Hand (Non-Fecal)",
        "category": "Out-of-Distribution",
        "is_ood": True,
        "source": "data/ood/hands_skin/hand_000.jpg",
        "description": "Human hand/fingers pointing in pen frame. Must trigger INVALID_SAMPLE rejection.",
    },
    {
        "id": "ood_soil_01",
        "name": "Distractor: Clean Soil Floor (No Dropping)",
        "category": "Out-of-Distribution",
        "is_ood": True,
        "source": "data/ood/clean_soils/soil_000.jpg",
        "description": "Bare unsoiled earth with zero fecal matter. Must trigger OOD warning.",
    },
]

manifest_entries = []
for item in samples:
    src_path = PROJECT_ROOT / item["source"]
    if not src_path.exists():
        print(f"Warning: Source not found: {src_path}")
        continue
    dst_filename = f"{item['id']}_{src_path.name}"
    dst_path = SAMPLES_DIR / dst_filename
    shutil.copy2(src_path, dst_path)
    manifest_entries.append({
        "id": item["id"],
        "name": item["name"],
        "category": item["category"],
        "is_ood": item["is_ood"],
        "filename": dst_filename,
        "description": item["description"],
    })

manifest_file = SAMPLES_DIR / "manifest.json"
with open(manifest_file, "w") as f:
    json.dump(manifest_entries, f, indent=2)

print(f"Successfully staged {len(manifest_entries)} gallery samples in {SAMPLES_DIR}")
