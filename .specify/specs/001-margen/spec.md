# Especificación funcional de Margen

- **Versión:** 1.0.0
- **Estado:** Aprobada por el usuario — Specify y Clarify completadas
- **Fecha:** 2026-10-18
- **Edición pública:** nombres personales e inventario ajeno a Margen omitidos; sin cambios funcionales.
- **Usuario:** usuario individual, para uso personal
- **Constitución de referencia:** [constitution.md](../../memory/constitution.md), versión 1.0.0

## Objetivo y valor

Conservar las notas de lectura del usuario y ayudarle a recordar lo leído mediante resúmenes y recuperación de notas a partir de descripciones. La experiencia debe permitir alternar entre varios libros sin mezclar sus notas.

## Decisiones confirmadas por el usuario

1. La entrada inicial será mediante mensajes de texto por Telegram.
2. Cada libro se registrará con título y autor.
3. Registrar un libro no lo activa: la activación requiere una petición aparte.
4. Las notas se asignarán al libro activo hasta que el usuario lo cambie.
5. Cada guardado correcto se confirmará indicando el libro al que corresponde la nota.
6. Si no hay libro activo, la nota se conservará pendiente y Margen preguntará a qué libro corresponde.
7. Resolver esa asignación mediante la selección de un libro también lo activará para las siguientes notas. La asignación individual mediante `/mover` mantiene el libro activo, según la decisión 44.
8. Los resúmenes se generarán solo a petición del usuario.
9. Por defecto, incluirán todas las notas guardadas del libro seleccionado, en el orden en que se guardaron.
10. La búsqueda por descripción abarcará todos los libros por defecto.
11. Las peticiones se realizarán mediante los comandos explícitos definidos en este documento; los mensajes de texto sin comando se usarán para capturar notas de lectura, salvo durante una aclaración pendiente, según la decisión 48.
12. El comando `/resumen` generará un resumen breve por defecto y `/resumen detallado` generará un resumen detallado. Ambas modalidades usarán el libro activo; no admiten un libro como argumento.
13. El comando de registro será `/libro Título | Autor`, con título y autor separados por `|`; no activará el libro registrado.
14. El comando de activación será `/activar Título`. Si varios libros comparten ese título, Margen pedirá una aclaración antes de cambiar el libro activo.
15. El comando de búsqueda será `/buscar descripción` y buscará notas en todos los libros por defecto.
16. Cada resultado de búsqueda mostrará el texto completo de la nota, el título y autor del libro y una referencia que permita recuperar la nota.
17. El comando `/libros` listará los libros registrados e indicará cuál está activo.
18. El usuario confirma que se mantienen ambas formas de captura: texto sin comando y `/nota texto`. Ambas añaden la nota al libro activo y reciben la misma confirmación de guardado. El uso de `/nota` es opcional.
19. Si se intenta registrar un libro con el mismo título y autor que uno existente, Margen avisa de que ya está registrado y no crea un duplicado ni cambia el libro activo.
20. Si `/activar Título` no corresponde a ningún libro registrado, Margen indica cómo registrarlo con `/libro Título | Autor` y mantiene el libro activo actual; si no había ninguno, continúa sin libro activo.
21. Si se acumulan varias notas sin libro activo, al seleccionar un libro Margen pide confirmación antes de asignarle todas las pendientes. La selección activa el libro para las siguientes notas, pero no atribuye automáticamente el conjunto pendiente.
22. Si se solicita un resumen y no hay libro activo, Margen pide seleccionar uno y después genera el resumen solicitado, conservando la modalidad breve o detallada.
23. El comando `/editar referencia nuevo texto` permite corregir una nota identificada por su referencia. Margen conserva el original y señala los resúmenes que queden desactualizados por la corrección; no los regenera automáticamente.
24. El comando `/mover referencia | Título` permite cambiar el libro asignado a una nota sin cambiar el libro activo.
25. El comando `/ver referencia` muestra el texto vigente completo de una nota y el título y autor del libro al que pertenece.
26. El comando `/eliminar referencia` muestra primero la nota y solicita confirmación explícita antes de borrarla. Sin confirmación, la nota se conserva.
27. El comando `/exportar` permite descargar las notas del libro activo en un archivo Markdown, incluyendo título, autor y referencias de las notas, en orden de guardado.
28. Cada confirmación de guardado incluye la referencia de la nota para poder consultarla, editarla, moverla o eliminarla. Las notas conservadas pendientes de asignación también reciben una referencia, indicando claramente su estado.
29. Los comandos desconocidos o incompletos no se guardan como notas ni ejecutan la operación solicitada. Margen explica el problema y orienta sobre el uso correcto de los comandos.
30. `/buscar descripción` muestra inicialmente hasta cinco coincidencias ordenadas por relevancia y permite solicitar más resultados si los hay.
31. Las búsquedas incluyen las notas pendientes de asignación y las identifican como «Sin libro asignado», sin inventar título ni autor.
32. El comando `/mas` muestra hasta cinco resultados adicionales de la última búsqueda, sin repetir los ya mostrados y manteniendo el orden por relevancia.
33. Si se solicita `/exportar` sin libro activo, Margen pide seleccionar uno y después continúa con la exportación sin exigir repetir el comando. Si el libro no tiene notas, lo comunica sin generar un archivo vacío.
34. Al mover una nota a otro libro, se conserva su fecha original de guardado, que determina su posición en el orden de las notas del libro de destino.
35. El comando `/historial referencia` muestra el original y las versiones corregidas de una nota en orden cronológico.
36. Al confirmar `/eliminar referencia`, se eliminan la nota y todo su historial de versiones, incluido el texto original. La vista previa debe advertir de ese alcance antes de solicitar confirmación.
37. Los resúmenes anteriores afectados por la eliminación se conservan como desactualizados. El borrado de una nota no elimina retroactivamente la información incluida en resúmenes o archivos ya enviados por Telegram ni en copias descargadas; Margen debe explicar esta limitación.
38. El comando `/resumenes` lista los resúmenes guardados del libro activo, mostrando fecha, modalidad y estado, sin generar uno nuevo.
39. Cada resumen guardado tiene una referencia, visible al generarlo y en `/resumenes`. El comando `/ver_resumen referencia` permite consultar el resumen guardado e indica si está desactualizado.
40. Si se solicita `/resumenes` sin libro activo, Margen pide seleccionar uno y después muestra su listado de resúmenes sin exigir repetir el comando.
41. Cuando varios libros compartan título, Margen presenta opciones numeradas con título y autor. El usuario elige respondiendo con el número; esa respuesta se interpreta como selección y no se guarda como nota.
42. El comando `/cancelar` abandona una selección o confirmación pendiente sin ejecutar la acción que esperaba respuesta ni borrar las notas ya conservadas. No revierte acciones completadas.
43. El comando `/confirmar` acepta una eliminación o la asignación en bloque de notas pendientes previamente presentada para confirmación. El comando no se guarda como nota.
44. `/mover referencia | Título` también permite asignar individualmente una nota pendiente a un libro registrado, sin cambiar el libro activo. Esta operación explícita se distingue de seleccionar un libro en el flujo inicial de asignación, que sí lo activa para las siguientes notas.
45. Al solicitar confirmación para asignar varias notas pendientes, Margen muestra sus referencias y el libro de destino. `/confirmar` afecta únicamente a ese conjunto, sin incorporar notas recibidas posteriormente.
46. Para resumir otro libro, el usuario debe activarlo primero con `/activar Título` y después solicitar `/resumen` o `/resumen detallado`; no se añade una sintaxis de selección de libro a los comandos de resumen.
47. La extensión orientativa del resumen breve es de hasta 300 palabras y la del detallado, de hasta 1.000 palabras, ajustadas a la cantidad de notas y sin alargar artificialmente el contenido.
48. Mientras Margen espere una aclaración, el texto sin comando se interpreta como respuesta a esa pregunta y no se guarda como nota. Para registrar una nota nueva durante ese intercambio, el usuario usa `/nota texto`; esta nota sigue las reglas del libro activo o de conservación pendiente, sin resolver por sí misma la aclaración.
49. El volumen previsto es de cinco libros al año, con un número de notas variable según el libro. Esta previsión no constituye un límite de libros ni fija una cantidad de notas por libro.
50. El objetivo es confirmar el guardado de una nota en menos de cinco segundos en condiciones normales. Si un resumen, una búsqueda o una exportación tarda más de cinco segundos, Margen indica que sigue trabajando, sin afirmar que la operación ha terminado.
51. La validación de calidad usará notas de ejemplo: la búsqueda deberá recuperar la nota esperada entre los cinco primeros resultados en al menos ocho de diez consultas; los resúmenes deberán recoger las ideas principales identificadas en las notas, respetar su orden y no incluir afirmaciones sin respaldo; todas las referencias deberán recuperar la nota correcta.

