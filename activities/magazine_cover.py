import sys, os, hashlib, base64
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from utils import _sheets, _drive, inject_styles, PURPLE, TEAL

SHEET_ID       = '1Py7OFDrGKHvbHv9-MBgS4Nqv_D_EdwjO-29OOgIPHVI'
SUB_TAB        = 'Vision Submissions'
VOTE_TAB       = 'Vision Votes'
IMG_CACHE_TAB  = 'Image Cache'

COLUMNS = ['Timestamp', 'Year', 'Publication', 'Headline', 'The Story', 'Quote', 'Bottom Line', 'Image']

CATEGORIES = [
    ('Headline',    'The cover headline'),
    ('The Story',   'What Audeara achieved to make the cover'),
    ('Quote',       'A quote from the story'),
    ('Bottom Line', 'What the finance section says'),
    ('Image',       'The cover image'),
]

COVER_YEAR    = '2030'
PREVIEW_WIDTH = 260   # px — screen preview size; full image is 1024×1536 (portrait A4)

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
    if SUB_TAB not in existing:
        add_reqs.append({'addSheet': {'properties': {'title': SUB_TAB}}})
    if VOTE_TAB not in existing:
        add_reqs.append({'addSheet': {'properties': {'title': VOTE_TAB}}})
    if IMG_CACHE_TAB not in existing:
        add_reqs.append({'addSheet': {'properties': {'title': IMG_CACHE_TAB}}})
    if add_reqs:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID, body={'requests': add_reqs},
        ).execute()

    # Write / verify headers
    if SUB_TAB not in existing:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'{SUB_TAB}'!A1:H1",
            valueInputOption='RAW',
            body={'values': [COLUMNS]},
        ).execute()
    else:
        # Migrate: add Image column header if missing
        current = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{SUB_TAB}'!A1:H1",
        ).execute().get('values', [[]])
        headers = current[0] if current else []
        if 'Image' not in headers:
            col = len(headers) + 1
            col_letter = chr(ord('A') + len(headers))
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'{SUB_TAB}'!{col_letter}1",
                valueInputOption='RAW',
                body={'values': [['Image']]},
            ).execute()

    if VOTE_TAB not in existing:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'{VOTE_TAB}'!A1:C1",
            valueInputOption='RAW',
            body={'values': [['Category', 'Answer', 'Votes']]},
        ).execute()
    if IMG_CACHE_TAB not in existing:
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'{IMG_CACHE_TAB}'!A1:C1",
            valueInputOption='RAW',
            body={'values': [['Hash', 'Description', 'DriveFileId']]},
        ).execute()

# ── Sheet helpers ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=20, show_spinner=False)
def pull_submissions():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{SUB_TAB}'!A:H",
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
        spreadsheetId=SHEET_ID,
        range=f"'{SUB_TAB}'!A:H",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [[
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            year, pub, headline, story, quote, bottom, image_desc,
        ]]},
    ).execute()

@st.cache_data(ttl=20, show_spinner=False)
def pull_votes():
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{VOTE_TAB}'!A:C",
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
        spreadsheetId=SHEET_ID,
        range=f"'{VOTE_TAB}'!A:C",
    ).execute().get('values', [])
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 2 and row[0] == category and row[1].strip().lower() == answer.strip().lower():
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'{VOTE_TAB}'!C{i}",
                valueInputOption='RAW',
                body={'values': [[count]]},
            ).execute()
            return
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"'{VOTE_TAB}'!A:C",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [[category, answer, count]]},
    ).execute()

def upsert_vote(category, answer):
    svc  = _sheets()
    rows = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f"'{VOTE_TAB}'!A:C",
    ).execute().get('values', [])
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 2 and row[0] == category and row[1].strip().lower() == answer.strip().lower():
            current = int(row[2]) if len(row) > 2 else 0
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'{VOTE_TAB}'!C{i}",
                valueInputOption='RAW',
                body={'values': [[current + 1]]},
            ).execute()
            return
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"'{VOTE_TAB}'!A:C",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [[category, answer, 1]]},
    ).execute()

# ── Image generation ───────────────────────────────────────────────────────────

def _img_cache_key(description):
    return f"cover_img_1024x1536_v2_{hashlib.md5(description.encode()).hexdigest()}"

