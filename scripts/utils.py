from pathlib import Path
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_ATP_DIR = DATA_DIR / "raw" / "atp"
PROCESSED_DIR = DATA_DIR / "processed"


def parse_yyyymmdd(x) -> pd.Timestamp:
    """Parse dates of the form YYYYMMDD used in Sackmann datasets."""
    return pd.to_datetime(str(int(x)), format="%Y%m%d", errors="coerce")


def safe_float(x) -> float:
    try:
        return float(x)
    except Exception:
        return np.nan


def mean_last(values, n: int, default: float) -> float:
    """Mean of last n valid values, or default if insufficient history."""
    if not values:
        return default
    tail = [v for v in values[-n:] if not pd.isna(v)]
    return float(np.mean(tail)) if tail else default