## Historias de usuario y aceptación

### HU-01. Registrar y activar libros

Como usuario, quiero registrar libros y elegir cuál está activo para alternar mis lecturas sin mezclar notas.

- Dado un título y un autor, cuando registro el libro, queda disponible para su selección sin cambiar el libro activo existente.
- Al enviar `/libro Título | Autor` con ambos datos, Margen registra el libro y confirma su título y autor, sin activarlo. Si no había libro activo, sigue sin haberlo.
- Si el título y autor ya corresponden a un libro registrado, Margen informa de que ya existe, sin crear otro registro ni modificar el libro activo.
- Dado un libro registrado, cuando pido activarlo, Margen confirma su identidad y lo usa para las siguientes notas.
- Al enviar `/activar Título`, si el título identifica inequívocamente un libro registrado, Margen lo activa y confirma su título y autor.
- Si `/activar Título` no encuentra el libro entre los registrados, Margen informa de ello y muestra cómo registrarlo mediante `/libro Título | Autor`. No lo registra ni lo activa automáticamente y conserva la selección anterior, incluida la ausencia de libro activo.
- Si varios libros comparten el título indicado en `/activar`, Margen pide aclaración y mantiene el libro activo anterior hasta resolver la selección. Si no había libro activo, continúa sin haberlo.
- Las selecciones ambiguas de libro, incluida la de `/mover`, se resuelven mostrando opciones numeradas con título y autor. Una respuesta con un número válido selecciona únicamente la opción correspondiente y continúa la operación pendiente, sin crear una nota. Un número fuera de las opciones no resuelve la selección ni se guarda como nota.
- Dado que cambio de libro activo, las notas anteriores conservan su atribución.
- Al enviar `/libros`, Margen muestra el título y autor de cada libro registrado y señala cuál está activo. Si no hay libro activo o no hay libros registrados, lo indica expresamente.

