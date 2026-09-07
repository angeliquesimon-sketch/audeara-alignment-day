"""Shared data layer for the Strategy Cascade activity (rebuilt FY27)."""

import json as _json
import streamlit as st
import pandas as pd
from datetime import datetime
from utils import _sheets, _clear_sheets, with_retry

SHEET_ID = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'

CASCADE_SESSION_TAB       = 'Cascade Session'
CASCADE_COMMITMENTS_TAB   = 'Cascade Commitments'
CASCADE_CONTRIBUTIONS_TAB = 'Cascade Contributions'
CASCADE_CONFIDENCE_TAB    = 'Cascade Confidence'
CASCADE_CONTENT_TAB       = 'Cascade Content'       # Editable presentation content (Section | JSON)

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
        'id': 'c2',
        'number': '1',
        'title': 'Grow Australian Wholesale profitably',
        'description': (
            'We will deepen trusted clinic relationships, improve repeat ordering, broaden useful product '
            'access and turn frontline learning into better offers and better support.'
        ),
    },
    {
        'id': 'c3',
        'number': '2',
        'title': 'Convert AUA Technology capability into repeatable revenue',
        'description': (
            'We will prioritise programs that can progress from development to production, repeat orders '
            'and recurring licensing while building reusable capability rather than one-off engineering.'
        ),
    },
    {
        'id': 'c4',
        'number': '3',
        'title': 'Scale Auracast as a solutions business',
        'description': (
            'We will sell and support complete shared-listening outcomes: source, broadcast, receive, '
            'personalise, deploy and support.'
        ),
    },
    {
        'id': 'c7',
        'number': '4',
        'title': 'Build Listen & Learn into a scalable, funded partner model',
        'description': (
            'Secure the first funded deployments, prove impact with clinical evidence, '
            'and establish a partner pathway that can be replicated. '
            'FY27 is the year this goes from promising to proven.'
        ),
    },
    {
        'id': 'c1',
        'number': '5',
        'title': 'Win through customer outcomes',
        'description': (
            'We start with the life being improved, not the feature being shipped. '
            'Product quality, setup, support, connectivity and follow-through are all part of the outcome.'
        ),
    },
    {
        'id': 'c5',
        'number': '6',
        'title': 'Become tender-grade',
        'description': (
            'We will build the evidence, quality, service, supply, financial and partnership maturity '
            'required to participate credibly in the Hearing Australia tender.'
        ),
    },
    {
        'id': 'c6',
        'number': '7',
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

HOW_WE_WORK_ICONS = ['💡', '🤝', '✅', '🔬', '🔗', '🛡️', '🎯']

ENGINE_ATTRIBUTION = {
    'c2': 'Australian Wholesale',
    'c3': 'AUA Technology',
    'c4': 'Auracast Solutions',
    'c7': 'ShokzHear / OpenLearn',
}

ENGINE_DETAIL = {
    'wholesale': {
        'stats': [['1,500+', 'AU clinics'], ['12', 'countries stocked'], ['90%', 'of AU sites stocked']],
        'sections': [
            {'title': 'For clinics', 'content': [
                'Additional revenue stream for clinics.',
                'Solution for patients not yet ready for hearing aids.',
                'Products clinicians can confidently recommend.',
            ]},
            {'title': 'Where we are', 'content': [
                '1,500+ AU clinics. Network is built.',
                'FY27 = depth per clinic, not expansion.',
                'Major global chain relationships in place.',
            ]},
            {'title': 'Key channels', 'content': [
                'AU audiology clinics — major chains and independents.',
                'International: EU/US chains, Japan (growing), Taiwan (Clinico).',
            ]},
            {'title': 'FY27 priorities', 'content': [
                'Account depth and repeat ordering.',
                'Onboard incoming Clinical Business Managers.',
                'Simpler ordering, training and support.',
                'Stronger clinician feedback loops.',
            ]},
        ],
    },
    'aua_tech': {
        'stats': [['$1.68m', 'FY26 revenue'], ['+50%', 'YoY growth'], ['4', 'partners in market']],
        'sections': [
            {'title': 'How it works', 'content': [
                'Engineering services + white-label products + algorithm licensing.',
                'Three revenue streams: fees, licensing, white-label supply.',
                'Higher margin than hardware. Scales without proportional cost.',
            ]},
            {'title': 'Partners in market', 'content': [
                'Zildjian — Perfect Tune headphones, global.',
                'Eastech/China — NMPA certified, live on Tmall, JD.com.',
                'Clinico/Taiwan — white-label earbuds + Auracast range.',
                'Optek — AI algorithm licensing in consumer electronics chips.',
            ]},
            {'title': 'Pipeline', 'content': [
                'Rion and additional programs in development.',
                '7-gate framework: fund by readiness and strategic value.',
                'Reusable AUAI capability built once, deployed across partners.',
            ]},
            {'title': 'FY27 priorities', 'content': [
                'Progress programs to production revenue.',
                'Build reusable capability, not one-off engineering.',
                'Expand partner pipeline with disciplined selection.',
            ]},
        ],
    },
    'auracast': {
        'stats': [['∞', 'receivers per transmitter'], ['2', 'live deployments'], ['All', 'hearing abilities']],
        'sections': [
            {'title': 'What it is', 'content': [
                'Auracast is a Bluetooth LE broadcast standard for shared listening in venues.',
                'One transmitter → unlimited compatible receivers simultaneously.',
                'Complements hearing loops and hearing aids — works for all hearing abilities.',
            ]},
            {'title': 'Early wins', 'content': [
                'University of Queensland — classrooms and lectures.',
                'Bolton Clarke aged care — reference case for repeatable deployment.',
            ]},
            {'title': 'Priority environments', 'content': [
                'Senior living and aged care.',
                'Universities and classrooms.',
                'Healthcare and clinical settings.',
                'Public venues and AV partner installations.',
            ]},
            {'title': 'FY27 priorities', 'content': [
                'Formalise deployment offer, playbook and partner model.',
                'Convert Bolton Clarke into a repeatable package.',
                'Build AV sector pipeline. Grow Japan + Clinico Taiwan.',
            ]},
        ],
    },
    'shokzhear': {
        'stats': [['3-party', 'delivery model'], ['Exclusive AU', 'deployment rights'], ['FY27', 'first funded orders']],
        'sections': [
            {'title': 'The program', 'content': [
                'Audeara: program founder and device provider.',
                'Community delivery partners: charities who reach children.',
                'Funding partners: financial support in exchange for impact reporting.',
            ]},
            {'title': 'The product', 'content': [
                'OpenLearn Small by ShokzHear.',
                'Audeara sets specs. ShokzHear manufactures.',
                'Audeara holds exclusive Australian deployment rights.',
            ]},
            {'title': 'Path to scale', 'content': [
                'Schools and education systems.',
                'State and national programs + grants.',
                'Community delivery partners — no clinical intermediary needed.',
            ]},
            {'title': 'FY27 priorities', 'content': [
                'Initial customer orders.',
                'First funded deployments.',
                'Measurable evidence of impact.',
                'Repeatable partner model.',
            ]},
        ],
    },
}

CHOICE_DETAIL = {
    'c2': {
        'intro': 'Australian Wholesale is both a growth engine and our closest day-to-day learning loop with clinicians, partners and end users.',
        'sections': [
            {'title': 'What we will do', 'content': [
                'Build on FY26 momentum through account depth, repeat ordering and a focused portfolio.',
                'Onboard and enable the expanded field team, including the incoming Clinical Business Managers.',
                'Make ordering, training, setup and support simpler and more dependable.',
                'Strengthen feedback loops between clinicians, customer care, marketing, operations and product teams.',
                'Use returns, support and sales data to remove recurring friction.',
            ]},
            {'title': 'Customer promise', 'content': 'Easy to understand. Easy to order. Easy to set up. Dependable when help is needed.'},
        ],
    },
    'c3': {
        'intro': "AUA Technology turns Audeara's insight and engineering into capabilities that partners can deploy in products and platforms.",
        'sections': [
            {'title': 'Capability areas', 'content': [
                'Hearing insight, audio intelligence and clinical translation.',
                'Embedded systems, firmware, connectivity and device control.',
                'Applications, fitting tools, diagnostics and service interfaces.',
                'Platform implementation across supported chips, products and end-user environments.',
                'Evidence, validation, quality and controlled release.',
            ]},
            {'title': 'In market and scaling', 'content': [
                'A-02 TV Bundle and Audeara Buds.',
                'BT-03, BT-LE and the expanding Auracast solution set.',
                'Clinico and partner products moving toward repeatable revenue.',
            ]},
            {'title': 'Development and commercialisation', 'content': [
                'A-03 in development.',
                'OpenLearn Small by ShokzHear — initial orders and funded deployments.',
                'OPTEK.',
                'China hearing-aid programs.',
                'Rion and other prioritised partner opportunities.',
            ]},
            {'title': 'Portfolio discipline', 'content': 'We will describe products and programs honestly, fund them according to readiness and strategic value, and avoid turning possibility into an unvalidated promise.'},
        ],
    },
    'c4': {
        'intro': 'Auracast is becoming a distinct solutions business: not a single device or feature, but a complete system designed around a real environment and the people in it.',
        'sections': [
            {'title': 'The solution chain', 'content': [
                'Source — capture the right audio.',
                'Broadcast — distribute it reliably.',
                'Receive — connect compatible hearing and listening devices.',
                'Personalise — deliver the best useful experience for each listener.',
                'Deploy and support — make installation, training and ongoing use dependable.',
            ]},
            {'title': 'Priority environments', 'content': [
                'Senior living and care.',
                'Universities, classrooms and education.',
                'Healthcare and clinical settings.',
                'Public venues, events and partner-led installations.',
            ]},
            {'title': 'FY27 focus', 'content': 'The Bolton Clarke deployment gives us a reference point for turning technology into a repeatable, supportable solution. FY27 is about converting that learning into a clear offer, delivery playbook and partner model.'},
        ],
    },
    'c7': {
        'intro': 'A dedicated, partner-led commercial engine distinct from AUA Technology licensing and Auracast solutions.',
        'sections': [
            {'title': 'The product', 'content': 'OpenLearn Small by ShokzHear: Audeara sets functionality, size and audio-tuning requirements; ShokzHear customises and manufactures; Audeara holds exclusive Australian deployment rights.'},
            {'title': 'Path to scale', 'content': 'Institutional and community-led: schools and education systems, state and national programs, charities, grants and delivery partners. The Listen & Learn Community Impact Program is the delivery framework.'},
            {'title': 'FY27 focus', 'content': 'Initial customer orders, funded deployments, evidence of impact and a repeatable partner model.'},
        ],
    },
    'c1': {
        'intro': 'We start with the life being improved, not the feature being shipped.',
        'sections': [
            {'title': 'What this means in practice', 'content': [
                'Product quality, setup, support, connectivity and follow-through are all part of the outcome.',
                "Every function contributes to whether a customer's experience is good or not.",
                'Returns, support data and clinical feedback are signals — not just costs.',
            ]},
        ],
    },
    'c5': {
        'intro': 'The tender is exciting because it is a visible test of the company we are becoming. It is not a HALO project and it cannot be won by engineering, sales or leadership alone.',
        'sections': [
            {'title': 'Tender readiness is a whole-company capability', 'content': [
                'A compelling, dependable product portfolio.',
                'Clinical evidence and measurable customer outcomes.',
                'Quality, regulatory and risk discipline.',
                'National service, training, logistics and support.',
                'Supply, customisation and production partnerships.',
                'Financial capacity and working-capital planning.',
                'A coherent story about why Audeara and its partners can deliver.',
            ]},
            {'title': 'How each group contributes', 'content': [
                'Leadership: sets direction, makes trade-offs and creates internal and external cohesion.',
                'Market, Growth and Australian Wholesale: create demand, build trusted relationships and translate market learning into opportunity.',
                'Customer and Delivery: make promises real through operations, care, support, training and feedback.',
                'Technology and Product: turn insight into safe, useful, scalable products and platforms.',
                'Finance and Governance: protect sustainability, discipline, compliance and informed decision-making.',
            ]},
            {'title': 'Why it matters', 'content': 'Reaching the point where a tender is genuinely worth submitting will itself be an extraordinary achievement. It will show how far Audeara has progressed in one year.'},
        ],
    },
    'c6': {
        'intro': 'Opportunity is not the same as priority. FY27 requires deliberate trade-offs to protect cash and build what the strategy actually needs.',
        'sections': [
            {'title': 'What this means', 'content': [
                'Make trade-offs visibly — the whole team knows what we are not doing and why.',
                'Fund the work that best advances the strategy.',
                'Stop work that no longer earns its place.',
                'Revenue quality, gross margin, cash conversion and progress toward positive operating cash flow are the measures.',
            ]},
        ],
    },
}

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
                CASCADE_CONTENT_TAB,
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
        conf_hdr = ['Timestamp', 'ChoiceID', 'TeamScore', 'FunctionScore', 'Feedback']
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A1:E1",
        ).execute().get('values', [])
        if not rows or rows[0] != conf_hdr:
            svc.spreadsheets().values().clear(
                spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A:Z",
            ).execute()
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A1",
                valueInputOption='RAW', body={'values': [conf_hdr]},
            ).execute()

        # Content tab — seed header if empty
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTENT_TAB}'!A1:B1",
        ).execute().get('values', [])
        if not rows:
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTENT_TAB}'!A1",
                valueInputOption='RAW', body={'values': [['Section', 'JSON']]},
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


