"""The One Thing — participant page (Intro / Departmental / Personal tabs)."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL, with_retry, _clear_sheets
from one_thing_shared import (
    DEPARTMENTS, DEPARTMENT_MAP, DEPARTMENT_HEADS,
    ONE_THING_STAGES, ONE_THING_STAGE_LABELS,
    OPERATIONAL_FUNCTIONS, GOVERNANCE_FUNCTIONS, _fn_table_html,
    _ensure_one_thing_tabs,
    pull_one_thing_session, pull_one_thing_drafts,
    pull_one_thing_suggestions, save_one_thing_suggestion,
    pull_one_thing_winners, save_one_thing_winner,
)
from strategy_cascade_shared import (
    pull_commitments, save_commitment, pull_cascade_content,
)
from styles_shared import TEAM

inject_styles()

if not st.session_state.get('_one_thing_tabs_ready'):
    try:
        with_retry(_ensure_one_thing_tabs, on_retry=_clear_sheets)
        st.session_state['_one_thing_tabs_ready'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue — some features may not save correctly. ({_e})')

st.markdown('### The One Thing')

# ── Name selector ──────────────────────────────────────────────────────────────

name = st.selectbox('Your name', [''] + TEAM, key='ot_name')

if not name:
    st.caption('Select your name above to get started.')
    st.stop()

my_depts = DEPARTMENT_MAP.get(name, [])
is_dept_head = any(DEPARTMENT_HEADS.get(d) == name for d in my_depts)

tab_intro, tab_depts, tab_all, tab_personal = st.tabs([
    '💡 What is The One Thing?',
    '🏢 Functional One Things',
    '🌟 Our One Things',
    '✋ Your One Thing',
])

# ── Auto-refreshing stage gate ─────────────────────────────────────────────────

@st.fragment(run_every=5)
def _stage_check():
    pull_one_thing_session.clear()
    _new = pull_one_thing_session().get('stage', 'hidden')
    if _new != st.session_state.get('_ot_stage_last'):
        st.session_state['_ot_stage_last'] = _new
        st.rerun()

_stage_check()

session = pull_one_thing_session()
stage   = session.get('stage', 'hidden')

# ── Tab 1: Introduction ────────────────────────────────────────────────────────

with tab_intro:
    if stage == 'hidden':
        st.markdown(
            f'<div style="background:#F5F5F5;border-radius:10px;padding:28px;'
            f'text-align:center;color:#AAAAAA;font-size:0.9em;margin-top:8px;">'
            f'⏳  We\'ll get started shortly.<br>'
            f'<span style="font-size:0.85em;">Stay on this page.</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="font-size:0.85em;color:#888;margin-bottom:6px;">'
            f'You\'ve seen what each function is responsible for. Now the question is:'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("### What's the one thing you can do, such that by doing it, everything else becomes easier or unnecessary?")

        st.markdown(
            f'<div style="background:#F7F0F7;border-left:4px solid {PURPLE};'
            f'border-radius:0 8px 8px 0;padding:16px 20px;margin-bottom:16px;">'
            f'<div style="font-size:0.85em;font-weight:700;letter-spacing:2px;color:{PURPLE};margin-bottom:8px;">THE IDEA</div>'
            f'<div style="font-size:0.9em;color:#444;line-height:1.7;">'
            f'From Gary Keller\'s <em>The ONE Thing</em> — the idea that extraordinary results come not from doing more, '
            f'but from doing the right thing. When you identify the one action that makes everything else easier, '
            f'you stop spreading effort across too many priorities and start making real progress on what actually matters.'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        cols = st.columns(3)
        for col, (icon, heading, body) in zip(cols, [
            ('🎯', 'One lever, full reach', 'The right One Thing doesn\'t narrow what your function does — it\'s the action that moves all of it forward at once.'),
            ('🔗', 'Everything connects', 'The right One Thing at each level — company, team, individual — creates a chain of impact.'),
            ('📅', 'Today shapes tomorrow', 'Consistent daily focus on your One Thing compounds into results that scattered effort never reaches.'),
        ]):
            with col:
                st.markdown(
                    f'<div style="background:#F5F5F5;border-radius:8px;padding:14px 16px;">'
                    f'<div style="font-size:1.2em;margin-bottom:6px;">{icon}</div>'
                    f'<div style="font-weight:700;font-size:0.85em;color:#333;margin-bottom:4px;">{heading}</div>'
                    f'<div style="font-size:0.85em;color:#666;line-height:1.5;">{body}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('')
        st.markdown(
            f'<div style="background:#F0F8F8;border-left:4px solid {TEAL};'
            f'border-radius:0 8px 8px 0;padding:14px 20px;margin-bottom:20px;">'
            f'<div style="font-size:0.85em;font-weight:700;letter-spacing:2px;color:{TEAL};margin-bottom:6px;">TODAY</div>'
            f'<div style="font-size:0.9em;color:#444;line-height:1.6;">'
            f'The function tables below show what each function is responsible for. '
            f'Today we\'ll agree on the single action that will move all of it forward — '
            f'then you\'ll each commit to your personal One Thing for the year ahead. '
            f'These will be visible to the whole team.'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div style="border:1px solid #D0E8E8;border-radius:8px;background:#F4FBFB;'
            f'padding:16px 20px;margin-bottom:24px;">'
            f'<div style="font-size:0.85em;font-weight:700;letter-spacing:2px;color:{TEAL};margin-bottom:10px;">EXAMPLE — MARKETING</div>'
            f'<div style="font-size:0.85em;color:#555;line-height:1.6;margin-bottom:12px;">'
            f'Marketing is responsible for building brand awareness, driving demand, and communicating '
            f"Audeara's value across all channels — shaping the customer journey from first discovery "
            f'through to purchase and long-term engagement.'
            f'</div>'
            f'<div style="font-size:0.85em;font-weight:700;letter-spacing:1px;color:{TEAL};margin-bottom:6px;">THE ONE THING</div>'
            f'<div style="font-size:0.9em;font-weight:600;color:#1a1a1a;line-height:1.6;">'
            f'Make the customer outcome the starting point. Not the product, the channel, or the format.'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        ot_winners_intro = pull_one_thing_winners()
        st.markdown(
            _fn_table_html('OPERATIONAL FUNCTIONS', OPERATIONAL_FUNCTIONS, ot_winners_intro, show_lead=True) +
            _fn_table_html('GOVERNANCE &amp; OWNERSHIP', GOVERNANCE_FUNCTIONS, ot_winners_intro, show_lead=True),
            unsafe_allow_html=True,
        )

# ── Tab 2: Functional One Things ────────────────────────────────────────────

with tab_depts:
    if stage in ('hidden', 'intro'):
        st.markdown(
            f'<div style="background:#F5F5F5;border-radius:10px;padding:28px;'
            f'text-align:center;color:#AAAAAA;font-size:0.9em;">'
            f'⏳  This will open shortly.</div>',
            unsafe_allow_html=True,
        )
    else:
        @st.fragment(run_every=15)
        def _dept_section():
            drafts    = pull_one_thing_drafts()
            all_suggs = pull_one_thing_suggestions()
            winners   = pull_one_thing_winners()

            for dept in my_depts:
                draft  = drafts.get(dept, '')
                winner = winners.get(dept, '')
                head   = DEPARTMENT_HEADS.get(dept, '')
                i_am_head = (head == name)

                st.markdown(
                    f'<div style="font-weight:700;font-size:1em;color:{PURPLE};'
                    f'margin:16px 0 10px;">{dept}</div>',
                    unsafe_allow_html=True,
                )

                editing_winner = i_am_head and st.session_state.get(f'ot_dept_edit_{dept}', False)

                if winner and not editing_winner:
                    st.markdown(
                        f'<div style="background:#E8F5EE;border-left:4px solid #3EAA6D;'
                        f'border-radius:0 8px 8px 0;padding:14px 18px;margin-bottom:6px;">'
                        f'<div style="font-size:0.85em;font-weight:700;color:#2D7D4F;'
                        f'letter-spacing:1px;margin-bottom:6px;">AGREED ONE THING ✅</div>'
                        f'<div style="font-family:\'roc-grotesk\',sans-serif;font-feature-settings:\'ss01\' 1,\'ss02\' 1;font-size:0.9em;color:#1a1a1a;line-height:1.6;">{winner}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if i_am_head:
                        if st.button('Edit', key=f'ot_dept_edit_btn_{dept}', use_container_width=False):
                            st.session_state[f'ot_dept_edit_{dept}'] = True
                            st.rerun()
                elif winner and editing_winner:
                    st.markdown(
                        f'<div style="font-size:0.85em;font-weight:700;letter-spacing:1px;'
                        f'color:{TEAL};margin-bottom:6px;">UPDATE THE AGREED ONE THING</div>',
                        unsafe_allow_html=True,
                    )
                    winner_input = st.text_area(
                        f'Agreed One Thing for {dept}',
                        value=winner,
                        height=80,
                        key=f'ot_lock_{dept}',
                        label_visibility='collapsed',
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button('Cancel', key=f'ot_dept_cancel_{dept}', use_container_width=True):
                            st.session_state[f'ot_dept_edit_{dept}'] = False
                            st.rerun()
                    with c2:
                        if st.button(f'🔒 Update', key=f'ot_lock_btn_{dept}', type='primary', use_container_width=True):
                            if winner_input.strip():
                                try:
                                    save_one_thing_winner(dept, winner_input.strip(), name)
                                    st.cache_data.clear()
                                    st.session_state[f'ot_dept_edit_{dept}'] = False
                                    st.toast(f'{dept} One Thing updated ✓', icon='✅')
                                    st.rerun()
                                except Exception as _e:
                                    st.error(f'Could not update. ({_e})')
                            else:
                                st.warning('Type the agreed One Thing first.')
                elif draft:
                    st.markdown(
                        f'<div style="background:#F7F0F7;border-left:4px solid {PURPLE};'
                        f'border-radius:0 8px 8px 0;padding:14px 18px;margin-bottom:10px;">'
                        f'<div style="font-size:0.85em;font-weight:700;color:{PURPLE};'
                        f'letter-spacing:1px;margin-bottom:6px;">DRAFT ONE THING</div>'
                        f'<div style="font-size:0.9em;color:#1a1a1a;line-height:1.6;">{draft}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.info('No draft suggestion yet for this function.')

                # Suggestions from this dept
                dept_suggs = all_suggs[all_suggs['Department'] == dept] if not all_suggs.empty else all_suggs
                if not dept_suggs.empty:
                    st.markdown(
                        f'<div style="font-size:0.85em;font-weight:700;letter-spacing:1px;'
                        f'color:#888;margin:12px 0 6px;">TEAM SUGGESTIONS</div>',
                        unsafe_allow_html=True,
                    )
                    for _, row in dept_suggs.iterrows():
                        st.markdown(
                            f'<div style="border-left:3px solid #CCCCCC;padding:8px 14px;'
                            f'margin-bottom:6px;font-size:0.85em;color:#444;line-height:1.5;">'
                            f'{row["Suggestion"]}</div>',
                            unsafe_allow_html=True,
                        )

                # Suggestion form (not shown once winner is locked)
                if not winner:
                    already_suggested = (
                        not all_suggs.empty
                        and ((all_suggs['Name'] == name) & (all_suggs['Department'] == dept)).any()
                    )
                    if already_suggested:
                        st.caption('Your suggestion has been added.')
                    else:
                        with st.form(f'sugg_form_{dept}', clear_on_submit=True):
                            sugg = st.text_area(
                                'Suggest a refinement',
                                height=72,
                                placeholder='What would you change or add?',
                                label_visibility='collapsed',
                                key=f'sugg_input_{dept}',
                            )
                            if st.form_submit_button('Add suggestion', use_container_width=True):
                                if sugg.strip():
                                    try:
                                        save_one_thing_suggestion(name, dept, sugg.strip())
                                        st.toast('Suggestion added ✓', icon='✅')
                                        st.rerun()
                                    except Exception as _e:
                                        st.error(f'Could not save. ({_e})')
                                else:
                                    st.warning('Type a suggestion first.')

                # Winner lock (dept heads only, one dept at a time)
                if i_am_head and not winner:
                    st.markdown('')
                    st.markdown(
                        f'<div style="font-size:0.85em;font-weight:700;letter-spacing:1px;'
                        f'color:{TEAL};margin-bottom:6px;">LOCK THE AGREED ONE THING</div>',
                        unsafe_allow_html=True,
                    )
                    lock_key = f'ot_lock_{dept}'
                    winner_input = st.text_area(
                        f'Agreed One Thing for {dept}',
                        value=draft,
                        height=80,
                        key=lock_key,
                        label_visibility='collapsed',
                        placeholder='Type the agreed version here…',
                    )
                    if st.button(f'🔒 Lock for {dept}', key=f'ot_lock_btn_{dept}', type='primary'):
                        if winner_input.strip():
                            try:
                                save_one_thing_winner(dept, winner_input.strip(), name)
                                st.cache_data.clear()
                                st.toast(f'{dept} One Thing locked ✓', icon='✅')
                                st.rerun()
                            except Exception as _e:
                                st.error(f'Could not lock. ({_e})')
                        else:
                            st.warning('Type the agreed One Thing first.')

                if len(my_depts) > 1:
                    st.divider()

        _dept_section()

# ── Tab 3: Personal One Thing ─────────────────────────────────────────────────

with tab_personal:
    if stage in ('hidden', 'intro', 'departments'):
        st.markdown(
            f'<div style="background:#F5F5F5;border-radius:10px;padding:28px;'
            f'text-align:center;color:#AAAAAA;font-size:0.9em;">'
            f'⏳  This will open after the department discussion.</div>',
            unsafe_allow_html=True,
        )
    else:
        intro_text = (
            'Read through your departments\' One Things below, then write the single action '
            '<em>you</em> can commit to this year that will have the most impact. Be specific: '
            'what will you start, stop, or do more of?'
            if len(my_depts) > 1 else
            'Based on your department\'s One Thing — what\'s the single action <em>you</em> can commit to '
            'this year that will have the most impact on your function\'s goal? Be specific: '
            'what will you start, stop, or do more of?'
        )
        st.markdown(
            f'<div class="activity-card">{intro_text}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('')

        @st.fragment(run_every=15)
        def _personal_section():
            drafts  = pull_one_thing_drafts()
            winners = pull_one_thing_winners()
            goals_live, fn_live = pull_cascade_content()

            # Show ALL departments' One Things as context
            for dept in my_depts:
                one_thing_context = winners.get(dept) or drafts.get(dept) or fn_live.get(dept, '')
                if one_thing_context:
                    is_locked = bool(winners.get(dept))
                    bc = '#3EAA6D' if is_locked else PURPLE
                    bg = '#E8F5EE' if is_locked else '#F7F0F7'
                    label = 'AGREED ONE THING' if is_locked else 'DRAFT ONE THING'
                    st.markdown(
                        f'<div style="background:{bg};border-left:4px solid {bc};'
                        f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:10px;">'
                        f'<div style="font-size:0.85em;font-weight:700;color:{bc};'
                        f'letter-spacing:1px;margin-bottom:4px;">{label} — {dept.upper()}</div>'
                        f'<div style="font-size:0.9em;color:#333;line-height:1.6;">{one_thing_context}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown('')

            df_comm = pull_commitments()
            my_rows = df_comm[df_comm['Name'] == name] if not df_comm.empty else df_comm
            has_submitted = not my_rows.empty

            if has_submitted and not st.session_state.get(f'ot_edit_{name}'):
                commitment_text = my_rows.iloc[0]['Commitment']
                fn_labels = ' · '.join(my_rows['Function'].tolist())
                st.markdown(
                    f'<div style="border-left:4px solid #3EAA6D;background:#E8F5EE;'
                    f'border-radius:0 8px 8px 0;padding:14px 16px;">'
                    f'<div style="font-weight:700;color:#2D7D4F;margin-bottom:8px;">✅  Submitted</div>'
                    f'<div style="font-size:0.85em;color:#444;margin-bottom:2px;">'
                    f'<strong>Function{"s" if len(my_depts) > 1 else ""}:</strong> {fn_labels}</div>'
                    f'<div style="font-size:0.85em;color:#444;">'
                    f'<strong>One Thing:</strong> {commitment_text}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button('Edit my One Thing', key=f'ot_edit_btn_{name}'):
                    st.session_state[f'ot_edit_{name}'] = True
                    st.rerun()
                return

            default_commitment = my_rows.iloc[0]['Commitment'] if has_submitted else ''

            commitment = st.text_area(
                'My One Thing',
                value=default_commitment,
                height=100,
                placeholder='What one action, if you committed to it, would have the most impact?',
                key=f'ot_comm_{name}',
                label_visibility='collapsed',
            )

            st.markdown('')
            if st.button('Submit my One Thing', type='primary', key=f'ot_submit_{name}', use_container_width=True):
                if not commitment.strip():
                    st.warning('Please write your One Thing before submitting.')
                    return
                try:
                    for dept in my_depts:
                        save_commitment(name, dept, commitment.strip())
                    pull_commitments.clear()
                    st.session_state[f'ot_edit_{name}'] = False
                    st.toast('Your One Thing has been saved ✓', icon='✅')
                    st.rerun()
                except Exception as _e:
                    st.error(f'Could not save. ({_e})')

        _personal_section()

# ── Tab 4: Our One Things ─────────────────────────────────────────────────────

with tab_all:
    if stage in ('hidden', 'intro', 'departments'):
        st.markdown(
            f'<div style="background:#F5F5F5;border-radius:10px;padding:28px;'
            f'text-align:center;color:#AAAAAA;font-size:0.9em;">'
            f'⏳  The team\'s One Things will appear here once the facilitator opens this section.</div>',
            unsafe_allow_html=True,
        )
    else:
        @st.fragment(run_every=20)
        def _all_one_things():
            winners = pull_one_thing_winners()

            locked = {d: winners[d] for d in DEPARTMENTS if winners.get(d)}

            if not locked:
                st.markdown(
                    f'<div style="background:#F5F5F5;border-radius:10px;padding:28px;'
                    f'text-align:center;color:#AAAAAA;font-size:0.9em;">'
                    f'Functional One Things will appear here as they\'re agreed.</div>',
                    unsafe_allow_html=True,
                )
                return

            st.markdown(
                f'<div style="font-size:0.85em;font-weight:700;letter-spacing:2px;'
                f'color:#888;margin-bottom:16px;">AGREED ONE THINGS</div>',
                unsafe_allow_html=True,
            )

            for dept in DEPARTMENTS:
                w = winners.get(dept, '')
                if w:
                    st.markdown(
                        f'<div style="background:#E8F5EE;border-left:4px solid #3EAA6D;'
                        f'border-radius:0 8px 8px 0;padding:14px 18px;margin-bottom:10px;">'
                        f'<div style="font-size:0.85em;font-weight:700;color:#2D7D4F;'
                        f'letter-spacing:1px;margin-bottom:6px;">{dept.upper()}</div>'
                        f'<div style="font-size:0.9em;color:#1a1a1a;line-height:1.6;">{w}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div style="border-left:4px solid #DDDDDD;border-radius:0 8px 8px 0;'
                        f'padding:14px 18px;margin-bottom:10px;background:#FAFAFA;">'
                        f'<div style="font-size:0.85em;font-weight:700;color:#AAAAAA;'
                        f'letter-spacing:1px;margin-bottom:6px;">{dept.upper()}</div>'
                        f'<div style="font-size:0.85em;color:#BBBBBB;font-style:italic;">Still being agreed…</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        _all_one_things()
