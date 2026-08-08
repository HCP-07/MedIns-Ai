import os
import json
import shutil
import pandas as pd

class KaggleDatasetFetcher:
    def __init__(self):
        self.kaggle_username = "hcp07dawn"
        self.kaggle_key = "0bf35deb1e722ce11a3857baf011740a"
        self._load_from_kaggle_json()

    def _load_from_kaggle_json(self):
        # Set default environment variables directly
        os.environ["KAGGLE_USERNAME"] = self.kaggle_username
        os.environ["KAGGLE_KEY"] = self.kaggle_key
        
        user_kaggle_dir = os.path.expanduser("~/.kaggle")
        try:
            os.makedirs(user_kaggle_dir, exist_ok=True)
            os.environ["KAGGLE_CONFIG_DIR"] = user_kaggle_dir
        except Exception:
            pass

        possible_paths = [
            os.path.abspath("kaggle.json"),
            os.path.join(os.getcwd(), "kaggle.json"),
            os.path.expanduser("~/.kaggle/kaggle.json")
        ]

        for p in possible_paths:
            if os.path.exists(p):
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        u = str(data.get("username", "")).strip()
                        k = str(data.get("key", "")).strip()
                        
                        if u and k:
                            self.kaggle_username = u
                            self.kaggle_key = k
                            os.environ["KAGGLE_USERNAME"] = u
                            os.environ["KAGGLE_KEY"] = k
                            
                            target_file = os.path.join(user_kaggle_dir, "kaggle.json")
                            try:
                                if os.path.abspath(p) != os.path.abspath(target_file):
                                    shutil.copyfile(p, target_file)
                            except Exception:
                                pass

                            print(f"✅ Kaggle credentials loaded successfully for user: {self.kaggle_username}")
                            return
                except Exception:
                    pass

    def fetch_kaggle_claims_data(self, dataset_name="rohitgarg/healthcare-insurance-claims-fraud-detection"):
        """
        Fetches healthcare claims fraud dataset from Kaggle API.
        """
        if not self.kaggle_username or not self.kaggle_key:
            self._load_from_kaggle_json()

        if not self.kaggle_username or not self.kaggle_key:
            return False, "Kaggle API key (kaggle.json) not detected. Please ensure kaggle.json is in the app directory.", None

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
                return True, f"Successfully downloaded Kaggle dataset: {os.path.basename(csv_files[0])} ({len(df)} records)", df
            else:
                return False, "Downloaded Kaggle dataset zip, but no CSV file found inside.", None
        except Exception as e:
            return False, f"Kaggle API Authenticated Error: {str(e)}", None
