#!/usr/bin/env python3
"""Export one editable key frame per scene of a film page.

Outputs, per page:
  frames/<name>/NN_<t>s_<slug>.png   full-res 1080x1920 PNG per scene
  frames/<name>/<name>-cenas.pdf      vector PDF, one scene per page (text stays editable)
  frames/<name>/guia.png              contact sheet with scene numbers and times

Usage: python3 export-frames.py brand-film.html brand-film
"""
import http.server
import io
import os
import re
import socketserver
import sys
import threading
import unicodedata

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
import pypdfium2 as pdfium

ROOT = os.path.dirname(os.path.abspath(__file__))
CHROMIUM = "/opt/pw-browsers/chromium"
PORT = 8761

PAGE = sys.argv[1] if len(sys.argv) > 1 else "brand-film.html"
NAME = sys.argv[2] if len(sys.argv) > 2 else "brand-film"
OUT = os.path.join(ROOT, "frames", NAME)

# key frame = the moment each composition is complete (before any exit move)
SCENES = [
    (0.40, "Símbolo neon"),
    (0.70, "Símbolo positivo"),
    (0.95, "Símbolo sobre cor"),
    (1.70, "Capítulo 01 — Branding"),
    (2.45, "Paleta de cores"),
    (3.45, "Tipografia"),
    (3.95, "Billboard"),
    (4.70, "Papelaria"),
    (5.10, "Perfil do Instagram"),
    (6.20, "App no iPhone"),
    (6.95, "Capítulo 02 — Marketing"),
    (8.20, "Dashboard de campanhas"),
    (8.95, "Funil de performance"),
    (9.95, "Anúncio e notificações"),
    (10.70, "Busca — 1ª posição"),
    (11.60, "Marquee"),
    (12.60, "Macro do símbolo"),
    (13.45, "Manifesto 1"),
    (14.20, "Manifesto 2"),
    (15.90, "Endcard"),
]


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve():
    os.chdir(ROOT)
    with socketserver.TCPServer(("127.0.0.1", PORT), Quiet) as httpd:
        httpd.serve_forever()


def main():
    os.makedirs(OUT, exist_ok=True)
    threading.Thread(target=serve, daemon=True).start()
    pngs, pdf_pages = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM, headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.add_init_script("window.__RENDER__ = true;")
        page.goto(f"http://127.0.0.1:{PORT}/{PAGE}")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(400)
        for i, (t, title) in enumerate(SCENES, 1):
            page.evaluate(f"seek({t})")
            fn = os.path.join(OUT, f"{i:02d}_{t:05.2f}s_{slug(title)}.png")
            page.screenshot(path=fn)
            pngs.append((i, t, title, fn))
            pdf_pages.append(page.pdf(width="1080px", height="1920px", print_background=True,
                                      margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                                      page_ranges="1"))
            print(f"{i:02d} {t:5.2f}s {title}")
        browser.close()

    merged = pdfium.PdfDocument.new()
    for blob in pdf_pages:
        merged.import_pages(pdfium.PdfDocument(io.BytesIO(blob)))
    pdf_path = os.path.join(OUT, f"{NAME}-cenas.pdf")
    merged.save(pdf_path)

    cols, cw, ch = 5, 324, 576
    rows = (len(pngs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * (ch + 64)), "#141210")
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except OSError:
        font = small = ImageFont.load_default()
    for k, (i, t, title, fn) in enumerate(pngs):
        x, y = (k % cols) * cw, (k // cols) * (ch + 64)
        sheet.paste(Image.open(fn).resize((cw - 8, ch - 8), Image.LANCZOS), (x + 4, y + 4))
        d.text((x + 8, y + ch + 6), f"{i:02d}  ·  {t:.2f}s", fill="#FF6A2A", font=font)
        d.text((x + 8, y + ch + 34), title, fill="#E8E2DC", font=small)
    sheet.save(os.path.join(OUT, "guia.png"))
    print("pdf:", pdf_path)


if __name__ == "__main__":
    main()