# ── Contributions (multi-row per dept per choice) ──────────────────────────────

@st.cache_data(ttl=5, show_spinner=False)
def pull_cascade_contributions():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A:E",
        ).execute().get('values', [])
        if len(rows) <= 1:
            return pd.DataFrame(columns=['Timestamp', 'ChoiceID', 'Department', 'Text', 'Status'])
        data = [r + [''] * (5 - len(r)) for r in rows[1:]]
        df   = pd.DataFrame(data, columns=['Timestamp', 'ChoiceID', 'Department', 'Text', 'Status'])
        return df[df['Status'] != 'deleted'].reset_index(drop=True)
    except Exception:
        return pd.DataFrame(columns=['Timestamp', 'ChoiceID', 'Department', 'Text', 'Status'])


def save_cascade_contribution(choice_id, department, text):
    """Append a new draft contribution row (unlimited rows per dept per choice)."""
    def _do():
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        _sheets().spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A:E",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[ts, choice_id, department, text, 'draft']]},
        ).execute()
        pull_cascade_contributions.clear()
    with_retry(_do, on_retry=_clear_sheets)


def update_contribution(ts, new_status=None, new_text=None):
    """Update status and/or text for a specific row identified by Timestamp."""
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A:E",
        ).execute().get('values', [])
        for i, row in enumerate(rows[1:], start=2):
            if not row or row[0] != ts:
                continue
            cur_choice = row[1] if len(row) > 1 else ''
            cur_dept   = row[2] if len(row) > 2 else ''
            cur_text   = row[3] if len(row) > 3 else ''
            cur_status = row[4] if len(row) > 4 else 'draft'
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A{i}:E{i}",
                valueInputOption='RAW',
                body={'values': [[ts, cur_choice, cur_dept,
                                 new_text   if new_text   is not None else cur_text,
                                 new_status if new_status is not None else cur_status]]},
            ).execute()
            pull_cascade_contributions.clear()
            return
    with_retry(_do, on_retry=_clear_sheets)


