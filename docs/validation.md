# Estado de implementación y validación

Fecha: 2026-10-18. Versión de implementación: 0.1.0; esquema SQLite: 1. Documentos de producto aprobados: 1.0.0. **Entrega local para pruebas; no desplegada ni validada para uso personal en la Raspberry.**

## Hallazgo posterior: laboratorio Docker (2026-10-19)

Se preparó `deployment/docker/compose.yaml` con el Dockerfile oficial de la misma revisión, volumen exclusivo, sin puertos ni servicios del anfitrión montados. `docker compose config --quiet` valida su estructura; la construcción y ejecución están pendientes porque el daemon Docker local no estaba disponible. Docker y Compose v5.6.0 ya están instalados en la Raspberry; `hello-world` ARM64 funciona según la salida del usuario. La construcción de Hermes sigue pendiente. Ver `deployment/docker/README.md`.

La revisión del Dockerfile y `pyproject.toml` confirmó que la imagen oficial utiliza Python 3.14 y que 3.11 solo es un puente de instalación/actualización, con las dependencias principales excluidas. Las pruebas de dominio que pasaron en 3.11.15 siguen siendo evidencia válida del código de Margen, pero **no acreditan que Hermes completo funcione en un entorno nuevo con 3.11**. El dato del diagnóstico del anfitrión debe contrastarse con el runtime efectivo antes de cerrar T018/T032/T039. El laboratorio Docker no modifica por sí mismo la decisión de despliegue nativo ni el venv existente.

## Evidencia ejecutada

| Comprobación | Resultado y límite |
| --- | --- |
| Suite Python 3.11.15 + PTB 22.8 | 56 pruebas pasan, incluida inspección AST de la revisión Hermes objetivo. macOS ARM64, entorno temporal independiente. |
| Captura, estados y persistencia | Commit/rollback, identidad original, reentrega concurrente, reinicio, lote congelado, versiones y borrado. |
| Telegram aislado | Objetos Update y filtros PTB reales, transporte simulado, autorización antes de datos y detención del despacho en errores. |
| Trabajos largos | Prueba controlada de 5,1 s: aviso de progreso y captura concurrente; no se bloquea esperando inferencia. |
| Búsqueda con artefactos E5 reales | 9/10 entre primeros cinco; ambas consultas negativas sin resultados. Ver `search-local-result.json`. Validación Linux/Raspberry pendiente. |
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
- T032: carga integrada del plugin en una raíz Hermes aislada de la revisión objetivo. El contexto simulado no cierra esta puerta.
- T034: repetir CC-01 en Raspberry, >=8/10, referencias verificadas y recursos sin interferir con los otros perfiles.
- T039: completar instalación limpia **en destino**, contrato integrado y compatibilidad de todas las dependencias de Hermes. El paquete local y su manifiesto ya se pueden revisar.
- T040: bot exclusivo, autorización real, OpenRouter/Haiku, revisión humana de CC-02, reinicio de gateway, arranque persistente y CR-01/02.
- T041: cierre operativo tras esas pruebas. La transferencia y recuperación del SSD externo quedan pendientes mientras no se disponga de montaje válido; su reparación queda fuera del alcance.

No hay acceso remoto a la Raspberry ni credenciales en esta sesión. No se han instalado perfiles, modificado servicios ni ejecutado inferencia remota. Las limitaciones se mantienen visibles en la lista de tareas.
