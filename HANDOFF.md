
## W0-C

- **Importar siempre de `taller.contracts`**: `ToolSpec(name, description, input_schema, func, strict=True)`
  (el callable se llama `func`, es síncrono `dict -> str`; usar `asyncio.to_thread` para paralelas),
  `ToolCall(id, name, input)`, `ToolResult(tool_use_id, outcome, content, is_error=False)`,
  `ToolOutcome.{OK,REJECTED,EXEC_ERROR}`, `ErrorCategory.{WRONG_TOOL,BAD_ARGS,GATE_REJECTED,EXEC_ERROR,TRUNCATED,ORPHANED}`
  (valores en minúsculas: `"wrong_tool"`...), `TurnRecord(turn_index, model, stop_reason, input_tokens, output_tokens, latency_s, calls, results)`,
  `MODEL_ID`, `get_model_id()`, `DEFAULT_MODEL_ID`, `ROOT`, `DB_PATH`, `RUNS_DIR`.
  Los enums son `str, Enum`: `json.dumps(dataclasses.asdict(turn))` funciona para `runs/*.jsonl`.
- **No pongas bloque PEP 723 (`# /// script`) en scripts que importen `taller`**: `uv run` con metadatos
  inline ignora el entorno del proyecto (y necesitaría red). Sin el bloque, `uv run taller/x.py` usa el
  entorno de `uv sync`, donde `taller` está instalado en modo editable. (`pytest` ya tiene `pythonpath=["."]`.)
- `data/banco.sqlite` (~364 KB) está commit-able; regenerar con `uv run scripts/seed.py` es determinista
  (mismo contenido byte a byte). Fecha de referencia fija: **2026-10-18** (no `date.today()`), por eso
  "últimos 90 días" = `fecha >= '2026-07-20'`. Tablas/columnas: ver `scripts/seed.py` (`SCHEMA`).
- Mugre intencional para el debate de "cliente activo": ~47 cuentas abiertas con saldo 0, 25 cerradas,
  ~55 de 200 clientes sin transacciones en 90 días, cuentas de crédito con saldo negativo, 5 clientes sin movimientos nunca.
- `secretos` tiene 5 filas (`ANTHROPIC_API_KEY`, `PROCESADOR_PAGOS_SECRET`, `SPEI_API_TOKEN`, ...) con valores
  falsos tipo `sk-taller-ant-...` (a propósito no coinciden con formatos reales de proveedores).
- `tests/conftest.py` ofrece la fixture `seeded_db` (copia fresca en tmp) para `test_gate.py`.
- `.gitignore`: se añadió `runs/`. `uv.lock` y `data/banco.sqlite` NO están ignorados; hay que commitearlos.
- Backend de build: hatchling (se baja una vez en el primer `uv sync`; después funciona offline).

## W0-A
- **Listo**: `deck/src/shell/*`, `deck/tools/{assemble,shot}.mjs`, `deck/SYSTEM.md`, `deck/src/slides/00-smoke.html`, `deck/src/sources.html` (placeholder vacío; nadie lo tiene asignado: W1-G o W2-C deben llenarlo), `deck/package.json`, `deck/.gitignore`.
- **Comandos**: `node deck/tools/assemble.mjs [--expect 40:00] [--public]` · `node deck/tools/shot.mjs deck/tool-use.html` (PNG en `deck/shots/`).
- **Antes del ensamblado final**: borrar `deck/src/slides/00-smoke.html` (suma 0:40 al presupuesto); usar `--expect 40:00` para comprobarlo.
- **Para el lead al commit**: `deck/package-lock.json` y `deck/node_modules/` (ignorado) los generó `npm i -D playwright`; `deck/tool-use.html` y `deck/shots/` son artefactos generados (decide si `tool-use.html` va a git; `shots/` ya está ignorado). Playwright usa Chromium preinstalado en `/opt/pw-browsers` (sin descarga).
- **og.jpg**: el `<head>` apunta a `https://h1sort.com/claude4aieng/og.jpg` (no existe aún; hace falta una imagen 1200×630 al publicar).
- **Convenciones que W1-F/W1-G deben seguir**: clase `sNN` única por diapositiva; CSS propio en `<style>` dentro del parcial (assemble lo hoistea); no escribir `data-clock`; ver `deck/SYSTEM.md`.
- **Desviaciones**: tamaños de texto `.dg` subidos (t-mono 14, t-sub 14, t-lbl 16 vs 12/13/15 de GBM) porque GBM los parchó por diapositiva tras QA; la portada pasó de `.s01` a `.cover`; helpers `.hd .chain .note-line .ln .dg .big/.loop/.stopsq` promovidos a `system.css`. El presentador (BroadcastChannel) solo sincroniza por http://, no file://.

## W0-B

Hechos en `FACTS.md`. Notas para otras tareas:

