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

MISSION_STMT_TAB = 'Mission Statement'

def _ensure_mission_stmt_tab():
    try:
        svc      = _sheets()
        existing = {
            s['properties']['title']
            for s in svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute().get('sheets', [])
        }
        if MISSION_STMT_TAB not in existing:
            svc.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body={'requests': [{'addSheet': {'properties': {'title': MISSION_STMT_TAB}}}]},
            ).execute()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{MISSION_STMT_TAB}'!A1:B1",
        ).execute().get('values', [])
        if not rows:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{MISSION_STMT_TAB}'!A1",
                valueInputOption='RAW', body={'values': [['Type', 'Content']]},
            ).execute()
    except Exception:
        pass

@st.cache_data(ttl=5, show_spinner=False)
def pull_mission_statement():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{MISSION_STMT_TAB}'!A2:B10",
        ).execute().get('values', [])
        for row in rows:
            if len(row) >= 2 and row[0] == 'locked':
                return row[1]
        return ''
    except Exception:
        return ''

def save_mission_statement(text):
    svc  = _sheets()
    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{MISSION_STMT_TAB}'!A2:B10",
    ).execute().get('values', [])
    for i, row in enumerate(rows, start=2):
        if len(row) >= 1 and row[0] == 'locked':
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{MISSION_STMT_TAB}'!A{i}:B{i}",
                valueInputOption='RAW', body={'values': [['locked', text]]},
            ).execute()
            pull_mission_statement.clear()
            return
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID, range=f"'{MISSION_STMT_TAB}'!A:B",
        valueInputOption='RAW', insertDataOption='INSERT_ROWS',
        body={'values': [['locked', text]]},
    ).execute()
    pull_mission_statement.clear()

def generate_mission_polish(who, what, how, makes):
    from openai import OpenAI
    client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
    prompt = (
        'The Audeara team has voted on four building blocks for their mission statement:\n\n'
        f'- Who we serve: {who}\n'
        f'- What we provide: {what}\n'
        f'- How we do it: {how}\n'
        f'- What that makes possible: {makes}\n\n'
        'Rewrite these into a clean, natural mission statement that flows as proper English. '
        'One to two sentences. Keep the meaning of each building block intact. '
        'Do not add new ideas or change the intent. No hyphens or em dashes. British English. '
        'Output only the mission statement text, nothing else.'
    )
    resp = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=200,
    )
    return resp.choices[0].message.content.strip()

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

if not st.session_state.get('_mission_tab_ready'):
    _ensure_mission_stmt_tab()
    st.session_state['_mission_tab_ready'] = True

st.markdown('### Mission Statement Activity')

st.markdown(
    f'<div style="border-left:4px solid #005E63;background:#F0F7F7;'
    f'border-radius:0 8px 8px 0;padding:14px 18px;margin-bottom:20px;">'
    f'<div style="font-size:0.72em;font-weight:700;letter-spacing:1.5px;'
    f'color:#005E63;margin-bottom:6px;">JAMES\'S STARTING POINT</div>'
    f'<div style="font-size:1.05em;font-style:italic;color:#1a1a1a;'
    f'margin-bottom:8px;">"To connect people to the experiences that matter to them through sound technology."</div>'
    f'<div style="font-size:0.88em;color:#555;line-height:1.6;">'
    f'This is the draft mission statement. As a team today, we\'re going to work through '
    f'the building blocks of a mission and decide together on wording we all feel genuinely connected to.'
    f'</div></div>',
    unsafe_allow_html=True,
)

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
            try:
                append_submission(who.strip(), what.strip(), how.strip(), makes.strip())
                st.cache_data.clear()
                st.toast('Submitted. Head to the Vote tab to upvote your favourites.', icon='✅')
            except Exception as _e:
                st.error(f'Could not save — network issue. Please try submitting again. ({_e})')
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
                        try:
                            upsert_vote(col_key, answer)
                            st.session_state['voted_mission'].add(vote_key)
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as _e:
                            st.error(f'Vote not saved — network issue. Please try again. ({_e})')
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

        # ── AI polish ─────────────────────────────────────────────────────────────
        st.markdown('')
        all_four = all(k in top for k in ('Who', 'What', 'How', 'Makes Possible'))

        locked_mission = pull_mission_statement()
        if locked_mission:
            st.markdown(
                f'<div style="background:{TEAL};border-radius:10px;padding:18px 22px;margin-bottom:16px;">'
                f'<div style="font-size:0.68em;color:rgba(255,255,255,0.7);font-weight:700;'
                f'letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;">'
                f'Locked mission statement</div>'
                f'<div style="font-size:1.05em;color:#fff;font-weight:600;line-height:1.6;">'
                f'{locked_mission}</div></div>',
                unsafe_allow_html=True,
            )

        if all_four:
            if st.button('✨ Polish with AI', type='primary', key='mission_polish_btn'):
                with st.spinner('Rewriting…'):
                    try:
                        result = generate_mission_polish(
                            top['Who'][0], top['What'][0],
                            top['How'][0], top['Makes Possible'][0],
                        )
                        st.session_state['mission_generated'] = result
                    except Exception as _e:
                        st.error(f'Could not generate — {_e}')

            if 'mission_generated' in st.session_state:
                edited = st.text_area(
                    'Edit before locking',
                    value=st.session_state['mission_generated'],
                    height=100,
                    key='mission_edit_area',
                )
                if st.button('Lock this statement', key='mission_lock_btn'):
                    try:
                        save_mission_statement(edited.strip())
                        del st.session_state['mission_generated']
                        st.cache_data.clear()
                        st.toast('Mission statement locked ✓', icon='✅')
                        st.rerun()
                    except Exception as _e:
                        st.error(f'Could not save — {_e}')
        else:
            st.caption('All four categories need at least one vote before AI can polish the statement.')

        st.divider()

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
