import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import datetime
from utils import _sheets, inject_styles, PURPLE, TEAL

SHEET_ID = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'

CATEGORIES = [
    ('Who',            'Who do we serve?'),
    ('What',           'What do we provide?'),
    ('How',            'How do we do that?'),
    ('Makes Possible', 'What does that make possible?'),
]

# ── Sheet helpers ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=20, show_spinner=False)
def pull_submissions():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="'Submissions'!A:E",
        ).execute().get('values', [])
        if len(rows) < 2:
            return pd.DataFrame(columns=['Timestamp', 'Who', 'What', 'How', 'Makes Possible'])
        return pd.DataFrame(rows[1:], columns=rows[0])
    except Exception:
        return pd.DataFrame(columns=['Timestamp', 'Who', 'What', 'How', 'Makes Possible'])

def append_submission(who, what, how, makes):
    _sheets().spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range="'Submissions'!A:E",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [[datetime.now().strftime('%Y-%m-%d %H:%M:%S'), who, what, how, makes]]},
    ).execute()

@st.cache_data(ttl=20, show_spinner=False)
def pull_votes():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="'Votes'!A:C",
        ).execute().get('values', [])
        if len(rows) < 2:
            return pd.DataFrame(columns=['Category', 'Answer', 'Votes'])
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df['Votes'] = pd.to_numeric(df['Votes'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception:
        return pd.DataFrame(columns=['Category', 'Answer', 'Votes'])

def upsert_vote(category, answer):
    svc  = _sheets()
    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range="'Votes'!A:C",
    ).execute().get('values', [])
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 2 and row[0] == category and row[1].strip().lower() == answer.strip().lower():
            current = int(row[2]) if len(row) > 2 else 0
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'Votes'!C{i}",
                valueInputOption='RAW',
                body={'values': [[current + 1]]},
            ).execute()
            return
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range="'Votes'!A:C",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [[category, answer, 1]]},
    ).execute()

# ── Page ───────────────────────────────────────────────────────────────────────

inject_styles()

st.markdown('### Mission Statement Activity')
st.markdown(
    'Help shape how Audeara describes itself. Submit your ideas below, '
    'then vote on the answers that resonate most across each part of the sentence.'
)
st.markdown(
    f'<div class="activity-card">'
    f'We help <strong>[who]</strong> do <strong>[what]</strong> '
    f'by <strong>[how]</strong>, so they can <strong>[what does that make possible?]</strong>.'
    f'</div>',
    unsafe_allow_html=True,
)
st.markdown('')

tab_submit, tab_vote, tab_results = st.tabs(['💡 Submit ideas', '🗳️ Vote', '🏆 Results'])

# ── Submit ─────────────────────────────────────────────────────────────────────

with tab_submit:
    st.markdown('#### Your ideas')
    st.caption(
        'Answer each question with your honest instinct. '
        'No right or wrong answers. You can submit as many times as you like.'
    )
    with st.form('submit_form', clear_on_submit=True):
        who   = st.text_input('Who do we serve?',
                              placeholder='e.g. people with hearing loss, aged care residents...')
        what  = st.text_input('What do we provide?',
                              placeholder='e.g. personalised listening technology...')
        how   = st.text_input('How do we do that?',
                              placeholder='e.g. by adapting sound to each individual hearing profile...')
        makes = st.text_input('What does that make possible?',
                              placeholder='e.g. full participation in everyday life...')
        submitted = st.form_submit_button('Submit', type='primary', use_container_width=True)

    if submitted:
        if any([who.strip(), what.strip(), how.strip(), makes.strip()]):
            append_submission(who.strip(), what.strip(), how.strip(), makes.strip())
            st.cache_data.clear()
            st.toast('Submitted. Head to the Vote tab to upvote your favourites.', icon='✅')
        else:
            st.warning('Please fill in at least one field before submitting.')

    st.divider()
    subs = pull_submissions()
    if not subs.empty:
        st.markdown(f'#### {len(subs)} submission{"s" if len(subs) != 1 else ""} so far')
        for _, row in subs.iterrows():
            st.markdown(
                f'<div class="activity-card">'
                f'We help <strong>{row["Who"]}</strong> do <strong>{row["What"]}</strong> '
                f'by <strong>{row["How"]}</strong>, so they can <strong>{row["Makes Possible"]}</strong>.'
                f'</div>',
                unsafe_allow_html=True,
            )
        if st.button('Refresh', key='refresh_submit'):
            st.cache_data.clear()
            st.rerun()

