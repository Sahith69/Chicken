import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

os.makedirs("reports/figures", exist_ok=True)

# -------------------------------------------------------------
# 1. Pipeline Architecture Diagram
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
ax.set_xlim(0, 14)
ax.set_ylim(0, 7)
ax.axis("off")

navy = "#0F2043"
blue = "#2563EB"
emerald = "#107C41"
amber = "#D97706"
red = "#DC2626"
slate_bg = "#F8FAFC"
card_border = "#CBD5E1"

ax.text(7, 6.6, "KukuGuard Dual-Engine Screening & Biosecurity Triage Architecture", 
        ha="center", va="center", fontsize=16, fontweight="bold", color=navy)
ax.text(7, 6.25, "Option A (Dual-Engine Max-Safeguard) with Automated Representation-Space OOD Gating", 
        ha="center", va="center", fontsize=11, fontstyle="italic", color="#475569")

def draw_box(x, y, w, h, title, subtitle, color, fill_color="#FFFFFF", border_style="-"):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.15",
                                  facecolor=fill_color, edgecolor=color, linewidth=2, linestyle=border_style)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.28, title, ha="center", va="center", fontsize=10.5, fontweight="bold", color=color)
    ax.text(x + w/2, y + (h - 0.28)/2, subtitle, ha="center", va="center", fontsize=8.5, color="#1E293B")

def draw_arrow(x1, y1, x2, y2, label="", color="#64748B"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=2, shrinkA=3, shrinkB=3))
    if label:
        ax.text((x1+x2)/2, (y1+y2)/2 + 0.15, label, ha="center", va="center", fontsize=8, fontweight="bold", color=color)

# Block 1: Input
draw_box(0.5, 3.8, 2.0, 1.8, "Input Photograph", "Standard Smartphone\nField Image\n(224x224 RGB)", navy, "#F1F5F9")

# Arrow to OOD
draw_arrow(2.5, 4.7, 3.2, 4.7)

# Block 2: OOD Gating
draw_box(3.2, 3.4, 2.5, 2.6, "Stage 1: Cosine OOD Gate", "EfficientNet-B0 (1280-d)\nEmbedding Prototype Dist.\nRejects: Boots, Hands,\nTools, Pen Soil\n(98.0% OOD Rejection)", blue, "#EFF6FF")

# OOD Rejection Branch
draw_arrow(4.45, 3.4, 4.45, 1.8, "Dist > -0.47", red)
draw_box(3.2, 0.7, 2.5, 1.1, "OOD Rejection Alert", "Halt Pipeline Immediately\n'Non-Fecal Image Detected'\nZero False Alarms on Boots", red, "#FEF2F2")

# In-distribution pass
draw_arrow(5.7, 4.7, 6.6, 4.7, "Valid Feces (95% pass)", emerald)

# Fork into Dual Engine
# Engine 1: SVM RBF Center-Only
draw_box(6.6, 3.7, 3.2, 2.2, "Primary Diagnosis Engine", "60% Central Core Crop\n205-d Multi-Color/Texture\n(CIELAB, HSV, LBP, Wavelet)\nSVM RBF (Macro-F1: 0.9195)\nLatency: 14.2 ms CPU", emerald, "#F0FDF4")

# Engine 2: Neural + CAM
draw_box(6.6, 1.1, 3.2, 2.2, "Secondary Neural Engine", "EfficientNet-B0 ONNX FP32\nCalibrated Conf (T=1.63)\nGrad-CAM Spatial Focus\nLatency: 4.65 ms CPU\n(214.9 FPS)", blue, "#F8FAFC")

# Connect fork
draw_arrow(6.15, 4.7, 6.6, 4.7)
ax.plot([6.15, 6.15], [4.7, 2.2], color="#64748B", lw=2)
draw_arrow(6.15, 2.2, 6.6, 2.2)

# Newcastle Alert Tripwire
draw_arrow(9.8, 2.2, 10.5, 2.2)
draw_box(10.5, 1.1, 3.0, 2.2, "Newcastle Tripwire", "High-Sensitivity Sentinel:\nFlags acute viral outbreak\nif CNN detects NCD\n(CNN NCD Recall: 93.94%\nvs SVM 78.79%)", amber, "#FFFBEB")

# Consensus & Final Dashboard
draw_arrow(9.8, 4.7, 10.5, 4.7)
draw_arrow(12.0, 3.3, 12.0, 4.0, "Agreement / Alert", amber)
draw_box(10.5, 4.0, 3.0, 1.9, "Streamlit Dashboard", "Consensus Diagnosis\nCalibrated Confidence (%)\nGrad-CAM Heatmap Overlay\nBiosecurity Dossier (FAO/WOAH)", navy, "#F8FAFC")

