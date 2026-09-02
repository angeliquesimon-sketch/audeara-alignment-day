"""Strategy Cascade — facilitator page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL, with_retry, _sheets
from strategy_cascade_shared import (
    GOALS,
    STAGES, STAGE_LABELS,
    _ensure_cascade_tabs,
    pull_cascade_session, set_cascade_session,
    pull_commitments, pull_confidence,
    pull_cascade_content, save_cascade_content,
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

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    active = stage_idx == 0
    if st.button('▶ Functions', use_container_width=True,
                 type='primary' if active else 'secondary', disabled=not active):
        set_cascade_session('stage', 'functions')
        pull_cascade_session.clear()
        st.rerun()

with col2:
    active = stage_idx == 1
    if st.button('→ Goals', use_container_width=True,
                 type='primary' if active else 'secondary', disabled=not active):
        set_cascade_session('stage', 'goals')
        pull_cascade_session.clear()
        st.rerun()

with col3:
    active = stage_idx == 2
    if st.button('→ Goal Form', use_container_width=True,
                 type='primary' if active else 'secondary', disabled=not active):
        set_cascade_session('stage', 'confidence')
        pull_cascade_session.clear()
        st.rerun()

with col4:
    active = stage_idx == 3
    if st.button('→ One Thing', use_container_width=True,
                 type='primary' if active else 'secondary', disabled=not active):
        set_cascade_session('stage', 'commitment')
        pull_cascade_session.clear()
        st.rerun()

with col5:
    active = stage_idx == 4
    if st.button('✔ Complete', use_container_width=True,
                 type='primary' if active else 'secondary', disabled=not active):
        set_cascade_session('stage', 'complete')
        pull_cascade_session.clear()
        st.rerun()

with col6:
    if st.button('↩ Reset', use_container_width=True):
        set_cascade_session('stage', 'hidden')
        pull_cascade_session.clear()
        st.rerun()

with col7:
    if st.button('↺ Refresh', use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ── Edit cascade content ───────────────────────────────────────────────────────

st.markdown(
    f'<div style="font-weight:700;font-size:1em;color:{PURPLE};margin-bottom:16px;">Edit cascade content</div>',
    unsafe_allow_html=True,
)

# Initialise working state from sheet on first load (or after a save resets it).
# Goals use the goal ID as stable key; functions use a slot counter so renames
# and deletes don't collide with stale session-state widget values.
if 'edit_goal_ids' not in st.session_state:
    _init_goals, _init_fns = pull_cascade_content()
    st.session_state['edit_goal_ids'] = [g['id'] for g in _init_goals]
    for _g in _init_goals:
        st.session_state[f'eg_title_{_g["id"]}'] = _g['title']
        st.session_state[f'eg_desc_{_g["id"]}']  = _g['description']
    st.session_state['edit_fn_slots'] = []
    st.session_state['edit_fn_next']  = 0
    for _fname, _fot in _init_fns.items():
        _s = st.session_state['edit_fn_next']
        st.session_state[f'ef_name_{_s}'] = _fname
        st.session_state[f'ef_ot_{_s}']   = _fot
        st.session_state['edit_fn_slots'].append(_s)
        st.session_state['edit_fn_next'] += 1

# ── Goals ──────────────────────────────────────────────────────────────────────

st.markdown(
    f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;color:{PURPLE};margin-bottom:10px;">GOALS</div>',
    unsafe_allow_html=True,
)
_goal_ids = st.session_state['edit_goal_ids']
for _i, _gid in enumerate(_goal_ids):
    _c1, _c2 = st.columns([11, 1])
    with _c1:
        st.text_input(f'Goal {_i + 1} — title', key=f'eg_title_{_gid}')
        st.text_area(f'Goal {_i + 1} — description', key=f'eg_desc_{_gid}', height=68)
    with _c2:
        st.markdown('<br><br><br>', unsafe_allow_html=True)
        if len(_goal_ids) > 1 and st.button('✕', key=f'del_goal_{_gid}', help='Delete this goal'):
            _goal_ids.remove(_gid)
            st.session_state.pop(f'eg_title_{_gid}', None)
            st.session_state.pop(f'eg_desc_{_gid}', None)
            st.rerun()
    st.markdown('')

if st.button('+ Add goal', key='add_goal_btn'):
    _existing_ids = set(_goal_ids)
    _n = len(_goal_ids) + 1
    while f'G{_n}' in _existing_ids:
        _n += 1
    _new_id = f'G{_n}'
    _goal_ids.append(_new_id)
    st.session_state[f'eg_title_{_new_id}'] = ''
    st.session_state[f'eg_desc_{_new_id}']  = ''
    st.rerun()

st.markdown('')

# ── Functions ──────────────────────────────────────────────────────────────────

st.markdown(
    f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;color:{TEAL};margin:4px 0 10px;">FUNCTION ONE THINGS</div>',
    unsafe_allow_html=True,
)
_fn_slots = st.session_state['edit_fn_slots']
for _i, _slot in enumerate(_fn_slots):
    _c1, _c2 = st.columns([11, 1])
    with _c1:
        st.text_input(f'Function {_i + 1}', key=f'ef_name_{_slot}')
        st.text_area('One Thing', key=f'ef_ot_{_slot}', height=68)
    with _c2:
        st.markdown('<br><br><br>', unsafe_allow_html=True)
        if len(_fn_slots) > 1 and st.button('✕', key=f'del_fn_{_slot}', help='Delete this function'):
            _fn_slots.remove(_slot)
            st.session_state.pop(f'ef_name_{_slot}', None)
            st.session_state.pop(f'ef_ot_{_slot}', None)
            st.rerun()
    st.markdown('')

if st.button('+ Add function', key='add_fn_btn'):
    _new_slot = st.session_state['edit_fn_next']
    st.session_state[f'ef_name_{_new_slot}'] = ''
    st.session_state[f'ef_ot_{_new_slot}']   = ''
    _fn_slots.append(_new_slot)
    st.session_state['edit_fn_next'] += 1
    st.rerun()

st.markdown('')

if st.button('Save content', type='primary', key='save_cascade_content'):
    _saved_goals = [
        {
            'id':          _gid,
            'title':       st.session_state.get(f'eg_title_{_gid}', ''),
            'description': st.session_state.get(f'eg_desc_{_gid}', ''),
        }
        for _gid in _goal_ids
        if st.session_state.get(f'eg_title_{_gid}', '').strip()
    ]
    _saved_fns = {
        st.session_state.get(f'ef_name_{_s}', '').strip(): st.session_state.get(f'ef_ot_{_s}', '')
        for _s in _fn_slots
        if st.session_state.get(f'ef_name_{_s}', '').strip()
    }
    if _saved_goals and _saved_fns:
        save_cascade_content(_saved_goals, _saved_fns)
        _keys_to_clear = [k for k in list(st.session_state.keys())
                          if k.startswith(('eg_', 'ef_'))
                          or k in ('edit_goal_ids', 'edit_fn_slots', 'edit_fn_next')]
        for _k in _keys_to_clear:
            del st.session_state[_k]
        st.success('Saved.')
        st.rerun()
    else:
        st.warning('Add at least one goal and one function before saving.')

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

    for g in GOALS:
        conf_key = f'{g["id"]}_Confidence'
        risk_key = f'{g["id"]}_Risk'

        st.markdown(
            f'<div style="font-weight:700;font-size:0.88em;color:{PURPLE};margin:14px 0 6px;">'
            f'{g["title"]}</div>',
            unsafe_allow_html=True,
        )

        if not df_conf.empty:
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
        _, _fn_live_lt = pull_cascade_content()
        st.divider()
        st.markdown(
            f'<div style="font-weight:700;font-size:0.92em;color:{TEAL};margin-bottom:10px;">'
            f'Personal One Things</div>',
            unsafe_allow_html=True,
        )
        for fn in _fn_live_lt:
            fn_rows = df_comm[df_comm['Function'] == fn]
            if fn_rows.empty:
                continue
            st.markdown(
                f'<div style="font-size:0.72em;font-weight:700;color:{TEAL};'
                f'letter-spacing:1px;margin:10px 0 4px;">{fn.upper()}</div>',
                unsafe_allow_html=True,
            )
            for _, row in fn_rows.iterrows():
                st.markdown(
                    f'<div style="border-left:3px solid {TEAL};background:#F8F8F8;'
                    f'border-radius:0 6px 6px 0;padding:8px 12px;margin-bottom:6px;font-size:0.82em;">'
                    f'<strong style="color:#444;">{row["Name"].split()[0]}</strong>  '
                    f'<span style="color:#666;">{row["Commitment"]}</span></div>',
                    unsafe_allow_html=True,
                )

_live_tracker()

# ── Debrief ────────────────────────────────────────────────────────────────────

st.divider()
st.markdown(
    f'<div style="font-weight:700;font-size:1em;color:{PURPLE};margin-bottom:14px;">Debrief</div>',
    unsafe_allow_html=True,
)

if st.button('↺ Refresh debrief', key='debrief_refresh'):
    pull_commitments.clear()
    pull_confidence.clear()
    st.rerun()

_df_comm = pull_commitments()
_df_conf = pull_confidence()
_, _fn_live_db = pull_cascade_content()

def _score_cell(val):
    try:
        s = int(val)
    except (TypeError, ValueError):
        return '#F5F5F5', '#AAAAAA'
    if s >= 4: return '#E8F5EE', '#2D7D4F'
    if s == 3: return '#FEF5E7', '#B7770D'
    return '#FDECEA', '#C0392B'

if _df_conf.empty and _df_comm.empty:
    st.caption('No submissions yet.')
else:
    # ── Confidence grid ──────────────────────────────────────────────────────

    if not _df_conf.empty:
        goal_ths = ''.join(
            f'<th style="padding:8px 12px;font-size:0.78em;color:{PURPLE};font-weight:700;'
            f'text-align:center;border-bottom:2px solid #E8E0E8;min-width:130px;">{g["title"]}</th>'
            for g in GOALS
        )
        rows_html = ''
        for _, row in _df_conf.iterrows():
            name = row.get('Name', '')
            tds = f'<td style="padding:8px 12px;font-size:0.84em;font-weight:600;color:#444;border-bottom:1px solid #F0F0F0;">{name.split()[0]}</td>'
            for g in GOALS:
                val = row.get(f'{g["id"]}_Confidence', '')
                bg, tc = _score_cell(val)
                tds += (
                    f'<td style="padding:6px 12px;text-align:center;border-bottom:1px solid #F0F0F0;">'
                    f'<span style="background:{bg};color:{tc};font-weight:700;font-size:0.82em;'
                    f'padding:3px 12px;border-radius:20px;">{val if val else "—"}</span></td>'
                )
            rows_html += f'<tr>{tds}</tr>'

        # Team average row
        avg_tds = '<td style="padding:8px 12px;font-size:0.78em;font-weight:700;color:#888;background:#F8F8F8;">Team avg</td>'
        for g in GOALS:
            nums = []
            for v in _df_conf[f'{g["id"]}_Confidence'].tolist():
                try: nums.append(int(v))
                except (TypeError, ValueError): pass
            if nums:
                avg = sum(nums) / len(nums)
                bg, tc = _score_cell(round(avg))
                avg_tds += (
                    f'<td style="padding:6px 12px;text-align:center;background:#F8F8F8;">'
                    f'<span style="background:{bg};color:{tc};font-weight:700;font-size:0.82em;'
                    f'padding:3px 12px;border-radius:20px;">{avg:.1f}</span></td>'
                )
            else:
                avg_tds += '<td style="text-align:center;background:#F8F8F8;color:#AAA;">—</td>'
        rows_html += f'<tr>{avg_tds}</tr>'

        st.markdown(
            f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;color:#888;margin-bottom:10px;">CONFIDENCE GRID</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="overflow-x:auto;margin-bottom:24px;">'
            f'<table style="width:100%;border-collapse:collapse;">'
            f'<thead><tr>'
            f'<th style="padding:8px 12px;border-bottom:2px solid #E8E0E8;"></th>'
            f'{goal_ths}'
            f'</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table></div>',
            unsafe_allow_html=True,
        )

    # ── Risks by goal ────────────────────────────────────────────────────────

    if not _df_conf.empty:
        has_any_risk = any(
            _df_conf[f'{g["id"]}_Risk'].astype(str).str.strip().ne('').any()
            for g in GOALS
        )
        if has_any_risk:
            st.markdown(
                f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;color:#888;margin-bottom:10px;">RISKS BY GOAL</div>',
                unsafe_allow_html=True,
            )
            for g in GOALS:
                risks = [
                    (r['Name'], r[f'{g["id"]}_Risk'])
                    for _, r in _df_conf.iterrows()
                    if str(r.get(f'{g["id"]}_Risk', '')).strip()
                ]
                if not risks:
                    continue
                st.markdown(
                    f'<div style="font-weight:700;font-size:0.86em;color:{PURPLE};margin:10px 0 6px;">{g["title"]}</div>',
                    unsafe_allow_html=True,
                )
                for name, risk in risks:
                    st.markdown(
                        f'<div style="border-left:3px solid #E74C3C;background:#FEF5F5;'
                        f'border-radius:0 6px 6px 0;padding:7px 12px;margin-bottom:5px;font-size:0.84em;">'
                        f'<strong style="color:#C0392B;">{name.split()[0]}</strong>'
                        f'<span style="color:#444;margin-left:8px;">{risk}</span></div>',
                        unsafe_allow_html=True,
                    )

    # ── One Things by function ───────────────────────────────────────────────

    if not _df_comm.empty:
        st.markdown(
            f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;color:#888;margin:16px 0 10px;">PERSONAL ONE THINGS</div>',
            unsafe_allow_html=True,
        )
        for fn in _fn_live_db:
            fn_rows = _df_comm[_df_comm['Function'] == fn]
            if fn_rows.empty:
                continue
            items = ''.join(
                f'<div style="padding:7px 0;border-bottom:1px solid #F0F0F0;font-size:0.84em;">'
                f'<strong style="color:#444;min-width:80px;display:inline-block;">{row["Name"].split()[0]}</strong>'
                f'<span style="color:#666;">{row["Commitment"]}</span></div>'
                for _, row in fn_rows.iterrows()
            )
            st.markdown(
                f'<div style="border-left:4px solid {TEAL};background:#F8F8F8;'
                f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:10px;">'
                f'<div style="font-size:0.72em;font-weight:700;color:{TEAL};letter-spacing:1px;margin-bottom:8px;">{fn.upper()}</div>'
                f'{items}'
                f'</div>',
                unsafe_allow_html=True,
            )
