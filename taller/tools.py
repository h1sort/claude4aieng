"""Las herramientas del agente: lo que la aplicación ejecuta cuando el modelo PROPONE una llamada.

    sql_query(sql)                       lectura sobre data/banco.sqlite, detrás de la compuerta (paso-4)
    bloquear_tarjeta(ultimos4, motivo)   escritura: pide confirmación humana en la terminal

Convención de resultado: cada función devuelve texto. Si empieza con `RECHAZADA` ("rechazada:")
la aplicación la trató como rechazo (compuerta o humano) y el agente lo manda como `is_error`.
Si lanza una excepción, el agente la manda como error de ejecución.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import threading
import time
from collections.abc import Callable
from contextvars import ContextVar

from taller import contracts
from taller.contracts import ToolSpec

# ---------- consola: las etapas de la demo de GBM ----------

_TTY = sys.stdout.isatty()
DIM, BOLD, RESET = ("\033[2m", "\033[1m", "\033[0m") if _TTY else ("", "", "")
COLOR = {"SOLICITUD": "\033[33m", "VALIDACIÓN": "\033[36m", "EJECUCIÓN": "\033[32m",
         "OBSERVACIÓN": "\033[32m", "RECHAZADA": "\033[31m", "MODELO": "\033[35m"} if _TTY else {}
ECHO: ContextVar[bool] = ContextVar("ECHO", default=True)
"""Si es False, `stage` no imprime (lo usa el Agent con echo=False; to_thread copia el contexto)."""


def stage(name: str, text: str) -> None:
    if ECHO.get():
        print(f"{COLOR.get(name, '')}{BOLD}{name} ›{RESET} {text}", flush=True)


RECHAZADA = "rechazada:"


# ---------- sql_query ----------

def _gate(sql: str) -> str | None:
    """Llama a taller.gate.validate; si el módulo aún no existe, no hay compuerta."""
    try:
        from taller import gate
    except ModuleNotFoundError as exc:
        if exc.name != "taller.gate":
            raise
        return None
    motivo = gate.validate(sql)
    if motivo is None:
        stage("VALIDACIÓN", "compuerta · solo lectura sobre tablas permitidas")
    return motivo


MAX_ROWS = 200
"""Tope de filas que vuelven al modelo (un SELECT sin LIMIT no debe llenar el contexto)."""
TIME_LIMIT_S = 2.0
"""Tope de tiempo de una consulta: la compuerta valida la forma, no el costo (una CTE recursiva sin fin pasa)."""


def _render(columns: list[str], rows: list[tuple]) -> str:
    if not rows:
        return "(sin filas)"
    lines = [" | ".join(columns)] + [" | ".join(str(v) for v in r) for r in rows[:MAX_ROWS]]
    if len(rows) > MAX_ROWS:
        lines.append(f"... (resultado truncado a {MAX_ROWS} filas; agrega LIMIT o agrega con GROUP BY / COUNT para acotar)")
    return "\n".join(lines)


def sql_query(sql: str) -> str:
    """Ejecuta un SELECT sobre la base del banco (conexión de solo lectura) y devuelve una tabla en texto."""
    motivo = None
    # >>> paso-4
    # Válido por esquema no es correcto: strict garantiza que `sql` sea un string, no que sea seguro.
    # La compuerta decide qué SQL puede correr; si rechaza, el motivo vuelve al modelo como is_error.
    motivo = _gate(sql)
    # <<< paso-4
    if motivo:
        motivo = motivo if motivo.startswith(RECHAZADA) else f"{RECHAZADA} {motivo}"
        stage("RECHAZADA", motivo)
        return motivo
    # Defensa en profundidad: aunque la compuerta falle o no exista, esta conexión no puede escribir,
    # devuelve un máximo de filas y se aborta pasado el límite de tiempo.
    stage("VALIDACIÓN", f"segunda capa · conexión de solo lectura · máx. {MAX_ROWS} filas · {TIME_LIMIT_S:.0f} s")
    con = sqlite3.connect(f"file:{contracts.DB_PATH}?mode=ro", uri=True)
    t0 = time.monotonic()
    con.set_progress_handler(lambda: int(time.monotonic() - t0 > TIME_LIMIT_S), 10_000)
    try:
        cur = con.execute(sql)
        rows = cur.fetchmany(MAX_ROWS + 1)
        columns = [d[0] for d in cur.description or []]
    except sqlite3.OperationalError as exc:
        if "interrupted" in str(exc):
            raise TimeoutError(f"la consulta superó {TIME_LIMIT_S:.0f} s y se canceló; simplifícala, filtra o agrega LIMIT") from exc
        raise
    finally:
        con.close()
    stage("EJECUCIÓN", f"sqlite · {min(len(rows), MAX_ROWS)} filas · {time.monotonic() - t0:.2f} s")
    return _render(columns, rows)


# ---------- bloquear_tarjeta ----------

CONFIRM: Callable[[str], str] = input
"""Quien confirma. Recibe la pregunta y devuelve lo que tecleó la persona. Inyectable (pruebas, medir)."""
_confirm_lock = threading.Lock()  # llamadas paralelas: una pregunta a la vez en la terminal


def bloquear_tarjeta(ultimos4: str, motivo: str, confirm: Callable[[str], str] | None = None) -> str:
    """Bloquea una tarjeta activa, SOLO si una persona lo confirma en la terminal.

    El taller no modifica la base commiteada: el bloqueo se registra en runs/bloqueos.jsonl.
    """
    if not re.fullmatch(r"\d{4}", ultimos4):
        raise ValueError("ultimos4 debe ser exactamente 4 dígitos; pídeselos al usuario")
    con = sqlite3.connect(f"file:{contracts.DB_PATH}?mode=ro", uri=True)
    try:
        cards = con.execute(
            "SELECT t.id, c.nombre FROM tarjetas t JOIN clientes c ON c.id = t.cliente_id "
            "WHERE t.ultimos4 = ? AND t.estado = 'activa'", (ultimos4,)).fetchall()
    finally:
        con.close()
    if not cards:
        raise LookupError(f"no hay ninguna tarjeta activa que termine en {ultimos4}; verifica los dígitos con sql_query")
    if len(cards) > 1:
        raise LookupError(f"{len(cards)} tarjetas activas terminan en {ultimos4}; no se puede identificar una sola. "
                          "Dile al usuario que necesita más datos (p. ej. el cliente) y no reintentes con los mismos")
    card_id, nombre = cards[0]
    with _confirm_lock:
        stage("VALIDACIÓN", f"escritura · requiere confirmación humana · tarjeta ****{ultimos4} de {nombre}")
        answer = (confirm or CONFIRM)(f"¿Bloquear la tarjeta ****{ultimos4} de {nombre}? Motivo: {motivo} [s/N] ")
    if answer.strip().lower() not in {"s", "si", "sí", "y", "yes"}:
        msg = f"{RECHAZADA} el usuario no autorizó el bloqueo de la tarjeta ****{ultimos4}. No reintentes salvo que lo pida de nuevo"
        stage("RECHAZADA", msg)
        return msg
    contracts.RUNS_DIR.mkdir(parents=True, exist_ok=True)
    with (contracts.RUNS_DIR / "bloqueos.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "tarjeta_id": card_id, "ultimos4": ultimos4, "motivo": motivo}) + "\n")
    stage("EJECUCIÓN", f"bloqueo registrado · tarjeta {card_id}")
    return f"ok: tarjeta ****{ultimos4} bloqueada (registrado en runs/bloqueos.jsonl; la base del taller no se modifica)"


# ---------- registro ----------

TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="sql_query",
        description=("Ejecuta UNA sentencia SELECT (SQLite) sobre la base del banco y devuelve las filas como texto. "
                     "Solo lectura. Úsala para toda pregunta sobre clientes, cuentas, transacciones o tarjetas."),
        input_schema={"type": "object",
                      "properties": {"sql": {"type": "string", "description": "Una sola sentencia SELECT."}},
                      "required": ["sql"], "additionalProperties": False},
        func=lambda args: sql_query(args["sql"]),
    ),
    ToolSpec(
        name="bloquear_tarjeta",
        description=("Bloquea una tarjeta activa por sus últimos 4 dígitos. Es una ESCRITURA: una persona debe "
                     "confirmarla en la terminal antes de ejecutarse, y puede decir que no. Úsala solo si el usuario "
                     "pidió bloquear una tarjeta."),
        input_schema={"type": "object",
                      "properties": {"ultimos4": {"type": "string", "description": "Últimos 4 dígitos de la tarjeta."},
                                     "motivo": {"type": "string", "description": "Por qué se bloquea (p. ej. extravío, fraude)."}},
                      "required": ["ultimos4", "motivo"], "additionalProperties": False},
        func=lambda args: bloquear_tarjeta(args["ultimos4"], args["motivo"]),
    ),
]
