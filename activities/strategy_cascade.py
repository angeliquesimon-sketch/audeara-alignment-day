"""Strategy Cascade — participant page (Goals / Contributions / Confidence / Results)."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL
from strategy_cascade_shared import (
    GOALS,
    _ensure_cascade_tabs,
    pull_cascade_session, pull_cascade_context, pull_cascade_content,
    pull_team_contributions, save_team_contribution,
    pull_confidence, save_confidence,
)
from styles_shared import TEAM

inject_styles()

st.markdown('### Strategy Cascade')

# ── Name selector ──────────────────────────────────────────────────────────────

name = st.selectbox('Your name', [''] + TEAM, key='cascade_name')

if not name:
    st.caption('Select your name above to participate.')
    st.stop()

# ── Tabs ───────────────────────────────────────────────────────────────────────

tab_goals, tab_contrib, tab_conf, tab_results = st.tabs([
    '🎯 FY27 Goals',
    '🤝 Team Contributions',
    '💬 Individual Confidence',
    '📊 Results',
])

# ── Stage gate fragment ────────────────────────────────────────────────────────

@st.fragment(run_every=5)
def _stage_gate():
    pull_cascade_session.clear()
    _new = pull_cascade_session().get('stage', 'hidden')
    if _new != st.session_state.get('_casc_stage_last'):
        st.session_state['_casc_stage_last'] = _new
        st.rerun()

_stage_gate()

session = pull_cascade_session()
stage   = session.get('stage', 'hidden')

# ── Shared helpers ─────────────────────────────────────────────────────────────

def _waiting(msg='This will open shortly.'):
    st.markdown(
        f'<div style="background:#F5F5F5;border-radius:10px;padding:28px;'
        f'text-align:center;color:#AAAAAA;font-size:0.9em;">⏳  {msg}</div>',
        unsafe_allow_html=True,
    )

def _mission_vision_banner(mission_top, vision):
    if not mission_top and not vision:
        return
    parts = []
    if mission_top:
        m = (f'We help <strong>{mission_top.get("Who","…")}</strong> '
             f'do <strong>{mission_top.get("What","…")}</strong> '
             f'by <strong>{mission_top.get("How","…")}</strong>, '
             f'so they can <strong>{mission_top.get("Makes Possible","…")}</strong>.')
        parts.append(
            f'<div style="flex:1;background:#781E73;border-radius:10px;padding:14px 18px;">'
            f'<div style="font-size:0.6em;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,0.7);margin-bottom:5px;">MISSION</div>'
            f'<div style="font-size:0.82em;color:white;line-height:1.6;">{m}</div></div>'
        )
    if vision:
        parts.append(
            f'<div style="flex:1;background:#188383;border-radius:10px;padding:14px 18px;">'
            f'<div style="font-size:0.6em;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,0.7);margin-bottom:5px;">VISION</div>'
            f'<div style="font-size:0.82em;color:white;line-height:1.6;font-style:italic;">"{vision}"</div></div>'
        )
    if parts:
        st.markdown(
            f'<div style="display:flex;gap:12px;margin-bottom:16px;">{"".join(parts)}</div>',
            unsafe_allow_html=True,
        )

# ── Tab 1: FY27 Goals ─────────────────────────────────────────────────────────

with tab_goals:
    if stage == 'hidden':
        _waiting('James is about to walk through the FY27 goals. Stay on this page.')
    else:
        mission_top, vision = pull_cascade_context()
        goals_live, fn_live = pull_cascade_content()

        _mission_vision_banner(mission_top, vision)

        st.markdown(
            f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
            f'color:#888;margin-bottom:12px;">FY27 GOALS</div>',
            unsafe_allow_html=True,
        )
        for i, g in enumerate(goals_live):
            bc = ['#781E73', '#188383', '#50144B'][i % 3]
            st.markdown(
                f'<div style="border-left:4px solid {bc};background:#F8F8F8;'
                f'border-radius:0 8px 8px 0;padding:14px 18px;margin-bottom:10px;">'
                f'<div style="font-weight:700;font-size:0.92em;color:{bc};">{g["title"]}</div>'
                f'<div style="font-size:0.8em;color:#666;margin-top:4px;line-height:1.5;">{g["description"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ── Tab 2: Team Contributions ─────────────────────────────────────────────────

with tab_contrib:
    if stage in ('hidden', 'goals'):
        _waiting()
    else:
        goals_live, fn_live = pull_cascade_content()

        st.markdown(
            f'<div class="activity-card">'
            f'For each of the three FY27 goals, write one sentence about how your function contributes to it. '
            f'Be specific — what does your team actually do that moves this goal forward?'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown('')

        @st.fragment(run_every=15)
        def _contrib_form():
            df_contrib = pull_team_contributions()
            has_submitted = (
                not df_contrib.empty and name in df_contrib['Name'].values
            )

            if has_submitted and not st.session_state.get(f'casc_contrib_edit_{name}'):
                my_row = df_contrib[df_contrib['Name'] == name].iloc[0]
                st.markdown(
                    f'<div style="border-left:4px solid #3EAA6D;background:#E8F5EE;'
                    f'border-radius:0 8px 8px 0;padding:14px 16px;">'
                    f'<div style="font-weight:700;color:#2D7D4F;margin-bottom:10px;">✅  Submitted</div>',
                    unsafe_allow_html=True,
                )
                for g in goals_live:
                    val = my_row.get(g['id'], '')
                    st.markdown(
                        f'<div style="font-size:0.84em;color:#444;margin-bottom:6px;">'
                        f'<strong>{g["title"]}:</strong> {val}</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown('</div>', unsafe_allow_html=True)
                if st.button('Edit my contributions', key=f'casc_contrib_edit_btn_{name}'):
                    st.session_state[f'casc_contrib_edit_{name}'] = True
                    st.rerun()
                return

            # Determine function from DEPARTMENT_MAP
            from one_thing_shared import DEPARTMENT_MAP
            my_depts = DEPARTMENT_MAP.get(name, [])
            if len(my_depts) == 1:
                function = my_depts[0]
                st.markdown(
                    f'<div style="font-size:0.8em;color:#888;margin-bottom:12px;">'
                    f'Function: <strong style="color:#444;">{function}</strong></div>',
                    unsafe_allow_html=True,
                )
            else:
                function = st.selectbox(
                    'Your function',
                    my_depts,
                    key=f'casc_contrib_fn_{name}',
                )

            contrib = {}
            for g in goals_live:
                default = ''
                if has_submitted:
                    row = df_contrib[df_contrib['Name'] == name].iloc[0]
                    default = row.get(g['id'], '')
                bc = ['#781E73', '#188383', '#50144B'][goals_live.index(g) % 3]
                st.markdown(
                    f'<div style="border-left:3px solid {bc};padding:2px 0 2px 10px;margin-bottom:4px;">'
                    f'<div style="font-weight:700;font-size:0.88em;color:{bc};">{g["title"]}</div>'
                    f'<div style="font-size:0.76em;color:#888;">{g["description"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                contrib[g['id']] = st.text_input(
                    f'How does {function} contribute to this goal?',
                    value=default,
                    placeholder='One sentence…',
                    key=f'casc_contrib_{name}_{g["id"]}',
                    label_visibility='collapsed',
                )
                st.markdown('')

            if st.button('Submit contributions', type='primary', key=f'casc_contrib_submit_{name}', use_container_width=True):
                if not all(contrib[g['id']].strip() for g in goals_live):
                    st.warning('Please add a sentence for each goal before submitting.')
                    return
                try:
                    save_team_contribution(name, function, {k: v.strip() for k, v in contrib.items()})
                    pull_team_contributions.clear()
                    st.session_state[f'casc_contrib_edit_{name}'] = False
                    st.toast('Contributions saved ✓', icon='✅')
                    st.rerun()
                except Exception as _e:
                    st.error(f'Could not save. ({_e})')

        _contrib_form()

# ── Tab 3: Individual Confidence ──────────────────────────────────────────────

with tab_conf:
    if stage in ('hidden', 'goals', 'contributions'):
        _waiting()
    else:
        goals_live, _ = pull_cascade_content()

        st.markdown(
            f'<div class="activity-card">'
            f'This is anonymous — your name is not attached to these responses. '
            f'Rate how confident you feel about each goal, and share how you see yourself contributing.'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown('')

        if st.session_state.get('casc_conf_submitted'):
            st.success('Thank you — your response has been recorded anonymously.')
            st.caption('This form cannot be edited once submitted.')
        else:
            conf   = {}
            contrib = {}

            for i, g in enumerate(goals_live):
                bc = ['#781E73', '#188383', '#50144B'][i % 3]
                st.markdown(
                    f'<div style="border-left:4px solid {bc};padding:2px 0 2px 12px;margin-bottom:8px;">'
                    f'<div style="font-weight:700;font-size:0.9em;color:{bc};">{g["title"]}</div>'
                    f'<div style="font-size:0.78em;color:#666;">{g["description"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                conf[g['id']] = st.select_slider(
                    'Team confidence',
                    options=[1, 2, 3, 4, 5],
                    value=3,
                    format_func=lambda x: {
                        1: '1 — Low', 2: '2', 3: '3 — Moderate', 4: '4', 5: '5 — High',
                    }[x],
                    key=f'casc_conf_{g["id"]}',
                )
                contrib[g['id']] = st.text_input(
                    'How do I see myself contributing to this?',
                    placeholder='One sentence (optional)',
                    key=f'casc_contrib_anon_{g["id"]}',
                )
                st.markdown('')

            st.markdown('')
            if st.button('Submit anonymously', type='primary', key='casc_conf_submit', use_container_width=True):
                try:
                    save_confidence(
                        {g['id']: conf[g['id']] for g in goals_live},
                        {g['id']: contrib[g['id']].strip() for g in goals_live},
                    )
                    st.session_state['casc_conf_submitted'] = True
                    pull_confidence.clear()
                    st.rerun()
                except Exception as _e:
                    st.error(f'Could not save. ({_e})')

# ── Tab 4: Results ────────────────────────────────────────────────────────────

with tab_results:
    @st.fragment(run_every=30)
    def _results():
        df_conf   = pull_confidence()
        df_contrib = pull_team_contributions()
        goals_live, fn_live = pull_cascade_content()

        if df_conf.empty and df_contrib.empty:
            st.markdown(
                '<div style="background:#F5F5F5;border-radius:10px;padding:28px;'
                'text-align:center;color:#AAAAAA;font-size:0.9em;">'
                'Results will appear here as the team responds.</div>',
                unsafe_allow_html=True,
            )
            return

        # Aggregate confidence
        if not df_conf.empty:
            n = len(df_conf)
            st.markdown(
                f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
                f'color:#888;margin-bottom:12px;">GOAL CONFIDENCE — {n} anonymous response{"s" if n != 1 else ""}</div>',
                unsafe_allow_html=True,
            )
            for i, g in enumerate(goals_live):
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
                goal_bc = ['#781E73', '#188383', '#50144B'][i % 3]
                st.markdown(
                    f'<div style="border-left:4px solid {goal_bc};padding:12px 16px;'
                    f'background:#F8F8F8;border-radius:0 8px 8px 0;margin-bottom:10px;">'
                    f'<div style="font-weight:700;font-size:0.9em;color:{goal_bc};margin-bottom:8px;">{g["title"]}</div>'
                    f'<div style="display:flex;align-items:center;gap:12px;">'
                    f'<div style="flex:1;background:#E0E0E0;border-radius:4px;height:10px;">'
                    f'<div style="width:{avg/5*100:.0f}%;background:{bc};border-radius:4px;height:10px;"></div>'
                    f'</div>'
                    f'<span style="background:{bg};color:{bc};font-weight:700;font-size:0.78em;'
                    f'padding:3px 12px;border-radius:20px;white-space:nowrap;">{label}</span>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

        # Team contributions by function
        if not df_contrib.empty:
            st.markdown(
                f'<div style="font-size:0.72em;font-weight:700;letter-spacing:2px;'
                f'color:#888;margin:20px 0 12px;">TEAM CONTRIBUTIONS</div>',
                unsafe_allow_html=True,
            )
            from one_thing_shared import DEPARTMENTS
            for dept in DEPARTMENTS:
                dept_rows = df_contrib[df_contrib['Function'] == dept]
                if dept_rows.empty:
                    continue
                st.markdown(
                    f'<div style="border-left:4px solid {TEAL};background:#F8F8F8;'
                    f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:10px;">'
                    f'<div style="font-size:0.7em;font-weight:700;color:{TEAL};letter-spacing:1px;margin-bottom:8px;">{dept.upper()}</div>',
                    unsafe_allow_html=True,
                )
                for _, row in dept_rows.iterrows():
                    for g in goals_live:
                        val = row.get(g['id'], '')
                        if val:
                            st.markdown(
                                f'<div style="font-size:0.8em;color:#666;padding:3px 0;">'
                                f'<strong style="color:#444;">{g["title"]}:</strong> {val}</div>',
                                unsafe_allow_html=True,
                            )
                st.markdown('</div>', unsafe_allow_html=True)

    _results()
