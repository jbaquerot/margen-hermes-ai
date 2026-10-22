# Despliegue controlado

El usuario autorizó Docker como despliegue definitivo después de validar el laboratorio en Raspberry. La preparación está disponible en [procedimiento de producción](../deployment/docker/PRODUCTION.md); su ejecución y aceptación final siguen pendientes. Ver [evidencias y límites](validation.md).

## Decisión vigente

La revisión operativa 1.1 del plan sustituye la instalación nativa y la unidad por perfil por una imagen Docker ARM64 fijada a Hermes `22063fc099ec9ad8357d7f8f6e6248a0400680d3`, Python 3.14.7 y s6. Un gateway `default` compartido sirve el perfil `margen`. Docker proporciona el reinicio del contenedor y s6 el del proceso. El daemon Docker debe estar habilitado al iniciar la Raspberry.

Los datos permanecen en el volumen externo ya verificado `margen-hermes-lab_data`, sobre el NVMe. La ruta dentro del contenedor es `/opt/data/profiles/margen/plugin-data/margen/data.db`. Claves, configuración, modelo E5 y dependencias del perfil permanecen en el mismo volumen; no se copian a Git ni al repositorio. Los libros ficticios se conservan, con cambio explícito de libro activo para uso real.

No instalar `deployment/hermes-gateway-margen.service.example`: es una plantilla histórica incompatible con esta topología. No migrar ni modificar los Hermes nativos del anfitrión. El procedimiento definitivo no publica puertos ni monta el socket Docker en el contenedor.

## Comprobaciones antes y después

El script `scripts/deploy-docker-margen.py` comprueba imagen, volumen y exclusividad, toma una copia consistente, detiene el laboratorio y espera el estado saludable del nuevo servicio. Si el nuevo arranque falla, intenta recuperar el laboratorio sin arrancar dos instancias conocidas. La configuración Compose, los ensayos de fallo simulados y la suite local no equivalen a su ejecución real en la Raspberry.

La copia local y restauración en cuarentena se ensayaron en el runtime de destino. La transferencia al SSD externo y la recuperación ante pérdida del NVMe siguen pendientes. No se cambia el montaje ni el backup existente como parte de este procedimiento.

La puesta en marcha definitiva debe comprobar `/libros`, una nota conservada, los resúmenes existentes y una captura nueva en Telegram. Permanecen abiertas las pruebas de aceptación enumeradas en `validation.md`; la ausencia de otra cuenta para ensayar autorización se conserva como límite, sin relajar la allowlist.

Para los comandos de operación, actualización y reversión usar el procedimiento de producción. El laboratorio continúa documentado en [su README](../deployment/docker/README.md) únicamente como entorno probado y vía de reversión.
