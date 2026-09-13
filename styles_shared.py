"""Shared constants and helpers for the Different Styles activity."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
from datetime import datetime
from utils import _sheets, _clear_sheets, with_retry

SHEET_ID       = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'
STYLES_TAB     = 'Styles Submissions'
SESSION_TAB    = 'Styles Session'
SUMMARIES_TAB  = 'Styles Summaries'
RESPONSES_TAB           = 'Styles Responses'
PLAY_NICE_SESSION_TAB   = 'Play Nice Session'
PLAY_NICE_RESPONSES_TAB = 'Play Nice Responses'

PLAY_NICE_SITUATIONS = [
    dict(
        title='Getting alignment',
        prompt="You're trying to get alignment on a decision that not everyone agrees on. "
               "What would you need from the other person to feel like it was resolved well?",
    ),
    dict(
        title='Working style clash',
        prompt="Someone's working style is clashing with yours and it's affecting how you get "
               "things done. What would you need from the other person to feel like it was resolved well?",
    ),
    dict(
        title='After a disagreement',
        prompt="You need to bring someone back on board after a disagreement. "
               "What would you need from the other person to feel like it was resolved well?",
    ),
]

PLAY_NICE_CARDS = {
    0: {
        'Red': (
            "Lead with the outcome, not the process. Reds align around results, so frame the "
            "decision in terms of what it achieves rather than how you got there. Be direct about "
            "where you agree and where you don't. Don't bring too many options. If you need them "
            "to move off their position, give them a reason that matters to them — speed, impact, "
            "or a better result. They respond to logic paired with momentum."
        ),
        'Blue': (
            "Don't try to rush them to a conclusion. Blues need to feel they've had time to think "
            "the problem through before they can commit. Share your reasoning in advance so the "
            "conversation can focus on the decision rather than the information. Ask what concerns "
            "they still have and take those seriously. A Blue who feels heard on the substance will "
            "align. A Blue who feels pushed past their questions will hold out."
        ),
        'Yellow': (
            "Bring energy to it. Yellows align when they feel excited about where things are going, "
            "not when they're being managed toward a predetermined answer. Frame the decision as an "
            "opportunity. Let them contribute an idea, even a small one, so they feel ownership of "
            "the outcome. If they feel the conclusion was partly theirs, they'll champion it."
        ),
        'Green': (
            "Create safety before asking for agreement. Greens won't voice their reservations in a "
            "group, so if you push for a public commitment too early you'll get a yes that isn't "
            "real. Check in privately. Ask how they feel about it, not just what they think. Show "
            "that their concerns have been considered. Once they feel the relationship is intact and "
            "the people around them are okay, they'll align genuinely."
        ),
    },
    1: {
        'Red': (
            "Be direct and specific. Reds don't respond well to general feedback or long preambles. "
            "Name the behaviour, name the impact, and propose a concrete change. Keep it short. "
            "Avoid framing it as personal criticism. The most effective approach is to treat it as "
            "a practical problem to solve together: \"This is what's happening, here's what I need, "
            "how do we fix it?\" They'll respect the directness and move quickly."
        ),
        'Blue': (
            "Blue won't respond well to an emotional or vague complaint. Prepare for the "
            "conversation: be specific about what the clash looks like, why it's creating a problem, "
            "and what a better working arrangement would involve. Give them time to respond — they'll "
            "want to think before they answer. Avoid pressure for an immediate resolution. The more "
            "structured and reasoned your approach, the more effective it will be."
        ),
        'Yellow': (
            "Keep it warm. Yellows are sensitive to criticism and can internalise it as personal "
            "rejection. Focus on the situation, not the person. Use humour if the relationship "
            "allows it. Frame what you need as a way of helping things flow better for both of you, "
            "not as a complaint. Give them a role in designing the solution — they'll commit to a "
            "change they helped create."
        ),
        'Green': (
            "Be gentle and specific. Greens will absorb a clash silently rather than raise it, so "
            "even getting to this conversation is progress. Choose a calm, private moment. Reassure "
            "them that the relationship is fine and that you're raising it because you want things "
            "to work well. Avoid any language that sounds like blame. Ask what's been feeling hard "
            "for them too — there's often something on their side they haven't said."
        ),
    },
    2: {
        'Red': (
            "Address the substance, not just the temperature. Reds may appear to have moved on but "
            "the underlying issue often hasn't been resolved. Go to them directly. Keep it brief and "
            "practical: name what happened, say what you'd do differently, and ask if there's "
            "anything they need going forward. Don't over-process the emotional dimension. Resolution "
            "for a Red means the issue is closed and you're both moving forward."
        ),
        'Blue': (
            "Give them time, then create a structured moment to revisit it. Blues will have replayed "
            "the disagreement carefully and will want to understand what went wrong before they can "
            "move on. Don't try to resolve it in passing. Set aside time, let them work through "
            "their thinking, and engage with the substance of what they raise. A Blue who feels the "
            "issue has been properly examined will reconnect fully. One who feels it was brushed "
            "past will stay guarded."
        ),
        'Yellow': (
            "Start with the relationship, not the issue. Yellows take disagreements personally and "
            "need to feel things are okay between you before they can engage with the substance. A "
            "warm, genuine reach-out — even a brief one — opens the door. Don't wait for them to "
            "come to you. Once they feel safe they'll reconnect quickly. Keep the follow-up light "
            "on analysis and warm on acknowledgement."
        ),
        'Green': (
            "Go to them. Greens won't raise it and won't come to you, but they'll be sitting with "
            "it. Choose a quiet, private moment. Keep your tone calm and unhurried. Ask how they're "
            "feeling before you explain your own position. Show that you value the relationship "
            "independent of the outcome of the disagreement. Greens reconnect through feeling seen "
            "and valued as a person, not through reaching logical closure on the argument."
        ),
    },
}

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
    'Angelique Simon', 'Bill Peng', 'Bonar Dickson', 'Charli Every', 'Sayaka Smith',
    'Dylan Whitehouse', 'Ellissa Waters',
    "Ian O'Brien", 'James Fielding', 'John Krajewski',
    'Louise Heller', 'Misaki Kawashima', 'Rebekah Davidson', 'Robert Poulsen',
])

COLOUR_DESCRIPTORS = {
    'Red':    'Acts fast and drives for results. Values momentum, directness, and decisive action.',
    'Blue':   'Thinks it through. Values rigour, process, and getting it right before moving.',
    'Yellow': "Sees what's possible. Values creativity, opportunity, and thinking beyond the current frame.",
    'Green':  'Protects people. Values relationships, harmony, and bringing everyone along.',
}

SCENARIOS = [
    dict(
        title='Speed versus certainty',
        prompt='A promising new opportunity has appeared, but some details are still unclear. What is your natural response?',
        left_label='I want to understand it fully before we commit',
        left_colour='Blue',
        right_label="Let's start and figure it out as we go",
        right_colour='Red',
        discussion='What does the opposite instinct protect a team from, and when would you want it in the room?',
    ),
    dict(
        title='Possibility versus stability',
        prompt='Leadership announces a significant change in direction. Which one do you feel more aligned with?<br><em>Or as James would put it: Leadership announces a required optimisation of priorities to achieve a great outcome.</em>',
        left_label='I know what this disrupts for people and how they would feel about it',
        left_colour='Green',
        right_label='I notice the upside and what this could become',
        right_colour='Yellow',
        discussion='How could someone with the opposite instinct make your response to change stronger?',
        response_question='How could someone with the opposite instinct make your response to change stronger?',
    ),
    dict(
        title='Directness versus diplomacy',
        prompt="You strongly disagree with a colleague's proposed approach. What are you more likely to do?",
        left_label='Trust that <em>how</em> you say it shapes how well it resolves.',
        left_colour='Green',
        right_label='Trust that being direct gets to a better outcome faster.',
        right_colour='Red',
        discussion='What becomes possible when both instincts are in the conversation at the same time?',
    ),
    dict(
        title='Structure versus flexibility',
        prompt='You are starting a large project with a deadline several months away. What feels more comfortable?',
        left_label='Map it out — I want a clear plan before we start',
        left_colour='Blue',
        right_label='Stay adaptive — lock the goal, not the route',
        right_colour='Yellow',
        discussion='Where does the opposite instinct create space for you to do your best work?',
    ),
    dict(
        title='Definition versus discovery',
        prompt='A project has stalled and needs a reset. What feels most natural?',
        left_label='I want to zoom out and rethink the brief',
        left_colour='Yellow',
        right_label="Let's agree on a next step and go",
        right_colour='Red',
        discussion='How could the opposite instinct help you get to a better answer faster?',
    ),
    dict(
        title='Logic versus consensus',
        prompt="A decision needs to be made that not everyone agrees on. What matters most to you in the process?",
        left_label='The best argument should win — follow the reasoning',
        left_colour='Blue',
        right_label='Everyone should feel heard before we decide',
        right_colour='Green',
        discussion='What does it look like when a team gets the reasoning right and brings everyone with them?',
    ),
]

# ── Sheet setup ─────────────────────────────────────────────────────────────────

def _ensure_styles_tab():
    svc      = _sheets()
    meta     = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
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


def _ensure_session_tab():
    svc      = _sheets()
    meta     = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    existing = {s['properties']['title'] for s in meta.get('sheets', [])}
    if SESSION_TAB not in existing:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': [{'addSheet': {'properties': {'title': SESSION_TAB}}}]},
        ).execute()
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'{SESSION_TAB}'!A1:B4",
            valueInputOption='RAW',
            body={'values': [
                ['Key', 'Value'],
                ['current_scenario', '-1'],
                ['reveal_active', '0'],
                ['scenario_started_at', ''],
            ]},
        ).execute()

def _ensure_summaries_tab():
    svc      = _sheets()
    meta     = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    existing = {s['properties']['title'] for s in meta.get('sheets', [])}
    if SUMMARIES_TAB not in existing:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': [{'addSheet': {'properties': {'title': SUMMARIES_TAB}}}]},
        ).execute()
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'{SUMMARIES_TAB}'!A1:B1",
            valueInputOption='RAW',
            body={'values': [['Name', 'Summary']]},
        ).execute()


@st.cache_data(ttl=15, show_spinner=False)
def pull_summaries():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{SUMMARIES_TAB}'!A:B",
        ).execute().get('values', [])
        return {r[0]: r[1] for r in rows[1:] if len(r) >= 2}
    except Exception:
        return {}


def save_summary(name, summary):
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{SUMMARIES_TAB}'!A:B",
        ).execute().get('values', [])
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 1 and row[0] == name:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{SUMMARIES_TAB}'!B{i}",
                    valueInputOption='RAW',
                    body={'values': [[summary]]},
                ).execute()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{SUMMARIES_TAB}'!A:B",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[name, summary]]},
        ).execute()
    with_retry(_do, on_retry=_clear_sheets)
    st.cache_data.clear()


def generate_summary(name, scores, primary, secondary):
    from openai import OpenAI
    client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
    descriptors = {
        'Red':    'action-oriented and decisive, moves fast and values directness',
        'Blue':   'analytical and thorough, wants to understand fully before acting',
        'Yellow': 'possibility-focused and creative, drawn to opportunity and big ideas',
        'Green':  'people-focused and relationship-driven, attentive to how things land for others',
    }
    first       = name.split()[0]
    scores_text = ', '.join(f'{c} {v}%' for c, v in scores.items())
    resp = client.chat.completions.create(
        model='gpt-4o-mini',
        max_tokens=200,
        messages=[{
            'role': 'user',
            'content': (
                f'Write a 2-3 sentence summary of how {first} naturally shows up in a team, '
                f'based on their results from a workplace styles activity.\n\n'
                f'Primary style: {primary} — {descriptors[primary]}\n'
                f'Secondary style: {secondary} — {descriptors[secondary]}\n'
                f'Full colour mix: {scores_text}\n\n'
                f'Guidelines:\n'
                f'- Write in third person using their first name ({first})\n'
                f'- Warm, specific, and affirming — focus on what they bring to the team\n'
                f'- No corporate jargon. No hyphens or em dashes.\n'
                f'- Reference their primary instinct clearly, touch on their secondary where it adds nuance\n'
                f'- 2-3 sentences only. No bullet points.'
            ),
        }],
    )
    return resp.choices[0].message.content.strip()


# ── Session state ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=3, show_spinner=False)
def pull_session():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{SESSION_TAB}'!A:B",
        ).execute().get('values', [])
        return {r[0]: r[1] for r in rows[1:] if len(r) >= 2}
    except Exception:
        return {}


def set_session(key, value):
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{SESSION_TAB}'!A:B",
        ).execute().get('values', [])
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 1 and row[0] == key:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{SESSION_TAB}'!B{i}",
                    valueInputOption='RAW',
                    body={'values': [[str(value)]]},
                ).execute()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{SESSION_TAB}'!A:B",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[key, str(value)]]},
        ).execute()
    with_retry(_do, on_retry=_clear_sheets)
    st.cache_data.clear()

def _ensure_responses_tab():
    svc      = _sheets()
    meta     = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    existing = {s['properties']['title'] for s in meta.get('sheets', [])}
    if RESPONSES_TAB not in existing:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': [{'addSheet': {'properties': {'title': RESPONSES_TAB}}}]},
        ).execute()
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'{RESPONSES_TAB}'!A1:D1",
            valueInputOption='RAW',
            body={'values': [['Timestamp', 'Scenario', 'Pole', 'Response']]},
        ).execute()


@st.cache_data(ttl=5, show_spinner=False)
def pull_responses(scenario_idx):
    """Returns list of {'pole': 'left'|'right', 'text': str} for the given scenario."""
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{RESPONSES_TAB}'!A:D",
        ).execute().get('values', [])
        if len(rows) < 2:
            return []
        return [
            {'pole': r[2], 'text': r[3]}
            for r in rows[1:]
            if len(r) >= 4 and str(r[1]) == str(scenario_idx) and r[3].strip()
        ]
    except Exception:
        return []


def save_response(scenario_idx, pole, text):
    def _do():
        _sheets().spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=f"'{RESPONSES_TAB}'!A:D",
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': [[
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                scenario_idx, pole, text,
            ]]},
        ).execute()
    with_retry(_do, on_retry=_clear_sheets)
    pull_responses.clear()


# ── Play Nice ────────────────────────────────────────────────────────────────────

def _ensure_play_nice_tabs():
    svc      = _sheets()
    meta     = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    existing = {s['properties']['title'] for s in meta.get('sheets', [])}

    to_add = []
    if PLAY_NICE_SESSION_TAB not in existing:
        to_add.append({'addSheet': {'properties': {'title': PLAY_NICE_SESSION_TAB}}})
    if PLAY_NICE_RESPONSES_TAB not in existing:
        to_add.append({'addSheet': {'properties': {'title': PLAY_NICE_RESPONSES_TAB}}})
    if to_add:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID, body={'requests': to_add}
        ).execute()

    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{PLAY_NICE_SESSION_TAB}'!A1:B3",
    ).execute().get('values', [])
    if not rows:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"'{PLAY_NICE_SESSION_TAB}'!A1:B3",
            valueInputOption='RAW',
            body={'values': [
                ['Key', 'Value'],
                ['active_situation', '-1'],
                ['cards_revealed', '0'],
            ]},
        ).execute()

    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{PLAY_NICE_RESPONSES_TAB}'!A1:D1",
    ).execute().get('values', [])
    if not rows:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"'{PLAY_NICE_RESPONSES_TAB}'!A1:D1",
            valueInputOption='RAW',
            body={'values': [['Timestamp', 'Situation', 'Colour', 'Response']]},
        ).execute()


@st.cache_data(ttl=3, show_spinner=False)
def pull_play_nice_session():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{PLAY_NICE_SESSION_TAB}'!A:B",
        ).execute().get('values', [])
        return {r[0]: r[1] for r in rows[1:] if len(r) >= 2}
    except Exception:
        return {}


def set_play_nice_session(key, value):
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{PLAY_NICE_SESSION_TAB}'!A:B",
        ).execute().get('values', [])
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 1 and row[0] == key:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{PLAY_NICE_SESSION_TAB}'!B{i}",
                    valueInputOption='RAW', body={'values': [[str(value)]]},
                ).execute()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{PLAY_NICE_SESSION_TAB}'!A:B",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[key, str(value)]]},
        ).execute()
    with_retry(_do, on_retry=_clear_sheets)
    pull_play_nice_session.clear()


@st.cache_data(ttl=5, show_spinner=False)
def pull_play_nice_responses(situation_idx):
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{PLAY_NICE_RESPONSES_TAB}'!A:D",
        ).execute().get('values', [])
        if len(rows) < 2:
            return []
        return [
            {'colour': r[2], 'text': r[3]}
            for r in rows[1:]
            if len(r) >= 4 and str(r[1]) == str(situation_idx) and r[3].strip()
        ]
    except Exception:
        return []


def save_play_nice_response(situation_idx, colour, text):
    def _do():
        _sheets().spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=f"'{PLAY_NICE_RESPONSES_TAB}'!A:D",
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': [[
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                situation_idx, colour, text,
            ]]},
        ).execute()
    with_retry(_do, on_retry=_clear_sheets)
    pull_play_nice_responses.clear()


# ── Submission data ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=5, show_spinner=False)
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


def save_scenario(name, scenario_idx, value):
    """Save or update one scenario response for a participant (incremental)."""
    def _do():
        svc        = _sheets()
        rows       = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{STYLES_TAB}'!A:H",
        ).execute().get('values', [])
        now        = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        col_letter = chr(ord('C') + scenario_idx)  # S1→C, S2→D, ... S6→H

        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 2 and row[1] == name:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{STYLES_TAB}'!A{i}",
                    valueInputOption='RAW',
                    body={'values': [[now]]},
                ).execute()
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{STYLES_TAB}'!{col_letter}{i}",
                    valueInputOption='RAW',
                    body={'values': [[str(value)]]},
                ).execute()
                return

        new_row = [now, name, '50', '50', '50', '50', '50', '50']
        new_row[2 + scenario_idx] = str(value)
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{STYLES_TAB}'!A:H",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [new_row]},
        ).execute()
    with_retry(_do, on_retry=_clear_sheets)

# ── Scoring ─────────────────────────────────────────────────────────────────────

def compute_scores(row):
    c = {k: 0 for k in HEX}
    for i, sc in enumerate(SCENARIOS):
        v = int(row.get(f'S{i + 1}', 50))
        c[sc['left_colour']]  += (100 - v)
        c[sc['right_colour']] += v
    total = sum(c.values()) or 1
    return {k: round(v / total * 100, 1) for k, v in c.items()}


def top_two(scores):
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[0][0], ranked[1][0]

# ── Card HTML ───────────────────────────────────────────────────────────────────

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
        + ''.join(f'<span>{c}<br>{scores[c]:.1f}%</span>' for c in ['Red', 'Blue', 'Yellow', 'Green'])
        + '</div></div>'
    )


def card_html_small(name, scores):
    pri, sec = top_two(scores)
    pc, tc   = HEX[pri], TEXT[pri]
    return (
        f'<div style="background:{pc};border-radius:10px;padding:16px 12px 12px;'
        f'text-align:center;margin-bottom:8px;">'
        f'<div style="font-weight:700;color:{tc};font-size:0.88em;line-height:1.3;margin-bottom:6px;">{name}</div>'
        f'<div style="font-size:1.5em;font-weight:800;color:{tc};line-height:1.1;">{pri}</div>'
        f'<div style="font-size:0.72em;color:{tc};opacity:0.75;margin-bottom:10px;">+ {sec}</div>'
        f'<div style="display:flex;border-radius:3px;overflow:hidden;height:6px;">{colour_bar(scores)}</div>'
        f'</div>'
    )
