# Tareas de implementación de Margen

- **Versión:** 1.0.0
- **Estado:** Aprobado por el usuario — fase Tasks completada
- **Fecha:** 2026-10-18
- **Edición pública:** nombres personales e inventario ajeno a Margen omitidos; sin cambios funcionales.
- **Base:** [Constitución 1.0.0](../../memory/constitution.md), [especificación 1.0.0](spec.md) y [plan técnico 1.0.0](plan.md), aprobados.
- **Ejecución:** implementación iniciada el 2026-10-18 por autorización del usuario. Evidencia local y puertas de destino en [docs/validation.md](../../../docs/validation.md). El script de diagnóstico es evidencia previa.

## Convenciones y límites

Todas las rutas de archivos indicadas son relativas a la raíz de este proyecto. `plugins/margen/margen/` es el paquete de dominio y servicios; `plugins/margen/__init__.py` conecta ese paquete con Hermes. Las rutas de instalación de la Raspberry se indican expresamente cuando son relevantes.

- Cada `Tnnn` es una unidad revisable con dependencias y una condición de finalización observable. Marcarla completada solo con su evidencia correspondiente.
- `[P]` significa que puede ejecutarse en paralelo con otras tareas que tengan sus dependencias resueltas y no modifiquen los mismos archivos. No implica crear agentes ni ejecutar trabajo ahora.
- Los archivos futuros de pruebas se incluyen en las tareas que verifican comportamiento y riesgos reales. No se exige comparar literalmente la redacción de los resúmenes.
- No modificar los documentos aprobados para acomodar una incompatibilidad sin señalarla. Si cambia una decisión de arquitectura o un flujo aprobado, revisar el documento afectado antes de continuar con esa parte.
- No reparar el montaje del SSD externo, modificar otros perfiles, actualizar Hermes ni sustituir el Python del sistema como parte de esta implementación.
- Los comandos, credenciales y pruebas de producción no se ejecutan durante la elaboración de este documento. Los secretos se configurarán localmente al desplegar y no formarán parte de fixtures ni del repositorio.

## A. Contratos y preparación

- [x] **T001 — Verificar el contrato de extensión de la revisión de Hermes.**
  - **Depende de:** ninguna.
  - **Archivos:** `docs/compatibility.md`, `tests/test_hermes_contract.py`.
  - **Trabajo:** contrastar el código/documentación de `22063fc099ec9ad8357d7f8f6e6248a0400680d3` con registro de comandos, fábrica nativa de Telegram, carga por perfil, identidad del mensaje, entrega de archivos e inferencia de extensiones. Revisar los nombres aprobados frente a comandos nativos y el comportamiento de python-telegram-bot 22.8. Preparar la prueba de contrato aislada, sin tokens ni bot real.
  - **Finaliza cuando:** quedan documentadas firmas, rutas públicas, orden de despacho y limitaciones; se demuestra cómo obtener el mensaje original y evitar doble consumo. Una ausencia de capacidad no se suple con parches privados.

- [x] **T002 — Crear el esqueleto del paquete y el entorno de desarrollo.**
  - **Depende de:** T001.
  - **Archivos:** `pyproject.toml`, `.gitignore`, `plugins/margen/__init__.py`, `plugins/margen/margen/__init__.py`, `tests/conftest.py`.
  - **Trabajo:** declarar Python 3.11 y separar las dependencias de desarrollo de las del plugin. Excluir secretos, datos personales, bases, cachés, modelos descargados e informes privados; conservar scripts y fixtures sintéticos. No instalar ni arrancar el plugin en un perfil personal.
  - **Finaliza cuando:** los módulos vacíos se importan en el entorno de prueba y las pruebas pueden usar una raíz temporal independiente de `/home/claw/.hermes`.

- [x] **T003 — Definir los contratos propios de Margen.**
  - **Depende de:** T002.
  - **Archivos:** `plugins/margen/margen/domain.py`.
  - **Trabajo:** definir eventos de entrada, identidad autorizada, referencias N/R, fechas UTC, orden estable, versiones de notas, cobertura de resúmenes, estados de interacción/trabajo y resultados de entrega. Definir interfaces de almacenamiento, transporte e inferencia sin importaciones privadas de Hermes.
  - **Finaliza cuando:** cada servicio posterior puede trabajar con estos contratos sin depender del texto del chat ni de variables globales para conocer usuario, libro o mensaje.

- [x] **T004 [P] — Preparar datos de evaluación independientes de la implementación.**
  - **Depende de:** T003.
  - **Archivos:** `tests/fixtures/reading_notes.json`, `tests/fixtures/search_queries.json`, `tests/fixtures/summary_expectations.json`.
  - **Trabajo:** incluir cinco libros ficticios, dos con título compartido, al menos treinta notas, pendientes, citas identificadas, reflexiones, contradicciones, notas largas y fechas intercaladas. Fijar diez descripciones con sus referencias esperadas e ideas principales/orden para evaluar resúmenes.
  - **Finaliza cuando:** los resultados esperados están anotados antes de probar modelos y ninguna muestra usa datos privados del usuario. Incluir consultas sin coincidencia como casos adicionales, fuera del denominador de diez consultas de CC-01.

