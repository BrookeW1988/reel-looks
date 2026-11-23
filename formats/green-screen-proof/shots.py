#!/usr/bin/env python3
"""Screenshots the real web pages behind Green-screen proof (config.json "backgrounds") at phone width, and records
where each key line sits so build.py can zoom on it and draw the red mark exactly over the real words.

WHY headless Chrome and not a saved image: the proof must be the real page as anyone would see it on a phone today,
and the key line's position must be measured, not guessed. Output: assets/<id>.png + assets/shots.json
    $PY shots.py
(needs Playwright in that venv: `pip install playwright && playwright install chromium`)
"""
import json, os
from playwright.sync_api import sync_playwright

C = json.load(open("config.json"))
# Playwright's own Chromium by default (why: a fixed path breaks when Playwright updates). Set CHROME to use another.
CHROME = os.environ.get("CHROME") or None
CSS_W, DPR = 412, 4          # a 412 px phone viewport, captured at 4x (1648 px wide) so a 1.6x zoom stays sharp
CLIP_H = 640                 # css px of page captured per background

JS_RECTS = """([anchor, key]) => {
  // find the text node containing `needle` and return its client rects (one per line it wraps onto)
  function rectsOf(needle) {
    if (!needle) return null;
    const walker = document.createTreeWalker(document.querySelector('main') || document.body, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walker.nextNode())) {
      const i = n.textContent.indexOf(needle);
      if (i >= 0) {
        const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + needle.length);
        return Array.from(r.getClientRects()).map(q => ({x: q.x, y: q.y + window.scrollY, w: q.width, h: q.height}));
      }
    }
    return null;
  }
  return {anchor: rectsOf(anchor), key: rectsOf(key)};
}"""

out = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    ctx = b.new_context(viewport={"width": CSS_W, "height": 900}, device_scale_factor=DPR, is_mobile=True, has_touch=True,
                        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
                        locale="en-AU")
    pg = ctx.new_page()
    for bg in C["backgrounds"]:
        pg.goto(bg["url"], wait_until="networkidle")
        # hide banners that aren't the article (fundraising / cookie notices) so the page reads cleanly
        pg.add_style_tag(content=".cdx-message, #siteNotice, .frb, .mw-dismissable-notice { display:none !important; }")
        # mobile Wikipedia collapses every section after the lead: open them all so positions are real
        pg.evaluate("""() => { document.querySelectorAll('section[hidden], [hidden="until-found"]').forEach(x => x.removeAttribute('hidden'));
                              document.querySelectorAll('.collapsible-heading').forEach(h => h.classList.add('open-block')); }""")
        pg.wait_for_timeout(500)
        r = pg.evaluate(JS_RECTS, [bg["anchor"], bg.get("key")])
        print(bg["id"], "anchor", r["anchor"][:1] if r["anchor"] else None, "doc h", pg.evaluate("document.documentElement.scrollHeight"))
        if not r["anchor"]:
            raise SystemExit(f"{bg['id']}: anchor text not found on the page: {bg['anchor']!r}")
        top = 0 if bg["id"] == "bg1" else max(0, r["anchor"][0]["y"] - 70)   # bg1 keeps the page header
        pg.screenshot(path=f"assets/{bg['id']}.png", clip={"x": 0, "y": top, "width": CSS_W, "height": CLIP_H}, full_page=True)
        key = [{k: round((q[k] - (top if k == "y" else 0)) / CSS_W, 4) for k in q} for q in (r["key"] or [])]
        out[bg["id"]] = {"url": bg["url"], "css_w": CSS_W, "clip_h_ratio": round(CLIP_H / CSS_W, 4), "key_rects": key}
        print(bg["id"], "top", round(top), "key lines", len(key))
    b.close()
# rects are stored as fractions of the page width so they scale with however wide the image is drawn
json.dump(out, open("assets/shots.json", "w"), indent=1)
