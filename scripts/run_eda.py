"""Exploratory Data Analysis (EDA) and Substrate Confounder Analysis for Phase 1."""

import os
from pathlib import Path
import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from PIL import Image
from scipy.stats import chi2_contingency
from sklearn.cluster import KMeans
from tqdm import tqdm

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams["font.family"] = "sans-serif"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.csv"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
np.random.seed(SEED)


def load_manifest() -> pd.DataFrame:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found at {MANIFEST_PATH}")
    return pd.read_csv(MANIFEST_PATH)


def plot_class_distribution(df: pd.DataFrame) -> dict:
    """Plot class distribution and compute class imbalance ratios."""
    counts = df["label"].value_counts()
    total = len(df)
    max_count = counts.max()
    min_count = counts.min()
    imbalance_ratio = max_count / min_count

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    palette = sns.color_palette("muted", len(counts))
    bars = sns.barplot(x=counts.index, y=counts.values, ax=ax, palette=palette)

    for p in bars.patches:
        height = p.get_height()
        pct = (height / total) * 100
        ax.annotate(
            f"{int(height):,}\n({pct:.1f}%)",
            (p.get_x() + p.get_width() / 2.0, height / 2.0),
            ha="center",
            va="center",
            fontsize=11,
            color="white",
            fontweight="bold",
        )

    ax.set_title(
        f"Poultry Disease Dataset — Class Distribution (N = {total:,})\n"
        f"Imbalance Ratio (Max / Min): {imbalance_ratio:.2f}:1 "
        f"({counts.idxmax()} vs {counts.idxmin()})",
        fontsize=12,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Disease Class", fontsize=11, fontweight="bold")
    ax.set_ylabel("Image Count", fontsize=11, fontweight="bold")
    plt.tight_layout()

    out_path = FIGURES_DIR / "class_distribution.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Saved: {out_path}")

    return {
        "counts": counts.to_dict(),
        "imbalance_ratio": imbalance_ratio,
        "max_class": counts.idxmax(),
        "min_class": counts.idxmin(),
    }


