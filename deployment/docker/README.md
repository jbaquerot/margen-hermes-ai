# Laboratorio Docker de Hermes para Margen

Este laboratorio ejecuta **Hermes dentro de Docker** sobre Linux ARM64. Conserva la revisión aprobada `22063fc099ec9ad8357d7f8f6e6248a0400680d3` y utiliza su Dockerfile oficial, incluida la corrección de SQLite. No configura Docker como backend de terminal del Hermes nativo.

El volumen `margen-hermes-lab_data` es exclusivo del laboratorio. No se monta `/home/claw/.hermes`, el SSD de backup ni el socket Docker. Solo se montan directorios de código/pruebas seleccionados, de lectura. No se exponen puertos ni se configura arranque automático. La orden por defecto muestra la versión y termina.

## Diferencia de runtime

El Dockerfile oficial de esta revisión prepara **Python 3.14**. Su `pyproject.toml` admite 3.11 como puente de actualización, pero excluye de él las dependencias principales y declara expresamente que no es el runtime soportado. El diagnóstico previo del anfitrión mostró Python 3.11.15. No se cambia ese venv ni se actualiza el Hermes nativo.

Docker permite probar un runtime limpio y la integración real de Hermes/Margen. El resultado no valida la instalación nativa existente ni cambia el objetivo de despliegue aprobado automáticamente. Antes de dar por compatible ese despliegue hay que resolver esta diferencia con evidencia de su runtime efectivo.

## 1. Comprobar Docker en la Raspberry

Desde la raíz del checkout de Margen, como usuario con acceso al daemon:

```bash
uname -m
sudo docker version
sudo docker compose version
df -h .
```

Esperado: `aarch64`, cliente/servidor Docker accesibles y Compose v2 o posterior. No instalar o reconfigurar Docker como efecto de este fichero. La imagen oficial incluye más herramientas que Margen y su construcción puede tardar y ocupar varios GB; se requieren red y espacio libre en el NVMe. Los límites declarados de 4 GB/2 CPU se solicitan para ejecución, no para construcción. En el ensayo de la Raspberry, Docker avisó que no pudo aplicar el límite de memoria por falta de soporte/configuración de cgroups; no se debe dar por vigente ese límite. No se modifica el kernel dentro de estas pruebas.

## 2. Construir y comprobar el contenedor

Cuando el diagnóstico anterior sea correcto:

```bash
sudo docker compose -f deployment/docker/compose.yaml config --quiet
sudo docker compose -f deployment/docker/compose.yaml build hermes
sudo env MARGEN_LAB_UID="$(id -u)" MARGEN_LAB_GID="$(id -g)" \
  docker compose -f deployment/docker/compose.yaml run --rm hermes --version
```

Se construye desde el código fuente fijado; no se usa `latest` ni se presupone una etiqueta de imagen correspondiente a ese commit. La revisión del contexto y su etiqueta de construcción identifican el origen, aunque el banner de una compilación local pueda indicar revisión desconocida. El propio Dockerfile fija sus herramientas; la disponibilidad de todas las descargas debe comprobarse al construir en la Raspberry.

No añadir `--init` ni reemplazar el entrypoint: la imagen oficial usa s6 como PID 1 y prepara usuario/permisos. No hace falta ejecutar `docker compose up` para estos ensayos.

## 3. Perfil exclusivo de laboratorio

Solo después de superar la construcción y la comprobación anterior:

```bash
sudo env MARGEN_LAB_UID="$(id -u)" MARGEN_LAB_GID="$(id -g)" \
  docker compose -f deployment/docker/compose.yaml run --rm hermes profile create margen
sudo env MARGEN_LAB_UID="$(id -u)" MARGEN_LAB_GID="$(id -g)" \
  docker compose -f deployment/docker/compose.yaml run --rm hermes -p margen setup
```

Crear el perfil una sola vez. Configurar OpenRouter y un **bot nuevo de pruebas** mediante el asistente. No reutilizar el token de un bot en ejecución: dos gateways competirían por los mismos mensajes. Los secretos se escriben dentro del volumen de laboratorio; nunca se incluyen en Compose ni en Git. No compartir el archivo `.env` generado.

En bloques de shell alimentados por heredoc, añadir `-T --interactive=false` a los comandos `compose run` que no necesiten entrada: el modo interactivo predeterminado puede consumir las líneas siguientes del script. Para asistentes y preguntas interactivas, ejecutar el comando separado desde el terminal.

## 4. Validación de Margen pendiente

