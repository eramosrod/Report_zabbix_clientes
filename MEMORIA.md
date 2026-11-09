# Memoria del Proyecto: Generador de Informes Zabbix

## 1. Objetivo General
Desarrollar una aplicación en Python 3 para entorno local (con vista a empaquetar en Docker en fases posteriores) que se conecte a la API de Zabbix, capture datos en tiempo real de infraestructura y alertas, y genere un informe visual dinámico.

## 2. Requisitos y Especificaciones Técnicas
- **Lenguaje:** Python 3.
- **Entorno inicial:** Local (virtualenv).
- **Módulo de Login / Autenticación:** Interfaz previa que solicita dinámicamente:
  - URL de la API de Zabbix (`/api_jsonrpc.php`).
  - Usuario.
  - Contraseña.
- **Obtención Dinámica de Entornos:**
  - Los nombres de los paneles ("Estado Entornos") se obtienen dinámicamente mediante `hostgroup.get` a partir de los grupos de hosts configurados en Zabbix.
- **Secciones del Informe (basado en mockup visual):**
  1. Banner superior del informe.
  2. Estado de Entornos (bloques por HostGroups).
  3. Resumen de Alertas (Tabla: Host, Trigger / Alerta, Severidad, Nombre de problemas).
  4. Enlaces GLPI (Tabla de mapeo de tickets de soporte).
  5. Alertas Activas (Tabla temporal: Time, Recovery Time, Status, Host, Severity, Trigger/Problem, Duration).

## 3. Arquitectura del Proyecto
- `MEMORIA.md`: Documento vivo con las especificaciones y estado del proyecto.
- `CHANGELOG.md`: Registro histórico de avances y cambios implementados.
- `main.py`: Punto de entrada principal (autenticación, flujo del informe y argumentos CLI).
- `zabbix_api.py`: Cliente JSON-RPC para comunicación con API de Zabbix.
- `data_collector.py`: Módulo de recopilación y estructuración de datos (Fase 4).
  - Clase `DataCollector`: Encapsula toda la lógica de obtención y asociación de datos.
  - Caché inteligente para optimizar consultas repetidas a la API.
  - Métodos de agrupación por HostGroups y formateo para tablas de resumen.
- `report_generator.py`: Módulo de generación de informes visuales (Fase 5).
  - Clase `ReportGenerator`: Renderiza la estructura de datos en HTML y consola.
  - Función `generate_report()`: Punto de entrada unificado para ambas salidas.
  - Banner superior con metadata del informe.
  - Sección Estado Entornos: Tarjetas visuales por HostGroup con desglose de severidad.
  - Sección Resumen de Alertas: Tabla con Host, Trigger/Alerta, Severidad, Nombre de problemas.
  - Sección Enlaces GLPI: Placeholder para integración futura.
  - Sección Alertas Activas: Tabla temporal completa (Time, Recovery Time, Status, Host, Severity, Trigger/Problem, Duration).
  - Estilos CSS embebidos responsivos con badges de severidad codificados por color.
  - Vista de consola formateada con tablas alineadas y separadores.
- `requirements.txt`: Dependencias del proyecto (requests).

## 4. Estado Actual - Versión 0.17.0 (Fase 12 Completada)
### ✅ Implementado
- **Estructura base del proyecto** creada con `requirements.txt` (requests>=2.31.0).
- **Módulo de autenticación** en `main.py`:
  - Solicitud interactiva por consola de URL, usuario y contraseña (usando `getpass` para seguridad).
  - Implementación de cliente JSON-RPC para Zabbix (`ZabbixAPI` class).
  - Método `user.login` para autenticación y obtención de token de sesión.
  - **Refactorización**: Uso de cabecera HTTP `Authorization: Bearer <token>` en lugar de la propiedad `auth` en el JSON.
  - Manejo de errores de conexión y autenticación.
  - **NUEVO**: Soporte para argumentos CLI (`--url`, `--user`, `--html`, `--no-console`).
- **Consulta de HostGroups**:
  - Implementado método `hostgroup.get` para obtener lista de grupos de hosts.
  - Visualización por consola de todos los HostGroups encontrados (nombre e ID).
  - Ordenación alfabética por nombre.
- **Consulta de Alertas Activas (Legacy)**:
  - Implementado método `get_active_alerts` usando `trigger.get` filtrando por problemas activos (`value: 1`).
  - Visualización estructurada por consola (fecha, prioridad, descripción).
- **Consulta de Hosts por Grupo**:
  - Implementado método `get_hosts_by_group` usando `host.get`.
- **Consulta de Problemas Activos (Fase 3 - event.get)**:
  - Implementado método `get_active_problems` usando `event.get` (compatible con más versiones de Zabbix).
  - Parámetros: `output` (eventid, name, severity, clock), `selectHosts` (hostid, name), `selectTags`, `value=1` para solo problemas activos.
  - Enriquecimiento de datos: nombre del host, severidad textual (mapeo 0-5), cálculo de duración transcurrida.
  - Función auxiliar `_format_duration` para formatear duración en formato legible (días, horas, minutos, segundos).
- **Visualización Estructurada de Problemas (Fase 3)**:
  - Función `print_problems_table` para salida tabular por consola.
  - Columnas: **Tiempo** (inicio del problema), **Host**, **Severidad**, **Descripción**, **Duración**.
  - Ordenación por tiempo descendente (más recientes primero).
  - Totalizador de problemas activos.

