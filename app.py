import streamlit as st
import threading
import importlib
import sys

# Ensure shared modules are fully imported before any page can race on them.
# Uses a process-level lock so only one thread does the import; others wait
# and then find the module already in sys.modules.
_import_lock = threading.Lock()
with _import_lock:
    for _mod in ('utils', 'styles_shared', 'strategy_cascade_shared'):
        if _mod not in sys.modules:
            importlib.import_module(_mod)

st.set_page_config(
    page_title='Audeara Alignment Day',
    page_icon='🎯',
    layout='wide',
)

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
        st.Page('activities/strategy_cascade.py',               title='Strategy Cascade'),
    ],
    'Facilitator': [
        st.Page('activities/magazine_facilitate.py',            title='🎛️ Facilitate — Vision'),
        st.Page('activities/styles_facilitate.py',              title='🎛️ Facilitate — Styles'),
        st.Page('activities/strategy_cascade_facilitate.py',    title='🎛️ Facilitate — Cascade'),
    ],
})
pg.run()
