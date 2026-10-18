"""Fixtures compartidas: una copia fresca de la base sintética en un directorio temporal."""
from __future__ import annotations

import importlib.util
import sqlite3
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
