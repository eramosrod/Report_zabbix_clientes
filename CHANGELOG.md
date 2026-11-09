# Registro de Cambios (Changelog)

Todos los cambios notables en este proyecto serán documentados en este archivo.

## [0.19.0] - 2026-11-09

### Corregido
- **Filtro temporal en `get_problems_history()`**: Corregido el uso de `time_from` en `problem.get` para incluir problemas activos durante el periodo, no solo creados en él.
- **Pérdida de tags GLPI duplicados**: Corregido el parseo de tags en `data_collector.py` para preservar todos los tags `__zbx_glpi_link` en lugar de sobrescribirlos en un diccionario.
- **Filtro temporal incompleto en Fase 2**: Corregida la condición de inclusión de problemas resueltos en la Fase 2 para verificar `time_from <= resolution_clock <= time_till` (antes solo verificaba `<= time_till`), evitando que problemas resueltos antes del rango se incluyeran incorrectamente.

### Añadido
- **Depuración de API y Tags**: Añadidos logs de depuración para contar registros brutos de la API y detectar correctamente múltiples tags `__zbx_glpi_link`.

### Cambiado
- **`zabbix_api.py`**:
  - `get_problems_history()`: Ajustado el filtrado temporal para capturar correctamente el histórico (Fase 1 y Fase 2).
- **`data_collector.py`**:
  - `_enrich_problems()`: Modificado para preservar todos los tags en `tags_list` y mantener compatibilidad con `tags_dict`.
  - `get_glpi_links()`: Actualizado para iterar sobre `tags_list` y procesar múltiples enlaces GLPI.
- **Versión**: Incrementada a 0.19.0.

## [0.17.0] - 2026-11-09

### Corregido
- **Error API Zabbix: Invalid parameter "expandDescription"**: Eliminado el parámetro `expandDescription` de todas las consultas `event.get`, `problem.get` y `trigger.get` en `zabbix_api.py`, ya que no es un parámetro válido en versiones recientes de Zabbix (6.0+). Este error causaba el fallo: `Invalid params. - Invalid parameter "/": unexpected parameter "expandDescription"`.

### Añadido
- **Resolución manual de macros de Zabbix**: Implementado método `resolve_macros()` en `ZabbixAPI` para resolver macros comunes (`{HOST.NAME}`, `{ITEM.VALUE}`, `{TRIGGER.NAME}`, `{EVENT.TIME}`, etc.) en nombres de problemas, descripciones de triggers y nombres de eventos. Las macros ahora se resuelven correctamente en el informe HTML y consola.
- **Filtrado de triggers deshabilitados**: Añadido filtrado por `trigger.status = 0` (habilitado) en `get_active_problems()`, `get_active_problems_raw()`, `get_problems_history()` y `get_events_history()`. Ahora se excluyen alertas de triggers deshabilitados (status=1) además de hosts deshabilitados.
- **Filtrado mejorado de hosts deshabilitados**: Reforzado el filtrado por `host.status = 0` en todas las consultas de problemas y eventos.

### Cambiado
- **`zabbix_api.py`**:
  - Eliminado `expandDescription` de `get_active_problems()`, `get_active_problems_raw()`, `get_problems_history()`, `get_events_history()` y `get_active_alerts()` (legacy).
  - Añadido método `resolve_macros()` para resolución manual de macros de Zabbix.
  - Añadido diccionario `COMMON_MACROS` con macros soportadas.
  - Modificado `get_events_history()` para consultar `trigger.get` con campo `status` y filtrar triggers deshabilitados.
  - Modificado `get_active_problems()`, `get_active_problems_raw()` y `get_problems_history()` para consultar `trigger.get` y filtrar por `trigger.status = 0`.
- **`data_collector.py`**:
  - Actualizado `_enrich_events()` para usar `resolve_macros()` en descripciones de triggers.
  - Actualizado `_enrich_problems()` para usar `resolve_macros()` en nombres de problemas.
- **Versión**: Incrementada a 0.17.0 para reflejar la corrección crítica del error `expandDescription`, resolución de macros y filtrado de triggers/hosts deshabilitados.

## [0.16.0] - 2026-11-08

### Añadido
- **Gestión multi-cliente mediante archivo de configuración externo (`clients.json`)**: Nuevo archivo `clients.json` en la raíz del proyecto para definir perfiles de clientes con identificador, nombre de empresa, ruta del logo, URL de la API de Zabbix y credenciales específicas (`zabbix_user`, `zabbix_pass`).
- **Almacenamiento local de logotipos**: Carpeta `assets/logos/` para almacenar físicamente los archivos de imagen de los logotipos de los clientes.
- **Nuevo argumento CLI `--client` / `-c`**: Permite seleccionar el cliente desde `clients.json` para automatizar la conexión y personalización del informe.
- **Banner personalizado por cliente**: El banner del informe (HTML y consola) ahora muestra el nombre de la empresa del cliente y su logotipo (embebido en base64 en HTML).
- **Autenticación específica por cliente**: Cada cliente usa sus propias credenciales de Zabbix, permitiendo que el motor de Zabbix filtre nativamente los grupos y hosts permitidos para dicho usuario.

### Cambiado
- **`main.py`**:
  - Añadida función `load_client_config()` para cargar configuración desde `clients.json`.
  - Añadido argumento `--client` / `-c` al parser de argumentos.
  - Modificada función `main()` para soportar modo multi-cliente (`--client`) y modo legacy (interactivo o `--url`/`--user`).
  - Actualizada descripción CLI a "Fase 10".
  - Docstring actualizado con la nueva fase.
