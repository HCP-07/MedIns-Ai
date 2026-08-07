import os
import json
import pandas as pd

class KaggleDatasetFetcher:
    def __init__(self):
        self.kaggle_username = os.environ.get("KAGGLE_USERNAME", "").strip()
        self.kaggle_key = os.environ.get("KAGGLE_KEY", "").strip()
        
        # Check for local kaggle.json file
        if not self.kaggle_username or not self.kaggle_key:
            self._load_from_kaggle_json()

    def _load_from_kaggle_json(self):
        possible_paths = [
            "kaggle.json",
            os.path.expanduser("~/.kaggle/kaggle.json"),
            os.path.join(os.getcwd(), "kaggle.json")
        ]
        for p in possible_paths:
            if os.path.exists(p):
                try:
                    with open(p, 'r') as f:
                        data = json.load(f)
                        self.kaggle_username = data.get("username", "").strip()
                        self.kaggle_key = data.get("key", "").strip()
                        if self.kaggle_username and self.kaggle_key:
                            os.environ["KAGGLE_USERNAME"] = self.kaggle_username
                            os.environ["KAGGLE_KEY"] = self.kaggle_key
                            print(f"Loaded Kaggle credentials from '{p}'")
                            break
                except Exception as e:
                    print(f"Warning loading kaggle.json from {p}: {e}")

    def fetch_kaggle_claims_data(self, dataset_name="rohitgarg/healthcare-insurance-claims-fraud-detection"):
        """
        Fetches healthcare claims fraud dataset from Kaggle API if credentials are valid,
        otherwise falls back to local synthetic claims dataset.
        """
        if not self.kaggle_username or not self.kaggle_key:
            self._load_from_kaggle_json()

        if not self.kaggle_username or not self.kaggle_key:
            return False, "Kaggle API key (kaggle.json) not detected. Using baseline claims dataset.", None

        try:
            import kaggle
            kaggle.api.authenticate()
            target_dir = "kaggle_data"
            os.makedirs(target_dir, exist_ok=True)
            
            print(f"Downloading Kaggle dataset '{dataset_name}'...")
            kaggle.api.dataset_download_files(dataset_name, path=target_dir, unzip=True)
            
            csv_files = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.endswith('.csv')]
            if csv_files:
                df = pd.read_csv(csv_files[0])
                return True, f"Successfully loaded Kaggle dataset: {os.path.basename(csv_files[0])} ({len(df)} records)", df
            else:
                return False, "Downloaded Kaggle dataset zip, but no CSV file found.", None
        except Exception as e:
            return False, f"Kaggle API Error: {str(e)}", None
