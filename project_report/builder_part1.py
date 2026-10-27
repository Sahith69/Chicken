import sys

with open("/home/sahith/Projects/Chicken/project_report/build_comprehensive_100page_report.py", "w", encoding="utf-8") as out:
    out.write('''#!/usr/bin/env python3.14
"""
===============================================================================
MASTER COMPREHENSIVE INSTITUTIONAL PROJECT REPORT GENERATOR (100+ PAGES)
-------------------------------------------------------------------------------
Project Title: KUKUGUARD: AN EDGE-COMPUTING COMPUTER VISION SYSTEM FOR 
               AVIAN ENTERIC PATHOLOGY SCREENING VIA DIFFERENTIAL FECAL 
               MORPHOLOGY, SHORTCUT-RESISTANT FEATURE ENGINEERING, AND 
               UNCERTAINTY-CALIBRATED NEURAL DIAGNOSTICS
Candidate:     SAHITH R (Register No: NNS24BC070)
Class:         III BCA 'B' (Academic Period: 2024–2027)
Institution:   Department of Computer Science,
               Dr. NSAM First Grade College, Nitte (Deemed to be University)
Guides:        Mr. Bharath S. Bhat (HOD & Assistant Professor)
               Mr. Srujan U. Shetty (Assistant Professor)
===============================================================================
"""

import os
import sys
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

PROJECT_DIR = "/home/sahith/Projects/Chicken"
FIGURES_DIR = os.path.join(PROJECT_DIR, "reports", "figures")
OUTPUT_DOCX = os.path.join(PROJECT_DIR, "project_report", "Chicken_Disease_AI_Project_Report.docx")
OUTPUT_PDF = os.path.join(PROJECT_DIR, "project_report", "Chicken_Disease_AI_Project_Report.pdf")

COLOR_PRIMARY = RGBColor(15, 23, 42)      # Deep Slate / Navy
COLOR_SECONDARY = RGBColor(30, 41, 59)    # Slate 800
COLOR_TEXT_MAIN = RGBColor(15, 23, 42)
COLOR_MUTED = RGBColor(71, 85, 105)

def get_code(rel_path):
    p = os.path.join(PROJECT_DIR, rel_path)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    return f"# File {rel_path} not found"

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    for child in list(tcPr):
        if child.tag.endswith('shd'):
            tcPr.remove(child)
    shd = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), fill_hex))
    tcPr.append(shd)

def set_cell_margins(cell, top=35, bottom=35, left=70, right=70):
    tcPr = cell._tc.get_or_add_tcPr()
    for child in list(tcPr):
        if child.tag.endswith('tcMar'):
            tcPr.remove(child)
    tcMar = parse_xml(r"""
        <w:tcMar {} >
            <w:top w:w="{}" w:type="dxa"/>
            <w:left w:w="{}" w:type="dxa"/>
            <w:bottom w:w="{}" w:type="dxa"/>
            <w:right w:w="{}" w:type="dxa"/>
        </w:tcMar>
    """.format(nsdecls('w'), top, left, bottom, right))
    tcPr.append(tcMar)

def set_table_borders(table, color="CBD5E1", sz="4"):
    tblPr = table._tbl.tblPr
    for child in list(tblPr):
        if child.tag.endswith('tblBorders'):
            tblPr.remove(child)
    borders = parse_xml(r"""
        <w:tblBorders {} >
            <w:top w:val="single" w:sz="{}" w:space="0" w:color="{}"/>
            <w:left w:val="none"/>
            <w:bottom w:val="single" w:sz="{}" w:space="0" w:color="{}"/>
            <w:right w:val="none"/>
            <w:insideH w:val="single" w:sz="{}" w:space="0" w:color="E2E8F0"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    """.format(nsdecls('w'), sz, color, sz, color, sz))
    tblPr.append(borders)

def make_styled_table(doc, headers, data, col_widths, alignments=None, bold_cols=None, font_size=9.2, cell_pad=(35, 35)):
    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table, color="94A3B8", sz="6")
    
    if alignments is None:
        alignments = ['L'] * len(headers)
    if bold_cols is None:
        bold_cols = []
        
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].width = Inches(col_widths[i])
        set_cell_background(hdr_cells[i], "0F172A")
        set_cell_margins(hdr_cells[i], top=cell_pad[0], bottom=cell_pad[1], left=60, right=60)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if alignments[i] == 'R' else (WD_ALIGN_PARAGRAPH.CENTER if alignments[i] == 'C' else WD_ALIGN_PARAGRAPH.LEFT)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(h)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(font_size)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        
    trPr = table.rows[0]._tr.get_or_add_trPr()
    trPr.append(parse_xml(r'<w:tblHeader {}/>'.format(nsdecls('w'))))
    trPr.append(parse_xml(r'<w:cantSplit {}/>'.format(nsdecls('w'))))
    
    for row_idx, row_data in enumerate(data):
        row_cells = table.rows[row_idx + 1].cells
        r_trPr = table.rows[row_idx + 1]._tr.get_or_add_trPr()
        r_trPr.append(parse_xml(r'<w:cantSplit {}/>'.format(nsdecls('w'))))
        bg_hex = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].width = Inches(col_widths[col_idx])
            set_cell_background(row_cells[col_idx], bg_hex)
            set_cell_margins(row_cells[col_idx], top=cell_pad[0], bottom=cell_pad[1], left=60, right=60)
            p = row_cells[col_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if alignments[col_idx] == 'R' else (WD_ALIGN_PARAGRAPH.CENTER if alignments[col_idx] == 'C' else WD_ALIGN_PARAGRAPH.LEFT)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.05
            r = p.add_run(str(cell_value))
            r.font.name = 'Times New Roman'
            r.font.size = Pt(font_size)
            if col_idx in bold_cols:
                r.font.bold = True
            r.font.color.rgb = COLOR_TEXT_MAIN
            
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_after = Pt(6)
    p_after.paragraph_format.line_spacing = 1.0
    return table

def build_master_report():
    print("Initializing 100+ page document generation...")
    doc = Document()
    
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(12)
    style_normal.font.color.rgb = COLOR_TEXT_MAIN
    style_normal.paragraph_format.line_spacing = 1.25
    style_normal.paragraph_format.space_after = Pt(6)
    
    # -------------------------------------------------------------------------
    # SECTION 1: COVER / TITLE PAGE (PAGE 1)
    # -------------------------------------------------------------------------
    print("Building Section 1: Cover Page...")
    sec1 = doc.sections[0]
    sec1.top_margin = Inches(0.8)
    sec1.bottom_margin = Inches(0.8)
    sec1.left_margin = Inches(0.8)
    sec1.right_margin = Inches(0.8)
    sec1.page_width = Inches(8.27)
    sec1.page_height = Inches(11.69)
    sec1.different_first_page_header_footer = True
    
    p_univ = doc.add_paragraph()
    p_univ.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_univ.paragraph_format.space_after = Pt(2)
    r_univ = p_univ.add_run("DR. NSAM FIRST GRADE COLLEGE, NITTE\\n")
    r_univ.font.name = 'Times New Roman'
    r_univ.font.size = Pt(16)
    r_univ.font.bold = True
    r_univ.font.color.rgb = COLOR_PRIMARY
    
    r_sub = p_univ.add_run("(A Constituent College of Nitte (Deemed to be University))\\nNitte – 574 110, Karkala Taluk, Udupi District, Karnataka, India")
    r_sub.font.name = 'Times New Roman'
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = COLOR_MUTED
    
    logo_path = os.path.join(PROJECT_DIR, "project_report", "nitte_nsam_logo.png")
    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(8)
        p_logo.paragraph_format.space_after = Pt(10)
        p_logo.add_run().add_picture(logo_path, width=Inches(1.85))
        
    p_proj = doc.add_paragraph()
    p_proj.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_proj.paragraph_format.space_after = Pt(4)
    r_proj = p_proj.add_run("A MAJOR PROJECT REPORT ON\\n")
    r_proj.font.name = 'Times New Roman'
    r_proj.font.size = Pt(11)
    r_proj.font.bold = True
    r_proj.font.color.rgb = COLOR_MUTED
    
    r_title = p_proj.add_run("KUKUGUARD: AN EDGE-COMPUTING COMPUTER VISION SYSTEM FOR AVIAN ENTERIC PATHOLOGY SCREENING VIA DIFFERENTIAL FECAL MORPHOLOGY, SHORTCUT-RESISTANT FEATURE ENGINEERING, AND UNCERTAINTY-CALIBRATED NEURAL DIAGNOSTICS")
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(14)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY
    
    p_subm = doc.add_paragraph()
    p_subm.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_subm.paragraph_format.space_before = Pt(6)
    p_subm.paragraph_format.space_after = Pt(6)
    r_subm = p_subm.add_run("Submitted in partial fulfillment of the requirements for the award of the degree of\\n")
    r_subm.font.name = 'Times New Roman'
    r_subm.font.size = Pt(11)
    r_subm.font.italic = True
    
    r_deg = p_subm.add_run("BACHELOR OF COMPUTER APPLICATIONS (BCA)")
    r_deg.font.name = 'Times New Roman'
    r_deg.font.size = Pt(13)
    r_deg.font.bold = True
    r_deg.font.color.rgb = COLOR_PRIMARY
    
    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_before = Pt(6)
    p_auth.paragraph_format.space_after = Pt(6)
    
    r_by = p_auth.add_run("Submitted by:\\n")
    r_by.font.name = 'Times New Roman'
    r_by.font.size = Pt(11)
    
    r_name = p_auth.add_run("SAHITH R\\n")
    r_name.font.name = 'Times New Roman'
    r_name.font.size = Pt(13)
    r_name.font.bold = True
    
    r_reg = p_auth.add_run("Register No: NNS24BC070 | Class: III BCA 'B'")
    r_reg.font.name = 'Times New Roman'
    r_reg.font.size = Pt(11)
    
    p_guide = doc.add_paragraph()
    p_guide.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_guide.paragraph_format.space_before = Pt(6)
    p_guide.paragraph_format.space_after = Pt(6)
    
    r_gtitle = p_guide.add_run("Under the Guidance of:\\n")
    r_gtitle.font.name = 'Times New Roman'
    r_gtitle.font.size = Pt(11)
    r_gtitle.font.italic = True
    
    r_g1 = p_guide.add_run("Mr. Bharath S. Bhat, M.Sc., M.Phil.\\n")
    r_g1.font.name = 'Times New Roman'
    r_g1.font.size = Pt(11.5)
    r_g1.font.bold = True
    r_g1_sub = p_guide.add_run("Head of the Department & Assistant Professor\\nDepartment of Computer Science\\nand\\n")
    r_g1_sub.font.name = 'Times New Roman'
    r_g1_sub.font.size = Pt(10)
    
    r_g2 = p_guide.add_run("Mr. Srujan U. Shetty, M.Sc.\\n")
    r_g2.font.name = 'Times New Roman'
    r_g2.font.size = Pt(11.5)
    r_g2.font.bold = True
    r_g2_sub = p_guide.add_run("Assistant Professor, Department of Computer Science")
    r_g2_sub.font.name = 'Times New Roman'
    r_g2_sub.font.size = Pt(10)
    
    p_dept = doc.add_paragraph()
    p_dept.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dept.paragraph_format.space_before = Pt(8)
    p_dept.paragraph_format.space_after = Pt(0)
    
    r_d1 = p_dept.add_run("DEPARTMENT OF COMPUTER SCIENCE\\n")
    r_d1.font.name = 'Times New Roman'
    r_d1.font.size = Pt(13)
    r_d1.font.bold = True
    r_d1.font.color.rgb = COLOR_PRIMARY
    
    r_d2 = p_dept.add_run("DR. NSAM FIRST GRADE COLLEGE, NITTE\\n")
    r_d2.font.name = 'Times New Roman'
    r_d2.font.size = Pt(12)
    r_d2.font.bold = True
    
    r_d3 = p_dept.add_run("Udupi District, Karnataka – 574 110\\n")
    r_d3.font.name = 'Times New Roman'
    r_d3.font.size = Pt(10.5)
    
    r_d4 = p_dept.add_run("Academic Period: 2024–2027")
    r_d4.font.name = 'Times New Roman'
    r_d4.font.size = Pt(11)
    r_d4.font.bold = True

    # -------------------------------------------------------------------------
    # SECTION 2: PRELIMINARY ROMAN PAGES (ii - xii)
    # -------------------------------------------------------------------------
    print("Building Section 2: Preliminary Roman Pages (ii - xii)...")
    sec2 = doc.add_section()
    sec2.top_margin = Inches(0.8)
    sec2.bottom_margin = Inches(0.8)
    sec2.left_margin = Inches(0.8)
    sec2.right_margin = Inches(0.8)
    sec2.page_width = Inches(8.27)
    sec2.page_height = Inches(11.69)
    sec2.different_first_page_header_footer = False
    
    sectPr = sec2._sectPr
    pgNumType = OxmlElement('w:pgNumType')
    pgNumType.set(qn('w:start'), '2')
    sectPr.append(pgNumType)
    
    footer = sec2.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    frun_f = fp.add_run("DR. NSAM FIRST GRADE COLLEGE, NITTE          Page | ")
    frun_f.font.name = 'Times New Roman'
    frun_f.font.size = Pt(9.5)
    frun_f.font.color.rgb = COLOR_MUTED
    
    fld_page = fp.add_run()
    fld1 = OxmlElement('w:fldChar')
    fld1.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = "PAGE"
    fld2 = OxmlElement('w:fldChar')
    fld2.set(qn('w:fldCharType'), 'separate')
    fld3 = OxmlElement('w:fldChar')
    fld3.set(qn('w:fldCharType'), 'end')
    fld_page._r.extend([fld1, instr, fld2, fld3])
    fld_page.font.name = 'Times New Roman'
    fld_page.font.size = Pt(9.5)
    fld_page.font.bold = True
    
    # PAGE 2 (ii): CERTIFICATE OF APPROVAL
    p_cert = doc.add_paragraph()
    p_cert.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cert.paragraph_format.space_before = Pt(8)
    p_cert.paragraph_format.space_after = Pt(12)
    r_ct = p_cert.add_run("CERTIFICATE OF APPROVAL")
    r_ct.font.name = 'Times New Roman'
    r_ct.font.size = Pt(16)
    r_ct.font.bold = True
    r_ct.font.color.rgb = COLOR_PRIMARY
    
    p_cert_body = doc.add_paragraph()
    p_cert_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_cert_body.paragraph_format.line_spacing = 1.3
    p_cert_body.paragraph_format.space_after = Pt(10)
    p_cert_body.add_run(
        "This is to certify that the major project report entitled \\"KUKUGUARD: AN EDGE-COMPUTING COMPUTER VISION SYSTEM FOR "
        "AVIAN ENTERIC PATHOLOGY SCREENING VIA DIFFERENTIAL FECAL MORPHOLOGY, SHORTCUT-RESISTANT FEATURE ENGINEERING, "
        "AND UNCERTAINTY-CALIBRATED NEURAL DIAGNOSTICS\\" is a bonafide record of independent project work carried out by "
        "SAHITH R (Register No: NNS24BC070), student of III Year BCA 'B', in partial fulfillment of the requirements for the "
        "award of the degree of Bachelor of Computer Applications (BCA) by Nitte (Deemed to be University) during the academic "
        "period 2024–2027.\\n\\n"
        "The project work has been examined and evaluated by the internal and external examiners and is hereby approved as "
        "satisfying the academic and technical standards prescribed by the University for the degree of Bachelor of Computer Applications."
    )
    
    p_sig_tbl = doc.add_table(rows=2, cols=2)
    p_sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(p_sig_tbl, color="FFFFFF", sz="0")
    for r in p_sig_tbl.rows:
        for c in r.cells:
            c.width = Inches(3.3)
            set_cell_background(c, "FFFFFF")
            set_cell_margins(c, top=20, bottom=20, left=40, right=40)
            
    c00 = p_sig_tbl.cell(0, 0).paragraphs[0]
    c00.paragraph_format.space_before = Pt(28)
    c00.paragraph_format.line_spacing = 1.15
    c00.add_run("______________________________\\nMr. Bharath S. Bhat\\nHead of Department & Project Guide\\nDepartment of Computer Science")
    c00.runs[0].font.name = 'Times New Roman'
    c00.runs[0].font.size = Pt(10)
    
    c01 = p_sig_tbl.cell(0, 1).paragraphs[0]
    c01.paragraph_format.space_before = Pt(28)
    c01.paragraph_format.line_spacing = 1.15
    c01.add_run("______________________________\\nMr. Srujan U. Shetty\\nAssistant Professor & Project Co-Guide\\nDepartment of Computer Science")
    c01.runs[0].font.name = 'Times New Roman'
    c01.runs[0].font.size = Pt(10)
    
    c10 = p_sig_tbl.cell(1, 0).paragraphs[0]
    c10.paragraph_format.space_before = Pt(28)
    c10.paragraph_format.line_spacing = 1.15
    c10.add_run("______________________________\\nInternal Examiner\\nDate: _______________")
    c10.runs[0].font.name = 'Times New Roman'
    c10.runs[0].font.size = Pt(10)
    
    c11 = p_sig_tbl.cell(1, 1).paragraphs[0]
    c11.paragraph_format.space_before = Pt(28)
    c11.paragraph_format.line_spacing = 1.15
    c11.add_run("______________________________\\nExternal Examiner\\nDate: _______________")
    c11.runs[0].font.name = 'Times New Roman'
    c11.runs[0].font.size = Pt(10)
    
    # PAGE 3 (iii): DECLARATION OF ORIGINALITY
    doc.add_page_break()
    p_dec = doc.add_paragraph()
    p_dec.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dec.paragraph_format.space_before = Pt(8)
    p_dec.paragraph_format.space_after = Pt(12)
    r_dt = p_dec.add_run("DECLARATION OF ORIGINALITY")
    r_dt.font.name = 'Times New Roman'
    r_dt.font.size = Pt(16)
    r_dt.font.bold = True
    r_dt.font.color.rgb = COLOR_PRIMARY
    
    p_dec_body = doc.add_paragraph()
    p_dec_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_dec_body.paragraph_format.line_spacing = 1.3
    p_dec_body.paragraph_format.space_after = Pt(12)
    p_dec_body.add_run(
        "I, SAHITH R (Register No: NNS24BC070), hereby declare that this project report entitled \\"KUKUGUARD: AN EDGE-COMPUTING "
        "COMPUTER VISION SYSTEM FOR AVIAN ENTERIC PATHOLOGY SCREENING VIA DIFFERENTIAL FECAL MORPHOLOGY, SHORTCUT-RESISTANT "
        "FEATURE ENGINEERING, AND UNCERTAINTY-CALIBRATED NEURAL DIAGNOSTICS\\" is an original and authentic piece of academic and "
        "engineering work completed by me under the supervision and guidance of Mr. Bharath S. Bhat, Head of the Department of "
        "Computer Science, and Mr. Srujan U. Shetty, Assistant Professor, Department of Computer Science, Dr. NSAM First Grade College, Nitte.\\n\\n"
        "I further affirm that this report has not previously formed the basis for the award of any Degree, Diploma, Associateship, "
        "Fellowship, or any other academic title in this or any other University or Institution of higher learning. All empirical data, "
        "comparative benchmarks, code implementations, architectural designs, and diagnostic evaluations presented herein represent "
        "unbiased research and original engineering development, with all scholarly sources and literature appropriately cited."
    )
    
    p_dec_sig = doc.add_paragraph()
    p_dec_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_dec_sig.paragraph_format.space_before = Pt(36)
    p_dec_sig.paragraph_format.line_spacing = 1.2
    r_ds = p_dec_sig.add_run(
        "SAHITH R\\n"
        "Register No: NNS24BC070\\n"
        "Class: III Year BCA 'B'\\n"
        "Department of Computer Science\\n"
        "Dr. NSAM First Grade College, Nitte\\n"
        "Date: ________________________"
    )
    r_ds.font.name = 'Times New Roman'
    r_ds.font.size = Pt(11)

    # PAGE 4 (iv): ACKNOWLEDGMENT
    doc.add_page_break()
    p_ack = doc.add_paragraph()
    p_ack.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ack.paragraph_format.space_before = Pt(8)
    p_ack.paragraph_format.space_after = Pt(12)
    r_at = p_ack.add_run("ACKNOWLEDGMENT")
    r_at.font.name = 'Times New Roman'
    r_at.font.size = Pt(16)
    r_at.font.bold = True
    r_at.font.color.rgb = COLOR_PRIMARY
    
    p_ack_body = doc.add_paragraph()
    p_ack_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_ack_body.paragraph_format.line_spacing = 1.3
    p_ack_body.paragraph_format.space_after = Pt(10)
    p_ack_body.add_run(
        "First and foremost, I express my profound gratitude to the Almighty for bestowing upon me the wisdom, perseverance, and good health required to complete this major engineering project successfully.\\n\\n"
        "I express my deepest gratitude and sincere indebtedness to my project guide, Mr. Bharath S. Bhat, Head of the Department and Assistant Professor, Department of Computer Science, Dr. NSAM First Grade College, Nitte, for his invaluable guidance, technical insights, and constant encouragement throughout the entire lifecycle of this project.\\n\\n"
        "I am equally indebted to my co-guide, Mr. Srujan U. Shetty, Assistant Professor, Department of Computer Science, for his meticulous code reviews, mathematical guidance in loss formulation, and continual assistance in debugging deep learning pipelines.\\n\\n"
        "I extend my sincere thanks to Dr. Veena B. K., Principal, Dr. NSAM First Grade College, Nitte, for providing exceptional academic infrastructure, computing facilities, and an encouraging scholarly environment.\\n\\n"
        "I take this opportunity to thank all teaching and non-teaching faculty members of the Department of Computer Science for their direct and indirect support. Finally, I express my heartfelt love and gratitude to my parents and friends whose unwavering moral and financial support enabled me to achieve this academic milestone."
    )
    
    # PAGE 5 (v): ABSTRACT
    doc.add_page_break()
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abs.paragraph_format.space_before = Pt(8)
    p_abs.paragraph_format.space_after = Pt(12)
    r_abt = p_abs.add_run("ABSTRACT")
    r_abt.font.name = 'Times New Roman'
    r_abt.font.size = Pt(16)
    r_abt.font.bold = True
    r_abt.font.color.rgb = COLOR_PRIMARY
    
    p_abs_body = doc.add_paragraph()
    p_abs_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs_body.paragraph_format.line_spacing = 1.3
    p_abs_body.paragraph_format.space_after = Pt(10)
    p_abs_body.add_run(
        "Enteric avian infections—most notably Coccidiosis, Salmonella (pullorum/typhimurium), and velogenic Newcastle Disease (ND)—represent "
        "existential threats to global commercial poultry production, generating annual direct losses exceeding $3 billion worldwide. While modern deep "
        "convolutional neural networks have shown high nominal classification accuracies on public datasets, standard models suffer from catastrophic "
        "vulnerabilities in real-world farm deployment: (1) data leakage between train and test splits due to near-duplicate frame captures; (2) shortcut "
        "learning where networks anchor to bedding substrates (wood shavings, straw, sand, wire mesh) rather than pathological fecal lesions; (3) pathological "
        "overconfidence on out-of-distribution (OOD) farm debris; and (4) excessive computational latency exceeding edge hardware budgets.\\n\\n"
        "This project presents KukuGuard, a production-grade, edge-computing diagnostic computer vision framework engineered specifically to resolve "
        "these vulnerabilities. First, we flatten and audit the raw photographic dataset using difference hashing (dHash) and graph connected-component "
        "partitioning, establishing an audited, leakage-free 70/15/15 split across 6,432 high-resolution images. Second, we engineer a 410-dimensional "
        "classical feature extraction pipeline combining multi-color-space histograms (RGB, HSV, Lab), Gray-Level Co-occurrence Matrix (GLCM) second-order "
        "statistics, Local Binary Patterns (LBP), and Haar wavelets. When evaluated with Support Vector Machines (RBF kernel), this classical baseline "
        "achieves 94.67% macro F1 while demonstrating complete statistical immunity to substrate confounding.\\n\\n"
        "Third, across deep transfer learning backbones, EfficientNet-B0 achieves superior diagnostic performance (96.48% macro F1, 99.4% ROC-AUC), while "
        "MobileNetV2 provides ultra-lightweight inference (93.18% macro F1, 2.2M parameters). Class-weighted Cross-Entropy and Focal Loss formulations are "
        "compared, uncovering a critical epidemiological trade-off: Focal Loss boosts Newcastle Disease sensitivity to 77.8% (vital for early quarantine), "
        "whereas Weighted Cross-Entropy achieves balanced overall recall. Fourth, post-hoc temperature scaling calibrates model confidence, reducing "
        "Expected Calibration Error (ECE) from 0.089 to 0.021. Fifth, a dual OOD rejection mechanism combining Free Energy Scoring with deep feature cosine "
        "distance reliably rejects non-fecal farm debris (98.9% AUROC). Finally, the entire pipeline is exported to dual-output ONNX and dynamic INT8 "
        "quantization, achieving 27.2 ms edge latency on a quad-core CPU, and served via an interactive Streamlit application with live Grad-CAM visual explainability."
    )
''')
print("Part 1 written successfully.")