## B. Persistencia y captura verificable

- [x] **T005 — Crear el esquema inicial de SQLite.**
  - **Depende de:** T003.
  - **Archivos:** `plugins/margen/margen/migrations/001_initial.sql`.
  - **Trabajo:** crear tablas e índices del plan, incluidos fragmentos, embeddings y trabajos de indexación. Añadir claves únicas de libro normalizado y entrega, versiones únicas y relaciones con borrado de historial. La trazabilidad de un resumen conservado no debe impedir eliminar su nota original.
  - **Finaliza cuando:** una base temporal nueva aplica la migración, comprueba integridad y rechaza duplicados de identidad; el esquema tiene una versión explícita.

- [x] **T006 — Implementar almacenamiento y transacciones.**
  - **Depende de:** T005.
  - **Archivos:** `plugins/margen/margen/storage.py`, `tests/test_storage.py`.
  - **Trabajo:** resolver los datos fuera del paquete, activar claves foráneas y configurar WAL/conexiones e inserción con desempate estable. Implementar unidades de trabajo, consultas parametrizadas, invalidación de cobertura y publicación de trabajos de índice en la misma transacción de la mutación.
  - **Finaliza cuando:** commit/rollback funcionan, se conserva el estado al reabrir y un error no deja cambios parciales. No se mantiene una transacción mientras se espera al modelo o a Telegram.

- [x] **T007 — Implementar el análisis estricto de comandos.**
  - **Depende de:** T003.
  - **Archivos:** `plugins/margen/margen/commands.py`, `tests/test_command_parsing.py`.
  - **Trabajo:** reconocer todos los comandos aprobados, separadores y argumentos; distinguir texto de nota, respuestas a aclaraciones y errores. Reservar las dos formas de `/resumen`, sin argumento de libro. Tratar `/nota` vacío como incompleto; preservar el contenido de notas sin el prefijo del comando.
  - **Finaliza cuando:** comandos desconocidos/incompletos no se convierten en notas y cada formato aprobado produce una intención tipada sin intervención de IA. La normalización de títulos no altera el texto de las notas.

- [x] **T008 — Añadir aceptación idempotente y bandeja de salida.**
  - **Depende de:** T006.
  - **Archivos:** `plugins/margen/margen/events.py`, `plugins/margen/margen/outbox.py`, `tests/test_event_acceptance.py`.
  - **Trabajo:** vincular el evento original del bot/chat/mensaje con el resultado de la operación y su respuesta preparada. Aplicar commit antes de confirmar y reintentar la entrega sin repetir la mutación. No deduplicar por contenido textual ni guardar copias innecesarias del texto en recibos.
  - **Finaliza cuando:** repetir una entrega después de cambiar de libro mantiene el resultado original; dos mensajes distintos con texto igual siguen siendo dos notas distintas.

- [x] **T009 — Persistir aclaraciones y confirmaciones.**
  - **Depende de:** T006, T007, T008.
  - **Archivos:** `plugins/margen/margen/conversations.py`, `tests/test_conversations.py`.
  - **Trabajo:** implementar selección numérica, operación a continuar, `/confirmar` y `/cancelar`, conjunto/versión de objetivos y revalidación previa. Impedir reemplazar una interacción pendiente por otra. Admitir `/nota texto` durante la aclaración y mantenerla abierta; tratar el texto sin comando como respuesta.
  - **Finaliza cuando:** reiniciar no pierde la interacción, un número inválido no crea una nota, cancelar no revierte acciones completadas y confirmar nunca afecta a una acción o conjunto diferente del presentado.

- [x] **T010 — Registrar, activar y listar libros.**
  - **Depende de:** T006, T007, T009.
  - **Archivos:** `plugins/margen/margen/books.py`, `tests/test_books.py`.
  - **Trabajo:** implementar `/libro Título | Autor`, `/activar Título` y `/libros`, normalización y duplicados, títulos ambiguos y libros inexistentes. Registrar no activa; activar conserva la selección anterior hasta resolver una ambigüedad.
  - **Finaliza cuando:** el listado identifica el activo o su ausencia, la activación es duradera y no cambia notas anteriores; las selecciones compartidas muestran título y autor.

