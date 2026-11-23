#!/usr/bin/env python3
"""Capture REAL public pages as proof cards (headless Chrome, never your own logged-in browser).

WHY: the style shows the actual thing the speaker names, held long enough to read. Nothing is mocked up: we screenshot the
live page at a phone viewport (430 css px, 3x) and record where the spoken words sit, so build.py can sweep a
highlighter over exactly those words.

Usage:  $PY tools/capture_proof.py proof.json
Needs Playwright in that venv (not part of the base setup): $PY -m pip install playwright
and Google Chrome installed (it launches Chrome headless, channel="chrome").
proof.json: [{"id": "your-page", "url": "...", "top_text": "A heading", "marks": ["phrase", ...],
              "height": 1100, "hide": ["css selector", ...]}]
Writes assets/proof/<id>.png (the crop) and assets/proof/<id>.json (crop size + mark boxes in crop pixels).
"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

VIEW_W, DSF = 430, 3
JS_FIND = """([phrase]) => {
  // find the first visible text node containing the phrase and return its client rects (one per line)
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    const i = n.textContent.toLowerCase().indexOf(phrase.toLowerCase());
    if (i < 0) continue;
    const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + phrase.length);
    const rects = [...r.getClientRects()].filter(b => b.width > 2 && b.height > 2);
    if (!rects.length) continue;
    return rects.map(b => ({x: b.left + scrollX, y: b.top + scrollY, w: b.width, h: b.height}));
  }
  return null;
}"""

def main(cfg_path):
    items = json.load(open(cfg_path))
    out_dir = Path("assets/proof"); out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport={"width": VIEW_W, "height": 932}, device_scale_factor=DSF,
                                  color_scheme="light", locale="en-AU",
                                  user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
                                             "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
        for it in items:
            page = ctx.new_page()
            vw = it.get("view_w", VIEW_W)          # narrower viewport = bigger text relative to the card
            page.set_viewport_size({"width": vw, "height": 932})
            page.goto(it["url"], wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(1500)
            for sel in it.get("hide", []):     # cookie banners, sticky ads: hidden, never edited
                page.add_style_tag(content=f"{sel} {{ display: none !important; }}")
            top = page.evaluate(JS_FIND, [it["top_text"]])
            if not top:
                sys.exit(f"{it['id']}: top_text not found: {it['top_text']}")
            y0 = max(0, top[0]["y"] - it.get("pad_top", 24))
            h = it.get("height", 1000)
            marks = {}
            for m in it.get("marks", []):
                rects = page.evaluate(JS_FIND, [m])
                if not rects:
                    sys.exit(f"{it['id']}: mark not found: {m}")
                marks[m] = [{k: round((v - (y0 if k == "y" else 0)) * DSF, 1) for k, v in r.items()} for r in rects]
            png = out_dir / f"{it['id']}.png"
            page.screenshot(path=str(png), clip={"x": 0, "y": y0, "width": vw, "height": h}, full_page=True)
            meta = {"url": it["url"], "title": page.title(), "w": vw * DSF, "h": h * DSF, "marks": marks}
            json.dump(meta, open(out_dir / f"{it['id']}.json", "w"), indent=1)
            print(it["id"], meta["title"], {k: len(v) for k, v in marks.items()})
            page.close()
        browser.close()

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "proof.json")