# ── Vote ───────────────────────────────────────────────────────────────────────

with tab_vote:
    if 'voted_mission' not in st.session_state:
        st.session_state['voted_mission'] = set()

    subs  = pull_submissions()
    votes = pull_votes()

    if subs.empty:
        st.info('No submissions yet. Be the first to add ideas in the Submit tab.')
    else:
        st.markdown('#### Upvote the answers that resonate most')
        st.caption('Vote on individual answers in each category. Vote for as many as you like.')
        c_ref, _ = st.columns([1, 6])
        with c_ref:
            if st.button('Refresh', key='refresh_vote'):
                st.cache_data.clear()
                st.rerun()

        def _count(col_key, answer):
            if votes.empty:
                return 0
            match = votes[
                (votes['Category'] == col_key) &
                (votes['Answer'].str.strip().str.lower() == answer.lower())
            ]
            return int(match.iloc[0]['Votes']) if not match.empty else 0

        for col_key, col_label in CATEGORIES:
            st.markdown(f'<div class="category-header">{col_label}</div>', unsafe_allow_html=True)
            unique = list(dict.fromkeys(
                a.strip() for a in subs[col_key].fillna('').tolist() if a.strip()
            ))
            unique = sorted(unique, key=lambda a: _count(col_key, a), reverse=True)

            for i, answer in enumerate(unique):
                count         = _count(col_key, answer)
                vote_key      = f'mission::{col_key}::{answer}'
                already_voted = vote_key in st.session_state['voted_mission']
                a_col, b_col  = st.columns([7, 1])
                with a_col:
                    st.markdown(
                        f'<div class="answer-row">{answer}'
                        f'<span class="vote-count"> &nbsp;·&nbsp; {count} vote{"s" if count != 1 else ""}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with b_col:
                    if st.button('✓' if already_voted else '▲',
                                 key=f'vote_mission_{col_key}_{i}',
                                 disabled=already_voted,
                                 use_container_width=True):
                        upsert_vote(col_key, answer)
                        st.session_state['voted_mission'].add(vote_key)
                        st.cache_data.clear()
                        st.rerun()
            st.markdown('')

# ── Results ────────────────────────────────────────────────────────────────────

with tab_results:
    votes = pull_votes()
    subs  = pull_submissions()
    c_ref2, _ = st.columns([1, 6])
    with c_ref2:
        if st.button('Refresh', key='refresh_results'):
            st.cache_data.clear()
            st.rerun()

    if subs.empty:
        st.info('No submissions yet. Head to the Submit tab to add ideas.')
    else:
        top = {}
        if not votes.empty:
            for col_key, _ in CATEGORIES:
                cat_votes = votes[votes['Category'] == col_key].copy()
                if not cat_votes.empty:
                    best = cat_votes.sort_values('Votes', ascending=False).iloc[0]
                    top[col_key] = (best['Answer'], int(best['Votes']))

        who_str   = f'<strong>{top["Who"][0]}</strong>'            if 'Who'           in top else '<em>[who]</em>'
        what_str  = f'<strong>{top["What"][0]}</strong>'           if 'What'          in top else '<em>[what]</em>'
        how_str   = f'<strong>{top["How"][0]}</strong>'            if 'How'           in top else '<em>[how]</em>'
        makes_str = f'<strong>{top["Makes Possible"][0]}</strong>' if 'Makes Possible' in top else '<em>[what does that make possible?]</em>'

        st.markdown('#### Current leading sentence')
        st.markdown(
            f'<div class="winning-box">'
            f'We help {who_str} do {what_str} by {how_str}, so they can {makes_str}.'
            f'</div>',
            unsafe_allow_html=True,
        )

        if top:
            st.markdown('#### Top answer per category')
            for col_key, col_label in CATEGORIES:
                if col_key in top:
                    answer, count = top[col_key]
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f'**{col_label}**  \n{answer}')
                    with c2:
                        st.metric('Votes', count)
                    st.markdown('')
        else:
            st.caption('No votes yet — head to the Vote tab to start voting.')
