"""Shared constants and functions for the Vision Magazine Cover activity."""
import sys, os, hashlib, base64
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from utils import _sheets, _drive, PURPLE, TEAL

SHEET_ID       = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'
SUB_TAB        = 'Vision Submissions'
VOTE_TAB       = 'Vision Votes'
IMG_CACHE_TAB  = 'Image Cache'
STORY_TAB      = 'Generated Story'
VISION_TAB     = 'Vision Statement'
IMGS_FOLDER_ID = '19fcjPrNdAxpMrLb8il6pBK8KXGTVI9cA'

COLUMNS = ['Timestamp', 'Year', 'Publication', 'Headline', 'The Story', 'Quote', 'Bottom Line', 'Image']

CATEGORIES = [
    ('Headline',    'The cover headline'),
    ('The Story',   'What Audeara achieved to make the cover'),
    ('Quote',       'A quote from the story'),
    ('Bottom Line', 'What the finance section says'),
    ('Image',       'The cover image'),
]

COVER_YEAR    = '2030'
PREVIEW_WIDTH = 260

IMAGE_STYLE = (
    'Bold editorial magazine cover photograph. '
    'Warm, aspirational, human — real people in genuine moments of connection. '
    'Colour palette: warm sand and neutral tones as the foundation, with deep teal as the feature accent colour. '
    'Bright, inviting light — confident and optimistic, not dark or dramatic. '
    'Clean, modern composition. Stylish but approachable. '
    'No text, no letters, no words, no numbers. '
)

# ── Sheet setup ────────────────────────────────────────────────────────────────

def _ensure_tabs():
    svc  = _sheets()
    meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    existing = {s['properties']['title'] for s in meta.get('sheets', [])}
    add_reqs = []
    for tab in [SUB_TAB, VOTE_TAB, IMG_CACHE_TAB, STORY_TAB, VISION_TAB]:
        if tab not in existing:
            add_reqs.append({'addSheet': {'properties': {'title': tab}}})
    if add_reqs:
        svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={'requests': add_reqs}).execute()

    if SUB_TAB not in existing:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"'{SUB_TAB}'!A1:H1",
            valueInputOption='RAW', body={'values': [COLUMNS]},
        ).execute()
    else:
        headers = (svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{SUB_TAB}'!A1:H1",
        ).execute().get('values', [[]])[0] if True else [])
        if 'Image' not in headers:
            col_letter = chr(ord('A') + len(headers))
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{SUB_TAB}'!{col_letter}1",
                valueInputOption='RAW', body={'values': [['Image']]},
            ).execute()

    if VOTE_TAB not in existing:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"'{VOTE_TAB}'!A1:C1",
            valueInputOption='RAW', body={'values': [['Category', 'Answer', 'Votes']]},
        ).execute()
    if IMG_CACHE_TAB not in existing:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"'{IMG_CACHE_TAB}'!A1:C1",
            valueInputOption='RAW', body={'values': [['Hash', 'Description', 'DriveFileId']]},
        ).execute()
    if STORY_TAB not in existing:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"'{STORY_TAB}'!A1:B1",
            valueInputOption='RAW', body={'values': [['Timestamp', 'Content']]},
        ).execute()
    if VISION_TAB not in existing:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"'{VISION_TAB}'!A1:B1",
            valueInputOption='RAW', body={'values': [['Type', 'Content']]},
        ).execute()

# ── Sheet helpers ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=20, show_spinner=False)
def pull_submissions():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{SUB_TAB}'!A:H",
        ).execute().get('values', [])
        if len(rows) < 2:
            return pd.DataFrame(columns=COLUMNS)
        headers = rows[0]
        data    = [r + [''] * (len(headers) - len(r)) for r in rows[1:]]
        return pd.DataFrame(data, columns=headers)
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

def append_submission(year, pub, headline, story, quote, bottom, image_desc):
    _sheets().spreadsheets().values().append(
        spreadsheetId=SHEET_ID, range=f"'{SUB_TAB}'!A:H",
        valueInputOption='RAW', insertDataOption='INSERT_ROWS',
        body={'values': [[datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                          year, pub, headline, story, quote, bottom, image_desc]]},
    ).execute()

