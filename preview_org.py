#!/usr/bin/env python3
"""
Organogram preview — no Streamlit needed.

Usage:
    python3 preview_org.py           # render once and open in browser
    python3 preview_org.py --watch   # auto-regenerate on every file save
                                     # browser page auto-refreshes every second
"""

import ast, os, sys, time, webbrowser

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'activities', 'overview.py')
OUT = '/tmp/org_preview.html'

WATCH = '--watch' in sys.argv

# Placeholder style colours — swap these out when real data is wired in.
# Keys must match the name strings used in the SVG box calls exactly.
PLACEHOLDER_STYLES = {
    'James Fielding':   '#4285C8',  # Blue
    'Bill Peng':        '#E84040',  # Red
    'John Krajewski':   '#F5A623',  # Yellow
    'Louise Heller':    '#3EAA6D',  # Green
    'Andrew Morton':    '#4285C8',  # Blue
    'Rebekah Davidson': '#3EAA6D',  # Green
    'Angelique Simon':  '#F5A623',  # Yellow
    'Robert Poulsen':   '#3EAA6D',  # Green
    'Misaki Kawashima': '#E84040',  # Red
    "Dr Ian O'Brien":   '#4285C8',  # Blue
    'Alex Bartlett':    '#E84040',  # Red
    'Dylan Whitehouse': '#F5A623',  # Yellow
    'Bonar Dickson':    '#4285C8',  # Blue
    'Ellissa Waters':   '#3EAA6D',  # Green
    'Charli Every':     '#F5A623',  # Yellow
    'Sayaka Smith':     '#E84040',  # Red
}


def render():
    src = open(SRC).read()
    tree = ast.parse(src)
    fn_src = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == '_org_svg':
            lines = src.splitlines()
            fn_src = '\n'.join(lines[node.lineno - 1: node.end_lineno])
            break
    if fn_src is None:
        print('ERROR: _org_svg() not found in overview.py')
        return False
    ns = {}
    exec(fn_src, ns)          # executes only the pure SVG function — no Streamlit
    svg = ns['_org_svg'](PLACEHOLDER_STYLES)

    refresh = '<meta http-equiv="refresh" content="1">' if WATCH else ''
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  {refresh}
  <title>Org Chart Preview</title>
  <style>
    body {{ margin: 48px; background: #fff; }}
    .label {{ font-family: sans-serif; font-size: 11px; font-weight: 700;
               letter-spacing: 2px; color: #AAAAAA; margin-bottom: 16px; }}
  </style>
</head>
<body>
  <div class="label">ORG CHART PREVIEW — edit activities/overview.py and save</div>
  {svg}
</body>
</html>"""
    open(OUT, 'w').write(html)
    return True


if WATCH:
    mtime = 0
    print(f'Watching {SRC}')
    print(f'Browser will auto-refresh every second. Ctrl+C to stop.\n')
    opened = False
    while True:
        try:
            mt = os.path.getmtime(SRC)
        except FileNotFoundError:
            time.sleep(0.5)
            continue
        if mt != mtime:
            mtime = mt
            if render():
                ts = time.strftime('%H:%M:%S')
                print(f'[{ts}] Regenerated')
                if not opened:
                    webbrowser.open(f'file://{OUT}')
                    opened = True
        time.sleep(0.5)
else:
    if render():
        webbrowser.open(f'file://{OUT}')
        print(f'Opened {OUT}')
        print('Re-run to refresh, or use --watch for live updates.')
