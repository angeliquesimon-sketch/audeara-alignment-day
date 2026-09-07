"""Shared data layer for the Strategy Cascade activity (rebuilt FY27)."""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils import _sheets, _clear_sheets, with_retry

SHEET_ID = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'

CASCADE_SESSION_TAB       = 'Cascade Session'
CASCADE_COMMITMENTS_TAB   = 'Cascade Commitments'   # One Thing personal commitments (unchanged)
CASCADE_CONTRIBUTIONS_TAB = 'Cascade Contributions'  # New: dept contributions per strategic choice
CASCADE_CONFIDENCE_TAB    = 'Cascade Confidence'     # New schema: (Timestamp, ChoiceID, Score)

# ── Hardcoded content (from James's strategy doc) ─────────────────────────────

ENGINES = [
    {
        'id': 'wholesale',
        'title': 'Australian Wholesale',
        'subtitle': 'trusted access and customer learning',
        'description': (
            'Brings trusted hearing-health products to clinicians and customers, '
            'builds channel relationships and keeps us close to real-world needs.'
        ),
    },
    {
        'id': 'aua_tech',
        'title': 'AUA Technology',
        'subtitle': 'scalable partner capability',
        'description': (
            'Turns our hearing and audio capability into partner products, embedded platforms, '
            'licensing and repeatable production revenue.'
        ),
    },
    {
        'id': 'auracast',
        'title': 'Auracast Solutions',
        'subtitle': 'shared listening, made deployable',
        'description': (
            'Creates complete shared-listening solutions for education, care, healthcare '
            'and public environments.'
        ),
    },
    {
        'id': 'shokzhear',
        'title': 'ShokzHear / OpenLearn',
        'subtitle': 'education and community access',
        'description': (
            'A partner-led engine taking a customised open-ear assistive-listening solution '
            'to children with listening and learning challenges. FY27 is about initial customer '
            'orders, funded deployments, evidence of impact and a repeatable partner model.'
        ),
    },
]

OPERATING_SYSTEM = [
    'Customer insight and clinical evidence',
    'Quality, regulatory discipline and dependable delivery',
    'Software, embedded systems, connectivity and product management',
    'Marketing, sales, partnerships, finance and governance',
    'Fast learning, clear priorities and accountable owners',
]

CHOICES = [
    {
        'id': 'c1',
        'number': '1',
        'title': 'Win through customer outcomes',
        'description': (
            'We start with the life being improved, not the feature being shipped. '
            'Product quality, setup, support, connectivity and follow-through are all part of the outcome.'
        ),
    },
    {
        'id': 'c2',
        'number': '2',
        'title': 'Grow Australian Wholesale profitably',
        'description': (
            'We will deepen trusted clinic relationships, improve repeat ordering, broaden useful product '
            'access and turn frontline learning into better offers and better support.'
        ),
    },
    {
        'id': 'c3',
        'number': '3',
        'title': 'Convert AUA Technology capability into repeatable revenue',
        'description': (
            'We will prioritise programs that can progress from development to production, repeat orders '
            'and recurring licensing while building reusable capability rather than one-off engineering.'
        ),
    },
    {
        'id': 'c4',
        'number': '4',
        'title': 'Scale Auracast as a solutions business',
        'description': (
            'We will sell and support complete shared-listening outcomes: source, broadcast, receive, '
            'personalise, deploy and support.'
        ),
    },
    {
        'id': 'c5',
        'number': '5',
        'title': 'Become tender-grade',
        'description': (
            'We will build the evidence, quality, service, supply, financial and partnership maturity '
            'required to participate credibly in the Hearing Australia tender.'
        ),
    },
    {
        'id': 'c6',
        'number': '6',
        'title': 'Operate with focus and cash discipline',
        'description': (
            'Opportunity is not the same as priority. We will make trade-offs visibly, fund the work '
            'that best advances the strategy and stop work that no longer earns its place.'
        ),
    },
]

