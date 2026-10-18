#!/usr/bin/env node
// Capturas por diapositiva + chequeo de desbordes.
//
//   node deck/tools/shot.mjs deck/tool-use.html [--sizes 1920x1080,1280x720,390x844]
//                                               [--out deck/shots] [--only 3,4] [--chromium /ruta/a/chrome]
//
// Para cada tamaño y cada diapositiva abre  <html>?still=1&slide=N  (el runtime pone data-solo:
// solo esa diapositiva, sin pasos ni animaciones), guarda un PNG en deck/shots/ y FALLA (exit 1) si:
//   · el .slide desborda (scrollHeight > clientHeight o scrollWidth > clientWidth), o
//   · el contenido de .main desborda su caja, o se mete en el pie, o se sale por la derecha.
import { mkdirSync, existsSync, readdirSync } from 'node:fs';
import { dirname, join, resolve, basename } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const deckDir = resolve(here, '..');
const argv = process.argv.slice(2);
const opt = (name, def) => { const i = argv.indexOf(name); return i >= 0 ? argv[i + 1] : def; };
const flagsWithValue = new Set(['--sizes', '--out', '--only', '--chromium']);
const positional = argv.filter((a, i) => !a.startsWith('--') && !flagsWithValue.has(argv[i - 1]));
const htmlPath = resolve(positional[0] || join(deckDir, 'tool-use.html'));
const sizes = opt('--sizes', '1920x1080,1280x720,390x844').split(',').map(s => {
  const m = /^(\d+)x(\d+)$/.exec(s.trim());
  if (!m) { console.error(`Tamaño inválido: "${s}" (usa 1280x720)`); process.exit(2); }
  return { w: +m[1], h: +m[2], tag: s.trim() };
});
const outDir = resolve(opt('--out', join(deckDir, 'shots')));
const only = opt('--only', null)?.split(',').map(Number);

if (!existsSync(htmlPath)) { console.error(`No existe ${htmlPath}. ¿Corriste node deck/tools/assemble.mjs?`); process.exit(2); }

let chromium;
try { ({ chromium } = await import('playwright')); }
catch { try { ({ chromium } = await import(pathToFileURL(join(deckDir, 'node_modules/playwright/index.mjs')).href)); }
  catch { console.error('Falta playwright: cd deck && npm i -D playwright'); process.exit(2); } }

// ---------- lanzar chromium (default de Playwright → ruta indicada → Chrome/Chromium del sistema) ----------
async function launch() {
  const candidates = [opt('--chromium', null), process.env.CHROMIUM_PATH, process.env.CHROME_PATH].filter(Boolean);
  const tried = [];
  try { return await chromium.launch(); } catch (e) { tried.push(String(e.message).split('\n')[0]); }
  const sys = ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium'];
  const pwRoot = process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (pwRoot && existsSync(pwRoot)) for (const d of readdirSync(pwRoot).filter(d => d.startsWith('chromium'))) {
    sys.push(join(pwRoot, d, 'chrome-linux', 'chrome'), join(pwRoot, d, 'chrome-linux', 'headless_shell'));
  }
  for (const p of [...candidates, ...sys]) {
    if (!existsSync(p)) continue;
    try { return await chromium.launch({ executablePath: p }); } catch (e) { tried.push(`${p}: ${String(e.message).split('\n')[0]}`); }
  }
  console.error('No pude lanzar Chromium:\n  ' + tried.join('\n  ') + '\nInstala uno con `npx playwright install chromium` o pasa --chromium /ruta.');
  process.exit(2);
}

