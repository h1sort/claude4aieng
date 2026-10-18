#!/usr/bin/env node
// Ensambla el deck: shell + deck/src/slides/*.html (orden alfabético) → deck/tool-use.html
//
//   node deck/tools/assemble.mjs [--slides <dir>] [--out <archivo>] [--expect 40:00] [--public]
//
// Convención de CSS por diapositiva: cada parcial puede traer uno o más <style> con reglas
// acotadas a su clase (.s03 …). assemble los saca del parcial y los junta en el <style> del <head>,
// después de system.css. Nada de CSS fuera de un <style>.
//
// Falla (exit 1) si una diapositiva no tiene <aside class="notes"> o data-title/data-section/data-budget.
// data-clock se calcula aquí a partir de data-budget: no lo escribas a mano.
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const deckDir = resolve(here, '..');
const srcDir = join(deckDir, 'src');
const shellDir = join(srcDir, 'shell');

// ---------- argumentos ----------
const argv = process.argv.slice(2);
const opt = (name, def) => { const i = argv.indexOf(name); return i >= 0 ? argv[i + 1] : def; };
const slidesDir = resolve(opt('--slides', join(srcDir, 'slides')));
const sourcesFile = resolve(opt('--sources', join(srcDir, 'sources.html')));
const config = JSON.parse(readFileSync(join(shellDir, 'config.json'), 'utf8'));
const outFile = resolve(opt('--out', join(deckDir, config.file || 'tool-use.html')));
const expect = opt('--expect', null);
const makePublic = argv.includes('--public');

const errors = [];
const fail = msg => errors.push(msg);
const read = f => readFileSync(join(shellDir, f), 'utf8');
const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// ---------- tiempo ----------
const parseMS = s => { const m = /^(\d+):([0-5]\d)$/.exec(s || ''); return m ? (+m[1]) * 60 + (+m[2]) : null; };
const fmtMS = sec => `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`;

// ---------- slides ----------
if (!existsSync(slidesDir)) { console.error(`No existe ${slidesDir}`); process.exit(1); }
const files = readdirSync(slidesDir).filter(f => f.endsWith('.html')).sort();
if (!files.length) { console.error(`Sin parciales en ${slidesDir}`); process.exit(1); }

const hoisted = [];
const slideHtml = [];
const classSeen = new Map();
let elapsed = 0, count = 0;