### 🆕 **NUEVO en Fase 4 - Arquitectura Modular de Recopilación de Datos (`data_collector.py`)**:
- **Clase `DataCollector`**: Capa de abstracción que encapsula toda la lógica de recopilación y asociación de datos.
  - **Caché inteligente**: Evita consultas repetidas a la API almacenando HostGroups, hosts por grupo y problemas.
  - **Métodos principales**:
    - `get_all_hostgroups()`: Obtiene todos los grupos de hosts con caché.
    - `get_hosts_by_group(groupid)`: Obtiene hosts de un grupo con caché.
    - `get_all_hosts_by_group()`: Obtiene todos los hosts agrupados por grupo.
    - `get_active_problems()`: Obtiene problemas activos enriquecidos con caché.
    - `get_hostgroup_map()`: Crea mapa `hostid -> groupid` para asociación rápida.
- **Agrupación por Entornos (HostGroups)**:
  - `group_problems_by_hostgroup()`: Asocia cada problema a su HostGroup correspondiente mediante el mapa de hosts.
  - Manejo de problemas sin grupo asociado (clave `'sin_grupo'`).
- **Resumen por Entorno (`get_environment_summary`)**:
  - Genera estructura de datos completa para la tabla "Estado Entornos".
  - Incluye: groupid, name, total_hosts, total_problems, problems_by_severity (desglose por 6 niveles), hosts, problems.
  - Ordenación por total de problemas descendente.
- **Formateo para Tablas de Resumen**:
  - `format_problems_for_summary_table()`: Prepara datos para "Resumen de Alertas" (Host, Trigger/Alerta, Severidad, Nombre de problemas).
  - `format_problems_for_active_alerts_table()`: Prepara datos para "Alertas Activas" (Time, Recovery Time, Status, Host, Severity, Trigger/Problem, Duration).
  - Ordenación temporal descendente para alertas activas.
- **Estructura Completa de Informe (`get_complete_report_data`)**:
  - Agrega todas las secciones en un diccionario único listo para renderizado HTML/PDF.
  - Incluye: timestamp, total_problems, total_hosts, environments, alerts_summary, active_alerts, glpi_links (placeholder).
- **Funciones de Visualización en Consola**:
  - `print_environment_summary()`: Tabla de Estado Entornos con desglose por severidad.
  - `print_alerts_summary_table()`: Tabla de Resumen de Alertas.
  - `print_active_alerts_table()`: Tabla temporal de Alertas Activas.

### 🆕 **NUEVO en Fase 5 - Generación de Informe Visual (`report_generator.py`)**:
- **Clase `ReportGenerator`**: Motor de renderizado que transforma la estructura de datos en salida visual.
  - **Salida HTML** (`generate_html()`):
    - Documento HTML5 completo con estilos CSS embebidos (sin dependencias externas).
    - **Banner superior**: Gradiente azul, título, metadata (timestamp, totales hosts/problemas/entornos).
    - **Estado Entornos**: Grid responsivo de tarjetas por HostGroup con estadísticas (hosts, problemas, críticos) y desglose de 6 niveles de severidad con badges de color.
    - **Resumen de Alertas**: Tabla HTML con columnas Host, Trigger/Alerta, Severidad (badge color), Nombre de problemas.
    - **Enlaces GLPI**: Sección placeholder con estado "Pendiente" o tabla de tickets si hay datos.
    - **Alertas Activas**: Tabla temporal completa con 7 columnas (Time, Recovery Time, Status, Host, Severity, Trigger/Problem, Duration).
    - Badges de severidad codificados por color: 🔴 Desastre, 🟠 Alto, 🟡 Promedio, 🔵 Aviso, 🟢 Información, ⚪ No clasificado.
    - Diseño responsive (mobile-first) con breakpoints en 768px.
    - Tabla con header sticky y hover effects.
  - **Salida Consola** (`print_console_report()`):
    - Banner ASCII con metadata alineada.
    - Tablas formateadas con columnas alineadas y separadores visuales.
    - Mismo contenido y orden que la versión HTML.
    - Estados vacíos informativos cuando no hay datos.
  - **Función unificada** `generate_report()`: Punto de entrada único para ambas salidas.
  - **Corrección de sintaxis**: Arreglado error `SyntaxError: unterminated triple-quoted string literal` en `_escape_html()` - string literal `s.replace("'", ''')` corregido a `s.replace("'", "'")` para escapar comillas simples como entidad HTML `'`.
- **Integración en `main.py`**:
  - Argumentos CLI: `--html archivo.html` para exportar HTML, `--no-console` para solo HTML.
  - Flujo completo: Autenticación → Recopilación → Estructuración → Renderizado (HTML/Consola).
  - Mensajes de progreso por fase.

### 🆕 **NUEVO en Fase 7 - Optimización y Robustez (Versión 0.7.0)**:
- **Mejora en `zabbix_api.py` - Manejo robusto de red y errores**:
  - Parámetros configurables en constructor: `timeout` (default 30s), `max_retries` (default 3), `retry_delay` (default 1.0s con backoff exponencial).
  - Reintentos automáticos con backoff exponencial para errores transitorios (timeout, conexión, errores 5xx).
  - Detección y manejo de respuestas vacías del servidor.
  - Validación estricta de estructura JSON-RPC en respuestas.
  - Clasificación de errores: no reintentables (autenticación, parámetros inválidos) vs reintentables (red, servidor).
  - Nuevo método `get_active_problems_raw()` para obtener datos crudos de la API sin enriquecer (necesario para agrupación correcta por HostGroup).