@st.cache_data(ttl=20, show_spinner=False)
def pull_votes():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{VOTE_TAB}'!A:C",
        ).execute().get('values', [])
        if len(rows) < 2:
            return pd.DataFrame(columns=['Category', 'Answer', 'Votes'])
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df['Votes'] = pd.to_numeric(df['Votes'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception:
        return pd.DataFrame(columns=['Category', 'Answer', 'Votes'])

def set_vote_count(category, answer, count):
    svc  = _sheets()
    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{VOTE_TAB}'!A:C",
    ).execute().get('values', [])
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 2 and row[0] == category and row[1].strip().lower() == answer.strip().lower():
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{VOTE_TAB}'!C{i}",
                valueInputOption='RAW', body={'values': [[count]]},
            ).execute()
            return
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID, range=f"'{VOTE_TAB}'!A:C",
        valueInputOption='RAW', insertDataOption='INSERT_ROWS',
        body={'values': [[category, answer, count]]},
    ).execute()

def upsert_vote(category, answer):
    svc  = _sheets()
    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{VOTE_TAB}'!A:C",
    ).execute().get('values', [])
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 2 and row[0] == category and row[1].strip().lower() == answer.strip().lower():
            current = int(row[2]) if len(row) > 2 else 0
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, range=f"'{VOTE_TAB}'!C{i}",
                valueInputOption='RAW', body={'values': [[current + 1]]},
            ).execute()
            return
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID, range=f"'{VOTE_TAB}'!A:C",
        valueInputOption='RAW', insertDataOption='INSERT_ROWS',
        body={'values': [[category, answer, 1]]},
    ).execute()

# ── Image helpers ──────────────────────────────────────────────────────────────

def _img_cache_key(description):
    return f"cover_img_1024x1536_v2_{hashlib.md5(description.encode()).hexdigest()}"

def _desc_hash(description):
    return hashlib.md5(description.encode()).hexdigest()

@st.cache_data(ttl=300, show_spinner=False)
def _load_img_cache():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{IMG_CACHE_TAB}'!A:C",
        ).execute().get('values', [])
        return {row[0]: row[2] for row in rows[1:] if len(row) > 2}
    except Exception:
        return {}

def _drive_lookup(desc_hash):
    return _load_img_cache().get(desc_hash)

def _drive_upload(desc_hash, description, img_bytes):
    import io
    from googleapiclient.http import MediaIoBaseUpload
    meta  = {'name': f'cover-{desc_hash}.png', 'mimeType': 'image/png', 'parents': [IMGS_FOLDER_ID]}
    media = MediaIoBaseUpload(io.BytesIO(img_bytes), mimetype='image/png')
    file_id = _drive().files().create(
        body=meta, media_body=media, fields='id', supportsAllDrives=True,
    ).execute().get('id')
    _sheets().spreadsheets().values().append(
        spreadsheetId=SHEET_ID, range=f"'{IMG_CACHE_TAB}'!A:C",
        valueInputOption='RAW', insertDataOption='INSERT_ROWS',
        body={'values': [[desc_hash, description, file_id]]},
    ).execute()
    return file_id

def _drive_download(file_id):
    import io
    from googleapiclient.http import MediaIoBaseDownload
    buf = io.BytesIO()
    dl  = MediaIoBaseDownload(buf, _drive().files().get_media(fileId=file_id))
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue()

def generate_cover_image(description, save_to_drive=True):
    key = _img_cache_key(description)
    if isinstance(st.session_state.get(key), bytes):
        return st.session_state[key]
    dh      = _desc_hash(description)
    file_id = _drive_lookup(dh)
    if file_id:
        try:
            img_bytes = _drive_download(file_id)
            st.session_state[key] = img_bytes
            return img_bytes
        except Exception:
            pass
    try:
        from openai import OpenAI
        client    = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
        resp      = client.images.generate(
            model='gpt-image-1', prompt=IMAGE_STYLE + description, size='1024x1536', n=1,
        )
        img_bytes = base64.b64decode(resp.data[0].b64_json)
        if save_to_drive:
            try:
                _drive_upload(dh, description, img_bytes)
            except Exception:
                pass
        st.session_state[key] = img_bytes
        return img_bytes
    except Exception as e:
        st.session_state[key] = str(e)
        return None

