"""Strategy Cascade — participant page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL
from strategy_cascade_shared import (
    GOALS, FUNCTIONS, FUNCTION_ONE_THINGS,
    _ensure_cascade_tabs,
    pull_cascade_session, pull_cascade_context,
    pull_commitments, pull_confidence,
    save_commitment, save_confidence,
)
from styles_shared import TEAM

inject_styles()

# ── Page header ───────────────────────────────────────────────────────────────

st.markdown('### Strategy Cascade')
st.markdown(
    f'<div class="activity-card">'
    f'James will walk through the FY27 strategy cascade. This page updates live '
    f'as each level is revealed. Stay on this page — the form will open once he\'s '
    f'finished walking through.'
    f'</div>',
    unsafe_allow_html=True,
)

name = st.selectbox('Your name', [''] + TEAM, key='cascade_name')
if not name:
    st.stop()

# ── Cascade visual helpers ─────────────────────────────────────────────────────

def _mission_vision_html(mission_top, vision):
    """Mission and Vision side by side."""
    if mission_top:
        m_body = (
            f'We help <strong>{mission_top.get("Who", "…")}</strong> '
            f'do <strong>{mission_top.get("What", "…")}</strong> '
            f'by <strong>{mission_top.get("How", "…")}</strong>, '
            f'so they can <strong>{mission_top.get("Makes Possible", "…")}</strong>.'
        )
    else:
        m_body = '<em style="color:white;">Mission coming from the morning session.</em>'

    v_body = (
        f'<em>"{vision}"</em>' if vision
        else '<em style="color:white;">Vision coming from the morning session.</em>'
    )

    return (
        f'<div style="display:flex;gap:12px;margin-bottom:16px;">'

        f'<div style="flex:1;background:#781E73;border-radius:10px;padding:16px 18px;">'
        f'<div style="font-size:0.65em;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,0.7);margin-bottom:6px;">MISSION</div>'
        f'<div style="font-size:0.84em;color:white;line-height:1.6;">{m_body}</div>'
        f'</div>'

        f'<div style="flex:1;background:#188383;border-radius:10px;padding:16px 18px;">'
        f'<div style="font-size:0.65em;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,0.7);margin-bottom:6px;">VISION</div>'
        f'<div style="font-size:0.84em;color:white;line-height:1.6;">{v_body}</div>'
        f'</div>'

        f'</div>'
    )

def _function_one_things_html():
    """Function One Things in a 2-column grid."""
    fns = list(FUNCTION_ONE_THINGS.items())

    # Pair into rows of 2
    rows_html = ''
    for i in range(0, len(fns), 2):
        pair = fns[i:i + 2]
        row  = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">'
        for fn, one_thing in pair:
            row += (
                f'<div style="background:#F8F8F8;border-left:4px solid {TEAL};'
                f'border-radius:0 8px 8px 0;padding:12px 14px;">'
                f'<div style="font-size:0.72em;font-weight:700;color:{TEAL};margin-bottom:4px;">{fn.upper()}</div>'
                f'<div style="font-size:0.82em;color:#444;line-height:1.5;">{one_thing}</div>'
                f'</div>'
            )
        if len(pair) == 1:
            row += '<div></div>'
        row += '</div>'
        rows_html += row

    return (
        f'<div style="margin-bottom:16px;">'
        f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;color:#888;margin-bottom:10px;">FUNCTION ONE THINGS</div>'
        f'{rows_html}'
        f'</div>'
    )

def _goals_html():
    """Goals list as compact reference cards."""
    html = (
        f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;color:#888;margin-bottom:10px;">FY27 GOALS</div>'
    )
    for g in GOALS:
        html += (
            f'<div style="border-left:4px solid {PURPLE};background:#F8F8F8;'
            f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:8px;">'
            f'<div style="font-weight:700;font-size:0.88em;color:{PURPLE};">{g["title"]}</div>'
            f'<div style="font-size:0.78em;color:#666;margin-top:2px;">{g["description"]}</div>'
            f'</div>'
        )
    return f'<div style="margin-bottom:8px;">{html}</div>'

# ── Live fragment ─────────────────────────────────────────────────────────────

@st.fragment(run_every=5)
def _cascade_live(name):
    if not st.session_state.get('cascade_tabs_ready'):
        _ensure_cascade_tabs()
        st.session_state['cascade_tabs_ready'] = True

    pull_cascade_session.clear()
    session = pull_cascade_session()
    stage   = session.get('stage', 'hidden')

    # ── Waiting ────────────────────────────────────────────────────────────────
    if stage == 'hidden':
        st.markdown(
            f'<div style="background:#F5F5F5;border-radius:10px;padding:28px;'
            f'text-align:center;color:#AAAAAA;font-size:0.9em;margin-top:8px;">'
            f'⏳  James is about to walk through the strategy cascade.<br>'
            f'<span style="font-size:0.82em;">Stay on this page.</span></div>',
            unsafe_allow_html=True,
        )
        return

    # ── Pull context (Mission + Vision) ────────────────────────────────────────
    mission_top, vision = pull_cascade_context()

    # ── Cascade read-only view ─────────────────────────────────────────────────
    st.markdown(_mission_vision_html(mission_top, vision), unsafe_allow_html=True)
    st.markdown(_function_one_things_html(), unsafe_allow_html=True)
    st.markdown(_goals_html(), unsafe_allow_html=True)

    if stage == 'cascade':
        st.markdown(
            f'<div style="background:#F7F0F7;border-radius:8px;padding:14px 16px;'
            f'font-size:0.84em;color:#444;">'
            f'<strong>James is walking through the cascade.</strong> '
            f'The form will open once he\'s finished.'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    if stage == 'complete':
        st.markdown(
            f'<div style="background:#E8F5EE;border-radius:8px;padding:14px 16px;'
            f'font-size:0.84em;color:#2D7D4F;font-weight:600;">'
            f'✅  Session complete. Thank you.'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Submission form (stage == 'open') ─────────────────────────────────────
    pull_commitments.clear()
    pull_confidence.clear()
    df_comm = pull_commitments()
    df_conf = pull_confidence()

    has_commitment = name in df_comm['Name'].values if not df_comm.empty else False
    has_confidence = name in df_conf['Name'].values if not df_conf.empty else False
    already_done   = has_commitment and has_confidence

    if already_done and not st.session_state.get(f'cascade_edit_{name}'):
        comm_row = df_comm[df_comm['Name'] == name].iloc[0]
        conf_row = df_conf[df_conf['Name'] == name].iloc[0]

        st.markdown(
            f'<div style="border-left:4px solid #3EAA6D;background:#E8F5EE;'
            f'border-radius:0 8px 8px 0;padding:14px 16px;margin-top:4px;">'
            f'<div style="font-weight:700;color:#2D7D4F;margin-bottom:8px;">✅  Submitted</div>'
            f'<div style="font-size:0.84em;color:#444;margin-bottom:4px;">'
            f'<strong>Function:</strong> {comm_row["Function"]}</div>'
            f'<div style="font-size:0.84em;color:#444;margin-bottom:8px;">'
            f'<strong>Personal One Thing:</strong> {comm_row["Commitment"]}</div>'
            + ''.join(
                f'<div style="font-size:0.84em;color:#444;margin-bottom:2px;">'
                f'<strong>{g["title"]}:</strong> '
                + str(conf_row.get(g['id'] + '_Confidence', '—')) + '/5'
                + (f' — {conf_row.get(g["id"] + "_Risk", "")}' if conf_row.get(g['id'] + '_Risk', '') else '')
                + '</div>'
                for g in GOALS
            )
            + f'</div>',
            unsafe_allow_html=True,
        )
        if st.button('Edit my response', key=f'cascade_edit_btn_{name}'):
            st.session_state[f'cascade_edit_{name}'] = True
            st.rerun()
        return

    st.divider()
    st.markdown(
        f'<div style="font-weight:700;color:{PURPLE};font-size:1em;margin-bottom:14px;">'
        f'Your response</div>',
        unsafe_allow_html=True,
    )

    # Per-goal confidence + risk
    confidence = {}
    risks      = {}

    for g in GOALS:
        conf_key = f'{g["id"]}_Confidence'
        risk_key = f'{g["id"]}_Risk'
        default_conf = 3
        default_risk = ''
        if has_confidence:
            try:
                default_conf = int(df_conf[df_conf['Name'] == name].iloc[0].get(conf_key, 3))
            except (ValueError, TypeError):
                default_conf = 3
            default_risk = df_conf[df_conf['Name'] == name].iloc[0].get(risk_key, '')

        st.markdown(
            f'<div style="border-left:4px solid {PURPLE};padding:2px 0 2px 12px;margin-bottom:4px;">'
            f'<div style="font-weight:700;font-size:0.9em;color:{PURPLE};">{g["title"]}</div>'
            f'<div style="font-size:0.78em;color:#666;">{g["description"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        confidence[g['id']] = st.select_slider(
            'Confidence',
            options=[1, 2, 3, 4, 5],
            value=default_conf,
            format_func=lambda x: {1: '1 — Low', 2: '2', 3: '3 — Neutral', 4: '4', 5: '5 — High'}[x],
            key=f'conf_{name}_{g["id"]}',
        )
        risks[g['id']] = st.text_input(
            'Most likely thing to derail this goal',
            value=default_risk,
            placeholder='One sentence',
            key=f'risk_{name}_{g["id"]}',
        )
        st.markdown('')

    # Personal One Thing
    st.markdown(
        f'<div style="font-weight:700;color:{TEAL};font-size:0.92em;margin-bottom:6px;">'
        f'Your personal One Thing</div>',
        unsafe_allow_html=True,
    )

    fn_default  = ''
    if has_commitment:
        fn_default = df_comm[df_comm['Name'] == name].iloc[0].get('Function', '')
    fn_options  = [''] + FUNCTIONS
    fn_idx      = fn_options.index(fn_default) if fn_default in fn_options else 0
    function    = st.selectbox('Your function / team', fn_options, index=fn_idx,
                               key=f'cascade_fn_{name}')

    if function:
        one_thing = FUNCTION_ONE_THINGS.get(function, '')
        st.markdown(
            f'<div style="background:#F0F8F8;border-left:3px solid {TEAL};'
            f'border-radius:0 8px 8px 0;padding:10px 14px;margin:6px 0 10px;'
            f'font-size:0.82em;color:#444;">'
            f'<strong>{function} One Thing:</strong> {one_thing}</div>',
            unsafe_allow_html=True,
        )

    comm_default = ''
    if has_commitment:
        comm_default = df_comm[df_comm['Name'] == name].iloc[0].get('Commitment', '')

    commitment = st.text_area(
        'What one action, if you committed to it, would have the most impact on your function\'s goal?',
        value=comm_default,
        height=90,
        placeholder='Be specific — what will you start, stop, or do more of?',
        key=f'cascade_comm_{name}',
    )

    st.markdown('')
    if st.button('Submit', type='primary', key=f'cascade_submit_{name}', use_container_width=True):
        if not function:
            st.warning('Please select your function.')
            return
        if not commitment.strip():
            st.warning('Please add your personal One Thing.')
            return
        save_commitment(name, function, commitment.strip())
        save_confidence(name, confidence, risks)
        pull_commitments.clear()
        pull_confidence.clear()
        st.session_state[f'cascade_edit_{name}'] = False
        st.success('Saved. Thank you.')
        st.rerun()

_cascade_live(name)
