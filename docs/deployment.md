# Despliegue controlado

Estado: laboratorio Docker operativo en Raspberry con pruebas reales de Telegram, OpenRouter, reinicio y recuperación local en cuarentena. El despliegue definitivo y su aceptación siguen pendientes; ver `validation.md`.

**Procedimiento nativo bloqueado para la revisión Hermes fijada:** el ensayo Docker confirmó que rechaza un gateway separado con `-p margen`. Las instrucciones de arranque y la unidad por perfil que figuran más abajo son el diseño anterior y no deben ejecutarse ni instalarse hasta revisar la integración con el gateway compartido y la flota existente. La corrección aislada del laboratorio está en `deployment/docker/README.md`; no autoriza migrar los servicios nativos.

## Propuesta de despliegue definitivo — pendiente de decisión

Se recomienda consolidar Docker, conservando la revisión Hermes fijada, el perfil `margen`, la búsqueda local y el gateway compartido supervisado por s6 que ya se han ensayado. El plan aprobado preveía instalación nativa y systemd por perfil; esa topología requiere revisión por el rechazo de gateways separados en la revisión objetivo. Elegir Docker cambia esa decisión de despliegue, no los requisitos funcionales.

Si se elige Docker, preparar una configuración de servicio estable con política de reinicio, volumen de datos identificado y arranque reproducible; definir el tratamiento de los libros de prueba antes de usar notas personales. Mantener un solo proceso que consulte el token del bot. Conservar una reversión a la configuración probada y verificar el canal tras el cambio. La copia consistente y restauración local ya se ensayaron; la política de copias externas y las pruebas de aceptación aún abiertas deben quedar explícitas. No se activa ese servicio definitivo ni se borra el laboratorio con esta propuesta.

La alternativa nativa exige revisar primero el runtime soportado y la integración del gateway compartido con los servicios existentes. No instalar la plantilla antigua por perfil.

## Preparación aislada

1. Confirmar revisión Hermes objetivo y `/home/claw/.hermes/hermes-agent/venv/bin/python --version`: 3.11.15. No actualizar Hermes ni Python como parte de este procedimiento.
2. Descargar el paquete de Margen y verificar los hashes de `docs/release-manifest.json`. Crear un entorno temporal propio con Python 3.11.15. Instalar el paquete, el lock de búsqueda y las dependencias de prueba allí, sin alterar el venv del agente.
3. Ejecutar pruebas, preparar el modelo en un directorio nuevo y evaluar búsqueda en Linux ARM64. Si faltan ruedas compatibles o falla la instalación, detener el despliegue y registrar el error; la resolución del lock no demuestra su funcionamiento en la Raspberry.

```bash
python -m pip install --require-hashes -r requirements-runtime.lock
python -m pip install . 'pytest>=8,<9' 'python-telegram-bot==22.8'
python -m pytest -q
python scripts/prepare-search-model.py /ruta/nueva/modelo-e5
python scripts/evaluate-search.py /ruta/nueva/modelo-e5 --output /ruta/privada/search-arm64.json
python scripts/measure-margen.py --samples 100
```

Solo `prepare-search-model.py` descarga artefactos oficiales: revisión y SHA-256 fijos, unos 487 MB sin comprimir. Las búsquedas posteriores son locales. El lock fue resuelto para CPython 3.11, aarch64 y glibc >=2.28; Debian 13 cumple ese requisito. No instalarlo indiscriminadamente en un entorno compartido: ensayar la resolución conjunta con las dependencias de Hermes, sin actualizar dependencias ajenas por sorpresa.

## Perfil y canal de prueba

Crear un perfil nuevo mediante `hermes profile create margen`, sin clonar canales. Usar siempre `hermes -p margen ...`. Guardar el plugin completo `plugins/margen/` bajo el directorio de plugins del nuevo perfil y combinar `profile/config.example.yaml` con su configuración. Copiar `profile/SOUL.md` al nuevo perfil. No sobrescribir configuraciones existentes.

Configurar localmente un token exclusivo de Telegram, OpenRouter y el ID del único propietario/chat privado. No enviar claves a este chat ni guardarlas en Git. Usar el setup de la revisión instalada y sus variables de canal documentadas; establecer también su allowlist. El plugin aplica su propia comprobación de identidad antes del dominio.

Fijar `model.provider: openrouter` y `model.default: anthropic/claude-haiku-5.5`. No hay cambio automático de modelo. Comprobar disponibilidad real en OpenRouter antes de usar notas personales. Instalar dependencias del plugin en el entorno que ejecutará Hermes **solo después** de verificar compatibilidad conjunta; cualquier conflicto de versiones impide dar por listo el despliegue.

Los datos se resolverán mediante la API pública bajo `/home/claw/.hermes/profiles/margen/plugin-data/margen/data.db`. Preparar el modelo en la ruta de `model_dir`. Directorio privado, `umask 077`, base 0600. Las notas usadas en resúmenes salen a OpenRouter; las búsquedas no.

Arrancar inicialmente en primer plano con `hermes -p margen gateway run`. Confirmar en logs que se carga el plugin y se conectan los manejadores. Un plugin que no se carga no proporciona las garantías de persistencia; no usar el bot hasta completar esta comprobación.

## Servicio y aceptación

Tras los ensayos reales aprobados, revisar `deployment/hermes-gateway-margen.service.example` y copiar como `~/.config/systemd/user/hermes-gateway-margen.service`. La plantilla no ejecuta nada por sí sola. Comprobar `loginctl show-user claw -p Linger` para persistencia sin sesión; habilitar lingering requiere una operación aparte si no estuviera configurado. No reiniciar toda la Raspberry para probarlo.

Validar todos los comandos con datos ficticios, propietario ajeno rechazado, respuestas largas, documento Markdown, progreso >5 s, captura concurrente, reinicio del gateway y lectura de estado conservado. Completar la rúbrica real de Haiku y medir recepción de Telegram. Habilitar el servicio solo al superar estas comprobaciones.

## Reversión

Parar y deshabilitar únicamente `hermes-gateway-margen.service`. Conservar `plugin-data/margen` y su instantánea verificada. Retirar el plugin del perfil y revertir solo los cambios de ese perfil. No borrar datos para revertir código; no abrir una base de esquema más reciente con código antiguo. Restaurar primero en cuarentena según `operations.md`.