- [x] **T011 — Guardar notas de texto y emitir referencias.**
  - **Depende de:** T008, T009, T010.
  - **Archivos:** `plugins/margen/margen/notes.py`, `tests/test_capture.py`.
  - **Trabajo:** capturar texto sin comando y `/nota texto`, asociar el libro activo o conservar como pendiente, guardar original/versión inicial y preparar confirmación con referencia y libro/estado. Programar indexación e invalidar resúmenes afectados sin esperar inferencia.
  - **Finaliza cuando:** solo se confirma un guardado tras commit; fallos y pendientes se distinguen; referencias y fechas permanecen estables al reabrir la base.

- [x] **T012 — Resolver la atribución inicial de notas pendientes.**
  - **Depende de:** T009, T010, T011.
  - **Archivos:** `plugins/margen/margen/conversations.py`, `tests/test_pending_assignment.py`.
  - **Trabajo:** asignar una pendiente y activar el libro seleccionado; para varias, activar el libro y presentar sus referencias antes de asignarlas mediante `/confirmar`. Fijar el conjunto presentado e impedir que notas posteriores entren en él.
  - **Finaliza cuando:** rechazar/cancelar conserva las pendientes, una nueva captura usa el libro vigente y la asignación confirmada no cambia notas ajenas al conjunto.

## C. Ciclo de vida de notas

- [x] **T013 — Consultar notas y su historial.**
  - **Depende de:** T011.
  - **Archivos:** `plugins/margen/margen/notes.py`, `tests/test_note_queries.py`.
  - **Trabajo:** implementar `/ver referencia` y `/historial referencia`, mostrando texto vigente, original/versiones cronológicas, libro o estado sin asignar y errores de referencia inexistente.
  - **Finaliza cuando:** la consulta no modifica ni el libro activo ni la nota y distingue de forma inequívoca versión vigente y anteriores.

- [x] **T014 — Corregir el contenido de una nota.**
  - **Depende de:** T013.
  - **Archivos:** `plugins/margen/margen/notes.py`, `tests/test_note_editing.py`.
  - **Trabajo:** implementar `/editar referencia nuevo texto`, conservar originales, actualizar versión y señalar resúmenes afectados; invalidar el embedding anterior y programar el nuevo.
  - **Finaliza cuando:** mantiene referencia, fecha, posición y libro, y el texto vigente se usa para nuevas consultas; los fallos no pierden versiones ni producen una corrección parcial.

- [x] **T015 — Mover notas y asignar pendientes individualmente.**
  - **Depende de:** T012, T014.
  - **Archivos:** `plugins/margen/margen/notes.py`, `tests/test_note_moving.py`.
  - **Trabajo:** implementar `/mover referencia | Título`, destinos ambiguos/inexistentes y asignación individual de pendientes. Conservar referencia/contenido/fecha original y señalar coberturas afectadas de origen y destino.
  - **Finaliza cuando:** no duplica notas ni cambia el libro activo; la nota se ordena por su fecha original en el destino y no se asignan otras pendientes.

- [x] **T016 — Eliminar la nota completa mediante confirmación.**
  - **Depende de:** T009, T015.
  - **Archivos:** `plugins/margen/margen/notes.py`, `tests/test_note_deletion.py`.
  - **Trabajo:** implementar `/eliminar referencia`, vista previa y explicación de alcance, `/confirmar`, borrado de original/versiones/vectores y purga de copias temporales o entregas pendientes con el texto. Conservar resúmenes previos como desactualizados según lo acordado.
  - **Finaliza cuando:** rechazo o error conserva la nota; borrado completo impide recuperarla mediante consultas, historial, búsquedas o nuevos resultados derivados. Explica los límites sobre copias y mensajes anteriores y no cambia el libro activo.

## D. Trabajos y búsqueda local

- [x] **T017 — Ejecutar trabajos largos con estado persistente.**
  - **Depende de:** T008, T009.
  - **Archivos:** `plugins/margen/margen/jobs.py`, `tests/test_jobs.py`.
  - **Trabajo:** guardar operación, propietario, libro y parámetros capturados al iniciarla; separar pendiente/en curso/completado/fallido y proporcionar aviso tras cinco segundos. Mantener disponible la captura y ofrecer recuperación visible sin reejecuciones mutables silenciosas.
  - **Finaliza cuando:** cambiar el libro activo no redirige un trabajo iniciado, un fallo queda visible y el aviso de progreso nunca se presenta como resultado completado.

- [ ] **T018 [P] — Preparar el modelo local y su runtime verificable.**
  - **Depende de:** T001, T002, T003.
  - **Archivos:** `plugins/margen/margen/embeddings.py`, `scripts/prepare-search-model.py`, `model-manifest.json`, `requirements-search.lock`, `tests/test_embeddings.py`.
  - **Trabajo:** resolver `intfloat/multilingual-e5-small`, tokenizador y ONNX Runtime CPU para ARM64/Python 3.11; comprobar FastEmbed o preparar conversión ONNX reproducible si no ofrece el modelo. Registrar revisiones/hashes, prefijos, pooling, normalización, dimensión y contexto. Mantener los pesos fuera de Git.
  - **Finaliza cuando:** produce vectores locales de 384 dimensiones con los prefijos correctos, registra dependencias reproducibles y funciona sin red tras preparar artefactos. La equivalencia de una conversión y su funcionamiento ARM64 deben probarse, no deducirse de una importación en otro equipo.

