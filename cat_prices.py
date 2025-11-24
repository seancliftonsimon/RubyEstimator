import pandas as pd
import os
import logging
import re
from contextlib import contextmanager
from sqlalchemy import text

from database_config import create_database_engine
from persistence import ensure_schema

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
        ensure_schema()  # Ensure cat_prices table exists
        self.sync_from_csv_if_empty()
        self.load_data()

    @contextmanager
    def _connect(self):
        engine = create_database_engine()
        with engine.connect() as conn:
            yield conn

    def sync_from_csv_if_empty(self):
        """Load CSV data into DB if the cat_prices table is empty."""
        try:
            with self._connect() as conn:
                # Check if table has any rows
                result = conn.execute(text("SELECT COUNT(*) FROM cat_prices")).fetchone()
                if result[0] > 0:
                    logger.debug("Cat prices table already has data, skipping CSV sync")
                    return
                
                # Table is empty, load from CSV
                csv_path = os.path.join(os.path.dirname(__file__), 'cat prices - Cat Calculator.csv')
                
                if not os.path.exists(csv_path):
                    logger.warning(f"Cat prices CSV not found at {csv_path}, cannot sync")
                    return

                # Read CSV, skipping first 2 lines (header is on line 3, so skip 2 rows)
                df = pd.read_csv(csv_path, header=2)
                df.columns = [c.strip() for c in df.columns]
                
                inserted_count = 0
                for _, row in df.iterrows():
                    car_name = str(row['CAR']).strip().upper()
                    if not car_name or car_name == 'nan':
                        continue
                    
                    try:
                        cats_count = int(row['# OF CATS'])
                        total_sale_str = str(row['TOTAL SALE']).replace('$', '').strip()
                        total_sale = float(total_sale_str) if total_sale_str else 0.0
                        
                        # Parse optional columns
                        current_sale_str = str(row.get('CURRENT SALE', '')).replace('$', '').strip()
                        current_sale = float(current_sale_str) if current_sale_str and current_sale_str != 'nan' else None
                        
                        extra_cat_str = str(row.get('EXTRA CAT VALUE', '')).replace('$', '').strip()
                        extra_cat_value = float(extra_cat_str) if extra_cat_str and extra_cat_str != 'nan' else None
                        
                        conn.execute(
                            text("""
                                INSERT INTO cat_prices (vehicle_name, cat_count, total_sale, current_sale, extra_cat_value)
                                VALUES (:vehicle_name, :cat_count, :total_sale, :current_sale, :extra_cat_value)
                                ON CONFLICT (vehicle_name) DO NOTHING
                            """),
                            {
                                "vehicle_name": car_name,
                                "cat_count": cats_count,
                                "total_sale": total_sale,
                                "current_sale": current_sale,
                                "extra_cat_value": extra_cat_value
                            }
                        )
                        inserted_count += 1
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error parsing row for {car_name}: {e}")
                        continue
                
                conn.commit()
                logger.info(f"Synced {inserted_count} cat price entries from CSV to database")
                
        except Exception as e:
            logger.error(f"Failed to sync cat prices from CSV: {e}")

    def load_data(self):
        """Load cat prices from database into memory."""
        try:
            self._data = {}
            with self._connect() as conn:
                result = conn.execute(
                    text("SELECT vehicle_name, cat_count, total_sale FROM cat_prices")
                ).fetchall()
                
                for row in result:
                    vehicle_name, cat_count, total_sale = row
                    self._data[vehicle_name] = {
                        'count': cat_count,
                        'total_value': float(total_sale)
                    }
                    
            logger.info(f"Loaded {len(self._data)} cat price entries from database.")
            
        except Exception as e:
            logger.error(f"Failed to load cat prices from database: {e}")

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

    def get_all_entries(self):
        """
        Get all cat price entries as a pandas DataFrame for UI display.
        Returns DataFrame with columns: id, vehicle_name, cat_count, total_sale, current_sale, extra_cat_value
        """
        try:
            with self._connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT id, vehicle_name, cat_count, total_sale, current_sale, extra_cat_value
                        FROM cat_prices
                        ORDER BY vehicle_name
                    """)
                ).fetchall()
                
                df = pd.DataFrame(result, columns=['id', 'vehicle_name', 'cat_count', 'total_sale', 'current_sale', 'extra_cat_value'])
                # Keep optional numeric columns as NaN/None (not empty strings) for Streamlit NumberColumn compatibility
                # Streamlit's NumberColumn expects numeric types or None, not strings
                return df
        except Exception as e:
            logger.error(f"Failed to get all cat price entries: {e}")
            return pd.DataFrame(columns=['id', 'vehicle_name', 'cat_count', 'total_sale', 'current_sale', 'extra_cat_value'])

    def update_entries(self, edited_df):
        """
        Update cat prices from edited DataFrame.
        Handles inserts, updates, and deletes based on the DataFrame state.
        
        Args:
            edited_df: DataFrame with columns: id, vehicle_name, cat_count, total_sale, current_sale, extra_cat_value
                      Rows with empty id are new entries (insert)
                      Rows with id are existing entries (update)
                      Missing rows (compared to current DB) are deleted
        """
        try:
            with self._connect() as conn:
                # Get current entries from DB
                current_df = self.get_all_entries()
                # Convert IDs to integers for comparison (empty strings become NaN, which we'll handle)
                current_ids = set()
                if not current_df.empty:
                    for id_val in current_df['id'].values:
                        if pd.notna(id_val) and id_val != '':
                            try:
                                current_ids.add(int(id_val))
                            except (ValueError, TypeError):
                                pass
                
                # Process edited DataFrame
                edited_df = edited_df.copy()
                edited_ids_in_edit = set()
                
                # Handle updates and inserts
                for _, row in edited_df.iterrows():
                    vehicle_name = str(row['vehicle_name']).strip().upper()
                    if not vehicle_name or vehicle_name == '':
                        continue
                    
                    cat_count = int(row['cat_count']) if pd.notna(row['cat_count']) else 0
                    total_sale = float(row['total_sale']) if pd.notna(row['total_sale']) else 0.0
                    # Handle optional numeric columns - they should be NaN/None, not empty strings
                    current_sale = float(row['current_sale']) if pd.notna(row['current_sale']) else None
                    extra_cat_value = float(row['extra_cat_value']) if pd.notna(row['extra_cat_value']) else None
                    
                    # Handle ID - could be empty string, NaN, or a number
                    entry_id = row['id']
                    is_new_entry = False
                    
                    if pd.isna(entry_id) or entry_id == '' or str(entry_id).strip() == '' or str(entry_id).lower() == 'nan':
                        is_new_entry = True
                    else:
                        try:
                            entry_id = int(entry_id)
                            edited_ids_in_edit.add(entry_id)
                        except (ValueError, TypeError):
                            # Invalid ID, treat as new entry
                            is_new_entry = True
                    
                    if is_new_entry:
                        # New entry - insert with conflict handling for duplicate vehicle_name
                        try:
                            conn.execute(
                                text("""
                                    INSERT INTO cat_prices (vehicle_name, cat_count, total_sale, current_sale, extra_cat_value)
                                    VALUES (:vehicle_name, :cat_count, :total_sale, :current_sale, :extra_cat_value)
                                    ON CONFLICT (vehicle_name) DO UPDATE SET
                                        cat_count = EXCLUDED.cat_count,
                                        total_sale = EXCLUDED.total_sale,
                                        current_sale = EXCLUDED.current_sale,
                                        extra_cat_value = EXCLUDED.extra_cat_value,
                                        updated_at = CURRENT_TIMESTAMP
                                """),
                                {
                                    "vehicle_name": vehicle_name,
                                    "cat_count": cat_count,
                                    "total_sale": total_sale,
                                    "current_sale": current_sale,
                                    "extra_cat_value": extra_cat_value
                                }
                            )
                        except Exception as e:
                            # If conflict handling fails for any reason, raise a more descriptive error
                            logger.error(f"Failed to insert/update cat price for {vehicle_name}: {e}")
                            raise ValueError(f"Failed to save entry for '{vehicle_name}'. A vehicle with this name may already exist.") from e
                    else:
                        # Existing entry - update
                        conn.execute(
                            text("""
                                UPDATE cat_prices
                                SET vehicle_name = :vehicle_name,
                                    cat_count = :cat_count,
                                    total_sale = :total_sale,
                                    current_sale = :current_sale,
                                    extra_cat_value = :extra_cat_value,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = :id
                            """),
                            {
                                "id": entry_id,
                                "vehicle_name": vehicle_name,
                                "cat_count": cat_count,
                                "total_sale": total_sale,
                                "current_sale": current_sale,
                                "extra_cat_value": extra_cat_value
                            }
                        )
                
                # Handle deletes - remove entries that are no longer in the edited DataFrame
                deleted_ids = current_ids - edited_ids_in_edit
                for deleted_id in deleted_ids:
                    conn.execute(
                        text("DELETE FROM cat_prices WHERE id = :id"),
                        {"id": deleted_id}
                    )
                
                conn.commit()
                # Reload data into memory
                self.load_data()
                logger.info(f"Cat prices updated successfully. Inserted/updated {len(edited_df)} entries, deleted {len(deleted_ids)} entries.")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update cat prices: {e}", exc_info=True)
            return False
