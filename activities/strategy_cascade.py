"""Strategy Cascade — participant page.

Shows the FY27 goals and function One Things as the facilitator reveals them,
then collects personal commitments, per-goal confidence, and a risk statement.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL
from strategy_cascade_shared import (
    GOALS, FUNCTIONS, FUNCTION_ONE_THINGS, GOAL_COLOURS,
    STAGE_LABELS,
    _ensure_cascade_tabs,
    pull_cascade_session, pull_commitments, pull_confidence,
    save_commitment, save_confidence,
)
from styles_shared import TEAM

inject_styles()
_ensure_cascade_tabs()

# ── Helpers ────────────────────────────────────────────────────────────────────

def _confidence_colour(score):
    try:
        s = int(score)
    except (TypeError, ValueError):
        return '#CCCCCC'
    if s >= 4:
        return '#3EAA6D'
    if s == 3:
        return '#F5A623'
    return '#E74C3C'

def _cascade_levels_html(stage):
    """Vertical cascade visual showing revealed levels."""

    def _tier(label, sublabel, colour, active, items=None):
        if active:
            bg, tc, border = colour, 'white', 'none'
        else:
            bg, tc, border = '#F2F2F2', '#AAAAAA', '1px solid #DDDDDD'
        items_html = ''
        if active and items:
            items_html = ''.join(
                f'<div style="font-size:0.78em;line-height:1.6;padding:4px 0;'
                f'border-top:1px solid rgba(255,255,255,0.3);margin-top:5px;color:rgba(255,255,255,0.92);">{it}</div>'
                for it in items
            )
        return (
            f'<div style="background:{bg};border:{border};border-radius:10px;padding:14px 18px;'
            f'margin-bottom:6px;">'
            f'<div style="font-size:0.68em;font-weight:700;letter-spacing:2px;color:{tc};">{label}</div>'
            f'<div style="font-size:0.9em;font-weight:600;color:{tc};margin-top:3px;">{sublabel}</div>'
            f'{items_html}</div>'
        )

    def _arrow():
        return '<div style="text-align:center;font-size:1.1em;color:#CCCCCC;margin:2px 0;">↓</div>'

    goals_active    = stage in ('goals', 'functions', 'complete')
    func_active     = stage in ('functions', 'complete')
    commit_active   = stage == 'complete'

    goals_items = [f'{g["title"]}' for g in GOALS] if goals_active else None
    func_items  = [f'{fn}: {FUNCTION_ONE_THINGS[fn]}' for fn in FUNCTIONS] if func_active else None

    html = (
        f'<div style="max-width:560px;">'
        + _tier('MISSION + VISION', 'Where we come from and where we\'re going', '#50144B', True)
        + _arrow()
        + _tier('FY27 GOALS', 'What we need to achieve this year', GOAL_COLOURS[0], goals_active, goals_items)
        + _arrow()
        + _tier('FUNCTION ONE THINGS', 'The single priority each team must nail', GOAL_COLOURS[1], func_active, func_items)
        + _arrow()
        + _tier('PERSONAL COMMITMENTS', 'What you will do differently to make it happen', GOAL_COLOURS[3], commit_active)
        + '</div>'
    )
    return html

# ── Page ──────────────────────────────────────────────────────────────────────

st.markdown('### Strategy Cascade')
st.markdown(
    f'<div class="activity-card">'
    f'James will walk through the FY27 strategy live in the room. This page shows the cascade as it unfolds '
    f'and opens up for your input once the full picture is on screen. Stay on this page.'
    f'</div>',
    unsafe_allow_html=True,
)

name = st.selectbox('Your name', [''] + TEAM, key='cascade_name')
if not name:
    st.stop()

# ── Live activity fragment ─────────────────────────────────────────────────────

@st.fragment(run_every=5)
def _cascade_live(name):
    pull_cascade_session.clear()
    session = pull_cascade_session()
    stage   = session.get('stage', 'hidden')

    # ── Waiting state ──────────────────────────────────────────────────────────
    if stage == 'hidden':
        st.markdown('')
        st.markdown(
            f'<div style="background:#F5F5F5;border-radius:10px;padding:24px;text-align:center;'
            f'color:#AAAAAA;font-size:0.9em;max-width:560px;">'
            f'⏳  The facilitator will start the cascade shortly.<br>'
            f'<span style="font-size:0.82em;">Stay on this page.</span></div>',
            unsafe_allow_html=True,
        )
        return

    # ── Cascade visual ─────────────────────────────────────────────────────────
    st.markdown(_cascade_levels_html(stage), unsafe_allow_html=True)

    if stage == 'goals':
        st.markdown(
            f'<div style="background:#F7F0F7;border-radius:8px;padding:14px 16px;'
            f'max-width:560px;font-size:0.84em;color:#444;margin-top:8px;">'
            f'<strong>James is walking through the FY27 goals.</strong> The function priorities are coming next.'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Submission form — stage 'functions' or 'complete' ─────────────────────
    if stage not in ('functions', 'complete'):
        return

    pull_commitments.clear()
    pull_confidence.clear()
    df_comm = pull_commitments()
    df_conf = pull_confidence()

    has_commitment = name in df_comm['Name'].values if not df_comm.empty else False
    has_confidence = name in df_conf['Name'].values if not df_conf.empty else False
    already_done   = has_commitment and has_confidence

    if already_done and not st.session_state.get(f'cascade_edit_{name}', False):
        # Show submitted state with edit option
        comm_row  = df_comm[df_comm['Name'] == name].iloc[0]
        conf_row  = df_conf[df_conf['Name'] == name].iloc[0]

        st.markdown(
            f'<div style="border-left:4px solid #3EAA6D;background:#E8F5EE;'
            f'border-radius:0 8px 8px 0;padding:14px 16px;margin-top:12px;max-width:560px;">'
            f'<div style="font-weight:700;color:#2D7D4F;margin-bottom:6px;">✅  Submitted</div>'
            f'<div style="font-size:0.84em;color:#444;margin-bottom:4px;">'
            f'<strong>Function:</strong> {comm_row["Function"]}</div>'
            f'<div style="font-size:0.84em;color:#444;margin-bottom:4px;">'
            f'<strong>Commitment:</strong> {comm_row["Commitment"]}</div>'
            f'<div style="font-size:0.84em;color:#444;margin-bottom:4px;">'
            + ''.join(
                '<strong>' + g['title'] + ':</strong> ' +
                str(conf_row.get(g['id'] + '_Confidence', '—')) + '/5   '
                for g in GOALS
            )
            + '</div>'
            f'<div style="font-size:0.84em;color:#444;">'
            f'<strong>Risk:</strong> {conf_row.get("Risk", "")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button('Edit my response', key=f'cascade_edit_btn_{name}'):
            st.session_state[f'cascade_edit_{name}'] = True
            st.rerun()
        return

    st.markdown('')
    st.markdown(
        f'<div style="font-weight:700;color:{PURPLE};font-size:1em;margin-bottom:4px;">'
        f'Your response</div>',
        unsafe_allow_html=True,
    )

    # Function
    fn_default = ''
    if has_commitment:
        fn_default = df_comm[df_comm['Name'] == name].iloc[0].get('Function', '')
    fn_options = [''] + FUNCTIONS
    fn_idx     = fn_options.index(fn_default) if fn_default in fn_options else 0
    function   = st.selectbox(
        'Your function / team',
        fn_options,
        index=fn_idx,
        key=f'cascade_fn_{name}',
    )

    if function:
        one_thing = FUNCTION_ONE_THINGS.get(function, '')
        st.markdown(
            f'<div style="background:#F0F8F8;border-left:3px solid {TEAL};'
            f'border-radius:0 8px 8px 0;padding:10px 14px;margin:8px 0 14px;font-size:0.84em;color:#444;">'
            f'<strong>{function} One Thing:</strong> {one_thing}</div>',
            unsafe_allow_html=True,
        )

    # Personal commitment
    comm_default = ''
    if has_commitment:
        comm_default = df_comm[df_comm['Name'] == name].iloc[0].get('Commitment', '')

    commitment = st.text_area(
        'What\'s the one thing you personally need to do differently to make this happen?',
        value=comm_default,
        height=100,
        placeholder='Be specific — what will you start, stop, or do more of?',
        key=f'cascade_comm_{name}',
    )

    # Confidence per goal
    st.markdown(
        f'<div style="font-weight:600;color:#444;margin-top:14px;margin-bottom:6px;font-size:0.88em;">'
        f'Confidence check — how confident are you that the team can execute each goal?</div>',
        unsafe_allow_html=True,
    )

    confidence = {}
    for g in GOALS:
        col_key = f'{g["id"]}_Confidence'
        default = 3
        if has_confidence:
            try:
                default = int(df_conf[df_conf['Name'] == name].iloc[0].get(col_key, 3))
            except (ValueError, TypeError):
                default = 3
        confidence[g['id']] = st.select_slider(
            g['title'],
            options=[1, 2, 3, 4, 5],
            value=default,
            format_func=lambda x: {1: '1 — Low', 2: '2', 3: '3 — Neutral', 4: '4', 5: '5 — High'}[x],
            key=f'cascade_conf_{name}_{g["id"]}',
        )

    # Risk
    risk_default = ''
    if has_confidence:
        risk_default = df_conf[df_conf['Name'] == name].iloc[0].get('Risk', '')

    risk = st.text_input(
        'The most likely thing to derail our FY27 execution is...',
        value=risk_default,
        placeholder='Keep it to one sentence',
        key=f'cascade_risk_{name}',
    )

    st.markdown('')
    if st.button('Submit', type='primary', key=f'cascade_submit_{name}', use_container_width=True):
        if not function:
            st.warning('Please select your function.')
            return
        if not commitment.strip():
            st.warning('Please add your personal commitment.')
            return
        save_commitment(name, function, commitment.strip())
        save_confidence(name, confidence, risk.strip())
        pull_commitments.clear()
        pull_confidence.clear()
        st.session_state[f'cascade_edit_{name}'] = False
        st.success('Saved. Thank you.')
        st.rerun()

_cascade_live(name)
