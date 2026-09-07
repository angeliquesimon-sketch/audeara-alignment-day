"""Strategy Cascade — participant page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL, with_retry, _clear_sheets
from strategy_cascade_shared import (
    ENGINES, OPERATING_SYSTEM, CHOICES, HOW_WE_WORK, DEPARTMENTS,
    CHOICE_COLOURS, ENGINE_COLOURS,
    _ensure_cascade_tabs,
    pull_cascade_session, pull_cascade_contributions, save_cascade_contribution,
    pull_cascade_confidence, save_cascade_confidence,
)

inject_styles()

if not st.session_state.get('_cascade_tabs_ready'):
    try:
        with_retry(_ensure_cascade_tabs, on_retry=_clear_sheets)
        st.session_state['_cascade_tabs_ready'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue — some features may not save correctly. ({_e})')

st.markdown('### Strategy Cascade')

# ── Stage gate ─────────────────────────────────────────────────────────────────

@st.fragment(run_every=5)
def _stage_gate():
    pull_cascade_session.clear()
    sess = pull_cascade_session()
    sig  = f'{sess.get("stage","hidden")}_{sess.get("current_choice","0")}_{sess.get("confidence_open","0")}'
    if sig != st.session_state.get('_casc_sig_last'):
        st.session_state['_casc_sig_last'] = sig
        st.rerun()

_stage_gate()

session    = pull_cascade_session()
stage      = session.get('stage', 'hidden')
cur_idx    = int(session.get('current_choice', 0))
conf_open  = session.get('confidence_open', '0') == '1'

# ── Helpers ────────────────────────────────────────────────────────────────────

def _waiting(msg='This will open shortly.'):
    st.markdown(
        f'<div style="background:#F5F5F5;border-radius:10px;padding:32px;'
        f'text-align:center;color:#AAAAAA;font-size:0.9em;margin-top:8px;">⏳  {msg}</div>',
        unsafe_allow_html=True,
    )

def _section_label(text):
    st.markdown(
        f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
        f'color:#888;margin-bottom:16px;">{text}</div>',
        unsafe_allow_html=True,
    )

# ── hidden ─────────────────────────────────────────────────────────────────────

if stage == 'hidden':
    _waiting('James will open this session shortly.')

# ── engines ────────────────────────────────────────────────────────────────────

elif stage == 'engines':
    _section_label('THE COMPANY WE ARE BUILDING')
    st.markdown(
        f'<div style="font-size:0.88em;color:#555;line-height:1.7;margin-bottom:24px;">'
        f'Audeara is not simply a headphone company, a hearing-aid company, an app company or a '
        f'technology project. We are building one connected company with four commercial engines, '
        f'supported by a shared operating system.'
        f'</div>',
        unsafe_allow_html=True,
    )
    for i, engine in enumerate(ENGINES):
        bc = ENGINE_COLOURS[i]
        st.markdown(
            f'<div style="border-left:4px solid {bc};background:#F8F8F8;'
            f'border-radius:0 8px 8px 0;padding:16px 20px;margin-bottom:12px;">'
            f'<div style="font-weight:700;font-size:0.95em;color:{bc};">{engine["title"]}</div>'
            f'<div style="font-size:0.72em;color:#888;font-style:italic;margin-bottom:6px;">{engine["subtitle"]}</div>'
            f'<div style="font-size:0.84em;color:#555;line-height:1.6;">{engine["description"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    _section_label('ONE COMPANY OPERATING SYSTEM')
    for item in OPERATING_SYSTEM:
        st.markdown(
            f'<div style="border-left:3px solid {TEAL};padding:8px 14px;'
            f'margin-bottom:6px;font-size:0.84em;color:#444;">{item}</div>',
            unsafe_allow_html=True,
        )

# ── choices ────────────────────────────────────────────────────────────────────

elif stage == 'choices':
    _section_label('OUR SIX STRATEGIC CHOICES')
    for i, choice in enumerate(CHOICES):
        bc = CHOICE_COLOURS[i]
        st.markdown(
            f'<div style="border-left:4px solid {bc};background:#F8F8F8;'
            f'border-radius:0 8px 8px 0;padding:16px 20px;margin-bottom:12px;">'
            f'<div style="font-size:0.65em;font-weight:700;color:{bc};letter-spacing:1px;margin-bottom:4px;">{choice["number"]}</div>'
            f'<div style="font-weight:700;font-size:0.95em;color:#1a1a1a;margin-bottom:6px;">{choice["title"]}</div>'
            f'<div style="font-size:0.84em;color:#555;line-height:1.6;">{choice["description"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── working ────────────────────────────────────────────────────────────────────

elif stage == 'working':
    _section_label('HOW WE WILL WORK')
    for i, (principle, description) in enumerate(HOW_WE_WORK):
        bc = CHOICE_COLOURS[i % len(CHOICE_COLOURS)]
        st.markdown(
            f'<div style="border-left:4px solid {bc};background:#F8F8F8;'
            f'border-radius:0 8px 8px 0;padding:14px 20px;margin-bottom:10px;">'
            f'<div style="font-weight:700;font-size:0.92em;color:{bc};margin-bottom:4px;">{principle}</div>'
            f'<div style="font-size:0.84em;color:#555;line-height:1.6;">{description}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── cascade ────────────────────────────────────────────────────────────────────

elif stage == 'cascade':
    choice = CHOICES[min(cur_idx, len(CHOICES) - 1)]
    bc     = CHOICE_COLOURS[cur_idx % len(CHOICE_COLOURS)]

    # Choice header
    st.markdown(
        f'<div style="border-left:4px solid {bc};background:#F8F8F8;'
        f'border-radius:0 8px 8px 0;padding:18px 22px;margin-bottom:20px;">'
        f'<div style="font-size:0.65em;font-weight:700;color:{bc};letter-spacing:1px;margin-bottom:4px;">'
        f'STRATEGIC CHOICE {choice["number"]} OF {len(CHOICES)}</div>'
        f'<div style="font-weight:700;font-size:1.05em;color:#1a1a1a;margin-bottom:8px;">{choice["title"]}</div>'
        f'<div style="font-size:0.86em;color:#555;line-height:1.6;">{choice["description"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    _section_label('HOW EACH FUNCTION CONTRIBUTES')

    @st.fragment(run_every=8)
    def _contributions():
        df = pull_cascade_contributions()

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

            if status == 'locked':
                st.markdown(
                    f'<div style="background:#E8F5EE;border-left:4px solid #3EAA6D;'
                    f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:10px;">'
                    f'<div style="font-size:0.65em;font-weight:700;color:#2D7D4F;'
                    f'letter-spacing:1px;margin-bottom:4px;">{dept.upper()} ✅</div>'
                    f'<div style="font-size:0.86em;color:#1a1a1a;line-height:1.6;">{text}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            elif status == 'opted_out':
                st.markdown(
                    f'<div style="border-left:4px solid #DDDDDD;background:#FAFAFA;'
                    f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:10px;">'
                    f'<div style="font-size:0.65em;font-weight:700;color:#AAAAAA;letter-spacing:1px;margin-bottom:4px;">{dept.upper()}</div>'
                    f'<div style="font-size:0.82em;color:#BBBBBB;font-style:italic;">Not directly contributing to this choice.</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            else:
                # Draft or no submission yet — show editable field
                st.markdown(
                    f'<div style="font-size:0.72em;font-weight:700;color:{bc};'
                    f'letter-spacing:1px;margin-bottom:4px;">{dept.upper()}</div>',
                    unsafe_allow_html=True,
                )
                new_text = st.text_area(
                    dept,
                    value=text,
                    height=72,
                    placeholder=f'How does {dept} contribute to this?',
                    key=f'casc_ta_{choice["id"]}_{dept}',
                    label_visibility='collapsed',
                )
                if st.button(
                    'Submit for discussion',
                    key=f'casc_sub_{choice["id"]}_{dept}',
                    use_container_width=True,
                ):
                    if new_text.strip():
                        try:
                            save_cascade_contribution(choice['id'], dept, new_text.strip())
                            st.toast(f'{dept} submitted ✓', icon='💬')
                            st.rerun()
                        except Exception as _e:
                            st.error(f'Could not save. ({_e})')
                    else:
                        st.warning('Add a contribution before submitting.')
                st.markdown('')

        # Confidence vote (facilitator opens this per choice)
        if conf_open:
            st.divider()
            _section_label('TEAM CONFIDENCE — ANONYMOUS')
            if st.session_state.get(f'casc_conf_voted_{choice["id"]}'):
                st.success('Your vote has been recorded. Thank you.')
            else:
                score = st.select_slider(
                    'How confident are you that we will execute this choice well in FY27?',
                    options=[1, 2, 3, 4, 5],
                    value=3,
                    format_func=lambda x: {
                        1: '1 — Low', 2: '2', 3: '3 — Moderate', 4: '4', 5: '5 — High',
                    }[x],
                    key=f'casc_conf_slider_{choice["id"]}',
                )
                st.markdown('')
                if st.button(
                    'Submit vote anonymously',
                    type='primary',
                    key=f'casc_conf_btn_{choice["id"]}',
                    use_container_width=True,
                ):
                    try:
                        save_cascade_confidence(choice['id'], score)
                        st.session_state[f'casc_conf_voted_{choice["id"]}'] = True
                        st.rerun()
                    except Exception as _e:
                        st.error(f'Could not save. ({_e})')

    _contributions()

# ── reveal ─────────────────────────────────────────────────────────────────────

elif stage == 'reveal':
    _section_label('FY27 STRATEGY CASCADE')

    @st.fragment(run_every=30)
    def _reveal():
        df_c    = pull_cascade_contributions()
        df_conf = pull_cascade_confidence()

        for i, choice in enumerate(CHOICES):
            bc = CHOICE_COLOURS[i]

            # Confidence badge
            conf_badge = ''
            if not df_conf.empty:
                ch = df_conf[df_conf['ChoiceID'] == choice['id']]
                nums = []
                for v in ch['Score'].tolist():
                    try: nums.append(int(v))
                    except: pass
                if nums:
                    avg = sum(nums) / len(nums)
                    cbc = '#2D7D4F' if avg >= 4 else ('#B7770D' if avg >= 3 else '#C0392B')
                    cbg = '#E8F5EE' if avg >= 4 else ('#FEF5E7' if avg >= 3 else '#FDECEA')
                    conf_badge = (
                        f' <span style="font-size:0.8em;background:{cbg};color:{cbc};'
                        f'font-weight:700;padding:2px 10px;border-radius:10px;">'
                        f'{avg:.1f}/5</span>'
                    )

            st.markdown(
                f'<div style="border-left:4px solid {bc};padding:14px 18px;'
                f'background:#F8F8F8;border-radius:0 8px 8px 0;margin-bottom:6px;">'
                f'<div style="font-weight:700;font-size:0.92em;color:{bc};">'
                f'{choice["number"]}. {choice["title"]}{conf_badge}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if not df_c.empty:
                for dept in DEPARTMENTS:
                    match = df_c[
                        (df_c['ChoiceID'] == choice['id']) & (df_c['Department'] == dept)
                    ]
                    if match.empty:
                        continue
                    row    = match.iloc[0]
                    status = row['Status']
                    text   = row['Text']
                    if status == 'locked' and text:
                        st.markdown(
                            f'<div style="margin-left:20px;border-left:3px solid #3EAA6D;'
                            f'padding:8px 14px;margin-bottom:4px;font-size:0.83em;color:#333;line-height:1.5;">'
                            f'<strong style="color:#2D7D4F;">{dept}:</strong> {text}</div>',
                            unsafe_allow_html=True,
                        )
                    elif status == 'opted_out':
                        st.markdown(
                            f'<div style="margin-left:20px;border-left:3px solid #DDDDDD;'
                            f'padding:8px 14px;margin-bottom:4px;font-size:0.83em;'
                            f'color:#BBBBBB;font-style:italic;">{dept}: not contributing</div>',
                            unsafe_allow_html=True,
                        )

            st.markdown('<div style="margin-bottom:16px;"></div>', unsafe_allow_html=True)

    _reveal()
