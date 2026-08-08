import os
import io
import textwrap
from PIL import Image, ImageDraw

def clean_text_for_pdf(text):
    """Escapes XML characters for ReportLab Paragraphs."""
    if not isinstance(text, str):
        text = str(text)
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def generate_fraud_report_pdf(audit_data, output_filename="MedIns_Fraud_Audit_Report.pdf"):
    """
    Generates a professional PDF Forensic Audit Report using ReportLab or PIL canvas.
    Renders exact requested schema:
    - patient_info & provider_info
    - fraud_risk_score & risk_category
    - ai_reasoning_summary
    - detected_anomalies (type, severity, code_involved, description)
    """
    patient_info = audit_data.get('patient_info', {})
    provider_info = audit_data.get('provider_info', {})
    
    p_id = str(patient_info.get('patient_id', 'N/A'))
    p_name = str(patient_info.get('patient_name', 'N/A'))
    p_age = str(patient_info.get('age', 'N/A'))
    p_gender = str(patient_info.get('gender', 'N/A'))
    
    doc_name = str(provider_info.get('provider_name', 'N/A'))
    doc_spec = str(provider_info.get('specialty', 'N/A'))

    score = audit_data.get('fraud_risk_score', 0)
    category = str(audit_data.get('risk_category', 'Severe')).upper()
    summary_text = str(audit_data.get('ai_reasoning_summary', 'AI evaluation complete.'))
    anomalies = audit_data.get('detected_anomalies', [])
    llm_used = audit_data.get('llm_used', 'Groq LPU API')

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0F172A'), spaceAfter=4)
        sub_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#64748B'), spaceAfter=10)
        h2_style = ParagraphStyle('Heading2Custom', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#1E293B'), spaceBefore=8, spaceAfter=4)
        body_style = ParagraphStyle('BodyCustom', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#334155'), leading=13)
        summary_style = ParagraphStyle('SummaryCustom', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#0F172A'), leading=14)

        elements = []

        # Header
        elements.append(Paragraph("🛡️ MedIns AI — Health Insurance Fraud Audit Report", title_style))
        elements.append(Paragraph(f"Official Claim Docket #: {clean_text_for_pdf(p_id)} | Evaluated by: {clean_text_for_pdf(llm_used)}", sub_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#CBD5E1'), spaceAfter=10))

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

        # Patient & Provider Info Table
        elements.append(Paragraph("<b>📋 Patient & Provider Demographics</b>", h2_style))
        demo_data = [
            [Paragraph(f"<b>Patient Name:</b> {clean_text_for_pdf(p_name)}", body_style), Paragraph(f"<b>Patient ID:</b> {clean_text_for_pdf(p_id)}", body_style)],
            [Paragraph(f"<b>Age / Gender:</b> {clean_text_for_pdf(p_age)} yo | {clean_text_for_pdf(p_gender)}", body_style), Paragraph(f"<b>Provider:</b> {clean_text_for_pdf(doc_name)} ({clean_text_for_pdf(doc_spec)})", body_style)]
        ]
        t_demo = Table(demo_data, colWidths=[270, 270])
        t_demo.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(t_demo)
        elements.append(Spacer(1, 8))

        # Executive AI Reasoning Summary
        elements.append(Paragraph("<b>💡 Executive AI Reasoning Summary</b>", h2_style))
        summary_table = Table([[Paragraph(clean_text_for_pdf(summary_text), summary_style)]], colWidths=[540])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BFDBFE')),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 8))

        # Detected Anomalies Table
        elements.append(Paragraph("<b>🚩 Flagged Fraud & Rule Anomalies</b>", h2_style))
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
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_anom)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        print(f"ReportLab PDF generation error, using multi-line PIL canvas fallback: {e}")
        img = Image.new('RGB', (1000, 1400), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Header Box
        draw.rectangle([(0, 0), (1000, 80)], fill=(15, 23, 42))
        draw.text((40, 25), "MedIns AI - Health Insurance Fraud Audit Report", fill=(56, 189, 248))
        
        y = 100
        # Risk Score Banner
        draw.rectangle([(40, y), (960, y + 45)], fill=(190, 18, 60) if category == "SEVERE" else (239, 68, 68))
        draw.text((60, y + 12), f"FRAUD RISK SCORE: {score}/100 — RISK CATEGORY: {category}", fill=(255, 255, 255))
        y += 60

        draw.text((40, y), f"Patient: {p_name} ({p_id}) | Age: {p_age} | Gender: {p_gender}", fill=(15, 23, 42))
        y += 20
        draw.text((40, y), f"Provider: {doc_name} ({doc_spec})", fill=(15, 23, 42))
        y += 30

        # AI Reasoning Summary (Full Multi-Line Wrapping)
        draw.text((40, y), "EXECUTIVE AI REASONING SUMMARY:", fill=(30, 58, 138))
        y += 25
        sum_lines = textwrap.wrap(summary_text, width=110)
        for s_line in sum_lines:
            draw.text((40, y), s_line, fill=(51, 65, 85))
            y += 20
        y += 20

        # Detected Anomalies Section
        draw.text((40, y), "FLAGGED RULE & FRAUD ANOMALIES:", fill=(15, 23, 42))
        y += 25
        for a in anomalies:
            a_type = a.get('type', 'Anomaly')
            a_sev = a.get('severity', 'High')
            a_code = a.get('code_involved', 'N/A')
            a_desc = a.get('description', '')
            draw.text((40, y), f"• [{a_type}] (Severity: {a_sev} | Code: {a_code})", fill=(225, 29, 72))
            y += 20
            desc_lines = textwrap.wrap(a_desc, width=105)
            for d_line in desc_lines:
                draw.text((60, y), d_line, fill=(71, 85, 105))
                y += 18
            y += 8

        pdf_buffer = io.BytesIO()
        img.save(pdf_buffer, format='PDF')
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