for (const f of files) {
  let src = readFileSync(join(slidesDir, f), 'utf8');
  // 1) sacar <style> (se hoistean al <head>)
  src = src.replace(/<style\b[^>]*>([\s\S]*?)<\/style>/g, (_, css) => { hoisted.push(`/* --- ${f} --- */\n${css.trim()}\n`); return ''; });
  // 2) validar que fuera de <section> solo hay comentarios/espacio
  const outside = src.replace(/<section\b[\s\S]*?<\/section>/g, '').replace(/<!--[\s\S]*?-->/g, '').trim();
  if (outside) fail(`${f}: contenido fuera de <section class="slide"> → "${outside.slice(0, 60).replace(/\s+/g, ' ')}…"`);

  let found = 0;
  src = src.replace(/<section\b([^>]*)>([\s\S]*?)<\/section>/g, (whole, attrs, inner) => {
    const cls = (/\bclass="([^"]*)"/.exec(attrs) || [, ''])[1].split(/\s+/);
    if (!cls.includes('slide')) { fail(`${f}: <section> sin clase "slide"`); return whole; }
    found++; count++;
    const attr = n => { const m = new RegExp(`\\sdata-${n}="([^"]*)"`).exec(attrs); return m ? m[1] : null; };
    const where = `${f}${found > 1 ? ` (#${found})` : ''}`;
    for (const n of ['title', 'section', 'budget']) if (!attr(n)) fail(`${where}: falta data-${n}`);
    if (!/<aside class="notes">/.test(inner)) fail(`${where}: falta <aside class="notes">`);
    const b = parseMS(attr('budget'));
    if (attr('budget') && b === null) fail(`${where}: data-budget "${attr('budget')}" no es m:ss`);
    const tag = cls.find(c => /^s\d+[a-z]*$/.test(c));
    if (!tag) fail(`${where}: falta la clase de numeración sNN (p. ej. class="slide s03") para acotar su CSS`);
    else if (classSeen.has(tag)) fail(`${where}: la clase ${tag} ya la usa ${classSeen.get(tag)}`);
    else classSeen.set(tag, where);
    // data-clock calculado
    const start = elapsed; elapsed += b ?? 0;
    const clock = `${fmtMS(start)}–${fmtMS(elapsed)}`;
    let newAttrs = attrs.replace(/\sdata-clock="[^"]*"/, '');
    newAttrs = newAttrs.replace(/(\sdata-budget="[^"]*")/, `$1 data-clock="${clock}"`);
    return `<section${newAttrs}>${inner}</section>`;
  });
  if (!found) fail(`${f}: no contiene ninguna <section class="slide">`);
  slideHtml.push(`<!-- ===== ${f} ===== -->\n${src.trim()}\n`);
}

// ---------- fuentes ----------
let sources = existsSync(sourcesFile) ? readFileSync(sourcesFile, 'utf8') : '';
if (!sources.replace(/<!--[\s\S]*?-->/g, '').trim()) sources = '<h3>Fuentes</h3>\n<p>Sin fuentes registradas todavía.</p>';

if (errors.length) {
  console.error(`assemble: ${errors.length} error(es)\n` + errors.map(e => '  ✗ ' + e).join('\n'));
  process.exit(1);
}

// ---------- plantillas ----------
const head = read('head.html').replace(/\{\{(\w+)\}\}/g, (_, k) => {
  if (!(k in config)) { fail(`head.html usa {{${k}}} que no está en config.json`); return ''; }
  return esc(config[k]);
});
if (errors.length) { console.error(errors.join('\n')); process.exit(1); }

const runtimeCfg = Object.fromEntries(['topline', 'who', 'url', 'urlLabel', 'channel', 'x', 'linkedin', 'handle'].map(k => [k, config[k] ?? '']));
const overlays = read('overlays.html').replace('<!--@SOURCES@-->', sources.trim());

let html = [
  head.trimEnd(),
  `  <style>\n${read('fonts.css')}\n  </style>`,
  `  <style>\n${read('system.css')}\n${hoisted.join('\n')}\n  </style>`,
  '</head>',
  '<body>',
  read('body-open.html').trimEnd(),
  '',
  '  ' + read('defs.svg').trim(),
  '',
  '  <main class="deck" id="deck">',
  '',
  slideHtml.join('\n'),
  '  </main>',
  '',
  '  ' + overlays.trim(),
  '',
  `  <script>window.DECK_CONFIG = ${JSON.stringify(runtimeCfg).replace(/</g, '\\u003c')};</script>`,
  `  <script>\n${read('runtime.js')}  </script>`,
  '</body>',
  '</html>',
  '',
].join('\n');

if (makePublic) {
  // copia pública: sin notas y con data-public (sin barra de controles; N, P y ? desactivados)
  html = html.replace(/[ \t]*<aside class="notes">[\s\S]*?<\/aside>\n?/g, '');
  html = html.replace('<html lang="' + esc(config.lang) + '" class="no-js">', '<html lang="' + esc(config.lang) + '" class="no-js" data-public>');
}

writeFileSync(outFile, html);
const total = elapsed;
console.log(`assemble: ${count} diapositivas · presupuesto total ${fmtMS(total)} · ${(Buffer.byteLength(html) / 1024).toFixed(0)} KB → ${outFile}${makePublic ? ' (público)' : ''}`);
if (expect) {
  const want = parseMS(expect);
  if (want === null) { console.error(`--expect "${expect}" no es m:ss`); process.exit(1); }
  if (want !== total) { console.error(`✗ el presupuesto suma ${fmtMS(total)} y se esperaba ${expect} (diferencia ${total - want > 0 ? '+' : '−'}${fmtMS(Math.abs(total - want))})`); process.exit(1); }
  console.log(`✓ presupuesto = ${expect}`);
}
