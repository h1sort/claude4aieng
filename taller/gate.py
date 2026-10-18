"""La compuerta: el compilador de SQLite decide qué SQL puede ejecutarse. Sin LLM, sin regex.

    from taller.gate import validate
    motivo = validate(sql)   # None si se permite; si no, un texto para el tool_result con is_error

Por qué compilar con un autorizador y no filtrar texto:
  * Una lista de palabras prohibidas ("DROP", "DELETE"...) se esquiva con comentarios, mayúsculas,
    espacios raros o funciones; el compilador ya resolvió todo eso antes de preguntarnos.
  * El autorizador ve las ACCIONES que la sentencia ya compilada realizaría (leer la columna X de la
    tabla Y, escribir, hacer DDL, PRAGMA, ATTACH...) y no el texto: `/*DROP*/ SELECT 1` es un SELECT,
    y una lectura de `secretos` dentro de un JOIN o una subconsulta igual pasa por SQLITE_READ.
  * `EXPLAIN` compila sin ejecutar y sin tocar datos: usamos una copia VACÍA del esquema.
"""
from __future__ import annotations

import sqlite3
from functools import lru_cache

from taller.contracts import DB_PATH

ALLOWED_TABLES = {"clientes", "cuentas", "transacciones", "tarjetas"}


@lru_cache(maxsize=1)
def _schema_ddl() -> str:
    """Solo los CREATE TABLE de la base real (sqlite_master); jamás filas."""
    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as real:
        rows = real.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND sql IS NOT NULL")
        return ";\n".join(sql for (sql,) in rows)


def _authorizer(action, arg1, arg2, db, trigger):
    if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_RECURSIVE):
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION and arg2 != "load_extension":
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ and arg1 in ALLOWED_TABLES:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY  # escrituras, DDL, PRAGMA, ATTACH, secretos, load_extension...


_TABLAS = ", ".join(sorted(ALLOWED_TABLES))
_SOLO_LECTURA = f"rechazada: solo se permite leer {_TABLAS}; reescribe la consulta como un SELECT"


def validate(sql: str) -> str | None:
    """None si `sql` es una sola sentencia de solo lectura sobre ALLOWED_TABLES; si no, el motivo."""
    if not isinstance(sql, str) or not sql.strip(" \t\r\n;"):
        return "rechazada: la consulta está vacía; envía un SELECT sobre " + _TABLAS
    con = sqlite3.connect(":memory:", check_same_thread=False)  # una por llamada: sin candados
    try:
        con.executescript(_schema_ddl())   # esquema vacío, sin autorizador todavía
        con.set_authorizer(_authorizer)
        programa = con.execute("EXPLAIN " + sql).fetchall()  # compila, no ejecuta
        # VACUUM y REINDEX compilan sin pasar por el autorizador; un SELECT siempre emite ResultRow
        if not any(op[1] == "ResultRow" for op in programa):
            return _SOLO_LECTURA
    except sqlite3.ProgrammingError:
        return "rechazada: una sola sentencia por solicitud; envía un único SELECT sin ';' intermedios"
    except sqlite3.DatabaseError as exc:
        msg = str(exc)
        if "prohibited" in msg or "not authorized" in msg:
            if "secretos" in msg or "sqlite_" in msg:
                return f"{_SOLO_LECTURA}. La tabla a la que accediste no está disponible ({msg})"
            return _SOLO_LECTURA
        return f"rechazada: SQL inválido ({msg}); corrige la sintaxis y usa solo las tablas {_TABLAS}"
    finally:
        con.close()
    return None