- **`report_generator.py`**:
  - Constructor `ReportGenerator` ahora acepta y almacena datos del cliente (`client_name`, `client_empresa`, `client_logo_path`).
  - Método `_get_banner_section()`: Reescrito para mostrar logo del cliente (base64) y nombre de empresa en el banner HTML.
  - Método `_print_banner()`: Actualizado para mostrar información del cliente en consola.
  - Método `_get_html_footer()` y `_print_footer_console()`: Versión actualizada a 0.16.1.
  - Docstring actualizado con la nueva fase.
- **`clients.json`**: Nuevo archivo de configuración con estructura para múltiples clientes.
- **Versión**: Incrementada a 0.16.0 para reflejar la gestión multi-cliente y logotipos locales.

### Añadido (Fase 11 - Documentación)
- **`DOC_TECNICA.md`**: Documentación completa del sistema multi-cliente
- **`GUIA_CUSTOMIZACION.md`**: Guía detallada para modificar, adaptar y extender el script y los informes
- Ambos documentos creados en la raíz del proyecto para facilitar el mantenimiento y la extensión

## [0.15.0] - 2026-11-08

### Añadido
- **Simplificación de la tabla "Estado de Entornos" en HTML**: La tabla de HostGroups en el archivo `report.html` ahora muestra **únicamente dos columnas**: el **Nombre del Entorno** y el **Número de Problemas** (eliminando el desglose de columnas por cada severidad en el HTML).
- **Colores dinámicos en filas de entornos (HTML)**:
  - Filas con problemas (`total_problems > 0`): Fondo rojo (`#fdeaea`) y texto rojo (`#E45959`) - clase CSS `.env-row-has-alerts`.
  - Filas sin problemas (`total_problems == 0`): Fondo verde (`#e8f8f5`) y texto verde (`#1abc9c`) - clase CSS `.env-row-no-alerts`.
- **Respeto al formato de Consola**: La salida en texto plano (consola) **conserva su formato actual** con el desglose completo de severidades (Information, Warning, Average, High, Disaster, Not classified), ya que este cambio afecta **únicamente al diseño del archivo HTML**.

### Cambiado
- **`report_generator.py`**:
  - Método `_get_environments_section()`: Reescrito para generar una tabla HTML simple con 2 columnas en lugar de tarjetas con desglose de severidad.
  - Método `_get_html_header()`: Añadidos estilos CSS para las nuevas clases de filas coloreadas dinámicamente (`.env-row-has-alerts`, `.env-row-no-alerts`).
  - Método `_get_html_footer()` y `_print_footer_console()`: Versión actualizada a 0.15.0.
- **`main.py`**:
  - Descripción CLI actualizada a "Fase 9.7".
  - Mensajes de progreso actualizados.
  - Docstring actualizado con la nueva fase.
- **`MEMORIA.md`**: Actualizado a versión 0.15.0 documentando la nueva Fase 9.7 con simplificación de la tabla de entornos en HTML y colores dinámicos.
- **`report_generator.py`**: Método `_get_banner_section()` reescrito para generar una cabecera HTML limpia con solo título de empresa (y logo opcional), eliminando completamente todos los iconos, emojis, metadatos secundarios, timestamp, intervalo de tiempo y logo del cliente.
- **`main.py`**: Método `_print_banner()` sin cambios (consola mantiene formato completo).
- **`MEMORIA.md`**: Actualizado a versión 0.15.0 documentando la nueva Fase 10 con simplificación de la cabecera HTML.
- **Versión**: Incrementada a 0.15.0 para reflejar la simplificación visual de la tabla de entornos en HTML y la nueva simplificación de la cabecera HTML.

## [0.14.0] - 2026-11-08

### Añadido
- **Simplificación de la tabla "Estado de Entornos" en HTML**: La tabla de HostGroups en el archivo `report.html` ahora muestra **únicamente dos columnas**: el **Nombre del Entorno** y el **Número de Problemas** (eliminando el desglose de columnas por cada severidad en el HTML).
- **Colores dinámicos en filas de entornos (HTML)**:
  - Filas con problemas (`total_problems > 0`): Fondo rojo (`#fdeaea`) y texto rojo (`#E45959`) - clase CSS `.env-row-has-alerts`.
  - Filas sin problemas (`total_problems == 0`): Fondo verde (`#e8f8f5`) y texto verde (`#1abc9c`) - clase CSS `.env-row-no-alerts`.
- **Respeto al formato de Consola**: La salida en texto plano (consola) **conserva su formato actual** con el desglose completo de severidades (Information, Warning, Average, High, Disaster, Not classified), ya que este cambio afecta **únicamente al diseño del archivo HTML**.

### Cambiado
- **`report_generator.py`**:
  - Método `_get_environments_section()`: Reescrito para generar una tabla HTML simple con 2 columnas en lugar de tarjetas con desglose de severidad.
  - Método `_get_html_header()`: Añadidos estilos CSS para las nuevas clases de filas coloreadas dinámicamente (`.env-row-has-alerts`, `.env-row-no-alerts`).
  - Método `_get_html_footer()` y `_print_footer_console()`: Versión actualizada a 0.14.0.