def set_dept_opted_out(choice_id, dept):
    """Soft-delete all active rows for this dept+choice and add an opted_out marker."""
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A:E",
        ).execute().get('values', [])
        ts_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for i, row in enumerate(rows[1:], start=2):
            if (len(row) >= 5 and row[1] == choice_id and row[2] == dept
                    and row[4] not in ('opted_out', 'deleted')):
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!E{i}",
                    valueInputOption='RAW', body={'values': [['deleted']]},
                ).execute()
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A:E",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[ts_now, choice_id, dept, '', 'opted_out']]},
        ).execute()
        pull_cascade_contributions.clear()
    with_retry(_do, on_retry=_clear_sheets)


def restore_dept(choice_id, dept):
    """Remove opted_out marker for a dept, allowing fresh contributions."""
    def _do():
        svc  = _sheets()
        rows = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!A:E",
        ).execute().get('values', [])
        for i, row in enumerate(rows[1:], start=2):
            if (len(row) >= 5 and row[1] == choice_id and row[2] == dept
                    and row[4] == 'opted_out'):
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{CASCADE_CONTRIBUTIONS_TAB}'!E{i}",
                    valueInputOption='RAW', body={'values': [['deleted']]},
                ).execute()
        pull_cascade_contributions.clear()
    with_retry(_do, on_retry=_clear_sheets)


