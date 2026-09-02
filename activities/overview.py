"""Overview — Alignment Day home base. Brand funnel fills live as activities complete."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from utils import inject_styles, _sheets, PURPLE, TEAL
from styles_shared import TEAM as STYLES_TEAM

inject_styles()

SHEET_ID           = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'
MISSION_CATEGORIES = ['Who', 'What', 'How', 'Makes Possible']
VALUES             = 'Impact  ·  Quality  ·  Leadership  ·  Momentum'
MOTTO              = 'Feel connected.'

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

cols = st.columns(3)
for i, rule in enumerate(RULES):
    with cols[i % 3]:
        st.markdown(
            f'<div style="background:#F5F5F5;border-radius:8px;padding:12px 14px;'
            f'margin-bottom:10px;font-size:0.84em;color:#444;line-height:1.5;">'
            f'<span style="color:{TEAL};font-weight:700;margin-right:6px;">✦</span>{rule}</div>',
            unsafe_allow_html=True,
        )

st.divider()

# ── Why we're here ────────────────────────────────────────────────────────────

col_why, col_leave = st.columns(2)

with col_why:
    st.markdown(
        f'<div style="border-left:4px solid {PURPLE};background:#F7F0F7;'
        f'border-radius:0 8px 8px 0;padding:14px 18px;height:100%;">'
        f'<div style="font-weight:700;color:{PURPLE};margin-bottom:10px;">Why we\'re here</div>'
        f'<ul style="margin:0;padding-left:16px;font-size:0.85em;color:#444;line-height:1.8;">'
        f'<li>Reflect on where Audeara has come from</li>'
        f'<li>Clarify why we exist and where we are going</li>'
        f'<li>Agree on how we make strategic choices</li>'
        f'<li>Strengthen how we work together</li>'
        f'<li>Build a clearer link between company strategy and everyday decisions</li>'
        f'</ul></div>',
        unsafe_allow_html=True,
    )

with col_leave:
    st.markdown(
        f'<div style="border-left:4px solid {TEAL};background:#F0F8F8;'
        f'border-radius:0 8px 8px 0;padding:14px 18px;height:100%;">'
        f'<div style="font-weight:700;color:{TEAL};margin-bottom:10px;">What we want to leave with</div>'
        f'<ul style="margin:0;padding-left:16px;font-size:0.85em;color:#444;line-height:1.8;">'
        f'<li>Shared mission and vision themes</li>'
        f'<li>A clearer picture of Audeara\'s future</li>'
        f'<li>Greater understanding of our strategic choices</li>'
        f'<li>A common approach to prioritisation</li>'
        f'<li>Better understanding of how different working styles affect communication</li>'
        f'<li>Clear inputs for the FY27 strategy and beyond</li>'
        f'</ul></div>',
        unsafe_allow_html=True,
    )

st.markdown('')

@st.fragment(run_every=20)
def _overview():
    mission_top  = _mission_top()
    vision_final = _vision_locked()
    n_mission    = _row_count('Submissions')
    n_vision     = _row_count('Vision Submissions')
    n_styles     = _row_count('Styles Submissions')
    n_team       = len(STYLES_TEAM)

    mission_done  = len(mission_top) == 4
    mission_alive = n_mission > 0
    vision_done   = bool(vision_final)
    vision_alive  = n_vision > 0
    styles_done   = n_styles >= n_team
    styles_alive  = n_styles > 0

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
        font-size="9" font-weight="700" letter-spacing="2.5" fill="white" opacity="0.7">MOTTO</text>
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
                f'<div style="font-size:0.88em;line-height:1.7;margin-top:6px;">'
                f'We help <strong>{mission_top["Who"]}</strong> '
                f'do <strong>{mission_top["What"]}</strong> '
                f'by <strong>{mission_top["How"]}</strong>, '
                f'so they can <strong>{mission_top["Makes Possible"]}</strong>.'
                f'</div>'
            )
        elif mission_alive:
            m_bc, m_bg, m_icon = '#C4A0C2', '#FAF5FA', '💬'
            m_heading = f'Mission Statement — {n_mission} idea{"s" if n_mission != 1 else ""} in'
            m_body = '<div style="font-size:0.82em;color:#999;margin-top:4px;">Voting will surface the top answers.</div>'
        else:
            m_bc, m_bg, m_icon = '#CCCCCC', '#F5F5F5', '⏳'
            m_heading = 'Mission Statement'
            m_body = '<div style="font-size:0.82em;color:#AAAAAA;margin-top:4px;">What do we provide? Who do we serve? How do we do that? What does that make possible?</div>'

        st.markdown(
            f'<div style="border-left:4px solid {m_bc};background:{m_bg};'
            f'border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:12px;">'
            f'<div style="font-weight:700;font-size:0.85em;color:{m_bc};">{m_icon} {m_heading}</div>'
            f'{m_body}</div>',
            unsafe_allow_html=True,
        )

        # Vision panel
        if vision_done:
            v_bc, v_bg, v_icon = '#188383', '#F0F8F8', '✅'
            v_heading = 'Vision Statement'
            v_body = f'<div style="font-size:0.88em;line-height:1.7;margin-top:6px;font-style:italic;">"{vision_final}"</div>'
        elif vision_alive:
            v_bc, v_bg, v_icon = '#9BCFCF', '#F3FAFA', '🎨'
            v_heading = f'Vision — {n_vision} cover {"stories" if n_vision != 1 else "story"} in'
            v_body = '<div style="font-size:0.82em;color:#999;margin-top:4px;">Voting will surface the top answers. Facilitator locks the final statement.</div>'
        else:
            v_bc, v_bg, v_icon = '#CCCCCC', '#F5F5F5', '⏳'
            v_heading = 'Vision Statement'
            v_body = '<div style="font-size:0.82em;color:#AAAAAA;margin-top:4px;">Where are we in 3–5 years? What have we achieved? Who have we become?</div>'

        st.markdown(
            f'<div style="border-left:4px solid {v_bc};background:{v_bg};'
            f'border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:12px;">'
            f'<div style="font-weight:700;font-size:0.85em;color:{v_bc};">{v_icon} {v_heading}</div>'
            f'{v_body}</div>',
            unsafe_allow_html=True,
        )

        # Values (always filled)
        st.markdown(
            f'<div style="border-left:4px solid #50144B;background:#F5EFF5;'
            f'border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:12px;">'
            f'<div style="font-weight:700;font-size:0.85em;color:#50144B;">Values</div>'
            f'<div style="font-size:0.88em;color:#50144B;font-weight:600;margin-top:4px;">{VALUES}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Motto (always filled)
        st.markdown(
            f'<div style="border-left:4px solid #005E63;background:#EDF5F5;'
            f'border-radius:0 8px 8px 0;padding:14px 16px;">'
            f'<div style="font-weight:700;font-size:0.85em;color:#005E63;">Motto</div>'
            f'<div style="font-size:1em;color:#005E63;font-weight:700;margin-top:4px;">{MOTTO}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Agenda ────────────────────────────────────────────────────────────────

    st.divider()
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
            f'<div style="font-weight:700;color:{tc};">{icon}&nbsp; {label}</div>'
            f'<div style="font-size:0.8em;color:{tc};opacity:0.85;margin-top:3px;">{detail}</div>'
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

_overview()
