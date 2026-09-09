"""Shared data layer — FY27 Scorecard (entries + proposals)."""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils import _sheets, _clear_sheets, with_retry

SHEET_ID      = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'
SCORECARD_TAB = 'Scorecard Entries'
_COLS         = ['Timestamp', 'ChoiceID', 'Department', 'Metric', 'Target', 'Owner', 'LockedBy']

PROPOSALS_TAB = 'Scorecard Proposals'
_PROP_COLS    = ['Timestamp', 'ChoiceID', 'Department', 'Name', 'Metric', 'Target', 'Owner']


def _ensure_scorecard_tab():
    def _do():
        svc      = _sheets()
        existing = {
            s['properties']['title']
            for s in svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute().get('sheets', [])
        }
        if SCORECARD_TAB not in existing:
            svc.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body={'requests': [{'addSheet': {'properties': {'title': SCORECARD_TAB}}}]},
            ).execute()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{SCORECARD_TAB}'!A1:G1",
        ).execute().get('values', [])
        if not rows or rows[0][:3] != _COLS[:3]:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{SCORECARD_TAB}'!A1",
                valueInputOption='RAW', body={'values': [_COLS]},
            ).execute()
    with_retry(_do, on_retry=_clear_sheets)


def _ensure_scorecard_proposals_tab():
    def _do():
        svc      = _sheets()
        existing = {
            s['properties']['title']
            for s in svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute().get('sheets', [])
        }
        if PROPOSALS_TAB not in existing:
            svc.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body={'requests': [{'addSheet': {'properties': {'title': PROPOSALS_TAB}}}]},
            ).execute()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{PROPOSALS_TAB}'!A1:G1",
        ).execute().get('values', [])
        if not rows or rows[0] != _PROP_COLS:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{PROPOSALS_TAB}'!A1",
                valueInputOption='RAW', body={'values': [_PROP_COLS]},
            ).execute()
    with_retry(_do, on_retry=_clear_sheets)


@st.cache_data(ttl=5, show_spinner=False)
def pull_scorecard_entries():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{SCORECARD_TAB}'!A:G",
        ).execute().get('values', [])
        if len(rows) <= 1:
            return pd.DataFrame(columns=_COLS)
        data = [r + [''] * (7 - len(r)) for r in rows[1:]]
        return pd.DataFrame(data, columns=_COLS)
    except Exception:
        return pd.DataFrame(columns=_COLS)


@st.cache_data(ttl=5, show_spinner=False)
def pull_scorecard_proposals():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{PROPOSALS_TAB}'!A:G",
        ).execute().get('values', [])
        if len(rows) <= 1:
            return pd.DataFrame(columns=_PROP_COLS)
        data = [r + [''] * (7 - len(r)) for r in rows[1:]]
        return pd.DataFrame(data, columns=_PROP_COLS)
    except Exception:
        return pd.DataFrame(columns=_PROP_COLS)


def save_scorecard_proposal(choice_id: str, dept: str, name: str,
                             metric: str, target: str, owner: str):
    """Always append a new proposal row (multiple per person allowed)."""
    def _do():
        svc = _sheets()
        new = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
               choice_id, dept, name, metric, target, owner]
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{PROPOSALS_TAB}'!A:G",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [new]},
        ).execute()
        pull_scorecard_proposals.clear()
    with_retry(_do, on_retry=_clear_sheets)


def save_scorecard_entry(choice_id: str, dept: str, metric: str, target: str,
                         owner: str, locked_by: str = ''):
    """Upsert by (ChoiceID, Department)."""
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{SCORECARD_TAB}'!A:G",
        ).execute().get('values', [])
        new  = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                choice_id, dept, metric, target, owner, locked_by]
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 3 and row[1] == choice_id and row[2] == dept:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{SCORECARD_TAB}'!A{i}:G{i}",
                    valueInputOption='RAW', body={'values': [new]},
                ).execute()
                pull_scorecard_entries.clear()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{SCORECARD_TAB}'!A:G",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [new]},
        ).execute()
        pull_scorecard_entries.clear()
    with_retry(_do, on_retry=_clear_sheets)