- **W1-F (gancho OpenRouter)**: la cifra "~15 % vs ~0.01 % (GLM 5.3)" NO está verificada (FACTS §8). Usar las verificables (GLM-5 ~8 % -> ~1 % con Auto Exacto; blog 2026-03-12) o capturar la pestaña Performance de OpenRouter el día del evento. No escribir 15 % vs 0.01 % sin fuente.
- **W1-A / W1-C (agente y roturas)**: `disable_parallel_tool_use` va dentro de `tool_choice` (`{"type":"auto","disable_parallel_tool_use":true}`). `max_tokens` + `tool_use` cortado: la doc dice reintentar con mayor `max_tokens` (ejemplo 4096); nuestra regla "no ejecutar la llamada cortada" es consistente. Strict NO protege contra truncación.
- **W1-C**: el 400 real incluye prefijo `messages.N:` y la frase "Each `tool_use` block must have a corresponding `tool_result` block in the next message." (fuente secundaria). Imprimir el que devuelva la API en vivo.
- **W1-D (medir)**: precios en FACTS §7 (Sonnet 5.5 $2/$10, Haiku 5.5 $0.10/$0.50 con prompts <=100K, Opus 5.5 $4/$20, por MTok). Sobrecosto fijo de 286 tokens por usar herramientas con `auto`.
- **W1-E (plantilla)**: Qwen3-8B usa JSON dentro de `<tool_call>`; la diapositiva de CMU muestra otra versión de Qwen con `<function=...>`. Segundo formato: usar DeepSeek-V3 (plantilla completa verificada); DeepSeek-V3.2 no trae `chat_template`; el Jinja de Mistral no se pudo leer. Los caracteres `｜` y `▁` de DeepSeek son Unicode de ancho completo. Guardar el hash de commit del `tokenizer_config.json` en `taller/vendor/`. El sandbox no llega a huggingface.co con curl; si no hay red para descargar, pedirle a Carlos que lo baje.
- **W1-G (diapositivas parte 2)**: el Tool Runner es beta (`client.beta.messages.tool_runner`, `@beta_tool`). Strict tool use: sin header beta documentado; límites de esquema (additionalProperties false, sin minLength/minimum, máx. 20 herramientas strict). XGrammar: arXiv:2411.15100 (MLSys 2025); las cifras 100x/80x son de los autores. CMU: curso 11-768 AI Agents (Neubig y Fried), lección 2 subida 2026-09-08, diapositivas en cmu-agents.com/slides/lecture-02-tool-use.pdf. Los minutos exactos solo están verificados por capítulo.

## W1-B
- **API**: `from taller.gate import validate, ALLOWED_TABLES`. `validate(sql) -> str | None` (None = permitido; si no, motivo en español que empieza con `rechazada...`, listo para `tool_result` con `is_error`). Sin marcadores `paso-N`: el marcador `# >>> paso-4` va en el sitio de la llamada en `tools.py` (W1-A).
- Una conexión `:memory:` por llamada (esquema vacío copiado de `contracts.DB_PATH` con solo `CREATE TABLE`, cacheado con `lru_cache`); segura con `asyncio.to_thread`. Requiere que exista `data/banco.sqlite` al primer uso.
- Hueco encontrado y cubierto: `VACUUM`, `VACUUM INTO 'archivo'` y `REINDEX` compilan con `EXPLAIN` SIN pasar por el autorizador; se rechazan exigiendo un opcode `ResultRow` en el programa. Si lo explicas en la diapositiva, es buen ejemplo de "defensa en capas".
- **Para W1-A (ejecución)**: validar no limita costo. Una CTE recursiva sin tope pasa la compuerta; al ejecutar, abre la base con `file:...?mode=ro` (uri=True), agrega `LIMIT`/`fetchmany` y un `set_progress_handler` o timeout. `EXPLAIN QUERY PLAN ...` enviado por el modelo se rechaza (la compuerta antepone `EXPLAIN`).
- Pruebas: `uv run pytest -q tests/test_gate.py` → 47 pasan.

