"""KukuGuard: Poultry Disease Screening & Biosecurity System (Phase 8).

Streamlit Web Application featuring:
1. Out-of-Distribution (OOD) Rejection Gate (Deep Feature Cosine & Classical Core L2)
2. Primary Diagnostic Model: SVM RBF (Center-Only, 205-d shortcut-resistant)
3. Secondary Diagnostic Model & Temperature Scaling: EfficientNet-B0 (ONNX Runtime FP32)
4. Visual Explainability: Grad-CAM heatmap overlays with central attention energy metrics
5. Sample Gallery: 11 pre-loaded diagnostic & distractor samples for zero-setup demonstration
6. Robust Error Handling: Corrupt / non-image files caught gracefully
7. Clinical Knowledge Base: Disease causes, clinical signs, and farm biosecurity protocols
8. Dual Architecture Support: Option A (Dual-Engine Default) & Option B (Lightweight Edge)
"""

import json
from pathlib import Path
import sys
import time
from typing import Dict, Optional, Tuple, Any

import cv2
import joblib
import numpy as np
import onnxruntime as ort
import pandas as pd
from PIL import Image
import streamlit as st
import timm
import torch
import torch.nn as nn
from torchvision import transforms

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.baseline_ml import extract_features_single, get_feature_names
from src.gradcam import GradCAM, resolve_target_layer

# -----------------------------------------------------------------------------
# App Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="KukuGuard — Poultry Disease Screening",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded",
)

CLASSES = ["Coccidiosis", "Healthy", "Newcastle Disease", "Salmonella"]
CLASS_COLORS = {
    "Coccidiosis": "#d32f2f",
    "Healthy": "#2e7d32",
    "Newcastle Disease": "#7b1fa2",
    "Salmonella": "#f57c00",
}

# -----------------------------------------------------------------------------
# Cached Resource Loaders
# -----------------------------------------------------------------------------
@st.cache_resource
def load_classical_assets():
    svm_path = PROJECT_ROOT / "runs" / "classical" / "svm_center_only.joblib"
    scaler_path = PROJECT_ROOT / "runs" / "classical" / "scaler_center_only.joblib"
    proto_path = PROJECT_ROOT / "runs" / "ood" / "classical_train_prototypes.npy"

    svm_model = joblib.load(svm_path)
    scaler = joblib.load(scaler_path)
    prototypes = np.load(proto_path) if proto_path.exists() else None

    feature_names = get_feature_names()
    center_indices = [i for i, name in enumerate(feature_names) if name.startswith("center_")]
    return svm_model, scaler, prototypes, center_indices


@st.cache_resource
def load_deep_learning_assets():
    onnx_path = PROJECT_ROOT / "runs" / "export" / "efficientnet_b0_dual.onnx"
    pth_path = PROJECT_ROOT / "runs" / "20260920_215109_efficientnet_b0_weighted_ce" / "best_model.pth"
    temp_path = PROJECT_ROOT / "runs" / "20260920_215109_efficientnet_b0_weighted_ce" / "temperature.json"
    cnn_proto_path = PROJECT_ROOT / "runs" / "ood" / "cnn_train_prototypes.npy"
    ood_cfg_path = PROJECT_ROOT / "runs" / "ood" / "ood_config.json"

    # ONNX Runtime Session (FP32 Dual Output: logits & 1280-d features)
    ort_session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])

    # PyTorch Model for Grad-CAM
    pytorch_model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=4)
    state = torch.load(pth_path, map_location="cpu")
    pytorch_model.load_state_dict(state)
    pytorch_model.eval()

    target_layer = resolve_target_layer(pytorch_model, "efficientnet_b0")
    gradcam_engine = GradCAM(pytorch_model, target_layer)

    temperature = 1.6302
    if temp_path.exists():
        with open(temp_path) as f:
            t_data = json.load(f)
            temperature = float(t_data.get("temperature", 1.6302))

    cnn_prototypes = np.load(cnn_proto_path) if cnn_proto_path.exists() else None

    ood_config = {}
    if ood_cfg_path.exists():
        with open(ood_cfg_path) as f:
            ood_config = json.load(f)

    return ort_session, pytorch_model, gradcam_engine, temperature, cnn_prototypes, ood_config


