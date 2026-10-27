out_file = "/home/sahith/Projects/Chicken/project_report/build_exact_crop_style_report.py"

with open(out_file, "a", encoding="utf-8") as f:
    f.write('''
    # -------------------------------------------------------------------------
    # PAGES 6, 7, 8 (vi, vii, viii): TABLE OF CONTENTS (Continuous Table)
    # -------------------------------------------------------------------------
    all_toc = [
        ("—", "Certificate of Approval", "ii"),
        ("—", "Declaration of Originality", "iii"),
        ("—", "Acknowledgment", "iv"),
        ("—", "Abstract", "v"),
        ("—", "Table of Contents", "vi"),
        ("—", "List of Figures", "ix"),
        ("—", "List of Tables", "xi"),
        ("—", "List of Abbreviations & Acronyms", "xii"),
        ("1", "Chapter 1: Introduction", "1"),
        ("1.1", "Poultry Farming Sector Background & Global Economic Impact", "1"),
        ("1.2", "Avian Enteric Pathologies: Epidemiology, Etiology & Clinical Signs", "3"),
        ("1.3", "Veterinary Machine Learning: Paradigms, Substrates, and Edge Constraints", "6"),
        ("1.4", "Problem Statement and Vulnerabilities of Existing Computer Vision Frameworks", "8"),
        ("1.5", "Research Objectives (Primary Algorithmic & Secondary Engineering Goals)", "9"),
        ("1.6", "Scope, Operational Assumptions, and Delimitations of the Work", "10"),
        ("1.7", "Organization and Structural Roadmap of the Project Report", "11"),
        ("2", "Chapter 2: Requirement Specification & Literature Survey", "13"),
        ("2.1", "Comprehensive Survey of Existing Computer Vision Frameworks in Poultry Health", "13"),
        ("2.2", "Critical Research Gaps in Contemporary Poultry Health AI Systems", "16"),
        ("2.3", "Hardware and Software Environment Specifications (Development & Edge Stack)", "18"),
        ("2.4", "Functional Requirements Specification (FR-01 through FR-10)", "20"),
        ("2.5", "Non-Functional Requirements Specification (NFR-01 through NFR-08)", "22"),
        ("2.6", "Data Flow Modeling (Level 0 Context, Level 1 Subsystem, Level 2 Process Flow)", "24"),
        ("2.7", "Dataset Specifications, Class Taxonomies, and Substrate Confounding Audit", "27"),
        ("3", "Chapter 3: System Design & Methodology", "30"),
        ("3.1", "Overall System Architecture and Modular Engineering Blueprint", "30"),
        ("3.2", "Classical Multi-Scale Feature Engineering Formulation (Color, GLCM, LBP, Haar)", "32"),
        ("3.3", "Deep Convolutional Neural Transfer Learning Architectures & Model Backbones", "36"),
        ("3.4", "Loss Formulations for Extreme Class Imbalance (Weighted CE & Focal Loss)", "39"),
        ("3.5", "Post-Hoc Uncertainty Calibration via Temperature Scaling Formulation", "42"),
        ("3.6", "Out-of-Distribution Gating & Anomaly Scoring (MSP, Energy Score, Mahalanobis)", "45"),
        ("3.7", "Visual Explainability & Spatial Attribution Auditing (Grad-CAM & Pointing Game)", "48"),
        ("3.8", "Unified Modeling Language (UML) Structural Models (Use Case & Class Diagrams)", "51"),
        ("3.9", "Rigorous Statistical Auditing & Hypothesis Testing Framework (McNemar & Bootstrap)", "54"),
        ("4", "Chapter 4: System Implementation & Detailed Source Code", "56"),
        ("4.1", "System Configuration and Hardware Paths (src/config.py)", "56"),
        ("4.2", "PyTorch Dataset Ingestion, Augmentation & Stratification (src/data.py)", "59"),
        ("4.3", "Perceptual Hashing & Connected-Component Partitioning (src/dedup.py)", "64"),
        ("4.4", "Neural Model Architectures & Deep Feature Extraction Heads (src/model.py)", "68"),
        ("4.5", "Class-Weighted Cross-Entropy, Focal, and Composite Losses (src/losses.py)", "71"),
        ("4.6", "Reproducible Neural Training Engine & Early Stopping Loop (src/train.py)", "74"),
        ("4.7", "Transfer Learning, Layer Freezing & Fine-Tuning Pipeline (src/train_transfer.py)", "79"),
        ("4.8", "Statistical Evaluation Loop & Multi-Class Metric Profiling (src/evaluate.py)", "87"),
        ("4.9", "Temperature Scaling Uncertainty Calibration Engine (src/calibrate.py)", "92"),
        ("4.10", "Out-of-Distribution Rejection Gating & Energy Scoring (src/ood.py)", "97"),
        ("4.11", "Gradient-Weighted Class Activation Mapping (Grad-CAM) (src/gradcam.py)", "104"),
        ("4.12", "Classical Feature Engineering: GLCM, LBP, Color & SVM Baselines (src/baseline_ml.py)", "109"),
        ("4.13", "Multimodal Feature Fusion Architecture (src/multimodal_model.py)", "116"),
        ("4.14", "Tabular Sensor Data Processing & Environmental Ingestion (src/multimodal_data.py)", "119"),
        ("4.15", "Multimodal Joint Optimization Training Pipeline (src/train_multimodal.py)", "122"),
        ("4.16", "Dual-Output ONNX Runtime Export & INT8 Dynamic Quantization (src/export.py)", "125"),
        ("4.17", "Core Logging, System Checkpointing & Utilities (src/utils.py)", "130"),
        ("4.18", "Interactive Streamlit Web Dashboard & Live Inference Engine (app/streamlit_app.py)", "132"),
        ("4.19", "Substrate Confounding Discovery & Spatial Pointing Game (scripts/audit_classical_substrate.py)", "141"),
        ("4.20", "Substrate Stress Testing & Domain Shift Evaluation (scripts/evaluate_substrate_stress_test.py)", "146"),
        ("5", "Chapter 5: Testing & Experimental Verification", "151"),
        ("5.1", "Comprehensive Formal Test Plan, Strategy & Test Case Specifications (TC-01 - TC-16)", "151"),
        ("5.2", "Empirical Evaluation 1: Deep Learning vs Classical Baselines Benchmark Comparison", "154"),
        ("5.3", "Empirical Evaluation 2: Impact of Leak-Free Deduplication on Real Generalization", "160"),
        ("5.4", "Empirical Evaluation 3: Substrate Stress Testing & Bedding Invariance Analysis", "162"),
        ("5.5", "Empirical Evaluation 4: Uncertainty Calibration Performance & Reliability Diagrams", "165"),
        ("5.6", "Empirical Evaluation 5: Out-of-Distribution Gating Benchmark & ROC Analysis", "168"),
        ("5.7", "Empirical Evaluation 6: Explainability Localization Audit & Spatial Pointing Game", "171"),
        ("5.8", "Empirical Evaluation 7: Hardware Latency Profiling & Edge Quantization Benchmarks", "175"),
        ("5.9", "Empirical Evaluation 8: Interactive Streamlit Web Application Demonstration", "178"),
        ("6", "Chapter 6: Conclusion, Limitations & Future Scope", "182"),
        ("6.1", "Executive Summary of Technical Accomplishments & Contributions", "182"),
        ("6.2", "Detailed Discussion of Operational Limitations (The 10 Pillars of Constraints)", "183"),
        ("6.3", "Agricultural, Animal Welfare, and Environmental Biosecurity Impact", "185"),
        ("6.4", "Guidance for Poultry Farm Practitioners and Veterinary Technicians", "186"),
        ("6.5", "Future Algorithmic Enhancements & Edge TPU Deployment Roadmap", "187"),
        ("7", "Chapter 7: Bibliography & References", "189"),
        ("App A", "Appendix A: Complete System Installation, Package Dependencies & CLI Manual", "193"),
        ("App B", "Appendix B: Dataset Manifest Catalogs & Biosecurity SOP Dossiers", "195"),
        ("App C", "Appendix C: Mathematical Proofs & Theoretical Derivations", "197")
    ]

    doc.add_page_break()
    p_toc_title = doc.add_paragraph()
    p_toc_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc_title.paragraph_format.space_before = Pt(8)
    p_toc_title.paragraph_format.space_after = Pt(14)
    r_tt = p_toc_title.add_run("TABLE OF CONTENTS")
    r_tt.font.name = 'Times New Roman'
    r_tt.font.size = Pt(16)
    r_tt.font.bold = True
    make_styled_table(doc, ["Index", "Section / Chapter Title", "Page"], all_toc, [0.85, 5.35, 0.7], alignments=['C', 'L', 'C'], font_size=9.5, cell_pad=(70, 70))

    # PAGES 9, 10 (ix, x): LIST OF FIGURES
    figs_data = [
        ("Figure 1.1", "Diagnostic Class Distribution Across Evaluated Avian Fecal Dataset (6,432 Samples)", "Chapter 1 / 1.2", "4"),
        ("Figure 1.2", "Distribution of Raw Photographic Resolutions and Aspect Ratios", "Chapter 1 / 1.2", "4"),
        ("Figure 1.3", "Composite 4x5 Visual Sample Gallery Across All Four Diagnostic Classes", "Chapter 1 / 1.2", "5"),
        ("Figure 1.4", "Clinical Photographic Gallery: Avian Coccidiosis Fecal Droppings with Mucus/Blood", "Chapter 1 / 1.2", "5"),
        ("Figure 1.5", "Clinical Photographic Gallery: Normal Avian Fecal Droppings with White Uric Acid Caps", "Chapter 1 / 1.2", "5"),
        ("Figure 1.6", "Clinical Photographic Gallery: Newcastle Disease Fecal Droppings with Green Bile", "Chapter 1 / 1.2", "6"),
        ("Figure 1.7", "Clinical Photographic Gallery: Salmonella Fecal Droppings with Chalky White Diarrhea", "Chapter 1 / 1.2", "6"),
        ("Figure 1.8", "Channel-Wise Mean Color Histograms across RGB Channels for All Four Classes", "Chapter 1 / 1.2", "7"),
        ("Figure 2.1", "Level 0 Context Data Flow Diagram (DFD) for Avian Diagnostic Edge System", "Chapter 2 / 2.6", "24"),
        ("Figure 2.2", "Level 1 Functional Data Flow Diagram (DFD) Decomposing Subsystem Interactions", "Chapter 2 / 2.6", "25"),
        ("Figure 2.3", "Level 2 Detailed Process Flow Diagram: Ingestion, Feature Extraction & Inference", "Chapter 2 / 2.6", "26"),
        ("Figure 2.4", "Field Substrate Diversity Grid: Wood Shavings, Straw, Sand, Concrete, Wire Cages", "Chapter 2 / 2.7", "28"),
        ("Figure 2.5", "Substrate Cluster Cross-Tabulation Matrix Highlighting Background Confounding", "Chapter 2 / 2.7", "29"),
        ("Figure 3.1", "Complete End-to-End System Process Pipeline Architecture from Ingestion to XAI", "Chapter 3 / 3.1", "31"),
        ("Figure 3.2", "Unified Modeling Language (UML) Use Case Diagram: Actors & System Interactions", "Chapter 3 / 3.8", "52"),
        ("Figure 3.3", "Unified Modeling Language (UML) Class Diagram: Preprocessing, Models, OOD & Audit", "Chapter 3 / 3.8", "53"),
        ("Figure 4.1", "Preprocessed Training Batch Preview Demonstrating Dynamic Geometric Augmentations", "Chapter 4 / 4.2", "63"),
        ("Figure 5.1", "Baseline CNN Training and Validation Convergence Dynamics (Loss & Accuracy)", "Chapter 5 / 5.2", "155"),
        ("Figure 5.2", "MobileNetV2 Optimization Dynamics under Class-Weighted Cross-Entropy Loss", "Chapter 5 / 5.2", "156"),
        ("Figure 5.3", "EfficientNet-B0 Optimization Dynamics under Class-Weighted Cross-Entropy Loss", "Chapter 5 / 5.2", "156"),
        ("Figure 5.4", "EfficientNet-B0 Optimization Dynamics under Multi-Class Focal Loss Formulation", "Chapter 5 / 5.2", "157"),
        ("Figure 5.5", "ResNet-50 Optimization Dynamics under Class-Weighted Cross-Entropy Loss", "Chapter 5 / 5.2", "157"),
        ("Figure 5.6", "Test Set Confusion Matrix for Primary Deep Classifier (EfficientNet-B0)", "Chapter 5 / 5.2", "158"),
        ("Figure 5.7", "Test Set Confusion Matrix for Best Classical Baseline Classifier (SVM RBF)", "Chapter 5 / 5.2", "158"),
        ("Figure 5.8", "One-vs-Rest Receiver Operating Characteristic (ROC) Curves Across Diagnostic Classes", "Chapter 5 / 5.2", "159"),
        ("Figure 5.9", "Reliability Diagrams and Calibration Curves Before and After Temperature Scaling", "Chapter 5 / 5.5", "166"),
        ("Figure 5.10", "Grad-CAM Saliency Composite Grid on Representative Evaluated Validation Samples", "Chapter 5 / 5.7", "172"),
        ("Figure 5.11", "Grad-CAM Explainability Gallery on Hard Subsets and Confounded Backgrounds", "Chapter 5 / 5.7", "173"),
        ("Figure 5.12", "Classical Feature Attribution via SHAP Global Summary Plot (410-d Extractor)", "Chapter 5 / 5.7", "174"),
        ("Figure 5.13", "Spatially Constrained Feature Attribution via SHAP on Center-Cropped Fecal Patches", "Chapter 5 / 5.7", "174"),
        ("Figure 5.14", "Receiver Operating Characteristic (ROC) Curves for Out-of-Distribution Gating", "Chapter 5 / 5.6", "169"),
        ("Figure 5.15", "Free Energy Score Distribution for In-Distribution vs Out-of-Distribution Datasets", "Chapter 5 / 5.6", "170"),
        ("Figure 5.16", "Deep Feature Cosine Distance Distribution Across Evaluated Image Domains", "Chapter 5 / 5.6", "170")
    ]
    
    doc.add_page_break()
    p_lof_title = doc.add_paragraph()
    p_lof_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lof_title.paragraph_format.space_before = Pt(8)
    p_lof_title.paragraph_format.space_after = Pt(14)
    r_lft = p_lof_title.add_run("LIST OF FIGURES")
    r_lft.font.name = 'Times New Roman'
    r_lft.font.size = Pt(16)
    r_lft.font.bold = True
    make_styled_table(doc, ["Figure No.", "Figure Caption / Description", "Chapter / Section", "Page"], figs_data, [1.0, 4.3, 1.1, 0.5], alignments=['C', 'L', 'C', 'C'], font_size=9.0, cell_pad=(60, 60))

    # PAGE 11 (xi): LIST OF TABLES
    tables_data = [
        ("Table 2.1", "Comprehensive Comparative Literature Survey in Veterinary Computer Vision", "Chapter 2 / 2.1", "15"),
        ("Table 2.2", "Detailed Hardware and Software Engineering Development Specifications", "Chapter 2 / 2.3", "19"),
        ("Table 2.3", "Functional Requirements Specification Matrix (FR-01 through FR-10)", "Chapter 2 / 2.4", "21"),
        ("Table 2.4", "Non-Functional Requirements Specification Matrix (NFR-01 through NFR-08)", "Chapter 2 / 2.5", "23"),
        ("Table 2.5", "Dataset Class Distribution, Partition Counts, and Class Imbalance Weighting", "Chapter 2 / 2.7", "27"),
        ("Table 3.1", "Hyperparameter Configuration Matrix Across Evaluated Neural Backbones", "Chapter 3 / 3.3", "38"),
        ("Table 3.2", "Multi-Scale Classical Feature Extraction Vector Decomposition (410 Dimensions)", "Chapter 3 / 3.2", "34"),
        ("Table 5.1", "Comprehensive Formal System Test Plan and Verification Matrix (TC-01 - TC-16)", "Chapter 5 / 5.1", "152"),
        ("Table 5.2", "Master Diagnostic Benchmark Comparison: Deep Learning vs Classical Baselines", "Chapter 5 / 5.2", "154"),
        ("Table 5.3", "Normalized Confusion Matrix Breakdown for Primary Classifier (EfficientNet-B0)", "Chapter 5 / 5.2", "159"),
        ("Table 5.4", "Per-Class Diagnostic Performance Metrics (Sensitivity, Specificity, PPV, NPV)", "Chapter 5 / 5.2", "160"),
        ("Table 5.5", "Impact of Leak-Free Deduplication on Model Generalization and Accuracy", "Chapter 5 / 5.3", "161"),
        ("Table 5.6", "Bedding Substrate Stress-Testing Evaluation Across Diverse Floor Materials", "Chapter 5 / 5.4", "163"),
        ("Table 5.7", "Uncertainty Calibration Metric Progression (ECE, NLL, Brier Score)", "Chapter 5 / 5.5", "167"),
        ("Table 5.8", "Out-of-Distribution Gating Benchmark Across Diverse In-the-Wild Debris", "Chapter 5 / 5.6", "169"),
        ("Table 5.9", "Spatial Attribution Energy Ratio (Central 70% vs Outer 15% Background)", "Chapter 5 / 5.7", "173"),
        ("Table 5.10", "Hardware Latency Profiling, Parameter Footprints, and Dynamic INT8 Quantization", "Chapter 5 / 5.8", "176")
    ]
    
    doc.add_page_break()
    p_lot_title = doc.add_paragraph()
    p_lot_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lot_title.paragraph_format.space_before = Pt(8)
    p_lot_title.paragraph_format.space_after = Pt(14)
    r_ltt = p_lot_title.add_run("LIST OF TABLES")
    r_ltt.font.name = 'Times New Roman'
    r_ltt.font.size = Pt(16)
    r_ltt.font.bold = True
    make_styled_table(doc, ["Table No.", "Table Caption / Description", "Chapter / Section", "Page"], tables_data, [1.0, 4.3, 1.1, 0.5], alignments=['C', 'L', 'C', 'C'], font_size=9.0, cell_pad=(60, 60))

    # PAGE 12 (xii): LIST OF ABBREVIATIONS & ACRONYMS
    abbreviations_data = [
        ("AI", "Artificial Intelligence", "ND", "Newcastle Disease"),
        ("API", "Application Programming Interface", "NLL", "Negative Log-Likelihood"),
        ("AUROC", "Area Under Receiver Operating Characteristic", "OOD", "Out-of-Distribution"),
        ("BCA", "Bachelor of Computer Applications", "ONNX", "Open Neural Network Exchange"),
        ("CAM", "Class Activation Mapping", "PPV", "Positive Predictive Value (Precision)"),
        ("CNN", "Convolutional Neural Network", "pHash", "Perceptual Hash"),
        ("CPU", "Central Processing Unit", "QWK", "Quadratic Weighted Kappa"),
        ("DFD", "Data Flow Diagram", "RBF", "Radial Basis Function"),
        ("dHash", "Difference Hash", "ROC", "Receiver Operating Characteristic"),
        ("ECE", "Expected Calibration Error", "SHAP", "Shapley Additive Explanations"),
        ("FAO", "Food and Agriculture Organization", "SOP", "Standard Operating Procedure"),
        ("FPR", "False Positive Rate", "SVM", "Support Vector Machine"),
        ("GLCM", "Gray-Level Co-occurrence Matrix", "TPR", "True Positive Rate (Recall)"),
        ("GPU", "Graphics Processing Unit", "UML", "Unified Modeling Language"),
        ("HSV", "Hue Saturation Value", "WHO", "World Health Organization"),
        ("LBP", "Local Binary Patterns", "XAI", "Explainable Artificial Intelligence")
    ]
    
    doc.add_page_break()
    p_abb_title = doc.add_paragraph()
    p_abb_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abb_title.paragraph_format.space_before = Pt(6)
    p_abb_title.paragraph_format.space_after = Pt(8)
    r_abt = p_abb_title.add_run("LIST OF ABBREVIATIONS & ACRONYMS")
    r_abt.font.name = 'Times New Roman'
    r_abt.font.size = Pt(16)
    r_abt.font.bold = True
    make_styled_table(doc, ["Acronym", "Full Form", "Acronym", "Full Form"], abbreviations_data, [0.85, 2.6, 0.85, 2.6], alignments=['L', 'L', 'L', 'L'], bold_cols=[0, 2], font_size=9.2, cell_pad=(14, 14))

    # =========================================================================
    # SECTION 3: MAIN REPORT BODY (CHAPTER 1 - 7, APPENDICES)
    # =========================================================================
    print("Building Section 3: Main Chapters (Chapter 1 - 7, Appendices)...")
    sec3 = doc.add_section()
    sec3.top_margin = Inches(1.0)
    sec3.bottom_margin = Inches(1.0)
    sec3.left_margin = Inches(1.25)     # 1.25" Binding margin
    sec3.right_margin = Inches(1.0)
    sec3.page_width = Inches(8.27)
    sec3.page_height = Inches(11.69)
    sec3.different_first_page_header_footer = False
    
    # Restart page numbering at 1 (Arabic numerals)
    sectPr3 = sec3._sectPr
    pgNumType3 = OxmlElement('w:pgNumType')
    pgNumType3.set(qn('w:start'), '1')
    sectPr3.append(pgNumType3)
    
    # Header: Running Title
    header3 = sec3.header
    header3.is_linked_to_previous = False
    hp = header3.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hrun = hp.add_run("KUKUGUARD | ENTERIC PATHOLOGY AUDIT")
    hrun.font.name = 'Times New Roman'
    hrun.font.size = Pt(8.5)
    hrun.font.color.rgb = COLOR_MUTED
    
    # Footer: College and Dynamic Page Number
    footer3 = sec3.footer
    footer3.is_linked_to_previous = False
    fp3 = footer3.paragraphs[0]
    fp3.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    frun1 = fp3.add_run("DR. NSAM FIRST GRADE COLLEGE, NITTE\\t\\tPage | ")
    frun1.font.name = 'Times New Roman'
    frun1.font.size = Pt(9.5)
    frun1.font.color.rgb = COLOR_MUTED
    
    frun_page3 = fp3.add_run()
    fld1_3 = OxmlElement('w:fldChar')
    fld1_3.set(qn('w:fldCharType'), 'begin')
    instr_3 = OxmlElement('w:instrText')
    instr_3.set(qn('xml:space'), 'preserve')
    instr_3.text = "PAGE"
    fld2_3 = OxmlElement('w:fldChar')
    fld2_3.set(qn('w:fldCharType'), 'separate')
    fld3_3 = OxmlElement('w:fldChar')
    fld3_3.set(qn('w:fldCharType'), 'end')
    frun_page3._r.extend([fld1_3, instr_3, fld2_3, fld3_3])
    frun_page3.font.name = 'Times New Roman'
    frun_page3.font.size = Pt(9.5)
    frun_page3.font.bold = True

    # Helper formatters for body matching Crop exactly
    def add_ch_heading(ch_num, title):
        if ch_num > 1:
            doc.add_page_break()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        r1 = p.add_run(f"CHAPTER {ch_num}\\n")
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(16)
        r1.font.bold = True
        r2 = p.add_run(title.upper())
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(16)
        r2.font.bold = True
        
        p_div = doc.add_paragraph()
        p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_div.paragraph_format.space_after = Pt(16)
        r_div = p_div.add_run("____________________________________________________")
        r_div.font.color.rgb = RGBColor(120, 120, 120)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13.5)
        r.font.bold = True
        r.font.color.rgb = COLOR_TEXT_MAIN
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.font.bold = True
        return p

    def add_p(text):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        return p

    def add_callout(title, text):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        cell.width = Inches(6.0)
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(r'<w:shd {} w:fill="F1F5F9"/>'.format(nsdecls('w')))
        tcPr.append(shd)
        
        borders = parse_xml(r"""
            <w:tcBorders {} >
                <w:top w:val="none"/>
                <w:left w:val="single" w:sz="24" w:space="0" w:color="0F172A"/>
                <w:bottom w:val="none"/>
                <w:right w:val="none"/>
            </w:tcBorders>
        """.format(nsdecls('w')))
        tcPr.append(borders)
        
        cp = cell.paragraphs[0]
        cp.paragraph_format.space_before = Pt(4)
        cp.paragraph_format.space_after = Pt(2)
        r_t = cp.add_run(f"RESEARCH AUDIT INSIGHT: {title}\\n")
        r_t.font.name = 'Times New Roman'
        r_t.font.size = Pt(11)
        r_t.font.bold = True
        r_t.font.color.rgb = COLOR_TEXT_MAIN
        
        r_b = cp.add_run(text)
        r_b.font.name = 'Times New Roman'
        r_b.font.size = Pt(10.5)
        r_b.font.italic = True
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    def add_fig(img_path, caption_text, width=Inches(5.4)):
        if os.path.exists(img_path):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            run = p.add_run()
            run.add_picture(img_path, width=width)
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(2)
            p_cap.paragraph_format.space_after = Pt(8)
            p_cap.paragraph_format.keep_with_next = False
            r_cap = p_cap.add_run(caption_text)
            r_cap.font.name = 'Times New Roman'
            r_cap.font.size = Pt(9.5)
            r_cap.font.italic = True
            r_cap.font.color.rgb = COLOR_MUTED

    def add_code_block(title, code_str):
        p_cap = doc.add_paragraph()
        p_cap.paragraph_format.space_before = Pt(8)
        p_cap.paragraph_format.space_after = Pt(2)
        p_cap.paragraph_format.keep_with_next = True
        prefix = "" if (title.startswith("Figure ") or title.startswith("Listing ")) else "Listing: "
        r_cap = p_cap.add_run(f"{prefix}{title}")
        r_cap.font.name = 'Times New Roman'
        r_cap.font.size = Pt(9.5)
        r_cap.font.bold = True
        
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        cell.width = Inches(6.0)
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(r'<w:shd {} w:fill="F8FAFC"/>'.format(nsdecls('w')))
        tcPr.append(shd)
        
        borders = parse_xml(r"""
            <w:tcBorders {} >
                <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
                <w:left w:val="single" w:sz="18" w:space="0" w:color="0F172A"/>
                <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
                <w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
            </w:tcBorders>
        """.format(nsdecls('w')))
        tcPr.append(borders)
        
        tcMar = parse_xml(r"""
            <w:tcMar {} >
                <w:top w:w="120" w:type="dxa"/>
                <w:left w:w="160" w:type="dxa"/>
                <w:bottom w:w="120" w:type="dxa"/>
                <w:right w:w="140" w:type="dxa"/>
            </w:tcMar>
        """.format(nsdecls('w')))
        tcPr.append(tcMar)
        
        cp = cell.paragraphs[0]
        cp.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        cp.paragraph_format.line_spacing = 1.0
        cp.paragraph_format.space_before = Pt(4)
        cp.paragraph_format.space_after = Pt(4)
        
        clean_code = code_str.strip()
        r_code = cp.add_run(clean_code)
        r_code.font.name = 'Consolas'
        r_code.font.size = Pt(8.5)
        r_code.font.color.rgb = RGBColor(30, 41, 59)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)
''')
print("Part 2 written.")
