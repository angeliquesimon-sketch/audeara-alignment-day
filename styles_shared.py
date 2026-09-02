"""Shared constants and helpers for the Different Styles activity."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
from datetime import datetime
from utils import _sheets, with_retry

SHEET_ID    = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'
STYLES_TAB  = 'Styles Submissions'
SESSION_TAB = 'Styles Session'

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
        prompt='Leadership announces a significant change in direction. What do you notice first?',
        left_label='I notice what this disrupts and how it lands for people',
        left_colour='Green',
        right_label='I notice the upside and what this could become',
        right_colour='Yellow',
        discussion='How could someone with the opposite instinct make your response to change stronger?',
    ),
    dict(
        title='Directness versus diplomacy',
        prompt="You strongly disagree with a colleague's proposed approach. What are you more likely to do?",
        left_label='Trust that how you say it shapes how well it resolves.',
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
    with_retry(_do, on_retry=_sheets.clear)
    st.cache_data.clear()

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
    with_retry(_do, on_retry=_sheets.clear)

# ── Scoring ─────────────────────────────────────────────────────────────────────

def compute_scores(row):
    c = {k: 0 for k in HEX}
    for i, sc in enumerate(SCENARIOS):
        v = int(row.get(f'S{i + 1}', 50))
        c[sc['left_colour']]  += (100 - v)
        c[sc['right_colour']] += v
    return {k: round(v / 300 * 100) for k, v in c.items()}


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
