import sys, os, hashlib, base64
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import datetime
from utils import _sheets, inject_styles, PURPLE, TEAL

SHEET_ID = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'
SUB_TAB  = 'Vision Submissions'
VOTE_TAB = 'Vision Votes'

COLUMNS = ['Timestamp', 'Year', 'Publication', 'Headline', 'The Story', 'Quote', 'Bottom Line', 'Image']

CATEGORIES = [
    ('Headline',    'The cover headline'),
    ('The Story',   'What Audeara achieved to make the cover'),
    ('Quote',       'A quote from the story'),
    ('Bottom Line', 'What the finance section says'),
    ('Image',       'The cover image'),
]

COVER_YEAR    = '2030'
PREVIEW_WIDTH = 260   # px — screen preview size; full image is 1024×1536 (portrait A4)

IMAGE_STYLE = (
    'Bold editorial magazine cover photograph. '
    'Warm, aspirational, human — real people in genuine moments of connection. '
    'Colour palette: warm sand and neutral tones as the foundation, with deep teal as the feature accent colour. '
    'Bright, inviting light — confident and optimistic, not dark or dramatic. '
    'Clean, modern composition. Stylish but approachable. '
    'No text, no letters, no words, no numbers. '
)

# ── Sheet setup ────────────────────────────────────────────────────────────────

def _ensure_tabs():
    svc  = _sheets()
    meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    existing = {s['properties']['title'] for s in meta.get('sheets', [])}
    add_reqs = []
    if SUB_TAB not in existing:
        add_reqs.append({'addSheet': {'properties': {'title': SUB_TAB}}})
    if VOTE_TAB not in existing:
        add_reqs.append({'addSheet': {'properties': {'title': VOTE_TAB}}})
    if add_reqs:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID, body={'requests': add_reqs},
        ).execute()

    # Write / verify headers
    if SUB_TAB not in existing:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'{SUB_TAB}'!A1:H1",
            valueInputOption='RAW',
            body={'values': [COLUMNS]},
        ).execute()
    else:
        # Migrate: add Image column header if missing
        current = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{SUB_TAB}'!A1:H1",
        ).execute().get('values', [[]])
        headers = current[0] if current else []
        if 'Image' not in headers:
            col = len(headers) + 1
            col_letter = chr(ord('A') + len(headers))
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'{SUB_TAB}'!{col_letter}1",
                valueInputOption='RAW',
                body={'values': [['Image']]},
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
            range=f"'{SUB_TAB}'!A:H",
        ).execute().get('values', [])
        if len(rows) < 2:
            return pd.DataFrame(columns=COLUMNS)
        headers = rows[0]
        data    = [r + [''] * (len(headers) - len(r)) for r in rows[1:]]
        return pd.DataFrame(data, columns=headers)
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

