# SPEAKER — cómo enseña Carlos (para autores de diapositivas y revisores)

Basado en tres charlas recientes: GBM AI Experience (transcripción), Snowflake World Tour
(diapositivas) y la crítica posterior. Los autores de W1-F/W1-G escriben las notas de presentador
pensando en esto; W3-A revisa contra esto.

## Fortalezas: diseñar para que aparezcan

- **Datos del cuarto como protagonista.** La encuesta en vivo de GBM fue el mejor momento. En el
  taller, el equivalente son las corridas de cada asistente: preguntar y usar lo que salga.
- **Predecir y revelar.** La canción tocada en la mesa (Snowflake) funcionó porque el público se
  comprometió con una respuesta antes de ver el resultado. Cada rotura empieza con
  "¿qué creen que pasa?" y una respuesta del público que después se retoma.
- **Historias de terror concretas.** El clasificador que devolvió `null` y gastó $10 000 en
  reintentos ganó la sala. Una historia por rotura, en las notas, de ≤ 45 s.
- **Recuperarse con humor de una falla.** Es fortaleza, pero en un taller las fallas deben ser las
  planeadas: cada demo tiene modo inyectado y branch de respaldo.
- **Marcos con preguntas para llevarse** (Contexto × Evidencia × Control). Aquí: una pregunta por bloque.
- **Frases de remate.** "Producir el output se abarató, el outcome no" salió en preguntas y era
  mejor que el cierre. Las frases buenas se escriben en las notas como transición, no se improvisan.

## Debilidades: diseñar para que no aparezcan

- **Relleno antes del contenido** (historia de 7 min, esperar la encuesta). Regla: código o rotura
  en pantalla antes del minuto 5.
- **Autopromoción repetida.** Una diapositiva "quién es este tipo" (≤ 30 s) y el QR al final. Nada más.
- **Participación decorativa** (pedir definiciones y reemplazarlas por la de Willison). Solo
  preguntar si la respuesta se va a usar; la nota dice cómo.
- **Sobreafirmar bajo presión** ("nunca devuelve null", "nadie lo tiene en producción"). Las notas
  incluyen la cifra exacta de `FACTS.md`; ante la duda: "no lo sé, lo verifico y lo publico en el repo".
- **Demo que contradice la tesis** (LLM juzgando a LLM). Toda compuerta del taller es determinista.
- **Muletillas** ("¿no?", "fenomenal"). Una línea `.warn` en las notas de la portada lo recuerda.
- **Cierre que se diluye.** La última frase está escrita palabra por palabra en las notas.

## Específico de taller (formato nuevo para Carlos)

- **Puntos de control con la mano levantada** al final de cada paso ("levanten la mano si ya vieron
  el 400"). Si menos de la mitad, todos hacen `git checkout paso-N` y se sigue. Va en las notas.
- **Tiempo de silencio planeado**: cuando la gente teclea, el orador no habla. Las notas dicen
  cuántos minutos de teclado tiene cada paso.
- **Dos niveles**: quien termina antes tiene un "extra" por paso en el README (p. ej. medir con otro modelo).