# ── Confidence (anonymous, append-only) ───────────────────────────────────────

_CONF_COLS = ['Timestamp', 'ChoiceID', 'TeamScore', 'FunctionScore', 'Feedback']

@st.cache_data(ttl=5, show_spinner=False)
def pull_cascade_confidence():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A:E",
        ).execute().get('values', [])
        if len(rows) <= 1:
            return pd.DataFrame(columns=_CONF_COLS)
        # Pad short rows so DataFrame construction doesn't fail
        data = [r + [''] * (5 - len(r)) for r in rows[1:]]
        return pd.DataFrame(data, columns=_CONF_COLS)
    except Exception:
        return pd.DataFrame(columns=_CONF_COLS)


def save_cascade_confidence(choice_id, team_score, function_score='', feedback=''):
    def _do():
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        _sheets().spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONFIDENCE_TAB}'!A:E",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[now, choice_id, team_score, function_score, feedback]]},
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


# ── Content overrides (editable presentation content) ─────────────────────────

@st.cache_data(ttl=10, show_spinner=False)
def pull_cascade_content_overrides():
    """Returns {section: data} from the Cascade Content Sheet tab."""
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTENT_TAB}'!A:B",
        ).execute().get('values', [])
        result = {}
        for row in rows[1:]:
            if len(row) >= 2 and row[0] and row[1]:
                try:
                    result[row[0]] = _json.loads(row[1])
                except Exception:
                    pass
        return result
    except Exception:
        return {}


