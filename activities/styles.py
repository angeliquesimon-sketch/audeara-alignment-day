"""Different Styles, Shared Direction — participant activity page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from utils import inject_styles, with_retry, _sheets
from styles_shared import (
    HEX, TEXT, TEAM, SCENARIOS, COLOUR_DESCRIPTORS,
    _ensure_styles_tab, _ensure_session_tab, _ensure_summaries_tab,
    pull_styles, pull_session, pull_summaries, save_scenario,
    compute_scores, top_two, colour_bar, card_html_large, card_html_small,
)

inject_styles()

# ── Spectrum chart ────────────────────────────────────────────────────────────────

def _render_spectrum(current, sc, df, started_at):
    """Horizontal spectrum showing where each participant landed for this scenario."""
    col = f'S{current + 1}'
    lc  = HEX[sc['left_colour']]
    rc  = HEX[sc['right_colour']]

    if df.empty:
        return None

    df_shown = df[df['Timestamp'] >= started_at] if started_at else df
    if df_shown.empty:
        return None

    people = [(row['Name'].split()[0], int(row[col])) for _, row in df_shown.iterrows()]

    fig, ax = plt.subplots(figsize=(9, 2.4))
    fig.patch.set_facecolor('#FAFAFA')
    ax.set_facecolor('#FAFAFA')

    ax.axvspan(0,   50,  alpha=0.06, color=lc, zorder=0)
    ax.axvspan(50, 100,  alpha=0.06, color=rc, zorder=0)
    ax.axvline(50, color='#E0E0E0', linewidth=1, zorder=1)
    ax.axhline(0.28, color='#CCCCCC', linewidth=2, zorder=1, solid_capstyle='round')

    # Stack labels for clustered positions (bucket to nearest 5)
    bucket_rank = {}
    for name, val in sorted(people, key=lambda x: x[1]):
        bucket = round(val / 5) * 5
        bucket_rank[bucket] = bucket_rank.get(bucket, 0) + 1
        rank = bucket_rank[bucket]

        dot_colour = lc if val < 50 else (rc if val > 50 else '#999999')
        ax.scatter(val, 0.28, s=90, color=dot_colour, zorder=3,
                   edgecolors='white', linewidths=1.5, alpha=0.92)
        ax.annotate(
            name, (val, 0.28),
            textcoords='offset points', xytext=(0, 9 + (rank - 1) * 16),
            ha='center', va='bottom', fontsize=8.5, color='#333333',
        )

    ax.text(1,  -0.05, sc['left_colour'],  ha='left',  va='top', fontsize=9, color=lc, fontweight='bold')
    ax.text(99, -0.05, sc['right_colour'], ha='right', va='top', fontsize=9, color=rc, fontweight='bold')

    ax.set_xlim(-1, 101)
    ax.set_ylim(-0.2, 1.5)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    buf = io.BytesIO()
    fig.tight_layout(pad=0.8)
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf

# ── Init ─────────────────────────────────────────────────────────────────────────

if not st.session_state.get('_styles_tab_ensured'):
    try:
        with_retry(_ensure_styles_tab,    on_retry=_sheets.clear)
        with_retry(_ensure_session_tab,   on_retry=_sheets.clear)
        with_retry(_ensure_summaries_tab, on_retry=_sheets.clear)
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
            buf = _render_spectrum(current, sc, pull_styles(), started_at)
            if buf:
                st.image(buf, use_container_width=True)
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

        fig, ax = plt.subplots(figsize=(9, 6.5))
        fig.patch.set_facecolor('#F9F9F9')
        ax.set_facecolor('#F9F9F9')

        ax.fill_between([0.5, 1.0], [0.5, 0.5], [1.0, 1.0], color='#E84040', alpha=0.05)
        ax.fill_between([0.0, 0.5], [0.5, 0.5], [1.0, 1.0], color='#F5A623', alpha=0.05)
        ax.fill_between([0.5, 1.0], [0.0, 0.0], [0.5, 0.5], color='#3EAA6D', alpha=0.05)
        ax.fill_between([0.0, 0.5], [0.0, 0.0], [0.5, 0.5], color='#4285C8', alpha=0.05)

        ax.axvline(0.5, color='#ddd', linewidth=1.2, zorder=1)
        ax.axhline(0.5, color='#ddd', linewidth=1.2, zorder=1)

        ax.text(0.03, 0.5, 'Blue',   va='center', ha='left',   fontsize=10, color='#4285C8', fontweight='bold', transform=ax.transAxes)
        ax.text(0.97, 0.5, 'Red',    va='center', ha='right',  fontsize=10, color='#E84040', fontweight='bold', transform=ax.transAxes)
        ax.text(0.5,  0.03, 'Green', va='bottom', ha='center', fontsize=10, color='#3EAA6D', fontweight='bold', transform=ax.transAxes)
        ax.text(0.5,  0.97, 'Yellow',va='top',    ha='center', fontsize=10, color='#F5A623', fontweight='bold', transform=ax.transAxes)

        for p in profiles:
            s  = p['scores']
            x  = max(0.05, min(0.95, (s['Red']    - s['Blue'])  / 200 + 0.5))
            y  = max(0.05, min(0.95, (s['Yellow'] - s['Green']) / 200 + 0.5))
            pc = HEX[p['primary']]
            ax.scatter(x, y, s=220, color=pc, zorder=3, alpha=0.92,
                       edgecolors='white', linewidths=1.5)
            ax.annotate(
                p['name'].split()[0], (x, y),
                textcoords='offset points', xytext=(0, 9),
                ha='center', fontsize=8, color='#333333',
            )

        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        buf = io.BytesIO()
        fig.tight_layout(pad=1.5)
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        st.image(buf, use_container_width=True)

        st.divider()

        with st.expander('Individual breakdown'):
            st.caption("Each person's full colour mix across all six scenarios.")
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
            buf = _render_spectrum(i, sc_item, df, started_at='')
            if buf:
                st.image(buf, use_container_width=True)
