"""Los 4 modos de taller/romper.py en --inyectado: sin red, con las cadenas clave."""
from __future__ import annotations

import pytest

from taller import romper


@pytest.fixture(autouse=True)
def sin_api(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(romper, "LATENCIA_S", 0.2)  # el test no necesita esperar 0.8 s por llamada


def correr(modo: str, capsys, *extra: str) -> str:
    assert romper.main([modo, "--inyectado", *extra]) == 0
    return capsys.readouterr().out


def test_huerfano(capsys):
    out = correr("huerfano", capsys)
    assert "ANTES" in out and "DESPUÉS" in out and "LECCIÓN" in out
    assert "tool_use ids were found without tool_result blocks immediately after" in out
    assert "toolu_01HUERFANO" in out
    assert '"is_error": true' in out  # el historial saneado trae el tool_result de reparación


def test_truncado(capsys):
    out = correr("truncado", capsys)
    assert "max_tokens" in out and "toolu_01CORTADO" in out
    assert "ejecuciones de sql_query: 0" in out
    assert "DESPUÉS" in out and "LECCIÓN" in out


def test_paralelo(capsys):
    out = correr("paralelo", capsys)
    assert "latencia artificial" in out
    assert "secuencial:" in out and "gather:" in out and "más rápido" in out
    assert "toolu_fabricado2" in out


def test_drop(capsys):
    out = correr("drop", capsys)
    assert "DROP TABLE tarjetas" in out
    assert "is_error=True" in out and "outcome=rejected" in out
    assert "no inventamos la respuesta del modelo" in out
    assert "LECCIÓN" in out


def test_sin_clave_activa_inyectado(capsys):
    assert romper.main(["huerfano"]) == 0
    out = capsys.readouterr().out
    assert "falta ANTHROPIC_API_KEY" in out and "--inyectado" in out
