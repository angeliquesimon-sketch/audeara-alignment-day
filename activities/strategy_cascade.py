"""Strategy Cascade — participant page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL, with_retry, _clear_sheets
from strategy_cascade_shared import (
    ENGINES, OPERATING_SYSTEM, CHOICES, HOW_WE_WORK, DEPARTMENTS,
    CHOICE_COLOURS, ENGINE_COLOURS, HOW_WE_WORK_ICONS,
    _ensure_cascade_tabs,
    pull_cascade_session, pull_cascade_contributions, save_cascade_contribution,
    pull_cascade_confidence, save_cascade_confidence,
    get_live_engines, get_live_os, get_live_choices, get_live_how,
)
from one_thing_shared import pull_one_thing_winners

inject_styles()

FOREST = '#005E63'
WINE   = '#50144B'
BLACK  = '#000000'

if not st.session_state.get('_cascade_tabs_ready'):
    try:
        with_retry(_ensure_cascade_tabs, on_retry=_clear_sheets)
        st.session_state['_cascade_tabs_ready'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue — some features may not save correctly. ({_e})')

st.markdown('### Strategy Cascade')

# ── Stage gate (outside tabs — always polling) ─────────────────────────────────

@st.fragment(run_every=5)
def _stage_gate():
    pull_cascade_session.clear()
    sess = pull_cascade_session()
    sig  = f'{sess.get("stage","hidden")}_{sess.get("current_choice","0")}_{sess.get("confidence_open","0")}'
    if sig != st.session_state.get('_casc_sig_last'):
        st.session_state['_casc_sig_last'] = sig
        st.rerun()

_stage_gate()

session   = pull_cascade_session()
stage     = session.get('stage', 'hidden')
cur_idx   = int(session.get('current_choice', 0))
conf_open = session.get('confidence_open', '0') == '1'

STAGE_ORDER = ['hidden', 'engines', 'working', 'choices', 'cascade', 'reveal']
stage_idx   = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 0

# ── Helpers ────────────────────────────────────────────────────────────────────

def _waiting(msg='This will open shortly.'):
    st.markdown(
        f'<div style="background:#F5F5F5;border-radius:10px;padding:32px;'
        f'text-align:center;color:#AAAAAA;font-size:0.95em;margin-top:8px;">⏳  {msg}</div>',
        unsafe_allow_html=True,
    )

def _section_label(text):
    st.markdown(
        f'<div style="font-size:0.84em;font-weight:700;letter-spacing:2px;'
        f'color:#888;margin-bottom:16px;">{text}</div>',
        unsafe_allow_html=True,
    )

def _collapsed_engines():
    pills = ''.join([
        f'<span style="background:{FOREST};color:white;font-size:0.84em;'
        f'font-weight:600;padding:4px 11px;border-radius:14px;margin-right:6px;'
        f'display:inline-block;margin-bottom:5px;">{e["title"]}</span>'
        for e in get_live_engines()
    ])
    st.markdown(
        f'<div style="background:#F4F4F4;border-radius:8px;padding:10px 14px;margin-bottom:10px;">'
        f'<div style="font-size:0.75em;font-weight:700;color:#AAAAAA;letter-spacing:1.5px;'
        f'margin-bottom:8px;">COMMERCIAL ENGINES</div>'
        f'{pills}</div>',
        unsafe_allow_html=True,
    )

def _collapsed_choices():
    pills = ''.join([
        f'<span style="background:{WINE};color:white;font-size:0.84em;'
        f'font-weight:600;padding:4px 11px;border-radius:14px;margin-right:6px;'
        f'display:inline-block;margin-bottom:5px;">{c["title"]}</span>'
        for c in get_live_choices()
    ])
    st.markdown(
        f'<div style="background:#F4F4F4;border-radius:8px;padding:10px 14px;margin-bottom:10px;">'
        f'<div style="font-size:0.75em;font-weight:700;color:#AAAAAA;letter-spacing:1.5px;'
        f'margin-bottom:8px;">FY27 STRATEGIC CHOICES</div>'
        f'{pills}</div>',
        unsafe_allow_html=True,
    )

def _collapsed_working():
    pills = ''.join([
        f'<span style="background:{WINE};color:white;'
        f'font-size:0.84em;font-weight:600;padding:4px 11px;border-radius:14px;'
        f'margin-right:6px;display:inline-block;margin-bottom:5px;">{principle}</span>'
        for principle, _ in get_live_how()
    ])
    st.markdown(
        f'<div style="background:#F4F4F4;border-radius:8px;padding:10px 14px;margin-bottom:10px;">'
        f'<div style="font-size:0.75em;font-weight:700;color:#AAAAAA;letter-spacing:1.5px;'
        f'margin-bottom:8px;">HOW WE OPERATE AS ONE COMPANY</div>'
        f'{pills}</div>',
        unsafe_allow_html=True,
    )

# ── Two tabs ───────────────────────────────────────────────────────────────────

tab_pres, tab_activity, tab_results = st.tabs(['📊 Presentation', '💬 Activity', '📋 Results'])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PRESENTATION  (cumulative cascade — each layer collapses as the next opens)
# ═══════════════════════════════════════════════════════════════════════════════

with tab_pres:

    if stage == 'hidden':
        _waiting('James will open this session shortly.')

    else:
        # Tab 1 never collapses — it is a permanent record of the full presentation

        # ENGINES ── show from stage_idx 1 onwards
        if stage_idx >= 1:
            _live_engines = get_live_engines()
            _section_label('Commercial Engines')
            _engine_cards = ''.join([
                f'<div style="border-left:4px solid {FOREST};background:#F8F8F8;'
                f'border-radius:0 6px 6px 0;padding:14px 16px;">'
                f'<div style="font-weight:700;font-size:1.05em;color:{FOREST};margin-bottom:2px;">{e["title"]}</div>'
                f'<div style="font-size:0.75em;color:#999;font-style:italic;margin-bottom:6px;">{e.get("subtitle","")}</div>'
                f'<div style="font-size:0.95em;color:#555;line-height:1.55;">{e["description"]}</div>'
                f'</div>'
                for e in _live_engines
            ])
            n_engines = len(_live_engines)
            _cols = f'repeat({n_engines}, 1fr)' if n_engines <= 5 else 'repeat(4,1fr)'
            st.markdown(
                f'<div style="display:grid;grid-template-columns:{_cols};'
                f'gap:8px;margin-bottom:0;">'
                f'{_engine_cards}'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── Engine detail accordions — stats chips + 2-col card grid ────────
            st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
            for _e in _live_engines:
                _secs = _e.get('sections', [])
                _stats = _e.get('stats', [])
                if not _secs and not _stats:
                    continue
                with st.expander(_e['title'], expanded=False):
                    if _stats:
                        _chips = ''.join([
                            f'<div style="background:{FOREST};color:white;border-radius:8px;'
                            f'padding:10px 20px;text-align:center;min-width:90px;">'
                            f'<div style="font-size:1.25em;font-weight:700;line-height:1.2;">{s[0]}</div>'
                            f'<div style="font-size:0.72em;opacity:0.75;margin-top:2px;">{s[1]}</div>'
                            f'</div>'
                            for s in _stats
                        ])
                        st.markdown(
                            f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;">{_chips}</div>',
                            unsafe_allow_html=True,
                        )
                    _cards = ''
                    for _sec in _secs:
                        _sec_title   = _sec.get('title', '')
                        _sec_content = _sec.get('content', [])
                        if isinstance(_sec_content, list):
                            _items = ''.join([f'<li style="margin-bottom:3px;">{item}</li>' for item in _sec_content])
                            _body  = f'<ul style="font-size:0.84em;color:#333;line-height:1.5;margin:0;padding-left:16px;">{_items}</ul>'
                        else:
                            _body  = f'<div style="font-size:0.84em;color:#333;line-height:1.5;">{_sec_content}</div>'
                        _cards += (
                            f'<div style="background:#F8F8F8;border-radius:8px;padding:13px 15px;">'
                            f'<div style="font-size:0.72em;font-weight:700;color:{FOREST};'
                            f'letter-spacing:1px;margin-bottom:7px;">{_sec_title.upper()}</div>'
                            f'{_body}</div>'
                        )
                    st.markdown(
                        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">{_cards}</div>',
                        unsafe_allow_html=True,
                    )


        # HOW WE OPERATE ── show from stage_idx 2 onwards (before choices)
        if stage_idx >= 2:
            _live_how = get_live_how()
            _how_items = ''.join([
                f'<div style="background:rgba(255,255,255,0.1);border-radius:8px;padding:10px 14px;">'
                f'<div style="font-size:0.95em;font-weight:600;color:white;margin-bottom:4px;">'
                f'{HOW_WE_WORK_ICONS[i] if i < len(HOW_WE_WORK_ICONS) else "•"}&nbsp;{principle}</div>'
                f'<div style="font-size:0.84em;color:rgba(255,255,255,0.65);line-height:1.5;">{description}</div>'
                f'</div>'
                for i, (principle, description) in enumerate(_live_how)
            ])
            st.markdown(
                f'<div style="background:{WINE};border-radius:10px;padding:18px 20px;margin-top:28px;">'
                f'<div style="font-size:0.75em;font-weight:700;color:rgba(255,255,255,0.4);'
                f'letter-spacing:1.5px;margin-bottom:6px;">HOW WE OPERATE AS ONE COMPANY</div>'
                f'<div style="font-size:0.84em;color:rgba(255,255,255,0.55);margin-bottom:14px;line-height:1.5;">'
                f'All engines run on the same foundation: customer insight, quality and regulatory discipline, '
                f'software and product capability, and commercial and governance functions.</div>'
                f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">'
                f'{_how_items}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # CHOICES ── show from stage_idx 3 onwards
        if stage_idx >= 3:
            _live_choices = get_live_choices()
            st.markdown('<div style="margin-top:28px;"></div>', unsafe_allow_html=True)
            _section_label('FY27 STRATEGIC CHOICES')
            _choice_cards = ''.join([
                f'<div style="border-left:4px solid {WINE};background:#F8F8F8;'
                f'border-radius:0 8px 8px 0;padding:14px 16px;">'
                f'<div style="font-weight:700;font-size:1.05em;color:#1a1a1a;margin-bottom:6px;">{c["title"]}</div>'
                + (
                    f'<div style="margin-bottom:8px;">'
                    f'<span style="background:{FOREST};color:white;font-size:0.75em;'
                    f'font-weight:600;padding:3px 9px;border-radius:10px;">'
                    f'{c["attribution"]}</span></div>'
                    if c.get('attribution') else ''
                ) +
                f'<div style="font-size:0.95em;color:#555;line-height:1.55;">{c["description"]}</div>'
                f'</div>'
                for c in _live_choices
            ])
            _n_choices = len(_live_choices)
            _c_cols = f'repeat({min(_n_choices, 4)},1fr)'
            st.markdown(
                f'<div style="display:grid;grid-template-columns:{_c_cols};'
                f'gap:10px;">{_choice_cards}</div>',
                unsafe_allow_html=True,
            )

            # ── Choice detail accordions ─────────────────────────────────────────
            st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
            for _c in _live_choices:
                _intro = _c.get('intro', '')
                _secs  = _c.get('sections', [])
                if not _intro and not _secs:
                    continue
                with st.expander(_c['title'], expanded=False):
                    if _intro:
                        st.markdown(
                            f'<div style="font-size:0.95em;color:#555;font-style:italic;'
                            f'line-height:1.6;margin-bottom:14px;">{_intro}</div>',
                            unsafe_allow_html=True,
                        )
                    for _sec in _secs:
                        _sec_title   = _sec.get('title', '')
                        _sec_content = _sec.get('content', [])
                        st.markdown(
                            f'<div style="font-size:0.84em;font-weight:700;color:{WINE};'
                            f'letter-spacing:1px;margin-top:12px;margin-bottom:5px;">'
                            f'{_sec_title.upper()}</div>',
                            unsafe_allow_html=True,
                        )
                        if isinstance(_sec_content, list):
                            _items = ''.join([
                                f'<li style="margin-bottom:4px;">{item}</li>'
                                for item in _sec_content
                            ])
                            st.markdown(
                                f'<ul style="font-size:0.95em;color:#333;line-height:1.6;'
                                f'margin:0;padding-left:18px;">{_items}</ul>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f'<div style="font-size:0.95em;color:#333;line-height:1.6;">'
                                f'{_sec_content}</div>',
                                unsafe_allow_html=True,
                            )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ACTIVITY / REVEAL
# ═══════════════════════════════════════════════════════════════════════════════

with tab_activity:

    if stage in ('hidden', 'engines', 'choices', 'working'):
        _waiting('The cascade discussion will open here when James is ready.')

    elif stage in ('cascade', 'reveal'):
        pass

    if stage == 'cascade':
        _act_choices = get_live_choices()
        choice = _act_choices[min(cur_idx, len(_act_choices) - 1)]
        bc     = WINE

        st.markdown(
            f'<div style="border-left:4px solid {bc};background:#F8F8F8;'
            f'border-radius:0 8px 8px 0;padding:18px 22px;margin-bottom:20px;">'
            f'<div style="font-size:0.75em;font-weight:700;color:{bc};letter-spacing:1px;margin-bottom:4px;">'
            f'STRATEGIC CHOICE {choice["number"]} OF {len(CHOICES)}</div>'
            f'<div style="font-weight:700;font-size:1.05em;color:#1a1a1a;margin-bottom:8px;">{choice["title"]}</div>'
            f'<div style="font-size:0.95em;color:#555;line-height:1.6;">{choice["description"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Choice detail accordion (same data source as Presentation tab) ──────
        _act_intro = choice.get('intro', '')
        _act_secs  = choice.get('sections', [])
        if _act_intro or _act_secs:
            with st.expander(choice['title'], expanded=False):
                if _act_intro:
                    st.markdown(
                        f'<div style="font-size:0.95em;color:#555;font-style:italic;'
                        f'line-height:1.6;margin-bottom:14px;">{_act_intro}</div>',
                        unsafe_allow_html=True,
                    )
                for _act_sec in _act_secs:
                    _act_sec_title   = _act_sec.get('title', '')
                    _act_sec_content = _act_sec.get('content', [])
                    st.markdown(
                        f'<div style="font-size:0.84em;font-weight:700;color:{WINE};'
                        f'letter-spacing:1px;margin-top:12px;margin-bottom:5px;">'
                        f'{_act_sec_title.upper()}</div>',
                        unsafe_allow_html=True,
                    )
                    if isinstance(_act_sec_content, list):
                        _act_items = ''.join([
                            f'<li style="margin-bottom:4px;">{item}</li>'
                            for item in _act_sec_content
                        ])
                        st.markdown(
                            f'<ul style="font-size:0.95em;color:#333;line-height:1.6;'
                            f'margin:0;padding-left:18px;">{_act_items}</ul>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div style="font-size:0.95em;color:#333;line-height:1.6;">'
                            f'{_act_sec_content}</div>',
                            unsafe_allow_html=True,
                        )

        _section_label('HOW EACH FUNCTION CONTRIBUTES')

        @st.fragment(run_every=8)
        def _contributions():
            df       = pull_cascade_contributions()
            winners  = pull_one_thing_winners()
            ch_c     = df[df['ChoiceID'] == choice['id']] if not df.empty else df

            for dept in DEPARTMENTS:
                dept_rows   = ch_c[ch_c['Department'] == dept] if not ch_c.empty else ch_c
                locked_rows = dept_rows[dept_rows['Status'] == 'locked'] if not dept_rows.empty else dept_rows
                draft_rows  = dept_rows[dept_rows['Status'] == 'draft']  if not dept_rows.empty else dept_rows
                is_opted    = (not dept_rows.empty
                               and dept_rows['Status'].eq('opted_out').any()
                               and locked_rows.empty and draft_rows.empty)

                # Department heading + One Thing ref
                one_thing = winners.get(dept, '')
                ot_text   = one_thing if one_thing else 'One Thing not yet agreed'
                ot_colour = '#777777' if one_thing else '#BBBBBB'
                st.markdown(
                    f'<div style="font-size:0.84em;font-weight:700;color:{bc};'
                    f'letter-spacing:1px;margin-bottom:0;">{dept.upper()}</div>'
                    f'<div style="font-size:0.75em;color:{ot_colour};font-style:italic;'
                    f'margin-top:2px;margin-bottom:8px;">Our One Thing: {ot_text}</div>',
                    unsafe_allow_html=True,
                )

                if is_opted:
                    st.markdown(
                        f'<div style="border-left:4px solid #DDDDDD;background:#FAFAFA;'
                        f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:10px;">'
                        f'<div style="font-size:0.75em;font-weight:700;color:#AAAAAA;'
                        f'letter-spacing:1px;margin-bottom:4px;">{dept.upper()}</div>'
                        f'<div style="font-size:0.95em;color:#BBBBBB;font-style:italic;">'
                        f'Not directly contributing to this choice.</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown('')
                    continue

                # ── Locked rows (first 3 by default) ─────────────────────────
                if not locked_rows.empty:
                    show_key = f'casc_show_all_{choice["id"]}_{dept}'
                    show_all = st.session_state.get(show_key, False)
                    visible  = locked_rows if show_all else locked_rows.iloc[:3]
                    for _, lrow in visible.iterrows():
                        pts = [p.strip() for p in str(lrow['Text']).split('\n') if p.strip()]
                        if len(pts) == 1:
                            lbody = f'<div style="font-size:0.95em;color:#1a1a1a;line-height:1.6;">{pts[0]}</div>'
                        else:
                            litems = ''.join([f'<li style="margin-bottom:4px;">{p}</li>' for p in pts])
                            lbody  = f'<ul style="font-size:0.95em;color:#1a1a1a;line-height:1.6;margin:4px 0 0 0;padding-left:18px;">{litems}</ul>'
                        st.markdown(
                            f'<div style="background:#E8F5EE;border-left:4px solid #3EAA6D;'
                            f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:6px;">'
                            f'<div style="font-size:0.75em;font-weight:700;color:#2D7D4F;'
                            f'letter-spacing:1px;margin-bottom:4px;">{dept.upper()} ✅</div>'
                            f'{lbody}</div>',
                            unsafe_allow_html=True,
                        )
                    n_hidden = len(locked_rows) - 3
                    if not show_all and n_hidden > 0:
                        if st.button(f'Show {n_hidden} more', key=f'casc_showmore_{choice["id"]}_{dept}', use_container_width=True):
                            st.session_state[show_key] = True
                            st.rerun()
                    elif show_all and len(locked_rows) > 3:
                        if st.button('Show less', key=f'casc_showless_{choice["id"]}_{dept}', use_container_width=True):
                            st.session_state[show_key] = False
                            st.rerun()

                # ── Draft rows (read-only on participant side) ─────────────────
                for _, drow in draft_rows.iterrows():
                    pts = [p.strip() for p in str(drow['Text']).split('\n') if p.strip()]
                    if len(pts) == 1:
                        dbody = f'<div style="font-size:0.95em;color:#1a1a1a;line-height:1.6;">{pts[0]}</div>'
                    else:
                        ditems = ''.join([f'<li style="margin-bottom:4px;">{p}</li>' for p in pts])
                        dbody  = f'<ul style="font-size:0.95em;color:#1a1a1a;line-height:1.6;margin:4px 0 0 0;padding-left:18px;">{ditems}</ul>'
                    st.markdown(
                        f'<div style="background:#FEF9E7;border-left:4px solid #F4B942;'
                        f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:6px;">'
                        f'<div style="font-size:0.75em;font-weight:700;color:#B7860D;'
                        f'letter-spacing:1px;margin-bottom:4px;">{dept.upper()} 💬 IN DISCUSSION</div>'
                        f'{dbody}</div>',
                        unsafe_allow_html=True,
                    )

                # ── Add new contribution (always visible) ──────────────────────
                n_rows   = len(dept_rows)
                new_text = st.text_area(
                    dept,
                    value='',
                    height=68,
                    placeholder=f'Add {dept}\'s contribution to this choice…',
                    key=f'casc_ta_new_{choice["id"]}_{dept}_{n_rows}',
                    label_visibility='collapsed',
                )
                if st.button(
                    'Submit for discussion',
                    key=f'casc_sub_new_{choice["id"]}_{dept}_{n_rows}',
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

            # Confidence vote (facilitator opens per choice)
            if conf_open:
                st.divider()
                _section_label('TEAM CONFIDENCE — ANONYMOUS')
                if st.session_state.get(f'casc_conf_voted_{choice["id"]}'):
                    st.success('Your vote has been recorded. Thank you.')
                else:
                    _fmt = lambda x: {1: '1 — Low', 2: '2', 3: '3 — Moderate', 4: '4', 5: '5 — High'}[x]
                    team_score = st.select_slider(
                        'How confident are you that we will execute this Strategic Choice well in FY27?',
                        options=[1, 2, 3, 4, 5],
                        value=3,
                        format_func=_fmt,
                        key=f'casc_conf_slider_{choice["id"]}',
                    )
                    st.markdown('')
                    func_score_raw = st.select_slider(
                        'If your function is contributing above, how confident are you that you can help contribute to this Strategic Choice in FY27?',
                        options=['N/A', 1, 2, 3, 4, 5],
                        value='N/A',
                        format_func=lambda x: x if x == 'N/A' else _fmt(x),
                        key=f'casc_conf_func_{choice["id"]}',
                    )
                    st.markdown('')
                    feedback = st.text_area(
                        'Feedback (optional)',
                        placeholder='Any thoughts on this choice — what would make it more likely to succeed?',
                        key=f'casc_conf_fb_{choice["id"]}',
                        height=80,
                    )
                    st.markdown('')
                    if st.button(
                        'Submit vote anonymously',
                        type='primary',
                        key=f'casc_conf_btn_{choice["id"]}',
                        use_container_width=True,
                    ):
                        try:
                            fs = '' if func_score_raw == 'N/A' else func_score_raw
                            save_cascade_confidence(choice['id'], team_score, fs, feedback.strip())
                            st.session_state[f'casc_conf_voted_{choice["id"]}'] = True
                            st.rerun()
                        except Exception as _e:
                            st.error(f'Could not save. ({_e})')

        _contributions()

    elif stage == 'reveal':
        _section_label('FY27 STRATEGY CASCADE')

        @st.fragment(run_every=30)
        def _reveal():
            df_c    = pull_cascade_contributions()
            df_conf = pull_cascade_confidence()

            for i, choice in enumerate(get_live_choices()):
                bc = WINE

                conf_badge = ''
                if not df_conf.empty:
                    ch = df_conf[df_conf['ChoiceID'] == choice['id']]
                    nums = []
                    for v in ch['TeamScore'].tolist():
                        try: nums.append(int(v))
                        except: pass
                    if nums:
                        avg = sum(nums) / len(nums)
                        cbc = '#2D7D4F' if avg >= 4 else ('#B7770D' if avg >= 3 else '#C0392B')
                        cbg = '#E8F5EE' if avg >= 4 else ('#FEF5E7' if avg >= 3 else '#FDECEA')
                        conf_badge = (
                            f' <span style="font-size:0.84em;background:{cbg};color:{cbc};'
                            f'font-weight:700;padding:2px 10px;border-radius:10px;">'
                            f'{avg:.1f}/5</span>'
                        )

                st.markdown(
                    f'<div style="border-left:4px solid {bc};padding:14px 18px;'
                    f'background:#F8F8F8;border-radius:0 8px 8px 0;margin-bottom:6px;">'
                    f'<div style="font-weight:700;font-size:1.05em;color:{bc};">'
                    f'{choice["number"]}. {choice["title"]}{conf_badge}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if not df_c.empty:
                    for dept in DEPARTMENTS:
                        dept_rows   = df_c[(df_c['ChoiceID'] == choice['id']) & (df_c['Department'] == dept)]
                        locked_rows = dept_rows[dept_rows['Status'] == 'locked'] if not dept_rows.empty else dept_rows
                        is_opted    = (not dept_rows.empty
                                       and dept_rows['Status'].eq('opted_out').any()
                                       and locked_rows.empty)
                        for _, row in locked_rows.iterrows():
                            if not row['Text']:
                                continue
                            pts = [p.strip() for p in str(row['Text']).split('\n') if p.strip()]
                            if len(pts) == 1:
                                body = f'<strong style="color:#2D7D4F;">{dept}:</strong> {pts[0]}'
                            else:
                                items = ''.join([f'<li>{p}</li>' for p in pts])
                                body  = f'<strong style="color:#2D7D4F;">{dept}:</strong><ul style="margin:4px 0 0 0;padding-left:18px;">{items}</ul>'
                            st.markdown(
                                f'<div style="margin-left:20px;border-left:3px solid #3EAA6D;'
                                f'padding:8px 14px;margin-bottom:4px;font-size:0.95em;'
                                f'color:#333;line-height:1.5;">{body}</div>',
                                unsafe_allow_html=True,
                            )
                        if is_opted:
                            st.markdown(
                                f'<div style="margin-left:20px;border-left:3px solid #DDDDDD;'
                                f'padding:8px 14px;margin-bottom:4px;font-size:0.95em;'
                                f'color:#BBBBBB;font-style:italic;">{dept}: not contributing</div>',
                                unsafe_allow_html=True,
                            )

                st.markdown('<div style="margin-bottom:16px;"></div>', unsafe_allow_html=True)

        _reveal()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_results:

    @st.fragment(run_every=20)
    def _results():
        df_c    = pull_cascade_contributions()
        df_conf = pull_cascade_confidence()

        any_data = (not df_c.empty) or (not df_conf.empty)

        if not any_data:
            st.markdown(
                f'<div style="background:#F5F5F5;border-radius:10px;padding:28px;'
                f'text-align:center;color:#AAAAAA;font-size:0.95em;">'
                f'⏳  Results will appear here as the team works through each Strategic Choice.</div>',
                unsafe_allow_html=True,
            )
            return

        for choice in get_live_choices():
            # ── Confidence scores for this choice ──────────────────────────────
            team_nums = []
            func_nums = []
            feedbacks = []
            if not df_conf.empty:
                ch_conf = df_conf[df_conf['ChoiceID'] == choice['id']]
                for _, crow in ch_conf.iterrows():
                    try: team_nums.append(int(crow['TeamScore']))
                    except: pass
                    try: func_nums.append(int(crow['FunctionScore']))
                    except: pass
                    fb = str(crow.get('Feedback', '')).strip()
                    if fb:
                        feedbacks.append(fb)

            # ── Contributions for this choice ───────────────────────────────────
            locked_contribs = []
            if not df_c.empty:
                ch_c = df_c[df_c['ChoiceID'] == choice['id']]
                for dept in DEPARTMENTS:
                    dept_locked = ch_c[(ch_c['Department'] == dept) & (ch_c['Status'] == 'locked')]
                    for _, row in dept_locked.iterrows():
                        if row['Text']:
                            locked_contribs.append((dept, row['Text']))

            # Skip choices with nothing at all
            if not team_nums and not locked_contribs:
                continue

            # ── Choice header with inline confidence badge(s) ──────────────────
            badge_html = ''
            if team_nums:
                t_avg = sum(team_nums) / len(team_nums)
                t_n   = len(team_nums)
                t_fc  = '#2D7D4F' if t_avg >= 4 else ('#B7770D' if t_avg >= 3 else '#C0392B')
                t_bg  = '#E8F5EE' if t_avg >= 4 else ('#FEF5E7' if t_avg >= 3 else '#FDECEA')
                badge_html += (
                    f'<span style="font-size:0.84em;background:{t_bg};color:{t_fc};'
                    f'font-weight:700;padding:2px 9px;border-radius:10px;margin-left:8px;">'
                    f'Team {t_avg:.1f}/5 ({t_n})</span>'
                )
            if func_nums:
                f_avg = sum(func_nums) / len(func_nums)
                f_n   = len(func_nums)
                f_fc  = '#2D7D4F' if f_avg >= 4 else ('#B7770D' if f_avg >= 3 else '#C0392B')
                f_bg  = '#E8F5EE' if f_avg >= 4 else ('#FEF5E7' if f_avg >= 3 else '#FDECEA')
                badge_html += (
                    f'<span style="font-size:0.84em;background:{f_bg};color:{f_fc};'
                    f'font-weight:700;padding:2px 9px;border-radius:10px;margin-left:6px;">'
                    f'Function {f_avg:.1f}/5 ({f_n})</span>'
                )

            st.markdown(
                f'<div style="border-left:4px solid {WINE};padding:14px 18px;'
                f'background:#F8F8F8;border-radius:0 8px 8px 0;margin-bottom:10px;">'
                f'<div style="font-weight:700;font-size:1.05em;color:{WINE};">'
                f'{choice["number"]}. {choice["title"]}{badge_html}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── Contribution statements ─────────────────────────────────────────
            if locked_contribs:
                for dept, text in locked_contribs:
                    points = [p.strip() for p in text.split('\n') if p.strip()]
                    if len(points) == 1:
                        body = f'<span style="color:#333;">{points[0]}</span>'
                    else:
                        items = ''.join([f'<li style="margin-bottom:3px;">{p}</li>' for p in points])
                        body  = f'<ul style="margin:4px 0 0 0;padding-left:18px;color:#333;">{items}</ul>'
                    st.markdown(
                        f'<div style="margin-left:4px;border-left:3px solid {WINE};'
                        f'padding:8px 14px;margin-bottom:6px;background:#FDF8FC;border-radius:0 6px 6px 0;">'
                        f'<div style="font-size:0.75em;font-weight:700;color:{WINE};'
                        f'letter-spacing:1px;margin-bottom:4px;">{dept.upper()}</div>'
                        f'<div style="font-size:0.95em;line-height:1.6;">{body}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    f'<div style="font-size:0.95em;color:#BBBBBB;font-style:italic;'
                    f'margin-left:4px;margin-bottom:6px;">No contributions locked yet.</div>',
                    unsafe_allow_html=True,
                )

            # ── Feedback ────────────────────────────────────────────────────────
            if feedbacks:
                st.markdown(
                    f'<div style="font-size:0.75em;font-weight:700;color:#888;'
                    f'letter-spacing:1px;margin:8px 0 5px 4px;">FEEDBACK</div>',
                    unsafe_allow_html=True,
                )
                for fb in feedbacks:
                    st.markdown(
                        f'<div style="margin-left:4px;background:#F8F8F8;border-left:3px solid #DDDDDD;'
                        f'padding:7px 12px;border-radius:0 6px 6px 0;font-size:0.95em;'
                        f'color:#555;margin-bottom:4px;">{fb}</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown('<div style="margin-bottom:20px;"></div>', unsafe_allow_html=True)

    _results()
