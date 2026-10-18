# taller/vendor — plantillas de chat (solo JSON pequeño, sin pesos ni tokenizer.json)

Cada archivo conserva únicamente `bos_token`, `eos_token` y `chat_template` del `tokenizer_config.json` original.
El sandbox donde se construyó esto no llega a huggingface.co (`curl` -> 403 del proxy), así que **no se pudo
descargar con curl ni comparar byte a byte**. Verifica en una máquina con red (ver al final).

## qwen3-8b.tokenizer_config.json
- Fuente: https://huggingface.co/Qwen/Qwen3-8B/raw/main/tokenizer_config.json (campo `chat_template`)
- Obtención: WebFetch (2026-10-18) pidiendo el valor literal; el texto recibido es la plantilla completa y coincide
  con el formato conocido de Qwen3 (`<tool_call>` con JSON). No es una descarga directa: **tratar como "casi verbatim, sin
  verificar byte a byte"**. `eos_token` (`<|im_end|>`) escrito a mano; `bos_token` es `null` en Qwen3.
- Revisión: no registrada. FACTS.md anota el último commit visible `895c8d1` ("update tokenizer_config.json"); no se confirmó que sea la revisión leída.
- Licencia: Apache-2.0 (repo Qwen/Qwen3-8B).

## deepseek-v3.tokenizer_config.json  — RECONSTRUIDA
- Fuente: https://huggingface.co/deepseek-ai/DeepSeek-V3/raw/main/tokenizer_config.json
- WebFetch se negó a devolver el campo completo (límite de cita), así que la plantilla se **reconstruyó de memoria** de
  la plantilla pública de DeepSeek-V3 y se contrastó con fragmentos que WebFetch sí citó (apertura del archivo,
  `<｜tool▁calls▁end｜>` dentro de la rama `else` del bucle de llamadas, inicio del bloque `role == 'tool'`).
- Consecuencia visible: con **una sola** llamada esta versión de la plantilla no emite `<｜tool▁calls▁end｜><｜end▁of▁sentence｜>`
  (solo lo hace a partir de la segunda llamada). Es como lo muestran los fragmentos; si el archivo real difiere, la demo cambia sólo ahí.
- La plantilla V3 **no recibe `tools`**: la definición de la herramienta se pega en el prompt de sistema (lo hace `plantilla.py`).
- Los caracteres `｜` y `▁` son Unicode de ancho completo.
- Licencia: el repo declara licencia propia de DeepSeek (código MIT; pesos bajo "DeepSeek Model License"). Solo se usa texto de plantilla.

## Para verificar (con red)
    curl -sL https://huggingface.co/<repo>/raw/main/tokenizer_config.json | python -c "import json,sys;print(json.load(sys.stdin)['chat_template'])"
y comparar con `chat_template` de los JSON de esta carpeta; anotar el hash del commit aquí.