### HU-02. Capturar notas

Como usuario, quiero enviar una nota de texto y recibir confirmación de su guardado y del libro al que se ha asignado.

- Dado un libro activo, cuando envío una nota y se guarda correctamente, Margen confirma el guardado e identifica el libro y la referencia de la nota; por ejemplo: «Nota guardada en Título del libro. Referencia: N-001» (formato de referencia ilustrativo).
- Al enviar `/nota texto` con un libro activo, Margen conserva el texto que sigue al comando como contenido de la nota, sin incluir el prefijo `/nota`, y confirma su guardado indicando el libro.
- Si envío `/nota texto` sin libro activo, se aplica el mismo flujo de conservación pendiente y solicitud de asignación que a una nota sin comando.
- Si el guardado falla, Margen comunica el fallo sin afirmar que la nota se ha conservado.
- Sin un libro activo, la nota se conserva como pendiente de asignación y Margen pregunta por el libro. La respuesta distingue ese estado del guardado con atribución definitiva.
- La confirmación de conservación de una nota pendiente incluye su referencia y deja claro que todavía no se ha asignado a un libro.
- Si envío un comando desconocido o uno sin los datos obligatorios, Margen informa del problema sin guardarlo como nota ni modificar las notas o el libro activo. Para un comando conocido muestra su formato correcto; para uno desconocido indica los comandos disponibles sin atribuirle una intención inventada.
- Durante una aclaración pendiente, el texto sin comando se trata como respuesta a la pregunta, sin crear una nota. Si no resuelve la aclaración, Margen explica qué respuesta necesita y mantiene la interacción pendiente.
- Durante ese intercambio, `/nota texto` permite guardar una nota nueva: se atribuye al libro activo o se conserva pendiente si no hay uno. La captura no resuelve ni cancela por sí misma la aclaración en curso.
- Cuando identifico inequívocamente un libro registrado para la nota pendiente, Margen asigna la nota y activa ese libro para las siguientes notas, confirmando ambas acciones.
- Si hay varias notas pendientes, al seleccionar un libro Margen pide confirmación para asignarle todas ellas y no las atribuye en bloque sin esa confirmación. El libro seleccionado queda activo para las siguientes notas.
- La solicitud de confirmación identifica las referencias de las notas pendientes incluidas y el libro de destino. Las notas recibidas después no se incorporan al conjunto presentado; siguen el flujo de captura correspondiente al libro activo en ese momento.
- Al confirmar la asignación del conjunto pendiente, Margen asigna esas notas al libro seleccionado y confirma el resultado. Si rechazo la asignación en bloque, las notas siguen pendientes.
- Un reintento de entrega del mismo mensaje no crea otra nota inadvertidamente.

### HU-03. Resumir un libro

Como usuario, quiero pedir un resumen de mis notas de un libro para recordar sus ideas sin releer todos los mensajes.