def save_cascade_content_section(section, data):
    """Upsert the full JSON data list for a section."""
    def _do():
        svc      = _sheets()
        rows     = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTENT_TAB}'!A:B",
        ).execute().get('values', [])
        json_str = _json.dumps(data, ensure_ascii=False)
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0] == section:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{CASCADE_CONTENT_TAB}'!A{i}:B{i}",
                    valueInputOption='RAW',
                    body={'values': [[section, json_str]]},
                ).execute()
                pull_cascade_content_overrides.clear()
                return
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range=f"'{CASCADE_CONTENT_TAB}'!A:B",
            valueInputOption='RAW', insertDataOption='INSERT_ROWS',
            body={'values': [[section, json_str]]},
        ).execute()
        pull_cascade_content_overrides.clear()
    with_retry(_do, on_retry=_clear_sheets)


def get_live_engines():
    """Returns full engine list (card + accordion data) — Sheet overrides if set."""
    ovr = pull_cascade_content_overrides()
    if 'engines' in ovr:
        return ovr['engines']
    return [
        {
            'id': e['id'],
            'title': e['title'],
            'subtitle': e['subtitle'],
            'description': e['description'],
            'stats': ENGINE_DETAIL.get(e['id'], {}).get('stats', []),
            'sections': ENGINE_DETAIL.get(e['id'], {}).get('sections', []),
        }
        for e in ENGINES
    ]


def get_live_os():
    """Returns OS items list — Sheet overrides if set."""
    ovr = pull_cascade_content_overrides()
    return ovr.get('os', list(OPERATING_SYSTEM))


def get_live_choices():
    """Returns full choice list (card + accordion data) — Sheet overrides if set."""
    ovr = pull_cascade_content_overrides()
    if 'choices' in ovr:
        return ovr['choices']
    return [
        {
            'id': c['id'],
            'number': c['number'],
            'title': c['title'],
            'description': c['description'],
            'attribution': ENGINE_ATTRIBUTION.get(c['id'], ''),
            'intro': CHOICE_DETAIL.get(c['id'], {}).get('intro', ''),
            'sections': CHOICE_DETAIL.get(c['id'], {}).get('sections', []),
        }
        for c in CHOICES
    ]


def get_live_how():
    """Returns HOW_WE_WORK as list of (principle, description) tuples — Sheet overrides if set."""
    ovr = pull_cascade_content_overrides()
    if 'how' in ovr:
        return [(item['principle'], item['description']) for item in ovr['how']]
    return list(HOW_WE_WORK)


# ── Stub for backward compatibility (one_thing.py imports this) ───────────────

def pull_cascade_content():
    """Stub — retained for one_thing.py import compatibility."""
    return [], {}
