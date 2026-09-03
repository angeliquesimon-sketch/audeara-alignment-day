import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import streamlit.components.v1 as components
from utils import inject_styles, PURPLE, TEAL, with_retry, _sheets, _clear_sheets
from magazine_shared import (
    CATEGORIES, COVER_YEAR, IMGS_FOLDER_ID,
    _ensure_tabs, pull_submissions, pull_votes,
    set_vote_count, _img_cache_key,
    generate_cover_image, _compose_cover_image, _save_composed_to_drive,
    pull_generated_story, save_generated_story, generate_story,
    build_cover_html,
    pull_vision_data, save_vision_candidates, save_final_vision, generate_vision_candidates,
    pull_vision_candidate_votes, pull_mission_context,
)

inject_styles()

st.markdown(f'''
<style>
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
</style>
''', unsafe_allow_html=True)

if not st.session_state.get('_tabs_ensured_v2'):
    try:
        with_retry(_ensure_tabs, on_retry=_clear_sheets)
        st.session_state['_tabs_ensured_v2'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue — some features may not save correctly. ({_e})')

# ── Password gate ──────────────────────────────────────────────────────────────

st.markdown('### 🎛️ Facilitate — Magazine Cover Activity')

if 'facilitate_auth' not in st.session_state:
    st.session_state['facilitate_auth'] = False

if not st.session_state['facilitate_auth']:
    st.caption('This page is for the session facilitator only.')
    pwd_input = st.text_input('Password', type='password', key='facilitate_pwd_input')
    if st.button('Unlock', type='primary', key='facilitate_unlock'):
        correct = st.secrets.get('FACILITATE_PASSWORD', 'audeara2030')
        if pwd_input == correct:
            st.session_state['facilitate_auth'] = True
            st.rerun()
        else:
            st.error('Incorrect password.')
    st.stop()

# ── Authenticated ──────────────────────────────────────────────────────────────

if st.button('🔒 Lock', key='facilitate_lock'):
    st.session_state['facilitate_auth'] = False
    st.rerun()

st.markdown(
    f'📁 **[View saved cover images on Google Drive]'
    f'(https://drive.google.com/drive/folders/{IMGS_FOLDER_ID})**'
)
st.caption('Composed cover PNGs save automatically when you preview a version below. Raw AI images also land here.')

# ── Live submission counter (auto-refreshes every 20s) ─────────────────────────

@st.fragment(run_every=20)
def _submission_counter():
    _subs = pull_submissions()
    count = len(_subs)
    c_msg, c_btn = st.columns([5, 1])
    with c_msg:
        if count == 0:
            st.info('No submissions yet — waiting for the room.')
        else:
            st.success(f'**{count} submission{"s" if count != 1 else ""}** received so far.')
    with c_btn:
        if st.button('Refresh', key='fac_refresh_top', use_container_width=True):
            st.cache_data.clear()
            st.rerun()

_submission_counter()

fac_subs  = pull_submissions()
fac_votes = pull_votes()

if fac_subs.empty:
    st.stop()

# ── Vote adjustment ────────────────────────────────────────────────────────────

st.markdown('#### Adjust votes')
st.caption('Override any vote count directly. Changes update the sheet immediately and are reflected in the Results tab.')

c_ref, _ = st.columns([1, 5])
with c_ref:
    if st.button('Refresh all', key='fac_refresh'):
        st.cache_data.clear()
        st.rerun()

def _current_count(col_key, answer):
    if fac_votes.empty:
        return 0
    m = fac_votes[
        (fac_votes['Category'] == col_key) &
        (fac_votes['Answer'].str.strip().str.lower() == answer.lower())
    ]
    return int(m.iloc[0]['Votes']) if not m.empty else 0

for col_key, col_label in CATEGORIES:
    st.markdown(f'<div class="category-header">{col_label}</div>', unsafe_allow_html=True)
    unique = list(dict.fromkeys(
        a.strip() for a in fac_subs[col_key].fillna('').tolist() if a.strip()
    ))
    if not unique:
        st.caption('No answers submitted yet.')
        continue

    for answer in unique:
        cur      = _current_count(col_key, answer)
        key_slug = hashlib.md5(f'{col_key}:{answer}'.encode()).hexdigest()[:10]
        a_col, b_col, c_col = st.columns([5, 1, 1])
        with a_col:
            st.markdown(f'<div class="answer-row">{answer}</div>', unsafe_allow_html=True)
        with b_col:
            new_val = st.number_input(
                'Votes', min_value=0, value=cur,
                key=f'fac_ni_{key_slug}',
                label_visibility='collapsed',
            )
        with c_col:
            if st.button('Save', key=f'fac_sv_{key_slug}'):
                try:
                    set_vote_count(col_key, answer, int(new_val))
                    st.cache_data.clear()
                    st.toast(f'Saved — {col_label}: {int(new_val)} votes', icon='✅')
                    st.rerun()
                except Exception as _e:
                    st.error(f'Could not save. ({_e})')
    st.markdown('')

st.divider()

# ── Build cover versions ───────────────────────────────────────────────────────

st.markdown('#### Build cover versions')
st.caption('Mix and match any submitted answers to preview different cover combinations. Images are generated once and cached.')

def _col_options(col_name):
    return ['(none)'] + list(dict.fromkeys(
        v.strip() for v in fac_subs[col_name].fillna('').tolist() if v.strip()
    ))

for version in ['A', 'B']:
    with st.expander(f'Version {version}', expanded=(version == 'A')):
        v_pub     = st.selectbox('Publication',           _col_options('Publication'),   key=f'fac_pub_{version}')
        v_hl      = st.selectbox('Headline',              _col_options('Headline'),       key=f'fac_hl_{version}')
        v_partner = st.selectbox('Official ___ Partner',  _col_options('Partner Title'), key=f'fac_partner_{version}')
        v_qt      = st.selectbox('Quote',                 _col_options('Quote'),          key=f'fac_qt_{version}')
        v_standout = st.selectbox('Standout',             _col_options('Standout'),       key=f'fac_standout_{version}')
        v_img     = st.selectbox('Cover image',           _col_options('Image'),          key=f'fac_img_{version}')

        if st.button(f'Preview Version {version}', type='primary', key=f'fac_preview_{version}'):
            st.session_state[f'fac_cover_{version}'] = {
                'pub':     '' if v_pub      == '(none)' else v_pub,
                'hl':      '' if v_hl       == '(none)' else v_hl,
                'partner': '' if v_partner  == '(none)' else v_partner,
                'qt':      '' if v_qt       == '(none)' else v_qt,
                'standout': '' if v_standout == '(none)' else v_standout,
                'img':     '' if v_img      == '(none)' else v_img,
            }

        cover_state = st.session_state.get(f'fac_cover_{version}')
        if cover_state:
            v_img_bytes = None
            if cover_state['img']:
                cached = st.session_state.get(_img_cache_key(cover_state['img']))
                if isinstance(cached, bytes):
                    v_img_bytes = cached
                else:
                    with st.spinner('Generating image…'):
                        result = generate_cover_image(cover_state['img'])
                        v_img_bytes = result if isinstance(result, bytes) else None

            components.html(
                build_cover_html(
                    cover_state['pub'], cover_state['hl'],
                    cover_state['qt'],  cover_state['standout'], v_img_bytes,
                    partner_title=cover_state.get('partner', ''),
                ),
                height=622,
            )

            if v_img_bytes:
                vc_key = f'fac_composed_{version}_{hashlib.md5((cover_state["hl"] + cover_state["qt"] + cover_state["standout"]).encode()).hexdigest()}'
                if vc_key not in st.session_state:
                    with st.spinner(f'Saving Version {version} to Drive…'):
                        try:
                            vc = _compose_cover_image(
                                cover_state['pub'], cover_state['hl'],
                                cover_state['qt'],  cover_state['standout'], v_img_bytes,
                            )
                            _save_composed_to_drive(f"{cover_state['hl']}-v{version}", vc)
                            st.session_state[vc_key] = vc
                            st.toast(f'Version {version} saved to Drive ✓', icon='✅')
                        except Exception as _e:
                            st.session_state[vc_key] = None
                vc = st.session_state.get(vc_key)
                if isinstance(vc, bytes):
                    st.download_button(
                        label=f'⬇ Download Version {version} (PNG)',
                        data=vc,
                        file_name=f'audeara-cover-{COVER_YEAR}-v{version.lower()}.png',
                        mime='image/png',
                        key=f'fac_dl_{version}',
                    )

st.divider()

# ── Generate the full story ────────────────────────────────────────────────────

st.markdown('#### 📰 Generate the full story')
st.caption(
    'Uses the current top-voted content to write a magazine feature article. '
    'Once generated, it appears in the Results tab for everyone to read.'
)

_fac_top = {}
if not fac_votes.empty:
    for _ck, _ in CATEGORIES:
        _cv = fac_votes[fac_votes['Category'] == _ck].copy()
        if not _cv.empty:
            _best = _cv.sort_values('Votes', ascending=False).iloc[0]
            _fac_top[_ck] = _best['Answer']

def _fac_top_or_first(col_key, col_name):
    if col_key in _fac_top:
        return _fac_top[col_key]
    vals = fac_subs[col_name].fillna('').tolist() if col_name in fac_subs.columns else []
    return next((v.strip() for v in vals if v.strip()), '')

_st_pub     = fac_subs['Publication'].fillna('').iloc[0].strip() if 'Publication' in fac_subs.columns else ''
_st_headline = _fac_top_or_first('Headline',      'Headline')
_st_partner  = _fac_top_or_first('Partner Title', 'Partner Title')
_st_story    = _fac_top_or_first('The Story',     'The Story')
_st_quote    = _fac_top_or_first('Quote',         'Quote')
_st_standout = _fac_top_or_first('Standout',      'Standout')

with st.expander('Source material for the story', expanded=False):
    st.markdown(f'**Publication:** {_st_pub or "_none_"}')
    st.markdown(f'**Headline:** {_st_headline or "_none_"}')
    st.markdown(f'**Official partner:** {("Official " + _st_partner + " Partner · Brisbane 2032") if _st_partner else "_none_"}')
    st.markdown(f'**Story context:** {_st_story or "_none_"}')
    st.markdown(f'**Quote:** {_st_quote or "_none_"}')
    st.markdown(f'**Standout:** {_st_standout or "_none_"}')

_existing_story = pull_generated_story()
if _existing_story:
    st.caption('A story has already been generated — click below to regenerate with current content.')

if st.button('📰 Generate the full story', type='primary', key='fac_gen_story'):
    with st.spinner('Writing the feature article…'):
        try:
            _new_story = generate_story(_st_pub, _st_headline, _st_story, _st_quote, _st_standout, _st_partner)
            save_generated_story(_new_story)
            st.cache_data.clear()
            st.session_state['fac_story_preview'] = _new_story
            st.toast('Story generated and published to Results tab ✓', icon='✅')
        except Exception as _e:
            st.error(f'Could not generate story. ({_e})')

_preview_story = st.session_state.get('fac_story_preview', _existing_story)
if _preview_story:
    st.markdown('**Preview:**')
    st.markdown(
        f'<div style="background:#f9f9f9;border-left:4px solid #188383;'
        f'border-radius:0 6px 6px 0;padding:20px 24px;font-size:14px;'
        f'line-height:1.75;color:#1a1a1a;white-space:pre-wrap;">'
        f'{_preview_story}</div>',
        unsafe_allow_html=True,
    )

st.divider()

# ── Vision Statement ───────────────────────────────────────────────────────────

st.markdown('#### 🔭 Vision Statement')
st.caption(
    'Generates 3 candidate vision statements from the top-voted content. '
    'They appear on the Vision Statement tab for the room to discuss. '
    'Lock in the final agreed version below.'
)

_v_candidates, _v_final = pull_vision_data()

if st.button('✨ Draft vision statement candidates', type='primary', key='fac_gen_vision'):
    with st.spinner('Drafting candidates…'):
        try:
            _mission = pull_mission_context()
            _new_candidates = generate_vision_candidates(
                _st_pub, _st_headline, _st_story, _st_quote, _st_standout, _st_partner,
                mission=_mission,
            )
            save_vision_candidates(_new_candidates)
            st.cache_data.clear()
            st.toast('Candidates published to Vision Statement tab ✓', icon='✅')
            st.rerun()
        except Exception as _e:
            st.error(f'Could not generate candidates. ({_e})')

# Always read from sheet so participant suggestions appear without a full refresh
_v_candidates, _v_final = pull_vision_data()
if _v_candidates:
    _cv = pull_vision_candidate_votes()
    _sorted_cands = sorted(_v_candidates, key=lambda c: _cv.get(c, 0), reverse=True)
    st.markdown('**Candidates now showing on the Vision Statement tab:**')
    for c in _sorted_cands:
        count = _cv.get(c, 0)
        st.markdown(
            f'**{count} vote{"s" if count != 1 else ""}** &nbsp;·&nbsp; {c}'
        )

st.markdown('')
st.markdown('**Add a candidate manually**')
st.caption('Type anything the room comes up with and add it to the list on the Vision Statement tab.')

_manual_input = st.text_input(
    'Manual candidate',
    key='fac_manual_candidate',
    label_visibility='collapsed',
    placeholder='e.g. "Audeara makes every listening moment matter, for everyone."',
)
if st.button('➕ Add to candidates', key='fac_add_candidate'):
    if _manual_input.strip():
        try:
            _current, _ = pull_vision_data()
            save_vision_candidates((_current or []) + [_manual_input.strip()])
            st.cache_data.clear()
            st.session_state.pop('fac_manual_candidate', None)
            st.toast('Candidate added to Vision Statement tab ✓', icon='✅')
            st.rerun()
        except Exception as _e:
            st.error(f'Could not add candidate. ({_e})')
    else:
        st.warning('Type a candidate first.')

st.markdown('')
st.markdown('**Lock in the final vision statement**')
st.caption('Type the agreed version here — it will appear at the top of the Vision Statement tab for everyone.')

_final_input = st.text_area(
    'Final vision statement',
    value=_v_final,
    height=80,
    key='fac_final_vision_input',
    label_visibility='collapsed',
    placeholder='Type the agreed vision statement here…',
)
if st.button('🔒 Lock in final vision statement', key='fac_lock_vision'):
    if _final_input.strip():
        try:
            save_final_vision(_final_input.strip())
            st.cache_data.clear()
            st.toast('Vision statement locked in ✓', icon='✅')
            st.rerun()
        except Exception as _e:
            st.error(f'Could not save. ({_e})')
    else:
        st.warning('Type the vision statement before locking in.')
