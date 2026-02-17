"""
features_fatigue.py

Features de fatiga calculadas SOLO con fechas de partidos anteriores.
El estado (match_dates, last_date) se actualiza post-match.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd


def rest_days(last_date: Dict[int, pd.Timestamp], pid: int, date: pd.Timestamp, cap: int = 999) -> int:
    prev = last_date.get(pid)
    if prev is None:
        return cap
    d = (date - prev).days
    if d < 0:
        d = 0
    return min(d, cap)


def matches_last_days(match_dates: Dict[int, List[pd.Timestamp]], pid: int, date: pd.Timestamp, days: int) -> int:
    lst = match_dates.get(pid, [])
    if not lst:
        return 0
    keep = [d for d in lst if (date - d).days <= days]
    match_dates[pid] = keep
    return len(keep)


def update_fatigue_post_match(
    last_date: Dict[int, pd.Timestamp],
    match_dates: Dict[int, List[pd.Timestamp]],
    winner: int,
    loser: int,
    date: pd.Timestamp,
) -> None:
    last_date[winner] = date
    last_date[loser] = date

    match_dates.setdefault(winner, []).append(date)
    match_dates.setdefault(loser, []).append(date)