- Solo una petición de resumen inicia su generación; registrar un libro o una nota no la desencadena automáticamente.
- Por defecto, el resumen de un libro seleccionado usa todas sus notas guardadas y sigue el orden de guardado.
- Dado un libro activo, cuando envío `/resumen`, Margen resume todas las notas guardadas del libro activo en su orden de guardado. Para resumir otro libro, primero debo activarlo mediante `/activar Título`.
- `/resumen` produce una síntesis breve de las ideas principales; `/resumen detallado` desarrolla las ideas con mayor profundidad y conserva más matices relevantes de las notas.
- Las extensiones orientativas son de hasta 300 palabras para el resumen breve y hasta 1.000 para el detallado. No hay una extensión mínima: la longitud debe ajustarse a las notas disponibles, sin relleno ni contenido inventado para alcanzar una cifra.
- Ambas modalidades abarcan todas las notas guardadas del libro seleccionado y mantienen su orden; el nivel de detalle no modifica el libro ni el conjunto de notas utilizado.
- Si envío `/resumen` o `/resumen detallado` y no hay libro activo, Margen solicita seleccionar uno. Tras resolver la selección, continúa con el resumen sin exigir repetir la petición y mantiene la modalidad solicitada. Si el libro no tiene notas, informa de ello.
- El resultado identifica el libro, permite conocer qué notas abarca y explicita que resume las notas disponibles.
- Al generar y guardar un resumen, Margen muestra su referencia para poder consultarlo posteriormente con `/ver_resumen referencia`.
- El resumen no incorpora notas de otros libros ni inventa citas, páginas o contenido para completar vacíos.
- Si el libro no tiene notas, Margen lo comunica sin generar un resumen ficticio.

### HU-04. Encontrar notas por descripción

Como usuario, quiero describir una idea que recuerdo para encontrar las notas relacionadas aunque no recuerde las palabras exactas ni el libro.

- Una búsqueda sin restricción explícita de libro consulta las notas de todos los libros, independientemente del libro activo.
- Al enviar `/buscar descripción`, Margen busca notas relacionadas con esa descripción entre todos los libros, sin exigir las palabras exactas ni conocer el título; por ejemplo, `/buscar cómo influyen los hábitos en la identidad`.
- Cada coincidencia muestra el texto vigente completo de la nota, el título y autor del libro y una referencia que permite recuperar esa nota. Las versiones anteriores se consultan mediante `/historial`.
- También se incluyen las notas pendientes de asignación: cada coincidencia muestra su texto completo, su referencia y la indicación «Sin libro asignado» en lugar de título y autor. Consultarlas no les asigna un libro ni cambia el libro activo.
- Si hay varias coincidencias plausibles, Margen las presenta como posibles correspondencias.
- La primera respuesta muestra hasta cinco coincidencias, ordenadas de mayor a menor relevancia para la descripción. Si existen más resultados, Margen lo indica y permite solicitarlos, manteniendo el texto completo, el libro y la referencia de cada nota.
- Al enviar `/mas`, Margen muestra hasta cinco coincidencias adicionales de la última búsqueda, sin repetir las anteriores y manteniendo el orden por relevancia. Si no hay una búsqueda previa o se han agotado sus resultados, lo indica sin inventar coincidencias ni guardar el comando como nota.
- Si no encuentra coincidencias respaldadas por las notas, lo indica sin inventar referencias.

### HU-05. Corregir una nota

Como usuario, quiero corregir una nota mediante su referencia sin perder el original y saber qué resúmenes han quedado desactualizados.

- Al enviar `/editar referencia nuevo texto` con una referencia válida y un texto de reemplazo, Margen actualiza el contenido vigente de esa nota y confirma la corrección, identificando la nota y su libro.
- La corrección conserva el texto original y no cambia la atribución al libro ni la posición de la nota en el orden de guardado.
- Los resúmenes conservados que incluyan la versión anterior de la nota quedan señalados como desactualizados. No se regeneran automáticamente.
- Los nuevos resúmenes y las búsquedas usan el contenido vigente de la nota, manteniendo la referencia para recuperarla.
- Si la referencia no identifica una nota existente o falta el texto de reemplazo, Margen informa del problema sin modificar ninguna nota.
- Al enviar `/historial referencia` con una referencia válida, Margen muestra el texto original y las versiones corregidas en orden cronológico, identificando cuál es la vigente. Si no hubo correcciones, muestra únicamente el original y lo indica.
- Consultar el historial no modifica la nota ni el libro activo. Si la referencia no existe, Margen lo comunica sin inventar versiones.

### HU-06. Corregir el libro de una nota

Como usuario, quiero mover una nota a su libro correcto sin cambiar el libro que tengo activo.

