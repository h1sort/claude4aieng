# PLAN — Taller "Tool use sin abstracciones"

Claude Community CDMX · lunes 19 oct 2026 · bloque de 40 min · audiencia: ingenieros.
Autor: Carlos Haro (@h1sort). Este archivo es la fuente de verdad para el enjambre de subagentes.

> **Para cada subagente:** lee este archivo completo, después solo tu sección de tarea en §6.
> Si escribes diapositivas, notas o revisas el deck, lee también `SPEAKER.md`.
> Escribe **solo** en las rutas que tu tarea declara como tuyas. Si necesitas algo fuera de tu
> carpeta, déjalo en `HANDOFF.md` bajo tu ID de tarea en lugar de editarlo.

---

## 1. Qué entregamos

1. **El bloque para el host** (texto, §2). Ya está redactado; solo se ajusta si cambia el alcance.
2. **El deck**: `deck/tool-use.html`, un solo HTML autocontenido con el mismo sistema visual que
   `h1sort/gbm-ai-meetup/ai-en-la-banca.html` ("institutional daylight"). Notas de presentador,
   modo presentador, `?still=1`, `?slide=N`, pasos con `data-step`. Español.
3. **El repo del taller** (este repo): un agente de ~100 líneas sobre la API de Claude sin
   frameworks, un arnés que lo rompe a propósito, y un script que mide su tasa de error.
   Un branch por paso (`paso-0` … `paso-5`) para que nadie se quede atrás.

Tesis del taller (una frase, va en la portada y el cierre): **el modelo propone, la aplicación
ejecuta, y eso se mide.**

## 2. Bloque para el host (formato pedido)

> 1️⃣ **Tool use sin abstracciones: del token al `tool_result`, y las formas en que se rompe**
>
> 2️⃣ Cada quien escribe a mano un agente sobre la API de Claude (sin frameworks) y lo rompe a
> propósito: historial con `tool_use` huérfano, JSON truncado por `max_tokens`, llamadas
> paralelas, y una llamada válida pero semánticamente peligrosa. Repara cada falla en código y sale
> midiendo la tasa de error de herramientas de su propio agente, por categoría y con costo por tarea.
>
> 3️⃣ Python 3.11+, `uv`, API key de Anthropic con créditos, y `uv sync` del repo antes del evento.

## 3. Guion de 40 minutos (contrato entre deck y código)

| Min | Bloque | En pantalla | Lo que teclea la gente | Branch al terminar |
|---|---|---|---|---|
| 0–5 | **Las herramientas son texto** | Gancho OpenRouter: el error de tool calls de un mismo modelo depende de quién lo sirve (GLM-5: ~8 % → ~1 % al enrutar por calidad, `FACTS.md` §8; o captura con fecha de la pestaña Performance). **No** usar "15 % vs 0.01 %": no verificado. Plantilla de chat de Qwen renderizada. | `uv run taller/plantilla.py` | `paso-0` |
| 5–15 | **El bucle a nivel cable** | `stop_reason`, `tool_use.id`, `tool_result` primero en el mensaje, paralelas con `asyncio.gather`. | Completan `taller/agent.py` (el loop). **Rotura #1**: matar el proceso entre `tool_use` y `tool_result`, reanudar → 400. Arreglo: sanear historial con `is_error`. | `paso-1`, `paso-2` |
| 15–22 | **Decodificación restringida y su límite** | JSON Schema → gramática libre de contexto → autómata de pila → máscara de logits a −∞ (XGrammar). | **Rotura #2**: `max_tokens` bajo → tool call truncada. Arreglo: revisar `stop_reason`, nunca parsear una llamada cortada. | `paso-3` |
| 22–32 | **Válido ≠ correcto** | `strict: true` garantiza forma, no significado. MCP: credenciales que el modelo nunca ve. | **Rotura #3**: `DROP TABLE` válido por esquema. Arreglo: compuerta (autorizador de SQLite) que devuelve `is_error` y el modelo se corrige. | `paso-4` |
| 32–38 | **Medir** | Tabla de errores por categoría + tokens y costo por tarea; dos modelos lado a lado. | `uv run taller/medir.py` | `paso-5` |
| 38–40 | **Cierre** | El modelo propone, la aplicación ejecuta — ahora con números. QR al repo. | — | — |

