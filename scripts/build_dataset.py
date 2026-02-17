"""
scripts/build_dataset.py

Orquestador: construye un dataset PRE-MATCH para predecir ganador (y_p1_win)
usando el repo JeffSackmann/tennis_atp.

- Descarga: atp_matches_YYYY.csv (+ rankings si se piden) y atp_players.csv
- Separa qualies por round que empieza con "Q" (Q1/Q2/Q3/QR) dentro del mismo archivo.
- Features online (sin leakage): todo se calcula pre-match y se actualiza post-match.
- Output: data/processed/<out>.csv
"""

from __future__ import annotations

import argparse
import random
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd

from utils import PROCESSED_DIR
from download import ensure_atp_data, load_matches
from elo import EloState, SURFACES
from rankings import load_rankings, build_rank_hist, rank_delta_weeks

from features_form import winrate_last, get_streak, update_form_post_match
from features_fatigue import rest_days, matches_last_days, update_fatigue_post_match
from features_stats import stat_avg, update_stats_post_match
from h2h import h2h_pre_match, h2h_surface_pre_match, update_h2h_post_match


def _to_float(x) -> float:
    try:
        if x is None:
            return np.nan
        if isinstance(x, float) and np.isnan(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan


def build_dataset(
    df_main: pd.DataFrame,
    df_qual_for_updates: Optional[pd.DataFrame],
    rank_hist: Dict[int, List[Tuple[pd.Timestamp, int, int]]],
    seed: int,
    default_rank_impute: int = 2000,
    default_rp_impute: int = 0,
    roll_n: int = 20,
) -> pd.DataFrame:
    """
    Construye dataset PRE-MATCH (clasificación) evitando data leakage:
    - todo se calcula online (en orden temporal)
    - updates post-match: Elo, rolling stats, forma, fatiga, H2H, carga del torneo
    """

    random.seed(seed)
    np.random.seed(seed)

    elo = EloState()

    # Trackers online
    last_date: Dict[int, pd.Timestamp] = {}
    match_dates: Dict[int, List[pd.Timestamp]] = {}
    win_hist: Dict[int, List[int]] = {}
    streak: Dict[int, int] = {}
    h2h_global: Dict[Tuple[int, int], int] = {}
    h2h_surface: Dict[Tuple[str, int, int], int] = {}
    stats_hist: Dict[int, Dict[str, List[float]]] = {}
    tourney_matches: Dict[Tuple[str, int], int] = {}
    tourney_minutes: Dict[Tuple[str, int], int] = {}

    def post_match_update(
        r: pd.Series,
        date: pd.Timestamp,
        winner: int,
        loser: int,
        level: str,
        surface: str,
        tid: str,
    ) -> None:
        # Elo: surface-specific solo si la surface es estándar
        elo_surface = surface if surface in SURFACES else None
        elo.update(winner=winner, loser=loser, level=level, surface=elo_surface)

        update_fatigue_post_match(last_date, match_dates, winner, loser, date)
        update_form_post_match(win_hist, streak, winner, loser)
        update_h2h_post_match(h2h_global, h2h_surface, surface, winner, loser)
        update_stats_post_match(stats_hist, winner, loser, r)

        # Carga del torneo (pre-match se lee, post-match se incrementa)
        tourney_matches[(tid, winner)] = tourney_matches.get((tid, winner), 0) + 1
        tourney_matches[(tid, loser)] = tourney_matches.get((tid, loser), 0) + 1

        minutes = _to_float(r.get("minutes"))
        if not np.isnan(minutes):
            tourney_minutes[(tid, winner)] = tourney_minutes.get((tid, winner), 0) + int(minutes)
            tourney_minutes[(tid, loser)] = tourney_minutes.get((tid, loser), 0) + int(minutes)

    # 0) Qualies: SOLO updates (no filas)
    if df_qual_for_updates is not None and not df_qual_for_updates.empty:
        for _, r in df_qual_for_updates.iterrows():
            date = r["tourney_date"]
            w = int(r["winner_id"])
            l = int(r["loser_id"])
            surface = r.get("surface") if pd.notna(r.get("surface")) else "Unknown"
            level = str(r.get("tourney_level") or "UNK")
            tid = str(r.get("tourney_id"))

            w_rest = rest_days(last_date, w, date)
            l_rest = rest_days(last_date, l, date)
            elo.decay_if_needed(w, w_rest)
            elo.decay_if_needed(l, l_rest)

            post_match_update(r, date, w, l, level, surface, tid)

    # 1) Main draw: genera filas
    rows: List[dict] = []

    for _, r in df_main.iterrows():
        date = r["tourney_date"]
        w = int(r["winner_id"])
        l = int(r["loser_id"])
        surface = r.get("surface") if pd.notna(r.get("surface")) else "Unknown"
        level = str(r.get("tourney_level") or "UNK")
        tid = str(r.get("tourney_id"))

        round_ = r.get("round") if pd.notna(r.get("round")) else "UNK"
        best_of = _to_float(r.get("best_of"))

        # Decay pre-match
        w_rest = rest_days(last_date, w, date)
        l_rest = rest_days(last_date, l, date)
        elo.decay_if_needed(w, w_rest)
        elo.decay_if_needed(l, l_rest)

        # Elo pre-match
        w_elo = elo.get(w)
        l_elo = elo.get(l)
        w_selo = elo.get(w, surface if surface in SURFACES else None)
        l_selo = elo.get(l, surface if surface in SURFACES else None)

        # Forma pre-match
        w_wr10 = winrate_last(win_hist, w, 10)
        l_wr10 = winrate_last(win_hist, l, 10)
        w_wr20 = winrate_last(win_hist, w, 20)
        l_wr20 = winrate_last(win_hist, l, 20)
        w_st = get_streak(streak, w)
        l_st = get_streak(streak, l)

        # Fatiga pre-match
        w_m7 = matches_last_days(match_dates, w, date, 7)
        l_m7 = matches_last_days(match_dates, l, date, 7)
        w_m14 = matches_last_days(match_dates, w, date, 14)
        l_m14 = matches_last_days(match_dates, l, date, 14)
        w_m30 = matches_last_days(match_dates, w, date, 30)
        l_m30 = matches_last_days(match_dates, l, date, 30)

        # Carga del torneo pre-match
        w_tms = tourney_matches.get((tid, w), 0)
        l_tms = tourney_matches.get((tid, l), 0)
        w_tmin = tourney_minutes.get((tid, w), 0)
        l_tmin = tourney_minutes.get((tid, l), 0)

        # H2H pre-match (w vs l)
        wl_h2h = h2h_pre_match(h2h_global, w, l)
        wl_h2h_s = h2h_surface_pre_match(h2h_surface, surface, w, l)

        # Rankings desde el match file (imputados)
        w_rank = _to_float(r.get("winner_rank"))
        l_rank = _to_float(r.get("loser_rank"))
        w_rp = _to_float(r.get("winner_rank_points"))
        l_rp = _to_float(r.get("loser_rank_points"))

        if np.isnan(w_rank):
            w_rank = float(default_rank_impute)
        if np.isnan(l_rank):
            l_rank = float(default_rank_impute)
        if np.isnan(w_rp):
            w_rp = float(default_rp_impute)
        if np.isnan(l_rp):
            l_rp = float(default_rp_impute)

        # Deltas ranking (4/8 semanas) desde rank_hist
        w_rank_d4 = w_rp_d4 = l_rank_d4 = l_rp_d4 = np.nan
        w_rank_d8 = w_rp_d8 = l_rank_d8 = l_rp_d8 = np.nan

        wh = rank_hist.get(w, [])
        lh = rank_hist.get(l, [])

        dr, dp = rank_delta_weeks(wh, date, 4)
        if dr is not None:
            w_rank_d4 = float(dr)
        if dp is not None:
            w_rp_d4 = float(dp)

        dr, dp = rank_delta_weeks(lh, date, 4)
        if dr is not None:
            l_rank_d4 = float(dr)
        if dp is not None:
            l_rp_d4 = float(dp)

        dr, dp = rank_delta_weeks(wh, date, 8)
        if dr is not None:
            w_rank_d8 = float(dr)
        if dp is not None:
            w_rp_d8 = float(dp)

        dr, dp = rank_delta_weeks(lh, date, 8)
        if dr is not None:
            l_rank_d8 = float(dr)
        if dp is not None:
            l_rp_d8 = float(dp)

        # Seed/entry
        w_entry, l_entry = r.get("winner_entry"), r.get("loser_entry")
        w_seed = _to_float(r.get("winner_seed"))
        l_seed = _to_float(r.get("loser_seed"))

        # Stats rolling pre-match
        w_ace = stat_avg(stats_hist, w, "ace_rate", n=roll_n)
        l_ace = stat_avg(stats_hist, l, "ace_rate", n=roll_n)
        w_df = stat_avg(stats_hist, w, "df_rate", n=roll_n)
        l_df = stat_avg(stats_hist, l, "df_rate", n=roll_n)
        w_1stin = stat_avg(stats_hist, w, "first_in_rate", n=roll_n)
        l_1stin = stat_avg(stats_hist, l, "first_in_rate", n=roll_n)
        w_1stwon = stat_avg(stats_hist, w, "first_won_rate", n=roll_n)
        l_1stwon = stat_avg(stats_hist, l, "first_won_rate", n=roll_n)
        w_2ndwon = stat_avg(stats_hist, w, "second_won_rate", n=roll_n)
        l_2ndwon = stat_avg(stats_hist, l, "second_won_rate", n=roll_n)
        w_bps = stat_avg(stats_hist, w, "bp_saved_rate", n=roll_n)
        l_bps = stat_avg(stats_hist, l, "bp_saved_rate", n=roll_n)

        # Random swap (simetría)
        if random.random() < 0.5:
            # P1 = ganador real
            p1, p2, y = w, l, 1

            p1_elo, p2_elo = w_elo, l_elo
            p1_selo, p2_selo = w_selo, l_selo

            p1_rank, p2_rank = w_rank, l_rank
            p1_rp, p2_rp = w_rp, l_rp

            p1_rank_d4, p2_rank_d4 = w_rank_d4, l_rank_d4
            p1_rp_d4, p2_rp_d4 = w_rp_d4, l_rp_d4
            p1_rank_d8, p2_rank_d8 = w_rank_d8, l_rank_d8
            p1_rp_d8, p2_rp_d8 = w_rp_d8, l_rp_d8

            p1_wr10, p2_wr10 = w_wr10, l_wr10
            p1_wr20, p2_wr20 = w_wr20, l_wr20
            p1_st, p2_st = w_st, l_st

            p1_rest, p2_rest = w_rest, l_rest
            p1_m7, p2_m7 = w_m7, l_m7
            p1_m14, p2_m14 = w_m14, l_m14
            p1_m30, p2_m30 = w_m30, l_m30

            p1_tms, p2_tms = w_tms, l_tms
            p1_tmin, p2_tmin = w_tmin, l_tmin

            p1_entry, p2_entry = w_entry, l_entry
            p1_seed, p2_seed = w_seed, l_seed

            h2h_diff = wl_h2h
            h2h_surface_diff = wl_h2h_s

            p1_ace, p2_ace = w_ace, l_ace
            p1_df, p2_df = w_df, l_df
            p1_1stin, p2_1stin = w_1stin, l_1stin
            p1_1stwon, p2_1stwon = w_1stwon, l_1stwon
            p1_2ndwon, p2_2ndwon = w_2ndwon, l_2ndwon
            p1_bps, p2_bps = w_bps, l_bps
        else:
            # P1 = perdedor real
            p1, p2, y = l, w, 0

            p1_elo, p2_elo = l_elo, w_elo
            p1_selo, p2_selo = l_selo, w_selo

            p1_rank, p2_rank = l_rank, w_rank
            p1_rp, p2_rp = l_rp, w_rp

            p1_rank_d4, p2_rank_d4 = l_rank_d4, w_rank_d4
            p1_rp_d4, p2_rp_d4 = l_rp_d4, w_rp_d4
            p1_rank_d8, p2_rank_d8 = l_rank_d8, w_rank_d8
            p1_rp_d8, p2_rp_d8 = l_rp_d8, w_rp_d8

            p1_wr10, p2_wr10 = l_wr10, w_wr10
            p1_wr20, p2_wr20 = l_wr20, w_wr20
            p1_st, p2_st = l_st, w_st

            p1_rest, p2_rest = l_rest, w_rest
            p1_m7, p2_m7 = l_m7, w_m7
            p1_m14, p2_m14 = l_m14, w_m14
            p1_m30, p2_m30 = l_m30, w_m30

            p1_tms, p2_tms = l_tms, w_tms
            p1_tmin, p2_tmin = l_tmin, w_tmin

            p1_entry, p2_entry = l_entry, w_entry
            p1_seed, p2_seed = l_seed, w_seed

            h2h_diff = -wl_h2h
            h2h_surface_diff = -wl_h2h_s

            p1_ace, p2_ace = l_ace, w_ace
            p1_df, p2_df = l_df, w_df
            p1_1stin, p2_1stin = l_1stin, w_1stin
            p1_1stwon, p2_1stwon = l_1stwon, w_1stwon
            p1_2ndwon, p2_2ndwon = l_2ndwon, w_2ndwon
            p1_bps, p2_bps = l_bps, w_bps

        rows.append(
            {
                "date": date,
                "tourney_id": tid,
                "tourney_level": level,
                "surface": surface,
                "round": round_,
                "best_of": best_of,
                "p1_id": int(p1),
                "p2_id": int(p2),
                "y_p1_win": int(y),

                "elo_diff": p1_elo - p2_elo,
                "surface_elo_diff": p1_selo - p2_selo,

                "rank_diff": p1_rank - p2_rank,
                "rank_points_diff": p1_rp - p2_rp,
                "rank_d4_diff": p1_rank_d4 - p2_rank_d4,
                "rank_points_d4_diff": p1_rp_d4 - p2_rp_d4,
                "rank_d8_diff": p1_rank_d8 - p2_rank_d8,
                "rank_points_d8_diff": p1_rp_d8 - p2_rp_d8,

                "wr10_diff": p1_wr10 - p2_wr10,
                "wr20_diff": p1_wr20 - p2_wr20,
                "streak_diff": p1_st - p2_st,

                "rest_diff": p1_rest - p2_rest,
                "m7_diff": p1_m7 - p2_m7,
                "m14_diff": p1_m14 - p2_m14,
                "m30_diff": p1_m30 - p2_m30,

                "tourney_matches_so_far_diff": p1_tms - p2_tms,
                "tourney_minutes_so_far_diff": p1_tmin - p2_tmin,

                "h2h_diff": h2h_diff,
                "h2h_surface_diff": h2h_surface_diff,

                "seed_diff": (p1_seed - p2_seed) if (not np.isnan(p1_seed) and not np.isnan(p2_seed)) else np.nan,
                "entry_p1": str(p1_entry) if p1_entry is not None and not (isinstance(p1_entry, float) and np.isnan(p1_entry)) else "NONE",
                "entry_p2": str(p2_entry) if p2_entry is not None and not (isinstance(p2_entry, float) and np.isnan(p2_entry)) else "NONE",

                "ace_rate_diff": p1_ace - p2_ace,
                "df_rate_diff": p1_df - p2_df,
                "first_in_rate_diff": p1_1stin - p2_1stin,
                "first_won_rate_diff": p1_1stwon - p2_1stwon,
                "second_won_rate_diff": p1_2ndwon - p2_2ndwon,
                "bp_saved_rate_diff": p1_bps - p2_bps,
            }
        )

        # Post-match updates (con el orden real winner/loser)
        post_match_update(r, date, w, l, level, surface, tid)

    out = pd.DataFrame(rows)
    out["surface"] = out["surface"].fillna("Unknown")
    out["round"] = out["round"].fillna("UNK")
    out["tourney_level"] = out["tourney_level"].fillna("UNK")
    out["entry_p1"] = out["entry_p1"].fillna("NONE")
    out["entry_p2"] = out["entry_p2"].fillna("NONE")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year-from", type=int, default=2010)
    ap.add_argument("--year-to", type=int, default=2024)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=str, default="atp_match_prediction_full.csv")
    ap.add_argument("--no-rankings", action="store_true")
    ap.add_argument("--use-qual-for-elo", action="store_true", help="Usa qualies (round empieza con Q) SOLO para updates.")
    args = ap.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    ensure_atp_data(args.year_from, args.year_to, download_rankings=not args.no_rankings)

    df_all = load_matches(args.year_from, args.year_to)

    # Qualies dentro del mismo archivo: rounds que empiezan con "Q"
    is_qual = df_all["round"].astype(str).str.startswith("Q", na=False)
    df_main = df_all[~is_qual].reset_index(drop=True)
    df_qual = df_all[is_qual].reset_index(drop=True) if args.use_qual_for_elo else None

    if args.no_rankings:
        rank_hist = {}
    else:
        rankings = load_rankings(args.year_from, args.year_to)
        rank_hist = build_rank_hist(rankings)

    df_out = build_dataset(
        df_main=df_main,
        df_qual_for_updates=df_qual,
        rank_hist=rank_hist,
        seed=args.seed,
    )

    out_path = PROCESSED_DIR / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_path, index=False)

    print(f"Dataset generado: {out_path}")
    print("Balance y_p1_win:")
    print(df_out["y_p1_win"].value_counts(normalize=True).round(4))


if __name__ == "__main__":
    main()