def plot_image_size_distribution(df: pd.DataFrame) -> None:
    """Plot distribution of image dimensions and file sizes."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=150)

    # Resolution bar
    res_series = df["width"].astype(str) + "x" + df["height"].astype(str)
    res_counts = res_series.value_counts()
    sns.barplot(x=res_counts.index, y=res_counts.values, ax=axes[0], color="#4C72B0")
    axes[0].set_title("Resolution Distribution", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Dimensions (W x H)", fontsize=10, fontweight="bold")
    axes[0].set_ylabel("Count", fontsize=10, fontweight="bold")
    for p in axes[0].patches:
        axes[0].annotate(
            f"{int(p.get_height()):,} ({p.get_height()/len(df)*100:.1f}%)",
            (p.get_x() + p.get_width() / 2.0, p.get_height() / 2.0),
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
        )

    # Filesize KDE / Boxplot across classes
    df_kb = df.copy()
    df_kb["filesize_kb"] = df_kb["filesize"] / 1024.0
    sns.boxplot(x="label", y="filesize_kb", data=df_kb, ax=axes[1], palette="Set2")
    axes[1].set_title("File Size Distribution by Class (KB)", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Class", fontsize=10, fontweight="bold")
    axes[1].set_ylabel("File Size (KB)", fontsize=10, fontweight="bold")

    plt.tight_layout()
    out_path = FIGURES_DIR / "image_size_distribution.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_sample_grids(df: pd.DataFrame) -> None:
    """Plot 4x5 sample grid per class and a composite overview grid."""
    classes = sorted(df["label"].unique())

    # 1. Composite grid: 4 classes (rows) x 5 samples (cols)
    fig, axes = plt.subplots(len(classes), 5, figsize=(15, 12), dpi=150)
    for row_idx, cls in enumerate(classes):
        cls_df = df[df["label"] == cls]
        sample_paths = cls_df.sample(5, random_state=SEED)["filepath"].tolist()
        for col_idx, rel_path in enumerate(sample_paths):
            ax = axes[row_idx, col_idx]
            img = Image.open(PROJECT_ROOT / rel_path)
            ax.imshow(img)
            ax.axis("off")
            if col_idx == 0:
                ax.set_title(cls, fontsize=12, fontweight="bold", loc="left")

    plt.suptitle("Representative Fecal Samples by Class (Composite Grid)", fontsize=14, fontweight="bold", y=0.99)
    plt.tight_layout()
    comp_path = FIGURES_DIR / "sample_grid_composite.png"
    fig.savefig(comp_path)
    plt.close(fig)
    print(f"Saved: {comp_path}")

    # 2. Individual 4x5 sample grids per class (20 images each)
    for cls in classes:
        cls_df = df[df["label"] == cls]
        sample_paths = cls_df.sample(20, random_state=SEED)["filepath"].tolist()
        fig, axes = plt.subplots(4, 5, figsize=(15, 12), dpi=150)
        for i, rel_path in enumerate(sample_paths):
            ax = axes[i // 5, i % 5]
            img = Image.open(PROJECT_ROOT / rel_path)
            ax.imshow(img)
            ax.axis("off")
            filename = Path(rel_path).name
            ax.set_title(filename, fontsize=9)
        plt.suptitle(f"Sample Grid (4x5) — {cls} (20 Random Samples)", fontsize=14, fontweight="bold", y=0.99)
        plt.tight_layout()
        cls_path = FIGURES_DIR / f"sample_grid_4x5_{cls.replace(' ', '_')}.png"
        fig.savefig(cls_path)
        plt.close(fig)
        print(f"Saved: {cls_path}")


def compute_color_histograms(df: pd.DataFrame, max_samples_per_class: int = 500) -> None:
    """Compute and plot average RGB and HSV histograms per class."""
    classes = sorted(df["label"].unique())

    rgb_hists = {cls: {"R": np.zeros(256), "G": np.zeros(256), "B": np.zeros(256), "count": 0} for cls in classes}
    hsv_hists = {cls: {"H": np.zeros(180), "S": np.zeros(256), "V": np.zeros(256), "count": 0} for cls in classes}

    print("Computing mean color histograms...")
    for cls in classes:
        cls_df = df[df["label"] == cls]
        sample_df = cls_df.sample(min(len(cls_df), max_samples_per_class), random_state=SEED)

        for rel_path in sample_df["filepath"]:
            img_bgr = cv2.imread(str(PROJECT_ROOT / rel_path))
            if img_bgr is None:
                continue

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

            # RGB histograms
            for idx, channel in enumerate(["R", "G", "B"]):
                hist = cv2.calcHist([img_rgb], [idx], None, [256], [0, 256]).flatten()
                rgb_hists[cls][channel] += hist / hist.sum()

            # HSV histograms
            h_hist = cv2.calcHist([img_hsv], [0], None, [180], [0, 180]).flatten()
            s_hist = cv2.calcHist([img_hsv], [1], None, [256], [0, 256]).flatten()
            v_hist = cv2.calcHist([img_hsv], [2], None, [256], [0, 256]).flatten()

            hsv_hists[cls]["H"] += h_hist / h_hist.sum()
            hsv_hists[cls]["S"] += s_hist / s_hist.sum()
            hsv_hists[cls]["V"] += v_hist / v_hist.sum()
            rgb_hists[cls]["count"] += 1
            hsv_hists[cls]["count"] += 1

    # Normalize by count
    for cls in classes:
        cnt = rgb_hists[cls]["count"]
        for c in ["R", "G", "B"]:
            rgb_hists[cls][c] /= cnt
        for c in ["H", "S", "V"]:
            hsv_hists[cls][c] /= cnt

    # Plotting
    fig, axes = plt.subplots(4, 2, figsize=(16, 14), dpi=150)
    for i, cls in enumerate(classes):
        # RGB
        ax_rgb = axes[i, 0]
        ax_rgb.plot(rgb_hists[cls]["R"], color="red", label="Red", lw=1.8)
        ax_rgb.plot(rgb_hists[cls]["G"], color="green", label="Green", lw=1.8)
        ax_rgb.plot(rgb_hists[cls]["B"], color="blue", label="Blue", lw=1.8)
        ax_rgb.set_title(f"{cls} — Mean RGB Profile", fontsize=11, fontweight="bold")
        ax_rgb.set_xlim([0, 255])
        ax_rgb.set_ylabel("Normalized Density", fontsize=9)
        ax_rgb.legend(loc="upper right", frameon=True)

        # HSV
        ax_hsv = axes[i, 1]
        ax_hsv.plot(hsv_hists[cls]["H"][:180], color="orange", label="Hue (0-179)", lw=1.8)
        ax_hsv.plot(hsv_hists[cls]["S"], color="purple", label="Saturation (0-255)", lw=1.8)
        ax_hsv.plot(hsv_hists[cls]["V"], color="black", label="Value (0-255)", lw=1.8, linestyle="--")
        ax_hsv.set_title(f"{cls} — Mean HSV Profile", fontsize=11, fontweight="bold")
        ax_hsv.set_xlim([0, 255])
        ax_hsv.legend(loc="upper right", frameon=True)

    axes[3, 0].set_xlabel("Pixel Intensity (0-255)", fontsize=10, fontweight="bold")
    axes[3, 1].set_xlabel("Bin (0-255)", fontsize=10, fontweight="bold")

    plt.suptitle("Mean RGB and HSV Spectral Distributions per Class", fontsize=14, fontweight="bold", y=0.99)
    plt.tight_layout()
    out_path = FIGURES_DIR / "mean_color_histograms.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Saved: {out_path}")


def substrate_confounder_analysis(df: pd.DataFrame, border_frac: float = 0.15, n_clusters: int = 4) -> dict:
    """Analyze background/substrate confounder via border crop clustering and cross-tabulation."""
    print("Running Substrate Confounder Analysis on border crops...")
    border_features = []
    valid_indices = []

    # Border width in pixels for 224x224
    margin = int(224 * border_frac)

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Extracting border features"):
        rel_path = row["filepath"]
        img_bgr = cv2.imread(str(PROJECT_ROOT / rel_path))
        if img_bgr is None:
            continue

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # Extract border regions: top, bottom, left, right strips
        h, w, _ = img_rgb.shape
        top_rgb = img_rgb[:margin, :, :]
        bot_rgb = img_rgb[h - margin :, :, :]
        left_rgb = img_rgb[margin : h - margin, :margin, :]
        right_rgb = img_rgb[margin : h - margin, w - margin :, :]

        border_pixels_rgb = np.concatenate([
            top_rgb.reshape(-1, 3),
            bot_rgb.reshape(-1, 3),
            left_rgb.reshape(-1, 3),
            right_rgb.reshape(-1, 3),
        ], axis=0)

        border_pixels_hsv = np.concatenate([
            img_hsv[:margin, :, :].reshape(-1, 3),
            img_hsv[h - margin :, :, :].reshape(-1, 3),
            img_hsv[margin : h - margin, :margin, :].reshape(-1, 3),
            img_hsv[margin : h - margin, w - margin :, :].reshape(-1, 3),
        ], axis=0)

        # Feature vector: mean RGB, std RGB, mean HSV, std HSV of the border
        feat = np.hstack([
            border_pixels_rgb.mean(axis=0),
            border_pixels_rgb.std(axis=0),
            border_pixels_hsv.mean(axis=0),
            border_pixels_hsv.std(axis=0),
        ])
        border_features.append(feat)
        valid_indices.append(idx)

    X = np.array(border_features)
    kmeans = KMeans(n_clusters=n_clusters, random_state=SEED, n_init=10)
    clusters = kmeans.fit_predict(X)

    sub_df = df.loc[valid_indices].copy()
    cluster_names = [f"Substrate Cluster {i}" for i in range(n_clusters)]
    sub_df["substrate_cluster"] = [cluster_names[c] for c in clusters]

    # Cross-tabulation (counts and row/column percentages)
    ct_counts = pd.crosstab(sub_df["substrate_cluster"], sub_df["label"])
    ct_pct_col = pd.crosstab(sub_df["substrate_cluster"], sub_df["label"], normalize="columns") * 100
    ct_pct_row = pd.crosstab(sub_df["substrate_cluster"], sub_df["label"], normalize="index") * 100

    # Chi-squared test of independence
    chi2, p_val, dof, _ = chi2_contingency(ct_counts)
    n = len(sub_df)
    cramers_v = np.sqrt(chi2 / (n * (min(ct_counts.shape) - 1)))

    # Plot Cross-Tab Heatmap
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), dpi=150)
    sns.heatmap(ct_counts, annot=True, fmt="d", cmap="Blues", ax=axes[0])
    axes[0].set_title(
        f"Substrate Cluster vs Disease Class (Counts)\n"
        f"Chi2: {chi2:.1f}, p: {p_val:.2e}, Cramer's V: {cramers_v:.3f}",
        fontsize=11,
        fontweight="bold",
    )
    axes[0].set_ylabel("Substrate Cluster (Border Color/Texture)", fontsize=10, fontweight="bold")
    axes[0].set_xlabel("Disease Class", fontsize=10, fontweight="bold")

    sns.heatmap(ct_pct_col, annot=True, fmt=".1f", cmap="YlGnBu", ax=axes[1])
    axes[1].set_title("Column-Normalized Percentage (% within Class)", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("Substrate Cluster", fontsize=10, fontweight="bold")
    axes[1].set_xlabel("Disease Class", fontsize=10, fontweight="bold")

    plt.tight_layout()
    ct_path = FIGURES_DIR / "substrate_cluster_crosstab.png"
    fig.savefig(ct_path)
    plt.close(fig)
    print(f"Saved: {ct_path}")

    # Visual grid of substrate cluster representatives
    fig, axes = plt.subplots(n_clusters, 5, figsize=(15, 3 * n_clusters), dpi=150)
    for c_idx in range(n_clusters):
        c_name = cluster_names[c_idx]
        cluster_samples = sub_df[sub_df["substrate_cluster"] == c_name].sample(5, random_state=SEED)
        for s_idx, (_, sample_row) in enumerate(cluster_samples.iterrows()):
            ax = axes[c_idx, s_idx]
            img = Image.open(PROJECT_ROOT / sample_row["filepath"])
            ax.imshow(img)
            ax.axis("off")
            if s_idx == 0:
                ax.set_title(f"{c_name}\n({sample_row['label']})", fontsize=10, fontweight="bold", loc="left")
            else:
                ax.set_title(sample_row["label"], fontsize=9)

    plt.suptitle("Visual Substrate Audit — Exemplars across Border Clusters", fontsize=14, fontweight="bold", y=0.99)
    plt.tight_layout()
    grid_path = FIGURES_DIR / "substrate_visual_grid.png"
    fig.savefig(grid_path)
    plt.close(fig)
    print(f"Saved: {grid_path}")

    # Determine whether concerning
    # A Cramer's V > 0.3 indicates moderate-to-strong association
    is_concerning = cramers_v > 0.3 or p_val < 0.001

    return {
        "counts": ct_counts.to_dict(),
        "pct_col": ct_pct_col.to_dict(),
        "chi2": chi2,
        "p_val": p_val,
        "cramers_v": cramers_v,
        "is_concerning": is_concerning,
    }


def main():
    print("Loading manifest...")
    df = load_manifest()
    print(f"Loaded {len(df)} records.")

    print("1. Plotting class distribution...")
    dist_info = plot_class_distribution(df)

    print("2. Plotting image size distribution...")
    plot_image_size_distribution(df)

    print("3. Generating sample grids...")
    plot_sample_grids(df)

    print("4. Computing mean color histograms...")
    compute_color_histograms(df)

    print("5. Running substrate confounder check...")
    substrate_info = substrate_confounder_analysis(df)

    print("\nEDA and Substrate Analysis Completed Successfully!")
    print(f"Imbalance ratio: {dist_info['imbalance_ratio']:.2f}:1")
    print(f"Substrate Cramer's V: {substrate_info['cramers_v']:.3f} (Concerning: {substrate_info['is_concerning']})")


if __name__ == "__main__":
    main()
