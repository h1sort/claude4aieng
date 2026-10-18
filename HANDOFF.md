
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
