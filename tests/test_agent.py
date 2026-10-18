"""Pruebas del agente con un cliente falso: sin red ni API key.

El cliente falso devuelve objetos con la forma del SDK (content con bloques text/tool_use,
stop_reason, usage) y guarda cada petición para inspeccionar lo que el agente envió.
"""
from __future__ import annotations

import asyncio
import copy
import json
import time
from types import SimpleNamespace as NS

import pytest

from taller import agent as agent_mod
from taller.agent import Agent, execute_calls, sanitize_history, tools_payload, turn_categories
from taller.contracts import ErrorCategory, ToolCall, ToolOutcome, ToolSpec
from taller.tools import TOOLS


def text(t):
    return NS(type="text", text=t)


def use(id_, name, **inp):
    return NS(type="tool_use", id=id_, name=name, input=inp)


def reply(stop_reason, *content):
    return NS(content=list(content), stop_reason=stop_reason, usage=NS(input_tokens=10, output_tokens=5))


class FakeClient:
    def __init__(self, *responses):
        self.responses, self.requests = list(responses), []
        self.messages = NS(create=self.create)

    async def create(self, **kwargs):
        self.requests.append(copy.deepcopy(kwargs))  # foto del historial en ese momento
        return self.responses.pop(0)


def make_agent(client, tools=None, **kw):
    return Agent(client, model="modelo-falso", tools=tools or TOOLS, system="sistema", echo=False, **kw)


def slow_tool(name, delay, out):
    def func(args):
        time.sleep(delay)
        return out
    return ToolSpec(name, "d", {"type": "object", "properties": {}, "additionalProperties": False}, func)


def run(agent, messages):
    return asyncio.run(agent.run(messages))


def test_tools_payload_is_strict_and_closed():
    payload = tools_payload(TOOLS)
    assert {p["name"] for p in payload} == {"sql_query", "bloquear_tarjeta"}
    for p in payload:
        assert p["strict"] is True
        assert p["input_schema"]["additionalProperties"] is False


def test_parallel_calls_answered_in_one_user_message_with_results_first():
    tools = [slow_tool("a", 0.3, "A"), slow_tool("b", 0.3, "B")]
    client = FakeClient(
        reply("tool_use", text("voy"), use("t1", "a"), use("t2", "b")),
        reply("end_turn", text("listo")),
    )
    messages = [{"role": "user", "content": "hola"}]
    t0 = time.monotonic()
    turns = run(make_agent(client, tools), messages)
    assert time.monotonic() - t0 < 0.55  # en paralelo: ~0.3 s, no 0.6 s
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]
    results = messages[2]["content"]
    assert [b["type"] for b in results] == ["tool_result", "tool_result"]
    assert [b["tool_use_id"] for b in results] == ["t1", "t2"]
    assert [b["content"] for b in results] == ["A", "B"]
    assert all("is_error" not in b for b in results)
    # el segundo request llevó el historial con los resultados
    assert client.requests[1]["messages"][-1]["content"][0]["tool_use_id"] == "t1"
    assert client.requests[0]["tools"][0]["strict"] is True
    assert "tool_choice" not in client.requests[0]
    assert [t.stop_reason for t in turns] == ["tool_use", "end_turn"]
    assert (turns[0].input_tokens, turns[0].output_tokens) == (10, 5)
    assert [r.outcome for r in turns[0].results] == [ToolOutcome.OK, ToolOutcome.OK]


def test_unknown_tool_is_error_and_exception_is_exec_error():
    def boom(args):
        raise RuntimeError("se cayó")
    tools = [ToolSpec("boom", "d", {"type": "object", "properties": {}, "additionalProperties": False}, boom)]
    results = asyncio.run(execute_calls([ToolCall("u1", "no_existe", {}), ToolCall("u2", "boom", {})], tools))
    assert [r.tool_use_id for r in results] == ["u1", "u2"]
    assert all(r.is_error for r in results)
    assert results[0].outcome is ToolOutcome.EXEC_ERROR and "boom" in results[0].content
    assert results[1].outcome is ToolOutcome.EXEC_ERROR and "se cayó" in results[1].content


def test_unknown_tool_in_loop_goes_back_to_model_as_is_error():
    client = FakeClient(reply("tool_use", use("t1", "inventada")), reply("end_turn", text("ok")))
    messages = [{"role": "user", "content": "x"}]
    turns = run(make_agent(client), messages)
    assert messages[2]["content"][0]["is_error"] is True
    assert turn_categories(turns[0]) == [ErrorCategory.WRONG_TOOL]


