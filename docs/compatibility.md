# Contrato Hermes / Telegram

Objetivo: Hermes `22063fc099ec9ad8357d7f8f6e6248a0400680d3`, Python 3.11.15, python-telegram-bot 22.8. Se examinó el archivo público de esa revisión sin importar ni arrancar el agente. No se modifican fuentes de Hermes.

| Interfaz pública examinada | Uso |
| --- | --- |
| `hermes_cli/plugins.py`, `PluginContext.register_command(name, handler, description, args_hint, argument_mode)` | Registro de los 17 comandos; un rechazo por colisión impide el registro completo. |
| `PluginContext.register_platform_handler(platform, factory)` | Fábrica síncrona `(native_application, adapter)`. |
| `plugins/platforms/telegram/adapter.py`, `_wire_plugin_handlers(self._app)` | Hermes conecta las fábricas antes de sus manejadores generales; Margen usa grupo -100 y `ApplicationHandlerStop`. |
| `plugins/plugin_storage.py`, `plugin_data_dir`, `plugin_db` | Datos propios fuera del código; conexión con la política SQLite del anfitrión. |
| `agent/plugin_llm.py`, `PluginLlm.acomplete` | Inferencia heredada del perfil; sin gestionar claves ni sustituir proveedor. |
| `PluginContext.profile_name`, `get_config` | Aislamiento por perfil y lectura de `plugins.entries.margen.settings`. |

El manejador nativo conserva `bot.id`, `user.id`, `chat.id` y `message.message_id`. El despachador genérico de comandos no ofrece la identidad original necesaria para deduplicar: sus callbacks solo indican que el comando debe usarse en Telegram. Se autoriza antes de crear la base. Los comandos nativos reconocidos se delegan a Hermes; callbacks quedan fuera del filtro. Adjuntos se rechazan. Un fallo local se consume incluso si falla también el envío del error.

La revisión examinada no tiene colisiones entre sus nombres/alias nativos y los comandos de Margen. La plantilla usa la clave real de Hermes **`model.default`**, además de `model.provider`.

Las pruebas utilizan objetos `Update` y manejadores reales de PTB 22.8, transporte simulado y un contexto de registro controlado. La comprobación adicional con `HERMES_SOURCE` analiza firmas y colisiones mediante AST. **No equivale a cargar el gateway completo en la Raspberry**: esa prueba y la conexión del bot siguen pendientes en T032/T040.

```bash
HERMES_SOURCE=/ruta/al/archivo-de-la-revision python -m pytest -q
```

No se publica ni empaqueta el código fuente descargado de Hermes.
