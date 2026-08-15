import os
import io
import textwrap
import hashlib
from PIL import Image, ImageDraw

def mask_patient_name(name):
    """Masks patient names to comply with HIPAA Safe Harbor de-identification."""
    if not name or str(name).lower() in ["n/a", "unknown", "not specified", "null"]:
        return "Not Specified"
    parts = str(name).strip().split()
    masked = []
    for p in parts:
        if len(p) <= 2:
            masked.append(p[0] + "*")
        else:
            masked.append(p[0] + "*" * (len(p) - 1))
    return " ".join(masked)

def mask_patient_id(pid):
    """Masks patient IDs for enterprise data security."""
    if not pid or str(pid).lower() in ["n/a", "unknown", "not specified", "null"]:
        return "Not Specified"
    s = str(pid).strip()
    if len(s) <= 4:
        return s[0] + "*" * (len(s) - 1)
    return s[:4] + "*" * (len(s) - 4)

def clean_text_for_pdf(text):
    """Escapes XML characters for ReportLab Paragraphs."""
    if not isinstance(text, str):
        text = str(text)
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def create_pil_canvas_pdf_fallback(title_str, risk_banner_str, summary_str, info_dict, anomalies_list, is_severe=False):
    """
    Fail-safe high-resolution PIL Canvas PDF Generator.
    Guarantees a valid, openable 100% clean PDF file even if ReportLab is unavailable on cloud deployment.
    """
    img = Image.new('RGB', (1200, 1600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header Bar
    draw.rectangle([(0, 0), (1200, 100)], fill=(15, 23, 42))
    draw.text((50, 32), title_str, fill=(56, 189, 248))

    y = 130
    # Risk Banner
    banner_color = (190, 18, 60) if is_severe else (16, 185, 129)
    draw.rectangle([(50, y), (1150, y + 55)], fill=banner_color)
    draw.text((80, y + 16), risk_banner_str, fill=(255, 255, 255))
    y += 80

    # Executive AI Summary Box
    draw.rectangle([(50, y), (1150, y + 160)], fill=(239, 246, 255), outline=(191, 219, 254), width=2)
    draw.text((70, y + 15), "EXECUTIVE AI AUDIT SUMMARY & CLINICAL VERDICT:", fill=(30, 58, 138))
    
    sum_lines = textwrap.wrap(summary_str, width=110)
    sy = y + 45
    for s_line in sum_lines[:5]:
        draw.text((70, sy), s_line, fill=(15, 23, 42))
        sy += 22
    y += 180

    # Flagged Red Flags & Anomalies
    draw.text((50, y), "FLAGGED FRAUD RED FLAGS & WARNINGS:", fill=(15, 23, 42))
    y += 30
    if anomalies_list and anomalies_list != ["None detected"]:
        for a in anomalies_list[:4]:
            if isinstance(a, dict):
                a_type = a.get('type', 'Anomaly')
                a_desc = a.get('description', '')
                a_str = f"• [RED FLAG - {a_type}] {a_desc}"
            else:
                a_str = f"• [RED FLAG WARNING] {a}"
            
            draw.rectangle([(50, y), (1150, y + 40)], fill=(255, 228, 230), outline=(254, 205, 211), width=1)
            draw.text((70, y + 10), a_str[:110], fill=(153, 27, 27))
            y += 48
    else:
        draw.rectangle([(50, y), (1150, y + 40)], fill=(236, 253, 245), outline=(167, 243, 208), width=1)
        draw.text((70, y + 10), "✓ Clean Claim — No clinical red flags or test over-utilization detected.", fill=(16, 185, 129))
        y += 50
    y += 15

    # Demographics Info Box
    draw.rectangle([(50, y), (1150, y + 180)], fill=(241, 245, 249), outline=(203, 213, 225), width=1)
    draw.text((70, y + 15), "CLAIM & CLINICAL DEMOGRAPHICS:", fill=(30, 41, 59))
    dy = y + 45
    for k, v in info_dict.items():
        draw.text((70, dy), f"{k}: {v}", fill=(51, 65, 85))
        dy += 24

    pdf_buffer = io.BytesIO()
    img.save(pdf_buffer, format='PDF', quality=100)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

def generate_corporate_scheme_report_pdf(enquiry_res, output_filename="Corporate_Policy_Eligibility_Report.pdf"):
    """
    Generates a high-quality PDF Corporate Policy & Scheme Eligibility Report.
    Includes all details:
    - Corporate Employer & Group Policy Status
    - Patient Coverage Demographics (HIPAA Masked)
    - Scheme Limits vs Claim Coverage Matrix
    - Claim Applicability Verdict (APPLICABLE FOR CLAIM vs INELIGIBLE)
    - Policy Risk Warnings & Flagged Anomalies
    - Patient Historical Fraud Logs
    - 20pt Calibri / Helvetica-Bold Header Quality & SHA-256 Token
    """
    p_rec = enquiry_res.get("patient_record", {})
    emp = enquiry_res.get("employer_info", {})
    sch = enquiry_res.get("scheme_info", {})
    
    raw_pname = p_rec.get("patient_name", "N/A")
    raw_pid = p_rec.get("patient_id", "N/A")
    p_name = mask_patient_name(raw_pname)
    p_id = mask_patient_id(raw_pid)
    
    employer_name = emp.get("employer_code", "N/A")
    group_id = emp.get("policy_group_id", "N/A")
    insurer = emp.get("default_insurer", "N/A")
    
    scheme_name = sch.get("scheme_code", "N/A")
    max_cap = f"${sch.get('max_annual_sum_insured', 0):,.2f}"
    room_cap = f"${sch.get('room_rent_cap_per_day', 0):,.2f} / day"
    copay = sch.get("copay_percentage", "0%")
    wait_period = f"{sch.get('pre_existing_disease_wait_months', 0)} Months"
    
    claim_amount = f"${enquiry_res.get('claim_amount', 0):,.2f}"
    cpt_code = str(enquiry_res.get('cpt_code', 'N/A'))
    rem_sum = f"${p_rec.get('remaining_sum_insured', 0):,.2f}"
    
    is_app = enquiry_res.get("is_applicable", False)
    warnings = enquiry_res.get("risk_warnings", [])
    fraud_logs = p_rec.get("fraud_history_records", [])

    status_str = "APPLICABLE FOR CLAIM REQUEST" if is_app and not warnings else "CLAIM INELIGIBLE / POLICY FLAGGED"

    payload = f"{raw_pid}:{group_id}:{claim_amount}:{status_str}"
    security_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16].upper()

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_20pt_style = ParagraphStyle('DocTitle20_Corp', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#0F172A'), spaceAfter=4)
        header_20pt_style = ParagraphStyle('Header20_Corp', parent=styles['Heading2'], fontSize=15, leading=19, textColor=colors.HexColor('#1E293B'), spaceBefore=10, spaceAfter=4)
        sub_style = ParagraphStyle('DocSub_Corp', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#64748B'), spaceAfter=8)
        body_style = ParagraphStyle('BodyCustom_Corp', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#334155'), leading=14)
        summary_style = ParagraphStyle('SummaryCustom_Corp', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#0F172A'), leading=15)
        redflag_style = ParagraphStyle('RedFlagCustom_Corp', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#991B1B'), leading=14)

        elements = []

        # 1. 20pt Header
        elements.append(Paragraph("<b>Corporate Policy & Scheme Eligibility Audit Report</b>", title_20pt_style))
        elements.append(Paragraph(f"Employer: {clean_text_for_pdf(p_rec.get('employer', 'N/A'))} | Group Policy ID: {clean_text_for_pdf(group_id)} | SHA-256 Token: <code>{security_hash}</code>", sub_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#CBD5E1'), spaceAfter=8))

        # 2. Verdict Banner
        banner_color = colors.HexColor('#10B981') if is_app and not warnings else colors.HexColor('#BE123C')
        elements.append(Table([
            [Paragraph(f"<font size=12 color='#FFFFFF'><b>VERDICT: {clean_text_for_pdf(status_str)}</b></font>", body_style)]
        ], colWidths=[540], style=[
            ('BACKGROUND', (0,0), (-1,-1), banner_color),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(Spacer(1, 8))

        # 3. Patient & Employer Information
        elements.append(Paragraph("<b>Patient & Corporate Group Employer Details</b>", header_20pt_style))
        demo_data = [
            [Paragraph(f"<b>Patient Name:</b> {clean_text_for_pdf(p_name)} 🔒", body_style), Paragraph(f"<b>Patient ID:</b> {clean_text_for_pdf(p_id)} 🔒", body_style)],
            [Paragraph(f"<b>Corporate Employer:</b> {clean_text_for_pdf(p_rec.get('employer', 'N/A'))}", body_style), Paragraph(f"<b>Employer Code:</b> {clean_text_for_pdf(employer_name)}", body_style)],
            [Paragraph(f"<b>Employment Status:</b> {clean_text_for_pdf(p_rec.get('employment_status', 'N/A'))}", body_style), Paragraph(f"<b>Background Verification:</b> {clean_text_for_pdf(p_rec.get('background_verification', 'N/A'))}", body_style)],
            [Paragraph(f"<b>Assigned Policy Scheme:</b> {clean_text_for_pdf(p_rec.get('scheme_assigned', 'N/A'))}", body_style), Paragraph(f"<b>Assigned Insurer:</b> {clean_text_for_pdf(insurer)}", body_style)]
        ]
        t_demo = Table(demo_data, colWidths=[270, 270], style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ])
        elements.append(t_demo)
        elements.append(Spacer(1, 8))

        # 4. Scheme Limits vs Claim Evaluation Matrix
        elements.append(Paragraph("<b>Scheme Policy Terms vs Billed Claim Matrix</b>", header_20pt_style))
        matrix_data = [
            ["Policy Parameter", "Scheme Policy Terms", "Billed Claim Evaluation"],
            ["Max Annual Sum Insured Cap", max_cap, f"Billed Amount: {claim_amount}"],
            ["Patient Remaining Sum Insured", rem_sum, "Exceeded Sum Insured Cap!" if enquiry_res.get('exceeds_remaining') else "Within Remaining Cap"],
            ["Daily Room Rent Cap", room_cap, "Applies to Inpatient Admissions"],
            ["Co-Pay Requirement", copay, "Deducted at Settlement"],
            ["Pre-Existing Disease Wait", wait_period, "Verified against Doctor Notes"]
        ]
        t_matrix = Table([[Paragraph(clean_text_for_pdf(c), body_style) for c in row] for row in matrix_data], colWidths=[170, 170, 200], style=[
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
        ])
        elements.append(t_matrix)
        elements.append(Spacer(1, 8))

        # 5. Risk Warnings & Flags
        elements.append(Paragraph("<b>Policy Risk Warnings & Verification Flags</b>", header_20pt_style))
        if warnings:
            w_data = [["#", "Corporate Policy Risk Warning"]]
            for idx, w in enumerate(warnings, 1):
                w_data.append([str(idx), Paragraph(f"<b>⚠️ {clean_text_for_pdf(w)}</b>", redflag_style)])
            t_w = Table(w_data, colWidths=[30, 510], style=[
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FFE4E6')),
                ('GRID', (0,0), (-1,-1), 0.75, colors.HexColor('#FECDD3')),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
            ])
            elements.append(t_w)
        else:
            elements.append(Table([[Paragraph("<font color='#10B981'><b>✓ Clean Claim — Fully eligible under corporate policy terms.</b></font>", body_style)]], colWidths=[540], style=[
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ECFDF5')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#A7F3D0')),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
            ]))
        elements.append(Spacer(1, 8))

        # 6. Patient Historical Corporate Fraud Log
        elements.append(Paragraph("<b>Patient Historical Corporate Fraud Record Log</b>", header_20pt_style))
        if fraud_logs:
            f_data = [["Incident Date", "Incident Description", "Audit Settlement Status"]]
            for f in fraud_logs:
                f_data.append([
                    Paragraph(clean_text_for_pdf(f.get("date", "N/A")), body_style),
                    Paragraph(f"<b>⚠️ {clean_text_for_pdf(f.get('incident', 'N/A'))}</b>", redflag_style),
                    Paragraph(clean_text_for_pdf(f.get("status", "N/A")), body_style)
                ])
            t_f = Table(f_data, colWidths=[90, 290, 160], style=[
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
            ])
            elements.append(t_f)
        else:
            elements.append(Table([[Paragraph("<font color='#10B981'><b>✓ Clean Record — Zero prior corporate fraud incidents logged.</b></font>", body_style)]], colWidths=[540], style=[
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ECFDF5')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#A7F3D0')),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
            ]))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        print(f"ReportLab Corporate Scheme PDF generation fallback: {e}")
        info_d = {
            "Patient": p_name,
            "Employer": p_rec.get('employer', 'N/A'),
            "Scheme": p_rec.get('scheme_assigned', 'N/A'),
            "Claim Billed": claim_amount,
            "Verdict": status_str
        }
        return create_pil_canvas_pdf_fallback("Corporate Policy & Scheme Eligibility Report", f"VERDICT: {status_str}", f"Corporate scheme policy audit for {p_name} ({p_rec.get('employer', 'N/A')}).", info_d, warnings, is_severe=not is_app)

def generate_deep_forensic_report_pdf(audit_data, output_filename="Deep_Forensic_Audit_Report.pdf"):
    """
    Generates a high-quality PDF Forensic Audit Report for Tab 1 (Deep Single Claim Forensic Audit).
    Styles document title & main headers in 20pt font size.
    Places full Executive AI Summary and Flagged Red Flags front and center.
    """
    h_name = str(audit_data.get('hospital_name', 'N/A'))
    h_id = str(audit_data.get('hospital_id', 'N/A'))
    h_type = str(audit_data.get('hospital_type', 'N/A'))
    p_age = str(audit_data.get('patient_age', 'N/A'))
    p_gender = str(audit_data.get('patient_gender', 'N/A'))
    med_hist = str(audit_data.get('medical_history', 'None'))
    
    diag = str(audit_data.get('diagnosis', 'N/A'))
    cpt = str(audit_data.get('cpt_code', 'N/A'))
    amt = f"${audit_data.get('claim_amount', 0):,.2f}"
    billed_tests = str(audit_data.get('billed_tests', 'None'))
    rec_tests = str(audit_data.get('recommended_tests', 'None'))
    clin_notes = str(audit_data.get('clinical_notes', 'N/A'))

    score = audit_data.get('fraud_score_pct', 0)
    risk_level = str(audit_data.get('risk_level', 'LOW')).upper()

    matrix_data = audit_data.get('cross_evaluation_matrix', {})
    fin_var = str(matrix_data.get('financial_variance_status', 'N/A'))
    clin_nec = str(matrix_data.get('clinical_necessity_status', 'N/A'))
    upcode_prob = str(matrix_data.get('upcoding_probability_status', 'N/A'))

    clin_appr = str(audit_data.get('clinical_appropriateness', 'Evaluated against guidelines.'))
    red_flags = audit_data.get('fraud_red_flags', [])
    summary_text = str(audit_data.get('forensic_summary', 'Forensic audit complete.'))
    llm_used = str(audit_data.get('llm_used', 'MedIns Hybrid Clinical AI Engine'))

    # SHA-256 Security Audit Hash Token
    payload = f"{h_id}:{cpt}:{amt}:{score}:{risk_level}"
    security_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16].upper()

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_20pt_style = ParagraphStyle('DocTitle20_T1', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#0F172A'), spaceAfter=4)
        header_20pt_style = ParagraphStyle('Header20_T1', parent=styles['Heading2'], fontSize=15, leading=19, textColor=colors.HexColor('#1E293B'), spaceBefore=10, spaceAfter=4)
        sub_style = ParagraphStyle('DocSub_T1', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#64748B'), spaceAfter=8)
        body_style = ParagraphStyle('BodyCustom_T1', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#334155'), leading=14)
        summary_style = ParagraphStyle('SummaryCustom_T1', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#0F172A'), leading=15)
        redflag_style = ParagraphStyle('RedFlagCustom_T1', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#991B1B'), leading=14)

        elements = []

        elements.append(Paragraph("<b>Deep Forensic Claims Investigation Report</b>", title_20pt_style))
        elements.append(Paragraph(f"Hospital Dossier: {clean_text_for_pdf(h_name)} ({clean_text_for_pdf(h_id)}) | SHA-256 Token: <code>{security_hash}</code> | Engine: {clean_text_for_pdf(llm_used)}", sub_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#CBD5E1'), spaceAfter=8))

        risk_color = colors.HexColor('#BE123C') if risk_level in ["HIGH", "SEVERE"] else colors.HexColor('#F59E0B') if risk_level == "MEDIUM" else colors.HexColor('#10B981')
        
        banner_table = Table([
            [Paragraph(f"<font size=12 color='#FFFFFF'><b>MEDINS RISK INDEX: {score}% — RISK CATEGORY: {clean_text_for_pdf(risk_level)}</b></font>", body_style)]
        ], colWidths=[540])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), risk_color),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(banner_table)
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("<b>Executive AI Audit Summary & Verdict</b>", header_20pt_style))
        summary_table = Table([[Paragraph(f"<b>AI Summary:</b> {clean_text_for_pdf(summary_text)}", summary_style)]], colWidths=[540])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
            ('GRID', (0,0), (-1,-1), 0.75, colors.HexColor('#BFDBFE')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("<b>Flagged Fraud & Rule Anomalies (Red Flags)</b>", header_20pt_style))
        if red_flags and red_flags != ["None detected"]:
            rf_table_data = [["#", "Flagged Fraud Red Flag Warning"]]
            for idx, rf in enumerate(red_flags, 1):
                rf_table_data.append([str(idx), Paragraph(f"<b>⚠️ {clean_text_for_pdf(rf)}</b>", redflag_style)])
            t_rf = Table(rf_table_data, colWidths=[30, 510])
            t_rf.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FFE4E6')),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.75, colors.HexColor('#FECDD3')),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
            ]))
            elements.append(t_rf)
        else:
            clean_table = Table([[Paragraph("<font color='#10B981'><b>✓ Clean Claim — No clinical red flags or test over-utilization detected.</b></font>", body_style)]], colWidths=[540])
            clean_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ECFDF5')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#A7F3D0')),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
            ]))
            elements.append(clean_table)
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("<b>Hospital Dossier & Clinical Demographics</b>", header_20pt_style))
        demo_data = [
            [Paragraph(f"<b>Hospital Name:</b> {clean_text_for_pdf(h_name)}", body_style), Paragraph(f"<b>Hospital ID:</b> {clean_text_for_pdf(h_id)} ({clean_text_for_pdf(h_type)})", body_style)],
            [Paragraph(f"<b>Patient Demographics:</b> {clean_text_for_pdf(p_age)} yo | {clean_text_for_pdf(p_gender)}", body_style), Paragraph(f"<b>Medical History:</b> {clean_text_for_pdf(med_hist)}", body_style)],
            [Paragraph(f"<b>Diagnosis (ICD-10):</b> {clean_text_for_pdf(diag)}", body_style), Paragraph(f"<b>Billed CPT Code:</b> {clean_text_for_pdf(cpt)}", body_style)],
            [Paragraph(f"<b>Claimed Amount:</b> {clean_text_for_pdf(amt)}", body_style), Paragraph(f"<b>Billed Line Items:</b> {clean_text_for_pdf(billed_tests)}", body_style)]
        ]
        t_demo = Table(demo_data, colWidths=[270, 270])
        t_demo.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(t_demo)
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("<b>Multi-Dimensional Forensic Matrix</b>", header_20pt_style))
        matrix_table_data = [
            ["Dimension", "Status & Evaluation Findings"],
            ["1. Financial Billing Variance", Paragraph(clean_text_for_pdf(fin_var), body_style)],
            ["2. Clinical Care Necessity", Paragraph(clean_text_for_pdf(clin_nec), body_style)],
            ["3. Upcoding / Fraud Mismatch", Paragraph(clean_text_for_pdf(upcode_prob), body_style)]
        ]
        t_matrix = Table(matrix_table_data, colWidths=[170, 370])
        t_matrix.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_matrix)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        print(f"ReportLab Deep Forensic PDF generation fallback: {e}")
        info_d = {
            "Hospital": f"{h_name} ({h_id})",
            "Patient": f"{p_age} yo {p_gender}",
            "Diagnosis": diag,
            "Billed CPT": cpt,
            "Claimed Amount": amt
        }
        return create_pil_canvas_pdf_fallback("Deep Forensic Claims Investigation Report", f"MEDINS RISK INDEX: {score}% — RISK LEVEL: {risk_level}", summary_text, info_d, red_flags, is_severe=(risk_level in ["HIGH", "SEVERE"]))