- **`main.py`**:
  - Descripción CLI actualizada a "Fase 9.7".
  - Mensajes de progreso actualizados.
  - Docstring actualizado con la nueva fase.
- **`MEMORIA.md`**: Actualizado a versión 0.14.0 documentando la nueva Fase 9.7 con simplificación de la tabla de entornos en HTML y colores dinámicos.
- **Versión**: Incrementada a 0.14.0 para reflejar la simplificación visual de la tabla de entornos en HTML.

## [0.13.0] - 2026-11-07

### Añadido
- **Separación de fuentes de datos para filtrado temporal selectivo**: La tabla de "Alertas Activas" ahora es **independiente del intervalo de tiempo personalizado** (`--time-from` / `--time-till`). Muestra siempre todas las alertas activas actuales del sistema en el momento de la ejecución.
- **Aplicación selectiva del margen de tiempo**: El intervalo de tiempo elegido por el usuario se aplica **exclusivamente** a:
  1. **Resumen de Alertas** (Top Triggers histórico - agrupado por Host + Trigger Name)
  2. **Estado de Entornos** (HostGroups - desglose por severidad)
  3. **Enlaces GLPI** (extraídos del histórico de problemas)
- **Corrección en `zabbix_api.py` - `get_active_problems_raw()`**: Cambiado de `event.get` (que devuelve eventos de creación de problemas, incluyendo resueltos) a `problem.get` (que devuelve SOLO problemas actualmente activos). Se mantiene la estrategia de dos consultas para obtener nombres de hosts mediante `event.get` con los eventids.

### Cambiado
- **`data_collector.py`**:
  - `get_active_problems()`: Ahora usa `_enrich_problems()` con datos crudos de `get_active_problems_raw()` para obtener información completa **SIN filtro temporal**.
  - `get_complete_report_data()`: Desacopla las fuentes de datos:
    - `environment_summary` y `alerts_summary` usan datos históricos **CON filtro temporal** (`time_from`/`time_till`)
    - `active_alerts` usa `get_active_problems()` **SIN filtro temporal** (alertas activas actuales reales)
    - `glpi_links` se extrae del histórico de problemas **CON filtro temporal**
- **`report_generator.py`**:
  - Sección "Alertas Activas": Renombrada de "Alertas (Tabla Temporal - Histórico + Activas)" a **"Alertas Activas"**
  - Banner: Muestra "Problemas Activos (Actuales)" y aclara "Intervalo (Resumen/Entornos)" para distinguir qué secciones usan el filtro
  - Títulos y badges actualizados para reflejar que la tabla muestra solo alertas activas actuales
  - Versión incrementada a 0.13.0 en footer HTML y consola
- **`main.py`**:
  - Descripción CLI actualizada a "Fase 9.6"
  - Mensajes de progreso actualizados para indicar qué consultas usan filtro temporal y cuáles no
  - Argumentos `--time-from` y `--time-till` actualizados con ayuda descriptiva: "aplica a Resumen y Entornos"
- **`MEMORIA.md`**: Actualizado a versión 0.13.0 documentando la nueva Fase 9.6 con separación de fuentes de datos.
- **Versión**: Incrementada a 0.13.0 para reflejar la separación lógica de fuentes de datos.

## [0.12.0] - 2026-11-07

### Añadido
- **Paleta de colores oficial de Zabbix para severidades**: Actualizados los estilos CSS en `report_generator.py` para utilizar la paleta oficial de colores de Zabbix en las etiquetas de severidad (badges) del informe HTML:
  - `Information`: Azul (`#7499FF`)
  - `Warning`: Amarillo (`#FFC859`)
  - `Average`: Naranja (`#FFA15C`)
  - `High`: Rojo Claro (`#E97659`)
  - `Disaster`: Rojo Oscuro / Borgoña (`#E45959`)
  - `Not classified`: Gris (`#7f8c8d`) - sin cambios
- **Estados visuales dinámicos en "Estado de Entornos" (HostGroups)**: Implementada lógica condicional en `report_generator.py` para resaltar visualmente los entornos según su estado de alertas:
  - **Entornos con alertas activas** (`total_problems > 0`): Borde izquierdo rojo (`#E45959`) de 5px, título en rojo, clases CSS `.env-card.has-alerts` y `.env-card-title.has-alerts`
  - **Entornos sin alertas activas** (`total_problems == 0`): Borde izquierdo verde (`#1abc9c`) de 5px, título en verde, clases CSS `.env-card.no-alerts` y `.env-card-title.no-alerts`

### Cambiado
- **`report_generator.py`**:
  - Método `_get_html_header()`: Estilos CSS actualizados con nueva paleta Zabbix y clases para estados de entorno
  - Método `_get_environments_section()`: Lógica condicional para asignar clases CSS según `total_problems`
  - Método `_get_html_footer()` y `_print_footer_console()`: Versión actualizada a 0.12.0
- **`main.py`**: Descripción CLI actualizada a "Fase 9.5" y mensajes de progreso actualizados.
- **`MEMORIA.md`**: Actualizado a versión 0.12.0 documentando la nueva Fase 9.5 con paleta de colores oficial Zabbix y estados visuales de entornos.
- **Versión**: Incrementada a 0.12.0 para reflejar los cambios visuales y de estilo.

## [0.11.0] - 2026-11-07