- **Corrección en `data_collector.py` - Asociación precisa problema-entorno**:
  - `group_problems_by_hostgroup()` ahora usa `get_active_problems_raw()` para acceder al campo `hosts` original de la API.
  - `get_environment_summary()` convierte severidad numérica a texto usando `SEVERITY_MAP` del cliente Zabbix para conteo correcto.
  - Eliminada ambigüedad entre problemas enriquecidos (sin campo `hosts`) y problemas crudos (con campo `hosts`).
- **Corrección en `report_generator.py` - Escape HTML correcto**:
  - Función `_escape_html()` corregida: `s.replace("'", ''')` para escapar comillas simples como entidad HTML numérica `'`.
  - Previene inyección HTML y asegura renderizado correcto de caracteres especiales en todas las secciones.
- **Salida de informe refinada y limpia**:
  - Todas las secciones clave (Banner, Estado Entornos con nombres reales de HostGroups, Resumen de Alertas, Alertas Activas) se reflejan fielmente.
  - Manejo defensivo de valores nulos/vacíos en tablas HTML y consola.
  - Estados vacíos informativos con iconos SVG cuando no hay datos.

### 🆕 **NUEVO en Fase 8 - Histórico de Alertas, Resumen Agrupado y GLPI (Versión 0.8.0)**:
- **Método `get_problems_history()` en `zabbix_api.py`**:
  - Implementado usando `problem.get` para obtener problemas históricos (activos + resueltos).
  - Parámetros `time_from` y `time_till` para filtrado por rango temporal (por defecto últimos 30 días).
  - Incluye `selectHosts` para obtener nombres de hosts asociados, `selectSuppressionData` y `selectTags` para enriquecimiento completo.
  - Retorna campo `r_eventid` para identificar problemas resueltos y su tiempo de recuperación.
- **Mejoras en `data_collector.py`**:
  - Nuevo método `_enrich_problems()`: Lógica común de enriquecimiento para problemas activos e históricos (mapeo severidad, duración, host, tags, estado, tiempo de recuperación).
  - Nuevo método `get_problems_history()`: Obtiene problemas históricos con caché inteligente (clave `problems_history`).
  - **Agrupación y conteo en `format_problems_for_summary_table()`**: Agrupa problemas por tupla `(host, descripción)` contando ocurrencias (`count`), preservando el timestamp más reciente para ordenación.
  - **Filtrado GLPI en `get_glpi_links()`**: Extrae tag `__zbx_glpi_link` de los problemas, parsea ticket IDs desde URLs completas (regex) o IDs directos, genera enlaces GLPI navegables.
  - `format_problems_for_active_alerts_table()`: Ahora usa datos enriquecidos con `status` (PROBLEM/OK) y `recovery_time` para mostrar tanto alertas activas como resueltas.
  - `get_complete_report_data()`: Usa problemas históricos para tabla de resumen y tabla temporal; problemas activos solo para resumen de entornos y contador de activos; incluye `total_active_problems` y `glpi_links`.
- **Actualizaciones en `report_generator.py`**:
  - **Banner**: Muestra "Problemas Totales (Histórico)" y "Problemas Activos" por separado.
  - **Resumen de Alertas**: Nueva columna "Veces" con conteo de ocurrencias; tabla agrupada por Host + Trigger/Alerta.
  - **Enlaces GLPI**: Columnas Host y Severidad añadidas; extracción desde tag `__zbx_glpi_link` con enlace directo a ticket GLPI.
  - **Alertas Activas**: Renombrada a "Histórico + Activas"; muestra badge de estado (PROBLEM/OK) y tiempo de recuperación para resueltas.
  - **Salida consola**: Todas las tablas actualizadas para reflejar nuevas estructuras de datos (columnas Veces, Host/Severidad en GLPI, Status/Recovery Time en tabla temporal).
- **Actualización en `main.py`**:
  - Flujo dual: Obtiene `active_problems` (event.get) y `history_problems` (problem.get).
  - Usa `history_problems` para tabla de resumen agrupada y tabla temporal completa.
  - Usa `active_problems` solo para resumen de entornos y contador de problemas activos.
  - Mensajes de progreso actualizados y descripción CLI a "Fase 8".

### 🆕 **NUEVO en Fase 9 - Corrección de Nombres de Host y Histórico Completo (Versión 0.9.0)**:
- **Corrección en `zabbix_api.py` - `get_problems_history()`**:
  - Implementada estrategia de dos consultas para compatibilidad con versiones de Zabbix que no soportan `selectHosts` en `problem.get`:
    1. Primera consulta: `problem.get` para obtener histórico completo (activos + resueltos) con `r_eventid`, tags, etc.
    2. Segunda consulta: `event.get` con los `eventids` obtenidos y `selectHosts: ["hostid", "name"]` para recuperar nombres de hosts.
  - Procesamiento en lotes (batch size 500) para evitar límites de la API.
  - Esto permite mostrar el nombre real del host en lugar de "Desconocido" en todas las tablas del informe.
- **Corrección en `data_collector.py` - Enriquecimiento de problemas**:
  - El método `_enrich_problems()` ya estaba preparado para leer el campo `hosts` devuelto por la API.
  - Ahora los nombres de host se extraen correctamente del campo `hosts[0].name` de la respuesta combinada.
- **Verificación en `report_generator.py`**:
  - Confirmado que las tablas "Resumen de Alertas", "Enlaces GLPI" y "Histórico + Activas" muestran correctamente los nombres de host.
  - El histórico de problemas ahora incluye tanto problemas activos como resueltos correctamente.

