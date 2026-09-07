"""Strategy Cascade — participant page."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from utils import inject_styles, PURPLE, TEAL, with_retry, _clear_sheets
from strategy_cascade_shared import (
    ENGINES, OPERATING_SYSTEM, CHOICES, HOW_WE_WORK, DEPARTMENTS,
    CHOICE_COLOURS, ENGINE_COLOURS,
    _ensure_cascade_tabs,
    pull_cascade_session, pull_cascade_contributions, save_cascade_contribution,
    pull_cascade_confidence, save_cascade_confidence,
)
from one_thing_shared import pull_one_thing_winners

inject_styles()

FOREST = '#005E63'
WINE   = '#50144B'
BLACK  = '#000000'

if not st.session_state.get('_cascade_tabs_ready'):
    try:
        with_retry(_ensure_cascade_tabs, on_retry=_clear_sheets)
        st.session_state['_cascade_tabs_ready'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue — some features may not save correctly. ({_e})')

st.markdown('### Strategy Cascade')

# ── Stage gate (outside tabs — always polling) ─────────────────────────────────

@st.fragment(run_every=5)
def _stage_gate():
    pull_cascade_session.clear()
    sess = pull_cascade_session()
    sig  = f'{sess.get("stage","hidden")}_{sess.get("current_choice","0")}_{sess.get("confidence_open","0")}'
    if sig != st.session_state.get('_casc_sig_last'):
        st.session_state['_casc_sig_last'] = sig
        st.rerun()

_stage_gate()

session   = pull_cascade_session()
stage     = session.get('stage', 'hidden')
cur_idx   = int(session.get('current_choice', 0))
conf_open = session.get('confidence_open', '0') == '1'

STAGE_ORDER = ['hidden', 'engines', 'choices', 'working', 'cascade', 'reveal']
stage_idx   = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 0

# ── Helpers ────────────────────────────────────────────────────────────────────

def _waiting(msg='This will open shortly.'):
    st.markdown(
        f'<div style="background:#F5F5F5;border-radius:10px;padding:32px;'
        f'text-align:center;color:#AAAAAA;font-size:0.95em;margin-top:8px;">⏳  {msg}</div>',
        unsafe_allow_html=True,
    )

def _section_label(text):
    st.markdown(
        f'<div style="font-size:0.84em;font-weight:700;letter-spacing:2px;'
        f'color:#888;margin-bottom:16px;">{text}</div>',
        unsafe_allow_html=True,
    )

def _collapsed_engines():
    pills = ''.join([
        f'<span style="background:{FOREST};color:white;font-size:0.84em;'
        f'font-weight:600;padding:4px 11px;border-radius:14px;margin-right:6px;'
        f'display:inline-block;margin-bottom:5px;">{e["title"]}</span>'
        for i, e in enumerate(ENGINES)
    ])
    st.markdown(
        f'<div style="background:#F4F4F4;border-radius:8px;padding:10px 14px;margin-bottom:10px;">'
        f'<div style="font-size:0.75em;font-weight:700;color:#AAAAAA;letter-spacing:1.5px;'
        f'margin-bottom:8px;">COMMERCIAL ENGINES</div>'
        f'{pills}</div>',
        unsafe_allow_html=True,
    )

def _collapsed_choices():
    _lookup = {c['id']: c for c in CHOICES}
    _order  = [_lookup[i] for i in ['c2','c3','c4','c7','c1','c5','c6']]
    pills = ''.join([
        f'<span style="background:{WINE};color:white;font-size:0.84em;'
        f'font-weight:600;padding:4px 11px;border-radius:14px;margin-right:6px;'
        f'display:inline-block;margin-bottom:5px;">{c["title"]}</span>'
        for c in _order
    ])
    st.markdown(
        f'<div style="background:#F4F4F4;border-radius:8px;padding:10px 14px;margin-bottom:10px;">'
        f'<div style="font-size:0.75em;font-weight:700;color:#AAAAAA;letter-spacing:1.5px;'
        f'margin-bottom:8px;">FY27 STRATEGIC CHOICES</div>'
        f'{pills}</div>',
        unsafe_allow_html=True,
    )

def _collapsed_working():
    pills = ''.join([
        f'<span style="background:{WINE};color:white;'
        f'font-size:0.84em;font-weight:600;padding:4px 11px;border-radius:14px;'
        f'margin-right:6px;display:inline-block;margin-bottom:5px;">{principle}</span>'
        for i, (principle, _) in enumerate(HOW_WE_WORK)
    ])
    st.markdown(
        f'<div style="background:#F4F4F4;border-radius:8px;padding:10px 14px;margin-bottom:10px;">'
        f'<div style="font-size:0.75em;font-weight:700;color:#AAAAAA;letter-spacing:1.5px;'
        f'margin-bottom:8px;">HOW WE WILL WORK</div>'
        f'{pills}</div>',
        unsafe_allow_html=True,
    )

# ── Two tabs ───────────────────────────────────────────────────────────────────

tab_pres, tab_activity, tab_results = st.tabs(['📊 Presentation', '💬 Activity', '📋 Results'])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PRESENTATION  (cumulative cascade — each layer collapses as the next opens)
# ═══════════════════════════════════════════════════════════════════════════════

with tab_pres:

    if stage == 'hidden':
        _waiting('James will open this session shortly.')

    else:
        # Tab 1 never collapses — it is a permanent record of the full presentation

        # ENGINES ── show from stage_idx 1 onwards
        if stage_idx >= 1:
            _section_label('Commercial Engines')
            _engine_cards = ''.join([
                f'<div style="border-left:4px solid {FOREST};background:#F8F8F8;'
                f'border-radius:0 6px 6px 0;padding:14px 16px;">'
                f'<div style="font-weight:700;font-size:1.05em;color:{FOREST};margin-bottom:2px;">{e["title"]}</div>'
                f'<div style="font-size:0.75em;color:#999;font-style:italic;margin-bottom:6px;">{e["subtitle"]}</div>'
                f'<div style="font-size:0.95em;color:#555;line-height:1.55;">{e["description"]}</div>'
                f'</div>'
                for e in ENGINES
            ])
            _OS_ICONS = ['🔬', '🛡️', '⚡', '🤝', '🎯']
            _os_pills = ''.join([
                f'<span style="background:rgba(255,255,255,0.15);color:white;font-size:0.95em;'
                f'font-weight:500;padding:6px 13px;border-radius:20px;'
                f'display:inline-flex;align-items:center;gap:5px;margin:3px;">'
                f'{icon}&nbsp;{item}</span>'
                for icon, item in zip(_OS_ICONS, OPERATING_SYSTEM)
            ])
            st.markdown(
                f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;'
                f'gap:8px;margin-bottom:0;">'
                f'{_engine_cards}'
                f'</div>'
                f'<div style="background:{FOREST};border-radius:0 0 10px 10px;'
                f'padding:16px 20px;margin-top:8px;">'
                f'<div style="font-size:0.75em;font-weight:700;color:rgba(255,255,255,0.5);'
                f'letter-spacing:1.5px;margin-bottom:10px;">ONE COMPANY OPERATING SYSTEM</div>'
                f'<div style="display:flex;flex-wrap:wrap;">{_os_pills}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── Engine detail accordions ──────────────────────────────────────
            _ENGINE_DETAIL = {
                'wholesale': {
                    'intro': (
                        'Australian Wholesale is our most established commercial engine — the foundation of '
                        'Audeara\'s revenue and our closest connection to clinicians and customers. '
                        'We\'re not building the network anymore. We\'re deepening it.'
                    ),
                    'sections': [
                        ('What we do for clinics', [
                            'We give clinics an additional revenue stream and a solution for the 35% of patients who leave without hearing aids.',
                            'Audeara bridges the gap between "not ready for hearing aids" and the full clinical relationship.',
                            'Clinicians get products they can confidently recommend — premium, evidence-backed, and easy to demonstrate.',
                        ]),
                        ('Where we are', [
                            '1,500+ clinics across Australia. Stocked in 12 countries.',
                            'The network is established. FY27 is about account depth, repeat ordering, and fewer one-off purchases.',
                            'Major global audiology chain relationships in place.',
                        ]),
                        ('Key channels', [
                            'Australian audiology clinics — major chains and independents.',
                            'International: EU and US (global chains), Japan (growing), Taiwan (Clinico partnership).',
                            'NDIS and e-commerce.',
                        ]),
                        ('FY27 priorities', [
                            'Account depth and repeat ordering.',
                            'Onboard and enable the expanded field team, including incoming Clinical Business Managers.',
                            'Make ordering, training and support simpler and more dependable.',
                            'Strengthen clinician feedback loops across sales, operations, marketing and product teams.',
                        ]),
                    ],
                },
                'aua_tech': {
                    'intro': (
                        'AUA Technology turns Audeara\'s proprietary hearing and audio capability into partner products, '
                        'embedded platforms and repeatable licensing revenue. It\'s our highest-margin division and our '
                        'clearest path to sustainable profitability. $1.68m in FY26, up 50% year on year.'
                    ),
                    'sections': [
                        ('How it works', [
                            'We provide engineering services, white-label products and algorithm licensing to global partners.',
                            'Revenue comes from three streams: engineering fees, product licensing, and white-label supply.',
                            'Higher margin than hardware, and it scales without proportional cost.',
                        ]),
                        ('Partners in market', [
                            'Zildjian — Perfect Tune headphones, global distribution, multiple shipments.',
                            'Eastech / China — NMPA-certified hearing aids, live on Tmall, JD.com and Pinduoduo.',
                            'Clinico / Taiwan — white-label earbuds plus an expanding Auracast product range.',
                            'Optek — AI algorithm licensing embedded into audio chipsets used across global consumer electronics.',
                        ]),
                        ('Pipeline and discipline', [
                            'Additional partner programs progressing, including Rion.',
                            'Disciplined portfolio decisions using the seven-gate framework — fund based on readiness and strategic value.',
                            'Reusable capability built once and deployed across multiple partners.',
                        ]),
                        ('FY27 priorities', [
                            'Progress development programs to production revenue and repeat orders.',
                            'Build reusable AUAI module capability rather than one-off engineering.',
                            'Expand the partner pipeline with disciplined selection.',
                        ]),
                    ],
                },
                'auracast': {
                    'intro': (
                        'Auracast is how we move beyond the clinic. It\'s a solutions business for venues and institutions — '
                        'shared listening infrastructure that works for everyone in the room, not just hearing aid wearers.'
                    ),
                    'sections': [
                        ('What it is', [
                            'Auracast is a Bluetooth standard that replaces traditional hearing loops.',
                            'One transmitter broadcasts to an unlimited number of compatible devices simultaneously.',
                            'Easier to deploy, lower cost, better audio quality — and it benefits people of all hearing abilities, not just those with hearing loss.',
                        ]),
                        ('Early wins', [
                            'University of Queensland — classroom and lecture deployment.',
                            'Bolton Clarke aged care — our reference case for a repeatable, supportable deployment.',
                            'These prove the model works in real environments with real users.',
                        ]),
                        ('Priority environments', [
                            'Senior living and care.',
                            'Universities, classrooms and education.',
                            'Healthcare and clinical settings.',
                            'Public venues, events and AV partner-led installations.',
                        ]),
                        ('FY27 priorities', [
                            'Formalise the deployment offer, delivery playbook and partner model.',
                            'Convert the Bolton Clarke learning into a repeatable solution package.',
                            'Build a qualified pipeline of environments for AV sector distribution.',
                            'Grow Japan and Clinico Taiwan channels as the Auracast product range expands.',
                        ]),
                    ],
                },
                'shokzhear': {
                    'intro': (
                        'Listen & Learn is how Audeara makes an impact. It\'s a partner-funded program that gets assistive '
                        'listening technology to children who need it — in schools and community settings — through a model '
                        'that doesn\'t depend on clinical channels or individual purchasing.'
                    ),
                    'sections': [
                        ('The program', [
                            'Three groups work together: Audeara (program founder and device provider), community delivery partners (charities and organisations who identify children, distribute devices and report impact), and funding partners (who provide financial support in exchange for impact reporting).',
                            'The three-party model removes the individual purchasing barrier and lowers customer acquisition cost.',
                        ]),
                        ('The product', [
                            'OpenLearn Small by ShokzHear.',
                            'Audeara sets the functionality, size and audio-tuning requirements.',
                            'ShokzHear customises and manufactures.',
                            'Audeara holds exclusive Australian deployment rights.',
                        ]),
                        ('Path to scale', [
                            'Schools and education systems.',
                            'State and national programs.',
                            'Charities, grants and community delivery partners.',
                            'Institutional and community-led reach — sustainable without a clinical intermediary.',
                        ]),
                        ('FY27 priorities', [
                            'Initial customer orders.',
                            'First funded deployments.',
                            'Measurable evidence of impact.',
                            'A repeatable partner model that can be replicated across new delivery partners.',
                        ]),
                    ],
                },
            }

            st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
            for _e in ENGINES:
                _edetail = _ENGINE_DETAIL.get(_e['id'])
                if not _edetail:
                    continue
                with st.expander(_e['title'], expanded=False):
                    if _edetail.get('intro'):
                        st.markdown(
                            f'<div style="font-size:0.95em;color:#555;font-style:italic;'
                            f'line-height:1.6;margin-bottom:14px;">{_edetail["intro"]}</div>',
                            unsafe_allow_html=True,
                        )
                    for _sec_title, _sec_content in _edetail['sections']:
                        st.markdown(
                            f'<div style="font-size:0.84em;font-weight:700;color:{FOREST};'
                            f'letter-spacing:1px;margin-top:12px;margin-bottom:5px;">'
                            f'{_sec_title.upper()}</div>',
                            unsafe_allow_html=True,
                        )
                        if isinstance(_sec_content, list):
                            _items = ''.join([
                                f'<li style="margin-bottom:4px;">{item}</li>'
                                for item in _sec_content
                            ])
                            st.markdown(
                                f'<ul style="font-size:0.95em;color:#333;line-height:1.6;'
                                f'margin:0;padding-left:18px;">{_items}</ul>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f'<div style="font-size:0.95em;color:#333;line-height:1.6;">'
                                f'{_sec_content}</div>',
                                unsafe_allow_html=True,
                            )

        # CHOICES ── show from stage_idx 2 onwards
        if stage_idx >= 2:
            st.markdown('<div style="margin-top:28px;"></div>', unsafe_allow_html=True)
            _section_label('FY27 STRATEGIC CHOICES')
            _ENGINE_ATTRIBUTION = {
                'c2': 'Australian Wholesale',
                'c3': 'AUA Technology',
                'c4': 'Auracast Solutions',
                'c7': 'ShokzHear / OpenLearn',
            }
            _choice_lookup = {c['id']: c for c in CHOICES}
            _display_order = [
                _choice_lookup['c2'],
                _choice_lookup['c3'],
                _choice_lookup['c4'],
                _choice_lookup['c7'],
                _choice_lookup['c1'],
                _choice_lookup['c5'],
                _choice_lookup['c6'],
            ]
            _choice_cards = ''.join([
                f'<div style="border-left:4px solid {WINE};background:#F8F8F8;'
                f'border-radius:0 8px 8px 0;padding:14px 16px;">'
                f'<div style="font-weight:700;font-size:1.05em;color:#1a1a1a;margin-bottom:6px;">{c["title"]}</div>'
                + (
                    f'<div style="margin-bottom:8px;">'
                    f'<span style="background:{FOREST};color:white;font-size:0.75em;'
                    f'font-weight:600;padding:3px 9px;border-radius:10px;">'
                    f'{_ENGINE_ATTRIBUTION[c["id"]]}</span></div>'
                    if c['id'] in _ENGINE_ATTRIBUTION else ''
                ) +
                f'<div style="font-size:0.95em;color:#555;line-height:1.55;">{c["description"]}</div>'
                f'</div>'
                for c in _display_order
            ])
            st.markdown(
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);'
                f'gap:10px;">{_choice_cards}</div>',
                unsafe_allow_html=True,
            )

            # ── Detail accordions (collapsed by default — James opens as he speaks) ──
            _CHOICE_DETAIL = {
                'c2': {
                    'intro': 'Australian Wholesale is both a growth engine and our closest day-to-day learning loop with clinicians, partners and end users.',
                    'sections': [
                        ('What we will do', [
                            'Build on FY26 momentum through account depth, repeat ordering and a focused portfolio.',
                            'Onboard and enable the expanded field team, including the incoming Clinical Business Managers.',
                            'Make ordering, training, setup and support simpler and more dependable.',
                            'Strengthen feedback loops between clinicians, customer care, marketing, operations and product teams.',
                            'Use returns, support and sales data to remove recurring friction.',
                        ]),
                        ('Customer promise', 'Easy to understand. Easy to order. Easy to set up. Dependable when help is needed.'),
                    ],
                },
                'c3': {
                    'intro': 'AUA Technology turns Audeara\'s insight and engineering into capabilities that partners can deploy in products and platforms.',
                    'sections': [
                        ('Capability areas', [
                            'Hearing insight, audio intelligence and clinical translation.',
                            'Embedded systems, firmware, connectivity and device control.',
                            'Applications, fitting tools, diagnostics and service interfaces.',
                            'Platform implementation across supported chips, products and end-user environments.',
                            'Evidence, validation, quality and controlled release.',
                        ]),
                        ('In market and scaling', [
                            'A-02 TV Bundle and Audeara Buds.',
                            'BT-03, BT-LE and the expanding Auracast solution set.',
                            'Clinico and partner products moving toward repeatable revenue.',
                        ]),
                        ('Development and commercialisation', [
                            'A-03 in development.',
                            'OpenLearn Small by ShokzHear — initial orders and funded deployments.',
                            'OPTEK.',
                            'China hearing-aid programs.',
                            'Rion and other prioritised partner opportunities.',
                        ]),
                        ('Portfolio discipline', 'We will describe products and programs honestly, fund them according to readiness and strategic value, and avoid turning possibility into an unvalidated promise.'),
                    ],
                },
                'c4': {
                    'intro': 'Auracast is becoming a distinct solutions business: not a single device or feature, but a complete system designed around a real environment and the people in it.',
                    'sections': [
                        ('The solution chain', [
                            'Source — capture the right audio.',
                            'Broadcast — distribute it reliably.',
                            'Receive — connect compatible hearing and listening devices.',
                            'Personalise — deliver the best useful experience for each listener.',
                            'Deploy and support — make installation, training and ongoing use dependable.',
                        ]),
                        ('Priority environments', [
                            'Senior living and care.',
                            'Universities, classrooms and education.',
                            'Healthcare and clinical settings.',
                            'Public venues, events and partner-led installations.',
                        ]),
                        ('FY27 focus', 'The Bolton Clarke deployment gives us a reference point for turning technology into a repeatable, supportable solution. FY27 is about converting that learning into a clear offer, delivery playbook and partner model.'),
                    ],
                },
                'c7': {
                    'intro': 'A dedicated, partner-led commercial engine distinct from AUA Technology licensing and Auracast solutions.',
                    'sections': [
                        ('The product', 'OpenLearn Small by ShokzHear: Audeara sets functionality, size and audio-tuning requirements; ShokzHear customises and manufactures; Audeara holds exclusive Australian deployment rights.'),
                        ('Path to scale', 'Institutional and community-led: schools and education systems, state and national programs, charities, grants and delivery partners. The Listen & Learn Community Impact Program is the delivery framework.'),
                        ('FY27 focus', 'Initial customer orders, funded deployments, evidence of impact and a repeatable partner model.'),
                    ],
                },
                'c1': {
                    'intro': 'We start with the life being improved, not the feature being shipped.',
                    'sections': [
                        ('What this means in practice', [
                            'Product quality, setup, support, connectivity and follow-through are all part of the outcome.',
                            'Every function contributes to whether a customer\'s experience is good or not.',
                            'Returns, support data and clinical feedback are signals — not just costs.',
                        ]),
                    ],
                },
                'c5': {
                    'intro': 'The tender is exciting because it is a visible test of the company we are becoming. It is not a HALO project and it cannot be won by engineering, sales or leadership alone.',
                    'sections': [
                        ('Tender readiness is a whole-company capability', [
                            'A compelling, dependable product portfolio.',
                            'Clinical evidence and measurable customer outcomes.',
                            'Quality, regulatory and risk discipline.',
                            'National service, training, logistics and support.',
                            'Supply, customisation and production partnerships.',
                            'Financial capacity and working-capital planning.',
                            'A coherent story about why Audeara and its partners can deliver.',
                        ]),
                        ('How each group contributes', [
                            'Leadership: sets direction, makes trade-offs and creates internal and external cohesion.',
                            'Market, Growth and Australian Wholesale: create demand, build trusted relationships and translate market learning into opportunity.',
                            'Customer and Delivery: make promises real through operations, care, support, training and feedback.',
                            'Technology and Product: turn insight into safe, useful, scalable products and platforms.',
                            'Finance and Governance: protect sustainability, discipline, compliance and informed decision-making.',
                        ]),
                        ('Why it matters', 'Reaching the point where a tender is genuinely worth submitting will itself be an extraordinary achievement. It will show how far Audeara has progressed in one year.'),
                    ],
                },
                'c6': {
                    'intro': 'Opportunity is not the same as priority. FY27 requires deliberate trade-offs to protect cash and build what the strategy actually needs.',
                    'sections': [
                        ('What this means', [
                            'Make trade-offs visibly — the whole team knows what we are not doing and why.',
                            'Fund the work that best advances the strategy.',
                            'Stop work that no longer earns its place.',
                            'Revenue quality, gross margin, cash conversion and progress toward positive operating cash flow are the measures.',
                        ]),
                    ],
                },
            }

            st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
            for _c in _display_order:
                _detail = _CHOICE_DETAIL.get(_c['id'])
                if not _detail:
                    continue
                with st.expander(_c['title'], expanded=False):
                    if _detail.get('intro'):
                        st.markdown(
                            f'<div style="font-size:0.95em;color:#555;font-style:italic;'
                            f'line-height:1.6;margin-bottom:14px;">{_detail["intro"]}</div>',
                            unsafe_allow_html=True,
                        )
                    for _sec_title, _sec_content in _detail['sections']:
                        st.markdown(
                            f'<div style="font-size:0.84em;font-weight:700;color:{WINE};'
                            f'letter-spacing:1px;margin-top:12px;margin-bottom:5px;">'
                            f'{_sec_title.upper()}</div>',
                            unsafe_allow_html=True,
                        )
                        if isinstance(_sec_content, list):
                            _items = ''.join([
                                f'<li style="margin-bottom:4px;">{item}</li>'
                                for item in _sec_content
                            ])
                            st.markdown(
                                f'<ul style="font-size:0.95em;color:#333;line-height:1.6;'
                                f'margin:0;padding-left:18px;">{_items}</ul>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f'<div style="font-size:0.95em;color:#333;line-height:1.6;">'
                                f'{_sec_content}</div>',
                                unsafe_allow_html=True,
                            )

        # HOW WE WORK ── show from stage_idx 3 onwards
        if stage_idx >= 3:
            _HOW_ICONS = ['💡', '🤝', '✅', '🔬', '🔗', '🛡️', '🎯']
            _how_items = ''.join([
                f'<div style="background:rgba(255,255,255,0.1);border-radius:8px;padding:10px 14px;">'
                f'<div style="font-size:0.95em;font-weight:600;color:white;margin-bottom:4px;">'
                f'{icon}&nbsp;{principle}</div>'
                f'<div style="font-size:0.84em;color:rgba(255,255,255,0.65);line-height:1.5;">{description}</div>'
                f'</div>'
                for icon, (principle, description) in zip(_HOW_ICONS, HOW_WE_WORK)
            ])
            st.markdown(
                f'<div style="background:{WINE};border-radius:10px;padding:18px 20px;margin-top:28px;">'
                f'<div style="font-size:0.75em;font-weight:700;color:rgba(255,255,255,0.4);'
                f'letter-spacing:1.5px;margin-bottom:12px;">HOW WE WILL WORK</div>'
                f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">'
                f'{_how_items}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ACTIVITY / REVEAL
# ═══════════════════════════════════════════════════════════════════════════════

with tab_activity:

    if stage in ('hidden', 'engines', 'choices', 'working'):
        _waiting('The cascade discussion will open here when James is ready.')

    elif stage in ('cascade', 'reveal'):
        # Compact strategy reference — full detail stays on the Presentation tab
        _collapsed_engines()
        _collapsed_choices()
        _collapsed_working()
        st.markdown('<div style="margin-bottom:20px;"></div>', unsafe_allow_html=True)

    if stage == 'cascade':
        choice = CHOICES[min(cur_idx, len(CHOICES) - 1)]
        bc     = WINE

        st.markdown(
            f'<div style="border-left:4px solid {bc};background:#F8F8F8;'
            f'border-radius:0 8px 8px 0;padding:18px 22px;margin-bottom:20px;">'
            f'<div style="font-size:0.75em;font-weight:700;color:{bc};letter-spacing:1px;margin-bottom:4px;">'
            f'STRATEGIC CHOICE {choice["number"]} OF {len(CHOICES)}</div>'
            f'<div style="font-weight:700;font-size:1.05em;color:#1a1a1a;margin-bottom:8px;">{choice["title"]}</div>'
            f'<div style="font-size:0.95em;color:#555;line-height:1.6;">{choice["description"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        _section_label('HOW EACH FUNCTION CONTRIBUTES')

        @st.fragment(run_every=8)
        def _contributions():
            df       = pull_cascade_contributions()
            winners  = pull_one_thing_winners()

            for dept in DEPARTMENTS:
                status = 'none'
                text   = ''
                if not df.empty:
                    match = df[(df['ChoiceID'] == choice['id']) & (df['Department'] == dept)]
                    if not match.empty:
                        row    = match.iloc[0]
                        status = row['Status']
                        text   = row['Text']

                one_thing = winners.get(dept, '')

                # Department heading + One Thing reference
                ot_text = one_thing if one_thing else 'One Thing not yet agreed'
                ot_colour = '#777777' if one_thing else '#BBBBBB'
                ot_html = (
                    f'<div style="font-size:0.75em;color:{ot_colour};font-style:italic;'
                    f'margin-top:2px;margin-bottom:8px;">Our One Thing: {ot_text}</div>'
                )
                st.markdown(
                    f'<div style="font-size:0.84em;font-weight:700;color:{bc};'
                    f'letter-spacing:1px;margin-bottom:0;">{dept.upper()}</div>'
                    f'{ot_html}',
                    unsafe_allow_html=True,
                )

                if status == 'locked':
                    st.markdown(
                        f'<div style="background:#E8F5EE;border-left:4px solid #3EAA6D;'
                        f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:10px;">'
                        f'<div style="font-size:0.75em;font-weight:700;color:#2D7D4F;'
                        f'letter-spacing:1px;margin-bottom:4px;">{dept.upper()} ✅</div>'
                        f'<div style="font-size:0.95em;color:#1a1a1a;line-height:1.6;">{text}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                elif status == 'opted_out':
                    st.markdown(
                        f'<div style="border-left:4px solid #DDDDDD;background:#FAFAFA;'
                        f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:10px;">'
                        f'<div style="font-size:0.75em;font-weight:700;color:#AAAAAA;'
                        f'letter-spacing:1px;margin-bottom:4px;">{dept.upper()}</div>'
                        f'<div style="font-size:0.95em;color:#BBBBBB;font-style:italic;">'
                        f'Not directly contributing to this choice.</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                elif status == 'draft':
                    # Submitted and visible to the room — under discussion
                    _points = [p.strip() for p in text.split('\n') if p.strip()]
                    if len(_points) == 1:
                        _body = f'<div style="font-size:0.95em;color:#1a1a1a;line-height:1.6;">{_points[0]}</div>'
                    else:
                        _items = ''.join([f'<li style="margin-bottom:4px;">{p}</li>' for p in _points])
                        _body  = f'<ul style="font-size:0.95em;color:#1a1a1a;line-height:1.6;margin:4px 0 0 0;padding-left:18px;">{_items}</ul>'
                    st.markdown(
                        f'<div style="background:#FEF9E7;border-left:4px solid #F4B942;'
                        f'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:10px;">'
                        f'<div style="font-size:0.75em;font-weight:700;color:#B7860D;'
                        f'letter-spacing:1px;margin-bottom:4px;">{dept.upper()} 💬 IN DISCUSSION</div>'
                        f'{_body}</div>',
                        unsafe_allow_html=True,
                    )
                    add_text = st.text_area(
                        dept,
                        value='',
                        height=60,
                        placeholder='Add another point…',
                        key=f'casc_ta_{choice["id"]}_{dept}_{len(_points)}',
                        label_visibility='collapsed',
                    )
                    if st.button(
                        'Add to discussion',
                        key=f'casc_sub_{choice["id"]}_{dept}',
                        use_container_width=True,
                    ):
                        if add_text.strip():
                            try:
                                save_cascade_contribution(choice['id'], dept, text + '\n' + add_text.strip())
                                st.toast(f'{dept} added ✓', icon='💬')
                                st.rerun()
                            except Exception as _e:
                                st.error(f'Could not save. ({_e})')
                        else:
                            st.warning('Add a point before submitting.')
                    st.markdown('')

                else:
                    # No submission yet — show editable field
                    new_text = st.text_area(
                        dept,
                        value=text,
                        height=72,
                        placeholder=f'How does {dept} contribute to this?',
                        key=f'casc_ta_{choice["id"]}_{dept}',
                        label_visibility='collapsed',
                    )
                    if st.button(
                        'Submit for discussion',
                        key=f'casc_sub_{choice["id"]}_{dept}',
                        use_container_width=True,
                    ):
                        if new_text.strip():
                            try:
                                save_cascade_contribution(choice['id'], dept, new_text.strip())
                                st.toast(f'{dept} submitted ✓', icon='💬')
                                st.rerun()
                            except Exception as _e:
                                st.error(f'Could not save. ({_e})')
                        else:
                            st.warning('Add a contribution before submitting.')
                    st.markdown('')

            # Confidence vote (facilitator opens per choice)
            if conf_open:
                st.divider()
                _section_label('TEAM CONFIDENCE — ANONYMOUS')
                if st.session_state.get(f'casc_conf_voted_{choice["id"]}'):
                    st.success('Your vote has been recorded. Thank you.')
                else:
                    _fmt = lambda x: {1: '1 — Low', 2: '2', 3: '3 — Moderate', 4: '4', 5: '5 — High'}[x]
                    team_score = st.select_slider(
                        'How confident are you that we will execute this Strategic Choice well in FY27?',
                        options=[1, 2, 3, 4, 5],
                        value=3,
                        format_func=_fmt,
                        key=f'casc_conf_slider_{choice["id"]}',
                    )
                    st.markdown('')
                    func_score_raw = st.select_slider(
                        'If your function is contributing above, how confident are you that you can help contribute to this Strategic Choice in FY27?',
                        options=['N/A', 1, 2, 3, 4, 5],
                        value='N/A',
                        format_func=lambda x: x if x == 'N/A' else _fmt(x),
                        key=f'casc_conf_func_{choice["id"]}',
                    )
                    st.markdown('')
                    feedback = st.text_area(
                        'Feedback (optional)',
                        placeholder='Any thoughts on this choice — what would make it more likely to succeed?',
                        key=f'casc_conf_fb_{choice["id"]}',
                        height=80,
                    )
                    st.markdown('')
                    if st.button(
                        'Submit vote anonymously',
                        type='primary',
                        key=f'casc_conf_btn_{choice["id"]}',
                        use_container_width=True,
                    ):
                        try:
                            fs = '' if func_score_raw == 'N/A' else func_score_raw
                            save_cascade_confidence(choice['id'], team_score, fs, feedback.strip())
                            st.session_state[f'casc_conf_voted_{choice["id"]}'] = True
                            st.rerun()
                        except Exception as _e:
                            st.error(f'Could not save. ({_e})')

        _contributions()

    elif stage == 'reveal':
        _section_label('FY27 STRATEGY CASCADE')

        @st.fragment(run_every=30)
        def _reveal():
            df_c    = pull_cascade_contributions()
            df_conf = pull_cascade_confidence()

            for i, choice in enumerate(CHOICES):
                bc = WINE

                conf_badge = ''
                if not df_conf.empty:
                    ch = df_conf[df_conf['ChoiceID'] == choice['id']]
                    nums = []
                    for v in ch['TeamScore'].tolist():
                        try: nums.append(int(v))
                        except: pass
                    if nums:
                        avg = sum(nums) / len(nums)
                        cbc = '#2D7D4F' if avg >= 4 else ('#B7770D' if avg >= 3 else '#C0392B')
                        cbg = '#E8F5EE' if avg >= 4 else ('#FEF5E7' if avg >= 3 else '#FDECEA')
                        conf_badge = (
                            f' <span style="font-size:0.84em;background:{cbg};color:{cbc};'
                            f'font-weight:700;padding:2px 10px;border-radius:10px;">'
                            f'{avg:.1f}/5</span>'
                        )

                st.markdown(
                    f'<div style="border-left:4px solid {bc};padding:14px 18px;'
                    f'background:#F8F8F8;border-radius:0 8px 8px 0;margin-bottom:6px;">'
                    f'<div style="font-weight:700;font-size:1.05em;color:{bc};">'
                    f'{choice["number"]}. {choice["title"]}{conf_badge}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if not df_c.empty:
                    for dept in DEPARTMENTS:
                        match = df_c[
                            (df_c['ChoiceID'] == choice['id']) & (df_c['Department'] == dept)
                        ]
                        if match.empty:
                            continue
                        row    = match.iloc[0]
                        status = row['Status']
                        text   = row['Text']
                        if status == 'locked' and text:
                            st.markdown(
                                f'<div style="margin-left:20px;border-left:3px solid #3EAA6D;'
                                f'padding:8px 14px;margin-bottom:4px;font-size:0.95em;'
                                f'color:#333;line-height:1.5;">'
                                f'<strong style="color:#2D7D4F;">{dept}:</strong> {text}</div>',
                                unsafe_allow_html=True,
                            )
                        elif status == 'opted_out':
                            st.markdown(
                                f'<div style="margin-left:20px;border-left:3px solid #DDDDDD;'
                                f'padding:8px 14px;margin-bottom:4px;font-size:0.95em;'
                                f'color:#BBBBBB;font-style:italic;">{dept}: not contributing</div>',
                                unsafe_allow_html=True,
                            )

                st.markdown('<div style="margin-bottom:16px;"></div>', unsafe_allow_html=True)

        _reveal()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_results:

    @st.fragment(run_every=20)
    def _results():
        df_c    = pull_cascade_contributions()
        df_conf = pull_cascade_confidence()

        any_data = (not df_c.empty) or (not df_conf.empty)

        if not any_data:
            st.markdown(
                f'<div style="background:#F5F5F5;border-radius:10px;padding:28px;'
                f'text-align:center;color:#AAAAAA;font-size:0.95em;">'
                f'⏳  Results will appear here as the team works through each Strategic Choice.</div>',
                unsafe_allow_html=True,
            )
            return

        for choice in CHOICES:
            # ── Confidence scores for this choice ──────────────────────────────
            team_nums = []
            func_nums = []
            feedbacks = []
            if not df_conf.empty:
                ch_conf = df_conf[df_conf['ChoiceID'] == choice['id']]
                for _, crow in ch_conf.iterrows():
                    try: team_nums.append(int(crow['TeamScore']))
                    except: pass
                    try: func_nums.append(int(crow['FunctionScore']))
                    except: pass
                    fb = str(crow.get('Feedback', '')).strip()
                    if fb:
                        feedbacks.append(fb)

            # ── Contributions for this choice ───────────────────────────────────
            locked_contribs = []
            if not df_c.empty:
                ch_c = df_c[df_c['ChoiceID'] == choice['id']]
                for dept in DEPARTMENTS:
                    match = ch_c[ch_c['Department'] == dept]
                    if match.empty:
                        continue
                    row = match.iloc[0]
                    if row['Status'] == 'locked' and row['Text']:
                        locked_contribs.append((dept, row['Text']))

            # Skip choices with nothing at all
            if not team_nums and not locked_contribs:
                continue

            # ── Choice header with inline confidence badge(s) ──────────────────
            badge_html = ''
            if team_nums:
                t_avg = sum(team_nums) / len(team_nums)
                t_n   = len(team_nums)
                t_fc  = '#2D7D4F' if t_avg >= 4 else ('#B7770D' if t_avg >= 3 else '#C0392B')
                t_bg  = '#E8F5EE' if t_avg >= 4 else ('#FEF5E7' if t_avg >= 3 else '#FDECEA')
                badge_html += (
                    f'<span style="font-size:0.84em;background:{t_bg};color:{t_fc};'
                    f'font-weight:700;padding:2px 9px;border-radius:10px;margin-left:8px;">'
                    f'Team {t_avg:.1f}/5 ({t_n})</span>'
                )
            if func_nums:
                f_avg = sum(func_nums) / len(func_nums)
                f_n   = len(func_nums)
                f_fc  = '#2D7D4F' if f_avg >= 4 else ('#B7770D' if f_avg >= 3 else '#C0392B')
                f_bg  = '#E8F5EE' if f_avg >= 4 else ('#FEF5E7' if f_avg >= 3 else '#FDECEA')
                badge_html += (
                    f'<span style="font-size:0.84em;background:{f_bg};color:{f_fc};'
                    f'font-weight:700;padding:2px 9px;border-radius:10px;margin-left:6px;">'
                    f'Function {f_avg:.1f}/5 ({f_n})</span>'
                )

            st.markdown(
                f'<div style="border-left:4px solid {WINE};padding:14px 18px;'
                f'background:#F8F8F8;border-radius:0 8px 8px 0;margin-bottom:10px;">'
                f'<div style="font-weight:700;font-size:1.05em;color:{WINE};">'
                f'{choice["number"]}. {choice["title"]}{badge_html}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── Contribution statements ─────────────────────────────────────────
            if locked_contribs:
                for dept, text in locked_contribs:
                    points = [p.strip() for p in text.split('\n') if p.strip()]
                    if len(points) == 1:
                        body = f'<span style="color:#333;">{points[0]}</span>'
                    else:
                        items = ''.join([f'<li style="margin-bottom:3px;">{p}</li>' for p in points])
                        body  = f'<ul style="margin:4px 0 0 0;padding-left:18px;color:#333;">{items}</ul>'
                    st.markdown(
                        f'<div style="margin-left:4px;border-left:3px solid {WINE};'
                        f'padding:8px 14px;margin-bottom:6px;background:#FDF8FC;border-radius:0 6px 6px 0;">'
                        f'<div style="font-size:0.75em;font-weight:700;color:{WINE};'
                        f'letter-spacing:1px;margin-bottom:4px;">{dept.upper()}</div>'
                        f'<div style="font-size:0.95em;line-height:1.6;">{body}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    f'<div style="font-size:0.95em;color:#BBBBBB;font-style:italic;'
                    f'margin-left:4px;margin-bottom:6px;">No contributions locked yet.</div>',
                    unsafe_allow_html=True,
                )

            # ── Feedback ────────────────────────────────────────────────────────
            if feedbacks:
                st.markdown(
                    f'<div style="font-size:0.75em;font-weight:700;color:#888;'
                    f'letter-spacing:1px;margin:8px 0 5px 4px;">FEEDBACK</div>',
                    unsafe_allow_html=True,
                )
                for fb in feedbacks:
                    st.markdown(
                        f'<div style="margin-left:4px;background:#F8F8F8;border-left:3px solid #DDDDDD;'
                        f'padding:7px 12px;border-radius:0 6px 6px 0;font-size:0.95em;'
                        f'color:#555;margin-bottom:4px;">{fb}</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown('<div style="margin-bottom:20px;"></div>', unsafe_allow_html=True)

    _results()