def _desc_hash(description):
    return hashlib.md5(description.encode()).hexdigest()

def _drive_lookup(desc_hash):
    """Return Drive file ID for a cached image, or None."""
    try:
        rows = _sheets().spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{IMG_CACHE_TAB}'!A:C",
        ).execute().get('values', [])
        for row in rows[1:]:
            if row and row[0] == desc_hash:
                return row[2] if len(row) > 2 else None
    except Exception:
        pass
    return None

def _drive_upload(desc_hash, description, img_bytes):
    """Upload PNG to Drive and record the file ID in the Image Cache sheet."""
    import io
    from googleapiclient.http import MediaIoBaseUpload
    meta  = {'name': f'cover-{desc_hash}.png', 'mimeType': 'image/png'}
    media = MediaIoBaseUpload(io.BytesIO(img_bytes), mimetype='image/png')
    file_id = _drive().files().create(
        body=meta, media_body=media, fields='id',
    ).execute().get('id')
    _sheets().spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"'{IMG_CACHE_TAB}'!A:C",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': [[desc_hash, description, file_id]]},
    ).execute()
    return file_id

def _drive_download(file_id):
    """Download image bytes from Drive by file ID."""
    import io
    from googleapiclient.http import MediaIoBaseDownload
    buf = io.BytesIO()
    dl  = MediaIoBaseDownload(buf, _drive().files().get_media(fileId=file_id))
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue()

def generate_cover_image(description, save_to_drive=True):
    """Return PNG bytes — checks Drive cache first, generates with OpenAI if not found."""
    key = _img_cache_key(description)

    # 1. Session cache (fastest)
    if isinstance(st.session_state.get(key), bytes):
        return st.session_state[key]

    # 2. Drive cache (persistent across sessions)
    dh      = _desc_hash(description)
    file_id = _drive_lookup(dh)
    if file_id:
        try:
            img_bytes = _drive_download(file_id)
            st.session_state[key] = img_bytes
            return img_bytes
        except Exception:
            pass  # fall through to generation

    # 3. Generate with OpenAI
    try:
        from openai import OpenAI
        client    = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
        resp      = client.images.generate(
            model='gpt-image-1',
            prompt=IMAGE_STYLE + description,
            size='1024x1536',
            n=1,
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
    """Generate and display a cover image for the given description."""
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
    else:
        st.caption('_(Image generation failed — unknown error)_')

def _compose_cover_image(pub, headline, quote, bottom, img_bytes):
    """Compose the full magazine cover as a PNG using Pillow."""
    from PIL import Image, ImageDraw, ImageFont
    import io

    img = Image.open(io.BytesIO(img_bytes)).convert('RGBA')
    W, H = img.size
    MAST_H = int(H * 0.09)
    TEAL   = (24, 131, 131, 255)
    PAD    = int(W * 0.045)

    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W, MAST_H)], fill=(255, 255, 255, 240))
    draw.rectangle([(0, MAST_H - 5), (W, MAST_H)], fill=TEAL)

    def _font(size, bold=False):
        for p in [
            f'/usr/share/fonts/truetype/dejavu/DejaVuSans{"-Bold" if bold else ""}.ttf',
            f'/usr/share/fonts/truetype/noto/NotoSans{"-Bold" if bold else "-Regular"}.ttf',
            f'/usr/share/fonts/truetype/liberation/LiberationSans{"-Bold" if bold else "-Regular"}.ttf',
        ]:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()

    pub_font = _font(int(W * 0.058), bold=True)
    draw.text((PAD, int(MAST_H * 0.15)), (pub or 'AUDEARA').upper(), font=pub_font, fill=(17, 17, 17, 255))

    grad = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(grad)
    gs   = int(H * 0.40)
    for y in range(gs, H):
        a = int(210 * min(1.0, (y - gs) / (H * 0.42)))
        gd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    img  = Image.alpha_composite(img, grad)
    draw = ImageDraw.Draw(img)

    def _wrap(text, font, max_w):
        words, lines, cur = text.split(), [], []
        for w in words:
            test  = ' '.join(cur + [w])
            w_px  = draw.textbbox((0, 0), test, font=font)[2]
            if w_px > max_w and cur:
                lines.append(' '.join(cur))
                cur = [w]
            else:
                cur.append(w)
        if cur:
            lines.append(' '.join(cur))
        return lines

    text_w = W - PAD * 2
    y      = int(H * 0.55)

    hl_font = _font(int(W * 0.072), bold=True)
    for line in _wrap((headline or 'The Future of Hearing').upper(), hl_font, text_w):
        draw.text((PAD, y), line, font=hl_font, fill=(255, 255, 255, 255))
        y += draw.textbbox((0, 0), line, font=hl_font)[3] + int(H * 0.008)
    y += int(H * 0.018)

    if quote:
        draw.rectangle([(PAD, y), (PAD + 4, y + int(H * 0.09))], fill=TEAL)
        qt_font = _font(int(W * 0.036))
        for line in _wrap(f'"{quote}"', qt_font, text_w - 20):
            draw.text((PAD + 14, y), line, font=qt_font, fill=(215, 215, 215, 255))
            y += draw.textbbox((0, 0), line, font=qt_font)[3] + 4
        y += int(H * 0.018)

    if bottom:
        bl_label = _font(int(W * 0.028), bold=True)
        draw.text((PAD, y), 'THE BOTTOM LINE', font=bl_label, fill=TEAL)
        y += draw.textbbox((0, 0), 'THE BOTTOM LINE', font=bl_label)[3] + 8
        bl_font = _font(int(W * 0.034))
        for line in _wrap(bottom, bl_font, text_w):
            draw.text((PAD, y), line, font=bl_font, fill=(175, 175, 175, 255))
            y += draw.textbbox((0, 0), line, font=bl_font)[3] + 4

    buf = io.BytesIO()
    img.convert('RGB').save(buf, format='PNG', optimize=True)
    return buf.getvalue()