### 🆕 **NUEVO en Fase 9.1 - Corrección de Histórico Completo de Problemas (Versión 0.9.1)**:
- **Corrección en `zabbix_api.py` - `get_problems_history()`**:
  - Añadido parámetro `limit` (por defecto 10000) a la consulta `problem.get` para evitar el límite por defecto de la API de Zabbix que restringía el número de resultados.
  - Eliminado el uso implícito de filtrado "recent" que podía limitar los resultados solo a problemas recientes.
  - La consulta ahora recupera el histórico completo de problemas (activos + resueltos) dentro del rango temporal especificado (`time_from` / `time_till`).
- **Actualización en `data_collector.py`**:
  - Método `get_problems_history()` actualizado para aceptar y propagar el parámetro `limit`.
  - Método `get_complete_report_data()` actualizado para aceptar y propagar el parámetro `limit`.
- **Actualización en `main.py`**:
  - Llamadas a `get_problems_history()` y `get_complete_report_data()` ahora pasan `limit=10000` explícitamente.
- **Resultado**: El informe ahora captura y cuenta correctamente tanto las alertas activas como las ya resueltas (histórico completo), reflejando fielmente el número total de incidencias históricas y resueltas en la consola y el archivo `report.html`.

### 🆕 **NUEVO en Fase 9 - Histórico tipo Top Triggers con event.get (Versión 0.9.0)**:
- **Nuevo método `get_events_history()` en `zabbix_api.py`**:
  - Implementado usando `event.get` para replicar exactamente la consulta del informe "Top Triggers" de Zabbix.
  - Parámetros clave configurados:
    - `source: 0` (eventos de disparadores/triggers)
    - `object: 0` (triggers)
    - `value: 1` (solo eventos de creación de problemas, para contar cada vez que salta la alerta)
    - `time_from`: Timestamp hacia atrás (por defecto últimos 30 días)
    - `selectHosts: ["hostid", "name"]` para obtener el nombre real del host
    - `selectTriggers: ["triggerid", "description", "priority"]` para obtener nombre y severidad del trigger
  - Permite obtener un recuento exacto y agrupado de las alertas por Host y Nombre de Trigger.
- **Nuevo método `_enrich_events()` en `data_collector.py`**:
  - Enriquece los eventos crudos de `event.get` extrayendo host (del campo `hosts[]`) y trigger (del campo `triggers[]`).
  - Convierte la prioridad del trigger a severidad textual usando `SEVERITY_MAP`.
  - Calcula duración y formatea timestamps.
- **Nuevo método `format_events_for_summary_table()` en `data_collector.py`**:
  - Agrupa **estrictamente por Host + Nombre del Trigger** (trigger_description).
  - Suma el recuento total de ocurrencias históricas (cada evento value=1 es una ocurrencia individual).
  - Ordena por conteo descendente y timestamp más reciente.
  - Replica fielmente la lógica de agrupación del informe "Top Triggers" de Zabbix.
- **Actualización en `get_complete_report_data()`**:
  - Ahora obtiene dos fuentes de datos separadas:
    1. `get_problems_history()` (problem.get) → para tabla temporal "Histórico + Activas" y enlaces GLPI (incluye resueltos con recovery_time).
    2. `get_events_history()` (event.get tipo Top Triggers) → para tabla "Resumen de Alertas" agrupada por Host + Trigger Name.
  - Añade campo `total_events` al informe para mostrar total de eventos de triggers.
- **Actualización en `main.py`**:
  - Flujo triple: Obtiene `active_problems` (event.get), `history_problems` (problem.get) y `history_events` (event.get tipo Top Triggers).
  - Usa `history_events` para la tabla de Resumen de Alertas (agrupación tipo Top Triggers).
  - Usa `history_problems` para tabla temporal y enlaces GLPI.
  - Usa `active_problems` solo para resumen de entornos y contador de activos.
  - Mensajes de progreso actualizados y descripción CLI a "Fase 9".
- **Actualización en `report_generator.py`**:
  - **Banner**: Muestra "Problemas Totales (Histórico problem.get)", "Eventos Totales (Histórico event.get - Top Triggers)" y "Problemas Activos" por separado.
  - **Resumen de Alertas**: Ahora agrupado estrictamente por Host + Trigger Name con conteo exacto de ocurrencias (tipo Top Triggers).
  - **Versión**: Incrementada a 0.9.0 en footer HTML y consola.
### 🆕 **NUEVO en Fase 9.2 - Histórico tipo Top Triggers con `event.get` (Versión 0.9.2)**:
- **Consulta de Histórico (`event.get`)**: Implementada consulta masiva de eventos (`source: 0`, `object: 0`, `value: 1`) para replicar el informe "Top Triggers" de Zabbix, capturando el histórico real de alertas (activas y resueltas).
- **Agrupación y Recuento**: Ajustada la lógica en `DataCollector` para agrupar estrictamente por par `(Host, Nombre del Trigger)`, sumando el recuento total de ocurrencias históricas.
- **Corrección de Parámetros**: **CORREGIDO** - Eliminado el parámetro no soportado `selectTriggers` de la consulta `event.get`. Implementada estrategia de dos consultas:
  1. Primera consulta: `event.get` con `selectHosts: ["hostid", "name"]` para obtener eventos y nombres de hosts.
  2. Segunda consulta: `trigger.get` con los `objectid` obtenidos para recuperar detalles de triggers (triggerid, description, priority).
  3. Combinación de datos: Mapeo de triggers a eventos para enriquecer la información.
