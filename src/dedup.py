"""Deduplication and Group-Aware Splitting for Poultry Disease Detection.

Implements exact MD5 matching, perceptual hashing (pHash), connected components
clustering, and leak-free StratifiedGroupKFold splitting.
"""

from pathlib import Path
from typing import Dict, List, Tuple
import imagehash
import networkx as nx
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.model_selection import StratifiedGroupKFold
from tqdm import tqdm

from src.config import load_config
from src.utils import set_seed


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def compute_phashes(manifest_df: pd.DataFrame, root_dir: Path = PROJECT_ROOT) -> Tuple[List[imagehash.ImageHash], np.ndarray]:
    """Compute 64-bit perceptual hashes for all images in the manifest."""
    hashes = []
    print(f"Computing perceptual hashes (pHash) for {len(manifest_df)} images...")
    for rel_path in tqdm(manifest_df["filepath"], desc="pHash computation"):
        full_path = root_dir / rel_path
        with Image.open(full_path) as img:
            h = imagehash.phash(img)
            hashes.append(h)

    # Convert to (N, 64) boolean matrix for vectorized Hamming computation
    bool_matrix = np.array([h.hash.flatten() for h in hashes], dtype=bool)
    return hashes, bool_matrix


def compute_hamming_distance_matrix(bool_matrix: np.ndarray) -> np.ndarray:
    """Compute pairwise Hamming distance matrix vectorized via linear algebra."""
    float_mat = bool_matrix.astype(np.float32)
    row_sums = float_mat.sum(axis=1, keepdims=True)
    # Hamming distance: d(u,v) = sum(u) + sum(v) - 2*(u . v)
    dot = np.dot(float_mat, float_mat.T)
    dist = row_sums + row_sums.T - 2.0 * dot
    # Round to avoid precision artifacts
    return np.round(dist).astype(int)


def cluster_connected_components(dist_matrix: np.ndarray, threshold: int = 4) -> Tuple[List[int], dict]:
    """Extract connected components where Hamming distance <= threshold."""
    n = dist_matrix.shape[0]
    G = nx.Graph()
    G.add_nodes_from(range(n))

    # Add edges where distance <= threshold (upper triangular only)
    i_indices, j_indices = np.where((dist_matrix <= threshold) & (np.triu(np.ones((n, n), dtype=bool), k=1)))
    for i, j in zip(i_indices, j_indices):
        G.add_edge(i, j)

    components = list(nx.connected_components(G))
    group_ids = [0] * n
    for group_idx, comp in enumerate(components):
        for node in comp:
            group_ids[node] = group_idx

    group_sizes = [len(c) for c in components]
    stats = {
        "threshold": threshold,
        "total_images": n,
        "total_groups": len(components),
        "duplicate_burden": n - len(components),
        "singletons": sum(1 for s in group_sizes if s == 1),
        "clustered_groups": sum(1 for s in group_sizes if s > 1),
        "max_group_size": max(group_sizes) if group_sizes else 0,
        "mean_group_size": float(np.mean(group_sizes)) if group_sizes else 0.0,
    }
    return group_ids, stats