def test_gate_rejection_is_error_result():
    client = FakeClient(reply("tool_use", use("t1", "sql_query", sql="DROP TABLE clientes")), reply("end_turn", text("ok")))
    messages = [{"role": "user", "content": "x"}]
    turns = run(make_agent(client), messages)
    block = messages[2]["content"][0]
    # con la compuerta (paso-4) es un rechazo; sin ella, la conexión de solo lectura lo frena como error de ejecución
    assert block["is_error"] is True
    assert turns[0].results[0].outcome in (ToolOutcome.REJECTED, ToolOutcome.EXEC_ERROR)


def test_truncated_tool_use_is_not_executed():
    called = []
    spy = ToolSpec("spy", "d", {"type": "object", "properties": {}, "additionalProperties": False},
                   lambda a: called.append(a) or "x")
    client = FakeClient(reply("max_tokens", text("voy a"), use("t1", "spy")))
    messages = [{"role": "user", "content": "x"}]
    turns = run(make_agent(client, [spy], max_tokens=16), messages)
    assert called == []
    assert len(client.requests) == 1  # no hubo reintento silencioso
    assert turns[0].stop_reason == "max_tokens" and turns[0].results == []
    assert turn_categories(turns[0]) == [ErrorCategory.TRUNCATED]
    # el historial queda válido: ningún tool_use sin tool_result
    assert all(b["type"] != "tool_use" for m in messages[1:] for b in m["content"])


def test_truncated_run_prints_clear_message(capsys):
    client = FakeClient(reply("max_tokens", use("t1", "sql_query")))
    agent = Agent(client, model="m", system="s", echo=True)
    run(agent, [{"role": "user", "content": "x"}])
    assert "max_tokens" in capsys.readouterr().out


def test_sanitize_inserts_error_result_first():
    history = [
        {"role": "user", "content": "q"},
        {"role": "assistant", "content": [{"type": "text", "text": "voy"},
                                          {"type": "tool_use", "id": "t1", "name": "sql_query", "input": {"sql": "select 1"}},
                                          {"type": "tool_use", "id": "t2", "name": "sql_query", "input": {"sql": "select 2"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t2", "content": "2"},
                                     {"type": "text", "text": "sigue"}]},
    ]
    before = copy.deepcopy(history)
    fixed = sanitize_history(history)
    assert history == before  # no muta la entrada
    content = fixed[2]["content"]
    assert [b["type"] for b in content] == ["tool_result", "tool_result", "text"]
    assert content[0]["tool_use_id"] == "t1" and content[0]["is_error"] is True
    assert "interrump" in content[0]["content"]
    assert content[1]["tool_use_id"] == "t2" and "is_error" not in content[1]


def test_sanitize_when_history_ends_at_tool_use_and_is_idempotent():
    history = [{"role": "user", "content": "q"},
               {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "x", "input": {}}]}]
    fixed = sanitize_history(history)
    assert fixed[-1]["role"] == "user" and fixed[-1]["content"][0]["is_error"] is True
    assert sanitize_history(fixed) == fixed
    # texto nuevo del usuario se une al mensaje de resultados, después de ellos
    agent_mod.add_user_text(fixed, "hola otra vez")
    assert [b["type"] for b in fixed[-1]["content"]] == ["tool_result", "text"]


def test_sanitize_string_user_message_after_orphan():
    history = [{"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "x", "input": {}}]},
               {"role": "user", "content": "nuevo mensaje"}]
    content = sanitize_history(history)[1]["content"]
    assert [b["type"] for b in content] == ["tool_result", "text"]


def test_bloquear_tarjeta_asks_confirmation(tmp_path, monkeypatch):
    from taller import contracts, tools
    monkeypatch.setattr(contracts, "RUNS_DIR", tmp_path)
    import sqlite3
    ultimos4 = sqlite3.connect(contracts.DB_PATH).execute(
        "SELECT ultimos4 FROM tarjetas WHERE estado='activa' GROUP BY 1 HAVING count(*)=1 LIMIT 1").fetchone()[0]
    no = tools.bloquear_tarjeta(ultimos4, "extravío", confirm=lambda q: "n")
    assert no.startswith("rechazada:")
    assert not (tmp_path / "bloqueos.jsonl").exists()
    si = tools.bloquear_tarjeta(ultimos4, "extravío", confirm=lambda q: "s")
    assert si.startswith("ok")
    assert json.loads((tmp_path / "bloqueos.jsonl").read_text())["ultimos4"] == ultimos4


def test_log_and_on_message(tmp_path):
    saved = []
    client = FakeClient(reply("end_turn", text("hola")))
    agent = make_agent(client, log_path=tmp_path / "x.jsonl", on_message=lambda m: saved.append(len(m)))
    run(agent, [{"role": "user", "content": "x"}])
    row = json.loads((tmp_path / "x.jsonl").read_text().splitlines()[0])
    assert row["stop_reason"] == "end_turn" and row["input_tokens"] == 10 and row["categories"] == []
    assert saved == [2]
