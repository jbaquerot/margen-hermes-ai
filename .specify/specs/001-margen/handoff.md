# Handoff de implementación — Margen

- **Versión:** 1.0.0
- **Estado:** Aprobado por el usuario — fase Handoff completada
- **Fecha:** 2026-10-18
- **Edición pública:** nombres personales e inventario ajeno a Margen omitidos; sin cambios funcionales.
- **Destino:** contexto inicial para Codex o Claude Code en el proyecto Margen.
- **Situación:** Constitución, especificación, plan y tareas aprobados como versión 1.0.0. Implementación no iniciada.

Este documento puede copiarse como mensaje inicial de una sesión de implementación con acceso al proyecto. Prepararlo no ha ejecutado las instrucciones que siguen. Los cuatro documentos aprobados son la fuente normativa; este resumen no los sustituye.

---

## Encargo para el agente de implementación

Implementa **Margen**, un perfil personal de Hermes Agent paral usuario. Conserva notas de sus lecturas recibidas por Telegram, genera resúmenes solo a petición y permite encontrar notas describiendo una idea sin recordar el libro ni las palabras exactas. El usuario lee varios libros simultáneamente; estima cinco libros al año, con una cantidad variable de notas. Esa estimación no es una cuota.

### 1. Lee primero el paquete aprobado

Rutas relativas a la raíz del proyecto:

1. [`.specify/memory/constitution.md`](../../memory/constitution.md): principios de fidelidad, trazabilidad, separación de libros, privacidad e integridad.
2. [`.specify/specs/001-margen/spec.md`](spec.md): historias de usuario, RF-01 a RF-44 y criterios de aceptación.
3. [`.specify/specs/001-margen/plan.md`](plan.md): arquitectura, entorno diagnosticado, modelos, persistencia y despliegue.
4. [`.specify/specs/001-margen/tasks.md`](tasks.md): 41 tareas, dependencias, archivos, verificación y trazabilidad.

Lee también las instrucciones locales aplicables del repositorio. Si encuentras una contradicción que cambie el comportamiento o la arquitectura aprobados, señálala antes de avanzar con la parte afectada. No alteres una especificación para justificar retrospectivamente una implementación diferente.

### 2. Estado real y primer paso

El repositorio contiene los documentos de diseño y [`scripts/diagnostico-margen.sh`](../../../scripts/diagnostico-margen.sh). No hay todavía un plugin Margen implementado, un perfil desplegado ni pruebas del producto superadas.

Empieza por **T001**, comprobando el contrato de extensión de la revisión objetivo de Hermes. El diagnóstico encontró símbolos en sus fuentes y se consultó documentación fijada al commit; eso no demuestra el funcionamiento del futuro plugin. No vuelvas a pedir al usuario los datos del sistema que ya constan en el plan.

Después sigue `tasks.md` por dependencia. `[P]` indica posibilidad de trabajo paralelo sobre archivos independientes, no una obligación de delegación. Solo marca tareas completadas cuando exista la evidencia de su condición de finalización. Si no tienes acceso a la Raspberry o al canal real, completa lo que pueda verificarse en aislamiento y deja las comprobaciones de destino pendientes de forma explícita.

### 3. Entorno de destino

| Elemento | Base confirmada |
| --- | --- |
| Equipo | Raspberry Pi 5, ARM64/aarch64, aproximadamente 16 GB de RAM. |
| Sistema | Debian GNU/Linux 13 (trixie), kernel `6.18.50+rpt-rpi-2712`. |
| Disco de trabajo | NVMe local con ext4. |
| Usuario | `claw`. |
| Hermes | Instalación Git en `/home/claw/.hermes/hermes-agent`. |
| Commit | `22063fc099ec9ad8357d7f8f6e6248a0400680d3`. |
| Intérprete examinado | `/home/claw/.hermes/hermes-agent/venv/bin/python`, Python `3.11.15`. |
| Dependencias examinadas | OpenAI SDK `2.24.0`, python-telegram-bot `22.8`, SQLite `3.53.1` con FTS5 y API de backup disponibles. |
| Supervisión existente | Servicios systemd de usuario por perfil; preservar los servicios ajenos a Margen. |

