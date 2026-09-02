"""Different Styles, Shared Direction — activity page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import io
from datetime import datetime
from utils import inject_styles, with_retry, _sheets

inject_styles()

# ── Constants ──────────────────────────────────────────────────────────────────

SHEET_ID   = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'
STYLES_TAB = 'Styles Submissions'

HEX = {
    'Red':    '#E84040',
    'Blue':   '#4285C8',
    'Yellow': '#F5A623',
    'Green':  '#3EAA6D',
}

TEXT = {
    'Red':    '#FFFFFF',
    'Blue':   '#FFFFFF',
    'Yellow': '#1A1A1A',
    'Green':  '#FFFFFF',
}

TEAM = sorted([
    'Alex Bartlett', 'Andrew Morton',
    'Angelique Simon', 'Bill Peng', 'Charli Every', 'Sayaka Smith',
    'Dylan Whitehouse', 'Ellissa Waters',
    "Ian O'Brien", 'James Fielding', 'John Krajewski',
    'Louise Heller', 'Misaki Kawashima', 'Rebekah Davidson', 'Robert Poulsen',
])

SCENARIOS = [
    dict(
        title='Speed versus certainty',
        prompt='A promising new opportunity has appeared, but some details are still unclear. What is your natural response?',
        left_label='Understand first', left_colour='Blue',
        right_label='Act now',         right_colour='Red',
    ),
    dict(
        title='Possibility versus stability',
        prompt='Leadership announces a significant change in direction. What do you notice first?',
        left_label='The impact',      left_colour='Green',
        right_label='The opportunity', right_colour='Yellow',
    ),
    dict(
        title='Directness versus diplomacy',
        prompt="You strongly disagree with a colleague's proposed approach. What are you more likely to do?",
        left_label='Protect the relationship', left_colour='Green',
        right_label='Say it directly',         right_colour='Red',
    ),
    dict(
        title='Structure versus flexibility',
        prompt='You are starting a large project with a deadline several months away. What feels more comfortable?',
        left_label='Create the plan', left_colour='Blue',
        right_label='Keep it open',   right_colour='Yellow',
    ),
    dict(
        title='Definition versus discovery',
        prompt='A project has stalled and needs a reset. What feels most natural?',
        left_label='Step back',      left_colour='Yellow',
        right_label='Define and move', right_colour='Red',
    ),
    dict(
        title='Logic versus consensus',
        prompt="A decision needs to be made that not everyone agrees on. What matters most to you in the process?",
        left_label='Sound reasoning', left_colour='Blue',
        right_label='Everyone heard', right_colour='Green',
    ),
]

# ── Sheet helpers ──────────────────────────────────────────────────────────────

def _ensure_styles_tab():
    svc  = _sheets()
    meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    existing = {s['properties']['title'] for s in meta.get('sheets', [])}
    if STYLES_TAB not in existing:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': [{'addSheet': {'properties': {'title': STYLES_TAB}}}]},
        ).execute()
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'{STYLES_TAB}'!A1:H1",
            valueInputOption='RAW',
            body={'values': [['Timestamp', 'Name', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6']]},
        ).execute()


@st.cache_data(ttl=15, show_spinner=False)
def pull_styles():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{STYLES_TAB}'!A:H",
        ).execute().get('values', [])
        if len(rows) < 2:
            return pd.DataFrame(columns=['Timestamp', 'Name', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6'])
        padded = [(r + [''] * 8)[:8] for r in rows[1:]]
        df = pd.DataFrame(padded, columns=['Timestamp', 'Name', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6'])
        for col in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(50).astype(int)
        df = df.sort_values('Timestamp').drop_duplicates('Name', keep='last')
        return df
    except Exception:
        return pd.DataFrame(columns=['Timestamp', 'Name', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6'])


def save_styles(name, scores):
    svc  = _sheets()
    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{STYLES_TAB}'!A:H",
    ).execute().get('values', [])
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 2 and row[1] == name:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'{STYLES_TAB}'!A{i}:H{i}",
                valueInputOption='RAW',
                body={'values': [[now, name] + scores]},
            ).execute()
            return
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID, range=f"'{STYLES_TAB}'!A:H",
        valueInputOption='RAW', insertDataOption='INSERT_ROWS',
        body={'values': [[now, name] + scores]},
    ).execute()


# ── Scoring ────────────────────────────────────────────────────────────────────

def compute_scores(row):
    """Returns dict of colour -> percentage (0-100), independently scored."""
    c = {k: 0 for k in HEX}
    for i, sc in enumerate(SCENARIOS):
        v = int(row.get(f'S{i + 1}', 50))
        c[sc['left_colour']]  += (100 - v)
        c[sc['right_colour']] += v
    return {k: round(v / 300 * 100) for k, v in c.items()}


def top_two(scores):
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[0][0], ranked[1][0]


# ── Colour card HTML ───────────────────────────────────────────────────────────

def colour_bar(scores):
    return ''.join(
        f'<div style="flex:{scores[c]};background:{HEX[c]};min-width:2px;"></div>'
        for c in ['Red', 'Blue', 'Yellow', 'Green']
    )


def card_html_large(name, scores):
    pri, sec = top_two(scores)
    pc, tc   = HEX[pri], TEXT[pri]
    return (
        f'<div style="background:{pc};border-radius:14px;padding:28px 24px 20px;'
        f'text-align:center;max-width:300px;margin:16px auto 8px;">'
        f'<div style="font-size:0.68em;font-weight:700;letter-spacing:0.16em;'
        f'text-transform:uppercase;color:{tc};opacity:0.7;margin-bottom:8px;">Your style</div>'
        f'<div style="font-size:2.4em;font-weight:800;color:{tc};line-height:1.1;margin-bottom:4px;">{pri}</div>'
        f'<div style="font-size:0.88em;color:{tc};opacity:0.75;margin-bottom:18px;">with {sec} tendencies</div>'
        f'<div style="display:flex;border-radius:4px;overflow:hidden;height:10px;">{colour_bar(scores)}</div>'
        f'<div style="display:flex;justify-content:space-between;margin-top:7px;'
        f'font-size:0.68em;color:{tc};opacity:0.65;">'
        + ''.join(f'<span>{c}<br>{scores[c]}%</span>' for c in ['Red', 'Blue', 'Yellow', 'Green'])
        + '</div></div>'
    )


def card_html_small(name, scores):
    pri, sec = top_two(scores)
    pc, tc   = HEX[pri], TEXT[pri]
    first    = name.split()[0]
    return (
        f'<div style="background:{pc};border-radius:10px;padding:16px 12px 12px;'
        f'text-align:center;margin-bottom:8px;">'
        f'<div style="font-weight:700;color:{tc};font-size:0.95em;line-height:1.3;margin-bottom:6px;">{first}</div>'
        f'<div style="font-size:1.5em;font-weight:800;color:{tc};line-height:1.1;">{pri}</div>'
        f'<div style="font-size:0.72em;color:{tc};opacity:0.75;margin-bottom:10px;">+ {sec}</div>'
        f'<div style="display:flex;border-radius:3px;overflow:hidden;height:6px;">{colour_bar(scores)}</div>'
        f'</div>'
    )


# ── Init ───────────────────────────────────────────────────────────────────────

if not st.session_state.get('_styles_tab_ensured'):
    try:
        with_retry(_ensure_styles_tab)
        st.session_state['_styles_tab_ensured'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue — some features may not save correctly. ({_e})')

# ── Page ───────────────────────────────────────────────────────────────────────

st.markdown('### Team Activity — Different Styles, Shared Direction')
st.markdown(
    'We all approach decisions, change and collaboration differently. '
    'This activity makes those differences visible and explores how they shape the way we work together.'
)

tab_submit, tab_team = st.tabs(['🧭 Submit your results', '🎨 Team map'])

# ── Submit tab ─────────────────────────────────────────────────────────────────

with tab_submit:

    name = st.selectbox('Your name', ['Select your name...'] + TEAM, key='styles_name')

    if name and name != 'Select your name...':
        df_all = pull_styles()
        already = not df_all.empty and name in df_all['Name'].values

        if already and not st.session_state.get('styles_resubmit'):
            row    = df_all[df_all['Name'] == name].iloc[0]
            scores = compute_scores(row)
            st.markdown(card_html_large(name, scores), unsafe_allow_html=True)
            st.caption("You've already submitted. Head to the Team map to see the full picture.")
            if st.button('Change my answers', key='styles_change'):
                st.session_state['styles_resubmit'] = True
                st.rerun()

        else:
            st.caption(
                'Move each slider to where your natural preference sits. '
                'Choose what feels most instinctive, not what sounds most professional.'
            )
            st.markdown('')

            slider_vals = []
            for i, sc in enumerate(SCENARIOS):
                lc = HEX[sc['left_colour']]
                rc = HEX[sc['right_colour']]

                st.markdown(
                    f'<div style="margin:28px 0 8px;">'
                    f'<div style="font-size:0.68em;font-weight:700;letter-spacing:0.12em;'
                    f'text-transform:uppercase;color:#bbb;margin-bottom:3px;">'
                    f'Scenario {i + 1} of {len(SCENARIOS)}</div>'
                    f'<div style="font-size:1.05em;font-weight:700;color:#111;margin-bottom:4px;">{sc["title"]}</div>'
                    f'<div style="font-size:0.88em;color:#666;line-height:1.55;">{sc["prompt"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                c_left, c_mid, c_right = st.columns([2, 4, 2])
                with c_left:
                    st.markdown(
                        f'<div style="text-align:right;padding-top:8px;">'
                        f'<div style="font-weight:700;color:{lc};font-size:0.88em;">{sc["left_label"]}</div>'
                        f'<div style="font-size:0.73em;color:{lc};opacity:0.75;">{sc["left_colour"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with c_mid:
                    val = st.slider(
                        f'Scenario {i + 1}',
                        min_value=0, max_value=100, value=50,
                        label_visibility='collapsed',
                        key=f'styles_s{i + 1}',
                    )
                with c_right:
                    st.markdown(
                        f'<div style="text-align:left;padding-top:8px;">'
                        f'<div style="font-weight:700;color:{rc};font-size:0.88em;">{sc["right_label"]}</div>'
                        f'<div style="font-size:0.73em;color:{rc};opacity:0.75;">{sc["right_colour"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                slider_vals.append(val)

            st.markdown('')
            if st.button('Submit', type='primary', use_container_width=True, key='styles_submit'):
                try:
                    save_styles(name, slider_vals)
                    st.session_state.pop('styles_resubmit', None)
                    st.cache_data.clear()
                    scores = compute_scores({f'S{i + 1}': v for i, v in enumerate(slider_vals)})
                    st.markdown(card_html_large(name, scores), unsafe_allow_html=True)
                    st.toast('Submitted! Head to the Team map to see the full picture.', icon='✅')
                    st.rerun()
                except Exception as _e:
                    st.error(f'Could not save — please try again. ({_e})')

# ── Team map tab ───────────────────────────────────────────────────────────────

with tab_team:

    c_ref, _ = st.columns([1, 8])
    with c_ref:
        if st.button('Refresh', key='styles_refresh'):
            st.cache_data.clear()
            st.rerun()

    df = pull_styles()

    if df.empty:
        st.info('No results yet. Ask the team to submit their responses in the Submit tab.')
    else:
        profiles = []
        for _, row in df.iterrows():
            sc  = compute_scores(row)
            pri, sec = top_two(sc)
            profiles.append({'name': row['Name'], 'scores': sc, 'primary': pri, 'secondary': sec})

        # ── Colour cards grid ──────────────────────────────────────────────────

        submitted_count = len(profiles)
        total_count     = len(TEAM)
        st.markdown(
            f'<div style="margin-bottom:16px;">'
            f'<span style="font-size:1.1em;font-weight:700;">The team</span>'
            f'&nbsp;&nbsp;<span style="font-size:0.8em;color:#999;font-weight:400;">'
            f'{submitted_count} of {total_count} submitted</span></div>',
            unsafe_allow_html=True,
        )

        n_cols = 4
        for i in range(0, len(profiles), n_cols):
            batch = profiles[i:i + n_cols]
            cols  = st.columns(n_cols)
            for col, p in zip(cols, batch):
                with col:
                    st.markdown(card_html_small(p['name'], p['scores']), unsafe_allow_html=True)

        st.divider()

        # ── Bubble chart ───────────────────────────────────────────────────────

        st.markdown('#### Team map')
        st.caption(
            'X axis: Blue (analytical) to Red (decisive). '
            'Y axis: Green (people-first) to Yellow (possibility-first).'
        )

        fig, ax = plt.subplots(figsize=(9, 6.5))
        fig.patch.set_facecolor('#F9F9F9')
        ax.set_facecolor('#F9F9F9')

        # Quadrant shading
        ax.fill_between([0.5, 1.0], [0.5, 0.5], [1.0, 1.0], color='#E84040', alpha=0.05)
        ax.fill_between([0.0, 0.5], [0.5, 0.5], [1.0, 1.0], color='#F5A623', alpha=0.05)
        ax.fill_between([0.5, 1.0], [0.0, 0.0], [0.5, 0.5], color='#3EAA6D', alpha=0.05)
        ax.fill_between([0.0, 0.5], [0.0, 0.0], [0.5, 0.5], color='#4285C8', alpha=0.05)

        ax.axvline(0.5, color='#ddd', linewidth=1.2, zorder=1)
        ax.axhline(0.5, color='#ddd', linewidth=1.2, zorder=1)

        # Axis colour labels
        ax.text(0.03, 0.5, 'Blue',   va='center', ha='left',   fontsize=10, color='#4285C8', fontweight='bold', transform=ax.transAxes)
        ax.text(0.97, 0.5, 'Red',    va='center', ha='right',  fontsize=10, color='#E84040', fontweight='bold', transform=ax.transAxes)
        ax.text(0.5,  0.03, 'Green', va='bottom', ha='center', fontsize=10, color='#3EAA6D', fontweight='bold', transform=ax.transAxes)
        ax.text(0.5,  0.97, 'Yellow',va='top',    ha='center', fontsize=10, color='#F5A623', fontweight='bold', transform=ax.transAxes)

        for p in profiles:
            s  = p['scores']
            # Scores are 0-100 percentages; differential / 200 maps to -0.5 to +0.5, then + 0.5 → 0 to 1
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

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
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

        # ── Individual breakdown ───────────────────────────────────────────────

        with st.expander('Individual breakdown'):
            st.caption("Each person's full colour mix across all six scenarios.")
            for p in sorted(profiles, key=lambda x: (x['primary'], x['secondary'])):
                bar = ''.join(
                    f'<div style="flex:{p["scores"][c]};background:{HEX[c]};min-width:2px;"></div>'
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
