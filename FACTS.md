# FACTS — Taller "Tool use sin abstracciones"

Tarea W0-B. Todos los hechos verificados el 2026-10-18. Formato: `- [hecho] — fuente (URL) — verificado AAAA-MM-DD`.
Lo marcado `NO VERIFICADO` no entra al deck.

Nota de método: las páginas se leyeron con WebFetch (que resume la página con un modelo pequeño) porque `curl` desde el sandbox
no llega a platform.claude.com, huggingface.co ni cmu-agents.com (proxy 403). Los nombres de parámetros y las cifras
se contrastaron entre al menos dos páginas cuando fue posible. Citas textuales de menos de 15 palabras; el resto está parafraseado.
Antes de proyectar una cifra o un mensaje de error en vivo, vale la pena abrir la fuente una vez más.

URLs base (docs oficiales):
- TU = https://platform.claude.com/docs/en/agents-and-tools/tool-use

---

## 1. Llamadas paralelas y `tool_choice`

- El parámetro que desactiva las llamadas paralelas se llama exactamente `disable_parallel_tool_use` — fuente (TU/parallel-tool-use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use) — verificado 2026-10-18
- Va **dentro** del objeto `tool_choice`; la página aclara que no es un parámetro de nivel superior de la petición. Forma: `tool_choice={"type": "auto", "disable_parallel_tool_use": True}` — misma fuente — verificado 2026-10-18
- Con `tool_choice` `auto` (el valor por defecto), `disable_parallel_tool_use: true` hace que Claude llame como máximo a una herramienta por respuesta (puede responder solo con texto) — misma fuente — verificado 2026-10-18
- Con `any` o `tool`, el mismo campo hace que Claude llame exactamente a una herramienta — misma fuente — verificado 2026-10-18
- En Claude Opus 5.5, Sonnet 5.5, Fable 5.1 y Mythos 5.1, `tool_choice` `any` y `tool` devuelven 400; la página recomienda `auto` con strict tool use (o structured outputs) — fuente (https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools) — verificado 2026-10-18
- Por tanto, en esos modelos la única forma documentada de usar el flag es `auto` + `disable_parallel_tool_use: true`. La página de paralelas no lista modelos uno por uno: su ejemplo de `auto` usa `claude-opus-5-5` y no menciona a Sonnet 5.5 explícitamente. Que funcione en Sonnet 5.5 es una inferencia razonable, no un enunciado de la documentación — misma fuente — verificado 2026-10-18 (inferencia marcada)
- Inconsistencia en la documentación: el ejemplo de `any` con el flag usa `model="claude-opus-5"` (no `claude-opus-5-5`); en el taller usar siempre `claude-sonnet-5-5` — fuente (parallel-tool-use y define-tools) — verificado 2026-10-18
- `disable_parallel_tool_use` **no** aparece en la página define-tools; ahí solo se explican `auto`/`any`/`tool`/`none` — fuente (define-tools) — verificado 2026-10-18
- Por defecto los modelos Claude 4 y posteriores hacen llamadas paralelas cuando la petición se beneficia; todas las respuestas del turno deben ir juntas en **un** mensaje de usuario (mensajes separados reducen el uso paralelo) — fuente (parallel-tool-use) — verificado 2026-10-18
- La API no impone orden de ejecución ni orden entre los `tool_result` de un turno paralelo: se emparejan por `tool_use_id`. La regla de orden es solo que todos los `tool_result` van antes de cualquier texto — fuente (parallel-tool-use) — verificado 2026-10-18
- Para fomentar paralelismo, la página sugiere un bloque de system prompt `<use_parallel_tool_calls>`; para Fable 5.1 advierte que puede hacer menos llamadas paralelas en bucles largos — fuente (parallel-tool-use) — verificado 2026-10-18
- Sobrecosto de tokens por usar herramientas: el system prompt automático añade 286 tokens con `auto`/`none` y 406 con `any`/`tool` en Opus 5.5, Sonnet 5.5 y Haiku 5.5 — fuente (https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) — verificado 2026-10-18

