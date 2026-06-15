import streamlit as st

from lib import assets
from lib import components as C
from lib import theme as T
from lib.data import LEAGUE_NAME, LEAGUE_FULL, LEAGUE_COUNTRY, TIER


def render(df):
    C.page_header(
        "Overview",
        "Football Betting Market Efficiency Monitor",
        "Can you bit bookmakers? A market-efficiency study with anomaly screening — seven seasons of football odds.",
    )

    c1, c2, c3 = st.columns(3)
    C.kpi(c1, "8,915", "matches analysed")
    C.kpi(c2, "4", "leagues · Bundesliga · EPL · Turkey · Greece")
    C.kpi(c3, "7", "seasons · 2019/20 – 2025/26")

    st.write("")
    st.markdown(
        "**Source:** football-data.co.uk — real Bet365 &amp; Pinnacle odds "
        "(opening + closing).", unsafe_allow_html=True)

    C.soft_divider()

    st.markdown('<div class="eyebrow">Leagues analysed</div>', unsafe_allow_html=True)
    counts = df["league"].value_counts().to_dict()
    cols = st.columns(4)
    for col, code in zip(cols, ["D1", "E0", "T1", "G1"]):
        tier_cls = "tier-elite" if TIER[code] == "elite" else "tier-mid"
        tier_lbl = "ELITE" if TIER[code] == "elite" else "MID-TIER"
        n = counts.get(code, 0)
        with col:
            with C.card():
                st.markdown(
                    f'<div class="league-card">'
                    f'<div class="emblem">{assets.league_emblem_html(code, 40)}</div>'
                    f'<div class="lname">{LEAGUE_NAME[code]}</div>'
                    f'<div class="lfull">{LEAGUE_FULL[code]} · {LEAGUE_COUNTRY[code]}</div>'
                    f'<div class="lmeta">{n:,} matches</div>'
                    f'<span class="tier-tag {tier_cls}">{tier_lbl}</span>'
                    f'</div>', unsafe_allow_html=True)

    C.soft_divider()

    st.markdown('<div class="eyebrow">Pipeline</div>', unsafe_allow_html=True)

    PIPELINE = [
        ("python", "Python", "Extract data + EDA"),
        ("postgresql", "PostgreSQL", "Warehouse"),
        ("dbt", "dbt", "Transformation + tests"),
        ("python", "Python", "Modeling"),
        ("streamlit", "Streamlit", "Presentation"),
    ]
    row = ['<div class="pipeline-row">']
    for i, (key, label, sub) in enumerate(PIPELINE):
        if i > 0:
            row.append('<span class="pl-arrow">›</span>')
        row.append(f'<div class="pl-step">{assets.tool_emblem_html(key, 32)}'
                    f'<div class="pl-text"><div class="pl-label">{label}</div>'
                    f'<div class="pl-sub">{sub}</div></div></div>')
    row.append('</div>')

    st.markdown("".join(row), unsafe_allow_html=True)

    st.write("")

    st.markdown(
        "**Methods:** Data Extract → EDA → 35 engineered features → Isolation Forest → "
        "SHAP → Hypothesis testing")

    C.soft_divider()

    left, right = st.columns([1.15, 1])
    with left:
        with st.expander("What this is — and what it is not"):
            st.markdown(
                "This project studies how an efficient market with a built-in fee "
                "behaves, and screens for matches whose odds behave **unlike their "
                "league**. It is framed as a *market-efficiency study with anomaly "
                "screening*, not a match-fixing detector.\n\n"
                "There are no ground-truth fixing labels, so the honest output is a "
                "**differential flagging rate** — never a false-positive rate or an "
                "accusation. The same way professional integrity monitors operate: "
                "*unusual ≠ rigged.*")
    with right:
        with st.expander("The four hypotheses"):
            
            st.markdown(
                "**H1** · Mid-tier leagues are priced less efficiently than elite leagues  \n"
                "**H2** · Draws are systematically mispriced  \n"
                "**H3** · Anomalous matches can be identified from odds features  \n"
                "**H4** · Bookmaker disagreement concentrates towards the end of the season")

    if df["_synthetic"].iloc[0]:
        st.write("")
        st.info(
            "Running on a **calibrated demo dataset** (real files not detected). "
            "Aggregate figures — flag rates, overround, spreads, drift — match the "
            "project's real results. Drop `scored_matches.parquet` and "
            "`features.parquet` into `data/processed/` to switch to live data.",
            icon="🧪")
