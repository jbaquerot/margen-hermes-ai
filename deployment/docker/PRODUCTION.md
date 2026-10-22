# Margen en Docker: despliegue definitivo

Decisión autorizada por el usuario; documentada el 2026-10-22. Preparación comprobada localmente y promoción ejecutada en Raspberry: snapshot verificado y contenedor `margen` healthy en 30,8 s; recorrido Telegram posterior confirmado: libros, activo, consultas y nueva captura. No equivale a cerrar toda la aceptación funcional y operativa.

## Configuración

`compose.production.yaml` se usa solo, sin los archivos Compose del laboratorio. Define proyecto `margen`, servicio `hermes` y contenedor `margen`. Reutiliza la imagen local ARM64 fijada a Hermes `22063fc099ec9ad8357d7f8f6e6248a0400680d3`, ya construida como `margen-hermes-lab:22063fc099ec`. No descarga ni construye otra imagen. El runtime observado es Python 3.14.7.

El volumen externo es **`margen-hermes-lab_data`**, montado en `/opt/data`. Se mantiene su nombre deliberadamente para conservar perfil, claves, base SQLite, modelos E5 y generaciones de dependencias. Un volumen ausente provoca error en lugar de crear una instalación vacía. La promoción conserva los libros ficticios, sin limpieza automática. El usuario los retiró posteriormente mediante la utilidad de mantenimiento y confirmó el catálogo vacío el 2026-10-22; ver `docs/operations.md`. Registrar y activar un libro real al empezar a usarlo.

El contenedor no monta el repositorio ni directorios Hermes del anfitrión, no publica puertos y conserva el entrypoint oficial. s6 supervisa el gateway compartido `default`, que sirve el perfil `margen`; Docker aplica `restart: unless-stopped`. UID/GID se copian selectivamente del laboratorio, sin leer ni imprimir credenciales. El límite de memoria de 4 GB sigue siendo una solicitud descartada por el kernel actual, no una garantía. Logs rotados: tres archivos de hasta 10 MB cada uno.

La comprobación de salud lee exclusivamente el estado operativo de Hermes: proceso vivo, perfil servido y Telegram conectado. No llama a OpenRouter, no envía mensajes y no prueba por sí sola las funciones de Margen. Un estado `unhealthy` requiere diagnóstico: Docker no reinicia automáticamente un contenedor solo por estar unhealthy; s6 reinicia el proceso si termina. Docker reinicia el contenedor si sale, salvo una parada explícita del operador.

