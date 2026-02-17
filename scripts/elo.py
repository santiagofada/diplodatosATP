import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional

ELO_BASE = 1500.0
SURFACES = {"Hard", "Clay", "Grass", "Carpet"}

# Experience-based K
K_MIN = 16.0
K_MAX = 48.0
K_EXP_SCALE = 40.0

# Tournament importance
LEVEL_MULT = {
    "G": 1.35,  # Grand Slam
    "M": 1.15,  # Masters 1000
    "F": 1.10,  # ATP Finals
    "A": 1.00,  # ATP 500
    "B": 0.90,  # ATP 250
}

# Inactivity decay
DECAY_START_DAYS = 180
HALF_LIFE_DAYS = 180


@dataclass
class EloState:
    """
    Online Elo rating system.
    Ratings are updated strictly post-match to avoid leakage.
    """
    elo_global: Dict[int, float]
    elo_surface: Dict[str, Dict[int, float]]
    matches_played: Dict[int, int]

    def __init__(self):
        self.elo_global = {}
        self.elo_surface = {s: {} for s in SURFACES}
        self.matches_played = {}

    @staticmethod
    def win_prob(ra: float, rb: float) -> float:
        return 1.0 / (1.0 + 10 ** ((rb - ra) / 400))

    def get(self, pid: int, surface: Optional[str] = None) -> float:
        if surface in SURFACES:
            return self.elo_surface[surface].get(pid, ELO_BASE)
        return self.elo_global.get(pid, ELO_BASE)

    def k_experience(self, pid: int) -> float:
        m = self.matches_played.get(pid, 0)
        return K_MIN + (K_MAX - K_MIN) * np.exp(-m / K_EXP_SCALE)

    def decay_if_needed(self, pid: int, rest_days: int) -> None:
        if rest_days < DECAY_START_DAYS:
            return

        def decay(cur):
            return ELO_BASE + (cur - ELO_BASE) * (0.5 ** (rest_days / HALF_LIFE_DAYS))

        self.elo_global[pid] = decay(self.get(pid))
        for s in SURFACES:
            self.elo_surface[s][pid] = decay(self.get(pid, s))

    def update(self, winner: int, loser: int, level: str, surface: Optional[str]) -> None:
        k = self.k_experience(winner)
        k *= LEVEL_MULT.get(level, 1.0)

        ra, rb = self.get(winner), self.get(loser)
        pa = self.win_prob(ra, rb)

        self.elo_global[winner] = ra + k * (1 - pa)
        self.elo_global[loser] = rb - k * (1 - pa)

        if surface in SURFACES:
            rsa, rsb = self.get(winner, surface), self.get(loser, surface)
            psa = self.win_prob(rsa, rsb)
            self.elo_surface[surface][winner] = rsa + k * (1 - psa)
            self.elo_surface[surface][loser] = rsb - k * (1 - psa)

        self.matches_played[winner] = self.matches_played.get(winner, 0) + 1
        self.matches_played[loser] = self.matches_played.get(loser, 0) + 1