- **Resultado**: El informe ahora muestra correctamente los nombres de hosts y triggers, evitando "Desconocido", y genera el resumen de alertas tipo Top Triggers sin errores de API.

### 🆕 **NUEVO en Fase 9.3 - Filtrado por Intervalo de Tiempo Personalizado (Versión 0.10.0)**
- **Nuevos Argumentos CLI** en `main.py`:
  - `--time-from`: Fecha/hora de inicio (formato: YYYY-MM-DD HH:MM:SS o timestamp Unix)
  - `--time-till`: Fecha/hora de fin (formato: YYYY-MM-DD HH:MM:SS o timestamp Unix)
  - Si no se especifican, se usa el rango por defecto (últimos 30 días)
- **Actualización en `zabbix_api.py`**:
  - Método `get_problems_history()`: Ahora acepta y usa parámetros `time_from` y `time_till` para filtrar problemas históricos por rango temporal.
  - Método `get_events_history()`: Ahora acepta y usa parámetros `time_from` y `time_till` para filtrar eventos históricos por rango temporal.
- **Actualización en `data_collector.py`**:
  - Método `group_problems_by_hostgroup()`: Ahora acepta y propaga parámetros `time_from` y `time_till` para filtrar problemas por grupo de hosts.
  - Método `get_environment_summary()`: Ahora acepta y propaga parámetros `time_from` y `time_till` para filtrar el resumen de entornos.
  - Método `get_problems_history()`: Ahora acepta y propaga parámetros `time_from` y `time_till`; usa caché solo cuando no hay filtros temporales.
  - Método `get_events_history()`: Ahora acepta y propaga parámetros `time_from` y `time_till`; usa caché solo cuando no hay filtros temporales.
  - Método `get_complete_report_data()`: Ahora acepta y propaga parámetros `time_from` y `time_till` a todas las consultas.
- **Actualización en `report_generator.py`**:
  - Clase `ReportGenerator`: Constructor ahora acepta parámetros `time_from` y `time_till`.
  - Sección `_get_banner_section()`: Muestra intervalo de tiempo formateado en banner HTML si está disponible.
  - Sección `_print_banner()`: Muestra intervalo de tiempo formateado en banner de consola si está disponible.
  - Función `generate_report()`: Ahora acepta y propaga parámetros `time_from` y `time_till`.
- **Resultado**: El informe ahora puede filtrar datos por cualquier rango temporal personalizado especificado por el usuario, mostrando el intervalo seleccionado en el banner del informe (tanto HTML como consola) y reflejando exclusivamente los datos dentro del rango seleccionado.
### 🆕 **NUEVO en Fase 9.4 - Nomenclatura Oficial de Severidades y Simplificación GLPI (Versión 0.11.0)**
- **Nomenclatura exacta de Severidades**: Modificado el mapeo `SEVERITY_MAP` en `zabbix_api.py` para utilizar exactamente los nombres oficiales de Zabbix en inglés en todo el informe:
  - `Information` (en lugar de Información/Info)
  - `Warning` (en lugar de Aviso)
  - `Average` (en lugar de Promedio)
  - `High` (en lugar de Alto)
  - `Disaster` (en lugar de Desastre)
  - `Not classified` (en lugar de No clasificado)
- **Actualización en `data_collector.py`**: Método `get_environment_summary()` y función `print_environment_summary()` actualizados para usar los nuevos nombres de severidad en la tabla de Estado de Entornos (tanto en HTML como en consola).
- **Actualización en `report_generator.py`**: Método `_get_severity_class()` actualizado para mapear los nuevos nombres en inglés a las clases CSS correspondientes (severity-disaster, severity-high, severity-average, severity-warning, severity-info, severity-notclassified).
- **Simplificación en la Tabla de Enlaces GLPI**: Eliminada la columna "Estado" (Abierto/Resuelto) de la sección de Enlaces GLPI en ambas salidas:
  - **HTML**: Tabla reducida a 5 columnas (Ticket ID, Título, Host, Severidad, Enlace) eliminando la columna Estado.
  - **Consola**: Salida simplificada mostrando solo Ticket, Título, Host, Severidad y URL (sin mención de Estado).
- **Resultado**: El informe ahora utiliza la nomenclatura oficial de Zabbix en inglés para todas las severidades, garantizando consistencia con la interfaz de Zabbix, y la sección GLPI muestra únicamente los datos esenciales del ticket, la alerta asociada, el host y la severidad con su enlace correspondiente.

### 🆕 **NUEVO en Fase 9.5 - Paleta de Colores Oficial Zabbix y Estados Visuales de Entornos (Versión 0.12.0)**
- **Paleta de colores oficial de Zabbix para severidades**: Actualizados los estilos CSS en `report_generator.py` para utilizar la paleta oficial de colores de Zabbix en las etiquetas de severidad (badges) del informe HTML:
  - `Information`: Azul (`#7499FF`)
  - `Warning`: Amarillo (`#FFC859`)
  - `Average`: Naranja (`#FFA15C`)
  - `High`: Rojo Claro (`#E97659`)
  - `Disaster`: Rojo Oscuro / Borgoña (`#E45959`)
  - `Not classified`: Gris (`#7f8c8d`) - sin cambios
