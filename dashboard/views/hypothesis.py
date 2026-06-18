import streamlit as st

from lib import charts
from lib import components as C
from lib import theme as T
from lib.data import OVERROUND_B365

ROWS = [
    ("H1", "Smaller leagues priced less efficiently than big ones",
     "Pre-registered", "Not supported", "red"),
    ("H2", "Draws mispriced",
     "EDA-informed", "Mixed", "amber"),
    ("H3", "Anomalies detectable, league-aware tuning rebalances flags",
     "Pre-registered", "Supported", "green"),
    ("H4", "Bookmaker disagreement spikes at season's end",
     "Pre-registered", "Rejected", "red"),
]


def render(df):
    C.page_header(
        "Hypothesis Testing",
        "Four predictions, written down first",
    )

    with C.card():
        head = st.columns([0.5, 4.2, 1.6, 1.6])
        for col, txt in zip(head, ["#", "What we predicted", "Type", "Result"]):
            col.markdown(f"<div class='note' style='font-size:0.8rem;letter-spacing:"
                         f"0.1em;text-transform:uppercase'>{txt}</div>",
                         unsafe_allow_html=True)
        st.markdown("<hr class='soft' style='margin:10px 0'>", unsafe_allow_html=True)
        for h, pred, typ, verdict, kind in ROWS:
            c0, c1, c2, c3 = st.columns([0.5, 4.2, 1.6, 1.6])
            c0.markdown(f"**{h}**")
            c1.markdown(pred)
            c2.markdown(f"<span class='note'>{typ}</span>", unsafe_allow_html=True)
            c3.markdown(C.pill(verdict, kind), unsafe_allow_html=True)
            st.write("")

    st.write("")
    st.markdown(
        "<div class='note'>Click a hypothesis below to see why</div>", unsafe_allow_html=True
        )
    st.write("")

    row1_l, row1_r = st.columns(2)
    with row1_l:
        with st.expander("H1 — Smaller leagues priced less efficiently than big ones",
                         expanded=False):
            st.plotly_chart(charts.bar_overround(OVERROUND_B365), width="stretch",
                            config={"displayModeBar": False})
            C.note("If H1 held, you'd expect a clean elite/mid-tier split: both "
                   "Bundesliga and EPL low, both Turkey and Greece high. Instead "
                   "**Turkey (6.8%) is the standalone outlier** and Greece (6.2%) "
                   "sits closer to the elite pair than to Turkey. The pattern is "
                   "league-specific, not tier-level — so H1 isn't supported as "
                   "originally framed.")
    with row1_r:
        with st.expander("H2 — Draws mispriced",
                         expanded=False):
            st.plotly_chart(charts.draw_mispricing(), width="stretch",
                            config={"displayModeBar": False})
            C.note("EPL's implied and realised draw rates are nearly identical "
                   "(23.8% vs 23.6%) — correctly priced, as predicted. Greece's "
                   "gap is the widest (25.7% → 27.2%, draws happen **more** than "
                   "the market expects). The direction matches H2, but with "
                   "only 7 league-seasons to test on, the gap isn't large "
                   "enough to call statistically significant for every league "
                   "— hence *mixed*, not a clean win.")

    row2_l, row2_r = st.columns(2)
    with row2_l:
        with st.expander("H3 — Anomalies detectable, league-aware tuning "
                         "rebalances flags", expanded=False):
            st.plotly_chart(charts.h3_winbar(), width="stretch",
                            config={"displayModeBar": False}, key="h3_expander_chart")
            C.note("The universal model over-flags Greece at 10.6% — more than "
                   "double the 5% target. Re-scoring matches against their own "
                   "league's history instead of the whole dataset pulls that "
                   "down to 5.5%, right at baseline. This is the cleanest result "
                   "of the four: the pre-registered threshold (cut the gap by "
                   "at least half) was met with room to spare.")
    with row2_r:
        with st.expander("H4 — Bookmaker disagreement spikes at season's end",
                         expanded=False):
            st.plotly_chart(charts.h4_seasonal_trend(), width="stretch",
                            config={"displayModeBar": False})
            C.note("Greece is consistently the noisiest market all season, but "
                   "its spread **peaks mid-season (Q3) and falls toward the "
                   "end (Q5)** — the opposite of what H4 predicted. The other "
                   "three leagues stay essentially flat throughout. Disagreement "
                   "doesn't spike at season's end anywhere in this data, so H4 "
                   "is rejected as framed.")

    C.soft_divider()
    with st.expander("Effect sizes & test details (the honest reading)"):
        st.markdown(
            "- **H1**: pooled KS is significant on 4/4 efficiency features (p ≈ 0), "
            "but within-tier pairs are also significant, so the tier framing fails. "
            "Overround ordering: T1 1.068 > G1 1.062 > D1 1.056 > E0 1.055.\n"
            "- **H2**: mean draw gaps are real (D1 +6.7%, G1 +6.0%, T1 +2.9%, "
            "EPL −0.8%) and EPL is confirmed correctly priced, but at n=7 "
            "league-seasons the Holm-corrected test falls short, so the threshold "
            "is not met. D1 alone is significant vs zero (p=0.020, |r|=0.71).\n"
            "- **H3**: the binding, pre-registered result (met in 03) is a ~48% "
            "flag-rate gap reduction (G1 0.106 to 0.055), clearing the half "
            "threshold. A separate, circularity-caveated check finds flagged "
            "matches separate strongly on spread (KS D=0.896, |r|=0.978), but "
            "that is internal consistency only.\n"
            "- **H4**: ANOVA is technically significant (an n-artefact, "
            "η²<0.01) but Kruskal-Wallis is not, and both effect sizes are "
            "negligible, so the hypothesis is rejected as framed.")