plt.tight_layout()
plt.savefig("reports/figures/fig_kukuguard_pipeline_architecture.png", dpi=300, bbox_inches="tight")
plt.close()
print("Generated fig_kukuguard_pipeline_architecture.png")


# -------------------------------------------------------------
# 2. Master Model Benchmark Comparison Chart
# -------------------------------------------------------------
models = ["Baseline CNN\n(Scratch)", "MobileNetV2\n(100)", "ResNet-50\n(Fine-Tuned)", "EfficientNet-B0\n(Champion CNN)", "SVM RBF\n(Full 410-d)", "SVM RBF (Center)\n(Champion Clean)"]
overall_f1 = [84.80, 84.97, 86.22, 87.14, 94.28, 91.95]
hard_f1 = [78.07, 78.50, 80.12, 82.04, 91.03, 86.90]

x = np.arange(len(models))
width = 0.35

fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
rects1 = ax.bar(x - width/2, overall_f1, width, label="Overall Test Macro-F1 (N=1,209)", color="#1B365D", edgecolor="#0F2043")
rects2 = ax.bar(x + width/2, hard_f1, width, label="Hard Minority Substrate Macro-F1 (n=374)", color="#107C41", edgecolor="#0A5029")

ax.set_ylabel("Macro-F1 Score (%)", fontsize=12, fontweight="bold", color="#0F172A")
ax.set_title("Master Performance Audit: Overall Test vs. Hard Bedding Substrate Slices", fontsize=14, fontweight="bold", color="#0F2043", pad=15)
ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=9.5, fontweight="bold", color="#1E293B")
ax.set_ylim(65, 100)
ax.legend(frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=10.5)
ax.grid(axis="y", linestyle="--", alpha=0.5)

