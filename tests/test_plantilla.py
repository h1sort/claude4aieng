import pytest

from taller import plantilla


@pytest.mark.parametrize("familia,marcador", [("qwen", "<tool_call>"), ("deepseek", "<｜tool▁calls▁begin｜>")])
def test_renderiza_familia(familia, marcador):
    texto = plantilla.renderizar(familia)
    assert marcador in texto
    assert "sql_query" in texto
    assert "tarjetas bloqueadas" in texto and "26" in texto
    assert "{{" not in texto and "{%" not in texto


def test_qwen_formato_json_en_tool_call():
    texto = plantilla.renderizar("qwen")
    assert '<tool_call>\n{"name": "sql_query", "arguments": {"query":' in texto
    assert "<|im_start|>assistant" in texto and "<tool_response>" in texto


def test_deepseek_usa_bloque_json_y_separador():
    texto = plantilla.renderizar("deepseek")
    assert "function<｜tool▁sep｜>sql_query\n```json\n" in texto
    assert "<｜tool▁outputs▁begin｜>" in texto


def test_parser_de_una_familia_no_sirve_para_la_otra():
    import re
    emitido = {f: re.search(plantilla.FAMILIAS[f][2], plantilla.renderizar(f), re.S).group() for f in plantilla.FAMILIAS}
    for fam, otra in (("qwen", "deepseek"), ("deepseek", "qwen")):
        assert re.findall(plantilla.FAMILIAS[fam][3], emitido[fam], re.S)
        assert not re.findall(plantilla.FAMILIAS[fam][3], emitido[otra], re.S)


def test_resaltar_marca_especiales_y_caja():
    out = plantilla.resaltar(plantilla.renderizar("qwen"), "qwen", color=True)
    assert "\033[1;36m<|im_start|>" in out and "┌─" in out
