import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import os
import json

# Optional Plotly import with fallback
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from fraud_engine import TabularFraudDetector
from llm_auditor import LLMClinicalAuditor
from sample_generator import create_sample_bills

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="MedIns AI - Claims Fraud Detector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Safe styling without overriding Streamlit's Material Icons font ligatures
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@600;700;800&display=swap');

    /* Target specific typography ONLY - do NOT use wildcard overrides that break Material Symbols font ligatures */
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

# Initialize engines
@st.cache_resource
def load_engines():
    create_sample_bills("sample_bills")
    ml_engine = TabularFraudDetector("claims_dataset.csv")
    ml_engine.train_or_load()
    llm_engine = LLMClinicalAuditor()
    return ml_engine, llm_engine

ml_engine, llm_engine = load_engines()

# Sidebar Setup & API Key configuration
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <span style="font-size: 3rem;">🛡️</span>
        <h2 style="color: #38BDF8; margin-top: 5px; font-weight: 800; font-family: 'Outfit', sans-serif;">MedIns AI</h2>
        <p style="color: #94A3B8; font-size: 0.85rem;">Enterprise Fraud Intelligence Platform</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.subheader("🔑 Open-Source LLM Setup")
    groq_key_input = st.text_input("Groq API Key (Llama 3.1)", type="password", help="Enter free key from console.groq.com for live Llama 3.1 LLM reasoning.")
    
    if groq_key_input:
        os.environ["GROQ_API_KEY"] = groq_key_input
        llm_engine = LLMClinicalAuditor()
        st.success("✅ Connected to Groq (Llama 3.1)")
    else:
        st.info("💡 Running in Simulation Mode (No key required for demo). Enter Groq key for live LLM inference.")

    st.divider()
    st.markdown("**Open-Source Tech Stack:**")
    st.markdown("- 🧠 **LLM:** Meta Llama 3.1 8B")
    st.markdown("- 📊 **ML Engine:** Isolation Forest & Random Forest")
    st.markdown("- 👁️ **Vision/OCR:** EasyOCR / PIL")
    st.markdown("- ⚡ **Inference:** Groq API / Local Fallback")

