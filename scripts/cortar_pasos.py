"""Corta los branches paso-0 … paso-5 desde main (la solución completa).

    uv run python scripts/cortar_pasos.py --seco        # resumen de diferencias; no toca git
    uv run python scripts/cortar_pasos.py               # recrea paso-0…paso-5 desde main, los verifica y los sube
    uv run python scripts/cortar_pasos.py --sin-push    # igual, pero solo en local

Marcadores en el código de solución (cualquier .py versionado, una línea sola):

    # >>> paso-N        N = 1..4
    ...solución...
    # <<< paso-N

Semántica (el asistente hace `git checkout paso-K` para EMPEZAR el paso K+1):

    paso-0  bloques 1-4 reemplazados     paso-3  solo el bloque 4
    paso-1  bloques 2-4 reemplazados     paso-4  ninguno (solución completa)
    paso-2  bloques 3-4 reemplazados     paso-5  idéntico a paso-4 en código (medir no se teclea)

Un bloque reemplazado se vuelve `# TODO(paso-N): <pista>` (+ código mínimo si hace falta), con la
misma indentación que el marcador. Cada branch es UN commit encima de main con: el código cortado,
`BRANCH.md` y, si hay pasos sin escribir, un gancho en `tests/conftest.py` que salta las pruebas de
esos pasos (para que `uv run pytest -q` salga en verde). Es re-ejecutable: los branches se recrean
desde main y solo ellos se suben con `--force-with-lease`. main nunca se toca.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCHES = tuple(range(6))  # paso-0 … paso-5
PASOS = (1, 2, 3, 4)  # bloques con marcador
MARCA_ABRE = re.compile(r"^(?P<sangria>[ \t]*)# >>> paso-(?P<n>\d+)[ \t]*$")
MARCA_CIERRA = re.compile(r"^(?P<sangria>[ \t]*)# <<< paso-(?P<n>\d+)[ \t]*$")
# Los dos archivos de este cortador citan marcadores en sus cadenas: nunca se transforman.
PROPIOS = {"scripts/cortar_pasos.py", "tests/test_cortar_pasos.py"}
TRAILERS = (
    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
    "Claude-Session: https://claude.ai/code/session_01LUSeAETMjFFgQ42Bp3BbT2"
)
FIN_CONFTEST = "# --- generado por scripts/cortar_pasos.py (solo en los branches paso-*) ---"


# ---------- qué se escribe en lugar de cada bloque ----------

@dataclass(frozen=True)
class Reemplazo:
    pista: str                    # una línea, en español: va tras `# TODO(paso-N): `
    codigo: tuple[str, ...] = ()  # líneas extra (código o comentarios), sangría relativa al marcador
    requiere_despues: str = ""    # texto que debe seguir existiendo tras el bloque (red de seguridad del TODO)


REEMPLAZOS: dict[int, Reemplazo] = {
    # El `if not results: raise NotImplementedError("paso-1: ...")` que sigue al bloque es lo que falla con
    # claridad; no hay `raise` aquí para que el asistente no tenga que borrarlo antes de teclear.
    1: Reemplazo(
        "ejecuta las llamadas con execute_calls y contesta con UN mensaje de usuario (un tool_result por llamada)",
        ("# Un tool_result por llamada, con su tool_use_id y ANTES de cualquier texto; is_error si falló.",
         "# Mientras falte, `results` queda vacío y el bucle falla justo debajo con NotImplementedError."),
        'raise NotImplementedError("paso-1',
    ),
    # El esqueleto de sanitize_history queda (el bucle, los ids de tool_use, el mensaje de usuario siguiente);
    # sin la inserción devuelve el historial intacto: `--reanudar` produce el 400 real de la API.
    2: Reemplazo(
        "si hay `orphans`, mete un tool_result (is_error=True) por cada uno AL PRINCIPIO del mensaje de usuario siguiente",
        ("# Arma `errores`: un {type: tool_result, tool_use_id, is_error: True, content: HUERFANO_MSG} por huérfano.",
         "# Luego reemplaza fixed[i + 1:hasta] por un mensaje de usuario con errores + content (resultados primero).",
         "# Sin esto el historial se reenvía tal cual y la API responde 400."),
    ),
    # Sin la rama (no-op: el bucle sigue de largo), el tool_use cortado entra al historial y el siguiente turno da 400.
    3: Reemplazo(
        'con stop_reason == "max_tokens" y algún tool_use el JSON puede estar cortado: ni lo ejecutes ni lo guardes',
        ("# Sube self.max_tokens (min(.. * 2, MAX_TOKENS_TOPE)), registra el turno con self._log(turn) y `continue`:",
         "# se repite la misma petición. Mientras falte, el tool_use cortado se guarda y el siguiente mensaje da 400."),
    ),
    # Sin compuerta, la lectura de `secretos` llega a SQLite y devuelve las claves; el DROP lo frena solo la
    # conexión de solo lectura (segunda capa: error de ejecución, no rechazo).
    4: Reemplazo(
        "falta la compuerta: llama a _gate(sql) y deja el resultado en `motivo` (None = permitido)",
        ('stage("VALIDACIÓN", "SIN COMPUERTA (TODO paso-4): el SQL llega a SQLite sin validar")',),
    ),
}

# Pruebas de main que ejercitan un paso: se saltan en los branches donde ese paso aún no está escrito
# (paso-K tiene escritos los pasos <= K). Clave: "archivo::prueba" o "archivo" completo.
REQUIERE: dict[str, int] = {
    "tests/test_agent.py::test_parallel_calls_answered_in_one_user_message_with_results_first": 1,
    "tests/test_agent.py::test_unknown_tool_in_loop_goes_back_to_model_as_is_error": 1,
    "tests/test_agent.py::test_gate_rejection_is_error_result": 1,
    "tests/test_agent.py::test_sanitize_inserts_error_result_first": 2,
    "tests/test_agent.py::test_sanitize_when_history_ends_at_tool_use_and_is_idempotent": 2,
    "tests/test_agent.py::test_sanitize_string_user_message_after_orphan": 2,
    "tests/test_agent.py::test_truncated_tool_use_is_not_executed_and_is_retried": 3,
    "tests/test_agent.py::test_truncated_retry_is_capped": 3,
    "tests/test_medir.py::test_con_agent_real_consulta_y_bloqueo_rechazado": 1,
    "tests/test_romper.py::test_huerfano": 2,
    "tests/test_romper.py::test_truncado": 3,
    "tests/test_romper.py::test_drop": 4,
    "tests/test_romper.py::test_detectar_compuerta_es_en_ejecucion": 4,
}


# ---------- el reemplazo de bloques (puro: texto entra, texto sale) ----------

@dataclass(frozen=True)
class Bloque:
    n: int
    abre: int      # índice de línea del `# >>>`
    cierra: int    # índice de línea del `# <<<`
    sangria: str


def buscar_bloques(texto: str) -> list[Bloque]:
    """Bloques de un texto, en orden. Falla si hay anidación, cierres huérfanos o N distinto."""
    bloques: list[Bloque] = []
    abierto: tuple[int, int, str] | None = None
    for i, linea in enumerate(texto.splitlines()):
        if m := MARCA_ABRE.match(linea):
            if abierto:
                raise ValueError(f"línea {i + 1}: `>>> paso-{m['n']}` dentro del bloque paso-{abierto[0]} abierto en la línea {abierto[1] + 1}")
            abierto = (int(m["n"]), i, m["sangria"])
        elif m := MARCA_CIERRA.match(linea):
            if not abierto or abierto[0] != int(m["n"]):
                raise ValueError(f"línea {i + 1}: `<<< paso-{m['n']}` sin su `>>> paso-{m['n']}`")
            bloques.append(Bloque(abierto[0], abierto[1], i, abierto[2]))
            abierto = None
    if abierto:
        raise ValueError(f"el bloque paso-{abierto[0]} (línea {abierto[1] + 1}) no se cierra")
    return bloques


def cortar_bloques(texto: str, cortar: Iterable[int], reemplazos: dict[int, Reemplazo] = REEMPLAZOS) -> str:
    """Sustituye los bloques cuyo N esté en `cortar` por su `# TODO(paso-N)`; deja los demás tal cual."""
    cortar = set(cortar)
    lineas = texto.splitlines(keepends=True)
    fin = "\r\n" if lineas and lineas[0].endswith("\r\n") else "\n"
    for b in sorted(buscar_bloques(texto), key=lambda x: -x.abre):  # de atrás hacia delante: los índices no se mueven
        if b.n not in cortar:
            continue
        r = reemplazos[b.n]
        if "\n" in r.pista:
            raise ValueError(f"la pista de paso-{b.n} debe ser de una sola línea")
        nuevo = [f"{b.sangria}# TODO(paso-{b.n}): {r.pista}{fin}"] + [f"{b.sangria}{x}{fin}" for x in r.codigo]
        lineas[b.abre:b.cierra + 1] = nuevo
    return "".join(lineas)


def ramas_de(k: int) -> set[int]:
    """Bloques que se reemplazan en paso-K."""
    return {n for n in PASOS if n > k}


# ---------- BRANCH.md y gancho de pruebas ----------

SIGUIENTE = {
    0: ("el paso 1, el bucle",
        "Abre `taller/agent.py`, busca `# TODO(paso-1)` dentro de `Agent.run` y ejecuta las llamadas con `execute_calls`; "
        "contesta con UN mensaje de usuario con un `tool_result` por llamada.",
        "`uv run python -m taller.agent` y pregunta «¿cuántas tarjetas bloqueadas hay?» (respuesta: 26)."),
    1: ("el paso 2, el saneo del historial huérfano",
        "Busca `# TODO(paso-2)` dentro de `sanitize_history` (`taller/agent.py`): el esqueleto ya encuentra los `orphans`; "
        "tú inserta (3 líneas) un `tool_result` con `is_error` PRIMERO en el mensaje de usuario siguiente.",
        "`uv run python -m taller.romper huerfano` (antes: el 400 y «sanitize_history todavía es un TODO»; después: el modelo continúa)."),
    2: ("el paso 3, la rama `max_tokens`",
        'Busca `# TODO(paso-3)` en el bucle de `taller/agent.py` (4 líneas): con `stop_reason == "max_tokens"` y algún '
        "`tool_use`, no lo ejecutes ni lo guardes: sube `max_tokens`, registra el turno y `continue` (repite la petición).",
        "`uv run python -m taller.romper truncado` (antes: el 400 del seguimiento; después: el seguimiento funciona y el reintento sube max_tokens)."),
    3: ("el paso 4, la compuerta",
        "Busca `# TODO(paso-4)` en `sql_query` (`taller/tools.py`): `motivo = _gate(sql)`; si hay motivo, la consulta "
        "no se ejecuta y vuelve al modelo como `is_error`.",
        "`uv run python -m taller.romper drop` (antes: `secretos` se lee; después: la compuerta rechaza la lectura y el DROP)."),
    4: ("el paso 5, medir",
        "No hay nada que teclear: corre la medición sobre tu propio agente y lee la tabla por categoría de error, "
        "con tokens y costo por tarea resuelta.",
        "`uv run python -m taller.medir` (opcional: `--vs claude-opus-5-5`; `--seco` para ver la forma sin API)."),
    5: ("leer tus números",
        "No hay nada que teclear: este branch trae el mismo código que `paso-4` (la solución completa). "
        "Úsalo si te quedaste atrás en el paso de medir y quieres seguir con los números de la pantalla.",
        "`uv run python -m taller.medir --seco` (sin API) o `uv run python -m taller.medir`."),
}


def branch_md(k: int) -> str:
    que, instruccion, verifica = SIGUIENTE[k]
    pendientes = sorted(ramas_de(k))
    if pendientes:
        estado = ("Faltan en este branch los bloques " + ", ".join(f"`# TODO(paso-{n})`" for n in pendientes)
                  + ". Las pruebas de los pasos que aún no escribes salen como *skipped*, con el motivo; "
                  "`uv run pytest -q` queda en verde.")
    else:
        estado = "No queda ningún `# TODO(paso-N)`: es la solución completa. `uv run pytest -q` corre todas las pruebas."
    lineas = [
        f"# Estás en paso-{k}", "",
        f"**Estás en paso-{k}: lo que sigue es {que}.**", "",
        instruccion, "",
        f"- Comprueba con: {verifica}",
        f"- {estado}",
    ]
    if k < 5:
        lineas.append(f"- ¿Te atrasaste? `git checkout paso-{k + 1}` trae lo que sigue ya resuelto; "
                      f"si git se queja de tus cambios: `git stash` o `git checkout -f paso-{k + 1}`.")
    lineas.append("- Este archivo lo genera `scripts/cortar_pasos.py` desde `main`; no lo edites.")
    return "\n".join(lineas) + "\n"


def gancho_conftest(k: int) -> str:
    """Código que se anexa a tests/conftest.py del branch: salta las pruebas de pasos no escritos."""
    pendientes = {nodo: n for nodo, n in REQUIERE.items() if n > k}
    filas = "".join(f"    {nodo!r}: {n},\n" for nodo, n in sorted(pendientes.items()))
    return (
        f"\n\n\n{FIN_CONFTEST}\n"
        f"PASO_ACTUAL = {k}  # estás en paso-{k}: tienes escritos los pasos 1..{k}\n"
        f"REQUIERE_PASO = {{\n{filas}}}\n\n\n"
        "def pytest_collection_modifyitems(config, items):\n"
        '    """Salta (con motivo) las pruebas de los pasos que todavía no escribes."""\n'
        "    for item in items:\n"
        '        archivo, _, prueba = item.nodeid.partition("::")\n'
        '        paso = REQUIERE_PASO.get(f"{archivo}::{prueba.split(\'[\')[0]}", REQUIERE_PASO.get(archivo, 0))\n'
        "        if paso > PASO_ACTUAL:\n"
        "            item.add_marker(pytest.mark.skip(\n"
        '                reason=f"requiere el paso {paso}: aún no lo escribes (estás en paso-{PASO_ACTUAL})"))\n'
    )


# ---------- git ----------

def git(*args: str, cwd: Path = ROOT, check: bool = True, entrada: str | None = None) -> str:
    p = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, input=entrada)
    if check and p.returncode:
        raise SystemExit(f"git {' '.join(args)} falló ({p.returncode}):\n{p.stderr.strip()}")
    return p.stdout


def leer_base(base: str) -> Callable[[str], str]:
    return lambda ruta: git("show", f"{base}:{ruta}")


def archivos_py(base: str) -> list[str]:
    return [r for r in git("ls-tree", "-r", "--name-only", base).splitlines()
            if r.endswith(".py") and r not in PROPIOS]


def inventario(base: str) -> dict[int, list[str]]:
    """Marcadores del repo entero: N -> archivos que lo contienen. Valida que existan 1..4 exactamente una vez."""
    leer = leer_base(base)
    donde: dict[int, list[str]] = {n: [] for n in PASOS}
    for ruta in archivos_py(base):
        try:
            bloques = buscar_bloques(leer(ruta))
        except ValueError as exc:
            raise SystemExit(f"{ruta}: marcadores mal formados: {exc}")
        for b in bloques:
            if b.n not in donde:
                raise SystemExit(f"{ruta}: paso-{b.n} no existe (solo 1..4)")
            donde[b.n].append(ruta)
    for n, rutas in donde.items():
        if len(rutas) != 1:
            raise SystemExit(f"paso-{n}: esperaba exactamente un bloque en el repo, encontré {len(rutas)}: {rutas}")
    for n, r in REEMPLAZOS.items():
        if r.requiere_despues and r.requiere_despues not in leer(donde[n][0]):
            raise SystemExit(f"paso-{n}: {donde[n][0]} ya no contiene {r.requiere_despues!r}; sin eso el TODO no falla con claridad")
    return donde


def planear(base: str, k: int, donde: dict[int, list[str]]) -> dict[str, str]:
    """Archivos que cambian en paso-K: ruta -> contenido nuevo (incluye BRANCH.md y el gancho de pruebas)."""
    leer = leer_base(base)
    cambios: dict[str, str] = {}
    for ruta in sorted({r for n in ramas_de(k) for r in donde[n]}):
        cambios[ruta] = cortar_bloques(leer(ruta), ramas_de(k))
    if ramas_de(k):
        cambios["tests/conftest.py"] = leer("tests/conftest.py").rstrip("\n") + gancho_conftest(k)
    cambios["BRANCH.md"] = branch_md(k)
    return cambios


def resumen(base: str, k: int, cambios: dict[str, str]) -> str:
    leer = leer_base(base)
    filas = []
    for ruta, nuevo in cambios.items():
        try:
            viejo = leer(ruta)
        except SystemExit:
            viejo = ""
        a, b = viejo.splitlines(), nuevo.splitlines()
        quitadas = len([x for x in a if x not in set(b)])
        puestas = len([x for x in b if x not in set(a)])
        filas.append(f"    {ruta:<22} -{quitadas:<3} +{puestas:<3}" + ("  (nuevo)" if not viejo else ""))
    cortados = ", ".join(f"paso-{n}" for n in sorted(ramas_de(k))) or "ninguno"
    saltos = sum(1 for n in REQUIERE.values() if n > k)
    return f"paso-{k}: bloques reemplazados: {cortados}; pruebas que se saltan: {saltos}\n" + "\n".join(filas)


def verificar(arbol: Path, k: int) -> None:
    """Importa los módulos y corre pytest dentro del árbol del branch (con el Python de este entorno)."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(arbol)}
    importar = "import taller.agent, taller.tools, taller.romper, taller.medir; print(taller.agent.__file__)"
    p = subprocess.run([sys.executable, "-c", importar], cwd=arbol, env=env, text=True, capture_output=True)
    if p.returncode or str(arbol) not in p.stdout:
        raise SystemExit(f"paso-{k}: no importan los módulos:\n{p.stdout}{p.stderr}")
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                       cwd=arbol, env=env, text=True, capture_output=True)
    ultima = (p.stdout.strip().splitlines() or ["(sin salida)"])[-1]
    if p.returncode:
        raise SystemExit(f"paso-{k}: pytest falló ({ultima}):\n{p.stdout[-3000:]}{p.stderr[-1000:]}")
    print(f"  verificado: imports ok · pytest: {ultima}")


