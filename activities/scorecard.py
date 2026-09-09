"""FY27 Scorecard — participant input and live display."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from utils import inject_styles, with_retry, _clear_sheets, PURPLE, TEAL
from strategy_cascade_shared import pull_cascade_contributions, get_live_choices
from scorecard_shared import (
    _ensure_scorecard_tab, _ensure_scorecard_proposals_tab,
    pull_scorecard_entries, pull_scorecard_proposals,
    save_scorecard_proposal, save_scorecard_entry,
)
from one_thing_shared import DEPARTMENT_MAP, DEPARTMENT_HEADS, DEPARTMENTS
from styles_shared import TEAM

inject_styles()

WINE           = '#50144B'
FOREST         = '#005E63'
CHOICE_COLOURS = [WINE, FOREST, '#781E73', '#005E63', WINE, FOREST, '#781E73']

# ── Sheet setup ────────────────────────────────────────────────────────────────

if not st.session_state.get('_sc_tabs_ready'):
    try:
        with_retry(_ensure_scorecard_tab,           on_retry=_clear_sheets)
        with_retry(_ensure_scorecard_proposals_tab, on_retry=_clear_sheets)
        st.session_state['_sc_tabs_ready'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue. ({_e})')

# ── Header ─────────────────────────────────────────────────────────────────────

st.markdown(
    f'<div style="font-weight:700;font-size:1.3em;color:{WINE};margin-bottom:4px;">'
    f'FY27 Scorecard</div>',
    unsafe_allow_html=True,
)

# ── Name selector ─────────────────────────────────────────────────────────────

name = st.selectbox('Your name', [''] + TEAM, key='sc_name')

if not name:
    st.caption('Select your name above to get started.')
    st.stop()

my_depts = DEPARTMENT_MAP.get(name, [])

if not my_depts:
    st.warning("We don't have a function on file for your name.")
    st.stop()

# ── Tabs ───────────────────────────────────────────────────────────────────────

tab_about, tab_dept, tab_all = st.tabs(['📋 About', '🏢 My Function', '🌟 All Functions'])

# ── Tab: About ─────────────────────────────────────────────────────────────────

with tab_about:
    st.markdown(
        f'<div style="background:#F7F0F7;border-left:4px solid {WINE};'
        f'border-radius:0 8px 8px 0;padding:16px 20px;margin-bottom:16px;">'
        f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
        f'color:{WINE};margin-bottom:8px;">WHAT IS THE SCORECARD?</div>'
        f'<div style="font-size:0.88em;color:#444;line-height:1.7;">'
        f'The Scorecard turns the commitments your team made in the Strategy Cascade into '
        f'measurable outcomes. For each strategic choice your function contributed to, '
        f'you\'ll agree on a metric, a target, and an owner — so there\'s no ambiguity '
        f'about what success looks like or who is responsible.'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for col, (icon, heading, body) in zip(cols, [
        ('🎯', 'Cascade to commitment',
         'Your function\'s cascade input becomes the context for setting a clear metric and target.'),
        ('👤', 'Named ownership',
         'Every entry has an owner — a real person accountable for the outcome, not a team or a function.'),
        ('✏️', 'Always editable',
         'Function leads can update entries at any time. The scorecard evolves as the year does.'),
    ]):
        with col:
            st.markdown(
                f'<div style="background:#F5F5F5;border-radius:8px;padding:14px 16px;">'
                f'<div style="font-size:1.2em;margin-bottom:6px;">{icon}</div>'
                f'<div style="font-weight:700;font-size:0.84em;color:#333;margin-bottom:4px;">'
                f'{heading}</div>'
                f'<div style="font-size:0.78em;color:#666;line-height:1.5;">{body}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('')
    st.markdown(
        f'<div style="background:#F0F8F8;border-left:4px solid {TEAL};'
        f'border-radius:0 8px 8px 0;padding:14px 20px;">'
        f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
        f'color:{TEAL};margin-bottom:6px;">HOW IT WORKS</div>'
        f'<div style="font-size:0.88em;color:#444;line-height:1.6;">'
        f'Break into your function groups. Anyone can propose a metric, target, and owner '
        f'for each strategic choice. Function leads review the proposals and confirm the '
        f'final entry — which stays editable throughout the day.'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)
    _fl_rows = ''.join(
        f'<tr>'
        f'<td style="padding:8px 14px;font-size:0.84em;font-weight:600;color:#1a1a1a;'
        f'border-bottom:1px solid #F0EBF0;">{fn}</td>'
        f'<td style="padding:8px 14px;font-size:0.84em;color:#555;'
        f'border-bottom:1px solid #F0EBF0;">{lead}</td>'
        f'</tr>'
        for fn, lead in DEPARTMENT_HEADS.items()
    )
    st.markdown(
        f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
        f'color:{WINE};margin-bottom:10px;">FUNCTION LEADS</div>'
        f'<table style="width:100%;border-collapse:collapse;background:#FAFAFA;'
        f'border-radius:8px;overflow:hidden;">'
        f'<thead><tr>'
        f'<th style="text-align:left;padding:8px 14px;font-size:0.7em;font-weight:700;'
        f'letter-spacing:1px;color:{WINE};background:#F5F0F5;border-bottom:2px solid #E8DEE8;">'
        f'FUNCTION</th>'
        f'<th style="text-align:left;padding:8px 14px;font-size:0.7em;font-weight:700;'
        f'letter-spacing:1px;color:{WINE};background:#F5F0F5;border-bottom:2px solid #E8DEE8;">'
        f'LEAD</th>'
        f'</tr></thead>'
        f'<tbody>{_fl_rows}</tbody>'
        f'</table>',
        unsafe_allow_html=True,
    )

# ── Tab: My Function ───────────────────────────────────────────────────────────

with tab_dept:

    # Role indicator — show all depts the user belongs to
    role_parts = []
    for d in my_depts:
        role = 'Function Lead' if DEPARTMENT_HEADS.get(d) == name else 'Team Member'
        role_colour = WINE if DEPARTMENT_HEADS.get(d) == name else '#888888'
        role_parts.append(
            f'<span style="color:{role_colour};font-weight:600;">{d}</span>'
            f'<span style="color:#CCCCCC;"> ({role})</span>'
        )
    st.markdown(
        f'<div style="font-size:0.75em;margin-bottom:16px;">'
        + ' &nbsp;·&nbsp; '.join(role_parts)
        + '</div>',
        unsafe_allow_html=True,
    )

    # Refresh
    col_hd, col_ref = st.columns([9, 1])
    with col_ref:
        if st.button('↺', key='sc_refresh', use_container_width=True):
            pull_scorecard_proposals.clear()
            pull_scorecard_entries.clear()
            pull_cascade_contributions.clear()
            for key in list(st.session_state.keys()):
                if key.startswith('_sc_loaded_'):
                    del st.session_state[key]
            st.rerun()

    choices      = get_live_choices()
    contribs_df  = pull_cascade_contributions()
    proposals_df = pull_scorecard_proposals()
    entries_df   = pull_scorecard_entries()

    # Helper: latest cascade text for a given dept + choice
    def _cascade_text(cid: str, d: str) -> str:
        if contribs_df.empty:
            return ''
        sub = contribs_df[
            (contribs_df['ChoiceID'] == cid) &
            (contribs_df['Department'] == d) &
            (~contribs_df['Status'].isin(['deleted', 'opted_out']))
        ].sort_values('Timestamp', ascending=False)
        return sub.iloc[0]['Text'].strip() if not sub.empty else ''

    # Initialise HOD entry fields from saved sheet data — once per name
    load_flag = f'_sc_loaded_{name}'
    if not st.session_state.get(load_flag):
        for d in my_depts:
            if DEPARTMENT_HEADS.get(d) != name:
                continue
            my_entries = entries_df[
                entries_df['Department'] == d
            ] if not entries_df.empty else pd.DataFrame(columns=entries_df.columns)
            for choice in choices:
                cid   = choice['id']
                entry = my_entries[my_entries['ChoiceID'] == cid]
                for fld in ['Metric', 'Target', 'Owner']:
                    k = f'sc_entry_{fld.lower()}_{cid}_{d}'
                    if k not in st.session_state:
                        st.session_state[k] = entry.iloc[0][fld] if not entry.empty else ''
        st.session_state[load_flag] = True

    # Check if any of the user's depts have contributed to any choice
    any_contribs = any(_cascade_text(c['id'], d) for c in choices for d in my_depts)
    if not any_contribs:
        st.info(
            'Your function hasn\'t contributed to the Strategy Cascade yet. '
            'Complete the cascade activity first, then come back here.'
        )
        st.stop()

    # ── Per-choice sections ────────────────────────────────────────────────────

    multi_dept = len(my_depts) > 1

    for idx, choice in enumerate(choices):
        cid    = choice['id']
        colour = CHOICE_COLOURS[idx % len(CHOICE_COLOURS)]

        # Only show this choice if at least one of the user's depts contributed
        dept_texts = {d: _cascade_text(cid, d) for d in my_depts}
        if not any(dept_texts.values()):
            continue

        # Choice header
        st.markdown(
            f'<div style="border-left:4px solid {colour};padding:10px 14px;'
            f'margin-top:20px;margin-bottom:8px;background:#FAFAFA;border-radius:0 8px 8px 0;">'
            f'<div style="font-size:0.68em;color:{colour};font-weight:700;'
            f'text-transform:uppercase;letter-spacing:1px;">Strategic Choice {choice["number"]}</div>'
            f'<div style="font-weight:700;font-size:0.95em;color:#1a1a1a;">{choice["title"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Per-dept sections within this choice ──────────────────────────────

        for d in my_depts:
            cascade_text = dept_texts[d]
            if not cascade_text:
                continue

            is_hod = DEPARTMENT_HEADS.get(d) == name

            # Dept subheading — only shown when the user has multiple depts
            if multi_dept:
                st.markdown(
                    f'<div style="font-size:0.8em;font-weight:700;color:{colour};'
                    f'text-transform:uppercase;letter-spacing:0.5px;'
                    f'margin-top:14px;margin-bottom:6px;">{d}</div>',
                    unsafe_allow_html=True,
                )

            # Cascade reference
            st.markdown(
                f'<div style="background:#F7F7F7;border-left:3px solid #DDDDDD;'
                f'border-radius:0 6px 6px 0;padding:8px 12px;margin-bottom:14px;'
                f'font-size:0.82em;color:#444;line-height:1.5;">'
                f'<span style="font-size:0.72em;color:#AAAAAA;font-weight:700;'
                f'text-transform:uppercase;letter-spacing:0.5px;">Your cascade input</span><br>'
                f'{cascade_text}</div>',
                unsafe_allow_html=True,
            )

            # All proposals for this function + choice — yellow cards, visible to everyone
            dept_props = (
                proposals_df[
                    (proposals_df['ChoiceID'] == cid) & (proposals_df['Department'] == d)
                ]
                if not proposals_df.empty else pd.DataFrame(columns=proposals_df.columns)
            )
            n_props = len(dept_props)

            st.markdown(
                f'<div style="font-size:0.72em;color:#888;font-weight:700;'
                f'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">'
                f'Proposals</div>',
                unsafe_allow_html=True,
            )
            if dept_props.empty:
                st.markdown(
                    '<div style="font-size:0.82em;color:#BBBBBB;font-style:italic;'
                    'margin-bottom:10px;">No proposals yet.</div>',
                    unsafe_allow_html=True,
                )
            else:
                for pi, (_, prop) in enumerate(dept_props.iterrows()):
                    prop_card = (
                        f'<div style="background:#FEF9E7;border-left:4px solid #F4B942;'
                        f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:6px;">'
                        f'<div style="font-size:0.68em;font-weight:700;color:#B7860D;'
                        f'letter-spacing:1px;margin-bottom:6px;">'
                        f'{prop["Name"].upper()} 💬 IN DISCUSSION</div>'
                        f'<div style="display:flex;gap:20px;flex-wrap:wrap;">'
                        f'<div><div style="font-size:0.65em;color:#B7860D;font-weight:700;'
                        f'text-transform:uppercase;letter-spacing:0.5px;">Metric</div>'
                        f'<div style="font-size:0.84em;color:#1a1a1a;">{prop["Metric"] or "—"}</div></div>'
                        f'<div><div style="font-size:0.65em;color:#B7860D;font-weight:700;'
                        f'text-transform:uppercase;letter-spacing:0.5px;">Target</div>'
                        f'<div style="font-size:0.84em;color:#1a1a1a;">{prop["Target"] or "—"}</div></div>'
                        f'<div><div style="font-size:0.65em;color:#B7860D;font-weight:700;'
                        f'text-transform:uppercase;letter-spacing:0.5px;">Owner</div>'
                        f'<div style="font-size:0.84em;color:#1a1a1a;">{prop["Owner"] or "—"}</div></div>'
                        f'</div></div>'
                    )
                    if is_hod:
                        col_card, col_use = st.columns([5, 1])
                        with col_card:
                            st.markdown(prop_card, unsafe_allow_html=True)
                        with col_use:
                            if st.button('Use', key=f'sc_use_{cid}_{d}_{pi}',
                                         use_container_width=True):
                                st.session_state[f'sc_entry_metric_{cid}_{d}'] = prop['Metric']
                                st.session_state[f'sc_entry_target_{cid}_{d}'] = prop['Target']
                                st.session_state[f'sc_entry_owner_{cid}_{d}']  = prop['Owner']
                                st.session_state[f'sc_entry_edit_{cid}_{d}']   = True
                                st.rerun()
                    else:
                        st.markdown(prop_card, unsafe_allow_html=True)

            # Add a metric — always-append, key resets after each submit
            st.markdown(
                f'<div style="font-size:0.72em;color:#888;font-weight:700;'
                f'text-transform:uppercase;letter-spacing:0.5px;'
                f'margin-top:12px;margin-bottom:4px;">Add a metric</div>',
                unsafe_allow_html=True,
            )
            col_m, col_t, col_o, col_btn = st.columns([3, 2, 2, 1])
            with col_m:
                st.text_input('Metric', key=f'sc_new_metric_{cid}_{d}_{n_props}',
                              placeholder='e.g. Repeat order rate',
                              label_visibility='visible')
            with col_t:
                st.text_input('Target', key=f'sc_new_target_{cid}_{d}_{n_props}',
                              placeholder='e.g. 40% of clinics',
                              label_visibility='visible')
            with col_o:
                st.text_input('Owner', key=f'sc_new_owner_{cid}_{d}_{n_props}',
                              placeholder='e.g. JK',
                              label_visibility='visible')
            with col_btn:
                st.markdown('<br>', unsafe_allow_html=True)
                if st.button('Add', key=f'sc_submit_{cid}_{d}_{n_props}',
                             use_container_width=True):
                    m = st.session_state.get(f'sc_new_metric_{cid}_{d}_{n_props}', '').strip()
                    t = st.session_state.get(f'sc_new_target_{cid}_{d}_{n_props}', '').strip()
                    o = st.session_state.get(f'sc_new_owner_{cid}_{d}_{n_props}', '').strip()
                    if m or t or o:
                        try:
                            save_scorecard_proposal(cid, d, name, m, t, o)
                            st.session_state.pop(load_flag, None)
                            st.toast('Metric added ✓', icon='✅')
                            st.rerun()
                        except Exception as _e:
                            st.error(f'Could not save. ({_e})')
                    else:
                        st.warning('Enter at least one field.')

            # Function answer — confirmed visible to all; entry/edit for Function Lead only
            entry_row = (
                entries_df[
                    (entries_df['ChoiceID'] == cid) & (entries_df['Department'] == d)
                ]
                if not entries_df.empty else pd.DataFrame()
            )
            confirmed  = not entry_row.empty
            edit_flag  = f'sc_entry_edit_{cid}_{d}'
            is_editing = st.session_state.get(edit_flag, False)

            st.markdown(
                f'<div style="font-size:0.72em;color:{colour};font-weight:700;'
                f'text-transform:uppercase;letter-spacing:0.5px;margin-top:16px;'
                f'margin-bottom:6px;">Function answer</div>',
                unsafe_allow_html=True,
            )

            if confirmed and not is_editing:
                row = entry_row.iloc[0]
                st.markdown(
                    f'<div style="background:#E8F5EE;border-left:4px solid #3EAA6D;'
                    f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:6px;">'
                    f'<div style="font-size:0.7em;font-weight:700;color:#2D7D4F;'
                    f'letter-spacing:1px;margin-bottom:8px;">CONFIRMED ✅</div>'
                    f'<div style="display:flex;gap:24px;flex-wrap:wrap;">'
                    f'<div><div style="font-size:0.65em;color:#3EAA6D;font-weight:700;'
                    f'text-transform:uppercase;letter-spacing:0.5px;">Metric</div>'
                    f'<div style="font-size:0.88em;color:#1a1a1a;font-weight:600;">'
                    f'{row["Metric"] or "—"}</div></div>'
                    f'<div><div style="font-size:0.65em;color:#3EAA6D;font-weight:700;'
                    f'text-transform:uppercase;letter-spacing:0.5px;">Target</div>'
                    f'<div style="font-size:0.88em;color:#1a1a1a;font-weight:600;">'
                    f'{row["Target"] or "—"}</div></div>'
                    f'<div><div style="font-size:0.65em;color:#3EAA6D;font-weight:700;'
                    f'text-transform:uppercase;letter-spacing:0.5px;">Owner</div>'
                    f'<div style="font-size:0.88em;color:#1a1a1a;font-weight:600;">'
                    f'{row["Owner"] or "—"}</div></div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                if is_hod:
                    if st.button('Edit', key=f'sc_edit_btn_{cid}_{d}'):
                        st.session_state[edit_flag] = True
                        st.rerun()
            elif is_hod:
                col_m2, col_t2, col_o2 = st.columns([3, 2, 2])
                with col_m2:
                    st.text_input('Metric ', key=f'sc_entry_metric_{cid}_{d}',
                                  placeholder='e.g. Repeat order rate')
                with col_t2:
                    st.text_input('Target ', key=f'sc_entry_target_{cid}_{d}',
                                  placeholder='e.g. 40% of clinics')
                with col_o2:
                    st.text_input('Owner ', key=f'sc_entry_owner_{cid}_{d}',
                                  placeholder='e.g. JK')
                save_label = 'Update' if confirmed else 'Confirm'
                btn_c1, btn_c2 = st.columns([1, 1])
                with btn_c1:
                    if confirmed:
                        if st.button('Cancel', key=f'sc_cancel_{cid}_{d}',
                                     use_container_width=True):
                            st.session_state[edit_flag] = False
                            st.rerun()
                with btn_c2:
                    if st.button(save_label, key=f'sc_confirm_{cid}_{d}',
                                 type='primary', use_container_width=True):
                        metric = st.session_state.get(
                            f'sc_entry_metric_{cid}_{d}', '').strip()
                        target = st.session_state.get(
                            f'sc_entry_target_{cid}_{d}', '').strip()
                        owner  = st.session_state.get(
                            f'sc_entry_owner_{cid}_{d}', '').strip()
                        if metric or target or owner:
                            try:
                                save_scorecard_entry(
                                    cid, d, metric, target, owner, locked_by=name)
                                pull_scorecard_entries.clear()
                                st.session_state.pop(load_flag, None)
                                st.session_state[edit_flag] = False
                                st.toast('Function answer saved ✓', icon='✅')
                                st.rerun()
                            except Exception as _e:
                                st.error(f'Could not save. ({_e})')
                        else:
                            st.warning('Enter at least one field.')
            else:
                st.markdown(
                    '<div style="font-size:0.82em;color:#AAAAAA;font-style:italic;">'
                    'Pending — Function Lead will confirm.</div>',
                    unsafe_allow_html=True,
                )

            # Separator between depts within a choice (not after the last one)
            if multi_dept and d != my_depts[-1] and dept_texts.get(my_depts[my_depts.index(d) + 1], ''):
                st.markdown(
                    '<hr style="border:none;border-top:1px solid #F0F0F0;margin:12px 0;">',
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<hr style="border:none;border-top:1px solid #EEEEEE;margin:16px 0;">',
            unsafe_allow_html=True,
        )

# ── Tab: All Departments ───────────────────────────────────────────────────────

with tab_all:

    @st.fragment(run_every=20)
    def _all_depts():
        choices     = get_live_choices()
        entries_df  = pull_scorecard_entries()
        contribs_df = pull_cascade_contributions()

        def _dept_contribs(cid: str) -> dict:
            if contribs_df.empty:
                return {}
            sub = contribs_df[
                (contribs_df['ChoiceID'] == cid) &
                (~contribs_df['Status'].isin(['deleted', 'opted_out']))
            ].sort_values('Timestamp', ascending=False)
            result = {}
            for _, row in sub.iterrows():
                if row['Department'] not in result and row['Text'].strip():
                    result[row['Department']] = row['Text'].strip()
            return result

        if entries_df.empty:
            st.markdown(
                f'<div style="background:#F7F0F7;border-radius:10px;padding:24px;'
                f'text-align:center;color:#AAAAAA;font-size:0.9em;">'
                f'Function answers will appear here as groups confirm their entries.</div>',
                unsafe_allow_html=True,
            )

        for idx, choice in enumerate(choices):
            cid          = choice['id']
            colour       = CHOICE_COLOURS[idx % len(CHOICE_COLOURS)]
            dept_inputs  = _dept_contribs(cid)
            choice_entries = (
                entries_df[entries_df['ChoiceID'] == cid]
                if not entries_df.empty else entries_df
            )

            rows = []
            for d in DEPARTMENTS:
                if not dept_inputs.get(d, ''):
                    continue
                entry = choice_entries[choice_entries['Department'] == d]
                rows.append({
                    'dept':    d,
                    'cascade': dept_inputs.get(d, ''),
                    'metric':  entry.iloc[0]['Metric'] if not entry.empty else '',
                    'target':  entry.iloc[0]['Target'] if not entry.empty else '',
                    'owner':   entry.iloc[0]['Owner']  if not entry.empty else '',
                    'saved':   not entry.empty,
                })

            if not rows:
                st.markdown(
                    f'<div style="border-left:4px solid #DDDDDD;background:#FAFAFA;'
                    f'border-radius:0 10px 10px 0;padding:14px 16px;margin-bottom:10px;">'
                    f'<div style="font-size:0.68em;color:#CCCCCC;font-weight:700;'
                    f'letter-spacing:1px;text-transform:uppercase;">Strategic Choice {choice["number"]}</div>'
                    f'<div style="font-weight:700;font-size:0.92em;color:#CCCCCC;">{choice["title"]}</div>'
                    f'<div style="font-size:0.78em;color:#CCCCCC;margin-top:6px;">No cascade inputs yet</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                continue

            n_saved  = sum(1 for r in rows if r['saved'])
            n_total  = len(rows)
            all_done = n_saved == n_total

            status_colour = '#3EAA6D' if all_done else '#F5A623' if n_saved > 0 else '#AAAAAA'
            status_label  = (
                f'All {n_total} confirmed' if all_done
                else f'{n_saved} of {n_total} confirmed' if n_saved > 0
                else 'Pending'
            )

            st.markdown(
                f'<div style="border-left:4px solid {colour};background:#FFFFFF;'
                f'border-radius:0 10px 10px 0;padding:14px 16px;margin-bottom:2px;'
                f'box-shadow:0 1px 4px rgba(0,0,0,0.05);">'
                f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
                f'<div>'
                f'<div style="font-size:0.68em;color:{colour};font-weight:700;'
                f'letter-spacing:1px;text-transform:uppercase;">Strategic Choice {choice["number"]}</div>'
                f'<div style="font-weight:700;font-size:0.95em;color:#1a1a1a;">{choice["title"]}</div>'
                f'</div>'
                f'<div style="font-size:0.72em;color:{status_colour};font-weight:600;">'
                f'{status_label}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            for row in rows:
                text_col = '#1a1a1a' if row['saved'] else '#AAAAAA'
                if row['saved']:
                    metric_html = (
                        f'<div style="display:flex;gap:24px;flex-wrap:wrap;">'
                        f'<div><div style="font-size:0.65em;color:#AAAAAA;font-weight:700;'
                        f'text-transform:uppercase;letter-spacing:0.5px;">Metric</div>'
                        f'<div style="font-size:0.85em;color:{text_col};font-weight:600;">'
                        f'{row["metric"] or "—"}</div></div>'
                        f'<div><div style="font-size:0.65em;color:#AAAAAA;font-weight:700;'
                        f'text-transform:uppercase;letter-spacing:0.5px;">Target</div>'
                        f'<div style="font-size:0.85em;color:{text_col};font-weight:600;">'
                        f'{row["target"] or "—"}</div></div>'
                        f'<div><div style="font-size:0.65em;color:#AAAAAA;font-weight:700;'
                        f'text-transform:uppercase;letter-spacing:0.5px;">Owner</div>'
                        f'<div style="font-size:0.85em;color:{text_col};font-weight:600;">'
                        f'{row["owner"] or "—"}</div></div>'
                        f'</div>'
                    )
                else:
                    metric_html = (
                        '<div style="font-size:0.78em;color:#CCCCCC;">Pending</div>'
                    )

                cascade_html = (
                    f'<div style="font-size:0.75em;color:#888;margin-bottom:8px;'
                    f'padding:6px 10px;background:#F7F7F7;border-radius:4px;'
                    f'line-height:1.5;font-style:italic;">{row["cascade"]}</div>'
                )
                st.markdown(
                    f'<div style="border-left:2px solid #EEEEEE;padding:10px 14px 10px 16px;'
                    f'margin-left:4px;margin-bottom:2px;">'
                    f'<div style="font-size:0.72em;font-weight:700;color:{colour};'
                    f'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">'
                    f'{row["dept"]}</div>'
                    f'{cascade_html}'
                    f'{metric_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown('<div style="margin-bottom:16px;"></div>', unsafe_allow_html=True)

    _all_depts()