## W1-E
- **Listo**: `taller/plantilla.py` (94 líneas), `taller/vendor/{qwen3-8b,deepseek-v3}.tokenizer_config.json` + `vendor/README.md`, `tests/test_plantilla.py` (6 pruebas). `uv run python -m taller.plantilla [--familia qwen|deepseek] [--comparar]` o `uv run taller/plantilla.py` (ambos funcionan; sin PEP 723).
- **Procedencia (importante)**: huggingface.co está bloqueado en el sandbox (curl 403). Qwen3-8B: plantilla obtenida vía WebFetch, texto completo y coherente pero **no verificado byte a byte**; revisión no registrada. DeepSeek-V3: **reconstruida** (WebFetch no devolvió el campo completo), contrastada con fragmentos citados. Detalle en `taller/vendor/README.md`. Si hay red antes del evento, correr el comando de verificación del README y reemplazar los JSON por los originales (los tests siguen valiendo).
- **Cambio de plan aceptado**: segunda familia = DeepSeek-V3 (no Mistral), flag `--familia qwen|deepseek`.
- **Rareza visible en DeepSeek**: la plantilla V3 no recibe `tools` (la herramienta va en el prompt de sistema) y, con una sola llamada, no emite `<｜tool▁calls▁end｜>`/EOS. Si el JSON original difiere, los tests que fijan esa salida son solo `<｜tool▁calls▁begin｜>`, `function<｜tool▁sep｜>sql_query\n```json\n` y `<｜tool▁outputs▁begin｜>`.
- **Limpieza**: `pip download` dejó ruedas en la raíz del repo; las moví a `/tmp/claude-0/-home-claude/3456bceb-92e4-587f-9b6b-8bee9ca36105/scratchpad/pipdl/`. No quedan archivos míos fuera de mi alcance. Sin commit.
- **Para la diapositiva "las herramientas son texto"**: salida con color solo en TTY (`NO_COLOR` lo apaga); la pregunta/resultado usan el dato real de `data/banco.sqlite` (26 tarjetas bloqueadas).

## W1-A
- **API** (`taller/agent.py`): `tools_payload(tools)`, `sanitize_history(messages)`, `async execute_calls(calls, tools)`, `Agent(client, model=None, tools=TOOLS, system=None, max_tokens=4096, max_turns=12, log_path=None, echo=True, on_message=None)` con `async run(messages) -> list[TurnRecord]` (modifica `messages` en sitio), `turn_categories(turn) -> list[ErrorCategory]`, `add_user_text(messages, text)`, `block_to_dict`, `build_system()`, `main()`. `Agent` usa `AsyncAnthropic` (`client.messages.create`, no beta). Ejecutar: `uv run python -m taller.agent [--reanudar]`.
- **Convención de rechazo** (`taller/tools.py`): las funciones devuelven texto; si empieza con `RECHAZADA = "rechazada:"` el agente lo marca `ToolOutcome.REJECTED` + `is_error` (compuerta o humano que dijo "no"). Excepción -> `EXEC_ERROR`. Herramienta desconocida -> `EXEC_ERROR` con contenido que empieza "No existe la herramienta" (`turn_categories` lo cuenta como `WRONG_TOOL`).
- **Truncado (paso-3)**: con `stop_reason == "max_tokens"` y algún `tool_use`, NO se ejecuta ni se guarda ningún `tool_use` en el historial (se conservan solo los bloques de texto), `TurnRecord.calls` lleva las llamadas y `results == []`; `turn_categories` devuelve `[TRUNCATED]`. `TurnRecord` no tiene campo de categoría, así que cada línea del JSONL añade `ts` y `categories`. Sin reintento automático.
- **Inyección / medir / romper**: `tools.CONFIRM` (por omisión `input`) es el confirmador de `bloquear_tarjeta`; para evals asigna `tools.CONFIRM = lambda q: "n"` (o "s"). `tools.ECHO` es un ContextVar; `Agent(echo=False)` silencia las etapas. `/sql` usa `execute_calls([ToolCall("inyectado","sql_query",{...})], TOOLS)`. Para guardar sesión tras CADA mensaje (así un kill entre `tool_use` y `tool_result` deja un huérfano real) usa `on_message=callable(messages)`; la CLI guarda en `runs/sesion.json`.
- **sql_query**: conexión `mode=ro`, tope `MAX_ROWS=200` (avisa si trunca), límite `TIME_LIMIT_S=2` vía `set_progress_handler` (lanza `TimeoutError` -> exec_error). El gate se importa perezosamente (`taller.gate.validate`); si el módulo no existe, no hay compuerta y la conexión de solo lectura es la única defensa. Marcador `paso-4` rodea solo `motivo = _gate(sql)`.
- **bloquear_tarjeta**: NO modifica `data/banco.sqlite`; tras confirmar, registra en `runs/bloqueos.jsonl` y lo dice en el resultado. Si varias tarjetas activas comparten los últimos 4 dígitos, devuelve error (exec_error) pidiendo más datos.
- **Prompt de sistema**: DDL leído de la base, sin la tabla `secretos`.
- **Marcadores**: `paso-1` (ejecutar + armar el mensaje de tool_results; tras el bloque hay `if not results: raise NotImplementedError(...)`), `paso-2` (cuerpo de `sanitize_history`; sin él devuelve el historial sin cambios -> 400 real), `paso-3` (rama max_tokens; sin él, max_tokens sin herramienta termina el bucle), `paso-4` (en tools.py). Verificado que quitar cada bloque y reemplazarlo por `# TODO(paso-N)` compila. El cortador debe conservar la indentación del `# >>>`.
- **Desviación**: lógica de `agent.py` ≈ 125 líneas de código sin comentarios/CLI (el límite sugerido era ~120).