@st.cache_data
def load_sample_gallery():
    manifest_path = PROJECT_ROOT / "app" / "samples" / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return []


# -----------------------------------------------------------------------------
# Diagnostic & OOD Inference Pipelines
# -----------------------------------------------------------------------------
def preprocess_image_for_cnn(pil_img: Image.Image) -> Tuple[np.ndarray, torch.Tensor]:
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    rgb_img = pil_img.convert("RGB")
    tensor = transform(rgb_img).unsqueeze(0)
    return tensor.numpy(), tensor


def evaluate_deep_ood_gate(
    features_1280: np.ndarray,
    prototypes: np.ndarray,
    threshold: float = -0.4585,
) -> Tuple[bool, float]:
    """KNN Cosine Distance to training fecal prototypes. Returns (is_ood, distance_score)."""
    norm_feat = features_1280 / np.linalg.norm(features_1280, axis=1, keepdims=True)
    # Cosine similarities: dot product
    sims = np.dot(prototypes, norm_feat.T).squeeze()  # [N_proto]
    cosine_dists = 1.0 - sims
    # Top-5 nearest neighbors
    top5_dists = np.partition(cosine_dists, 5)[:5]
    mean_dist = float(np.mean(top5_dists))
    score = -mean_dist  # Higher = closer to in-distribution, Lower = OOD
    is_ood = score < threshold
    return is_ood, score


def evaluate_classical_ood_gate(
    scaled_205d: np.ndarray,
    prototypes: np.ndarray,
    threshold: float = -10.9736,
) -> Tuple[bool, float]:
    """KNN L2 Distance to training core fecal prototypes. Returns (is_ood, distance_score)."""
    diffs = prototypes - scaled_205d
    l2_dists = np.linalg.norm(diffs, axis=1)
    top5_dists = np.partition(l2_dists, 5)[:5]
    mean_dist = float(np.mean(top5_dists))
    score = -mean_dist
    is_ood = score < threshold
    return is_ood, score


# -----------------------------------------------------------------------------
# UI Header & Global Disclaimers
# -----------------------------------------------------------------------------
st.title("🐔 KukuGuard: Avian Disease Screening & Biosecurity Aid")
st.markdown(
    "**An evidence-grounded machine learning screening system for smallholder poultry farming.** "
    "Features leak-safe spatial feature extraction, out-of-distribution (OOD) safeguard gating, and Grad-CAM visual transparency."
)

st.warning(
    "⚠️ **Veterinary Screening Aid Only**: This application is an automated screening and triage tool for field poultry health workers and farmers. "
    "It is **NOT** a definitive veterinary diagnosis. Critical treatment, antimicrobial use, or culling decisions must be validated by a licensed veterinarian or laboratory testing (e.g. PCR/bacterial culture)."
)

with st.expander("ℹ️ **Important Substrate Guidance (Phase 5 Audit Finding)**", expanded=False):
    st.markdown(
        """
        **Known Limitation:** In our rigorous Phase 5 substrate stress-test, genuinely **Healthy** droppings photographed on bare dark soil or mixed straw bedding 
        exhibited an elevated false-alarm rate (Healthy recall collapsed from **86.2%** on wood shavings down to **68.5%** on minority soils). 
        
        *Farmer Recommendation:* For highest diagnostic reliability, always photograph droppings situated on **clean wood shavings** or against a neutral light backing. 
        Exercise caution before treating healthy-looking birds whose stools were photographed on wet dirt.
        """
    )

# -----------------------------------------------------------------------------
# Sidebar: Pipeline Architecture & Sample Selection
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Deployment Architecture")

architecture_mode = st.sidebar.radio(
    "Select Operating Pipeline:",
    options=[
        "Option A: Dual-Engine Max-Safeguard (Default)",
        "Option B: Lightweight-First Edge Mode",
    ],
    index=0,
    help="Option A uses the 98% Deep Feature OOD Gate, Primary SVM diagnosis, and instant Grad-CAM (~21.6 ms). Option B uses Classical Core Distance OOD and pure SVM (~14.4 ms).",
)

