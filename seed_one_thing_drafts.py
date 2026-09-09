#!/usr/bin/env python3
"""
Seed James's draft One Things into the Google Sheet.
Run once from the repo root: python3 seed_one_thing_drafts.py
"""

import json, sys, os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SHEET_ID  = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'
DRAFTS_TAB = 'One Thing Drafts'

DRAFTS = [
    ('Marketing',
     'Make the customer outcome the starting point. Not the product, the channel, or the format.'),
    ('Sales',
     'Understand the clinic\'s business before offering a solution. The sale follows the fit, not the other way around.'),
    ('Engineering',
     'Earn the right to build something new by first making what already exists work flawlessly.'),
    ('Operations',
     'Fix the system before fixing the symptom. Every repeated problem is a signal that the process needs to change.'),
    ('Customer Service',
     'Leave every customer and every clinic more capable and confident than when they came to us.'),
    ('Finance',
     'Make financial information useful for the next decision, not just accurate about the last one.'),
    ('Leadership & Strategy',
     'Set direction clearly enough that the team can make good decisions without you in the room.'),
    ('Product Owners',
     'Make the customer\'s job the centre of every product decision. A feature is only valid if it helps someone do something they couldn\'t do before.'),
    ('R&D',
     'Only pursue evidence that would force a decision. If the answer won\'t change what we build, who we target, or how we position, the question isn\'t right yet.'),
]

def _creds():
    token_path = os.path.expanduser('~/.config/signal-studio/google-token.json')
    return Credentials.from_authorized_user_file(token_path)

def main():
    svc = build('sheets', 'v4', credentials=_creds(), cache_discovery=False)

    # Read existing drafts so we can update in place rather than append duplicates
    result = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f"'{DRAFTS_TAB}'!A:B",
    ).execute()
    rows = result.get('values', [])

    # Build index of existing row numbers (1-based, skipping header)
    existing = {}
    for i, row in enumerate(rows[1:], start=2):
        if row:
            existing[row[0]] = i

    for dept, draft in DRAFTS:
        if dept in existing:
            row_num = existing[dept]
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'{DRAFTS_TAB}'!A{row_num}:B{row_num}",
                valueInputOption='RAW',
                body={'values': [[dept, draft]]},
            ).execute()
            print(f'  Updated: {dept}')
        else:
            svc.spreadsheets().values().append(
                spreadsheetId=SHEET_ID,
                range=f"'{DRAFTS_TAB}'!A:B",
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [[dept, draft]]},
            ).execute()
            print(f'  Added:   {dept}')

    print('\nDone. All 9 drafts saved to the sheet.')

if __name__ == '__main__':
    main()
