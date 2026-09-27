#!/usr/bin/env python3
"""Final render: 1440x1440 @ 60 fps, 14 s.

4 subframes per output frame (240 fps virtual shutter) blended with
ffmpeg tmix for motion blur. Frames are piped straight into ffmpeg —
nothing is written to disk until the encode.
"""
import http.server
import os
import socketserver
import subprocess
import sys
import threading
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
CHROMIUM = "/opt/pw-browsers/chromium"
FFMPEG = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
PORT = 8741
FPS = 60
SUB = 4
DUR = 14.0
FRAMES = int(FPS * DUR)
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/exp-video.mp4"


def serve():
    os.chdir(ROOT)
    with socketserver.TCPServer(("127.0.0.1", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()


def main():
    threading.Thread(target=serve, daemon=True).start()

    ff = subprocess.Popen(
        [FFMPEG, "-y", "-loglevel", "error",
         "-f", "image2pipe", "-framerate", str(FPS * SUB), "-i", "-",
         "-vf", f"tmix=frames={SUB},select='not(mod(n\\,{SUB}))',setpts=N/{FPS}/TB",
         "-r", str(FPS),
         "-c:v", "libx264", "-preset", "slow", "-crf", "16",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         OUT],
        stdin=subprocess.PIPE,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM, headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.add_init_script("window.__RENDER__ = true;")
        page.goto(f"http://127.0.0.1:{PORT}/index.html")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(300)

        t0 = time.time()
        for k in range(FRAMES):
            for j in range(SUB):
                t = k / FPS + j / (FPS * SUB)
                page.evaluate(f"seek({t})")
                ff.stdin.write(page.screenshot(type="jpeg", quality=90))
            if k % 60 == 0:
                el = time.time() - t0
                eta = el / (k + 1) * (FRAMES - k - 1)
                print(f"frame {k}/{FRAMES}  elapsed {el:.0f}s  eta {eta:.0f}s", flush=True)
        browser.close()

    ff.stdin.close()
    ff.wait()
    assert ff.returncode == 0, "ffmpeg failed"
    print("wrote", OUT)


if __name__ == "__main__":
    main()
