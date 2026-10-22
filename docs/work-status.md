# Estado de entrega de Margen

Revisión: 2026-10-22. **El trabajo completo no está terminado.** La implementación 0.1.0 y el despliegue definitivo Docker están entregados y arrancados; la aceptación operativa continúa abierta. El usuario autorizó Docker como destino definitivo.

| Bloque | Comprobado | Pendiente |
| --- | --- | --- |
| Implementación | Libros, activo, notas, referencias, historial, búsqueda local, resúmenes, movimiento, borrado, exportación. 72 pruebas locales pasan. | No equivale a verificar cada requisito con el canal real. |
| Integración Raspberry | Docker ARM64, runtime 3.14.7, plugin, Telegram, OpenRouter, Haiku y modelo E5 local. | Resto del contrato integrado y reproducibilidad completa. |
| Búsqueda | 9/10 en el conjunto fijo sin red; consultas por descripción, entre libros y exclusión de una nota borrada en Telegram. | Referencia de pooling, contexto extenso, paginación y demás casos de vigencia/concurrencia. |
| Resúmenes | Breve/detallado, alcance por libro, matices, cita ficticia, reflexión personal, fuentes, conservación y desactualización. | Diez casos completos, notas extensas y concurrencia real. El fallo aislado anterior no tiene causa identificada. |
| Integridad visible | Edición con original, cancelación, borrado confirmado, movimiento, reinicio y conservación de datos. | Reentrega y fallos de destino no ensayados todavía en el canal real. |
| Autorización | Restricciones configuradas y pruebas automatizadas. | Ensayo real de otra cuenta: usuario no dispone de ella. |
| Rendimiento | Aviso real de progreso; mediciones locales del dominio. | Latencia Telegram medida y captura durante inferencia real (CR-01/02). |
| Recuperación | Snapshot y restauración en cuarentena verificadas en Raspberry, con base activa conservada. | Copia externa al SSD y recuperación ante pérdida del NVMe; no se modifica su montaje. |
| Docker definitivo | Preflight, daemon enabled, copia previa, promoción y estado healthy; Telegram confirma libros, activo, nota y resúmenes conservados, y nueva captura. | Arranque real tras reinicio del anfitrión (no ejecutado) y aceptación ampliada. |

## Trabajo inmediato

1. La puesta en marcha y su recorrido básico en Telegram están verificados; no repetir la promoción ni borrar los datos de prueba de forma implícita.
2. Completar las puertas de aceptación aún abiertas. No reiniciar el anfitrión como prueba implícita de Docker.
3. Mantener explícitos los límites de concurrencia real, rendimiento, contexto extenso y copia externa antes de cerrar T040/T041.

## Tareas que siguen abiertas

T018 (runtime/modelo y referencia), T032 (contrato integrado restante), T034 (búsqueda restante), T039 (reproducibilidad e instalación limpia), T040 (aceptación real) y T041 (cierre de entrega). Las casillas marcadas en `tasks.md` acreditan implementación/comprobaciones descritas, no aceptación operativa total.

La base de evidencia está en `validation.md`; las pruebas de calidad, en `summary-evaluation.md` y `search-evaluation.md`. Los comandos en la Raspberry fueron ejecutados por el usuario y se revisó su salida; esta sesión no accedió remotamente al equipo ni utilizó sus credenciales.
