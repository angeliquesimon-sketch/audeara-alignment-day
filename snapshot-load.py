"""Restore all Alignment Day sheet tabs from a named snapshot JSON file.

Usage:
    python3 snapshot-load.py demo     ← toggle demo mode ON
    python3 snapshot-load.py empty    ← toggle demo mode OFF
"""

import os, sys, json, pathlib, time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

SHEET_ID = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'

def _svc():
    creds = Credentials.from_authorized_user_file(
        os.path.expanduser('~/.config/signal-studio/google-token.json'))
    return build('sheets', 'v4', credentials=creds, cache_discovery=False)

name = sys.argv[1] if len(sys.argv) > 1 else 'snapshot'
snap_file = pathlib.Path(__file__).parent / 'snapshots' / f'{name}.json'

if not snap_file.exists():
    print(f'Snapshot not found: snapshots/{name}.json')
    sys.exit(1)

data = json.loads(snap_file.read_text())
svc  = _svc()

def _refresh_tabs():
    meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    return {s['properties']['title']: s['properties']['sheetId'] for s in meta['sheets']}

existing = _refresh_tabs()

for tab, rows in data.items():
    # Create tab if missing
    if tab not in existing:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'requests': [{'addSheet': {'properties': {'title': tab}}}]},
        ).execute()
        existing = _refresh_tabs()

    # Clear then rewrite with retry on rate-limit
    for attempt in range(5):
        try:
            svc.spreadsheets().values().clear(
                spreadsheetId=SHEET_ID, range=f"'{tab}'!A:Z",
            ).execute()
            break
        except HttpError as e:
            if e.resp.status == 429 and attempt < 4:
                time.sleep(15)
            else:
                raise

    if rows:
        for attempt in range(5):
            try:
                svc.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=f"'{tab}'!A1",
                    valueInputOption='RAW',
                    body={'values': rows},
                ).execute()
                break
            except HttpError as e:
                if e.resp.status == 429 and attempt < 4:
                    time.sleep(15)
                else:
                    raise

    time.sleep(1)  # stay under 60 writes/min
    print(f'  {tab}: {len(rows)} rows restored')

print(f'\nLoaded snapshots/{name}.json → {len(data)} tabs restored')