def append_submission(year, pub, headline, story, quote, bottom, image_desc):
    _sheets().spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"'{SUB_TAB}'!A:H",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [[
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            year, pub, headline, story, quote, bottom, image_desc,
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

# ── Image generation ───────────────────────────────────────────────────────────

def _img_cache_key(description):
    return f"cover_img_1024x1536_v2_{hashlib.md5(description.encode()).hexdigest()}"

def generate_cover_image(description):
    """Return PNG bytes for a given image description, cached in session_state."""
    key = _img_cache_key(description)
    if key in st.session_state:
        return st.session_state[key]

    try:
        from openai import OpenAI
        client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
        prompt = IMAGE_STYLE + description
        resp      = client.images.generate(
            model='gpt-image-1',
            prompt=prompt,
            size='1024x1536',
            n=1,
        )
        img_bytes = base64.b64decode(resp.data[0].b64_json)
        st.session_state[key] = img_bytes
        return img_bytes
    except Exception as e:
        st.session_state[key] = str(e)
        return None

def _show_image(description, caption=None):
    """Generate and display a cover image for the given description."""
    if not description or not description.strip():
        return
    if not st.secrets.get('OPENAI_API_KEY'):
        st.caption('_(Image generation not configured)_')
        return
    key = _img_cache_key(description)
    if key not in st.session_state:
        with st.spinner('Generating cover image…'):
            generate_cover_image(description)
    img = st.session_state.get(key)
    if isinstance(img, bytes):
        st.image(img, caption=caption, width=PREVIEW_WIDTH)
    elif isinstance(img, str):
        st.caption(f'_(Image generation failed: {img})_')
    else:
        st.caption('_(Image generation failed — unknown error)_')

# ── Styles ─────────────────────────────────────────────────────────────────────

inject_styles()

st.markdown(f'''
<style>
.magazine-cover {{
    background: #111;
    color: #fff;
    border-radius: 10px;
    padding: 32px 36px 28px;
    margin: 0 0 16px 0;
}}
.mag-pub {{
    font-size: 0.72em;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 6px;
}}
.mag-year {{
    font-size: 0.7em;
    color: {TEAL};
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 18px;
}}
.mag-headline {{
    font-size: 1.9em;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 14px;
    color: #fff;
}}
.mag-story {{
    font-size: 0.88em;
    color: #ccc;
    line-height: 1.7;
    margin-bottom: 18px;
    border-left: 3px solid {TEAL};
    padding-left: 14px;
}}
.mag-quote {{
    font-size: 1em;
    font-style: italic;
    color: #fff;
    background: rgba(255,255,255,0.06);
    border-left: 4px solid {PURPLE};
    border-radius: 0 6px 6px 0;
    padding: 12px 16px;
    margin-bottom: 18px;
    line-height: 1.6;
}}
.mag-bl-label {{
    background: {TEAL};
    color: #fff;
    font-size: 0.7em;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 4px;
    display: inline-block;
    margin-bottom: 6px;
}}
.mag-bottom-text {{
    color: #bbb;
    font-size: 0.86em;
    line-height: 1.5;
}}
</style>
''', unsafe_allow_html=True)

# ── Init ───────────────────────────────────────────────────────────────────────

_ensure_tabs()

# ── Page header ────────────────────────────────────────────────────────────────

st.markdown('### Vision Activity — Magazine Cover Story')
st.markdown(
    'Imagine it\'s 2030. Audeara has made the cover of a major publication. '
    'What\'s the story? What did we achieve? What does the world say about us?'
)
st.markdown(
    f'<div class="activity-card">'
    f'<strong>Flag on the hill:</strong> If Audeara were on the cover of a major magazine '
    f'in 2030 — what would the headline say? What did we build? What does the cover look like?'
    f'</div>',
    unsafe_allow_html=True,
)
st.markdown('')

tab_submit, tab_vote, tab_results = st.tabs(['💡 Submit ideas', '🗳️ Vote', '🏆 Results'])

# ── Submit ─────────────────────────────────────────────────────────────────────

with tab_submit:
    st.markdown('#### Your cover story')
    st.caption(
        'Think about Audeara in 2030. What did we achieve? '
        'Fill in as many or as few fields as you like — there are no wrong answers.'
    )
    with st.form('vision_submit_form', clear_on_submit=True):
        pub = st.text_input(
            'Publication',
            placeholder='e.g. Fast Company, The Australian, Time, Harvard Business Review…',
        )
        headline = st.text_input(
            'Cover headline ✦',
            placeholder='e.g. "The company that made the world listen"',
        )
        story = st.text_area(
            'The story — what did Audeara achieve?',
            placeholder='e.g. "Audeara reached 1 million people across 40 countries by making hearing technology truly accessible…"',
            height=90,
        )
        quote = st.text_input(
            'A quote from the story',
            placeholder='e.g. "We didn\'t set out to build a hearing company. We set out to help people feel connected." — James Fielding',
        )
        bottom = st.text_input(
            'The bottom line — what does the finance section say?',
            placeholder='e.g. "Revenue crossed $50M, driven by Auracast partnerships across 3 continents."',
        )
        image_desc = st.text_area(
            '🎨 Describe the cover image',
            placeholder=(
                'Describe a scene, image, or feeling for the cover — '
                'AI will generate it in Audeara\'s brand style.\n'
                'e.g. "A person wearing headphones in a packed auditorium, '
                'surrounded by light and warmth, connected to the crowd."'
            ),
            height=90,
        )
        submitted = st.form_submit_button('Submit', type='primary', use_container_width=True)

    if submitted:
        if any([headline.strip(), story.strip(), quote.strip(), bottom.strip(), image_desc.strip()]):
            append_submission(
                COVER_YEAR, pub.strip(), headline.strip(),
                story.strip(), quote.strip(), bottom.strip(), image_desc.strip(),
            )
            st.cache_data.clear()
            st.toast('Submitted! Head to the Vote tab to upvote your favourites.', icon='✅')
            if image_desc.strip():
                st.toast('Generating your cover image in the background…', icon='🎨')
        else:
            st.warning('Please fill in at least one field before submitting.')

    st.divider()
    subs = pull_submissions()
    if not subs.empty:
        st.markdown(f'#### {len(subs)} submission{"s" if len(subs) != 1 else ""} so far')
        for _, row in subs.iterrows():
            img_desc = row.get('Image', '').strip()
            pub_str  = f' · {row.get("Publication","").strip()}' if row.get('Publication','').strip() else ''
            c_text, c_img = st.columns([3, 2]) if img_desc else (st.container(), None)
            with (c_text if img_desc else c_text):
                st.markdown(
                    f'<div class="activity-card">'
                    f'<span style="font-size:0.75em;color:#888;">{COVER_YEAR}{pub_str}</span><br>'
                    f'<span style="font-size:1.05em;font-weight:700;">{row.get("Headline","")}</span><br>'
                    f'<span style="font-size:0.88em;color:#555;">{row.get("The Story","")}</span><br>'
                    f'<em style="font-size:0.85em;">{row.get("Quote","")}</em><br>'
                    f'<span style="font-size:0.82em;color:#777;">{row.get("Bottom Line","")}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            if img_desc and c_img:
                with c_img:
                    _show_image(img_desc)
            st.markdown('')

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

                if col_key == 'Image':
                    # Show the generated image above the vote row
                    img_col, _ = st.columns([2, 1])
                    with img_col:
                        _show_image(answer)
                    a_col, b_col = st.columns([7, 1])
                else:
                    a_col, b_col = st.columns([7, 1])

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

        has_votes = bool(top)

        def _top_or_first(col_key, col_name):
            if col_key in top:
                return top[col_key][0]
            vals = subs[col_name].fillna('').tolist() if col_name in subs.columns else []
            return next((v.strip() for v in vals if v.strip()), '')

        headline_val = _top_or_first('Headline',    'Headline')
        story_val    = _top_or_first('The Story',   'The Story')
        quote_val    = _top_or_first('Quote',       'Quote')
        bottom_val   = _top_or_first('Bottom Line', 'Bottom Line')
        pub_val      = subs['Publication'].fillna('').iloc[0].strip() if 'Publication' in subs.columns else ''

        # Cover image: use the top-voted image description, fall back to first submission with one
        cover_img_desc = ''
        if 'Image' in top:
            cover_img_desc = top['Image'][0]
        elif 'Image' in subs.columns:
            cover_img_desc = next(
                (v.strip() for v in subs['Image'].fillna('').tolist() if v.strip()), ''
            )

        st.markdown('#### The cover story so far')
        if not has_votes:
            st.caption('No votes yet — showing the first submission. Head to Vote to start shaping the result.')

        col_img, col_cover = st.columns([1, 1], gap='large')

        with col_img:
            if cover_img_desc:
                _show_image(cover_img_desc, caption=f'Cover image · {COVER_YEAR}')
            else:
                st.markdown(
                    f'<div style="background:#1a1a2e;border-radius:10px;height:340px;'
                    f'display:flex;align-items:center;justify-content:center;'
                    f'color:#555;font-size:0.88em;text-align:center;padding:24px;">'
                    f'Add an image description in your submission<br>and it will appear here.'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        with col_cover:
            pub_display = pub_val or 'Audeara · Cover Story'
            st.markdown(
                f'<div class="magazine-cover">'
                f'<div class="mag-pub">{pub_display}</div>'
                f'<div class="mag-year">It\'s {COVER_YEAR}.</div>'
                f'<div class="mag-headline">{headline_val or "<em style=color:#555>Headline coming soon</em>"}</div>'
                f'{"<div class=mag-story>" + story_val + "</div>" if story_val else ""}'
                f'{"<div class=mag-quote>" + quote_val + "</div>" if quote_val else ""}'
                f'{"<div class=mag-bl-label>The Bottom Line</div><div class=mag-bottom-text>" + bottom_val + "</div>" if bottom_val else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )

            if has_votes:
                st.markdown('**Votes by category**')
                for col_key, col_label in CATEGORIES:
                    if col_key in top:
                        _, count = top[col_key]
                        c1, c2 = st.columns([5, 1])
                        with c1:
                            st.markdown(f'_{col_label}_')
                        with c2:
                            st.write(f'**{count}**')
