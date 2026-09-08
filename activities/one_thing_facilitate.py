"""The One Thing — facilitator page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL, with_retry, _clear_sheets
from one_thing_shared import (
    DEPARTMENTS, DEPARTMENT_HEADS,
    ONE_THING_STAGES, ONE_THING_STAGE_LABELS,
    _ensure_one_thing_tabs,
    pull_one_thing_session, set_one_thing_session,
    pull_one_thing_drafts, save_one_thing_draft,
    pull_one_thing_suggestions,
    pull_one_thing_winners, save_one_thing_winner,
)
from strategy_cascade_shared import pull_commitments
from styles_shared import TEAM

inject_styles()

# ── Auth ───────────────────────────────────────────────────────────────────────

if 'ot_fac_auth' not in st.session_state:
    st.session_state['ot_fac_auth'] = False

if not st.session_state['ot_fac_auth']:
    st.caption('This page is for the session facilitator only.')
    pwd = st.text_input('Password', type='password', key='ot_fac_pwd')
    if st.button('Unlock', type='primary', key='ot_fac_unlock'):
        if pwd == st.secrets.get('FACILITATE_PASSWORD', ''):
            st.session_state['ot_fac_auth'] = True
            st.rerun()
        else:
            st.error('Incorrect password.')
    st.stop()

if not st.session_state.get('_ot_fac_tabs_ready'):
    try:
        with_retry(_ensure_one_thing_tabs, on_retry=_clear_sheets)
        st.session_state['_ot_fac_tabs_ready'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue. ({_e})')

st.markdown('### 🎛️ Facilitate — The One Thing')

if st.button('🔒 Lock', key='ot_fac_lock'):
    st.session_state['ot_fac_auth'] = False
    st.rerun()

# ── Stage controls ─────────────────────────────────────────────────────────────

session   = pull_one_thing_session()
stage     = session.get('stage', 'hidden')

st.markdown(
    f'<div style="background:#F5F0F5;border-radius:8px;padding:10px 16px;margin-bottom:14px;'
    f'font-size:0.84em;color:{PURPLE};font-weight:600;">'
    f'Current stage: {ONE_THING_STAGE_LABELS.get(stage, stage)}</div>',
    unsafe_allow_html=True,
)

_stage_cols = st.columns(len(ONE_THING_STAGES) + 1)

for i, s in enumerate(ONE_THING_STAGES):
    with _stage_cols[i]:
        label = ONE_THING_STAGE_LABELS[s].split()[0] if s != 'hidden' else 'Hidden'
        if st.button(label, use_container_width=True,
                     type='primary' if stage == s else 'secondary',
                     key=f'ot_stage_{s}'):
            set_one_thing_session('stage', s)
            pull_one_thing_session.clear()
            st.rerun()

with _stage_cols[-1]:
    if st.button('↺ Refresh', use_container_width=True, key='ot_fac_refresh'):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ── Department draft editor ────────────────────────────────────────────────────

st.markdown(
    f'<div style="font-weight:700;font-size:1em;color:{PURPLE};margin-bottom:4px;">Department draft One Things</div>',
    unsafe_allow_html=True,
)
st.caption('Enter James\'s draft for each department. These appear on participants\' screens when the Departmental stage opens.')

drafts = pull_one_thing_drafts()

for dept in DEPARTMENTS:
    current_draft = drafts.get(dept, '')
    head          = DEPARTMENT_HEADS.get(dept, '')
    col_a, col_b  = st.columns([9, 2])
    with col_a:
        new_draft = st.text_area(
            dept,
            value=current_draft,
            height=68,
            key=f'ot_draft_{dept}',
            placeholder=f'Draft One Thing for {dept}…',
        )
    with col_b:
        st.markdown('<br>', unsafe_allow_html=True)
        st.caption(f'Head: {head if head else "—"}')
        if st.button('Save', key=f'ot_save_draft_{dept}', use_container_width=True):
            if new_draft.strip():
                try:
                    save_one_thing_draft(dept, new_draft.strip())
                    st.toast(f'{dept} draft saved ✓', icon='✅')
                    st.rerun()
                except Exception as _e:
                    st.error(f'Could not save. ({_e})')
            else:
                st.warning('Type a draft first.')

st.divider()

# ── Live suggestions + winner status ─────────────────────────────────────────

st.markdown(
    f'<div style="font-weight:700;font-size:1em;color:{PURPLE};margin-bottom:14px;">Live suggestions and winner status</div>',
    unsafe_allow_html=True,
)

@st.fragment(run_every=12)
def _suggestions_view():
    all_suggs = pull_one_thing_suggestions()
    winners   = pull_one_thing_winners()
    drafts_v  = pull_one_thing_drafts()

    for dept in DEPARTMENTS:
        winner = winners.get(dept, '')
        head   = DEPARTMENT_HEADS.get(dept, '')

        bc = '#3EAA6D' if winner else PURPLE
        bg = '#E8F5EE' if winner else '#F7F0F7'
        status_label = f'✅ Locked by {head}' if winner else '⏳ Awaiting agreement'

        st.markdown(
            f'<div style="border-left:4px solid {bc};background:{bg};'
            f'border-radius:0 8px 8px 0;padding:10px 16px;margin-bottom:6px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
            f'<div style="font-weight:700;font-size:0.88em;color:{bc};">{dept}</div>'
            f'<div style="font-size:0.72em;color:{bc};opacity:0.85;">{status_label}</div>'
            f'</div>'
            + (f'<div style="font-size:0.84em;color:#1a1a1a;margin-top:6px;line-height:1.5;">{winner}</div>' if winner else '')
            + '</div>',
            unsafe_allow_html=True,
        )

        dept_suggs = all_suggs[all_suggs['Department'] == dept] if not all_suggs.empty else all_suggs
        if not dept_suggs.empty:
            for _, row in dept_suggs.iterrows():
                st.markdown(
                    f'<div style="border-left:2px solid #CCCCCC;padding:6px 14px;'
                    f'margin:4px 0 4px 8px;font-size:0.8em;color:#555;">'
                    f'{row["Suggestion"]}</div>',
                    unsafe_allow_html=True,
                )
        elif not winner:
            st.caption('No suggestions yet.')

        # Facilitator winner override (if not yet locked, or to change it)
        with st.expander(f'Override winner for {dept}', expanded=False):
            override_val = winner or drafts_v.get(dept, '')
            override_input = st.text_area(
                'Winner text',
                value=override_val,
                height=68,
                key=f'ot_override_{dept}',
                label_visibility='collapsed',
            )
            if st.button(f'Save winner — {dept}', key=f'ot_override_btn_{dept}'):
                if override_input.strip():
                    try:
                        save_one_thing_winner(dept, override_input.strip(), 'Facilitator')
                        st.cache_data.clear()
                        st.toast(f'Winner saved for {dept} ✓', icon='✅')
                        st.rerun()
                    except Exception as _e:
                        st.error(f'Could not save. ({_e})')
                else:
                    st.warning('Type the winner text first.')

        st.markdown('')

_suggestions_view()

st.divider()

# ── Personal One Things tracker ───────────────────────────────────────────────

st.markdown(
    f'<div style="font-weight:700;font-size:1em;color:{TEAL};margin-bottom:14px;">Personal One Things</div>',
    unsafe_allow_html=True,
)

@st.fragment(run_every=12)
def _personal_tracker():
    df_comm = pull_commitments()
    submitted = set(df_comm['Name'].tolist()) if not df_comm.empty else set()
    n_done    = len(submitted)

    st.markdown(
        f'<div style="font-size:0.84em;color:#888;margin-bottom:10px;">'
        f'{n_done} of {len(TEAM)} submitted</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    for i, person in enumerate(TEAM):
        done = person in submitted
        bg   = '#E8F5EE' if done else '#F5F5F5'
        tc   = '#2D7D4F' if done else '#AAAAAA'
        with cols[i % 4]:
            st.markdown(
                f'<div style="background:{bg};border-radius:8px;padding:8px 10px;'
                f'margin-bottom:8px;text-align:center;font-size:0.8em;color:{tc};font-weight:600;">'
                f'{"✅" if done else "○"} {person}</div>',
                unsafe_allow_html=True,
            )

    if df_comm.empty:
        return

    st.markdown('')
    _, fn_live = pull_one_thing_drafts(), None
    from strategy_cascade_shared import pull_cascade_content
    _, fn_live = pull_cascade_content()

    for dept in DEPARTMENTS:
        dept_rows = df_comm[df_comm['Function'] == dept]
        if dept_rows.empty:
            continue
        items = ''.join(
            f'<div style="padding:7px 0;border-bottom:1px solid #F0F0F0;font-size:0.84em;">'
            f'<strong style="color:#444;min-width:100px;display:inline-block;">{row["Name"]}</strong>'
            f'<span style="color:#555;">{row["Commitment"]}</span>'
            f'</div>'
            for _, row in dept_rows.iterrows()
        )
        st.markdown(
            f'<div style="border-left:4px solid {TEAL};background:#F8F8F8;'
            f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:10px;">'
            f'<div style="font-size:0.7em;font-weight:700;color:{TEAL};letter-spacing:1px;margin-bottom:8px;">{dept.upper()}</div>'
            f'{items}</div>',
            unsafe_allow_html=True,
        )

_personal_tracker()
