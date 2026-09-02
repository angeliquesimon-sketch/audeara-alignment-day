"""Different Styles, Shared Direction — participant activity page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, with_retry, _sheets, _clear_sheets
from styles_shared import (
    HEX, TEXT, TEAM, SCENARIOS, COLOUR_DESCRIPTORS,
    _ensure_styles_tab, _ensure_session_tab, _ensure_summaries_tab,
    pull_styles, pull_session, pull_summaries, save_scenario,
    compute_scores, top_two, colour_bar, card_html_large, card_html_small,
)

inject_styles()

# ── Spectrum chart (pure SVG — no matplotlib) ─────────────────────────────────────

def _render_spectrum(current, sc, df, started_at):
    """Horizontal spectrum as inline SVG."""
    col = f'S{current + 1}'
    lc  = HEX[sc['left_colour']]
    rc  = HEX[sc['right_colour']]

    if df.empty:
        return None
    df_shown = df[df['Timestamp'] >= started_at] if started_at else df
    if df_shown.empty:
        return None

    people = [(row['Name'].split()[0], int(row[col])) for _, row in df_shown.iterrows()]

    W, LINE_Y, H = 600, 46, 90

    bucket_rank: dict = {}
    dots_svg = ''
    for name, val in sorted(people, key=lambda x: x[1]):
        bucket = round(val / 5) * 5
        bucket_rank[bucket] = bucket_rank.get(bucket, 0) + 1
        rank = bucket_rank[bucket]
        x = val * W / 100
        color = lc if val < 50 else (rc if val > 50 else '#999999')
        label_y = LINE_Y - 12 - (rank - 1) * 14
        dots_svg += (
            f'<circle cx="{x:.1f}" cy="{LINE_Y}" r="6" fill="{color}" '
            f'stroke="white" stroke-width="1.5" opacity="0.92"/>'
            f'<text x="{x:.1f}" y="{label_y}" text-anchor="middle" '
            f'font-size="9" fill="#333333" font-family="sans-serif">{name}</text>'
        )

    return (
        f'<div style="background:#FAFAFA;border-radius:6px;padding:4px 0;margin:4px 0;">'
        f'<svg viewBox="0 0 {W} {H}" style="width:100%;">'
        f'<rect x="0" y="{LINE_Y-8}" width="300" height="16" fill="{lc}" opacity="0.07"/>'
        f'<rect x="300" y="{LINE_Y-8}" width="300" height="16" fill="{rc}" opacity="0.07"/>'
        f'<line x1="0" y1="{LINE_Y}" x2="{W}" y2="{LINE_Y}" '
        f'stroke="#CCCCCC" stroke-width="2" stroke-linecap="round"/>'
        f'<line x1="300" y1="{LINE_Y-9}" x2="300" y2="{LINE_Y+9}" stroke="#E0E0E0" stroke-width="1"/>'
        f'{dots_svg}'
        f'<text x="5" y="{H-5}" font-size="9" fill="{lc}" font-weight="bold" '
        f'font-family="sans-serif">{sc["left_colour"]}</text>'
        f'<text x="{W-5}" y="{H-5}" text-anchor="end" font-size="9" fill="{rc}" '
        f'font-weight="bold" font-family="sans-serif">{sc["right_colour"]}</text>'
        f'</svg></div>'
    )


def _team_map_svg(profiles, width=600, height=430):
    """Pure SVG team scatter map — no matplotlib needed."""
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

# ── Init ─────────────────────────────────────────────────────────────────────────

if not st.session_state.get('_styles_tab_ensured'):
    try:
        with_retry(_ensure_styles_tab,    on_retry=_clear_sheets)
        with_retry(_ensure_session_tab,   on_retry=_clear_sheets)
        with_retry(_ensure_summaries_tab, on_retry=_clear_sheets)
        st.session_state['_styles_tab_ensured'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue — some features may not save correctly. ({_e})')

# ── Page ─────────────────────────────────────────────────────────────────────────

st.markdown('### Team Activity — Different Styles, Shared Direction')
st.markdown(
    'We all approach decisions, change and collaboration differently. '
    'This activity makes those differences visible and explores how they shape the way we work together. '
    'One thing to know before you start: your results are visible to the whole team, not anonymous. '
    'This is intentional. The goal is to understand each other better, not to judge where anyone lands.'
)
st.markdown(
    f'<div class="activity-card">'
    f'<strong>Borrowed from <em>Surrounded by Idiots</em> by Thomas Erikson</strong> — a book with a title that sounds '
    f'like a complaint and turns out to be an invitation. The premise: the people who frustrate you most '
    f'aren\'t doing it on purpose. They just have a completely different set of instincts to you. '
    f'We\'re mapping those today.'
    f'</div>',
    unsafe_allow_html=True,
)
st.markdown('')

tab_submit, tab_team = st.tabs(['🧭 Submit your results', '🎨 Team map'])

# ── Submit tab ──────────────────────────────────────────────────────────────────

@st.fragment(run_every=4)
def _scenario_view():
    _name = st.session_state.get('styles_guided_name', 'Select your name...')
    if not _name or _name == 'Select your name...':
        return

    session    = pull_session()
    current    = int(session.get('current_scenario', -1))
    reveal     = session.get('reveal_active', '0') == '1'
    started_at = session.get('scenario_started_at', '')

    # ── Not started ──────────────────────────────────────────────────────────────
    if current == -1:
        st.markdown('')
        st.info(
            'Waiting for the facilitator to start. '
            'Keep this page open — it will update automatically.'
        )
        return

    # ── Activity complete ─────────────────────────────────────────────────────────
    if current >= len(SCENARIOS):
        df_all = pull_styles()
        if not df_all.empty and _name in df_all['Name'].values:
            row    = df_all[df_all['Name'] == _name].iloc[0]
            scores = compute_scores(row)
            st.success('All six scenarios done!')
            st.markdown(card_html_large(_name, scores), unsafe_allow_html=True)
            st.caption('Head to the Team map tab to see where everyone landed.')
        else:
            st.info('Activity complete. Head to the Team map tab to see the results.')
        return

    # ── Active scenario ───────────────────────────────────────────────────────────
    sc            = SCENARIOS[current]
    submitted_key = f'_styles_submitted_s{current}'
    submitted     = st.session_state.get(submitted_key, False)

    st.markdown(
        f'<div style="margin:16px 0 10px;">'
        f'<div style="font-size:0.68em;font-weight:700;letter-spacing:0.12em;'
        f'text-transform:uppercase;color:#bbb;margin-bottom:4px;">'
        f'Scenario {current + 1} of {len(SCENARIOS)}</div>'
        f'<div style="font-size:1.2em;font-weight:700;color:#111;margin-bottom:6px;">{sc["title"]}</div>'
        f'<div style="font-size:0.92em;color:#555;line-height:1.6;">{sc["prompt"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    lc = HEX[sc['left_colour']]  if reveal else '#999'
    rc = HEX[sc['right_colour']] if reveal else '#999'

    c_left, c_mid, c_right = st.columns([2, 4, 2])
    with c_left:
        html = (
            f'<div style="text-align:right;padding-top:8px;">'
            f'<div style="font-weight:700;color:{lc};font-size:0.88em;">{sc["left_label"]}</div>'
        )
        if reveal:
            html += f'<div style="font-size:0.73em;color:{lc};opacity:0.8;">{sc["left_colour"]}</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
    with c_mid:
        val = st.slider(
            f'Scenario {current + 1}',
            min_value=0, max_value=100, value=50,
            label_visibility='collapsed',
            key=f'guided_s{current}',
            disabled=submitted,
        )
    with c_right:
        html = (
            f'<div style="text-align:left;padding-top:8px;">'
            f'<div style="font-weight:700;color:{rc};font-size:0.88em;">{sc["right_label"]}</div>'
        )
        if reveal:
            html += f'<div style="font-size:0.73em;color:{rc};opacity:0.8;">{sc["right_colour"]}</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    st.markdown('')

    if submitted:
        if reveal:
            col_l, col_r = st.columns(2)
            for col, colour in [(col_l, sc['left_colour']), (col_r, sc['right_colour'])]:
                ch   = HEX[colour]
                desc = COLOUR_DESCRIPTORS[colour]
                with col:
                    st.markdown(
                        f'<div style="border-left:3px solid {ch};background:{ch}18;'
                        f'border-radius:0 6px 6px 0;padding:12px 14px;">'
                        f'<div style="font-weight:700;color:{ch};margin-bottom:5px;">{colour}</div>'
                        f'<div style="font-size:0.82em;color:#555;line-height:1.5;">{desc}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            svg_html = _render_spectrum(current, sc, pull_styles(), started_at)
            if svg_html:
                st.markdown(svg_html, unsafe_allow_html=True)
            st.markdown(
                f'<div style="background:#F5F5F5;border-radius:6px;padding:14px 16px;margin-top:4px;">'
                f'<div style="font-size:0.68em;font-weight:700;letter-spacing:0.1em;'
                f'text-transform:uppercase;color:#bbb;margin-bottom:6px;">Discuss</div>'
                f'<div style="font-size:0.88em;color:#444;line-height:1.6;">{sc["discussion"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.success('Submitted. Waiting for the colour reveal...')
    else:
        if st.button('Submit', type='primary', use_container_width=True, key=f'submit_s{current}'):
            try:
                save_scenario(_name, current, val)
                st.session_state[submitted_key] = True
                st.cache_data.clear()
                st.rerun()
            except Exception as _e:
                st.error(f'Could not save — please try again. ({_e})')


# ── Team cards fragment (auto-refreshes to pick up AI summaries) ─────────────────

@st.fragment(run_every=10)
def _team_cards():
    df_c      = pull_styles()
    summaries = pull_summaries()
    session_c = pull_session()
    activity_complete = int(session_c.get('current_scenario', -1)) >= len(SCENARIOS)

    if df_c.empty:
        st.info('No results yet. The team map will appear here as responses come in.')
        return

    profiles = []
    for _, row in df_c.iterrows():
        sc_score = compute_scores(row)
        pri, sec = top_two(sc_score)
        profiles.append({'name': row['Name'], 'scores': sc_score, 'primary': pri, 'secondary': sec})

    st.markdown(
        f'<div style="margin-bottom:16px;">'
        f'<span style="font-size:1.1em;font-weight:700;">The team</span>'
        f'&nbsp;&nbsp;<span style="font-size:0.8em;color:#999;font-weight:400;">'
        f'{len(profiles)} of {len(TEAM)} submitted</span></div>',
        unsafe_allow_html=True,
    )

    n_cols = 4
    for i in range(0, len(profiles), n_cols):
        batch = profiles[i:i + n_cols]
        cols  = st.columns(n_cols)
        for col, p in zip(cols, batch):
            with col:
                st.markdown(card_html_small(p['name'], p['scores']), unsafe_allow_html=True)
                if activity_complete and p['name'] in summaries:
                    st.markdown(
                        f'<div style="font-size:0.75em;color:#444;line-height:1.55;'
                        f'margin:4px 2px 14px;padding:8px 10px;background:#F7F7F7;'
                        f'border-radius:6px;">{summaries[p["name"]]}</div>',
                        unsafe_allow_html=True,
                    )


with tab_submit:
    st.selectbox('Your name', ['Select your name...'] + TEAM, key='styles_guided_name')
    name = st.session_state.get('styles_guided_name', 'Select your name...')
    if name and name != 'Select your name...':
        _scenario_view()

# ── Team map tab ─────────────────────────────────────────────────────────────────

with tab_team:

    c_ref, _ = st.columns([1, 8])
    with c_ref:
        if st.button('Refresh', key='styles_refresh'):
            st.cache_data.clear()
            st.rerun()

    # ── Colour reference ──────────────────────────────────────────────────────────

    cols_def = st.columns(4)
    for col, colour in zip(cols_def, ['Red', 'Blue', 'Yellow', 'Green']):
        ch   = HEX[colour]
        desc = COLOUR_DESCRIPTORS[colour]
        with col:
            st.markdown(
                f'<div style="border-left:4px solid {ch};background:{ch}12;'
                f'border-radius:0 6px 6px 0;padding:10px 12px;margin-bottom:16px;">'
                f'<div style="font-weight:700;color:{ch};margin-bottom:4px;">{colour}</div>'
                f'<div style="font-size:0.78em;color:#444;line-height:1.5;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    df = pull_styles()

    profiles = []
    if not df.empty:
        for _, row in df.iterrows():
            sc_score = compute_scores(row)
            pri, sec = top_two(sc_score)
            profiles.append({'name': row['Name'], 'scores': sc_score, 'primary': pri, 'secondary': sec})

    _team_cards()

    if not df.empty:
        st.divider()

        st.markdown('#### Team map')
        st.caption(
            'X axis: Blue (analytical) to Red (decisive). '
            'Y axis: Green (people-first) to Yellow (possibility-first).'
        )

        st.markdown(_team_map_svg(profiles), unsafe_allow_html=True)

        st.divider()

        with st.expander('Individual breakdown'):
            st.caption("Each person's full colour mix across all six scenarios.")
            summaries_bd = pull_summaries()
            session_bd   = pull_session()
            activity_complete_bd = int(session_bd.get('current_scenario', -1)) >= len(SCENARIOS)
            for p in sorted(profiles, key=lambda x: (x['primary'], x['secondary'])):
                bar  = ''.join(
                    f'<div style="flex:{p["scores"][c]};background:{HEX[c]};min-width:2px;'
                    f'display:flex;align-items:center;justify-content:center;">'
                    + (f'<span style="font-size:0.7em;font-weight:700;color:{TEXT[c]};'
                       f'opacity:0.9;white-space:nowrap;">{p["scores"][c]}%</span>'
                       if p['scores'][c] >= 10 else '')
                    + '</div>'
                    for c in ['Red', 'Blue', 'Yellow', 'Green']
                )
                pc_b = HEX[p['primary']]
                tc_b = TEXT[p['primary']]
                st.markdown(
                    f'<div style="display:flex;align-items:center;margin:5px 0;gap:10px;">'
                    f'<div style="width:120px;font-size:0.84em;color:#444;text-align:right;flex-shrink:0;">'
                    f'{p["name"]}</div>'
                    f'<div style="display:flex;border-radius:4px;overflow:hidden;height:22px;flex:1;">{bar}</div>'
                    f'<div style="flex-shrink:0;background:{pc_b};color:{tc_b};font-size:0.7em;'
                    f'font-weight:700;padding:3px 10px;border-radius:20px;white-space:nowrap;">'
                    f'{p["primary"]} / {p["secondary"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if activity_complete_bd and p['name'] in summaries_bd:
                    st.markdown(
                        f'<div style="display:flex;gap:10px;margin:-2px 0 10px;">'
                        f'<div style="width:120px;flex-shrink:0;"></div>'
                        f'<div style="flex:1;font-size:0.76em;color:#555;line-height:1.55;'
                        f'padding:6px 10px;background:#F7F7F7;border-radius:4px;">'
                        f'{summaries_bd[p["name"]]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        st.divider()

        # ── Per-scenario spectrums ─────────────────────────────────────────────────

        st.markdown('#### Scenario breakdown')
        st.caption('Where the team landed on each of the six spectrums.')

        for i, sc_item in enumerate(SCENARIOS):
            lc = HEX[sc_item['left_colour']]
            rc = HEX[sc_item['right_colour']]
            st.markdown(
                f'<div style="margin:24px 0 6px;">'
                f'<div style="font-size:0.68em;font-weight:700;letter-spacing:0.12em;'
                f'text-transform:uppercase;color:#bbb;margin-bottom:3px;">Scenario {i + 1}</div>'
                f'<div style="font-size:0.95em;font-weight:700;color:#111;margin-bottom:4px;">{sc_item["title"]}</div>'
                f'<div style="font-size:0.82em;color:#666;line-height:1.55;margin-bottom:8px;">{sc_item["prompt"]}</div>'
                f'<div style="display:flex;gap:8px;">'
                f'<div style="flex:1;font-size:0.78em;font-weight:700;color:{lc};'
                f'background:{lc}12;border-left:3px solid {lc};border-radius:0 4px 4px 0;'
                f'padding:6px 10px;">{sc_item["left_label"]}</div>'
                f'<div style="flex:1;font-size:0.78em;font-weight:700;color:{rc};'
                f'background:{rc}12;border-right:3px solid {rc};border-radius:4px 0 0 4px;'
                f'padding:6px 10px;text-align:right;">{sc_item["right_label"]}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            svg_html = _render_spectrum(i, sc_item, df, started_at='')
            if svg_html:
                st.markdown(svg_html, unsafe_allow_html=True)
