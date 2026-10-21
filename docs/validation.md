# Estado de implementación y validación

Inicio: 2026-10-18; actualización: 2026-10-20. Versión de implementación: 0.1.0; esquema SQLite: 1. Documentos de producto aprobados: 1.0.0. **Laboratorio Docker desplegado en Raspberry; uso personal todavía en validación.**

## Laboratorio Docker en Raspberry (2026-10-19)

El laboratorio usa la revisión Hermes fijada y un volumen independiente. La imagen oficial prepara Python 3.14; `pyproject.toml` admite 3.11 únicamente como puente de instalación/actualización. Las pruebas de Margen en 3.11.15 siguen siendo evidencia del dominio, pero no acreditan un Hermes nuevo sobre ese runtime. El laboratorio no modifica el venv nativo ni cambia automáticamente el objetivo de despliegue aprobado.

| Comprobación aportada por el usuario | Evidencia |
| --- | --- |
| Docker y Compose | `hello-world` ARM64 correcto; Compose v5.6.0. |
| Imagen y CLI Hermes | Imagen `ba77c43768f6`; Python 3.14.7, SDK OpenAI 2.24.0, método Docker y banner `vunknown (2026.9.24)`. |
| Perfil | `margen` creado en `/opt/data/profiles/margen`, sin alias ni skills. |
| Plugin instalado | Fuente fijada a `e98479f9a444e0e06116f766ae671b4e5aae22b4`. Instalación inicial desactivada y sin dependencias; Plugin Doctor pasó sus comprobaciones básicas en un perfil temporal. Su guarda de perfil impide interpretar ese resultado como prueba de los 17 comandos. |
| Dependencias admitidas | PM resolvió e instaló las dependencias; `Plugin margen enabled`, salida `0`; el siguiente arranque seleccionó el entorno `current`. |
| Proveedor | El asistente guardó OpenRouter, `anthropic/claude-haiku-5.5`, esfuerzo `low`. Primeros resúmenes reales recibidos; falta completar la rúbrica humana de T040. |
| Telegram y permisos | Bot de pruebas, allowlist de un único propietario y home channel privado. Permisos propios de Margen guardados y leídos selectivamente; no se publican token ni IDs. |
| Modelo E5 | Descarga con hashes verificados, salida `0`, ruta dentro del volumen de laboratorio. |
| Búsqueda real sin red | `compose.offline.yaml` con `network_mode: none`: **9/10, aarch64, salida 0**, informe `plugin-data/margen/validation/search-arm64.json`. Cumple el umbral de recuperación del conjunto fijo en el laboratorio. El preflight posterior verificó las dos consultas negativas sin resultados y recogió métricas/versiones. |

El script `scripts/preflight-container-margen.py` comprueba el registro real de los comandos y de la fábrica Telegram en el perfil, compara permisos sin imprimir IDs y recoge versiones/métricas del informe sintético. Puede aplicar el SOUL de Margen guardando el anterior y rechazando sobrescribir una edición posterior. El usuario ejecutó el preflight en la Raspberry: todas las comprobaciones `true`, `soul: applied`, `ok: true`, código `0`. El registro real de los 17 comandos y la fábrica de Telegram está comprobado. Versiones y métricas completas en `docs/docker-preflight-result.json`; sus fechas conservan el UTC observado. El primer comando real del canal se confirmó después, según el ensayo descrito más abajo; falta completar el recorrido y la evaluación semántica ampliada de Haiku.

Limitaciones observadas: Docker descartó el límite de memoria por falta de soporte/configuración de cgroups; no se considera aplicado. Durante la preparación del modelo apareció un `s6-ftrigrd ... Broken pipe`, seguido de finalización correcta; se conserva como observación, sin atribuirle una causa no comprobada. La configuración Compose se valida localmente; el daemon Docker del equipo de desarrollo no está disponible. Ver `deployment/docker/README.md`.

El primer arranque de canal con `hermes -p margen gateway run --no-supervise -v` fue rechazado por la guarda de gateway compartido antes de conectar Telegram (salida aportada por el usuario). La corrección documentada arranca `-p default` dentro del volumen de laboratorio para servir el perfil `margen`; su ejecución y el despacho de `/libros` quedaron confirmados en el ensayo posterior. El código de la revisión fijada carga plugins y conecta adaptadores secundarios dentro del contexto de cada perfil (`gateway/run_adapters.py`). La plantilla nativa de servicio separado queda marcada como no instalable hasta revisar esa integración.