def _show_image(description, caption=None, save_to_drive=True):
    if not description or not description.strip():
        return
    if not st.secrets.get('OPENAI_API_KEY'):
        st.caption('_(Image generation not configured)_')
        return
    key = _img_cache_key(description)
    if key not in st.session_state:
        with st.spinner('Generating cover image…'):
            generate_cover_image(description, save_to_drive=save_to_drive)
    img = st.session_state.get(key)
    if isinstance(img, bytes):
        st.image(img, caption=caption, width=PREVIEW_WIDTH)
    elif isinstance(img, str):
        st.caption(f'_(Image generation failed: {img})_')

def _compose_cover_image(pub, headline, quote, bottom, img_bytes):
    from PIL import Image, ImageDraw, ImageFont
    import io
    img = Image.open(io.BytesIO(img_bytes)).convert('RGBA')
    W, H   = img.size
    MAST_H = int(H * 0.09)
    _TEAL  = (24, 131, 131, 255)
    PAD    = int(W * 0.045)
    draw   = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W, MAST_H)], fill=(255, 255, 255, 240))
    draw.rectangle([(0, MAST_H - 5), (W, MAST_H)], fill=_TEAL)

    def _font(size, bold=False):
        for p in [
            f'/usr/share/fonts/truetype/dejavu/DejaVuSans{"-Bold" if bold else ""}.ttf',
            f'/usr/share/fonts/truetype/noto/NotoSans{"-Bold" if bold else "-Regular"}.ttf',
            f'/usr/share/fonts/truetype/liberation/LiberationSans{"-Bold" if bold else "-Regular"}.ttf',
        ]:
            try: return ImageFont.truetype(p, size)
            except Exception: pass
        try: return ImageFont.load_default(size=size)
        except TypeError: return ImageFont.load_default()

    draw.text((PAD, int(MAST_H * 0.15)), (pub or 'AUDEARA').upper(),
              font=_font(int(W * 0.058), bold=True), fill=(17, 17, 17, 255))
    grad = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(grad)
    gs   = int(H * 0.40)
    for y in range(gs, H):
        gd.line([(0, y), (W, y)], fill=(0, 0, 0, int(210 * min(1.0, (y - gs) / (H * 0.42)))))
    img  = Image.alpha_composite(img, grad)
    draw = ImageDraw.Draw(img)

    def _wrap(text, font, max_w):
        words, lines, cur = text.split(), [], []
        for w in words:
            test = ' '.join(cur + [w])
            if draw.textbbox((0, 0), test, font=font)[2] > max_w and cur:
                lines.append(' '.join(cur)); cur = [w]
            else:
                cur.append(w)
        if cur: lines.append(' '.join(cur))
        return lines

    text_w = W - PAD * 2
    y      = int(H * 0.55)
    hl_font = _font(int(W * 0.072), bold=True)
    for line in _wrap((headline or 'The Future of Hearing').upper(), hl_font, text_w):
        draw.text((PAD, y), line, font=hl_font, fill=(255, 255, 255, 255))
        y += draw.textbbox((0, 0), line, font=hl_font)[3] + int(H * 0.008)
    y += int(H * 0.018)
    if quote:
        draw.rectangle([(PAD, y), (PAD + 4, y + int(H * 0.09))], fill=_TEAL)
        qt_font = _font(int(W * 0.036))
        for line in _wrap(f'"{quote}"', qt_font, text_w - 20):
            draw.text((PAD + 14, y), line, font=qt_font, fill=(215, 215, 215, 255))
            y += draw.textbbox((0, 0), line, font=qt_font)[3] + 4
        y += int(H * 0.018)
    if bottom:
        bl_label = _font(int(W * 0.028), bold=True)
        draw.text((PAD, y), 'THE BOTTOM LINE', font=bl_label, fill=_TEAL)
        y += draw.textbbox((0, 0), 'THE BOTTOM LINE', font=bl_label)[3] + 8
        bl_font = _font(int(W * 0.034))
        for line in _wrap(bottom, bl_font, text_w):
            draw.text((PAD, y), line, font=bl_font, fill=(175, 175, 175, 255))
            y += draw.textbbox((0, 0), line, font=bl_font)[3] + 4
    buf = io.BytesIO()
    img.convert('RGB').save(buf, format='PNG', optimize=True)
    return buf.getvalue()

