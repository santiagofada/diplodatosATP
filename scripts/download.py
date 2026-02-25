import urllib.request
import urllib.error
import pandas as pd
from pathlib import Path

from utils import RAW_ATP_DIR, parse_yyyymmdd

ATP_BASE = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/"


def download(url: str, out: Path) -> bool:
    """
    Download a file if it exists upstream.
    Non-existing files are skipped silently (HTTP 404).
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        return True
    try:
        urllib.request.urlretrieve(url, out)
        return True
    except Exception:
        return False


def ensure_atp_data(year_from: int, year_to: int, download_rankings: bool = True) -> None:
    """
    Download all required ATP datasets from Jeff Sackmann repository.
    """
    RAW_ATP_DIR.mkdir(parents=True, exist_ok=True)

    for y in range(year_from, year_to + 1):
        download(
            ATP_BASE + f"atp_matches_{y}.csv",
            RAW_ATP_DIR / f"atp_matches_{y}.csv",
        )

    if download_rankings:
        for rf in [
            "atp_rankings_00s.csv",
            "atp_rankings_10s.csv",
            "atp_rankings_20s.csv",
            "atp_rankings_current.csv",
        ]:
            download(ATP_BASE + rf, RAW_ATP_DIR / rf)

    download(ATP_BASE + "atp_players.csv", RAW_ATP_DIR / "atp_players.csv")


def load_matches(year_from: int, year_to: int) -> pd.DataFrame:
    """
    Load ATP matches and return them ordered chronologically.
    """
    parts = []
    for y in range(year_from, year_to + 1):
        p = RAW_ATP_DIR / f"atp_matches_{y}.csv"
        if p.exists():
            parts.append(pd.read_csv(p, low_memory=False))

    df = pd.concat(parts, ignore_index=True)
    df["tourney_date"] = df["tourney_date"].apply(parse_yyyymmdd)

    df = df.dropna(subset=["tourney_date", "winner_id", "loser_id"])
    df["winner_id"] = df["winner_id"].astype(int)
    df["loser_id"] = df["loser_id"].astype(int)

    return df.sort_values(
        ["tourney_date", "tourney_id", "match_num"],
        kind="mergesort"
    ).reset_index(drop=True)

def load_players_lookup() -> dict:
    """
    Load atp_players.csv and return dict: pid -> {"dob": Timestamp, "height": float, "hand": str}
    """
    p = RAW_ATP_DIR / "atp_players.csv"
    if not p.exists():
        raise FileNotFoundError(f"No existe {p}. Corré ensure_atp_data primero.")

    df = pd.read_csv(p)

    # dob viene como YYYYMMDD (a veces vacío)
    df["dob"] = pd.to_datetime(df["dob"], format="%Y%m%d", errors="coerce")

    # height a numérico
    df["height"] = pd.to_numeric(df.get("height"), errors="coerce")

    # hand suele ser "R" / "L" (puede venir NaN)
    df["hand"] = df.get("hand")

    # player_id es la key
    df["player_id"] = pd.to_numeric(df["player_id"], errors="coerce").astype("Int64")

    out = {}
    for row in df.itertuples(index=False):
        pid = getattr(row, "player_id")
        if pd.isna(pid):
            continue
        out[int(pid)] = {
            "dob": getattr(row, "dob"),
            "height": getattr(row, "height"),
            "hand": getattr(row, "hand"),
        }
    return out