Actualización del ensayo de canal (2026-10-20): el usuario ejecutó el arranque corregido y aportó logs de las 20:27 que enumeran ambos perfiles. En Telegram, `/libros` devolvió exactamente `No hay libros registrados.` y `Sin libro activo.`. Quedan comprobados el arranque compartido y el despacho real de ese comando a Margen. No demuestra todavía captura, inferencia, rechazo de terceros ni recuperación tras reinicio; T032 y T040 siguen abiertas para el recorrido restante.

## Evidencia ejecutada

| Comprobación | Resultado y límite |
| --- | --- |
| Suite Python 3.11.15 + PTB 22.8 | 57 pruebas pasan, incluida inspección AST de la revisión Hermes objetivo. macOS ARM64, entorno temporal independiente. |
| Captura, estados y persistencia | Commit/rollback, identidad original, reentrega concurrente, reinicio, lote congelado, versiones y borrado. |
| Telegram aislado | Objetos Update y filtros PTB reales, transporte simulado, autorización antes de datos y detención del despacho en errores. |
| Trabajos largos | Prueba controlada de 5,1 s: aviso de progreso y captura concurrente; no se bloquea esperando inferencia. |
| Búsqueda con artefactos E5 reales | 9/10 local y 9/10 en Docker Linux ARM64 sin red; código 0. Preflight posterior: ambas negativas vacías, carga 1,997 s y máximo RSS 1.195.552 KiB (aprox. 1,14 GiB). Ver `search-local-result.json` para el ensayo macOS. |
| Resúmenes | Dobles de proveedor: referencias, orden, fragmentos largos, errores y desactualización. Semántica del modelo real pendiente. |
| Backup | API SQLite, manifiesto, integridad y cuarentena; montaje ausente aborta. Transferencia de archivos ensayada con sonda de montaje simulada; fallo conserva copia previa. SSD real pendiente. |
| Dependencias y entrega | Lock con hashes resuelto para Python 3.11/aarch64/glibc 2.28; instalación comprobada en entorno limpio Python 3.11.15 macOS. No demuestra compatibilidad conjunta con Hermes en Linux. |

La suite se ejecutó con:

```bash
HERMES_SOURCE=/ruta/fuentes-hermes-revision-objetivo python -m pytest -q
```

Sin `HERMES_SOURCE`, se omite exclusivamente la inspección estática adicional. Las pruebas no usan credenciales ni un bot real. El archivo fuente de Hermes se obtuvo de la revisión pública exacta; no se incluye en la entrega.

Medición local con 100 notas sintéticas: mediana 0,208 ms, p95 0,308 ms, máximo 1,077 ms para admisión y commit. Son cifras de este equipo, **excluyen** red y aceptación de Telegram. No cierran CR-01 en Raspberry. `scripts/measure-margen.py` permite repetir esa parte sin notas personales. Para CR-01 real, cronometrar desde recepción del Update hasta retorno de `send_message` aceptado por Telegram, conservando solo duraciones e IDs sintéticos; documentar red, carga y tamaño, exigir <5 s en condiciones normales. Para CR-02 real, provocar una operación >5 s, verificar aviso y capturar otra nota mientras sigue activa.

## Trazabilidad funcional

| Requisitos | Implementación / prueba local | Cierre externo pendiente |
| --- | --- | --- |
| RF-01/02/16/18/20/21/39 | `books`, `application`, parser; duplicados, activo, ambigüedad, selección numérica | Recorrido con bot real |
| RF-03/04/05/06/13/19/22/40/41/43/44 | `notes`, interacciones, recibos y transacciones; lote/versiones y reintentos | Recorrido con bot real |
| RF-07/08/12/14/15/23 | `summaries`, `jobs`, adaptador Hermes; instantánea, cobertura y orden formal | CC-02 semántico y acceso real Haiku |
| RF-09/10/17/30/31/32 | `embeddings`, `indexing`, `search`; datos reales del modelo, paginación y texto íntegro | CC-01 y recursos Linux ARM64 |
| RF-11/24/25/26/27/34/35/42 | Ciclo de notas, original/historial, invalidación, confirmación y borrado en cascada | Recorrido con bot real |
| RF-28/33 | Exportación Markdown desde instantánea, documento en memoria y entrega simulada | Descargar archivo real en Telegram |
| RF-29 | Parser estricto; comandos desconocidos/incompletos no crean notas | Recorrido con bot real |
| RF-36/37/38 | Resúmenes conservados con R/fecha/modalidad/estado y selección reanudada | Recorrido con bot real |
| CC-03 | Referencias comprobadas, fuentes retenidas sin impedir borrado, resultados actuales | Repetición en destino y canal |
| CC-04 | Integridad, rollback y serialización concurrente; sin confirmaciones falsas en fallos ensayados | Recuperación real del gateway |
| CR-01/02 | Procedimiento y mediciones locales; progreso >5 s probado | Latencias reales Raspberry/Telegram |