- Al enviar `/mover referencia | Título` con una referencia válida y un libro de destino registrado e inequívoco, Margen cambia la atribución de la nota y confirma la referencia y los libros de origen y destino.
- La operación conserva el contenido y la referencia de la nota; no crea una copia ni cambia el libro activo.
- Si la referencia corresponde a una nota pendiente de asignación, `/mover referencia | Título` la asigna individualmente al libro indicado y confirma el resultado, sin asignar otras notas pendientes ni cambiar el libro activo. La confirmación indica que antes estaba sin libro asignado.
- La nota conserva su fecha original de guardado y se sitúa según ella entre las notas del libro de destino. La fecha del movimiento no sustituye a la fecha de guardado para ordenar notas, resúmenes o exportaciones.
- Si el título corresponde a varios libros, Margen solicita una aclaración antes de mover la nota. Si la referencia o el libro de destino no existen, comunica el problema sin modificar la atribución.
- Los resúmenes conservados cuya cobertura quede afectada por el cambio de libro se señalan como desactualizados; no se regeneran automáticamente.

### HU-07. Consultar una nota por su referencia

Como usuario, quiero recuperar una nota concreta mediante su referencia para consultar su contenido vigente y el libro al que pertenece.

- Al enviar `/ver referencia` con una referencia válida, Margen muestra la referencia, el texto vigente completo y el título y autor del libro asociado.
- Si la nota está pendiente de asignación, muestra su texto e indica ese estado sin inventar un libro asociado.
- Si la referencia no existe, Margen lo indica sin mostrar contenido inventado.
- Consultar una nota no modifica su contenido, su atribución ni el libro activo.

### HU-08. Eliminar una nota con confirmación

Como usuario, quiero revisar la nota que voy a eliminar y confirmar la operación antes de que se borre.

- Al enviar `/eliminar referencia` con una referencia válida, Margen muestra la referencia, el texto vigente completo y el libro asociado, o su estado pendiente de asignación, y pide confirmación explícita.
- Antes de solicitar la confirmación, Margen advierte de que el borrado incluye el texto original y todo el historial de versiones de la nota.
- Antes de la confirmación, la nota permanece conservada. Si rechazo la eliminación, no se borra.
- Tras confirmar y completar correctamente el borrado, Margen confirma qué nota se ha eliminado. Si la operación falla, informa del fallo sin afirmar que se ha completado.
- Una eliminación completada borra la nota, su original y todas las versiones corregidas. La nota deja de estar disponible mediante `/ver`, `/historial`, las búsquedas y las nuevas exportaciones o resúmenes de Margen. Los resúmenes anteriores pueden conservar información derivada de ella según las reglas siguientes.
- Si la referencia no existe, Margen lo indica sin modificar otras notas.
- La operación no cambia el libro activo. Los resúmenes conservados cuya cobertura quede afectada se señalan como desactualizados y no se regeneran automáticamente.
- Los resúmenes anteriores afectados se conservan señalados como desactualizados, sin regenerarlos automáticamente. La explicación previa al borrado debe aclarar que estos pueden seguir conteniendo información derivada de la nota.
- El borrado no retira ni modifica retroactivamente los resúmenes y archivos ya enviados por Telegram o las copias descargadas. Margen debe explicar esta limitación sin afirmar que se han borrado esas copias.

### HU-09. Exportar las notas de un libro

Como usuario, quiero descargar las notas del libro activo en Markdown para conservarlas y consultarlas fuera de Margen.

- Al enviar `/exportar` con un libro activo que tiene notas, Margen entrega un archivo Markdown descargable con el título y autor del libro y el texto vigente completo y la referencia de cada nota, en orden de guardado.
- La exportación abarca todas las notas del libro activo y no incluye notas de otros libros.
- Exportar no modifica las notas ni el libro activo y no genera un resumen.
- Si se solicita `/exportar` sin libro activo, Margen pide seleccionar un libro y, tras resolver la selección, continúa con la exportación sin exigir repetir el comando.
- Si el libro seleccionado no tiene notas, Margen lo indica y no genera un archivo vacío.
- Si la exportación falla, Margen informa del problema sin afirmar que el archivo se ha entregado.

### HU-10. Consultar el listado de resúmenes guardados

Como usuario, quiero ver los resúmenes anteriores de mi libro activo y saber si están actualizados sin solicitar una nueva generación.

- Al enviar `/resumenes` con un libro activo, Margen identifica el libro y lista sus resúmenes guardados con referencia, fecha de generación, modalidad breve o detallada y estado actualizado o desactualizado respecto de las notas vigentes.
- Los resúmenes desactualizados permanecen en el listado y se distinguen claramente de los actualizados.
- Si el libro activo no tiene resúmenes guardados, Margen lo indica sin generar uno.
- Si envío `/resumenes` sin libro activo, Margen pide seleccionar un libro y después muestra sus resúmenes sin exigir repetir la petición. Si el libro seleccionado no tiene resúmenes, lo indica sin generar uno.
- Consultar el listado no genera ni modifica resúmenes y no cambia el libro activo.
- Al enviar `/ver_resumen referencia` con una referencia válida, Margen muestra el contenido completo del resumen guardado, su referencia, libro, fecha, modalidad y estado. Si está desactualizado, lo advierte expresamente sin actualizarlo ni regenerarlo.
- Si la referencia no identifica un resumen existente, Margen informa del problema sin generar contenido nuevo. Consultar un resumen por referencia no cambia el libro activo.