El dato inicial de Python 3.14.7 quedó corregido por el diagnóstico del venv. No actualices Python ni Hermes como parte implícita de Margen. El commit es la referencia de compatibilidad; no deduzcas el canal del proceso activo de una etiqueta de `git describe`.

### 4. Arquitectura y decisiones cerradas

- Perfil `margen`, identidad propia y bot de Telegram exclusivo, en conversación privada y con acceso limitado al usuario. Configurar credenciales e IDs localmente al desplegar, sin solicitarlos en informes ni incluirlos en Git.
- Plugin Python con dominio determinista, persistencia transaccional y adaptador nativo de Telegram registrado mediante interfaces públicas de Hermes. Verificar autenticación antes de acceder al dominio, IDs originales y ausencia de doble despacho; no parchear funciones privadas.
- SQLite propia, separada de las bases internas de Hermes y del paquete actualizable. Ruta propuesta para el perfil: `/home/claw/.hermes/profiles/margen/plugin-data/margen/data.db`, resuelta y comprobada con el mecanismo de datos del perfil.
- Telegram es la interfaz. No construir web React, API FastAPI ni servidor MongoDB: el plan adapta el contexto genérico de Grady a este uso personal.
- Resúmenes breves y detallados con OpenRouter, modelo explícito **`anthropic/claude-haiku-5.5`**. Las notas necesarias para resumir salen al proveedor; no gestionar ni refrescar credenciales directamente. No cambiar automáticamente a otros modelos.
- Búsqueda completamente local con **`intfloat/multilingual-e5-small`**, SQLite FTS5, vectores de 384 dimensiones y similitud/fusión de posiciones. Propuesta de ejecución ONNX Runtime CPU; verificar disponibilidad del modelo en el envoltorio y, si hace falta, preparar una conversión reproducible. Fijar versiones y hashes al resolver dependencias.
- Usar los prefijos de recuperación del modelo, fragmentar notas largas y agrupar resultados por nota. Descargar artefactos durante la preparación; después `/buscar` y `/mas` deben funcionar sin red y no enviar notas, consultas ni vectores a servicios externos.
- Unidad dedicada de usuario propuesta: `hermes-gateway-margen.service`, con reinicio tras fallo y arranque persistente. Verificar lingering y el intérprete efectivo antes de habilitarla. No tocar otros perfiles ni sus tokens.

### 5. Contrato de conversación y comandos

| Entrada | Comportamiento |
| --- | --- |
| Texto sin comando | Guardar nota en el libro activo, salvo durante una aclaración pendiente. |
| `/nota texto` | Guardar nota explícitamente; también disponible durante aclaraciones. |
| `/libro Título \| Autor` | Registrar libro con ambos datos, sin activarlo. Evitar duplicado de título y autor. |
| `/activar Título` | Activar un libro registrado; si es ambiguo, opciones numeradas con título y autor. |
| `/libros` | Listar títulos/autores e identificar el activo o su ausencia. |
| `/ver referencia` | Mostrar texto vigente completo y libro o estado sin asignar. |
| `/editar referencia nuevo texto` | Corregir conservando original y versiones anteriores. |
| `/mover referencia \| Título` | Cambiar libro o asignar una pendiente individualmente; no cambia el activo. |
| `/historial referencia` | Mostrar original y correcciones cronológicas, identificando la vigente. |
| `/eliminar referencia` | Mostrar nota y alcance; borrar original e historial solo tras `/confirmar`. |
| `/resumen` | Resumen breve del libro activo, hasta 300 palabras orientativas. |
| `/resumen detallado` | Resumen detallado del libro activo, hasta 1.000 palabras orientativas. |
| `/resumenes` | Listar referencias, fecha, modalidad y estado de resúmenes guardados. |
| `/ver_resumen referencia` | Abrir un resumen guardado, advirtiendo si está desactualizado. |
| `/buscar descripción` | Buscar entre todos los libros y pendientes; hasta cinco resultados por relevancia. |
| `/mas` | Hasta cinco resultados adicionales de la última búsqueda, sin repeticiones. |
| `/exportar` | Archivo Markdown con todas las notas vigentes del libro activo, título, autor y referencias. |
| `/confirmar` | Aceptar exclusivamente la acción y objetivos presentados para confirmación. |
| `/cancelar` | Abandonar la interacción pendiente sin borrar notas ni revertir acciones completadas. |