**Orden de recorte si vamos tarde** (nunca recortar *Medir*): 1) comparación de dos modelos,
2) llamadas paralelas, 3) detalle del autómata de pila (dejar solo la máscara de logits).

## 4. Hechos verificados (no reinventar; citar)

Verificado contra la documentación el 2026-10-18:

- `tool_result` debe ir **inmediatamente** después del mensaje con los `tool_use`, y dentro del
  mensaje de usuario los `tool_result` van **primero**; texto antes de ellos → **400**. Mensaje de
  error a mostrar en la diapositiva: *"tool_use ids were found without tool_result blocks immediately after"*.
  — https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls
- `is_error: true` en el `tool_result` cuando la herramienta falla; el contenido debe ser
  instructivo (qué falló y qué intentar). Ante llamadas inválidas Claude reintenta 2–3 veces. — misma página.
- `strict: true` en la definición de la herramienta valida el input contra el esquema.
  — https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
- ⚠️ **Trampa para el taller**: en Claude Opus 5.5, Sonnet 5.5, Fable 5.1 y Mythos 5.1,
  `tool_choice` `any` y `tool` devuelven **400**. Recomendado: `auto` con strict tool use.
  No enseñar "forzar la herramienta" en esos modelos; sí mencionarlo como trampa.
  — https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
- `name` de herramienta: `^[a-zA-Z0-9_-]{1,128}$`. — misma página.

**Por verificar en W0-B** (§6): `disable_parallel_tool_use` (nombre exacto y dónde va), manejo
documentado de `stop_reason: "max_tokens"` con un `tool_use` incompleto, si strict tool use es GA o
beta (y header), API exacta del Tool Runner del SDK de Python, precios por MTok de los modelos que
compararemos, y el estado actual del benchmark de OpenRouter. **Resuelto en `FACTS.md`** (2026-10-18). Todo hecho que llegue a una diapositiva debe estar en `FACTS.md` con URL.

## 5. Convenciones

- **Idioma**: diapositivas, notas, mensajes de consola y comentarios en español. Identificadores
  de código en inglés. Términos de la API tal cual (`tool_use`, `stop_reason`).
- **Python**: 3.11+, `uv`, scripts con metadatos PEP 723 como `gbm-ai-meetup/demo/agent.py`.
  Dependencias mínimas: `anthropic`, `jinja2`. Nada de LangChain ni frameworks de agentes.
- **Modelo**: siempre `os.environ.get("MODEL_ID", "claude-sonnet-5-5")`. `max_tokens` explícito.
- **Sin red en el venue**: nada se descarga en vivo salvo llamadas a la API. La plantilla de Qwen
  se versiona como JSON en `taller/vendor/` (solo `tokenizer_config.json`, no pesos).
- **`.gitignore` ignora `build/` y `dist/`**: el código fuente del deck vive en `deck/src/` y las
  herramientas en `deck/tools/`, nunca en `build/`.
- **Marcadores de paso** en el código de solución: `# >>> paso-N` … `# <<< paso-N`. El cortador
  (W2-A) los usa para generar cada branch; en `paso-(N-1)` ese bloque se reemplaza por `# TODO(paso-N)`.
- **Sin sobreafirmaciones** (lección de la charla de GBM): nada de "nunca", "garantiza" o "nadie lo
  tiene en producción" sin fuente. Los números del deck vienen de `FACTS.md` o de una corrida medida.
- **Commits**: uno por tarea, mensaje `W1-C: …`. No `git add -A`.

## 6. Tareas por ola

Cada tarea es independiente dentro de su ola. Modelo: **Sonnet 5.5** salvo que se indique.

### Ola 0 — cimientos (3 en paralelo)

**W0-A · Extraer el sistema visual** — dueño de `deck/src/shell/`, `deck/tools/`, `deck/SYSTEM.md`
- Fuente: `gbm-ai-meetup/ai-en-la-banca.html` (clonar en solo lectura). Su `build/` original no
  está en el repo: hay que reconstruirlo desde el HTML ensamblado.
