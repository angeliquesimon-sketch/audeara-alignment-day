import json
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

@st.cache_resource
def _sheets():
    return build('sheets', 'v4', credentials=_creds())

@st.cache_resource
def _drive():
    return build('drive', 'v3', credentials=_creds())

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
