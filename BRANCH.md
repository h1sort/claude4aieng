# Estás en paso-0

**Estás en paso-0: lo que sigue es el paso 1, el bucle.**

Abre `taller/agent.py`, busca `# TODO(paso-1)` dentro de `Agent.run` y ejecuta las llamadas con `execute_calls`; contesta con UN mensaje de usuario con un `tool_result` por llamada.

- Comprueba con: `uv run python -m taller.agent` y pregunta «¿cuántas tarjetas bloqueadas hay?» (respuesta: 26).
- Faltan en este branch los bloques `# TODO(paso-1)`, `# TODO(paso-2)`, `# TODO(paso-3)`, `# TODO(paso-4)`. Las pruebas de los pasos que aún no escribes salen como *skipped*, con el motivo; `uv run pytest -q` queda en verde.
- ¿Te atrasaste? `git checkout paso-1` trae lo que sigue ya resuelto; si git se queja de tus cambios: `git stash` o `git checkout -f paso-1`.
- Este archivo lo genera `scripts/cortar_pasos.py` desde `main`; no lo edites.
