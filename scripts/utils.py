from pathlib import Path
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_ATP_DIR = DATA_DIR / "raw" / "atp"
PROCESSED_DIR = DATA_DIR / "processed"


def parse_yyyymmdd(x):
    if x is None or (isinstance(x, float) and np.isnan(x)) or pd.isna(x):
        return pd.NaT

    # a veces viene como string o como float tipo 19870101.0
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]

    # si no son 8 dígitos, lo marco como inválido
    if len(s) != 8 or not s.isdigit():
        return pd.NaT

    return pd.to_datetime(s, format="%Y%m%d", errors="coerce")


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


def load_players_lookup() -> dict[int, dict]:
    p = RAW_ATP_DIR / "atp_players.csv"
    df = pd.read_csv(p, low_memory=False)

    # dob viene como YYYYMMDD en Sackmann; parse_yyyymmdd ya existe
    df["dob"] = df["dob"].apply(parse_yyyymmdd)

    keep = ["player_id", "hand", "height", "dob"]
    df = df[keep].copy()

    df["height"] = pd.to_numeric(df["height"], errors="coerce")

    return df.set_index("player_id").to_dict(orient="index")