def _save_composed_to_drive(headline, composed_bytes):
    import io
    from googleapiclient.http import MediaIoBaseUpload
    slug  = ''.join(c for c in (headline or 'cover')[:40] if c.isalnum() or c in ' -').strip().replace(' ', '-')
    meta  = {'name': f'Audeara-Vision-Cover-2030-{slug}.png', 'mimeType': 'image/png', 'parents': [IMGS_FOLDER_ID]}
    media = MediaIoBaseUpload(io.BytesIO(composed_bytes), mimetype='image/png')
    return _drive().files().create(body=meta, media_body=media, fields='id', supportsAllDrives=True).execute().get('id')

# ── Story helpers ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=20, show_spinner=False)
def pull_generated_story():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{STORY_TAB}'!B2",
        ).execute().get('values', [])
        return rows[0][0] if rows and rows[0] else ''
    except Exception:
        return ''

def save_generated_story(content):
    _sheets().spreadsheets().values().update(
        spreadsheetId=SHEET_ID, range=f"'{STORY_TAB}'!A2:B2",
        valueInputOption='RAW',
        body={'values': [[datetime.now().strftime('%Y-%m-%d %H:%M:%S'), content]]},
    ).execute()

def generate_story(pub, headline, story_seed, quote, bottom):
    from openai import OpenAI
    client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
    context_parts = []
    if story_seed: context_parts.append(f'What happened: {story_seed}')
    if quote:      context_parts.append(f'Key quote: "{quote}"')
    if bottom:     context_parts.append(f'Financial headline: {bottom}')
    context = '\n'.join(context_parts) or 'A major milestone for Audeara in hearing technology and accessibility.'
    prompt = (
        f'Write a magazine feature article for {pub or "a major business publication"} dated 2030.\n\n'
        f'Cover headline: "{headline or "Audeara: The Company That Made the World Listen"}"\n\n'
        f'Context from the team:\n{context}\n\n'
        'Write a proper magazine feature — 400 to 500 words. Include:\n'
        '- A compelling lede that draws the reader in\n'
        '- 3 to 4 narrative paragraphs expanding on what Audeara achieved\n'
        '- The pull quote set on its own line, formatted with quotation marks\n'
        '- A resonant closing line\n\n'
        'Style: high-quality business magazine. British English. Warm, specific, inspiring. '
        'No hyphens or em dashes. No bullet points. Prose only.'
    )
    resp = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=900,
    )
    return resp.choices[0].message.content

# ── Vision Statement helpers ───────────────────────────────────────────────────

@st.cache_data(ttl=10, show_spinner=False)
def pull_vision_data():
    """Returns (candidates: list[str], final: str)."""
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{VISION_TAB}'!A2:B10",
        ).execute().get('values', [])
        candidates, final = [], ''
        for row in rows:
            if len(row) < 2:
                continue
            if row[0] == 'final':
                final = row[1]
            elif row[0].startswith('candidate'):
                candidates.append(row[1])
        return candidates, final
    except Exception:
        return [], ''

def save_vision_candidates(candidates):
    svc = _sheets()
    svc.spreadsheets().values().clear(
        spreadsheetId=SHEET_ID, range=f"'{VISION_TAB}'!A2:B10",
    ).execute()
    rows = [[f'candidate_{i+1}', c] for i, c in enumerate(candidates)]
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID, range=f"'{VISION_TAB}'!A2",
        valueInputOption='RAW', body={'values': rows},
    ).execute()

def save_final_vision(text):
    svc   = _sheets()
    rows  = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{VISION_TAB}'!A2:B10",
    ).execute().get('values', [])
    final_row = next(
        (i + 2 for i, r in enumerate(rows) if r and r[0] == 'final'), None
    )
    if final_row:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"'{VISION_TAB}'!B{final_row}",
            valueInputOption='RAW', body={'values': [[text]]},
        ).execute()
    else:
        next_row = len(rows) + 2
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"'{VISION_TAB}'!A{next_row}:B{next_row}",
            valueInputOption='RAW', body={'values': [['final', text]]},
        ).execute()

