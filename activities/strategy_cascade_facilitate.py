"""Strategy Cascade — facilitator page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL, with_retry, _sheets
from strategy_cascade_shared import (
    GOALS, FUNCTIONS, FUNCTION_ONE_THINGS, GOAL_COLOURS, FUNC_COLOURS,
    STAGES, STAGE_LABELS,
    _ensure_cascade_tabs,
    pull_cascade_session, set_cascade_session,
    pull_commitments, pull_confidence,
)
from styles_shared import TEAM

inject_styles()

# ── Auth ───────────────────────────────────────────────────────────────────────

if 'cas_fac_auth' not in st.session_state:
    st.session_state['cas_fac_auth'] = False

if not st.session_state['cas_fac_auth']:
    st.caption('This page is for the session facilitator only.')
    pwd_input = st.text_input('Password', type='password', key='cas_fac_pwd')
    if st.button('Unlock', type='primary', key='cas_fac_unlock'):
        if pwd_input == st.secrets.get('FACILITATE_PASSWORD', ''):
            st.session_state['cas_fac_auth'] = True
            st.rerun()
        else:
            st.error('Incorrect password.')
    st.stop()

if not st.session_state.get('cascade_tabs_ready'):
    try:
        _ensure_cascade_tabs()
        st.session_state['cascade_tabs_ready'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue — some features may not save correctly. ({_e})')

st.markdown('### Facilitate — Strategy Cascade')

if st.button('🔒 Lock', key='cas_fac_lock'):
    st.session_state['cas_fac_auth'] = False
    st.rerun()

# ── Stage controls ─────────────────────────────────────────────────────────────

session   = pull_cascade_session()
stage     = session.get('stage', 'hidden')
stage_idx = STAGES.index(stage) if stage in STAGES else 0

st.markdown(
    f'<div style="background:#F5F0F5;border-radius:8px;padding:10px 16px;margin-bottom:14px;'
    f'font-size:0.84em;color:{PURPLE};font-weight:600;">'
    f'Current stage: {STAGE_LABELS.get(stage, stage)}</div>',
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    active = stage_idx == 0
    if st.button('▶  Show Cascade', use_container_width=True,
                 type='primary' if active else 'secondary', disabled=not active):
        set_cascade_session('stage', 'cascade')
        pull_cascade_session.clear()
        st.rerun()

with col2:
    active = stage_idx == 1
    if st.button('📝  Open Submissions', use_container_width=True,
                 type='primary' if active else 'secondary', disabled=not active):
        set_cascade_session('stage', 'open')
        pull_cascade_session.clear()
        st.rerun()

with col3:
    active = stage_idx == 2
    if st.button('✔  Mark Complete', use_container_width=True,
                 type='primary' if active else 'secondary', disabled=not active):
        set_cascade_session('stage', 'complete')
        pull_cascade_session.clear()
        st.rerun()

with col4:
    if st.button('↩  Reset', use_container_width=True):
        set_cascade_session('stage', 'hidden')
        pull_cascade_session.clear()
        st.rerun()

st.divider()

# ── Content preview ────────────────────────────────────────────────────────────

with st.expander('Review cascade content', expanded=False):
    st.markdown('**Function One Things**')
    for i, fn in enumerate(FUNCTIONS):
        colour = FUNC_COLOURS[i % len(FUNC_COLOURS)]
        st.markdown(
            f'<div style="border-left:4px solid {colour};background:#F8F8F8;'
            f'border-radius:0 6px 6px 0;padding:8px 14px;margin-bottom:8px;">'
            f'<div style="font-weight:700;font-size:0.84em;color:{colour};">{fn}</div>'
            f'<div style="font-size:0.8em;color:#666;margin-top:2px;">{FUNCTION_ONE_THINGS[fn]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown('**FY27 Goals**')
    for i, g in enumerate(GOALS):
        colour = GOAL_COLOURS[i % len(GOAL_COLOURS)]
        st.markdown(
            f'<div style="border-left:4px solid {colour};background:#F8F8F8;'
            f'border-radius:0 6px 6px 0;padding:8px 14px;margin-bottom:8px;">'
            f'<div style="font-weight:700;font-size:0.88em;color:{colour};">{g["title"]}</div>'
            f'<div style="font-size:0.8em;color:#666;margin-top:2px;">{g["description"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Live tracker ───────────────────────────────────────────────────────────────

@st.fragment(run_every=8)
def _live_tracker():
    pull_commitments.clear()
    pull_confidence.clear()
    df_comm = pull_commitments()
    df_conf = pull_confidence()

    submitted_comm = set(df_comm['Name'].tolist()) if not df_comm.empty else set()
    submitted_conf = set(df_conf['Name'].tolist()) if not df_conf.empty else set()
    submitted_both = submitted_comm & submitted_conf
    n_done         = len(submitted_both)

    st.markdown(
        f'<div style="font-weight:700;font-size:1em;color:{PURPLE};margin-bottom:10px;">'
        f'Submissions — {n_done} of {len(TEAM)} complete</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    for i, person in enumerate(TEAM):
        done = person in submitted_both
        bg   = '#E8F5EE' if done else '#F5F5F5'
        tc   = '#2D7D4F' if done else '#AAAAAA'
        icon = '✅' if done else '○'
        with cols[i % 4]:
            st.markdown(
                f'<div style="background:{bg};border-radius:8px;padding:8px 10px;'
                f'margin-bottom:8px;text-align:center;font-size:0.8em;color:{tc};font-weight:600;">'
                f'{icon} {person.split()[0]}</div>',
                unsafe_allow_html=True,
            )

    if n_done == 0:
        return

    st.divider()

    # ── Per-goal confidence + risks ────────────────────────────────────────────

    def _score_bg(score):
        try:
            s = int(score)
        except (TypeError, ValueError):
            return '#F5F5F5', '#AAAAAA'
        if s >= 4:
            return '#E8F5EE', '#2D7D4F'
        if s == 3:
            return '#FEF5E7', '#B7770D'
        return '#FDECEA', '#C0392B'

    for i, g in enumerate(GOALS):
        colour     = GOAL_COLOURS[i % len(GOAL_COLOURS)]
        conf_key   = f'{g["id"]}_Confidence'
        risk_key   = f'{g["id"]}_Risk'

        st.markdown(
            f'<div style="font-weight:700;font-size:0.88em;color:{colour};margin:14px 0 6px;">'
            f'{g["title"]}</div>',
            unsafe_allow_html=True,
        )

        if not df_conf.empty:
            # Confidence row
            conf_vals = [(r['Name'], r.get(conf_key, '')) for _, r in df_conf.iterrows() if r.get('Name')]
            if conf_vals:
                cells = ''
                total = 0
                count = 0
                for person, val in conf_vals:
                    bg, tc = _score_bg(val)
                    cells += (
                        f'<span style="display:inline-block;background:{bg};color:{tc};'
                        f'font-weight:700;font-size:0.78em;padding:4px 10px;border-radius:20px;'
                        f'margin:2px 4px 2px 0;">{person.split()[0]}: {val if val else "—"}</span>'
                    )
                    try:
                        total += int(val)
                        count += 1
                    except (ValueError, TypeError):
                        pass
                avg_str = f'{total/count:.1f}' if count else '—'
                bg_avg, tc_avg = _score_bg(round(total / count) if count else 3)
                st.markdown(
                    f'<div style="margin-bottom:6px;">'
                    f'<span style="font-size:0.72em;font-weight:700;color:#888;'
                    f'letter-spacing:1px;margin-right:8px;">CONFIDENCE</span>'
                    f'<span style="background:{bg_avg};color:{tc_avg};font-weight:700;'
                    f'font-size:0.78em;padding:3px 10px;border-radius:20px;margin-right:8px;">'
                    f'avg {avg_str}</span>'
                    f'{cells}</div>',
                    unsafe_allow_html=True,
                )

            # Risks
            risks = [(r['Name'], r.get(risk_key, '')) for _, r in df_conf.iterrows()
                     if r.get(risk_key, '').strip()]
            if risks:
                st.markdown(
                    f'<div style="font-size:0.72em;font-weight:700;color:#888;'
                    f'letter-spacing:1px;margin-bottom:4px;">RISKS</div>',
                    unsafe_allow_html=True,
                )
                for person, risk in risks:
                    st.markdown(
                        f'<div style="border-left:3px solid #E74C3C;background:#FEF5F5;'
                        f'border-radius:0 6px 6px 0;padding:6px 12px;margin-bottom:4px;font-size:0.82em;">'
                        f'<strong style="color:#C0392B;">{person.split()[0]}</strong>  '
                        f'<span style="color:#444;">{risk}</span></div>',
                        unsafe_allow_html=True,
                    )

    # ── Personal One Things ────────────────────────────────────────────────────

    if not df_comm.empty:
        st.divider()
        st.markdown(
            f'<div style="font-weight:700;font-size:0.92em;color:{TEAL};margin-bottom:10px;">'
            f'Personal One Things</div>',
            unsafe_allow_html=True,
        )
        for fn in FUNCTIONS:
            fn_rows = df_comm[df_comm['Function'] == fn]
            if fn_rows.empty:
                continue
            colour = FUNC_COLOURS[FUNCTIONS.index(fn) % len(FUNC_COLOURS)]
            st.markdown(
                f'<div style="font-size:0.72em;font-weight:700;color:{colour};'
                f'letter-spacing:1px;margin:10px 0 4px;">{fn.upper()}</div>',
                unsafe_allow_html=True,
            )
            for _, row in fn_rows.iterrows():
                st.markdown(
                    f'<div style="border-left:3px solid {colour};background:#F8F8F8;'
                    f'border-radius:0 6px 6px 0;padding:8px 12px;margin-bottom:6px;font-size:0.82em;">'
                    f'<strong style="color:#444;">{row["Name"].split()[0]}</strong>  '
                    f'<span style="color:#666;">{row["Commitment"]}</span></div>',
                    unsafe_allow_html=True,
                )

_live_tracker()
