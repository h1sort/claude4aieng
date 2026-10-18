#!/usr/bin/env python3
"""Verifica que tu máquina está lista para el taller.

    uv run scripts/check.py

Revisa: Python >= 3.11, dependencias, data/banco.sqlite, ANTHROPIC_API_KEY y una
llamada mínima (max_tokens=1) para confirmar que la llave funciona y tiene créditos.
Nunca imprime la llave. Sale con código 1 si algo falla.

Nota: este script no lleva metadatos PEP 723 a propósito; usa el entorno del proyecto
(`uv sync`), así funciona sin red después del primer sync.
"""
from __future__ import annotations

import os
import sqlite3
import sys

OK, FAIL = "\033[32m✓\033[0m", "\033[31m✗\033[0m"
TABLAS = {"clientes", "cuentas", "transacciones", "tarjetas", "secretos"}
fallas: list[str] = []


def ok(msg: str) -> None:
    print(f"{OK} {msg}")


def fail(msg: str, arreglo: str) -> None:
    print(f"{FAIL} {msg}\n    → {arreglo}")
    fallas.append(msg)


def check_python() -> None:
    v = sys.version_info
    if v >= (3, 11):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        fail(f"Python {v.major}.{v.minor} es muy viejo (se necesita 3.11 o superior)",
             "Corre `uv sync`: uv descarga un Python adecuado, o `uv python install 3.12`.")


def check_deps() -> bool:
    try:
        import anthropic  # noqa: F401
        import jinja2  # noqa: F401
        from taller.contracts import MODEL_ID  # noqa: F401
    except ImportError as e:
        fail(f"Falta una dependencia o el paquete del taller ({e.name})",
             "Corre `uv sync` en la raíz del repo y vuelve a ejecutar con `uv run scripts/check.py`.")
        return False
    ok(f"Dependencias instaladas (anthropic {anthropic.__version__})")
    return True


def check_db() -> None:
    from taller.contracts import DB_PATH
    if not DB_PATH.exists():
        fail(f"No existe {DB_PATH}", "Genera la base con `uv run scripts/seed.py`.")
        return
    try:
        con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        tablas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        con.close()
    except sqlite3.Error as e:
        fail(f"No se pudo abrir {DB_PATH}: {e}", "Regenera la base con `uv run scripts/seed.py`.")
        return
    faltan = TABLAS - tablas
    if faltan:
        fail(f"A la base le faltan tablas: {', '.join(sorted(faltan))}",
             "Regenera la base con `uv run scripts/seed.py`.")
    else:
        ok(f"data/banco.sqlite con las {len(TABLAS)} tablas")


def check_api() -> None:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        fail("ANTHROPIC_API_KEY no está definida (llamada a la API omitida)",
             "Crea una llave en https://console.anthropic.com/settings/keys y corre "
             "`export ANTHROPIC_API_KEY=...` en esta terminal.")
        return
    ok("ANTHROPIC_API_KEY presente")

    import anthropic
    from taller.contracts import get_model_id

    model = get_model_id()
    try:
        client = anthropic.Anthropic(max_retries=1, timeout=30.0)
        resp = client.messages.create(model=model, max_tokens=1,
                                      messages=[{"role": "user", "content": "hola"}])
    except anthropic.AuthenticationError:
        fail("La API rechazó la llave (401)",
             "Revisa que la copiaste completa, sin espacios ni comillas, y que no fue revocada.")
    except anthropic.PermissionDeniedError:
        fail(f"Tu llave no tiene permiso para usar {model} (403)",
             "Revisa el workspace de la llave en la consola, o prueba otro modelo con `MODEL_ID=...`.")
    except anthropic.RateLimitError:
        fail("Límite de uso alcanzado (429)",
             "Espera un minuto y repite; si persiste, revisa los límites de tu organización en la consola.")
    except anthropic.NotFoundError:
        fail(f"El modelo '{model}' no existe o no está disponible para tu cuenta (404)",
             "Define un modelo válido con `export MODEL_ID=...`.")
    except anthropic.BadRequestError as e:
        texto = str(e).lower()
        if "credit" in texto or "balance" in texto or "billing" in texto:
            fail("Tu cuenta no tiene créditos (400: saldo insuficiente)",
                 "Agrega créditos en https://console.anthropic.com/settings/billing y repite.")
        else:
            fail(f"La API respondió 400: {str(e)[:200]}",
                 "Revisa MODEL_ID; si el mensaje no ayuda, avisa a los organizadores.")
    except anthropic.APIConnectionError:
        fail("No se pudo conectar con la API",
             "Revisa tu conexión a internet o tu proxy/VPN y repite.")
    except anthropic.APIStatusError as e:
        fail(f"La API respondió con error {e.status_code}: {str(e)[:200]}",
             "Repite en un minuto; si persiste, avisa a los organizadores.")
    else:
        ok(f"Llamada mínima a {model} correcta ({resp.usage.input_tokens} tokens de entrada): la llave funciona y hay créditos")


def main() -> int:
    print("Revisando el entorno del taller...\n")
    check_python()
    if check_deps():
        check_db()
        check_api()
    print()
    if fallas:
        print(f"{FAIL} {len(fallas)} problema(s). Arréglalos y vuelve a correr `uv run scripts/check.py`.")
        return 1
    print(f"{OK} Todo listo. Nos vemos el lunes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