- **Estados visuales dinámicos en "Estado de Entornos" (HostGroups)**: Implementada lógica condicional en `report_generator.py` para resaltar visualmente los entornos según su estado de alertas:
  - **Entornos con alertas activas** (`total_problems > 0`):
    - Borde izquierdo rojo (`#E45959`) de 5px en la tarjeta
    - Título del entorno en color rojo (`#E45959`)
    - Clase CSS `.env-card.has-alerts` y `.env-card-title.has-alerts`
  - **Entornos sin alertas activas** (`total_problems == 0`):
    - Borde izquierdo verde (`#1abc9c`) de 5px en la tarjeta
    - Título del entorno en color verde (`#1abc9c`)
    - Clase CSS `.env-card.no-alerts` y `.env-card-title.no-alerts`
- **Actualización en `report_generator.py`**:
  - Método `_get_html_header()`: Estilos CSS actualizados con nueva paleta Zabbix y clases para estados de entorno
  - Método `_get_environments_section()`: Lógica condicional para asignar clases CSS según `total_problems`
  - Método `_get_html_footer()` y `_print_footer_console()`: Versión actualizada a 0.12.0
- **Actualización en `main.py`**: Descripción CLI actualizada a "Fase 9.5" y mensajes de progreso actualizados.
- **Resultado**: El informe HTML ahora refleja fielmente la identidad visual de Zabbix mediante su paleta oficial de colores, y proporciona una indicación visual inmediata del estado de salud de cada entorno (HostGroup) mediante códigos de color rojo/verde, mejorando drásticamente la legibilidad y la capacidad de detección rápida de problemas.

### 🆕 **NUEVO en Fase 9.6 - Separación de Fuentes de Datos: Alertas Activas sin Filtro Temporal (Versión 0.13.0)**
- **Independencia del Margen de Tiempo para Alertas Activas**: La tabla de "Alertas Activas" **ya no se ve afectada** por el intervalo de tiempo personalizado (`--time-from` / `--time-till`). Ahora muestra **siempre todas las alertas que se encuentran activas en el sistema en el momento de la ejecución**, independientemente de las fechas introducidas.
- **Aplicación Selectiva del Margen de Tiempo**: El intervalo de tiempo elegido por el usuario (`--time-from` y `--time-till`) se aplica **exclusivamente** a:
  1. **Resumen de Alertas** (Top Triggers histórico - agrupado por Host + Trigger Name)
  2. **Estado de Entornos** (HostGroups - desglose por severidad)
  3. **Enlaces GLPI** (extraídos del histórico de problemas)
- **Modificaciones en `data_collector.py`**:
  - `get_active_problems()`: Ahora usa `_enrich_problems()` con datos crudos de `get_active_problems_raw()` para obtener información completa (status, recovery_time, is_resolved) **SIN filtro temporal**.
  - `get_complete_report_data()`: Desacopla las fuentes de datos:
    - `environment_summary` y `alerts_summary` usan datos históricos **CON filtro temporal** (`time_from`/`time_till`)
    - `active_alerts` usa `get_active_problems()` **SIN filtro temporal** (alertas activas actuales reales)
    - `glpi_links` se extrae del histórico de problemas **CON filtro temporal**
- **Modificaciones en `report_generator.py`**:
  - Sección "Alertas Activas": Renombrada de "Alertas (Tabla Temporal - Histórico + Activas)" a **"Alertas Activas"**
  - Banner: Muestra "Problemas Activos (Actuales)" y aclara "Intervalo (Resumen/Entornos)" para distinguir qué secciones usan el filtro
  - Títulos y badges actualizados para reflejar que la tabla muestra solo alertas activas actuales
  - Versión incrementada a 0.13.0 en footer HTML y consola
- **Modificaciones en `main.py`**:
  - Descripción CLI actualizada a "Fase 9.6"
  - Mensajes de progreso actualizados para indicar qué consultas usan filtro temporal y cuáles no
  - Argumentos `--time-from` y `--time-till` actualizados con ayuda descriptiva: "aplica a Resumen y Entornos"
- **Resultado**: El informe ahora proporciona una visión clara y separada: la tabla de Alertas Activas refleja el estado **real y actual** del sistema (independiente del rango temporal), mientras que el Resumen de Alertas y el Estado de Entornos permiten análisis histórico **filtrado por el intervalo elegido por el usuario**.

### 🆕 **NUEVO en Fase 9.7 - Simplificación de la Tabla "Estado de Entornos" en HTML (Versión 0.14.0)**
- **Tabla Simplificada de HostGroups en HTML**: La tabla de "Estado de Entornos" en el archivo `report.html` ahora muestra **únicamente dos columnas**: el **Nombre del Entorno** y el **Número de Problemas** (eliminando el desglose de columnas por cada severidad en el HTML).
- **Colores Dinámicos en el HTML**:
  - Si el número de problemas del entorno es mayor que 0 (`> 0`), la fila del entorno se resalta completamente en color **ROJO** (fondo `#fdeaea`, texto `#E45959`).
  - Si el entorno no tiene problemas (`0`), la fila se resalta completamente en color **VERDE** (fondo `#e8f8f5`, texto `#1abc9c`).
  - Clases CSS añadidas: `.env-row-has-alerts` y `.env-row-no-alerts`.
- **Respeto al formato de Consola**: La salida del informe en texto plano (consola) **conserva su formato actual** con el desglose de severidades (Information, Warning, Average, High, Disaster, Not classified), ya que este cambio estético simplificado afecta **únicamente al diseño del archivo HTML**.
- **Modificaciones en `report_generator.py`**:
  - Método `_get_environments_section()`: Reescrito para generar una tabla HTML simple con 2 columnas en lugar de tarjetas con desglose de severidad.
  - Método `_get_html_header()`: Añadidos estilos CSS para las nuevas clases de filas coloreadas dinámicamente.
  - Método `_get_html_footer()` y `_print_footer_console()`: Versión actualizada a 0.14.0.
