#!/usr/bin/env python3
"""
Build the complete, academically rigorous 25-slide presentation for KukuGuard
Poultry Disease AI, modeled exactly after Crop_Disease_AI_Presentation_New.pptx.
"""

import os
import shutil
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    BASE_DIR = '/home/sahith/Projects/Chicken'
    OUT_PPTX = os.path.join(BASE_DIR, 'Chicken_Disease_AI_Presentation.pptx')
    DESKTOP_PPTX = '/home/sahith/Desktop/Chicken_Disease_AI_Presentation.pptx'

    # Color Palette matching Crop Presentation
    C_NAVY_DARK = RGBColor(15, 32, 67)       # Deep Academic Navy (#0F2043)
    C_NAVY_LIGHT = RGBColor(27, 54, 93)      # Secondary Navy (#1B365D)
    C_SLATE_BG = RGBColor(248, 250, 252)     # Clean Crisp Slate Background (#F8FAFC)
    C_WHITE = RGBColor(255, 255, 255)
    C_DARK_TEXT = RGBColor(15, 23, 42)       # High-contrast Charcoal (#0F172A)
    C_MUTED = RGBColor(71, 85, 105)          # Slate Gray (#475569)
    C_EMERALD = RGBColor(16, 124, 65)        # Clean Agri Green (#107C41)
    C_AMBER = RGBColor(217, 119, 6)          # Accent Amber (#D97706)
    C_RED = RGBColor(220, 38, 38)            # Alert Red (#DC2626)
    C_BLUE = RGBColor(37, 99, 235)           # Process Blue (#2563EB)
    C_CARD_BORDER = RGBColor(203, 213, 225)  # Border Gray (#CBD5E1)
    C_CARD_BG = RGBColor(255, 255, 255)

    def set_slide_bg(slide, color):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, title_text, tracker="KUKUGUARD RESEARCH AUDIT"):
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(0.35))
        tf_c = cat_box.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = tf_c.margin_right = tf_c.margin_top = tf_c.margin_bottom = 0
        p_c = tf_c.paragraphs[0]
        p_c.text = tracker.upper()
        p_c.font.size = Pt(11)
        p_c.font.bold = True
        p_c.font.color.rgb = C_EMERALD

        t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.733), Inches(0.8))
        tf_t = t_box.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_right = tf_t.margin_top = tf_t.margin_bottom = 0
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(25)
        p_t.font.bold = True
        p_t.font.color.rgb = C_NAVY_DARK

        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.55), Inches(11.733), Inches(0.025))
        line.fill.solid()
        line.fill.fore_color.rgb = C_CARD_BORDER
        line.line.color.rgb = C_CARD_BORDER

    def add_card(slide, left, top, width, height, bg_color=C_CARD_BG, border_color=C_CARD_BORDER):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        if border_color:
            shape.line.color.rgb = border_color
            shape.line.width = Pt(1.2)
        else:
            shape.line.fill.background()
        return shape

    def add_act_slide(act_num_str, act_title, subtitle, badges):
        s = prs.slides.add_slide(blank_layout)
        set_slide_bg(s, C_NAVY_DARK)

        logo_path = os.path.join(BASE_DIR, 'project_report/nitte_nsam_logo.png')
        if os.path.exists(logo_path):
            s.shapes.add_picture(logo_path, Inches(0.8), Inches(0.6), height=Inches(0.85))

        tb = s.shapes.add_textbox(Inches(0.8), Inches(1.9), Inches(11.733), Inches(2.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p_act = tf.paragraphs[0]
        p_act.text = act_num_str.upper()
        p_act.font.size = Pt(15)
        p_act.font.bold = True
        p_act.font.color.rgb = C_EMERALD

        p_t = tf.add_paragraph()
        p_t.text = act_title
        p_t.font.size = Pt(32)
        p_t.font.bold = True
        p_t.font.color.rgb = C_WHITE
        p_t.space_before = Pt(8)

        p_sub = tf.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.size = Pt(16)
        p_sub.font.italic = True
        p_sub.font.color.rgb = RGBColor(186, 215, 233)
        p_sub.space_before = Pt(10)

        # Badges at bottom
        n = len(badges)
        w_b = (11.733 - 0.3 * (n - 1)) / n
        for idx, (b_title, b_val, b_col) in enumerate(badges):
            b_card = add_card(s, Inches(0.8 + idx * (w_b + 0.3)), Inches(4.7), Inches(w_b), Inches(1.8), bg_color=C_NAVY_LIGHT, border_color=None)
            tf_b = b_card.text_frame
            tf_b.word_wrap = True
            p = tf_b.paragraphs[0]
            p.text = b_title.upper()
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = b_col
            
            p_val = tf_b.add_paragraph()
            p_val.text = b_val
            p_val.font.size = Pt(13)
            p_val.font.color.rgb = C_WHITE
            p_val.space_before = Pt(6)
        return s

    # =========================================================================
    # SLIDE 1: TITLE & DETAILS
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s1, C_NAVY_DARK)

    logo_path = os.path.join(BASE_DIR, 'project_report/nitte_nsam_logo.png')
    if os.path.exists(logo_path):
        s1.shapes.add_picture(logo_path, Inches(0.8), Inches(0.6), height=Inches(0.95))

    t_box = s1.shapes.add_textbox(Inches(0.8), Inches(1.75), Inches(11.733), Inches(2.4))
    tf1 = t_box.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Auditing Vision-Based Poultry Disease Screening Under Leakage and Confounder Controls"
    p1.font.size = Pt(26)
    p1.font.bold = True
    p1.font.color.rgb = C_WHITE

    p1_sub = tf1.add_paragraph()
    p1_sub.text = "A Methodological Audit: Deep Architectures, Shortcut-Resistant Classical Baselines, Representation-Space OOD Gating, and Edge Limits on Tanzanian Avian Pathology"
    p1_sub.font.size = Pt(14)
    p1_sub.font.italic = True
    p1_sub.font.color.rgb = RGBColor(186, 215, 233)
    p1_sub.space_before = Pt(8)

    c_cand = add_card(s1, Inches(0.8), Inches(4.4), Inches(5.6), Inches(2.3), bg_color=C_NAVY_LIGHT, border_color=None)
    tf_c = c_cand.text_frame
    tf_c.word_wrap = True
    p = tf_c.paragraphs[0]
    p.text = "STUDENT INVESTIGATOR"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_EMERALD

    p_c1 = tf_c.add_paragraph()
    p_c1.text = "Mr. Shamanth\nRegister Number: NNS24BC070\nClass: III BCA 'B'\nDepartment of Computer Science"
    p_c1.font.size = Pt(14)
    p_c1.font.color.rgb = C_WHITE
    p_c1.space_before = Pt(6)

    c_guide = add_card(s1, Inches(6.8), Inches(4.4), Inches(5.733), Inches(2.3), bg_color=C_NAVY_LIGHT, border_color=None)
    tf_g = c_guide.text_frame
    tf_g.word_wrap = True
    p = tf_g.paragraphs[0]
    p.text = "PROJECT GUIDANCE"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_EMERALD

    p_g1 = tf_g.add_paragraph()
    p_g1.text = "Mr. Bharath S. Bhat (Head of Department & Asst. Professor Gd-II)\nMr. Srujan U. Shetty (Assistant Professor)\n\nDr. NSAM First Grade College, Nitte (Deemed to be University)"
    p_g1.font.size = Pt(14)
    p_g1.font.color.rgb = C_WHITE
    p_g1.space_before = Pt(6)

    # =========================================================================
    # SLIDE 2: WHY WE CHOSE THIS (AGRICULTURAL CONTEXT & OBJECTIVES)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s2, C_SLATE_BG)
    add_header(s2, "Why We Chose This: Avian Pathology & Smallholder Farming Crisis", tracker="KUKUGUARD | PROBLEM CONTEXT & RESEARCH MOTIVATION")

    w3 = Inches(3.64)
    gap = Inches(0.4)
    top_pos = Inches(1.8)
    h_card = Inches(5.1)

    cards_s2 = [
        ("The Smallholder Avian Crisis", C_NAVY_DARK, [
            "Poultry is the primary animal protein and economic lifeline for >80% of rural smallholders across developing agrarian economies (FAO, 2022).",
            "Enteric & systemic epizootics (Coccidiosis, Salmonella, virulent Newcastle Disease) trigger sudden catastrophic flock mortality (up to 100% in 48–72 hours).",
            "Horizontal fecal-oral contagion spreads rapidly across confined shed floors, demanding immediate early triage before pen-wide outbreak."
        ]),
        ("The Practical Bottleneck", C_AMBER, [
            "Diagnostic Deserts: Laboratory PCR confirmation and necropsy diagnostics are geographically inaccessible and cost-prohibitive ($15–$40/bird) for rural farmers.",
            "Visual Ambiguity: Non-specific fecal changes (bloody mucus, sulfur-yellow urates, bile green diarrhea) are routinely confused under uncalibrated human inspection.",
            "Over-Medication & AMR: Fear of total flock loss drives excessive indiscriminate prophylactic antibiotic use, accelerating Antimicrobial Resistance (AMR)."
        ]),
        ("Our Research Objectives", C_EMERALD, [
            "Build an edge-deployable, leak-safe diagnostic classifier across 4 primary avian conditions (Healthy, Coccidiosis, Newcastle Disease, Salmonella).",
            "Unsparing Methodological Audit: Quantify and resolve near-duplicate camera burst leakage, pen bedding confounders, and overconfident distractor classifications.",
            "Deliver an uncertainty-calibrated, dual-engine screening dashboard with certified representation-space OOD gating running offline on standard smartphones."
        ])
    ]

    for idx, (title, color, points) in enumerate(cards_s2):
        c = add_card(s2, Inches(0.8) + (w3 + gap)*idx, top_pos, w3, h_card)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = color

        for pt in points:
            p_pt = tf.add_paragraph()
            p_pt.text = "• " + pt
            p_pt.font.size = Pt(11.5)
            p_pt.font.color.rgb = C_DARK_TEXT
            p_pt.space_before = Pt(12)

    # =========================================================================
    # SLIDE 3: CLINICAL FOUNDATION & PATHOLOGY DEFINITIONS
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s3, C_SLATE_BG)
    add_header(s3, "Avian Pathologies: Etiology, Gross Fecal Morphology & Clinical Risks", tracker="ACT 1: CLINICAL FOUNDATION & PATHOLOGY")

    c_math = add_card(s3, Inches(0.8), Inches(1.8), Inches(11.733), Inches(1.1))
    tf_m = c_math.text_frame
    tf_m.word_wrap = True
    p = tf_m.paragraphs[0]
    p.text = "PCR-Confirmed Avian Fecal Pathology Spectrum (Machuve et al., 2022)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK

    p_sub = tf_m.add_paragraph()
    p_sub.text = "Each condition exhibits characteristic biochemical chrominance and morphological texture signatures in excreted droppings, reflecting distinct physiological disease pathways:"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = C_DARK_TEXT
    p_sub.space_before = Pt(3)

    w4 = Inches(2.7)
    gap4 = Inches(0.31)
    t4 = Inches(3.1)
    h4 = Inches(3.8)

    tiers = [
        ("Healthy Control", "Normal Physiological State", C_EMERALD, [
            "Pristine cylindrical fecal form with intact uric acid cap.",
            "Uniform olive-brown matrix with normal intestinal mucosal sheen.",
            "Zero detectable hemorrhage or watery bile extravasation.",
            "Serves as the baseline negative control; no flock intervention required."
        ]),
        ("Coccidiosis", "Eimeria tenella / acervulina", C_RED, [
            "Severe mucoid diarrhea with frank blood & tissue shredding.",
            "Caused by intracellular protozoan destruction of cecal epithelial lining.",
            "High morbidity (80–100%) in broiler chicks aged 3–6 weeks.",
            "Urgent therapeutic anticoccidial administration (toltrazuril) required."
        ]),
        ("Newcastle Disease", "Avian Paramyxovirus-1 (APMV-1)", C_AMBER, [
            "Profuse bright emerald-green watery diarrhea with urate discharge.",
            "Accompanied by acute nervous signs (torticollis) & respiratory rales.",
            "WOAH List-A reportable epizootic; flock mortality 90–100% within 48h.",
            "Mandates emergency flock quarantine and immediate biosecurity cordon."
        ]),
        ("Salmonella", "S. pullorum / gallinarum", C_BLUE, [
            "Chalky, sulfur-yellow to whitish watery diarrhea pasted to cloacal vent.",
            "Causes Bacillary White Diarrhea & systemic Fowl Typhoid.",
            "Vertical transmission via hatcheries and horizontal litter contagion.",
            "Requires targeted antimicrobial therapy and rigorous pen disinfection."
        ])
    ]

    for idx, (title, rng, color, points) in enumerate(tiers):
        c = add_card(s3, Inches(0.8) + (w4 + gap4)*idx, t4, w4, h4)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = color

        p_r = tf.add_paragraph()
        p_r.text = rng
        p_r.font.size = Pt(11)
        p_r.font.bold = True
        p_r.font.color.rgb = C_NAVY_DARK
        p_r.space_before = Pt(2)

        for pt in points:
            p_pt = tf.add_paragraph()
            p_pt.text = "• " + pt
            p_pt.font.size = Pt(10.5)
            p_pt.font.color.rgb = C_DARK_TEXT
            p_pt.space_before = Pt(6)

    # =========================================================================
    # SLIDE 4: ARCHITECTURAL FRAMEWORK (DUAL-ENGINE BLUEPRINT)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s4, C_SLATE_BG)
    add_header(s4, "Architectural Blueprint: The KukuGuard Dual-Engine Framework", tracker="SYSTEM ARCHITECTURE | DUAL-ENGINE FRAMEWORK")

    fig_arch = os.path.join(BASE_DIR, 'reports/figures/fig_kukuguard_pipeline_architecture.png')
    if os.path.exists(fig_arch):
        s4.shapes.add_picture(fig_arch, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_dual = add_card(s4, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf_du = c_dual.text_frame
    tf_du.word_wrap = True
    p = tf_du.paragraphs[0]
    p.text = "DUAL-ENGINE SPECIALIZATION DESIGN"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK

    dual_pts = [
        ("Stage 1 — Penultimate Cosine OOD Gate (1280-d):", "Pre-screens incoming image embeddings against class prototypes. Rejects farm distractors (boots, hands, tools, bare soil) before disease classification (98.00% OOD rejection)."),
        ("Stage 2 — Primary Diagnosis Engine (Center-Only SVM):", "Extracts 205-d color & texture features strictly from the 60% central core (CIELAB, HSV, LBP, Haar wavelets), blinding the model to outer bedding (Macro-F1: 0.9195, 14.2 ms CPU)."),
        ("Stage 3 — Secondary Opinion Engine (EfficientNet-B0 ONNX):", "Generates calibrated probabilities (T=1.63) and Grad-CAM spatial heatmaps at 214.9 FPS (4.65 ms CPU)."),
        ("Stage 4 — High-Sensitivity Newcastle Tripwire:", "If the neural model detects Newcastle Disease when SVM is borderline, the system activates an emergency outbreak alert (CNN achieves 93.94% recall on hard atypical droppings)."),
        ("Streamlit Field Dashboard:", "Combines diagnostic consensus, calibrated confidence bars, explainability heatmaps, and veterinary dossiers (FAO/WOAH guidelines).")
    ]
    for title, desc in dual_pts:
        p_t = tf_du.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_EMERALD
        p_t.space_before = Pt(6)

        p_d = tf_du.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 5: DATASET COMPILATION & HYGIENE
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s5, C_SLATE_BG)
    add_header(s5, "Dataset Compilation: PCR-Verified Tanzanian Poultry Benchmark", tracker="DATA ACQUISITION & INTEGRITY AUDIT")

    c_s5 = add_card(s5, Inches(0.8), Inches(1.8), Inches(5.0), Inches(5.1))
    tf5 = c_s5.text_frame
    tf5.word_wrap = True
    p = tf5.paragraphs[0]
    p.text = "DATASET COMPILATION & HYGIENE"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_EMERALD

    gather_items = [
        ("Source & Laboratory Verification:", "Machuve et al. (2022), captured on smallholder farms in Arusha and Kilimanjaro, Tanzania. First public benchmark with laboratory PCR confirmation."),
        ("Total Pooled Dataset Size:", "8,067 high-resolution RGB fecal images uniformly resized to 224 × 224 pixels across 4 diagnostic categories."),
        ("Flattening & Decontamination Protocol:", "Upstream Kaggle mirrors arrived pre-split into train/val/test folders via naive random splitting. All upstream splits were flattened to data/raw/ to purge cross-split burst leakage before regrouping."),
        ("Four Target Diagnostic Classes:", "• Salmonella: 2,625 images (32.54%)\n• Coccidiosis: 2,476 images (30.70%)\n• Healthy: 2,404 images (29.80%)\n• Newcastle Disease: 562 images (6.97% - Severe Imbalance)."),
        ("Integrity Audit:", "0 corrupt files; 280 exact MD5 duplicates flagged for graph deduplication; uniform 3-channel RGB depth.")
    ]
    for title, desc in gather_items:
        p_t = tf5.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_NAVY_DARK
        p_t.space_before = Pt(5)

        p_d = tf5.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    fig_grid = os.path.join(BASE_DIR, 'reports/figures/sample_grid_composite.png')
    if os.path.exists(fig_grid):
        s5.shapes.add_picture(fig_grid, Inches(6.1), Inches(1.8), width=Inches(6.433))

    # =========================================================================
    # SLIDE 6: CANDIDATE ARCHITECTURE AUDIT
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s6, C_SLATE_BG)
    add_header(s6, "Architectural Exploration: Comparison of Model Backbones", tracker="MODEL BENCHMARKING | CANDIDATE ARCHITECTURES")

    fig_curves = os.path.join(BASE_DIR, 'reports/figures/curves_efficientnet_b0_weighted_ce.png')
    if os.path.exists(fig_curves):
        s6.shapes.add_picture(fig_curves, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_mcomp = add_card(s6, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf_mc = c_mcomp.text_frame
    tf_mc.word_wrap = True
    p = tf_mc.paragraphs[0]
    p.text = "CANDIDATE ARCHITECTURE AUDIT"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK

    model_pts = [
        ("BaselineCNN (Scratch 4-Block CNN | 98K Params):", "Trained from scratch without ImageNet priors. Serves as honest empirical floor: achieves 84.80% Macro-F1 and 88.17% accuracy, confirming strong baseline diagnostic separation."),
        ("MobileNetV2 (2.23M Params | 10.8 ms CPU):", "Lightweight inverted residual architecture. Achieved 84.97% test Macro-F1 and 85.71% Newcastle recall, but exhibited higher variance on uncalibrated backgrounds."),
        ("EfficientNet-B0 Champion (4.01M Params | 15.6 ms CPU):", "Achieved superior balance across parameters, latency, and diagnostic fidelity: 87.14% Macro-F1, 89.41% accuracy, and 90.48% Newcastle recall under weighted cross-entropy."),
        ("ResNet-50 (23.52M Params | 52.3 ms CPU):", "Heavy 23.5M parameter capacity caused rapid memorization of background bedding textures rather than fecal pathology. Gained zero Macro-F1 (86.22%) while quadrupling inference latency."),
        ("The Agricultural Trade-Off:", "Deep vision demands Pareto-optimal balance between representational capacity, edge latency, and resistance to background shortcut overfitting.")
    ]
    for title, desc in model_pts:
        p_t = tf_mc.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = C_EMERALD
        p_t.space_before = Pt(5)

        p_d = tf_mc.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.8)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 7: DATASET IMBALANCE & SPLITS
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s7, C_SLATE_BG)
    add_header(s7, "Dataset Imbalance & The 4.67:1 Newcastle Skew Reality", tracker="DATASET HYGIENE & CLASS DISTRIBUTION")

    fig_dist = os.path.join(BASE_DIR, 'reports/figures/class_distribution.png')
    if os.path.exists(fig_dist):
        s7.shapes.add_picture(fig_dist, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_imb = add_card(s7, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf_imb = c_imb.text_frame
    tf_imb.word_wrap = True
    p = tf_imb.paragraphs[0]
    p.text = "THE SKEW REALITY & PROTOCOLS"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK

    imb_pts = [
        ("The Severe Newcastle Skew (4.67 : 1):", "Salmonella (2,625), Coccidiosis (2,476), and Healthy (2,404) dominate the dataset (~30% each), while Newcastle Disease comprises only 562 images (6.97%)."),
        ("The Clinical Epizootic Threat:", "Newcastle Disease is the most lethal condition (WOAH List-A). A naive model optimizing unweighted cross-entropy will sacrifice Newcastle sensitivity to maximize bulk accuracy, leading to uncontained viral outbreaks."),
        ("Stratified 70 / 15 / 15 Group Partitioning:", "Enforced StratifiedGroupKFold across 7,714 independent perceptual scene groups: Train (5,649 imgs, 70.0%), Val (1,209 imgs, 15.0%), Test (1,209 imgs, 15.0%)."),
        ("Exact Class Ratio Preservation:", "Every split preserves exact class proportions within 0.1% (Salmonella ~32.5%, Coccidiosis ~30.7%, Healthy ~29.8%, Newcastle ~7.0%)."),
        ("Zero Group Overlap Verification:", "Mathematically asserted zero group_id overlap across train, val, and test splits (0 group leakage confirmed).")
    ]
    for title, desc in imb_pts:
        p_t = tf_imb.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = C_AMBER
        p_t.space_before = Pt(5)

        p_d = tf_imb.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.8)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 8: RESOLVING IMBALANCE (WEIGHTS & AUGMENTATION)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s8, C_SLATE_BG)
    add_header(s8, "Resolving Natural Imbalance: Class Weights & Augmentation Policy", tracker="MITIGATION PROTOCOLS | CLASS IMBALANCE")

    cards_s8 = [
        ("1. INVERSE-FREQUENCY CLASS WEIGHTS", C_NAVY_DARK, [
            "Loss Gradients Scaled by Class Inverses: Salmonella (0.51), Healthy (0.56), Coccidiosis (0.54), Newcastle (2.39).",
            "Forces the network to treat a missed Newcastle dropping with ~4.5x greater penalty than an overrepresented Salmonella sample.",
            "Neutralizes class imbalance directly during backpropagation without discarding majority data."
        ]),
        ("2. FOCAL LOSS DYNAMIC HARD-MINING", C_BLUE, [
            "Focal Loss Formulation: FL(p_t) = -α_t (1 - p_t)^γ log(p_t) with focusing parameter γ = 2.0.",
            "Dynamically down-weights easy, well-classified examples, concentrating capacity on hard, ambiguous fecal boundaries.",
            "Elevated Newcastle recall to 89.29% while maintaining solid precision across majority classes."
        ]),
        ("3. BIOLOGICAL AUGMENTATION POLICY", C_EMERALD, [
            "Hard Ban on MixUp / CutMix: Blending bloody mucoid stool with normal droppings produces a biologically impossible hybrid that destroys diagnostic features.",
            "Hue & Saturation Jitter Strictly Locked to 0: Preserves vital biochemical chrominance (bile green, hemoglobin red, urate yellow).",
            "Random rotation ±20° with reflection padding eliminates artificial black corner artifacts."
        ]),
        ("4. UNBIASED EVALUATION METRICS", C_AMBER, [
            "Macro-Averaged F1: Computes arithmetic mean of individual class F1 scores, weighting the 7% Newcastle minority equally with majority classes.",
            "Per-Class Sensitivity Tripwires: Monitored Newcastle recall at every epoch; models failing 85% sensitivity were rejected.",
            "Guarantees that high nominal test accuracy is never achieved by sacrificing vulnerable minority disease detection."
        ])
    ]

    w4_s8 = Inches(2.7)
    gap4_s8 = Inches(0.31)
    for idx, (title, color, points) in enumerate(cards_s8):
        c = add_card(s8, Inches(0.8) + (w4_s8 + gap4_s8)*idx, Inches(1.8), w4_s8, Inches(5.1))
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = color

        for pt in points:
            p_pt = tf.add_paragraph()
            p_pt.text = "• " + pt
            p_pt.font.size = Pt(10.5)
            p_pt.font.color.rgb = C_DARK_TEXT
            p_pt.space_before = Pt(10)

    # =========================================================================
    # SLIDE 9: ACT 2 TRANSITION (THE LEAKAGE AUDIT)
    # =========================================================================
    add_act_slide(
        "ACT 2: THE LEAKAGE AUDIT & EMPIRICAL REALITY",
        "The Near-Duplicate Burst Leakage Revelation",
        "Exposing Camera Burst Duplication, the Illusion of >95% Accuracy, and Establishing the Leak-Free Group-Aware Benchmark",
        [
            ("8,067 Images Audited", "Raw Pooled Benchmark", C_BLUE),
            ("353 Burst Duplicate Twins", "Identified via pHash <= 4", C_RED),
            ("7,714 Scene Groups", "Connected Components", C_AMBER),
            ("Zero Group Overlap", "Programmatically Asserted", C_EMERALD)
        ]
    )

    # =========================================================================
    # SLIDE 10: THE LEAKAGE DISCOVERY
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s10, C_SLATE_BG)
    add_header(s10, "The Leakage Discovery: Exposing Burst Duplicate Contamination", tracker="LEAKAGE AUDIT | CAMERA BURST DECONTAMINATION")

    fig_dedup = os.path.join(BASE_DIR, 'reports/figures/fig_dedup_burst_leakage.png')
    if os.path.exists(fig_dedup):
        s10.shapes.add_picture(fig_dedup, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_leak = add_card(s10, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf_lk = c_leak.text_frame
    tf_lk.word_wrap = True
    p = tf_lk.paragraphs[0]
    p.text = "THE LEAKAGE AUDIT REVELATION"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_RED

    leak_pts = [
        ("The Camera Burst Capture Phenomenon:", "Field photographers take rapid burst photos (3–5 shots/sec) of an individual fecal dropping from slightly rotated angles. Under naive random splitting, identical droppings are scattered across both train and test splits."),
        ("Perceptual Hashing Graph Partitioning:", "Computed 64-bit perceptual hashes (imagehash.phash) across all 8,067 images. Built an adjacency graph connecting pairs with Hamming distance ≤ 4, resolving 7,714 connected components and uncovering 353 duplicate burst twins."),
        ("Compact Cluster Verification (≤ 4 vs ≤ 6):", "Sweeping the Hamming threshold to ≤ 6 yielded identical results (7,714 groups, 353 duplicates), proving that cluster boundaries are compact and sharp (no spurious merging of unrelated images)."),
        ("Group-Aware Stratified Partitioning:", "Using StratifiedGroupKFold, all near-duplicate bursts were strictly sequestered into single splits, establishing an honest holdout test benchmark (N = 1,209 images across 1,158 groups)."),
        ("The Published Benchmark Collapse:", "Published papers reported 95%–98% accuracy on naive random splits. Under our leak-free holdout, true generalized neural accuracy drops to 89.41%, exposing ~6–9 pp of burst memorization.")
    ]
    for title, desc in leak_pts:
        p_t = tf_lk.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = C_NAVY_DARK
        p_t.space_before = Pt(5)

        p_d = tf_lk.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.8)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 11: DEEP CNN RESULTS ON LEAK-FREE BENCHMARK
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s11, C_SLATE_BG)
    add_header(s11, "Deep CNN Empirical Results on Leak-Free Benchmark", tracker="MODEL EVALUATION | LEAK-FREE NEURAL BENCHMARK")

    fig_cm = os.path.join(BASE_DIR, 'reports/figures/confusion_matrix_efficientnet_b0.png')
    if os.path.exists(fig_cm):
        s11.shapes.add_picture(fig_cm, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_res = add_card(s11, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf_res = c_res.text_frame
    tf_res.word_wrap = True
    p = tf_res.paragraphs[0]
    p.text = "THE NEURAL GENERALIZATION VERDICT"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK

    res_pts = [
        ("Held-Out Test Performance (N = 1,209):", "• Test Accuracy: 89.41% (1,081 / 1,209 correct)\n• Test Macro-F1: 0.8714 | Weighted-F1: 0.8953\n• Macro-Average ROC-AUC: 0.9830 (Near-perfect discriminative capacity)."),
        ("Per-Class Diagnostic Breakdown:", "• Coccidiosis: Precision 95.01% | Recall 92.70% | F1 0.9384\n• Healthy: Precision 87.85% | Recall 86.15% | F1 0.8699\n• Newcastle Disease: Precision 67.26% | Recall 90.48% | F1 0.7716\n• Salmonella: Precision 92.13% | Recall 89.09% | F1 0.9058."),
        ("Coccidiosis ↔ Salmonella Separation:", "In clinical pathology, both conditions produce mucoid diarrhea. In our leak-free test, cross-confusion was just 1.44% (11 / 764 samples), cleanly distinguishing frank blood from yellow urates."),
        ("Newcastle Sensitivity Success:", "Weighted cross-entropy captured 76 / 84 minority Newcastle cases (90.48% recall), neutralizing the 1:4.5 class imbalance penalty."),
        ("The Realistic Ceiling:", "True generalized neural performance settles at ~89.4%, proving that >95% published claims relied on test set burst leakage.")
    ]
    for title, desc in res_pts:
        p_t = tf_res.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = C_EMERALD
        p_t.space_before = Pt(5)

        p_d = tf_res.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.8)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 12: UNCERTAINTY CALIBRATION
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s12, C_SLATE_BG)
    add_header(s12, "Uncertainty Calibration: Temperature Scaling Reliability Audit", tracker="UNCERTAINTY CALIBRATION | RELIABILITY AUDIT")

    fig_cal = os.path.join(BASE_DIR, 'reports/figures/calibration_curves_efficientnet_b0.png')
    if os.path.exists(fig_cal):
        s12.shapes.add_picture(fig_cal, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_cal = add_card(s12, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf_cal = c_cal.text_frame
    tf_cal.word_wrap = True
    p = tf_cal.paragraphs[0]
    p.text = "EMPIRICAL CALIBRATION VERDICT"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK

    cal_pts = [
        ("The Neural Overconfidence Problem:", "Modern deep networks trained with cross-entropy produce overconfident, peaky probabilities. In field veterinary triage, an uncalibrated 95% confidence score on a borderline infection leads to misplaced farmer complacency."),
        ("Temperature Scaling Optimization:", "Fitted a post-processing scalar temperature T on validation logits via Negative Log-Likelihood (NLL) minimization: optimal T = 1.6302 > 1.0 (indicating raw logit overconfidence)."),
        ("52.2% Reduction in Calibration Error:", "• Expected Calibration Error (ECE): Cut from 5.50% down to 2.63% (-2.87 percentage points).\n• Negative Log-Likelihood (NLL): Improved from 0.3675 to 0.3046.\n• Brier Score: Reduced from 0.1669 to 0.1581."),
        ("Empirical Reliability in Practice:", "Post-calibration, a predicted probability of 80% corresponds to an exact 80% empirical hit rate, establishing trustworthy confidence for farm decision-making."),
        ("Zero Latency Deployment:", "Temperature scaling modifies only output logits by dividing by scalar T (0.001 ms CPU), preserved in the Streamlit application.")
    ]
    for title, desc in cal_pts:
        p_t = tf_cal.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = C_BLUE
        p_t.space_before = Pt(5)

        p_d = tf_cal.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.8)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 13: ACT 3 TRANSITION (SUBSTRATE CONFOUNDER)
    # =========================================================================
    add_act_slide(
        "ACT 3: THE SUBSTRATE CONFOUNDER & SHORTCUT LEARNING",
        "Unmasking Pen Bedding Confounders",
        "Statistical Dependency Analysis, Grad-CAM Attention Dispersion, and the Hard Minority Performance Collapse",
        [
            ("χ² = 3,159.75", "p < 10⁻³⁰⁰ Significance", C_RED),
            ("Cramer's V = 0.361", "High Confounder Risk (>0.30)", C_AMBER),
            ("86.5% Healthy on Wood", "Severe Background Shortcut", C_BLUE),
            ("71.3% Cocci on Soil/Litter", "Pathology / Substrate Confound", C_EMERALD)
        ]
    )

    # =========================================================================
    # SLIDE 14: THE CONFOUNDER DISCOVERY (CROSS-TABULATION)
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s14, C_SLATE_BG)
    add_header(s14, "The Confounder Discovery: Acute Substrate-Disease Correlation", tracker="CONFOUNDER AUDIT | STATISTICAL PROOF")

    fig_crosstab = os.path.join(BASE_DIR, 'reports/figures/substrate_cluster_crosstab.png')
    if os.path.exists(fig_crosstab):
        s14.shapes.add_picture(fig_crosstab, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_conf = add_card(s14, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf_cf = c_conf.text_frame
    tf_cf.word_wrap = True
    p = tf_cf.paragraphs[0]
    p.text = "EMPIRICAL SUBSTRATE AUDIT"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_RED

    conf_pts = [
        ("Outer-Border Clustering Audit:", "Extracted outer 15% border margins from all 8,067 images, isolating pure pen bedding away from droppings. K-Means clustered background textures into 4 dominant substrates: Dark Soil (0), Wood Shavings (1), Reddish Litter (2), Mixed Straw (3)."),
        ("Acute Bedding-Disease Correlation:", "• Healthy Droppings: 86.48% (2,079 / 2,404) sat on Light Wood Shavings!\n• Coccidiosis Droppings: 71.29% (1,765 / 2,476) sat on Dark Soil or Reddish Litter!\n• Salmonella & Newcastle: ~58% on Wood Shavings, ~20% on Straw."),
        ("Statistical Independence Refutation:", "Chi-Square Test: χ² = 3,159.75 (p < 10⁻³⁰⁰). Cramer's V = 0.361, comfortably exceeding the 0.30 threshold of serious concern."),
        ("The Background Shortcut Threat:", "A deep neural network can achieve ~80% nominal accuracy without analyzing fecal pathology at all — simply learning: 'Wood shavings = Healthy; Dark Soil = Coccidiosis'!"),
        ("Mandatory Audit:", "Demanded a dedicated hard-subset stress test and peripheral background feature ablation.")
    ]
    for title, desc in conf_pts:
        p_t = tf_cf.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = C_NAVY_DARK
        p_t.space_before = Pt(5)

        p_d = tf_cf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.8)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 15: HARD MINORITY STRESS TEST
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s15, C_SLATE_BG)
    add_header(s15, "The Hard Minority Stress Test: Neural Performance Collapse", tracker="STRESS-TEST AUDIT | MINORITY SUBSTRATES")

    c_s15_t = add_card(s15, Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.1))
    tf15 = c_s15_t.text_frame
    tf15.word_wrap = True
    p = tf15.paragraphs[0]
    p.text = "THE HARD MINORITY SUBSTRATE AUDIT (n = 374, 30.9% of Test Set)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK

    p_desc = tf15.add_paragraph()
    p_desc.text = "We audited test images photographed strictly on each disease's atypical minority bedding (e.g., Healthy on bare soil/straw; Coccidiosis on wood shavings):"
    p_desc.font.size = Pt(11)
    p_desc.font.color.rgb = C_DARK_TEXT
    p_desc.space_before = Pt(4)

    # Table of stress test results
    t_shape = s15.shapes.add_table(5, 6, Inches(0.9), Inches(2.6), Inches(11.533), Inches(2.0))
    table = t_shape.table
    table.columns[0].width = Inches(2.3)
    table.columns[1].width = Inches(1.8)
    table.columns[2].width = Inches(1.8)
    table.columns[3].width = Inches(1.8)
    table.columns[4].width = Inches(1.8)
    table.columns[5].width = Inches(2.033)

    headers = ["Diagnostic Class", "Overall Recall", "Hard Recall (n=374)", "Recall Delta", "Mean Center CAM", "Operational Impact"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_NAVY_DARK
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = C_WHITE

    row_data = [
        ("Coccidiosis (on wood / straw)", "92.70%", "90.35%", "-2.35 pp", "74.2%", "Resilient: Blood overrides bedding"),
        ("Healthy (on soil / reddish / straw)", "86.15%", "68.52%", "-17.63 pp", "51.4%", "VULNERABLE: Severe False Alarms!"),
        ("Newcastle Disease (on soil / reddish)", "90.48%", "93.94%", "+3.46 pp", "58.1%", "Resilient: Dispersed green watery bile"),
        ("Salmonella (on soil / reddish)", "89.09%", "89.02%", "-0.07 pp", "71.6%", "Resilient: Yellow urate contrast")
    ]
    for i, row in enumerate(row_data, 1):
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(254, 242, 242) if "-17.63" in val or "VULNERABLE" in val else (RGBColor(241, 245, 249) if i%2==0 else C_WHITE)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(10)
                p.font.color.rgb = C_RED if "-17.63" in val or "VULNERABLE" in val else C_DARK_TEXT
                if j == 0 or j == 3: p.font.bold = True

    # Bullet points at bottom
    c_bot = add_card(s15, Inches(0.9), Inches(4.8), Inches(11.533), Inches(1.9), bg_color=RGBColor(255, 251, 235), border_color=C_AMBER)
    tf_b = c_bot.text_frame
    tf_b.word_wrap = True
    p = tf_b.paragraphs[0]
    p.text = "CRITICAL AUDIT TAKEAWAY: THE HEALTHY FALSE-ALARM CRISIS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_AMBER

    pts_bot = [
        "Healthy Dropping Collapse: When normal droppings appear on soil or straw instead of familiar wood shavings, recall plummets from 86.15% down to 68.52% (-17.63 pp).",
        "False Alarm Mechanism: In the absence of bright wood shavings, the neural network panics and misclassifies normal brown/green feces as Coccidiosis or Newcastle.",
        "Clinical Consequence: Healthy flocks would be subjected to unwarranted chemical medication or quarantine simply because the farmer changed pen bedding!"
    ]
    for pt in pts_bot:
        p_pt = tf_b.add_paragraph()
        p_pt.text = "• " + pt
        p_pt.font.size = Pt(10)
        p_pt.font.color.rgb = C_DARK_TEXT
        p_pt.space_before = Pt(3)

    # =========================================================================
    # SLIDE 16: GRAD-CAM EXPLAINABILITY AUDIT
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s16, C_SLATE_BG)
    add_header(s16, "Explainability Audit: Grad-CAM Attention Dispersion Analysis", tracker="EXPLAINABLE AI | GRAD-CAM SPATIAL AUDIT")

    fig_cam = os.path.join(BASE_DIR, 'reports/figures/gradcam_composite_grid_efficientnet_b0.png')
    if os.path.exists(fig_cam):
        s16.shapes.add_picture(fig_cam, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_cam = add_card(s16, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf_cm = c_cam.text_frame
    tf_cm.word_wrap = True
    p = tf_cm.paragraphs[0]
    p.text = "THE EXPLAINABILITY AUDIT REVELATION"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK

    cam_pts = [
        ("Automated Target-Layer Resolution:", "Grad-CAM hooked into conv_head (Conv2d 320→1280) of EfficientNet-B0. Audited 24 representative test samples (3 correct + 3 incorrect per class)."),
        ("Spatial Activation Energy Quantification:", "Computed activation energy in central 70% bounding region vs outer 15% bedding margin:\n• Overall Test Set: 75.9% Central Energy (Focal Focus)\n• Hard Minority Subset: Drops to 52.8% Central Energy (Litter Dispersion!)."),
        ("Focal Attributions on Primary Lesions:", "For high-confidence correct classifications, attention centers tightly on authentic biological markers: crimson hemorrhages for Coccidiosis, yellow urate caps for Salmonella."),
        ("Attention Dispersion on Hard Substrates:", "On atypical substrates, heatmaps broaden across stool boundaries, lighting up straw edges, wood shavings, and bare dirt."),
        ("Veterinary Screening Warning:", "Post-hoc saliency maps cannot serve as sole confirmation of diagnosis; visual heatmaps can mislead practitioners when background textures distract neural filters.")
    ]
    for title, desc in cam_pts:
        p_t = tf_cm.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = C_EMERALD
        p_t.space_before = Pt(5)

        p_d = tf_cm.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.8)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 17: ACT 4 TRANSITION (SHORTCUT-RESISTANT FEATURE ENGINEERING)
    # =========================================================================
    add_act_slide(
        "ACT 4: SHORTCUT-RESISTANT FEATURE ENGINEERING",
        "The Classical ML Counter-Offensive",
        "Ablating the Background: Can Domain-Engineered Core Features Outperform Deep Convolutional Networks?",
        [
            ("205-d Core Features", "Strict Central 60% Crop", C_EMERALD),
            ("0% Litter Visibility", "Completely Blind to Bedding", C_BLUE),
            ("SVM F1: 0.9195", "+4.81 pp Over Deep CNN", C_RED),
            ("2.65 MB Footprint", "14.2 ms CPU Latency", C_AMBER)
        ]
    )

    # =========================================================================
    # SLIDE 18: FEATURE ENGINEERING (CORE EXTRACTION)
    # =========================================================================
    s18 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s18, C_SLATE_BG)
    add_header(s18, "Feature Engineering: Multimodal Color, Texture & Core Extraction", tracker="FEATURE ENGINEERING | DOMAIN EXTRACTION")

    cards_s18 = [
        ("1. COLOR SPACES: CIELAB & HSV", C_NAVY_DARK, [
            "RGB fails under uncalibrated farm lighting. CIELAB decouples lightness (L*) from chromaticity (a*, b*).",
            "a* Channel (Green-Red): Directly isolates crimson hemoglobin hemorrhage in Coccidiosis stool.",
            "b* Channel (Blue-Yellow): Quantifies uric acid crystals and sulfur-yellow Salmonella discharge.",
            "HSV Hue & Saturation: Captures emerald bile tones of Newcastle Disease. 16-bin histograms + 4 statistical moments (mean, std, skew, kurtosis)."
        ]),
        ("2. MICRO-TEXTURE & WAVELETS", C_BLUE, [
            "Local Binary Patterns (LBP): Circular uniform patterns (P=8, R=1, 10 bins) capture fine mucosal granulation and fibrinous flakes in droppings.",
            "2-Level 2D Haar Discrete Wavelet Transform (DWT): Decomposes fecal image into LL, LH, HL, HH sub-bands.",
            "Extracts horizontal, vertical, and diagonal energy distributions, isolating watery mucosal boundaries from dry stool surfaces."
        ]),
        ("3. CENTRAL 60% CORE MASKING", C_EMERALD, [
            "The Confounder Blinding Protocol: Droppings naturally occupy the center frame under standard smartphone photography.",
            "Engineered features extracted strictly from the inner 60% concentric bounding core (center_ features), discarding outer 40% borders.",
            "Mathematically guarantees zero background litter visibility, eliminating wood shavings and dirt shortcuts permanently."
        ])
    ]

    for idx, (title, color, points) in enumerate(cards_s18):
        c = add_card(s18, Inches(0.8) + (w3 + gap)*idx, top_pos, w3, h_card)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = color

        for pt in points:
            p_pt = tf.add_paragraph()
            p_pt.text = "• " + pt
            p_pt.font.size = Pt(11)
            p_pt.font.color.rgb = C_DARK_TEXT
            p_pt.space_before = Pt(12)

    # =========================================================================
    # SLIDE 19: CLASSICAL BREAKTHROUGH (SVM VS CNN)
    # =========================================================================
    s19 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s19, C_SLATE_BG)
    add_header(s19, "The Classical Breakthrough: Core-Ablated SVM Outperforms Deep CNN", tracker="CLASSICAL VS DEEP CNN | BENCHMARK VERDICT")

    fig_master = os.path.join(BASE_DIR, 'reports/figures/fig_master_model_benchmark.png')
    if os.path.exists(fig_master):
        s19.shapes.add_picture(fig_master, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_s19 = add_card(s19, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf19 = c_s19.text_frame
    tf19.word_wrap = True
    p = tf19.paragraphs[0]
    p.text = "THE HONEST SCIENTIFIC VERDICT"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK

    s19_pts = [
        ("The Background Confounder Confirmed:", "Full 410-d SVM dropped from 0.9428 to 0.9195 (-0.0233) when global features were removed. This confirms that global bedding statistics (global_lab_b_skew) had indeed provided shortcut leverage."),
        ("Center-Only SVM Dominates Deep CNN:", "Even when 100% blinded to the background, Center-Only SVM achieves 0.9195 Macro-F1 (93.55% Acc) vs 0.8714 Macro-F1 (89.41% Acc) for EfficientNet-B0 — beating deep learning by +4.81 percentage points!"),
        ("Superior Hard-Subset Robustness:", "On the 374 hard minority images, Center-Only SVM hits 0.8690 Macro-F1 vs 0.8204 for the deep CNN, proving far greater resilience against bedding shifts."),
        ("Edge Footprint & Latency Triumph:", "• Model Disk Size: 2.65 MB (SVM) vs 16.0 MB (PyTorch CNN)\n• End-to-End Latency: 14.2 ms (SVM) vs 15.6 ms (PyTorch CNN)\n• Training Time: 0.6 seconds vs ~7.5 hours on CPU."),
        ("Takeaway for Low-Resource Edge AI:", "Deep learning is not universally superior. Well-engineered domain color features with spatial masking outperform unconstrained CNNs.")
    ]
    for title, desc in s19_pts:
        p_t = tf19.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = C_EMERALD
        p_t.space_before = Pt(5)

        p_d = tf19.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.8)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 20: SHAP INTERPRETABILITY & THE VETERINARY TRADE-OFF
    # =========================================================================
    s20 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s20, C_SLATE_BG)
    add_header(s20, "SHAP Interpretability & The Critical Veterinary Trade-Off", tracker="SHAP INTERPRETABILITY & VETERINARY TRADE-OFF")

    fig_shap = os.path.join(BASE_DIR, 'reports/figures/shap_summary_center_only.png')
    if os.path.exists(fig_shap):
        s20.shapes.add_picture(fig_shap, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_s20 = add_card(s20, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf20 = c_s20.text_frame
    tf20.word_wrap = True
    p = tf20.paragraphs[0]
    p.text = "THE NEWCASTLE DILEMMA & SYNERGY"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_AMBER

    s20_pts = [
        ("100% Core Fecal Biomarkers (SHAP):", "Top features driving the center-only model: center_lab_b_bin10 (yellow urate / Salmonella), center_rgb_r_bin15 (crimson hemorrhage / Coccidiosis), and center_hsv_h_bin2 (emerald bile / Newcastle). Zero background artifacts dominate."),
        ("The Critical Newcastle Trade-Off:", "While SVM excels on Healthy recall (79.63% vs 68.52% on hard bedding), Newcastle recall drops from 93.94% (CNN) down to 78.79% (SVM) on atypical droppings!"),
        ("Why Classical Models Struggle on Newcastle:", "Newcastle droppings produce irregular, watery bile puddles where color histograms alone miss subtle spatial bile gradients that hierarchical CNN receptive fields capture."),
        ("The Dual-Engine Mandate:", "Neither model is sufficient alone: SVM eliminates substrate false alarms, while EfficientNet-B0 guards against missed Newcastle outbreaks."),
        ("Operational Synergy:", "Option A runs both engines in parallel: SVM provides primary triage; CNN triggers a high-sensitivity tripwire alert if Newcastle is suspected.")
    ]
    for title, desc in s20_pts:
        p_t = tf20.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = C_NAVY_DARK
        p_t.space_before = Pt(5)

        p_d = tf20.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.8)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 21: ACT 5 TRANSITION (OOD & EDGE LIMITS)
    # =========================================================================
    add_act_slide(
        "ACT 5: OUT-OF-DISTRIBUTION SAFEGUARDS & EDGE LIMITS",
        "Out-of-Distribution Distractors & Edge Quantization",
        "Defeating ImageNet Linear Projection Bias, 2.88x ONNX FP32 Speedup, and Dynamic INT8 Collapse",
        [
            ("300 Real Distractors", "Boots, Hands, Tools, Soil", C_BLUE),
            ("Logit Energy: 23.0%", "Catastrophic OOD Failure", C_RED),
            ("Cosine Dist: 98.0%", "100% Boots/Hands Blocked", C_EMERALD),
            ("ONNX FP32: 4.65 ms", "214.9 FPS Real-Time CPU", C_AMBER)
        ]
    )

    # =========================================================================
    # SLIDE 22: OOD AUDIT (LOGIT FAILURE VS COSINE DISTANCE)
    # =========================================================================
    s22 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s22, C_SLATE_BG)
    add_header(s22, "The OOD Audit: Why Logit Scores Failed & Representation Distance Won", tracker="OOD DETECTION | METHODOLOGICAL BREAKTHROUGH")

    fig_ood = os.path.join(BASE_DIR, 'reports/figures/fig_ood_rejection_summary.png')
    if os.path.exists(fig_ood):
        s22.shapes.add_picture(fig_ood, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_s22 = add_card(s22, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf22 = c_s22.text_frame
    tf22.word_wrap = True
    p = tf22.paragraphs[0]
    p.text = "IMAGENET PROJECTION BIAS EXPOSED"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK

    s22_pts = [
        ("The 300 Real Farm Distractor Benchmark:", "Evaluated 4 non-fecal categories: rubber boots (75), human hands/skin (75), domestic buckets/tools (75), and clean pen soil (75)."),
        ("Catastrophic Logit-Based Collapse:", "Free Energy (23.0%), MLS (23.3%), and Softmax (21.3%) failed completely, admitting 77% of boots and hands and confidently diagnosing rubber footwear as Coccidiosis!"),
        ("The Mechanism — ImageNet Projection Bias:", "Backbone yields large-norm feature vectors for common objects (boots, hands). In a 4-class linear head (W · z), high-norm vectors randomly project strongly onto positive disease weights, creating high energy scores."),
        ("The Representation Distance Solution:", "Deep Cosine Feature Distance in R¹²⁸⁰ measures geometric distance against in-distribution class centroids (μ_c). Achieves 98.00% OOD rejection (100% on boots, hands, tools; AUROC 0.9966)!"),
        ("Classical Fallback:", "For low-power microcontrollers, Classical Core Distance achieves 92.67% rejection (AUROC 0.9882) without requiring any neural inference.")
    ]
    for title, desc in s22_pts:
        p_t = tf22.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = C_RED if "Collapse" in title or "Bias" in title else C_EMERALD
        p_t.space_before = Pt(5)

        p_d = tf22.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.8)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 23: EDGE QUANTIZATION AUDIT
    # =========================================================================
    s23 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s23, C_SLATE_BG)
    add_header(s23, "Edge Deployment & Quantization Audit: The INT8 Depthwise Trap", tracker="EDGE COMPUTING | QUANTIZATION AUDIT")

    fig_quant = os.path.join(BASE_DIR, 'reports/figures/fig_edge_quantization_audit.png')
    if os.path.exists(fig_quant):
        s23.shapes.add_picture(fig_quant, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_s23 = add_card(s23, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf23 = c_s23.text_frame
    tf23.word_wrap = True
    p = tf23.paragraphs[0]
    p.text = "ENGINEERING EXPORT AUDIT"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK

    s23_pts = [
        ("ONNX FP32 Engine (4.65 ms | 214.9 FPS):", "Exporting PyTorch to optimized ONNX Runtime FP32 slashed CPU latency from 15.6 ms to 4.65 ms — a 2.88x speedup with exact numerical fidelity (max absolute difference < 10⁻⁵)."),
        ("The Dynamic INT8 Quantization Collapse:", "Dynamic 8-bit quantization shrank model disk size from 15.28 MB to 4.11 MB (-73.1%), but top-1 test accuracy catastrophically collapsed from 89.41% down to 15.50% (-73.9 pp collapse)!"),
        ("Root Cause — Depthwise Accumulation Degradation:", "Depthwise separable convolutions in EfficientNet-B0 have small dynamic per-channel activation ranges that clip severely under dynamic affine INT8 quantization."),
        ("Edge Deployment Policy:", "Never deploy dynamic INT8 on depthwise mobile backbones without full Post-Training Calibration or Quantization-Aware Training (QAT)."),
        ("The Optimal Edge Architecture:", "ONNX FP32 runs in 4.65 ms on standard mobile CPUs, rendering risky INT8 compression completely unnecessary for real-time operation.")
    ]
    for title, desc in s23_pts:
        p_t = tf23.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = C_RED if "Collapse" in title or "Degradation" in title else C_EMERALD
        p_t.space_before = Pt(5)

        p_d = tf23.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.8)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 24: KUKUGUARD FIELD APPLICATION & STREAMLIT DEMO
    # =========================================================================
    s24 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s24, C_SLATE_BG)
    add_header(s24, "KukuGuard Field Screening Dashboard & Dual-Engine Triage", tracker="SYSTEM IMPLEMENTATION | FIELD INTERACTION")

    fig_gallery = os.path.join(BASE_DIR, 'reports/figures/fig_app_sample_triage_gallery.png')
    if os.path.exists(fig_gallery):
        s24.shapes.add_picture(fig_gallery, Inches(0.8), Inches(1.8), width=Inches(6.2))

    c_s24 = add_card(s24, Inches(7.3), Inches(1.8), Inches(5.233), Inches(5.1))
    tf24 = c_s24.text_frame
    tf24.word_wrap = True
    p = tf24.paragraphs[0]
    p.text = "FIELD APPLICATION & BIOSECURITY"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_NAVY_DARK

    dash_features = [
        ("Dual Pipeline Modes (Sidebar Switch):", "• Option A (Dual-Engine Max-Safeguard): Cosine OOD Gate + Center SVM + ONNX CNN + Grad-CAM (~21.6 ms end-to-end CPU).\n• Option B (Edge Micro-Pipeline): Classical OOD Gate + Center SVM only (~14.4 ms CPU, 2.65 MB footprint)."),
        ("Automated OOD Gate Interception:", "Non-fecal uploads (boots, bare dirt, hands) are intercepted immediately: displays clear notice 'Non-Fecal Image Detected' and halts classification before false alarms can occur."),
        ("Dual-Model Consensus & Newcastle Alert:", "Displays primary SVM prediction alongside secondary CNN probability. Triggers an urgent warning banner if the CNN detects Newcastle Disease (93.9% vs 78.8% hard recall)."),
        ("Grad-CAM Spatial Focus Badge:", "Calculates real-time central vs border energy ratio. Displays green badge ('Focal Attention Confirmed ≥ 65%') or yellow warning if attention disperses onto bedding."),
        ("Pre-Staged 11-Sample Interactive Gallery:", "Shipped with 11 representative samples (2 per disease + 3 distractors) for instant evaluation without requiring live chicken dropping photos."),
        ("Comprehensive Disease Dossiers:", "Includes clinical etiology, transmission vectors, clinical signs, medical therapy, and biosecurity cordon protocols compiled from FAO / WOAH Terrestrial Manual standards.")
    ]
    for title, desc in dash_features:
        p_t = tf24.add_paragraph()
        p_t.text = "• " + title
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_EMERALD
        p_t.space_before = Pt(4)

        p_d = tf24.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.2)
        p_d.font.color.rgb = C_DARK_TEXT
        p_d.space_before = Pt(1)

    # =========================================================================
    # SLIDE 25: LIMITATIONS, FUTURE SCOPE & CONCLUSIONS
    # =========================================================================
    s25 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s25, C_SLATE_BG)
    add_header(s25, "Scientific Limitations, Future Scope & Conclusions", tracker="CRITICAL APPRAISAL | DEFENSE SYNTHESIS")

    cards_s25 = [
        ("Critical Limitations", C_RED, [
            "Single Geographic Provenance: Dataset collected exclusively in northern Tanzania (Arusha/Kilimanjaro); performance across exotic European/Asian breeds or automated cage batteries unverified.",
            "Isolated Stool Assumption: Evaluates individual droppings; does not integrate flock-level water intake, temperature curves, or mortality records.",
            "Screening Aid, Not Final Diagnosis: Gross fecal appearance indicates organ pathology, not definitive microbiological proof; PCR confirmation remains mandatory for statutory epizootic reporting."
        ]),
        ("Strategic Future Scope", C_BLUE, [
            "Intrinsic Spatial Cross-Attention: Replace post-hoc Grad-CAM with Vision Transformer patch cross-attention trained directly on segmented fecal masks.",
            "Multi-Modal Sensor Integration: Fuse fecal computer vision with acoustic microphone rale detection and IoT environmental humidity telemetry.",
            "Quantization-Aware Training (QAT): Train dedicated INT8 models with learned per-channel scale factors to recover depthwise accuracy on ultra-low-power microcontrollers."
        ]),
        ("Core Takeaways for Defense", C_EMERALD, [
            "Published >95% Benchmarks Were Artifactual: Camera burst leakage inflates accuracy; true leak-free neural baseline is 89.41%.",
            "Domain-Engineered Core Features Win: Center-Only SVM achieves 91.95% Macro-F1, beating deep CNNs by +4.81 pp while eliminating bedding shortcuts.",
            "Representation OOD Gating is Essential: Deep Cosine Distance eliminates catastrophic false alarms on farm boots and hands (98.0% rejection vs 23.0% for logit energy)."
        ])
    ]

    for idx, (title, color, points) in enumerate(cards_s25):
        c = add_card(s25, Inches(0.8) + (w3 + gap)*idx, top_pos, w3, h_card)
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = color

        for pt in points:
            p_pt = tf.add_paragraph()
            p_pt.text = "• " + pt
            p_pt.font.size = Pt(11)
            p_pt.font.color.rgb = C_DARK_TEXT
            p_pt.space_before = Pt(12)

    # Save presentation
    prs.save(OUT_PPTX)
    print(f"Saved master presentation to: {OUT_PPTX}")

    # Copy to Desktop if Desktop exists
    if os.path.exists('/home/sahith/Desktop'):
        shutil.copy(OUT_PPTX, DESKTOP_PPTX)
        print(f"Copied presentation to Desktop: {DESKTOP_PPTX}")

if __name__ == "__main__":
    build_presentation()