Reglas que no debes simplificar:

- El libro activo persiste hasta cambiarlo. Confirmar cada guardado exitoso con libro y referencia N; si no hay activo, conservar como pendiente, dar referencia y preguntar a qué libro corresponde.
- Resolver la selección inicial de una nota pendiente activa el libro para las siguientes. Si hay varias pendientes, presentar las referencias y confirmar su asignación en bloque. El conjunto no incorpora notas posteriores. La asignación individual por `/mover` es distinta y no cambia el activo.
- Mientras se espera una aclaración, el texto sin comando responde a esa pregunta y no es una nota nueva. `/nota texto` sigue capturando sin resolver ni cancelar la interacción. Una nueva operación que requiera otra respuesta debe esperar a resolver/cancelar la anterior.
- Los comandos desconocidos o incompletos no se guardan como notas. Las respuestas numéricas solo seleccionan dentro de la interacción que las espera.
- Ambos resúmenes abarcan todas las notas vigentes del libro activo, en orden original de guardado. Para otro libro, activarlo primero; no añadir argumentos de selección de libro a `/resumen`.
- Si no hay activo al pedir resumen, exportación o listado de resúmenes, solicitar selección y continuar la petición sin repetirla. Sin notas no inventar resumen ni generar una exportación vacía.
- Cada resultado de búsqueda muestra nota vigente completa, referencia y título/autor, o «Sin libro asignado». No devolver versiones históricas como resultado vigente ni inventar referencias.
- Editar/mover conserva la referencia y fecha original; mover ordena según esa fecha en el destino. Las consultas no cambian el activo.
- Conservar cobertura de resúmenes mediante referencias y versiones. Notas nuevas, correcciones, movimientos y borrados pueden dejarlos desactualizados; mantenerlos identificados y no regenerarlos automáticamente.
- Eliminar una nota no retira información de resúmenes conservados ni de archivos o mensajes ya enviados. Explicar ese alcance antes de confirmar.

### 6. Garantías de datos y recuperación

La fuente de verdad es SQLite; la memoria del asistente y el historial de Telegram no sustituyen la conservación de notas. Mantén originales y versiones hasta una eliminación confirmada. No inventes citas, capítulos, páginas ni ideas del autor. Separa citas identificadas por el usuario, reflexiones propias e interpretaciones del asistente.

Usa la identidad original bot/chat/mensaje para idempotencia, nunca el contenido de la nota. Un reintento después de cambiar el activo debe recuperar el resultado original. Mensajes distintos con el mismo texto pueden ser notas distintas.

La mutación, su recibo y la preparación de la respuesta deben confirmarse transaccionalmente antes de decir «guardada». Un fallo de entrega reintenta la respuesta, no la captura. Serializa mutaciones por propietario y no mantengas transacciones abiertas durante inferencia o red.

Los trabajos largos capturan libro y parámetros al iniciarse. La indexación no bloquea el guardado. Invalida versiones obsoletas, evita que una caché resucite notas borradas y distingue una búsqueda incompleta o fallida de una búsqueda completa sin coincidencias.

### 7. Backup: diseño y límite de alcance

El backup existente usa rsync y un SSD externo exFAT destinado a permanecer montado en `/mnt/backup-ssd`, con destino comunicado `/mnt/backup-ssd/backups/`. Cron invoca `/home/claw/scripts/backup-claw.sh` semanalmente; el análisis detectó exclusiones y `--delete`, pero no certificó cobertura de `.hermes` ni retención.

En el diagnóstico el USB estaba presente sin montar, y la carpeta de backup apuntaba al NVMe. **el usuario ha pedido expresamente no diagnosticar ni reparar ese montaje dentro de este trabajo.** Conserva la incidencia como dependencia externa de validación del backup.

Prepara la instantánea actual consistente con la API SQLite, manifiesto, integridad y hash. No reemplaces la última verificada por una copia parcial ni escribas al destino cuando falte el montaje esperado. No amplíes `--delete`, no introduzcas purgas automáticas ni una nueva serie histórica. Documenta la retención externa real al integrar el script; las copias antiguas pueden conservar notas eliminadas.