### Añadido
- **Nomenclatura oficial de severidades en inglés**: Actualizado `SEVERITY_MAP` en `zabbix_api.py` para usar exactamente los nombres oficiales de Zabbix en inglés:
  - `Information` (en lugar de Información)
  - `Warning` (en lugar de Aviso)
  - `Average` (en lugar de Promedio)
  - `High` (en lugar de Alto)
  - `Disaster` (en lugar de Desastre)
  - `Not classified` (en lugar de No clasificado)
- **Simplificación de la sección GLPI**: Eliminada la columna "Estado" de la tabla de Enlaces GLPI en ambas salidas (HTML y consola), mostrando únicamente los datos esenciales: Ticket ID, Título, Host, Severidad y Enlace.

### Cambiado
- **`data_collector.py`**: Actualizado `get_environment_summary()` y `print_environment_summary()` para usar los nuevos nombres de severidad en inglés en la tabla de Estado de Entornos.
- **`report_generator.py`**: Actualizado `_get_severity_class()` para mapear los nuevos nombres en inglés a las clases CSS correspondientes. Eliminada la columna "Estado" en `_get_glpi_links_section()` (HTML) y `_print_glpi_links_console()` (consola).
- **`MEMORIA.md`**: Actualizado a versión 0.11.0 documentando la nueva Fase 9.4 con nomenclatura oficial de severidades y simplificación GLPI.
- **Versión**: Incrementada a 0.11.0 para reflejar los cambios de formato y nomenclatura.

## [0.10.0] - 2026-11-06

### Añadido
- **Nuevo método `get_events_history()` en `zabbix_api.py`**: Implementado usando `event.get` para replicar exactamente la consulta del informe "Top Triggers" de Zabbix.
  - Parámetros clave configurados:
    - `source: 0` (eventos de disparadores/triggers)
    - `object: 0` (triggers)
    - `value: 1` (solo eventos de creación de problemas, para contar cada vez que salta la alerta)
    - `time_from`: Timestamp hacia atrás (por defecto últimos 30 días)
    - `selectHosts: ["hostid", "name"]` para obtener el nombre real del host
    - `selectTriggers: ["triggerid", "description", "priority"]` para obtener nombre y severidad del trigger
  - Permite obtener un recuento exacto y agrupado de las alertas por Host y Nombre de Trigger.
- **Nuevo método `_enrich_events()` en `data_collector.py`**: Enriquece los eventos crudos de `event.get` extrayendo host (del campo `hosts[]`) y trigger (del campo `triggers[]`).
  - Convierte la prioridad del trigger a severidad textual usando `SEVERITY_MAP`.
  - Calcula duración y formatea timestamps.
- **Nuevo método `format_events_for_summary_table()` en `data_collector.py`**: Agrupa **estrictamente por Host + Nombre del Trigger** (trigger_description), sumando el recuento total de ocurrencias históricas (cada evento value=1 es una ocurrencia individual).
  - Ordena por conteo descendente y timestamp más reciente.
  - Replica fielmente la lógica de agrupación del informe "Top Triggers" de Zabbix.
- **Actualización en `get_complete_report_data()`**: Ahora obtiene dos fuentes de datos separadas:
  1. `get_problems_history()` (problem.get) → para tabla temporal "Histórico + Activas" y enlaces GLPI (incluye resueltos con recovery_time).
  2. `get_events_history()` (event.get tipo Top Triggers) → para tabla "Resumen de Alertas" agrupada por Host + Trigger Name.
  - Añade campo `total_events` al informe para mostrar total de eventos de triggers.
- **Actualización en `main.py`**: Flujo triple: Obtiene `active_problems` (event.get), `history_problems` (problem.get) y `history_events` (event.get tipo Top Triggers).
  - Usa `history_events` para la tabla de Resumen de Alertas (agrupación tipo Top Triggers).
  - Usa `history_problems` para tabla temporal y enlaces GLPI.
  - Usa `active_problems` solo para resumen de entornos y contador de activos.
  - Mensajes de progreso actualizados y descripción CLI a "Fase 9".
- **Actualización en `report_generator.py`**:
  - **Banner**: Muestra "Problemas Totales (Histórico problem.get)", "Eventos Totales (Histórico event.get - Top Triggers)" y "Problemas Activos" por separado.
  - **Resumen de Alertas**: Ahora agrupado estrictamente por Host + Trigger Name con conteo exacto de ocurrencias (tipo Top Triggers).
  - **Versión**: Incrementada a 0.9.0 en footer HTML y consola.
- **Nuevos Argumentos CLI** en `main.py`:
  - `--time-from`: Fecha/hora de inicio (formato: YYYY-MM-DD HH:MM:SS o timestamp Unix)
  - `--time-till`: Fecha/hora de fin (formato: YYYY-MM-DD HH:MM:SS o timestamp Unix)
  - Si no se especifican, se usa el rango por defecto (últimos 30 días)
- **Actualización en `zabbix_api.py`**:
  - Método `get_problems_history()`: Ahora acepta y usa parámetros `time_from` y `time_till` para filtrar problemas históricos por rango temporal.
  - Método `get_events_history()`: Ahora acepta y usa parámetros `time_from` y `time_till` para filtrar eventos históricos por rango temporal.
- **Actualización en `data_collector.py`**:
  - Método `get_problems_history()`: Ahora acepta y propaga parámetros `time_from` y `time_till`; usa caché solo cuando no hay filtros temporales.
  - Método `get_events_history()`: Ahora acepta y propaga parámetros `time_from` y `time_till`; usa caché solo cuando no hay filtros temporales.
  - Método `get_complete_report_data()`: Ahora acepta y propaga parámetros `time_from` y `time_till` a todas las consultas.
