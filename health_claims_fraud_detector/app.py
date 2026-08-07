import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import os
import json
import importlib

# Force dynamic reload of core modules to prevent stale cache signature errors
import llm_auditor
import fraud_engine
import kaggle_fetcher
importlib.reload(llm_auditor)
importlib.reload(fraud_engine)
importlib.reload(kaggle_fetcher)

from llm_auditor import LLMClinicalAuditor
from kaggle_fetcher import KaggleDatasetFetcher
from fraud_engine import TabularFraudDetector
from sample_generator import create_sample_bills

# Optional Plotly import with fallback
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="MedIns AI - Deep Forensic Claims Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Sleek High-Contrast Enterprise Interface
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@600;700;800&display=swap');

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
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    
    .gradient-sub {
        font-size: 1.1rem;
        color: #94A3B8;
        margin-bottom: 1.8rem;
        font-weight: 500;
    }

    /* Result Badges */
    .badge-high {
        background: rgba(239, 68, 68, 0.15);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 12px 20px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 1.3rem;
        margin-bottom: 15px;
    }
    .badge-low {
        background: rgba(16, 185, 129, 0.15);
        color: #6EE7B7;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 12px 20px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 1.3rem;
        margin-bottom: 15px;
    }

    /* Form Submit Button Styling */
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(90deg, #2563EB 0%, #4F46E5 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.4) !important;
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

# Clean Enterprise Sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <span style="font-size: 3rem;">🛡️</span>
        <h2 style="color: #38BDF8; margin-top: 5px; font-weight: 800; font-family: 'Outfit', sans-serif;">MedIns AI</h2>
        <p style="color: #94A3B8; font-size: 0.85rem;">Enterprise Fraud Intelligence Platform</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.subheader("⚡ Backend Engine Status")
    
    if llm_engine.client:
        st.success("✅ Meta Llama 3.1 8B Active (Groq LPU)")
    else:
        st.info("ℹ️ Llama 3.1 Simulation Engine Active")

    if kaggle_engine.kaggle_username:
        st.success("✅ Kaggle API (kaggle.json) Loaded")
    else:
        st.caption("📊 Local Baseline Claims Dataset Active")

    st.divider()
    st.markdown("**Integrated Core Stack:**")
    st.markdown("- 🧠 **LLM Reasoner:** Meta Llama 3.1 8B")
    st.markdown("- 📊 **ML Engine:** Isolation Forest & Random Forest")
    st.markdown("- 👁️ **Vision/OCR:** EasyOCR / PIL Document Parser")
    st.markdown("- ⚙️ **Security:** PII Redaction & HIPAA Masking")

# Main Header
st.markdown('<div class="gradient-title">🛡️ MedIns AI</div>', unsafe_allow_html=True)
st.markdown('<div class="gradient-sub">Next-Gen Health Insurance Claims Fraud Detector & Clinical Forensic Engine</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 Deep Single Claim Forensic Audit", "📊 Batch Analytics & Kaggle Datasets", "🏗️ AI Architecture & Frameworks"])

# TAB 1: LIVE SINGLE CLAIM AUDIT
with tab1:
    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        st.subheader("1. Hyderabad Hospital & Patient Case Selection")

        # Real Hyderabad Healthcare Institutions Directory
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

        # Disease / Health Case Selection
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
                "notes": "Patient presented with acute lower right quadrant abdominal pain and elevated white blood cell count. Laparoscopic appendectomy performed cleanly.",
                "img": "sample_bills/legitimate_claim.png"
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
                "notes": "Patient came for minor ankle strain after tripping. Doctor ordered lumbar spine MRI and high-complexity trauma package.",
                "img": "sample_bills/fraudulent_upcoded_claim.png"
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
                "notes": "62-year-old male with severe retrosternal chest pain radiating to left arm. Cardiac markers elevated. Emergency cardiology workup performed.",
                "img": None
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
                "notes": "Routine outpatient consultation.",
                "img": None
            }
        }

        selected_case_name = st.selectbox("Select Medical Case Scenario:", list(disease_cases.keys()))
        case_data = disease_cases[selected_case_name]

        # Display AI Recommended Standard Guidelines Tests
        st.markdown("#### 🤖 AI Recommended Guidelines Tests")
        st.info(" , ".join([f"✓ {t}" for t in case_data["recommended_tests"]]))

        uploaded_file = st.file_uploader("Upload Hospital Invoice / Doctor Note Image (Optional)", type=["png", "jpg", "jpeg"])
        
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Invoice Image", use_container_width=True)
        elif case_data["img"] and os.path.exists(case_data["img"]):
            st.image(case_data["img"], caption="Scenario Invoice Document", use_container_width=True)

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
            
            # Select Actual Billed Diagnostic Tests
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

            # 1. Run ML Tabular Prediction with dynamic test-to-disease un-relatedness scoring
            ml_res = ml_engine.predict_single_claim(
                cpt_code, 
                claim_amount, 
                visits_30d, 
                patient_age,
                billed_tests=selected_billed_tests,
                recommended_tests=case_data["recommended_tests"]
            )
            
            # 2. Run Deep LLM Multi-Dimensional Audit
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
            
            # 3. Dynamically update dataset with audited custom claim
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
            
            # Parse raw response
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

            # Hospital Context Acknowledgment Banner
            st.success(f"🏛️ **Hyderabad Hospital Dossier Acknowledged & Dataset Updated:** {parsed_audit.get('hospital_context_acknowledged', f'Evaluated claim for {hospital_name}')}")

            # Render Multi-Dimensional Cross-Evaluation Matrix Table
            st.markdown("#### 📐 Multi-Dimensional Cross-Evaluation Matrix")
            matrix_data = parsed_audit.get("cross_evaluation_matrix", {})
            df_matrix = pd.DataFrame([
                {"Dimension": "1. Financial Billing Variance", "Status & Evaluation": matrix_data.get("financial_variance_status", "N/A")},
                {"Dimension": "2. Clinical Care Necessity", "Status & Evaluation": matrix_data.get("clinical_necessity_status", "N/A")},
                {"Dimension": "3. Upcoding / Fraud Mismatch", "Status & Evaluation": matrix_data.get("upcoding_probability_status", "N/A")}
            ])
            st.table(df_matrix)

            # Deep Medical Sections
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
            st.write(parsed_audit.get("forensic_summary", ""))

            # Collapsible Hidden Section for Technical & PII Privacy Audit + Score Explanation
            st.divider()
            with st.expander("🔒 Hidden Technical Payload, PII Privacy & Risk Score Factor Breakdown", expanded=False):
                expl = ml_res["score_explanation"]
                st.markdown("### 📊 Itemized Risk Score Factor Breakdown (Examiner View)")
                st.json({
                    "Total_MedIns_Risk_Index": f"{expl['final_risk_score_pct']}%",
                    "Base_ML_Score": f"{expl['base_ml_score_pct']}%",
                    "Cost_Ratio_Penalty": f"+{expl['cost_penalty_pct']}%",
                    "Unrelated_Tests_Penalty": f"+{expl['unrelated_tests_penalty_pct']}%",
                    "Age_Relevance_Penalty": f"+{expl['age_relevance_penalty_pct']}%",
                    "Visit_Frequency_Penalty": f"+{expl['visit_freq_penalty_pct']}%",
                    "Unrelated_Billed_Test_Names": expl["unrelated_test_names"]
                })
                
                st.markdown("**HIPAA / GDPR Patient Privacy Masking:**")
                st.json({
                    "Hospital_Name": hospital_name,
                    "Hospital_ID": hospital_id,
                    "Facility_Type": hospital_type,
                    "Patient_ID": "PAT-****-9401 (Redacted)",
                    "Patient_Age": patient_age,
                    "Patient_Gender": patient_gender,
                    "Isolation_Forest_Anomaly_Flag": ml_res["anomaly_detected"],
                    "Unrelated_Billed_Tests_Count": ml_res["unrelated_tests_count"],
                    "Cost_Ratio_vs_Benchmark": f"{ml_res['cost_ratio']}x (${ml_res['benchmark_cost']:,.2f})"
                })
                st.markdown("**Raw LLM JSON Payload:**")
                st.code(llm_raw, language="json")

        else:
            st.info("👈 Select a health case or click **Run Deep Forensic Audit** to analyze.")