Restaura primero en cuarentena, sin reactivar entregas, trabajos o confirmaciones antiguas. Verifica las eliminaciones posteriores cuando haya registro; si no puede determinarse ese alcance, exige revisión explícita de la recuperación histórica antes de reemplazar la base activa. No declares el backup externo validado mientras falte la evidencia correspondiente.

### 8. Orden de trabajo y archivos

`tasks.md` determina las dependencias exactas:

1. T001–T004: contrato, esqueleto, interfaces y datos sintéticos anotados.
2. T005–T016: esquema, transacciones, idempotencia, conversaciones, libros y ciclo de notas.
3. T017–T021: trabajos persistentes, modelo e indexación locales, búsqueda y paginación.
4. T022–T026: inferencia de resúmenes, cobertura, consultas y exportación.
5. T027–T030: adaptadores, transporte, despacho, manifiesto e identidad del perfil.
6. T031–T035: fallos, integración y evaluación del rendimiento y calidad.
7. T036–T041: instantáneas/restauración, documentación, empaquetado y validación controlada.

Implementa el núcleo bajo `plugins/margen/margen/`, la entrada de plugin en `plugins/margen/__init__.py`, el manifiesto en `plugins/margen/plugin.yaml` y las plantillas en `profile/`. Añade las pruebas, scripts y documentos en los archivos asignados por cada tarea. Los documentos aprobados describen nombres propios de Margen; no los confundas con APIs existentes de Hermes.

### 9. Evidencia exigida para aceptar la entrega

| Criterio | Verificación |
| --- | --- |
| RF-01 a RF-44 | Matriz de trazabilidad de Tasks y escenarios observables de la especificación. |
| CR-01 | Confirmación de guardado en menos de cinco segundos bajo las condiciones normales documentadas, sin anticipar el éxito de la transacción. |
| CR-02 | Aviso de trabajo en curso cuando resumen, búsqueda o exportación superen cinco segundos. |
| CC-01 | En diez consultas con resultado esperado fijado de antemano, al menos ocho recuperan la nota entre las primeras cinco. |
| CC-02 | Resúmenes con ideas principales anotadas, orden respetado y cero afirmaciones sin respaldo; revisión semántica, no igualdad de redacción. |
| CC-03 | Todas las referencias emitidas en la evaluación recuperan la nota correcta; informar si fue eliminada posteriormente. |
| CC-04 | Reintentos, fallos y concurrencia no provocan notas duplicadas por reentrega, confirmaciones falsas ni cambios de notas ajenas. |

Comprueba además búsqueda sin red tras la descarga del modelo, autorización, respuestas largas, archivo Markdown, persistencia del activo y pendientes, reinicio del gateway y arranque de la unidad. Las pruebas reales de Haiku y Telegram son distintas de mocks y pruebas estáticas.

### 10. Forma de informar y finalizar

Comunica avances y problemas en español. Para cada bloque terminado, identifica tareas completadas, archivos afectados y pruebas ejecutadas. Mantén pendientes las comprobaciones que no hayas podido realizar, con su causa concreta.

La implementación puede avanzar en un entorno aislado; no confundas esta instrucción con autorización para reparar el SSD, modificar otros perfiles, activar producción o reiniciar la Raspberry. Aplica el alcance de despliegue autorizado en la sesión de ejecución y prepara resultados revisables antes de solicitar las decisiones operativas que falten.

Al finalizar, entrega un paquete reproducible, instrucciones de operación/reversión y evidencia consolidada en `docs/validation.md`. Distingue «funciona en pruebas», «canal real validado» y «recuperación externa validada». No declares Margen listo para uso personal con backup comprobado si esa última condición sigue pendiente.

---

## Revisión del Handoff

- [x] Resume los cuatro artefactos aprobados y enlaza sus archivos.
- [x] Contexto de producto, comandos y excepciones relevantes conservados.
- [x] Entorno diagnosticado y modelos acordados identificados.
- [x] Primer paso T001, orden y evidencia de aceptación explícitos.
- [x] Límites de alcance y comprobaciones pendientes diferenciados de resultados ejecutados.
- [x] Aprobación del usuario del documento de traspaso.

## Historial de aprobación

| Versión | Fecha | Estado | Cambio |
| --- | --- | --- | --- |
| 1.0.0 | 2026-10-18 | Aprobado | el usuario aprueba el Handoff; paquete de especificaciones completo, implementación no iniciada. |