def generate_fraud_report_pdf(audit_data, output_filename="MedIns_Fraud_Audit_Report.pdf"):
    """
    Generates a high-quality PDF Forensic Fraud Audit Report for Tab 3 (AI Health Insurance Fraud Auditor API).
    Styles document title & main headers in 20pt font size.
    Places full Executive AI Summary and Flagged Red Flags / Anomalies front and center.
    """
    patient_info = audit_data.get('patient_info', {})
    provider_info = audit_data.get('provider_info', {})
    
    raw_p_id = str(patient_info.get('patient_id', 'N/A'))
    raw_p_name = str(patient_info.get('patient_name', 'N/A'))
    
    p_id = mask_patient_id(raw_p_id)
    p_name = mask_patient_name(raw_p_name)
    p_age = str(patient_info.get('age', 'N/A'))
    p_gender = str(patient_info.get('gender', 'N/A'))
    
    doc_name = str(provider_info.get('provider_name', 'N/A'))
    doc_spec = str(provider_info.get('specialty', 'N/A'))

    score = audit_data.get('fraud_risk_score', 0)
    category = str(audit_data.get('risk_category', 'Severe')).upper()
    summary_text = str(audit_data.get('ai_reasoning_summary', 'AI evaluation complete.'))
    anomalies = audit_data.get('detected_anomalies', [])
    llm_used = audit_data.get('llm_used', 'Groq LPU API')

    audit_payload = f"{raw_p_name}:{raw_p_id}:{score}:{category}"
    security_hash = hashlib.sha256(audit_payload.encode('utf-8')).hexdigest()[:16].upper()

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_20pt_style = ParagraphStyle('DocTitle20_T2', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#0F172A'), spaceAfter=4)
        header_20pt_style = ParagraphStyle('Header20_T2', parent=styles['Heading2'], fontSize=15, leading=19, textColor=colors.HexColor('#1E293B'), spaceBefore=10, spaceAfter=4)
        sub_style = ParagraphStyle('DocSub_T2', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#64748B'), spaceAfter=8)
        body_style = ParagraphStyle('BodyCustom_T2', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#334155'), leading=14)
        summary_style = ParagraphStyle('SummaryCustom_T2', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#0F172A'), leading=15)
        redflag_style = ParagraphStyle('RedFlagCustom_T2', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#991B1B'), leading=14)

        elements = []

        elements.append(Paragraph("<b>Health Insurance Fraud Investigation Audit Report</b>", title_20pt_style))
        elements.append(Paragraph(f"🔒 HIPAA Redacted Docket #: {clean_text_for_pdf(p_id)} | SHA-256 Token: <code>{security_hash}</code> | Engine: {clean_text_for_pdf(llm_used)}", sub_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#CBD5E1'), spaceAfter=8))

        risk_color = colors.HexColor('#BE123C') if category == "SEVERE" else colors.HexColor('#EF4444') if category == "HIGH" else colors.HexColor('#F59E0B') if category == "MEDIUM" else colors.HexColor('#10B981')
        
        banner_table = Table([
            [Paragraph(f"<font size=12 color='#FFFFFF'><b>FRAUD RISK SCORE: {score}/100 — RISK CATEGORY: {clean_text_for_pdf(category)}</b></font>", body_style)]
        ], colWidths=[540])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), risk_color),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(banner_table)
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("<b>Executive AI Audit Summary & Clinical Findings</b>", header_20pt_style))
        summary_table = Table([[Paragraph(f"<b>AI Summary:</b> {clean_text_for_pdf(summary_text)}", summary_style)]], colWidths=[540])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
            ('GRID', (0,0), (-1,-1), 0.75, colors.HexColor('#BFDBFE')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("<b>Flagged Fraud & Coding Violations (Red Flags)</b>", header_20pt_style))
        if anomalies:
            anom_table_data = [["Anomaly Type", "Severity", "Code Involved", "Rule Violation Description"]]
            for a in anomalies:
                anom_table_data.append([
                    Paragraph(f"<b>⚠️ {clean_text_for_pdf(a.get('type', 'N/A'))}</b>", redflag_style),
                    Paragraph(f"<b>{clean_text_for_pdf(a.get('severity', 'High'))}</b>", redflag_style),
                    Paragraph(clean_text_for_pdf(a.get('code_involved', 'N/A')), body_style),
                    Paragraph(clean_text_for_pdf(a.get('description', 'N/A')), body_style)
                ])
                
            t_anom = Table(anom_table_data, colWidths=[110, 65, 85, 280])
            t_anom.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FFE4E6')),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.75, colors.HexColor('#FECDD3')),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(t_anom)
        else:
            clean_table = Table([[Paragraph("<font color='#10B981'><b>✓ Clean Claim — No clinical anomalies or billing violations detected.</b></font>", body_style)]], colWidths=[540])
            clean_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ECFDF5')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#A7F3D0')),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
            ]))
            elements.append(clean_table)
        elements.append(Spacer(1, 8))

        elements.append(Paragraph("<b>Patient & Provider Demographics (HIPAA Masked)</b>", header_20pt_style))
        demo_data = [
            [Paragraph(f"<b>Patient Name:</b> {clean_text_for_pdf(p_name)} 🔒", body_style), Paragraph(f"<b>Patient ID:</b> {clean_text_for_pdf(p_id)} 🔒", body_style)],
            [Paragraph(f"<b>Age / Gender:</b> {clean_text_for_pdf(p_age)} yo | {clean_text_for_pdf(p_gender)}", body_style), Paragraph(f"<b>Provider:</b> {clean_text_for_pdf(doc_name)} ({clean_text_for_pdf(doc_spec)})", body_style)]
        ]
        t_demo = Table(demo_data, colWidths=[270, 270])
        t_demo.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(t_demo)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        print(f"ReportLab PDF generation error: {e}")
        info_d = {
            "Patient Name": p_name,
            "Patient ID": p_id,
            "Age / Gender": f"{p_age} yo {p_gender}",
            "Provider": f"{doc_name} ({doc_spec})"
        }
        return create_pil_canvas_pdf_fallback("Health Insurance Fraud Investigation Audit Report", f"FRAUD RISK SCORE: {score}/100 — RISK CATEGORY: {category}", summary_text, info_d, anomalies, is_severe=(category in ["HIGH", "SEVERE"]))

def generate_visual_fraud_report_pdf(audit_data, output_filename="Visual_Claim_Audit_Report.pdf"):
    """Legacy visual report exporter wrapper."""
    return generate_fraud_report_pdf(audit_data, output_filename)
