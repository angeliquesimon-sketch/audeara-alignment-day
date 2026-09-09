"""Save all Alignment Day sheet tabs to a named snapshot JSON file.

Usage:
    python3 snapshot-save.py demo
    python3 snapshot-save.py empty
"""

import os, sys, json, pathlib
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SHEET_ID = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'

def _svc():
    creds = Credentials.from_authorized_user_file(
        os.path.expanduser('~/.config/signal-studio/google-token.json'))
    return build('sheets', 'v4', credentials=creds, cache_discovery=False)

name = sys.argv[1] if len(sys.argv) > 1 else 'snapshot'
out_dir = pathlib.Path(__file__).parent / 'snapshots'
out_dir.mkdir(exist_ok=True)
out_file = out_dir / f'{name}.json'

svc = _svc()
meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
tabs = [s['properties']['title'] for s in meta['sheets']]

data = {}
for tab in tabs:
    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{tab}'!A:Z",
    ).execute().get('values', [])
    data[tab] = rows
    print(f'  {tab}: {len(rows)} rows')

out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
print(f'\nSaved → snapshots/{name}.json ({len(tabs)} tabs)')
