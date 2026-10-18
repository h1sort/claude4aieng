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
    assert "todavía es un TODO" not in out


def test_huerfano_con_sanitize_sin_escribir(capsys, monkeypatch):
    monkeypatch.setattr(romper, "sanitize_history", lambda m: m)  # lo que hace el TODO(paso-2) vacío
    out = correr("huerfano", capsys)
    assert "sanitize_history todavía es un TODO" in out
    assert "tool_use ids were found without tool_result blocks immediately after" in out
    assert "DESPUÉS" not in out and '\n"¿"\n' not in out  # ni el "¿" suelto de antes
    assert "inserta" not in out  # no dice que insertó algo


def test_truncado(capsys):
    out = correr("truncado", capsys)
    assert "max_tokens" in out and "toolu_01CORTADO" in out
    assert "la llamada cortada (turno 0) NO se ejecutó" in out
    assert "max_tokens 24 -> 96" in out  # el agente reintentó la misma petición con más margen
    assert "tool_use sin tool_result: 0" in out
    assert "DESPUÉS" in out and "LECCIÓN" in out
    assert "tool_use ids were found" not in out
    assert "partial_json" not in out  # sin fuente en FACTS.md


def test_truncado_sin_arreglo_el_seguimiento_da_400(capsys, monkeypatch, modulo_cortado):
    monkeypatch.setattr(romper, "Agent", modulo_cortado("taller/agent.py", {3}).Agent)  # TODO(paso-3) sin escribir
    out = correr("truncado", capsys)
    assert "GUARDÓ el tool_use cortado" in out and "['toolu_01CORTADO']" in out
    assert "tool_use ids were found without tool_result blocks immediately after" in out
    assert "documentado" in out  # sin API: se dice que es el texto documentado, no una llamada en vivo
    assert "DESPUÉS" not in out and "la llamada cortada (turno 0) NO se ejecutó" in out
    assert "TODO(paso-3)" in out


def test_paralelo(capsys):
    out = correr("paralelo", capsys)
    assert "latencia artificial" in out
    assert "secuencial:" in out and "gather:" in out and "más rápido" in out
    assert "toolu_fabricado2" in out


def test_drop(capsys):
    out = correr("drop", capsys)
    assert "compuerta en sql_query: SÍ" in out
    assert "DROP TABLE tarjetas" in out and "FROM secretos" in out
    assert out.count("is_error=True") == 2 and out.count("outcome=rejected") == 2
    assert "no inventamos la respuesta del modelo" in out
    assert "ANTES › sql_query NO consulta" not in out
    assert "LECCIÓN" in out


def test_drop_sin_compuerta_filtra_secretos_y_el_drop_lo_frena_solo_lectura(capsys, monkeypatch, modulo_cortado):
    monkeypatch.setattr(romper, "TOOLS", modulo_cortado("taller/tools.py", {4}).TOOLS)  # TODO(paso-4) sin escribir
    out = correr("drop", capsys)
    assert "compuerta en sql_query: NO" in out
    assert "sk-taller-ant-" in out  # las claves falsas llegaron a la observación
    assert "LLEGÓ A SQLITE y devolvió 5 filas: fuga de secretos" in out
    assert "segunda capa: la conexión de solo lectura" in out
    assert "outcome=ok" in out and "outcome=exec_error" in out and "outcome=rejected" not in out
    assert "DESPUÉS" not in out and "TODO(paso-4)" in out


def test_detectar_compuerta_es_en_ejecucion(monkeypatch, modulo_cortado):
    assert romper.detectar_compuerta() is True
    monkeypatch.setattr(romper, "TOOLS", modulo_cortado("taller/tools.py", {4}).TOOLS)
    assert romper.detectar_compuerta() is False


def test_sin_clave_activa_inyectado(capsys):
    assert romper.main(["huerfano"]) == 0
    out = capsys.readouterr().out
    assert "falta ANTHROPIC_API_KEY" in out and "--inyectado" in out