- **Actualización en `report_generator.py`**:
  - Clase `ReportGenerator`: Constructor ahora acepta parámetros `time_from` y `time_till`.
  - Sección `_get_banner_section()`: Muestra intervalo de tiempo formateado en banner HTML si está disponible.
  - Sección `_print_banner()`: Muestra intervalo de tiempo formateado en banner de consola si está disponible.
  - Función `generate_report()`: Ahora acepta y propaga parámetros `time_from` y `time_till`.
- **Resultado**: El informe ahora puede filtrar datos por cualquier rango temporal personalizado especificado por el usuario, mostrando el intervalo seleccionado en el banner del informe (tanto HTML como consola) y reflejando exclusivamente los datos dentro del rango seleccionado.

### Corregido
- **Histórico de Alertas incompleto (solo 2 problemas)**: Solucionado añadiendo el parámetro `limit` a `problem.get` para evitar el límite por defecto de la API. Ahora se recuperan correctamente tanto problemas activos como resueltos (histórico completo) dentro del rango temporal especificado.
- **Recuento total y tabla temporal**: Ahora reflejan fielmente ambos estados (activos y resueltos) en la consola y el archivo `report.html`.
- **Error de API Zabbix: Invalid parameter "/": unexpected parameter "selectTriggers"**: **CORREGIDO** - Eliminado el parámetro no soportado `selectTriggers` de la consulta `event.get` en `get_events_history()`. Implementada estrategia de dos consultas:
  1. Primera consulta: `event.get` con `selectHosts: ["hostid", "name"]` para obtener eventos y nombres de hosts.
  2. Segunda consulta: `trigger.get` con los `objectid` obtenidos para recuperar detalles de triggers (triggerid, description, priority).
  3. Combinación de datos: Mapeo de triggers a eventos para enriquecer la información.
  4. Resultado: El informe ahora muestra correctamente los nombres de hosts y triggers, evitando "Desconocido", y genera el resumen de alertas tipo Top Triggers sin errores de API.

### Cambiado
- **MEMORIA.md**: Actualizado a versión 0.10.0 documentando la nueva Fase 9.3 con filtrado por intervalo de tiempo personalizado.
- **Versión**: Incrementada a 0.10.0 para reflejar la nueva funcionalidad de filtrado por intervalo de tiempo personalizado.
- Extendido el filtrado por intervalo de tiempo (`--time-from`, `--time-till`) a la tabla de "Estado del Entorno" (HostGroups) en `data_collector.py` y `zabbix_api.py`.

## [0.9.1] - 2026-11-05

### Añadido
- **Parámetro `limit` en `get_problems_history()` (`zabbix_api.py`)**: Añadido parámetro `limit` (por defecto 10000) a la consulta `problem.get` para evitar el límite por defecto de la API de Zabbix que restringía el número de resultados devueltos.
- **Propagación del parámetro `limit`**: Actualizados `data_collector.py` (`get_problems_history()`, `get_complete_report_data()`) y `main.py` para pasar explícitamente `limit=10000` y asegurar la obtención del histórico completo.

### Corregido
- **Histórico de Alertas incompleto (solo 2 problemas)**: Solucionado añadiendo el parámetro `limit` a `problem.get` para evitar el límite por defecto de la API. Ahora se recuperan correctamente tanto problemas activos como resueltos (histórico completo) dentro del rango temporal especificado.
- **Recuento total y tabla temporal**: Ahora reflejan fielmente ambos estados (activos y resueltos) en la consola y el archivo `report.html`.

### Cambiado
- **MEMORIA.md**: Actualizado a versión 0.9.1 documentando la corrección del parámetro `limit` en `problem.get` para histórico completo.
- **Versión**: Incrementada a 0.9.1 para reflejar la corrección crítica en la obtención del histórico completo de problemas.

## [0.9.0] - 2026-11-05

### Añadido
- **Estrategia de dos consultas en `get_problems_history()` (`zabbix_api.py`)**: Para compatibilidad con versiones de Zabbix que no soportan `selectHosts` en `problem.get`:
  1. Primera consulta: `problem.get` para histórico completo (activos + resueltos) con `r_eventid`, tags, suppression data.
  2. Segunda consulta: `event.get` con `eventids` y `selectHosts: ["hostid", "name"]` para obtener nombres de hosts.
  3. Procesamiento en lotes (batch size 500) para evitar límites de la API.
- **Nombres de host reales en informe**: Ahora las tablas muestran el nombre real del host en lugar de "Desconocido" en Resumen de Alertas, Enlaces GLPI y tabla Histórico + Activas.

### Corregido
- **Nombres de Host en "Desconocido"**: Solucionado mediante estrategia de doble consulta (`problem.get` + `event.get`) para recuperar hosts en versiones de Zabbix sin soporte `selectHosts` en `problem.get`.
- **Histórico de Alertas incompleto**: Confirmado que `problem.get` con `time_from`/`time_till` recupera correctamente tanto problemas activos como resueltos (histórico completo).

### Cambiado
- **MEMORIA.md**: Actualizado a versión 0.9.0 documentando la estrategia de dos consultas para selección de hosts y verificación del histórico.
- **Versión**: Incrementada a 0.9.0 para reflejar las correcciones críticas en la obtención de nombres de host y verificación del histórico.

