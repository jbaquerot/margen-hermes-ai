# Margen · Hermes AI

Perfil personal de Hermes Agent para conservar notas de lectura por Telegram, generar resúmenes a petición y recuperar notas describiendo una idea.

**Estado:** especificaciones, plan y 41 tareas aprobados. Implementación pendiente.

## Funcionalidad prevista

- Varios libros registrados con título y autor y un libro activo para capturar notas.
- Notas de texto, con o sin `/nota`, confirmación de guardado y referencia estable.
- Resúmenes breves y detallados basados en las notas guardadas.
- Búsqueda semántica local entre libros y notas pendientes de asignación.
- Consulta, edición con historial, cambio de libro y eliminación confirmada.
- Exportación de notas a Markdown.

## Documentación

| Documento | Contenido |
| --- | --- |
| [Constitución](.specify/memory/constitution.md) | Principios del proyecto. |
| [Especificación](.specify/specs/001-margen/spec.md) | Flujos, comandos y criterios de aceptación. |
| [Plan técnico](.specify/specs/001-margen/plan.md) | Arquitectura y entorno de destino. |
| [Tareas](.specify/specs/001-margen/tasks.md) | 41 tareas ordenadas por dependencia. |
| [Handoff](.specify/specs/001-margen/handoff.md) | Contexto para iniciar la implementación en Codex o Claude Code. |

La edición pública omite nombres personales y detalles de otros perfiles del anfitrión. Conserva las decisiones funcionales y técnicas aprobadas. Los informes de diagnóstico, datos de lectura y credenciales no se publican.

## Arquitectura prevista

- Raspberry Pi 5 con Linux ARM64 y almacenamiento NVMe local.
- Perfil `margen`, plugin Python, SQLite y bot privado de Telegram.
- Búsqueda local con FTS5 y `intfloat/multilingual-e5-small`.
- Resúmenes mediante OpenRouter con el modelo especificado en el plan.
- Supervisión mediante systemd de usuario.

Las versiones, interfaces y modelos indicados en el diseño requieren las pruebas de compatibilidad y calidad descritas en el plan antes del despliegue. El repositorio aún no contiene un bot listo para instalar.

## Diagnóstico de despliegue

[scripts/diagnostico-margen.sh](scripts/diagnostico-margen.sh) recoge información selectiva del entorno de destino. Revisar el script antes de ejecutarlo y no publicar el informe generado: puede revelar información del anfitrión aunque omita credenciales y notas.

```bash
umask 077
bash scripts/diagnostico-margen.sh > margen-diagnostico.json
```

Ejecutar sin `sudo`. El script no instala componentes ni ejecuta Hermes o el backup.
