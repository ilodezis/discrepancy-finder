"""Business logic for Excel file processing and discrepancy detection.

This module has no Qt dependencies so it can be tested and reused on its own.
"""

import logging
import math
import re
import sys
from dataclasses import dataclass
from numbers import Number
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd
import yaml

__version__ = "1.2.0"

BASE_DIR = Path(__file__).parent.resolve()

STATUS_MISMATCH = "mismatch"
STATUS_ONLY_REGISTRY = "only_registry"
STATUS_ONLY_ACT = "only_act"

_MERGE_STATUS = {
    "both": STATUS_MISMATCH,
    "left_only": STATUS_ONLY_REGISTRY,
    "right_only": STATUS_ONLY_ACT,
}

# Spaces used as thousand separators by Excel/1C exports
_SPACES = re.compile(r"[\s  ']")
_NOT_NUMERIC = re.compile(r"[^\d,.\-]")
_FLOAT_ID = re.compile(r"^(\d+)\.0+$")


def resource_path(relative_path: str) -> Path:
    """Get absolute path to a bundled resource (PyInstaller compatible)."""
    base_path = Path(getattr(sys, "_MEIPASS", BASE_DIR))
    return base_path / relative_path


def load_config() -> Dict:
    """Load configuration.

    A ``config.yaml`` placed next to the executable wins over the bundled one,
    so settings can be tweaked in a frozen build without rebuilding it.
    """
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).parent / "config.yaml")
    candidates.append(resource_path("config.yaml"))

    for path in candidates:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
    raise FileNotFoundError("config.yaml not found")


class DataError(ValueError):
    """Problem with the input data; ``key`` is a translation key for the UI."""

    def __init__(self, key: str, *params):
        super().__init__(f"{key}: {params}" if params else key)
        self.key = key
        self.params = params


@dataclass
class LoadedFile:
    """Excel file reduced to one row per ID with a summed amount."""

    path: Path
    data: pd.DataFrame  # columns: ID, Amount
    id_col: str
    amount_col: str
    rows: int  # data rows before aggregation
    unparsed_amounts: int

    @property
    def total(self) -> float:
        return float(self.data["Amount"].sum())


def _is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return isinstance(value, str) and not value.strip()


def parse_amount(value) -> Optional[float]:
    """Convert a cell to float.

    Handles numbers stored as text in both RU and EN formats:
    ``"1 234,56"``, ``"1,234.56"``, ``"1.234,56"``, ``"(100,00)"``, ``"-5 ₽"``.
    Returns 0.0 for empty cells and None when the value can't be parsed.
    """
    if _is_empty(value):
        return 0.0
    if isinstance(value, bool):
        return None
    if isinstance(value, Number):
        return float(value)

    s = _SPACES.sub("", str(value)).replace("−", "-")
    negative = s.startswith("(") and s.endswith(")")
    s = _NOT_NUMERIC.sub("", s)
    if not s or not any(ch.isdigit() for ch in s):
        return None

    if "," in s and "." in s:
        # The last separator is the decimal one
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif s.count(",") > 1:
        s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    elif s.count(".") > 1:
        s = s.replace(".", "")

    try:
        result = float(s)
    except ValueError:
        return None
    return -abs(result) if negative else result