for r in rects1:
    h = r.get_height()
    ax.annotate(f"{h:.1f}%", xy=(r.get_x() + r.get_width() / 2, h), xytext=(0, 3),
                textcoords="offset points", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#1B365D")

for r in rects2:
    h = r.get_height()
    ax.annotate(f"{h:.1f}%", xy=(r.get_x() + r.get_width() / 2, h), xytext=(0, 3),
                textcoords="offset points", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#107C41")

# Highlight note
ax.annotate("Center-Only SVM completely blinded to litter\nOutperforms Deep CNN by +4.81% Macro-F1",
            xy=(5 + width/2, 86.90), xytext=(3.5, 71),
            arrowprops=dict(facecolor="#DC2626", shrink=0.08, width=1.5, headwidth=6),
            fontsize=9.5, fontweight="bold", color="#DC2626",
            bbox=dict(boxstyle="round,pad=0.4", fc="#FEF2F2", ec="#DC2626", lw=1.2))

plt.tight_layout()
plt.savefig("reports/figures/fig_master_model_benchmark.png", dpi=300, bbox_inches="tight")
plt.close()
print("Generated fig_master_model_benchmark.png")


# -------------------------------------------------------------
# 3. OOD Method Comparison Chart (300 Real Distractor Benchmark)
# -------------------------------------------------------------
methods = ["Deep Cosine\nFeature Dist (1280-d)", "Classical Core\nDistance (205-d)", "Free Energy Logits\n(T=1.63, 4-d)", "Max Logit Score\n(MLS, 4-d)", "Max Softmax\nProbability (MSP)"]
rejection = [98.00, 92.67, 23.00, 23.33, 21.33]
aurocs = [0.9966, 0.9882, 0.8405, 0.8495, 0.8279]
colors = ["#107C41", "#2563EB", "#DC2626", "#D97706", "#64748B"]

fig, ax1 = plt.subplots(figsize=(11, 5.5), dpi=300)
bars = ax1.bar(methods, rejection, color=colors, width=0.55, edgecolor="#334155")
ax1.set_ylabel("OOD Distractor Rejection Rate (%)", fontsize=12, fontweight="bold", color="#0F172A")
ax1.set_ylim(0, 115)
ax1.grid(axis="y", linestyle="--", alpha=0.5)
ax1.set_title("OOD Distractor Rejection vs. ImageNet Projection Bias (300 Farm Distractors)", fontsize=13, fontweight="bold", color="#0F2043", pad=15)

ax1.axhline(90, color="#107C41", linestyle=":", lw=1.8, label="Project Target Requirement (≥ 90%)")

for bar, rej, auroc in zip(bars, rejection, aurocs):
    y = bar.get_height()
    status = "PASSED" if rej >= 90 else "FAILED"
    ax1.annotate(f"{rej:.1f}%\n(AUROC: {auroc:.4f})\n[{status}]",
                 xy=(bar.get_x() + bar.get_width() / 2, y),
                 xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                 fontsize=8.5, fontweight="bold", color="#0F172A")

ax1.legend(loc="upper right", frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1")
plt.tight_layout()
plt.savefig("reports/figures/fig_ood_rejection_summary.png", dpi=300, bbox_inches="tight")
plt.close()
print("Generated fig_ood_rejection_summary.png")


# -------------------------------------------------------------
# 4. Deduplication & Grouped Splitting Flowchart
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 5), dpi=300)
ax.set_xlim(0, 12)
ax.set_ylim(0, 5)
ax.axis("off")

ax.text(6, 4.6, "Leak-Free Grouped Splitting Protocol via Perceptual Hashing", 
        ha="center", va="center", fontsize=14, fontweight="bold", color=navy)

draw_box(0.5, 1.8, 2.2, 2.2, "Raw Image Pool", "8,067 Total Images\nFlattened from Kaggle\n(De-contaminated)\n280 Exact MD5 Dups", navy, "#F1F5F9")
draw_arrow(2.7, 2.9, 3.4, 2.9)

draw_box(3.4, 1.5, 2.6, 2.6, "Perceptual Graph", "64-bit imagehash.phash\nAdjacency threshold:\nHamming Dist <= 4\nConnected Components\n-> 7,714 Scene Groups\n(353 Duplicate Twins)", blue, "#EFF6FF")
draw_arrow(6.0, 2.9, 6.7, 2.9)

draw_box(6.7, 1.5, 2.4, 2.6, "StratifiedGroupKFold", "K=20 Grouped Split\nStratified by Class\nZero Group Overlap\nTrain: 5,649 (70.0%)\nVal:   1,209 (15.0%)\nTest:  1,209 (15.0%)", emerald, "#F0FDF4")
draw_arrow(9.1, 2.9, 9.8, 2.9)

draw_box(9.8, 1.8, 1.8, 2.2, "Holdout Test", "N = 1,209 Clean\n1,158 Isolated Groups\nZero Burst Overlap\nTrue Generalization", amber, "#FFFBEB")

plt.tight_layout()
plt.savefig("reports/figures/fig_dedup_burst_leakage.png", dpi=300, bbox_inches="tight")
plt.close()
print("Generated fig_dedup_burst_leakage.png")


# -------------------------------------------------------------
# 5. Edge Quantization Audit (FP32 vs INT8 Collapse)
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

formats = ["PyTorch FP32", "ONNX FP32\n(Optimized)", "ONNX Dynamic\nINT8"]
accs = [89.41, 89.41, 15.50]
lats = [15.6, 4.65, 7.4]
mem = [16.0, 15.28, 4.11]

# Subplot 1: Accuracy Collapse
bars_acc = ax1.bar(formats, accs, color=["#1B365D", "#107C41", "#DC2626"], width=0.5, edgecolor="#0F172A")
ax1.set_ylabel("Test Top-1 Accuracy (%)", fontsize=11, fontweight="bold", color="#0F172A")
ax1.set_ylim(0, 105)
ax1.set_title("Top-1 Accuracy: FP32 vs. INT8 Collapse", fontsize=12, fontweight="bold", color="#0F2043")
ax1.grid(axis="y", linestyle="--", alpha=0.5)

for b in bars_acc:
    h = b.get_height()
    ax1.annotate(f"{h:.1f}%", xy=(b.get_x() + b.get_width()/2, h), xytext=(0, 3),
                 textcoords="offset points", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

# Subplot 2: Latency Speedup
bars_lat = ax2.bar(formats, lats, color=["#1B365D", "#107C41", "#D97706"], width=0.5, edgecolor="#0F172A")
ax2.set_ylabel("CPU Latency per Image (ms)", fontsize=11, fontweight="bold", color="#0F172A")
ax2.set_ylim(0, 20)
ax2.set_title("CPU Latency: 2.88x FP32 ONNX Speedup", fontsize=12, fontweight="bold", color="#0F2043")
ax2.grid(axis="y", linestyle="--", alpha=0.5)

for b in bars_lat:
    h = b.get_height()
    ax2.annotate(f"{h:.2f} ms", xy=(b.get_x() + b.get_width()/2, h), xytext=(0, 3),
                 textcoords="offset points", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

fig.suptitle("Edge Quantization Audit: Depthwise Separable Degradation & ONNX Speedup", fontsize=13, fontweight="bold", color="#0F2043")
plt.tight_layout()
plt.savefig("reports/figures/fig_edge_quantization_audit.png", dpi=300, bbox_inches="tight")
plt.close()
print("Generated fig_edge_quantization_audit.png")
