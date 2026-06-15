# Football Betting Market Efficiency Analysis

A cross-league study of betting-market efficiency across European football, with anomaly screening as one analytical layer. Analyses **8,915 matches** across four leagues (Bundesliga, EPL, Turkey, Greece) over seven seasons (2019/20–2025/26) to measure how bookmaker pricing efficiency differs between elite and mid-tier markets — and demonstrates that anomaly-detection thresholds must be calibrated to each market's own baseline rather than applied universally.

**[Tableau Dashboard](#)** · **[Streamlit App](#)**

---

## The Problem

Betting markets are not equally efficient. Elite leagues (Bundesliga, EPL) have deep liquidity, tight bookmaker margins, and close agreement between bookmakers. Mid-tier leagues (Turkey, Greece) have wider margins, thinner liquidity, and more bookmaker disagreement — for entirely legitimate structural reasons unrelated to manipulation.

This creates a problem for any anomaly-detection system built on top of these markets. Professional integrity tools (Sportradar, Genius Sports) apply anomaly thresholds across leagues; a single universal threshold will:
- **miss real anomalies** in efficient elite markets (threshold too high for their tight baseline), and
- **over-flag structurally noisier mid-tier markets** (their normal behaviour looks anomalous against an elite benchmark).

This project first measures the efficiency differences directly, then shows that calibrating anomaly thresholds to each market's own baseline addresses the over-flagging problem — the same principle that governs segment-aware fraud detection in fintech.

**Framing discipline:** this is a *market-efficiency study with anomaly screening as one layer*, not a "match-fixing detector." No ground-truth labels for fixed matches exist, so the project reports **differential flagging rates** by tier/league — never "false positive rates." Flagged matches are statistically unusual for their market, not accusations of wrongdoing.

---

## Hypotheses

Four hypotheses were tested against **pre-committed success criteria** set before analysis, with **two-tier provenance labelling** (pre-registered vs EDA-informed vs exploratory) to prevent post-hoc storytelling. Formal tests: Kolmogorov–Smirnov, Mann–Whitney U, ANOVA. Throughout, "anomalous" means *statistically unusual for its market* — never "fixed." With no ground-truth labels, results are reported as **differential flagging rates**, not false-positive rates.

### H1 — Mid-tier leagues are priced less efficiently than elite leagues
- **Provenance:** pre-registered
- **Criterion:** efficiency metrics (overround, spread) differ significantly between tiers (KS / Mann–Whitney U, p < 0.05) and flagging concentrates in the mid tier.
- **Verdict: Not supported as a tier claim — reframed to a league-level effect.** Margin and spread *are* wider in the mid tier descriptively, but anomaly flagging does not split by tier: Greece (universal flag rate 0.106) and Turkey (0.020) sit at opposite extremes — Turkey is the most expensive market by margin yet the *fewest* flagged anomalies. Within-tier league pairs also differ significantly. Efficiency varies **league-by-league, not tier-by-tier**; the signal is concentrated in Greece.

### H2 — Draws are systematically mispriced
- **Provenance:** EDA-informed (confirmatory)
- **Criterion:** realised draw rate departs from implied, consistently across leagues.
- **Verdict: Partially supported — mispricing is real but league-specific, not systematic.** Greece underprices draws by **+6.1%** (realised 27.2% vs implied 25.7%); EPL is correctly priced (**−0.8%**). Effect sizes are substantive, but the season-level test is **underpowered (n = 7)**, so formal significance is not reached at threshold. The honest refinement: draws are mispriced *in specific leagues*, not across the board. (Extreme single-season spikes appear in Greece 22/23 and Turkey 25/26, +4.3–4.4pp.)

### H3 — Anomalous matches can be identified from odds features
- **Provenance:** pre-registered
- **Criterion:** an unsupervised model separates unusual matches, and per-league calibration balances flagging across leagues.
- **Verdict: Supported.** A pooled (universal) Isolation Forest separates unusual matches on odds features; a per-league-calibrated (tier-aware) model rebalances flagging so each league converges to ~5%, versus the universal model's 2.0%–10.6% spread. The two models flag **different matches** (328 shared, 118 universal-only, 118 tier-only) — calibration changes *who* gets caught, not just how many. SHAP attributes the flags chiefly to spread (~0.49) and drift (~0.34). *Caveat:* "identifiable" means statistically separable, **not** proven manipulation.

### H4 — Bookmaker disagreement concentrates toward the end of the season
- **Provenance:** a priori directional claim → rejected → documented as an exploratory reframe
- **Criterion:** spread/disagreement rises across season quintiles, peaking in the final quarter.
- **Verdict: Disproven.** The opposite holds — disagreement is **lowest in the final quarter** across all four leagues, and Greece's spreads peak mid-season (Q3). Markets appear to *stabilise* as the season closes.

### The thread across all four: Greece
Each hypothesis independently points back to Greece — widest spreads and drift (Pinnacle away drift 0.300, the single highest value in the dataset, 71% wider than EPL), highest anomaly flag rate (10.6%), largest draw-pricing gap (+6.1%), and SHAP attributing ~2/3 of its anomaly score to spread (~0.49) and drift (~0.34). No single finding proves wrongdoing; the **consistency across four independent analytical angles** is the finding.

---

## The Modeling Experiment (H2 vs H3)

The core experiment is an A/B between two Isolation Forests on the same 35 features:

| League | Universal model (pooled, raw features) | Tier-aware model (per-league z-scores) |
|---|---|---|
| Bundesliga (elite) | 0.049 | 0.054 |
| EPL (elite) | 0.044 | 0.051 |
| **Greece (mid)** | **0.106** | 0.055 |
| Turkey (mid) | 0.020 | 0.043 |
| *Global target* | *0.05* | *0.05* |

The universal model over-flags Greece (10.6%) and under-flags Turkey (2.0%) — mistaking structurally different markets for anomalies. Calibrating each league against its own baseline pulls every league to ~5%. **This is the project's headline result and the direct analogue of segment-aware fraud detection in fintech.**

Keeping the two feature representations separate is essential: the universal model trains on *natural-unit* features, the tier-aware model on *per-league-season z-scored* features. If both used z-scores, the universal model would be implicitly tier-aware and the over-flagging failure mode (the whole point of the comparison) would vanish.

---

## Data

| Source | Leagues | Seasons | Matches |
|---|---|---|---|
| [football-data.co.uk](https://www.football-data.co.uk) | Bundesliga (D1), EPL (E0), Turkey (T1), Greece (G1) | 2019/20 → 2025/26 | 8,915 |

**Why these leagues**: Bundesliga and EPL are the reference elite markets (well-monitored, high liquidity, deep bookmaker coverage). Turkey and Greece are documented mid-tier integrity-risk markets — Greece in particular was at the centre of one of European football's largest match-fixing scandals (2011), making it a well-cited case study in academic integrity research. All four are in the Main Leagues section of football-data.co.uk with identical CSV format — no scraping required.

**Why Greece over Russia**: Russia was initially considered but dropped — its CSVs lacked the full per-bookmaker odds columns needed for spread and drift features. Greece has complete column parity with the other three leagues across all 7 seasons.

**Why 7 seasons (2019/20–2025/26)**: A column-availability audit confirmed opening, closing, and Pinnacle odds (both opening and closing) are present for **all four leagues across all seven seasons, with no gaps**. The 2019/20 COVID season is flagged separately (`is_covid_season`) and z-scored against itself; it is carried as a modeling lever and as a known-disruption reference case.

**Data quality**: Two confirmed data errors were removed (Olympiakos vs Larisa 2021 with `MaxCA=100.0`; Volos NFC vs Olympiakos 22/23 with an impossible B365 drift). No winsorisation was applied — legitimate extreme values are preserved for the anomaly detector. A structural Pinnacle gap in 25/26 (~50% missing, heaviest in mid-tier, from a football-data.co.uk upload lag) is median-imputed but flagged via `pinnacle_missing` so the model does not over-trust imputed sharp-money signal.

---

## Features (35 model features, 5 signal families)

Two genuine time points per match (open and close) make line-movement a real measurement, not a proxy — though continuous intra-day movement is not observable. Every signal is kept in **two representations**: natural-unit (for the universal model) and per-league-season z-scored (for the tier-aware model).

| Family | What it measures | In market terms |
|---|---|---|
| **Drift** | Closing odds minus opening odds (B365 and Pinnacle) | How far the line moved before kickoff — a large one-way move suggests informed money |
| **Spread** | Max minus Avg closing odds per outcome | How much bookmakers disagree — wide spread = thin/inefficient market (widest in Greece) |
| **Implied-probability imbalance** | Overround (sum of 1/odds − 1) vs league baseline | The bookmaker's built-in margin; an unusually small margin signals a soft market |
| **Public–sharp divergence** | Bet365 (biggest retail book, public money) vs Pinnacle (sharpest book, professional money) at close | A large gap means public and informed money disagree on the outcome |
| **Reversal proxy** | Direction-disagreement between Bet365 and Pinnacle | A sign of conflicting signals — the weakest, indirect family (true reversals need intra-day data) |

Plus scale-free booleans carried into both model sets (`dir_disagree_h/d/a`, `margin_tightened`, `pinnacle_missing`) and rolling temporal features (`roll_draw_rate_z`, `roll_drift_mag_z`, 38-match window, season-boundary reset, leakage guard). `xmkt_div_abs` was excluded with cause (redundant with the public–sharp divergence features).

> *Naming note: in code and dbt this family uses the column prefix `b365_vs_ps_close_*` (originally labelled "CLV / cross-book"). "Public–sharp divergence" is the accurate term — it measures the gap between the retail book (Bet365) and the sharp book (Pinnacle) at close, not textbook closing-line value, which is a time-based open-to-close measure captured here by the drift family instead.*

---

## Pipeline

Built **pandas-first** (a complete, presentable analysis on its own), with the PostgreSQL + dbt warehouse layer over the top as an engineering showcase. At ~9,000 rows the cloud stack is a deliberate skills demonstration, not an analytical necessity.

```
football-data.co.uk CSVs
   ↓  Python (requests, pandas)          download + clean + merge → master_enriched.csv (8,915 rows)
   ↓  PostgreSQL on AWS RDS              loaded via SQLAlchemy (schema s_vladislavkivaev)
   ↓  dbt Core (dbt/)                    stg_matches → int_matches_with_features → mart_matches_clean
   ↓  Python (scikit-learn, SHAP)        features → Isolation Forest (universal + tier-aware) → scored_matches
   ↓  scipy                              KS / Mann–Whitney U / ANOVA hypothesis tests
   ↓  Tableau + Streamlit                dashboards + interactive risk-scorer
```

**dbt models** (all build into schema `s_vladislavkivaev`, 9 data-quality tests passing, with a saved lineage DAG):
- `stg_matches` (view) — renames mixed-case columns to snake_case, casts types, adds `is_covid_season`
- `int_matches_with_features` (view) — adds `b365_vs_ps_close_h/d/a`, `margin_tightened`, `overround_change`, `home_shortened`, `home_win`
- `mart_matches_clean` (table) — the notebook's read target

---

## Tech Stack

| Layer | Tool |
|---|---|
| Extraction & analysis | Python 3.13, pandas, NumPy |
| Warehouse | PostgreSQL on AWS RDS (SQLAlchemy loader) |
| Transformation | dbt Core (`dbt-postgres`) |
| Modeling | scikit-learn (Isolation Forest), SHAP |
| Statistics | scipy (KS, Mann–Whitney U, ANOVA) |
| Visualisation | Tableau (primary), Streamlit (interactive app) |
| Version control | Git + GitHub |

---

## Repo Structure

```
football-betting-integrity-monitor/
├── dashboard/                   # Tableau workbook + Streamlit risk-scorer app
├── data/
│   ├── raw/                     # Downloaded CSVs (gitignored)
│   └── processed/               # master_enriched.csv, features.parquet, scored_matches.parquet
|   └── figures/                 # Saved charts images
├── dbt/                         # dbt Core project (staging → intermediate → marts)
├── notebooks/
│   ├── 01_eda.ipynb       # Cleaning, merge, EDA (market structure, calibration, drift)
│   ├── 02_features.ipynb        # Feature engineering — 5 families, 2 representations
│   ├── 03_modeling.ipynb        # Isolation Forest (universal vs tier-aware) + SHAP
│   └── 04_hypothesis_tests.ipynb # KS / Mann–Whitney U / ANOVA against pre-committed criteria
|   └── 05_exploratory_flags.ipynb # Anomaly analysis
├── scripts/
│   ├── load_to_rds.py           # Loads master_enriched.csv into PostgreSQL on RDS
│   └── feature_engineering.py   # Reproducible regenerator of the feature matrix
|   └── download_data.py         # Download data from the source
├── requirements.txt
└── README.md
```

---

## Status — Complete

| Stage | State |
|---|---|
| Data collection, cleaning, EDA | ✅ Done (8,915 rows, 13 charts, 16 findings) |
| PostgreSQL + dbt pipeline | ✅ Done (3 models, 9 tests passing, lineage DAG) |
| Feature engineering | ✅ Done (35 features, 2 representations) |
| Modeling (Isolation Forest + SHAP) | ✅ Done (universal vs tier-aware A/B) |
| Hypothesis tests (KS / MWU / ANOVA) | ✅ Done (all four tested vs pre-committed criteria) |
| Tableau dashboards | ✅ Done |
| Streamlit app | ✅ Done |
| Final presentation & write-up | ✅ Done |

---

## Limitations

- **No ground-truth labels**: no confirmed list of fixed matches exists. Flagged matches are statistically unusual, not proven corrupt. The project reports *differential flagging rates*, not false-positive rates — the hypothesis verdicts are inferences about market structure, not measurements of manipulation.
- **Tier and region are confounded**: the elite tier (Germany, England) and mid tier (Turkey, Greece) also differ by region and wealth. With two leagues per tier, a "tier" effect cannot be cleanly separated from a country effect — which is part of why H1 was reframed to a Greece-specific finding.
- **Two time points, not continuous**: opening and closing odds are available, so open-to-close drift is real, but intra-day line movement (and true mid-window reversals) cannot be observed.
- **Scandal cases predate the data**: the Greek (2011) and Turkish scandals motivate league selection but fall before the 2019/20 window — they justify these leagues as higher-risk markets, but specific scandal matches cannot be validated against.
- **No betting volume**: volume spikes, a strong integrity signal, are not in the dataset.
- **League imbalance**: the Greek Super League fields ~14 teams (~182 matches/season) vs ~306–380 for the others, making Greece the thinnest per-league sample.
- **Public-output caution**: match-level flags are presented as statistical anomalies, explicitly **not** accusations of wrongdoing.

---

## Relevance to Financial Crime & Fintech

The methodology maps directly onto transaction-fraud / AML detection:

| This project | Fintech equivalent |
|---|---|
| Per-league baseline | Customer-segment / cohort baseline |
| Odds anomaly features | Transaction-pattern features |
| Tier-aware Isolation Forest | Segment-aware fraud model |
| Anomaly score per match | Risk score per transaction |
| Differential flagging rate by league | Flagging rate by customer segment |

The central lesson — that anomaly thresholds must be calibrated to each population's own baseline rather than applied globally — is exactly the problem a fraud or risk team faces when a naive global threshold over-flags whichever customer segment is structurally noisier.

---

## Author

**Vladislav Kivaev** · Spiced Academy Data Analytics Bootcamp · Berlin, 2026