### HU-11. Cancelar una interacción pendiente

Como usuario, quiero abandonar una selección o confirmación pendiente sin perder mis notas.

- Al enviar `/cancelar` durante una selección o confirmación pendiente, Margen cierra esa interacción, confirma la cancelación y no ejecuta la acción que esperaba respuesta.
- Las notas ya guardadas se conservan; las pendientes de asignación continúan pendientes. No se revierte una activación ni otra acción ya completada.
- Si la selección cancelada correspondía a un resumen, una exportación o un listado, la petición interrumpida no continúa automáticamente.
- Si no hay una interacción pendiente, Margen lo indica sin modificar datos ni guardar el comando como nota.
- Para aceptar una eliminación o la asignación en bloque, el usuario envía `/confirmar` tras revisar la acción presentada. Margen aplica únicamente la acción pendiente de confirmación y comunica el resultado; `/cancelar` permite rechazarla sin ejecutarla.
- Si se envía `/confirmar` sin una acción pendiente de confirmación, Margen lo indica sin modificar datos ni crear una nota.

## Requisitos funcionales

| ID | Requisito |
| --- | --- |
| RF-01 | Registrar libros mediante `/libro Título \| Autor`, con ambos datos obligatorios, y confirmar el registro sin activarlos automáticamente. |
| RF-02 | Mantener la selección del libro activo hasta un cambio solicitado por el usuario, incluida la activación al resolver una nota pendiente. |
| RF-03 | Conservar las notas de texto originales y su atribución al libro correspondiente. |
| RF-04 | Confirmar cada guardado correcto e identificar el libro de destino y la referencia de la nota. Si se conserva pendiente de asignación, mostrar su referencia y ese estado sin atribuirle un libro. |
| RF-05 | Conservar como pendiente una nota recibida sin libro activo y solicitar su asignación. |
| RF-06 | Al resolver la selección de libro del flujo inicial de asignación pendiente, asignar la nota y activar el libro indicado para futuras notas. La asignación individual mediante `/mover` sigue RF-42 y no cambia el libro activo. |
| RF-07 | Generar resúmenes únicamente cuando el usuario los solicite. |
| RF-08 | Resumir por defecto todas las notas guardadas del libro seleccionado siguiendo su orden de guardado. |
| RF-09 | Permitir buscar notas a partir de una descripción, en todos los libros por defecto. |
| RF-10 | Mostrar en cada resultado de búsqueda el texto completo de la nota, el título y autor del libro y una referencia verificable para recuperarla. En las notas pendientes, sustituir título y autor por «Sin libro asignado». |
| RF-11 | Permitir consultar, corregir, exportar y solicitar la eliminación de las notas conforme a la Constitución y a los flujos y comandos definidos en esta especificación. |
| RF-12 | Distinguir citas identificadas por el usuario, reflexiones personales e interpretaciones del asistente. |
| RF-13 | Distinguir las peticiones mediante comandos explícitos y admitir notas mediante texto sin comando o `/nota texto`. No guardar los comandos como contenido de las notas; en `/nota texto`, guardar únicamente el texto de la nota. |
| RF-14 | Usar el libro activo como destino de `/resumen` y `/resumen detallado`, sin admitir un libro como argumento; para resumir otro, seleccionarlo primero mediante `/activar Título`. |
| RF-15 | Generar un resumen breve con `/resumen` (hasta 300 palabras orientativas) y uno detallado con `/resumen detallado` (hasta 1.000 palabras orientativas), manteniendo la cobertura y el orden acordados y ajustando la extensión a las notas sin relleno. |
| RF-16 | Activar un libro mediante `/activar Título` y pedir aclaración antes de cambiar la selección si varios libros comparten el título. |
| RF-17 | Buscar notas mediante `/buscar descripción`, con todos los libros como ámbito por defecto. |
| RF-18 | Listar los libros registrados mediante `/libros`, mostrando título y autor e identificando el libro activo, o indicando su ausencia. |
| RF-19 | Admitir `/nota texto` para añadir una nota al libro activo, confirmar el guardado identificando el libro y conservarla pendiente de asignación si no hay libro activo. |
| RF-20 | Evitar registrar otro libro con el mismo título y autor: informar de que ya está registrado y mantener el libro activo. |
| RF-21 | Ante `/activar Título` sin un libro registrado que corresponda, indicar cómo registrarlo sin crear un libro ni cambiar la selección activa. |
| RF-22 | Cuando haya varias notas pendientes, pedir confirmación antes de asignarlas todas al libro seleccionado; conservarlas pendientes si no se confirma. |
| RF-23 | Si se solicita un resumen y no hay libro activo, solicitar su selección y continuar después con la modalidad de resumen solicitada. |
| RF-24 | Corregir una nota mediante `/editar referencia nuevo texto`, conservando el original, su referencia, libro y orden de guardado; señalar como desactualizados los resúmenes que incluyan la versión anterior, sin regenerarlos automáticamente. |
| RF-25 | Cambiar la atribución de una nota mediante `/mover referencia \| Título`, conservando su contenido, referencia y fecha original de guardado, que determina su orden en el libro de destino, sin duplicarla ni cambiar el libro activo; señalar los resúmenes cuya cobertura quede desactualizada. |
| RF-26 | Consultar una nota mediante `/ver referencia`, mostrando su referencia, texto vigente completo y título y autor del libro, o su estado pendiente de asignación, sin modificar la nota ni el libro activo. |
| RF-27 | Eliminar una nota y todo su historial, incluido el original, mediante `/eliminar referencia` solo después de mostrarla, advertir de ese alcance y recibir confirmación explícita; confirmar el borrado únicamente si se completa y señalar los resúmenes afectados como desactualizados, sin cambiar el libro activo. |
| RF-28 | Exportar mediante `/exportar` todas las notas del libro activo como archivo Markdown descargable, con título, autor, texto vigente completo y referencias de las notas, en orden de guardado, sin modificar las notas ni el libro activo. |
| RF-29 | Rechazar los comandos desconocidos o incompletos sin guardarlos como notas ni modificar datos; explicar el problema y mostrar el formato correcto o los comandos disponibles, según corresponda. |
| RF-30 | Mostrar inicialmente hasta cinco coincidencias de búsqueda ordenadas por relevancia e indicar y permitir consultar más resultados cuando existan. |
| RF-31 | Incluir las notas pendientes de asignación en las búsquedas, identificándolas como «Sin libro asignado», sin asignarlas ni cambiar el libro activo. |
| RF-32 | Permitir consultar más resultados mediante `/mas`, en grupos de hasta cinco de la última búsqueda, sin repetir los mostrados y manteniendo el orden por relevancia; informar si no hay búsqueda previa o más resultados. |
| RF-33 | Ante `/exportar` sin libro activo, pedir seleccionar uno y continuar después con la exportación; si el libro no tiene notas, informar sin generar un archivo vacío. |
| RF-34 | Consultar el original y las versiones corregidas mediante `/historial referencia`, en orden cronológico e identificando la versión vigente, sin modificar la nota ni el libro activo. |
| RF-35 | Conservar los resúmenes anteriores afectados por una eliminación como desactualizados y explicar que estos, los resúmenes y archivos ya enviados por Telegram y las copias descargadas pueden seguir conteniendo información de la nota eliminada. |
| RF-36 | Listar mediante `/resumenes` los resúmenes guardados del libro activo, con referencia, fecha, modalidad y estado actualizado o desactualizado, sin generar ni modificar resúmenes. |
| RF-37 | Asignar una referencia a cada resumen guardado, mostrarla al generarlo y permitir consultarlo mediante `/ver_resumen referencia`, con su contenido completo, libro, fecha, modalidad y estado, advirtiendo si está desactualizado y sin regenerarlo ni cambiar el libro activo. |
| RF-38 | Ante `/resumenes` sin libro activo, solicitar la selección de un libro y mostrar después su listado de resúmenes sin exigir repetir el comando ni generar un resumen nuevo. |
| RF-39 | Resolver las selecciones ambiguas de libro mediante opciones numeradas con título y autor; interpretar la respuesta numérica como selección para continuar la operación pendiente, sin guardarla como nota. |
| RF-40 | Permitir abandonar una selección o confirmación pendiente mediante `/cancelar`, sin ejecutar la acción pendiente, borrar notas conservadas ni revertir acciones completadas. |
| RF-41 | Aceptar mediante `/confirmar` únicamente la eliminación o asignación en bloque presentada y pendiente de confirmación; informar sin modificar datos si no hay una acción que confirmar. |
| RF-42 | Permitir asignar individualmente una nota pendiente mediante `/mover referencia \| Título`, sin asignar otras notas pendientes ni cambiar el libro activo. |
| RF-43 | Delimitar la asignación en bloque mostrando las referencias incluidas y el libro de destino antes de confirmar; aplicar `/confirmar` únicamente a ese conjunto, sin incorporar notas posteriores. |
| RF-44 | Durante una aclaración, interpretar el texto sin comando como respuesta sin guardarlo como nota y permitir capturar una nota mediante `/nota texto`, sin resolver ni cancelar por ello la aclaración pendiente. |

