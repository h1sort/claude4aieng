"""Un agente sobre la API de Claude, a mano: sin Tool Runner, sin frameworks.

    uv run python -m taller.agent              # conversación nueva
    uv run python -m taller.agent --reanudar   # retoma runs/sesion.json (y sanea el historial)

Tesis: el modelo PROPONE (bloques `tool_use`), la aplicación EJECUTA, y eso se mide (TurnRecord).
Dentro de la conversación, `/sql <consulta>` manda SQL escrito por ti directo a la herramienta,
sin pasar por el modelo (sirve para probar la compuerta).
"""
from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path

from taller import contracts, tools as tools_mod
from taller.contracts import (ErrorCategory, ToolCall, ToolOutcome, ToolResult, ToolSpec, TurnRecord)
from taller.tools import DIM, RECHAZADA, RESET, TOOLS, stage


def tools_payload(tools: list[ToolSpec]) -> list[dict]:
    """Definiciones tal como las espera la API. `strict: true` valida la FORMA del input, no su sentido."""
    return [{"name": t.name, "description": t.description, "input_schema": t.input_schema, "strict": t.strict}
            for t in tools]


def block_to_dict(block) -> dict:
    """Bloque de la respuesta -> dict plano (para reenviarlo en el historial y guardarlo como JSON)."""
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    return block.model_dump(exclude_none=True)  # p. ej. thinking: debe viajar de vuelta intacto


HUERFANO_MSG = ("El proceso se interrumpió antes de ejecutar esta herramienta; no hay resultado. "
                "Si la información sigue siendo necesaria, vuelve a llamar a la herramienta.")


def sanitize_history(messages: list) -> list:
    """Repara un historial con `tool_use` huérfanos (proceso muerto entre el tool_use y su tool_result).

    La API exige un tool_result para CADA tool_use, en el mensaje de usuario inmediato siguiente; si falta,
    responde 400 "tool_use ids were found without tool_result blocks immediately after". No borramos nada:
    le decimos al modelo, con is_error, qué pasó y que reintente si aún hace falta.
    """
    fixed = [dict(m) for m in messages]
    for i, msg in enumerate(fixed):
        if msg["role"] != "assistant" or not isinstance(msg["content"], list):
            continue
        ids = [b["id"] for b in msg["content"] if b.get("type") == "tool_use"]  # lo que el modelo pidió
        if not ids:
            continue
        nxt = fixed[i + 1] if i + 1 < len(fixed) and fixed[i + 1]["role"] == "user" else None
        content = nxt["content"] if nxt else []  # el mensaje de usuario que sigue (puede no existir)
        content = [{"type": "text", "text": content}] if isinstance(content, str) else list(content)
        done = {b.get("tool_use_id") for b in content if b.get("type") == "tool_result"}
        orphans = [t for t in ids if t not in done]  # tool_use sin su tool_result
        hasta = i + 2 if nxt else i + 1  # el mensaje de usuario siguiente (si existe) se reemplaza por el unido
        # TODO(paso-2): si hay `orphans`, mete un tool_result (is_error=True) por cada uno AL PRINCIPIO del mensaje de usuario siguiente
        # Arma `errores`: un {type: tool_result, tool_use_id, is_error: True, content: HUERFANO_MSG} por huérfano.
        # Luego reemplaza fixed[i + 1:hasta] por un mensaje de usuario con errores + content (resultados primero).
        # Sin esto el historial se reenvía tal cual y la API responde 400.
    return fixed


TIMEOUT_HERRAMIENTA_S = 5.0  # tope por llamada: una herramienta lenta no detiene al agente


