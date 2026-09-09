"""Overview — Alignment Day home base. Brand funnel fills live as activities complete."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from utils import inject_styles, _sheets, PURPLE, TEAL, WINE, FOREST
from styles_shared import (
    TEAM as STYLES_TEAM, pull_styles, compute_scores, top_two,
    HEX as STYLE_HEX, TEXT as STYLE_TEXT,
)
from strategy_cascade_shared import (
    pull_cascade_session, pull_commitments as _pull_casc_comm,
    CHOICES as CASCADE_CHOICES, pull_cascade_contributions as _pull_casc_contribs,
    get_live_choices,
)
from scorecard_shared import pull_scorecard_entries, pull_scorecard_proposals
from one_thing_shared import (
    pull_one_thing_session, pull_one_thing_winners, DEPARTMENTS as OT_DEPARTMENTS,
    OPERATIONAL_FUNCTIONS, GOVERNANCE_FUNCTIONS, _fn_table_html,
)

inject_styles()

SHEET_ID           = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'
MISSION_CATEGORIES = ['Who', 'What', 'How', 'Makes Possible']
VALUES             = 'Impact  ·  Quality  ·  Leadership  ·  Momentum'
BRAND_PROMISE      = 'Feel connected.'

# ── Organogram SVG ─────────────────────────────────────────────────────────────

def _org_svg(styles=None) -> str:
    # L3 row holds 11 boxes side by side (Rebekah×2, JK×4, Louise×5).
    # l3_w=100, gap=10 → each slot is 110px wide.
    W, H = 1700, 420

    DARK      = '#50144B'   # Wine — James, Bill
    KAVI_WINE = '#73436F'   # 80% tint of Wine — Kavi
    FOREST_D  = '#005E63'   # Forest — JK, Louise, Rebekah
    LIGHT   = '#F9F9F9'
    GREY_BG = '#EEEEEE'
    GREY_FG = '#AAAAAA'
    LINE    = '#BBBBBB'
    LINE_D  = '#CCCCCC'

    james_y, james_h = 20, 58
    l1_y,   l1_h    = 100, 58
    l2_y,   l2_h    = 180, 58
    l3_y,   l3_h    = 260, 58
    l4_y,   l4_h    = 340, 58

    james_w, l1_w, l2_w, l3_w, l4_w = 128, 128, 128, 128, 128

    # L3 column centers — 11 boxes, gap=10, l3_w=128 (step=138)
    # Order left→right: Rebekah's 2 | JK's 4 | Louise's 5
    # Start at 220 so c_ellissa left-edge (156) clears Sayaka right-edge (144)
    c_ellissa = 220; c_charli = 358                                              # Rebekah's 2
    c_ang     = 496; c_rob   = 634; c_vac1 = 772; c_vac2 = 910                  # JK's 4
    c_andrew  = 1048; c_ian   = 1186; c_alex = 1324; c_dylan = 1462; c_bonar = 1600  # Louise's 5

    c_rebekah = (c_ellissa + c_charli) // 2  # 289
    c_jk      = (c_ang     + c_vac2)   // 2  # 703
    c_louise  = (c_andrew  + c_bonar)  // 2  # 1324

    c_kavi   = 80                                      # left of the main tree
    c_bill   = (c_rebekah + c_louise)  // 2            # 806 — midpoint of L2 span
    james_cx = c_bill                                  # James directly above Bill

    james_bot = james_y + james_h
    l1_bot    = l1_y + l1_h
    l2_bot    = l2_y + l2_h
    l3_bot    = l3_y + l3_h

    L = []; a = L.append

    a(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
      f'style="width:100%;max-width:{W}px;display:block;margin:0 auto;">')

    def _box(cx, y, w, h, name, titles, fill,
             nc='white', tc='white', to=0.85, stroke=None, rx=7):
        bx = cx - w // 2
        s = f'stroke="{stroke}" stroke-width="0.8"' if stroke else ''
        a(f'<rect x="{bx}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {s}/>')
        mid = y + (h - 5) // 2   # shift up to clear the 5px bottom stripe
        n = len(titles)
        if n == 0:
            a(f'<text x="{cx}" y="{mid+5}" text-anchor="middle" font-family="sans-serif" '
              f'font-size="10" font-weight="700" fill="{nc}">{name}</text>')
        elif n == 1:
            a(f'<text x="{cx}" y="{mid-4}" text-anchor="middle" font-family="sans-serif" '
              f'font-size="10" font-weight="700" fill="{nc}">{name}</text>')
            a(f'<text x="{cx}" y="{mid+9}" text-anchor="middle" font-family="sans-serif" '
              f'font-size="7.5" fill="{tc}" opacity="{to}">{titles[0]}</text>')
        else:
            a(f'<text x="{cx}" y="{mid-9}" text-anchor="middle" font-family="sans-serif" '
              f'font-size="10" font-weight="700" fill="{nc}">{name}</text>')
            a(f'<text x="{cx}" y="{mid+4}" text-anchor="middle" font-family="sans-serif" '
              f'font-size="7.5" fill="{tc}" opacity="{to}">{titles[0]}</text>')
            a(f'<text x="{cx}" y="{mid+15}" text-anchor="middle" font-family="sans-serif" '
              f'font-size="7.5" fill="{tc}" opacity="{to}">{titles[1]}</text>')

    def _stripe(cx, y, w, h, name, rx=7):
        sc = (styles or {}).get(name)
        if not sc:
            return
        bx = cx - w // 2
        cid = f's{abs(hash((cx, y))) % 99991}'
        a(f'<clipPath id="{cid}"><rect x="{bx}" y="{y}" width="{w}" height="{h}" rx="{rx}"/></clipPath>')
        a(f'<rect x="{bx}" y="{y+h-5}" width="{w}" height="5" fill="{sc}" clip-path="url(#{cid})"/>')

    def mgmt(cx, y, w, h, name, titles, fill=DARK):
        _box(cx, y, w, h, name, titles, fill, 'white', 'white', to=0.85)
        _stripe(cx, y, w, h, name)

    def team(cx, y, w, h, name, titles):
        _box(cx, y, w, h, name, titles, LIGHT, '#1A1A1A', '#555555', to=1.0, stroke=DARK)
        _stripe(cx, y, w, h, name)

    def grey_b(cx, y, w, h, name, titles):
        _box(cx, y, w, h, name, titles, GREY_BG, GREY_FG, GREY_FG, to=0.9)

    def _vl(x, y1, y2, col=LINE, w=1.5, dash=''):
        d = f'stroke-dasharray="{dash}"' if dash else ''
        a(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{col}" stroke-width="{w}" {d}/>')

    def _hl(x1, x2, y, col=LINE, w=1.5):
        a(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{col}" stroke-width="{w}"/>')

    def _conn(pcx, pb, cxs, ct, col=LINE, dash=''):
        jy = (pb + ct) // 2
        _vl(pcx, pb, jy, col, dash=dash)
        if len(cxs) == 1 and cxs[0] == pcx:
            _vl(cxs[0], jy, ct, col, dash=dash)
        else:
            _hl(min(cxs), max(cxs), jy, col)
            for cx in cxs:
                _vl(cx, jy, ct, col, dash=dash)

    # ── Connectors (drawn first, below boxes) ─────────────────────────────────

    jy0 = (james_bot + l1_y) // 2
    _vl(james_cx, james_bot, jy0)
    _hl(c_kavi, c_bill, jy0)             # bar from Kavi (left) to Bill/James
    _vl(c_bill, jy0, l1_y)
    _vl(c_kavi, jy0, l1_y, LINE_D, dash='4,3')

    _conn(c_bill, l1_bot, [c_rebekah, c_jk, c_louise], l2_y)
    _conn(c_kavi, l1_bot, [c_kavi], l3_y, LINE_D, dash='4,3')
    # Sayaka ↔ Bill dotted-line — exits Sayaka right, up the gap, right to Bill left edge
    rm      = (c_kavi + l3_w // 2 + c_ellissa - l3_w // 2) // 2  # midpoint of 12px gap (≈150)
    s_right = c_kavi + l3_w // 2          # Sayaka right edge (144)
    s_mid_y = l3_y  + l3_h // 2           # Sayaka vertical centre (289)
    b_left  = c_bill - l1_w // 2          # Bill left edge (742)
    b_mid_y = l1_y  + l1_h // 2           # Bill mid-height (129)
    for x1, y1, x2, y2 in [
        (s_right, s_mid_y, rm,     s_mid_y),  # right from Sayaka
        (rm,      s_mid_y, rm,     b_mid_y),  # up the gap (x=150 clears all boxes)
        (rm,      b_mid_y, b_left, b_mid_y),  # right to Bill's left edge at mid-height
    ]:
        a(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
          f'stroke="{LINE_D}" stroke-width="1.5" stroke-dasharray="4,3"/>')

    _conn(c_jk,      l2_bot, [c_ang, c_rob, c_vac1, c_vac2],              l3_y)
    _conn(c_louise,  l2_bot, [c_andrew, c_ian, c_alex, c_dylan, c_bonar], l3_y)
    _conn(c_rebekah, l2_bot, [c_ellissa, c_charli],                        l3_y)

    _conn(c_rob, l3_bot, [c_rob], l4_y)

    # ── Boxes ─────────────────────────────────────────────────────────────────

    mgmt(james_cx, james_y, james_w, james_h, 'James Fielding',
         ['Chief Executive Officer'])

    mgmt(c_bill, l1_y, l1_w, l1_h, 'Bill Peng', ['Chief Operating Officer'])
    mgmt(c_kavi, l1_y, l1_w, l1_h, 'Kavi Bekarma', ['Effective Chief', 'Financial Officer'],
         fill=KAVI_WINE)

    mgmt(c_rebekah, l2_y, l2_w, l2_h, 'Rebekah Davidson',
         ['Head of Operations'], fill=FOREST_D)
    mgmt(c_jk,      l2_y, l2_w, l2_h, 'John Krajewski',
         ['Head of International', 'Sales &amp; Marketing'], fill=FOREST_D)
    mgmt(c_louise,  l2_y, l2_w, l2_h, 'Louise Heller',
         ['Engineering Program Manager'], fill=FOREST_D)
    team(c_kavi,    l3_y, l3_w, l3_h, 'Sayaka Smith', ['Accounting Manager'])

    team(c_ellissa, l3_y, l3_w, l3_h, 'Ellissa Waters',
         ['Customer Support &amp;', 'Technical Specialist'])
    team(c_charli,  l3_y, l3_w, l3_h, 'Charli Every',
         ['Customer Care &amp;', 'Sales Assistant'])

    team(c_ang,  l3_y, l3_w, l3_h, 'Angelique Simon', ['Marketing Manager'])
    team(c_rob,  l3_y, l3_w, l3_h, 'Robert Poulsen',
         ['Business Development', '&amp; Relationships'])
    grey_b(c_vac1, l3_y, l3_w, l3_h, '[Vacant]', ['Territory Sales Manager'])
    grey_b(c_vac2, l3_y, l3_w, l3_h, '[Vacant]', ['Territory Sales Manager'])

    team(c_andrew, l3_y, l3_w, l3_h, 'Andrew Morton',
         ['Head of Software', 'Development'])
    team(c_ian,   l3_y, l3_w, l3_h, "Dr Ian O'Brien",  ['Research Audiologist'])
    team(c_alex,  l3_y, l3_w, l3_h, 'Alex Bartlett',   ['Firmware Engineer'])
    team(c_dylan, l3_y, l3_w, l3_h, 'Dylan Whitehouse',
         ['Electronic &amp;', 'Software Engineer'])
    team(c_bonar, l3_y, l3_w, l3_h, 'Bonar Dickson',   ['Engineering Consultant'])

    team(c_rob, l4_y, l4_w, l4_h, 'Misaki Kawashima', ['Business Development Intern'])

    a('</svg>')
    return '\n'.join(L)


# ── Data ──────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=20, show_spinner=False)
def _mission_top():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range="'Votes'!A:C",
        ).execute().get('values', [])
        if len(rows) < 2:
            return {}
        df = pd.DataFrame(rows[1:], columns=['Category', 'Answer', 'Votes'])
        df['Votes'] = pd.to_numeric(df['Votes'], errors='coerce').fillna(0).astype(int)
        top = {}
        for cat in MISSION_CATEGORIES:
            sub = df[df['Category'] == cat].sort_values('Votes', ascending=False)
            if not sub.empty and sub.iloc[0]['Votes'] > 0:
                top[cat] = sub.iloc[0]['Answer']
        return top
    except Exception:
        return {}

@st.cache_data(ttl=10, show_spinner=False)
def _vision_locked():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range="'Vision Statement'!A2:B10",
        ).execute().get('values', [])
        for row in rows:
            if len(row) >= 2 and row[0] == 'final':
                return row[1]
        return ''
    except Exception:
        return ''

@st.cache_data(ttl=20, show_spinner=False)
def _row_count(tab, col='A'):
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{tab}'!{col}:{col}",
        ).execute().get('values', [])
        return max(0, len(rows) - 1)
    except Exception:
        return 0

# ── Page ──────────────────────────────────────────────────────────────────────

st.markdown('### Audeara Alignment Day')
st.markdown('FY27 strategy and alignment. One team, one direction.')
st.markdown('')

# ── Ground rules ──────────────────────────────────────────────────────────────

st.markdown(
    f'<div style="font-weight:700;font-size:1.05em;color:{TEAL};margin-bottom:14px;">'
    f'Good times. Good vibes.</div>',
    unsafe_allow_html=True,
)

RULES = [
    'Be open and constructive',
    'Challenge ideas, not people',
    'Make space for different perspectives',
    'Focus on the company, not individual agendas',
    'Seek clarity rather than perfect wording',
    'Stay curious when someone sees things differently',
]

cols = st.columns(2)
for i, rule in enumerate(RULES):
    with cols[i % 2]:
        st.markdown(
            f'<div style="background:#F5F5F5;border-radius:8px;padding:12px 14px;'
            f'margin-bottom:10px;font-size:0.95em;color:#444;line-height:1.5;">'
            f'<span style="color:{TEAL};font-weight:700;margin-right:6px;">✦</span>{rule}</div>',
            unsafe_allow_html=True,
        )

st.divider()

# ── Why we're here ────────────────────────────────────────────────────────────

WHY_HERE = [
    'Clarify why we exist and where we are going',
    'Understand how strategic choices are made and how I can contribute to them',
    'Strengthen how we work together',
    'Build a clearer link between company strategy and everyday decisions',
]

LEAVE_WITH = [
    'Shared mission and vision themes',
    'Greater understanding of our strategic choices',
    'Better understanding of how different working styles affect communication',
    'Clear inputs for the FY27 strategy and beyond',
]

col_why, col_leave = st.columns(2)

with col_why:
    st.markdown(
        f'<div style="font-weight:700;color:{PURPLE};margin-bottom:10px;">Why we\'re here</div>',
        unsafe_allow_html=True,
    )
    for item in WHY_HERE:
        st.markdown(
            f'<div style="background:#F7F0F7;border-radius:8px;padding:12px 14px;'
            f'margin-bottom:10px;font-size:0.95em;color:#444;line-height:1.5;">'
            f'<span style="color:{PURPLE};font-weight:700;margin-right:6px;">✦</span>{item}</div>',
            unsafe_allow_html=True,
        )

with col_leave:
    st.markdown(
        f'<div style="font-weight:700;color:{TEAL};margin-bottom:10px;">What we want to leave with</div>',
        unsafe_allow_html=True,
    )
    for item in LEAVE_WITH:
        st.markdown(
            f'<div style="background:#F0F8F8;border-radius:8px;padding:12px 14px;'
            f'margin-bottom:10px;font-size:0.95em;color:#444;line-height:1.5;">'
            f'<span style="color:{TEAL};font-weight:700;margin-right:6px;">✦</span>{item}</div>',
            unsafe_allow_html=True,
        )

st.markdown('')

st.divider()


@st.fragment(run_every=20)
def _overview():
    mission_top     = _mission_top()
    vision_final    = _vision_locked()
    n_mission       = _row_count('Submissions')
    n_vision        = _row_count('Vision Submissions')
    n_styles        = _row_count('Styles Submissions')
    n_team          = len(STYLES_TEAM)
    casc_session    = pull_cascade_session()
    casc_stage      = casc_session.get('stage', 'hidden')
    casc_df         = _pull_casc_comm()
    n_casc_comm     = len(casc_df) if not casc_df.empty else 0
    ot_session      = pull_one_thing_session()
    ot_stage        = ot_session.get('stage', 'hidden')
    ot_winners      = pull_one_thing_winners()
    n_ot_winners    = len(ot_winners)
    styles_df       = pull_styles()
    casc_contribs   = _pull_casc_contribs()
    submitted_set   = set(styles_df['Name'].tolist()) if not styles_df.empty else set()
    sc_entries_df   = pull_scorecard_entries()
    sc_proposals_df = pull_scorecard_proposals()
    sc_choices      = get_live_choices()
    n_sc_choices    = len(sc_choices)
    n_sc_filled     = len(sc_entries_df['ChoiceID'].unique()) if not sc_entries_df.empty else 0
    n_sc_proposals  = len(sc_proposals_df) if not sc_proposals_df.empty else 0

    mission_done  = len(mission_top) == 4
    mission_alive = n_mission > 0
    vision_done   = bool(vision_final)
    vision_alive  = n_vision > 0
    styles_done   = n_styles >= n_team
    styles_alive  = n_styles > 0

    # ── Agenda ────────────────────────────────────────────────────────────────

    st.markdown("#### Today's agenda")

    def _step(label, status, detail):
        if status == 'done':
            bc, bg, icon, tc = '#3EAA6D', '#E8F5EE', '✅', '#2D7D4F'
        elif status == 'active':
            bc, bg, icon, tc = PURPLE, '#F7F0F7', '▶', PURPLE
        else:
            bc, bg, icon, tc = '#CCCCCC', '#F5F5F5', '○', '#999999'
        st.markdown(
            f'<div style="border-left:4px solid {bc};background:{bg};'
            f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:10px;">'
            f'<div style="font-weight:700;font-size:1.05em;color:{tc};">{icon}&nbsp; {label}</div>'
            f'<div style="font-size:0.95em;color:{tc};opacity:0.85;margin-top:3px;">{detail}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    _step(
        'Mission Statement',
        'done'   if mission_done  else ('active' if mission_alive else 'upcoming'),
        'Agreed.' if mission_done else
            (f'{n_mission} idea{"s" if n_mission != 1 else ""} submitted — vote on the answers that resonate most.' if mission_alive
             else 'Submit ideas for each part of the mission sentence, then vote on the best answers.'),
    )
    _step(
        'Vision Statement — Magazine Cover',
        'done'   if vision_done  else ('active' if vision_alive else 'upcoming'),
        'Locked.' if vision_done else
            (f'{n_vision} cover {"stories" if n_vision != 1 else "story"} submitted — vote and the facilitator locks the final statement.' if vision_alive
             else 'Imagine Audeara on the cover of a major publication in 2030. Submit, vote, and lock a shared vision.'),
    )
    _step(
        'Different Styles, Shared Direction',
        'done'   if styles_done  else ('active' if styles_alive else 'upcoming'),
        f'{n_styles} of {n_team} submitted.' if styles_done else
            (f'{n_styles} of {n_team} submitted so far.' if styles_alive
             else 'Map how the team approaches decisions, change, and collaboration.'),
    )
    n_ot_depts    = len(OT_DEPARTMENTS)
    ot_done       = n_ot_winners == n_ot_depts and n_casc_comm >= n_team
    ot_alive      = ot_stage != 'hidden' or n_ot_winners > 0 or n_casc_comm > 0
    if ot_done:
        ot_detail = 'Complete.'
    elif ot_stage == 'personal':
        ot_detail = f'{n_casc_comm} of {n_team} personal One Things submitted.'
    elif ot_stage == 'departments' or n_ot_winners > 0:
        ot_detail = f'{n_ot_winners} of {n_ot_depts} departments agreed.'
    elif ot_alive:
        ot_detail = 'The One Thing activity is underway.'
    else:
        ot_detail = 'Each department agrees on their One Thing, then everyone commits to a personal One Thing.'
    _step(
        'The One Thing',
        'done'   if ot_done  else ('active' if ot_alive else 'upcoming'),
        ot_detail,
    )

    casc_done  = casc_stage == 'reveal'
    casc_alive = casc_stage in ('engines', 'choices', 'working', 'cascade', 'reveal')
    if casc_done:
        casc_detail = 'Complete.'
    elif casc_stage == 'cascade':
        n_conf = _row_count('Cascade Confidence')
        casc_detail = f'Cascade underway — {n_conf} confidence vote{"s" if n_conf != 1 else ""} in.'
    elif casc_stage in ('engines', 'choices', 'working'):
        casc_detail = 'The FY27 strategy is being presented.'
    elif casc_alive:
        casc_detail = 'Strategy Cascade is underway.'
    else:
        casc_detail = 'The FY27 strategy is presented. Each function agrees how they contribute to each strategic choice.'
    _step(
        'Strategy Cascade',
        'done'   if casc_done  else ('active' if casc_alive else 'upcoming'),
        casc_detail,
    )

    sc_done  = n_sc_choices > 0 and n_sc_filled >= n_sc_choices
    sc_alive = n_sc_filled > 0 or n_sc_proposals > 0
    if sc_done:
        sc_detail = 'Complete.'
    elif sc_alive:
        sc_detail = f'{n_sc_filled} of {n_sc_choices} strategic choices have a scorecard metric.'
    else:
        sc_detail = 'Each strategic choice gets a metric, target, and owner — the team\'s FY27 scorecard.'
    _step(
        'Scorecard',
        'done'   if sc_done  else ('active' if sc_alive else 'upcoming'),
        sc_detail,
    )

    st.divider()

    # ── Funnel colours ────────────────────────────────────────────────────────

    if mission_done:
        m_fill, m_text_col = '#781E73', '#FFFFFF'
    elif mission_alive:
        m_fill, m_text_col = '#C4A0C2', '#FFFFFF'
    else:
        m_fill, m_text_col = '#E0E0E0', '#AAAAAA'

    if vision_done:
        v_fill, v_text_col = '#188383', '#FFFFFF'
    elif vision_alive:
        v_fill, v_text_col = '#9BCFCF', '#FFFFFF'
    else:
        v_fill, v_text_col = '#E0E0E0', '#AAAAAA'

    m_sublabel = 'Our mission' if mission_done else ('Ideas coming in' if mission_alive else 'What do we do and why?')
    v_sublabel = 'Our vision'  if vision_done  else ('Taking shape'   if vision_alive  else 'Where are we going?')

    svg = f"""
