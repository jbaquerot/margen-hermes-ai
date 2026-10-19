# Evaluación de búsqueda

Se fijaron 32 notas sintéticas en cinco libros (dos comparten título), una pendiente y una nota larga, diez descripciones con referencia esperada y dos consultas negativas. No contienen notas personales. Las expectativas se anotaron antes de probar el modelo.

Modelo oficial `intfloat/multilingual-e5-small`, revisión `614241f622f53c4eeff9890bdc4f31cfecc418b3`. Los hashes de sus dos artefactos están en `deployment/search-artifacts.json`. Se usa el ONNX FP32 oficial, sin conversión ni cuantización alternativa. No se usa un modelo avx512 en ARM.

Proceso: prefijos `query:`/`passage:`, fragmentos de 450 tokens con avance de 400, máximo 512 con prefijo/especiales, pooling con máscara y normalización L2, 384 dimensiones. Hasta dos hilos de CPU y carga diferida. Cada resultado agrupa todos los fragmentos de una nota y devuelve el texto vigente completo.

Orden final: coseno >=0,83, FTS5 unicode61 con diacríticos normalizados, palabras funcionales españolas excluidas de la consulta léxica, fusión de posiciones `1/(10+r_semántico) + 0,2/(10+r_léxico)` cuando exista cada rango. La coincidencia léxica no elude el mínimo semántico. Paginación de cinco referencias sin repetir.

## Evidencia local

`search-local-baseline.json` conserva la primera ejecución: 7/10 con RRF simétrica, palabras funcionales y umbral 0,80. Esa combinación dejaba que términos frecuentes desplazasen notas semánticamente pertinentes. Se eliminó ese ruido y se redujo el peso léxico; el umbral final 0,83 evita las coincidencias negativas de este conjunto. No se cambiaron las diez consultas ni sus resultados esperados durante el ajuste.

`search-local-result.json` registra la ejecución final sobre **macOS ARM64, Python 3.11.15**, artefactos reales y ONNX Runtime 1.31.0. El resultado local supera el mínimo de 8/10. La consulta sobre distracciones no recupera F07 entre los cinco primeros; el modelo pequeño tiene límites de relevancia. Este conjunto también sirvió para calibrar parámetros: no demuestra generalización a cualquier libro.

La primera consulta incluye la indexación inicial de todas las notas; las posteriores usan el índice. El RSS es el máximo del proceso y debe leerse con la unidad indicada en el JSON. La telemetría de ONNX Runtime se deshabilita antes de crear la sesión; no hay clientes remotos ni descargas en el código de búsqueda. Las ejecuciones locales se realizaron sin habilitar acceso de red para la inferencia.

## Evidencia de Raspberry y trabajo pendiente — T018/T034

El usuario ejecutó el mismo evaluador en Docker sobre la Raspberry con `network_mode: none`: **9/10; aarch64; salida 0**. Esto supera el umbral del conjunto fijo. El informe completo sigue en el volumen del laboratorio. El preflight recoge las métricas y confirma ambas negativas vacías en `docs/docker-preflight-result.json`: Python 3.14.7, ONNX Runtime 1.29.0, tokenizers 0.23.1 y NumPy 2.4.3; carga 1,997 s y RSS máximo 1.195.552 KiB (aprox. 1,14 GiB).

Completar la evaluación en Linux aarch64 con Python 3.11.15, modelo ya preparado y red denegada para el proceso de prueba. Registrar hashes, dependencias, RAM y tiempos. Comprobar captura simultánea durante indexación, notas largas, edición, borrado y notas pendientes. Exigir >=8/10 y referencias correctas, sin sustituir el modelo ni habilitar una búsqueda remota. La evaluación de macOS no cierra este criterio en Raspberry.

```bash
python scripts/evaluate-search.py /ruta/modelo-e5 --output /ruta/privada/search-arm64.json
```