## Puertas pendientes

- T018: probar runtime y artefactos en **Linux aarch64**, sin red durante búsqueda; equivalencia de pooling con referencia del modelo y dependencias del anfitrión.
- T032: el gestor real de Hermes registró los 17 comandos y la fábrica Telegram en Docker ARM64. El despacho real está confirmado para registro, activación, captura, listado, búsqueda, resúmenes, edición, historial y exportación; falta completar el resto de comandos y situaciones de error. El contexto simulado por sí solo no cerraba esta puerta.
- T034: umbral de CC-01 superado en Docker Raspberry (9/10 sin red), negativas y métricas recogidas. Falta completar vigencia/borrado y concurrencia en destino.
- T039: completar instalación limpia **en destino**, contrato integrado y compatibilidad de todas las dependencias de Hermes. El paquete local y su manifiesto ya se pueden revisar.
- T040: bot exclusivo, autorización real, OpenRouter/Haiku, revisión humana de CC-02, reinicio de gateway, arranque persistente y CR-01/02.
- T041: cierre operativo tras esas pruebas. La transferencia y recuperación del SSD externo quedan pendientes mientras no se disponga de montaje válido; su reparación queda fuera del alcance.

No hay acceso remoto a la Raspberry ni credenciales en esta sesión. El usuario ha creado el perfil de laboratorio y configurado proveedor/canal mediante los comandos indicados; se ha probado `/libros` en el bot real; se han recibido ambos modos de resumen; falta completar la evaluación ampliada y el resto del recorrido. El Hermes nativo y sus servicios permanecen fuera de este procedimiento. Las limitaciones se mantienen visibles en la lista de tareas.

## Recorrido inicial de captura y resumen (2026-10-20)

El usuario confirmó mediante respuestas del bot: registro de un libro ficticio sin activación automática, activación explícita, dos notas con referencias distintas (texto libre y `/nota`) y listado del libro activo. Después recibió `/resumen` y `/resumen detallado`, con referencias R distintas, fecha y modalidad correctas, estado actualizado y las dos fuentes en orden. Ambos textos conservan las dos ideas sobre constancia y entorno sin añadir hechos externos. El adaptador de producción exige respuesta OpenRouter del modelo aprobado y no incluye una alternativa de resumen local. Esta es evidencia del recorrido real, no de toda la rúbrica: dos frases no permiten evaluar síntesis extensa, contradicciones, citas ni una diferencia sustancial entre modalidades. No se registran IDs de usuario, credenciales ni el contenido de notas personales.

## Búsqueda, dos libros, versiones y exportación (2026-10-20)

Evidencia aportada por el usuario en Telegram, con datos ficticios:

- Dos consultas por descripción recuperan las notas esperadas. La consulta sobre entorno devuelve esa nota primero; la consulta sobre repetición devuelve únicamente la nota correspondiente.
- Registrar un segundo libro no cambia el activo; activarlo asigna la siguiente nota al segundo libro. Una búsqueda recupera la nota del primero aunque esté activo el segundo.
- El resumen del segundo libro incluye exclusivamente su nota. Al reactivar el primero, se conservan sus resúmenes breve y detallado.
- Editar una nota conserva la versión original y muestra la segunda como vigente en `/historial`. Ambos resúmenes previos quedan desactualizados sin regeneración automática.
- `/ver_resumen` conserva el texto antiguo y advierte de la desactualización. Un nuevo `/resumen` incorpora el matiz editado, conserva ambas fuentes y se presenta actualizado.
- `/exportar` entregó un Markdown que el usuario descargó y adjuntó. Inspección directa del archivo: título y autor correctos, exactamente las dos notas del primer libro en orden de captura, referencias y fechas de guardado; incluye la versión corregida y excluye la nota del segundo libro. El archivo no se incorpora al repositorio.

