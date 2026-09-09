"""Shared data layer for The One Thing activity."""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils import _sheets, _clear_sheets, with_retry, WINE, FOREST

SHEET_ID = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'

ONE_THING_SESSION_TAB     = 'One Thing Session'
ONE_THING_DRAFTS_TAB      = 'One Thing Drafts'
ONE_THING_SUGGESTIONS_TAB = 'One Thing Suggestions'
ONE_THING_WINNERS_TAB     = 'One Thing Winners'

DEPARTMENTS = [
    'Marketing',
    'Sales',
    'Engineering',
    'Operations',
    'Customer Service',
    'Finance',
    'Leadership & Strategy',
    'Product Owners',
    'R&D',
]

FUNCTION_TIER = {
    'Marketing':           'operational',
    'Sales':               'operational',
    'Engineering':         'operational',
    'Operations':          'operational',
    'Customer Service':    'operational',
    'Finance':             'operational',
    'Leadership & Strategy': 'governance',
    'Product Owners':      'governance',
    'R&D':                 'governance',
}

DEPARTMENT_MAP = {
    'Alex Bartlett':    ['Engineering'],
    'Andrew Morton':    ['Engineering'],
    'Angelique Simon':  ['Marketing', 'Product Owners'],
    'Bill Peng':        ['Operations', 'Finance', 'Leadership & Strategy', 'Product Owners'],
    'Bonar Dickson':    ['Engineering'],
    'Charli Every':     ['Customer Service'],
    'Dylan Whitehouse': ['Engineering'],
    'Ellissa Waters':   ['Customer Service'],
    "Ian O'Brien":      ['Engineering', 'R&D'],
    'James Fielding':   ['Finance', 'Leadership & Strategy', 'Product Owners', 'R&D'],
    'John Krajewski':   ['Marketing', 'Sales', 'Product Owners'],
    'Louise Heller':    ['Engineering'],
    'Misaki Kawashima': ['Sales'],
    'Rebekah Davidson': ['Operations', 'Customer Service'],
    'Robert Poulsen':   ['Sales', 'Product Owners'],
    'Sayaka Smith':     ['Finance'],
}

DEPARTMENT_HEADS = {
    'Marketing':           'Angelique Simon',
    'Sales':               'John Krajewski',
    'Engineering':         'Louise Heller',
    'Operations':          'Bill Peng',
    'Customer Service':    'Rebekah Davidson',
    'Finance':             'James Fielding',
    'Leadership & Strategy': 'James Fielding',
    'Product Owners':      'James Fielding',
    'R&D':                 "Ian O'Brien",
}

ONE_THING_STAGES = ['hidden', 'intro', 'departments', 'personal']
ONE_THING_STAGE_LABELS = {
    'hidden':      'Not started',
    'intro':       'Introduction visible',
    'departments': 'Function One Things open',
    'personal':    'Personal One Things open',
}

OPERATIONAL_FUNCTIONS = [
    dict(name='Marketing',
         defn="Building brand awareness, driving demand, and communicating Audeara's value across all channels — shaping the customer journey from first discovery through to purchase and long-term engagement",
         members='Angelique Simon, John Krajewski'),
    dict(name='Sales',
         defn='Converting commercial opportunities into revenue through wholesale clinic and international distributor channels',
         members='John Krajewski, Robert Poulsen, Misaki Kawashima'),
    dict(name='Engineering',
         defn="Designing, building, and maintaining Audeara's hardware, firmware, and software products",
         members="Louise Heller, Andrew Morton, Dr Ian O'Brien, Alex Bartlett, Dylan Whitehouse, Bonar Dickson"),
    dict(name='Operations',
         defn='Managing supply chain, logistics, inventory, and internal processes to keep the business running efficiently',
         members='Bill Peng, Rebekah Davidson'),
    dict(name='Customer Service',
         defn='Supporting customers and clinics post-purchase through technical assistance, troubleshooting, and care — including the onboarding and ongoing administration of clinics as Audeara stockists',
         members='Rebekah Davidson, Ellissa Waters, Charli Every'),
    dict(name='Finance',
         defn='Managing accounting, financial reporting, and commercial financial decisions including ASX obligations',
         members='Bill Peng, James Fielding, Sayaka Smith'),
]

GOVERNANCE_FUNCTIONS = [
    dict(name='Leadership & Strategy',
         defn='Setting company direction, making major decisions, and holding accountability for performance, compliance, and growth',
         members='Bill Peng, James Fielding'),
    dict(name='Product Owners',
         defn='Holding commercial and strategic ownership over specific product lines from launch through lifecycle',
         members='Bill Peng, James Fielding, John Krajewski, Angelique Simon, Robert Poulsen'),
    dict(name='R&D',
         defn="Owning Audeara's scientific and clinical research agenda and setting the direction of the knowledge base that underpins product development, clinical credibility, and market differentiation",
         members="Dr Ian O'Brien, James Fielding"),
]


def _fn_table_html(label, functions, winners):
    TH = (
        'text-align:left;font-size:0.7em;font-weight:700;letter-spacing:1px;'
        f'color:{WINE};padding:8px 12px;'
    )
    rows = ''
    for i, fn in enumerate(functions):
        winner = winners.get(fn['name'], '')
        border = '' if i == len(functions) - 1 else 'border-bottom:1px solid #F0EBF0;'
        if winner:
            ot = f'<span style="font-size:0.82em;color:{FOREST};line-height:1.45;">{winner}</span>'
        else:
            ot = '<span style="font-size:0.82em;color:#CCCCCC;font-style:italic;">Not yet agreed</span>'
        rows += (
            f'<tr style="{border}">'
            f'<td style="font-weight:700;font-size:0.8em;color:{WINE};padding:10px 12px;'
            f'vertical-align:top;white-space:nowrap;">{fn["name"]}</td>'
            f'<td style="font-size:0.77em;color:#555;line-height:1.5;padding:10px 12px;'
            f'vertical-align:top;">{fn["defn"]}</td>'
            f'<td style="font-size:0.77em;color:#777;padding:10px 12px;'
            f'vertical-align:top;">{fn["members"]}</td>'
            f'<td style="padding:10px 12px;vertical-align:top;">{ot}</td>'
            f'</tr>'
        )
    return (
        f'<div style="font-size:0.75em;font-weight:700;letter-spacing:2px;color:#888;'
        f'margin-bottom:8px;">{label}</div>'
        f'<div style="border:1px solid #E8E0E8;border-radius:8px;overflow:hidden;margin-bottom:24px;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr style="background:#FAF6FA;border-bottom:2px solid #E0D0DF;">'
        f'<th style="{TH}width:13%;">FUNCTION</th>'
        f'<th style="{TH}width:37%;">RESPONSIBLE FOR</th>'
        f'<th style="{TH}width:22%;">MEMBERS</th>'
        f'<th style="{TH}width:28%;">THE ONE THING</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table></div>'
    )


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