El código queda disponible en `/lab/plugins/margen`, las pruebas en `/lab/tests` y los scripts en `/lab/scripts`. El montaje de código por sí solo **no instala ni habilita Margen**, no inicia el gateway y no presupone que el lock de Python 3.11 sea válido para el runtime 3.14 de la imagen.

La siguiente fase dentro del laboratorio es resolver las dependencias del plugin junto con las de Hermes, comprobar su registro en el perfil `margen`, instalar/configurar la extensión con IDs de prueba y ejecutar la suite y la evaluación local con red deshabilitada. Después se probarán Telegram y Haiku con notas ficticias. No instalar paquetes a ciegas sobre el entorno administrado de la imagen oficial.

Las pruebas de contenedor no cubren systemd de usuario, lingering, el venv nativo ni la recuperación del SSD real. Esas comprobaciones mantienen su estado en `docs/validation.md`.

## Evaluación de búsqueda sin red

Tras descargar y verificar los artefactos, combinar `compose.yaml` con `compose.offline.yaml`: el contenedor usa `network_mode: none`. No se cambia el acceso de red de otros contenedores.

La imagen tiene un entorno base y generaciones de dependencias administradas por PM. Antes de ejecutar el evaluador, importar `hermes_bootstrap` aplica la selección vigente, igual que los entrypoints de Hermes; no instalar paquetes con pip sobre la imagen. El `PYTHONPATH` añade el paquete de Margen ya instalado para que el script independiente pueda importarlo. Las notas de evaluación se crean en una base temporal y el informe queda en el volumen de laboratorio.

```bash
sudo env MARGEN_LAB_UID="$(id -u)" MARGEN_LAB_GID="$(id -g)" \
  docker compose -f deployment/docker/compose.yaml \
  -f deployment/docker/compose.offline.yaml \
  run -d --name margen-lab-search --pull never -T --interactive=false \
  -e PYTHONPATH=/opt/hermes:/opt/data/profiles/margen/plugins/margen \
  hermes python -c 'import hermes_bootstrap, runpy; runpy.run_path("/lab/scripts/evaluate-search.py", run_name="__main__")' \
  /opt/data/profiles/margen/plugin-data/margen/models/e5 \
  --output /opt/data/profiles/margen/plugin-data/margen/validation/search-arm64.json

sudo docker logs --follow margen-lab-search
sudo docker inspect --format 'Estado: {{.State.Status}} | Código: {{.State.ExitCode}}' margen-lab-search
```

Resultado esperado: >=8/10, arquitectura `aarch64`, informe JSON y salida `0`. La puntuación y las consultas negativas deben revisarse en el informe: el código de salida del script por sí solo no certifica CC-01. Si falla, conservar el contenedor y sus logs; no habilitar una alternativa remota. El nombre fijo identifica el primer ensayo: no lanzar otro con el mismo nombre mientras exista ese contenedor.

## Preflight del perfil antes de arrancar el bot

`scripts/preflight-container-margen.py` usa el bootstrap de Hermes para seleccionar sus dependencias y, solo dentro del proceso de prueba, selecciona el perfil `margen`. Comprueba los 17 comandos y la fábrica de Telegram usando las interfaces públicas reales. Verifica allowlist/configuración sin imprimir IDs, recoge versiones y lee las métricas/negativas del informe de búsqueda. SQLite se prueba solo en memoria. No inicia un gateway ni solicita inferencia.

Con `--apply-soul`, si pasan las comprobaciones, copia `/lab/profile/SOUL.md` al perfil. Conserva un SOUL anterior en `SOUL.before-margen.md` y rechaza reemplazar una edición posterior. Guarda un informe sin credenciales ni notas en `plugin-data/margen/validation/preflight.json`. Ejecutar con ambos archivos Compose para mantener el proceso sin red:

```bash
sudo env MARGEN_LAB_UID="$(id -u)" MARGEN_LAB_GID="$(id -g)" \
  docker compose -f deployment/docker/compose.yaml \
  -f deployment/docker/compose.offline.yaml \
  run -d --name margen-lab-preflight --pull never -T --interactive=false \
  -e PYTHONPATH=/opt/hermes:/opt/data/profiles/margen/plugins/margen \
  hermes python /lab/scripts/preflight-container-margen.py --apply-soul

sudo docker logs --follow margen-lab-preflight
sudo docker inspect --format 'Estado: {{.State.Status}} | Código: {{.State.ExitCode}}' margen-lab-preflight
```

Un resultado `ok: true` permite continuar a las pruebas del canal. No demuestra por sí solo entrega real, latencia del bot ni fidelidad de Haiku.

## Primer arranque y prueba de Telegram