HOW_WE_WORK = [
    ('Purpose before projects',      'Explain the human outcome first.'),
    ('One company',                  'Share context early and solve across functions.'),
    ('Clear owners',                 'Every priority has one accountable owner and a visible next gate.'),
    ('Evidence with enthusiasm',     'Test assumptions with customer, clinical, technical and commercial evidence.'),
    ('Partnership by design',        'Build the right internal and external team for the outcome.'),
    ('Safe, controlled improvement', 'Move quickly without losing quality, traceability or trust.'),
    ('Focus is a decision',          'When priorities change, say what stops.'),
]

DEPARTMENTS = [
    'Marketing',
    'Sales',
    'Product / R&D',
    'Operations & Customer Service',
    'Finance',
    'Leadership & Strategy',
]

CHOICE_COLOURS = ['#781E73', '#188383', '#50144B', '#005E63', '#781E73', '#188383']
ENGINE_COLOURS = ['#781E73', '#188383', '#50144B', '#005E63']

# ── Sheet setup ────────────────────────────────────────────────────────────────

def _ensure_cascade_tabs():
    def _do():
        svc      = _sheets()
        existing = {
            s['properties']['title']
            for s in svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute().get('sheets', [])
        }
        to_add = [
            tab for tab in [
                CASCADE_SESSION_TAB, CASCADE_COMMITMENTS_TAB,
                CASCADE_CONTRIBUTIONS_TAB, CASCADE_CONFIDENCE_TAB,
            ]
            if tab not in existing
        ]
        if to_add:
            svc.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body={'requests': [{'addSheet': {'properties': {'title': t}}} for t in to_add]},
            ).execute()

        # Session tab — seed if empty, ensure current_choice + confidence_open rows exist
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_SESSION_TAB}'!A:B",
        ).execute().get('values', [])
        if not rows:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{CASCADE_SESSION_TAB}'!A1",
                valueInputOption='RAW',
                body={'values': [
                    ['Key', 'Value'],
                    ['stage', 'hidden'],
                    ['current_choice', '0'],
                    ['confidence_open', '0'],
                ]},
            ).execute()
        else:
            keys = {r[0] for r in rows if r}
            appends = []
            if 'current_choice' not in keys:
                appends.append(['current_choice', '0'])
            if 'confidence_open' not in keys:
                appends.append(['confidence_open', '0'])
            if appends:
                svc.spreadsheets().values().append(
                    spreadsheetId=SHEET_ID, range=f"'{CASCADE_SESSION_TAB}'!A:B",
                    valueInputOption='RAW', insertDataOption='INSERT_ROWS',
                    body={'values': appends},
                ).execute()

        # Commitments tab — seed header if empty (unchanged schema)
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_COMMITMENTS_TAB}'!A1:D1",
        ).execute().get('values', [])
        if not rows:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{CASCADE_COMMITMENTS_TAB}'!A1",
                valueInputOption='RAW',
                body={'values': [['Timestamp', 'Name', 'Function', 'Commitment']]},
            ).execute()

        # Contributions tab — seed header, reset if schema differs
        new_hdr = ['Timestamp', 'ChoiceID', 'Department', 'Text', 'Status']
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A1:E1",
        ).execute().get('values', [])
        if not rows or rows[0] != new_hdr:
            svc.spreadsheets().values().clear(
                spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A:E",
            ).execute()
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A1",
                valueInputOption='RAW', body={'values': [new_hdr]},
            ).execute()

        # Confidence tab — seed header, reset if schema differs
        conf_hdr = ['Timestamp', 'ChoiceID', 'Score']
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A1:C1",
        ).execute().get('values', [])
        if not rows or rows[0] != conf_hdr:
            svc.spreadsheets().values().clear(
                spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A:Z",
            ).execute()
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A1",
                valueInputOption='RAW', body={'values': [conf_hdr]},
            ).execute()

    with_retry(_do, on_retry=_clear_sheets)


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


