"""scripts/cortar_pasos.py: el reemplazo de bloques sobre una cadena de ejemplo (sin tocar git)."""
from __future__ import annotations

import ast
import importlib.util
import re
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cortar_pasos", ROOT / "scripts" / "cortar_pasos.py")
cp = importlib.util.module_from_spec(spec)
sys.modules["cortar_pasos"] = cp  # dataclasses lo busca ahí
spec.loader.exec_module(cp)

EN_BRANCH = (ROOT / "BRANCH.md").exists()  # BRANCH.md solo existe en paso-*; allí los bloques ya están cortados

FIXTURE = textwrap.dedent('''\
    def uno(messages):
        fixed = list(messages)
        # >>> paso-2
        # solución del paso 2
        for m in fixed:
            m["ok"] = True
        # <<< paso-2
        return fixed


    class Agente:
        async def run(self, resp):
            if resp:
                # >>> paso-3
                if resp == "corte":
                    return None
                # <<< paso-3
                x = 1
                # >>> paso-1
                x = await ejecutar()
                # <<< paso-1
                if not x:
                    raise NotImplementedError("paso-1: falta")
            return x


    def sql(s):
        motivo = None
        # >>> paso-4
        motivo = _gate(s)
        # <<< paso-4
        return motivo
''')


def lineas(texto: str) -> list[str]:
    return texto.splitlines()


def test_busca_los_cuatro_bloques_con_su_sangria():
    bloques = cp.buscar_bloques(FIXTURE)
    assert [(b.n, len(b.sangria)) for b in bloques] == [(2, 4), (3, 12), (1, 12), (4, 4)]


def test_reemplaza_solo_los_pedidos_y_conserva_la_sangria():
    out = cp.cortar_bloques(FIXTURE, {2, 4})
    assert "solución del paso 2" not in out and "_gate(s)" not in out
    assert "    # TODO(paso-2): " in out and "    # TODO(paso-4): " in out
    assert 'if resp == "corte"' in out and "await ejecutar()" in out  # 1 y 3 intactos
    assert "# >>> paso-1" in out and "# >>> paso-3" in out  # y conservan sus marcadores
    assert "# >>> paso-2" not in out and "# >>> paso-4" not in out
    for linea in lineas(out):
        if "TODO(paso-" in linea:
            assert linea.startswith("    # TODO(paso-") or linea.startswith("        # TODO(paso-")


def test_sangria_de_bloques_anidados_en_if():
    out = cp.cortar_bloques(FIXTURE, {1, 3})
    todo = [x for x in lineas(out) if "TODO(paso-" in x]
    assert todo and all(x.startswith(" " * 12 + "# TODO(paso-") for x in todo)
    # el código extra del reemplazo hereda esa sangría
    siguiente = lineas(out)[lineas(out).index(todo[0]) + 1]
    assert siguiente.startswith(" " * 12)


@pytest.mark.parametrize("k", range(6))
def test_semantica_de_cada_branch(k):
    out = cp.cortar_bloques(FIXTURE, cp.ramas_de(k))
    ast.parse(out)  # siempre sigue siendo Python válido
    for n in cp.PASOS:
        cortado = n > k
        assert (f"# TODO(paso-{n}):" in out) is cortado
        assert (f"# >>> paso-{n}" in out) is (not cortado)
    assert cp.ramas_de(k) == {n for n in (1, 2, 3, 4) if n > k}


def test_paso_4_y_paso_5_no_cambian_nada():
    assert cp.cortar_bloques(FIXTURE, cp.ramas_de(4)) == FIXTURE
    assert cp.cortar_bloques(FIXTURE, cp.ramas_de(5)) == FIXTURE


def test_paso_0_no_deja_marcadores_y_es_idempotente():
    out = cp.cortar_bloques(FIXTURE, cp.ramas_de(0))
    assert not re.search(r"# [<>]{3} paso-", out)
    assert cp.cortar_bloques(out, cp.ramas_de(0)) == out
    assert cp.buscar_bloques(out) == []


def test_conserva_finales_de_linea_crlf():
    out = cp.cortar_bloques(FIXTURE.replace("\n", "\r\n"), {1, 2, 3, 4})
    assert "\r\n" in out and "\n" not in out.replace("\r\n", "")


def test_la_pista_es_una_linea_y_en_espanol():
    for n, r in cp.REEMPLAZOS.items():
        assert "\n" not in r.pista and len(r.pista) < 130, n
        assert re.search(r"[a-záéíóú]", r.pista)
    assert set(cp.REEMPLAZOS) == set(cp.PASOS)


