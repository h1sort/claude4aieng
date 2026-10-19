# Estás en paso-1

**Estás en paso-1: lo que sigue es el paso 2: cada `tool_use` con su `tool_result` (huérfano al reanudar y llamada paralela que no termina).**

Busca `# TODO(paso-2)` dentro de `sanitize_history` (`taller/agent.py`): el esqueleto ya encuentra los `orphans`; tú inserta (3 líneas) un `tool_result` con `is_error` PRIMERO en el mensaje de usuario siguiente. Luego `# TODO(paso-2b)` en `execute_calls` (4 líneas): un `tool_result` por cada llamada, y un timeout es `is_error`.

- Comprueba con: `uv run python -m taller.romper huerfano` y `uv run python -m taller.romper paralelo` (antes: el 400; después: el modelo continúa).
- Faltan en este branch los bloques `# TODO(paso-2)`, `# TODO(paso-3)`, `# TODO(paso-4)`. Las pruebas de los pasos que aún no escribes salen como *skipped*, con el motivo; `uv run pytest -q` queda en verde.
- ¿Te atrasaste? `git checkout paso-2` trae lo que sigue ya resuelto; si git se queja de tus cambios: `git stash` o `git checkout -f paso-2`.
- Este archivo lo genera `scripts/cortar_pasos.py` desde `main`; no lo edites.