def set_cascade_session(**kwargs):
    """Update one or more session keys atomically."""
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_SESSION_TAB}'!A:B",
        ).execute().get('values', [])
        key_to_row = {r[0]: i + 2 for i, r in enumerate(rows[1:]) if r}
        for key, val in kwargs.items():
            val_str = str(val)
            if key in key_to_row:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{CASCADE_SESSION_TAB}'!B{key_to_row[key]}",
                    valueInputOption='RAW', body={'values': [[val_str]]},
                ).execute()
            else:
                svc.spreadsheets().values().append(
                    spreadsheetId=SHEET_ID, range=f"'{CASCADE_SESSION_TAB}'!A:B",
                    valueInputOption='RAW', insertDataOption='INSERT_ROWS',
                    body={'values': [[key, val_str]]},
                ).execute()
        pull_cascade_session.clear()
    with_retry(_do, on_retry=_clear_sheets)


# ── Contributions ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=5, show_spinner=False)
def pull_cascade_contributions():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A:E",
        ).execute().get('values', [])
        if len(rows) <= 1:
            return pd.DataFrame(columns=['Timestamp', 'ChoiceID', 'Department', 'Text', 'Status'])
        return pd.DataFrame(rows[1:], columns=['Timestamp', 'ChoiceID', 'Department', 'Text', 'Status'])
    except Exception:
        return pd.DataFrame(columns=['Timestamp', 'ChoiceID', 'Department', 'Text', 'Status'])


def save_cascade_contribution(choice_id, department, text):
    """Upsert (choice_id, department) with status=draft."""
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A:E",
        ).execute().get('values', [])
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new = [now, choice_id, department, text, 'draft']
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 3 and row[1] == choice_id and row[2] == department:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A{i}:E{i}",
                    valueInputOption='RAW', body={'values': [new]},
                ).execute()
                pull_cascade_contributions.clear()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A:E",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [new]},
        ).execute()
        pull_cascade_contributions.clear()
    with_retry(_do, on_retry=_clear_sheets)


def set_contribution_status(choice_id, department, status, text=None):
    """Set status (locked / opted_out / draft) for a (choice_id, department) row.
    Optionally update text at the same time (facilitator edit before locking)."""
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A:E",
        ).execute().get('values', [])
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 3 and row[1] == choice_id and row[2] == department:
                new_text = text if text is not None else (row[3] if len(row) >= 4 else '')
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A{i}:E{i}",
                    valueInputOption='RAW',
                    body={'values': [[now, choice_id, department, new_text, status]]},
                ).execute()
                pull_cascade_contributions.clear()
                return
        # No existing row — create one (e.g. opt-out with no prior text)
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A:E",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[now, choice_id, department, text or '', status]]},
        ).execute()
        pull_cascade_contributions.clear()
    with_retry(_do, on_retry=_clear_sheets)


# ── Confidence (anonymous, append-only) ───────────────────────────────────────

@st.cache_data(ttl=5, show_spinner=False)
def pull_cascade_confidence():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A:C",
        ).execute().get('values', [])
        if len(rows) <= 1:
            return pd.DataFrame(columns=['Timestamp', 'ChoiceID', 'Score'])
        return pd.DataFrame(rows[1:], columns=['Timestamp', 'ChoiceID', 'Score'])
    except Exception:
        return pd.DataFrame(columns=['Timestamp', 'ChoiceID', 'Score'])


def save_cascade_confidence(choice_id, score):
    def _do():
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        _sheets().spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A:C",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[now, choice_id, score]]},
        ).execute()
        pull_cascade_confidence.clear()
    with_retry(_do, on_retry=_clear_sheets)


# ── Personal commitments (One Thing page writes here — schema unchanged) ───────

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
    """Upsert by (name, function) — one row per function for multi-dept people."""
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_COMMITMENTS_TAB}'!A:D",
        ).execute().get('values', [])
        new  = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), name, function, commitment]
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 3 and row[1] == name and row[2] == function:
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
    with_retry(_do, on_retry=_clear_sheets)


# ── Stub for backward compatibility (one_thing.py imports this) ───────────────

def pull_cascade_content():
    """Stub — content is now hardcoded. Returns empty structures."""
    return [], {}