- **Modificaciones en `main.py`**:
  - Descripción CLI actualizada a "Fase 9.7".
  - Mensajes de progreso actualizados.
  - Docstring actualizado con la nueva fase.
- **Resultado**: El informe HTML ahora presenta una vista resumida y visualmente inmediata del estado de los entornos, permitiendo detectar de un vistazo qué entornos tienen problemas (rojo) y cuáles están limpios (verde), mientras que la consola mantiene el detalle completo para análisis profundo.
- **NUEVO en Fase 10 - Simplificación de la Cabecera HTML**: La cabecera del informe HTML (`report.html`) ahora muestra **únicamente el título de la empresa** (ej: `Informe de Estado Zabbix - [Nombre de la Empresa]`), eliminando completamente:
  - Todos los iconos, emojis y metadatos secundarios (total de hosts, problemas totales, eventos totales, problemas activos, entornos)
  - El rango de tiempo o fechas ("Desde...", "Hasta...")
  - El logo del cliente (si está presente)
  - El timestamp de generación
  - **Respeto absoluto a la salida en consola (Bash)**: La salida en consola **no se modifica** y conserva exactamente el diseño actual con todos los metadatos, iconos y formato.
  - **Modificaciones en `report_generator.py`**:
    - Método `_get_banner_section()`: Reescrito para generar una cabecera HTML limpia con solo título de empresa (y logo opcional).
    - Método `_print_banner()`: Sin cambios (consola mantiene formato completo).
    - Método `_get_html_footer()` y `_print_footer_console()`: Versión actualizada a 0.15.0.
  - **Resultado**: El informe HTML ahora presenta una cabecera limpia y minimalista, mientras que la consola mantiene toda su información detallada para análisis completo.

### 🆕 **NUEVO en Fase 12 - Corrección Error expandDescription, Resolución de Macros y Filtrado de Triggers/Hosts Deshabilitados (Versión 0.17.0)**

#### 🐛 **Corrección Crítica: Error API Zabbix "expandDescription"**
- **Problema**: Al ejecutar `main.py`, la API de Zabbix devolvía el error: `Error API Zabbix: Invalid params. - Invalid parameter "/": unexpected parameter "expandDescription"`.
- **Causa**: El parámetro `expandDescription` ya no es válido en las consultas `event.get`, `problem.get` y `trigger.get` en versiones recientes de Zabbix (6.0+).
- **Solución**: Eliminado el parámetro `expandDescription` de todas las consultas API en `zabbix_api.py`:
  - `get_active_problems()` (event.get)
  - `get_active_problems_raw()` (problem.get)
  - `get_problems_history()` (problem.get)
  - `get_events_history()` (event.get + trigger.get)
  - `get_active_alerts()` (trigger.get - legacy)

#### 🔧 **Resolución Manual de Macros de Zabbix**
Se ha implementado el método `resolve_macros()` en `ZabbixAPI` para resolver macros comunes (`{HOST.NAME}`, `{ITEM.VALUE}`, `{TRIGGER.NAME}`, `{EVENT.TIME}`, etc.).
*Actualización (Versión 0.18.0):* Se han añadido `{ITEM.VALUE1}` y `{HOST.CONN}` para garantizar la consistencia total entre la salida por consola y el informe HTML generado.
- **Implementación**: Nuevo método `resolve_macros()` en la clase `ZabbixAPI` (`zabbix_api.py`).
- **Funcionalidad**: Resuelve macros comunes de Zabbix en textos (nombres de problemas, descripciones de triggers, nombres de eventos):
  - **Macros de Host**: `{HOST.NAME}`, `{HOST.HOST}`, `{HOST.IP}`, `{HOST.DNS}`, `{HOST.CONN}`, `{HOST.PORT}`
  - **Macros de Trigger**: `{TRIGGER.NAME}`, `{TRIGGER.DESCRIPTION}`, `{TRIGGER.STATUS}`, `{TRIGGER.SEVERITY}`, `{TRIGGER.PRIORITY}`, `{TRIGGER.URL}`
  - **Macros de Item**: `{ITEM.NAME}`, `{ITEM.KEY}`, `{ITEM.VALUE}`, `{ITEM.LASTVALUE}`
  - **Macros de Evento**: `{EVENT.ID}`, `{EVENT.NAME}`, `{EVENT.OPDATA}`, `{EVENT.VALUE}`, `{EVENT.STATUS}`, `{EVENT.TIME}`, `{EVENT.DATE}`
- **Integración**:
  - `_enrich_events()` en `data_collector.py` usa `resolve_macros()` para descripciones de triggers.
  - `_enrich_problems()` en `data_collector.py` usa `resolve_macros()` para nombres de problemas.
- **Resultado**: Los nombres de alertas/problemas en el informe HTML y consola ahora muestran valores reales en lugar de macros sin resolver (ej. `{HOST.NAME}` → "Servidor-Web-01").

#### 🚫 **Filtrado de Triggers y Hosts Deshabilitados**
- **Filtrado de Hosts (ya existente, reforzado)**: Se mantiene y refuerza el filtrado por `host.status = 0` (habilitado) en todas las consultas. Los problemas de hosts deshabilitados (status=1) se excluyen.
- **Filtrado de Triggers (NUEVO)**: Añadido filtrado por `trigger.status = 0` (habilitado) en:
  - `get_active_problems()`: Consulta adicional a `trigger.get` para obtener status y filtrar.
  - `get_active_problems_raw()`: Consulta adicional a `trigger.get` para obtener status y filtrar.
  - `get_problems_history()`: Consulta adicional a `trigger.get` para obtener status y filtrar.
  - `get_events_history()`: La consulta a `trigger.get` ya incluye `status` y se filtra en el mapeo.