Requisito: preflight `ok: true`, SOUL aplicado y bot exclusivo configurado. El ensayo del canal necesita la configuración base con red; no añadir `compose.offline.yaml` en este paso. Esta revisión exige arrancar el gateway compartido desde `default`: carga los adaptadores, credenciales y plugins del perfil `margen` en su propio contexto. `default` es el del volumen Docker de laboratorio; no es el Hermes nativo de la Raspberry. El gateway queda en primer plano dentro del contenedor, sin redirección a s6, y el contenedor persiste aunque se cierre SSH:

```bash
sudo env MARGEN_LAB_UID="$(id -u)" MARGEN_LAB_GID="$(id -g)" \
  docker compose -f deployment/docker/compose.yaml \
  run -d --name margen-lab-host-gateway --pull never -T --interactive=false \
  hermes -p default gateway run --no-supervise -v

sudo docker logs --follow margen-lab-host-gateway
```

`Ctrl+C` termina solo el seguimiento de logs. En Telegram, abrir el bot de pruebas, pulsar Iniciar si procede y enviar `/libros`. En un perfil nuevo se espera `No hay libros registrados` y `Sin libro activo`. Comprobar esa respuesta antes de pasar a capturas, búsqueda y resúmenes. Una respuesta genérica distinta no demuestra funcionamiento del plugin; revisar la conexión y el registro del manejador.

Para detener solo este gateway de laboratorio:

```bash
sudo docker stop margen-lab-host-gateway
```

El intento anterior con `-p margen` fue rechazado por la guarda de gateway compartido antes de conectar Telegram. Se conserva el contenedor fallido `margen-lab-gateway`; la orden corregida usa otro nombre. El arranque corregido y la respuesta real del bot siguen pendientes de evidencia. No ejecutar esta orden dos veces si ya está funcionando.

Conservar los contenedores de ensayos si se necesitan sus logs. No usar `--force`, `--replace`, `gateway.standalone` ni eliminar huérfanos para eludir una negativa de supervisión. No ejecutar una migración de los servicios nativos como parte de este laboratorio. El límite de memoria descartado por el anfitrión sigue sin aplicarse.

## Detener y conservar datos

```bash
sudo docker compose -f deployment/docker/compose.yaml down
```

Esta orden conserva el volumen de laboratorio. No usar `down -v` salvo que se quiera eliminar expresamente todos sus datos y credenciales. No afecta a los servicios Hermes del anfitrión.

## Evidencia y fuentes

Estado (2026-10-19): Docker instalado en la Raspberry y contenedor `hello-world` ARM64 ejecutado correctamente, según salida aportada por el usuario. Docker Compose v5.6.0. Configuración validada con `docker compose config --quiet`. La construcción terminó: imagen `ba77c43768f6`, 4,74 GB según Docker. El contenedor ejecutó `hermes --version`: versión `vunknown (2026.9.24)`, método Docker, Python 3.14.7 y OpenAI SDK 2.24.0. `vunknown` es compatible con la ausencia de metadatos Git en la construcción local; el contexto de build sigue fijado al SHA aprobado. Aviso observado: el límite de memoria no se aplica en este host. El perfil `margen` fue creado correctamente en `/opt/data/profiles/margen` con `--no-alias --no-skills`, según salida del usuario. El código del plugin se instaló correctamente en `/opt/data/profiles/margen/plugins/margen`, fijado a `e98479f9a444e0e06116f766ae671b4e5aae22b4`, con `--no-deps --no-enable`. El listado confirmó el plugin desactivado y fijado a esa revisión. Plugin Doctor pasó sus comprobaciones básicas y advirtió que faltan `onnxruntime`, `tokenizers` y `numpy`. El doctor usa un perfil temporal: este resultado no verifica los 17 comandos de Margen. La habilitación posterior mediante `plugins enable margen` resolvió e instaló las dependencias y terminó con código `0`. Faltan comprobaciones del runtime efectivo, configuración y carga funcional. El daemon Docker del equipo de desarrollo no estaba disponible para una construcción local.

- [Docker oficial de la revisión fijada](https://github.com/NousResearch/hermes-agent/blob/22063fc099ec9ad8357d7f8f6e6248a0400680d3/Dockerfile).
- [Guía Docker de esa revisión](https://github.com/NousResearch/hermes-agent/blob/22063fc099ec9ad8357d7f8f6e6248a0400680d3/website/docs/user-guide/docker.md).
- [Declaración de runtime/dependencias](https://github.com/NousResearch/hermes-agent/blob/22063fc099ec9ad8357d7f8f6e6248a0400680d3/pyproject.toml).
