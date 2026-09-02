"""Strategy Cascade — facilitator page.

Stage controls, live submission tracker, confidence heatmap, and results summary.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL
from strategy_cascade_shared import (
    GOALS, FUNCTIONS, FUNCTION_ONE_THINGS, GOAL_COLOURS, STAGES, STAGE_LABELS,
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
    _ensure_cascade_tabs()
    st.session_state['cascade_tabs_ready'] = True

st.markdown('### Facilitate — Strategy Cascade')

if st.button('🔒 Lock', key='cas_fac_lock'):
    st.session_state['cas_fac_auth'] = False
    st.rerun()

# ── Stage controls ─────────────────────────────────────────────────────────────

session = pull_cascade_session()
stage   = session.get('stage', 'hidden')

st.markdown(
    f'<div style="background:#F5F0F5;border-radius:8px;padding:10px 16px;margin-bottom:14px;'
    f'font-size:0.84em;color:{PURPLE};font-weight:600;">'
    f'Current stage: {STAGE_LABELS.get(stage, stage)}</div>',
    unsafe_allow_html=True,
)

stage_idx = STAGES.index(stage) if stage in STAGES else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    if stage_idx < 1:
        if st.button('▶  Reveal Goals', use_container_width=True, type='primary'):
            set_cascade_session('stage', 'goals')
            pull_cascade_session.clear()
            st.rerun()
    else:
        st.button('▶  Reveal Goals', use_container_width=True, disabled=True)

with col2:
    if stage_idx == 1:
        if st.button('▶  Reveal Function One Things', use_container_width=True, type='primary'):
            set_cascade_session('stage', 'functions')
            pull_cascade_session.clear()
            st.rerun()
    else:
        st.button('▶  Reveal Function One Things', use_container_width=True, disabled=True)

with col3:
    if stage_idx == 2:
        if st.button('✔  Mark Complete', use_container_width=True, type='primary'):
            set_cascade_session('stage', 'complete')
            pull_cascade_session.clear()
            st.rerun()
    else:
        st.button('✔  Mark Complete', use_container_width=True, disabled=True)

with col4:
    if st.button('↩  Reset', use_container_width=True):
        set_cascade_session('stage', 'hidden')
        pull_cascade_session.clear()
        st.rerun()

st.divider()

# ── Content preview ────────────────────────────────────────────────────────────

with st.expander('Review goals and function One Things', expanded=False):
    st.markdown('**FY27 Goals**')
    for i, g in enumerate(GOALS):
        colour = GOAL_COLOURS[i % len(GOAL_COLOURS)]
        st.markdown(
            f'<div style="border-left:4px solid {colour};padding:8px 14px;'
            f'border-radius:0 6px 6px 0;background:#F8F8F8;margin-bottom:8px;">'
            f'<div style="font-weight:700;font-size:0.88em;color:{colour};">{g["title"]}</div>'
            f'<div style="font-size:0.8em;color:#666;margin-top:2px;">{g["description"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown('')
    st.markdown('**Function One Things**')
    for j, fn in enumerate(FUNCTIONS):
        colour = GOAL_COLOURS[j % len(GOAL_COLOURS)]
        st.markdown(
            f'<div style="border-left:4px solid {colour};padding:8px 14px;'
            f'border-radius:0 6px 6px 0;background:#F8F8F8;margin-bottom:8px;">'
            f'<div style="font-weight:700;font-size:0.84em;color:{colour};">{fn}</div>'
            f'<div style="font-size:0.8em;color:#666;margin-top:2px;">{FUNCTION_ONE_THINGS[fn]}</div>'
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
    n_done = len(submitted_both)

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

    # ── Confidence heatmap ─────────────────────────────────────────────────────

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

    st.markdown(
        f'<div style="font-weight:700;font-size:0.92em;color:{PURPLE};margin-bottom:8px;">'
        f'Confidence by goal</div>',
        unsafe_allow_html=True,
    )

    # Header row
    def _th(title):
        label = (title[:22] + '…') if len(title) > 22 else title
        return (
            f'<td style="font-size:0.72em;font-weight:700;color:#666;'
            f'padding:5px 8px;text-align:center;background:#F0F0F0;">{label}</td>'
        )
    header_cells = ''.join(_th(g['title']) for g in GOALS)

    rows_html = ''
    if not df_conf.empty:
        for _, row in df_conf.iterrows():
            person = row.get('Name', '')
            if not person:
                continue
            name_cell = (
                f'<td style="font-size:0.75em;font-weight:600;color:#444;'
                f'padding:5px 10px;white-space:nowrap;">{person.split()[0]}</td>'
            )
            score_cells = ''
            for g in GOALS:
                col_key = f'{g["id"]}_Confidence'
                raw     = row.get(col_key, '')
                bg, tc  = _score_bg(raw)
                score_cells += (
                    f'<td style="text-align:center;padding:5px 8px;background:{bg};'
                    f'color:{tc};font-weight:700;font-size:0.82em;">{raw if raw else "—"}</td>'
                )
            rows_html += f'<tr>{name_cell}{score_cells}</tr>'

    # Avg row
    avg_cells = ''
    if not df_conf.empty:
        for g in GOALS:
            col_key = f'{g["id"]}_Confidence'
            vals    = [v for v in df_conf[col_key].tolist() if str(v).strip().isdigit()]
            if vals:
                avg    = sum(int(v) for v in vals) / len(vals)
                bg, tc = _score_bg(round(avg))
                avg_cells += (
                    f'<td style="text-align:center;padding:5px 8px;background:{bg};'
                    f'color:{tc};font-weight:700;font-size:0.82em;border-top:2px solid #CCC;">'
                    f'{avg:.1f}</td>'
                )
            else:
                avg_cells += '<td style="text-align:center;padding:5px 8px;">—</td>'
    else:
        avg_cells = ''.join(f'<td>—</td>' for _ in GOALS)

    table = (
        f'<div style="overflow-x:auto;margin-bottom:16px;">'
        f'<table style="border-collapse:collapse;width:100%;max-width:720px;">'
        f'<thead><tr>'
        f'<td style="padding:5px 10px;background:#F0F0F0;font-size:0.72em;font-weight:700;color:#666;"></td>'
        + header_cells +
        f'</tr></thead>'
        f'<tbody>{rows_html}'
        f'<tr><td style="font-size:0.72em;font-weight:700;color:#666;padding:5px 10px;'
        f'background:#F0F0F0;border-top:2px solid #CCC;">Avg</td>{avg_cells}</tr>'
        f'</tbody></table></div>'
    )
    st.markdown(table, unsafe_allow_html=True)

    # ── Risks ──────────────────────────────────────────────────────────────────

    risks = [(r.get('Name', ''), r.get('Risk', '')) for _, r in df_conf.iterrows()
             if r.get('Risk', '').strip()]
    if risks:
        st.markdown(
            f'<div style="font-weight:700;font-size:0.92em;color:{PURPLE};margin-bottom:8px;">'
            f'Risks surfaced</div>',
            unsafe_allow_html=True,
        )
        for person, risk in risks:
            st.markdown(
                f'<div style="border-left:3px solid #E74C3C;background:#FEF5F5;'
                f'border-radius:0 6px 6px 0;padding:8px 12px;margin-bottom:6px;font-size:0.82em;">'
                f'<strong style="color:#C0392B;">{person.split()[0]}</strong>  '
                f'<span style="color:#444;">{risk}</span></div>',
                unsafe_allow_html=True,
            )

    # ── Commitments ────────────────────────────────────────────────────────────

    if not df_comm.empty:
        st.markdown(
            f'<div style="font-weight:700;font-size:0.92em;color:{TEAL};margin-bottom:8px;">'
            f'Personal commitments</div>',
            unsafe_allow_html=True,
        )
        for fn in FUNCTIONS:
            fn_rows = df_comm[df_comm['Function'] == fn]
            if fn_rows.empty:
                continue
            colour = GOAL_COLOURS[FUNCTIONS.index(fn) % len(GOAL_COLOURS)]
            st.markdown(
                f'<div style="font-size:0.78em;font-weight:700;color:{colour};'
                f'letter-spacing:1px;margin:12px 0 4px;">{fn.upper()}</div>',
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