## Condiciones de calidad heredadas de la Constitución

- Conservar originales y mantener la trazabilidad de resúmenes y resultados de búsqueda.
- Evitar mezclas entre libros, duplicados por reintento y confirmaciones falsas de guardado.
- Hacer visibles los estados pendientes y los fallos, con una vía de recuperación.
- Proteger el acceso a las notas y solicitar confirmación ante una eliminación irreversible de originales.
- Permitir identificar la cobertura de un resumen conservado cuando se añadan o corrijan notas.
- Resolver ambigüedades con aclaraciones breves, de una en una.

## Límites iniciales

- Las notas de voz y las fotografías quedan fuera del formato inicial solicitado.
- No se contemplan resúmenes automáticos.
- El propósito es trabajar con las notas personales; no se presupone acceso al texto completo de los libros.
- Las decisiones técnicas se reservan para la fase Plan.

## Volumen previsto de uso

- Uso personal del usuario, con una previsión aproximada de cinco libros al año y posibilidad de leer varios simultáneamente.
- La cantidad de notas depende del libro; no se ha fijado una cifra por libro ni debe deducirse una a partir de esta estimación.
- El volumen previsto sirve para dimensionar la validación y la planificación; no es una cuota de uso.

## Criterios de rendimiento

- **CR-01 — Guardado:** el objetivo es confirmar el guardado de una nota en menos de cinco segundos en condiciones normales, tanto para texto sin comando como para `/nota texto`. Nunca se confirma un guardado antes de su éxito para cumplir el objetivo de tiempo.
- **CR-02 — Operaciones largas:** si un resumen, una búsqueda o una exportación supera cinco segundos, Margen comunica que sigue trabajando y después informa del resultado o del fallo.
- Las condiciones normales y los puntos de medición de extremo a extremo se concretarán en Plan para que las comprobaciones sean reproducibles.

