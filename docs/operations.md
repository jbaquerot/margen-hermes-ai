# Operación y recuperación

## Comandos

| Acción | Formato |
| --- | --- |
| Registrar sin activar | `/libro Título \| Autor` |
| Activar para próximas notas | `/activar Título` |
| Ver libros | `/libros` |
| Capturar | texto libre o `/nota texto` |
| Consultar / historial | `/ver N-UUID`, `/historial N-UUID` |
| Corregir conservando original | `/editar N-UUID nuevo texto` |
| Reasignar sin cambiar activo | `/mover N-UUID \| Título` |
| Eliminar con confirmación | `/eliminar N-UUID`, después `/confirmar` |
| Resumir notas del activo | `/resumen`, `/resumen detallado` |
| Consultar resúmenes conservados | `/resumenes`, `/ver_resumen R-UUID` |
| Buscar en todos los libros y pendientes | `/buscar descripción`, `/mas` |
| Exportar notas del activo | `/exportar` |
| Resolver interacción | número/título, `/confirmar`, `/cancelar` |

Una nota sin activo queda conservada pendiente y abre selección. Una sola se asigna al elegir; varias requieren confirmación de las referencias presentadas. Las nuevas quedan fuera de ese lote. Durante una aclaración, usar `/nota` para capturar; texto libre se interpreta como respuesta. Un fallo de inferencia no afecta a notas guardadas. Un error de almacenamiento nunca confirma el guardado.

El historial contiene el original y las revisiones. Mover o editar invalida resúmenes afectados; no los regenera. Eliminar borra original, revisiones y vectores; se conservan resúmenes previos marcados desactualizados. No se retiran copias ya enviadas por Telegram ni archivos exportados. El borrado es lógico en SQLite, no una garantía forense sobre soportes físicos.

## Entrega e interrupciones

Cada mensaje original tiene un recibo persistente y una respuesta pendiente. Reentregar el mismo evento no repite la mutación, aunque haya cambiado el activo. Dos mensajes nuevos con texto igual son dos notas. Se conserva el progreso de fragmentos que Telegram confirmó; un corte entre aceptación remota y registro local puede repetir una respuesta, porque Telegram no ofrece una transacción conjunta con SQLite. No se promete entrega exactamente una vez.

Al siguiente mensaje autorizado tras arrancar, se reintentan entregas conservadas. Trabajos de inferencia pendientes/en curso de una ejecución anterior quedan fallidos y no se regeneran automáticamente: solicitar de nuevo. Las aclaraciones normales sobreviven a reinicios. La cuarentena de restauración las descarta expresamente.

## Instantánea actual

Usar el Python que tenga instalado el paquete Margen; no copiar una base abierta y sus WAL mediante rsync como sustituto de una instantánea consistente.

```bash
umask 077
python scripts/backup-margen.py \
  --database /home/claw/.hermes/profiles/margen/plugin-data/margen/data.db \
  --snapshot /home/claw/.hermes/profiles/margen/plugin-data/margen/current.tar
```

El archivo contiene exclusivamente `data.db` y un manifiesto con fecha, esquema y hash. Se publica de forma atómica tras verificar SQLite; un fallo anterior conserva la instantánea previa. Es la copia actual, sin nuevas series históricas.

Para transferir, añadir `--mount /mnt/backup-ssd --expected-source /dev/disk/by-uuid/IDENTIFICADOR_VERIFICADO_LOCALMENTE`. El programa exige montaje exacto, identidad del volumen y descriptores anclados al dispositivo; vuelve a leer los bytes antes de reemplazar `/mnt/backup-ssd/backups/margen-current.tar`. Si falta el montaje aborta, sin escribir bajo esa carpeta del NVMe. No monta ni repara nada.

El diagnóstico previo mostró el SSD sin montar. La transferencia real, su compatibilidad exFAT y la cobertura del cron existente **no están validadas**. Revisar localmente `/home/claw/scripts/backup-claw.sh`, fuentes, exclusiones y orden antes de integrar esta instantánea con el cron semanal (sábado 04:00). Evitar que un rsync posterior con `--delete` borre el archivo independiente. No ampliar sus borrados ni retención como efecto secundario de Margen. Una instantánea local no demuestra recuperación desde el SSD.

## Cuarentena

```bash
python scripts/restore-margen.py /ruta/margen-current.tar /ruta/nueva/cuarentena \
  --current-database /ruta/base-actual/data.db
```

El destino debe ser nuevo. Se verifican miembros permitidos, hash, esquema e integridad; se eliminan trabajos, entregas, sesiones de búsqueda y confirmaciones restaurados. No se inicia un bot ni se sobrescribe una base activa. Si se aporta una base actual legible, su registro de eliminaciones evita reintroducir esas referencias. Sin un registro posterior disponible, el programa **no puede saber** qué notas se borraron después: `REVIEW_REQUIRED.txt` exige revisar antes de activar cualquier recuperación histórica. Los resúmenes conservados se marcan desactualizados.

Revisar datos legibles, referencias, propietario, permisos y eliminaciones antes de una sustitución operativa. Las credenciales y el modelo se configuran por separado. No restaurar directamente sobre un perfil en ejecución.
