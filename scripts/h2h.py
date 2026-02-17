"""
h2h.py

Head-to-head global y por superficie, actualizado post-match.
Guardamos el balance en una clave ordenada (min_id, max_id):
- valor positivo => favorece al menor id
- valor negativo => favorece al mayor id
Para un orden (p1,p2) se devuelve con signo según quién sea p1.
"""

from __future__ import annotations

from typing import Dict, Tuple


def _pair(a: int, b: int) -> Tuple[int, int]:
    return (a, b) if a < b else (b, a)


def h2h_pre_match(h2h_global: Dict[Tuple[int, int], int], p1: int, p2: int) -> int:
    p_min, p_max = _pair(p1, p2)
    cur = h2h_global.get((p_min, p_max), 0)
    return cur if p1 == p_min else -cur


def h2h_surface_pre_match(
    h2h_surface: Dict[Tuple[str, int, int], int], surface: str, p1: int, p2: int
) -> int:
    p_min, p_max = _pair(p1, p2)
    cur = h2h_surface.get((surface, p_min, p_max), 0)
    return cur if p1 == p_min else -cur


def update_h2h_post_match(
    h2h_global: Dict[Tuple[int, int], int],
    h2h_surface: Dict[Tuple[str, int, int], int],
    surface: str,
    winner: int,
    loser: int,
) -> None:
    p_min, p_max = _pair(winner, loser)

    cur_g = h2h_global.get((p_min, p_max), 0)
    cur_s = h2h_surface.get((surface, p_min, p_max), 0)

    change = 1 if winner == p_min else -1
    h2h_global[(p_min, p_max)] = cur_g + change
    h2h_surface[(surface, p_min, p_max)] = cur_s + change