def _save_composed_to_drive(headline, composed_bytes):
    """Upload a composed cover PNG to Drive and return the file ID."""
    import io
    from googleapiclient.http import MediaIoBaseUpload
    slug = ''.join(c for c in (headline or 'cover')[:40] if c.isalnum() or c in ' -').strip().replace(' ', '-')
    meta  = {'name': f'Audeara-Vision-Cover-2030-{slug}.png', 'mimeType': 'image/png'}
    media = MediaIoBaseUpload(io.BytesIO(composed_bytes), mimetype='image/png')
    return _drive().files().create(body=meta, media_body=media, fields='id').execute().get('id')

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
.cover{{
    width:380px;height:570px;position:relative;border-radius:3px;
    overflow:hidden;box-shadow:0 12px 40px rgba(0,0,0,0.45);
    {bg}
}}
.masthead{{
    position:absolute;top:0;left:0;right:0;
    background:#fff;padding:10px 16px 8px;
    border-bottom:4px solid #188383;z-index:2;
}}
.pub-name{{
    font-family:'Oswald',sans-serif;font-size:30px;font-weight:700;
    letter-spacing:0.04em;text-transform:uppercase;color:#111;line-height:1;
}}
.pub-meta{{
    font-family:'Noto Sans',sans-serif;font-size:9px;letter-spacing:0.14em;
    color:#999;margin-top:4px;text-transform:uppercase;
}}
.overlay{{
    position:absolute;bottom:0;left:0;right:0;
    background:linear-gradient(to top,rgba(0,0,0,0.93) 55%,rgba(0,0,0,0.5) 82%,transparent);
    padding:44px 18px 20px;z-index:2;
}}
.headline{{
    font-family:'roc-grotesk',sans-serif;font-size:27px;font-weight:700;
    line-height:1.12;color:#fff;text-transform:uppercase;
    letter-spacing:0.02em;margin-bottom:12px;
}}
.quote{{
    font-family:'Noto Sans',sans-serif;font-size:12px;font-style:italic;font-weight:300;
    color:rgba(255,255,255,0.85);border-left:3px solid #188383;
    padding-left:10px;line-height:1.55;margin-bottom:12px;
}}
.bl-tag{{
    font-family:'Noto Sans',sans-serif;font-size:8px;font-weight:700;
    letter-spacing:0.12em;text-transform:uppercase;color:#188383;margin-bottom:4px;
}}
.bl-text{{
    font-family:'Noto Sans',sans-serif;font-size:11px;font-weight:300;
    color:rgba(255,255,255,0.72);line-height:1.45;
}}
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