<div style="padding:8px 0 16px;">
<svg viewBox="0 0 300 400" xmlns="http://www.w3.org/2000/svg"
     style="width:100%;max-width:320px;display:block;margin:0 auto">

  <polygon points="0,0 300,0 283,92 17,92" fill="{m_fill}"/>
  <text x="150" y="30" text-anchor="middle" font-family="sans-serif"
        font-size="9" font-weight="700" letter-spacing="2.5" fill="{m_text_col}" opacity="0.7">MISSION</text>
  <text x="150" y="58" text-anchor="middle" font-family="sans-serif"
        font-size="12" font-weight="600" fill="{m_text_col}">{m_sublabel}</text>

  <polygon points="17,97 283,97 266,189 34,189" fill="{v_fill}"/>
  <text x="150" y="127" text-anchor="middle" font-family="sans-serif"
        font-size="9" font-weight="700" letter-spacing="2.5" fill="{v_text_col}" opacity="0.7">VISION</text>
  <text x="150" y="155" text-anchor="middle" font-family="sans-serif"
        font-size="12" font-weight="600" fill="{v_text_col}">{v_sublabel}</text>

  <polygon points="34,194 266,194 249,286 51,286" fill="#50144B"/>
  <text x="150" y="224" text-anchor="middle" font-family="sans-serif"
        font-size="9" font-weight="700" letter-spacing="2.5" fill="white" opacity="0.7">VALUES</text>
  <text x="150" y="246" text-anchor="middle" font-family="sans-serif"
        font-size="9.5" font-weight="600" fill="white">Impact · Quality</text>
  <text x="150" y="262" text-anchor="middle" font-family="sans-serif"
        font-size="9.5" font-weight="600" fill="white">Leadership · Momentum</text>

  <polygon points="51,291 249,291 232,383 68,383" fill="#005E63"/>
  <text x="150" y="321" text-anchor="middle" font-family="sans-serif"
        font-size="9" font-weight="700" letter-spacing="2.5" fill="white" opacity="0.7">BRAND PROMISE</text>
  <text x="150" y="347" text-anchor="middle" font-family="sans-serif"
        font-size="13" font-weight="700" fill="white">Feel connected.</text>