async def execute_calls(calls: list[ToolCall], tools: list[ToolSpec], timeout_s: float | None = None) -> list[ToolResult]:
    """Ejecuta las llamadas en paralelo con un tope de tiempo por llamada (asyncio.gather conserva el orden)."""
    by_name = {t.name: t for t in tools}

    async def one(call: ToolCall) -> ToolResult:
        tool = by_name.get(call.name)
        if tool is None:
            known = ", ".join(by_name)
            return ToolResult(call.id, ToolOutcome.EXEC_ERROR, f"No existe la herramienta «{call.name}». Usa solo: {known}.", True)
        stage("SOLICITUD", f"{call.name} {DIM}{json.dumps(call.input, ensure_ascii=False)}{RESET}")
        try:
            out = await asyncio.to_thread(tool.func, call.input)  # las herramientas son síncronas
        except Exception as exc:
            msg = f"Falló la ejecución de {call.name}: {type(exc).__name__}: {exc}. Corrige los argumentos y reintenta, o explica el problema."
            stage("OBSERVACIÓN", f"{DIM}error · {msg}{RESET}")
            return ToolResult(call.id, ToolOutcome.EXEC_ERROR, msg, True)
        rejected = out.startswith(RECHAZADA)
        stage("OBSERVACIÓN", "\n" + "\n".join(out.splitlines()[:12]))
        return ToolResult(call.id, ToolOutcome.REJECTED if rejected else ToolOutcome.OK, out, rejected)

    tope = TIMEOUT_HERRAMIENTA_S if timeout_s is None else timeout_s
    hechos = await asyncio.gather(*(asyncio.wait_for(one(c), tope) for c in calls), return_exceptions=True)
    # Versión ingenua: devuelve solo las que terminaron. La que pasó el tope se pierde y su tool_use queda huérfano.
    results = [r for r in hechos if isinstance(r, ToolResult)]
    # TODO(paso-2b): un tool_result POR CADA llamada, también la que no terminó: un timeout se devuelve como is_error
    # Recorre zip(calls, hechos): si r es ToolResult úsalo; si no (timeout/excepción), arma
    # ToolResult(c.id, ToolOutcome.EXEC_ERROR, "<qué pasó y qué intentar>", True). Mientras falte, `romper paralelo` da 400.
    return results


def turn_categories(turn: TurnRecord) -> list[ErrorCategory]:
    """Categorías de error de un turno, derivadas de lo registrado (las usa el JSONL y medir.py)."""
    cats = [ErrorCategory.TRUNCATED] if turn.stop_reason == "max_tokens" and turn.calls and not turn.results else []
    for r in turn.results:
        if r.outcome is ToolOutcome.REJECTED:
            cats.append(ErrorCategory.GATE_REJECTED)
        elif r.outcome is ToolOutcome.EXEC_ERROR:
            cats.append(ErrorCategory.WRONG_TOOL if r.content.startswith("No existe la herramienta") else ErrorCategory.EXEC_ERROR)
    return cats


MAX_TOKENS_TOPE = 16_384
"""Tope al que sube max_tokens al reintentar una llamada cortada."""

SYSTEM_BASE = (
    "Eres un agente de datos de un banco minorista mexicano. Respondes preguntas con la herramienta sql_query "
    "(una sola sentencia SELECT de SQLite) y, solo si el usuario lo pide, bloqueas tarjetas con bloquear_tarjeta "
    "(una persona debe confirmarlo; si lo rechaza, no insistas). No inventes números: consulta. "
    "Si una herramienta devuelve un error, léelo, corrige y reintenta una vez; si no se puede, dilo. "
    "Fecha de hoy: 2026-10-18. Responde en español, breve, con cifras y su denominador cuando aplique.\n\n"
    "Tablas disponibles:\n{ddl}"
)


