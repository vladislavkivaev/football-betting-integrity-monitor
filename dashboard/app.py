"""Football Betting Market Efficiency Monitor — Streamlit presentation + dashboard.

Run with:  streamlit run app.py
"""
import streamlit as st

from lib import theme as T
from lib.data import load_matches
from views import overview, betting101, efficiency, hypothesis, anomaly, dashboard

st.set_page_config(
    page_title="Betting Market Efficiency Monitor",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(T.GLOBAL_CSS, unsafe_allow_html=True)

df = load_matches()

PAGES = {
    "Overview": overview,
    "Betting 101": betting101,
    "Market Efficiency": efficiency,
    "Hypothesis Testing": hypothesis,
    "Anomaly Detection": anomaly,
    "Match Dashboard": dashboard,
}

# ------------------------------ SIDEBAR ----------------------------------- #
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="logo"><span></span></div>'
        '<div class="name">Betting Market Efficiency <br>Monitor</div></div>',
        unsafe_allow_html=True)
    st.markdown('<div class="sidebar-label">PRESENTATION</div>',
                unsafe_allow_html=True)
    choice = st.radio("nav", list(PAGES.keys()), label_visibility="collapsed")
    st.markdown(
        '<div class="sidebar-foot">Vladislav Kivaev<br>'
        'Spiced Academy · Berlin 2026</div>', unsafe_allow_html=True)

# ------------------------------- ROUTE ------------------------------------ #
PAGES[choice].render(df)
