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
            features = ["Claim_Amount", "Benchmark_Cost", "Cost_Ratio", "Visits_Last_30Days", "Patient_Age"]
            X = df[features]
            y = df["Is_Fraud"]

            X_scaled = self.scaler.fit_transform(X)
            self.iso_forest.fit(X_scaled)
            self.rf_classifier.fit(X_scaled, y)
        
        self.is_trained = True

    def predict_single_claim(self, cpt_code, claim_amount, visits_30d, age):
        if not self.is_trained:
            self.train_or_load()

        benchmark = self.benchmarks.get(cpt_code, 1000.0)
        cost_ratio = round(claim_amount / benchmark, 2)

        flags = []
        if cost_ratio > 2.0:
            flags.append(f"Billing amount is {cost_ratio}x higher than regional benchmark (${benchmark}).")
        if visits_30d > 7:
            flags.append(f"Unusually high visit frequency ({visits_30d} visits in 30 days).")

        if HAS_SKLEARN:
            input_data = pd.DataFrame([{
                "Claim_Amount": claim_amount,
                "Benchmark_Cost": benchmark,
                "Cost_Ratio": cost_ratio,
                "Visits_Last_30Days": visits_30d,
                "Patient_Age": age
            }])

            input_scaled = self.scaler.transform(input_data)
            anomaly_flag = self.iso_forest.predict(input_scaled)[0]
            anomaly_raw_score = self.iso_forest.score_samples(input_scaled)[0]
            normalized_anomaly = round(float(np.clip((0.5 - anomaly_raw_score) * 2, 0.0, 1.0)), 2)
            rf_prob = round(float(self.rf_classifier.predict_proba(input_scaled)[0][1]), 2)
            final_fraud_score = round(max(normalized_anomaly, rf_prob), 2)
            
            if anomaly_flag == -1:
                flags.append("Statistical outlier detected by Isolation Forest algorithm.")
            
            is_anomaly = (anomaly_flag == -1)
        else:
            # Pure Python statistical score fallback
            score = 0.1
            if cost_ratio > 1.8:
                score += min(0.6, (cost_ratio - 1.0) * 0.3)
            if visits_30d > 5:
                score += min(0.3, (visits_30d - 5) * 0.05)
            
            final_fraud_score = round(min(0.98, score), 2)
            is_anomaly = cost_ratio > 2.0 or visits_30d > 7
            if is_anomaly:
                flags.append("Statistical outlier flagged by Z-score benchmark engine.")

        return {
            "fraud_score": final_fraud_score,
            "cost_ratio": cost_ratio,
            "benchmark_cost": benchmark,
            "flags": flags,
            "anomaly_detected": is_anomaly
        }
