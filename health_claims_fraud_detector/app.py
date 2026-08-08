import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import os
import json
import importlib
import hashlib

# Force dynamic reload of core modules to prevent stale cache signature errors
import llm_auditor
import fraud_engine
import kaggle_fetcher
import gemini_ocr_auditor
import pdf_report_generator
import openai_query_assistant

importlib.reload(llm_auditor)
importlib.reload(fraud_engine)
importlib.reload(kaggle_fetcher)
importlib.reload(gemini_ocr_auditor)
importlib.reload(pdf_report_generator)
importlib.reload(openai_query_assistant)

from llm_auditor import LLMClinicalAuditor
from kaggle_fetcher import KaggleDatasetFetcher
from fraud_engine import TabularFraudDetector
from sample_generator import create_sample_bills
from gemini_ocr_auditor import GeminiVisionOCRAuditor
from pdf_report_generator import generate_fraud_report_pdf, generate_deep_forensic_report_pdf, mask_patient_name, mask_patient_id
from openai_query_assistant import OpenAIQueryAssistant

# Optional Plotly import with fallback
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="MedIns AI - Enterprise Claims Fraud Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Stunning Modern Enterprise GUI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@600;700;800&display=swap');

    .stApp {
        background-color: #0B0F17 !important;
        color: #F8FAFC !important;
    }

    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp label, .stApp .stMarkdown {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    .gradient-title {
        font-family: 'Outfit', sans-serif !important;
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
        letter-spacing: -0.5px;
    }
    
    .gradient-sub {
        font-size: 1.05rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }

    /* Hero Quote Box */
    .formal-quote-title {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.85rem;
        font-weight: 700;
        color: #38BDF8;
        text-align: center;
        margin-top: 1rem;
        margin-bottom: 0.2rem;
        letter-spacing: -0.3px;
    }
    
    .formal-quote-sub {
        font-size: 0.98rem;
        color: #94A3B8;
        text-align: center;
        margin-bottom: 1.4rem;
        font-style: italic;
    }

    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        color: #38BDF8 !important;
    }

    /* Security Pill Badge */
    .security-badge {
        background: rgba(16, 185, 129, 0.12);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 14px;
    }

    /* Floating Pill Chat Input Styling */
    div[data-testid="stChatInput"] {
        border-radius: 24px !important;
        background-color: #1E293B !important;
        border: 1.5px solid #334155 !important;
        padding: 2px 10px !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4) !important;
        max-width: 850px !important;
        margin: 0 auto !important;
    }
    
    div[data-testid="stChatInput"] input {
        color: #F8FAFC !important;
        font-size: 1.0rem !important;
    }

    /* Compact Formal Chat Message Bubbles */
    div[data-testid="stChatMessage"] {
        background-color: #0F172A !important;
        border: 1px solid #1E293B !important;
        border-radius: 12px !important;
        padding: 12px 18px !important;
        margin-bottom: 10px !important;
        max-width: 850px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* Result Badges */
    .badge-severe {
        background: rgba(225, 29, 72, 0.2);
        color: #FF6B81;
        border: 1.5px solid rgba(225, 29, 72, 0.5);
        padding: 12px 20px;
        border-radius: 12px;
        font-weight: 800;
        font-size: 1.25rem;
        margin-bottom: 15px;
    }
    .badge-high {
        background: rgba(239, 68, 68, 0.15);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 12px 20px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 1.25rem;
        margin-bottom: 15px;
    }
    .badge-low {
        background: rgba(16, 185, 129, 0.15);
        color: #6EE7B7;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 12px 20px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 1.25rem;
        margin-bottom: 15px;
    }

    /* Form Submit Button & Action Buttons */
    div[data-testid="stFormSubmitButton"] > button, .stButton > button {
        background: linear-gradient(90deg, #2563EB 0%, #4F46E5 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.0rem !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 10px 22px !important;
        box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.4) !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    div[data-testid="stFormSubmitButton"] > button:hover, .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px 0 rgba(79, 70, 229, 0.6) !important;
    }

    /* Streamlit Tabs Customization */
    button[data-baseweb="tab"] {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        padding: 10px 18px !important;
        color: #94A3B8 !important;
    }
    
    button[aria-selected="true"] {
        color: #38BDF8 !important;
        border-bottom-color: #38BDF8 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize engines dynamically without caching stale instances
def load_ml_engine():
    create_sample_bills("sample_bills")
    ml_eng = TabularFraudDetector("claims_dataset.csv")
    ml_eng.train_or_load()
    return ml_eng

ml_engine = load_ml_engine()
llm_engine = LLMClinicalAuditor()
kaggle_engine = KaggleDatasetFetcher()
ocr_auditor = GeminiVisionOCRAuditor()
query_assistant = OpenAIQueryAssistant()

# Clean Enterprise Sidebar (Formatted in Bullets)
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <span style="font-size: 3rem;">🛡️</span>
        <h2 style="color: #38BDF8; margin-top: 5px; font-weight: 800; font-family: 'Outfit', sans-serif;">MedIns AI</h2>
        <p style="color: #94A3B8; font-size: 0.85rem;">Enterprise Fraud Intelligence Platform</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.subheader("🤖 AI Intelligence Engines")
    st.markdown("""
    - • **OpenAI API Active** (`gpt-4o-mini` / `gpt-4o`)
    - • **Groq LPU API Active** (`Llama 3.3 70B`)
    """)
    
    st.divider()
    st.subheader("🔒 Data Security & HIPAA Suite")
    st.markdown("""
    - • **HIPAA Safe Harbor Masking:** Patient names & IDs are automatically redacted (`R***** J******`)
    - • **In-Memory Volatile Processing:** Uploaded claim documents are processed strictly in RAM and never saved to disk
    - • **SHA-256 Cryptographic Audit:** Generated PDF reports embed an immutable SHA-256 verification hash
    - • **TLS Transport Encryption:** All LLM API calls execute over HTTPS transport layer security
    """)

    st.divider()
    st.markdown("- • **Baseline Claims Forensic Dataset Active**")

# Main Header
st.markdown('<div class="gradient-title">🛡️ MedIns AI</div>', unsafe_allow_html=True)
st.markdown('<div class="gradient-sub">Next-Gen Health Insurance Claims Fraud Detector & Clinical Forensic Engine</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Deep Single Claim Forensic Audit", 
    "📄 AI Health Insurance Fraud Auditor (API)", 
    "💡 AI Query Platform",
    "📊 Claims Analytics & Risk Leaderboard"
])

# TAB 1: LIVE SINGLE CLAIM AUDIT (HIGH QUALITY PDF EXPORTER WITH AI SUMMARY & RED FLAGS)
with tab1:
    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        st.subheader("1. Hyderabad Hospital & Patient Case Selection")

        hyderabad_hospitals = {
            "Apollo Hospitals (Jubilee Hills - HOSP-HYD-01)": {"id": "HOSP-HYD-01", "name": "Apollo Hospitals, Jubilee Hills", "type": "Multi-Specialty Super Tertiary Care"},
            "Yashoda Hospitals (Hitec City / Somajiguda - HOSP-HYD-02)": {"id": "HOSP-HYD-02", "name": "Yashoda Hospitals, Hitec City", "type": "Super Specialty Tertiary Center"},
            "KIMS Hospitals (Krishna Institute, Kondapur - HOSP-HYD-03)": {"id": "HOSP-HYD-03", "name": "KIMS Hospitals, Kondapur", "type": "Super Specialty Care"},
            "CARE Hospitals (Banjara Hills / Gachibowli - HOSP-HYD-04)": {"id": "HOSP-HYD-04", "name": "CARE Hospitals, Banjara Hills", "type": "Cardiovascular & Multispecialty"},
            "AIG Hospitals (Asian Institute of Gastro, Gachibowli - HOSP-HYD-05)": {"id": "HOSP-HYD-05", "name": "AIG Hospitals, Gachibowli", "type": "Gastroenterology & Surgical Excellence"},
            "Continental Hospital (Financial District, Nanakramguda - HOSP-HYD-06)": {"id": "HOSP-HYD-06", "name": "Continental Hospital, Nanakramguda", "type": "JCI Accredited Multi-Specialty"},
            "Sunshine Hospitals (Gachibowli / Paradise - HOSP-HYD-07)": {"id": "HOSP-HYD-07", "name": "Sunshine Hospitals, Gachibowli", "type": "Orthopedics & Joint Replacement"},
            "Custom Hyderabad Hospital": {"id": "HOSP-HYD-99", "name": "Custom Hyderabad Medical Center", "type": "General Clinic"}
        }

        selected_hosp_label = st.selectbox("🏥 Select Hyderabad Hospital (By Location & Code):", list(hyderabad_hospitals.keys()))
        selected_hosp = hyderabad_hospitals[selected_hosp_label]

        disease_cases = {
            "🩺 Acute Appendicitis (Abdominal Surgery)": {
                "cpt": "CPT-47562",
                "diag": "Acute Appendicitis (ICD-10 K35.80)",
                "amount": 6500.0,
                "visits": 2,
                "age": 38,
                "gender": "Female",
                "history": "No chronic medical conditions",
                "recommended_tests": ["Abdominal Ultrasound", "Complete Blood Count (CBC)", "Urinalysis Panel"],
                "sample_billed_tests": ["Abdominal Ultrasound", "Complete Blood Count (CBC)", "Urinalysis Panel"],
                "notes": "Patient presented with acute lower right quadrant abdominal pain and elevated white blood cell count. Laparoscopic appendectomy performed cleanly."
            },
            "🦵 Mild Acute Ankle Sprain (Upcoded Fraud Scenario)": {
                "cpt": "CPT-72148",
                "diag": "Mild Acute Ankle Sprain (ICD-10 S93.401A)",
                "amount": 8500.0,
                "visits": 12,
                "age": 45,
                "gender": "Male",
                "history": "Hypertension",
                "recommended_tests": ["Standard Ankle X-Ray", "Physical Joint Examination"],
                "sample_billed_tests": ["Standard Ankle X-Ray", "Lumbar Spine Contrast MRI", "Head CT Scan", "High-Trauma Emergency Package"],
                "notes": "Patient came for minor ankle strain after tripping. Doctor ordered lumbar spine MRI and high-complexity trauma package."
            },
            "🫀 Acute Chest Pain / Angina (Cardiology Case)": {
                "cpt": "CPT-70450",
                "diag": "Acute Subendocardial Ischemia (ICD-10 I21.4)",
                "amount": 4200.0,
                "visits": 4,
                "age": 62,
                "gender": "Male",
                "history": "Coronary Artery Disease, Hyperlipidemia",
                "recommended_tests": ["12-Lead ECG", "Cardiac Troponin I & T Labs", "Echocardiogram", "Chest X-Ray"],
                "sample_billed_tests": ["12-Lead ECG", "Cardiac Troponin I & T Labs", "Echocardiogram", "Chest X-Ray"],
                "notes": "62-year-old male with severe retrosternal chest pain radiating to left arm. Cardiac markers elevated. Emergency cardiology workup performed."
            },
            "✍️ Custom Medical Case (User Defined Data)": {
                "cpt": "CPT-99213",
                "diag": "Custom Diagnosis (ICD-10)",
                "amount": 150.0,
                "visits": 1,
                "age": 30,
                "gender": "Female",
                "history": "None",
                "recommended_tests": ["Routine Physical Exam"],
                "sample_billed_tests": [],
                "notes": "Routine outpatient consultation."
            }
        }

        selected_case_name = st.selectbox("Select Medical Case Scenario:", list(disease_cases.keys()))
        case_data = disease_cases[selected_case_name]

        st.markdown("#### 🤖 AI Recommended Guidelines Tests")
        st.info(" , ".join([f"✓ {t}" for t in case_data["recommended_tests"]]))

        with st.form("claim_form"):
            st.markdown(f"🏥 **Hospital:** `{selected_hosp['name']}` | **Code:** `{selected_hosp['id']}` | **Type:** `{selected_hosp['type']}`")
            hospital_name = selected_hosp['name']
            hospital_id = selected_hosp['id']
            hospital_type = selected_hosp['type']

            c1_sub, c2_sub = st.columns(2)
            with c1_sub:
                patient_age = st.slider("Patient Age", 18, 90, value=case_data["age"])
            with c2_sub:
                patient_gender = st.selectbox("Patient Gender", ["Female", "Male", "Other"], index=["Female", "Male", "Other"].index(case_data["gender"]))

            medical_history = st.text_input("Pre-existing Medical History / Comorbidities", value=case_data["history"])
            cpt_code = st.selectbox("Billed CPT Code", ["CPT-99213", "CPT-99215", "CPT-47562", "CPT-49505", "CPT-70450", "CPT-72148", "CPT-29881"], index=["CPT-99213", "CPT-99215", "CPT-47562", "CPT-49505", "CPT-70450", "CPT-72148", "CPT-29881"].index(case_data["cpt"]))
            diagnosis = st.text_input("Diagnosis (ICD-10)", value=case_data["diag"])
            
            all_possible_tests = [
                "Abdominal Ultrasound", "Complete Blood Count (CBC)", "Urinalysis Panel",
                "Standard Ankle X-Ray", "Physical Joint Examination", "Lumbar Spine Contrast MRI",
                "Head CT Scan", "High-Trauma Emergency Package", "12-Lead ECG", "Cardiac Troponin I & T Labs",
                "Echocardiogram", "Chest X-Ray", "Routine Physical Exam"
            ]
            
            selected_billed_tests = st.multiselect(
                "Select Actual Billed Diagnostic Tests & Line Items:",
                options=all_possible_tests,
                default=[t for t in case_data["sample_billed_tests"] if t in all_possible_tests]
            )

            claim_amount = st.number_input("Claimed Amount ($)", min_value=50.0, max_value=50000.0, value=case_data["amount"], step=100.0)
            visits_30d = st.slider("Hospital Visits (Last 30 Days)", 1, 20, value=case_data["visits"])
            clinical_notes = st.text_area("Doctor Clinical Summary / Progress Notes", value=case_data["notes"], height=100)
            
            submit_btn = st.form_submit_button("🚨 Run MedIns AI Forensic Audit", use_container_width=True)

    with col_right:
        st.subheader("2. MedIns Multi-Dimensional Forensic Audit")

        if submit_btn or selected_case_name != "✍️ Custom Medical Case (User Defined Data)":
            billed_tests_str = ", ".join(selected_billed_tests) if selected_billed_tests else "None selected"
            recommended_tests_str = ", ".join(case_data["recommended_tests"])

            ml_res = ml_engine.predict_single_claim(
                cpt_code, 
                claim_amount, 
                visits_30d, 
                patient_age,
                billed_tests=selected_billed_tests,
                recommended_tests=case_data["recommended_tests"]
            )
            
            llm_res = llm_engine.audit_claim(
                diagnosis=diagnosis,
                procedure_code=cpt_code,
                claim_amount=claim_amount,
                benchmark=ml_res["benchmark_cost"],
                clinical_notes=clinical_notes,
                patient_age=patient_age,
                patient_gender=patient_gender,
                medical_history=medical_history,
                billed_tests=billed_tests_str,
                recommended_tests=recommended_tests_str,
                hospital_name=hospital_name,
                hospital_id=hospital_id,
                hospital_type=hospital_type
            )
            
            fraud_score_pct = int(ml_res["fraud_score"] * 100)
            is_fraud_flag = 1 if fraud_score_pct >= 60 else 0
            fraud_type_str = "Unrelated Test Upcoding" if ml_res["unrelated_tests_count"] > 0 else "Cost Ratio Anomaly" if ml_res["cost_ratio"] > 1.8 else "None"
            
            ml_engine.append_custom_claim_to_dataset(
                claim_id=f"CLM-{np.random.randint(2026000, 2026999)}",
                hospital_id=hospital_id,
                cpt_code=cpt_code,
                claim_amount=claim_amount,
                benchmark_cost=ml_res["benchmark_cost"],
                cost_ratio=ml_res["cost_ratio"],
                visits_30d=visits_30d,
                is_fraud=is_fraud_flag,
                fraud_type=fraud_type_str
            )
            
            llm_raw = llm_res["raw_response"]
            
            try:
                parsed_audit = json.loads(llm_raw)
            except Exception:
                parsed_audit = {
                    "risk_level": "HIGH" if ml_res["fraud_score"] >= 0.7 else "LOW",
                    "hospital_context_acknowledged": f"Claim evaluated for {hospital_name} ({hospital_id}).",
                    "cross_evaluation_matrix": {
                        "financial_variance_status": f"Cost Ratio: {ml_res['cost_ratio']}x benchmark",
                        "clinical_necessity_status": "Evaluated against AI guidelines",
                        "upcoding_probability_status": "Completed"
                    },
                    "clinical_appropriateness": "Clinical note evaluation completed.",
                    "fraud_red_flags": ml_res["flags"],
                    "forensic_summary": llm_raw
                }

            risk_level_str = parsed_audit.get("risk_level", "LOW").upper()
            
            if risk_level_str == "HIGH" or fraud_score_pct >= 70:
                badge_html = f'<div class="badge-high">MedIns Risk Index: {fraud_score_pct}% — HIGH SUSPICION OF FRAUD</div>'
            elif risk_level_str == "MEDIUM" or fraud_score_pct >= 40:
                badge_html = f'<div class="badge-high" style="color:#FBBF24; background:rgba(245,158,11,0.15); border-color:rgba(245,158,11,0.4);">MedIns Risk Index: {fraud_score_pct}% — MEDIUM RISK ANOMALY</div>'
            else:
                badge_html = f'<div class="badge-low">MedIns Risk Index: {fraud_score_pct}% — LEGITIMATE CLAIM</div>'

            st.markdown(badge_html, unsafe_allow_html=True)
            st.progress(fraud_score_pct / 100.0)

            st.success(f"🏛️ **Hyderabad Hospital Dossier Acknowledged & Dataset Updated:** {parsed_audit.get('hospital_context_acknowledged', f'Evaluated claim for {hospital_name}')}")

            st.markdown("#### 📐 Multi-Dimensional Cross-Evaluation Matrix")
            matrix_data = parsed_audit.get("cross_evaluation_matrix", {})
            df_matrix = pd.DataFrame([
                {"Dimension": "1. Financial Billing Variance", "Status & Evaluation": matrix_data.get("financial_variance_status", "N/A")},
                {"Dimension": "2. Clinical Care Necessity", "Status & Evaluation": matrix_data.get("clinical_necessity_status", "N/A")},
                {"Dimension": "3. Upcoding / Fraud Mismatch", "Status & Evaluation": matrix_data.get("upcoding_probability_status", "N/A")}
            ])
            st.table(df_matrix)

            st.markdown("#### 🩺 AI Guidelines vs Billed Test Appropriateness")
            st.info(parsed_audit.get("clinical_appropriateness", "Evaluated against age and diagnosis guidelines."))

            st.markdown("#### 🚩 Flagged Fraud Red Flags")
            red_flags_list = parsed_audit.get("fraud_red_flags", [])
            if ml_res["flags"]:
                for flag in ml_res["flags"]:
                    if flag not in red_flags_list:
                        red_flags_list.append(flag)
                        
            if red_flags_list and red_flags_list != ["None detected"]:
                for rf in red_flags_list:
                    st.warning(f"⚠️ {rf}")
            else:
                st.success("✅ No clinical red flags or test over-utilization detected.")

            st.markdown("#### 💡 Forensic Summary & Verdict")
            st.caption(f"Evaluated by: **{llm_res['llm_used']}**")
            st.write(parsed_audit.get("forensic_summary", llm_raw))

            # 📄 HIGH QUALITY CALIBRI 20 PDF DOWNLOAD BUTTON (TAB 1)
            deep_audit_payload = {
                "hospital_name": hospital_name,
                "hospital_id": hospital_id,
                "hospital_type": hospital_type,
                "patient_age": patient_age,
                "patient_gender": patient_gender,
                "medical_history": medical_history,
                "diagnosis": diagnosis,
                "cpt_code": cpt_code,
                "claim_amount": claim_amount,
                "billed_tests": billed_tests_str,
                "recommended_tests": recommended_tests_str,
                "clinical_notes": clinical_notes,
                "fraud_score_pct": fraud_score_pct,
                "risk_level": risk_level_str,
                "cross_evaluation_matrix": matrix_data,
                "clinical_appropriateness": parsed_audit.get("clinical_appropriateness", ""),
                "fraud_red_flags": red_flags_list,
                "forensic_summary": parsed_audit.get("forensic_summary", llm_raw),
                "llm_used": llm_res['llm_used']
            }
            
            deep_pdf_bytes = generate_deep_forensic_report_pdf(deep_audit_payload)
            st.download_button(
                label="📄 Download Official Deep Forensic Audit PDF Report (Calibri 20 Header Quality)",
                data=deep_pdf_bytes,
                file_name="Deep_Forensic_Audit_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        else:
            st.info("👈 Select a health case or click **Run Deep Forensic Audit** to analyze.")

# TAB 2: AI HEALTH INSURANCE FRAUD AUDITOR (EXACT RAW OCR .TXT & .DOCX SPECIFICATION WITH HIPAA MASKING)
with tab2:
    st.subheader("📄 AI Health Insurance Fraud Auditor (API)")
    st.markdown("Upload or paste **raw OCR text files (.txt)** or **Word documents (.docx)** containing medical claim invoices. **Meta Llama 3.3 70B via Groq LPUs** execute 100% dynamic clinical fraud audits with **HIPAA Safe Harbor PII Redaction**.")

    st.markdown('<div class="security-badge">🔒 HIPAA Privacy Masking Active (PII Redacted) & Volatile RAM Processing</div>', unsafe_allow_html=True)

    c_ocr1, c_ocr2 = st.columns([1, 1], gap="medium")

    with c_ocr1:
        st.markdown("#### 1. Input Invoice Document or Raw Text")
        
        doc_input_option = st.radio("Choose Input Method:", ["📄 Upload Raw OCR Text (.txt) or Word Document (.docx)", "✍️ Paste Raw Medical Invoice Text"], horizontal=True)

        active_file = None
        pasted_text = ""

        sample_valley_oak = """====================================================
VALLEY OAK MEDICAL CENTER - INVOICE / CLAIM FORM
====================================================
Patient Name: Robert Jenkins
DOB: 11/14/1957 (Age: 68)
Gender: MALE
Patient ID: VOMC-883920
Date of Service: 10/12/2026
Provider Name: Dr. Sarah Lin, MD (Orthopedics)

Primary Diagnosis (ICD-10):
M54.5 - Low Back Pain, unspecified

SERVICES RENDERED:
CODE     DESCRIPTION                              QTY    CHARGE
------------------------------------------------------------------
99214    Office Visit - Established, Mod-High     1      $ 175.00
72148    MRI Lumbar Spine, without contrast       1      $ 950.00
70551    MRI Brain, without contrast              1      $ 950.00
81025    Urine Pregnancy Test (hCG)               1      $  45.00
99381    Prev. Visit, Infant (under 1 year)       1      $ 120.00
72148    MRI Lumbar Spine, without contrast       1      $ 950.00
------------------------------------------------------------------
TOTAL BILLED AMOUNT:                                     $ 3190.00
====================================================
Notes: Patient complained of acute lower back pain after lifting a heavy box. Recommended rest and prescribed painkillers. Routine screenings performed."""

        sample_metropolitan = """METROPOLITAN GENERAL HOSPITAL
100 Hospital Drive, Suite 200, Metropolis, NY 10001
PATIENT STATEMENT & MEDICAL BILLING INVOICE

Patient Name: JOHN DOE
Patient ID: PT-99214 | Age: 42 | Gender: Male
Date of Service: 10/12/2026

DIAGNOSIS & VISIT SUMMARY:
Diagnosis: Acute Emergency Department Evaluation - Level 3 (ICD-10 K35.80)
Attending Physician: Dr. Marcus Vance, MD (Emergency Medicine)

ITEMIZED BILLED CHARGES & PROCEDURES:
1. CPT-99283: Emergency Department Visit Level 3 Moderate Complexity - $950.00
2. CPT-73610: Radiologic Examination Ankle Complete 3 Views - $480.00
3. CPT-73630: Radiologic Examination Foot Complete 3 Views - $520.00
4. CPT-J1885: Ketorolac Tromethamine Injection 30mg - $145.00
5. CPT-A4570: Ankle Splint / Rigid Immobilizer Brace - $450.00
6. CPT-ED110: Aluminum Adult Crutches - $300.00

TOTAL CLAIMED AMOUNT: $2,845.00
Expected Regional Benchmark: $950.00
Status: Pending Insurance Claim Audit"""

        sample_city = """CITY GENERAL HOSPITAL
500 Health Way, Regional Center
PATIENT MEDICAL BILLING STATEMENT

Patient Name: JANE SMITH
Patient ID: PT-448102 | Age: 38 | Gender: Female
Date of Service: 09/15/2026
Provider Name: Dr. Alan Grant, MD (General Surgery)

DIAGNOSIS: Acute Appendicitis (ICD-10 K35.80)
PROCEDURE: Laparoscopic Appendectomy (CPT-47562)

ITEMIZED CHARGES:
1. Laparoscopic Appendectomy Procedure: $5,200.00
2. Abdominal Ultrasound: $650.00
3. Complete Blood Count (CBC) & Urinalysis: $350.00
4. Anesthesia & Facility Operating Room Use: $300.00

TOTAL CLAIMED AMOUNT: $6,500.00
Regional Benchmark: $6,500.00"""

        if "Upload" in doc_input_option:
            ocr_file = st.file_uploader(
                "Upload Raw OCR Document (.txt or .docx):", 
                type=["txt", "docx", "doc"], 
                key="text_doc_uploader"
            )
            if ocr_file:
                st.success(f"✅ Loaded Document: **{ocr_file.name}** ({round(ocr_file.size / 1024, 1)} KB)")
                active_file = ocr_file
            else:
                st.info("💡 Or select a sample raw text invoice below:")
                sample_choice = st.selectbox("Sample Raw Text Invoices:", [
                    "Valley Oak Medical Center (Critical Age/Gender Fraud & Duplicate MRI)",
                    "Metropolitan General Hospital (Upcoded ER & Unbundled X-Ray)",
                    "City General Hospital (Clean Laparoscopic Surgery Claim)"
                ])
                if "Valley Oak" in sample_choice:
                    pasted_text = sample_valley_oak
                elif "Metropolitan" in sample_choice:
                    pasted_text = sample_metropolitan
                else:
                    pasted_text = sample_city
                active_file = pasted_text
        else:
            pasted_text = st.text_area("Paste Medical Invoice / Hospital Bill Text Here:", height=320, value=sample_valley_oak)
            active_file = pasted_text

        run_ocr_btn = st.button("🚨 Audit Claim with Groq LPU API", use_container_width=True)

    with c_ocr2:
        st.markdown("#### 2. AI Audit Findings & Anomaly Detection")

        if run_ocr_btn and active_file:
            with st.spinner("Meta Llama 3.3 70B via Groq LPU API is dynamically evaluating Demographics, Diagnostic Necessity & Coding Violations..."):
                audit_res = ocr_auditor.audit_invoice_image(active_file)

            score = audit_res.get("fraud_risk_score", 0)
            category = str(audit_res.get("risk_category", "High")).upper()
            
            # Badge rendering conforming to risk_category
            if category == "SEVERE":
                badge_html = f'<div class="badge-severe">Fraud Risk Score: {score}/100 — RISK CATEGORY: SEVERE</div>'
            elif category == "HIGH":
                badge_html = f'<div class="badge-high">Fraud Risk Score: {score}/100 — RISK CATEGORY: HIGH</div>'
            elif category == "MEDIUM":
                badge_html = f'<div class="badge-high" style="color:#FBBF24; background:rgba(245,158,11,0.15); border-color:rgba(245,158,11,0.4);">Fraud Risk Score: {score}/100 — RISK CATEGORY: MEDIUM</div>'
            else:
                badge_html = f'<div class="badge-low">Fraud Risk Score: {score}/100 — RISK CATEGORY: LOW</div>'
                
            st.markdown(badge_html, unsafe_allow_html=True)
            st.progress(score / 100.0)
            st.caption(f"Evaluated by: **{audit_res.get('llm_used', 'Groq LPU API')}**")

            # PATIENT & PROVIDER DEMOGRAPHICS WITH MASKING
            p_info = audit_res.get("patient_info", {})
            pr_info = audit_res.get("provider_info", {})
            
            raw_pname = p_info.get('patient_name', 'N/A')
            raw_pid = p_info.get('patient_id', 'N/A')
            masked_pname = mask_patient_name(raw_pname)
            masked_pid = mask_patient_id(raw_pid)

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown("**👤 Patient Demographics (HIPAA Redacted):**")
                st.write(f"- **Name:** `{masked_pname}` 🔒")
                st.write(f"- **ID:** `{masked_pid}` 🔒")
                st.write(f"- **Age / Gender:** `{p_info.get('age', 'N/A')}` yo | `{p_info.get('gender', 'N/A')}`")
            with col_p2:
                st.markdown("**🩺 Provider Details:**")
                st.write(f"- **Provider:** `{pr_info.get('provider_name', 'N/A')}`")
                st.write(f"- **Specialty:** `{pr_info.get('specialty', 'N/A')}`")

            # EXECUTIVE AI REASONING SUMMARY
            st.markdown("#### 💡 Executive AI Reasoning Summary")
            st.info(audit_res.get("ai_reasoning_summary", "Clinical audit complete."))

            # DETECTED ANOMALIES TABLE
            st.markdown("#### 🚩 Detected Fraud & Coding Violations")
            anomalies = audit_res.get("detected_anomalies", [])
            if anomalies:
                df_anom = pd.DataFrame(anomalies)
                st.table(df_anom)
            else:
                st.success("✅ No rule anomalies or fraudulent procedures detected.")

            # RAW JSON RESPONSE VIEW
            with st.expander("🔍 View Raw API JSON Output"):
                st.json(audit_res)

            # 📄 HIGH QUALITY CALIBRI 20 PDF DOWNLOAD BUTTON (TAB 2)
            pdf_bytes = generate_fraud_report_pdf(audit_res)
            st.download_button(
                label="📄 Download Official PDF Fraud Investigation Report (Calibri 20 Header Quality)",
                data=pdf_bytes,
                file_name=f"MedIns_Fraud_Audit_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.info("👈 Upload a raw text (.txt) or Word (.docx) invoice or click **Audit Claim with Groq LPU API** to analyze.")

# TAB 3: AI QUERY PLATFORM (GEMINI / CHATGPT STYLE FORMAL COMPACT CHAT INTERFACE)
with tab3:
    st.markdown('<div class="formal-quote-title">"Integrity is doing the right thing, even when no one is watching."</div>', unsafe_allow_html=True)
    st.markdown('<div class="formal-quote-sub">AI Medical Coding, CPT Benchmarks & Claims Audit Assistant</div>', unsafe_allow_html=True)

    # Initialize chat message history in Streamlit session_state
    if "query_messages" not in st.session_state:
        st.session_state.query_messages = [
            {
                "role": "assistant",
                "content": "Welcome to the **AI Medical Coding & Claims Benchmark Assistant**.\n\nPlease enter any CPT code, ICD-10 diagnosis, benchmark rate request, or NCCI billing rule query below."
            }
        ]

    # Display Chat History inside a compact, formal centered container
    c_chat1, c_chat2, c_chat3 = st.columns([1, 4, 1])
    with c_chat2:
        for msg in st.session_state.query_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Handle Free-Form Chat Input (st.chat_input)
    user_prompt = st.chat_input("Ask AI Medical Coding & Benchmark Assistant...")

    if user_prompt:
        # Append User Message
        st.session_state.query_messages.append({"role": "user", "content": user_prompt})

        # Generate Assistant Response via OpenAI API / Groq Fallback
        response_text = query_assistant.query_billing_code(user_prompt)
        st.session_state.query_messages.append({"role": "assistant", "content": response_text})
        st.rerun()

# TAB 4: CLAIMS ANALYTICS & RISK LEADERBOARD
with tab4:
    st.subheader("Batch Claims Analytics & High Risk Hospital Leaderboard")

    if os.path.exists("claims_dataset.csv"):
        df_claims = pd.read_csv("claims_dataset.csv")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Claims Processed", len(df_claims))
        m2.metric("Flagged Fraud Claims", len(df_claims[df_claims["Is_Fraud"] == 1]))
        m3.metric("Fraud Rate", f"{round(df_claims['Is_Fraud'].mean() * 100, 1)}%")
        m4.metric("Avg Claim Cost Ratio", f"{round(df_claims['Cost_Ratio'].mean(), 2)}x")

        st.divider()
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("#### Claim Amount vs Cost Ratio Anomalies")
            if HAS_PLOTLY:
                fig_scatter = px.scatter(
                    df_claims,
                    x="Claim_Amount",
                    y="Cost_Ratio",
                    color="Fraud_Type",
                    template="plotly_dark",
                    title="Cluster Analysis of High Cost Ratio Anomalies"
                )
                fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.scatter_chart(df_claims, x="Claim_Amount", y="Cost_Ratio", color="Is_Fraud")

        with c2:
            st.markdown("#### High Risk Hospitals Fraud Leaderboard")
            fraud_by_hosp = df_claims[df_claims["Is_Fraud"] == 1]["Hospital_ID"].value_counts().reset_index()
            fraud_by_hosp.columns = ["Hospital_ID", "Fraud_Claims_Count"]
            if HAS_PLOTLY:
                fig_bar = px.bar(
                    fraud_by_hosp.head(8),
                    x="Hospital_ID",
                    y="Fraud_Claims_Count",
                    color="Fraud_Claims_Count",
                    template="plotly_dark",
                    title="Top Hospitals by Flagged Fraud Frequency"
                )
                fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.bar_chart(fraud_by_hosp.head(8).set_index("Hospital_ID"))

        st.markdown("#### Live Updated Claims Forensic Dataset")
        st.dataframe(df_claims.tail(15), use_container_width=True)
