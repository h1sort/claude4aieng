"""Fixtures compartidas: una copia fresca de la base sintética en un directorio temporal."""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def seed_module():
    spec = importlib.util.spec_from_file_location("seed", ROOT / "scripts" / "seed.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def seeded_db(tmp_path: Path, seed_module) -> Path:
    """Base sintética regenerada en un tmp (no toca data/banco.sqlite)."""
    import random
    path = tmp_path / "banco.sqlite"
    con = sqlite3.connect(path)
    seed_module.build(con, random.Random(seed_module.SEED))
    con.close()
    return path


@pytest.fixture(scope="session")
def modulo_cortado():
    """modulo_cortado("taller/agent.py", {3}) -> el módulo con esos pasos sin escribir (# TODO), como en un branch paso-*."""
    spec = importlib.util.spec_from_file_location("cortar_pasos_fixture", ROOT / "scripts" / "cortar_pasos.py")
    cp = importlib.util.module_from_spec(spec)
    sys.modules["cortar_pasos_fixture"] = cp  # dataclasses lo busca ahí
    spec.loader.exec_module(cp)

    def cargar(ruta: str, pasos: set[int]) -> types.ModuleType:
        fuente = cp.cortar_bloques((ROOT / ruta).read_text(encoding="utf-8"), pasos)
        mod = types.ModuleType("cortado_" + Path(ruta).stem)
        exec(compile(fuente, ruta, "exec"), mod.__dict__)
        return mod

    return cargar


# --- generado por scripts/cortar_pasos.py (solo en los branches paso-*) ---
PASO_ACTUAL = 3  # estás en paso-3: tienes escritos los pasos 1..3
REQUIERE_PASO = {
    'tests/test_romper.py::test_detectar_compuerta_es_en_ejecucion': 4,
    'tests/test_romper.py::test_drop': 4,
}


def pytest_collection_modifyitems(config, items):
    """Salta (con motivo) las pruebas de los pasos que todavía no escribes."""
    for item in items:
        archivo, _, prueba = item.nodeid.partition("::")
        paso = REQUIERE_PASO.get(f"{archivo}::{prueba.split('[')[0]}", REQUIERE_PASO.get(archivo, 0))
        if paso > PASO_ACTUAL:
            item.add_marker(pytest.mark.skip(
                reason=f"requiere el paso {paso}: aún no lo escribes (estás en paso-{PASO_ACTUAL})"))
