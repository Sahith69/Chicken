import os
import sys

crop_script_path = "/home/sahith/Projects/Crop/project_report/build_project_report.py"
chick_script_path = "/home/sahith/Projects/Chicken/project_report/build_comprehensive_100page_report.py"
target_script_path = "/home/sahith/Projects/Chicken/project_report/build_exact_crop_style_report.py"

with open(crop_script_path, "r", encoding="utf-8") as f:
    crop_lines = f.readlines()

with open(chick_script_path, "r", encoding="utf-8") as f:
    chick_lines = f.readlines()

out_lines = []

out_lines.append('#!/usr/bin/env python3.14\n')
out_lines.append('"""\n')
out_lines.append('EXACT CROP-FORMAT REPLICATION FOR KUKUGUARD PROJECT REPORT\n')
out_lines.append('===============================================================================\n')
out_lines.append('Project Title: KUKUGUARD: AN EDGE-COMPUTING COMPUTER VISION SYSTEM FOR\n')
out_lines.append('               AVIAN ENTERIC PATHOLOGY SCREENING VIA DIFFERENTIAL FECAL\n')
out_lines.append('               MORPHOLOGY, SHORTCUT-RESISTANT FEATURE ENGINEERING, AND\n')
out_lines.append('               UNCERTAINTY-CALIBRATED NEURAL DIAGNOSTICS\n')
out_lines.append('Candidate:     Mr. SHAMANTH (Register Number: NNS24BC070)\n')
out_lines.append('Class:         III BCA \'B\' (Academic Period: 2024–2027)\n')
out_lines.append('Institution:   Department of Computer Science,\n')
out_lines.append('               Dr. NSAM First Grade College, Nitte (Deemed to be University)\n')
out_lines.append('Guides:        Mr. Bharath S. Bhat (HOD & Assistant Professor Gd-II)\n')
out_lines.append('               Mr. Srujan U. Shetty (Assistant Professor)\n')
out_lines.append('===============================================================================\n')
out_lines.append('"""\n\n')

# Standard imports
imports_block = '''import os
import sys
import subprocess
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

PROJECT_DIR = "/home/sahith/Projects/Chicken"
REPORT_DIR = os.path.join(PROJECT_DIR, "project_report")
FIGURES_DIR = os.path.join(PROJECT_DIR, "reports", "figures")
LOGO_PATH = os.path.join(REPORT_DIR, "nitte_nsam_logo.png")
OUTPUT_DOCX = os.path.join(REPORT_DIR, "Chicken_Disease_AI_Project_Report.docx")
OUTPUT_PDF = os.path.join(REPORT_DIR, "Chicken_Disease_AI_Project_Report.pdf")

COLOR_NAVY_HEX = "0F172A"       # Tailwind Slate 900
COLOR_BORDER_HEX = "CBD5E1"     # Tailwind Slate 300
COLOR_ROW_ALT_HEX = "F8FAFC"    # Tailwind Slate 50
COLOR_TEXT_MAIN = RGBColor(15, 23, 42)
COLOR_MUTED = RGBColor(71, 85, 105)
'''
out_lines.append(imports_block)

# Copy Crop lines 38 to 169 (helpers: get_code, set_cell_background, set_cell_margins, set_table_borders, make_styled_table, build_master_report setup)
out_lines.extend(crop_lines[38:169])

# Cover page from Crop (lines 169 to 286) with Chicken title and Shamanth:
for line in crop_lines[169:286]:
    if 'DEEP LEARNING FOR CROP' in line:
        out_lines.append('    r_title = p_title.add_run("KUKUGUARD: AN EDGE-COMPUTING COMPUTER VISION SYSTEM FOR\\nAVIAN ENTERIC PATHOLOGY SCREENING VIA DIFFERENTIAL FECAL\\nMORPHOLOGY, SHORTCUT-RESISTANT FEATURE ENGINEERING,\\nAND UNCERTAINTY-CALIBRATED NEURAL DIAGNOSTICS")\n')
    elif 'SEVERITY GRADING UNDER' in line or 'EVALUATION: RESULTS' in line:
        continue # replaced above
    elif 'Mr. SAHITH R' in line:
        out_lines.append('    r_by2 = p_sub_by.add_run("Mr. SHAMANTH\\n")\n')
    elif 'Sahith R' in line:
        out_lines.append(line.replace('Sahith R', 'Shamanth'))
    elif 'SAHITH R' in line:
        out_lines.append(line.replace('SAHITH R', 'SHAMANTH'))
    else:
        out_lines.append(line)

