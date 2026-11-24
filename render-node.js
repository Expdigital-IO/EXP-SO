// Render em Node (para máquinas sem o Playwright de Python).
// Uso: RENDER_SUB=4 node render-node.js saida.mp4 pagina.html segundos
// Igual ao render.py: SUB subquadros por quadro misturados (motion blur), 1080×1920 a 60 fps.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

const [out = '/tmp/exp-video.mp4', page = 'index.html', durS = '14'] = process.argv.slice(2);
const FPS = 60, SUB = +(process.env.RENDER_SUB || 4), DUR = +durS, FRAMES = Math.round(FPS * DUR);

(async () => {
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS * SUB), '-i', '-',
    '-vf', `tmix=frames=${SUB},select='not(mod(n\\,${SUB}))',setpts=N/${FPS}/TB`, '-r', String(FPS),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.addInitScript('window.__RENDER__ = true;');
  await p.goto('file://' + path.resolve(__dirname, page));
  await p.evaluate('document.fonts.ready'); await p.waitForTimeout(300);
  const t0 = Date.now();
  for (let k = 0; k < FRAMES; k++) {
    for (let j = 0; j < SUB; j++) {
      await p.evaluate(`seek(${k / FPS + j / (FPS * SUB)})`);
      const buf = await p.screenshot({ type: 'jpeg', quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    if (k % 60 === 0) { const el = (Date.now() - t0) / 1000; console.log(`frame ${k}/${FRAMES} elapsed ${el.toFixed(0)}s eta ${(el / (k + 1) * (FRAMES - k - 1)).toFixed(0)}s`); }
  }
  await b.close(); ff.stdin.end();
  ff.on('close', c => { if (c) { console.error('ffmpeg falhou'); process.exit(1); } console.log('wrote', out); });
})();
