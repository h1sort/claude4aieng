# Estás en paso-4

**Estás en paso-4: lo que sigue es el paso 5, medir.**

No hay nada que teclear: corre la medición sobre tu propio agente y lee la tabla por categoría de error, con tokens y costo por tarea resuelta.

- Comprueba con: `uv run python -m taller.medir` (opcional: `--vs claude-opus-5-5`; `--seco` para ver la forma sin API).
- No queda ningún `# TODO(paso-N)`: es la solución completa. `uv run pytest -q` corre todas las pruebas.
- ¿Te atrasaste? `git checkout paso-5` trae lo que sigue ya resuelto; si git se queja de tus cambios: `git stash` o `git checkout -f paso-5`.
- Este archivo lo genera `scripts/cortar_pasos.py` desde `main`; no lo edites.
