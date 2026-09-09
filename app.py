import streamlit as st
import threading
import importlib
import sys

# Ensure shared modules are fully imported before any page can race on them.
_import_lock = threading.Lock()
with _import_lock:
    for _mod in ('utils', 'styles_shared', 'strategy_cascade_shared',
                 'magazine_shared', 'one_thing_shared', 'scorecard_shared'):
        if _mod not in sys.modules:
            importlib.import_module(_mod)

st.set_page_config(
    page_title='Audeara Alignment Day',
    page_icon='🎯',
    layout='wide',
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400&display=swap');
@import url('https://use.typekit.net/bxp8awr.css');

html, body, [class*="css"], .stMarkdown, .stTextInput > div > div > input,
.stTextArea > div > div > textarea, .stSelectbox > div > div,
.stButton > button, .stRadio > div, .stSlider > div,
h1, h2, h3, h4, h5, h6 {
    font-family: 'Noto Sans', sans-serif !important;
}
h1, h2, h3, h4 {
    font-family: 'roc-grotesk', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

st.title('Audeara Alignment Day')
st.caption('FY27 · Strategy and alignment activities')

pg = st.navigation({
    'Overview': [
        st.Page('activities/overview.py',                       title='🏠 Overview'),
    ],
    'Activities': [
        st.Page('activities/mission_statement.py',              title='Mission Statement'),
        st.Page('activities/magazine_cover.py',                 title='Vision Statement'),
        st.Page('activities/styles.py',                         title='Different Styles'),
        st.Page('activities/one_thing.py',                      title='The One Thing'),
        st.Page('activities/strategy_cascade.py',               title='Strategy Cascade'),
        st.Page('activities/scorecard.py',                      title='FY27 Scorecard'),
    ],
    'Facilitator': [
        st.Page('activities/magazine_facilitate.py',            title='🎛️ Facilitate — Vision'),
        st.Page('activities/styles_facilitate.py',              title='🎛️ Facilitate — Styles'),
        st.Page('activities/one_thing_facilitate.py',           title='🎛️ Facilitate — One Thing'),
        st.Page('activities/strategy_cascade_facilitate.py',    title='🎛️ Facilitate — Cascade'),
        st.Page('activities/scorecard_facilitate.py',           title='🎛️ Facilitate — Scorecard'),
    ],
})
pg.run()
