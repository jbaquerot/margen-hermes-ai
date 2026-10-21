# Evaluación de resúmenes

Los tests locales utilizan dobles del modelo para comprobar estructura, cobertura de referencias, orden, fragmentación sin truncado, errores y desactualización. **No demuestran la fidelidad semántica de Haiku real.**

Los datos públicos de evaluación y sus ideas esperadas están en `tests/fixtures/reading_notes.json` y `summary_expectations.json`. Incluyen citas ficticias marcadas, reflexiones, matices y contradicción explícita. Ninguna cita procede de un libro real.

`scripts/evaluate-summaries.py` proporciona `build_cases(ctx)`, un generador asíncrono de diez casos (cinco libros, dos modalidades), usando el `PluginContext` real de Hermes. No contiene un cliente alternativo ni lee claves. Para ejecutarlo en la validación del plugin, importar esa función en el entorno de prueba de Hermes y guardar sus resultados en una ruta privada. También se pueden recorrer los mismos libros/notas mediante el bot de prueba y recoger `/resumen` y `/resumen detallado`.

Cada resultado necesita revisión humana:

1. Cada idea principal anotada aparece y puede vincularse a una fuente concreta.
2. El texto sigue el orden de captura, conserva matices y no resuelve contradicciones inventando una conclusión.
3. No incorpora hechos externos, páginas, capítulos ni citas inexistentes.
4. Distingue la reflexión personal de una afirmación atribuida al autor y respeta las citas identificadas.
5. Usa la modalidad pedida: hasta 300/1.000 palabras orientativas, ajustándose a la cantidad de notas sin rellenar.
6. Las referencias consultadas existen y corresponden a la instantánea del libro solicitado; el resumen se conserva con referencia R y avisa si quedó desactualizado.

Una referencia correcta no prueba que la frase esté respaldada. Rechazar un resultado con afirmaciones sin fuente, aunque sus comprobaciones estructurales pasen. Revisar especialmente la última nota en entradas largas y el resultado tras editar mientras se genera.

Estado: el usuario ejecutó ambos modos en su bot de laboratorio el 2026-10-20 y compartió dos resúmenes correctos de dos notas ficticias. El adaptador exige OpenRouter y el modelo aprobado; las llamadas se ejecutaron en la Raspberry con las credenciales configuradas localmente por el usuario. Cobertura, orden y ausencia de añadidos se cumplen en este caso mínimo. La evaluación ampliada de diez casos y la rúbrica completa siguen **pendientes de T040**; no se considera cerrada la calidad semántica con dos frases.


Repetición del caso de matices (2026-10-21): `/resumen detallado` completó tras un aviso de progreso. Revisión del texto aportado: las tres notas están representadas en orden con las referencias esperadas; mantiene la tensión entre constancia y adaptación, reconoce el equilibrio no explicado y separa la reflexión personal de las afirmaciones atribuidas al autor. Este caso pasa. El intento anterior había fallado sin causa identificada; una repetición correcta no determina esa causa ni acredita fiabilidad sostenida. La rúbrica completa y los diez casos siguen pendientes.
