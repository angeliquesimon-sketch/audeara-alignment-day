"""Strategy Cascade — facilitator page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL
from strategy_cascade_shared import (
    CHOICES, DEPARTMENTS, CHOICE_COLOURS,
    pull_cascade_session, set_cascade_session,
    pull_cascade_contributions, save_cascade_contribution,
    set_contribution_status, pull_cascade_confidence,
)

inject_styles()

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
    bc     = CHOICE_COLOURS[cur_idx % len(CHOICE_COLOURS)]

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
            row    = None
            status = 'none'
            text   = ''
            if not df.empty:
                match = df[(df['ChoiceID'] == choice['id']) & (df['Department'] == dept)]
                if not match.empty:
                    row    = match.iloc[0]
                    status = row['Status']
                    text   = row['Text']

            st.markdown(
                f'<div style="font-size:0.72em;font-weight:700;color:{bc};'
                f'letter-spacing:1px;margin-bottom:6px;">{dept.upper()}</div>',
                unsafe_allow_html=True,
            )

            if status == 'locked':
                st.markdown(
                    f'<div style="background:#E8F5EE;border-left:3px solid #3EAA6D;'
                    f'padding:10px 14px;border-radius:0 6px 6px 0;font-size:0.84em;'
                    f'color:#1a1a1a;margin-bottom:6px;">✅ {text}</div>',
                    unsafe_allow_html=True,
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button('Unlock to edit', key=f'fac_unlock_{choice["id"]}_{dept}', use_container_width=True):
                        set_contribution_status(choice['id'], dept, 'draft')
                        st.rerun()
                with c2:
                    if st.button('Opt out', key=f'fac_opt_{choice["id"]}_{dept}', use_container_width=True):
                        set_contribution_status(choice['id'], dept, 'opted_out')
                        st.rerun()

            elif status == 'opted_out':
                st.markdown(
                    f'<div style="background:#FAFAFA;border-left:3px solid #DDDDDD;'
                    f'padding:10px 14px;border-radius:0 6px 6px 0;font-size:0.84em;'
                    f'color:#AAAAAA;font-style:italic;margin-bottom:6px;">Not contributing to this choice</div>',
                    unsafe_allow_html=True,
                )
                if st.button('Restore', key=f'fac_restore_{choice["id"]}_{dept}', use_container_width=True):
                    set_contribution_status(choice['id'], dept, 'draft')
                    st.rerun()

            else:
                edited = st.text_area(
                    dept,
                    value=text,
                    height=72,
                    placeholder=f'Edit or type the agreed contribution for {dept}…',
                    key=f'fac_edit_{choice["id"]}_{dept}',
                    label_visibility='collapsed',
                )
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    if edited.strip() and edited.strip() != text:
                        if st.button('Save draft', key=f'fac_save_{choice["id"]}_{dept}', use_container_width=True):
                            save_cascade_contribution(choice['id'], dept, edited.strip())
                            st.rerun()
                with c2:
                    if st.button('✅ Lock', key=f'fac_lock_{choice["id"]}_{dept}', type='primary', use_container_width=True):
                        final = edited.strip() or text
                        if final:
                            set_contribution_status(choice['id'], dept, 'locked', text=final)
                            st.rerun()
                        else:
                            st.warning('Nothing to lock.')
                with c3:
                    if st.button('Opt out', key=f'fac_opt_{choice["id"]}_{dept}', use_container_width=True):
                        set_contribution_status(choice['id'], dept, 'opted_out')
                        st.rerun()

            st.markdown('')

        # Confidence results
        if not df_conf.empty:
            ch_conf = df_conf[df_conf['ChoiceID'] == choice['id']]
            if not ch_conf.empty:
                nums = []
                for v in ch_conf['Score'].tolist():
                    try: nums.append(int(v))
                    except: pass
                if nums:
                    st.divider()
                    avg = sum(nums) / len(nums)
                    n   = len(nums)
                    fc  = '#2D7D4F' if avg >= 4 else ('#B7770D' if avg >= 3 else '#C0392B')
                    bg  = '#E8F5EE' if avg >= 4 else ('#FEF5E7' if avg >= 3 else '#FDECEA')

                    st.markdown(
                        f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
                        f'color:#888;margin-bottom:10px;">CONFIDENCE VOTES</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div style="background:{bg};border-radius:8px;padding:14px 18px;'
                        f'text-align:center;margin-bottom:12px;">'
                        f'<div style="font-size:2em;font-weight:700;color:{fc};">{avg:.1f}</div>'
                        f'<div style="font-size:0.78em;color:{fc};">average · {n} vote{"s" if n!=1 else ""}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    for score in range(5, 0, -1):
                        count = nums.count(score)
                        pct   = count / n * 100 if n else 0
                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">'
                            f'<span style="font-size:0.76em;color:#888;width:14px;">{score}</span>'
                            f'<div style="flex:1;background:#E0E0E0;border-radius:4px;height:9px;">'
                            f'<div style="width:{pct:.0f}%;background:{fc};border-radius:4px;height:9px;"></div></div>'
                            f'<span style="font-size:0.72em;color:#888;width:18px;">{count}</span>'
                            f'</div>',
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
            bc     = CHOICE_COLOURS[i]
            locked = opted = pending = 0
            if not df_c.empty:
                ch      = df_c[df_c['ChoiceID'] == choice['id']]
                locked  = len(ch[ch['Status'] == 'locked'])
                opted   = len(ch[ch['Status'] == 'opted_out'])
                pending = len(DEPARTMENTS) - locked - opted

            conf_str = ''
            if not df_conf.empty:
                nums = []
                for v in df_conf[df_conf['ChoiceID'] == choice['id']]['Score'].tolist():
                    try: nums.append(int(v))
                    except: pass
                if nums:
                    conf_str = f'  ·  {sum(nums)/len(nums):.1f}/5'

            st.markdown(
                f'<div style="border-left:4px solid {bc};padding:10px 14px;'
                f'background:#F8F8F8;border-radius:0 6px 6px 0;margin-bottom:8px;">'
                f'<div style="font-weight:700;font-size:0.88em;color:{bc};">'
                f'{choice["number"]}. {choice["title"]}{conf_str}</div>'
                f'<div style="font-size:0.74em;color:#888;margin-top:4px;">'
                f'✅ {locked} locked · {opted} opted out · {pending} pending</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    _reveal_summary()

else:
    st.info('Advance to Cascade to manage department contributions.')