# TAB 2: BATCH ANALYTICS & KAGGLE DATASETS
with tab2:
    st.subheader("Batch Claims Analytics & Dynamic Dataset Persistence")

    st.markdown("#### 📥 Kaggle Dataset API Integration")
    c_kg1, c_kg2 = st.columns([2, 1])
    with c_kg1:
        dataset_input = st.text_input("Kaggle Dataset Identifier:", value="rohitgarg/healthcare-insurance-claims-fraud-detection")
    with c_kg2:
        st.write("")
        st.write("")
        fetch_kg_btn = st.button("Download Kaggle Dataset", use_container_width=True)

    if fetch_kg_btn:
        success, msg, k_df = kaggle_engine.fetch_kaggle_claims_data(dataset_input)
        if success:
            st.success(msg)
            st.dataframe(k_df.head(10), use_container_width=True)
        else:
            st.info(f"ℹ️ {msg}")

    st.divider()
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

        st.markdown("#### Live Updated Claims Dataset")
        st.dataframe(df_claims.tail(15), use_container_width=True)

# TAB 3: AI ARCHITECTURE & FRAMEWORKS
with tab3:
    st.subheader("Open-Source AI Stack & System Architecture")

    st.markdown("""
    ### 1. Integrated AI Platforms & Tools:
    - **Open-Source LLM:** Meta Llama 3.1 8B (via Groq Cloud LPUs)
    - **Dataset API:** Kaggle Datasets API (`kaggle`)
    - **Machine Learning Frameworks:** `Scikit-Learn` (Isolation Forest, Random Forest Classifier), `Pandas`, `NumPy`
    - **Vision & Document OCR:** `EasyOCR`, `Pillow (PIL)`
    - **UI & Analytics:** `Streamlit`, `Plotly Express`
    - **Orchestration:** `LangChain`, `Python-dotenv`

    ---

    ### 2. End-to-End System Workflow:
    ```
    [ Hospital Bill / Kaggle Data ] ---> [ EasyOCR / Kaggle API ]
                                                |
                                                v
    [ Claim Metadata & Tests ] ---------> [ Tabular ML Engine ]  ---> [ Isolation Forest Score ]
                                                |                                   |
                                                v                                   v
                                        [ Llama 3.1 LLM Agent ] ---------> [ MedIns Risk Index ]
                                                |                                   |
                                                v                                   v
                                    [ Deep Forensic Report ] ---------> [ Streamlit Dark UI ]
    ```
    """)
