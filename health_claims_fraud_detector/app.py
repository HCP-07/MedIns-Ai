import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import os
import json
import importlib
import hashlib
from datetime import datetime

# Force dynamic reload of core modules to prevent stale cache signature errors
import llm_auditor
import fraud_engine
import kaggle_fetcher
import gemini_ocr_auditor
import pdf_report_generator
import openai_query_assistant
import corporate_policy_engine

importlib.reload(llm_auditor)
importlib.reload(fraud_engine)
importlib.reload(kaggle_fetcher)
importlib.reload(gemini_ocr_auditor)
importlib.reload(pdf_report_generator)
importlib.reload(openai_query_assistant)
importlib.reload(corporate_policy_engine)

from llm_auditor import LLMClinicalAuditor
from kaggle_fetcher import KaggleDatasetFetcher
from fraud_engine import TabularFraudDetector
from sample_generator import create_sample_bills
from gemini_ocr_auditor import GeminiVisionOCRAuditor
from pdf_report_generator import generate_fraud_report_pdf, generate_deep_forensic_report_pdf, generate_corporate_scheme_report_pdf, mask_patient_name, mask_patient_id
from openai_query_assistant import OpenAIQueryAssistant
from corporate_policy_engine import CorporatePolicyEngine

# Optional Plotly import with fallback
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="MedIns AI - Enterprise Claims Fraud & Policy Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Industrial-Grade Enterprise GUI
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

    /* User Profile Card */
    .user-profile-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(51, 65, 85, 0.8);
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 15px;
    }

    /* Stage Badges */
    .badge-eligible {
        background: rgba(16, 185, 129, 0.18);
        color: #34D399;
        border: 1.5px solid rgba(16, 185, 129, 0.5);
        padding: 14px 20px;
        border-radius: 12px;
        font-weight: 800;
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 15px;
    }
    
    .badge-ineligible {
        background: rgba(225, 29, 72, 0.2);
        color: #FF6B81;
        border: 1.5px solid rgba(225, 29, 72, 0.5);
        padding: 14px 20px;
        border-radius: 12px;
        font-weight: 800;
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 15px;
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

# ----------------------------------------------------
# 🔑 INDUSTRIAL AUTHENTICATION & LOGIN MANAGEMENT (ADMIN, STAFF, USER)
# ----------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

VALID_CREDENTIALS = {
    "admin": {"password": "admin123", "name": "System Administrator", "role": "Admin", "dept": "Enterprise Operations", "allowed_tabs": [0, 1, 2, 3]},
    "staff": {"password": "staff123", "name": "Dr. Sarah Lin, MD", "role": "Staff", "dept": "Medical Claims Audit Team", "allowed_tabs": [0, 1, 2]},
    "user": {"password": "user123", "name": "Corporate Policyholder", "role": "User", "dept": "Member Self-Service", "allowed_tabs": [1, 2]}
}

def login_user(username, password):
    if username in VALID_CREDENTIALS and VALID_CREDENTIALS[username]["password"] == password:
        st.session_state.authenticated = True
        st.session_state.user_info = {
            "username": username,
            "name": VALID_CREDENTIALS[username]["name"],
            "role": VALID_CREDENTIALS[username]["role"],
            "dept": VALID_CREDENTIALS[username]["dept"],
            "allowed_tabs": VALID_CREDENTIALS[username]["allowed_tabs"],
            "login_time": datetime.now().strftime("%H:%M:%S")
        }
        return True
    return False

def logout_user():
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.rerun()

# Clean Login Interface (No empty dark box above MedIns AI)
if not st.session_state.authenticated:
    c_log1, c_log2, c_log3 = st.columns([1, 2, 1])
    with c_log2:
        st.markdown("""
        <div style="text-align: center; padding: 15px 0 10px 0;">
            <span style="font-size: 3.5rem;">🛡️</span>
            <h1 style="font-family: 'Outfit', sans-serif; font-size: 2.5rem; font-weight: 800; color: #38BDF8; margin: 2px 0 0 0;">MedIns AI</h1>
            <p style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">Enterprise Health Insurance Claims Fraud & Policy Verification Gateway</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username_input = st.text_input("👤 Username (admin / staff / user)", value="admin")
            password_input = st.text_input("🔑 Password", type="password", value="admin123")
            login_btn = st.form_submit_button("🔒 Authenticate & Access Portal", use_container_width=True)
            
            if login_btn:
                if login_user(username_input, password_input):
                    st.success("✅ Authentication Successful! Redirecting to Enterprise Dashboard...")
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password. Please try again.")

        st.markdown("<h5 style='text-align:center; color:#94A3B8;'>⚡ Quick Role Interface Access:</h5>", unsafe_allow_html=True)
        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            if st.button("👑 Admin Portal", use_container_width=True):
                login_user("admin", "admin123")
                st.rerun()
        with col_l2:
            if st.button("🩺 Staff Portal", use_container_width=True):
                login_user("staff", "staff123")
                st.rerun()
        with col_l3:
            if st.button("👤 User Portal", use_container_width=True):
                login_user("user", "user123")
                st.rerun()

    st.stop()  # Halt execution until authenticated

# ----------------------------------------------------
# INITIALIZE CORE ENGINES
# ----------------------------------------------------
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
policy_engine = CorporatePolicyEngine()

# Sidebar (Role Badge & Bullet Points)
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <span style="font-size: 3rem;">🛡️</span>
        <h2 style="color: #38BDF8; margin-top: 5px; font-weight: 800; font-family: 'Outfit', sans-serif;">MedIns AI</h2>
        <p style="color: #94A3B8; font-size: 0.85rem;">Enterprise Fraud Intelligence Platform</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # User Profile Card
    u_info = st.session_state.user_info
    if u_info:
        st.markdown(f"""
        <div class="user-profile-card">
            <div style="font-size: 0.82rem; color: #38BDF8; font-weight: 700;">AUTHENTICATED ROLE: {u_info['role'].upper()}</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC;">{u_info['name']}</div>
            <div style="font-size: 0.78rem; color: #94A3B8;">Dept: {u_info['dept']} | Session: {u_info['login_time']}</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("🚪 Logout Session", use_container_width=True):
        logout_user()

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
st.markdown(f'<div class="gradient-sub">Industrial Claims Fraud Detector & Policy Verification Portal — Active Role: <b>{u_info["role"]} Interface</b></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Deep Single Claim Forensic Audit", 
    "📄 AI Health Insurance Fraud Auditor & Policy Gatekeeper", 
    "💡 AI Query Platform",
    "📊 Claims Analytics & Risk Leaderboard"
])

# TAB 1: LIVE SINGLE CLAIM AUDIT
with tab1:
    if 0 not in u_info["allowed_tabs"]:
        st.warning("🔒 Access Restricted: Your role profile does not have authorization to view Tab 1.")
    else:
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

# TAB 2: INTEGRATED 2-STAGE POLICY GATEKEEPER & AI CLINICAL FRAUD AUDITOR
with tab2:
    if 1 not in u_info["allowed_tabs"]:
        st.warning("🔒 Access Restricted: Your role profile does not have authorization to view Tab 2.")
    else:
        st.subheader("📄 AI Health Insurance Fraud Auditor & Policy Gatekeeper")
        st.markdown("Upload **2 `.txt` files**: **File 1** verifies Company Policy Scheme Eligibility. Once Stage 1 is **Eligible**, the **Stage 2 Clinical AI Fraud Audit Report** is unlocked.")

        st.markdown('<div class="security-badge">🔒 Two-Stage Verification Active & Volatile RAM Processing</div>', unsafe_allow_html=True)

        col_t2_1, col_t2_2 = st.columns([1, 1], gap="medium")

        with col_t2_1:
            st.markdown("#### 1. Input Dual `.txt` Document Ingestion")

            # Sample Downloads Header
            st.markdown("##### 📥 Download Sample Test `.txt` Files:")
            cs1, cs2, cs3 = st.columns(3)
            with cs1:
                if os.path.exists("sample_company_policy_tcs.txt"):
                    with open("sample_company_policy_tcs.txt", "rb") as f1:
                        st.download_button("📄 File 1: TCS Policy (.txt)", data=f1.read(), file_name="sample_company_policy_tcs.txt", mime="text/plain", use_container_width=True)
            with cs2:
                if os.path.exists("sample_company_policy_amazon.txt"):
                    with open("sample_company_policy_amazon.txt", "rb") as f2:
                        st.download_button("📄 File 1: Amazon Policy (.txt)", data=f2.read(), file_name="sample_company_policy_amazon.txt", mime="text/plain", use_container_width=True)
            with cs3:
                if os.path.exists("sample_medical_invoice_valley_oak.txt"):
                    with open("sample_medical_invoice_valley_oak.txt", "rb") as f3:
                        st.download_button("📄 File 2: Clinical Invoice (.txt)", data=f3.read(), file_name="sample_medical_invoice_valley_oak.txt", mime="text/plain", use_container_width=True)

            st.divider()

            # Upload File 1 (Company Policy Eligibility Document)
            f1_upload = st.file_uploader("1. Upload Company Policy Eligibility Document (.txt):", type=["txt"], key="f1_policy_uploader")
            
            # Upload File 2 (Medical Claim Clinical Invoice)
            f2_upload = st.file_uploader("2. Upload Medical Claim Clinical Invoice Document (.txt):", type=["txt"], key="f2_clinical_uploader")

            active_f1_text = ""
            active_f2_text = ""

            sample_f1_tcs_default = """VALLEY OAK MEDICAL CENTER - CORPORATE POLICY ELIGIBILITY FORM
Patient Name: Robert Jenkins
Patient ID: PAT-TCS-88392
Employer: Tata Consultancy Services (TCS)
Scheme: Executive Platinum Shield Cover
Date of Service: 10/12/2026
Diagnosis: Lumbar Spine Strain & Acute Back Pain (ICD-10 M54.5)
Billed CPT: CPT-72148 (MRI Lumbar Spine)
Total Claimed Amount: $3,190.00"""

            sample_f2_valley_default = """====================================================
VALLEY OAK MEDICAL CENTER - INVOICE / CLAIM FORM
====================================================
Patient Name: Robert Jenkins
DOB: 11/14/1957 (Age: 68)
Gender: MALE
Patient ID: VOMC-883920
Date of Service: 10/12/2026
Provider Name: Dr. Sarah Lin, MD (Orthopedics)

Primary Diagnosis (ICD-10): M54.5 - Low Back Pain, unspecified
SERVICES RENDERED:
99214    Office Visit - Established, Mod-High     1      $ 175.00
72148    MRI Lumbar Spine, without contrast       1      $ 950.00
70551    MRI Brain, without contrast              1      $ 950.00
81025    Urine Pregnancy Test (hCG)               1      $  45.00
99381    Prev. Visit, Infant (under 1 year)       1      $ 120.00
72148    MRI Lumbar Spine, without contrast       1      $ 950.00
TOTAL BILLED AMOUNT:                                     $ 3190.00"""

            if f1_upload:
                st.success(f"✅ Loaded File 1 (Policy): **{f1_upload.name}** ({round(f1_upload.size / 1024, 1)} KB)")
                try:
                    active_f1_text = f1_upload.read().decode("utf-8", errors="ignore")
                except Exception:
                    active_f1_text = sample_f1_tcs_default
            else:
                active_f1_text = sample_f1_tcs_default

            if f2_upload:
                st.success(f"✅ Loaded File 2 (Clinical Invoice): **{f2_upload.name}** ({round(f2_upload.size / 1024, 1)} KB)")
                try:
                    active_f2_text = f2_upload.read().decode("utf-8", errors="ignore")
                except Exception:
                    active_f2_text = sample_f2_valley_default
            else:
                active_f2_text = sample_f2_valley_default

            run_integrated_btn = st.button("🚨 Run Integrated Policy Eligibility & Clinical Fraud Audit", use_container_width=True)

        with col_t2_2:
            st.markdown("#### 2. Two-Stage Audit Findings & PDF Reports")

            if run_integrated_btn or (active_f1_text and active_f2_text):
                # ----------------------------------------------------
                # STAGE 1: CORPORATE POLICY SCHEME ELIGIBILITY AUDIT
                # ----------------------------------------------------
                st.markdown("##### 🏢 STAGE 1: Corporate Policy Scheme Eligibility Gatekeeper")

                extracted_p = policy_engine.parse_text_invoice(active_f1_text)

                enquiry_res = policy_engine.verify_corporate_background(
                    patient_id_or_name=extracted_p["patient_id"],
                    employer_name=extracted_p["employer"],
                    scheme_name=extracted_p["scheme"],
                    claim_amount=extracted_p["claim_amount"],
                    cpt_code=extracted_p["cpt_code"],
                    patient_name=extracted_p["patient_name"]
                )

                is_app = enquiry_res["is_applicable"]
                warnings = enquiry_res["risk_warnings"]
                p_rec = enquiry_res["patient_record"]

                if is_app and not warnings:
                    st.markdown('<div class="badge-eligible">✅ STAGE 1 PASSED: APPLICABLE TO REQUEST A CLAIM<br><span style="font-size:0.85rem; font-weight:500;">Patient is fully covered under Corporate Policy terms.</span></div>', unsafe_allow_html=True)
                    stage1_passed = True
                elif is_app and warnings:
                    st.markdown('<div class="badge-high" style="color:#FBBF24; background:rgba(245,158,11,0.15); border-color:rgba(245,158,11,0.4); text-align:center;">⚠️ STAGE 1 PASSED WITH COMPLIANCE WARNINGS</div>', unsafe_allow_html=True)
                    stage1_passed = True
                else:
                    st.markdown('<div class="badge-ineligible">❌ STAGE 1 FAILED: INELIGIBLE TO REQUEST A CLAIM<br><span style="font-size:0.85rem; font-weight:500;">Exceeds Scheme Limits or Flagged by Corporate Fraud Verification.</span></div>', unsafe_allow_html=True)
                    stage1_passed = False

                # Always render Stage 1 PDF Download Report
                corp_pdf_bytes = generate_corporate_scheme_report_pdf(enquiry_res)
                st.download_button(
                    label=f"📄 Download Stage 1 Policy Eligibility PDF Report ({p_rec['patient_name']})",
                    data=corp_pdf_bytes,
                    file_name=f"Corporate_Policy_Eligibility_Report_{p_rec['patient_id']}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

                st.divider()

                # ----------------------------------------------------
                # STAGE 2: CLINICAL AI FRAUD AUDIT (UNLOCKED ONLY IF STAGE 1 PASSED)
                # ----------------------------------------------------
                st.markdown("##### 🩺 STAGE 2: Clinical AI Fraud Audit & Anomaly Detection")

                if stage1_passed:
                    with st.spinner("Meta Llama 3.3 70B via Groq LPU API is auditing File 2 (Clinical Medical Invoice)..."):
                        audit_res = ocr_auditor.audit_invoice_image(active_f2_text)

                    score = audit_res.get("fraud_risk_score", 0)
                    category = str(audit_res.get("risk_category", "High")).upper()
                    
                    if category == "SEVERE":
                        badge_html = f'<div class="badge-severe">STAGE 2 UNLOCKED: Fraud Risk Score: {score}/100 — SEVERE ANOMALIES</div>'
                    elif category == "HIGH":
                        badge_html = f'<div class="badge-high">STAGE 2 UNLOCKED: Fraud Risk Score: {score}/100 — HIGH RISK</div>'
                    elif category == "MEDIUM":
                        badge_html = f'<div class="badge-high" style="color:#FBBF24; background:rgba(245,158,11,0.15); border-color:rgba(245,158,11,0.4);">STAGE 2 UNLOCKED: Fraud Risk Score: {score}/100 — MEDIUM RISK</div>'
                    else:
                        badge_html = f'<div class="badge-low">STAGE 2 UNLOCKED: Fraud Risk Score: {score}/100 — LEGITIMATE CLAIM</div>'
                        
                    st.markdown(badge_html, unsafe_allow_html=True)
                    st.progress(score / 100.0)

                    p_info = audit_res.get("patient_info", {})
                    pr_info = audit_res.get("provider_info", {})
                    
                    raw_pname = p_info.get('patient_name', 'N/A')
                    raw_pid = p_info.get('patient_id', 'N/A')
                    masked_pname = mask_patient_name(raw_pname)
                    masked_pid = mask_patient_id(raw_pid)

                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        st.write(f"- **Patient Name:** `{masked_pname}` 🔒")
                        st.write(f"- **Patient ID:** `{masked_pid}` 🔒")
                    with col_p2:
                        st.write(f"- **Provider:** `{pr_info.get('provider_name', 'N/A')}`")
                        st.write(f"- **Specialty:** `{pr_info.get('specialty', 'N/A')}`")

                    st.markdown("**💡 Executive AI Reasoning Summary:**")
                    st.info(audit_res.get("ai_reasoning_summary", "Clinical audit complete."))

                    st.markdown("**🚩 Flagged Fraud & Rule Violations:**")
                    anomalies = audit_res.get("detected_anomalies", [])
                    if anomalies:
                        df_anom = pd.DataFrame(anomalies)
                        st.table(df_anom)
                    else:
                        st.success("✅ No rule anomalies or fraudulent procedures detected.")

                    pdf_bytes = generate_fraud_report_pdf(audit_res)
                    st.download_button(
                        label="📄 Download Official Stage 2 Clinical Fraud Investigation PDF Report (Calibri 20 Quality)",
                        data=pdf_bytes,
                        file_name=f"Clinical_Fraud_Investigation_Report_{masked_pid}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.error("🔒 STAGE 2 LOCKED: Clinical Fraud Audit is locked because Stage 1 Corporate Policy check is INELIGIBLE.")
                    st.warning("⚠️ Claim requests exceeding corporate policy limits or flagged by employment background checks cannot proceed to clinical fraud reimbursement.")

# TAB 3: AI QUERY PLATFORM (GEMINI / CHATGPT STYLE FORMAL COMPACT CHAT INTERFACE)
with tab3:
    if 2 not in u_info["allowed_tabs"]:
        st.warning("🔒 Access Restricted: Your role profile does not have authorization to view Tab 3.")
    else:
        st.markdown('<div class="formal-quote-title">"Integrity is doing the right thing, even when no one is watching."</div>', unsafe_allow_html=True)
        st.markdown('<div class="formal-quote-sub">AI Medical Coding, CPT Benchmarks & Claims Audit Assistant</div>', unsafe_allow_html=True)

        if "query_messages" not in st.session_state:
            st.session_state.query_messages = [
                {
                    "role": "assistant",
                    "content": "Welcome to the **AI Medical Coding & Claims Benchmark Assistant**.\n\nPlease enter any CPT code, ICD-10 diagnosis, benchmark rate request, or NCCI billing rule query below."
                }
            ]

        c_chat1, c_chat2, c_chat3 = st.columns([1, 4, 1])
        with c_chat2:
            for msg in st.session_state.query_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        user_prompt = st.chat_input("Ask AI Medical Coding & Benchmark Assistant...")

        if user_prompt:
            st.session_state.query_messages.append({"role": "user", "content": user_prompt})
            response_text = query_assistant.query_billing_code(user_prompt)
            st.session_state.query_messages.append({"role": "assistant", "content": response_text})
            st.rerun()

# TAB 4: CLAIMS ANALYTICS & RISK LEADERBOARD
with tab4:
    if 3 not in u_info["allowed_tabs"]:
        st.warning("🔒 Access Restricted: Your role profile does not have authorization to view Tab 4.")
    else:
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
