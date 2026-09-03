import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import streamlit.components.v1 as components
from utils import inject_styles, PURPLE, TEAL, with_retry, _sheets, _clear_sheets
from magazine_shared import (
    CATEGORIES, COVER_YEAR, PREVIEW_WIDTH,
    _ensure_tabs, pull_submissions, append_submission,
    pull_votes, upsert_vote, _img_cache_key,
    generate_cover_image, _show_image,
    _compose_cover_image, _save_composed_to_drive,
    pull_generated_story, build_cover_html, build_partner_badge_html,
    pull_vision_data,
)

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

if not st.session_state.get('_tabs_ensured_v2'):
    try:
        with_retry(_ensure_tabs, on_retry=_clear_sheets)
        st.session_state['_tabs_ensured_v2'] = True
    except Exception as _e:
        st.warning(f'Sheet setup issue — some features may not save correctly. ({_e})')

# ── Page header ────────────────────────────────────────────────────────────────

st.markdown('### Vision Activity — Magazine Cover Story')
st.markdown(
    f'It\'s {COVER_YEAR}. Audeara has been named an Official Partner of the Brisbane 2032 Olympic Games '
    f'— and it just made the cover of a major publication. '
    f'What kind of partner are we? What did we build to get here?'
)
st.markdown(
    f'<div class="activity-card">'
    f'<strong>Let\'s discover our shared vision by thinking big together.</strong> '
    f'The cover story is an announcement of our Official Olympic Partnership. '
    f'Think about what that partnership looks like, what we\'ve accomplished by 2032 that makes us the obvious choice, '
    f'and what the world is saying about us. Shoot for the moon.'
    f'</div>',
    unsafe_allow_html=True,
)
st.markdown('')

tab_submit, tab_vote, tab_results, tab_vision = st.tabs(['💡 Submit ideas', '🗳️ Vote', '🏆 Results', '🔭 Vision Statement'])

# ── Submit ─────────────────────────────────────────────────────────────────────

