import streamlit as st

from lib import charts
from lib import components as C
from lib import theme as T
from lib.data import OVERROUND_B365


def render(df):
    C.page_header(
        "Betting 101",
        "How odds work &amp; how books make money",
        "World Cup 2026 opener example — Mexico vs South Africa (Bet365).",
    )

    left, right = st.columns([1.25, 1])
    with left:
        with C.card("Reading the odds"):
            st.markdown(
                "Bookmakers post a number for each outcome. **Decimal** odds are what "
                "this dataset uses; **US** odds are the American style; the **implied "
                "probability** is just `1 ÷ decimal odds`.")
            st.table({
                "Outcome": ["🇲🇽 Mexico (home)", "🤝 Draw", "🇿🇦 South Africa (away)"],
                "Decimal": ["1.48", "4.33", "6.50"],
                "US": ["−208", "+333", "+550"],
                "Implied %": ["67.6%", "23.1%", "15.4%"],
            })
            st.markdown(
                "<div class='note'>Decimal 1.48 = stake × 1.48 back. "
                "US −208 = bet 208 to win 100, US +333 = profit 333 on a bet 100. Implied % = 1 ÷ decimal odds.</div>",
                unsafe_allow_html=True)
    with right:
        with C.card("The catch: it sums to 106%"):
            st.markdown(
                f"<div style='font-size:3.4rem;font-weight:800;color:{T.BLUE};"
                f"line-height:1'>106%</div>"
                f"<div class='note' style='margin:4px 0 14px'>67.6 + 23.1 + 15.4</div>",
                unsafe_allow_html=True)
            st.markdown(
                "A fair coin's outcomes sum to 100%. These sum to **106%**. That extra "
                "**6%** is the bookmaker's fee — the *overround* (or 'vig'). It's baked "
                "into every price, so the house profits whoever wins.\n\n"
                "Strip it out and the market's true read is roughly "
                "**Mexico 63.7% · Draw 21.8% · South Africa 14.5%**.")

    C.soft_divider()

    with C.card("Real overround in this data — median fee by league (Bet 365 closing odds)"):
        st.markdown(
            "<div class='note'>Across 8,915 league matches the fee sits in the same "
            "5–7% range as that World Cup game. Turkey is priciest market, the two "
            "elite leagues are the cheapest.</div>", unsafe_allow_html=True)
        st.plotly_chart(charts.bar_overround(OVERROUND_B365), width="stretch",
                        config={"displayModeBar": False})

    st.write("")
    g1, g2 = st.columns(2)
    with g1:
        with C.card("Mini-glossary"):
            st.markdown(
                "**Favourite / longshot** — the low-odds vs high-odds outcome.  \n"
                "**Spread** — 'max − avg' odds across books: how much they disagree.  \n"
                "**Opening vs closing odds** — first price posted vs the final one.  \n"
                "**Drift** — how far a price moved from open to close."
                )
    with g2:
        with C.card("Why the fee matters here"):
            st.markdown(
                "A confident bookmaker posts a tighter margin. An uncertain or thin "
                "market posts a wider one. So the fee and how much books disagree "
                "on it becomes a measurable signal for the efficiency and anomaly "
                "work in the next sections.")
