import streamlit as st

st.set_page_config(
    page_title='Audeara Alignment Day',
    page_icon='🎯',
    layout='wide',
)

st.title('Audeara Alignment Day')
st.caption('FY27 · Strategy and alignment activities')

pg = st.navigation({
    'Activities': [
        st.Page('activities/mission_statement.py', title='Mission Statement'),
        st.Page('activities/magazine_cover.py',    title='Vision — Magazine Cover'),
    ],
})
pg.run()
