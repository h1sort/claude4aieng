"""Contrato compartido del taller: solo tipos, sin lógica.

Todas las tareas importan de aquí. Los nombres son estables:

    from taller.contracts import (
        ToolSpec, ToolCall, ToolResult, ToolOutcome, TurnRecord, ErrorCategory,
        MODEL_ID, DEFAULT_MODEL_ID, get_model_id, ROOT, DB_PATH, RUNS_DIR,
    )

Los enums heredan de `str`, así que `json.dumps(dataclasses.asdict(turn))` los
serializa directo a `runs/*.jsonl`.
"""
from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# ---------- constantes ----------

DEFAULT_MODEL_ID: str = "claude-sonnet-5-5"
"""Modelo por omisión del taller."""

ROOT: Path = Path(__file__).resolve().parents[1]
"""Raíz del repositorio."""

DB_PATH: Path = ROOT / "data" / "banco.sqlite"
"""Base SQLite sintética que genera `scripts/seed.py`."""

RUNS_DIR: Path = ROOT / "runs"
"""Carpeta de bitácoras `*.jsonl` y mediciones (ignorada por git)."""


def get_model_id() -> str:
    """Modelo a usar: la variable de entorno `MODEL_ID`, o `DEFAULT_MODEL_ID`."""
    return os.environ.get("MODEL_ID") or DEFAULT_MODEL_ID


MODEL_ID: str = get_model_id()
"""Valor de `get_model_id()` al importar. Usa la función si necesitas releer el entorno."""


# ---------- herramientas ----------

ToolFunc = Callable[[dict[str, Any]], str]
"""Implementación de una herramienta: recibe el `input` del `tool_use` (ya como dict)
y devuelve el texto del `tool_result`. Es síncrona; el agente la corre con
`asyncio.to_thread` para las llamadas paralelas. Si falla, lanza una excepción."""


@dataclass(frozen=True)
class ToolSpec:
    """Definición de una herramienta: lo que se manda a la API y lo que se ejecuta aquí."""

    name: str
    """Nombre, `^[a-zA-Z0-9_-]{1,128}$`."""
    description: str
    """Qué hace y cuándo usarla; es lo que el modelo lee."""
    input_schema: dict[str, Any]
    """JSON Schema del input (con `additionalProperties: false` si `strict`)."""
    func: ToolFunc
    """Callable que ejecuta la herramienta en la aplicación (no en el modelo)."""
    strict: bool = True
    """`strict: true` en la definición: garantiza forma, no significado."""


@dataclass(frozen=True)
class ToolCall:
    """Un bloque `tool_use` que el modelo propuso."""

    id: str
    """`tool_use.id`; el `tool_result` debe devolverlo como `tool_use_id`."""
    name: str
    input: dict[str, Any]


class ToolOutcome(str, Enum):
    """Resultado de procesar una llamada a herramienta."""

    OK = "ok"
    """Se ejecutó y devolvió contenido."""
    REJECTED = "rejected"
    """La compuerta (o la confirmación humana) no la dejó ejecutar."""
    EXEC_ERROR = "exec_error"
    """Se intentó ejecutar y la herramienta falló."""


@dataclass
class ToolResult:
    """Un bloque `tool_result` que la aplicación devuelve al modelo."""

    tool_use_id: str
    outcome: ToolOutcome
    content: str
    """Texto para el modelo; si `is_error`, debe decir qué falló y qué intentar."""
    is_error: bool = False
    """Se manda como `is_error` en el `tool_result` (True para rejected y exec_error)."""


class ErrorCategory(str, Enum):
    """Categorías de error de herramientas que mide `taller/medir.py`."""

    WRONG_TOOL = "wrong_tool"
    """El modelo eligió una herramienta equivocada (o usó una cuando no hacía falta)."""
    BAD_ARGS = "bad_args"
    """Argumentos inválidos o que no cumplen el esquema."""
    GATE_REJECTED = "gate_rejected"
    """Válida por esquema pero la compuerta la rechazó."""
    EXEC_ERROR = "exec_error"
    """La herramienta falló al ejecutarse."""
    TRUNCATED = "truncated"
    """`stop_reason: "max_tokens"` cortó un `tool_use`; no se ejecuta."""
    ORPHANED = "orphaned"
    """`tool_use` sin su `tool_result` en el historial."""


# ---------- registro de turnos ----------

@dataclass
class TurnRecord:
    """Un turno del bucle: una llamada a la API y lo que la aplicación hizo con ella."""

    turn_index: int
    """Número de turno dentro de la tarea, desde 0."""
    model: str
    stop_reason: str | None
    """`end_turn`, `tool_use`, `max_tokens`, ..."""
    input_tokens: int
    output_tokens: int
    latency_s: float
    """Segundos de la llamada a la API."""
    calls: list[ToolCall] = field(default_factory=list)
    """`tool_use` completos que el modelo propuso en este turno."""
    results: list[ToolResult] = field(default_factory=list)
    """`tool_result` que se devolvieron, en el mismo orden que `calls`."""