## [0.8.0] - 2026-11-05

### Añadido
- **Método `get_problems_history()` en `zabbix_api.py`**: Nuevo método usando `problem.get` para obtener problemas históricos (activos y resueltos) con parámetros `time_from`/`time_till` (por defecto últimos 30 días), `selectSuppressionData` y `selectTags`.
- **Método `_enrich_problems()` en `data_collector.py`**: Lógica unificada de enriquecimiento para problemas activos e históricos (severidad textual, duración, host, tags, estado PROBLEM/OK, recovery_time).
- **Método `get_problems_history()` en `data_collector.py`**: Obtiene problemas históricos con caché inteligente (clave `problems_history`).
- **Agrupación y conteo en `format_problems_for_summary_table()`**: Agrupa problemas por `(host, descripción)` con campo `count` de ocurrencias, preservando timestamp más reciente para ordenación.
- **Filtrado GLPI en `get_glpi_links()`**: Extrae tag `__zbx_glpi_link`, parsea ticket IDs desde URLs completas (regex) o IDs directos, genera enlaces navegables a GLPI.
- **Banner actualizado en `report_generator.py`**: Muestra "Problemas Totales (Histórico)" y "Problemas Activos" por separado.
- **Columna "Veces" en Resumen de Alertas**: Tabla agrupada con conteo de ocurrencias por Host + Trigger/Alerta.
- **Columnas Host y Severidad en Enlaces GLPI**: Extracción desde tag `__zbx_glpi_link` con enlace directo a ticket.
- **Tabla "Histórico + Activas"**: Renombrada de "Alertas Activas", muestra badge de estado (PROBLEM/OK) y recovery_time para resueltas.
- **Flujo dual en `main.py`**: Obtiene `active_problems` (event.get) y `history_problems` (problem.get); usa históricos para resumen agrupado y tabla temporal; activos para resumen de entornos.

### Corregido
- **Estructura de datos unificada**: Separación clara entre problemas activos (para entornos) e históricos (para resumen y tabla temporal).
- **Manejo de problemas resueltos**: Campo `r_eventid` y `recovery_time` correctamente procesados para mostrar tiempo de recuperación.
- **Escape HTML**: Validación defensiva en todas las nuevas columnas de tablas HTML y consola.

### Cambiado
- **Resumen de Alertas**: De lista plana a tabla agrupada con conteo de ocurrencias (columna "Veces").
- **Enlaces GLPI**: De placeholder a tabla funcional con filtrado por tag `__zbx_glpi_link` y parsing de URLs/IDs.
- **Alertas Activas**: Renombrada a "Histórico + Activas" con columna Status y Recovery Time poblados.
- **Arquitectura de datos**: `DataCollector.get_complete_report_data()` ahora usa problemas históricos como fuente principal para resumen y tabla temporal.
- **CLI en `main.py`**: Descripción actualizada a "Fase 8: Histórico de Alertas, Resumen agrupado y GLPI".
- **MEMORIA.md**: Actualizado a versión 0.8.0 documentando problem.get histórico, agrupación con conteo, filtrado GLPI por tag, y nuevas estructuras de datos.

## [0.7.0] - 2026-11-05

### Añadido
- **Manejo robusto de red en `zabbix_api.py`**: Cliente ZabbixAPI mejorado con parámetros configurables (`timeout`, `max_retries`, `retry_delay`) y reintentos automáticos con backoff exponencial para errores transitorios.
- **Nuevo método `get_active_problems_raw()`**: Obtiene problemas crudos de la API (con campo `hosts` original) para asociación correcta por HostGroup en `DataCollector`.
- **Validación estricta de respuestas JSON-RPC**: Verificación de estructura de respuesta, detección de respuestas vacías, y clasificación de errores reintentables vs no reintentables.

### Corregido
- **Asociación problema-entorno en `data_collector.py`**: `group_problems_by_hostgroup()` ahora usa datos crudos de la API para acceder al campo `hosts` y asociar correctamente cada problema a su HostGroup.
- **Conteo de severidad en `get_environment_summary()`**: Conversión correcta de severidad numérica a texto usando `SEVERITY_MAP` del cliente Zabbix para desglose preciso por niveles.
- **Escape HTML en `report_generator.py`**: Función `_escape_html()` corregida para escapar comillas simples como entidad HTML numérica `'` (`s.replace("'", ''')`), previniendo inyección HTML.
- **Manejo de valores nulos/vacíos**: Validación defensiva en todas las tablas (HTML y consola) para evitar errores de renderizado.

### Cambiado
- **Arquitectura de datos**: Separación clara entre problemas "crudos" (con campo `hosts` para agrupación) y problemas "enriquecidos" (para visualización en tablas).
- **Cliente ZabbixAPI**: Constructor ahora acepta parámetros de configuración de red (`timeout=30`, `max_retries=3`, `retry_delay=1.0`).
- **MEMORIA.md**: Actualizado a versión 0.7.0 documentando mejoras de robustez, correcciones de asociación de datos, y refinamiento de salida de informe.
- **Flujo de datos**: `DataCollector` usa `get_active_problems_raw()` para agrupación y `get_active_problems()` (enriquecido) para tablas de resumen.

### Eliminado
- N/A

## [0.5.0] - 2026-11-05