- [x] **T019 — Indexar versiones vigentes sin bloquear la captura.**
  - **Depende de:** T006, T011, T014, T016, T018.
  - **Archivos:** `plugins/margen/margen/indexing.py`, `tests/test_indexing.py`.
  - **Trabajo:** consumir trabajos de índice, fragmentar textos largos con solapamiento y referencia/versión, escribir FTS5/vectores e ignorar trabajos obsoletos. Limitar inicialmente a un trabajador y hasta dos hilos CPU de inferencia.
  - **Finaliza cuando:** no trunca una nota silenciosamente, no publica vectores de una versión eliminada o sustituida y reconstruye el índice desde la base vigente sin acceso externo.

- [x] **T020 — Recuperar y ordenar notas por descripción localmente.**
  - **Depende de:** T004, T017, T019.
  - **Archivos:** `plugins/margen/margen/search.py`, `tests/test_search.py`.
  - **Trabajo:** implementar `/buscar descripción` con candidatos FTS5 y coseno, fusión de posiciones y agrupación por nota. Buscar en todos los libros y pendientes, mostrando texto vigente completo, libro/autor o «Sin libro asignado» y referencia real. Definir la política de relevancia con las muestras, sin forzar coincidencias cuando no haya respaldo.
  - **Finaliza cuando:** ninguna búsqueda llama a OpenRouter; múltiples fragmentos producen una sola nota y los fallos de índice/modelo se distinguen de una búsqueda completa sin resultados. Registrar cobertura incompleta si hay notas aún no indexables.

- [x] **T021 — Paginar la última búsqueda sin repetir resultados.**
  - **Depende de:** T020.
  - **Archivos:** `plugins/margen/margen/search.py`, `tests/test_search_pagination.py`.
  - **Trabajo:** persistir orden/cursor de la última búsqueda, devolver hasta cinco notas inicialmente y por `/mas`, e indicar agotamiento o falta de consulta previa. Revalidar existencia y autorización antes de mostrar resultados posteriores.
  - **Finaliza cuando:** no repite notas, no cambia el libro activo y una nota borrada después de buscar no reaparece por la caché de paginación.

## E. Resúmenes y exportación

- [x] **T022 [P] — Encapsular Haiku mediante la interfaz de Hermes.**
  - **Depende de:** T001, T002, T003.
  - **Archivos:** `plugins/margen/margen/model.py`, `tests/test_model_port.py`.
  - **Trabajo:** conectar la inferencia administrada por Hermes a OpenRouter con `anthropic/claude-haiku-5.5`, verificar parámetros realmente admitidos y manejar tiempo de espera/error. No leer ni refrescar credenciales directamente ni cambiar automáticamente de modelo.
  - **Finaliza cuando:** la prueba de contrato y los dobles de proveedor verifican modelo, parámetros y fallos; la confirmación de acceso real queda reservada a la prueba autorizada de despliegue. El adaptador no se usa para la búsqueda.

- [x] **T023 — Generar y conservar resúmenes con cobertura.**
  - **Depende de:** T004, T013, T017, T022.
  - **Archivos:** `plugins/margen/margen/summaries.py`, `tests/test_summary_generation.py`.
  - **Trabajo:** implementar `/resumen` y `/resumen detallado` con instantánea de todas las notas del libro activo, orden de guardado, fuente/versión y referencia R. Aplicar extensiones orientativas de 300/1.000 palabras, distinguir citas/reflexiones y procesar por bloques contiguos si excede contexto.
  - **Finaliza cuando:** no genera nada al guardar una nota, no incluye otros libros ni fuentes externas y no omite las últimas notas por límites de contexto. Sin libro activo retoma la petición tras seleccionar; sin notas informa sin inventar contenido.

- [x] **T024 — Verificar la cobertura y desactualización de resúmenes.**
  - **Depende de:** T014, T015, T016, T023.
  - **Archivos:** `plugins/margen/margen/summaries.py`, `tests/test_summary_coverage.py`.
  - **Trabajo:** contrastar huella de referencias/versiones/pertenencia y conservar fuentes de notas eliminadas sin copias del original. Integrar cambios nuevos, edición, movimiento y borrado, incluidos los que ocurren durante la generación.
  - **Finaliza cuando:** un resumen cuya cobertura ya no corresponde se marca desactualizado, incluso al terminar su generación, y nunca se regenera automáticamente.

