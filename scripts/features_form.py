"""
features_form.py

Features de "forma" (momentum) calculadas SOLO con historia previa.
El estado se actualiza post-match.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np


def winrate_last(win_hist: Dict[int, List[int]], pid: int, n: int, default: float = 0.5) -> float:
    h = win_hist.get(pid, [])
    if not h:
        return default
    tail = h[-n:]
    return float(np.mean(tail)) if tail else default


def get_streak(streak: Dict[int, int], pid: int) -> int:
    return int(streak.get(pid, 0))


def update_form_post_match(win_hist: Dict[int, List[int]], streak: Dict[int, int], winner: int, loser: int) -> None:
    win_hist.setdefault(winner, []).append(1)
    win_hist.setdefault(loser, []).append(0)

    sw = streak.get(winner, 0)
    sl = streak.get(loser, 0)

    streak[winner] = sw + 1 if sw >= 0 else 1
    streak[loser] = sl - 1 if sl <= 0 else -1
