"""Reset all Alignment Day activities — clears participant data, resets sessions."""

import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

_creds = Credentials.from_authorized_user_file(
    os.path.expanduser('~/.config/signal-studio/google-token.json')
)
svc = build('sheets', 'v4', credentials=_creds, cache_discovery=False).spreadsheets()

SHEET_ID = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'

def clear(tab, rng):
    svc.values().clear(
        spreadsheetId=SHEET_ID,
        range=f"'{tab}'!{rng}",
    ).execute()
    print(f'  cleared  {tab}!{rng}')

def reset_session(tab, defaults):
    """Overwrite known key rows back to default values."""
    rows = svc.values().get(
        spreadsheetId=SHEET_ID,
        range=f"'{tab}'!A:B",
    ).execute().get('values', [])
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 1 and row[0] in defaults:
            svc.values().update(
                spreadsheetId=SHEET_ID,
                range=f"'{tab}'!B{i}",
                valueInputOption='RAW',
                body={'values': [[defaults[row[0]]]]},
            ).execute()
            print(f'  reset    {tab} → {row[0]} = {defaults[row[0]]}')

print('\n── Mission Statement ──────────────────────────────')
clear('Submissions', 'A2:E')
clear('Votes', 'A2:C')

print('\n── Magazine Cover / Vision ────────────────────────')
clear('Vision Submissions', 'A2:I')
clear('Vision Votes', 'A2:C')
clear('Vision Statement', 'A2:B')
clear('Vision Candidate Votes', 'A2:C')
clear('Image Cache', 'A2:C')
clear('Generated Story', 'A2:B')

print('\n── Different Styles ───────────────────────────────')
clear('Styles Submissions', 'A2:H')
clear('Styles Summaries', 'A2:B')
reset_session('Styles Session', {
    'current_scenario': '-1',
    'reveal_active':    '0',
    'scenario_started_at': '',
})

print('\n── The One Thing ──────────────────────────────────')
clear('One Thing Drafts', 'A2:B')
clear('One Thing Suggestions', 'A2:D')
clear('One Thing Winners', 'A2:D')
reset_session('One Thing Session', {'stage': 'hidden'})

print('\n── Strategy Cascade ───────────────────────────────')
clear('Cascade Contributions', 'A2:E')
clear('Cascade Confidence', 'A2:F')
clear('Cascade Commitments', 'A2:D')
reset_session('Cascade Session', {
    'stage':            'hidden',
    'current_choice':   '0',
    'confidence_open':  '0',
})
print('  (Cascade Content preserved — edited presentation content kept)')

print('\n── Scorecard ──────────────────────────────────────')
clear('Scorecard Entries',   'A2:G')
clear('Scorecard Proposals', 'A2:G')

print('\n✅ All activities reset.\n')