- [x] **T025 — Listar y abrir resúmenes conservados.**
  - **Depende de:** T009, T024.
  - **Archivos:** `plugins/margen/margen/summaries.py`, `tests/test_summary_queries.py`.
  - **Trabajo:** implementar `/resumenes` y `/ver_resumen referencia`, con libro, referencia, fecha, modalidad y estado. Continuar el listado tras seleccionar libro cuando no haya activo; manejar listas vacías y referencias inexistentes.
  - **Finaliza cuando:** las consultas muestran contenido conservado sin generar ni modificar resúmenes, advierten su desactualización y una consulta por referencia no cambia el libro activo.

- [x] **T026 — Exportar el libro activo en Markdown.**
  - **Depende de:** T009, T013, T017.
  - **Archivos:** `plugins/margen/margen/exports.py`, `tests/test_exports.py`.
  - **Trabajo:** implementar `/exportar` con instantánea de título/autor, notas vigentes completas y referencias en orden original. Generar un archivo temporal y gestionar su ciclo de vida; seleccionar libro y continuar si no hay activo.
  - **Finaliza cuando:** no incluye notas ajenas, no genera archivos vacíos ni un resumen y no altera el libro activo ya seleccionado. El archivo queda disponible para entrega y se retira tras entrega o fallo definitivo.

## F. Integración con el perfil y Telegram

- [x] **T027 [P] — Implementar el adaptador de entrada y autorización.**
  - **Depende de:** T001, T003, T007.
  - **Archivos:** `plugins/margen/margen/ingress.py`, `tests/test_ingress.py`.
  - **Trabajo:** registrar la fábrica nativa pública de Telegram y normalizar mensaje original, perfil/bot, chat y remitente. Filtrar al usuario/chat privado autorizado antes de acceder al dominio. Separar mensajes, comandos de Margen, comandos nativos y callbacks de Hermes sin capturarlos indebidamente.
  - **Finaliza cuando:** un tercero no alcanza ningún servicio de datos, un evento consumido no se despacha dos veces y los IDs originales están disponibles para deduplicación. No importar Hermes ni ejecutar plugins durante el diagnóstico.

- [x] **T028 [P] — Implementar el transporte de respuestas y archivos.**
  - **Depende de:** T001, T003, T008, T017.
  - **Archivos:** `plugins/margen/margen/delivery.py`, `tests/test_delivery_recovery.py`.
  - **Trabajo:** entregar texto, documentos Markdown y avisos de progreso al chat de origen; dividir respuestas largas en partes ordenadas, incluidas cinco notas extensas. Conectar la bandeja de salida con reintentos acotados y errores visibles.
  - **Finaliza cuando:** una caída tras guardar reintenta la respuesta sin crear otra nota, una entrega parcial no vuelve a mandar las partes ya confirmadas por el transporte y los errores inciertos no se anuncian como éxito. No garantizar entrega exactamente una vez si la respuesta de Telegram se pierde.

- [x] **T029 — Conectar intenciones y servicios en un único despacho.**
  - **Depende de:** T012, T016, T021, T025, T026, T027, T028.
  - **Archivos:** `plugins/margen/margen/commands.py`, `plugins/margen/__init__.py`, `tests/test_command_dispatch.py`.
  - **Trabajo:** conectar todos los comandos y texto sin comando con autorización, aceptación idempotente, estado de interacción y respuesta. Registrar menú/formatos según T001, sin saltarse el adaptador original al ejecutar comandos mutables.
  - **Finaliza cuando:** cada comando aprobado tiene un recorrido observable y la operación pendiente se reanuda tras seleccionar, sin otra petición ni respuestas convertidas accidentalmente en notas.

- [x] **T030 — Preparar manifiesto e identidad del perfil.**
  - **Depende de:** T029.
  - **Archivos:** `plugins/margen/plugin.yaml`, `profile/SOUL.md`, `profile/config.example.yaml`.
  - **Trabajo:** declarar las interfaces/capacidades/dependencias usadas realmente y el alcance del perfil. Incluir configuración ilustrativa de modelo y rutas, sin tokens ni IDs reales. Alinear la identidad con memoria de lectura, fidelidad y ausencia de regeneraciones automáticas.
  - **Finaliza cuando:** el plugin solo actúa en Margen, su manifiesto coincide con lo registrado y las plantillas no habilitan ni cambian los perfiles existentes. Las instrucciones de personalidad no sustituyen las garantías del código.

## G. Verificación del producto

- [x] **T031 — Verificar fallos, concurrencia y persistencia del dominio.**
  - **Depende de:** T016, T017, T024.
  - **Archivos:** `tests/test_persistence_recovery.py`, `tests/test_concurrency.py`.
  - **Trabajo:** cubrir reentrega tras cambio de libro, caída antes/después de commit, almacenamiento lleno/error, confirmación con versiones modificadas, nota nueva durante asignación en bloque y reinicio con interacción pendiente. Comprobar serialización de mutaciones por propietario.
  - **Finaliza cuando:** se cumplen CC-04 y los invariantes de integridad sin confirmaciones falsas, pérdida de originales ni modificaciones de notas ajenas. No basta con una prueba que reproduzca la implementación.

