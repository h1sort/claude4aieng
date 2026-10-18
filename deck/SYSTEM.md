# SYSTEM — guía para autores de diapositivas

Sistema visual "institutional daylight" (papel marfil, tinta verde, cobre = consecuencia), extraído de
`ai-en-la-banca.html` y reconstruido en `deck/src/shell/`. Un deck = un HTML autocontenido.

```
deck/src/shell/   head.html · fonts.css (base64, no tocar) · system.css · defs.svg · body-open.html
                  overlays.html · runtime.js · config.json   ← no editar desde una tarea de diapositivas
deck/src/slides/  NN-nombre.html   ← un parcial por diapositiva (o varias <section>); orden = nombre de archivo
deck/src/sources.html             ← contenido del overlay Fuentes (tecla S)
deck/tools/       assemble.mjs · shot.mjs
```

## Comandos

```bash
node deck/tools/assemble.mjs                 # → deck/tool-use.html (imprime nº de diapositivas y suma de data-budget)
node deck/tools/assemble.mjs --expect 40:00  # además falla si el presupuesto no suma 40:00
node deck/tools/assemble.mjs --public        # copia sin notas y con data-public (sitio): sin HUD, N/P/? desactivados
node deck/tools/shot.mjs deck/tool-use.html  # PNG en deck/shots/ (ignorado) y falla si algo desborda
node deck/tools/shot.mjs deck/tool-use.html --sizes 1280x720 --only 3,4
# probar en vivo:  cd deck && python3 -m http.server 8000  →  http://localhost:8000/tool-use.html
```

`assemble` **falla** si una diapositiva no tiene `<aside class="notes">`, `data-title`, `data-section`,
`data-budget` (formato `m:ss`) o una clase `sNN` única. `data-clock` **no se escribe**: lo calcula
`assemble` acumulando los `data-budget` (`0:00–0:20`, …).

