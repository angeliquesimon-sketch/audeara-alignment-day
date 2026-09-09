#!/usr/bin/env python3
"""
Badge style mockup — compares three treatments for showing Different Styles
results on organogram name cards.
Run: python3 preview_badge.py
"""

import webbrowser

DARK  = '#50144B'
LIGHT = '#F9F9F9'

STYLES = [
    ('Red',    '#E84040', '#FFFFFF'),
    ('Blue',   '#4285C8', '#FFFFFF'),
    ('Yellow', '#F5A623', '#1A1A1A'),
    ('Green',  '#3EAA6D', '#FFFFFF'),
]

BW, BH   = 104, 42   # box width / height
GAP      = 20        # horizontal gap between boxes
LEFT_LBL = 148       # x where boxes start
ROW_H    = 96        # vertical space per option row
TOP_PAD  = 36
STRIPE_H = 5         # height of bottom stripe

OPTIONS = [
    'C  —  Left dot',
    'Stripe  —  Bottom edge',
    'Fill  —  Full box',
]

W = LEFT_LBL + len(STYLES) * (BW + GAP) + 24
H = TOP_PAD + len(OPTIONS) * ROW_H + 24

L = []; a = L.append

a(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
  f'style="width:100%;max-width:{W}px;font-family:sans-serif;">')
a(f'<rect width="{W}" height="{H}" fill="#F0F0F0"/>')

# ── Drawing helpers ────────────────────────────────────────────────────────────

def _base_box(bx, by, fill, stroke, rx=7):
    a(f'<rect x="{bx}" y="{by}" width="{BW}" height="{BH}" rx="{rx}" '
      f'fill="{fill}" stroke="{stroke}" stroke-width="0.8"/>')

def _name_title(cx, by, name_col, title_col):
    mid = by + BH // 2
    a(f'<text x="{cx}" y="{mid-4}" text-anchor="middle" '
      f'font-size="9.5" font-weight="700" fill="{name_col}">Alex Bartlett</text>')
    a(f'<text x="{cx}" y="{mid+8}" text-anchor="middle" '
      f'font-size="7" fill="{title_col}">Firmware Engineer</text>')

def _name_title_offset(bx, by, name_col, title_col, x_offset=26):
    mid = by + BH // 2
    tx  = bx + x_offset
    a(f'<text x="{tx}" y="{mid-4}" text-anchor="start" '
      f'font-size="9" font-weight="700" fill="{name_col}">Alex Bartlett</text>')
    a(f'<text x="{tx}" y="{mid+8}" text-anchor="start" '
      f'font-size="6.5" fill="{title_col}">Firmware Engineer</text>')

# ── Option renderers ───────────────────────────────────────────────────────────

def draw_left_dot(cx, by, style_hex, style_text):
    bx = cx - BW // 2
    _base_box(bx, by, LIGHT, DARK)
    dot_cx = bx + 15
    dot_cy = by + BH // 2
    a(f'<circle cx="{dot_cx}" cy="{dot_cy}" r="7" fill="{style_hex}"/>')
    _name_title_offset(bx, by, '#1A1A1A', '#555555', x_offset=28)

def draw_stripe(cx, by, style_hex, style_text):
    bx = cx - BW // 2
    # base box with clip path so stripe respects border radius
    clip_id = f'clip_{cx}_{by}'
    a(f'<clipPath id="{clip_id}">'
      f'<rect x="{bx}" y="{by}" width="{BW}" height="{BH}" rx="7"/>'
      f'</clipPath>')
    _base_box(bx, by, LIGHT, DARK)
    a(f'<rect x="{bx}" y="{by + BH - STRIPE_H}" width="{BW}" height="{STRIPE_H}" '
      f'fill="{style_hex}" clip-path="url(#{clip_id})"/>')
    _name_title(cx, by, '#1A1A1A', '#555555')

def draw_fill(cx, by, style_hex, style_text):
    bx = cx - BW // 2
    _base_box(bx, by, style_hex, style_hex)
    _name_title(cx, by, style_text, style_text)

RENDERERS = [draw_left_dot, draw_stripe, draw_fill]

# ── Render rows ────────────────────────────────────────────────────────────────

for row_i, (opt_label, renderer) in enumerate(zip(OPTIONS, RENDERERS)):
    ry = TOP_PAD + row_i * ROW_H

    a(f'<text x="10" y="{ry + BH//2 + 4}" font-size="11" font-weight="700" '
      f'fill="#50144B">{opt_label}</text>')

    for col_i, (style_name, style_hex, style_text) in enumerate(STYLES):
        cx = LEFT_LBL + col_i * (BW + GAP) + BW // 2
        renderer(cx, ry, style_hex, style_text)

        if row_i == 0:
            a(f'<text x="{cx}" y="{ry - 10}" text-anchor="middle" '
              f'font-size="9" font-weight="700" fill="{style_hex}">{style_name}</text>')

a('</svg>')
svg = '\n'.join(L)

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Style Treatment Mockup</title>
<style>
  body {{ margin: 48px; background: #fff; }}
  h2   {{ font-family: sans-serif; font-size: 11px; font-weight: 700;
          letter-spacing: 2px; color: #AAAAAA; margin-bottom: 28px; }}
</style>
</head><body>
<h2>STYLE TREATMENT OPTIONS — DIFFERENT STYLES × ORGANOGRAM</h2>
{svg}
</body></html>"""

out = '/tmp/badge_mockup.html'
open(out, 'w').write(html)
webbrowser.open(f'file://{out}')
print(f'Opened {out}')