- [ ] **T032 — Ejecutar el contrato integrado de Hermes/Telegram en aislamiento.**
  - **Depende de:** T030, T031.
  - **Archivos:** `tests/test_hermes_contract.py`, `tests/test_telegram_integration.py`, `docs/compatibility.md`.
  - **Trabajo:** cargar manifiesto y registro en una raíz de prueba, comprobar identidad de perfil, orden de manejadores y ausencia de colisiones, autorización y despachos con eventos PTB de prueba. Verificar errores locales sin caída al agente general que pueda confirmar una nota ficticiamente.
  - **Finaliza cuando:** la integración pasa sobre las versiones objetivo o se documenta una incompatibilidad y se revisa el plan antes de desplegar. No confundir estos eventos simulados con un bot operativo.

- [x] **T033 — Preparar y aplicar la medición de rendimiento.**
  - **Depende de:** T028, T032.
  - **Archivos:** `scripts/measure-margen.py`, `docs/validation.md`.
  - **Trabajo:** instrumentar admisión, escritura y aceptación de respuesta por Telegram, sin registrar notas. Medir CR-01 en condiciones normales documentadas y CR-02 con una operación controlada que supere cinco segundos, sin bloquear la captura.
  - **Finaliza cuando:** existe un procedimiento reproducible; las mediciones locales y las pendientes del bot real están separadas. Las muestras en Raspberry y con Telegram real se completan en T040 y no se inventan para cerrar esta tarea.

- [ ] **T034 — Evaluar búsqueda local en la Raspberry.**
  - **Depende de:** T004, T018, T021.
  - **Archivos:** `scripts/evaluate-search.py`, `docs/search-evaluation.md`.
  - **Trabajo:** ejecutar el conjunto fijo en ARM64, medir aciertos, consumo de RAM y tiempos; comprobar búsqueda sin red, notas pendientes y largas, versiones obsoletas y borrados. Registrar modelo/hashes, parámetros y referencias recuperadas.
  - **Finaliza cuando:** CC-01 alcanza al menos 8/10 entre los primeros cinco y las referencias cumplen CC-03. Si falla, ajustar recuperación local y reevaluar con evidencia; no habilitar búsqueda externa ni cambiar el modelo aprobado silenciosamente.

- [x] **T035 [P] — Preparar la evaluación de fidelidad de resúmenes.**
  - **Depende de:** T004, T023, T024.
  - **Archivos:** `scripts/evaluate-summaries.py`, `docs/summary-evaluation.md`.
  - **Trabajo:** construir la rúbrica de CC-02 y verificar fuente, cobertura, orden, citas/reflexiones, vacíos y extensión. Preparar captura de resultados del modelo real, sin una comparación exacta de cadenas ni un evaluador automático como única garantía.
  - **Finaliza cuando:** se puede revisar cada idea contra su fuente y la rúbrica rechaza afirmaciones sin respaldo. La ejecución real mediante OpenRouter y la revisión de sus resultados se completan en T040.

## H. Backup y entrega para despliegue

- [x] **T036 — Crear una instantánea consistente y su manifiesto.**
  - **Depende de:** T006, T016, T024.
  - **Archivos:** `plugins/margen/margen/backup.py`, `scripts/backup-margen.py`, `tests/test_backup_snapshot.py`.
  - **Trabajo:** usar la API de backup de SQLite, cerrar/verificar la copia, generar manifiesto y hash y publicar la instantánea actual sin reemplazar la última verificada por una parcial. Preparar la transferencia al destino solo si el volumen esperado está montado. No copiar una base abierta con WAL como sustituto de este procedimiento.
  - **Finaliza cuando:** con datos de prueba la copia es íntegra y el fallo de generación/transferencia conserva la anterior; la ausencia del montaje aborta sin escribir en el NVMe bajo la carpeta de backup. No repara ni intenta montar el SSD.

- [x] **T037 — Preparar restauración en cuarentena.**
  - **Depende de:** T036.
  - **Archivos:** `scripts/restore-margen.py`, `tests/test_backup_restore.py`, `docs/operations.md`.
  - **Trabajo:** restaurar a una ubicación de prueba, comprobar hash/esquema/integridad y reconstruir permisos. Desactivar trabajos, entregas y confirmaciones restaurados. Comparar eliminaciones posteriores cuando haya registro; si no lo hay, explicar la limitación y exigir revisión antes de activar una recuperación histórica.
  - **Finaliza cuando:** una copia probada recupera datos legibles sin enviar mensajes ni reintroducir automáticamente notas eliminadas. El script no sobrescribe por defecto una base activa.

