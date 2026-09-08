"""Shared data layer — FY27 Scorecard."""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils import _sheets, _clear_sheets, with_retry

SHEET_ID      = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'
SCORECARD_TAB = 'Scorecard Entries'
_COLS         = ['Timestamp', 'ChoiceID', 'Department', 'Metric', 'Target', 'Owner']


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
            spreadsheetId=SHEET_ID, range=f"'{SCORECARD_TAB}'!A1:F1",
        ).execute().get('values', [])
        if not rows or rows[0] != _COLS:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{SCORECARD_TAB}'!A1",
                valueInputOption='RAW', body={'values': [_COLS]},
            ).execute()
    with_retry(_do, on_retry=_clear_sheets)


@st.cache_data(ttl=5, show_spinner=False)
def pull_scorecard_entries():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{SCORECARD_TAB}'!A:F",
        ).execute().get('values', [])
        if len(rows) <= 1:
            return pd.DataFrame(columns=_COLS)
        data = [r + [''] * (6 - len(r)) for r in rows[1:]]
        return pd.DataFrame(data, columns=_COLS)
    except Exception:
        return pd.DataFrame(columns=_COLS)


def save_scorecard_entry(choice_id: str, dept: str, metric: str, target: str, owner: str):
    """Upsert by (ChoiceID, Department)."""
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{SCORECARD_TAB}'!A:F",
        ).execute().get('values', [])
        new  = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), choice_id, dept, metric, target, owner]
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 3 and row[1] == choice_id and row[2] == dept:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{SCORECARD_TAB}'!A{i}:F{i}",
                    valueInputOption='RAW', body={'values': [new]},
                ).execute()
                pull_scorecard_entries.clear()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{SCORECARD_TAB}'!A:F",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [new]},
        ).execute()
        pull_scorecard_entries.clear()
    with_retry(_do, on_retry=_clear_sheets)
