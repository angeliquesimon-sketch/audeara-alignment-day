import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import datetime
from utils import _sheets, inject_styles, PURPLE, TEAL

SHEET_ID = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'

SUB_TAB  = 'Vision Submissions'
VOTE_TAB = 'Vision Votes'

CATEGORIES = [
    ('Headline',    'The cover headline'),
    ('The Story',   'What Audeara achieved to make the cover'),
    ('Quote',       'A quote from the story'),
    ('Bottom Line', 'What the finance section says'),
]

YEARS = ['2028', '2029', '2030', '2032', '2035']

# ── Sheet setup ────────────────────────────────────────────────────────────────

def _ensure_tabs():
    svc = _sheets()
    meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    existing = {s['properties']['title'] for s in meta.get('sheets', [])}
    requests = []
    if SUB_TAB not in existing:
        requests.append({'addSheet': {'properties': {'title': SUB_TAB}}})
    if VOTE_TAB not in existing:
        requests.append({'addSheet': {'properties': {'title': VOTE_TAB}}})
    if requests:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': requests},
        ).execute()
        # Write headers
        if SUB_TAB not in existing:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'{SUB_TAB}'!A1:G1",
                valueInputOption='RAW',
                body={'values': [['Timestamp', 'Year', 'Publication', 'Headline', 'The Story', 'Quote', 'Bottom Line']]},
            ).execute()
        if VOTE_TAB not in existing:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'{VOTE_TAB}'!A1:C1",
                valueInputOption='RAW',
                body={'values': [['Category', 'Answer', 'Votes']]},
            ).execute()

# ── Sheet helpers ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=20, show_spinner=False)
def pull_submissions():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{SUB_TAB}'!A:G",
        ).execute().get('values', [])
        if len(rows) < 2:
            return pd.DataFrame(columns=['Timestamp', 'Year', 'Publication', 'Headline', 'The Story', 'Quote', 'Bottom Line'])
        return pd.DataFrame(rows[1:], columns=rows[0])
    except Exception:
        return pd.DataFrame(columns=['Timestamp', 'Year', 'Publication', 'Headline', 'The Story', 'Quote', 'Bottom Line'])

def append_submission(year, pub, headline, story, quote, bottom):
    _sheets().spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"'{SUB_TAB}'!A:G",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [[
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            year, pub, headline, story, quote, bottom,
        ]]},
    ).execute()

@st.cache_data(ttl=20, show_spinner=False)
def pull_votes():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{VOTE_TAB}'!A:C",
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
        range=f"'{VOTE_TAB}'!A:C",
    ).execute().get('values', [])
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 2 and row[0] == category and row[1].strip().lower() == answer.strip().lower():
            current = int(row[2]) if len(row) > 2 else 0
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'{VOTE_TAB}'!C{i}",
                valueInputOption='RAW',
                body={'values': [[current + 1]]},
            ).execute()
            return
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"'{VOTE_TAB}'!A:C",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [[category, answer, 1]]},
    ).execute()

# ── Styles ─────────────────────────────────────────────────────────────────────

inject_styles()

st.markdown(f'''
<style>
.magazine-cover {{
    background: #111;
    color: #fff;
    border-radius: 10px;
    padding: 32px 36px 28px;
    margin: 16px 0 24px 0;
    position: relative;
}}
.mag-pub {{
    font-size: 0.75em;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 8px;
}}
.mag-year {{
    font-size: 0.72em;
    color: {TEAL};
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 20px;
}}
.mag-headline {{
    font-size: 2em;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 12px;
    color: #fff;
}}
.mag-story {{
    font-size: 0.9em;
    color: #ccc;
    line-height: 1.7;
    margin-bottom: 20px;
    border-left: 3px solid {TEAL};
    padding-left: 14px;
}}
.mag-quote {{
    font-size: 1.05em;
    font-style: italic;
    color: #fff;
    background: rgba(255,255,255,0.06);
    border-left: 4px solid {PURPLE.replace("#","#")};
    border-radius: 0 6px 6px 0;
    padding: 12px 16px;
    margin-bottom: 20px;
    line-height: 1.6;
}}
.mag-bottom-line {{
    background: {TEAL};
    color: #fff;
    font-size: 0.78em;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 4px 10px;
    border-radius: 4px;
    display: inline-block;
    margin-bottom: 6px;
}}
.mag-bottom-text {{
    color: #bbb;
    font-size: 0.88em;
    line-height: 1.5;
}}
</style>
''', unsafe_allow_html=True)