# ── Styles ─────────────────────────────────────────────────────────────────────

inject_styles()

st.markdown(f'''
<style>
.magazine-cover {{
    background: #111;
    color: #fff;
    border-radius: 10px;
    padding: 32px 36px 28px;
    margin: 0 0 16px 0;
}}
.mag-pub {{
    font-size: 0.72em;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 6px;
}}
.mag-year {{
    font-size: 0.7em;
    color: {TEAL};
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 18px;
}}
.mag-headline {{
    font-size: 1.9em;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 14px;
    color: #fff;
}}
.mag-story {{
    font-size: 0.88em;
    color: #ccc;
    line-height: 1.7;
    margin-bottom: 18px;
    border-left: 3px solid {TEAL};
    padding-left: 14px;
}}
.mag-quote {{
    font-size: 1em;
    font-style: italic;
    color: #fff;
    background: rgba(255,255,255,0.06);
    border-left: 4px solid {PURPLE};
    border-radius: 0 6px 6px 0;
    padding: 12px 16px;
    margin-bottom: 18px;
    line-height: 1.6;
}}
.mag-bl-label {{
    background: {TEAL};
    color: #fff;
    font-size: 0.7em;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 4px;
    display: inline-block;
    margin-bottom: 6px;
}}
.mag-bottom-text {{
    color: #bbb;
    font-size: 0.86em;
    line-height: 1.5;
}}
</style>
''', unsafe_allow_html=True)

# ── Init ───────────────────────────────────────────────────────────────────────

try:
    _ensure_tabs()
except Exception as _e:
    st.warning(f'Sheet setup issue — some features may not save correctly. ({_e})')

# ── Page header ────────────────────────────────────────────────────────────────

st.markdown('### Vision Activity — Magazine Cover Story')
st.markdown(
    'Imagine it\'s 2030. Audeara has made the cover of a major publication. '
    'What\'s the story? What did we achieve? What does the world say about us?'
)
st.markdown(
    f'<div class="activity-card">'
    f'<strong>Flag on the hill:</strong> If Audeara were on the cover of a major magazine '
    f'in 2030 — what would the headline say? What did we build? What does the cover look like?'
    f'</div>',
    unsafe_allow_html=True,
)
st.markdown('')

tab_submit, tab_vote, tab_results, tab_facilitate = st.tabs(['💡 Submit ideas', '🗳️ Vote', '🏆 Results', '🎛️ Facilitate'])

# ── Submit ─────────────────────────────────────────────────────────────────────

