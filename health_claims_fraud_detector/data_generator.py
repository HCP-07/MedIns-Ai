import pandas as pd
import numpy as np
import os

def generate_claims_dataset(num_samples=1000, save_path="claims_dataset.csv"):
    """
    Generates a synthetic health insurance claims dataset containing realistic patterns
    of legitimate claims and fraudulent claims (upcoding, ghost billing, duplicates).
    """
    np.random.seed(42)

    # Standard medical procedures with typical benchmark costs
    procedures = {
        "CPT-99213": {"name": "Low-complexity Outpatient Visit", "mean_cost": 150, "std_cost": 25},
        "CPT-99215": {"name": "High-complexity Outpatient Visit", "mean_cost": 350, "std_cost": 50},
        "CPT-47562": {"name": "Laparoscopic Cholecystectomy (Gallbladder)", "mean_cost": 6500, "std_cost": 800},
        "CPT-49505": {"name": "Inguinal Hernia Repair", "mean_cost": 4200, "std_cost": 500},
        "CPT-70450": {"name": "Head CT Scan", "mean_cost": 850, "std_cost": 120},
        "CPT-72148": {"name": "Lumbar Spine MRI", "mean_cost": 1400, "std_cost": 200},
        "CPT-29881": {"name": "Knee Arthroscopy", "mean_cost": 3800, "std_cost": 450},
    }

    cpt_codes = list(procedures.keys())
    data = []

    for i in range(1, num_samples + 1):
        cpt = np.random.choice(cpt_codes)
        proc_info = procedures[cpt]
        
        patient_id = f"PAT-{np.random.randint(10000, 99999)}"
        hospital_id = f"HOSP-{np.random.randint(100, 150)}"
        patient_age = np.random.randint(18, 85)
        claim_freq_30d = np.random.poisson(lam=1) + 1  # 1 to 5 visits typically
        
        # Decide if this claim is fraudulent (~12% fraud rate in realistic data)
        is_fraud = 1 if np.random.rand() < 0.12 else 0
        fraud_type = "None"

        if is_fraud:
            fraud_choice = np.random.choice(["upcoded_amount", "excessive_frequency", "duplicate_ghost"])
            if fraud_choice == "upcoded_amount":
                # Inflate bill by 2.5x to 5x benchmark
                claim_amount = round(proc_info["mean_cost"] * np.random.uniform(2.5, 5.0), 2)
                fraud_type = "Upcoded / Inflated Billing"
            elif fraud_choice == "excessive_frequency":
                claim_amount = round(np.random.normal(proc_info["mean_cost"], proc_info["std_cost"]), 2)
                claim_freq_30d = np.random.randint(8, 20) # Abnormal visit count
                fraud_type = "High Visit Frequency Anomaly"
            else:
                # Duplicate ghost billing
                claim_amount = round(np.random.normal(proc_info["mean_cost"], proc_info["std_cost"]), 2)
                fraud_type = "Duplicate Ghost Billing"
        else:
            # Normal claim within expected bell curve
            claim_amount = max(50.0, round(np.random.normal(proc_info["mean_cost"], proc_info["std_cost"]), 2))

        benchmark_cost = proc_info["mean_cost"]
        cost_ratio = round(claim_amount / benchmark_cost, 2)

        data.append({
            "Claim_ID": f"CLM-{20260000 + i}",
            "Patient_ID": patient_id,
            "Patient_Age": patient_age,
            "Hospital_ID": hospital_id,
            "CPT_Code": cpt,
            "Procedure_Name": proc_info["name"],
            "Claim_Amount": claim_amount,
            "Benchmark_Cost": benchmark_cost,
            "Cost_Ratio": cost_ratio,
            "Visits_Last_30Days": claim_freq_30d,
            "Is_Fraud": is_fraud,
            "Fraud_Type": fraud_type
        })

    df = pd.DataFrame(data)
    df.to_csv(save_path, index=False)
    print(f"Generated {num_samples} synthetic claims records saved to {save_path}")
    return df

if __name__ == "__main__":
    generate_claims_dataset()
