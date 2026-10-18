"""La compuerta rechaza todo lo que no sea lectura de las tablas permitidas, y deja pasar lo demás."""
from __future__ import annotations

import pytest

from taller.gate import ALLOWED_TABLES, validate

VALIDAS = [
    "SELECT * FROM clientes LIMIT 5",
    "select count(*) from transacciones",
    "SeLeCt nombre FrOm ClIeNtEs",
    "SELECT 1;",
    "SELECT 1 -- comentario al final",
    "/* comentario */ SELECT id FROM clientes",
    "SELECT c.id, count(*) FROM clientes c JOIN cuentas a ON a.cliente_id = c.id GROUP BY c.id",
    "SELECT * FROM tarjetas WHERE cliente_id IN (SELECT id FROM clientes)",
    "WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM n WHERE x < 10) SELECT sum(x) FROM n",
    "WITH t AS (SELECT * FROM cuentas) SELECT count(*) FROM t",
    "SELECT upper(nombre), length(nombre) FROM clientes",
]

RECHAZADAS = {
    "drop": "DROP TABLE clientes",
    "drop_minusculas": "drop table clientes",
    "delete": "DELETE FROM clientes",
    "update": "UPDATE cuentas SET saldo = 0",
    "insert": "INSERT INTO clientes (id) VALUES (999999)",
    "create": "CREATE TABLE x (a)",
    "alter": "ALTER TABLE clientes ADD COLUMN x",
    "attach": "ATTACH DATABASE ':memory:' AS otra",
    "pragma": "PRAGMA table_info(clientes)",
    "pragma_funcion": "SELECT * FROM pragma_table_info('clientes')",
    "sqlite_master": "SELECT * FROM sqlite_master",
    "dos_sentencias": "SELECT 1; DROP TABLE clientes",
    "dos_selects": "SELECT 1; SELECT 2",
    "secretos_directo": "SELECT * FROM secretos",
    "secretos_join": "SELECT c.id, s.valor FROM clientes c JOIN secretos s ON 1 = 1",
    "secretos_subconsulta": "SELECT (SELECT valor FROM secretos LIMIT 1) FROM clientes",
    "secretos_cte": "WITH s AS (SELECT * FROM secretos) SELECT * FROM s",
    "secretos_mayusculas": "SELECT * FROM SECRETOS",
    "load_extension": "SELECT load_extension('/tmp/evil.so')",
    "drop_en_comentario": "/*DROP*/ DROP/**/TABLE clientes",
    "drop_tras_select": "SELECT 1 /* x */; /* y */ DROP TABLE clientes",
    "cte_que_escribe": "WITH x AS (SELECT 1) DELETE FROM clientes",
    "insert_select": "INSERT INTO clientes SELECT * FROM clientes",
    "transaccion": "BEGIN",
    "vacuum": "VACUUM",
    "vacuum_into": "VACUUM INTO '/tmp/copia.db'",
    "reindex": "REINDEX",
    "explain_envuelto": "EXPLAIN DROP TABLE clientes",
}


@pytest.mark.parametrize("sql", VALIDAS)
def test_permite_lecturas(sql):
    assert validate(sql) is None


@pytest.mark.parametrize("sql", RECHAZADAS.values(), ids=RECHAZADAS.keys())
def test_rechaza(sql):
    motivo = validate(sql)
    assert motivo, f"debió rechazar: {sql}"
    assert motivo.startswith("rechazada"), motivo


@pytest.mark.parametrize("sql", ["", "   ", "\n;\n", None])
def test_vacia(sql):
    assert "vacía" in (validate(sql) or "")


def test_motivos_son_instructivos():
    """Cada motivo dice qué falló y qué intentar (a qué tablas ceñirse / cómo reescribir)."""
    assert "SELECT" in validate("DROP TABLE clientes")
    assert all(t in validate("DROP TABLE clientes") for t in ALLOWED_TABLES)
    assert "una sola sentencia" in validate("SELECT 1; SELECT 2")
    sintaxis = validate("SELEC * FORM clientes")
    assert "sintaxis" in sintaxis and "syntax error" in sintaxis
    assert "no such table" in validate("SELECT * FROM inexistente")


def test_secretos_no_esta_permitida():
    assert "secretos" not in ALLOWED_TABLES


def test_esquema_sin_datos():
    """La copia del esquema es vacía: solo CREATE, jamás INSERT."""
    from taller.gate import _schema_ddl
    ddl = _schema_ddl().upper()
    assert "CREATE TABLE" in ddl and "INSERT" not in ddl


def test_threads():
    """Una conexión por llamada: seguro con asyncio.to_thread."""
    from concurrent.futures import ThreadPoolExecutor
    consultas = ["SELECT 1 FROM clientes", "DROP TABLE clientes", "SELECT * FROM secretos", "SELECT 2"] * 20
    with ThreadPoolExecutor(8) as pool:
        res = list(pool.map(validate, consultas))
    assert [r is None for r in res] == [True, False, False, True] * 20