with tab_submit:
    st.markdown('#### Your cover story')
    st.caption(
        'Think about Audeara in 2030. What did we achieve? '
        'Fill in as many or as few fields as you like — there are no wrong answers.'
    )
    with st.form('vision_submit_form', clear_on_submit=True):
        pub = st.text_input(
            'Publication',
            placeholder='e.g. Fast Company, The Australian, Time, Harvard Business Review…',
        )
        headline = st.text_input(
            'Cover headline ✦',
            placeholder='e.g. "The company that made the world listen"',
        )
        story = st.text_area(
            'The story — what did Audeara achieve?',
            placeholder='e.g. "Audeara reached 1 million people across 40 countries by making hearing technology truly accessible…"',
            height=90,
        )
        quote = st.text_input(
            'A quote from the story',
            placeholder='e.g. "We didn\'t set out to build a hearing company. We set out to help people feel connected." — James Fielding',
        )
        bottom = st.text_input(
            'The bottom line — what does the finance section say?',
            placeholder='e.g. "Revenue crossed $50M, driven by Auracast partnerships across 3 continents."',
        )
        image_desc = st.text_area(
            '🎨 Describe the cover image',
            placeholder=(
                'Describe a scene, image, or feeling for the cover — '
                'AI will generate it in Audeara\'s brand style.\n'
                'e.g. "A person wearing headphones in a packed auditorium, '
                'surrounded by light and warmth, connected to the crowd."'
            ),
            height=90,
            key='vision_form_img_desc',
        )
        submitted = st.form_submit_button('Submit', type='primary', use_container_width=True)

    if submitted:
        if any([headline.strip(), story.strip(), quote.strip(), bottom.strip(), image_desc.strip()]):
            try:
                append_submission(
                    COVER_YEAR, pub.strip(), headline.strip(),
                    story.strip(), quote.strip(), bottom.strip(), image_desc.strip(),
                )
                st.cache_data.clear()
                st.toast('Submitted! Head to the Vote tab to upvote your favourites.', icon='✅')
                if image_desc.strip():
                    st.toast('Generating your cover image in the background…', icon='🎨')
            except Exception as _e:
                st.error(f'Could not save — network issue. Please try submitting again. ({_e})')
        else:
            st.warning('Please fill in at least one field before submitting.')

    # Image preview — outside the form so clicking it doesn't submit or block the flow
    if not submitted:
        _preview_desc = st.session_state.get('vision_form_img_desc', '').strip()
        if _preview_desc:
            c_cap, c_btn = st.columns([4, 1])
            with c_cap:
                st.caption('Want to see what your cover image will look like?')
            with c_btn:
                _do_preview = st.button('👁 Preview', key='vision_img_preview_btn', use_container_width=True)
            if _do_preview:
                st.session_state['_vision_preview_for'] = _preview_desc
            if st.session_state.get('_vision_preview_for') == _preview_desc:
                _show_image(
                    _preview_desc,
                    caption='Preview — image saves to Drive when you submit.',
                    save_to_drive=False,
                )

    st.divider()
    subs = pull_submissions()
    if not subs.empty:
        st.markdown(f'#### {len(subs)} submission{"s" if len(subs) != 1 else ""} so far')
        for _, row in subs.iterrows():
            img_desc = row.get('Image', '').strip()
            pub_str  = f' · {row.get("Publication","").strip()}' if row.get('Publication','').strip() else ''
            c_text, c_img = st.columns([3, 2]) if img_desc else (st.container(), None)
            with (c_text if img_desc else c_text):
                st.markdown(
                    f'<div class="activity-card">'
                    f'<span style="font-size:0.75em;color:#888;">{COVER_YEAR}{pub_str}</span><br>'
                    f'<span style="font-size:1.05em;font-weight:700;">{row.get("Headline","")}</span><br>'
                    f'<span style="font-size:0.88em;color:#555;">{row.get("The Story","")}</span><br>'
                    f'<em style="font-size:0.85em;">{row.get("Quote","")}</em><br>'
                    f'<span style="font-size:0.82em;color:#777;">{row.get("Bottom Line","")}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            if img_desc and c_img:
                with c_img:
                    _show_image(img_desc)
            st.markdown('')

        if st.button('Refresh', key='refresh_vision_submit'):
            st.cache_data.clear()
            st.rerun()

# ── Vote ───────────────────────────────────────────────────────────────────────

with tab_vote:
    if 'voted_vision' not in st.session_state:
        st.session_state['voted_vision'] = set()

    subs  = pull_submissions()
    votes = pull_votes()

    if subs.empty:
        st.info('No submissions yet. Be the first to add your cover story in the Submit tab.')
    else:
        st.markdown('#### Upvote the answers that resonate most')
        st.caption('Vote for the headlines, story lines, quotes, and bottom lines that feel most true to where Audeara is headed.')
        c_ref, _ = st.columns([1, 6])
        with c_ref:
            if st.button('Refresh', key='refresh_vision_vote'):
                st.cache_data.clear()
                st.rerun()

        def _count(col_key, answer):
            if votes.empty:
                return 0
            match = votes[
                (votes['Category'] == col_key) &
                (votes['Answer'].str.strip().str.lower() == answer.lower())
            ]
            return int(match.iloc[0]['Votes']) if not match.empty else 0

        for col_key, col_label in CATEGORIES:
            st.markdown(f'<div class="category-header">{col_label}</div>', unsafe_allow_html=True)
            unique = list(dict.fromkeys(
                a.strip() for a in subs[col_key].fillna('').tolist() if a.strip()
            ))
            unique = sorted(unique, key=lambda a: _count(col_key, a), reverse=True)

            if not unique:
                st.caption('No answers submitted for this category yet.')
                continue

            for i, answer in enumerate(unique):
                count         = _count(col_key, answer)
                vote_key      = f'vision::{col_key}::{answer}'
                already_voted = vote_key in st.session_state['voted_vision']

                if col_key == 'Image':
                    # Show the generated image above the vote row
                    img_col, _ = st.columns([2, 1])
                    with img_col:
                        _show_image(answer)
                    a_col, b_col = st.columns([7, 1])
                else:
                    a_col, b_col = st.columns([7, 1])

                with a_col:
                    st.markdown(
                        f'<div class="answer-row">{answer}'
                        f'<span class="vote-count"> &nbsp;·&nbsp; {count} vote{"s" if count != 1 else ""}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with b_col:
                    if st.button('✓' if already_voted else '▲',
                                 key=f'vote_vision_{col_key}_{i}',
                                 disabled=already_voted,
                                 use_container_width=True):
                        try:
                            upsert_vote(col_key, answer)
                            st.session_state['voted_vision'].add(vote_key)
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as _e:
                            st.error(f'Vote not saved — network issue. Please try again. ({_e})')
            st.markdown('')

# ── Results ────────────────────────────────────────────────────────────────────

with tab_results:
    votes = pull_votes()
    subs  = pull_submissions()
    c_ref2, _ = st.columns([1, 6])
    with c_ref2:
        if st.button('Refresh', key='refresh_vision_results'):
            st.cache_data.clear()
            st.rerun()

    if subs.empty:
        st.info('No submissions yet. Head to the Submit tab to add your cover story.')
    else:
        top = {}
        if not votes.empty:
            for col_key, _ in CATEGORIES:
                cat_votes = votes[votes['Category'] == col_key].copy()
                if not cat_votes.empty:
                    best = cat_votes.sort_values('Votes', ascending=False).iloc[0]
                    top[col_key] = (best['Answer'], int(best['Votes']))

        has_votes = bool(top)

        def _top_or_first(col_key, col_name):
            if col_key in top:
                return top[col_key][0]
            vals = subs[col_name].fillna('').tolist() if col_name in subs.columns else []
            return next((v.strip() for v in vals if v.strip()), '')

        headline_val = _top_or_first('Headline',    'Headline')
        story_val    = _top_or_first('The Story',   'The Story')
        quote_val    = _top_or_first('Quote',       'Quote')
        bottom_val   = _top_or_first('Bottom Line', 'Bottom Line')
        pub_val      = subs['Publication'].fillna('').iloc[0].strip() if 'Publication' in subs.columns else ''

        # Cover image: use the top-voted image description, fall back to first submission with one
        cover_img_desc = ''
        if 'Image' in top:
            cover_img_desc = top['Image'][0]
        elif 'Image' in subs.columns:
            cover_img_desc = next(
                (v.strip() for v in subs['Image'].fillna('').tolist() if v.strip()), ''
            )

        st.markdown('#### The cover story so far')
        if not has_votes:
            st.caption('No votes yet — showing the first submission. Head to Vote to start shaping the result.')

        col_img, col_cover = st.columns([1, 1], gap='large')

        with col_img:
            if cover_img_desc:
                _show_image(cover_img_desc, caption=f'Cover image · {COVER_YEAR}')
            else:
                st.markdown(
                    f'<div style="background:#1a1a2e;border-radius:10px;height:340px;'
                    f'display:flex;align-items:center;justify-content:center;'
                    f'color:#555;font-size:0.88em;text-align:center;padding:24px;">'
                    f'Add an image description in your submission<br>and it will appear here.'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        with col_cover:
            pub_display = pub_val or 'Audeara · Cover Story'
            st.markdown(
                f'<div class="magazine-cover">'
                f'<div class="mag-pub">{pub_display}</div>'
                f'<div class="mag-year">It\'s {COVER_YEAR}.</div>'
                f'<div class="mag-headline">{headline_val or "<em style=color:#555>Headline coming soon</em>"}</div>'
                f'{"<div class=mag-story>" + story_val + "</div>" if story_val else ""}'
                f'{"<div class=mag-quote>" + quote_val + "</div>" if quote_val else ""}'
                f'{"<div class=mag-bl-label>The Bottom Line</div><div class=mag-bottom-text>" + bottom_val + "</div>" if bottom_val else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )

            if has_votes:
                st.markdown('**Votes by category**')
                for col_key, col_label in CATEGORIES:
                    if col_key in top:
                        _, count = top[col_key]
                        c1, c2 = st.columns([5, 1])
                        with c1:
                            st.markdown(f'_{col_label}_')
                        with c2:
                            st.write(f'**{count}**')

        # ── Assemble Cover ─────────────────────────────────────────────────────
        st.divider()
        st.markdown('#### Assemble the magazine cover')
        st.caption('Puts all the winning pieces together — publication, headline, quote, bottom line, and image — into a proper magazine cover.')

        if st.button('🎨 Generate Magazine Cover', type='primary'):
            st.session_state['assembled_cover'] = True

        if st.session_state.get('assembled_cover'):
            cover_img_bytes = None
            if cover_img_desc:
                cached = st.session_state.get(_img_cache_key(cover_img_desc))
                if isinstance(cached, bytes):
                    cover_img_bytes = cached
                else:
                    with st.spinner('Generating cover image first…'):
                        result = generate_cover_image(cover_img_desc)
                        cover_img_bytes = result if isinstance(result, bytes) else None

            components.html(
                build_cover_html(pub_val, headline_val, quote_val, bottom_val, cover_img_bytes),
                height=622,
            )

            if cover_img_bytes:
                composed_key = f'composed_cover_{hashlib.md5((headline_val + quote_val + bottom_val).encode()).hexdigest()}'
                if composed_key not in st.session_state:
                    with st.spinner('Saving composed cover to Drive…'):
                        try:
                            composed = _compose_cover_image(pub_val, headline_val, quote_val, bottom_val, cover_img_bytes)
                            _save_composed_to_drive(headline_val, composed)
                            st.session_state[composed_key] = composed
                            st.toast('Cover saved to Drive ✓', icon='✅')
                        except Exception as _e:
                            st.session_state[composed_key] = None
                composed = st.session_state.get(composed_key)
                if isinstance(composed, bytes):
                    st.download_button(
                        label='⬇ Download composed cover (PNG)',
                        data=composed,
                        file_name=f'audeara-cover-{COVER_YEAR}.png',
                        mime='image/png',
                        key='dl_composed_results',
                    )

# ── Facilitate ─────────────────────────────────────────────────────────────────

with tab_facilitate:
    if 'facilitate_auth' not in st.session_state:
        st.session_state['facilitate_auth'] = False

    if not st.session_state['facilitate_auth']:
        st.markdown('#### Facilitator access')
        st.caption('This tab is for the session facilitator only.')
        pwd_input = st.text_input('Password', type='password', key='facilitate_pwd_input')
        if st.button('Unlock', type='primary', key='facilitate_unlock'):
            correct = st.secrets.get('FACILITATE_PASSWORD', 'audeara2030')
            if pwd_input == correct:
                st.session_state['facilitate_auth'] = True
                st.rerun()
            else:
                st.error('Incorrect password.')
    else:
        if st.button('🔒 Lock', key='facilitate_lock'):
            st.session_state['facilitate_auth'] = False
            st.rerun()

        fac_subs  = pull_submissions()
        fac_votes = pull_votes()

        if fac_subs.empty:
            st.info('No submissions yet.')
        else:
            # ── Vote adjustment ──────────────────────────────────────────────
            st.markdown('#### Adjust votes')
            st.caption('Override any vote count directly. Changes update the sheet immediately and are reflected in the Results tab.')

            c_ref, _ = st.columns([1, 5])
            with c_ref:
                if st.button('Refresh', key='fac_refresh'):
                    st.cache_data.clear()
                    st.rerun()

            def _current_count(col_key, answer):
                if fac_votes.empty:
                    return 0
                m = fac_votes[
                    (fac_votes['Category'] == col_key) &
                    (fac_votes['Answer'].str.strip().str.lower() == answer.lower())
                ]
                return int(m.iloc[0]['Votes']) if not m.empty else 0

            for col_key, col_label in CATEGORIES:
                st.markdown(f'<div class="category-header">{col_label}</div>', unsafe_allow_html=True)
                unique = list(dict.fromkeys(
                    a.strip() for a in fac_subs[col_key].fillna('').tolist() if a.strip()
                ))
                if not unique:
                    st.caption('No answers submitted yet.')
                    continue

                for answer in unique:
                    cur = _current_count(col_key, answer)
                    key_slug = hashlib.md5(f'{col_key}:{answer}'.encode()).hexdigest()[:10]
                    a_col, b_col, c_col = st.columns([5, 1, 1])
                    with a_col:
                        st.markdown(
                            f'<div class="answer-row">{answer}</div>',
                            unsafe_allow_html=True,
                        )
                    with b_col:
                        new_val = st.number_input(
                            'Votes', min_value=0, value=cur,
                            key=f'fac_ni_{key_slug}',
                            label_visibility='collapsed',
                        )
                    with c_col:
                        if st.button('Save', key=f'fac_sv_{key_slug}'):
                            try:
                                set_vote_count(col_key, answer, int(new_val))
                                st.cache_data.clear()
                                st.toast(f'Saved — {col_label}: {int(new_val)} votes', icon='✅')
                                st.rerun()
                            except Exception as _e:
                                st.error(f'Could not save. ({_e})')
                st.markdown('')

            st.divider()

            # ── Build cover versions ─────────────────────────────────────────
            st.markdown('#### Build cover versions')
            st.caption('Mix and match any submitted answers to preview different cover combinations. Images are generated once and cached.')

            def _col_options(col_name):
                return ['(none)'] + list(dict.fromkeys(
                    v.strip() for v in fac_subs[col_name].fillna('').tolist() if v.strip()
                ))

            for version in ['A', 'B']:
                with st.expander(f'Version {version}', expanded=(version == 'A')):
                    v_pub = st.selectbox('Publication',  _col_options('Publication'),  key=f'fac_pub_{version}')
                    v_hl  = st.selectbox('Headline',     _col_options('Headline'),     key=f'fac_hl_{version}')
                    v_qt  = st.selectbox('Quote',        _col_options('Quote'),        key=f'fac_qt_{version}')
                    v_bl  = st.selectbox('Bottom Line',  _col_options('Bottom Line'),  key=f'fac_bl_{version}')
                    v_img = st.selectbox('Cover image',  _col_options('Image'),        key=f'fac_img_{version}')

                    if st.button(f'Preview Version {version}', type='primary', key=f'fac_preview_{version}'):
                        st.session_state[f'fac_cover_{version}'] = {
                            'pub': '' if v_pub == '(none)' else v_pub,
                            'hl':  '' if v_hl  == '(none)' else v_hl,
                            'qt':  '' if v_qt  == '(none)' else v_qt,
                            'bl':  '' if v_bl  == '(none)' else v_bl,
                            'img': '' if v_img == '(none)' else v_img,
                        }

                    cover_state = st.session_state.get(f'fac_cover_{version}')
                    if cover_state:
                        v_img_bytes = None
                        if cover_state['img']:
                            cached = st.session_state.get(_img_cache_key(cover_state['img']))
                            if isinstance(cached, bytes):
                                v_img_bytes = cached
                            else:
                                with st.spinner('Generating image…'):
                                    result = generate_cover_image(cover_state['img'])
                                    v_img_bytes = result if isinstance(result, bytes) else None

                        components.html(
                            build_cover_html(
                                cover_state['pub'], cover_state['hl'],
                                cover_state['qt'],  cover_state['bl'], v_img_bytes,
                            ),
                            height=622,
                        )

                        if v_img_bytes:
                            vc_key = f'fac_composed_{version}_{hashlib.md5((cover_state["hl"] + cover_state["qt"] + cover_state["bl"]).encode()).hexdigest()}'
                            if vc_key not in st.session_state:
                                with st.spinner(f'Saving Version {version} to Drive…'):
                                    try:
                                        vc = _compose_cover_image(
                                            cover_state['pub'], cover_state['hl'],
                                            cover_state['qt'],  cover_state['bl'], v_img_bytes,
                                        )
                                        _save_composed_to_drive(f"{cover_state['hl']}-v{version}", vc)
                                        st.session_state[vc_key] = vc
                                        st.toast(f'Version {version} saved to Drive ✓', icon='✅')
                                    except Exception as _e:
                                        st.session_state[vc_key] = None
                            vc = st.session_state.get(vc_key)
                            if isinstance(vc, bytes):
                                st.download_button(
                                    label=f'⬇ Download Version {version} (PNG)',
                                    data=vc,
                                    file_name=f'audeara-cover-{COVER_YEAR}-v{version.lower()}.png',
                                    mime='image/png',
                                    key=f'fac_dl_{version}',
                                )
