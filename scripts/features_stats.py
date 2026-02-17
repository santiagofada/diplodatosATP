"""
features_stats.py

Stats históricas (rolling) de servicio/devolución.

Se calculan desde columnas post-match del CSV (w_*, l_*),
pero se usan SOLO como promedios de partidos anteriores (rolling pre-match).
Luego se actualizan post-match agregando las rates de este partido.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


def _safe_float(x):
    try:
        if x is None:
            return np.nan
        return float(x)
    except Exception:
        return np.nan


def _rate(num, den):
    if den is None or np.isnan(den) or den <= 0:
        return np.nan
    if num is None or np.isnan(num):
        return np.nan
    return float(num) / float(den)


def rates_from_row(is_winner: bool, r: pd.Series) -> Dict[str, float]:
    pref = "w_" if is_winner else "l_"

    ace = _safe_float(r.get(pref + "ace"))
    df = _safe_float(r.get(pref + "df"))
    svpt = _safe_float(r.get(pref + "svpt"))

    first_in = _safe_float(r.get(pref + "1stIn"))
    first_won = _safe_float(r.get(pref + "1stWon"))
    second_won = _safe_float(r.get(pref + "2ndWon"))

    bp_saved = _safe_float(r.get(pref + "bpSaved"))
    bp_faced = _safe_float(r.get(pref + "bpFaced"))

    second_total = (svpt - first_in) if (not np.isnan(svpt) and not np.isnan(first_in)) else np.nan

    return {
        "ace_rate": _rate(ace, svpt),
        "df_rate": _rate(df, svpt),
        "first_in_rate": _rate(first_in, svpt),
        "first_won_rate": _rate(first_won, first_in),
        "second_won_rate": _rate(second_won, second_total),
        "bp_saved_rate": _rate(bp_saved, bp_faced),
    }


def stat_avg(stats_hist: Dict[int, Dict[str, List[float]]], pid: int, metric: str, n: int = 20, default: float = 0.0) -> float:
    h = stats_hist.get(pid, {}).get(metric, [])
    if not h:
        return default
    tail = [v for v in h[-n:] if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if not tail:
        return default
    return float(np.mean(tail))


def update_stats_post_match(stats_hist: Dict[int, Dict[str, List[float]]], winner: int, loser: int, r: pd.Series) -> None:
    w_rates = rates_from_row(True, r)
    l_rates = rates_from_row(False, r)

    stats_hist.setdefault(winner, {})
    stats_hist.setdefault(loser, {})

    for k, v in w_rates.items():
        stats_hist[winner].setdefault(k, []).append(v)
    for k, v in l_rates.items():
        stats_hist[loser].setdefault(k, []).append(v)
