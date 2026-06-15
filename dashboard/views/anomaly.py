import streamlit as st

from lib import charts
from lib import components as C
from lib import theme as T
from lib.data import FLAG_RATE_UNIVERSAL
from lib.data import FLAG_RATE_TIER


def render(df):
    C.page_header(
        "Anomaly Detection",
        "Teaching a model to flag the odd ones",
        "Isolation Forest on 35 odds features · explained with SHAP.",
    )

    top_l, top_r = st.columns([1.4, 1])
    with top_l:
        with C.card("Anomaly score distribution — flag threshold"):
            thr = df["score_raw"].quantile(0.95)
            st.plotly_chart(charts.score_distribution(df["score_raw"], thr),
                            width="stretch", config={"displayModeBar": False})
            C.note("Most matches look normal (blue). The long red tail — the top ~5% "
                   "by score — is what gets flagged for a closer look.")
    with top_r:
        with C.card("SHAP — what drives a flag"):
            st.plotly_chart(charts.shap_drivers(), width="stretch",
                            config={"displayModeBar": False})
            C.note("Spread and drift together account for **~two-thirds** of the "
                   "model's decisions — the same two signals the EDA flagged for "
                   "Greece.")

    st.write("")
    mid_l, mid_r = st.columns([1.4, 1])
    with mid_l:
        with C.card("What makes a match unusual — odds drift, open → close"):
            st.markdown(
                "<div class='note'>Aris vs PAOK · Greece · 2025-03-02 · "
                "the away price drifted hard late</div>", unsafe_allow_html=True)
            st.plotly_chart(charts.drift_example(), width="stretch",
                            config={"displayModeBar": False})
            C.note("The away odds jumped 2.85 → 3.60 — a big, late move. On its own "
                   "that's nothing; combined with a wide book disagreement, the model "
                   "treats it as a red flag worth a human look.")
    with mid_r:
        with C.card("The signals the model watches"):
            st.markdown(
                "**Drift** — how far open → close odds moved  \n"
                "**Spread** — disagreement between bookmakers  \n"
                "**Implied imbalance** — lopsided home/draw/away pricing  \n"
                "**Public–sharp gap** — Bet365 vs Pinnacle divergence  \n"
                "**Reversal proxy** — price moves then snaps back")
            st.markdown(f"<div style='color:{T.BLUE_LIGHT};font-style:italic;"
                        f"margin-top:8px'>35 features in 5 families — no team or "
                        f"player data, by design.</div>", unsafe_allow_html=True)

    st.write("")
    with C.card("Flag rate by league — league-aware model"):
        st.plotly_chart(charts.flag_rate_by_league(FLAG_RATE_UNIVERSAL),
                        width="stretch", config={"displayModeBar": False})
        C.note("Greece is flagged most — spread &amp; drift drive ~two-thirds of its "
               "score. Turkey, the priciest book, is the *least*-flagged: expensive "
               "but orderly. Unusual is not an accusation.")

    st.write("")
    with C.card("Two models, one A/B test"):
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown(
                "**Universal** — one pooled model on natural-unit features. Asks: *is "
                "this match unusual compared to all 8,915?* Concentrates flags in "
                "Greece (10.6%) and barely touches Turkey (2.0%).")
        with cc2:
            st.markdown(
                "**League-aware** — the same model on per-league-season z-scored "
                "features. Asks: *is this match unusual **for its own league**?* Pulls "
                "Greece to 5.5% and nudges Turkey to 4.3% — every league near "
                "baseline.")
        st.markdown(
            "<div class='note'>They agree on 328 matches but each catch 118 the other "
            "misses — different lenses on the same data, which is exactly the point "
            "of the comparison.</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown(
        f"<div class='card' style='border-color:{T.AMBER}'>"
        f"<h3 style='color:{T.AMBER}'>⚖️ No ground-truth labels exist.</h3>"
        f"<div class='muted'>So this reports <b>differential flagging rates</b> — "
        f"never false-positive rates or claims of wrongdoing. A flag means a match's "
        f"odds behaved unlike its league; it is a screening signal, not a verdict. "
        f"The honest output is \u201chere is where a human should look\u201d — the "
        f"same way real integrity monitors operate. <b>Unusual \u2260 rigged.</b>"
        f"</div></div>", unsafe_allow_html=True)