st.sidebar.markdown("---")
st.sidebar.header("📸 Image Input Source")

input_mode = st.sidebar.radio(
    "Choose Input Method:",
    options=["Pick from Sample Gallery", "Upload Custom Photo"],
    index=0,
)

gallery_samples = load_sample_gallery()

selected_sample = None
uploaded_file = None

if input_mode == "Pick from Sample Gallery":
    sample_options = [f"{s['category']}: {s['name']}" for s in gallery_samples]
    selected_idx = st.sidebar.selectbox("Choose a pre-loaded sample:", range(len(sample_options)), format_func=lambda i: sample_options[i])
    selected_sample = gallery_samples[selected_idx]
    st.sidebar.info(f"**Description:** {selected_sample['description']}")
else:
    uploaded_file = st.sidebar.file_uploader(
        "Upload a fecal photograph (JPG/PNG):",
        type=["jpg", "jpeg", "png"],
        help="Ensure image is clear, well-lit, and centered on the fecal droplet.",
    )

# -----------------------------------------------------------------------------
# Image Loading & Validation
# -----------------------------------------------------------------------------
pil_image = None
image_source_label = ""

if input_mode == "Pick from Sample Gallery" and selected_sample:
    sample_path = PROJECT_ROOT / "app" / "samples" / selected_sample["filename"]
    try:
        pil_image = Image.open(sample_path)
        image_source_label = f"Gallery Sample: {selected_sample['name']}"
    except Exception as e:
        st.error(f"Error loading gallery sample '{sample_path}': {e}")
        st.stop()

elif input_mode == "Upload Custom Photo" and uploaded_file is not None:
    try:
        pil_image = Image.open(uploaded_file)
        # Verify image integrity
        pil_image.verify()
        # Re-open after verify() closes it
        uploaded_file.seek(0)
        pil_image = Image.open(uploaded_file).convert("RGB")
        image_source_label = f"Uploaded File: {uploaded_file.name}"
    except Exception:
        st.error("🚨 **Error:** Uploaded file is corrupt, truncated, or not a valid image. Please provide a standard JPEG or PNG photo.")
        st.stop()

if pil_image is None:
    st.info("👈 Please select a sample from the sidebar gallery or upload an image to begin screening.")
    st.stop()

# -----------------------------------------------------------------------------
# Asset Loading
# -----------------------------------------------------------------------------
try:
    svm_model, scaler, class_prototypes, center_indices = load_classical_assets()
    ort_session, pytorch_model, gradcam_engine, calibrated_T, cnn_prototypes, ood_config = load_deep_learning_assets()
