import json
import time
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

PURPLE = '#781E73'
TEAL   = '#188383'

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
]

def _creds():
    sa_info = json.loads(st.secrets['GOOGLE_SERVICE_ACCOUNT_JSON'])
    return service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)

def _sheets():
    if 'sheets_service' not in st.session_state:
        st.session_state['sheets_service'] = build('sheets', 'v4', credentials=_creds(), cache_discovery=False)
    return st.session_state['sheets_service']

def _drive():
    if 'drive_service' not in st.session_state:
        st.session_state['drive_service'] = build('drive', 'v3', credentials=_creds(), cache_discovery=False)
    return st.session_state['drive_service']

def _clear_sheets():
    st.session_state.pop('sheets_service', None)

def with_retry(fn, attempts=3, delay=1.0, on_retry=None):
    last_err = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last_err = e
            if i < attempts - 1:
                if on_retry:
                    on_retry()
                time.sleep(delay)
    raise last_err

def inject_styles():
    st.markdown(f'''
<style>
.activity-card {{
    background: #f9f5f9;
    border-left: 4px solid {PURPLE};
    border-radius: 6px;
    padding: 14px 18px;
    font-size: 16px;
    line-height: 1.6;
    margin: 8px 0;
}}
.category-header {{
    color: {PURPLE};
    font-size: 15px;
    font-weight: 700;
    margin: 20px 0 8px 0;
}}
.answer-row {{
    border-bottom: 1px solid #f0f0f0;
    padding: 6px 0;
}}
.vote-count {{
    font-size: 13px;
    color: #888;
}}
.winning-box {{
    background: linear-gradient(135deg, #f9f5f9, #f0fafa);
    border: 2px solid {TEAL};
    border-radius: 10px;
    padding: 24px 28px;
    font-size: 18px;
    font-weight: 500;
    line-height: 1.7;
    margin: 16px 0 24px 0;
}}
</style>
''', unsafe_allow_html=True)
