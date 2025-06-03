"""Business logic for Excel file processing and discrepancy detection."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yaml


def load_config() -> Dict:
    """Load application configuration from config.yaml."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class ExcelProcessor:
    """Handles Excel file processing and comparison logic."""

    def __init__(self):
        self.config = load_config()
        self.tr = {}  # Store translations

    def load_translation(self, lang_code: str) -> Dict[str, str]:
        """Load language translations from i18n/[lang_code].json.

        Args:
            lang_code: Two-letter language code ('en' or 'ru')

        Returns:
            Dictionary with translation strings
        """
        try:
            i18n_path = Path(__file__).parent / "i18n" / f"{lang_code}.json"
            with open(i18n_path, "r", encoding="utf-8") as f:
                self.tr = json.load(f)
                return self.tr
        except FileNotFoundError as e:
            logging.exception("Translation file not found")
            raise FileNotFoundError(
                f"Translation file for {lang_code} not found"
            ) from e

    def detect_header(self, path: Path) -> Optional[int]:
        """Detect the header row in an Excel file."""
        try:
            raw = pd.read_excel(
                path,
                header=None,
                nrows=self.config["excel"]["max_header_rows"],
                engine=self.config["excel"]["engine"],
            )
            # Try to find header by ID column presence
            for i, row in raw.iterrows():
                txt = " ".join(map(str, row.fillna(""))).lower()
                if any(k in txt for k in self.config["id_columns"]):
                    return i

            # Fallback: use row with maximum non-empty cells
            counts = raw.notna().sum(axis=1)
            max_rows = counts[counts == counts.max()].index
            return int(max_rows[0]) if len(max_rows) else None

        except FileNotFoundError as e:
            logging.exception("Excel file not found")
            raise FileNotFoundError(f"Could not find file: {path}") from e
        except pd.errors.EmptyDataError as e:
            logging.exception("Excel file is empty")
            raise ValueError("The Excel file is empty") from e
        except (pd.errors.ParserError, ValueError) as e:
            logging.exception("Error parsing Excel file")
            raise ValueError(f"Failed to parse Excel file: {str(e)}") from e

    def get_column_names(self, df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """Find ID and amount column names in the DataFrame."""
        cols = list(df.columns)
        id_cols = [
            c
            for c in cols
            if any(k in str(c).lower() for k in self.config["id_columns"])
        ]
        amt_cols = [
            c
            for c in cols
            if any(k in str(c).lower() for k in self.config["amount_columns"])
            and c not in id_cols
        ]
        return id_cols, amt_cols

    def load_excel(self, path: Path) -> Tuple[pd.DataFrame, str, str]:
        """Load and preprocess Excel file, returns DataFrame and column names."""
        header = self.detect_header(path)
        if header is None:
            raise ValueError("Could not detect header row")

        df = pd.read_excel(path, header=header, engine=self.config["excel"]["engine"])
        id_cols, amt_cols = self.get_column_names(df)

        if not id_cols:
            raise ValueError(f"ID column not found. Available: {list(df.columns)}")
        if not amt_cols:
            raise ValueError(f"Amount column not found. Available: {list(df.columns)}")

        return df, id_cols[0], amt_cols[0]

    def preprocess_dataframe(
        self, df: pd.DataFrame, id_col: str, amount_col: str
    ) -> pd.DataFrame:
        """Clean and preprocess DataFrame for comparison."""
        # Filter out totals and empty rows
        mask = df[id_col].notna() & ~df[id_col].astype(str).str.lower().isin(
            self.config["skip_rows"]
        )
        df_clean = df.loc[mask].copy()

        # Remove duplicates and convert amounts to numeric
        df_clean = df_clean.drop_duplicates(subset=[id_col])
        df_clean[amount_col] = pd.to_numeric(
            df_clean[amount_col], errors="coerce"
        ).fillna(0)

        return df_clean

    def find_discrepancies(
        self,
        reg_df: pd.DataFrame,
        act_df: pd.DataFrame,
        reg_id: str,
        reg_amt: str,
        act_id: str,
        act_amt: str,
    ) -> pd.DataFrame:
        """Compare registry and act data to find discrepancies."""
        # Prepare data for comparison
        registry = pd.DataFrame(
            {"ID": reg_df[reg_id].astype(str), "Registry": reg_df[reg_amt]}
        )
        act = pd.DataFrame({"ID": act_df[act_id].astype(str), "Act": act_df[act_amt]})

        # Merge and find differences
        merged = pd.merge(registry, act, on="ID", how="outer").fillna(0)
        merged["Diff"] = merged["Registry"] - merged["Act"]

        # Filter by configured epsilon
        diffs = merged.loc[merged["Diff"].abs() > self.config["epsilon"]]

        # Format numeric columns
        for col in ["Registry", "Act", "Diff"]:
            diffs[col] = diffs[col].map(lambda x: f"{x:,.2f}")

        return diffs
