"""Shared data layer for The One Thing activity."""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils import _sheets, _clear_sheets, with_retry

SHEET_ID = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'

ONE_THING_SESSION_TAB     = 'One Thing Session'
ONE_THING_DRAFTS_TAB      = 'One Thing Drafts'
ONE_THING_SUGGESTIONS_TAB = 'One Thing Suggestions'
ONE_THING_WINNERS_TAB     = 'One Thing Winners'

DEPARTMENTS = [
    'Marketing',
    'Sales',
    'Product / R&D',
    'Operations & Customer Service',
    'Finance',
    'Leadership & Strategy',
]

DEPARTMENT_MAP = {
    'Alex Bartlett':    ['Product / R&D'],
    'Andrew Morton':    ['Product / R&D'],
    'Angelique Simon':  ['Marketing'],
    'Bill Peng':        ['Operations & Customer Service'],
    'Charli Every':     ['Operations & Customer Service'],
    'Dylan Whitehouse': ['Product / R&D'],
    'Ellissa Waters':   ['Operations & Customer Service'],
    "Ian O'Brien":      ['Product / R&D'],
    'James Fielding':   ['Finance', 'Leadership & Strategy'],
    'John Krajewski':   ['Marketing', 'Sales'],
    'Louise Heller':    ['Product / R&D'],
    'Misaki Kawashima': ['Sales'],
    'Rebekah Davidson': ['Operations & Customer Service'],
    'Robert Poulsen':   ['Sales'],
    'Sayaka Smith':     ['Finance'],
}

DEPARTMENT_HEADS = {
    'Marketing':                     'John Krajewski',
    'Sales':                         'John Krajewski',
    'Product / R&D':                 'Louise Heller',
    'Operations & Customer Service': 'Bill Peng',
    'Finance':                       'James Fielding',
    'Leadership & Strategy':         'James Fielding',
}

ONE_THING_STAGES = ['hidden', 'intro', 'departments', 'personal']
ONE_THING_STAGE_LABELS = {
    'hidden':      'Not started',
    'intro':       'Introduction visible',
    'departments': 'Departmental One Things open',
    'personal':    'Personal One Things open',
}

# ── Sheet setup ────────────────────────────────────────────────────────────────

def _ensure_one_thing_tabs():
    def _do():
        svc      = _sheets()
        existing = {s['properties']['title'] for s in
                    svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute().get('sheets', [])}

        to_add = []
        for tab in [ONE_THING_SESSION_TAB, ONE_THING_DRAFTS_TAB,
                    ONE_THING_SUGGESTIONS_TAB, ONE_THING_WINNERS_TAB]:
            if tab not in existing:
                to_add.append({'addSheet': {'properties': {'title': tab}}})
        if to_add:
            svc.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID, body={'requests': to_add},
            ).execute()

        # Session tab — seed if empty
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_SESSION_TAB}'!A1:B2",
        ).execute().get('values', [])
        if not rows:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{ONE_THING_SESSION_TAB}'!A1:B2",
                valueInputOption='RAW',
                body={'values': [['Key', 'Value'], ['stage', 'hidden']]},
            ).execute()

        # Drafts tab — seed header if empty
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_DRAFTS_TAB}'!A1:B1",
        ).execute().get('values', [])
        if not rows:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{ONE_THING_DRAFTS_TAB}'!A1:B1",
                valueInputOption='RAW',
                body={'values': [['Department', 'Draft']]},
            ).execute()

        # Suggestions tab — seed header if empty
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_SUGGESTIONS_TAB}'!A1:D1",
        ).execute().get('values', [])
        if not rows:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{ONE_THING_SUGGESTIONS_TAB}'!A1:D1",
                valueInputOption='RAW',
                body={'values': [['Timestamp', 'Name', 'Department', 'Suggestion']]},
            ).execute()

        # Winners tab — seed header if empty
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_WINNERS_TAB}'!A1:D1",
        ).execute().get('values', [])
        if not rows:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{ONE_THING_WINNERS_TAB}'!A1:D1",
                valueInputOption='RAW',
                body={'values': [['Department', 'Winner', 'LockedBy', 'Timestamp']]},
            ).execute()

    with_retry(_do, on_retry=_clear_sheets)

# ── Session ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3, show_spinner=False)
def pull_one_thing_session():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_SESSION_TAB}'!A:B",
        ).execute().get('values', [])
        return {r[0]: r[1] for r in rows[1:] if len(r) >= 2}
    except Exception:
        return {}

def set_one_thing_session(key, value):
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_SESSION_TAB}'!A:B",
        ).execute().get('values', [])
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0] == key:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{ONE_THING_SESSION_TAB}'!B{i}",
                    valueInputOption='RAW', body={'values': [[value]]},
                ).execute()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_SESSION_TAB}'!A:B",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[key, value]]},
        ).execute()
    with_retry(_do, on_retry=_clear_sheets)

# ── Drafts ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=15, show_spinner=False)
def pull_one_thing_drafts():
    """Returns {dept: draft_text}."""
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_DRAFTS_TAB}'!A:B",
        ).execute().get('values', [])
        if len(rows) < 2:
            return {}
        return {r[0]: r[1] for r in rows[1:] if len(r) >= 2 and r[0]}
    except Exception:
        return {}

def save_one_thing_draft(dept, text):
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_DRAFTS_TAB}'!A:B",
        ).execute().get('values', [])
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 1 and row[0] == dept:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{ONE_THING_DRAFTS_TAB}'!A{i}:B{i}",
                    valueInputOption='RAW', body={'values': [[dept, text]]},
                ).execute()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_DRAFTS_TAB}'!A:B",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[dept, text]]},
        ).execute()
    with_retry(_do, on_retry=_clear_sheets)
    pull_one_thing_drafts.clear()

# ── Suggestions ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=10, show_spinner=False)
def pull_one_thing_suggestions():
    """Returns DataFrame with columns [Timestamp, Name, Department, Suggestion]."""
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_SUGGESTIONS_TAB}'!A:D",
        ).execute().get('values', [])
        if len(rows) < 2:
            return pd.DataFrame(columns=['Timestamp', 'Name', 'Department', 'Suggestion'])
        return pd.DataFrame(rows[1:], columns=['Timestamp', 'Name', 'Department', 'Suggestion'])
    except Exception:
        return pd.DataFrame(columns=['Timestamp', 'Name', 'Department', 'Suggestion'])

def save_one_thing_suggestion(name, dept, suggestion):
    def _do():
        _sheets().spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_SUGGESTIONS_TAB}'!A:D",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                name, dept, suggestion,
            ]]},
        ).execute()
    with_retry(_do, on_retry=_clear_sheets)
    pull_one_thing_suggestions.clear()

# ── Winners ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=10, show_spinner=False)
def pull_one_thing_winners():
    """Returns {dept: winner_text}."""
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_WINNERS_TAB}'!A:D",
        ).execute().get('values', [])
        if len(rows) < 2:
            return {}
        return {r[0]: r[1] for r in rows[1:] if len(r) >= 2 and r[0]}
    except Exception:
        return {}

def save_one_thing_winner(dept, winner, locked_by):
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_WINNERS_TAB}'!A:D",
        ).execute().get('values', [])
        new  = [dept, winner, locked_by, datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 1 and row[0] == dept:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{ONE_THING_WINNERS_TAB}'!A{i}:D{i}",
                    valueInputOption='RAW', body={'values': [new]},
                ).execute()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{ONE_THING_WINNERS_TAB}'!A:D",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [new]},
        ).execute()
    with_retry(_do, on_retry=_clear_sheets)
    pull_one_thing_winners.clear()