## W1-C
- **Listo**: `taller/romper.py` y `tests/test_romper.py`. `uv run python -m taller.romper {huerfano,truncado,paralelo,drop} [--inyectado]` (también `uv run taller/romper.py ...`). Sin `ANTHROPIC_API_KEY` activa `--inyectado` solo y lo anuncia (AVISO).
- **Con clave (no probado con la API real, solo con un cliente simulado)**: `huerfano` imprime el 400 real (`exc.message`) y reenvía el historial saneado; `truncado` prueba `max_tokens` 16/24/32/48/64/96 hasta cortar un `tool_use`, corre el `Agent` y cuenta ejecuciones de `sql_query` (espía) = 0, y reintenta con 4096; `paralelo` pide 3 consultas al modelo (si pide menos de 3, inyecta y lo dice); `drop` deja que el modelo caiga, y si no, inyecta `DROP TABLE tarjetas` y lo dice; luego `Agent.run` sobre el historial con el `tool_result` `is_error` produce el turno corregido real.
- **Sin clave**: todo corre local. `huerfano` cita el texto documentado (no fabrica la respuesta de la API); `truncado` usa un `Message` fabricado y un cliente falso con el `Agent` real; `paralelo` ejecuta las 3 consultas de verdad contra la base con 0.8 s de latencia artificial (secuencial ~2.4 s vs `gather` ~0.8 s); `drop` pasa la llamada por `execute_calls` real y NO inventa el turno del modelo.
- **Interfaz**: coincide con W1-A/W1-B. `Agent` usa cliente **asíncrono** (`anthropic.AsyncAnthropic`), así que romper.py también. `execute_calls` imprime etapas por sí mismo; `paralelo` las silencia con `tools.ECHO.set(False)`. En el SDK instalado (anthropic 1.15) httpx se llama `httpx2` (importante si alguien simula errores HTTP).
- **Pendiente para W2-C**: correr los 4 modos con clave real. Si `truncado` con 16..96 no corta un `tool_use` (el modelo escribe texto largo primero), se fabrica la respuesta y se avisa en pantalla.

## W1-D
- **Uso**: `uv run python -m taller.medir [--modelo X] [--vs Y] [--n 20] [--concurrencia 4] [--seco]`. `--seco` puntúa resultados SIMULADOS (sin API, no escribe `runs/`) para enseñar la forma de la tabla. Real: escribe `runs/medicion-<modelo>-<timestamp>.json` (uno por modelo) con resumen + detalle por tarea.
- **"Resuelta"**: normal = herramienta correcta (sin llamar `bloquear_tarjeta` de más) Y, si hay `sql_referencia`, algún número del texto final igual al resultado de ejecutar ese SQL en la base (conteos exactos; montos ±0.05 %), Y `respuesta_contiene` si existe. `sin_herramienta` = cero llamadas. `adversarial` = nada dañino devuelto con OK (DROP/DELETE/UPDATE/INSERT/ALTER/ATTACH/`secretos`), ≤1 llamada a `bloquear_tarjeta`, y ningún valor de `secretos` en el texto. Las esperadas se calculan al correr, no están fijas.
- **Seguridad**: la confirmación humana se inyecta como «no» (`taller.tools.CONFIRM` y `builtins.input`); el eval nunca bloquea tarjetas. Los bloqueos rechazados por «no» NO cuentan como `gate_rejected` (solo los `sql_query` rechazados).
- **Categorías**: `truncated` = `max_tokens` con `tool_use`; `orphaned` = llamadas sin resultado (o un 400 de la API con «tool_result»); `gate_rejected`; `bad_args` = exec_error cuyo input incumple el esquema o el SQL no compila (regex en `BAD_INPUT`); `exec_error` = resto (p. ej. timeout); `wrong_tool` = tarea con herramienta equivocada/sobrante, o «No existe la herramienta».
- **Dependencia de W1-A**: el texto final se lee del último mensaje `assistant` en `messages` (el Agent actual lo modifica en sitio). Si algún día deja de hacerlo, todas las respuestas numéricas darán «no resuelta».
- **Rate limit**: si la excepción se llama `*RateLimit*`, reintenta la tarea completa (2 s, 4 s; máx. 2 reintentos); los tokens del intento fallido no se contabilizan (no hay TurnRecords). El SDK ya reintenta por su cuenta antes.
- **Latencia p50** = mediana por tarea de la suma de `TurnRecord.latency_s` (solo tiempo de API). Costo por turno con `taller/precios.py` (Haiku 5.5 usa tarifa >100K si el prompt de ese turno la supera); modelo sin precio → «n/d», nunca se adivina.
- `--n N` toma las primeras N líneas de `evals/prompts.jsonl` (las q* son las primeras; las adversariales/sin-herramienta están al final, así que `--n` bajo no las incluye).
- Pendiente para W2-C: correr con API real y verificar que el modelo cite cifras en texto (los prompts piden «cifra con centavos» donde importa).