def build_system() -> str:
    """Prompt de sistema con el DDL leído del archivo sqlite (sin la tabla `secretos`: el modelo no necesita saber de ella)."""
    try:
        with sqlite3.connect(f"file:{contracts.DB_PATH}?mode=ro", uri=True) as con:
            ddl = "\n".join(s for (s,) in con.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name != 'secretos' AND sql IS NOT NULL"))
    except sqlite3.Error:
        ddl = "(no se pudo leer el esquema; ejecuta `uv run scripts/seed.py`)"
    return SYSTEM_BASE.format(ddl=ddl)


class Agent:
    def __init__(self, client, model: str | None = None, tools: list[ToolSpec] = TOOLS, system: str | None = None,
                 max_tokens: int = 4096, max_turns: int = 12, log_path: str | Path | None = None, echo: bool = True,
                 on_message: Callable[[list], None] | None = None):
        self.client, self.model, self.tools = client, model or contracts.get_model_id(), tools
        self.system, self.max_tokens, self.max_turns = system or build_system(), max_tokens, max_turns
        self.log_path, self.echo, self.on_message = Path(log_path) if log_path else None, echo, on_message

    def _save(self, messages: list) -> None:
        if self.on_message:
            self.on_message(messages)  # guardar la sesión TRAS cada mensaje: así un kill deja huérfanos reales

    async def run(self, messages: list) -> list[TurnRecord]:
        """Itera mientras el modelo pida herramientas. Modifica `messages` en sitio; devuelve un TurnRecord por turno."""
        tools_mod.ECHO.set(self.echo)
        self.turns = turns = []  # visible desde fuera aunque run() termine con una excepción (lo usa romper.py)
        for index in range(self.max_turns):
            if turns and ErrorCategory.TRUNCATED in turn_categories(turns[-1]):
                stage("MODELO", f"reintento de la misma petición con max_tokens={self.max_tokens}")
            t0 = time.monotonic()
            resp = await self.client.messages.create(  # tool_choice queda en auto: any/tool dan 400 en Sonnet/Opus 5.5
                model=self.model, max_tokens=self.max_tokens, system=self.system,
                tools=tools_payload(self.tools), messages=messages)
            turn = TurnRecord(index, self.model, resp.stop_reason, resp.usage.input_tokens, resp.usage.output_tokens,
                              time.monotonic() - t0)
            turns.append(turn)
            for block in resp.content:
                if block.type == "text" and block.text.strip():
                    stage("MODELO", block.text.strip())
            uses = [b for b in resp.content if b.type == "tool_use"]
            turn.calls = [ToolCall(b.id, b.name, b.input) for b in uses]
            if resp.stop_reason == "max_tokens":
                stage("MODELO", f"stop_reason=max_tokens con max_tokens={self.max_tokens}"
                                + (f": la llamada a {', '.join(b.name for b in uses)} puede venir cortada" if uses else ""))
            # TODO(paso-3): con stop_reason == "max_tokens" y algún tool_use el JSON puede estar cortado: ni lo ejecutes ni lo guardes
            # Sube self.max_tokens (min(.. * 4, MAX_TOKENS_TOPE)), registra el turno con self._log(turn) y `continue`:
            # se repite la misma petición. Mientras falte, el tool_use cortado se guarda y el siguiente mensaje da 400.
            messages.append({"role": "assistant", "content": [block_to_dict(b) for b in resp.content]})
            self._save(messages)
            if resp.stop_reason != "tool_use":  # end_turn, refusal, max_tokens sin llamadas...
                if resp.stop_reason in ("refusal", "max_tokens"):
                    stage("MODELO", f"(la respuesta terminó con stop_reason={resp.stop_reason})")
                self._log(turn)
                break
            results: list[ToolResult] = []
            # TODO(paso-1): ejecuta las llamadas con execute_calls y contesta con UN mensaje de usuario (un tool_result por llamada)
            # Un tool_result por llamada, con su tool_use_id y ANTES de cualquier texto; is_error si falló.
            # Mientras falte, `results` queda vacío y el bucle falla justo debajo con NotImplementedError.
            if not results:
                raise NotImplementedError("paso-1: ejecuta las llamadas y devuelve los tool_result en un mensaje de usuario")
            turn.results = results
            self._save(messages)
            self._log(turn)
        else:
            stage("MODELO", f"(se acabaron los turnos: max_turns={self.max_turns})")
        return turns

    def _log(self, turn: TurnRecord) -> None:
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            row = dataclasses.asdict(turn) | {"ts": time.time(), "categories": [c.value for c in turn_categories(turn)]}
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------- CLI ----------

SESSION_PATH = contracts.RUNS_DIR / "sesion.json"


def add_user_text(messages: list, text: str) -> None:
    """Texto nuevo del usuario. Si el historial acaba en un mensaje de tool_results, va en ese mismo mensaje, después."""
    last = messages[-1] if messages else None
    if last and last["role"] == "user" and isinstance(last["content"], list):
        last["content"].append({"type": "text", "text": text})
    else:
        messages.append({"role": "user", "content": text})


def save_session(messages: list, path: Path = SESSION_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(messages, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    import anthropic

    parser = argparse.ArgumentParser(description="Agente de herramientas del taller")
    parser.add_argument("--reanudar", action="store_true", help=f"retoma {SESSION_PATH.relative_to(contracts.ROOT)}")
    args = parser.parse_args()
    messages: list = []
    if args.reanudar:
        messages = sanitize_history(json.loads(SESSION_PATH.read_text(encoding="utf-8")))
        stage("MODELO", f"sesión retomada: {len(messages)} mensajes")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    agent = Agent(anthropic.AsyncAnthropic(), log_path=contracts.RUNS_DIR / f"agente-{stamp}.jsonl",
                  on_message=save_session)
    print(f"{DIM}modelo {agent.model} · /sql <consulta> la escribes tú · Ctrl-D para salir · "
          f"sesión en {SESSION_PATH.relative_to(contracts.ROOT)}{RESET}\n")
    while True:
        try:
            text = input("tú › ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not text:
            continue
        if text.startswith("/sql "):
            stage("SOLICITUD", f"escrita por el orador\n{DIM}{text[5:]}{RESET}")
            asyncio.run(execute_calls([ToolCall("inyectado", "sql_query", {"sql": text[5:]})], TOOLS))
            continue
        add_user_text(messages, text)
        save_session(messages)
        try:
            asyncio.run(agent.run(messages))
        except KeyboardInterrupt:
            print("\ninterrumpido: la sesión quedó guardada; retómala con --reanudar")
            return
        except anthropic.APIStatusError as exc:
            stage("RECHAZADA", f"la API respondió {exc.status_code}: {exc.message}")
        print()


if __name__ == "__main__":
    main()