def perform_stratified_group_split(
    df: pd.DataFrame,
    output_dir: Path = PROJECT_ROOT / "data" / "splits",
    n_folds: int = 20,
    train_folds_count: int = 14,
    val_folds_count: int = 3,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Partition dataset into 70/15/15 train/val/test using StratifiedGroupKFold."""
    set_seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    sgkf = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    
    # Generate folds
    fold_assignments = np.zeros(len(df), dtype=int)
    for fold_idx, (_, test_idx) in enumerate(sgkf.split(df, df["label"], groups=df["group_id"])):
        fold_assignments[test_idx] = fold_idx

    # Allocate folds: 14/20 = 70% train, 3/20 = 15% val, 3/20 = 15% test
    train_mask = fold_assignments < train_folds_count
    val_mask = (fold_assignments >= train_folds_count) & (fold_assignments < train_folds_count + val_folds_count)
    test_mask = fold_assignments >= (train_folds_count + val_folds_count)

    train_df = df[train_mask].copy().reset_index(drop=True)
    val_df = df[val_mask].copy().reset_index(drop=True)
    test_df = df[test_mask].copy().reset_index(drop=True)

    # Zero-leakage assertion
    train_groups = set(train_df["group_id"])
    val_groups = set(val_df["group_id"])
    test_groups = set(test_df["group_id"])

    overlap_train_val = train_groups & val_groups
    overlap_train_test = train_groups & test_groups
    overlap_val_test = val_groups & test_groups

    if overlap_train_val or overlap_train_test or overlap_val_test:
        raise AssertionError(
            f"CRITICAL LEAKAGE DETECTED across splits!\n"
            f"Train-Val overlap: {len(overlap_train_val)} groups\n"
            f"Train-Test overlap: {len(overlap_train_test)} groups\n"
            f"Val-Test overlap: {len(overlap_val_test)} groups"
        )

    # Save split files
    cols_to_save = ["filepath", "label", "group_id"]
    train_df[cols_to_save].to_csv(output_dir / "train.csv", index=False)
    val_df[cols_to_save].to_csv(output_dir / "val.csv", index=False)
    test_df[cols_to_save].to_csv(output_dir / "test.csv", index=False)

    print(f"Splits saved successfully to {output_dir}")
    return train_df, val_df, test_df


def run_deduplication():
    """Main pipeline for deduplication and splitting."""
    cfg = load_config()
    threshold = cfg.get("dedup", {}).get("hamming_threshold", 4)
    seed = cfg.get("seed", 42)

    manifest_path = PROJECT_ROOT / cfg["paths"]["manifest_path"]
    df = pd.read_csv(manifest_path)

    # 1. Exact MD5 check
    exact_dups = len(df) - df["md5"].nunique()
    print(f"1. Exact MD5 Duplicates: {exact_dups} duplicate records ({df['md5'].nunique()} unique hashes)")

    # 2. Perceptual hashing & distance matrix
    _, bool_mat = compute_phashes(df)
    dist_mat = compute_hamming_distance_matrix(bool_mat)

    # 3. Sweep threshold <= 4 vs threshold <= 6
    group_ids_4, stats_4 = cluster_connected_components(dist_mat, threshold=4)
    _, stats_6 = cluster_connected_components(dist_mat, threshold=6)

    print("\n--- Deduplication Clustering Comparison ---")
    print(f"Threshold <= 4 (Configured):")
    print(f"  Total Images: {stats_4['total_images']}")
    print(f"  Total Groups: {stats_4['total_groups']}")
    print(f"  Duplicate Burden (Images - Groups): {stats_4['duplicate_burden']} images ({(stats_4['duplicate_burden']/stats_4['total_images'])*100:.1f}%)")
    print(f"  Singletons: {stats_4['singletons']}")
    print(f"  Multi-image clusters: {stats_4['clustered_groups']} (Max cluster size: {stats_4['max_group_size']})")

    print(f"\nThreshold <= 6 (Sensitivity Comparison):")
    print(f"  Total Images: {stats_6['total_images']}")
    print(f"  Total Groups: {stats_6['total_groups']}")
    print(f"  Duplicate Burden (Images - Groups): {stats_6['duplicate_burden']} images ({(stats_6['duplicate_burden']/stats_6['total_images'])*100:.1f}%)")
    print(f"  Singletons: {stats_6['singletons']}")
    print(f"  Multi-image clusters: {stats_6['clustered_groups']} (Max cluster size: {stats_6['max_group_size']})")

    # 4. Assign group_id to manifest
    df["group_id"] = group_ids_4
    df.to_csv(manifest_path, index=False)
    print(f"\nUpdated {manifest_path} with group_id.")

    # 5. StratifiedGroupKFold Split
    train_df, val_df, test_df = perform_stratified_group_split(
        df,
        output_dir=PROJECT_ROOT / cfg["paths"]["splits_dir"],
        seed=seed,
    )

    print("\n--- Split Proportions & Counts ---")
    n_total = len(df)
    print(f"Train: {len(train_df)} ({len(train_df)/n_total*100:.2f}%) across {train_df['group_id'].nunique()} groups")
    print(f"Val:   {len(val_df)} ({len(val_df)/n_total*100:.2f}%) across {val_df['group_id'].nunique()} groups")
    print(f"Test:  {len(test_df)} ({len(test_df)/n_total*100:.2f}%) across {test_df['group_id'].nunique()} groups")

    print("\n--- Class Proportions across Splits ---")
    classes = sorted(df["label"].unique())
    split_summary = []
    for cls in classes:
        tr_cnt = (train_df["label"] == cls).sum()
        va_cnt = (val_df["label"] == cls).sum()
        te_cnt = (test_df["label"] == cls).sum()
        tot_cnt = tr_cnt + va_cnt + te_cnt
        split_summary.append({
            "Class": cls,
            "Train (%)": f"{tr_cnt} ({tr_cnt/len(train_df)*100:.1f}%)",
            "Val (%)": f"{va_cnt} ({va_cnt/len(val_df)*100:.1f}%)",
            "Test (%)": f"{te_cnt} ({te_cnt/len(test_df)*100:.1f}%)",
            "Overall Total": tot_cnt,
        })
    print(pd.DataFrame(split_summary).to_string(index=False))

    return stats_4, stats_6


if __name__ == "__main__":
    run_deduplication()
