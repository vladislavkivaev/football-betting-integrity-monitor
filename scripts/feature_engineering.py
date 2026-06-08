"""
feature_engineering.py
Football Betting Integrity Monitor — feature build (production).

Reads the dbt mart (s_<schema>.mart_matches_clean) from PostgreSQL and produces the
modelling feature matrix plus its documentation. This is the reproducible counterpart to
notebooks/02_features.ipynb: same logic, none of the exploratory cells.

Outputs (default data/processed/):
  - features.parquet          full enriched matrix (8,915 rows)
  - feature_roles.json        column -> role map + the two model sets (H2 universal, H3 tier-aware)
  - feature_dictionary.csv    per-feature family / representation / tail shape / imputation plan

Design notes (decided in 02_features):
  - Features are z-scored per league-season. COVID (19/20) is its own baseline group, so it is
    scored against itself — no masking. The is_covid_season flag is carried for 03_modeling.
  - Both representations are kept: natural-unit (-> universal IF, H2) and z-scored (-> tier-aware, H3).
  - Reversal is a proxy: Bet365 vs Pinnacle direction disagreement (open+close only, no intra-window data).
  - xmkt_div_abs is EXCLUDED from the model set (redundant with b365_vs_ps_close_*); its
    signed/outcome columns are kept descriptive-only.
  - pinnacle_missing flags the structural ~50% Pinnacle gap in 25/26 (football-data upload lag,
    cuts off ~Jan 2026) plus thin early mid-tier coverage. Built BEFORE any imputation.
  - Imputation itself runs in 03_modeling; this script only records the plan.

Usage:
    python scripts/feature_engineering.py                 # writes to data/processed/
    python scripts/feature_engineering.py --output-dir /tmp/out
Run from the repo root. Requires .env with DB_HOST/PORT/NAME/USER/PASSWORD/SCHEMA.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("feature_engineering")

# --------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------
GROUP_KEYS = ["league", "season"]
ROLL_WINDOW = 38
ROLL_MIN_PERIODS = 10

DRIFT_COLS = ["b365_drift_h", "b365_drift_d", "b365_drift_a",
              "pinnacle_drift_h", "pinnacle_drift_d", "pinnacle_drift_a"]
SPREAD_COLS = ["opening_spread_h", "opening_spread_d", "opening_spread_a",
               "closing_spread_h", "closing_spread_d", "closing_spread_a",
               "spread_change_h", "spread_change_d", "spread_change_a",
               "max_opening_spread", "max_closing_spread", "max_spread_change"]
IMPLIED_COLS = ["implied_prob_sum_open", "implied_prob_sum_close", "overround_change"]
CLV_COLS = ["b365_vs_market_h", "b365_vs_market_d", "b365_vs_market_a",
            "b365_vs_ps_close_h", "b365_vs_ps_close_d", "b365_vs_ps_close_a"]
FAMILIES = {"drift": DRIFT_COLS, "spread": SPREAD_COLS,
            "implied": IMPLIED_COLS, "clv": CLV_COLS}

ID_COLS = ["match_date", "home_team", "away_team", "home_goals", "away_goals",
           "full_time_result", "league", "season", "tier", "is_covid_season"]
LABEL_COLS = ["home_win"]
EXCLUDED_COLS = ["xmkt_div_abs", "xmkt_div_abs_z"]  # redundant with b365_vs_ps_close_*


# --------------------------------------------------------------------------------------
# Data access
# --------------------------------------------------------------------------------------
def get_engine():
    load_dotenv()
    user = os.environ["DB_USER"]
    pwd = os.environ["DB_PASSWORD"]
    host = os.environ["DB_HOST"]
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ["DB_NAME"]
    return create_engine(
        f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}",
        connect_args={"sslmode": "require"},
    )


def load_mart(engine) -> pd.DataFrame:
    schema = os.environ.get("DB_SCHEMA", "s_vladislavkivaev")
    df = pd.read_sql(f"SELECT * FROM {schema}.mart_matches_clean", engine)
    df["match_date"] = pd.to_datetime(df["match_date"])
    df = df.sort_values("match_date").reset_index(drop=True)
    log.info("Loaded mart: %s rows, %s cols", len(df), df.shape[1])
    return df


# --------------------------------------------------------------------------------------
# Baseline engine (load-bearing)
# --------------------------------------------------------------------------------------
def zscore_by_group(df, cols, group_keys=GROUP_KEYS, baseline_mask=None, suffix="_z"):
    """Per-group z-score. Guards: std == 0 / NaN / missing-group -> z = 0.0.
    baseline_mask (boolean aligned to df rows) restricts which rows define the baseline;
    None = all rows in each group (the 02_features default)."""
    group_keys = list(group_keys)
    cols = list(cols)
    out = df.reset_index(drop=True).copy()

    base = out if baseline_mask is None else out.loc[baseline_mask.values]
    agg = base.groupby(group_keys)[cols].agg(["mean", "std"])
    agg.columns = [f"{c}__{stat}" for c, stat in agg.columns]
    agg = agg.reset_index()

    merged = out.merge(agg, on=group_keys, how="left", sort=False)
    for col in cols:
        mean = merged[f"{col}__mean"]
        std = merged[f"{col}__std"]
        z = (merged[col] - mean) / std
        z = z.where(std.notna() & (std != 0), 0.0).fillna(0.0)
        out[f"{col}{suffix}"] = z.to_numpy()
    return out


# --------------------------------------------------------------------------------------
# Feature builders
# --------------------------------------------------------------------------------------
def resolve_present(df) -> list[str]:
    """Intersect canonical family columns with what the mart actually has; warn on gaps."""
    present = []
    for fam, cols in FAMILIES.items():
        have = [c for c in cols if c in df.columns]
        missing = [c for c in cols if c not in df.columns]
        if missing:
            log.warning("Family %s missing columns: %s", fam, missing)
        present.extend(have)
    return present


def build_reversal_flags(df) -> pd.DataFrame:
    """Direction disagreement between sharp (Pinnacle) and public (Bet365) book per outcome."""
    flags = []
    for o in ["h", "d", "a"]:
        col = f"dir_disagree_{o}"
        df[col] = ((np.sign(df[f"b365_drift_{o}"]) * np.sign(df[f"pinnacle_drift_{o}"])) < 0).astype(int)
        flags.append(col)
    df["dir_disagree_any"] = df[flags].max(axis=1)
    return df


def build_steam(df) -> pd.DataFrame:
    """Concerted same-direction move across the two books; collapse to the strongest outcome."""
    signed = []
    for o in ["h", "d", "a"]:
        b, p = df[f"b365_drift_{o}"], df[f"pinnacle_drift_{o}"]
        same_dir = (np.sign(b) * np.sign(p)) > 0
        df[f"steam_{o}"] = np.where(same_dir, (b + p) / 2.0, 0.0)
        signed.append(f"steam_{o}")
    steam_abs = df[signed].abs()
    pos = steam_abs.to_numpy().argmax(axis=1)
    df["steam_abs"] = steam_abs.to_numpy()[np.arange(len(df)), pos]
    df["steam_signed"] = df[signed].to_numpy()[np.arange(len(df)), pos]
    df["steam_outcome"] = pd.Series(["h", "d", "a"])[pos].to_numpy()
    df.loc[df["steam_abs"] == 0, "steam_outcome"] = None
    return df


def build_cross_market_divergence(df) -> pd.DataFrame:
    """Collapse b365-vs-pinnacle closing gap to magnitude/signed/outcome.
    Magnitude is EXCLUDED from the model set (redundant); signed/outcome kept descriptive."""
    ps_cols = ["b365_vs_ps_close_h", "b365_vs_ps_close_d", "b365_vs_ps_close_a"]
    ps_abs = df[ps_cols].abs()
    pos = ps_abs.to_numpy().argmax(axis=1)
    df["xmkt_div_abs"] = ps_abs.to_numpy()[np.arange(len(df)), pos]
    df["xmkt_div_signed"] = df[ps_cols].to_numpy()[np.arange(len(df)), pos]
    df["xmkt_div_outcome"] = pd.Series(["h", "d", "a"])[pos].to_numpy()
    df.loc[df["xmkt_div_abs"] == 0, "xmkt_div_outcome"] = None
    return df


def build_rolling(df) -> pd.DataFrame:
    """Per-league-season trailing draw-rate and drift magnitude, current match excluded (shift1).
    Leakage-safe fallback: expanding mean, then global mean for the first fixture of a season."""
    df = df.sort_values(["league", "season", "match_date"]).reset_index(drop=True)
    df["is_draw"] = (df["full_time_result"] == "D").astype(int)
    df["drift_mag"] = df[["b365_drift_h", "b365_drift_d", "b365_drift_a"]].abs().mean(axis=1)

    g = df.groupby(["league", "season"])
    for src, dst in [("is_draw", "roll_draw_rate"), ("drift_mag", "roll_drift_mag")]:
        df[dst] = g[src].transform(
            lambda s: s.shift(1).rolling(ROLL_WINDOW, min_periods=ROLL_MIN_PERIODS).mean())
        df[dst] = df[dst].fillna(g[src].transform(lambda s: s.shift(1).expanding().mean()))
        df[dst] = df[dst].fillna(df[dst].mean())
    return df


# --------------------------------------------------------------------------------------
# Roles, dictionary, persistence
# --------------------------------------------------------------------------------------
def assemble_roles(df, present):
    """Build the role map and the two model sets, derived from roles (never hardcoded)."""
    model_natural = present + ["steam_abs", "roll_draw_rate", "roll_drift_mag"]
    model_z = [f"{c}_z" for c in present] + ["steam_abs_z", "roll_draw_rate_z", "roll_drift_mag_z"]
    model_both = ["dir_disagree_h", "dir_disagree_d", "dir_disagree_a",
                  "margin_tightened", "pinnacle_missing"]

    # scale-free booleans must be clean ints
    for c in model_both:
        df[c] = df[c].fillna(0).astype(int)

    roles = {}
    for role, cols in [("id", ID_COLS), ("model_natural", model_natural), ("model_z", model_z),
                       ("model_both", model_both), ("label", LABEL_COLS), ("excluded", EXCLUDED_COLS)]:
        for c in cols:
            roles[c] = role
    for c in df.columns:
        roles.setdefault(c, "descriptive")

    universal_set = model_natural + model_both     # H2
    tier_aware_set = model_z + model_both          # H3

    leak = (set(universal_set) | set(tier_aware_set)) & (set(LABEL_COLS) | set(ID_COLS))
    if leak:
        raise AssertionError(f"LEAKAGE: id/label column in a model set -> {leak}")

    log.info("Model sets — universal(H2): %d  tier_aware(H3): %d  model_both: %d",
             len(universal_set), len(tier_aware_set), len(model_both))
    return df, roles, model_natural, model_z, model_both, universal_set, tier_aware_set


def _classify(col, model_both):
    is_z = col.endswith("_z")
    base = col[:-2] if is_z else col
    rep = "boolean" if col in model_both else ("z" if is_z else "natural")
    if "drift" in base:                                          fam, tail = "drift", "two_tailed"
    elif "spread_change" in base or base == "max_spread_change": fam, tail = "spread", "two_tailed"
    elif "spread" in base:                                       fam, tail = "spread", "upper"
    elif base.startswith("implied_prob") or base == "overround_change":
                                                                 fam, tail = "implied_prob_imbalance", "two_tailed"
    elif base.startswith("b365_vs_market"):                      fam, tail = "clv_crossbook", "upper"
    elif base.startswith("b365_vs_ps"):                          fam, tail = "clv_crossbook", "two_tailed"
    elif base.startswith("dir_disagree"):                        fam, tail = "reversal", "n/a"
    elif base.startswith("steam"):                               fam, tail = "steam", "upper"
    elif base.startswith("roll_draw"):                           fam, tail = "rolling_temporal", "two_tailed"
    elif base.startswith("roll"):                                fam, tail = "drift", "two_tailed"
    elif base == "margin_tightened":                             fam, tail = "margin", "n/a"
    elif base == "pinnacle_missing":                             fam, tail = "coverage", "n/a"
    else:                                                        fam, tail = "other", "n/a"
    return base, fam, rep, tail


def _impute_plan(base, rep):
    if rep != "natural":
        return "none (boolean; z-guard zeros NaN)"
    if base.startswith("pinnacle") or base.startswith("b365_vs_ps"):
        return "per-league-season median + pinnacle_missing flag (structural 25/26 gap)"
    return "per-league-season median"


def build_dictionary(universal_set, tier_aware_set, model_both):
    model_cols = list(dict.fromkeys(universal_set + tier_aware_set))
    rows = []
    for col in model_cols:
        base, fam, rep, tail = _classify(col, model_both)
        rows.append({"column": col, "family": fam, "representation": rep, "tail_shape": tail,
                     "in_universal_H2": col in universal_set, "in_tier_aware_H3": col in tier_aware_set,
                     "imputation": _impute_plan(base, rep)})
    return pd.DataFrame(rows).sort_values(["family", "representation", "column"]).reset_index(drop=True)


def persist(df, roles, sets, feat_dict, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    universal_set, tier_aware_set, model_both = sets
    df.to_parquet(out_dir / "features.parquet", index=False)
    with open(out_dir / "feature_roles.json", "w") as f:
        json.dump({
            "roles": roles,
            "universal_set_H2": universal_set,
            "tier_aware_set_H3": tier_aware_set,
            "model_both": model_both,
            "label": LABEL_COLS,
            "excluded": EXCLUDED_COLS,
            "notes": {
                "covid": "z-scored per league-season; 19/20 is its own baseline group, no masking",
                "pinnacle_gap": "structural ~50% missing in 25/26 (football-data upload lag, ~Jan 2026) "
                                "plus thin early mid-tier coverage; flagged via pinnacle_missing",
                "imputation_runs_in": "03_modeling",
            },
        }, f, indent=2)
    feat_dict.to_csv(out_dir / "feature_dictionary.csv", index=False)
    log.info("Wrote features.parquet %s, feature_roles.json, feature_dictionary.csv (%d features) -> %s",
             df.shape, len(feat_dict), out_dir)


# --------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------
def build_features(df) -> tuple:
    present = resolve_present(df)
    df = build_reversal_flags(df)
    df = build_steam(df)
    df = build_cross_market_divergence(df)
    df = build_rolling(df)

    # z-score families + steam magnitude + xmkt magnitude (xmkt_div_abs_z later excluded) + rolling
    to_z = present + ["steam_abs", "xmkt_div_abs", "roll_draw_rate", "roll_drift_mag"]
    df = zscore_by_group(df, cols=to_z)

    # coverage flag — BEFORE any imputation
    df["pinnacle_missing"] = df["pinnacle_drift_h"].isna().astype(int)

    df, roles, mn, mz, mb, uni, tier = assemble_roles(df, present)
    feat_dict = build_dictionary(uni, tier, mb)
    return df, roles, (uni, tier, mb), feat_dict


def main():
    ap = argparse.ArgumentParser(description="Build the betting-integrity feature matrix.")
    ap.add_argument("--output-dir", default="data/processed", type=Path,
                    help="where to write features.parquet + docs (default: data/processed)")
    args = ap.parse_args()

    engine = get_engine()
    df = load_mart(engine)
    if len(df) != 8915:
        log.warning("Expected 8,915 rows, got %s", len(df))

    df, roles, sets, feat_dict = build_features(df)
    persist(df, roles, sets, feat_dict, args.output_dir)
    log.info("Done.")


if __name__ == "__main__":
    main()