URLs: `?slide=N` · `?slide=N&step=K` · `?still=1` (todo apilado y visible) · `?still=1&slide=N` (solo esa
diapositiva, sin pasos ni animación: lo que usa `shot.mjs`) · `?presenter=1` (ventana del presentador;
sincroniza por BroadcastChannel `tool-use`, **requiere http://**, no funciona desde `file://`).
Teclas: → espacio AvPág siguiente · ← RePág anterior · Inicio/Fin · **N** notas · **P** presentador ·
**S** fuentes · **F** pantalla completa · **?** ayuda · Esc cierra.

## Esqueleto de diapositiva (copiar y pegar)

```html
<style>
  /* CSS propio, SIEMPRE acotado a la clase de la diapositiva (ver "CSS por diapositiva") */
  .s07 h2{max-width:20ch}
</style>

<!-- ============ 07 · título corto ============ -->
<section class="slide s07" data-title="Título que ve el presentador" data-section="El bucle" data-budget="1:30"
         style="--slide-accent:var(--action)">
  <div class="main">
    <div class="hd">
      <p class="eyebrow reveal">Etiqueta</p>
      <h2 class="reveal d1">Titular con <em>énfasis</em></h2>
      <p class="lede reveal d2">Una línea de apoyo.</p>
    </div>
    <div class="figure fill reveal d2">
      <svg class="dg" viewBox="0 0 1000 440" role="img" aria-label="Descripción completa del diagrama para lectores de pantalla.">
        <!-- ver "Gramática de diagramas" -->
      </svg>
    </div>
  </div>
  <aside class="notes">
    <p><strong>Propósito:</strong> qué debe entender la sala al salir de aquí. (1:30)</p>
    <blockquote>Lo que dice el ponente, en voz natural.</blockquote>
    <p class="warn">Advertencia: lo que NO se debe decir o lo que hay que preparar antes.</p>
    <p><strong>Transición:</strong> “Frase puente a la siguiente.”</p>
  </aside>
</section>
```

- `data-section` va a la esquina superior derecha. `data-title` solo se ve en notas/presentador.
- `--slide-accent` tiñe eyebrow, `<em>`, línea superior, grid y resplandor: `var(--evidence)` (verde, por
  defecto), `var(--action)` (cobre) o `var(--warm-ink)` (dorado).
- Modificadores de `.slide`: `bare` (portada: oculta cabecera y pie salvo enlaces), `nofoot` (sin pie),
  `quiet` (sin movimiento detrás, p. ej. un QR), `cover` (portada: ver abajo).
- Dentro de `.main` (centrado vertical, con `gap`): `.hd` (eyebrow+h2+lede), `.split` (2 columnas;
  `.even`, `.wide-left`), `.cols3`, `.stack`, `.figure` (caja del SVG; `fill` = ocupa el resto), `.panel`
  (`.ev` `.act` `.mod` = filete superior verde/cobre/dorado discontinuo), `.code`, `.chips`, `.quote`+`.cite`.
- Tipografía: `h1` (portada), `h2`, `.statement` (frase grande, ≤ ~16ch), `.lede`, `.body`, `.label`
  (mono en mayúsculas), `.eyebrow`, `.tag` (`.live` cobre = demo en vivo, `.illus` dorado = ilustrativo),
  `.num` (cifras). `<em>` dentro de h1/h2/.statement = cursiva en el color de acento.
- Entradas: `.reveal` + `.d1`…`.d6` (retardo escalonado). Todo `.reveal` se ve completo en `?still` y con reduced-motion.
- **Portada**: `<section class="slide cover bare s01">` con `.motif` (SVG a la derecha, hijos de `<g>`
  entran escalonados; clases `.pt .stray .slot .slotbar .lead .tick` y `.gate`) y `.main` con
  `.eyebrow`, `h1 > span*2`, `.sub`, `.byline` (`.rule` + `.label`).
- **Código**: `<div class="code"><span class="cap">archivo · L10–20</span>…</div>`; colores `.k` (evidencia,
  palabra clave), `.s` (cadena), `.c` (comentario), `.a` (acción/atención). Con números de línea:
  `class="code lined"` y `<span class="ln" data-n="12" style="--i:4">…</span>` por línea.

## Gramática de diagramas (`<svg class="dg">`)

El significado va en **forma + estilo de trazo + palabra**, no solo en color (se proyecta en una sala).
Escribe el `viewBox` con ancho ≈ 1000 para que el texto (`.t-mono` 14px, `.t-sub` 14px, `.t-lbl` 16px) se
lea a ≥ 12 px en un proyector de 1280.

| Clase | Qué es | Se ve como |
|---|---|---|
| `.model` | región del modelo (donde se *propone*) | rect redondeado, punteado dorado |
| `.app` | aplicación / runtime de confianza (donde se *ejecuta*) | rect con borde tinta |
| `.gate` | compuerta de confianza | barra alta con borde cobre (+ dos rayitas `path` a media altura) |
| `.reach` | frontera de lo alcanzable | rect discontinuo verde |
| `.node` (`.ev` `.act` `.mod` `.ghost`) | caja/nodo; `.ev` autorizado, `.act` consecuencia, `.mod` propuesta del modelo, `.ghost` pendiente / fuera de alcance | borde tinta / verde / cobre / punteado dorado / gris discontinuo |
| `.join` | punto de unión de evidencia | rombo cobre |
| `.exec` (+`.big`) | **ejecución permitida / flujo requerido** | trazo **sólido** verde (`.big` más grueso) |
| `.propose` | **solicitud o propuesta: aún NO es un efecto** | **discontinuo** dorado |
| `.return` | observación / retroalimentación (`tool_result`) | **punteado** verde |
| `.refuse` | rechazo; termina en barra ⊣ (`marker-end="url(#bar-act)"`) | sólido cobre con tope |
| `.wire` | conexión neutra | gris fino |
| `.rail` | riel operativo | guion-punto tenue |
| `.loop` | flecha de "otro turno" | arco dorado |
| `.stopsq` | cuadrito de condición de salida | negro |
| `.t-title` `.t-lbl` `.t-sub` `.t-mono` | texto: título serif · etiqueta · subtexto · mono mayúsculas | |
| `.t-ev` `.t-act` `.t-mod` | color de texto verde / cobre / dorado | |

Marcadores (definidos en `defs.svg`, úsalos con `marker-end`): `url(#arr)` gris, `url(#arr-ev)` verde,
`url(#arr-mod)` dorado (para `.propose`), `url(#arr-act)` cobre, `url(#bar-act)` barra de rechazo ⊣.

Animación de trazos: añade `.draw` y `pathLength="1"` a un `path` sólido (`.exec`, `.refuse`, `.wire`) y se
dibuja al llegar su paso; `.propose`/`.return`/`.rail` con `.draw` aparecen en fundido (**no** les pongas
`pathLength`: el runtime lo quita porque deforma los guiones). `.exec.flow` añade un pulso que viaja.

## Semántica de color

| Token | Color | Significa | Úsalo para |
|---|---|---|---|
| `--evidence` | verde `#257a68` | autorizado, ejecutado, evidencia | `.exec`, `.return`, ✓, resultado correcto |
| `--action` | cobre `#b75437` | consecuencia, compuerta, rechazo, incertidumbre | `.gate`, `.refuse`, ✕, errores, "aquí se rompe" |
| `--warm` / `--warm-ink` | dorado | región del modelo, propuestas | `.model`, `.propose`, `tool_use` aún sin efecto |
| `--ink` / `--ink-2` / `--ink-dim` | verde oscuro | texto / texto secundario / apagado | todo lo demás |
| `--paper`, `--paper-hi` | marfil | fondo / superficie elevada | cajas, paneles |

Regla de oro del deck: **nunca animar una solicitud como ejecutada antes de cruzar la compuerta.** Una
solicitud es discontinua dorada; un efecto es sólido verde.

## `data-step` (construir en vivo)

Cualquier elemento con `data-step="n"` aparece en el n-ésimo "siguiente" (→) dentro de la diapositiva;
al terminar los pasos, → pasa a la siguiente. En SVG ponlo en un `<g>`:

```html
<g data-step="1"> <path class="propose draw" d="…" marker-end="url(#arr-mod)"/> <text class="t-sub">…</text> </g>
<g data-step="2"> <path class="exec big draw flow" pathLength="1" d="…" marker-end="url(#arr-ev)"/> … </g>
```

- Empieza en 1 y no saltes números. Describe los pasos en las notas ("Pasos con →: 1 …; 2 …").
- Con `?still`, reduced-motion y sin JS todo se ve a la vez: el diseño final **debe leerse con todos los
  pasos visibles** (es lo que captura `shot.mjs`).

## Formato de `<aside class="notes">`

Obligatorio. Se ve con **N** y en la ventana del presentador. Estructura:

1. `<p><strong>Propósito:</strong> …(m:ss)</p>` — qué debe llevarse la sala, con el tiempo asignado.
2. `<blockquote>…</blockquote>` — **lo que se dice**, una frase por bloque, tal cual.
3. `<p>` opcionales: pasos con →, procedimiento de demo (`<ol>`), comandos en `<code>`.
4. `<p class="warn">…</p>` — advertencias en cobre: qué no afirmar, qué preparar antes, plan B si falla la red/API.
5. `<p><strong>Transición:</strong> “…”</p>` — la frase puente.

Sin sobreafirmaciones: cada cifra o hecho debe estar en `FACTS.md`; evita "nunca", "garantiza" sin fuente.

Atributos de `<section>`: `data-title` (nombre), `data-section` (rótulo superior derecho), `data-budget`
(`m:ss`; la suma de todo el deck debe dar 40:00), `data-clock` (**calculado**, no escribir).

## CSS por diapositiva

Convención: un `<style>` **dentro del parcial**, antes de la `<section>`, con reglas acotadas a la clase
`sNN` de esa diapositiva (`.s07 .figure{…}`). `assemble.mjs` extrae todos los `<style>` de los parciales
y los junta en el `<style>` del `<head>`, después de `system.css`. Reglas:

- La clase `sNN` es obligatoria y única en todo el deck (`s07`, `s07b`); usa el número del archivo.
- Nunca reglas sin acotar ni overrides de clases del sistema fuera de `.sNN`.
- Si una regla sirve a varias diapositivas, proponla en `HANDOFF.md` para `system.css` en vez de copiarla.
- Respeta las escalas `--t-*` (usa `clamp()`), y comprueba 1280×720 y 1920×1080 con `shot.mjs`.
- Para animaciones propias usa `.sNN.active …` y desactívalas con `html[data-still] .sNN … {animation:none!important}`
  y en `@media (prefers-reduced-motion:reduce)`.

## Trampas conocidas

- La fuente embebida (latin) no trae `→ ← ≠ ≥ ⊣ ✓ ✕`; caen a la fuente del sistema (se ven bien, pero no
  uses esos glifos en tamaño hero). `↑ ↓ − ∕` sí están.
- 390×844 existe para revisar que nada se corte; los diagramas se ven pequeños, es normal. Lo que no
  puede pasar es desborde (`shot.mjs` lo detecta).
- `window.open` del presentador y el canal `tool-use` requieren servir por http; `file://` abre pero no sincroniza.
- Fuera de `data-public` el HUD (NOTAS · FUENTES · ? · ⛶) aparece al pasar el mouse.