- **Resultado**: El panel de alertas activas y el resumen histórico ahora excluyen correctamente cualquier trigger deshabilitado (status=1) o que pertenezca a un host deshabilitado (status=1).

#### 📝 **Archivos Modificados**
- **`zabbix_api.py`**:
  - Eliminado `expandDescription` de todos los parámetros de consultas API.
  - Añadido método `resolve_macros()` con soporte para macros comunes de Zabbix.
  - Añadido diccionario `COMMON_MACROS` de referencia.
  - Modificadas `get_active_problems()`, `get_active_problems_raw()`, `get_problems_history()`, `get_events_history()` para filtrar triggers deshabilitados.
- **`data_collector.py`**:
  - Actualizado `_enrich_events()` para resolver macros en `trigger_description`.
  - Actualizado `_enrich_problems()` para resolver macros en `name` del problema.
- **`CHANGELOG.md`**: Registrada versión 0.17.0 con detalles de correcciones y nuevas funcionalidades.

### 🆕 **NUEVO en Fase 13 - Corrección UnboundLocalError, Filtrado String/Integer y Triggers Deshabilitados en Alertas Activas (Versión 0.18.0)**

#### 🐛 **Corrección Crítica: UnboundLocalError en `get_events_history()`**
- **Problema**: Error `UnboundLocalError: cannot access local variable 'final_events' where it is not associated with a value` en `zabbix_api.py:646`.
- **Causa**: La variable `final_events` solo se definía dentro del bloque `if filtered_events:`, causando fallo cuando no había eventos filtrados (lista vacía).
- **Solución**: Inicializada `final_events = []` antes del bloque condicional `if filtered_events:`.

#### 🔧 **Corrección de Filtrado: String vs Integer en campos `status`**
- **Problema**: La API de Zabbix devuelve los campos `status` (host y trigger) como **strings** ("0"/"1"), no enteros. El filtrado `h.get("status") == 0` fallaba silenciosamente (comparación string vs int), permitiendo que hosts/triggers deshabilitados pasaran el filtro.
- **Solución**: Corregido en **4 ubicaciones** usando `str(h.get("status", "0")) == "0"` para manejar ambos tipos y default a habilitado:
  1. `get_active_problems()` - líneas ~259, ~289
  2. `get_active_problems_raw()` - líneas ~460, ~488
  3. `get_problems_history()` - líneas ~589, ~605
  4. `get_events_history()` - líneas ~690, ~708

#### 🚫 **Filtrado de Triggers Deshabilitados en `get_active_problems_raw()` (Tabla "Alertas Activas")**
- **Problema**: El método `get_active_problems_raw()` (usado para la tabla "Alertas Activas") solo filtraba por estado de host, **NO por estado de trigger**. Los triggers deshabilitados (status=1) aparecían en el informe.
- **Causa Raíz Adicional**: La consulta `problem.get` no devolvía `objectid` (triggerid) por defecto, impidiendo consultar `trigger.get` para obtener el status.
- **Solución**:
  1. Añadido `"objectid"` al parámetro `output` en `problem.get` (línea ~406).
  2. Implementado filtrado de triggers deshabilitados consultando `trigger.get` con los `objectid` obtenidos (líneas ~468-501).
- **Verificación**: Debug confirmó filtrado correcto:
  - Trigger 32671 (status='1' deshabilitado) → **FILTRADO**
  - Trigger 32758 (status='0' habilitado) → **MANTENIDO**
  - Resultado: Informe muestra "1 alertas activas actuales" en lugar de 2.

#### 🧹 **Limpieza de Código de Producción**
- Eliminados todos los `print(f"DEBUG: ...")` de depuración añadidos durante la investigación del bug.

#### 📝 **Archivos Modificados**
- **`zabbix_api.py`**:
  - `get_events_history()`: Inicializada `final_events = []` antes del bloque `if filtered_events:`.
  - `get_active_problems()`: Filtrado host/trigger usando `str(status) == "0"`.
  - `get_active_problems_raw()`: Añadido `"objectid"` a `output` + filtrado de triggers deshabilitados.
  - `get_problems_history()`: Filtrado host/trigger usando `str(status) == "0"`.
  - `get_events_history()`: Filtrado host/trigger usando `str(status) == "0"`.
  - Eliminados todos los `print(f"DEBUG: ...")` de depuración.
- **`CHANGELOG.md`**: Registrada versión 0.18.0 con detalles de correcciones.
- **`MEMORIA.md`**: Actualizada con documentación técnica de la Fase 13.

### 🔄 Próximos Pasos (Fase 9+)
- Exportación a CSV/Excel.
- Filtros avanzados por severidad, entorno, rango temporal.
- Empaquetado Docker.
- Generación de PDF (vía wkhtmltopdf o weasyprint).
- Programación periódica (cron/systemd timer).
- **NUEVO en Fase 11 - Documentación Técnica y Guía de Personalización**:
  - `DOC_TECNICA.md`: Documentación completa del sistema multi-cliente
  - `GUIA_CUSTOMIZACION.md`: Guía detallada para modificar, adaptar y extender el script y los informes
  - Ambos documentos creados en la raíz del proyecto para facilitar el mantenimiento y la extensión


