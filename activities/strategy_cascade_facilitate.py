"""Strategy Cascade — facilitator page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL
from strategy_cascade_shared import (
    CHOICES, DEPARTMENTS, CHOICE_COLOURS, HOW_WE_WORK_ICONS,
    pull_cascade_session, set_cascade_session,
    pull_cascade_contributions, save_cascade_contribution,
    update_contribution, set_dept_opted_out, restore_dept,
    pull_cascade_confidence,
    get_live_engines, get_live_os, get_live_choices, get_live_how,
    save_cascade_content_section, pull_cascade_content_overrides,
)

inject_styles()

WINE   = '#50144B'
FOREST = '#005E63'

st.markdown('### 🎛️ Facilitate — Strategy Cascade')

session   = pull_cascade_session()
stage     = session.get('stage', 'hidden')
cur_idx   = int(session.get('current_choice', 0))
conf_open = session.get('confidence_open', '0') == '1'

STAGE_LABELS = {
    'hidden':  'Hidden',
    'engines': 'Commercial Engines',
    'working': 'How We Operate',
    'choices': 'Strategic Choices',
    'cascade': 'Cascade',
    'reveal':  'Full Reveal',
}
STAGES = list(STAGE_LABELS)

# ── View selector (Facilitate vs Edit Content) ─────────────────────────────────

_view_col, _ = st.columns([3, 2])
with _view_col:
    _page_view = st.radio(
        'view', ['🎛️ Facilitate', '📝 Edit Content'],
        horizontal=True, label_visibility='collapsed',
        key='fac_page_view',
    )

if _page_view == '📝 Edit Content':

    st.markdown(
        f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
        f'color:#888;margin-bottom:4px;">PRESENTATION CONTENT EDITOR</div>',
        unsafe_allow_html=True,
    )
    st.caption('Each item has its own Save button — changes write to Google Sheets immediately and appear on the Presentation tab within ~10 seconds. Reload to see current saved state.')

    _rc1, _rc2 = st.columns([1, 4])
    with _rc1:
        if st.button('🔄 Reload', use_container_width=True):
            pull_cascade_content_overrides.clear()
            st.rerun()

    _live_eng = get_live_engines()
    _live_os  = get_live_os()
    _live_cho = get_live_choices()
    _live_how = get_live_how()

    st.divider()

    # ── COMMERCIAL ENGINES ──────────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:0.84em;font-weight:700;letter-spacing:2px;'
        f'color:{FOREST};margin-bottom:12px;">COMMERCIAL ENGINES</div>',
        unsafe_allow_html=True,
    )
    _eng_draft = list(_live_eng)

    for _ei, _eng in enumerate(_eng_draft):
        with st.expander(f'**{_eng["title"]}** — {_eng.get("subtitle","")}', expanded=False):
            _new_title = st.text_input('Title', value=_eng['title'], key=f'ce_eng_title_{_ei}')
            _new_sub   = st.text_input('Subtitle', value=_eng.get('subtitle',''), key=f'ce_eng_sub_{_ei}')
            _new_desc  = st.text_area('Description', value=_eng['description'], height=80, key=f'ce_eng_desc_{_ei}')

            st.markdown('<div style="font-size:0.75em;color:#888;font-weight:700;margin-top:8px;margin-bottom:4px;">STAT CHIPS (value | label)</div>', unsafe_allow_html=True)
            _curr_stats = list(_eng.get('stats', []))
            while len(_curr_stats) < 3:
                _curr_stats.append(['', ''])
            _new_stats = []
            for _si in range(3):
                _sc1, _sc2 = st.columns(2)
                with _sc1:
                    _sv = st.text_input(f'stat_v_{_ei}_{_si}', value=_curr_stats[_si][0] if _si < len(_curr_stats) and _curr_stats[_si] else '', key=f'ce_eng_sv_{_ei}_{_si}', label_visibility='collapsed', placeholder=f'Stat {_si+1} value')
                with _sc2:
                    _sl = st.text_input(f'stat_l_{_ei}_{_si}', value=_curr_stats[_si][1] if _si < len(_curr_stats) and len(_curr_stats[_si]) > 1 else '', key=f'ce_eng_sl_{_ei}_{_si}', label_visibility='collapsed', placeholder='label')
                if _sv.strip():
                    _new_stats.append([_sv.strip(), _sl.strip()])

            st.markdown('<div style="font-size:0.75em;color:#888;font-weight:700;margin-top:8px;margin-bottom:4px;">ACCORDION SECTIONS</div>', unsafe_allow_html=True)
            _curr_secs = list(_eng.get('sections', []))
            _new_secs  = []
            for _si, _sec in enumerate(_curr_secs):
                _stc1, _stc2 = st.columns([3, 1])
                with _stc1:
                    _sec_title = st.text_input(f'sec_t_{_ei}_{_si}', value=_sec.get('title',''), key=f'ce_eng_sect_{_ei}_{_si}', label_visibility='collapsed', placeholder='Section title')
                with _stc2:
                    _del_sec = st.button('✕', key=f'ce_eng_delsec_{_ei}_{_si}', use_container_width=True)
                if _del_sec:
                    continue
                _cnt = _sec.get('content', [])
                _cnt_str = '\n'.join(_cnt) if isinstance(_cnt, list) else str(_cnt)
                _sec_cnt = st.text_area(f'sec_c_{_ei}_{_si}', value=_cnt_str, height=72, key=f'ce_eng_secc_{_ei}_{_si}', label_visibility='collapsed', placeholder='One bullet per line (or a single paragraph)')
                if _sec_title.strip():
                    _lines = [l.strip() for l in _sec_cnt.split('\n') if l.strip()]
                    _new_secs.append({'title': _sec_title.strip(), 'content': _lines if len(_lines) != 1 else _lines[0]})

            _add_sec_t = st.text_input('new_sec', value='', key=f'ce_eng_addsect_{_ei}', label_visibility='collapsed', placeholder='+ Add section title…')
            if _add_sec_t.strip():
                _new_secs.append({'title': _add_sec_t.strip(), 'content': []})

            _cb1, _cb2, _cb3, _cb4 = st.columns([2, 1, 1, 1])
            with _cb1:
                if st.button('Save engine', key=f'ce_eng_save_{_ei}', type='primary', use_container_width=True):
                    _eng_draft[_ei] = {'id': _eng['id'], 'title': _new_title.strip() or _eng['title'], 'subtitle': _new_sub.strip(), 'description': _new_desc.strip(), 'stats': _new_stats, 'sections': _new_secs}
                    save_cascade_content_section('engines', _eng_draft)
                    st.toast('Engine saved ✓', icon='✅')
                    st.rerun()
            with _cb2:
                if st.button('Delete', key=f'ce_eng_del_{_ei}', use_container_width=True):
                    _eng_draft.pop(_ei)
                    save_cascade_content_section('engines', _eng_draft)
                    st.toast('Deleted', icon='🗑️')
                    st.rerun()
            with _cb3:
                if _ei > 0 and st.button('↑', key=f'ce_eng_up_{_ei}', use_container_width=True):
                    _eng_draft[_ei-1], _eng_draft[_ei] = _eng_draft[_ei], _eng_draft[_ei-1]
                    save_cascade_content_section('engines', _eng_draft)
                    st.rerun()
            with _cb4:
                if _ei < len(_eng_draft)-1 and st.button('↓', key=f'ce_eng_dn_{_ei}', use_container_width=True):
                    _eng_draft[_ei+1], _eng_draft[_ei] = _eng_draft[_ei], _eng_draft[_ei+1]
                    save_cascade_content_section('engines', _eng_draft)
                    st.rerun()

    with st.expander('➕ Add new engine', expanded=False):
        _ne_title = st.text_input('Title', key='ce_new_eng_title', placeholder='e.g. Retail')
        _ne_sub   = st.text_input('Subtitle', key='ce_new_eng_sub', placeholder='e.g. ndis, ecommerce, healthy hearing')
        _ne_desc  = st.text_area('Description', key='ce_new_eng_desc', height=68, placeholder='One or two sentences.')
        if st.button('Add engine', key='ce_new_eng_add', type='primary') and _ne_title.strip():
            import re as _re
            _new_id = _re.sub(r'[^a-z0-9]', '_', _ne_title.strip().lower())
            _eng_draft.append({'id': _new_id, 'title': _ne_title.strip(), 'subtitle': _ne_sub.strip(), 'description': _ne_desc.strip(), 'stats': [], 'sections': []})
            save_cascade_content_section('engines', _eng_draft)
            st.toast('Engine added ✓', icon='✅')
            st.rerun()

    st.divider()

    # ── OPERATING SYSTEM ────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:0.84em;font-weight:700;letter-spacing:2px;'
        f'color:{FOREST};margin-bottom:12px;">ONE COMPANY OPERATING SYSTEM</div>',
        unsafe_allow_html=True,
    )
    _os_draft = list(_live_os)
    for _oi, _os_item in enumerate(_os_draft):
        _oc1, _oc2, _oc3, _oc4 = st.columns([5, 1, 1, 1])
        with _oc1:
            _os_val = st.text_input(f'os_{_oi}', value=_os_item, key=f'ce_os_{_oi}', label_visibility='collapsed')
        with _oc2:
            if st.button('Save', key=f'ce_os_save_{_oi}', use_container_width=True):
                _os_draft[_oi] = _os_val.strip() or _os_item
                save_cascade_content_section('os', _os_draft)
                st.toast('Saved ✓', icon='✅')
                st.rerun()
        with _oc3:
            if st.button('✕', key=f'ce_os_del_{_oi}', use_container_width=True):
                _os_draft.pop(_oi)
                save_cascade_content_section('os', _os_draft)
                st.rerun()
        with _oc4:
            if _oi > 0 and st.button('↑', key=f'ce_os_up_{_oi}', use_container_width=True):
                _os_draft[_oi-1], _os_draft[_oi] = _os_draft[_oi], _os_draft[_oi-1]
                save_cascade_content_section('os', _os_draft)
                st.rerun()

    _oc_a1, _oc_a2 = st.columns([5, 1])
    with _oc_a1:
        _new_os = st.text_input('new_os', value='', key='ce_os_new', label_visibility='collapsed', placeholder='+ Add OS principle…')
    with _oc_a2:
        if st.button('Add', key='ce_os_add', use_container_width=True) and _new_os.strip():
            _os_draft.append(_new_os.strip())
            save_cascade_content_section('os', _os_draft)
            st.toast('Added ✓', icon='✅')
            st.rerun()

    st.divider()

    # ── STRATEGIC CHOICES ───────────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:0.84em;font-weight:700;letter-spacing:2px;'
        f'color:{WINE};margin-bottom:12px;">FY27 STRATEGIC CHOICES</div>',
        unsafe_allow_html=True,
    )
    _cho_draft = list(_live_cho)
    for _ci, _cho in enumerate(_cho_draft):
        with st.expander(f'**{_cho.get("number",_ci+1)}.** {_cho["title"]}', expanded=False):
            _cc1, _cc2 = st.columns([1, 5])
            with _cc1:
                _cho_num = st.text_input('No.', value=str(_cho.get('number', _ci+1)), key=f'ce_cho_num_{_ci}')
            with _cc2:
                _cho_title = st.text_input('Title', value=_cho['title'], key=f'ce_cho_title_{_ci}')
            _cho_attr  = st.text_input('Engine attribution tag (leave blank for none)', value=_cho.get('attribution',''), key=f'ce_cho_attr_{_ci}')
            _cho_desc  = st.text_area('Card description', value=_cho['description'], height=80, key=f'ce_cho_desc_{_ci}')
            _cho_intro = st.text_area('Accordion intro (italic)', value=_cho.get('intro',''), height=56, key=f'ce_cho_intro_{_ci}')

            st.markdown('<div style="font-size:0.75em;color:#888;font-weight:700;margin-top:8px;margin-bottom:4px;">ACCORDION SECTIONS</div>', unsafe_allow_html=True)
            _csecs     = list(_cho.get('sections', []))
            _new_csecs = []
            for _csi, _csec in enumerate(_csecs):
                _cs1, _cs2 = st.columns([3, 1])
                with _cs1:
                    _cst = st.text_input(f'cho_st_{_ci}_{_csi}', value=_csec.get('title',''), key=f'ce_cho_sect_{_ci}_{_csi}', label_visibility='collapsed', placeholder='Section title')
                with _cs2:
                    _cdel = st.button('✕', key=f'ce_cho_delsec_{_ci}_{_csi}', use_container_width=True)
                if _cdel:
                    continue
                _csc = _csec.get('content', [])
                _csc_str = '\n'.join(_csc) if isinstance(_csc, list) else str(_csc)
                _csc_new = st.text_area(f'cho_sc_{_ci}_{_csi}', value=_csc_str, height=68, key=f'ce_cho_secc_{_ci}_{_csi}', label_visibility='collapsed', placeholder='One bullet per line (or a paragraph)')
                if _cst.strip():
                    _lines = [l.strip() for l in _csc_new.split('\n') if l.strip()]
                    _new_csecs.append({'title': _cst.strip(), 'content': _lines if len(_lines) != 1 else (_lines[0] if _lines else '')})
            _add_cst = st.text_input('new_cho_sec', value='', key=f'ce_cho_addsec_{_ci}', label_visibility='collapsed', placeholder='+ Add section…')
            if _add_cst.strip():
                _new_csecs.append({'title': _add_cst.strip(), 'content': []})

            _cb1, _cb2, _cb3, _cb4 = st.columns([2, 1, 1, 1])
            with _cb1:
                if st.button('Save choice', key=f'ce_cho_save_{_ci}', type='primary', use_container_width=True):
                    _cho_draft[_ci] = {'id': _cho['id'], 'number': _cho_num.strip() or str(_ci+1), 'title': _cho_title.strip() or _cho['title'], 'description': _cho_desc.strip(), 'attribution': _cho_attr.strip(), 'intro': _cho_intro.strip(), 'sections': _new_csecs}
                    save_cascade_content_section('choices', _cho_draft)
                    st.toast('Choice saved ✓', icon='✅')
                    st.rerun()
            with _cb2:
                if st.button('Delete', key=f'ce_cho_del_{_ci}', use_container_width=True):
                    _cho_draft.pop(_ci)
                    save_cascade_content_section('choices', _cho_draft)
                    st.rerun()
            with _cb3:
                if _ci > 0 and st.button('↑', key=f'ce_cho_up_{_ci}', use_container_width=True):
                    _cho_draft[_ci-1], _cho_draft[_ci] = _cho_draft[_ci], _cho_draft[_ci-1]
                    save_cascade_content_section('choices', _cho_draft)
                    st.rerun()
            with _cb4:
                if _ci < len(_cho_draft)-1 and st.button('↓', key=f'ce_cho_dn_{_ci}', use_container_width=True):
                    _cho_draft[_ci+1], _cho_draft[_ci] = _cho_draft[_ci], _cho_draft[_ci+1]
                    save_cascade_content_section('choices', _cho_draft)
                    st.rerun()

    with st.expander('➕ Add new choice', expanded=False):
        _nc_num   = st.text_input('Number', key='ce_new_cho_num', placeholder='8')
        _nc_title = st.text_input('Title', key='ce_new_cho_title', placeholder='Choice title…')
        _nc_desc  = st.text_area('Description', key='ce_new_cho_desc', height=56, placeholder='One sentence.')
        _nc_attr  = st.text_input('Engine tag (optional)', key='ce_new_cho_attr', placeholder='e.g. Retail')
        if st.button('Add choice', key='ce_new_cho_add', type='primary') and _nc_title.strip():
            import re as _re2
            _nc_id = 'cx_' + _re2.sub(r'[^a-z0-9]', '_', _nc_title.strip().lower()[:12])
            _cho_draft.append({'id': _nc_id, 'number': _nc_num.strip() or str(len(_cho_draft)+1), 'title': _nc_title.strip(), 'description': _nc_desc.strip(), 'attribution': _nc_attr.strip(), 'intro': '', 'sections': []})
            save_cascade_content_section('choices', _cho_draft)
            st.toast('Choice added ✓', icon='✅')
            st.rerun()

    st.divider()

    # ── HOW WE WILL WORK ────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:0.84em;font-weight:700;letter-spacing:2px;'
        f'color:{WINE};margin-bottom:12px;">HOW WE WILL WORK</div>',
        unsafe_allow_html=True,
    )
    _how_draft = [{'principle': p, 'description': d} for p, d in _live_how]
    for _hi, _hw in enumerate(_how_draft):
        _icon = HOW_WE_WORK_ICONS[_hi] if _hi < len(HOW_WE_WORK_ICONS) else '•'
        with st.expander(f'{_icon} {_hw["principle"]}', expanded=False):
            _hw_p = st.text_input('Principle', value=_hw['principle'], key=f'ce_hw_p_{_hi}')
            _hw_d = st.text_input('Description', value=_hw['description'], key=f'ce_hw_d_{_hi}')
            _hb1, _hb2, _hb3, _hb4 = st.columns([2, 1, 1, 1])
            with _hb1:
                if st.button('Save', key=f'ce_hw_save_{_hi}', type='primary', use_container_width=True):
                    _how_draft[_hi] = {'principle': _hw_p.strip() or _hw['principle'], 'description': _hw_d.strip()}
                    save_cascade_content_section('how', _how_draft)
                    st.toast('Saved ✓', icon='✅')
                    st.rerun()
            with _hb2:
                if st.button('Delete', key=f'ce_hw_del_{_hi}', use_container_width=True):
                    _how_draft.pop(_hi)
                    save_cascade_content_section('how', _how_draft)
                    st.rerun()
            with _hb3:
                if _hi > 0 and st.button('↑', key=f'ce_hw_up_{_hi}', use_container_width=True):
                    _how_draft[_hi-1], _how_draft[_hi] = _how_draft[_hi], _how_draft[_hi-1]
                    save_cascade_content_section('how', _how_draft)
                    st.rerun()
            with _hb4:
                if _hi < len(_how_draft)-1 and st.button('↓', key=f'ce_hw_dn_{_hi}', use_container_width=True):
                    _how_draft[_hi+1], _how_draft[_hi] = _how_draft[_hi], _how_draft[_hi+1]
                    save_cascade_content_section('how', _how_draft)
                    st.rerun()

    with st.expander('➕ Add new principle', expanded=False):
        _nhw_p = st.text_input('Principle', key='ce_new_hw_p', placeholder='e.g. Act with purpose')
        _nhw_d = st.text_input('Description', key='ce_new_hw_d', placeholder='One short sentence.')
        if st.button('Add principle', key='ce_new_hw_add', type='primary') and _nhw_p.strip():
            _how_draft.append({'principle': _nhw_p.strip(), 'description': _nhw_d.strip()})
            save_cascade_content_section('how', _how_draft)
            st.toast('Added ✓', icon='✅')
            st.rerun()

    st.divider()
    if st.button('↩️ Reset all content to Python defaults', key='ce_reset_all'):
        _sheets_svc = __import__('utils', fromlist=['_sheets'])._sheets()
        _sheets_svc.spreadsheets().values().clear(
            spreadsheetId='1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI',
            range="'Cascade Content'!A2:B",
        ).execute()
        pull_cascade_content_overrides.clear()
        st.toast('Reset to defaults ✓', icon='↩️')
        st.rerun()

    st.stop()  # prevent facilitate section from rendering when editing content

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
            held_rows   = dept_rows[dept_rows['Status'] == 'held']   if not dept_rows.empty else dept_rows
            is_opted    = (not dept_rows.empty
                           and dept_rows['Status'].eq('opted_out').any()
                           and locked_rows.empty and draft_rows.empty and held_rows.empty)
            n_active    = len(locked_rows) + len(draft_rows) + len(held_rows)

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

                for _, row in held_rows.iterrows():
                    ts   = row['Timestamp']
                    text = row['Text']
                    pts  = [p.strip() for p in str(text).split('\n') if p.strip()]
                    if len(pts) == 1:
                        hbody = f'<div style="font-size:0.84em;color:#1a1a1a;line-height:1.6;">📌 {pts[0]}</div>'
                    else:
                        hitems = ''.join([f'<li style="margin-bottom:3px;">{p}</li>' for p in pts])
                        hbody  = (f'<div style="font-size:0.76em;color:#005E63;margin-bottom:3px;">📌 KEPT FOR LATER</div>'
                                  f'<ul style="font-size:0.84em;color:#1a1a1a;line-height:1.6;margin:0;padding-left:18px;">{hitems}</ul>')
                    st.markdown(
                        f'<div style="background:#EEF6F6;border-left:3px solid #188383;'
                        f'padding:10px 14px;border-radius:0 6px 6px 0;margin-bottom:4px;">'
                        f'{hbody}</div>',
                        unsafe_allow_html=True,
                    )
                    c1, c2, c3 = st.columns([1, 1, 1])
                    with c1:
                        if st.button('✅ Lock', key=f'fac_lock_h_{ts}', type='primary', use_container_width=True):
                            update_contribution(ts, new_status='locked')
                            st.rerun()
                    with c2:
                        if st.button('Release', key=f'fac_rel_{ts}', use_container_width=True):
                            update_contribution(ts, new_status='draft')
                            st.rerun()
                    with c3:
                        if st.button('Delete', key=f'fac_del_h_{ts}', use_container_width=True):
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
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
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
                        if st.button('Hold', key=f'fac_hold_{ts}', use_container_width=True):
                            final = edited.strip() or text
                            update_contribution(ts, new_status='held', new_text=final)
                            st.rerun()
                    with c4:
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
