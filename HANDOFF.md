
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