## 2. `stop_reason: "max_tokens"` con un `tool_use` incompleto

- Valores de `stop_reason` documentados: `end_turn`, `max_tokens`, `stop_sequence`, `tool_use`, `pause_turn`, `refusal`, `model_context_window_exceeded` — fuente (https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons) — verificado 2026-10-18
- Manejo recomendado: si `stop_reason == "max_tokens"` y el último bloque de `content` es de tipo `tool_use`, la respuesta está truncada; reintentar la misma petición con un `max_tokens` mayor (el ejemplo usa 4096; la doc no fija un valor) — misma fuente — verificado 2026-10-18
- La doc no dice explícitamente "no ejecutes la llamada truncada", pero el reintento sustituye a la respuesta cortada. La regla del taller (no parsear ni ejecutar un `tool_use` cortado) es consistente con la doc y es decisión de diseño nuestra — misma fuente (inferencia marcada) — verificado 2026-10-18
- Las páginas handle-tool-calls y parallel-tool-use no tratan la truncación; solo enlazan a la página de stop reasons — fuente (https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — verificado 2026-10-18
- Con salidas estructuradas, si `stop_reason` es `max_tokens` la salida puede quedar incompleta y no cumplir el esquema; la doc indica reintentar con más `max_tokens`. O sea: strict no protege contra la truncación — fuente (https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — verificado 2026-10-18

## 3. Strict tool use

- Se activa con `"strict": true` como propiedad de primer nivel de la definición de la herramienta, junto a `name`, `description` e `input_schema` — fuente (https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use) — verificado 2026-10-18
- Garantiza: el `input` de la herramienta sigue el `input_schema`, el `name` es siempre válido (de las herramientas dadas) y los argumentos llegan con el tipo correcto — misma fuente — verificado 2026-10-18
- No garantiza significado: valida forma, no si la llamada es sensata, autorizada o correcta. (La clase de CMU lo dice así en la diapositiva 28: la restricción asegura forma, no verdad, permisos, elección de herramienta ni éxito de la tarea.) — fuente (https://www.cmu-agents.com/slides/lecture-02-tool-use.pdf) — verificado 2026-10-18
- Estado GA/beta: la página de strict tool use no dice "beta" ni "GA" ni menciona header. La página de structured outputs dice que los headers beta ya no se requieren para la forma actual (`output_config.format`); el header `structured-outputs-2025-11-13` solo aplica al parámetro antiguo `output_format`, ya obsoleto. Conclusión práctica: no hay header beta para `strict: true`; la doc no usa la palabra "GA" — fuente (strict-tool-use y structured-outputs) — verificado 2026-10-18
- Modelos: la lista de compatibilidad está en la página de structured outputs (Fable 5/5.1, Mythos 5/5.1, Opus 4.5–5.5, Sonnet 4.5–5.5, Haiku 4.5 y 5.5), no específica de strict tool use. Incluye Sonnet 5.5, Opus 5.5 y Haiku 5.5 — fuente (https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — verificado 2026-10-18
- Límites del esquema (subconjunto de JSON Schema): `additionalProperties` debe ser `false` en objetos; sin esquemas recursivos; sin `minimum`/`maximum`/`multipleOf`; sin `minLength`/`maxLength`; `minItems` solo 0 o 1. Complejidad: hasta 20 herramientas strict, 24 parámetros opcionales y 16 de tipo unión por petición; si se excede, error "Schema is too complex for compilation" — misma fuente — verificado 2026-10-18
- Los toolsets de computer use y browser use no aceptan `strict: true` (la petición se rechaza) — fuente (strict-tool-use) — verificado 2026-10-18
- Retención: los esquemas de herramientas se cachean temporalmente hasta 24 horas desde el último uso — fuente (strict-tool-use) — verificado 2026-10-18
- La página de handle-tool-calls recomienda `strict: true` como prevención de parámetros inválidos — fuente (https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — verificado 2026-10-18

## 4. Tool Runner (SDK de Python)

- Llamada exacta: `client.beta.messages.tool_runner(...)`, que devuelve un runner iterable — fuente (https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner) — verificado 2026-10-18
- Decorador: `@beta_tool`, importado con `from anthropic import Anthropic, beta_tool`; deriva el esquema JSON de las anotaciones de tipo y del docstring (sección `Args:`) — misma fuente — verificado 2026-10-18
- La página dice que el tool runner está en beta — misma fuente — verificado 2026-10-18
- Forma mínima: `runner = client.beta.messages.tool_runner(model=..., max_tokens=1024, tools=[mi_funcion], messages=[...])` y luego `for message in runner: ...`; cada iteración entrega una respuesta de Claude y el runner ejecuta las herramientas y devuelve resultados solo — misma fuente — verificado 2026-10-18
- Solo el mensaje final: `final_message = runner.until_done()`; límite de iteraciones: `max_iterations=N`; streaming: `stream=True` — misma fuente — verificado 2026-10-18
- Variante asíncrona: `@beta_async_tool` con funciones `async def`; la página no muestra un ejemplo completo del runner asíncrono — misma fuente — verificado 2026-10-18
- Ejemplo de la doc (para la diapositiva "lo que NO usamos hoy"):
  ```python
  @beta_tool
  def calculate_sum(a: int, b: int) -> str:
      """Add two numbers together. Args: a: First number; b: Second number"""
      return str(a + b)
  runner = client.beta.messages.tool_runner(
      model="claude-opus-5-5", max_tokens=1024,
      tools=[calculate_sum],
      messages=[{"role": "user", "content": "What is 15 + 27?"}])
  for message in runner: print(message)
  ```
  — misma fuente (abreviado) — verificado 2026-10-18

## 5. Orden de `tool_result` y error 400 por `tool_use` huérfano

- Los bloques `tool_result` deben seguir de inmediato a los `tool_use` correspondientes; no puede haber mensajes entre el mensaje del asistente con `tool_use` y el mensaje de usuario con `tool_result` — fuente (https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — verificado 2026-10-18
- Dentro del mensaje de usuario, los `tool_result` van **primero** en el arreglo `content`; cualquier texto va después de todos los resultados. Poner texto antes causa 400 — misma fuente — verificado 2026-10-18
- Texto del error que cita la documentación: "tool_use ids were found without tool_result blocks immediately after" (la doc solo da este fragmento) — misma fuente — verificado 2026-10-18
- Texto completo del error real (fuente secundaria, reporte de usuarios de Claude Code; no es la doc oficial): tipo `invalid_request_error`, mensaje `` `tool_use` ids were found without `tool_result` blocks immediately after: toolu_… `` seguido de `` Each `tool_use` block must have a corresponding `tool_result` block in the next message. `` y con prefijo `messages.N:` indicando el índice — fuente secundaria (https://claudeissues.com/issue/3086-missing-tool-result-block-for-tool-use-id) — verificado 2026-10-18. Para la diapositiva usar el fragmento oficial; para la demo, el texto real lo imprime `romper.py huerfano` desde la API en vivo
- `is_error: true` en el `tool_result` cuando la herramienta falla; el contenido debe decir qué falló y qué intentar (ejemplo de la doc: reintentar tras 60 segundos). Con parámetros inválidos o faltantes, Claude reintenta 2–3 veces con correcciones antes de disculparse — misma fuente — verificado 2026-10-18
- Si el turno incluye una herramienta de servidor pendiente, el mensaje de usuario debe contener solo bloques `tool_result` — misma fuente — verificado 2026-10-18

## 6. Nombres de herramientas y definición

- `name` debe cumplir `^[a-zA-Z0-9_-]{1,128}$` — fuente (https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools) — verificado 2026-10-18
- `tool_choice` admite `auto` (por defecto con `tools`), `any`, `tool` y `none` (por defecto sin `tools`). Con `any`/`tool` la API prellena el mensaje del asistente, así que no hay texto antes del `tool_use`; cambiar `tool_choice` invalida bloques de mensajes en caché — misma fuente — verificado 2026-10-18
- Con thinking manual (`thinking: {type: "enabled"}`), `any` y `tool` tampoco se admiten — misma fuente — verificado 2026-10-18

## 7. Precios por MTok (página oficial de pricing)

- claude-sonnet-5-5: entrada $2, salida $10 por MTok — fuente (https://platform.claude.com/docs/en/about-claude/pricing) — verificado 2026-10-18
- claude-haiku-5-5: entrada $0.10, salida $0.50 por MTok para prompts de hasta 100K tokens; $0.50 / $2.50 si el prompt pasa de 100K — misma fuente — verificado 2026-10-18
- claude-opus-5-5: entrada $4, salida $20 por MTok — misma fuente — verificado 2026-10-18
- Para contexto: Fable 5.1 cuesta $10 / $50 por MTok (`claude-fable-5-1`) — fuente (https://platform.claude.com/docs/en/about-claude/models/overview) — verificado 2026-10-18
- Cuerdas de modelo de la API confirmadas: `claude-sonnet-5-5`, `claude-haiku-5-5`, `claude-opus-5-5`; las tres con ventana de 1M tokens y salida máxima de 128K — misma fuente — verificado 2026-10-18
- Batch API: 50 % menos (Sonnet 5.5: $1 / $5; Opus 5.5: $2 / $10; Haiku 5.5 ≤100K: $0.05 / $0.25). Caché: lectura de caché $0.10 (Sonnet 5.5), $0.20 (Opus 5.5), $0.01 (Haiku 5.5) por MTok; escritura de 5 min $2.50 / $5 / $0.125 — fuente (pricing) — verificado 2026-10-18
- La página de pricing no muestra fecha de vigencia y remite a claude.com/pricing para lo más actual. `medir.py` debe tomar los precios de este archivo y declarar la fecha 2026-10-18 — misma fuente — verificado 2026-10-18
- Mythos 5.1 no aparece en la tabla de la página de modelos; no se compara en el taller — misma fuente — verificado 2026-10-18

## 8. OpenRouter: tasa de error de tool calls por proveedor

- **NO VERIFICADO**: la cifra "~15 % vs ~0.01–0.05 % para GLM 5.3" de la clase de CMU. Lo intentado: texto de la diapositiva 57 del PDF de la clase (solo trae título "Provider tool-call error rates" y la fuente "OpenRouter provider analytics · Aug. 27, 2026"; las cifras están en una imagen que no se extrae como texto); páginas openrouter.ai/z-ai/glm-5.3 y /performance (renderizan sin datos de error por proveedor en lo que alcanza WebFetch); docs de Auto Exacto; publicación de Exacto; leaderboard τ²-Bench. Ninguna publica por proveedor un valor de 15 % ni de 0.01–0.05 % para ese modelo. No poner esa cifra en una diapositiva sin ver la imagen de la diapositiva 57 o la pestaña Performance en vivo — fuente (https://www.cmu-agents.com/slides/lecture-02-tool-use.pdf) — intentado 2026-10-18
- Dónde vive el dato: OpenRouter muestra "Tool Call Error Rate" por endpoint y por día en la pestaña Performance de cada página de modelo — fuente (https://openrouter.ai/docs/guides/routing/auto-exacto) — verificado 2026-10-18
- Definición de la métrica: por petición, no por llamada. Es `requests_with_tool_call_errors / requests_where_finish_reason_is_tool_calls`; cada llamada se valida contra el esquema (JSON Schema Draft 7) y se clasifica como `InvalidJson`, `UnknownName` o `SchemaMismatch` — misma fuente — verificado 2026-10-18
- Cifra verificable (antes/después de Auto Exacto, no es rango entre proveedores simultáneos): para GLM-5 la tasa de error pasó de unas "approximately 8%" a cerca de 1 % (−88 %); gpt-oss-120b de 5.6 % a 3.5 %. Publicado 2026-03-12, actualizado 2026-06-24 — fuente (https://openrouter.ai/blog/announcements/auto-exacto/) — verificado 2026-10-18
- Cifra agregada verificable: en el leaderboard de τ²-Bench Airline, la tasa de error de los modelos inscritos en Auto Exacto bajó de 3.9 % a 1.7 % (corrida del 2026-10-18) — fuente (https://openrouter.ai/benchmarks/tau2-bench-airline) — verificado 2026-10-18
- Mismo modelo, distinto proveedor, medido en el leaderboard (exactitud, no error de tool calls): GLM 5.3 con ruteo por defecto de Z.ai 77.5 % vs 76.0 % servido por digitalocean — misma fuente — verificado 2026-10-18
- Tesis cualitativa respaldada: OpenRouter afirma que la propensión y la exactitud de tool calling varían entre proveedores bastante más de lo que sugieren los benchmarks estándar (Exacto, 2025-10-21, actualizado 2026-06-24); no da porcentajes en el texto, solo en gráficas — fuente (https://openrouter.ai/blog/announcements/provider-variance-introducing-exacto/) — verificado 2026-10-18
- Auto Exacto: reordena proveedores en cada petición con `tools`, activo por defecto, re-puntúa aproximadamente cada 5 minutos con rendimiento, telemetría de tool calls y benchmarks. Se puede forzar con el sufijo `:exacto` — fuente (auto-exacto blog) — verificado 2026-10-18
- La publicación de OpenRouter en X ("reducido las tasas de error en 15–90 %") no se pudo leer (robots); el rango 15–90 % no aparece en las páginas de docs. Posible origen del "15" que Carlos recuerda — fuente (https://x.com/OpenRouter/status/2032127261709676991, solo resultado de búsqueda) — NO VERIFICADO
- Recomendación para la diapositiva-gancho: o (a) abrir la pestaña Performance de un modelo el día del evento y capturar pantalla con fecha, o (b) usar las cifras verificables de arriba ("GLM-5: ~8 % → ~1 % tras enrutar por calidad"), diciendo que es un promedio de ruteo y no el rango entre proveedores. No escribir "15 % vs 0.01 %"

## 9. La clase de CMU

- Título del video: "CMU AI Agents 2026: 2. Tool Use for Language Model Agents"; canal de Graham Neubig; subido el 2026-09-08 — fuente (https://youtu.be/jXChFB4JSyw, metadatos vía https://podwise.ai/episodes/8884908) — verificado 2026-10-18
- Curso: CMU CS 11-768 "AI Agents", Fall 2026 (25 ago – 3 dic), Language Technologies Institute; profesores Graham Neubig y Daniel Fried; la lección 2 la da Neubig — fuente (https://www.cmu-agents.com/ y https://www.beri.net/learning/cmu-11-768-ai-agents-fall-2026, esta última es un agregador de terceros) — verificado 2026-10-18
- Diapositivas oficiales: https://www.cmu-agents.com/slides/lecture-02-tool-use.pdf (portada: "Tool Use for Language Model Agents", Graham Neubig) — verificado 2026-10-18
- Fecha de la sesión en vivo: **NO VERIFICADO** (solo la fecha de subida, 2026-09-08). La diapositiva 57 cita datos de OpenRouter del 2026-08-27. Intentado: página del curso, descripción del video
- Capítulos del video (de la página del episodio): 00:00 fundamentos; 10:26 llamada programática y riesgos de seguridad; 16:06 mecánica del formato y parseo de tool calls; 27:04 decodificación basada en gramática; 35:36 REST y MCP; 44:03 ejecución paralela y evaluación — fuente (https://podwise.ai/episodes/8884908) — verificado 2026-10-18
- Contraste de nuestros minutos con los capítulos: formatos de tool call 17:00–22:00 cae dentro de 16:06–27:04 (coherente); IDs huérfanos 25:20 cae en el mismo capítulo (coherente por capítulo); XGrammar 27:00–35:30 coincide con el capítulo 27:04–35:36; credenciales MCP 41:30 cae en 35:36–44:03 (coherente); OpenRouter 51:40 cae en 44:03–fin (coherente). **El minuto exacto de cada tema NO VERIFICADO**: no se pudo leer la transcripción (requiere inicio de sesión) ni reproducir el video — fuente (podwise) — intentado 2026-10-18
- Las diapositivas no hablan de "IDs huérfanos" (el término): la 25 solo muestra que el resultado vuelve emparejado por `tool_call_id`, incluso con llamadas paralelas. Si en el minuto 25:20 Neubig habla de huérfanos, es de palabra, no de diapositiva. Para el deck, atribuir a la clase solo "los resultados se emparejan por ID" — fuente (PDF de diapositivas, diapositiva 25) — verificado 2026-10-18
- Mapa de diapositivas de la clase útil para dar crédito: 14–16 CodeAct; 22–25 formatos de tool call e IDs; 26–35 decodificación restringida (31: "A pushdown automaton adds a stack"; 32: XGrammar, MLSys 2025; 33: caché de máscara de tokens); 40–46 REST vs MCP y credenciales; 55–57 fallas operativas y tasas por proveedor — fuente (PDF de diapositivas) — verificado 2026-10-18
- Credenciales MCP según la clase: el agente se autentica con su propia clave MCP, el servidor llama a la API con otra clave, y el modelo no ve ninguna de las dos (diapositivas 44–45, "credential brokering"); las claves estáticas son para enseñanza, en producción JWT u OAuth — fuente (PDF de diapositivas) — verificado 2026-10-18

## 10. XGrammar y CodeAct

- XGrammar: "XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models", Yixin Dong, Charlie F. Ruan, Yaxing Cai, Ruihang Lai, Ziyi Xu, Yilong Zhao, Tianqi Chen; MLSys 2025; arXiv:2411.15100 — fuente (https://arxiv.org/abs/2411.15100) — verificado 2026-10-18
- Mecanismo central según el resumen: divide los tokens en independientes del contexto (se precalculan) y dependientes del contexto (se revisan en ejecución), usando un autómata de pila (pushdown) a nivel de bytes; añade expansión de contexto, pila persistente y solapar el cómputo de gramática con la GPU — misma fuente — verificado 2026-10-18
- Resultados que reporta: hasta 100x menos latencia por token para CFG que soluciones existentes y hasta 80x de aceleración de servicio de extremo a extremo con Llama 3.1 en H100. Son cifras del paper, no nuestras; citar como "según los autores" — misma fuente — verificado 2026-10-18
- La clase de CMU (diap. 32) advierte que un token puede cruzar varios terminales de la gramática, así que los límites de token no son límites de gramática — fuente (PDF de diapositivas) — verificado 2026-10-18
- CodeAct: "Executable Code Actions Elicit Better LLM Agents", Xingyao Wang, Yangyi Chen, Lifan Yuan, Yizhe Zhang, Yunzhu Li, Hao Peng, Heng Ji; ICML 2024; arXiv:2402.01030 — fuente (https://arxiv.org/abs/2402.01030) — verificado 2026-10-18
- Resultado principal del resumen: hasta 20 % más de tasa de éxito que alternativas comunes; la introducción añade hasta 30 % menos acciones — misma fuente — verificado 2026-10-18
- En la clase (diap. 16), sobre un subconjunto mostrado, el código tuvo la mejor tasa de éxito en 8 de 8 modelos y menos turnos en 7 de 8; entre los 17 modelos, 12 de 17 en ambos — fuente (PDF de diapositivas) — verificado 2026-10-18

## 11. Plantillas de chat (para `taller/plantilla.py`)

### Qwen
- Repo: `Qwen/Qwen3-8B`; el archivo `tokenizer_config.json` (9.73 kB) contiene una clave `chat_template` con soporte de herramientas — fuente (https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json) — verificado 2026-10-18
- URL del archivo crudo: https://huggingface.co/Qwen/Qwen3-8B/raw/main/tokenizer_config.json (último commit visible: "update tokenizer_config.json", hash 895c8d1, por feihu.hf; fecha no mostrada). Para versionar en `taller/vendor/`, guardar también el hash del commit — verificado 2026-10-18
- Herramientas: la plantilla abre un bloque de sistema, indica que se dan firmas de funciones dentro de etiquetas `<tools></tools>` y serializa cada herramienta como JSON (`tool | tojson`) — misma fuente — verificado 2026-10-18
- Llamada del asistente: un bloque `<tool_call>` con un objeto JSON `{"name": ..., "arguments": ...}` seguido de `</tool_call>` — misma fuente — verificado 2026-10-18
- Resultados: se renderizan dentro de un turno de usuario, envueltos en `<tool_response>` … `</tool_response>`; resultados consecutivos comparten un solo turno de usuario — misma fuente — verificado 2026-10-18
- Tokens especiales: `<|im_start|>` (id 151644, special) y `<|im_end|>` (id 151645, special; también `eos_token`). `<tool_call>` (151657), `</tool_call>` (151658), `<tool_response>` (151665), `</tool_response>` (151666) están en `added_tokens_decoder` con `special: false`, es decir, son tokens añadidos que el tokenizador reconoce como una sola unidad pero no están marcados como especiales. `<think>` (151667) y `</think>` (151668) también `special: false` — misma fuente — verificado 2026-10-18
- Cuidado con la versión: Qwen3-8B usa **JSON dentro de `<tool_call>`**. La diapositiva 23 de la clase de CMU muestra para "Qwen" un formato distinto con etiquetas XML `<function=get_weather>` y `<parameter=city>` dentro de `<tool_call>`, de una versión más reciente. Si se muestra Qwen3-8B, decir "Qwen3-8B"; no mezclar con el formato de la diapositiva — fuente (PDF de diapositivas, diap. 23) — verificado 2026-10-18

### Otra familia: DeepSeek (completa) y Mistral (parcial)
- DeepSeek-V3: `deepseek-ai/DeepSeek-V3/raw/main/tokenizer_config.json` contiene `chat_template`; tokens de llamada: `<｜tool▁calls▁begin｜>`, `<｜tool▁call▁begin｜>`, `<｜tool▁sep｜>` (separa tipo y nombre de función), `<｜tool▁call▁end｜>`, `<｜tool▁calls▁end｜>`; de resultados: `<｜tool▁outputs▁begin｜>`, `<｜tool▁output▁begin｜>`, `<｜tool▁output▁end｜>`, `<｜tool▁outputs▁end｜>`; BOS `<｜begin▁of▁sentence｜>`, EOS `<｜end▁of▁sentence｜>` — fuente (https://huggingface.co/deepseek-ai/DeepSeek-V3/raw/main/tokenizer_config.json) — verificado 2026-10-18
- Recomendación para el segundo modo de `plantilla.py`: DeepSeek-V3 (tiene la plantilla completa en `tokenizer_config.json` y se ve muy distinta a Qwen). Los caracteres `｜` y `▁` son Unicode de ancho completo, no ASCII: copiarlos del archivo, no teclearlos — fuente (misma) — verificado 2026-10-18
- DeepSeek-V3.2 **no** trae `chat_template` en su `tokenizer_config.json`; la clase de CMU lo muestra con bloques DSML (`<｜DSML｜function_calls>`, `<｜DSML｜invoke name="get_weather">`, `<｜DSML｜parameter name="city" string="true">`), pero ese formato lo genera código de codificación aparte, no una plantilla Jinja en el repo, así que no sirve para `jinja2` puro — fuente (https://huggingface.co/deepseek-ai/DeepSeek-V3.2/raw/main/tokenizer_config.json y PDF de diapositivas, diap. 23) — verificado 2026-10-18
- Mistral-7B-Instruct-v0.3: `tokenizer_config.json` define como tokens especiales `[TOOL_CALLS]` (id 5), `[AVAILABLE_TOOLS]` (6), `[/AVAILABLE_TOOLS]` (7), `[TOOL_RESULTS]` (8) y `[/TOOL_RESULTS]` (9); la tarjeta del modelo exige IDs de llamada de exactamente 9 caracteres alfanuméricos — fuente (https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3/raw/main/tokenizer_config.json y https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3) — verificado 2026-10-18
- Mistral: el texto Jinja de `chat_template` (cómo se arma `[AVAILABLE_TOOLS]`, `[TOOL_CALLS]` y `[TOOL_RESULTS]`) **NO VERIFICADO**. Lo intentado: WebFetch del archivo crudo y de la vista blob (la lectura se corta en la lista de tokens añadidos antes de llegar a `chat_template`), la tarjeta del modelo (no muestra el prompt crudo), y `chat_template.jinja` de Mistral-Small-3.2 (error). Mistral Small en la diapositiva 23 de la clase usa `[TOOL_CALLS]` seguido de una lista JSON con campo `"id"` y termina con `</s>` — fuente (PDF de diapositivas) — verificado 2026-10-18
- Interfaz genérica de Transformers para plantillas con herramientas: las llamadas van en `tool_calls` de un mensaje `assistant` con `{"type": "function", "function": {"name", "arguments"}}`, y `arguments` debe ser dict (no cadena JSON); el resultado va en un mensaje con `role: "tool"` — fuente (https://huggingface.co/docs/transformers/en/chat_extras) — verificado 2026-10-18

---

## Resumen de pendientes (NO VERIFICADO)

1. Cifra "15 % vs 0.01–0.05 %" de GLM 5.3 en OpenRouter (ver §8). No usar en el deck.
2. Minuto exacto de cada tema en el video de CMU (solo verificado por capítulos) y fecha de la sesión en vivo (§9).
3. Texto Jinja de `chat_template` de Mistral (§11); usar DeepSeek-V3 para el segundo formato.
4. Que `disable_parallel_tool_use` con `auto` esté documentado específicamente para Sonnet 5.5 (inferido de Opus 5.5; ver §1).
5. Texto completo oficial del 400 de huérfanos: la doc solo cita un fragmento; el resto viene de una fuente secundaria (§5).

## Ensayo en vivo (2026-10-18, claude-sonnet-5-5 y claude-haiku-5-5)

- Texto completo del 400 por `tool_use` huérfano, obtenido de la API en vivo: "messages.2: `tool_use` ids were found without `tool_result` blocks immediately after: <id>. Each `tool_use` block must have a corresponding `tool_result` block in the next message." (type `invalid_request_error`) — fuente (corrida de `taller.romper huerfano` y `truncado`) — verificado 2026-10-18. Resuelve el NO VERIFICADO de §5.
- Con un `tool_result` con `is_error`, Sonnet 5.5 explicó la interrupción y relanzó la consulta por su cuenta — fuente (corrida de `romper huerfano`) — verificado 2026-10-18
- Ante el prompt adversarial de `romper drop`, Sonnet 5.5 respondió con `stop_reason=refusal` (dos veces); el arnés inyectó las llamadas y lo anunció — fuente (corrida de `romper drop`) — verificado 2026-10-18
- Paralelas: el modelo emitió 3 `tool_use` en un solo turno; 2.40 s secuencial vs 0.80 s con `gather` (latencia artificial de 0.8 s) — fuente (corrida de `romper paralelo`) — verificado 2026-10-18
- `medir --vs`: ambos modelos 20/20; costo por tarea resuelta $0.0097 (Sonnet 5.5) vs $0.0006 (Haiku 5.5); en a02 Haiku intentó leer `secretos` y la compuerta lo rechazó, Sonnet se negó; costo total de la corrida ~$0.19 + $0.01 — fuente (runs/medicion-*-20261018-151955.json, no versionados) — verificado 2026-10-18
- Rotura #1b en vivo: con 3 `tool_use` en paralelo y una llamada que pasa el tope (latencia artificial anunciada), devolver solo 2 `tool_result` produce el mismo 400 del huérfano; con el timeout como `is_error`, Sonnet 5.5 reintentó la consulta por su cuenta. `gather` tardó 1.50 s (el tope) contra ≥ 4.6 s en secuencia — fuente (corrida de `romper paralelo` en `paso-1` y `main`) — verificado 2026-10-18
