# Estás en paso-3

**Estás en paso-3: lo que sigue es el paso 4, la compuerta.**

Busca `# TODO(paso-4)` en `sql_query` (`taller/tools.py`): `motivo = _gate(sql)`; si hay motivo, la consulta no se ejecuta y vuelve al modelo como `is_error`.

- Comprueba con: `uv run python -m taller.romper drop` (antes: `secretos` se lee; después: la compuerta rechaza la lectura y el DROP).
- Faltan en este branch los bloques `# TODO(paso-4)`. Las pruebas de los pasos que aún no escribes salen como *skipped*, con el motivo; `uv run pytest -q` queda en verde.
- ¿Te atrasaste? `git checkout paso-4` trae lo que sigue ya resuelto; si git se queja de tus cambios: `git stash` o `git checkout -f paso-4`.
- Este archivo lo genera `scripts/cortar_pasos.py` desde `main`; no lo edites.