def normalize_id(value) -> Optional[str]:
    """Normalize an order ID so that 12345, 12345.0 and ' 12345 ' match."""
    if _is_empty(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    s = " ".join(str(value).split())
    match = _FLOAT_ID.match(s)
    return match.group(1) if match else s


def _norm_name(value) -> str:
    return " ".join(str(value).lower().split())


def match_columns(columns: Sequence, keywords: Sequence[str]) -> List:
    """Return columns matching any keyword, best candidates first.

    Exact matches beat partial ones, earlier keywords beat later ones and
    shorter names beat longer ones: "Сумма" is preferred over "Сумма НДС".
    """
    ranked = []
    for pos, col in enumerate(columns):
        name = _norm_name(col)
        for rank, kw in enumerate(keywords):
            if name == kw:
                ranked.append(((0, rank, 0, pos), col))
                break
            if kw in name:
                ranked.append(((1, rank, len(name), pos), col))
                break
    return [col for _, col in sorted(ranked, key=lambda item: item[0])]


class ExcelProcessor:
    """Handles Excel file processing and comparison logic."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config if config is not None else load_config()
        self.id_keywords = [_norm_name(k) for k in self.config["id_columns"]]
        self.amount_keywords = [_norm_name(k) for k in self.config["amount_columns"]]
        self.skip_rows = [_norm_name(k) for k in self.config["skip_rows"]]

    @property
    def _engine(self) -> Optional[str]:
        # None lets pandas pick openpyxl for .xlsx and xlrd for .xls
        return self.config.get("excel", {}).get("engine")

    def detect_header(self, path: Path) -> Optional[int]:
        """Find the header row: first row with an ID-like cell, else the widest row."""
        raw = pd.read_excel(
            path,
            header=None,
            nrows=self.config["excel"]["max_header_rows"],
            engine=self._engine,
        )
        if raw.empty:
            return None

        for i, row in raw.iterrows():
            cells = [_norm_name(v) for v in row.dropna()]
            if any(kw in cell for cell in cells for kw in self.id_keywords):
                return int(i)

        counts = raw.notna().sum(axis=1)
        return int(counts.idxmax()) if counts.max() > 0 else None

    def get_column_names(self, df: pd.DataFrame) -> Tuple[List, List]:
        """Find ID and amount column candidates in the DataFrame."""
        id_cols = match_columns(df.columns, self.id_keywords)
        amt_cols = [
            c
            for c in match_columns(df.columns, self.amount_keywords)
            if c not in id_cols
        ]
        return id_cols, amt_cols

    def read_excel(self, path: Path) -> Tuple[pd.DataFrame, str, str]:
        """Read an Excel file and detect its ID and amount columns."""
        path = Path(path)
        header = self.detect_header(path)
        if header is None:
            raise DataError("err_header")

        df = pd.read_excel(path, header=header, engine=self._engine)
        id_cols, amt_cols = self.get_column_names(df)
        columns = [str(c) for c in df.columns]
        if not id_cols:
            raise DataError("err_id", columns)
        if not amt_cols:
            raise DataError("err_amount", columns)

        if len(amt_cols) > 1:
            logging.info(
                "%s: amount column candidates %s, using '%s'",
                path.name,
                [str(c) for c in amt_cols],
                amt_cols[0],
            )
        return df, id_cols[0], amt_cols[0]

    def prepare(
        self, df: pd.DataFrame, id_col, amount_col
    ) -> Tuple[pd.DataFrame, int, int]:
        """Clean a DataFrame down to unique IDs with amounts.

        Returns the prepared data, the number of data rows (totals excluded) and
        the number of amounts that couldn't be parsed (those are counted as 0
        and reported to the user).
        """
        data = pd.DataFrame(
            {
                "ID": df[id_col].map(normalize_id),
                "Amount": df[amount_col].map(parse_amount).astype(float),
            }
        )
        is_total = (
            data["ID"].fillna("").str.lower().str.startswith(tuple(self.skip_rows))
        )
        data = data.loc[data["ID"].notna() & ~is_total].copy()
        rows = len(data)

        unparsed = int(data["Amount"].isna().sum())
        data["Amount"] = data["Amount"].fillna(0.0)

        if self.config.get("duplicate_ids", "sum") == "first":
            data = data.drop_duplicates(subset="ID")
        else:
            data = data.groupby("ID", sort=False, as_index=False)["Amount"].sum()
        return data.reset_index(drop=True), rows, unparsed

    def load_file(self, path: Path) -> LoadedFile:
        """Read and prepare one Excel file."""
        path = Path(path)
        df, id_col, amount_col = self.read_excel(path)
        data, rows, unparsed = self.prepare(df, id_col, amount_col)
        loaded = LoadedFile(
            path=path,
            data=data,
            id_col=str(id_col),
            amount_col=str(amount_col),
            rows=rows,
            unparsed_amounts=unparsed,
        )
        logging.info(
            "Loaded %s: ID='%s', amount='%s', %d IDs",
            path.name,
            loaded.id_col,
            loaded.amount_col,
            len(data),
        )
        if unparsed:
            logging.warning(
                "%s: %d amounts could not be parsed and were counted as 0",
                path.name,
                unparsed,
            )
        return loaded

    def find_discrepancies(
        self, registry: pd.DataFrame, act: pd.DataFrame
    ) -> pd.DataFrame:
        """Compare prepared registry and act data.

        Returns rows whose amounts differ by more than ``epsilon`` and IDs present
        in only one of the files. Columns: ID, Registry, Act, Diff, Status.
        """
        merged = pd.merge(
            registry.rename(columns={"Amount": "Registry"}),
            act.rename(columns={"Amount": "Act"}),
            on="ID",
            how="outer",
            indicator=True,
        )
        merged["Status"] = merged.pop("_merge").astype(str).map(_MERGE_STATUS)
        merged[["Registry", "Act"]] = merged[["Registry", "Act"]].fillna(0.0)
        merged["Diff"] = (merged["Registry"] - merged["Act"]).round(2)

        mask = (merged["Diff"].abs() > self.config["epsilon"]) | (
            merged["Status"] != STATUS_MISMATCH
        )
        diffs = merged.loc[mask, ["ID", "Registry", "Act", "Diff", "Status"]]
        diffs = diffs.sort_values("Diff", key=abs, ascending=False, kind="stable")
        return diffs.reset_index(drop=True)