with tab_submit:
    st.markdown('#### Your cover story')
    st.caption(
        f'Think about Audeara in {COVER_YEAR}. We\'ve landed an Official Olympic Partnership — '
        f'what kind of partner are we, and what makes us the obvious choice? '
        f'Fill in as many or as few fields as you like.'
    )

    pub      = st.text_input('Publication',
                             placeholder='e.g. Fast Company, The Australian, Time, Harvard Business Review…',
                             key='vsub_pub')
    headline = st.text_input('Cover headline',
                             placeholder='e.g. "The Brisbane company that made the Olympics more accessible"',
                             key='vsub_headline')
    partner  = st.text_input('Official ___ Partner of the Brisbane 2032 Olympic Games',
                             placeholder='e.g. Assistive Listening, Hearing Technology, Accessibility…',
                             key='vsub_partner')
    story    = st.text_area('The story — what makes us the obvious choice?',
                            placeholder='e.g. "By 2032 Audeara had reached 2 million people across 60 countries, making world-class listening technology accessible to anyone, anywhere…"',
                            height=90, key='vsub_story')
    quote    = st.text_input('A quote from the story',
                             placeholder='e.g. "We didn\'t set out to be an Olympic partner. We set out to help people feel connected." — James Fielding',
                             key='vsub_quote')
    standout = st.text_input('The standout — what\'s the fact, stat, or moment that defines the journey?',
                             placeholder='e.g. "Every athlete at Brisbane 2032 could access Audeara\'s technology in their language."',
                             key='vsub_standout')
    image_desc = st.text_area(
        '🎨 Describe the cover image (optional)',
        placeholder=(
            'Describe a scene, image, or feeling for the cover — '
            'AI will generate it in Audeara\'s brand style.\n'
            'e.g. "An athlete in a packed Olympic stadium, headphones on, fully absorbed in the moment — surrounded by light and energy."'
        ),
        height=90,
        key='vision_img_desc_outer',
    )

    _preview_desc = image_desc.strip()
    c_cap, c_btn = st.columns([4, 1])
    with c_cap:
        st.caption('Describe a cover image above, then preview it before submitting.')
    with c_btn:
        _do_preview = st.button(
            '👁 Preview', key='vision_img_preview_btn',
            use_container_width=True, disabled=not _preview_desc,
        )
    if _do_preview:
        st.session_state['_vision_preview_for'] = _preview_desc
    if _preview_desc and st.session_state.get('_vision_preview_for') == _preview_desc:
        _show_image(
            _preview_desc,
            caption='Preview — not yet saved. Click Submit to save.',
            save_to_drive=False,
        )

    submitted = st.button('Submit', type='primary', use_container_width=True, key='vsub_submit')

    if submitted:
        _pub      = st.session_state.get('vsub_pub', '').strip()
        _headline = st.session_state.get('vsub_headline', '').strip()
        _partner  = st.session_state.get('vsub_partner', '').strip()
        _story    = st.session_state.get('vsub_story', '').strip()
        _quote    = st.session_state.get('vsub_quote', '').strip()
        _standout = st.session_state.get('vsub_standout', '').strip()
        _img_desc = st.session_state.get('vision_img_desc_outer', '').strip()
        if any([_headline, _partner, _story, _quote, _standout, _img_desc]):
            try:
                append_submission(COVER_YEAR, _pub, _headline, _partner, _story, _quote, _standout, _img_desc)
                for _k in ['vsub_pub', 'vsub_headline', 'vsub_partner', 'vsub_story', 'vsub_quote', 'vsub_standout', 'vision_img_desc_outer']:
                    st.session_state.pop(_k, None)
                st.session_state.pop('_vision_preview_for', None)
                st.cache_data.clear()
                st.toast('Submitted! Head to the Vote tab to upvote your favourites.', icon='✅')
                st.rerun()
            except Exception as _e:
                st.error(f'Could not save — network issue. Please try submitting again. ({_e})')
        else:
            st.warning('Please fill in at least one field before submitting.')

    st.divider()
    subs = pull_submissions()
    if not subs.empty:
        st.markdown(f'#### {len(subs)} submission{"s" if len(subs) != 1 else ""} so far')
        for _, row in subs.iterrows():
            pub_str     = f' · {row.get("Publication","").strip()}' if row.get('Publication','').strip() else ''
            partner_str = row.get('Partner Title', '').strip()
            st.markdown(
                f'<div class="activity-card">'
                f'<span style="font-size:0.75em;color:#888;">{COVER_YEAR}{pub_str}</span><br>'
                + (f'<span style="font-size:0.78em;font-weight:700;color:{TEAL};">Official {partner_str} Partner · Brisbane 2032</span><br>' if partner_str else '')
                + f'<span style="font-size:1.05em;font-weight:700;">{row.get("Headline","")}</span><br>'
                f'<span style="font-size:0.88em;color:#555;">{row.get("The Story","")}</span><br>'
                f'<em style="font-size:0.85em;">{row.get("Quote","")}</em><br>'
                f'<span style="font-size:0.82em;color:#777;">{row.get("Standout","")}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
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
        st.caption('Vote for the headlines, partner titles, stories, quotes, and standout facts that feel most true to where Audeara is headed.')
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
            if col_key == 'Image':
                hdr_col, btn_col = st.columns([5, 2])
                with hdr_col:
                    st.markdown(f'<div class="category-header">{col_label}</div>', unsafe_allow_html=True)
                with btn_col:
                    _imgs_visible = st.session_state.get('_show_vote_images', False)
                    if st.button(
                        '🙈 Hide images' if _imgs_visible else '👁 Show all images',
                        key='toggle_vote_images',
                    ):
                        st.session_state['_show_vote_images'] = not _imgs_visible
                        st.rerun()
            else:
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
                    if st.session_state.get('_show_vote_images'):
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

        headline_val     = _top_or_first('Headline',      'Headline')
        partner_val      = _top_or_first('Partner Title', 'Partner Title')
        story_val        = _top_or_first('The Story',     'The Story')
        quote_val        = _top_or_first('Quote',         'Quote')
        standout_val     = _top_or_first('Standout',      'Standout')
        pub_val          = subs['Publication'].fillna('').iloc[0].strip() if 'Publication' in subs.columns else ''

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
            if partner_val:
                st.markdown(build_partner_badge_html(partner_val), unsafe_allow_html=True)

        with col_cover:
            pub_display = pub_val or 'Audeara · Cover Story'
            partner_label = f'Official {partner_val} Partner · Brisbane 2032' if partner_val else f'Brisbane 2032'
            st.markdown(
                f'<div class="magazine-cover">'
                f'<div class="mag-pub">{pub_display}</div>'
                f'<div class="mag-year">{partner_label}</div>'
                f'<div class="mag-headline">{headline_val or "<em style=color:#555>Headline coming soon</em>"}</div>'
                f'{"<div class=mag-story>" + story_val + "</div>" if story_val else ""}'
                f'{"<div class=mag-quote>" + quote_val + "</div>" if quote_val else ""}'
                f'{"<div class=mag-bl-label>Standout</div><div class=mag-bottom-text>" + standout_val + "</div>" if standout_val else ""}'
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
        st.caption('Puts all the winning pieces together into a proper magazine cover.')

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
                build_cover_html(pub_val, headline_val, quote_val, standout_val, cover_img_bytes, partner_title=partner_val),
                height=622,
            )

            if cover_img_bytes:
                composed_key = f'composed_cover_{hashlib.md5((headline_val + quote_val + standout_val).encode()).hexdigest()}'
                if composed_key not in st.session_state:
                    with st.spinner('Saving composed cover to Drive…'):
                        try:
                            composed = _compose_cover_image(pub_val, headline_val, quote_val, standout_val, cover_img_bytes)
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

        # ── Full story pull-out (auto-polls every 20s) ────────────────────────
        @st.fragment(run_every=20)
        def _story_section(pub_v, headline_v):
            _story_text = pull_generated_story()
            if _story_text:
                st.divider()
                st.markdown('#### 📰 The full story')
                st.markdown(
                    f'<div style="'
                    f'background:#fff;border:1px solid #e0e0e0;border-radius:8px;'
                    f'padding:36px 40px;max-width:680px;margin:0 auto;'
                    f'font-family:\'Noto Sans\',sans-serif;font-size:15px;line-height:1.8;'
                    f'color:#1a1a1a;box-shadow:0 4px 20px rgba(0,0,0,0.06);'
                    f'">'
                    f'<div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;'
                    f'color:#188383;font-weight:700;margin-bottom:6px;">'
                    f'{pub_v or "AUDEARA"} &nbsp;·&nbsp; {COVER_YEAR} FEATURE</div>'
                    f'<div style="font-family:\'roc-grotesk\',sans-serif;font-size:22px;font-weight:700;'
                    f'line-height:1.2;margin-bottom:24px;color:#111;">'
                    f'{headline_v or ""}</div>'
                    + ''.join(
                        f'<p style="margin:0 0 16px 0;'
                        + ('border-left:3px solid #188383;padding-left:16px;font-style:italic;color:#333;"'
                           if ln.startswith('"') else '"')
                        + f'>{ln}</p>'
                        for ln in _story_text.split('\n') if ln.strip()
                    )
                    + '</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.divider()
                st.caption('The facilitator will generate the full story once voting is complete. It will appear here automatically.')

        _story_section(pub_val, headline_val)

# ── Vision Statement ───────────────────────────────────────────────────────────

with tab_vision:
    _candidates, _final = pull_vision_data()

    c_ref3, _ = st.columns([1, 6])
    with c_ref3:
        if st.button('Refresh', key='refresh_vision_statement'):
            st.cache_data.clear()
            st.rerun()

    if _final:
        st.markdown(
            f'<div style="'
            f'background:linear-gradient(135deg,#f0fafa,#e8f5f5);'
            f'border:3px solid {TEAL};border-radius:14px;'
            f'padding:44px 48px;margin:8px 0 36px 0;text-align:center;">'
            f'<div style="font-size:10px;letter-spacing:0.22em;text-transform:uppercase;'
            f'color:{TEAL};font-weight:700;margin-bottom:16px;">✦ Our Vision</div>'
            f'<div style="font-family:\'roc-grotesk\',sans-serif;font-size:1.9em;font-weight:700;'
            f'line-height:1.3;color:#111;">{_final}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if _candidates:
            st.markdown(
                '<div style="font-size:0.8em;color:#aaa;margin:8px 0 4px 0;'
                'letter-spacing:0.06em;text-transform:uppercase;">Candidates discussed</div>',
                unsafe_allow_html=True,
            )
            for i, c in enumerate(_candidates):
                st.markdown(
                    f'<div style="'
                    f'background:#f7f7f7;border:1px solid #e8e8e8;border-radius:8px;'
                    f'padding:16px 20px;margin:6px 0;opacity:0.5;'
                    f'border-left:4px solid #ccc;">'
                    f'<span style="font-size:0.68em;font-weight:700;letter-spacing:0.1em;'
                    f'text-transform:uppercase;color:#bbb;">Option {i+1}</span><br>'
                    f'<span style="font-size:0.95em;line-height:1.5;color:#999;">{c}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    elif _candidates:
        st.markdown('#### Candidates from the room')
        st.caption('Discuss as a group — the facilitator will lock in the final version once you\'ve agreed.')
        for i, c in enumerate(_candidates):
            st.markdown(
                f'<div style="'
                f'background:#fff;border:1px solid #e0e0e0;border-radius:8px;'
                f'padding:20px 24px;margin:10px 0;'
                f'border-left:4px solid {PURPLE};">'
                f'<span style="font-size:0.7em;font-weight:700;letter-spacing:0.1em;'
                f'text-transform:uppercase;color:{PURPLE};">Option {i+1}</span><br>'
                f'<span style="font-size:1.05em;line-height:1.5;">{c}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('')
        st.info('The facilitator will generate vision statement candidates once voting is complete. Check back soon.')
