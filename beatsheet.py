#!/usr/bin/env python3
"""Render one frame per beat (plus key half-beats) as a contact sheet.

Run this before the full render to check the grid: anything off the beat,
cramped or hard to read gets fixed here first.
"""
import http.server
import os
import socketserver
import threading

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("BEATSHEET_OUT", "/tmp/beatsheet")
PAGE = os.environ.get("BEATSHEET_PAGE", "index.html")
DUR = float(os.environ.get("BEATSHEET_DUR", "14"))
CHROMIUM = "/opt/pw-browsers/chromium"
PORT = 8731

# every beat, plus mid-action extras worth checking
TIMES = sorted(set(round(b * 0.5, 3) for b in range(int(DUR * 2))) |
               set(round(b * 0.5 + 0.25, 3) for b in range(int(DUR * 2))))


def serve():
    os.chdir(ROOT)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        httpd.serve_forever()


def main():
    os.makedirs(OUT, exist_ok=True)
    threading.Thread(target=serve, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM, headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.add_init_script("window.__RENDER__ = true;")
        page.goto(f"http://127.0.0.1:{PORT}/{PAGE}")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(300)

        shots = []
        for t in TIMES:
            page.evaluate(f"seek({t})")
            path = os.path.join(OUT, f"t{t:06.3f}.png")
            page.screenshot(path=path)
            shots.append((t, path))
            print(f"beat frame t={t}")
        browser.close()

    # contact sheet (9:16 cells)
    cols, cw, ch = 7, 300, 533
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * (ch + 26)), "#333")
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for i, (t, path) in enumerate(shots):
        im = Image.open(path).resize((cw, ch), Image.LANCZOS)
        x, y = (i % cols) * cw, (i // cols) * (ch + 26)
        sheet.paste(im, (x, y))
        d.text((x + 8, y + ch + 5), f"t={t:.2f}  b={t/0.5:g}", fill="#fff")
    sheet_path = os.path.join(OUT, "sheet.png")
    sheet.save(sheet_path)
    print("sheet:", sheet_path)


if __name__ == "__main__":
    main()