def generate_vision_candidates(pub, headline, story_seed, quote, bottom):
    from openai import OpenAI
    client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
    context_parts = []
    if headline:    context_parts.append(f'Cover headline: {headline}')
    if story_seed:  context_parts.append(f'What Audeara achieved: {story_seed}')
    if quote:       context_parts.append(f'Key quote: "{quote}"')
    if bottom:      context_parts.append(f'Financial headline: {bottom}')
    context = '\n'.join(context_parts) or 'Audeara is a leader in hearing technology and accessibility.'
    prompt = (
        'You are helping a team distil their collective vision into a single company vision statement.\n\n'
        f'The team imagined Audeara on the cover of a major magazine in 2030. Here is what they said:\n{context}\n\n'
        'Write exactly 3 candidate vision statements for Audeara. Each should:\n'
        '- Be one or two sentences, under 30 words\n'
        '- Start with "Audeara"\n'
        '- Be ambitious but credible — grounded in the team\'s inputs\n'
        '- Focus on human outcome, not technology\n'
        '- Use plain, direct language — no corporate jargon\n'
        '- Use British English\n'
        '- No hyphens or em dashes\n\n'
        'Return only the 3 statements, each on its own line, numbered 1. 2. 3. No other text.'
    )
    resp = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=300,
    )
    raw   = resp.choices[0].message.content.strip()
    lines = [ln.lstrip('0123456789. ').strip() for ln in raw.split('\n') if ln.strip()]
    return lines[:3]

# ── HTML cover builder ─────────────────────────────────────────────────────────

def build_cover_html(pub, headline, quote, bottom, img_bytes):
    if img_bytes:
        img_b64 = base64.b64encode(img_bytes).decode()
        bg = f'background-image:url(data:image/png;base64,{img_b64});background-size:cover;background-position:center top;'
    else:
        bg = 'background:linear-gradient(160deg,#094B4B,#188383);'
    quote_html  = f'<div class="quote">{quote}</div>'   if quote  else ''
    bottom_html = (
        f'<div class="bl-tag">The Bottom Line</div>'
        f'<div class="bl-text">{bottom}</div>'
    ) if bottom else ''
    return f'''<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" href="https://use.typekit.net/bxp8awr.css">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:ital,wght@0,300;0,400;0,700;1,300;1,400&family=Oswald:wght@400;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#e0e0e0;display:flex;justify-content:center;padding:20px;font-size:16px;}}
.cover{{width:380px;height:570px;position:relative;border-radius:3px;overflow:hidden;box-shadow:0 12px 40px rgba(0,0,0,0.45);{bg}}}
.masthead{{position:absolute;top:0;left:0;right:0;background:#fff;padding:10px 16px 8px;border-bottom:4px solid #188383;z-index:2;}}
.pub-name{{font-family:'Oswald',sans-serif;font-size:30px;font-weight:700;letter-spacing:0.04em;text-transform:uppercase;color:#111;line-height:1;}}
.pub-meta{{font-family:'Noto Sans',sans-serif;font-size:9px;letter-spacing:0.14em;color:#999;margin-top:4px;text-transform:uppercase;}}
.overlay{{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(to top,rgba(0,0,0,0.93) 55%,rgba(0,0,0,0.5) 82%,transparent);padding:44px 18px 20px;z-index:2;}}
.headline{{font-family:'roc-grotesk',sans-serif;font-size:27px;font-weight:700;line-height:1.12;color:#fff;text-transform:uppercase;letter-spacing:0.02em;margin-bottom:12px;}}
.quote{{font-family:'Noto Sans',sans-serif;font-size:12px;font-style:italic;font-weight:300;color:rgba(255,255,255,0.85);border-left:3px solid #188383;padding-left:10px;line-height:1.55;margin-bottom:12px;}}
.bl-tag{{font-family:'Noto Sans',sans-serif;font-size:8px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#188383;margin-bottom:4px;}}
.bl-text{{font-family:'Noto Sans',sans-serif;font-size:11px;font-weight:300;color:rgba(255,255,255,0.72);line-height:1.45;}}
</style>
</head>
<body>
<div class="cover">
    <div class="masthead">
        <div class="pub-name">{pub or 'Audeara'}</div>
        <div class="pub-meta">2030 &nbsp;&middot;&nbsp; Special Edition</div>
    </div>
    <div class="overlay">
        <div class="headline">{headline or 'The Future of Hearing'}</div>
        {quote_html}
        {bottom_html}
    </div>
</div>
</body>
</html>'''
