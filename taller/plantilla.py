"""Minuto 2: lo que el modelo realmente recibe cuando le mandas herramientas. Sin red, sin pesos."""
import argparse
import json
import os
import re
import sys
from pathlib import Path

from jinja2 import TemplateError
from jinja2.sandbox import ImmutableSandboxedEnvironment

VENDOR = Path(__file__).parent / "vendor"
TOOL = {"type": "function", "function": {
    "name": "sql_query",
    "description": "Ejecuta un SELECT de solo lectura sobre la base del banco (clientes, cuentas, transacciones, tarjetas).",
    "parameters": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}}}
SQL = {"sql": "SELECT COUNT(*) FROM tarjetas WHERE estado = 'bloqueada'"}
SYS, PREGUNTA, RESULTADO, FINAL = ("Eres un asistente del banco.", "¿cuántas tarjetas bloqueadas hay?",
                                   '[{"COUNT(*)": 26}]', "Hay 26 tarjetas bloqueadas.")

FAMILIAS = {  # archivo vendor, tokens especiales a resaltar, región de la llamada, parser que necesitaría
    "qwen": ("qwen3-8b", r"<\|im_(?:start|end)\|>|</?(?:tool_call|tool_response|tools|think)>",
             r'<tool_call>\n\{"name": ".*?</tool_call>', r"<tool_call>\s*(\{.*?\})\s*</tool_call>"),
    "deepseek": ("deepseek-v3", r"<｜[^｜>]+｜>", r"<｜tool▁calls▁begin｜>.*?<｜tool▁call▁end｜>(?:<｜tool▁calls▁end｜>)?",
                 r"<｜tool▁call▁begin｜>(\w+)<｜tool▁sep｜>(\w+)\n```json\n(.*?)\n```<｜tool▁call▁end｜>"),
}


def mensajes(familia):
    """Mismo intercambio; cada familia espera `arguments` distinto (dict en Qwen, cadena JSON en DeepSeek)."""
    args = SQL if familia == "qwen" else json.dumps(SQL)
    sistema = SYS if familia == "qwen" else f"{SYS}\n\nHerramientas disponibles:\n{json.dumps(TOOL['function'], ensure_ascii=False)}"
    return [{"role": "system", "content": sistema}, {"role": "user", "content": PREGUNTA},
            {"role": "assistant", "content": "" if familia == "qwen" else None,
             "tool_calls": [{"type": "function", "function": {"name": "sql_query", "arguments": args}}]},
            {"role": "tool", "content": RESULTADO}, {"role": "assistant", "content": FINAL}]


def renderizar(familia="qwen"):
    """Como `apply_chat_template` de HF: entorno sandbox, trim_blocks, lstrip_blocks, raise_exception, tojson."""
    archivo, *_ = FAMILIAS[familia]
    cfg = json.loads((VENDOR / f"{archivo}.tokenizer_config.json").read_text(encoding="utf-8"))
    env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)

    def raise_exception(msg):
        raise TemplateError(msg)
    env.globals["raise_exception"] = raise_exception
    env.filters["tojson"] = lambda x, **kw: json.dumps(x, ensure_ascii=False)  # el tojson de jinja escapa < > &
    return env.from_string(cfg["chat_template"]).render(
        messages=mensajes(familia), tools=[TOOL], bos_token=cfg["bos_token"] or "", eos_token=cfg["eos_token"])


def resaltar(texto, familia, color=True):
    _, especiales, region, _ = FAMILIAS[familia]
    c = (lambda s, n: f"\033[{n}m{s}\033[0m") if color else (lambda s, n: s)
    pintar = lambda t: re.sub(especiales, lambda m: c(m.group(), "1;36"), t)
    salida = ""
    for i, trozo in enumerate(re.split(f"({region})", texto, flags=re.S)):
        if i % 2 == 0:
            salida += pintar(trozo)
            continue
        caja = "\n".join(c("│ ", 33) + l for l in pintar(trozo).split("\n"))
        salida += "\n" * (not salida.endswith("\n")) + c("┌─ la llamada a la herramienta (lo que el modelo EMITE)\n", 33) + caja + c("\n└─\n", 33)
    return salida


def comparar(textos):
    print("\n== ¿Qué parser necesita cada familia? ==")
    for fam, (_, _, _, parser) in FAMILIAS.items():
        print(f"  {fam:9s} re.findall(r'{parser}', texto) + json.loads de los argumentos")
    for fam, (_, _, _, parser) in FAMILIAS.items():
        for otra, texto in textos.items():
            n = len(re.findall(parser, re.search(FAMILIAS[otra][2], texto, re.S).group(), flags=re.S))
            print(f"  parser de {fam:8s} sobre la llamada de {otra:8s}: {n} llamada(s) encontradas")
    print("Un parser escrito para una familia NO parsea la otra: otros marcadores, otra sintaxis, otra forma de los argumentos.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--familia", choices=FAMILIAS, default="qwen")
    ap.add_argument("--comparar", action="store_true", help="muestra las dos familias y sus parsers")
    a = ap.parse_args()
    color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    textos = {f: renderizar(f) for f in (FAMILIAS if a.comparar else [a.familia])}
    for fam, texto in textos.items():
        print(f"\n== {fam}: texto crudo que recibe el modelo ==\n{resaltar(texto, fam, color)}")
    if a.comparar:
        comparar(textos)
    print("\nNota: la API de Claude te devuelve `tool_use` como bloques de contenido estructurados, pero por debajo\n"
          "el modelo sigue emitiendo tokens en un formato entrenado; la API los parsea por ti.")


if __name__ == "__main__":
    main()