except Exception as e:
    st.error(f"Failed to load required model artifacts: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# Main Screening Workflow
# -----------------------------------------------------------------------------
col_img, col_diag = st.columns([1.1, 1.4], gap="large")

with col_img:
    st.subheader("📷 Input Photograph")
    st.image(pil_image, caption=image_source_label, use_container_width=True)

    w, h = pil_image.size
    st.caption(f"Dimensions: {w} × {h} pixels | Format: {pil_image.format or 'RGB'}")

# Preprocess image
cnn_input_np, cnn_input_tensor = preprocess_image_for_cnn(pil_image)

# Save temporary image for classical feature extraction
temp_img_path = PROJECT_ROOT / "app" / "temp_input.jpg"
pil_image.convert("RGB").save(temp_img_path, "JPEG", quality=95)

t_start = time.perf_counter()

# Step 1: Execute OOD Gate
is_ood = False
ood_score = 0.0
ood_threshold = 0.0
detector_name = ""

if "Option A" in architecture_mode:
    detector_name = "Deep Feature Cosine Distance (KNN-OOD)"
    ood_threshold = -0.4585
    # Run ONNX dual model for features
    outputs = ort_session.run(["logits", "features"], {"input": cnn_input_np})
    cnn_logits = outputs[0][0]
    cnn_features = outputs[1]
    is_ood, ood_score = evaluate_deep_ood_gate(cnn_features, cnn_prototypes, threshold=ood_threshold)
else:
    detector_name = "Classical Core Distance (KNN-OOD)"
    ood_threshold = -10.9736
    # Extract 205-d center features
    feat_410 = extract_features_single(str(temp_img_path))
    feat_205 = np.nan_to_num(feat_410[center_indices], nan=0.0).reshape(1, -1)
    feat_205_scaled = scaler.transform(feat_205)
    is_ood, ood_score = evaluate_classical_ood_gate(feat_205_scaled, class_prototypes, threshold=ood_threshold)
    # Also get CNN logits for consensus if requested
    cnn_logits = ort_session.run(["logits"], {"input": cnn_input_np})[0][0]

t_ood = time.perf_counter()

with col_diag:
    st.subheader("🛡️ Step 1: Out-of-Distribution (OOD) Gate")

    metric_delta = ood_score - ood_threshold
    status_icon = "❌" if is_ood else "✅"

    st.markdown(
        f"**Detector Method:** `{detector_name}`  \n"
        f"**Distance Score:** `{ood_score:.4f}` (Gate Threshold: `{ood_threshold:.4f}`)  \n"
        f"**Status:** {status_icon} **{'REJECTED (Non-Fecal Distractor)' if is_ood else 'PASSED (Valid Avian Stool)'}**"
    )

    if is_ood:
        st.error(
            "### 🚨 INVALID SAMPLE: NOT RECOGNIZED AS POULTRY FECES\n\n"
            "The OOD safeguard gate determined that this image does not sit on the manifold of avian fecal matter "
            "(e.g., rubber work boot, human hand, equipment container, or clean unsoiled pen floor).\n\n"
            "**Action:** Disease diagnosis has been automatically suspended to prevent a false alarm. "
            "Please ensure the camera is aimed directly at an actual chicken dropping."
        )
        st.stop()
    else:
        st.success("Avian fecal signature verified. Proceeding to differential pathology analysis...")

    st.markdown("---")
    st.subheader("🔬 Step 2: Differential Diagnosis")

    # Classical SVM Primary Model Execution
    if "Option A" in architecture_mode:
        feat_410 = extract_features_single(str(temp_img_path))
        feat_205 = np.nan_to_num(feat_410[center_indices], nan=0.0).reshape(1, -1)
        feat_205_scaled = scaler.transform(feat_205)

    svm_pred_idx = int(svm_model.predict(feat_205_scaled)[0])
    svm_decision = svm_model.decision_function(feat_205_scaled)[0]
    # Softmax over decision function for pseudo-probabilities
    svm_exp = np.exp(svm_decision - np.max(svm_decision))
    svm_probs = svm_exp / np.sum(svm_exp)

    # Secondary Model (EfficientNet-B0) with Temperature Scaling
    scaled_logits = cnn_logits / calibrated_T
    cnn_exp = np.exp(scaled_logits - np.max(scaled_logits))
    cnn_probs = cnn_exp / np.sum(cnn_exp)
    cnn_pred_idx = int(np.argmax(cnn_probs))

    t_end = time.perf_counter()
    total_latency_ms = (t_end - t_start) * 1000.0

    primary_class = CLASSES[svm_pred_idx]
    primary_conf = svm_probs[svm_pred_idx]

    # Primary Diagnosis Card
    st.markdown(
        f"""
        <div style="background-color: #f0f4f8; border-left: 6px solid {CLASS_COLORS[primary_class]}; padding: 16px; border-radius: 6px; margin-bottom: 12px;">
            <h3 style="margin: 0; color: #1a202c;">Primary Diagnosis: {primary_class}</h3>
            <p style="margin: 4px 0 0 0; color: #4a5568; font-size: 14px;">
                Engine: <b>SVM RBF (Center-Only 60% Core)</b> | Confidence: <b>{primary_conf*100:.1f}%</b> | Latency: <b>{total_latency_ms:.1f} ms</b>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Uncertainty Check
    if primary_conf < 0.45:
        st.warning("⚠️ **Low Confidence Result (< 45%):** Ambiguous presentation. Recommend resampling under better lighting or veterinary lab testing.")

    # Model Consensus Indicator
    secondary_class = CLASSES[cnn_pred_idx]
    secondary_conf = cnn_probs[cnn_pred_idx]

    if primary_class == secondary_class:
        st.info(f"🤝 **High Dual-Engine Consensus:** Both Primary SVM and Secondary EfficientNet-B0 agree on **{primary_class}** ({secondary_conf*100:.1f}% CNN confidence).")
    else:
        st.warning(
            f"⚡ **Architectural Disagreement:**  \n"
            f"• **Primary Model (SVM Center-Only):** `{primary_class}` ({primary_conf*100:.1f}%)  \n"
            f"• **Secondary Model (EfficientNet-B0):** `{secondary_class}` ({secondary_conf*100:.1f}%)"
        )

        # Newcastle High-Sensitivity Flag
        if secondary_class == "Newcastle Disease" and primary_class != "Newcastle Disease":
            st.error(
                "🚨 **VETERINARY ADVISORY (Newcastle Alert):** EfficientNet-B0 flagged potential Newcastle Disease indicators "
                "(CNN retains 93.9% recall on atypical substrates, where SVM dropped to 78.8%). "
                "Because Newcastle is an acute, flock-decimating viral infection, immediate quarantine and rapid confirmatory testing are strongly recommended."
            )

    # Probability Distribution Bar Chart
    prob_df = pd.DataFrame({
        "Condition": CLASSES,
        "SVM Probability (%)": [p * 100 for p in svm_probs],
        "CNN Scaled Probability (%)": [p * 100 for p in cnn_probs],
    }).set_index("Condition")

    st.bar_chart(prob_df)

# -----------------------------------------------------------------------------
# Step 3: Visual Explainability (Grad-CAM Heatmap)
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔍 Step 3: Visual Explainability (Grad-CAM)")

render_gradcam = True
if "Option B" in architecture_mode:
    render_gradcam = st.checkbox("Generate Grad-CAM Visual Heatmap (Invokes EfficientNet-B0)", value=False)

if render_gradcam:
    with st.spinner("Generating Grad-CAM activation heatmap..."):
        heatmap = gradcam_engine.generate_heatmap(cnn_input_tensor, target_class=cnn_pred_idx)
        rgb_resized = cv2.resize(cv2.imread(str(temp_img_path))[:, :, ::-1], (224, 224))
        overlay = gradcam_engine.overlay_on_image(rgb_resized, heatmap, alpha=0.55)

        # Compute Central vs Peripheral Energy
        h, w = heatmap.shape
        margin_y, margin_x = int(h * 0.15), int(w * 0.15)
        center_region = heatmap[margin_y : h - margin_y, margin_x : w - margin_x]
        total_energy = np.sum(heatmap) + 1e-8
        center_energy_pct = (np.sum(center_region) / total_energy) * 100.0

        col_cam1, col_cam2, col_cam3 = st.columns([1, 1, 1.2])
        with col_cam1:
            st.image(rgb_resized, caption="Cropped Diagnostic Region (224×224)", use_container_width=True)
        with col_cam2:
            st.image(overlay, caption=f"Grad-CAM Overlay ({CLASSES[cnn_pred_idx]})", use_container_width=True)
        with col_cam3:
            st.markdown(
                f"""
                **Heatmap Spatial Energy Audit:**
                - **Central Dropping Energy:** `{center_energy_pct:.1f}%`
                - **Peripheral Bedding Energy:** `{100.0 - center_energy_pct:.1f}%`
                """
            )
            if center_energy_pct >= 65.0:
                st.success("✅ **Focal Pathology Grounding:** Network attention is concentrated on the fecal mass rather than the background litter.")
            else:
                st.warning("⚠️ **Substrate Dispersion Warning:** Attention has partially dispersed into peripheral bedding textures, consistent with the known substrate confounder.")

# -----------------------------------------------------------------------------
# Step 4: Clinical & Management Knowledge Base
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📚 Step 4: Disease Profile & Biosecurity Protocol")
st.caption(
    "ℹ️ **Clinical Reference Notice:** The etiological agents, clinical signs, pharmacological treatments, and biosecurity protocols below "
    "are compiled from standard avian veterinary references (FAO Animal Health Manual No. 4, WOAH Terrestrial Manual, and the Merck Veterinary Manual). "
    "They represent established veterinary clinical standards and are provided strictly as educational reference material, "
    "NOT as empirical findings or treatment regimens derived from the machine learning model."
)

disease_dossiers = {
    "Coccidiosis": {
        "pathogen": "Protozoan parasite (*Eimeria tenella*, *E. acervulina*, *E. maxima*)",
        "transmission": "Ingestion of sporulated oocysts in contaminated litter, damp bedding, feed, or drinking water.",
        "signs": "Frank crimson blood or mucus in feces, ruffled feathers, huddling, pale combs, depressed growth rate.",
        "treatment": "Administer anticoccidials (Amprolium or Toltrazuril) immediately via flock drinking water for 3–5 days.",
        "biosecurity": "Keep litter dry (<25% moisture); eliminate drinker leaks; turn bedding frequently; clean and disinfect between flock cycles.",
    },
    "Salmonella": {
        "pathogen": "Bacterium (*Salmonella pullorum*, *Salmonella gallinarum* — Fowl Typhoid / Pullorum Disease)",
        "transmission": "Vertical (hen to chick via transovarial egg transmission) and horizontal (fecal-oral contact, contaminated rodents/feed).",
        "signs": "Pasty sulfur-yellow or chalky-white vent staining, severe chick mortality, somnolence, dehydration, anorexia.",
        "treatment": "Perform veterinary antimicrobial sensitivity testing before treatment. Supportive electrolyte supplementation.",
        "biosecurity": "Enforce strict rodent control; test breeding stock; cull persistent chronic carriers; thoroughly disinfect incubators.",
    },
    "Newcastle Disease": {
        "pathogen": "Avian Paramyxovirus Serotype 1 (APMV-1 / Velogenic or Mesogenic strains)",
        "transmission": "Highly contagious airborne aerosols, direct bird-to-bird secretions, contaminated footwear, and wild bird contact.",
        "signs": "Emerald-green watery diarrhea, acute respiratory distress, facial edema, neurological torticollis (twisted neck), catastrophic mortality.",
        "treatment": "**NOTIFIABLE DISEASE**: No curative antiviral exists. Immediately isolate suspected pens and report to district veterinary officers.",
        "biosecurity": "Enforce emergency farm quarantine; vaccinate unaffected neighboring flocks; strictly restrict farm visitors; incinerate mortality.",
    },
    "Healthy": {
        "pathogen": "None (Normal Avian Digestion)",
        "transmission": "N/A",
        "signs": "Firm brownish/green stool with a white uric acid cap, or homogeneous brownish-yellow cecal dropping.",
        "treatment": "No treatment required. Maintain balanced commercial ration and clean ad-libitum water.",
        "biosecurity": "Maintain clean dry wood shavings (5–10 cm depth); ensure adequate pen ventilation; follow routine biosecurity.",
    },
}

dossier = disease_dossiers[primary_class]

with st.container():
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Etiological Agent / Cause:**  \n{dossier['pathogen']}")
        st.markdown(f"**Transmission Mode:**  \n{dossier['transmission']}")
        st.markdown(f"**Key Clinical Signs:**  \n{dossier['signs']}")
    with c2:
        st.markdown(f"**Immediate Action / Medical Management:**  \n{dossier['treatment']}")
        st.markdown(f"**Long-term Farm Biosecurity Protocol:**  \n{dossier['biosecurity']}")

st.markdown("---")
st.caption(
    "KukuGuard v1.0 | Built with PyTorch, ONNX Runtime, scikit-learn, and Streamlit. "
    "Primary: SVM RBF (Center-Only) | Secondary: EfficientNet-B0 (ONNX FP32). "
    "Dataset: Machuve et al. (2022) Frontiers in AI. Tanzanian smallholder poultry benchmark."
)