- Separar en: `shell/head.html` (meta, OG), `shell/fonts.css` (los `@font-face` con base64 tal cual),
  `shell/system.css` (tokens `:root`, atmósfera, chrome, tipografía, código, paneles, **gramática de
  diagramas** `.dg`, reveals, overlays, presentador, `still`, reduced-motion, no-js, `data-public`),
  `shell/defs.svg` (marcadores `arr`, `arr-ev`, `arr-mod`, `arr-act`, `bar-act`), `shell/runtime.js`
  (navegación, pasos, notas, presentador vía BroadcastChannel, rueda/touch).
- Parametrizar lo específico de GBM: texto de `.topline` ("AI en la banca" → "Tool use"), `.who`
  ("GBM AI Experience" → "Claude Community CDMX"), URL del footer (→ `h1sort.com/claude4aieng`),
  nombre del BroadcastChannel, título/OG.
- `deck/tools/assemble.mjs`: concatena shell + `deck/src/slides/*.html` en orden → `deck/tool-use.html`.
- `deck/tools/shot.mjs`: Playwright, `?still=1&slide=N`, tamaños `1920x1080,1280x720,390x844`;
  falla si algún `.slide` desborda (scrollHeight > clientHeight) y guarda PNGs en `deck/shots/` (ignorado).
- `deck/SYSTEM.md`: guía corta para autores de diapositivas: clases, tokens semánticos
  (`--evidence` = autorizado/ejecutado, `--action` = consecuencia/compuerta/rechazo, `--warm` = región
  del modelo/propuestas), trazos (`.exec` sólido, `.propose` discontinuo, `.return` punteado,
  `.refuse` termina en ⊣), `data-step`, formato de `<aside class="notes">` (Propósito con tiempo,
  blockquotes con lo que se dice, `.warn`, Transición), atributos `data-title/section/budget/clock`.
- Aceptación: un `deck/src/slides/00-smoke.html` de prueba ensambla y se ve idéntico en estilo a una
  diapositiva de GBM; `shot.mjs` pasa.

