"""Precios por MTok (USD) de los modelos que comparamos.

Fuente: https://platform.claude.com/docs/en/about-claude/pricing (consultados el 2026-10-18)
Verificado 2026-10-18. La página no trae fecha de vigencia: revisa claude.com/pricing antes de citar cifras.
Solo precio estándar sin caché ni Batch; medir.py no usa ninguno de los dos.
"""
from __future__ import annotations

FECHA_PRECIOS = "2026-10-18"

# modelo -> (entrada, salida) por MTok; Haiku 5.5 sube de precio si el prompt pasa de 100K tokens.
PRECIOS: dict[str, tuple[float, float]] = {
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-opus-5-5": (4.00, 20.00),
}
HAIKU_LARGO = ("claude-haiku-5-5", 100_000, (0.50, 2.50))
_avisados: set[str] = set()


def costo_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Costo en USD de una llamada. Modelo desconocido -> None (nunca se adivina un precio)."""
    if model not in PRECIOS:
        if model not in _avisados:
            _avisados.add(model)
            print(f"precio desconocido para {model!r}: no se calcula costo")
        return None
    p_in, p_out = PRECIOS[model]
    if model == HAIKU_LARGO[0] and input_tokens > HAIKU_LARGO[1]:
        p_in, p_out = HAIKU_LARGO[2]
    return (input_tokens * p_in + output_tokens * p_out) / 1_000_000
