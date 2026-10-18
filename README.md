# Tool use sin abstracciones

Taller de Claude Community CDMX · lunes 19 de octubre de 2026 · 40 minutos · para ingenieros.

Escribes a mano un agente de ~100 líneas sobre la API de Claude (sin frameworks, sin Tool Runner), lo
rompes a propósito (historial con `tool_use` huérfano, JSON truncado por `max_tokens`, una llamada
válida pero peligrosa) y lo reparas en código. Sales midiendo la tasa de error de herramientas de
tu propio agente, por categoría y con costo por tarea. La tesis: **el modelo propone, la aplicación
ejecuta, y eso se mide.**

## Antes del evento (hazlo en casa: el wifi del venue no aguanta descargas)

Necesitas Python 3.11+ (si no lo tienes, `uv` lo descarga), una API key de Anthropic con créditos y unos minutos de red.

**1. Instala `uv`**

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Cierra y abre la terminal para que `uv` quede en el PATH.

**2. Clona e instala las dependencias** (`anthropic`, `jinja2`; nada más)

```bash
git clone https://github.com/h1sort/claude4aieng && cd claude4aieng && uv sync
```

**3. Define tu llave** (crea una en https://console.anthropic.com/settings/keys)

```bash
export ANTHROPIC_API_KEY=sk-ant-...        # macOS / Linux
```

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."      # Windows (PowerShell)
```

**4. Verifica todo**

```bash
uv run python scripts/check.py
```

Revisa Python, dependencias, `data/banco.sqlite`, la llave y hace una llamada de 1 token para confirmar
que hay créditos. Cada fallo trae el arreglo en español. Si todo sale con `✓`, ya estás listo; después del
primer `uv sync` no se descarga nada en vivo, salvo las llamadas a la API.

Por defecto se usa `claude-sonnet-5-5`; puedes cambiarlo con `export MODEL_ID=...`.

## Durante el taller

Los tiempos son del guion; los branches son por si te quedas atrás. `paso-N` es el repo con la solución
hasta el paso N y los `# TODO(paso-N+1)` pendientes.

| Min | Paso | Branch al terminar | Comando | Qué tecleas |
|---|---|---|---|---|
| 0–5 | Las herramientas son texto | `paso-0` | `uv run python -m taller.plantilla` | Nada: lee la plantilla de chat de Qwen ya renderizada, con las herramientas como texto. |
| 5–15 | El bucle a nivel cable | `paso-1` | `uv run python -m taller.agent` | En `taller/agent.py`, `# TODO(paso-1)`: ejecuta las llamadas del turno con `execute_calls` y devuelve **un** mensaje de usuario con todos los `tool_result`, primero y con su `tool_use_id`. Prueba con `¿cuántas tarjetas bloqueadas hay?` (26). |
| 5–15 | Rotura #1: `tool_use` huérfano | `paso-2` | `uv run python -m taller.romper huerfano` | En `sanitize_history` (el esqueleto ya está), `# TODO(paso-2)`, 3 líneas: para los `tool_use` sin resultado, inserta `tool_result` con `is_error: true` **al inicio** del mensaje siguiente. Antes: 400. Después: la conversación sigue. También puedes matar `taller.agent` con Ctrl-C y reanudar con `--reanudar`. |
| 15–22 | Rotura #2: `max_tokens` | `paso-3` | `uv run python -m taller.romper truncado` | En `Agent.run`, `# TODO(paso-3)`, 4 líneas: si `stop_reason == "max_tokens"` y hay un `tool_use`, no lo ejecutes ni lo guardes; sube `max_tokens` y reintenta. Antes: el `tool_use` cortado se queda en el historial y la siguiente petición da 400. Después: 0 huérfanos. |
| 22–32 | Rotura #3: válido no es correcto | `paso-4` | `uv run python -m taller.romper drop` | En `taller/tools.py`, `# TODO(paso-4)`, 1 línea: `motivo = _gate(sql)`. Antes: `SELECT clave, valor FROM secretos` devuelve las claves (falsas) y el `DROP` solo lo frena la conexión de solo lectura. Después: la compuerta rechaza ambos antes de ejecutar y el motivo vuelve como `is_error`. |
| 32–38 | Medir | `paso-5` | `uv run python -m taller.medir` | Nada: corre las 20 tareas y lee la tabla de errores, tokens y costo. |

**¿Te quedaste atrás?** Guarda tu intento y salta al branch del último paso que alcanzaste:

```bash
git fetch && git stash && git checkout paso-N
```

(`git checkout main` tiene la solución completa; `git stash pop` recupera tu intento.)

## Comandos

Todos con `uv run python -m taller.<nombre>` desde la raíz del repo.

| Comando | Qué hace | Flags |
|---|---|---|
| `plantilla` | Renderiza con `jinja2` la plantilla de chat de un modelo abierto para un mensaje con herramientas y una llamada. Sin red, sin pesos. | `--familia qwen\|deepseek` (por omisión `qwen`) · `--comparar` muestra las dos familias y el parser que necesitaría cada una |
| `agent` | El agente interactivo, con etapas SOLICITUD / VALIDACIÓN / EJECUCIÓN / OBSERVACIÓN / RECHAZADA. Herramientas: `sql_query` (solo lectura) y `bloquear_tarjeta` (pide confirmación humana en la terminal). | `--reanudar` retoma `runs/sesion.json` y sanea el historial · dentro de la sesión, `/sql <consulta>` manda SQL escrito por ti directo a la herramienta, sin pasar por el modelo · Ctrl-D sale |
| `romper` | Rompe el agente a propósito y lo repara. Modos: `huerfano`, `truncado`, `paralelo`, `drop`. | `--inyectado` fabrica la entrada en lugar de depender de que el modelo caiga en la trampa |
| `medir` | Corre las 20 tareas de `evals/prompts.jsonl` (3 adversariales, 2 sin herramienta), clasifica los errores por categoría y reporta tokens, costo y costo por tarea resuelta. Guarda `runs/medicion-*.json`. | `--modelo X` (por omisión `MODEL_ID`) · `--vs Y` compara con un segundo modelo · `--n N` usa solo las primeras N tareas · `--concurrencia 4` · `--seco` |

Categorías de error: `wrong_tool`, `bad_args`, `gate_rejected`, `exec_error`, `truncated`, `orphaned`.

**Sin API key y sin gastar nada:** `romper ... --inyectado` y `medir --seco` no llaman a la API. El primero fabrica la
entrada y la dice en pantalla; el segundo puntúa resultados **simulados** solo para mostrar la forma de la tabla (no
mide tu agente). Si falta `ANTHROPIC_API_KEY`, `romper` activa `--inyectado` por su cuenta. Úsalos si te quedas sin créditos
o sin red; `plantilla` y `/sql` tampoco usan la API.

La confirmación de `bloquear_tarjeta` en `medir` se responde siempre «no»: la medición nunca bloquea tarjetas.

## Costo

Precios por MTok con los que calcula `taller/precios.py` (verificados el 2026-10-18; revísalos en
claude.com/pricing):

| Modelo | Entrada | Salida |
|---|---|---|
| `claude-sonnet-5-5` | $2 | $10 |
| `claude-haiku-5-5` | $0.10 | $0.50 |
| `claude-opus-5-5` | $4 | $20 |

Orden de magnitud: la corrida simulada `medir --seco` usa unos 46 000 tokens de entrada y 6 000 de salida
en las 20 tareas, lo que con Sonnet 5.5 da aprox. $0.15 (unos 15 centavos de dólar). Con Haiku 5.5 sería aprox.
$0.01 y con Opus 5.5 aprox. $0.30. Son números simulados: el consumo real depende de cuántas vueltas dé el
modelo. Las pruebas de `romper` son unas pocas llamadas. Aprox., todo el taller debería costar centavos; revisa
tu consola (console.anthropic.com) para el gasto real.

## Extras para quien termina antes

Uno por paso. Ninguno es necesario para seguir el taller.

| Paso | Extra |
|---|---|
| 0 | `uv run python -m taller.plantilla --familia deepseek`, y luego `--comparar`: compara dónde van las llamadas y los resultados, y por qué el parser de una familia no sirve para la otra. |
| 1 | En `Agent.run`, prueba `tool_choice={"type": "auto", "disable_parallel_tool_use": True}` (va dentro de `tool_choice`, no al nivel de la petición) y compara con `romper paralelo`. No uses `any` ni `tool`: devuelven 400 en Sonnet 5.5 y Opus 5.5. |
| 2 | Mata el proceso con varias llamadas paralelas en el mismo turno y reanuda con `--reanudar`: ¿a cuáles les inventa resultado `sanitize_history`? |
| 3 | Reintenta automáticamente la misma petición con un `max_tokens` mayor cuando llegue `stop_reason: "max_tokens"` con un `tool_use`, en vez de pedirle al usuario que repita. Prueba valores distintos en `romper truncado`. |
| 4 | Agrega una segunda tabla sensible en `scripts/seed.py` y escribe en `tests/test_gate.py` la prueba de que la compuerta la rechaza (la compuerta lista las tablas permitidas, `ALLOWED_TABLES`). Después, agrega una permitida. |
| 5 | `uv run python -m taller.medir --vs claude-haiku-5-5`: ¿cambia el costo por tarea resuelta, y no solo el costo por token? |

## Diapositivas

https://h1sort.com/claude4aieng/ (se publica después del evento)

Para abrir el deck local, desde la raíz del repo:

```bash
cd deck && python3 -m http.server 8000
```

y abre http://localhost:8000/tool-use.html. Sirve por `http`, no con `file://`: el modo presentador sincroniza
ventanas con `BroadcastChannel`, que solo funciona por http.

## Estructura del repo

```
taller/
  plantilla.py   chat template de Qwen / DeepSeek renderizado     (vendor/: JSON de las plantillas)
  agent.py       el bucle del agente, con los TODO(paso-N)
  tools.py       sql_query y bloquear_tarjeta
  gate.py        la compuerta: autorizador de SQLite, determinista, sin LLM
  romper.py      huerfano | truncado | paralelo | drop
  medir.py       20 tareas -> errores por categoría, tokens, costo
  precios.py     precios por MTok (2026-10-18)
  contracts.py   tipos compartidos y MODEL_ID
evals/prompts.jsonl   las 20 tareas
data/banco.sqlite     base sintética (clientes, cuentas, transacciones, tarjetas, secretos)
scripts/check.py      verificación previa     scripts/seed.py  regenera la base
deck/                 diapositivas (tool-use.html)
tests/                pytest
```

## Créditos

- La clase **CMU 11-768 AI Agents** (Graham Neubig y Daniel Fried, Language Technologies Institute, otoño 2026),
  lección 2, "Tool Use for Language Model Agents", de Neubig: [video](https://youtu.be/jXChFB4JSyw) ·
  [diapositivas](https://www.cmu-agents.com/slides/lecture-02-tool-use.pdf) · [curso](https://www.cmu-agents.com/).
- XGrammar: Dong et al., "XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models",
  MLSys 2025. https://arxiv.org/abs/2411.15100
- CodeAct: Wang et al., "Executable Code Actions Elicit Better LLM Agents", ICML 2024. https://arxiv.org/abs/2402.01030
- Documentación de tool use de Anthropic: https://platform.claude.com/docs/en/agents-and-tools/tool-use

Los hechos y sus fuentes están en `FACTS.md`; lo que no se pudo verificar está marcado ahí y no entra al taller.

Autor: Carlos Haro (@h1sort) · h1sort.com
