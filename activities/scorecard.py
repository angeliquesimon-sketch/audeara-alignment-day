"""FY27 Scorecard — live synthesis of strategic choices and team commitments."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, with_retry, _clear_sheets
from strategy_cascade_shared import (
    pull_cascade_contributions, get_live_choices, DEPARTMENTS,
)
from scorecard_shared import _ensure_scorecard_tab, pull_scorecard_entries

inject_styles()

WINE   = '#50144B'
FOREST = '#005E63'

CHOICE_COLOURS = [WINE, FOREST, '#781E73', '#005E63', WINE, FOREST, '#781E73']

# ── Tab setup ──────────────────────────────────────────────────────────────────

if not st.session_state.get('_sc_tab_ready'):
    try:
        with_retry(_ensure_scorecard_tab, on_retry=_clear_sheets)
        st.session_state['_sc_tab_ready'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue. ({_e})')

# ── Header ─────────────────────────────────────────────────────────────────────

st.markdown(
    f'<div style="font-weight:700;font-size:1.3em;color:{WINE};margin-bottom:4px;">FY27 Scorecard</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div style="color:#666;font-size:0.88em;margin-bottom:24px;">'
    'What we committed to and how we will measure it. Updated live.</div>',
    unsafe_allow_html=True,
)

# ── Helper: latest cascade contribution per dept ───────────────────────────────

def _dept_contribs(contribs_df, choice_id: str) -> dict:
    if contribs_df.empty:
        return {}
    sub = contribs_df[
        (contribs_df['ChoiceID'] == choice_id) &
        (~contribs_df['Status'].isin(['deleted', 'opted_out']))
    ].sort_values('Timestamp', ascending=False)
    result = {}
    for _, row in sub.iterrows():
        if row['Department'] not in result and row['Text'].strip():
            result[row['Department']] = row['Text'].strip()
    return result

# ── Live scorecard ─────────────────────────────────────────────────────────────

@st.fragment(run_every=20)
def _scorecard():
    choices     = get_live_choices()
    entries_df  = pull_scorecard_entries()
    contribs_df = pull_cascade_contributions()

    any_entries = not entries_df.empty

    if not any_entries:
        st.markdown(
            f'<div style="background:#F7F0F7;border-radius:10px;padding:24px;'
            f'text-align:center;color:#AAAAAA;font-size:0.9em;">'
            f'Scorecard entries will appear here once the facilitator begins capturing '
            f'metrics from the Strategy Cascade.</div>',
            unsafe_allow_html=True,
        )

    for idx, choice in enumerate(choices):
        cid          = choice['id']
        colour       = CHOICE_COLOURS[idx % len(CHOICE_COLOURS)]
        dept_inputs  = _dept_contribs(contribs_df, cid)
        choice_entries = (
            entries_df[entries_df['ChoiceID'] == cid]
            if not entries_df.empty
            else entries_df
        )

        # Build rows: depts that have a cascade contribution, in dept order
        rows = []
        for dept in DEPARTMENTS:
            cascade_text = dept_inputs.get(dept, '')
            if not cascade_text:
                continue
            entry = choice_entries[choice_entries['Department'] == dept]
            if not entry.empty:
                row = entry.iloc[0]
                rows.append({
                    'dept':   dept,
                    'cascade': cascade_text,
                    'metric': row['Metric'],
                    'target': row['Target'],
                    'owner':  row['Owner'],
                    'saved':  True,
                })
            else:
                rows.append({
                    'dept':   dept,
                    'cascade': cascade_text,
                    'metric': '',
                    'target': '',
                    'owner':  '',
                    'saved':  False,
                })

        if not rows:
            # No cascade contributions yet — muted card
            st.markdown(
                f'<div style="border-left:4px solid #DDDDDD;background:#FAFAFA;'
                f'border-radius:0 10px 10px 0;padding:14px 16px;margin-bottom:10px;">'
                f'<div style="font-size:0.68em;color:#CCCCCC;font-weight:700;'
                f'letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">'
                f'Choice {choice["number"]}</div>'
                f'<div style="font-weight:700;font-size:0.92em;color:#CCCCCC;">{choice["title"]}</div>'
                f'<div style="font-size:0.78em;color:#CCCCCC;margin-top:6px;">No cascade inputs yet</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            continue

        n_saved   = sum(1 for r in rows if r['saved'])
        n_total   = len(rows)
        all_done  = n_saved == n_total
        some_done = n_saved > 0

        status_colour = '#3EAA6D' if all_done else '#F5A623' if some_done else '#AAAAAA'
        status_label  = (
            f'All {n_total} entries complete' if all_done
            else f'{n_saved} of {n_total} entries saved' if some_done
            else 'Entries pending'
        )

        # Choice header
        st.markdown(
            f'<div style="border-left:4px solid {colour};background:#FFFFFF;'
            f'border-radius:0 10px 10px 0;padding:14px 16px;margin-bottom:2px;'
            f'box-shadow:0 1px 4px rgba(0,0,0,0.05);">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
            f'<div>'
            f'<div style="font-size:0.68em;color:{colour};font-weight:700;'
            f'letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">'
            f'Choice {choice["number"]}</div>'
            f'<div style="font-weight:700;font-size:0.95em;color:#1a1a1a;">{choice["title"]}</div>'
            f'</div>'
            f'<div style="font-size:0.72em;color:{status_colour};font-weight:600;">'
            f'{status_label}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # Department rows
        for row in rows:
            dept     = row['dept']
            saved    = row['saved']
            bc       = '#EEEEEE'
            text_col = '#1a1a1a' if saved else '#AAAAAA'

            # Cascade reference text
            cascade_html = (
                f'<div style="font-size:0.75em;color:#888;margin-bottom:6px;'
                f'padding:6px 10px;background:#F7F7F7;border-radius:4px;line-height:1.5;">'
                f'<em>{row["cascade"]}</em></div>'
            )

            if saved:
                metric_html = (
                    f'<div style="display:flex;gap:24px;flex-wrap:wrap;">'
                    + (
                        f'<div><div style="font-size:0.65em;color:#AAAAAA;font-weight:700;'
                        f'text-transform:uppercase;letter-spacing:0.5px;">Metric</div>'
                        f'<div style="font-size:0.85em;color:{text_col};font-weight:600;">'
                        f'{row["metric"] or "—"}</div></div>'
                    )
                    + (
                        f'<div><div style="font-size:0.65em;color:#AAAAAA;font-weight:700;'
                        f'text-transform:uppercase;letter-spacing:0.5px;">Target</div>'
                        f'<div style="font-size:0.85em;color:{text_col};font-weight:600;">'
                        f'{row["target"] or "—"}</div></div>'
                    )
                    + (
                        f'<div><div style="font-size:0.65em;color:#AAAAAA;font-weight:700;'
                        f'text-transform:uppercase;letter-spacing:0.5px;">Owner</div>'
                        f'<div style="font-size:0.85em;color:{text_col};font-weight:600;">'
                        f'{row["owner"] or "—"}</div></div>'
                    )
                    + f'</div>'
                )
            else:
                metric_html = (
                    f'<div style="font-size:0.78em;color:#CCCCCC;">Metric / Target / Owner — pending</div>'
                )

            st.markdown(
                f'<div style="border-left:2px solid {bc};padding:10px 14px 10px 16px;'
                f'margin-left:4px;margin-bottom:2px;">'
                f'<div style="font-size:0.72em;font-weight:700;color:{colour};'
                f'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">{dept}</div>'
                f'{cascade_html}'
                f'{metric_html}'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div style="margin-bottom:16px;"></div>', unsafe_allow_html=True)

_scorecard()
