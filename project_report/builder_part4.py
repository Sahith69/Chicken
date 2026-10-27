import sys

with open("/home/sahith/Projects/Chicken/project_report/build_comprehensive_100page_report.py", "a", encoding="utf-8") as out:
    out.write('''
    # =========================================================================
    # CHAPTER 3: SYSTEM DESIGN & METHODOLOGY
    # =========================================================================
    print("Writing Chapter 3: System Design & Methodology...")
    add_ch_heading(3, "System Design & Methodology")
    
    add_h2("3.1 Overall System Architecture and Modular Engineering Blueprint")
    add_p(
        "KukuGuard is engineered as a robust, decoupled, multi-stage diagnostic pipeline designed for verifiable edge deployment. "
        "The architecture rejects monolithic black-box deep learning in favor of an ensemble paradigm that pairs a 410-dimensional shortcut-resistant "
        "classical feature extractor with modern lightweight deep convolutional backbones, gated by out-of-distribution anomaly scoring and "
        "calibrated via temperature scaling."
    )

    arch_str = """
+---------------------------------------------------------------------------------------------------+
|                        KUKUGUARD END-TO-END PIPELINE ARCHITECTURAL BLUEPRINT                      |
+---------------------------------------------------------------------------------------------------+

                    +------------------------------------+
                    |   Raw Optical Image X in R^{HxWx3} |
                    +------------------------------------+
                                      |
                                      v
                    +------------------------------------+
                    |  Stage 1: Out-of-Distribution Gate |
                    |  - Penultimate Cosine Distance     |
                    |  - Free Energy Score Threshold     |
                    +------------------------------------+
                                 |            |
                      [Pass OOD] |            | [Fail OOD]
                                 v            +------------------------+
              +------------------------------------+                   |
              | Stage 2: Dual Feature Extraction   |                   v
              +------------------------------------+         +-------------------+
                     |                      |                | Reject: Non-Fecal |
                     v                      v                | Debris / Anomaly  |
         +-----------------------+ +-----------------------+ +-------------------+
         | Path A: Classical     | | Path B: Deep CNN      |
         | 410-d Vector Extractor| | Feature Backbone      |
         | - Color Histograms    | | - EfficientNet-B0     |
         | - GLCM Haralick       | | - MobileNetV2         |
         | - Local Binary Patterns| | - ResNet-50           |
         | - Haar Wavelet Energy | +-----------------------+
         +-----------------------+            |
                     |                        v
                     v            +-----------------------+
         +-----------------------+| Raw Logits vector l   |
         | Multi-Class RBF SVM   |+-----------------------+
         | Linear Decision Hyper |            |
         +-----------------------+            v
                     |            +-----------------------+
                     v            | Stage 3: Calibration  |
         +-----------------------+| Temperature Scaling T*|
         | Prediction y_svm      |+-----------------------+
         +-----------------------+            |
                     |                        v
                     |            +-----------------------+
                     |            | Calibrated Prob. p_cal|
                     |            +-----------------------+
                     |                        |
                     +------------+-----------+
                                  |
                                  v
                    +------------------------------------+
                    | Stage 4: Consensus & Attribution   |
                    | - Check Prediction Agreement       |
                    | - Compute Grad-CAM Saliency Maps   |
                    | - Verify Central Spatial Energy    |
                    +------------------------------------+
                                  |
                                  v
                    +------------------------------------+
                    | Stage 5: Decision Support & Dossier|
                    | - Calibrated Class Probabilities   |
                    | - Verified Clinical Category       |
                    | - Biosecurity Containment SOP      |
                    +------------------------------------+
"""
    add_code_block("Figure 3.1: Complete End-to-End System Process Pipeline Architecture from Ingestion to XAI", arch_str)

    add_h2("3.2 Classical Multi-Scale Feature Engineering Formulation (Color, GLCM, LBP, Haar)")
    add_p(
        "To provide a rock-solid diagnostic baseline that does not succumb to neural shortcut learning or background bedding memorization, "
        "we construct a comprehensive 410-dimensional hand-crafted feature extraction pipeline. Features are extracted across three complementary "
        "color spaces (RGB, HSV, and CIE L*a*b*), spatial co-occurrence matrices, rotational texture encodings, and multi-resolution wavelet decompositions:"
    )
    add_p(
        "1. Multi-Color-Space Histograms (192 dimensions): Fecal pathology is strongly characterized by color shifts: bloody mucoid red in Coccidiosis, "
        "chalky white in Salmonella, bright biliverdin green in Newcastle Disease, and balanced earthy brown in healthy birds. We compute 16-bin "
        "histograms across each channel of RGB, HSV, and CIE L*a*b* spaces (3 channels x 16 bins x 3 spaces = 144 features), augmented with channel-wise "
        "first four statistical moments: Mean, Standard Deviation, Skewness, and Kurtosis (3 channels x 4 moments x 4 representations = 48 features)."
    )
    add_p(
        "2. Gray-Level Co-occurrence Matrix (GLCM) Second-Order Texture (96 dimensions): Dropping consistency ranges from fibrous, firm clumps to watery, "
        "amorphous diarrhea. We convert images to 8-bit grayscale and evaluate GLCM matrices across 4 spatial distances (d in {1, 2, 4, 8} pixels) and "
        "4 angular directions (theta in {0, 45, 90, 135} degrees). From each matrix, we extract 6 Haralick texture descriptors: Contrast, Dissimilarity, "
        "Homogeneity, Energy, Correlation, and Angular Second Moment (ASM), yielding 4 x 4 x 6 = 96 texture features."
    )
    add_p(
        "3. Local Binary Patterns (LBP) Micro-Texture (54 dimensions): To capture rotation-invariant surface roughness independent of overall lighting, "
        "we evaluate uniform Local Binary Patterns using a circular neighborhood with radius R=1 (P=8 points), radius R=2 (P=16 points), and radius R=3 (P=24 points), "
        "accumulating 18-bin normalized histograms across the three radii (3 x 18 = 54 features)."
    )
    add_p(
        "4. Haar Discrete Wavelet Transform (DWT) Decomposition (68 dimensions): To separate macro-morphological structure from high-frequency mucosal mucus, "
        "we apply 3-level 2D Haar discrete wavelet decomposition. At each decomposition scale, we compute the energy, entropy, variance, and mean absolute "
        "value across the approximation (LL), horizontal detail (LH), vertical detail (HL), and diagonal detail (HH) sub-bands, yielding 68 wavelet features."
    )

    feat_table = [
        ["Color Histograms & Moments", "RGB, HSV, CIE L*a*b* channels; 16 bins per channel + 4 statistical moments (Mean, Std, Skew, Kurtosis)", "192"],
        ["GLCM Haralick Textures", "4 spatial distances (d=1,2,4,8), 4 orientations (0, 45, 90, 135 deg); Contrast, Homogeneity, Energy, Correlation", "96"],
        ["Local Binary Patterns (LBP)", "Rotation-invariant uniform patterns across 3 multi-scale radii (R=1, P=8; R=2, P=16; R=3, P=24)", "54"],
        ["Haar Wavelet Sub-bands", "3-level 2D Haar DWT; Energy, entropy, variance, and L1 norm across LL, LH, HL, HH sub-bands", "68"],
        ["Total Feature Dimensionality", "Complete Multi-Scale Spatial-Chromatic-Wavelet Feature Vector Representation", "410"]
    ]
    make_styled_table(doc, ["Feature Extraction Subsystem", "Mathematical Extraction Parameters & Sub-band Decompositions", "Dimensions"], feat_table, [1.8, 3.8, 0.8], bold_cols=[0, 2], font_size=8.8, cell_pad=(25, 25))

    add_h2("3.3 Deep Convolutional Neural Transfer Learning Architectures & Model Backbones")
    add_p(
        "In parallel with classical feature engineering, we investigate modern deep convolutional neural backbones initialized with ImageNet-1k "
        "pretrained weights. We deliberately select architectures optimized for parameter efficiency, mobile edge inference, and high representational capacity:"
    )
    add_p(
        "1. MobileNetV2 (Sandler et al., 2018): Utilizes inverted residual blocks with linear bottlenecks and depthwise separable convolutions. With only "
        "2.23 million parameters and 0.31 GFLOPs, it provides an ultra-lightweight edge benchmark suited for microcontrollers and older mobile chips."
    )
    add_p(
        "2. EfficientNet-B0 (Tan & Le, 2019): Employs neural architecture search (NAS) to uniformly scale network depth, width, and resolution using a fixed "
        "compound coefficient. Built from mobile inverted bottleneck convolutions (MBConv) enriched with Squeeze-and-Excitation (SE) channel-attention "
        "modules, EfficientNet-B0 achieves superior feature representation with only 4.01 million parameters and 0.39 GFLOPs."
    )
    add_p(
        "3. ResNet-50 (He et al., 2016): Serves as the heavy industry standard baseline, incorporating 50 deep convolutional layers structured into "
        "bottleneck residual blocks with identity shortcut connections. While featuring 23.51 million parameters and 4.12 GFLOPs, it provides high "
        "capacity to benchmark whether larger models offer genuine diagnostic benefits over compact edge networks."
    )

    hp_table = [
        ["Input Dimensions", "224 x 224 x 3 pixels (RGB normalized with ImageNet mean/std)", "224 x 224 x 3 pixels", "224 x 224 x 3 pixels"],
        ["Trainable Parameters", "2,228,868 (2.23M)", "4,012,504 (4.01M)", "23,516,228 (23.52M)"],
        ["Computational GFLOPs", "0.31 GFLOPs", "0.39 GFLOPs", "4.12 GFLOPs"],
        ["Base Learning Rate", "1e-4 (AdamW optimizer)", "1e-4 (AdamW optimizer)", "5e-5 (AdamW optimizer)"],
        ["Weight Decay", "1e-4", "1e-4", "1e-4"],
        ["Batch Size", "32 samples per mini-batch", "32 samples per mini-batch", "32 samples per mini-batch"],
        ["LR Schedule", "Cosine Annealing with T_max=30", "Cosine Annealing with T_max=30", "Cosine Annealing with T_max=30"],
        ["Early Stopping", "Patience = 7 epochs on Val F1", "Patience = 7 epochs on Val F1", "Patience = 7 epochs on Val F1"]
    ]
    make_styled_table(doc, ["Architectural Hyperparameter", "MobileNetV2 (1.0x)", "EfficientNet-B0", "ResNet-50 Baseline"], hp_table, [1.8, 1.5, 1.5, 1.5], font_size=8.5, cell_pad=(25, 25))

    add_h2("3.4 Loss Formulations for Extreme Class Imbalance (Weighted CE & Focal Loss)")
    add_p(
        "Because acute Newcastle Disease droppings represent only 5.8% of photographic observations (374 out of 6,432 images), unweighted loss "
        "optimization causes neural networks to default towards majority classes (Coccidiosis and Healthy droppings). We formulate and compare two "
        "rigorous loss functions specifically adapted to severe epidemiological class imbalance:"
    )
    add_p(
        "1. Class-Weighted Cross-Entropy Loss: We assign inverse class-frequency weights w_c = N / (C * N_c), where N is total samples, C=4 is class count, "
        "and N_c is class sample count. This scales the loss penalty by 4.299x for Newcastle Disease while penalizing Coccidiosis at 0.765x:\\n"
        "L_WCE(y, p) = - sum_{c=1}^C w_c * y_c * log(p_c)"
    )
    add_p(
        "2. Multi-Class Focal Loss (Lin et al., 2017): Focal loss dynamically suppresses the relative loss contribution of easy-to-classify samples "
        "while focusing gradient updates on hard, ambiguous borderline cases by introducing a modulating factor (1 - p_c)^gamma with focusing parameter gamma=2.0:\\n"
        "L_Focal(y, p) = - sum_{c=1}^C w_c * (1 - p_c)^gamma * y_c * log(p_c)"
    )

    add_h2("3.5 Post-Hoc Uncertainty Calibration via Temperature Scaling Formulation")
    add_p(
        "Modern deep neural networks trained with cross-entropy loss are notoriously overconfident: an uncalibrated network frequently outputs a Softmax "
        "probability of 0.98 on a sample where empirical accuracy is only 0.55. In veterinary diagnostics, this false confidence can lead a farm manager to "
        "overlook early signs of an acute Newcastle Disease outbreak."
    )
    add_p(
        "To guarantee that predicted confidence p matches the true empirical probability of correctness, we implement post-hoc Temperature Scaling "
        "(Guo et al., 2017). For a raw logit vector l in R^C, calibrated probabilities are generated by scaling logits by a single scalar parameter T > 0:\\n"
        "p_i(T) = exp(l_i / T) / ( sum_{j=1}^C exp(l_j / T) )\\n\\n"
        "Because T scales all logits equally, the argmax prediction remains invariant, preserving exact classification accuracy while calibrating confidence. "
        "The optimal parameter T* is learned by minimizing Negative Log-Likelihood (NLL) on the held-out validation set using L-BFGS-B optimization:\\n"
        "T* = argmin_T [ - sum_{k=1}^{N_{val}} log( p_{y_k}(T) ) ]"
    )
    add_p(
        "Calibration quality is quantitatively evaluated using Expected Calibration Error (ECE) under M=10 equal-width confidence bins B_m:\\n"
        "ECE = sum_{m=1}^M ( |B_m| / N ) * | acc(B_m) - conf(B_m) |"
    )

    add_h2("3.6 Out-of-Distribution Gating & Anomaly Scoring (MSP, Energy Score, Mahalanobis)")
    add_p(
        "In commercial poultry operations, an automated camera system inevitably captures non-fecal artifacts: rubber boots, feathers, feed pellets, "
        "water droplets, wire mesh, and soil. To prevent catastrophic false alarms, KukuGuard deploys a dual-mechanism Out-of-Distribution (OOD) filter:"
    )
    add_p(
        "1. Free Energy Score (Liu et al., 2020): Rather than relying on Maximum Softmax Probability (MSP)—which suffers from abnormal overconfidence on noise—we "
        "compute the Helmholtz free energy of the logit vector l:\\n"
        "E(X; T) = - T * log( sum_{c=1}^C exp( l_c / T ) )\\n"
        "In-distribution fecal samples exhibit low, highly negative free energy values, whereas out-of-distribution debris generates significantly higher "
        "(less negative) energy scores."
    )
    add_p(
        "2. Deep Feature Cosine Distance: To detect semantic anomalies that happen to produce high logit norms, we extract the 1280-dimensional penultimate "
        "embedding z = phi(X) from EfficientNet-B0 and compute the minimum cosine distance to empirical class centroids mu_c established during training:\\n"
        "d_cos(z) = min_{c in {1..C}} [ 1 - ( z . mu_c ) / ( ||z||_2 * ||mu_c||_2 ) ]\\n"
        "If either E(X) > tau_energy or d_cos(z) > tau_cos, the sample is immediately intercepted and flagged as Out-of-Distribution before clinical classification."
    )

    add_h2("3.7 Visual Explainability & Spatial Attribution Auditing (Grad-CAM & Pointing Game)")
    add_p(
        "To ensure that deep models base their diagnostic predictions on genuine biological pathology rather than surrounding bedding litter, we "
        "integrate Gradient-Weighted Class Activation Mapping (Grad-CAM; Selvaraju et al., 2017). We attach forward and backward gradient hooks to the "
        "penultimate convolutional feature maps A in R^{C_f x H_f x W_f} of EfficientNet-B0 (the conv_head layer, emitting 1280 channels at 7x7 spatial resolution)."
    )
    add_p(
        "The importance weight alpha_k^c of feature map k for clinical class c is calculated via global average pooling of gradients:\\n"
        "alpha_k^c = (1 / Z) * sum_i sum_j ( d y^c / d A_{ij}^k )\\n"
        "The class-discriminative localization map L_GradCAM^c is generated by linear combination followed by a Rectified Linear Unit (ReLU):\\n"
        "L_GradCAM^c = ReLU( sum_k alpha_k^c * A^k )"
    )
    add_p(
        "Spatial Pointing Game & Bedding Confounder Ratio: We quantify background confounding by computing the ratio of activation energy concentrated "
        "in the central 70% spatial bounding box (where fecal matter resides) versus the outer 15% perimeter (dominated by bedding litter):\\n"
        "Ratio_spatial = sum_{(i,j) in Center} L_GradCAM(i,j) / ( sum_{(i,j) in Perimeter} L_GradCAM(i,j) + epsilon )\\n"
        "Models with Ratio_spatial > 3.0 demonstrate genuine pathological focus; models with Ratio_spatial < 1.0 indicate severe substrate shortcut learning."
    )

    add_h2("3.8 Unified Modeling Language (UML) Structural Models (Use Case & Class Diagrams)")
    add_p("The operational and object-oriented structure of KukuGuard is formalized via standard Unified Modeling Language (UML) diagrams:")

    uml_uc_str = """
+---------------------------------------------------------------------------------------------------+
|                        UML USE CASE DIAGRAM: ACTORS & SYSTEM INTERACTIONS                         |
+---------------------------------------------------------------------------------------------------+

      ACTORS                                    USE CASES (KUKUGUARD SYSTEM)
      ======                                    ============================

  +---------------+                             +-----------------------------------+
  |               | --------------------------> | UC-1: Ingest Optical Fecal Image  |
  | Poultry Farm  |                             +-----------------------------------+
  | Worker        |                                               |
  |               |                                               v <<include>>
  +---------------+                             +-----------------------------------+
                                                | UC-2: Execute OOD Anomaly Filter  |
                                                +-----------------------------------+
  +---------------+                                               |
  |               |                                               v <<include>>
  | Veterinary    |                             +-----------------------------------+
  | Epidemiologist| --------------------------> | UC-3: Run Dual-Path Inference     |
  |               |                             |       (410-d SVM + Calibrated CNN)|
  +---------------+                             +-----------------------------------+
                                                                  |
                                                                  v <<include>>
                                                +-----------------------------------+
                                                | UC-4: Inspect Grad-CAM XAI Saliency|
                                                +-----------------------------------+
                                                                  |
                                                                  v <<include>>
  +---------------+                             +-----------------------------------+
  | System Admin /| --------------------------> | UC-5: Access Biosecurity SOP &    |
  | Farm Manager  |                             |       Export Diagnostic Dossier   |
  +---------------+                             +-----------------------------------+
                                                                  |
                                                                  v <<include>>
                                                +-----------------------------------+
                                                | UC-6: Retrain Pipeline & Update   |
                                                |       INT8 ONNX Edge Binaries     |
                                                +-----------------------------------+
"""
    add_code_block("Figure 3.2: Unified Modeling Language (UML) Use Case Diagram: Actors & System Interactions", uml_uc_str)

    uml_class_str = """
+---------------------------------------------------------------------------------------------------+
|                    UML CLASS DIAGRAM: DATA, MODELS, CALIBRATION & INFERENCE                       |
+---------------------------------------------------------------------------------------------------+

  +------------------------------+             +-------------------------------+
  |       ChickenDataset         |             |     ClassicalFeatureExtractor |
  +------------------------------+             +-------------------------------+
  | - image_paths: List[str]     |             | - color_spaces: List[str]     |
  | - labels: List[int]          |             | - glcm_distances: List[int]   |
  | - transforms: Compose        |             | - lbp_radii: List[int]        |
  +------------------------------+             +-------------------------------+
  | + __len__(): int             |             | + extract_color(img): Array   |
  | + __getitem__(idx): Tuple    |             | + extract_glcm(img): Array    |
  +------------------------------+             | + extract_lbp(img): Array     |
                 |                             | + extract_haar(img): Array    |
                 v                             | + extract_all(img): Array[410]|
  +------------------------------+             +-------------------------------+
  |       ModelFactory           |                             |
  +------------------------------+                             v
  | + create_model(arch, c): NN  |             +-------------------------------+
  | + BaselineCNN                |             |       SVMClassifier           |
  | + MobileNetV2Wrapper         |             +-------------------------------+
  | + EfficientNetWrapper        |             | - kernel: str = 'rbf'         |
  | + ResNet50Wrapper            |             | - scaler: StandardScaler      |
  +------------------------------+             +-------------------------------+
                 |                             | + fit(X, y): void             |
                 v                             | + predict(X): Array           |
  +------------------------------+             +-------------------------------+
  |     TemperatureScaler        |                             |
  +------------------------------+                             v
  | - temperature: nn.Parameter  |             +-------------------------------+
  +------------------------------+             |       InferenceEngine         |
  | + forward(logits): Tensor    |             +-------------------------------+
  | + fit(val_loader, model): T* |             | - cnn_model: nn.Module        |
  +------------------------------+             | - svm_model: SVMClassifier    |
                 |                             | - temp_scaler: TempScaler     |
                 v                             | - ood_gate: OODFilter         |
  +------------------------------+             +-------------------------------+
  |        GradCAMHook           |             | + predict(img): Dict          |
  +------------------------------+             | + compute_energy(l): float    |
  | - target_layer: nn.Module    |             | + generate_cam(img): Array    |
  +------------------------------+             | + check_consensus(): bool     |
  | + generate_heatmap(): Array  |             +-------------------------------+
  +------------------------------+
"""
    add_code_block("Figure 3.3: Unified Modeling Language (UML) Class Diagram: Preprocessing, Models, OOD & Audit", uml_class_str)

    add_h2("3.9 Rigorous Statistical Auditing & Hypothesis Testing Framework (McNemar & Bootstrap)")
    add_p(
        "To ensure that diagnostic performance claims reflect statistically significant superiority rather than stochastic artifact, we incorporate "
        "paired non-parametric hypothesis testing. For comparing the classification outputs of model A (e.g., EfficientNet-B0) versus model B (e.g., RBF SVM), "
        "we construct a 2x2 contingency matrix of discordant predictions on the test set: n_{01} (samples correct by A but incorrect by B) and n_{10} "
        "(samples correct by B but incorrect by A)."
    )
    add_p(
        "We compute Edwards' continuity-corrected McNemar test statistic:\\n"
        "chi^2 = ( |n_{01} - n_{10}| - 1 )^2 / ( n_{01} + n_{10} )\\n"
        "Under the null hypothesis H_0: P_A = P_B, chi^2 follows a chi-squared distribution with 1 degree of freedom (critical threshold = 3.841 at alpha=0.05). "
        "Furthermore, 95% confidence intervals for Macro F1, Sensitivity, and ECE are established using non-parametric percentile bootstrapping with B=2,000 resamples."
    )
''')
print("Part 4 written successfully.")