Estos casos acreditan los recorridos indicados; siguen pendientes reinicio/persistencia en el canal, movimiento, borrado y cancelación, autorización ajena, concurrencia y evaluación semántica ampliada. No se cierra T040 con estos ensayos parciales.

## Incidencia de reinicio del laboratorio (2026-10-20)

El usuario reinició `margen-lab-host-gateway` y el bot dejó de responder. Los logs muestran `prior_state=running action=started` para default, dos mensajes de arranque, detección de un gateway existente y apagado de s6. La combinación de orden principal `--no-supervise` y recuperación automática del slot s6 no mantiene abierto el contenedor tras reinicio. Se añade `compose.gateway.yaml` para usar el flujo oficial supervisado: variable de opt-out a `0`, orden `-p default gateway run` y gracia de apagado de 60 s. Se conserva el mismo volumen y el contenedor previo para diagnóstico. Configuración validada estáticamente; recuperación y reinicio reales pendientes del ensayo en Raspberry. El aviso de vida anterior sin cierre limpio no demuestra OOM: el propio log indica `suspected_oom=False`.

Los logs aportados confirman adicionalmente cuatro llamadas reales `plugin_llm.acomplete` de Margen mediante OpenRouter y el modelo aprobado, correspondientes a los resúmenes ya observados. No se publican IDs ni rutas del canal privado.

## Recuperación y reinicio supervisado confirmados (2026-10-20)

El usuario ejecutó la corrección con `compose.gateway.yaml`: los logs confirman supervisión s6 y conexión Telegram en polling. `/libros` recuperó los dos libros ficticios y el primero activo. Posteriormente reinició `margen-lab-supervised-gateway` con un plazo de apagado de 60 segundos y verificó en Telegram:

- `/libros`: ambos libros conservados, primero activo.
- `/ver`: nota editada conservada con el texto vigente.
- `/resumenes`: tres resúmenes del primero conservados; el último actualizado y los dos anteriores desactualizados.

Pasa el recorrido de recuperación tras reinicio explícito del contenedor con datos en el volumen de laboratorio. No acredita arranque tras reinicio del anfitrión, recuperación ante corte brusco, reentrega concurrente ni copias externas. La ejecución posterior también cierra la incertidumbre de arranque del archivo supervisado registrada en la incidencia anterior; T040 conserva las demás comprobaciones pendientes.

## Cancelación, borrado y movimiento en Telegram (2026-10-20)

Con la nota ficticia del segundo libro, `/eliminar` mostró el texto y pidió confirmación; `/cancelar` conservó la nota, comprobada con `/ver`. En un segundo intento, `/confirmar` devolvió la eliminación y `/ver` respondió que la nota no existe o fue eliminada. Su resumen anterior siguió consultable con advertencia de desactualización. Una búsqueda por dormir/recuperación/ejercicio no devolvió coincidencias tras el borrado. Este recorrido acredita el comportamiento visible; no equivale a inspección forense del almacenamiento.

`/mover` reasignó la nota sobre el entorno del primero al segundo libro conservando su referencia. `/ver` mostró el segundo libro como propietario de la nota y `/libros` mantuvo activo el primero. Pendiente comprobar con resúmenes nuevos la distribución resultante y completar el resto de escenarios de T040.

## Fallo del resumen de matices y diagnóstico seguro (2026-10-20)

Los resúmenes nuevos tras mover y borrar respetaron la distribución vigente: el primero solo constancia, el segundo solo entorno, ambos con su única fuente actual. A continuación, el usuario creó un tercer libro ficticio con tres notas sobre horario fijo, límites de la rigidez y una reflexión personal. `/resumen detallado` devolvió el error genérico y no produjo un resumen. No se considera aprobada esta prueba de calidad.

La consulta acotada a los últimos 15 minutos de logs no mostró una llamada de resumen ni su causa; no permite atribuir el fallo a OpenRouter o al validador. El código anterior ocultaba esa distinción guardando solo `operation_failed`. Se añade diagnóstico cerrado en `jobs.error` y en el logger `margen`: operación, etapa (`generate`/`save`) y código, sin IDs, notas, respuesta del proveedor, mensajes de excepción ni traceback. Los códigos diferencian proveedor, modelo distinto/vacío, JSON, estructura, fuentes, orden, cobertura, reducción/contexto, timeout y almacenamiento; los fallos desconocidos conservan el código genérico. No se relajan las comprobaciones ni se reintenta automáticamente una llamada facturable. El fallo anterior no se puede reconstruir retrospectivamente con esta mejora.