def test_paso_4_deja_sql_funcionando_sin_compuerta():
    out = cp.cortar_bloques(FIXTURE, {4})
    todo = lineas(out)
    i = next(i for i, x in enumerate(todo) if "TODO(paso-4)" in x)
    assert "_gate" in todo[i]  # la pista dice qué llamar
    assert "SIN COMPUERTA" in out  # y avisa en consola que no hay compuerta
    assert "motivo = _gate(s)" not in out


@pytest.mark.parametrize("texto, mensaje", [
    ("# >>> paso-1\nx\n", "no se cierra"),
    ("x\n# <<< paso-1\n", "sin su"),
    ("# >>> paso-1\n# >>> paso-2\n# <<< paso-2\n# <<< paso-1\n", "dentro del bloque"),
    ("# >>> paso-1\nx\n# <<< paso-2\n", "sin su"),
])
def test_marcadores_mal_formados_fallan_con_claridad(texto, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        cp.buscar_bloques(texto)


def test_branch_md_dice_donde_estas_y_que_sigue():
    for k in range(6):
        md = cp.branch_md(k)
        assert f"Estás en paso-{k}: lo que sigue es " in md
    assert "TODO(paso-1)" in cp.branch_md(0) and "TODO(paso-2)" in cp.branch_md(1)
    assert "TODO(paso-3)" in cp.branch_md(2) and "TODO(paso-4)" in cp.branch_md(3)
    assert "medir" in cp.branch_md(4)
    assert "No queda ningún" in cp.branch_md(4) and "No queda ningún" in cp.branch_md(5)


def test_gancho_de_pruebas_salta_solo_lo_que_falta():
    class Item:
        def __init__(self, nodeid): self.nodeid, self.marcas = nodeid, []
        def add_marker(self, m): self.marcas.append(m)

    class FalsoPytest:
        class mark:
            @staticmethod
            def skip(reason): return reason

    ns = {"pytest": FalsoPytest}
    exec(cp.gancho_conftest(2), ns)
    pedido3 = next(n for n, v in cp.REQUIERE.items() if v == 3)
    pedido2 = next(n for n, v in cp.REQUIERE.items() if v == 2)
    items = [Item(pedido3), Item(pedido2), Item("tests/test_gate.py::test_cualquiera"), Item(pedido3 + "[param]")]
    ns["pytest_collection_modifyitems"](None, items)
    assert [bool(i.marcas) for i in items] == [True, False, False, True]
    assert "requiere el paso 3" in items[0].marcas[0] and "paso-2" in items[0].marcas[0]


def test_gancho_vacio_no_salta_nada_en_paso_4():
    ns = {"pytest": object}
    exec(cp.gancho_conftest(4), ns)
    assert ns["REQUIERE_PASO"] == {}


def test_requiere_apunta_a_pruebas_que_existen():
    for clave, paso in cp.REQUIERE.items():
        archivo, _, prueba = clave.partition("::")
        assert re.search(rf"^(async )?def {re.escape(prueba)}\(", (ROOT / archivo).read_text(encoding="utf-8"), re.M), clave
        assert paso in cp.PASOS


@pytest.mark.skipif(EN_BRANCH, reason="en un branch paso-* los bloques ya están cortados; esta prueba es de main")
def test_main_tiene_los_cuatro_marcadores_una_sola_vez():
    encontrados: dict[int, list[str]] = {}
    for ruta in sorted(ROOT.glob("**/*.py")):
        rel = ruta.relative_to(ROOT).as_posix()
        if rel in cp.PROPIOS or rel.startswith((".venv/", "deck/", "node_modules/")):
            continue
        for b in cp.buscar_bloques(ruta.read_text(encoding="utf-8")):
            encontrados.setdefault(b.n, []).append(rel)
    assert {n: len(v) for n, v in encontrados.items()} == {1: 1, 2: 1, 3: 1, 4: 1}, encontrados
    for n, r in cp.REEMPLAZOS.items():
        if r.requiere_despues:
            assert r.requiere_despues in (ROOT / encontrados[n][0]).read_text(encoding="utf-8")


@pytest.mark.skipif(EN_BRANCH, reason="en un branch paso-* los bloques ya están cortados; esta prueba es de main")
def test_cortar_todo_el_codigo_real_sigue_compilando():
    for ruta in ("taller/agent.py", "taller/tools.py"):
        original = (ROOT / ruta).read_text(encoding="utf-8")
        compile(cp.cortar_bloques(original, cp.PASOS), ruta, "exec")
