"""Strategy Cascade — facilitator page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL
from strategy_cascade_shared import (
    CHOICES, DEPARTMENTS, CHOICE_COLOURS,
    pull_cascade_session, set_cascade_session,
    pull_cascade_contributions, save_cascade_contribution,
    update_contribution, set_dept_opted_out, restore_dept,
    pull_cascade_confidence,
)

inject_styles()

WINE = '#50144B'

st.markdown('### 🎛️ Facilitate — Strategy Cascade')

session   = pull_cascade_session()
stage     = session.get('stage', 'hidden')
cur_idx   = int(session.get('current_choice', 0))
conf_open = session.get('confidence_open', '0') == '1'

STAGE_LABELS = {
    'hidden':  'Hidden',
    'engines': 'Commercial Engines',
    'choices': 'Strategic Choices',
    'working': 'How We Will Work',
    'cascade': 'Cascade',
    'reveal':  'Full Reveal',
}
STAGES = list(STAGE_LABELS)

# ── Stage selector ─────────────────────────────────────────────────────────────

st.markdown(
    f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
    f'color:#888;margin-bottom:10px;">PRESENTATION STAGE</div>',
    unsafe_allow_html=True,
)
cols = st.columns(len(STAGES))
for col, s in zip(cols, STAGES):
    with col:
        if st.button(
            STAGE_LABELS[s],
            key=f'stage_btn_{s}',
            type='primary' if stage == s else 'secondary',
            use_container_width=True,
        ):
            kwargs = {'stage': s}
            if s != 'cascade':
                kwargs['confidence_open'] = '0'
            set_cascade_session(**kwargs)
            st.rerun()

st.divider()

# ── Cascade controls ───────────────────────────────────────────────────────────

if stage == 'cascade':
    choice = CHOICES[min(cur_idx, len(CHOICES) - 1)]
    bc     = WINE

    st.markdown(
        f'<div style="border-left:4px solid {bc};background:#F8F8F8;'
        f'border-radius:0 8px 8px 0;padding:14px 18px;margin-bottom:16px;">'
        f'<div style="font-size:0.65em;font-weight:700;color:{bc};letter-spacing:1px;margin-bottom:4px;">'
        f'CHOICE {choice["number"]} OF {len(CHOICES)}</div>'
        f'<div style="font-weight:700;font-size:0.95em;color:#1a1a1a;">{choice["title"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    nav_l, nav_r = st.columns(2)
    with nav_l:
        if cur_idx > 0 and st.button('← Previous choice', use_container_width=True):
            set_cascade_session(current_choice=cur_idx - 1, confidence_open='0')
            st.rerun()
    with nav_r:
        if cur_idx < len(CHOICES) - 1:
            if st.button('Next choice →', type='primary', use_container_width=True):
                set_cascade_session(current_choice=cur_idx + 1, confidence_open='0')
                st.rerun()
        else:
            if st.button('Move to Full Reveal →', type='primary', use_container_width=True):
                set_cascade_session(stage='reveal', confidence_open='0')
                st.rerun()

    st.markdown('')

    if conf_open:
        if st.button('🔒 Close confidence vote', use_container_width=True):
            set_cascade_session(confidence_open='0')
            st.rerun()
    else:
        if st.button('📊 Open confidence vote (anonymous)', use_container_width=True):
            set_cascade_session(confidence_open='1')
            st.rerun()

    st.divider()

    @st.fragment(run_every=6)
    def _fac_contributions():
        df      = pull_cascade_contributions()
        df_conf = pull_cascade_confidence()

        st.markdown(
            f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
            f'color:#888;margin-bottom:14px;">DEPARTMENT CONTRIBUTIONS</div>',
            unsafe_allow_html=True,
        )

        for dept in DEPARTMENTS:
            dept_rows   = df[(df['ChoiceID'] == choice['id']) & (df['Department'] == dept)] if not df.empty else df
            locked_rows = dept_rows[dept_rows['Status'] == 'locked'] if not dept_rows.empty else dept_rows
            draft_rows  = dept_rows[dept_rows['Status'] == 'draft']  if not dept_rows.empty else dept_rows
            is_opted    = (not dept_rows.empty
                           and dept_rows['Status'].eq('opted_out').any()
                           and locked_rows.empty and draft_rows.empty)
            n_active    = len(locked_rows) + len(draft_rows)

            st.markdown(
                f'<div style="font-size:0.72em;font-weight:700;color:{bc};'
                f'letter-spacing:1px;margin-bottom:6px;">{dept.upper()}</div>',
                unsafe_allow_html=True,
            )

            if is_opted:
                st.markdown(
                    f'<div style="background:#FAFAFA;border-left:3px solid #DDDDDD;'
                    f'padding:10px 14px;border-radius:0 6px 6px 0;font-size:0.84em;'
                    f'color:#AAAAAA;font-style:italic;margin-bottom:6px;">Not contributing to this choice</div>',
                    unsafe_allow_html=True,
                )
                if st.button('Restore', key=f'fac_restore_{choice["id"]}_{dept}', use_container_width=True):
                    restore_dept(choice['id'], dept)
                    st.rerun()
            else:
                # ── All active rows — keyed on Timestamp so indices never shift ──
                for _, row in locked_rows.iterrows():
                    ts   = row['Timestamp']
                    text = row['Text']
                    pts  = [p.strip() for p in str(text).split('\n') if p.strip()]
                    if len(pts) == 1:
                        rbody = f'✅ {pts[0]}'
                    else:
                        items = ''.join([f'<li>{p}</li>' for p in pts])
                        rbody = f'✅<ul style="margin:4px 0 0 0;padding-left:18px;">{items}</ul>'
                    st.markdown(
                        f'<div style="background:#E8F5EE;border-left:3px solid #3EAA6D;'
                        f'padding:10px 14px;border-radius:0 6px 6px 0;font-size:0.84em;'
                        f'color:#1a1a1a;margin-bottom:4px;">{rbody}</div>',
                        unsafe_allow_html=True,
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button('Unlock', key=f'fac_unlock_{ts}', use_container_width=True):
                            update_contribution(ts, new_status='draft')
                            st.rerun()
                    with c2:
                        if st.button('Delete', key=f'fac_del_l_{ts}', use_container_width=True):
                            update_contribution(ts, new_status='deleted')
                            st.rerun()

                for _, row in draft_rows.iterrows():
                    ts   = row['Timestamp']
                    text = row['Text']
                    pts  = [p.strip() for p in str(text).split('\n') if p.strip()]
                    if len(pts) == 1:
                        dbody = f'<div style="font-size:0.84em;color:#1a1a1a;line-height:1.6;">💬 {pts[0]}</div>'
                    else:
                        ditems = ''.join([f'<li style="margin-bottom:3px;">{p}</li>' for p in pts])
                        dbody  = (f'<div style="font-size:0.76em;color:#B7860D;margin-bottom:3px;">💬 IN DISCUSSION</div>'
                                  f'<ul style="font-size:0.84em;color:#1a1a1a;line-height:1.6;margin:0;padding-left:18px;">{ditems}</ul>')
                    st.markdown(
                        f'<div style="background:#FEF9E7;border-left:3px solid #F4B942;'
                        f'padding:10px 14px;border-radius:0 6px 6px 0;margin-bottom:4px;">'
                        f'{dbody}</div>',
                        unsafe_allow_html=True,
                    )
                    edited = st.text_area(
                        ts,
                        value=text,
                        height=56,
                        placeholder='Edit before locking…',
                        key=f'fac_edit_{ts}',
                        label_visibility='collapsed',
                    )
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        if edited.strip() and edited.strip() != text:
                            if st.button('Save edit', key=f'fac_save_{ts}', use_container_width=True):
                                update_contribution(ts, new_text=edited.strip())
                                st.rerun()
                    with c2:
                        if st.button('✅ Lock', key=f'fac_lock_{ts}', type='primary', use_container_width=True):
                            final = edited.strip() or text
                            if final:
                                update_contribution(ts, new_status='locked', new_text=final)
                                st.rerun()
                            else:
                                st.warning('Nothing to lock.')
                    with c3:
                        if st.button('Delete', key=f'fac_del_d_{ts}', use_container_width=True):
                            update_contribution(ts, new_status='deleted')
                            st.rerun()

                # ── Add new contribution ───────────────────────────────────────
                st.markdown('<div style="margin-top:4px;"></div>', unsafe_allow_html=True)
                new_text = st.text_area(
                    f'{dept} new',
                    value='',
                    height=56,
                    placeholder=f'Add a contribution for {dept}…',
                    key=f'fac_add_{choice["id"]}_{dept}_{n_active}',
                    label_visibility='collapsed',
                )
                c1, c2 = st.columns([3, 1])
                with c1:
                    if st.button('Add', key=f'fac_addbtn_{choice["id"]}_{dept}_{n_active}', use_container_width=True):
                        if new_text.strip():
                            save_cascade_contribution(choice['id'], dept, new_text.strip())
                            st.rerun()
                        else:
                            st.warning('Nothing to add.')
                with c2:
                    if st.button('No contrib', key=f'fac_opt_{choice["id"]}_{dept}', use_container_width=True):
                        set_dept_opted_out(choice['id'], dept)
                        st.rerun()

            st.markdown('')

        # Confidence results
        if not df_conf.empty:
            ch_conf = df_conf[df_conf['ChoiceID'] == choice['id']]
            if not ch_conf.empty:
                team_nums = []
                func_nums = []
                feedbacks = []
                for _, crow in ch_conf.iterrows():
                    try: team_nums.append(int(crow['TeamScore']))
                    except: pass
                    try:
                        fs = int(crow['FunctionScore'])
                        func_nums.append(fs)
                    except: pass
                    fb = str(crow.get('Feedback', '')).strip()
                    if fb:
                        feedbacks.append(fb)

                if team_nums:
                    st.divider()
                    n    = len(team_nums)
                    avg  = sum(team_nums) / n
                    fc   = '#2D7D4F' if avg >= 4 else ('#B7770D' if avg >= 3 else '#C0392B')
                    bg   = '#E8F5EE' if avg >= 4 else ('#FEF5E7' if avg >= 3 else '#FDECEA')

                    st.markdown(
                        f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
                        f'color:#888;margin-bottom:10px;">CONFIDENCE VOTES</div>',
                        unsafe_allow_html=True,
                    )

                    col_t, col_f = st.columns(2)
                    with col_t:
                        st.markdown(
                            f'<div style="font-size:0.65em;color:#888;font-weight:700;'
                            f'letter-spacing:1px;margin-bottom:6px;">TEAM EXECUTION</div>'
                            f'<div style="background:{bg};border-radius:8px;padding:12px 16px;'
                            f'text-align:center;margin-bottom:10px;">'
                            f'<div style="font-size:1.9em;font-weight:700;color:{fc};">{avg:.1f}</div>'
                            f'<div style="font-size:0.74em;color:{fc};">avg · {n} vote{"s" if n!=1 else ""}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        for score in range(5, 0, -1):
                            count = team_nums.count(score)
                            pct   = count / n * 100
                            st.markdown(
                                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
                                f'<span style="font-size:0.76em;color:#888;width:14px;">{score}</span>'
                                f'<div style="flex:1;background:#E0E0E0;border-radius:4px;height:8px;">'
                                f'<div style="width:{pct:.0f}%;background:{fc};border-radius:4px;height:8px;"></div></div>'
                                f'<span style="font-size:0.72em;color:#888;width:18px;">{count}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                    with col_f:
                        if func_nums:
                            fa    = sum(func_nums) / len(func_nums)
                            fn    = len(func_nums)
                            ffc   = '#2D7D4F' if fa >= 4 else ('#B7770D' if fa >= 3 else '#C0392B')
                            fbg   = '#E8F5EE' if fa >= 4 else ('#FEF5E7' if fa >= 3 else '#FDECEA')
                            st.markdown(
                                f'<div style="font-size:0.65em;color:#888;font-weight:700;'
                                f'letter-spacing:1px;margin-bottom:6px;">FUNCTION CONFIDENCE</div>'
                                f'<div style="background:{fbg};border-radius:8px;padding:12px 16px;'
                                f'text-align:center;margin-bottom:10px;">'
                                f'<div style="font-size:1.9em;font-weight:700;color:{ffc};">{fa:.1f}</div>'
                                f'<div style="font-size:0.74em;color:{ffc};">avg · {fn} response{"s" if fn!=1 else ""}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            for score in range(5, 0, -1):
                                count = func_nums.count(score)
                                pct   = count / fn * 100
                                st.markdown(
                                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
                                    f'<span style="font-size:0.76em;color:#888;width:14px;">{score}</span>'
                                    f'<div style="flex:1;background:#E0E0E0;border-radius:4px;height:8px;">'
                                    f'<div style="width:{pct:.0f}%;background:{ffc};border-radius:4px;height:8px;"></div></div>'
                                    f'<span style="font-size:0.72em;color:#888;width:18px;">{count}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.markdown(
                                f'<div style="font-size:0.65em;color:#888;font-weight:700;'
                                f'letter-spacing:1px;margin-bottom:6px;">FUNCTION CONFIDENCE</div>'
                                f'<div style="color:#BBBBBB;font-size:0.8em;font-style:italic;'
                                f'padding:10px 0;">No function responses yet</div>',
                                unsafe_allow_html=True,
                            )

                    if feedbacks:
                        st.markdown(
                            f'<div style="font-size:0.65em;font-weight:700;color:#888;'
                            f'letter-spacing:1px;margin:10px 0 6px;">FEEDBACK</div>',
                            unsafe_allow_html=True,
                        )
                        for fb in feedbacks:
                            st.markdown(
                                f'<div style="background:#F8F8F8;border-left:3px solid #DDDDDD;'
                                f'padding:8px 12px;border-radius:0 6px 6px 0;font-size:0.82em;'
                                f'color:#444;margin-bottom:5px;">{fb}</div>',
                                unsafe_allow_html=True,
                            )

    _fac_contributions()

elif stage == 'reveal':
    st.success('Full cascade is now visible to all participants.')

    @st.fragment(run_every=15)
    def _reveal_summary():
        df_c    = pull_cascade_contributions()
        df_conf = pull_cascade_confidence()

        for i, choice in enumerate(CHOICES):
            bc     = WINE
            locked = opted = pending = 0
            if not df_c.empty:
                ch      = df_c[df_c['ChoiceID'] == choice['id']]
                locked  = len(ch[ch['Status'] == 'locked'])
                opted   = len(ch[ch['Status'] == 'opted_out'])
                pending = len(DEPARTMENTS) - locked - opted

            conf_str = ''
            if not df_conf.empty:
                nums = []
                for v in df_conf[df_conf['ChoiceID'] == choice['id']]['TeamScore'].tolist():
                    try: nums.append(int(v))
                    except: pass
                if nums:
                    conf_str = f'  ·  {sum(nums)/len(nums):.1f}/5'

            n_locked_depts = ch['Department'][ch['Status'] == 'locked'].nunique() if not df_c.empty else 0
            n_opted_depts  = ch['Department'][ch['Status'] == 'opted_out'].nunique() if not df_c.empty else 0
            n_locked_items = int((ch['Status'] == 'locked').sum()) if not df_c.empty else 0
            n_pending      = len(DEPARTMENTS) - n_locked_depts - n_opted_depts

            st.markdown(
                f'<div style="border-left:4px solid {bc};padding:10px 14px;'
                f'background:#F8F8F8;border-radius:0 6px 6px 0;margin-bottom:8px;">'
                f'<div style="font-weight:700;font-size:0.88em;color:{bc};">'
                f'{choice["number"]}. {choice["title"]}{conf_str}</div>'
                f'<div style="font-size:0.74em;color:#888;margin-top:4px;">'
                f'✅ {n_locked_depts} dept{"s" if n_locked_depts!=1 else ""} locked '
                f'({n_locked_items} contribution{"s" if n_locked_items!=1 else ""}) · '
                f'{n_opted_depts} opted out · {n_pending} pending</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    _reveal_summary()

else:
    st.info('Advance to Cascade to manage department contributions.')