// ---------- medición dentro de la página ----------
const measure = () => {
  const s = document.querySelector('#deck > .slide.active');
  if (!s) return { error: 'no hay .slide.active (¿?slide=N fuera de rango?)' };
  const issues = [];
  const tol = 2;
  if (s.scrollHeight > s.clientHeight + tol) issues.push(`slide: scrollHeight ${s.scrollHeight} > clientHeight ${s.clientHeight}`);
  if (s.scrollWidth > s.clientWidth + tol) issues.push(`slide: scrollWidth ${s.scrollWidth} > clientWidth ${s.clientWidth}`);
  const main = s.querySelector(':scope > .main');
  const foot = s.querySelector(':scope > .bottomline');
  if (main) {
    if (main.scrollHeight > main.clientHeight + tol) issues.push(`.main: contenido ${main.scrollHeight}px en caja de ${main.clientHeight}px`);
    const mr = main.getBoundingClientRect();
    const footTop = foot && getComputedStyle(foot).visibility !== 'hidden' ? foot.getBoundingClientRect().top : Infinity;
    const vw = document.documentElement.clientWidth;
    let worst = null;
    for (const el of main.querySelectorAll('*')) {
      if (el.closest('.motif, .atmo, .notes')) continue;      // decorativos: pueden sangrar a propósito
      const r = el.getBoundingClientRect();
      if (!r.width && !r.height) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      const why = r.bottom > footTop + tol ? 'invade el pie' : r.right > vw + tol ? 'se sale por la derecha' : r.left < -tol ? 'se sale por la izquierda' : r.bottom > mr.bottom + 48 ? 'cae bajo .main' : null;
      if (why && (!worst || r.bottom > worst.bottom)) worst = { why, bottom: r.bottom, sel: el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).join('.') : '') };
    }
    if (worst) issues.push(`${worst.sel} ${worst.why} (bottom ${Math.round(worst.bottom)})`);
  }
  return { issues, title: s.dataset.title || '', n: [...document.querySelectorAll('#deck > .slide')].indexOf(s) + 1 };
};

mkdirSync(outDir, { recursive: true });
const browser = await launch();
const base = pathToFileURL(htmlPath).href;
const stem = basename(htmlPath, '.html');
let bad = 0, shots = 0;

for (const sz of sizes) {
  const ctx = await browser.newContext({ viewport: { width: sz.w, height: sz.h }, deviceScaleFactor: 1, hasTouch: sz.w < 700, reducedMotion: 'no-preference' });
  const page = await ctx.newPage();
  const pageErrors = [];
  page.on('pageerror', e => pageErrors.push(e.message));
  await page.goto(`${base}?still=1`);
  const total = await page.evaluate(() => document.querySelectorAll('#deck > .slide').length);
  if (!total) { console.error('El HTML no tiene diapositivas.'); process.exit(2); }
  console.log(`\n== ${sz.tag} · ${total} diapositivas ==`);
  for (let n = 1; n <= total; n++) {
    if (only && !only.includes(n)) continue;
    await page.goto(`${base}?still=1&slide=${n}`);
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
    const solo = await page.evaluate(() => document.documentElement.dataset.solo === '1' && document.documentElement.dataset.still === '1');
    const m = await page.evaluate(measure);
    const file = join(outDir, `${stem}-${sz.tag}-${String(n).padStart(2, '0')}.png`);
    await page.screenshot({ path: file });
    shots++;
    const issues = m.error ? [m.error] : [...m.issues, ...(solo ? [] : ['el runtime no activó still+solo'])];
    if (issues.length) { bad++; console.log(`  ✗ ${String(n).padStart(2, '0')} ${m.title}\n      ${issues.join('\n      ')}`); }
    else console.log(`  ✓ ${String(n).padStart(2, '0')} ${m.title}`);
  }
  if (pageErrors.length) { bad++; console.log('  ✗ errores de JS en la página:\n      ' + [...new Set(pageErrors)].join('\n      ')); }
  await ctx.close();
}
await browser.close();
console.log(`\n${shots} capturas en ${outDir}`);
if (bad) { console.error(`✗ ${bad} problema(s) de desborde o ejecución`); process.exit(1); }
console.log('✓ sin desbordes');