### Añadido
- **Nuevo módulo `report_generator.py`**: Generación de informe visual completo en HTML y vista de consola formateada.
- **Clase `ReportGenerator`**: Motor de renderizado que transforma la estructura de datos de `DataCollector` en salida visual.
  - **Salida HTML** (`generate_html()`):
    - Documento HTML5 autocontenido con estilos CSS embebidos (sin dependencias externas).
    - **Banner superior**: Gradiente azul profesional con título, timestamp de generación, totales de hosts, problemas y entornos.
    - **Estado Entornos**: Grid responsivo de tarjetas por HostGroup con estadísticas clave (hosts, problemas totales, críticos) y desglose visual de 6 niveles de severidad con badges de color.
    - **Resumen de Alertas**: Tabla HTML con columnas Host, Trigger/Alerta, Severidad (badge color), Nombre de problemas.
    - **Enlaces GLPI**: Sección placeholder informativa (integración pendiente para fase futura).
    - **Alertas Activas**: Tabla temporal completa con 7 columnas (Time, Recovery Time, Status, Host, Severity, Trigger/Problem, Duration).
    - Badges de severidad codificados por color: 🔴 Desastre (#c0392b), 🟠 Alto (#e67e22), 🟡 Promedio (#f39c12), 🔵 Aviso (#2980b9), 🟢 Información (#1abc9c), ⚪ No clasificado (#7f8c8d).
    - Diseño responsive mobile-first con breakpoints en 768px, header sticky en tablas, hover effects.
  - **Salida Consola** (`print_console_report()`):
    - Banner ASCII con metadata alineada y separadores visuales.
    - Tablas formateadas con columnas alineadas usando f-strings y anchos fijos.
    - Mismo contenido, orden y estructura que la versión HTML.
    - Estados vacíos informativos con iconos SVG cuando no hay datos.
  - **Función unificada** `generate_report()`: Punto de entrada único para generar HTML, consola, o ambos.
- **Argumentos CLI en `main.py`**:
  - `--html ARCHIVO` / `-H ARCHIVO`: Guardar informe en archivo HTML.
  - `--no-console` / `-n`: Suprimir salida en consola (solo HTML).
  - `--url` / `-u`: URL de Zabbix (modo no interactivo).
  - `--user` / `-U`: Usuario de Zabbix (modo no interactivo).
- **Flujo completo Fase 5**: Autenticación → Recopilación (DataCollector) → Estructuración → Renderizado (ReportGenerator).

### Corregido
- **Escape HTML**: Función `_escape_html()` para prevenir inyección en salida HTML.
- **Manejo de valores nulos**: Validación defensiva en formateo de tablas (consola y HTML).
- **Error de sintaxis en `_escape_html()`**: Corregido string literal no terminado en `s.replace("'", ''')` (línea 616) cambiándolo a `s.replace("'", "'")` para escapar correctamente comillas simples como entidad HTML `'`.

### Cambiado
- **Arquitectura**: Separación completa en 4 capas - `ZabbixAPI` (comunicación) ↔ `DataCollector` (lógica/estructuración) ↔ `ReportGenerator` (renderizado) ↔ `main.py` (orquestación/CLI).
- **main.py**: Refactorizado para usar `argparse`, integrar `ReportGenerator`, y mostrar progreso por fases.
- **MEMORIA.md**: Actualizado a versión 0.5.0 documentando la lógica de renderizado del informe (HTML + Consola), estructura de secciones, badges de severidad, y diseño responsive.

### Eliminado
- N/A

## [0.4.0] - 2026-11-05

### Añadido
- **Nuevo módulo `data_collector.py`**: Arquitectura modular para recopilación y estructuración de datos, separando la lógica de negocio del punto de entrada principal.
- **Clase `DataCollector`**: Capa de abstracción que encapsula toda la lógica de obtención y asociación de datos desde Zabbix.
  - Sistema de **caché inteligente** para HostGroups, hosts por grupo y problemas activos, evitando consultas repetidas a la API.
  - Método `get_all_hostgroups()`: Obtiene grupos de hosts con caché.
  - Método `get_hosts_by_group(groupid)`: Obtiene hosts de un grupo con caché.
  - Método `get_all_hosts_by_group()`: Obtiene todos los hosts agrupados por su grupo.
  - Método `get_active_problems()`: Obtiene problemas activos enriquecidos con caché.
  - Método `get_hostgroup_map()`: Crea mapa `hostid -> groupid` para asociación rápida de problemas a entornos.
- **Agrupación de problemas por HostGroup/Entorno**:
  - Método `group_problems_by_hostgroup()`: Asocia cada problema activo a su HostGroup correspondiente.
  - Manejo de problemas sin grupo asociado mediante clave especial `'sin_grupo'`.
- **Resumen por Entorno (`get_environment_summary`)**:
  - Genera estructura de datos completa para la tabla "Estado Entornos".
  - Incluye: groupid, name, total_hosts, total_problems, desglose `problems_by_severity` (6 niveles: Desastre, Alto, Promedio, Aviso, Información, No clasificado), lista de hosts y problemas.
  - Ordenación por total de problemas descendente, luego por nombre.
- **Formateo de datos para tablas de resumen (preparado para HTML/PDF)**:
  - `format_problems_for_summary_table()`: Prepara datos para "Resumen de Alertas" (Host, Trigger/Alerta, Severidad, Nombre de problemas).
  - `format_problems_for_active_alerts_table()`: Prepara datos para "Alertas Activas" (Time, Recovery Time, Status, Host, Severity, Trigger/Problem, Duration) con ordenación temporal descendente.
- **Estructura completa de informe (`get_complete_report_data`)**:
  - Agrega todas las secciones en un diccionario único listo para renderizado en fases futuras.
  - Incluye: timestamp, total_problems, total_hosts, environments, alerts_summary, active_alerts, glpi_links (placeholder para fase futura).
- **Funciones de visualización en consola para las nuevas tablas**:
  - `print_environment_summary()`: Tabla de Estado Entornos con desglose por severidad y totales.
  - `print_alerts_summary_table()`: Tabla de Resumen de Alertas con columnas especificadas en requisitos.
  - `print_active_alerts_table()`: Tabla temporal de Alertas Activas con formato temporal completo.
- **Actualización de `main.py`**: Flujo principal refactorizado para usar la nueva arquitectura modular (`DataCollector`), generando las tres tablas de resumen requeridas.

### Corregido
- **Asociación problema-entorno**: Resuelto el filtrado de problemas por HostGroup mediante el mapa de hosts, permitiendo la visualización por entornos solicitada en los requisitos.

### Cambiado
- **Arquitectura**: Separación de responsabilidades - `ZabbixAPI` (comunicación API) ↔ `DataCollector` (lógica de negocio y estructuración) ↔ `main.py` (orquestación y presentación).
- **MEMORIA.md**: Actualizado a versión 0.4.0 documentando la arquitectura modular de recopilación de datos, métodos de la clase `DataCollector`, y las nuevas tablas de resumen implementadas.

### Eliminado
- N/A

## [0.3.0] - 2026-11-05

### Añadido
- **Consulta de Problemas Activos (event.get)**: Implementado método `get_active_problems` en `ZabbixAPI` usando `event.get` (compatible con más versiones de Zabbix), con parámetros `output`, `selectHosts`, `selectTags`, `value=1` para problemas activos.
- **Mapeo de Severidades**: Añadido diccionario `SEVERITY_MAP` para convertir severidades numéricas (0-5) a texto descriptivo (No clasificado, Información, Aviso, Promedio, Alto, Desastre).
- **Cálculo de Duración**: Implementado método auxiliar `_format_duration` para formatear la duración transcurrida en formato legible (días, horas, minutos, segundos).
- **Tabla Estructurada de Salida**: Nueva función `print_problems_table` que muestra los problemas en formato tabular con columnas: **Tiempo**, **Host**, **Severidad**, **Descripción**, **Duración**.
- **Enriquecimiento de Datos**: Los problemas incluyen ahora nombre del host, severidad textual, timestamp formateado y duración calculada dinámicamente.

### Corregido
- **Compatibilidad API**: Cambiado de `problem.get` a `event.get` para soportar el parámetro `selectHosts` en versiones de Zabbix donde `problem.get` no lo permite.

### Cambiado
- **main.py**: Actualizado el flujo principal para usar `get_active_problems` (event.get) en lugar de `get_active_alerts` (legacy), mostrando la nueva tabla estructurada.
- **ZabbixAPI**: Mantenido `get_active_alerts` (trigger.get) por compatibilidad, pero marcado como legacy.
- **MEMORIA.md**: Actualizado a versión 0.3.0 con detalles de la Fase 3 completada.

### Eliminado
- N/A

## [0.2.0] - 2026-11-05

### Añadido
- **Consulta de Alertas Activas**: Implementado método `get_active_alerts` en `ZabbixAPI` usando `trigger.get` para obtener problemas activos.
- **Consulta de Hosts por Grupo**: Implementado método `get_hosts_by_group` en `ZabbixAPI` usando `host.get`.
- **Visualización**: Añadida previsualización estructurada de alertas activas en la consola en `main.py`.

### Corregido
- **Autenticación**: Refactorizado `_make_request` para utilizar la cabecera HTTP `Authorization: Bearer <token>` en lugar de la propiedad `auth` en el payload JSON, cumpliendo con las mejores prácticas de la API de Zabbix.

### Cambiado
- **main.py**: Actualizado el flujo principal para incluir la consulta y visualización de alertas activas.

### Eliminado
- N/A

## [0.1.0] - 2026-11-05

### Añadido
- Creación de los archivos de control de contexto `MEMORIA.md` y `CHANGELOG.md`.
- Definición de la arquitectura inicial en Python 3 para desarrollo en local.
- Definición del flujo de autenticación dinámico (URL, usuario y contraseña mediante `user.login`).
- Definición del requerimiento de extracción dinámica de `HostGroups` para los paneles de entornos.
- **Estructura base del proyecto**: Creado `requirements.txt` con dependencia `requests>=2.31.0`.
- **Módulo principal `main.py`**:
  - Clase `ZabbixAPI` para comunicación JSON-RPC con Zabbix.
  - Solicitud interactiva de credenciales por consola (URL, usuario, contraseña con `getpass`).
  - Implementación del método `user.login` para autenticación y obtención de token de sesión.
  - Manejo robusto de errores (conexión, autenticación, respuestas inválidas).
- **Consulta de HostGroups**:
  - Implementación del método `hostgroup.get` con parámetros `output` y `sortfield`.
  - Listado por consola de todos los grupos de hosts (nombre e ID) ordenados alfabéticamente.
  - Validación de autenticación previa antes de consultar.

### Corregido
- N/A (versión inicial)

### Cambiado
- N/A (versión inicial)

### Eliminado
- N/A (versión inicial)