- [x] **T038 — Preparar el despliegue y la integración de backup por escrito.**
  - **Depende de:** T030, T032, T036, T037.
  - **Archivos:** `deployment/hermes-gateway-margen.service.example`, `docs/deployment.md`, `docs/operations.md`.
  - **Trabajo:** describir perfil nuevo, instalación de extensión, credenciales locales, usuario/chat autorizado, ruta de datos y unidad systemd de usuario `hermes-gateway-margen.service`, con arranque persistente y reinicio tras fallo. Documentar verificación de lingering y ejecución con el venv Python 3.11.15. Preparar la integración de la instantánea en el backup semanal, condicionada a revisar sus fuentes/exclusiones y sin ampliar `--delete` ni crear retención histórica adicional.
  - **Finaliza cuando:** hay pasos reproducibles de instalación, validación y reversión; la incidencia externa del montaje está identificada sin convertirse en tarea de reparación. La plantilla no arranca nada ni incorpora tokens y respeta los demás gateways.

- [ ] **T039 — Empaquetar una entrega reproducible.**
  - **Depende de:** T018, T030, T032, T038.
  - **Archivos:** `requirements-runtime.lock`, `scripts/package-margen.py`, `docs/release-manifest.json`.
  - **Trabajo:** fijar las dependencias resueltas compatibles con ARM64/Python 3.11 y las revisiones de artefactos; generar paquete y manifiesto con hashes, esquema y revisión Hermes objetivo. Separar código, modelos descargables y datos del usuario.
  - **Finaliza cuando:** el paquete se instala en una raíz limpia de prueba, carga con el contrato validado y no contiene bases, notas, credenciales ni cachés personales. El backup del usuario no es un artefacto de distribución.

- [ ] **T040 — Validar el despliegue controlado con el canal real.**
  - **Depende de:** T033, T034, T035, T039.
  - **Archivos de evidencia:** `docs/validation.md`, `docs/summary-evaluation.md`, `docs/deployment.md`.
  - **Destino futuro:** perfil y bot de prueba en Raspberry; posterior perfil `margen` bajo `/home/claw/.hermes/profiles/margen` y unidad de usuario dedicada.
  - **Trabajo:** una vez iniciada la implementación y disponible el despliegue autorizado, verificar token exclusivo y autorización con IDs locales. Probar todos los comandos con notas ficticias, archivo Markdown, respuestas largas, aviso de progreso, recuperación tras reinicio del gateway y arranque persistente. Completar CR-01/02, CC-02 con Haiku real y CC-03. No reiniciar toda la Raspberry sin una autorización de operación que incluya ese efecto sobre otros servicios.
  - **Finaliza cuando:** la evidencia real respalda cada afirmación de funcionamiento y rendimiento. La validación del backup externo se declara pendiente si su montaje sigue sin resolver; no se marca como superada ni se repara dentro de esta tarea. Se deja explícito si el entorno está listo solo para pruebas o para uso personal con recuperación validada.

- [ ] **T041 — Cerrar la entrega y la trazabilidad.**
  - **Depende de:** T031, T032, T034, T035, T037, T040.
  - **Archivos:** `docs/validation.md`, `docs/operations.md`, `README.md`.
  - **Trabajo:** consolidar comandos, arquitectura, instalación, limitaciones, resultados de pruebas y estado del backup. Revisar RF-01 a RF-44, CR-01/02 y CC-01 a CC-04 frente a evidencias y actualizar el estado de cada tarea sin marcar dependencias externas como resueltas.
  - **Finaliza cuando:** el usuario puede distinguir funcionalidad entregada, pruebas ejecutadas y condiciones operativas pendientes, y dispone del procedimiento de consulta, recuperación y reversión sin acceder al historial de esta conversación.

## Evidencia de ejecución (2026-10-18)

Las casillas completadas acreditan implementación y comprobaciones locales de sus criterios; no implican activar el perfil ni superar las puertas de destino. Las dependencias que requieren el entorno objetivo siguen abiertas y bloquean la aceptación operativa de los módulos relacionados.

