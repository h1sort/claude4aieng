# Estás en paso-2

**Estás en paso-2: lo que sigue es el paso 3, la rama `max_tokens`.**

Busca `# TODO(paso-3)` en el bucle de `taller/agent.py` (4 líneas): con `stop_reason == "max_tokens"` y algún `tool_use`, no lo ejecutes ni lo guardes: sube `max_tokens`, registra el turno y `continue` (repite la petición).

- Comprueba con: `uv run python -m taller.romper truncado` (antes: el 400 del seguimiento; después: el seguimiento funciona y el reintento sube max_tokens).
- Faltan en este branch los bloques `# TODO(paso-3)`, `# TODO(paso-4)`. Las pruebas de los pasos que aún no escribes salen como *skipped*, con el motivo; `uv run pytest -q` queda en verde.
- ¿Te atrasaste? `git checkout paso-3` trae lo que sigue ya resuelto; si git se queja de tus cambios: `git stash` o `git checkout -f paso-3`.
- Este archivo lo genera `scripts/cortar_pasos.py` desde `main`; no lo edites.