def crear_branch(base: str, k: int, cambios: dict[str, str], con_verificar: bool) -> None:
    tmp = Path(tempfile.mkdtemp(prefix=f"paso-{k}-"))
    arbol = tmp / "arbol"
    try:
        git("worktree", "add", "-q", "-B", f"paso-{k}", str(arbol), base)
        for ruta, texto in cambios.items():
            destino = arbol / ruta
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(texto, encoding="utf-8", newline="")
        if con_verificar:
            verificar(arbol, k)
        git("add", "--", *cambios, cwd=arbol)
        mensaje = (f"paso-{k}: generado por scripts/cortar_pasos.py desde {git('rev-parse', '--short', base).strip()}\n\n"
                   f"{TRAILERS}\n")
        git("commit", "-q", "-F", "-", cwd=arbol, entrada=mensaje)
    finally:
        git("worktree", "remove", "--force", str(arbol), check=False)
        shutil.rmtree(tmp, ignore_errors=True)
        git("worktree", "prune", check=False)


def subir(remoto: str) -> None:
    """Sube SOLO paso-0…paso-5 (main nunca). Cada uno con un --force-with-lease explícito contra lo recién traído."""
    ramas = [f"paso-{k}" for k in BRANCHES]
    # El refspec de fetch por omisión solo trae main; sin esta línea el lease "desnudo" no ve los paso-* remotos.
    git("fetch", "-q", remoto, f"+refs/heads/paso-*:refs/remotes/{remoto}/paso-*")
    leases = []
    for r in ramas:
        visto = git("rev-parse", "--verify", "-q", f"refs/remotes/{remoto}/{r}", check=False).strip()
        leases.append(f"--force-with-lease={r}:{visto}")  # vacío = el branch remoto no debe existir aún
    git("push", *leases, remoto, *[f"refs/heads/{r}:refs/heads/{r}" for r in ramas])
    print(f"subidos: {', '.join(ramas)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Genera paso-0…paso-5 desde main.")
    ap.add_argument("--seco", action="store_true", help="solo imprime el resumen de diferencias; no crea ni sube nada")
    ap.add_argument("--sin-push", action="store_true", help="crea los branches en local y no los sube")
    ap.add_argument("--sin-verificar", action="store_true", help="no corre imports ni pytest en cada branch")
    ap.add_argument("--base", default="main", help="rama de la solución completa (por omisión main)")
    ap.add_argument("--remoto", default="origin")
    args = ap.parse_args(argv)

    base = git("rev-parse", "--verify", f"{args.base}^{{commit}}").strip()
    donde = inventario(base)
    print(f"base {args.base} = {base[:9]} · marcadores: "
          + ", ".join(f"paso-{n} en {rutas[0]}" for n, rutas in donde.items()))
    if args.seco:
        for k in BRANCHES:
            print(resumen(base, k, planear(base, k, donde)))
        print("\n(--seco: no se creó ni se subió nada)")
        return 0
    if git("status", "--porcelain", "--untracked-files=no").strip():
        print("aviso: el árbol de trabajo tiene cambios sin commit; los branches salen de lo COMMITEADO en "
              f"{args.base}, no de esos cambios.", file=sys.stderr)
    for k in BRANCHES:
        cambios = planear(base, k, donde)
        print(resumen(base, k, cambios))
        crear_branch(base, k, cambios, not args.sin_verificar)
    if args.sin_push:
        print("\nbranches creados en local (--sin-push).")
    else:
        subir(args.remoto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