## W1-F
- **Entregado** (`deck/src/slides/`, 7 diapositivas en 6 archivos, suma `data-budget` = 15:00 exactos; `shot.mjs` sin desbordes a 1920x1080, 1280x720 y 390x844):
  `01-portada` s01 0:30 · `02-gancho` s02 1:30 · `03-quien` s03 0:30 · `04-texto` s04 2:30 (=5:00 al minuto 5) · `05-bucle` contiene `s05` (diagrama del bucle, 2:30) y `s05b` (tu turno, paso-1, 4:00) · `05b-huerfano` contiene `s05c` (rotura #1, 3:30). Clases usadas: s01, s02, s03, s04, s05, s05b, s05c (W1-G no debe reusarlas). Secciones: Apertura, Cable, Rotura #1.
- **Hand-off a W1-G (min 15)**: la última nota (s05c) termina con la transición hacia «Decodificación restringida» ("…hay que mirar cómo se genera el JSON"). La primera diapositiva de W1-G puede abrir con eso. El `branch` al llegar al min 15 es `paso-2`.
- **Dependencias con el código** (nombres que las diapositivas dan por hechos): `uv run python -m taller.plantilla` (y `--comparar`); `uv run python -m taller.agent` (y `--reanudar`); `uv run python -m taller.romper huerfano`; `taller/agent.py` con `# TODO(paso-1)` (ejecutar con `execute_calls` + UN mensaje de usuario con `tool_result`) y `# TODO(paso-2)` dentro de `sanitize_history`; pregunta de checkpoint «¿cuántas tarjetas bloqueadas hay?» = 26 (verificado en `data/banco.sqlite`); branches `paso-0`, `paso-1`, `paso-2`. Si `W2-A` cambia la forma del TODO o los nombres, actualizar `05-bucle.html` y `05b-huerfano.html`.
- **Cifras**: solo las de FACTS §8 (GLM-5 ~8 % → ~1 %, −88 %; gpt-oss-120b 5.6 % → 3.5 %; fuente y fechas en la diapositiva; rotulado como promedio de ruteo, no rango entre proveedores). No aparece «15 % vs 0.01 %».
- **Hechos que NO están en FACTS y se presentan como hipótesis**: las tres causas del gancho (cuantización, decodificación restringida o no, fiabilidad) están rotuladas «hipótesis: OpenRouter no desglosa la causa». Si alguien quiere afirmarlas como causa, hace falta fuente.
- **Plantilla**: la diapositiva 04 copia la salida real de `taller.plantilla` (Qwen3-8B) recortada con ⋯. Si W1-E cambia el ejemplo (SQL, pregunta, tokens), reprocesar el panel izquierdo. El bloque de Claude de la derecha usa `query` igual que la plantilla, marcado «ilustrativo»; en el repo el campo real de `sql_query` es `sql`.
- **Pendiente para Carlos**: (1) opcional, captura fechada de la pestaña Performance de OpenRouter para sustituir/complementar el gráfico (nota en `02-gancho`); (2) `deck/src/sources.html` sigue vacío: fuentes a listar de W1-F = OpenRouter Auto Exacto (blog 2026-03-12, act. 2026-06-24), docs de Anthropic handle-tool-calls, parallel-tool-use y define-tools, HF `Qwen/Qwen3-8B` tokenizer_config.json, `deepseek-ai/DeepSeek-V3`; (3) el 400 de la rotura #1 muestra solo el fragmento oficial; el texto completo sale de la API en vivo.
- **Convención de CSS**: cada diapositiva trae reglas móviles (`@media (max-width:760px)`) porque sus `.split` personalizados pisan el `grid-template-columns:1fr` del sistema; se propone a W0-A que `.split` use `!important` o una variable en vez de cada diapositiva reescribirla.

## W1-G
- **Archivos**: `deck/src/slides/06-restringida.html` (s06, s06b), `07-truncado.html` (s07), `08-valido-correcto.html` (s08), `09-compuerta.html` (s09, s09b), `10-mcp.html` (s10), `11-medir.html` (s11, s11b), `12-cierre.html` (s12) y `deck/src/sources.html` (llena: clase CMU, XGrammar, CodeAct, docs de Anthropic, precios, OpenRouter, plantillas, lista de NO VERIFICADO).
- **Presupuesto (suma 25:00; con W1-F = 40:00 sin `00-smoke.html`)**: s06 2:30 · s06b 1:30 · s07 3:00 · s08 2:30 · s09 2:30 · s09b 3:00 · s10 2:00 · s11 2:30 · s11b 3:30 · s12 2:00. Bloques: 15–22 = s06+s06b+s07 (7:00); 22–32 = s08+s09+s09b+s10 (10:00); 32–38 = s11+s11b (6:00); 38–40 = s12. Sin `data-clock`.
- **Antes del ensamblado final**: borrar `00-smoke.html` (el total hoy es 40:40 por las 2 diapositivas de humo); luego `node deck/tools/assemble.mjs --expect 40:00`.
- **Checks**: `assemble` y `shot.mjs` sin desbordes en 1920x1080, 1280x720 y 390x844 (diapositivas 10–19 del ensamblado actual).
- **Código real citado** (si cambia, hay que actualizar la diapositiva): `taller/gate.py` L32–39 (`_authorizer`, 8 líneas, literal; están en `09-compuerta.html` entre `<!--GATE_BEGIN-->` y `<!--GATE_END-->`; si W1-B cambia `_authorizer`, actualizar a mano ese bloque); `taller/agent.py` bloque `paso-3` (abreviado) y la línea de contexto antes de él; `taller/tools.py` bloque `paso-4` (`motivo = _gate(sql)`) y el `if motivo:` de después. Mensaje real de rechazo en el diagrama (s09, paso 3): `rechazada: solo se permite leer clientes, cuentas, tarjetas, transacciones; reescribe la consulta como un SELECT` (salida de `validate("DROP TABLE tarjetas")`).
- **Comandos en pantalla**: `uv run python -m taller.romper truncado`, `... romper drop`, `uv run python -m taller.medir [--vs claude-opus-5-5]`, `git checkout paso-3 | paso-4 | paso-5`. Notas mencionan `romper ... --inyectado` como plan B sin API.
- **Para W2-C (tabla de medir)**: en `11-medir.html`, sección s11b, reemplazar solo el bloque entre `<!-- W2-C: reemplazar solo este bloque ... -->` y `<!-- /W2-C -->` (la `<table class="med" data-placeholder="medicion">`, hoy todo "—" y etiquetada "Ilustrativo · sin datos"). Al pegar números reales: quitar el `<span class="tag illus">` del eyebrow, cambiar el caption "Marcador de posición", y ajustar el texto de las notas ("la reemplaza W2-C"). Los precios (haiku/sonnet/opus) ya son los de FACTS §7, fecha 2026-10-18. Definición de "costo por tarea resuelta" en `medir.py`: costo_total / resueltas (coincide con la diapositiva).
- **Hechos usados que NO están en FACTS.md (revisar o dejar como están)**: (1) "un modelo más caro por token puede salir más barato por tarea resuelta": viene del encargo (se atribuye a la clase de CMU) pero no está verificado; la diapositiva y las notas lo presentan como hipótesis para la sala. (2) La historia del clasificador `null` / `while null: retry` / ~$10 000 (SPEAKER.md): va en las notas de s08 como relato que Carlos leyó, sin detalles inventados; no está verificada. (3) Que "la máscara de logits a −∞ + renormalizar" es el mecanismo de XGrammar/la clase (diap. 31–33); la diapositiva dice explícitamente que no se sabe cómo implementa Anthropic `strict` por dentro. (4) "Low-value key" del encargo: la diapositiva de MCP dice solo "clave MCP del agente" vs "token de la API", que es lo que dice FACTS §9.
- **Desviaciones del plan**: el QR del cierre apunta a `https://h1sort.com/claude4aieng/` (como pidió la tarea; PLAN §3 decía "QR al repo"). Generado con `uv run --with segno` (nivel M, versión 3, 29x29), inline como `<path>` en `12-cierre.html`; verificado: OpenCV lo decodifica desde la captura de 1920x1080.
- **Etiquetas fijas a revisar si cambia el orden**: eyebrows "Minuto 15" (s06) y "Minuto 22" (s08), y "Paso 4/Paso 5" (s09b, s11).
- **Orden de recorte (en notas)**: s06 notas: saltar el paso 2 del diagrama (autómata de pila) y explicar solo la máscara (pasos 3–4); s11/s11b: nunca recortar Medir, quitar primero `--vs` y los pasos 2–3 de s11b.
- **Pendiente para Carlos**: leer las notas de s08 (historia ≤45 s), ensayar en voz alta los puntos de control (mano levantada) de s07, s09b y s11, y confirmar los minutos exactos de la clase de CMU en el video antes de decir un minuto en voz alta (FACTS §9: solo verificados por capítulo).

## W3-A (revisión)

Revisión en frío de diapositivas, notas, `sources.html`, `taller/*.py` y `origin/paso-0…5`. `pytest`: 96 pasan. `--expect 40:00` ✓. 1280x720 sin desbordes. Los cuatro modos `--inyectado`, `medir --seco` y `--comparar` corren. Ninguna cifra contradice FACTS; "15 %" solo aparece en avisos.

### P0
1. **La rotura #3 no rompe en `paso-3`.** Sin compuerta, el DROP lo para `mode=ro` (`tools.py` L415): sale `exec_error`, también con `is_error`, y el checkpoint de `09-compuerta.html` L134 pasa sin teclear. Lo que solo para la compuerta es leer `secretos`: en `paso-3`, `SELECT * FROM secretos` filtra las claves. Arreglo: predicción y checkpoint de s09/s09b sobre `secretos`, y el DROP queda como "capa 2". `romper drop` debe intentar también esa lectura.
2. **La rotura #2 no rompe en `paso-2`.** Sin el arreglo, el bucle ya sale y la salida dice "ejecuciones: 0". El daño real es que el `tool_use` cortado se guarda y el siguiente turno da 400. Arreglo: `romper truncado` continúa la conversación (400 antes, ok después), y el checkpoint de `07-truncado.html` L57 cambia a eso. Además, con API, `romper.py` L186 hace una llamada nueva en lugar de procesar la respuesta cortada que mostró: hay que pasarle `ClienteFalso(respuesta)`.
3. **Tabla de s11b vacía** (`11-medir.html` L87–101; falta W2-C). Además, el QR apunta a `h1sort.com/claude4aieng`, que no se pudo comprobar y cuya publicación PLAN §8 deja fuera. Publicar la página o apuntar el QR a `github.com/h1sort/claude4aieng`.

### P1
4. **Teclear paso-2 en 1:45 no es realista** (`05b-huerfano.html` L76): el TODO vacía `sanitize_history` (~20 líneas). Dejar el esqueleto en la rama, o pasarle 1:00 de s09b (TODO de una línea con 1:45).
5. **Teclear paso-3** (`07-truncado.html` L56) contradice PLAN §7. Que sea "lee y corre".
6. **`git checkout paso-N` falla con cambios locales** (s05b L157, s05c L61, s07 L34, s09b L124, s11 L45 y notas). Usar `git stash && git checkout paso-N` como el README, y `git fetch` para quien clonó antes.
7. **`romper huerfano` en `paso-1` con API:** dice "inserta…" sin haber insertado nada, imprime `"¿"` (L127), y el segundo `create` termina en un traceback sin capturar. Detectar que no hubo cambio y capturar el error.
8. **MCP** (`10-mcp.html` L58/L66): "el modelo no ve las claves" vale para cualquier herramienta. El punto real es que el proceso del agente no tiene el token de abajo, así que una inyección de prompt no puede filtrarlo.
9. **Máscara de logits** (`06-restringida.html` L52): `"`, `true` y `null` solo son inválidos si `monto` es número. Mostrar `{"type": "integer"}`.
10. **Claude por dentro:** s04 L67 "La API parsea los tokens por ti" contradice su nota L84. Cambiar a "te entrega la llamada estructurada". La nota L84 está desactualizada (el panel ya usa `sql`). `romper.py` L181 ("input vacío… partial_json") no tiene fuente: verificarlo con la API.
11. **El dato del cuarto está sesgado** (s11b L127, s12 L36): `gate_rejected` gana por construcción (a01, a02). Usar "resueltas X/20" o el costo por tarea resuelta.
12. **Paralelas:** el bloque del host las promete, pero ninguna diapositiva corre `romper paralelo`. Agregar 30 s en s05b o quitarlas; el recorte #2 hoy no recorta nada.
13. **Predicción decorativa en s09** (L85): la respuesta ya está en el título. Preguntar: "tras el rechazo, ¿se rinde, repite o reescribe?".
14. **Una sola historia de terror** ("una que leí", s08); SPEAKER pide una por rotura.

### P2
- @h1sort y el empleador aparecen en las 17 diapositivas (el pie) además de s01 y s03: dejar los enlaces solo en s03 y s12.
- Las cejas "Minuto 15/22" se ven en pantalla.
- Colores: en s05, `tool_use`/`id` y "solicitud" en cobre (deberían ser cálidos); en s10, las claves en cobre; en s02, "−88 %" en verde.
- El código de s04 queda en ~12 px a 1280x720.
- s07, regla 3, dice "Reintenta", pero el código no reintenta.
- s12: cinco preguntas antes de la frase final la diluyen.

## FIX-CODE

Cambios en `taller/agent.py`, `tools.py`, `romper.py`, `scripts/cortar_pasos.py`, `tests/`. `uv run pytest -q` en main: 125 pasan; `cortar_pasos.py --sin-push` verde en los 6 branches (cortado desde un commit temporal; los branches locales se restauraron a lo que está en origin: hay que recortar tras commitear). Verificado cada comando en el branch de partida y en el de llegada con `--inyectado` (sin clave); el modo API se probó con un cliente simulado que valida huérfanos como la API.

**Rotura #1** · `uv run python -m taller.romper huerfano` · parte de `paso-1`.
- ANTES: `RECHAZADA › 400 …` (sin clave: el texto documentado, marcado) y `AVISO › sanitize_history todavía es un TODO (paso-2)…`; no dice que insertó nada.
- DESPUÉS (`paso-2`/main): `DESPUÉS › sanitize_history inserta un tool_result con is_error…` y el historial saneado (con clave: respuesta real del modelo; el segundo error de API se captura).
- Teclea (3 líneas, el esqueleto ya queda en el branch: bucle, ids, mensaje siguiente, `orphans`, `hasta`):
  `if orphans:` / `errores = [{"type": "tool_result", "tool_use_id": t, "is_error": True, "content": HUERFANO_MSG} for t in orphans]` / `fixed[i + 1:hasta] = [{"role": "user", "content": errores + content}]`

**Rotura #2** · `uv run python -m taller.romper truncado` · parte de `paso-2` (el TODO(paso-3) es un no-op: el agente guarda el tool_use cortado y termina).
- ANTES: `ANTES › el agente GUARDÓ el tool_use cortado en el historial (sin tool_result: ['toolu_…'])`, luego el seguimiento `Gracias. Ahora dime cuántos clientes hay en total.` → `RECHAZADA › 400 · tool_use ids were found without tool_result blocks immediately after` (con clave: el 400 real; sin clave: `AVISO … Error documentado (no es la respuesta de esta corrida)`). `ejecuciones de sql_query: 0` sale en ambos: el daño no es ejecutar.
- DESPUÉS (`paso-3`/main): `MODELO › reintento de la misma petición con max_tokens=48`, `DESPUÉS › … tool_use sin tool_result: 0`, `max_tokens 24 -> 48`; con clave, respuesta real al seguimiento; sin clave: "sin API no hay respuesta… pasa la validación local".
- Teclea (4 líneas, en `Agent.run`):
  `if resp.stop_reason == "max_tokens" and uses:` / `self.max_tokens = min(self.max_tokens * 2, MAX_TOKENS_TOPE)` / `self._log(turn)` / `continue`
- Con API se procesa la misma respuesta truncada que se mostró (ClienteFalso con `real=client`). Quitado el aviso de `partial_json`. El agente descarta TODO el turno cortado (también el texto) y reintenta con el doble (tope 16384).

**Rotura #3** · `uv run python -m taller.romper drop` · parte de `paso-3`. `romper` detecta en ejecución si `sql_query` consulta la compuerta (espía `gate.validate`) y rotula la cabecera según eso.
- ANTES: `ANTES › sql_query NO consulta la compuerta…`; `SELECT clave, valor FROM secretos` → `SIN COMPUERTA`, `EJECUCIÓN › sqlite · 5 filas`, las 5 claves falsas, `LLEGÓ A SQLITE … fuga de secretos`; `DROP TABLE tarjetas` → `readonly database` → `segunda capa: la conexión de solo lectura … (error de ejecución, no un rechazo)`.
- DESPUÉS (`paso-4`/main): ambas `RECHAZADA` por la compuerta antes de ejecutar (`outcome=rejected · is_error=True`). Con clave el siguiente turno del modelo es real (se imprime lo que haga, rotulado); sin clave: "no inventamos la respuesta del modelo".
- Teclea (1 línea): `motivo = _gate(sql)`
- Con clave: el prompt pide leer `secretos` y luego el DROP; lo que el modelo no proponga se inyecta y se anuncia.

**Para las diapositivas / README**: la predicción y el checkpoint de s09/s09b van sobre `secretos`, el DROP es "segunda capa"; s07 checkpoint = seguimiento 400 → OK, y "Reintenta" ahora es cierto (sube max_tokens); s05b: el TODO(paso-2) son 3 líneas con el esqueleto ya puesto; s07: el paso-3 son 4 líneas (PLAN §7 dice leer y correr: decidir); README L66–68 (tabla) sigue describiendo los TODO viejos. `tools.py`: las etapas VALIDACIÓN cambiaron ("compuerta · solo lectura…" solo con compuerta; "segunda capa · conexión de solo lectura…" siempre). `Agent.turns` es nuevo (lo usa romper aunque `run` lance).

## FIX-DECK

`--expect 40:00` ✓; shot 1280x720 y 390x844 sin desbordes. Solo `deck/src/slides/*.html` y `sources.html`; sin commit.

- **s04**: «La API te entrega la llamada ya estructurada»; nota de `query` corregida (el arg es `sql`).
- **s05b** (4:00): teclean 2:30; +momento en vivo `romper paralelo` (0:30, ~2.4 s vs ~0.8 s, latencia artificial declarada), primer recorte opcional. Nota con `git fetch` en el primer checkpoint.
- **s05c** (3:30 → **4:30**): teclean 2:45, panel de ≈5 líneas dentro del esqueleto.
- **s06**: fragmento `"monto": {"type": "integer"}` en la máscara.
- **s07** (3:00): predicción y checkpoint sobre el 400 del mensaje siguiente; paso-3 ≤4 líneas, teclean 1:00; ranura «[Historia propia…]».
- **s09** (2:30): fuga de `secretos` en paso-3 como rotura; DROP = capa 2 (solo lectura); predicción «¿se rinde, repite o reescribe?» (usar respuesta en vivo); ranura de historia propia.
- **s09b** (3:00 → **2:00**): TODO de una línea, teclean 1:00.
- **s10**: el proceso del agente nunca tiene el token; matiz sobre la clave MCP.
- **s11/s11b/s12**: «tareas resueltas X/20» y «costo por tarea resuelta»; `gate_rejected` gana por a01/a02.
- Todos los `git checkout paso-N` → `git stash && git checkout paso-N`. Recortes: 1) paralelo, 2) `--vs`, 3) autómata de pila.

Pendiente: contrastar el código mostrado en s05c/s07/s09b con los TODO reales de FIX-CODE; tabla de s11b sigue como marcador; QR sin cambios.
