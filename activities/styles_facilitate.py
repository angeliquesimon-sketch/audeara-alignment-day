"""Facilitator control panel — Different Styles activity."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from datetime import datetime
from utils import inject_styles, with_retry, _sheets, PURPLE, TEAL
from styles_shared import (
    TEAM, SCENARIOS, HEX, TEXT,
    _ensure_styles_tab, _ensure_session_tab, _ensure_summaries_tab,
    pull_styles, pull_session, pull_summaries, set_session,
    save_summary, generate_summary,
    compute_scores, top_two, colour_bar, card_html_small,
)

inject_styles()

# ── Pure-SVG team map (no matplotlib) ────────────────────────────────────────────

def _team_map_svg(profiles, width=600, height=430):
    hw, hh = width // 2, height // 2
    dots_svg = ''
    for p in profiles:
        s  = p['scores']
        xn = max(0.05, min(0.95, (s['Red']    - s['Blue'])  / 200 + 0.5))
        yn = max(0.05, min(0.95, (s['Yellow'] - s['Green']) / 200 + 0.5))
        cx = int(xn * width)
        cy = int((1 - yn) * height)
        color = HEX[p['primary']]
        name  = p['name'].split()[0]
        dots_svg += (
            f'<circle cx="{cx}" cy="{cy}" r="10" fill="{color}" '
            f'stroke="white" stroke-width="2" opacity="0.92"/>'
            f'<text x="{cx}" y="{cy - 14}" text-anchor="middle" '
            f'font-size="10" fill="#333333" font-family="sans-serif">{name}</text>'
        )
    return (
        f'<div style="background:#F9F9F9;border-radius:8px;padding:8px 0;">'
        f'<svg viewBox="0 0 {width} {height}" style="width:100%;">'
        f'<rect x="0" y="0" width="{hw}" height="{hh}" fill="#F5A623" opacity="0.05"/>'
        f'<rect x="{hw}" y="0" width="{hw}" height="{hh}" fill="#E84040" opacity="0.05"/>'
        f'<rect x="0" y="{hh}" width="{hw}" height="{hh}" fill="#4285C8" opacity="0.05"/>'
        f'<rect x="{hw}" y="{hh}" width="{hw}" height="{hh}" fill="#3EAA6D" opacity="0.05"/>'
        f'<line x1="{hw}" y1="0" x2="{hw}" y2="{height}" stroke="#dddddd" stroke-width="1.2"/>'
        f'<line x1="0" y1="{hh}" x2="{width}" y2="{hh}" stroke="#dddddd" stroke-width="1.2"/>'
        f'<text x="10" y="{hh}" dominant-baseline="middle" font-size="11" '
        f'fill="#4285C8" font-weight="bold" font-family="sans-serif">Blue</text>'
        f'<text x="{width-10}" y="{hh}" text-anchor="end" dominant-baseline="middle" '
        f'font-size="11" fill="#E84040" font-weight="bold" font-family="sans-serif">Red</text>'
        f'<text x="{hw}" y="{height-8}" text-anchor="middle" font-size="11" '
        f'fill="#3EAA6D" font-weight="bold" font-family="sans-serif">Green</text>'
        f'<text x="{hw}" y="16" text-anchor="middle" font-size="11" '
        f'fill="#F5A623" font-weight="bold" font-family="sans-serif">Yellow</text>'
        f'{dots_svg}'
        f'</svg></div>'
    )

# ── Password ─────────────────────────────────────────────────────────────────────

if 'styles_fac_auth' not in st.session_state:
    st.session_state['styles_fac_auth'] = False

if not st.session_state['styles_fac_auth']:
    st.caption('This page is for the session facilitator only.')
    pwd_input = st.text_input('Password', type='password', key='styles_fac_pw')
    if st.button('Unlock', type='primary', key='styles_fac_unlock'):
        if pwd_input == st.secrets.get('FACILITATE_PASSWORD', ''):
            st.session_state['styles_fac_auth'] = True
            st.rerun()
        else:
            st.error('Incorrect password.')
    st.stop()

# ── Setup ─────────────────────────────────────────────────────────────────────────

if st.button('🔒 Lock', key='styles_fac_lock'):
    st.session_state['styles_fac_auth'] = False
    st.rerun()

if not st.session_state.get('_styles_fac_tab_ensured'):
    try:
        with_retry(_ensure_styles_tab,    on_retry=_sheets.clear)
        with_retry(_ensure_session_tab,   on_retry=_sheets.clear)
        with_retry(_ensure_summaries_tab, on_retry=_sheets.clear)
        st.session_state['_styles_fac_tab_ensured'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue. ({_e})')

st.markdown('### 🎛️ Facilitate — Different Styles')

# ── Load state ────────────────────────────────────────────────────────────────────

session    = pull_session()
current    = int(session.get('current_scenario', -1))
reveal     = session.get('reveal_active', '0') == '1'
started_at = session.get('scenario_started_at', '')
n_scen     = len(SCENARIOS)
n_total    = len(TEAM)

# ── Status banner ─────────────────────────────────────────────────────────────────

if current == -1:
    status_bg, status_tc = '#F0F0F0', '#666'
    status_text = 'Not started'
elif current >= n_scen:
    status_bg, status_tc = '#3EAA6D', '#fff'
    status_text = 'Activity complete'
else:
    status_bg, status_tc = PURPLE, '#fff'
    status_text = f'Scenario {current + 1} of {n_scen} — {SCENARIOS[current]["title"]}'
    if reveal:
        status_text += ' · Colours revealed'

st.markdown(
    f'<div style="background:{status_bg};color:{status_tc};border-radius:10px;'
    f'padding:14px 22px;margin-bottom:20px;font-weight:700;font-size:1.05em;">'
    f'{status_text}</div>',
    unsafe_allow_html=True,
)

# ── Controls ──────────────────────────────────────────────────────────────────────

col_a, col_b, col_c, col_d, col_e = st.columns(5)

with col_a:
    if current == -1:
        if st.button('▶  Start activity', type='primary', use_container_width=True):
            set_session('current_scenario', '0')
            set_session('reveal_active', '0')
            set_session('scenario_started_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            st.rerun()
    elif current < n_scen:
        next_label = (
            f'→  Scenario {current + 2}' if current < n_scen - 1 else '✓  End activity'
        )
        if st.button(next_label, type='primary', use_container_width=True):
            set_session('current_scenario', str(current + 1))
            set_session('reveal_active', '0')
            set_session('scenario_started_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            st.rerun()

with col_b:
    if current > 0:
        back_label = (
            f'←  Scenario {current}' if current <= n_scen else f'←  Scenario {n_scen}'
        )
        if st.button(back_label, use_container_width=True):
            set_session('current_scenario', str(current - 1))
            set_session('reveal_active', '0')
            # Clear started_at so tracker counts all existing submissions (no timestamp filter)
            set_session('scenario_started_at', '')
            st.rerun()

with col_c:
    if 0 <= current < n_scen:
        reveal_label = '🙈  Hide colours' if reveal else '🎨  Reveal colours'
        if st.button(reveal_label, use_container_width=True):
            set_session('reveal_active', '0' if reveal else '1')
            st.rerun()

with col_d:
    if current != -1:
        if st.button('↩  Reset activity', use_container_width=True):
            set_session('current_scenario', '-1')
            set_session('reveal_active', '0')
            set_session('scenario_started_at', '')
            st.rerun()

with col_e:
    if st.button('↺  Refresh', use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ── Submission tracker ────────────────────────────────────────────────────────────

if 0 <= current < n_scen:
    df = pull_styles()

    if not df.empty and started_at:
        submitted_names = set(df[df['Timestamp'] >= started_at]['Name'].values)
    elif not df.empty:
        submitted_names = set(df['Name'].values)
    else:
        submitted_names = set()

    n_done = len(submitted_names)

    st.markdown(
        f'<div style="margin-bottom:10px;">'
        f'<span style="font-weight:700;">Scenario {current + 1} responses</span>'
        f'&nbsp;&nbsp;<span style="font-size:0.85em;color:#999;">{n_done} of {n_total}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.progress(n_done / n_total if n_total > 0 else 0)
    st.markdown('')

    cols = st.columns(3)
    for i, person in enumerate(TEAM):
        done = person in submitted_names
        bg   = '#E8F5EE' if done else '#F5F5F5'
        tc   = '#2D7D4F' if done else '#AAAAAA'
        fw   = '600' if done else '400'
        icon = '✓' if done else '○'
        cols[i % 3].markdown(
            f'<div style="background:{bg};border-radius:6px;padding:8px 12px;'
            f'margin-bottom:6px;font-size:0.84em;color:{tc};font-weight:{fw};">'
            f'{icon} {person}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Current scenario detail ───────────────────────────────────────────────────

    sc = SCENARIOS[current]
    lc = HEX[sc['left_colour']]  if reveal else '#AAAAAA'
    rc = HEX[sc['right_colour']] if reveal else '#AAAAAA'

    st.markdown(f'**{sc["title"]}** — _{sc["prompt"]}_')
    st.markdown('')

    c_left, c_right = st.columns(2)
    with c_left:
        body = f'<div style="font-weight:700;color:{lc};">{sc["left_label"]}</div>'
        if reveal:
            body += f'<div style="font-size:0.75em;color:{lc};opacity:0.85;">{sc["left_colour"]}</div>'
        st.markdown(
            f'<div style="padding:10px 14px;background:{lc}18;border-left:4px solid {lc};border-radius:4px;">'
            f'{body}</div>',
            unsafe_allow_html=True,
        )
    with c_right:
        body = f'<div style="font-weight:700;color:{rc};">{sc["right_label"]}</div>'
        if reveal:
            body += f'<div style="font-size:0.75em;color:{rc};opacity:0.85;">{sc["right_colour"]}</div>'
        st.markdown(
            f'<div style="padding:10px 14px;background:{rc}18;border-left:4px solid {rc};border-radius:4px;">'
            f'{body}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

# ── Live team map ─────────────────────────────────────────────────────────────────

if current >= 0:
    expanded = current >= n_scen
    with st.expander('Live team map', expanded=expanded):
        df_map = pull_styles()
        if df_map.empty:
            st.info('No submissions yet.')
        else:
            profiles = []
            for _, row in df_map.iterrows():
                sc_scores = compute_scores(row)
                pri, sec  = top_two(sc_scores)
                profiles.append({
                    'name': row['Name'], 'scores': sc_scores,
                    'primary': pri, 'secondary': sec,
                })

            n_cols = 4
            for i in range(0, len(profiles), n_cols):
                batch = profiles[i:i + n_cols]
                cols  = st.columns(n_cols)
                for col, p in zip(cols, batch):
                    with col:
                        st.markdown(card_html_small(p['name'], p['scores']), unsafe_allow_html=True)

            if len(profiles) >= 2:
                st.markdown(_team_map_svg(profiles), unsafe_allow_html=True)

# ── AI summaries ──────────────────────────────────────────────────────────────────

if current >= n_scen:
    st.divider()
    st.markdown('### AI summaries')
    st.markdown(
        'Generate a short personalised summary for each team member based on their colour profile. '
        'Once generated, summaries appear live under each card on the participant Team map tab.'
    )

    df_sum  = pull_styles()
    summaries = pull_summaries()

    if df_sum.empty:
        st.info('No submissions yet — nothing to summarise.')
    else:
        profiles = []
        for _, row in df_sum.iterrows():
            sc_scores = compute_scores(row)
            pri, sec  = top_two(sc_scores)
            profiles.append({'name': row['Name'], 'scores': sc_scores, 'primary': pri, 'secondary': sec})

        already_done = [p for p in profiles if p['name'] in summaries]
        pending      = [p for p in profiles if p['name'] not in summaries]

        if pending:
            btn_label = (
                'Generate summaries' if not already_done
                else f'Generate remaining {len(pending)} summaries'
            )
            if st.button(btn_label, type='primary'):
                progress = st.progress(0)
                status   = st.empty()
                for i, p in enumerate(pending):
                    status.markdown(f'Generating summary for **{p["name"]}**...')
                    try:
                        text = generate_summary(p['name'], p['scores'], p['primary'], p['secondary'])
                        save_summary(p['name'], text)
                    except Exception as _e:
                        st.warning(f'Failed for {p["name"]}: {_e}')
                    progress.progress((i + 1) / len(pending))
                status.markdown('Done.')
                st.cache_data.clear()
                st.rerun()
        else:
            st.success(f'All {len(profiles)} summaries generated.')

        if summaries:
            st.markdown('---')
            for p in profiles:
                if p['name'] in summaries:
                    pri_hex = HEX[p['primary']]
                    st.markdown(
                        f'<div style="border-left:4px solid {pri_hex};padding:10px 16px;'
                        f'margin-bottom:10px;background:{pri_hex}0D;border-radius:4px;">'
                        f'<strong style="color:{pri_hex};">{p["name"]}</strong><br>'
                        f'<span style="font-size:0.9em;color:#333;">{summaries[p["name"]]}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