# Section 2 Init (lines 286 to 323)
out_lines.extend(crop_lines[286:323])

# Certificate (lines 323 to 425) with Chicken title and Shamanth:
for line in crop_lines[323:425]:
    if 'DEEP LEARNING FOR CROP' in line:
        out_lines.append('    r_pname = p_c1.add_run(\'"KUKUGUARD: AN EDGE-COMPUTING COMPUTER VISION SYSTEM FOR AVIAN ENTERIC PATHOLOGY SCREENING VIA DIFFERENTIAL FECAL MORPHOLOGY, SHORTCUT-RESISTANT FEATURE ENGINEERING, AND UNCERTAINTY-CALIBRATED NEURAL DIAGNOSTICS"\')\n')
    elif 'Sahith R' in line:
        out_lines.append(line.replace('Sahith R', 'Shamanth'))
    elif 'SAHITH R' in line:
        out_lines.append(line.replace('SAHITH R', 'SHAMANTH'))
    else:
        out_lines.append(line)

# Declaration (lines 425 to 485) with Chicken title and Shamanth:
for line in crop_lines[425:485]:
    if 'DEEP LEARNING FOR CROP' in line:
        out_lines.append('    p_d1.add_run(\'"KUKUGUARD: AN EDGE-COMPUTING COMPUTER VISION SYSTEM FOR AVIAN ENTERIC PATHOLOGY SCREENING VIA DIFFERENTIAL FECAL MORPHOLOGY, SHORTCUT-RESISTANT FEATURE ENGINEERING, AND UNCERTAINTY-CALIBRATED NEURAL DIAGNOSTICS"\').font.bold = True\n')
    elif 'Sahith R' in line:
        out_lines.append(line.replace('Sahith R', 'Shamanth'))
    elif 'SAHITH R' in line:
        out_lines.append(line.replace('SAHITH R', 'SHAMANTH'))
    else:
        out_lines.append(line)

# Acknowledgment (lines 485 to 543) adapted to Chicken & Shamanth:
for line in crop_lines[485:543]:
    if 'crop disease AI auditing' in line:
        out_lines.append(line.replace('crop disease AI auditing', 'avian enteric pathology AI diagnostic'))
    elif 'Paddy Doctor benchmark' in line:
        out_lines.append('        "I am deeply grateful to the open-source contributors of the Tanzanian poultry pathology benchmark and the veterinary research community who generously shared field photographic registries, biological insights, and clinical standards.",\n')
    elif 'Sahith R' in line:
        out_lines.append(line.replace('Sahith R', 'Shamanth'))
    elif 'SAHITH R' in line:
        out_lines.append(line.replace('SAHITH R', 'SHAMANTH'))
    else:
        out_lines.append(line)