Validación local: **66 pruebas pasan** en Python 3.11.15 con el contrato estático de la revisión Hermes fijada, incluyendo códigos de rechazo y ausencia de contenido privado en logs. Actualización del plugin del laboratorio y repetición real de la prueba pendientes. El plugin instalado seguía fijado a la revisión inicial: un `git pull` del repositorio de trabajo por sí solo no actualiza ese código.

## Repetición satisfactoria del resumen de matices (2026-10-21)

Tras las instrucciones de actualización del plugin, el usuario repitió `/resumen detallado` y aportó un aviso `Sigo trabajando. Las notas guardadas se conservan.` seguido del resumen completado. La revisión del texto compartido confirma las tres ideas en orden y sus tres referencias: atribuye la constancia al autor, conserva el matiz sobre rigidez y la falta de un equilibrio explicado, y distingue explícitamente la experiencia personal. No añade una solución a la tensión ni hechos externos. El resumen aparece como actualizado y de modalidad detallada. El caso de matices pasa en esta repetición; la causa del fallo original sigue desconocida. No se aportó la salida del instalador para confirmar independientemente el SHA efectivo.

El aviso acredita progreso visible durante una operación real, pero la salida compartida no contiene marcas de tiempo del aviso ni una captura concurrente; no cierra por sí sola CR-01/02. Continúan pendientes las pruebas de concurrencia, acceso ajeno, entradas largas/citas y el resto de la rúbrica de T040.

## Nueva nota y conservación del resumen anterior (2026-10-21)

El usuario solicitó un resumen detallado de las tres notas de matices; este terminó antes de enviar la cuarta nota, por lo que el ensayo no demuestra captura concurrente. La cuarta nota se guardó con una referencia nueva. Un resumen posterior incluyó las cuatro notas en orden, separando las dos reflexiones personales de las afirmaciones atribuidas al autor. Al consultar el resumen previo con `/ver_resumen`, este conservó su texto y sus tres fuentes originales y mostró `DESACTUALIZADO: las notas han cambiado.`. Pasa la invalidación por alta de una nota sin regeneración automática ni alteración del resumen conservado. La salida del resumen posterior lo mostraba actualizado al generarse; no se ha vuelto a consultar después.

Pendientes de aceptación real: concurrencia durante inferencia, rechazo de identidad ajena, citas/entradas extensas y el resto de escenarios de T040. No se cierra CR-02 con una secuencia de operaciones terminadas antes de la siguiente captura.

## Cita ficticia y límite de la prueba de autorización (2026-10-21)

El usuario no dispone de otra cuenta de Telegram. El rechazo de una identidad ajena sigue cubierto por las pruebas automatizadas, pero pendiente de ensayo real; no se modifica la allowlist ni se simula una identidad Telegram como sustituto de esa evidencia.

Tras añadir una quinta nota marcada como cita ficticia y sin página, `/resumen detallado` emitió aviso de progreso y completó. El texto compartido conserva literalmente la cita ficticia, la identifica como creada para la prueba y atribuida al autor en la nota, e indica que no hay página. Distingue las dos reflexiones personales, mantiene la tensión sin resolver y presenta las cinco referencias en orden. Este caso pasa la revisión manual de fidelidad, atribución y ausencia de página inventada. No acredita manejo de citas auténticas verificadas ni síntesis de entradas extensas. Concurrencia real y mediciones de latencia siguen pendientes.

## Recuperación local comprobada en Raspberry (2026-10-21)

El usuario ejecutó `snapshot` y `restore` dentro del contenedor supervisado, como usuario `hermes` y con la base del perfil de laboratorio. La salida confirmó instantánea SQLite creada/verificada y restauración en un directorio nuevo `restore-check-*`, sin activar esa copia. Las funciones verifican hash, esquema, integridad y relaciones; la restauración contrasta el registro de eliminaciones actual, purga estados transitorios y marca los resúmenes desactualizados en la copia. La base activa sigue siendo la original.

Este ensayo acredita copia consistente y preparación de recuperación en cuarentena en el runtime Raspberry/Docker. La copia está en el mismo volumen NVMe: no acredita recuperación tras perder el disco, transferencia al SSD externo ni activación del bot sobre una base restaurada. No se publica la copia ni su contenido. La concurrencia manual anterior volvió a terminar el resumen antes de la nueva nota, por lo que sigue pendiente.
