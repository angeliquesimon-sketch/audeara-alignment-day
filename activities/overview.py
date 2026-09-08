"""Overview — Alignment Day home base. Brand funnel fills live as activities complete."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from utils import inject_styles, _sheets, PURPLE, TEAL
from styles_shared import (
    TEAM as STYLES_TEAM, pull_styles, compute_scores, top_two,
    HEX as STYLE_HEX, TEXT as STYLE_TEXT,
)
from strategy_cascade_shared import (
    pull_cascade_session, pull_commitments as _pull_casc_comm,
    CHOICES as CASCADE_CHOICES, pull_cascade_contributions as _pull_casc_contribs,
)
from one_thing_shared import pull_one_thing_session, pull_one_thing_winners, DEPARTMENTS as OT_DEPARTMENTS

inject_styles()

SHEET_ID           = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'
WINE               = '#50144B'
FOREST             = '#005E63'
MISSION_CATEGORIES = ['Who', 'What', 'How', 'Makes Possible']
VALUES             = 'Impact  ·  Quality  ·  Leadership  ·  Momentum'
BRAND_PROMISE      = 'Feel connected.'

# ── Organogram SVG ─────────────────────────────────────────────────────────────

def _org_svg() -> str:
    W, H = 1200, 440

    DARK    = '#50144B'
    LIGHT   = '#F9F9F9'
    GREY_BG = '#EEEEEE'
    GREY_FG = '#AAAAAA'
    LINE    = '#BBBBBB'
    LINE_D  = '#CCCCCC'

    james_y, james_h = 20, 58
    l1_y,   l1_h    = 100, 50
    l2_y,   l2_h    = 175, 44
    l3_y,   l3_h    = 244, 38
    l4_y,   l4_h    = 300, 34

    james_w, l1_w, l2_w, l3_w, l4_w = 178, 145, 128, 114, 106

    c_ang   = 70;  c_rob  = 196;  c_vac1 = 322;  c_vac2 = 448
    c_jk    = (c_ang + c_vac2) // 2                            # 259
    c_louise  = 580;  c_andrew  = 720
    c_ellissa = 856;  c_charli  = 982
    c_rebekah = (c_ellissa + c_charli) // 2                    # 919
    c_kavi    = 1090
    c_bill    = (c_jk + c_louise + c_andrew + c_rebekah) // 4  # 619
    james_cx  = (c_bill + c_kavi) // 2                         # 854

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
        mid = y + h // 2
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

    def mgmt(cx, y, w, h, name, titles):
        _box(cx, y, w, h, name, titles, DARK, 'white', 'white', to=0.85)

    def team(cx, y, w, h, name, titles):
        _box(cx, y, w, h, name, titles, LIGHT, '#1A1A1A', '#555555', to=1.0, stroke=DARK)

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

    # James → Bill (solid) + Kavi (dashed)
    jy0 = (james_bot + l1_y) // 2
    _vl(james_cx, james_bot, jy0)
    _hl(c_bill, c_kavi, jy0)
    _vl(c_bill, jy0, l1_y)
    _vl(c_kavi, jy0, l1_y, LINE_D, dash='4,3')

    # Bill → JK, Louise, Andrew, Rebekah
    _conn(c_bill, l1_bot, [c_jk, c_louise, c_andrew, c_rebekah], l2_y)

    # Kavi → Sayaka (dashed)
    _conn(c_kavi, l1_bot, [c_kavi], l2_y, LINE_D, dash='4,3')

    # JK → Angelique, Rob, Vac1, Vac2
    _conn(c_jk, l2_bot, [c_ang, c_rob, c_vac1, c_vac2], l3_y)

    # Rob → Misaki
    _conn(c_rob, l3_bot, [c_rob], l4_y)

    # Rebekah → Ellissa, Charli
    _conn(c_rebekah, l2_bot, [c_ellissa, c_charli], l3_y)

    # ── Boxes ─────────────────────────────────────────────────────────────────

    mgmt(james_cx, james_y, james_w, james_h, 'James Fielding',
         ['Chief Executive Officer'])

    mgmt(c_bill, l1_y, l1_w, l1_h, 'Bill Peng', ['Chief Operating Officer'])
    grey_b(c_kavi, l1_y, l1_w, l1_h, 'Kavi Bekarma', ['Chief Financial Officer'])

    mgmt(c_jk,      l2_y, l2_w, l2_h, 'John Krajewski',
         ['Head of International', 'Sales &amp; Marketing'])
    mgmt(c_louise,  l2_y, l2_w, l2_h, 'Louise Heller',
         ['Engineering Program Manager'])
    mgmt(c_andrew,  l2_y, l2_w, l2_h, 'Andrew Morton',
         ['Head of Software', 'Design &amp; Development'])
    mgmt(c_rebekah, l2_y, l2_w, l2_h, 'Rebekah Davidson',
         ['Head of Operations'])
    team(c_kavi,    l2_y, l2_w, l2_h, 'Sayaka Smith', ['Accounting Manager'])

    team(c_ang,  l3_y, l3_w, l3_h, 'Angelique Simon', ['Marketing Manager'])
    team(c_rob,  l3_y, l3_w, l3_h, 'Robert Poulsen',
         ['Business Dev.', '&amp; Relationships'])
    grey_b(c_vac1, l3_y, l3_w, l3_h, '[Vacant]', ['Territory Sales Manager'])
    grey_b(c_vac2, l3_y, l3_w, l3_h, '[Vacant]', ['Territory Sales Manager'])

    team(c_ellissa, l3_y, l3_w, l3_h, 'Ellissa Waters',
         ['Customer Support &amp;', 'Technical Specialist'])
    team(c_charli,  l3_y, l3_w, l3_h, 'Charli Every',
         ['Customer Care &amp;', 'Sales Assistant'])

    team(c_rob, l4_y, l4_w, l4_h, 'Misaki Kawashima', ['BD Intern'])

    # ── Louise's stacked engineers ─────────────────────────────────────────────
    engineers = [
        ("Dr Ian O'Brien",   ['Research Audiologist']),
        ('Alex Bartlett',    ['Firmware Engineer']),
        ('Dylan Whitehouse', ['Electronic &amp;', 'Software Engineer']),
        ('Bonar Dickson',    ['Engineering Consultant']),
    ]
    eng_h = 38; eng_gap = 8; prev_b = l2_bot
    for i, (ename, etitles) in enumerate(engineers):
        ey = l2_bot + 14 + i * (eng_h + eng_gap)
        _vl(c_louise, prev_b, ey)
        team(c_louise, ey, l2_w, eng_h, ename, etitles)
        prev_b = ey + eng_h

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
        casc_detail = 'James is presenting the FY27 strategy.'
    elif casc_alive:
        casc_detail = 'Strategy Cascade is underway.'
    else:
        casc_detail = 'James presents the FY27 strategy. Each function agrees how they contribute to each strategic choice.'
    _step(
        'Strategy Cascade',
        'done'   if casc_done  else ('active' if casc_alive else 'upcoming'),
        casc_detail,
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
        f"What we've built today</div>",
        unsafe_allow_html=True,
    )

    # ── Organogram ────────────────────────────────────────────────────────────

    st.markdown(
        '<div style="font-size:0.75em;font-weight:700;letter-spacing:2px;'
        'color:#888;margin-bottom:10px;">THE TEAM</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_org_svg(), unsafe_allow_html=True)
    st.markdown('<div style="margin-bottom:16px;"></div>', unsafe_allow_html=True)

    # ── Row 1: Styles (left) + One Things (right) ─────────────────────────────

    col_styles, col_ot = st.columns(2)

    with col_styles:
        st.markdown(
            f'<div style="font-size:0.75em;font-weight:700;letter-spacing:2px;'
            f'color:#888;margin-bottom:8px;">DIFFERENT STYLES</div>',
            unsafe_allow_html=True,
        )
        st.caption(f'{len(submitted_set)} of {n_team} submitted')
        chips = ''
        for name in STYLES_TEAM:
            if name in submitted_set:
                row    = styles_df[styles_df['Name'] == name].iloc[0]
                scores = compute_scores(row)
                pri, _ = top_two(scores)
                bg     = STYLE_HEX[pri]
                tc     = STYLE_TEXT[pri]
                chips += (
                    f'<div style="background:{bg};border-radius:8px;padding:8px 10px;text-align:center;">'
                    f'<div style="font-size:0.72em;font-weight:700;color:{tc};line-height:1.3;">{name}</div>'
                    f'<div style="font-size:0.68em;color:{tc};opacity:0.8;">{pri}</div>'
                    f'</div>'
                )
            else:
                chips += (
                    f'<div style="background:#EBEBEB;border-radius:8px;padding:8px 10px;text-align:center;">'
                    f'<div style="font-size:0.72em;font-weight:700;color:#BBBBBB;line-height:1.3;">{name}</div>'
                    f'<div style="font-size:0.68em;color:#CCCCCC;">?</div>'
                    f'</div>'
                )
        st.markdown(
            f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;">{chips}</div>',
            unsafe_allow_html=True,
        )

    with col_ot:
        st.markdown(
            f'<div style="font-size:0.75em;font-weight:700;letter-spacing:2px;'
            f'color:#888;margin-bottom:8px;">THE ONE THING</div>',
            unsafe_allow_html=True,
        )
        st.caption(f'{n_ot_winners} of {len(OT_DEPARTMENTS)} departments agreed')
        for dept in OT_DEPARTMENTS:
            winner = ot_winners.get(dept, '')
            if winner:
                bc, bg, tc = FOREST, '#F0F7F7', FOREST
                body = f'<div style="font-size:0.88em;color:#333;line-height:1.5;margin-top:4px;">{winner}</div>'
            else:
                bc, bg, tc = '#CCCCCC', '#F5F5F5', '#AAAAAA'
                body = f'<div style="font-size:0.88em;color:#CCCCCC;font-style:italic;margin-top:4px;">Not yet agreed</div>'
            st.markdown(
                f'<div style="border-left:4px solid {bc};background:{bg};'
                f'border-radius:0 6px 6px 0;padding:10px 12px;margin-bottom:8px;">'
                f'<div style="font-size:0.72em;font-weight:700;color:{tc};letter-spacing:1px;">{dept.upper()}</div>'
                f'{body}</div>',
                unsafe_allow_html=True,
            )

    # ── Row 2: Strategy Cascade (full width) ──────────────────────────────────

    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.75em;font-weight:700;letter-spacing:2px;'
        f'color:#888;margin-bottom:8px;">STRATEGY CASCADE</div>',
        unsafe_allow_html=True,
    )

    if not casc_alive:
        st.markdown(
            f'<div style="background:#F5F5F5;border-radius:8px;padding:16px;'
            f'text-align:center;font-size:0.9em;color:#AAAAAA;font-style:italic;">'
            f'Strategic choices and departmental decisions will appear here as the cascade progresses.</div>',
            unsafe_allow_html=True,
        )
    else:
        casc_cols = st.columns(2)
        for i, choice in enumerate(CASCADE_CHOICES):
            with casc_cols[i % 2]:
                dept_rows_html = ''
                for dept in OT_DEPARTMENTS:
                    locked = (
                        casc_contribs[
                            (casc_contribs['ChoiceID'] == choice['id']) &
                            (casc_contribs['Department'] == dept) &
                            (casc_contribs['Status'] == 'locked')
                        ]
                        if not casc_contribs.empty else casc_contribs
                    )
                    is_last = dept == OT_DEPARTMENTS[-1]
                    border  = '' if is_last else 'border-bottom:1px solid rgba(80,20,75,0.08);'
                    if not locked.empty:
                        text = ' · '.join(str(t) for t in locked['Text'].tolist() if str(t).strip())
                        if len(text) > 130:
                            text = text[:127] + '…'
                        dept_rows_html += (
                            f'<div style="padding:6px 0;{border}">'
                            f'<div style="font-size:0.65em;font-weight:700;color:{WINE};'
                            f'letter-spacing:0.8px;margin-bottom:2px;">{dept.upper()}</div>'
                            f'<div style="font-size:0.82em;color:#333;line-height:1.45;">{text}</div>'
                            f'</div>'
                        )
                    else:
                        dept_rows_html += (
                            f'<div style="padding:6px 0;{border}">'
                            f'<div style="font-size:0.65em;font-weight:700;color:#CCCCCC;'
                            f'letter-spacing:0.8px;margin-bottom:2px;">{dept.upper()}</div>'
                            f'<div style="font-size:0.82em;color:#CCCCCC;font-style:italic;">Pending</div>'
                            f'</div>'
                        )
                st.markdown(
                    f'<div style="border:1px solid #E8E0E8;border-top:3px solid {WINE};'
                    f'border-radius:0 0 8px 8px;padding:14px 16px;margin-bottom:12px;">'
                    f'<div style="font-size:0.68em;font-weight:700;color:{WINE};'
                    f'letter-spacing:1px;margin-bottom:4px;">CHOICE {choice["number"]}</div>'
                    f'<div style="font-weight:700;font-size:0.95em;color:#1a1a1a;'
                    f'margin-bottom:10px;line-height:1.3;">{choice["title"]}</div>'
                    f'{dept_rows_html}</div>',
                    unsafe_allow_html=True,
                )

_overview()
