import pandas as pd
from typing import Dict, List, Tuple

from utils import RAW_ATP_DIR, parse_yyyymmdd


def load_rankings(year_from: int, year_to: int) -> pd.DataFrame:
    """
    Load weekly ATP rankings and keep only relevant years.
    """
    parts = []
    for p in RAW_ATP_DIR.glob("atp_rankings_*.csv"):
        df = pd.read_csv(p)
        df["ranking_date"] = df["ranking_date"].apply(parse_yyyymmdd)
        df = df[
            (df["ranking_date"].dt.year >= year_from - 1) &
            (df["ranking_date"].dt.year <= year_to)
        ]
        parts.append(df[["ranking_date", "player", "rank", "points"]])

    if not parts:
        return pd.DataFrame()

    out = pd.concat(parts, ignore_index=True)
    out = out.rename(columns={"player": "player_id", "points": "rank_points"})
    return out.sort_values(["player_id", "ranking_date"])


def build_rank_hist(df: pd.DataFrame) -> Dict[int, List[Tuple[pd.Timestamp, int, int]]]:
    """
    Ranking history per player for fast temporal lookup.
    """
    hist = {}
    for pid, g in df.groupby("player_id"):
        hist[int(pid)] = list(zip(g["ranking_date"], g["rank"], g["rank_points"]))
    return hist


def rank_delta_weeks(hist, date, weeks: int):
    """Ranking change relative to a given number of weeks in the past."""
    if not hist:
        return None, None

    cur = next(((r, p) for d, r, p in reversed(hist) if d <= date), None)
    past_date = date - pd.Timedelta(days=7 * weeks)
    past = next(((r, p) for d, r, p in reversed(hist) if d <= past_date), None)

    if cur is None or past is None:
        return None, None

    return cur[0] - past[0], cur[1] - past[1]