# Abstract (lines 543 to 623) adapted to Chicken:
abstract_chicken = '''
    # PAGE 5 (v): ABSTRACT
    doc.add_page_break()
    p_abs_title = doc.add_paragraph()
    p_abs_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abs_title.paragraph_format.space_before = Pt(8)
    p_abs_title.paragraph_format.space_after = Pt(16)
    r_abt = p_abs_title.add_run("ABSTRACT")
    r_abt.font.name = 'Times New Roman'
    r_abt.font.size = Pt(16)
    r_abt.font.bold = True
    
    abs_p1 = (
        "Enteric avian infections—most notably Coccidiosis, Salmonella (pullorum/typhimurium), and velogenic Newcastle Disease (ND)—represent "
        "existential threats to global commercial poultry production, generating annual direct losses exceeding $3 billion worldwide. While modern deep "
        "convolutional neural networks have shown high nominal classification accuracies on public datasets, standard models suffer from catastrophic "
        "vulnerabilities in real-world farm deployment: (1) data leakage between train and test splits due to near-duplicate frame captures; (2) shortcut "
        "learning where networks anchor to bedding substrates (wood shavings, straw, sand, wire mesh) rather than pathological fecal lesions; (3) pathological "
        "overconfidence on out-of-distribution (OOD) farm debris; and (4) excessive computational latency exceeding edge hardware budgets."
    )
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(abs_p1)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11.5)
    
    abs_p2 = (
        "This project presents KukuGuard, a production-grade, edge-computing diagnostic computer vision framework engineered specifically to resolve "
        "these vulnerabilities. First, we flatten and audit the raw photographic dataset using difference hashing (dHash) and graph connected-component "
        "partitioning, establishing an audited, leakage-free 70/15/15 split across 6,432 high-resolution images. Second, we engineer a 410-dimensional "
        "classical feature extraction pipeline combining multi-color-space histograms (RGB, HSV, Lab), Gray-Level Co-occurrence Matrix (GLCM) second-order "
        "statistics, Local Binary Patterns (LBP), and Haar wavelets. When evaluated with Support Vector Machines (RBF kernel), this classical baseline "
        "achieves 94.67% macro F1 while demonstrating complete statistical immunity to substrate confounding."
    )
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(abs_p2)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11.5)
    
    abs_p3 = (
        "Across deep transfer learning backbones, EfficientNet-B0 achieves superior diagnostic performance (96.48% macro F1, 99.4% ROC-AUC), while "
        "MobileNetV2 provides ultra-lightweight inference (93.18% macro F1, 2.2M parameters). Class-weighted Cross-Entropy and Focal Loss formulations are "
        "compared, uncovering a critical epidemiological trade-off: Focal Loss boosts Newcastle Disease sensitivity to 77.8% (vital for early quarantine), "
        "whereas Weighted Cross-Entropy achieves balanced overall recall. Post-hoc temperature scaling calibrates model confidence, reducing Expected "
        "Calibration Error (ECE) from 0.089 to 0.021. Dual OOD gating combining Free Energy Scoring with deep feature cosine distance reliably rejects "
        "non-fecal farm debris (98.9% AUROC). Finally, the entire pipeline is exported to dual-output ONNX and dynamic INT8 quantization, achieving "
        "27.2 ms edge latency on a quad-core CPU, and served via an interactive Streamlit application with live Grad-CAM visual explainability."
    )
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(abs_p3)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11.5)
    
    p_kw = doc.add_paragraph()
    p_kw.paragraph_format.line_spacing = 1.3
    p_kw.paragraph_format.space_after = Pt(0)
    p_kw.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r_kwh = p_kw.add_run("Keywords: ")
    r_kwh.font.name = 'Times New Roman'
    r_kwh.font.size = Pt(11.5)
    r_kwh.font.bold = True
    r_kwt = p_kw.add_run("Avian Enteric Pathology, Computer Vision, Coccidiosis, Newcastle Disease, Salmonella, Split-Leakage Audit, Shortcut Learning, Temperature Scaling, Out-of-Distribution Gating, Explainable AI, Edge Deployment.")
    r_kwt.font.name = 'Times New Roman'
    r_kwt.font.size = Pt(11.5)
'''
out_lines.append(abstract_chicken)

# TOC, List of Figures, List of Tables, List of Abbreviations:
# lines 499 to 705 from Chicken's build_comprehensive_100page_report.py
for line in chick_lines[499:705]:
    out_lines.append(line)

# Section 3 Setup and helper formatters from Crop (lines 814 to 1096):
for line in crop_lines[814:1096]:
    if 'CROP DISEASE AI | LEAKAGE-CONTROLLED EVALUATION' in line:
        out_lines.append('    hrun = hp.add_run("KUKUGUARD | ENTERIC PATHOLOGY AUDIT")\n')
    else:
        out_lines.append(line)

# Chicken Chapters 1 to 7 and Appendices:
out_lines.extend(chick_lines[926:])

with open(target_script_path, "w", encoding="utf-8") as f:
    f.writelines(out_lines)

print(f"Master script successfully written to {target_script_path} ({len(out_lines)} lines)!")
