"""Strategy Cascade — facilitator page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL, with_retry, _sheets
from strategy_cascade_shared import (
    GOALS,
    CASCADE_STAGES, CASCADE_STAGE_LABELS,
    _ensure_cascade_tabs,
    pull_cascade_session, set_cascade_session,
    pull_commitments, pull_confidence,
    pull_team_contributions,
    pull_cascade_content, save_cascade_content,
)
from one_thing_shared import DEPARTMENTS
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

st.markdown('### 🎛️ Facilitate — Strategy Cascade')

if st.button('🔒 Lock', key='cas_fac_lock'):
    st.session_state['cas_fac_auth'] = False
    st.rerun()

# ── Stage controls ─────────────────────────────────────────────────────────────

session   = pull_cascade_session()
stage     = session.get('stage', 'hidden')

st.markdown(
    f'<div style="background:#F5F0F5;border-radius:8px;padding:10px 16px;margin-bottom:14px;'
    f'font-size:0.84em;color:{PURPLE};font-weight:600;">'
    f'Current stage: {CASCADE_STAGE_LABELS.get(stage, stage)}</div>',
    unsafe_allow_html=True,
)

_stage_btns = [
    ('Goals',          'goals'),
    ('Contributions',  'contributions'),
    ('Confidence',     'confidence'),
    ('Complete',       'complete'),
]

btn_cols = st.columns(len(_stage_btns) + 2)

for i, (_label, _target) in enumerate(_stage_btns):
    with btn_cols[i]:
        if st.button(_label, use_container_width=True,
                     type='primary' if stage == _target else 'secondary',
                     key=f'cas_stage_{_target}'):
            set_cascade_session('stage', _target)
            pull_cascade_session.clear()
            st.rerun()

with btn_cols[-2]:
    if st.button('↩ Reset', use_container_width=True, key='cas_reset'):
        set_cascade_session('stage', 'hidden')
        pull_cascade_session.clear()
        st.rerun()

with btn_cols[-1]:
    if st.button('↺ Refresh', use_container_width=True, key='cas_refresh'):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ── Edit cascade content ───────────────────────────────────────────────────────

st.markdown(
    f'<div style="font-weight:700;font-size:1em;color:{PURPLE};margin-bottom:16px;">Edit cascade content</div>',
    unsafe_allow_html=True,
)

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

# Goals
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
    _n = len(_goal_ids) + 1
    while f'G{_n}' in set(_goal_ids):
        _n += 1
    _new_id = f'G{_n}'
    _goal_ids.append(_new_id)
    st.session_state[f'eg_title_{_new_id}'] = ''
    st.session_state[f'eg_desc_{_new_id}']  = ''
    st.rerun()

st.markdown('')

# Function One Things
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
        if len(_fn_slots) > 1 and st.button('✕', key=f'del_fn_{_slot}', help='Delete'):
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
        {'id': _gid, 'title': st.session_state.get(f'eg_title_{_gid}', ''),
         'description': st.session_state.get(f'eg_desc_{_gid}', '')}
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
        for _k in [k for k in list(st.session_state.keys())
                   if k.startswith(('eg_', 'ef_'))
                   or k in ('edit_goal_ids', 'edit_fn_slots', 'edit_fn_next')]:
            del st.session_state[_k]
        st.success('Saved.')
        st.rerun()
    else:
        st.warning('Add at least one goal and one function before saving.')

st.divider()

# ── Live tracker ───────────────────────────────────────────────────────────────

@st.fragment(run_every=8)
def _live_tracker():
    pull_team_contributions.clear()
    pull_confidence.clear()
    df_contrib = pull_team_contributions()
    df_conf    = pull_confidence()
    goals_live, _ = pull_cascade_content()

    submitted_contrib = set(df_contrib['Name'].tolist()) if not df_contrib.empty else set()
    n_contrib = len(submitted_contrib)
    n_conf    = len(df_conf) if not df_conf.empty else 0

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f'<div style="font-weight:700;font-size:0.92em;color:{PURPLE};margin-bottom:8px;">'
            f'Team Contributions — {n_contrib} of {len(TEAM)}</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(4)
        for i, person in enumerate(TEAM):
            done = person in submitted_contrib
            bg   = '#E8F5EE' if done else '#F5F5F5'
            tc   = '#2D7D4F' if done else '#AAAAAA'
            with cols[i % 4]:
                st.markdown(
                    f'<div style="background:{bg};border-radius:8px;padding:6px 8px;'
                    f'margin-bottom:6px;text-align:center;font-size:0.76em;color:{tc};font-weight:600;">'
                    f'{"✅" if done else "○"} {person.split()[0]}</div>',
                    unsafe_allow_html=True,
                )
    with col_b:
        st.markdown(
            f'<div style="font-weight:700;font-size:0.92em;color:{PURPLE};margin-bottom:8px;">'
            f'Anonymous Confidence — {n_conf} response{"s" if n_conf != 1 else ""}</div>',
            unsafe_allow_html=True,
        )
        if n_conf > 0:
            for i, g in enumerate(goals_live):
                conf_col = f'{g["id"]}_Confidence'
                if conf_col not in df_conf.columns:
                    continue
                nums = []
                for v in df_conf[conf_col].tolist():
                    try: nums.append(int(v))
                    except (TypeError, ValueError): pass
                if not nums:
                    continue
                avg = sum(nums) / len(nums)
                if avg >= 4:
                    bc, bg = '#3EAA6D', '#E8F5EE'
                elif avg >= 3:
                    bc, bg = '#B7770D', '#FEF5E7'
                else:
                    bc, bg = '#C0392B', '#FDECEA'
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                    f'<div style="font-size:0.76em;color:#555;flex:1;">{g["title"]}</div>'
                    f'<span style="background:{bg};color:{bc};font-weight:700;font-size:0.76em;'
                    f'padding:2px 10px;border-radius:20px;white-space:nowrap;">{avg:.1f}/5</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption('No responses yet.')

_live_tracker()

st.divider()

# ── Debrief ────────────────────────────────────────────────────────────────────

st.markdown(
    f'<div style="font-weight:700;font-size:1em;color:{PURPLE};margin-bottom:14px;">Debrief</div>',
    unsafe_allow_html=True,
)

if st.button('↺ Refresh debrief', key='debrief_refresh'):
    pull_team_contributions.clear()
    pull_confidence.clear()
    st.rerun()

_df_contrib = pull_team_contributions()
_df_conf    = pull_confidence()
_goals_live, _fn_live = pull_cascade_content()

def _score_cell(val):
    try:
        s = int(val)
    except (TypeError, ValueError):
        return '#F5F5F5', '#AAAAAA'
    if s >= 4: return '#E8F5EE', '#2D7D4F'
    if s == 3: return '#FEF5E7', '#B7770D'
    return '#FDECEA', '#C0392B'

if _df_conf.empty and _df_contrib.empty:
    st.caption('No submissions yet.')
else:
    # ── Aggregate confidence ────────────────────────────────────────────────

    if not _df_conf.empty:
        n = len(_df_conf)
        st.markdown(
            f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;color:#888;margin-bottom:10px;">'
            f'CONFIDENCE — {n} anonymous response{"s" if n != 1 else ""}</div>',
            unsafe_allow_html=True,
        )

        for i, g in enumerate(_goals_live):
            conf_col = f'{g["id"]}_Confidence'
            cont_col = f'{g["id"]}_Contribution'
            bc_goal  = ['#781E73', '#188383', '#50144B'][i % 3]

            nums = []
            for v in _df_conf.get(conf_col, pd.Series()).tolist():
                try: nums.append(int(v))
                except (TypeError, ValueError): pass

            avg     = sum(nums) / len(nums) if nums else None
            dist    = {k: nums.count(k) for k in range(1, 6) if nums.count(k)}
            bc_avg, bg_avg = _score_cell(round(avg)) if avg else ('#CCCCCC', '#F5F5F5')

            st.markdown(
                f'<div style="border-left:4px solid {bc_goal};background:#F8F8F8;'
                f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:6px;">'
                f'<div style="font-weight:700;font-size:0.9em;color:{bc_goal};margin-bottom:8px;">{g["title"]}</div>'
                f'<div style="display:flex;align-items:center;gap:12px;">'
                f'<div style="flex:1;background:#E0E0E0;border-radius:4px;height:10px;">'
                f'<div style="width:{(avg or 0)/5*100:.0f}%;background:{bc_avg};border-radius:4px;height:10px;"></div>'
                f'</div>'
                + (f'<span style="background:{bg_avg};color:{bc_avg};font-weight:700;font-size:0.76em;'
                   f'padding:3px 10px;border-radius:20px;white-space:nowrap;">avg {avg:.1f}</span>' if avg else '')
                + '</div>'
                + (f'<div style="margin-top:6px;font-size:0.72em;color:#888;">'
                   + '  '.join(f'{k}★: {v}' for k, v in sorted(dist.items()))
                   + '</div>' if dist else '')
                + '</div>',
                unsafe_allow_html=True,
            )

            # Contribution texts (anonymous)
            if cont_col in _df_conf.columns:
                contribs = [str(v).strip() for v in _df_conf[cont_col].tolist() if str(v).strip()]
                if contribs:
                    st.markdown(
                        f'<div style="font-size:0.7em;font-weight:700;color:#888;'
                        f'letter-spacing:1px;margin:8px 0 4px;">HOW PEOPLE SEE THEMSELVES CONTRIBUTING</div>',
                        unsafe_allow_html=True,
                    )
                    for ct in contribs:
                        st.markdown(
                            f'<div style="border-left:2px solid #CCCCCC;padding:6px 12px;'
                            f'margin-bottom:4px;font-size:0.82em;color:#444;">{ct}</div>',
                            unsafe_allow_html=True,
                        )

        st.markdown('')

    # ── Team contributions by function ──────────────────────────────────────

    if not _df_contrib.empty:
        st.markdown(
            f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;color:#888;margin-bottom:10px;">TEAM CONTRIBUTIONS BY FUNCTION</div>',
            unsafe_allow_html=True,
        )
        for dept in DEPARTMENTS:
            dept_rows = _df_contrib[_df_contrib['Function'] == dept]
            if dept_rows.empty:
                continue
            items_html = ''
            for _, row in dept_rows.iterrows():
                for g in _goals_live:
                    val = row.get(g['id'], '')
                    if val:
                        items_html += (
                            f'<div style="padding:5px 0;border-bottom:1px solid #F0F0F0;font-size:0.82em;">'
                            f'<strong style="color:#444;display:inline-block;min-width:72px;">'
                            f'{row["Name"].split()[0]}</strong>'
                            f'<span style="font-size:0.82em;color:{TEAL};margin-right:6px;">[{g["title"]}]</span>'
                            f'<span style="color:#555;">{val}</span></div>'
                        )
            if items_html:
                st.markdown(
                    f'<div style="border-left:4px solid {TEAL};background:#F8F8F8;'
                    f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:10px;">'
                    f'<div style="font-size:0.7em;font-weight:700;color:{TEAL};'
                    f'letter-spacing:1px;margin-bottom:8px;">{dept.upper()}</div>'
                    f'{items_html}</div>',
                    unsafe_allow_html=True,
                )
