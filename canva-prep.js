/* Makes a frozen film page import cleanly into Canva's PDF importer:
   - CSS-masked logos (.mk .mk2 .ol .wd) become tinted PNG <img>s (Canva drops masks)
   - outlined text (-webkit-text-stroke) becomes a transparent PNG (Canva fills it)
   - kerning/ligatures off so text arrives as whole words, not split glyph runs
   - live text switches to fonts Canva has natively (Inter for Geist, Roboto Mono
     for Geist Mono) so weights and word spacing survive the import */
window.__canvaPrep = async function () {
  const st = document.createElement('style');
  st.textContent = '*{font-kerning:none!important;font-variant-ligatures:none!important}';
  document.head.appendChild(st);
  const cache = {};
  const load = url => cache[url] || (cache[url] = new Promise((ok, err) => {
    const im = new Image(); im.onload = () => ok(im); im.onerror = err; im.src = url;
  }));
  const S = 2;
  const sections = [...document.querySelectorAll('section')];
  for (const sec of sections) {
    const prev = sec.style.display;
    sec.style.display = 'block';
    for (const el of sec.querySelectorAll('.mk,.mk2,.ol,.wd')) {
      if (el.dataset.cv) continue;
      const cs = getComputedStyle(el);
      const m = (cs.webkitMaskImage || cs.maskImage || '').match(/url\("?(.*?)"?\)/);
      const w = el.offsetWidth, h = el.offsetHeight;
      if (!m || !w || !h) continue;
      const img = await load(m[1]);
      const c = document.createElement('canvas');
      c.width = Math.round(w * S); c.height = Math.round(h * S);
      const ctx = c.getContext('2d');
      const r = Math.min(c.width / img.width, c.height / img.height);
      const dw = img.width * r, dh = img.height * r;
      ctx.drawImage(img, (c.width - dw) / 2, (c.height - dh) / 2, dw, dh);
      ctx.globalCompositeOperation = 'source-in';
      ctx.fillStyle = cs.backgroundColor;
      ctx.fillRect(0, 0, c.width, c.height);
      el.style.webkitMaskImage = 'none'; el.style.maskImage = 'none';
      el.style.background = 'transparent';
      const out = document.createElement('img');
      out.src = c.toDataURL('image/png');
      out.style.cssText = 'display:block;width:100%;height:100%';
      el.appendChild(out);
      el.dataset.cv = '1';
    }
    const stroked = [...sec.querySelectorAll('*')].filter(el =>
      parseFloat(getComputedStyle(el).webkitTextStrokeWidth) > 0 &&
      [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()));
    for (const el of stroked) {
      const cs = getComputedStyle(el);
      const text = el.textContent;
      const inline = cs.display === 'inline';
      const w = el.offsetWidth, h = el.offsetHeight;
      const pad = Math.round(h * 0.25);
      const c = document.createElement('canvas');
      c.width = Math.round(w * S); c.height = Math.round((h + 2 * pad) * S);
      const ctx = c.getContext('2d');
      ctx.scale(S, S);
      ctx.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
      if (cs.letterSpacing !== 'normal') ctx.letterSpacing = cs.letterSpacing;
      const mt = ctx.measureText(text);
      const asc = mt.fontBoundingBoxAscent, desc = mt.fontBoundingBoxDescent;
      const y = (h - (asc + desc)) / 2 + asc;
      ctx.lineWidth = parseFloat(cs.webkitTextStrokeWidth);
      ctx.strokeStyle = cs.webkitTextStrokeColor;
      ctx.strokeText(text, 0, y + pad);
      const out = document.createElement('img');
      out.src = c.toDataURL('image/png');
      out.style.cssText = `display:block;width:${w}px;height:${h + 2 * pad}px;margin:${-pad}px 0`;
      el.textContent = '';
      el.style.webkitTextStroke = '0';
      if (inline) { el.style.display = 'inline-block'; el.style.verticalAlign = `${-desc}px`; }
      el.appendChild(out);
    }
    sec.style.display = prev;
  }
  const ff = document.createElement('style');
  ff.textContent = [400, 500, 600, 700].map(w =>
      `@font-face{font-family:Inter;src:url(fonts/canva/inter-latin-${w}-normal.woff2) format('woff2');font-weight:${w}}`).join('') +
    [400, 500].map(w =>
      `@font-face{font-family:'Roboto Mono';src:url(fonts/canva/roboto-mono-latin-${w}-normal.woff2) format('woff2');font-weight:${w}}`).join('') +
    `*{font-family:Inter,sans-serif!important}.mono,.mono *{font-family:'Roboto Mono',monospace!important}`;
  document.head.appendChild(ff);
  await Promise.all([400, 500, 600, 700].map(w => document.fonts.load(`${w} 40px Inter`))
    .concat([400, 500].map(w => document.fonts.load(`${w} 40px "Roboto Mono"`))));
  return true;
};
