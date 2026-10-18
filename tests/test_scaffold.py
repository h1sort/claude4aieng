"""Humo del andamio: la base se siembra de forma determinista y los contratos importan."""
from __future__ import annotations

import dataclasses
import json
import sqlite3

from taller import contracts
from taller.contracts import (DB_PATH, ErrorCategory, ToolCall, ToolOutcome, ToolResult,
                              ToolSpec, TurnRecord, get_model_id)


def test_seed_counts(seeded_db):
    con = sqlite3.connect(seeded_db)
    n = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
         for t in ("clientes", "cuentas", "transacciones", "tarjetas", "secretos")}
    assert n["clientes"] == 200
    assert 4000 <= n["transacciones"] <= 6000
    assert n["secretos"] >= 3
    assert seeded_db.stat().st_size < 1_000_000


def test_seed_has_messiness(seeded_db):
    con = sqlite3.connect(seeded_db)
    assert con.execute("SELECT COUNT(*) FROM cuentas WHERE saldo_mxn = 0 AND abierta = 1").fetchone()[0] > 0
    sin_mov = con.execute("""SELECT COUNT(*) FROM clientes c WHERE NOT EXISTS (
        SELECT 1 FROM transacciones t JOIN cuentas a ON a.id = t.cuenta_id
        WHERE a.cliente_id = c.id AND t.fecha >= '2026-07-20')""").fetchone()[0]
    assert sin_mov > 0


def test_committed_db_matches_seed(seeded_db):
    """data/banco.sqlite versionada es la que produce scripts/seed.py."""
    if not DB_PATH.exists():
        return
    q = "SELECT COUNT(*), SUM(monto_mxn) FROM transacciones"
    assert sqlite3.connect(seeded_db).execute(q).fetchone() == sqlite3.connect(DB_PATH).execute(q).fetchone()


def test_contracts_import_and_serialize(monkeypatch):
    assert {c.value for c in ErrorCategory} == {
        "wrong_tool", "bad_args", "gate_rejected", "exec_error", "truncated", "orphaned"}
    assert {o.value for o in ToolOutcome} == {"ok", "rejected", "exec_error"}
    spec = ToolSpec(name="eco", description="d", input_schema={"type": "object"}, func=lambda i: "x")
    assert spec.strict is True
    turn = TurnRecord(turn_index=0, model="m", stop_reason="tool_use", input_tokens=1, output_tokens=2,
                      latency_s=0.1, calls=[ToolCall("toolu_1", "eco", {})],
                      results=[ToolResult("toolu_1", ToolOutcome.REJECTED, "no", True)])
    assert json.loads(json.dumps(dataclasses.asdict(turn)))["results"][0]["outcome"] == "rejected"
    monkeypatch.delenv("MODEL_ID", raising=False)
    assert get_model_id() == contracts.DEFAULT_MODEL_ID == "claude-sonnet-5-5"
    monkeypatch.setenv("MODEL_ID", "otro")
    assert get_model_id() == "otro"