# Main Header
st.markdown('<div class="gradient-title">🛡️ MedIns AI</div>', unsafe_allow_html=True)
st.markdown('<div class="gradient-sub">Next-Gen Health Insurance Claims Fraud Detector & Clinical Forensic Engine</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 Live Single Claim Audit", "📊 Batch Analytics & Hospital Insights", "🏗️ AI Architecture & Frameworks"])

# TAB 1: LIVE SINGLE CLAIM AUDIT
with tab1:
    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        st.subheader("1. Claim Input & Invoice Upload")

        sample_choice = st.selectbox(
            "Select Scenario for Live Demo:",
            ["Custom Manual Entry", "Sample 1: Legitimate Claim (Appendectomy)", "Sample 2: Fraudulent Upcoding (Ankle Sprain -> Spine MRI)"]
        )

        default_cpt = "CPT-47562"
        default_diag = "Acute Appendicitis (ICD-10 K35.80)"
        default_amount = 6500.0
        default_visits = 2
        default_age = 38
        default_notes = "Patient presented with acute lower right quadrant pain. Laparoscopic appendectomy performed cleanly."
        sample_img_path = None

        if sample_choice == "Sample 1: Legitimate Claim (Appendectomy)":
            default_cpt = "CPT-47562"
            default_diag = "Acute Appendicitis (ICD-10 K35.80)"
            default_amount = 6500.0
            default_visits = 2
            default_age = 38
            default_notes = "Patient presented with acute lower right quadrant abdominal pain. Laparoscopic appendectomy performed without complications."
            sample_img_path = "sample_bills/legitimate_claim.png"

        elif sample_choice == "Sample 2: Fraudulent Upcoding (Ankle Sprain -> Spine MRI)":
            default_cpt = "CPT-72148"
            default_diag = "Mild Acute Ankle Sprain (ICD-10 S93.401A)"
            default_amount = 8500.0
            default_visits = 12
            default_age = 45
            default_notes = "Patient came for minor ankle strain after tripping. Doctor ordered lumbar spine MRI and high-complexity trauma package."
            sample_img_path = "sample_bills/fraudulent_upcoded_claim.png"

        uploaded_file = st.file_uploader("Upload Hospital Invoice / Doctor Note Image", type=["png", "jpg", "jpeg"])
        
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Invoice Image", use_container_width=True)
        elif sample_img_path and os.path.exists(sample_img_path):
            st.image(sample_img_path, caption="Sample Invoice Document", use_container_width=True)

        with st.form("claim_form"):
            cpt_code = st.selectbox("Billed CPT Code", ["CPT-99213", "CPT-99215", "CPT-47562", "CPT-49505", "CPT-70450", "CPT-72148", "CPT-29881"], index=["CPT-99213", "CPT-99215", "CPT-47562", "CPT-49505", "CPT-70450", "CPT-72148", "CPT-29881"].index(default_cpt))
            diagnosis = st.text_input("Diagnosis (ICD-10)", value=default_diag)
            claim_amount = st.number_input("Claimed Amount ($)", min_value=50.0, max_value=50000.0, value=default_amount, step=100.0)
            patient_age = st.slider("Patient Age", 18, 90, value=default_age)
            visits_30d = st.slider("Hospital Visits (Last 30 Days)", 1, 20, value=default_visits)
            clinical_notes = st.text_area("Doctor Clinical Summary / Notes", value=default_notes, height=100)
            
            submit_btn = st.form_submit_button("🚨 Run MedIns AI Forensic Audit", use_container_width=True)

    with col_right:
        st.subheader("2. MedIns AI Audit Findings")

        if submit_btn or sample_choice != "Custom Manual Entry":
            # 1. Run ML Tabular Prediction
            ml_res = ml_engine.predict_single_claim(cpt_code, claim_amount, visits_30d, patient_age)
            
            # 2. Run LLM Clinical Audit
            llm_res = llm_engine.audit_claim(diagnosis, cpt_code, claim_amount, ml_res["benchmark_cost"], clinical_notes)
            
            # Parse raw response
            llm_text = llm_res["raw_response"]
            fraud_score_pct = int(ml_res["fraud_score"] * 100)
            
            if "HIGH" in llm_text or fraud_score_pct >= 70:
                badge_html = f'<div class="badge-high">Risk Index: {fraud_score_pct}% — HIGH SUSPICION OF FRAUD</div>'
            elif "MEDIUM" in llm_text or fraud_score_pct >= 40:
                badge_html = f'<div class="badge-high" style="color:#FBBF24; background:rgba(245,158,11,0.15); border-color:rgba(245,158,11,0.4);">Risk Index: {fraud_score_pct}% — MEDIUM RISK ANOMALY</div>'
            else:
                badge_html = f'<div class="badge-low">Risk Index: {fraud_score_pct}% — LEGITIMATE CLAIM</div>'

            st.markdown(badge_html, unsafe_allow_html=True)
            st.progress(fraud_score_pct / 100.0)

            # Render Plotly Gauge if available
            if HAS_PLOTLY:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=fraud_score_pct,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Calculated Risk Score", 'font': {'color': '#F8FAFC', 'size': 18}},
                    number={'suffix': "%", 'font': {'color': '#38BDF8'}},
                    gauge={
                        'axis': {'range': [0, 100], 'tickcolor': "#94A3B8"},
                        'bar': {'color': "#EF4444" if fraud_score_pct>=70 else "#F59E0B" if fraud_score_pct>=40 else "#10B981"},
                        'bgcolor': "#0F172A",
                        'bordercolor': "#334155",
                        'steps': [
                            {'range': [0, 40], 'color': "#1E293B"},
                            {'range': [40, 70], 'color': "#334155"},
                            {'range': [70, 100], 'color': "#7F1D1D"}
                        ]
                    }
                ))
                fig_gauge.update_layout(height=180, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_gauge, use_container_width=True)

            # Display Anomaly Signals
            st.markdown("#### 🔍 Tabular Anomaly Signals (ML Engine)")
            st.write(f"**Billing Ratio:** `{ml_res['cost_ratio']}x` of regional benchmark (${ml_res['benchmark_cost']})")
            
            if ml_res["flags"]:
                for flag in ml_res["flags"]:
                    st.warning(f"⚠️ {flag}")
            else:
                st.success("✅ No numerical anomalies detected by Isolation Forest.")

            # Display LLM Explanation
            st.markdown("#### 🤖 Clinical Opinion (Open-Source LLM)")
            st.caption(f"Auditor Engine: **{llm_res['llm_used']}**")
            st.info(llm_text)
        else:
            st.info("👈 Select a sample scenario or click **Run MedIns AI Forensic Audit** to analyze.")

# TAB 2: BATCH ANALYTICS & HOSPITAL INSIGHTS
with tab2:
    st.subheader("Batch Claims Analytics & Fraud Distribution")
    
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

        st.markdown("#### Sample Processed Claims Dataset")
        st.dataframe(df_claims.head(10), use_container_width=True)

# TAB 3: AI ARCHITECTURE & FRAMEWORKS
with tab3:
    st.subheader("Open-Source AI Stack & System Architecture")

    st.markdown("""
    ### 1. Open-Source AI Stack Used:
    - **Open-Source LLM:** Meta Llama 3.1 8B (via Groq Cloud API & local Ollama support)
    - **Machine Learning Frameworks:** `Scikit-Learn` (Isolation Forest, Random Forest Classifier), `Pandas`, `NumPy`
    - **Vision & Document OCR:** `EasyOCR`, `Pillow (PIL)`
    - **UI & Analytics:** `Streamlit`, `Plotly Express`
    - **Orchestration:** `LangChain`, `Python-dotenv`

    ---

    ### 2. End-to-End System Workflow:
    ```
    [ Hospital Bill Upload ] ---> [ EasyOCR / Text Parser ]
                                        |
                                        v
    [ Claim Metadata ] ---------> [ Tabular ML Engine ]  ---> [ Isolation Forest Score ]
                                        |                                   |
                                        v                                   v
                                [ Llama 3.1 LLM Agent ] ---------> [ MedIns Risk Index ]
                                        |                                   |
                                        v                                   v
                            [ Natural Language Audit ] ----------> [ Streamlit Dark UI ]
    ```
    """)
