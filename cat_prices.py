import pandas as pd
import os
import logging
import re

logger = logging.getLogger(__name__)

class CatPriceManager:
    _instance = None
    _data = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.load_data()

    def load_data(self):
        try:
            # Path to the CSV file
            csv_path = os.path.join(os.path.dirname(__file__), 'cat prices - Cat Calculator.csv')
            
            if not os.path.exists(csv_path):
                logger.warning(f"Cat prices CSV not found at {csv_path}")
                return

            # Read CSV, skipping first 2 lines (header is on line 3, so skip 2 rows)
            # Line 1 and 2 are empty commas.
            # pandas read_csv header=2 (0-indexed, so row 2 is the 3rd row)
            df = pd.read_csv(csv_path, header=2)
            
            # Clean column names
            df.columns = [c.strip() for c in df.columns]
            
            # Iterate and populate dictionary
            for _, row in df.iterrows():
                car_name = str(row['CAR']).strip().upper()
                if not car_name or car_name == 'nan':
                    continue
                
                try:
                    cats_count = int(row['# OF CATS'])
                    total_sale_str = str(row['TOTAL SALE']).replace('$', '').strip()
                    total_sale = float(total_sale_str) if total_sale_str else 0.0
                    
                    self._data[car_name] = {
                        'count': cats_count,
                        'total_value': total_sale
                    }
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error parsing row for {car_name}: {e}")
                    continue
                    
            logger.info(f"Loaded {len(self._data)} cat price entries.")
            
        except Exception as e:
            logger.error(f"Failed to load cat prices: {e}")

    def normalize(self, s):
        """Remove non-alphanumeric characters and convert to uppercase."""
        if not s:
            return ""
        return re.sub(r'[^A-Z0-9]', '', str(s).upper())

    def get_cat_details(self, make, model):
        """
        Look up cat details for a given make and model.
        Returns dict {'count': int, 'total_value': float} or None.
        """
        if not make or not model:
            return None
            
        # Construct search key "MAKE MODEL"
        search_key = f"{make.strip()} {model.strip()}"
        norm_search = self.normalize(search_key)
        
        # 1. Try exact match of normalized strings
        for key, data in self._data.items():
            if self.normalize(key) == norm_search:
                return data
        
        # 2. Try partial match for specific cases (optional, but helpful)
        # e.g. "BMW X SERIES" matching "BMW X5"
        # This might be risky without more rules, but let's see.
        # For now, stick to exact normalized match to avoid false positives.
        
        return None
