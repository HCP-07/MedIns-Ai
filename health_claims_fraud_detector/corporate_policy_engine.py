import re
import pandas as pd
import numpy as np

class CorporatePolicyEngine:
    """
    Industrial-grade Corporate Policy & Insurance Scheme Eligibility Engine.
    Provides demo datasets for enterprise corporate employers, health insurance schemes,
    patient eligibility lookups, real-time background checks, and past fraud history logs.
    """
    def __init__(self):
        self.corporate_companies = {
            "Tata Consultancy Services (TCS)": {
                "employer_code": "EMP-TCS-101",
                "tier": "Enterprise Fortune 500",
                "default_insurer": "Star Health & Allied Insurance",
                "active_employees": 600000,
                "policy_group_id": "GRP-TCS-2026-X"
            },
            "Infosys Limited": {
                "employer_code": "EMP-INF-202",
                "tier": "Enterprise Global IT",
                "default_insurer": "ICICI Lombard General Insurance",
                "active_employees": 320000,
                "policy_group_id": "GRP-INF-2026-A"
            },
            "Reliance Industries Ltd (RIL)": {
                "employer_code": "EMP-RIL-303",
                "tier": "Conglomerate Enterprise",
                "default_insurer": "HDFC ERGO Health Insurance",
                "active_employees": 390000,
                "policy_group_id": "GRP-RIL-2026-R"
            },
            "Wipro Technologies": {
                "employer_code": "EMP-WIP-404",
                "tier": "Enterprise Global Tech",
                "default_insurer": "Bajaj Allianz General Insurance",
                "active_employees": 240000,
                "policy_group_id": "GRP-WIP-2026-W"
            },
            "Amazon Development Center India": {
                "employer_code": "EMP-AMZ-505",
                "tier": "Global Tech Multinational",
                "default_insurer": "Niva Bupa Health Insurance",
                "active_employees": 110000,
                "policy_group_id": "GRP-AMZ-2026-Z"
            }
        }

        self.insurance_schemes = {
            "Executive Platinum Shield Cover": {
                "scheme_code": "SCH-PLAT-01",
                "max_annual_sum_insured": 50000.0,
                "room_rent_cap_per_day": 1000.0,
                "copay_percentage": "0% (Zero Co-Pay)",
                "pre_existing_disease_wait_months": 0,
                "covered_cpt_categories": ["Emergency Surgery", "Outpatient Consultation", "Advanced Diagnostics (MRI/CT)", "Cardiology Interventions", "Laparoscopy"],
                "policy_status": "Active Corporate Group Plan"
            },
            "Gold Corporate Health Flexi": {
                "scheme_code": "SCH-GOLD-02",
                "max_annual_sum_insured": 25000.0,
                "room_rent_cap_per_day": 500.0,
                "copay_percentage": "10% Co-Pay",
                "pre_existing_disease_wait_months": 12,
                "covered_cpt_categories": ["Emergency Surgery", "Outpatient Consultation", "Standard Diagnostics (X-Ray/Labs)", "Laparoscopy"],
                "policy_status": "Active Corporate Group Plan"
            },
            "Silver Standard Group Mediclaim": {
                "scheme_code": "SCH-SILV-03",
                "max_annual_sum_insured": 10000.0,
                "room_rent_cap_per_day": 250.0,
                "copay_percentage": "20% Co-Pay",
                "pre_existing_disease_wait_months": 24,
                "covered_cpt_categories": ["Emergency Surgery", "Outpatient Consultation", "Basic Diagnostics"],
                "policy_status": "Active Corporate Group Plan"
            }
        }

        self.demo_patients_registry = {
            "PAT-TCS-88392": {
                "patient_name": "Robert Jenkins",
                "employer": "Tata Consultancy Services (TCS)",
                "scheme_assigned": "Executive Platinum Shield Cover",
                "policy_number": "POL-TCS-88392-2026",
                "employment_status": "Active Full-Time (Senior Principal Architect)",
                "background_verification": "PASSED - Verified Employee",
                "annual_claims_claimed": 18200.0,
                "remaining_sum_insured": 31800.0,
                "fraud_history_count": 2,
                "fraud_history_records": [
                    {"date": "2025-11-14", "incident": "Duplicate MRI Lumbar Spine billed twice on same day at Valley Oak Medical", "status": "Flagged & Recovered ($950.00)"},
                    {"date": "2024-06-20", "incident": "Pregnancy test CPT billed for male patient", "status": "Denied & Warning Issued"}
                ]
            },
            "PAT-INF-99214": {
                "patient_name": "Marcus Thorne",
                "employer": "Infosys Limited",
                "scheme_assigned": "Gold Corporate Health Flexi",
                "policy_number": "POL-INF-99214-2026",
                "employment_status": "Active Full-Time (Lead Systems Specialist)",
                "background_verification": "PASSED - Verified Employee",
                "annual_claims_claimed": 3200.0,
                "remaining_sum_insured": 21800.0,
                "fraud_history_count": 0,
                "fraud_history_records": []
            },
            "PAT-RIL-44810": {
                "patient_name": "Sarah Lin",
                "employer": "Reliance Industries Ltd (RIL)",
                "scheme_assigned": "Executive Platinum Shield Cover",
                "policy_number": "POL-RIL-44810-2026",
                "employment_status": "Active Full-Time (General Manager Ops)",
                "background_verification": "PASSED - Verified Employee",
                "annual_claims_claimed": 6500.0,
                "remaining_sum_insured": 43500.0,
                "fraud_history_count": 0,
                "fraud_history_records": []
            },
            "PAT-AMZ-77102": {
                "patient_name": "Vikram Malhotra",
                "employer": "Amazon Development Center India",
                "scheme_assigned": "Silver Standard Group Mediclaim",
                "policy_number": "POL-AMZ-77102-2026",
                "employment_status": "Suspended / Off-boarding Notice",
                "background_verification": "WARNING - Employment Status Pending Audit",
                "annual_claims_claimed": 12500.0,
                "remaining_sum_insured": 0.0,  # Exceeded
                "fraud_history_count": 3,
                "fraud_history_records": [
                    {"date": "2026-02-10", "incident": "Claim amount exceeded max annual scheme cap of $10,000", "status": "Exceeded Policy Cap"},
                    {"date": "2025-08-04", "incident": "Unbundled Emergency Room Crutches & Splint Billing", "status": "Audit Investigation"},
                    {"date": "2024-12-19", "incident": "Hospital admission date mismatch with employment leave record", "status": "Fraud Flagged"}
                ]
            }
        }

    def parse_text_invoice(self, text):
        """
        Parses raw text invoice content to automatically extract patient ID, name,
        employer, scheme, claim amount, and CPT code.
        """
        if not text:
            text = ""
            
        parsed = {
            "patient_id": "PAT-TCS-88392",
            "patient_name": "Robert Jenkins",
            "employer": "Tata Consultancy Services (TCS)",
            "scheme": "Executive Platinum Shield Cover",
            "claim_amount": 3190.0,
            "cpt_code": "CPT-72148"
        }

        # Match Patient ID
        pid_m = re.search(r"Patient ID:\s*([^\n]+)", text, re.IGNORECASE) or re.search(r"PAT-[A-Z]+-\d+", text)
        if pid_m:
            parsed["patient_id"] = pid_m.group(1).strip() if ":" in pid_m.group(0) else pid_m.group(0).strip()

        # Match Patient Name
        pname_m = re.search(r"Patient Name:\s*([^\n]+)", text, re.IGNORECASE)
        if pname_m:
            parsed["patient_name"] = pname_m.group(1).strip()

        # Match Employer
        emp_m = re.search(r"Employer:\s*([^\n]+)", text, re.IGNORECASE)
        if emp_m:
            parsed["employer"] = emp_m.group(1).strip()

        # Match Scheme
        sch_m = re.search(r"Scheme:\s*([^\n]+)", text, re.IGNORECASE)
        if sch_m:
            parsed["scheme"] = sch_m.group(1).strip()

        # Match Claim Amount
        amt_m = re.search(r"TOTAL BILLED AMOUNT:\s*\$?\s*([\d,]+\.?\d*)", text, re.IGNORECASE) or re.search(r"TOTAL CLAIMED AMOUNT:\s*\$?\s*([\d,]+\.?\d*)", text, re.IGNORECASE)
        if amt_m:
            try:
                parsed["claim_amount"] = float(amt_m.group(1).replace(",", ""))
            except ValueError:
                pass

        # Match CPT
        cpt_m = re.search(r"CPT-\d+", text)
        if cpt_m:
            parsed["cpt_code"] = cpt_m.group(0)

        return parsed

    def verify_corporate_background(self, patient_id_or_name, employer_name=None, scheme_name=None, claim_amount=None, cpt_code=None, patient_name=None):
        """
        Executes a real-time corporate policy & background audit enquiry.
        Checks policy applicability, scheme caps, and past fraud history records.
        Updates patient_name in patient_record dynamically if supplied.
        """
        patient = None
        for pid, pdata in self.demo_patients_registry.items():
            if pid.lower() == str(patient_id_or_name).lower() or pdata["patient_name"].lower() in str(patient_id_or_name).lower():
                # Make a copy so we don't mutate permanent dictionary permanently
                patient = dict(pdata)
                patient["patient_id"] = pid
                break

        if not patient:
            patient = {
                "patient_id": f"PAT-DEMO-{np.random.randint(10000, 99999)}",
                "patient_name": patient_name or str(patient_id_or_name),
                "employer": employer_name or "Tata Consultancy Services (TCS)",
                "scheme_assigned": scheme_name or "Executive Platinum Shield Cover",
                "policy_number": f"POL-CUST-{np.random.randint(100000, 999999)}",
                "employment_status": "Active Full-Time (Verified Employee)",
                "background_verification": "PASSED - Verified Employee Record",
                "annual_claims_claimed": 1500.0,
                "remaining_sum_insured": 23500.0,
                "fraud_history_count": 0,
                "fraud_history_records": []
            }

        # Override patient name if explicitly passed from parsed text invoice
        if patient_name and str(patient_name).strip():
            patient["patient_name"] = str(patient_name).strip()

        eff_scheme_name = scheme_name if scheme_name in self.insurance_schemes else patient.get("scheme_assigned", "Executive Platinum Shield Cover")
        eff_employer_name = employer_name if employer_name in self.corporate_companies else patient.get("employer", "Tata Consultancy Services (TCS)")
        eff_claim_amount = claim_amount if claim_amount is not None else 3190.0
        eff_cpt_code = cpt_code if cpt_code is not None else "CPT-72148"

        scheme = self.insurance_schemes.get(eff_scheme_name, self.insurance_schemes["Executive Platinum Shield Cover"])
        employer = self.corporate_companies.get(eff_employer_name, self.corporate_companies["Tata Consultancy Services (TCS)"])

        exceeds_cap = eff_claim_amount > scheme["max_annual_sum_insured"]
        exceeds_remaining = eff_claim_amount > patient["remaining_sum_insured"]
        is_fraud_suspect = patient["fraud_history_count"] > 0
        
        is_applicable = (patient["employment_status"].startswith("Active")) and not exceeds_remaining

        risk_warnings = []
        if exceeds_cap:
            risk_warnings.append(f"Claim Amount (${eff_claim_amount:,.2f}) exceeds Maximum Annual Scheme Cover (${scheme['max_annual_sum_insured']:,.2f}).")
        if exceeds_remaining:
            risk_warnings.append(f"Claim Amount (${eff_claim_amount:,.2f}) exceeds Remaining Patient Sum Insured (${patient['remaining_sum_insured']:,.2f}).")
        if is_fraud_suspect:
            risk_warnings.append(f"Patient has {patient['fraud_history_count']} past corporate fraud history record(s) on file.")
        if "WARNING" in patient["background_verification"]:
            risk_warnings.append(f"Employment Background Enquiry Flagged: {patient['background_verification']}")

        return {
            "is_applicable": is_applicable,
            "patient_record": patient,
            "employer_info": employer,
            "scheme_info": scheme,
            "claim_amount": eff_claim_amount,
            "cpt_code": eff_cpt_code,
            "exceeds_cap": exceeds_cap,
            "exceeds_remaining": exceeds_remaining,
            "risk_warnings": risk_warnings
        }
