import pandas as pd
import numpy as np
import os

try:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

class TabularFraudDetector:
    def __init__(self, data_path="claims_dataset.csv"):
        self.data_path = data_path
        self.is_trained = False
        
        # CPT procedure benchmark dictionary
        self.benchmarks = {
            "CPT-99213": 150.0,
            "CPT-99215": 350.0,
            "CPT-47562": 6500.0,
            "CPT-49505": 4200.0,
            "CPT-70450": 850.0,
            "CPT-72148": 1400.0,
            "CPT-29881": 3800.0,
        }

        if HAS_SKLEARN:
            self.scaler = StandardScaler()
            self.iso_forest = IsolationForest(contamination=0.12, random_state=42)
            self.rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42)

    def train_or_load(self):
        if not os.path.exists(self.data_path):
            from data_generator import generate_claims_dataset
            generate_claims_dataset(1000, self.data_path)

        if HAS_SKLEARN:
            df = pd.read_csv(self.data_path)
            features = ["Cost_Ratio", "Visits_Last_30Days", "Patient_Age"]
            X = df[features]
            y = df["Is_Fraud"]

            X_scaled = self.scaler.fit_transform(X)
            self.iso_forest.fit(X_scaled)
            self.rf_classifier.fit(X_scaled, y)
        
        self.is_trained = True

    def append_custom_claim_to_dataset(self, claim_id, hospital_id, cpt_code, claim_amount, benchmark_cost, cost_ratio, visits_30d, is_fraud, fraud_type):
        try:
            if os.path.exists(self.data_path):
                df = pd.read_csv(self.data_path)
            else:
                df = pd.DataFrame()

            new_row = {
                "Claim_ID": claim_id,
                "Patient_ID": f"PAT-{np.random.randint(10000, 99999)}",
                "Patient_Age": np.random.randint(25, 75),
                "Hospital_ID": hospital_id,
                "CPT_Code": cpt_code,
                "Procedure_Name": cpt_code,
                "Claim_Amount": claim_amount,
                "Benchmark_Cost": benchmark_cost,
                "Cost_Ratio": cost_ratio,
                "Visits_Last_30Days": visits_30d,
                "Is_Fraud": is_fraud,
                "Fraud_Type": fraud_type
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(self.data_path, index=False)
            self.train_or_load()
            return True
        except Exception as e:
            print(f"Error appending custom claim to dataset: {e}")
            return False

    def predict_single_claim(self, cpt_code, claim_amount, visits_30d, age, billed_tests=None, recommended_tests=None, **kwargs):
        if not self.is_trained:
            self.train_or_load()

        benchmark = self.benchmarks.get(cpt_code, 1000.0)
        cost_ratio = round(claim_amount / benchmark, 2)

        flags = []
        unrelated_count = 0
        unrelated_test_names = []
        
        # Determine if billed tests are genuinely present
        has_tests = False
        if billed_tests and isinstance(billed_tests, list) and len(billed_tests) > 0:
            valid_b_tests = [t for t in billed_tests if isinstance(t, str) and t.strip().lower() not in ["none", "none selected", "n/a", "choose options", "[]"]]
            if len(valid_b_tests) > 0:
                has_tests = True
                b_list = [t.strip().lower() for t in valid_b_tests]
                r_list = [t.strip().lower() for t in (recommended_tests or []) if isinstance(t, str)]
                
                for b_test in b_list:
                    is_related = False
                    for r_test in r_list:
                        if b_test in r_test or r_test in b_test:
                            is_related = True
                            break
                    
                    if not is_related:
                        unrelated_count += 1
                        unrelated_test_names.append(b_test.title())
                        flags.append(f"Unrelated Diagnostic Test: '{b_test.title()}' is not clinically indicated for this diagnosis.")

        if cost_ratio > 1.8:
            flags.append(f"Billing Ratio Anomaly: Billed amount (${claim_amount:,.2f}) exceeds regional benchmark (${benchmark:,.2f}) by {cost_ratio:.2f}x.")
        if visits_30d > 7:
            flags.append(f"High Frequency Anomaly: Unusually high visit count ({visits_30d} visits in 30 days).")

        # Age Relevance Factor
        age_penalty = 0.0
        if age < 18 and "cpt-70450" in cpt_code.lower():
            age_penalty = 0.10
            flags.append("Pediatric Radiation Caution: CT scan ordered for pediatric patient requires special justification.")

        # Score Breakdown components
        cost_penalty = max(0.0, round((cost_ratio - 1.0) * 0.15, 2)) if cost_ratio > 1.5 else 0.0
        test_penalty = min(0.65, round(unrelated_count * 0.35, 2)) if has_tests else 0.0
        freq_penalty = 0.15 if visits_30d > 7 else 0.0

        if HAS_SKLEARN:
            input_data = pd.DataFrame([{
                "Cost_Ratio": cost_ratio,
                "Visits_Last_30Days": visits_30d,
                "Patient_Age": age
            }])

            input_scaled = self.scaler.transform(input_data)
            anomaly_flag = self.iso_forest.predict(input_scaled)[0]
            rf_prob = round(float(self.rf_classifier.predict_proba(input_scaled)[0][1]), 2)
            
            base_score = rf_prob
            if cost_ratio <= 1.2 and visits_30d <= 4 and unrelated_count == 0:
                final_fraud_score = round(min(base_score, 0.10), 2)
            else:
                final_fraud_score = round(min(0.98, base_score + cost_penalty + test_penalty + freq_penalty + age_penalty), 2)

            is_anomaly = (anomaly_flag == -1 or unrelated_count >= 1 or cost_ratio > 1.8)
        else:
            base_score = 0.10
            final_fraud_score = round(min(0.98, base_score + cost_penalty + test_penalty + freq_penalty + age_penalty), 2)
            is_anomaly = (cost_ratio > 1.8 or visits_30d > 7 or unrelated_count >= 1)
            
        if is_anomaly and "Statistical outlier flagged by ML anomaly engine." not in flags:
            flags.append("Statistical outlier flagged by ML anomaly engine.")

        score_explanation = {
            "base_ml_score_pct": int(base_score * 100),
            "cost_penalty_pct": int(cost_penalty * 100),
            "unrelated_tests_penalty_pct": int(test_penalty * 100),
            "age_relevance_penalty_pct": int(age_penalty * 100),
            "visit_freq_penalty_pct": int(freq_penalty * 100),
            "final_risk_score_pct": int(final_fraud_score * 100),
            "unrelated_test_names": unrelated_test_names
        }

        return {
            "fraud_score": final_fraud_score,
            "cost_ratio": cost_ratio,
            "benchmark_cost": benchmark,
            "flags": flags,
            "unrelated_tests_count": unrelated_count,
            "anomaly_detected": is_anomaly,
            "score_explanation": score_explanation
        }
