"""Facilitator page — FY27 Scorecard entry."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, with_retry, _clear_sheets, PURPLE, TEAL
from strategy_cascade_shared import (
    pull_cascade_contributions, get_live_choices,
    DEPARTMENTS,
)
from scorecard_shared import (
    _ensure_scorecard_tab, pull_scorecard_entries, save_scorecard_entry,
)

inject_styles()

WINE   = '#50144B'
FOREST = '#005E63'

# ── Auth ───────────────────────────────────────────────────────────────────────

if 'sc_fac_auth' not in st.session_state:
    st.session_state['sc_fac_auth'] = False

if not st.session_state['sc_fac_auth']:
    st.caption('This page is for the session facilitator only.')
    pwd = st.text_input('Password', type='password', key='sc_fac_pwd')
    if st.button('Unlock', type='primary', key='sc_fac_unlock'):
        if pwd == st.secrets.get('FACILITATE_PASSWORD', ''):
            st.session_state['sc_fac_auth'] = True
            st.rerun()
        else:
            st.error('Incorrect password.')
    st.stop()

if st.button('🔒 Lock', key='sc_fac_lock'):
    st.session_state['sc_fac_auth'] = False
    st.rerun()

# ── Tab setup ──────────────────────────────────────────────────────────────────

if not st.session_state.get('_sc_fac_tab_ready'):
    try:
        with_retry(_ensure_scorecard_tab, on_retry=_clear_sheets)
        st.session_state['_sc_fac_tab_ready'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue. ({_e})')

st.markdown('### 🎛️ Facilitate — FY27 Scorecard')
st.caption(
    'Admin override — edit or correct any function entry. '
    'Primary input is via the FY27 Scorecard page where function groups work directly.'
)

# ── Load data ──────────────────────────────────────────────────────────────────

col_ref, col_reload = st.columns([8, 1])
with col_reload:
    if st.button('↺ Refresh', use_container_width=True, key='sc_fac_refresh'):
        pull_scorecard_entries.clear()
        pull_cascade_contributions.clear()
        st.session_state.pop('_sc_entries_loaded', None)
        st.rerun()

contribs_df = pull_cascade_contributions()
entries_df  = pull_scorecard_entries()
choices     = get_live_choices()

# ── Initialise session state from saved entries (once per session) ─────────────

if not st.session_state.get('_sc_entries_loaded'):
    for _, row in entries_df.iterrows():
        cid  = row['ChoiceID']
        dept = row['Department']
        for fld in ['Metric', 'Target', 'Owner']:
            k = f'sc_{fld.lower()}_{cid}_{dept}'
            if k not in st.session_state:
                st.session_state[k] = row[fld]
    st.session_state['_sc_entries_loaded'] = True

# ── Helper: latest contribution per dept for a choice ─────────────────────────

def _dept_contribs(choice_id: str) -> dict:
    """Returns {dept: text} — latest non-deleted, non-opted-out per dept."""
    if contribs_df.empty:
        return {}
    sub = contribs_df[
        (contribs_df['ChoiceID'] == choice_id) &
        (~contribs_df['Status'].isin(['deleted', 'opted_out']))
    ].sort_values('Timestamp', ascending=False)
    result = {}
    for _, row in sub.iterrows():
        if row['Department'] not in result and row['Text'].strip():
            result[row['Department']] = row['Text'].strip()
    return result

# ── Summary banner ─────────────────────────────────────────────────────────────

n_entries = len(entries_df)
n_choices = len(choices)
n_filled  = len(entries_df['ChoiceID'].unique()) if not entries_df.empty else 0

st.markdown(
    f'<div style="background:#F5F0F5;border-radius:8px;padding:10px 16px;margin-bottom:20px;'
    f'font-size:0.84em;color:{PURPLE};font-weight:600;">'
    f'{n_entries} scorecard entries saved · {n_filled} of {n_choices} choices have at least one entry'
    f'</div>',
    unsafe_allow_html=True,
)

st.divider()

# ── Choice sections ────────────────────────────────────────────────────────────

CHOICE_COLOURS = [WINE, FOREST, '#781E73', '#005E63', WINE, FOREST, '#781E73']

for idx, choice in enumerate(choices):
    cid          = choice['id']
    colour       = CHOICE_COLOURS[idx % len(CHOICE_COLOURS)]
    dept_inputs  = _dept_contribs(cid)
    choice_entries = entries_df[entries_df['ChoiceID'] == cid] if not entries_df.empty else entries_df
    n_saved      = len(choice_entries)
    n_contribs   = len(dept_inputs)

    label = f'Strategic Choice {choice["number"]} — {choice["title"]}'
    if n_saved > 0:
        label += f'  ✅ {n_saved} saved'
    elif n_contribs > 0:
        label += f'  · {n_contribs} dept inputs'
    else:
        label += '  · no cascade inputs yet'

    with st.expander(label, expanded=(n_contribs > 0 and n_saved < n_contribs)):

        st.markdown(
            f'<div style="font-size:0.85em;color:#555;margin-bottom:14px;'
            f'border-left:3px solid {colour};padding-left:10px;">'
            f'{choice["description"]}</div>',
            unsafe_allow_html=True,
        )

        if not dept_inputs:
            st.info('No function contributions recorded in the cascade for this choice yet.')
            continue

        for dept in DEPARTMENTS:
            cascade_text = dept_inputs.get(dept, '')
            if not cascade_text:
                continue

            metric_key = f'sc_metric_{cid}_{dept}'
            target_key = f'sc_target_{cid}_{dept}'
            owner_key  = f'sc_owner_{cid}_{dept}'

            # Ensure keys exist (for depts not in saved entries)
            st.session_state.setdefault(metric_key, '')
            st.session_state.setdefault(target_key, '')
            st.session_state.setdefault(owner_key, '')

            has_entry = not choice_entries[choice_entries['Department'] == dept].empty

            dept_status = '✅ Saved' if has_entry else '○ Pending'
            dept_status_colour = '#3EAA6D' if has_entry else '#AAAAAA'

            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
                f'margin-top:16px;margin-bottom:6px;">'
                f'<div style="font-size:0.8em;font-weight:700;color:{colour};'
                f'text-transform:uppercase;letter-spacing:0.5px;">{dept}</div>'
                f'<div style="font-size:0.72em;color:{dept_status_colour};">{dept_status}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div style="background:#F7F7F7;border-left:3px solid #DDDDDD;'
                f'border-radius:0 6px 6px 0;padding:8px 12px;margin-bottom:10px;'
                f'font-size:0.82em;color:#444;line-height:1.5;">'
                f'<span style="font-size:0.72em;color:#AAAAAA;font-weight:700;'
                f'text-transform:uppercase;letter-spacing:0.5px;">Cascade input</span><br>'
                f'{cascade_text}</div>',
                unsafe_allow_html=True,
            )

            col_m, col_t, col_o, col_btn = st.columns([3, 2, 2, 1])
            with col_m:
                st.text_input(
                    'Metric',
                    key=metric_key,
                    placeholder='e.g. Repeat order rate',
                    label_visibility='visible',
                )
            with col_t:
                st.text_input(
                    'Target',
                    key=target_key,
                    placeholder='e.g. 40% of clinics',
                    label_visibility='visible',
                )
            with col_o:
                st.text_input(
                    'Owner',
                    key=owner_key,
                    placeholder='e.g. JK',
                    label_visibility='visible',
                )
            with col_btn:
                st.markdown('<br>', unsafe_allow_html=True)
                if st.button('Save', key=f'sc_save_{cid}_{dept}', use_container_width=True, type='primary'):
                    metric = st.session_state.get(metric_key, '').strip()
                    target = st.session_state.get(target_key, '').strip()
                    owner  = st.session_state.get(owner_key, '').strip()
                    if metric or target or owner:
                        try:
                            save_scorecard_entry(cid, dept, metric, target, owner, locked_by='Facilitator')
                            st.session_state.pop('_sc_entries_loaded', None)
                            st.toast(f'{dept} saved ✓', icon='✅')
                            st.rerun()
                        except Exception as _e:
                            st.error(f'Could not save. ({_e})')
                    else:
                        st.warning('Enter at least one field before saving.')

            st.markdown('<hr style="border:none;border-top:1px solid #EEEEEE;margin:4px 0;">', unsafe_allow_html=True)
