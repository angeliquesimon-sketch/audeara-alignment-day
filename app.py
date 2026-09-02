import streamlit as st

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
        st.Page('activities/strategy_cascade_results.py',       title='Cascade Results'),
    ],
    'Facilitator': [
        st.Page('activities/magazine_facilitate.py',            title='🎛️ Facilitate — Vision'),
        st.Page('activities/styles_facilitate.py',              title='🎛️ Facilitate — Styles'),
        st.Page('activities/strategy_cascade_facilitate.py',    title='🎛️ Facilitate — Cascade'),
    ],
})
pg.run()
