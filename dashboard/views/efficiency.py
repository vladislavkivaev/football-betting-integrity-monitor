import streamlit as st

from lib import components as C
from lib import eff_charts as EC
from lib import efficiency_calcs as calc
from lib import theme as T
from lib.data import SEASONS


def render(df):
    C.page_header(
        "Market Efficiency",
        "Is the betting market any good?",
        "8,915 matches · what the odds get right, and where they bend.",
    )

    c1, c2, c3, c4 = st.columns(4)
    C.kpi(c1, "r = 0.99", "predicted vs actual")
    C.kpi(c2, "53.1%", "favourites win")
    C.kpi(c3, "64%", "Greece away spread vs EPL")
    C.kpi(c4, "2x", "Bet365 vs Pinnacle margin")
    C.note("Headline figures above are fixed reference points (closing B365 odds, "
           "all matches). The charts below respond to the filters.")

    C.soft_divider()

    # ------------------------------- FILTERS -------------------------------- #
    with C.card("Filters"):
        f1, f2, f3, f4 = st.columns(4)
        group_by = f1.selectbox("Split", ["Total", "By tier", "By league"], index=0)
        timing = f2.selectbox("Odds timing", ["Closing", "Opening"], index=0)
        bookmaker = f3.selectbox("Bookmaker", ["Bet365", "Pinnacle"], index=0)
        season = f4.selectbox("Season", ["All seasons"] + SEASONS, index=0)

    group_key = {"Total": "total", "By tier": "tier", "By league": "league"}[group_by]
    timing_key = "close" if timing == "Closing" else "open"
    bookmaker_key = "b365" if bookmaker == "Bet365" else "pinnacle"
    season_key = "total" if season == "All seasons" else season

    f = calc.filter_season(df, season_key)
    long_df = calc.build_long(f, bookmaker_key, timing_key)
    groups = list(calc.group_slices(f, long_df, group_key))
    n_total = len(f)

    if n_total == 0:
        st.warning("No matches for this selection.")
        return

    C.note(f"Showing <b>{n_total:,}</b> matches · {bookmaker} {timing.lower()} odds · "
           f"{season} · split: {group_by.lower()}")

    st.write("")

    # --------------------------- 1. RESULT DISTRIBUTION ---------------------- #
    with C.card("Results — actual vs predicted (Home / Draw / Away)"):
        results = {label: calc.result_distribution(df_sub, long_sub)
                   for label, color, df_sub, long_sub in groups}
        st.plotly_chart(EC.result_distribution_fig(groups, results, bookmaker),
                        width="stretch", config={"displayModeBar": False})
        C.note(f"Amber bars are what actually happened, blue bars are what "
               f"{bookmaker}'s {timing.lower()} odds implied. Home advantage shows up "
               f"as the tallest bar everywhere and the market gets it right.")

    st.write("")

    # ------------------------------ 2. CALIBRATION ---------------------------- #
    with C.card("Calibration — predicted probability vs what actually happened"):
        cal_series = {label: calc.calibration_series(long_sub)
                      for label, color, df_sub, long_sub in groups}
        st.plotly_chart(EC.calibration_fig(groups, cal_series, f"{bookmaker}, {timing.lower()}"),
                        width="stretch", config={"displayModeBar": False})
        C.note("When the market says 30%, does it happen ~30% of the time? Points on "
               "the diagonal mean yes. Across all matches the correlation is "
               "near-perfect (r ≈ 0.99) — but the chart below zooms in on the small "
               "systematic bends.")

    st.write("")

    # ------------------------------ 3. FLB --------------------------------- #
    with C.card("Favourite–longshot bias — the calibration gap, zoomed in"):
        flb_series = {label: calc.flb_series(long_sub)
                      for label, color, df_sub, long_sub in groups}
        st.plotly_chart(EC.flb_fig(groups, flb_series, f"{bookmaker}, {timing.lower()}"),
                        width="stretch", config={"displayModeBar": False})
        C.note("This is the same comparison as the calibration chart above, but "
               "plots <b>realised &minus; predicted</b> directly so the bend is "
               "visible — on a 0&ndash;100% calibration plot a few percentage points "
               "of bias is nearly invisible. Positive = realised more often than "
               "implied (underpriced); negative = overpriced.")

    st.write("")

    # --------------------------- 4. DRAW MISPRICING -------------------------- #
    with C.card("Draws — implied vs realised"):
        draw_vals = {label: calc.draw_mispricing_values(long_sub)
                     for label, color, df_sub, long_sub in groups}
        st.plotly_chart(EC.draw_mispricing_fig(groups, draw_vals),
                        width="stretch", config={"displayModeBar": False})
        C.note(f"The gap between the two bars is the draw-mispricing signal — "
               f"positive means draws happen more often than {bookmaker}'s "
               f"{timing.lower()} odds imply.")

    st.write("")

    # ------------------------------ 5. MARGIN -------------------------------- #
    with C.card("Bookmaker margin — Bet365 vs Pinnacle"):
        margin_vals = {label: calc.margin_values(df_sub, timing_key)
                       for label, color, df_sub, long_sub in groups}
        st.plotly_chart(EC.margin_fig(groups, margin_vals, timing.lower()),
                        width="stretch", config={"displayModeBar": False})
        C.note("Pinnacle (sharp, amber) runs at roughly half Bet365's margin "
               "(retail, blue) almost everywhere — the size of that gap is itself a "
               "signal the anomaly model watches. This chart always shows both "
               "books regardless of the Bookmaker filter above.")

    C.soft_divider()
    with C.card("So what?"):
        st.markdown(
            "The market is **broadly efficient** — calibration is near-perfect and "
            "the big patterns (home advantage, favourite strength) are priced "
            "correctly. The interesting story is in the **small, systematic "
            "bends**: the draw gap, the favourite–longshot bias, and the "
            "league-to-league differences in margin and disagreement. Use the "
            "filters above to see how these bends vary by tier, league, season, "
            "bookmaker, and odds timing — those bends are where the anomaly screen "
            "goes looking.")
