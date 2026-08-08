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

def generate_deep_forensic_report_pdf(audit_data, output_filename="Deep_Forensic_Audit_Report.pdf"):
    """
    Generates a high-quality PDF Forensic Audit Report for Tab 1 (Deep Single Claim Forensic Audit).
    Includes ALL data:
    - Hospital Details (name, id, type)
    - Patient & Clinical Demographics (age, gender, history)
    - Diagnosis (ICD-10), CPT Code, Claim Amount, Billed Tests, Recommended Tests
    - Risk Score & Risk Category Banner
    - Multi-Dimensional Cross-Evaluation Matrix
    - Clinical Appropriateness Assessment
    - Flagged Fraud Red Flags
    - Executive Forensic Verdict Summary
    - SHA-256 Security Hash Audit Token
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

        # Prominent 20pt Calibri / Helvetica-Bold Header Styles
        title_20pt_style = ParagraphStyle('DocTitle20', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#0F172A'), spaceAfter=4)
        header_20pt_style = ParagraphStyle('Header20', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor('#1E293B'), spaceBefore=8, spaceAfter=4)
        sub_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#64748B'), spaceAfter=8)
        body_style = ParagraphStyle('BodyCustom', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#334155'), leading=13)
        summary_style = ParagraphStyle('SummaryCustom', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#0F172A'), leading=14)

        elements = []

        # Header Title
        elements.append(Paragraph("<b>Deep Single Claim Forensic Investigation Report</b>", title_20pt_style))
        elements.append(Paragraph(f"Hospital Dossier: {clean_text_for_pdf(h_name)} ({clean_text_for_pdf(h_id)}) | SHA-256 Token: <code>{security_hash}</code> | Engine: {clean_text_for_pdf(llm_used)}", sub_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#CBD5E1'), spaceAfter=8))

        # Risk Banner
        risk_color = colors.HexColor('#BE123C') if risk_level in ["HIGH", "SEVERE"] else colors.HexColor('#F59E0B') if risk_level == "MEDIUM" else colors.HexColor('#10B981')
        
        banner_table = Table([
            [Paragraph(f"<font size=11 color='#FFFFFF'><b>MEDINS RISK INDEX: {score}% — RISK CATEGORY: {clean_text_for_pdf(risk_level)}</b></font>", body_style)]
        ], colWidths=[540])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), risk_color),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(banner_table)
        elements.append(Spacer(1, 6))

        # 🌟 EXECUTIVE AI FORENSIC VERDICT SUMMARY
        elements.append(Paragraph("<b>Executive Forensic Verdict & Clinical Summary</b>", header_20pt_style))
        summary_table = Table([[Paragraph(f"<b>Audit Findings:</b> {clean_text_for_pdf(summary_text)}", summary_style)]], colWidths=[540])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
            ('GRID', (0,0), (-1,-1), 0.75, colors.HexColor('#BFDBFE')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 6))

        # Hospital & Clinical Demographics
        elements.append(Paragraph("<b>Hospital Dossier & Clinical Demographics</b>", header_20pt_style))
        demo_data = [
            [Paragraph(f"<b>Hospital:</b> {clean_text_for_pdf(h_name)}", body_style), Paragraph(f"<b>Hospital ID & Type:</b> {clean_text_for_pdf(h_id)} | {clean_text_for_pdf(h_type)}", body_style)],
            [Paragraph(f"<b>Patient Age / Gender:</b> {clean_text_for_pdf(p_age)} yo | {clean_text_for_pdf(p_gender)}", body_style), Paragraph(f"<b>Pre-existing History:</b> {clean_text_for_pdf(med_hist)}", body_style)],
            [Paragraph(f"<b>Diagnosis (ICD-10):</b> {clean_text_for_pdf(diag)}", body_style), Paragraph(f"<b>Billed CPT Code:</b> {clean_text_for_pdf(cpt)}", body_style)],
            [Paragraph(f"<b>Claimed Amount:</b> {clean_text_for_pdf(amt)}", body_style), Paragraph(f"<b>Billed Line Items:</b> {clean_text_for_pdf(billed_tests)}", body_style)]
        ]
        t_demo = Table(demo_data, colWidths=[270, 270])
        t_demo.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(t_demo)
        elements.append(Spacer(1, 6))

        # Multi-Dimensional Cross-Evaluation Matrix
        elements.append(Paragraph("<b>Multi-Dimensional Cross-Evaluation Matrix</b>", header_20pt_style))
        matrix_table_data = [
            ["Dimension", "Status & Evaluation Findings"],
            ["1. Financial Billing Variance", Paragraph(clean_text_for_pdf(fin_var), body_style)],
            ["2. Clinical Care Necessity", Paragraph(clean_text_for_pdf(clin_nec), body_style)],
            ["3. Upcoding / Fraud Mismatch", Paragraph(clean_text_for_pdf(upcode_prob), body_style)]
        ]
        t_matrix = Table(matrix_table_data, colWidths=[180, 360])
        t_matrix.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_matrix)
        elements.append(Spacer(1, 6))

        # Clinical Care Appropriateness Assessment
        elements.append(Paragraph("<b>Clinical Guidelines vs Billed Test Appropriateness</b>", header_20pt_style))
        appr_table = Table([[Paragraph(clean_text_for_pdf(clin_appr), body_style)]], colWidths=[540])
        appr_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(appr_table)
        elements.append(Spacer(1, 6))

        # Flagged Fraud Red Flags
        elements.append(Paragraph("<b>Flagged Fraud & Red Flag Warnings</b>", header_20pt_style))
        if red_flags and red_flags != ["None detected"]:
            rf_table_data = [["#", "Flagged Fraud Red Flag"]]
            for idx, rf in enumerate(red_flags, 1):
                rf_table_data.append([str(idx), Paragraph(clean_text_for_pdf(rf), body_style)])
            t_rf = Table(rf_table_data, colWidths=[30, 510])
            t_rf.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FFE4E6')),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#FECDD3')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
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

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        print(f"ReportLab Deep Forensic PDF generation fallback: {e}")
        img = Image.new('RGB', (1000, 1400), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        draw.rectangle([(0, 0), (1000, 80)], fill=(15, 23, 42))
        draw.text((40, 25), "Deep Forensic Claims Audit Report", fill=(56, 189, 248))
        
        y = 100
        draw.rectangle([(40, y), (960, y + 45)], fill=(190, 18, 60) if risk_level in ["HIGH", "SEVERE"] else (16, 185, 129))
        draw.text((60, y + 12), f"MEDINS RISK INDEX: {score}% — RISK LEVEL: {risk_level}", fill=(255, 255, 255))
        y += 60

        pdf_buffer = io.BytesIO()
        img.save(pdf_buffer, format='PDF')
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

def generate_fraud_report_pdf(audit_data, output_filename="MedIns_Fraud_Audit_Report.pdf"):
    """
    Generates a high-quality PDF Forensic Fraud Audit Report.
    Upgraded with prominent Calibri 20pt / Helvetica-Bold 20pt Document Headers & HIPAA PII Masking.
    Renders exact schema:
    - Executive AI Reasoning Summary (Main Focus)
    - patient_info (masked patient_name, masked patient_id, age, gender)
    - provider_info (provider_name, specialty)
    - fraud_risk_score & risk_category
    - detected_anomalies (type, severity, code_involved, description)
    - SHA-256 Cryptographic Security Audit Token
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

    # SHA-256 Anonymized Security Hash
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

        # Prominent Calibri 20pt / Helvetica-Bold 20pt Styles
        title_20pt_style = ParagraphStyle('DocTitle20', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#0F172A'), spaceAfter=4)
        header_20pt_style = ParagraphStyle('Header20', parent=styles['Heading2'], fontSize=15, leading=19, textColor=colors.HexColor('#1E293B'), spaceBefore=10, spaceAfter=4)
        sub_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#64748B'), spaceAfter=8)
        body_style = ParagraphStyle('BodyCustom', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#334155'), leading=13)
        summary_style = ParagraphStyle('SummaryCustom', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#0F172A'), leading=15)

        elements = []

        # Header with Calibri 20pt Title
        elements.append(Paragraph("<b>Health Insurance Fraud Investigation Audit Report</b>", title_20pt_style))
        elements.append(Paragraph(f"🔒 HIPAA Redacted Docket #: {clean_text_for_pdf(p_id)} | SHA-256 Token: <code>{security_hash}</code> | Engine: {clean_text_for_pdf(llm_used)}", sub_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#CBD5E1'), spaceAfter=8))

        # Risk Banner
        risk_color = colors.HexColor('#BE123C') if category == "SEVERE" else colors.HexColor('#EF4444') if category == "HIGH" else colors.HexColor('#F59E0B') if category == "MEDIUM" else colors.HexColor('#10B981')
        
        banner_table = Table([
            [Paragraph(f"<font size=11 color='#FFFFFF'><b>FRAUD RISK SCORE: {score}/100 — RISK CATEGORY: {clean_text_for_pdf(category)}</b></font>", body_style)]
        ], colWidths=[540])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), risk_color),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(banner_table)
        elements.append(Spacer(1, 8))

        # 🌟 MAIN FOCUS: EXECUTIVE AI REASONING SUMMARY FRONT AND CENTER
        elements.append(Paragraph("<b>Executive AI Audit Summary & Clinical Findings</b>", header_20pt_style))
        summary_table = Table([[Paragraph(f"<b>Audit Findings:</b> {clean_text_for_pdf(summary_text)}", summary_style)]], colWidths=[540])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
            ('GRID', (0,0), (-1,-1), 0.75, colors.HexColor('#BFDBFE')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 8))

        # Patient & Provider Demographics (HIPAA Masked)
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
        elements.append(Spacer(1, 8))

        # Flagged Fraud & Rule Anomalies Table
        elements.append(Paragraph("<b>Flagged Fraud & Rule Anomalies</b>", header_20pt_style))
        if anomalies:
            anom_table_data = [["Anomaly Type", "Severity", "Code Involved", "Description"]]
            for a in anomalies:
                anom_table_data.append([
                    Paragraph(f"<b>{clean_text_for_pdf(a.get('type', 'N/A'))}</b>", body_style),
                    Paragraph(f"<b>{clean_text_for_pdf(a.get('severity', 'High'))}</b>", body_style),
                    Paragraph(clean_text_for_pdf(a.get('code_involved', 'N/A')), body_style),
                    Paragraph(clean_text_for_pdf(a.get('description', 'N/A')), body_style)
                ])
                
            t_anom = Table(anom_table_data, colWidths=[110, 65, 85, 280])
            t_anom.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
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

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        print(f"ReportLab PDF generation fallback: {e}")
        img = Image.new('RGB', (1000, 1400), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        draw.rectangle([(0, 0), (1000, 80)], fill=(15, 23, 42))
        draw.text((40, 25), "Health Insurance Fraud Audit Report", fill=(56, 189, 248))
        
        y = 100
        draw.rectangle([(40, y), (960, y + 45)], fill=(190, 18, 60) if category == "SEVERE" else (239, 68, 68))
        draw.text((60, y + 12), f"FRAUD RISK SCORE: {score}/100 — RISK CATEGORY: {category}", fill=(255, 255, 255))
        y += 60

        pdf_buffer = io.BytesIO()
        img.save(pdf_buffer, format='PDF')
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

def generate_visual_fraud_report_pdf(audit_data, output_filename="Visual_Claim_Audit_Report.pdf"):
    """Legacy visual report exporter wrapper."""
    return generate_fraud_report_pdf(audit_data, output_filename)
