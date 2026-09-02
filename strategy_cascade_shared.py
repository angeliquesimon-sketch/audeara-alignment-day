"""Shared data layer for the Strategy Cascade activity."""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils import _sheets, with_retry

SHEET_ID = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'

CASCADE_SESSION_TAB     = 'Cascade Session'
CASCADE_COMMITMENTS_TAB = 'Cascade Commitments'
CASCADE_CONFIDENCE_TAB  = 'Cascade Confidence'

STAGES = ['hidden', 'goals', 'functions', 'complete']
STAGE_LABELS = {
    'hidden':    'Not started',
    'goals':     'Goals revealed',
    'functions': 'Function priorities revealed — submissions open',
    'complete':  'Session complete',
}

# ── Edit these before the day with James's confirmed goals ────────────────────

GOALS = [
    {
        'id': 'G1',
        'title': 'Drive profitable consumer growth',
        'description': 'Grow Audeara consumer revenue through clinics, NDIS, DVA, and D2C with a focus on margin and channel quality.',
    },
    {
        'id': 'G2',
        'title': 'Grow AUA Technology revenue',
        'description': 'Expand the partner pipeline, execute existing agreements, and grow high-margin licensing and engineering revenue.',
    },
    {
        'id': 'G3',
        'title': 'Achieve sustainable profitability',
        'description': 'Reach and sustain positive operating cashflow through disciplined cost management and margin improvement across all channels.',
    },
]

FUNCTIONS = [
    'Marketing',
    'Sales',
    'Product / R&D',
    'Operations & Logistics',
    'Finance',
    'Leadership & Strategy',
]

# ── Edit these with James's confirmed One Things per function ─────────────────

FUNCTION_ONE_THINGS = {
    'Marketing':              'Build brand trust and awareness that converts to profitable demand.',
    'Sales':                  'Secure repeatable, profitable sales channels with strong unit margins.',
    'Product / R&D':          'Complete delivery on time while maintaining future readiness for the branded roadmap.',
    'Operations & Logistics': 'Minimise cost-to-serve while ensuring premium experience.',
    'Finance':                'Optimise margin and maintain capital efficiency.',
    'Leadership & Strategy':  'Focus on what most directly drives durable, profitable growth and strategic attractiveness.',
}

GOAL_COLOURS = ['#781E73', '#188383', '#50144B', '#005E63', '#C4A0C2', '#9BCFCF']

# ── Sheet setup ────────────────────────────────────────────────────────────────

def _ensure_cascade_tabs():
    svc      = _sheets()
    existing = {s['properties']['title'] for s in
                svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute().get('sheets', [])}
    to_add = []
    for tab in [CASCADE_SESSION_TAB, CASCADE_COMMITMENTS_TAB, CASCADE_CONFIDENCE_TAB]:
        if tab not in existing:
            to_add.append({'addSheet': {'properties': {'title': tab}}})
    if to_add:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID, body={'requests': to_add},
        ).execute()

    # Session tab
    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{CASCADE_SESSION_TAB}'!A1:B2",
    ).execute().get('values', [])
    if not rows:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_SESSION_TAB}'!A1:B2",
            valueInputOption='RAW',
            body={'values': [['Key', 'Value'], ['stage', 'hidden']]},
        ).execute()

    # Commitments tab
    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{CASCADE_COMMITMENTS_TAB}'!A1:D1",
    ).execute().get('values', [])
    if not rows:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_COMMITMENTS_TAB}'!A1:D1",
            valueInputOption='RAW',
            body={'values': [['Timestamp', 'Name', 'Function', 'Commitment']]},
        ).execute()

    # Confidence tab
    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A1:Z1",
    ).execute().get('values', [])
    if not rows:
        header = ['Timestamp', 'Name'] + [f'{g["id"]}_Confidence' for g in GOALS] + ['Risk']
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A1",
            valueInputOption='RAW', body={'values': [header]},
        ).execute()

# ── Session ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3, show_spinner=False)
def pull_cascade_session():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_SESSION_TAB}'!A:B",
        ).execute().get('values', [])
        return {r[0]: r[1] for r in rows[1:] if len(r) >= 2}
    except Exception:
        return {}

def set_cascade_session(key, value):
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_SESSION_TAB}'!A:B",
        ).execute().get('values', [])
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0] == key:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{CASCADE_SESSION_TAB}'!B{i}",
                    valueInputOption='RAW', body={'values': [[value]]},
                ).execute()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_SESSION_TAB}'!A:B",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[key, value]]},
        ).execute()
    with_retry(_do, on_retry=_sheets.clear)

# ── Commitments ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=10, show_spinner=False)
def pull_commitments():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_COMMITMENTS_TAB}'!A:D",
        ).execute().get('values', [])
        if len(rows) < 2:
            return pd.DataFrame(columns=['Timestamp', 'Name', 'Function', 'Commitment'])
        return pd.DataFrame(rows[1:], columns=['Timestamp', 'Name', 'Function', 'Commitment'])
    except Exception:
        return pd.DataFrame(columns=['Timestamp', 'Name', 'Function', 'Commitment'])

def save_commitment(name, function, commitment):
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_COMMITMENTS_TAB}'!A:B",
        ).execute().get('values', [])
        new  = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), name, function, commitment]
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 2 and row[1] == name:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{CASCADE_COMMITMENTS_TAB}'!A{i}:D{i}",
                    valueInputOption='RAW', body={'values': [new]},
                ).execute()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_COMMITMENTS_TAB}'!A:D",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [new]},
        ).execute()
    with_retry(_do, on_retry=_sheets.clear)

# ── Confidence ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=10, show_spinner=False)
def pull_confidence():
    try:
        n     = 2 + len(GOALS) + 1
        end   = chr(ord('A') + n - 1)
        rows  = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A:{end}",
        ).execute().get('values', [])
        cols  = ['Timestamp', 'Name'] + [f'{g["id"]}_Confidence' for g in GOALS] + ['Risk']
        if len(rows) < 2:
            return pd.DataFrame(columns=cols)
        return pd.DataFrame(rows[1:], columns=cols)
    except Exception:
        return pd.DataFrame(columns=['Timestamp', 'Name'] + [f'{g["id"]}_Confidence' for g in GOALS] + ['Risk'])

def save_confidence(name, confidence_dict, risk):
    def _do():
        svc      = _sheets()
        row_data = (
            [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), name] +
            [str(confidence_dict.get(g['id'], 3)) for g in GOALS] +
            [risk]
        )
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A:B",
        ).execute().get('values', [])
        n   = 2 + len(GOALS) + 1
        end = chr(ord('A') + n - 1)
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 2 and row[1] == name:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{CASCADE_CONFIDENCE_TAB}'!A{i}:{end}{i}",
                    valueInputOption='RAW', body={'values': [row_data]},
                ).execute()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A:A",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [row_data]},
        ).execute()
    with_retry(_do, on_retry=_sheets.clear)
