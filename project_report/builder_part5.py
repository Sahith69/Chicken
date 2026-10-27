import sys

with open("/home/sahith/Projects/Chicken/project_report/build_comprehensive_100page_report.py", "a", encoding="utf-8") as out:
    out.write('''
    # =========================================================================
    # CHAPTER 4: SYSTEM IMPLEMENTATION & SOURCE CODE
    # =========================================================================
    print("Writing Chapter 4: System Implementation & Detailed Source Code...")
    add_ch_heading(4, "System Implementation & Detailed Source Code")
    
    add_h2("4.1 System Configuration and Hardware Paths (src/config.py)")
    add_p(
        "Module src/config.py establishes global system paths, hardware accelerator device mappings, dataset splits, class name taxonomies, "
        "and standard image normalization constants across the entire KukuGuard repository:"
    )
    add_code_block("src/config.py: Global Architectural and System Path Configuration", get_code("src/config.py"))

    add_h2("4.2 PyTorch Dataset Ingestion, Augmentation & Stratification (src/data.py)")
    add_p(
        "Module src/data.py encapsulates PyTorch Dataset implementations, on-the-fly stochastic data augmentations (random horizontal/vertical flips, "
        "affine color jitter, rotation), class weight calculation, and stratified DataLoader generation:"
    )
    add_code_block("src/data.py: Dataset Management and Stratified Data Ingestion", get_code("src/data.py"))

    add_fig(os.path.join(FIGURES_DIR, "batch_preview.png"), "Figure 4.1: Preprocessed Training Batch Preview Demonstrating Dynamic Geometric Augmentations")

    add_h2("4.3 Perceptual Hashing & Connected-Component Partitioning (src/dedup.py)")
    add_p(
        "Module src/dedup.py implements difference hashing (dHash), pairwise Hamming distance calculation, and graph connected-component analysis "
        "to prevent video burst frames and near-duplicate images from leaking between training, validation, and test splits:"
    )
    add_code_block("src/dedup.py: Perceptual Hashing & Leak-Free Graph Splitting Algorithm", get_code("src/dedup.py"))

    add_h2("4.4 Neural Model Architectures & Deep Feature Extraction Heads (src/model.py)")
    add_p(
        "Module src/model.py defines the Baseline 4-layer CNN as well as transfer learning wrappers for MobileNetV2, EfficientNet-B0, and ResNet-50, "
        "managing custom linear classification heads and penultimate feature extraction hooks:"
    )
    add_code_block("src/model.py: Deep Neural Architectures and Head Initializations", get_code("src/model.py"))

    add_h2("4.5 Class-Weighted Cross-Entropy, Focal, and Composite Losses (src/losses.py)")
    add_p(
        "Module src/losses.py implements mathematical loss formulations for handling extreme class imbalance, including inverse-frequency weighted "
        "Cross-Entropy, Multi-Class Focal Loss with dynamic gamma modulation, and label smoothing:"
    )
    add_code_block("src/losses.py: Class-Weighted Cross-Entropy and Focal Loss Implementations", get_code("src/losses.py"))

    add_h2("4.6 Reproducible Neural Training Engine & Early Stopping Loop (src/train.py)")
    add_p(
        "Module src/train.py provides the unified, seed-locked (SEED=42) training pipeline for training the baseline CNN from scratch with AdamW "
        "optimization, cosine learning rate decay, validation loss tracking, and automatic checkpoint serialization:"
    )
    add_code_block("src/train.py: Unified Seed-Locked Neural Training Pipeline", get_code("src/train.py"))

    add_h2("4.7 Transfer Learning, Layer Freezing & Fine-Tuning Pipeline (src/train_transfer.py)")
    add_p(
        "Module src/train_transfer.py orchestrates transfer learning across pretrained backbones, managing two-phase training (frozen feature extractor "
        "followed by layer-wise unfreezing and differential learning rate fine-tuning):"
    )
    add_code_block("src/train_transfer.py: Two-Phase Pretrained Transfer Learning Pipeline", get_code("src/train_transfer.py"))

    add_h2("4.8 Statistical Evaluation Loop & Multi-Class Metric Profiling (src/evaluate.py)")
    add_p(
        "Module src/evaluate.py executes comprehensive evaluation on test sets, generating multi-class classification reports, macro/micro F1 scores, "
        "confusion matrices, and multi-class One-vs-Rest ROC curves:"
    )
    add_code_block("src/evaluate.py: Statistical Evaluation Loop and Metric Computation", get_code("src/evaluate.py"))

    add_h2("4.9 Temperature Scaling Uncertainty Calibration Engine (src/calibrate.py)")
    add_p(
        "Module src/calibrate.py implements post-hoc temperature scaling, fitting the optimal temperature parameter T* by minimizing Negative "
        "Log-Likelihood (NLL) via L-BFGS, and plotting 10-bin reliability diagrams:"
    )
    add_code_block("src/calibrate.py: Post-Hoc Temperature Scaling and ECE Optimization Engine", get_code("src/calibrate.py"))

    add_h2("4.10 Out-of-Distribution Rejection Gating & Energy Scoring (src/ood.py)")
    add_p(
        "Module src/ood.py executes out-of-distribution anomaly gating, calculating Helmholtz Free Energy, Maximum Softmax Probability (MSP), "
        "and Penultimate Cosine Feature Distances against empirical class prototypes:"
    )
    add_code_block("src/ood.py: Out-of-Distribution Scoring and Calibration Filter", get_code("src/ood.py"))

    add_h2("4.11 Gradient-Weighted Class Activation Mapping (Grad-CAM) (src/gradcam.py)")
    add_p(
        "Module src/gradcam.py registers forward and backward hooks on the penultimate convolutional layer of EfficientNet-B0 to extract spatial "
        "attribution heatmaps and evaluate the central 70% vs outer 15% spatial energy ratio:"
    )
    add_code_block("src/gradcam.py: Gradient-Weighted Class Activation Mapping (Grad-CAM) Engine", get_code("src/gradcam.py"))

    add_h2("4.12 Classical Feature Engineering: GLCM, LBP, Color & SVM Baselines (src/baseline_ml.py)")
    add_p(
        "Module src/baseline_ml.py implements the 410-dimensional spatial-chromatic-wavelet feature extractor, extracting multi-color-space histograms, "
        "GLCM Haralick descriptors, Local Binary Patterns, and Haar wavelets, training Random Forest and RBF SVM classifiers:"
    )
    add_code_block("src/baseline_ml.py: Multi-Scale 410-d Feature Extractor & Classical Classifiers", get_code("src/baseline_ml.py"))

    add_h2("4.13 Multimodal Feature Fusion Architecture (src/multimodal_model.py)")
    add_p(
        "Module src/multimodal_model.py implements the joint neural architecture that concatenates visual CNN feature embeddings with tabular "
        "flock telemetry (ambient temperature, humidity, age in days, flock mortality rate):"
    )
    add_code_block("src/multimodal_model.py: Joint Vision and Environmental Tabular Fusion Model", get_code("src/multimodal_model.py"))

    add_h2("4.14 Tabular Sensor Data Processing & Environmental Ingestion (src/multimodal_data.py)")
    add_p(
        "Module src/multimodal_data.py standardizes tabular farm sensor records, handles missing telemetry imputation, and generates joint "
        "multimodal PyTorch tensors:"
    )
    add_code_block("src/multimodal_data.py: Tabular Environmental Sensor Data Processing", get_code("src/multimodal_data.py"))

    add_h2("4.15 Multimodal Joint Optimization Training Pipeline (src/train_multimodal.py)")
    add_p(
        "Module src/train_multimodal.py manages the end-to-end multimodal joint training loop, synchronizing visual loss backpropagation with "
        "tabular feature weight adjustments:"
    )
    add_code_block("src/train_multimodal.py: Multimodal Joint Optimization Pipeline", get_code("src/train_multimodal.py"))

    add_h2("4.16 Dual-Output ONNX Runtime Export & INT8 Dynamic Quantization (src/export.py)")
    add_p(
        "Module src/export.py exports trained PyTorch models to dual-output ONNX graphs (emitting both classification logits and 1280-d penultimate "
        "feature vectors), applies INT8 dynamic quantization, and benchmarks edge CPU latency:"
    )
    add_code_block("src/export.py: Dual-Output ONNX Export and Dynamic INT8 Quantization", get_code("src/export.py"))

    add_h2("4.17 Core Logging, System Checkpointing & Utilities (src/utils.py)")
    add_p(
        "Module src/utils.py provides global random seed locking, deterministic PyTorch / CUDA backend configurations, formatted console logging, "
        "and atomic checkpoint serialization helpers:"
    )
    add_code_block("src/utils.py: Core System Utilities and Deterministic Seeding", get_code("src/utils.py"))

    add_h2("4.18 Interactive Streamlit Web Dashboard & Live Inference Engine (app/streamlit_app.py)")
    add_p(
        "Module app/streamlit_app.py implements the production web application featuring real-time image upload, OOD intercept gating, dual-path "
        "SVM/CNN consensus verification, Grad-CAM overlays, pre-staged sample galleries, and veterinary biosecurity dossiers:"
    )
    add_code_block("app/streamlit_app.py: Interactive Streamlit Web Dashboard Application", get_code("app/streamlit_app.py"))

    add_h2("4.19 Substrate Confounding Discovery & Spatial Pointing Game (scripts/audit_classical_substrate.py)")
    add_p(
        "Module scripts/audit_classical_substrate.py audits bedding substrate correlation across classes, performs unsupervised K-Means clustering "
        "on background pixels, and measures feature attribution drift:"
    )
    add_code_block("scripts/audit_classical_substrate.py: Substrate Confounding Discovery & Auditing", get_code("scripts/audit_classical_substrate.py"))

    add_h2("4.20 Substrate Stress Testing & Domain Shift Evaluation (scripts/evaluate_substrate_stress_test.py)")
    add_p(
        "Module scripts/evaluate_substrate_stress_test.py stress-tests diagnostic models across five distinct bedding litter substrates "
        "(wood shavings, straw, sand, concrete, wire cages) to quantify domain generalization robustness:"
    )
    add_code_block("scripts/evaluate_substrate_stress_test.py: Bedding Substrate Stress-Testing Engine", get_code("scripts/evaluate_substrate_stress_test.py"))
''')
print("Part 5 written successfully.")