## Criterios de calidad y éxito

- **CC-01 — Recuperación:** en diez consultas de prueba basadas en descripciones de notas existentes, la nota esperada debe aparecer entre las cinco primeras coincidencias en al menos ocho consultas. Cada consulta tendrá identificada previamente su nota esperada.
- **CC-02 — Fidelidad y cobertura:** los resúmenes de las notas de ejemplo deben recoger las ideas principales previamente identificadas, respetar el orden de las notas y no incluir afirmaciones sin respaldo en ellas. La revisión se realiza sobre el significado, sin exigir una redacción idéntica.
- **CC-03 — Referencias:** el 100 % de las referencias a notas devueltas en las pruebas debe recuperar la nota correcta. No se aceptan referencias inventadas ni atribuciones a otro libro.
- **CC-04 — Integridad:** los escenarios de aceptación deben verificar que los reintentos no duplican una misma entrega, los fallos no producen confirmaciones falsas de guardado y las operaciones sobre una nota no modifican otras notas inadvertidamente.

Estos son criterios de aceptación por verificar durante la implementación; no representan resultados de pruebas ya ejecutadas.

## Supuestos y detalles para Plan

- No quedan preguntas de producto abiertas de las tratadas en esta fase. El usuario ha aprobado la especificación funcional completa el 2026-10-18.
- El conjunto concreto de notas de ejemplo, consultas y sus resultados esperados se preparará en Plan para aplicar los criterios aprobados, sin convertir su tamaño en una cuota de uso.
- Las condiciones normales de servicio, los puntos de medición de los tiempos y los mecanismos de integración, conservación y recuperación se detallarán en Plan.
- Los números de referencia de los ejemplos son ilustrativos; la planificación concretará un formato estable que permita identificar inequívocamente notas y resúmenes.

## Revisión y aceptación

- [x] Propósito y usuario identificados.
- [x] Decisiones confirmadas separadas de cuestiones pendientes.
- [x] Historias principales con escenarios verificables.
- [x] Coherencia con la Constitución 1.0.0.
- [x] Flujos principales y casos límite tratados descritos con resultados observables.
- [x] Criterios de éxito medibles acordados.
- [x] Ambigüedades tratadas resueltas en la fase Clarify; detalles de validación y ejecución reservados para Plan.
- [x] Aprobación del usuario antes de pasar a Plan.

## Historial de aprobación

| Versión | Fecha | Estado | Cambio |
| --- | --- | --- | --- |
| 1.0.0 | 2026-10-18 | Aprobada | el usuario aprueba la especificación funcional tras completar Specify y Clarify. |
