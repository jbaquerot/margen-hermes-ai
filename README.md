# Margen · Hermes AI

Perfil personal de Hermes Agent para conservar notas de lectura por Telegram, generar resúmenes a petición y recuperar notas describiendo una idea.

**Estado:** implementación 0.1.0 probada en laboratorio Docker en Raspberry mediante Telegram y OpenRouter. Servicio definitivo Docker operativo y verificado en Telegram; copia y restauración local en cuarentena verificadas. Aceptación completa y copia externa pendientes.

## Funcionalidad implementada

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

## Arquitectura

- Raspberry Pi 5 con Linux ARM64 y almacenamiento NVMe local.
- Perfil `margen`, plugin Python, SQLite y bot privado de Telegram.
- Búsqueda local con FTS5 y `intfloat/multilingual-e5-small`.
- Resúmenes mediante OpenRouter con el modelo especificado en el plan.
- Laboratorio Docker: gateway compartido supervisado por s6. Docker aprobado como destino definitivo; servicio definitivo operativo y verificado en Raspberry.

El núcleo incluye SQLite transaccional, recibos idempotentes, interacciones persistentes, búsqueda local, trabajos de resumen y transporte de Telegram. La búsqueda E5 recupera 9/10 descripciones entre los cinco primeros tanto localmente como en Docker Linux ARM64 sin red. La suite local tiene 72 pruebas que pasan en Python 3.11.15 y PTB 22.8. El usuario ha verificado recorridos reales de captura, búsqueda, resúmenes, edición, movimiento, borrado, exportación y reinicio. Las limitaciones y pruebas pendientes están en `docs/validation.md`.

## Desarrollo

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest -q
```

La búsqueda real necesita preparar sus artefactos y dependencias; las pruebas ordinarias usan dobles locales. No se necesitan tokens para ejecutar la suite.

## Entrega y operación

- [Validación y requisitos](docs/validation.md): pruebas ejecutadas y puertas pendientes.
- [Contrato Hermes](docs/compatibility.md): interfaces de la revisión objetivo y límites del ensayo.
- [Evaluación de búsqueda](docs/search-evaluation.md) y [resúmenes](docs/summary-evaluation.md).
- [Despliegue](docs/deployment.md): preparación aislada, perfil, servicio y reversión.
- [Despliegue definitivo Docker](deployment/docker/PRODUCTION.md): promoción, operación, actualización y reversión.
- [Estado de entrega](docs/work-status.md): trabajo verificado y aceptación pendiente.
- [Laboratorio Docker en Raspberry](deployment/docker/README.md): Hermes aislado y diferencia entre runtimes 3.11/3.14.
- [Operación y recuperación](docs/operations.md): comandos, instantánea consistente y cuarentena.

`python scripts/package-margen.py` genera `dist/margen-0.1.0.tar` y un manifiesto de hashes. No incorpora modelos, bases ni credenciales. No activa ningún servicio.

## Diagnóstico de despliegue

[scripts/diagnostico-margen.sh](scripts/diagnostico-margen.sh) recoge información selectiva del entorno de destino. Revisar el script antes de ejecutarlo y no publicar el informe generado: puede revelar información del anfitrión aunque omita credenciales y notas.

```bash
umask 077
bash scripts/diagnostico-margen.sh > margen-diagnostico.json
```

Ejecutar sin `sudo`. El script no instala componentes ni ejecuta Hermes o el backup.
