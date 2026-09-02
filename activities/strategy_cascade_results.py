"""Strategy Cascade — team results (public view)."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL
from strategy_cascade_shared import GOALS, FUNCTIONS, pull_commitments, pull_confidence, pull_cascade_content

inject_styles()

st.markdown('### Strategy Cascade — Results')

@st.fragment(run_every=30)
def _results():
    df_comm = pull_commitments()
    df_conf = pull_confidence()

    goals_live, fn_live = pull_cascade_content()

    if df_comm.empty and df_conf.empty:
        st.markdown(
            '<div style="background:#F5F5F5;border-radius:10px;padding:28px;'
            'text-align:center;color:#AAAAAA;font-size:0.9em;">Results will appear here once the team has submitted.</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Goal confidence ────────────────────────────────────────────────────────

    if not df_conf.empty:
        st.markdown(
            '<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
            'color:#888;margin-bottom:12px;">GOAL CONFIDENCE</div>',
            unsafe_allow_html=True,
        )
        for g in goals_live:
            conf_col = f'{g["id"]}_Confidence'
            if conf_col not in df_conf.columns:
                continue
            nums = []
            for v in df_conf[conf_col].tolist():
                try: nums.append(int(v))
                except (TypeError, ValueError): pass
            if not nums:
                continue

            avg = sum(nums) / len(nums)
            if avg >= 4:
                bc, bg, label = '#3EAA6D', '#E8F5EE', f'{avg:.1f} — High'
            elif avg >= 3:
                bc, bg, label = '#B7770D', '#FEF5E7', f'{avg:.1f} — Moderate'
            else:
                bc, bg, label = '#C0392B', '#FDECEA', f'{avg:.1f} — Low'

            bar_pct = avg / 5 * 100

            st.markdown(
                f'<div style="border-left:4px solid {PURPLE};padding:12px 16px;'
                f'background:#F8F8F8;border-radius:0 8px 8px 0;margin-bottom:10px;">'
                f'<div style="font-weight:700;font-size:0.9em;color:{PURPLE};margin-bottom:8px;">{g["title"]}</div>'
                f'<div style="display:flex;align-items:center;gap:12px;">'
                f'<div style="flex:1;background:#E0E0E0;border-radius:4px;height:10px;">'
                f'<div style="width:{bar_pct:.0f}%;background:{bc};border-radius:4px;height:10px;"></div>'
                f'</div>'
                f'<span style="background:{bg};color:{bc};font-weight:700;font-size:0.78em;'
                f'padding:3px 12px;border-radius:20px;white-space:nowrap;">{label}</span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Personal One Things by function ───────────────────────────────────────

    if not df_comm.empty:
        st.markdown(
            '<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
            'color:#888;margin:20px 0 12px;">PERSONAL ONE THINGS</div>',
            unsafe_allow_html=True,
        )
        for fn in fn_live:
            fn_rows = df_comm[df_comm['Function'] == fn]
            if fn_rows.empty:
                continue
            items = ''.join(
                f'<div style="padding:7px 0;border-bottom:1px solid #EEF5F5;font-size:0.84em;line-height:1.5;">'
                f'<strong style="color:#444;display:inline-block;min-width:72px;">{row["Name"].split()[0]}</strong>'
                f'<span style="color:#555;">{row["Commitment"]}</span>'
                f'</div>'
                for _, row in fn_rows.iterrows()
            )
            st.markdown(
                f'<div style="border-left:4px solid {TEAL};background:#F8F8F8;'
                f'border-radius:0 8px 8px 0;padding:12px 14px;margin-bottom:10px;">'
                f'<div style="font-size:0.72em;font-weight:700;color:{TEAL};'
                f'letter-spacing:1px;margin-bottom:8px;">{fn.upper()}</div>'
                f'{items}'
                f'</div>',
                unsafe_allow_html=True,
            )

_results()