# ── Ensure sheet tabs exist ────────────────────────────────────────────────────

_ensure_tabs()

# ── Page header ────────────────────────────────────────────────────────────────

st.markdown('### Vision Activity — Magazine Cover Story')
st.markdown(
    'Imagine it\'s the future and Audeara has made the cover of a major publication. '
    'What\'s the story? What did we achieve? What does the world say about us?'
)

st.markdown(
    f'<div class="activity-card">'
    f'<strong>Flag on the hill:</strong> If Audeara were on the cover of a major magazine '
    f'in 2030 — what would the headline say? What did we build?'
    f'</div>',
    unsafe_allow_html=True,
)
st.markdown('')

tab_submit, tab_vote, tab_results = st.tabs(['💡 Submit ideas', '🗳️ Vote', '🏆 Results'])

# ── Submit ─────────────────────────────────────────────────────────────────────

with tab_submit:
    st.markdown('#### Your cover story')
    st.caption(
        'Answer some or all of the fields. Think 5–10 years out — what did Audeara achieve to earn this cover?'
    )
    with st.form('vision_submit_form', clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            year = st.selectbox('Year', YEARS, index=2)
        with c2:
            pub  = st.text_input('Publication', placeholder='e.g. Fast Company, The Australian, Time...')

        headline = st.text_input(
            'Cover headline',
            placeholder='e.g. "The company that made the world listen"',
        )
        story = st.text_area(
            'The story — what did Audeara achieve?',
            placeholder='e.g. "Audeara reached 1 million people in 40 countries by making hearing technology truly accessible..."',
            height=100,
        )
        quote = st.text_input(
            'A quote from the story',
            placeholder='e.g. "We didn\'t set out to build a hearing company. We set out to help people feel connected." — James Fielding',
        )
        bottom = st.text_input(
            'The bottom line — what does the finance section say?',
            placeholder='e.g. "Revenue crossed $50M, driven by B2B Auracast partnerships across 3 continents."',
        )
        submitted = st.form_submit_button('Submit', type='primary', use_container_width=True)

    if submitted:
        if any([headline.strip(), story.strip(), quote.strip(), bottom.strip()]):
            append_submission(year, pub.strip(), headline.strip(), story.strip(), quote.strip(), bottom.strip())
            st.cache_data.clear()
            st.toast('Submitted. Head to the Vote tab to upvote your favourites.', icon='✅')
        else:
            st.warning('Please fill in at least one field before submitting.')

    st.divider()
    subs = pull_submissions()
    if not subs.empty:
        st.markdown(f'#### {len(subs)} submission{"s" if len(subs) != 1 else ""} so far')
        for _, row in subs.iterrows():
            pub_str  = f' — {row["Publication"]}' if row.get('Publication', '').strip() else ''
            year_str = row.get('Year', '')
            st.markdown(
                f'<div class="activity-card">'
                f'<strong>{year_str}{pub_str}</strong><br>'
                f'<span style="font-size:1.1em;font-weight:700;">{row.get("Headline","")}</span><br>'
                f'<span style="font-size:0.9em;color:#555;">{row.get("The Story","")}</span><br>'
                f'<em style="font-size:0.88em;">{row.get("Quote","")}</em><br>'
                f'<span style="font-size:0.85em;color:#888;">{row.get("Bottom Line","")}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        if st.button('Refresh', key='refresh_vision_submit'):
            st.cache_data.clear()
            st.rerun()

# ── Vote ───────────────────────────────────────────────────────────────────────

with tab_vote:
    if 'voted_vision' not in st.session_state:
        st.session_state['voted_vision'] = set()

    subs  = pull_submissions()
    votes = pull_votes()

    if subs.empty:
        st.info('No submissions yet. Be the first to add your cover story in the Submit tab.')
    else:
        st.markdown('#### Upvote the answers that resonate most')
        st.caption('Vote for the headlines, story lines, quotes, and bottom lines that feel most true to where Audeara is headed.')
        c_ref, _ = st.columns([1, 6])
        with c_ref:
            if st.button('Refresh', key='refresh_vision_vote'):
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

            if not unique:
                st.caption('No answers submitted for this category yet.')
                continue

            for i, answer in enumerate(unique):
                count         = _count(col_key, answer)
                vote_key      = f'vision::{col_key}::{answer}'
                already_voted = vote_key in st.session_state['voted_vision']
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
                                 key=f'vote_vision_{col_key}_{i}',
                                 disabled=already_voted,
                                 use_container_width=True):
                        upsert_vote(col_key, answer)
                        st.session_state['voted_vision'].add(vote_key)
                        st.cache_data.clear()
                        st.rerun()
            st.markdown('')

# ── Results ────────────────────────────────────────────────────────────────────

with tab_results:
    votes = pull_votes()
    subs  = pull_submissions()
    c_ref2, _ = st.columns([1, 6])
    with c_ref2:
        if st.button('Refresh', key='refresh_vision_results'):
            st.cache_data.clear()
            st.rerun()

    if subs.empty:
        st.info('No submissions yet. Head to the Submit tab to add your cover story.')
    else:
        top = {}
        if not votes.empty:
            for col_key, _ in CATEGORIES:
                cat_votes = votes[votes['Category'] == col_key].copy()
                if not cat_votes.empty:
                    best = cat_votes.sort_values('Votes', ascending=False).iloc[0]
                    top[col_key] = (best['Answer'], int(best['Votes']))

        has_any = bool(top)

        # Derive display values — fall back to first submission if no votes yet
        def _top_or_first(col_key, col_df):
            if col_key in top:
                return top[col_key][0]
            vals = subs[col_df].fillna('').tolist()
            return next((v.strip() for v in vals if v.strip()), '')

        headline_val = _top_or_first('Headline', 'Headline')
        story_val    = _top_or_first('The Story', 'The Story')
        quote_val    = _top_or_first('Quote', 'Quote')
        bottom_val   = _top_or_first('Bottom Line', 'Bottom Line')

        st.markdown('#### The cover story so far')
        if not has_any:
            st.caption('No votes yet — showing ideas from the first submission. Head to Vote to start shaping the result.')

        col_cover, col_detail = st.columns([1, 1], gap='large')

        with col_cover:
            st.markdown(
                f'<div class="magazine-cover">'
                f'<div class="mag-pub">Audeara · Cover Story</div>'
                f'<div class="mag-year">It\'s 2030.</div>'
                f'<div class="mag-headline">{headline_val or "<em>Headline TBC</em>"}</div>'
                f'<div class="mag-story">{story_val or "<em>The story takes shape as submissions come in.</em>"}</div>'
                f'{"<div class=mag-quote>" + quote_val + "</div>" if quote_val else ""}'
                f'{"<div class=mag-bottom-line>The Bottom Line</div><div class=mag-bottom-text>" + bottom_val + "</div>" if bottom_val else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_detail:
            if has_any:
                st.markdown('#### Top votes per category')
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
                st.markdown('#### All submitted ideas')
                for _, row in subs.iterrows():
                    st.markdown(
                        f'<div class="activity-card" style="font-size:0.9em;">'
                        f'<strong>{row.get("Headline","")}</strong><br>'
                        f'<em>{row.get("Quote","")}</em>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