Fuentes fijadas: [supervisión Docker](https://github.com/NousResearch/hermes-agent/blob/22063fc099ec9ad8357d7f8f6e6248a0400680d3/website/docs/user-guide/docker.md), [estado operativo](https://github.com/NousResearch/hermes-agent/blob/22063fc099ec9ad8357d7f8f6e6248a0400680d3/gateway/status.py) y [adaptadores por perfil](https://github.com/NousResearch/hermes-agent/blob/22063fc099ec9ad8357d7f8f6e6248a0400680d3/gateway/run_adapters.py).

## Comprobar antes del cambio

Desde el repositorio de la Raspberry, con el laboratorio supervisado activo:

```bash
cd "$HOME/margen-hermes-lab"
git pull --ff-only
python3 scripts/deploy-docker-margen.py --sudo check
systemctl is-enabled docker.service
```

El primer comando de diagnóstico no modifica servicios. Comprueba imagen/revisión ARM64, volumen, UID/GID, exclusividad de uso y sintaxis de Compose. No imprime el JSON completo de Docker inspect, que puede contener secretos. `docker.service` debe estar enabled para que el daemon vuelva a arrancar con el anfitrión. Si no lo está, registrar ese estado y habilitarlo como operación explícita antes de prometer arranque al iniciar la Raspberry. No reiniciar el equipo para este ensayo.

## Cambiar al servicio definitivo

```bash
python3 scripts/deploy-docker-margen.py --sudo deploy
python3 scripts/deploy-docker-margen.py --sudo status
```

El script vuelve a comprobar las condiciones y guarda solamente UID, GID y nombre de volumen en `deployment/docker/.env.production`, modo 0600 y excluido de Git. Genera la instantánea SQLite actual antes de detener el laboratorio, espera hasta 60 segundos en el apagado e inicia el nuevo servicio. Espera hasta 180 segundos a que Docker declare sano el gateway y su conexión Telegram. Si falla ese arranque, intenta detener el nuevo servicio antes de arrancar el laboratorio; si no puede garantizar exclusividad, se detiene y solicita revisar Docker. No empieza un segundo poller conocido sobre el mismo volumen.

La imagen y el volumen permanecen en el equipo. El contenedor anterior se conserva detenido para reversión. El script rechaza repetir `deploy` si ya existe `margen`; no es una orden de actualización ni borra un servicio previo.

Después enviar `/libros`, consultar una nota existente y `/resumenes` en Telegram. Comprobar también una nota ficticia nueva y su confirmación antes de comenzar el uso personal. Compartir estados/resultados sin tokens. Un mensaje de Compose no sustituye esta comprobación de extremo a extremo.

## Operación

Desde el mismo repositorio:

```bash
python3 scripts/deploy-docker-margen.py --sudo status
sudo docker logs --since 5m --tail 100 margen
```

Reiniciar solo Margen: `sudo docker restart --timeout 60 margen`. Una parada explícita `sudo docker stop --timeout 60 margen` deja deshabilitado su reinicio automático hasta volver a arrancarlo con `sudo docker start margen`. No arrancar el contenedor del laboratorio mientras el definitivo esté usando el volumen/bot. No usar `down -v`, `docker volume rm` ni `--remove-orphans` para mantenimiento de datos.

## Copia y recuperación

```bash
python3 scripts/deploy-docker-margen.py --sudo backup
```

Genera y verifica `/opt/data/profiles/margen/plugin-data/margen/current.tar` mediante la API SQLite. Esta copia está en el mismo NVMe: no protege frente a perder ese disco. El ensayo del 2026-10-21 ya comprobó snapshot y restauración en cuarentena en el laboratorio, sin activar esa base. La transferencia al SSD externo, su retención y la integración en el backup semanal siguen pendientes; no se programa una copia ni se modifica el SSD con este despliegue.

Restaurar primero en un directorio nuevo de cuarentena y revisar el registro de eliminaciones; nunca reemplazar la base activa con el proceso funcionando. La copia incluye datos de lectura, no las credenciales del perfil ni los pesos E5. No publicarla ni añadirla a Git. Ver `docs/operations.md` para alcance de borrado, versiones y cuarentena.

## Actualizaciones y reversión

No ejecutar `hermes update`, un pull de otra imagen ni cambiar el SHA de Hermes como mantenimiento implícito. Para una actualización de código de Margen, revisar primero la revisión nueva y la compatibilidad de esquema; generar la copia actual, usar el instalador oficial dentro de `margen` con un SHA completo y reiniciar después. Guardar el SHA anterior para volver a instalarlo si el esquema sigue siendo compatible. Por ejemplo, sustituyendo el marcador por el commit revisado:

```text
sudo docker exec margen hermes -p margen plugins install jbaquerot/margen-hermes-ai/plugins/margen --force --ref SHA_COMPLETO_REVISADO --yes-deps --enable
sudo docker restart --timeout 60 margen
```

El plugin instalado en el volumen no cambia con `git pull` del repositorio. El código de despliegue se entrega separado de los datos; no borrar el volumen para actualizarlo.

Para volver al arranque probado del laboratorio:

```bash
python3 scripts/deploy-docker-margen.py --sudo rollback
```

Detiene el definitivo antes de arrancar el laboratorio y conserva el volumen. Revierte la forma de arranque, no el plugin ni las notas compartidas. Tras una actualización del plugin, esa orden por sí sola no recupera su versión anterior. Si una migración cambia el esquema, preparar una recuperación compatible en cuarentena; no hacer una regresión de código sobre una base incompatible. El laboratorio tiene política de reinicio `no`; una reversión no acredita el arranque persistente definitivo.

## Aceptación pendiente

El cambio ya se ejecutó correctamente en la Raspberry. El recorrido básico Telegram también está confirmado. Quedan mediciones de latencia, concurrencia real durante inferencia, contexto extenso/paginación y cierre de la rúbrica completa. El rechazo de otra identidad está probado automáticamente pero no en otra cuenta Telegram disponible. No se declara uso personal con recuperación externa validada mientras esa copia externa no esté comprobada.