</svg>
</div>"""

    # ── Layout ────────────────────────────────────────────────────────────────

    col_f, col_c = st.columns([1, 1.5])

    with col_f:
        st.markdown(svg, unsafe_allow_html=True)

    with col_c:
        # Mission panel
        if mission_done:
            m_bc, m_bg, m_icon = '#781E73', '#F7F0F7', '✅'
            m_heading = 'Mission Statement'
            m_body = (
                f'<div style="font-size:0.95em;line-height:1.7;margin-top:6px;">'
                f'We help <strong>{mission_top["Who"]}</strong> '
                f'do <strong>{mission_top["What"]}</strong> '
                f'by <strong>{mission_top["How"]}</strong>, '
                f'so they can <strong>{mission_top["Makes Possible"]}</strong>.'
                f'</div>'
            )
        elif mission_alive:
            m_bc, m_bg, m_icon = '#C4A0C2', '#FAF5FA', '💬'
            m_heading = f'Mission Statement — {n_mission} idea{"s" if n_mission != 1 else ""} in'
            m_body = '<div style="font-size:0.95em;color:#999;margin-top:4px;">Voting will surface the top answers.</div>'
        else:
            m_bc, m_bg, m_icon = '#CCCCCC', '#F5F5F5', '⏳'
            m_heading = 'Mission Statement'
            m_body = '<div style="font-size:0.95em;color:#AAAAAA;margin-top:4px;">What do we provide? Who do we serve? How do we do that? What does that make possible?</div>'

        st.markdown(
            f'<div style="border-left:4px solid {m_bc};background:{m_bg};'
            f'border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:12px;">'
            f'<div style="font-weight:700;font-size:1.05em;color:{m_bc};">{m_icon} {m_heading}</div>'
            f'{m_body}</div>',
            unsafe_allow_html=True,
        )

        # Vision panel
        if vision_done:
            v_bc, v_bg, v_icon = '#188383', '#F0F8F8', '✅'
            v_heading = 'Vision Statement'
            v_body = f'<div style="font-size:0.95em;line-height:1.7;margin-top:6px;font-style:italic;">"{vision_final}"</div>'
        elif vision_alive:
            v_bc, v_bg, v_icon = '#9BCFCF', '#F3FAFA', '🎨'
            v_heading = f'Vision — {n_vision} cover {"stories" if n_vision != 1 else "story"} in'
            v_body = '<div style="font-size:0.95em;color:#999;margin-top:4px;">Voting will surface the top answers. Facilitator locks the final statement.</div>'
        else:
            v_bc, v_bg, v_icon = '#CCCCCC', '#F5F5F5', '⏳'
            v_heading = 'Vision Statement'
            v_body = '<div style="font-size:0.95em;color:#AAAAAA;margin-top:4px;">Where are we in 3–5 years? What have we achieved? Who have we become?</div>'

        st.markdown(
            f'<div style="border-left:4px solid {v_bc};background:{v_bg};'
            f'border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:12px;">'
            f'<div style="font-weight:700;font-size:1.05em;color:{v_bc};">{v_icon} {v_heading}</div>'
            f'{v_body}</div>',
            unsafe_allow_html=True,
        )

        # Values (always filled)
        st.markdown(
            f'<div style="border-left:4px solid #50144B;background:#F5EFF5;'
            f'border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:12px;">'
            f'<div style="font-weight:700;font-size:1.05em;color:#50144B;">Values</div>'
            f'<div style="font-size:0.95em;color:#50144B;font-weight:600;margin-top:4px;">{VALUES}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Brand promise (always filled)
        st.markdown(
            f'<div style="border-left:4px solid #005E63;background:#EDF5F5;'
            f'border-radius:0 8px 8px 0;padding:14px 16px;">'
            f'<div style="font-weight:700;font-size:1.05em;color:#005E63;">Brand promise</div>'
            f'<div style="font-size:1.05em;color:#005E63;font-weight:700;margin-top:4px;">{BRAND_PROMISE}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown(
        f'<div style="font-weight:700;font-size:1.05em;color:#333;margin-bottom:16px;">'
        f"Who we are and how we work</div>",
        unsafe_allow_html=True,
    )

    # ── Organogram ────────────────────────────────────────────────────────────

    st.markdown(
        '<div style="font-size:0.75em;font-weight:700;letter-spacing:2px;'
        'color:#888;margin-bottom:10px;">THE TEAM</div>',
        unsafe_allow_html=True,
    )
    # Build style colour map — primary colour per person drives the bottom stripe on each box
    _NAME_MAP = {"Ian O'Brien": "Dr Ian O'Brien"}
    _org_styles = {}
    if not styles_df.empty:
        for _, row in styles_df.iterrows():
            scores   = compute_scores(row)
            pri, _   = top_two(scores)
            svg_name = _NAME_MAP.get(row['Name'], row['Name'])
            _org_styles[svg_name] = STYLE_HEX[pri]

    st.markdown(_org_svg(_org_styles or None), unsafe_allow_html=True)
    st.markdown('<div style="margin-bottom:16px;"></div>', unsafe_allow_html=True)

    # ── Row 1: Function tables with One Thing column ──────────────────────────

    st.markdown(
        _fn_table_html('OPERATIONAL FUNCTIONS', OPERATIONAL_FUNCTIONS, ot_winners) +
        _fn_table_html('GOVERNANCE &amp; OWNERSHIP', GOVERNANCE_FUNCTIONS, ot_winners),
        unsafe_allow_html=True,
    )

    # ── Row 2: Strategic Choices (cascade + scorecard, full width) ───────────────

    CHOICE_COLOURS = [WINE, FOREST, '#781E73', '#005E63', WINE, FOREST, '#781E73']

    def _dept_contribs(cid):
        if casc_contribs.empty:
            return {}
        sub = casc_contribs[
            (casc_contribs['ChoiceID'] == cid) &
            (~casc_contribs['Status'].isin(['deleted', 'opted_out']))
        ].sort_values('Timestamp', ascending=False)
        result = {}
        for _, row in sub.iterrows():
            if row['Department'] not in result and row['Text'].strip():
                result[row['Department']] = row['Text'].strip()
        return result

    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.75em;font-weight:700;letter-spacing:2px;'
        f'color:#888;margin-bottom:8px;">STRATEGIC CHOICES</div>',
        unsafe_allow_html=True,
    )

    if not casc_alive:
        st.markdown(
            f'<div style="background:#F5F5F5;border-radius:8px;padding:16px;'
            f'text-align:center;font-size:0.9em;color:#AAAAAA;font-style:italic;">'
            f'Strategic choices and scorecard entries will appear here as the session progresses.</div>',
            unsafe_allow_html=True,
        )
    else:
        left_col, right_col = st.columns(2)
        cols = [left_col, right_col]

        for idx, choice in enumerate(sc_choices):
            cid            = choice['id']
            colour         = CHOICE_COLOURS[idx % len(CHOICE_COLOURS)]
            dept_inputs    = _dept_contribs(cid)
            choice_entries = (
                sc_entries_df[sc_entries_df['ChoiceID'] == cid]
                if not sc_entries_df.empty else sc_entries_df
            )

            rows = []
            for d in OT_DEPARTMENTS:
                if not dept_inputs.get(d, ''):
                    continue
                entry = choice_entries[choice_entries['Department'] == d]
                rows.append({
                    'dept':    d,
                    'cascade': dept_inputs[d],
                    'entries': entry.to_dict('records') if not entry.empty else [],
                    'saved':   not entry.empty,
                })

            n_saved       = sum(1 for r in rows if r['saved'])
            n_total       = len(rows)
            all_done      = n_saved == n_total and n_total > 0
            status_colour = '#3EAA6D' if all_done else '#F5A623' if n_saved > 0 else '#AAAAAA'
            status_label  = (
                f'All {n_total} confirmed' if all_done
                else f'{n_saved}/{n_total} confirmed' if n_saved > 0
                else ('No inputs yet' if not rows else 'Pending')
            )

            dept_rows_html = ''
            for row in rows:
                cascade_text = row['cascade']
                if len(cascade_text) > 90:
                    cascade_text = cascade_text[:87] + '…'
                if row['entries']:
                    e = row['entries'][0]
                    metric_strip = (
                        f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px;">'
                        f'<span style="font-size:0.7em;background:{colour}14;color:{colour};'
                        f'font-weight:600;padding:2px 7px;border-radius:10px;">'
                        f'{e["Metric"] or "—"}</span>'
                        f'<span style="font-size:0.7em;background:#F0F0F0;color:#555;'
                        f'padding:2px 7px;border-radius:10px;">'
                        f'Target: {e["Target"] or "—"}</span>'
                        f'<span style="font-size:0.7em;background:#F0F0F0;color:#555;'
                        f'padding:2px 7px;border-radius:10px;">'
                        f'{e["Owner"] or "—"}</span>'
                        f'</div>'
                    )
                else:
                    metric_strip = (
                        f'<div style="font-size:0.7em;color:#CCCCCC;margin-top:3px;">'
                        f'Scorecard pending</div>'
                    )
                tick = '<span style="font-size:0.65em;color:#3EAA6D;">✓</span>' if row['saved'] else ''
                dept_rows_html += (
                    f'<div style="padding:7px 0;border-top:1px solid #F0EBF0;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
                    f'<span style="font-size:0.65em;font-weight:700;color:{colour};'
                    f'text-transform:uppercase;letter-spacing:0.6px;">{row["dept"]}</span>'
                    f'{tick}'
                    f'</div>'
                    f'<div style="font-size:0.76em;color:#666;line-height:1.4;margin-top:2px;'
                    f'font-style:italic;">{cascade_text}</div>'
                    f'{metric_strip}'
                    f'</div>'
                )

            with cols[idx % 2]:
                st.markdown(
                    f'<div style="border:1px solid #E8E0E8;border-top:3px solid {colour};'
                    f'border-radius:0 0 10px 10px;padding:12px 14px;margin-bottom:12px;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
                    f'margin-bottom:2px;">'
                    f'<div style="font-size:0.65em;font-weight:700;color:{colour};'
                    f'letter-spacing:1px;text-transform:uppercase;">Choice {choice["number"]}</div>'
                    f'<div style="font-size:0.65em;color:{status_colour};font-weight:600;">'
                    f'{status_label}</div>'
                    f'</div>'
                    f'<div style="font-weight:700;font-size:0.9em;color:#1a1a1a;'
                    f'line-height:1.35;margin-bottom:4px;">{choice["title"]}</div>'
                    f'{dept_rows_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

_overview()