**W0-B · Verificar hechos** — dueño de `FACTS.md`
- Resolver cada punto "por verificar" de §4 en la documentación oficial (platform.claude.com) y
  fuentes primarias. Para la clase de CMU (https://youtu.be/jXChFB4JSyw): confirmar curso, profesor
  y fecha; anotar los minutos que usamos (formatos de tool call 17:00–22:00, IDs huérfanos 25:20,
  XGrammar 27:00–35:30, credenciales MCP 41:30, OpenRouter 51:40). Paper de XGrammar y de CodeAct con URL.
- Formato: una línea por hecho, `- [hecho] — fuente (URL) — verificado AAAA-MM-DD`. Marcar
  `NO VERIFICADO` lo que no se pueda confirmar; esos hechos no entran al deck.

**W0-C · Andamio y contrato del código** — dueño de `pyproject.toml`, `taller/__init__.py`,
`taller/contracts.py`, `data/`, `scripts/seed.py`, `scripts/check.py`
- `pyproject.toml` con `uv`; `uv sync` debe funcionar sin red después del primer sync.
- `scripts/seed.py` → `data/banco.sqlite` sintético y pequeño (≤ 1 MB): `clientes`, `cuentas`,
  `transacciones`, `tarjetas`, más una tabla `secretos` que la compuerta debe proteger. Semilla fija.
- `taller/contracts.py`: firmas y tipos compartidos (sin lógica): `ToolSpec`, `ToolOutcome`
  (`ok | rejected | exec_error`), `TurnRecord` (tokens in/out, stop_reason, llamadas, resultados,
  latencia), `ErrorCategory` (`wrong_tool`, `bad_args`, `gate_rejected`, `exec_error`,
  `truncated`, `orphaned`). Todas las tareas de Ola 1 importan de aquí.
- `scripts/check.py`: verifica Python ≥ 3.11, `ANTHROPIC_API_KEY`, una llamada mínima con
  `max_tokens: 1` (créditos), y que existe `data/banco.sqlite`. Mensajes en español, accionables.

### Ola 1 — construcción (7 en paralelo, tras Ola 0)

**W1-A · El agente** — dueño de `taller/agent.py`, `taller/tools.py`
- Loop a mano con el SDK `anthropic` (sin Tool Runner): enviar `tools`, iterar mientras
  `stop_reason == "tool_use"`, ejecutar cada `tool_use`, devolver todos los `tool_result` en **un**
  mensaje de usuario, primero y con su `tool_use_id`. Paralelas con `asyncio.gather`. Límite de turnos.
- Herramientas: `sql_query` (lectura sobre `data/banco.sqlite`) y `bloquear_tarjeta` (escritura que
  exige confirmación humana en la terminal antes de ejecutar). `strict: true` en ambas.
- Consola como la demo de GBM: etapas SOLICITUD / VALIDACIÓN / EJECUCIÓN / OBSERVACIÓN / RECHAZADA con color.
- Registrar cada turno como `TurnRecord` en `runs/*.jsonl` (ignorado por git).
- Marcadores `# >>> paso-1` (loop básico), `paso-2` (saneo de huérfanos al reanudar), `paso-3`
  (manejo de `max_tokens`), `paso-4` (llamada a la compuerta). ≤ ~120 líneas sin contar comentarios.
- No usar `tool_choice` `any`/`tool` (ver trampa en §4).

**W1-B · La compuerta** — dueño de `taller/gate.py`
- Reusar la idea de `gbm-ai-meetup/demo/agent.py`: compilar con `EXPLAIN` sobre una copia vacía del
  esquema y `set_authorizer` de `sqlite3` — solo `SELECT`/lectura de tablas permitidas, una sola
  sentencia, `secretos` prohibida, sin `load_extension`. Determinista, sin LLM.
- Devuelve `None` o un motivo instructivo en español para `is_error` (qué falló y qué intentar).
- Pruebas `tests/test_gate.py`: `DROP`, `DELETE`, `ATTACH`, dos sentencias, lectura de `secretos`,
  CTE recursiva válida, `SELECT` válido.

**W1-C · El arnés de roturas** — dueño de `taller/romper.py`, `tests/test_romper.py`
- `uv run taller/romper.py huerfano|truncado|paralelo|drop`:
  - `huerfano`: guarda historial con un `tool_use` sin resultado, reanuda → muestra el 400 real y
    luego la reparación (insertar `tool_result` con `is_error`).
  - `truncado`: `max_tokens` muy bajo para forzar `stop_reason: "max_tokens"` a mitad de un
    `tool_use`; muestra el bloque cortado y que el agente no lo ejecuta.
  - `paralelo`: pregunta que dispara 3 llamadas independientes; mide tiempo secuencial vs `gather`.
  - `drop`: prompt adversarial que lleva al modelo a proponer `DROP TABLE` válido por esquema;
    la compuerta lo rechaza y el modelo se corrige.
- Cada modo imprime antes/después y es reproducible; si el modelo no cae en la trampa, el modo
  inyecta la llamada directamente (como `/sql` en la demo de GBM) y lo dice en pantalla.

**W1-D · Medir** — dueño de `taller/medir.py`, `evals/prompts.jsonl`
- 20 prompts en español con resultado esperado (herramienta correcta y/o verificación de la
  respuesta contra SQL de referencia). Incluir 3 adversariales y 2 que no requieren herramienta.
- Corre el agente sobre los 20 con `MODEL_ID` (y opcionalmente `--vs otro-modelo`), clasifica por
  `ErrorCategory`, y reporta tokens, costo (precios de `FACTS.md`) y costo **por tarea resuelta**.
- Salida: tabla en terminal + `runs/medicion-*.json`. Concurrencia acotada para no pegarle al rate limit.

**W1-E · La plantilla de chat** — dueño de `taller/plantilla.py`, `taller/vendor/`
- Renderizar con `jinja2` el `chat_template` de Qwen (versionado en `taller/vendor/`) para un
  mensaje con herramientas y una respuesta con tool call. Mostrar el texto crudo con los tokens
  especiales resaltados. Sin `transformers`, sin pesos, sin red.
- Segundo modo: el mismo intercambio con el formato de otra familia (Mistral o DeepSeek) para que se
  vea que un parser de una no sirve para la otra.

**W1-F · Diapositivas, parte 1 (min 0–15)** — dueño de `deck/src/slides/01-*.html` … `05-*.html`
- Portada; gancho OpenRouter (gráfico de barras, cifras de `FACTS.md`); quién es este tipo (breve,
  sin repetir redes al final como en GBM); "las herramientas son texto" (plantilla renderizada);
  el bucle a nivel cable (diagrama `.dg` con `tool_use.id` ↔ `tool_result`); rotura #1.
- Diagramas en la gramática `.dg` de `deck/SYSTEM.md`, con `data-step` para construir en vivo.

**W1-G · Diapositivas, parte 2 (min 15–40)** — dueño de `deck/src/slides/06-*.html` … `12-*.html`
- Decodificación restringida (CFG → autómata de pila → máscara de logits; el límite de
  `max_tokens`); rotura #2; válido ≠ correcto; compuerta; MCP y aislamiento de credenciales; medir
  (espacio para pegar la tabla real de W2-C); cierre con QR a `h1sort.com/claude4aieng` y crédito a la clase de CMU.
- Suma de `data-budget` de W1-F + W1-G = 40:00 exactos (ver §3).

### Ola 2 — integración (3 en paralelo, tras Ola 1)

**W2-A · Cortar los branches** — dueño de `scripts/cortar_pasos.py`
- Desde `main` (solución completa) generar `paso-0`…`paso-5` reemplazando bloques
  `# >>> paso-N` por `# TODO(paso-N)` en los pasos anteriores. Cada branch debe correr
  (aunque falle con un mensaje claro en el TODO). Push de los 6 branches.

**W2-B · README para asistentes** — dueño de `README.md`
- Instalación en 3 comandos, `scripts/check.py`, cómo cambiar de branch si te quedas atrás,
  qué hace cada script, crédito a la clase de CMU y enlace al deck.

**W2-C · Corrida real y QA del deck** — dueño de `deck/src/slides/11-*.html` (solo la tabla) y `HANDOFF.md`
- Requiere `ANTHROPIC_API_KEY` (Carlos lo corre local si el entorno del agente no llega a la API).
- Correr `romper.py` (los 4 modos) y `medir.py --vs`; pegar la tabla real en la diapositiva de medir.
- `node deck/tools/assemble.mjs && node deck/tools/shot.mjs deck/tool-use.html` sin desbordes.

### Ola 3 — revisión (1, modelo Opus)

**W3-A · Revisión en frío** — sin escribir código; reporte en `HANDOFF.md`
- Un agente que no vio la construcción revisa: cada número del deck contra `FACTS.md`, cada
  afirmación sin fuente, que el guion de §3 coincida con branches y diapositivas, que `data-budget`
  sume 40:00, y las fallas de la charla de GBM (relleno, autopromoción repetida, sobreafirmar).

## 7. Riesgos

- **Créditos**: si el host no los da, el taller muere en el minuto 5. Pedir confirmación hoy;
  plan B: pares de trabajo, y `romper.py` funciona en modo "inyectado" sin gastar mucho.
- **40 min es poco** para escribir código en vivo: el estudiante teclea el loop y
  tres arreglos cortos (3, 4 y 1 líneas). Todo lo demás ya viene en el branch.
- **Wifi del venue**: `uv sync` antes del evento (lo pide el bloque del host); nada se descarga en vivo.
- **Plazo**: el taller es mañana. Si falta tiempo, prioridad: W1-A, W1-B, W1-C, W0-A, W1-F/G, W1-D;
  la comparación de modelos y la publicación en h1sort.com quedan opcionales.

## 8. Fuera de alcance (por ahora)

- ~~Publicar el deck en `h1sort.com/claude4aieng`~~: publicado el 2026-10-18 (h1sort-website PR #21); refrescar con `.claude/skills/publish-to-site`.
- MCP en vivo (otros ponentes probablemente lo cubren; aquí solo el porqué de las credenciales).
