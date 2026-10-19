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

Esperado: `aarch64`, cliente/servidor Docker accesibles y Compose v2 o posterior. No instalar o reconfigurar Docker como efecto de este fichero. La imagen oficial incluye más herramientas que Margen y su construcción puede tardar y ocupar varios GB; se requieren red y espacio libre en el NVMe. El límite de 4 GB/2 CPU se aplica al contenedor de ejecución, no a la construcción.

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

## 4. Validación de Margen pendiente

El código queda disponible en `/lab/plugins/margen`, las pruebas en `/lab/tests` y los scripts en `/lab/scripts`. Esta configuración **todavía no instala ni habilita Margen**, no inicia el gateway y no presupone que el lock de Python 3.11 sea válido para el runtime 3.14 de la imagen.

La siguiente fase dentro del laboratorio es resolver las dependencias del plugin junto con las de Hermes, comprobar su registro en el perfil `margen`, instalar/configurar la extensión con IDs de prueba y ejecutar la suite y la evaluación local con red deshabilitada. Después se probarán Telegram y Haiku con notas ficticias. No instalar paquetes a ciegas sobre el entorno administrado de la imagen oficial.

Las pruebas de contenedor no cubren systemd de usuario, lingering, el venv nativo ni la recuperación del SSD real. Esas comprobaciones mantienen su estado en `docs/validation.md`.

## Detener y conservar datos

```bash
sudo docker compose -f deployment/docker/compose.yaml down
```

Esta orden conserva el volumen de laboratorio. No usar `down -v` salvo que se quiera eliminar expresamente todos sus datos y credenciales. No afecta a los servicios Hermes del anfitrión.

## Evidencia y fuentes

Estado (2026-10-19): Docker instalado en la Raspberry y contenedor `hello-world` ARM64 ejecutado correctamente, según salida aportada por el usuario. Docker Compose v5.6.0. Configuración validada con `docker compose config --quiet`. Construcción/arranque de Hermes pendientes. El daemon Docker del equipo de desarrollo no estaba disponible para una construcción local.

- [Docker oficial de la revisión fijada](https://github.com/NousResearch/hermes-agent/blob/22063fc099ec9ad8357d7f8f6e6248a0400680d3/Dockerfile).
- [Guía Docker de esa revisión](https://github.com/NousResearch/hermes-agent/blob/22063fc099ec9ad8357d7f8f6e6248a0400680d3/website/docs/user-guide/docker.md).
- [Declaración de runtime/dependencias](https://github.com/NousResearch/hermes-agent/blob/22063fc099ec9ad8357d7f8f6e6248a0400680d3/pyproject.toml).