| Tareas | Evidencia / estado |
| --- | --- |
| T001–T017 | Contrato estático, paquete, fixtures y núcleo transaccional; pruebas de dominio, reinicio y concurrencia. |
| T018 | Parcial: modelo oficial preparado con hashes, vectores reales y runtime Python 3.11.15; falta Linux ARM64 y contraste de referencia. |
| T019–T021 | Indexación y búsqueda implementadas, pruebas de vigencia y paginación; evaluación local 9/10. Aceptación en destino depende de T018/T034. |
| T022–T031 | Adaptador Hermes, resúmenes, exportación y transporte probados con dobles; PTB 22.8 real, sin bot conectado. |
| T032 | Parcial: el gestor real de Hermes en Docker ARM64 registra los 17 comandos y la fábrica Telegram; falta verificar despacho con el canal conectado. |
| T033 | Medición reproducible local y aviso >5 s ensayado; datos reales reservados a T040. |
| T034 | Parcial: 9/10 en Docker Raspberry Linux ARM64 sin red; preflight con negativas vacías y métricas/versiones recogidas. Faltan vigencia/borrado y concurrencia en destino. |
| T035 | Rúbrica y casos preparados; inferencia real/revisión humana en T040. |
| T036–T038 | Instantánea/cuarentena verificadas con datos de prueba y transferencia con montaje simulado; documentación y unidad ilustrativa. SSD real pendiente, sin reparación. |
| T039 | Parcial: lock, empaquetador y manifiesto; falta validación integrada e instalación limpia en Linux ARM64. |
| T040–T041 | Pendientes de entorno/canal real y cierre operativo. |

La suite local usa Python 3.11.15 y PTB 22.8. Los detalles y límites están en `docs/validation.md`; no se presenta la simulación como despliegue real.

## Trazabilidad de requisitos

| Requisitos o decisión | Tareas principales |
| --- | --- |
| RF-01, RF-16, RF-18, RF-20, RF-21, RF-39: libros y selecciones | T007, T009, T010, T029, T032 |
| RF-02, RF-03, RF-04, RF-05, RF-06, RF-13, RF-19: captura y activo | T006, T008, T011, T012, T031 |
| RF-22, RF-40, RF-41, RF-43, RF-44: interacción y confirmación | T009, T012, T016, T029, T031 |
| RF-11, RF-24, RF-25, RF-26, RF-27, RF-34, RF-35, RF-42: ciclo de notas | T013, T014, T015, T016, T024, T037 |
| RF-07, RF-08, RF-12, RF-14, RF-15, RF-23: generación de resúmenes | T017, T022, T023, T024, T035, T040 |
| RF-36, RF-37, RF-38: resúmenes conservados | T024, T025, T029 |
| RF-09, RF-10, RF-17, RF-30, RF-31, RF-32: búsqueda | T018, T019, T020, T021, T034 |
| RF-28, RF-33: exportación | T017, T026, T028, T040 |
| RF-29: comandos inválidos | T007, T027, T029, T032 |
| CR-01, CR-02: tiempos y progreso | T008, T017, T028, T033, T040 |
| CC-01: recuperación entre los cinco primeros | T004, T020, T034 |
| CC-02: fidelidad y cobertura semántica | T004, T023, T024, T035, T040 |
| CC-03: referencias correctas | T003, T013, T020, T021, T025, T034, T040 |
| CC-04: integridad | T006, T008, T016, T031, T032 |
| Búsqueda local aprobada; resúmenes externos aprobados | T018, T020, T022, T030, T034 |
| Perfil/bot exclusivo, autorización y arranque | T027, T029, T030, T038, T040 |
| Recuperación y límite de alcance sobre el SSD de backup | T036, T037, T038, T040, T041 |

## Dependencias y puntos de revisión

1. **Contrato confirmado:** T001 debe resolver la viabilidad de integración antes de construir el adaptador. Las coincidencias de símbolos del diagnóstico no bastan para superarlo.
2. **Captura y ciclo de notas:** T005–T016 establecen la integridad del producto antes de exponerlo en el bot real.
3. **Trabajo independiente posible:** T004, T018, T022 y T027 pueden avanzar tras sus dependencias respectivas. T028 también puede avanzar cuando estén los contratos de salida y trabajos. Coordinar cualquier edición compartida de archivos de infraestructura.
4. **Puerta de integración:** T029–T032 unen las capacidades y verifican los riesgos de entrada, estado y entrega.
5. **Puerta de entrega:** T034, T039 y T040 requieren evidencia del entorno objetivo. La activación personal no se confunde con una prueba simulada ni con una copia externa aún no verificada.

## Revisión y aprobación de Tasks

- [x] Tareas identificadas y ordenadas sin dependencias cíclicas.
- [x] Archivos y criterios de finalización concretos por tarea.
- [x] Cobertura explícita de RF-01 a RF-44, CR-01/02 y CC-01 a CC-04.
- [x] Trabajo paralelizable marcado sin implicar su ejecución ahora.
- [x] Implementación, validación y límites de despliegue diferenciados.
- [x] Reparación del montaje del SSD externo fuera de alcance.
- [x] Aprobación del usuario antes de pasar a Handoff.

## Historial de aprobación

| Versión | Fecha | Estado | Cambio |
| --- | --- | --- | --- |
| 1.0.0 | 2026-10-18 | Aprobado | el usuario aprueba las 41 tareas y autoriza continuar con Handoff; no se ha iniciado su implementación. |
