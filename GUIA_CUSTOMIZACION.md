# Guía de Personalización y Extensión - Generador de Informes Zabbix

## 1. Modificación de Plantillas Visuales (HTML/CSS)

### 1.1 Ajustar Colores de Severidad de Zabbix

El informe HTML utiliza la paleta oficial de colores de Zabbix. Para modificar los colores:

#### 1.1.1 Modificar Colores en `report_generator.py`

```python
# En la clase ReportGenerator, método _get_html_header()
# Localizar las definiciones de colores en el bloque <style>

# Ejemplo: Cambiar color de Disaster de #E45959 a #FF0000 (rojo puro)
.severity-disaster {
    background: #FF0000;  /* Cambiar de #E45959 */
    color: white;
}

# Ejemplo: Cambiar color de Information de #7499FF a #0066CC (azul más oscuro)
.severity-info {
    background: #0066CC;  /* Cambiar de #7499FF */
    color: white;
}
```

#### 1.1.2 Modificar Tipografía

```css
/* En _get_html_header(), dentro del bloque <style> */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    /* Cambiar a fuente personalizada */
    font-family: 'Roboto', 'Arial', sans-serif;
}

/* Para títulos */
.banner h1 {
    font-family: 'Roboto Bold', sans-serif;
    font-size: 2.5rem;  /* Aumentar tamaño */
}
```

### 1.2 Modificar Encabezado HTML

#### 1.2.1 Agregar Campos Adicionales

```python
# En report_generator.py, método _get_banner_section()

def _get_banner_section(self) -> str:
    # Agregar metadata adicional
    additional_info = f'''
    <div class="banner-extra">
        <span>📊 Total Hosts: {self.total_hosts}</span>
        <span>⚠️ Problemas: {self.total_problems}</span>
        <span>🔍 Eventos: {self.total_events}</span>
    </div>
    '''
    
    # Modificar el HTML del banner
    return f'''
    <div class="banner">
        <div style="display: flex; align-items: center;">
            {logo_html}
            <div>
                <h1>Informe de Estado Zabbix - {self._escape_html(self.client_empresa)}</h1>
                {additional_info}
            </div>
        </div>
    </div>'''
```

#### 1.2.2 Quitar Elementos del Encabezado

```python
# Para remover el logo (mantener solo título)
def _get_banner_section(self) -> str:
    # Descomentar para remover logo
    # logo_html = ""
    
    return f'''
    <div class="banner">
        <h1>Informe de Estado Zabbix - {self._escape_html(self.client_empresa)}</h1>
    </div>'''
```

## 2. Personalización del Banner en Consola (Bash)

### 2.1 Modificar Texto/ASCII Art

#### 2.1.1 Editar `enviar_reporte.sh`

```bash
# En la sección de banner del script (líneas 98-130)

echo "[$(date)] Generando informe para: $CLIENTE...]"

# Personalizar mensaje
CUSTOM_MESSAGE="[$(date)] 📊 GENERANDO INFORME EJECUTIVO ZABBIX - Cliente: $CLIENTE"
echo "$CUSTOM_MESSAGE"

# Agregar ASCII art personalizado
ASCII_ART="
╔══════════════════════════════════════════════════════════════╗
║           SISTEMA DE INFORMES ZABBIX MULTI-CLIENTE          ║
╚══════════════════════════════════════════════════════════════╝
"
echo -e "$ASCII_ART"
```

#### 2.1.2 Modificar Banner en `main.py`

```python
# En main.py, línea 127-130 (banner de cliente)

print("=" * 60)
print(f"  GENERADOR DE INFORMES ZABBIX - Cliente: {empresa}")
print("=" * 60)

# Personalizar con ASCII art adicional
print()
print("  ╔══════════════════════════════════════════════════════════════╗")
print("  ║              INFORME EJECUTIVO ZABBIX                        ║")
print("  ╚══════════════════════════════════════════════════════════════╝")
print()
```

## 3. Extensión de Consultas a la API de Zabbix

### 3.1 Agregar Nuevo Endpoint `item.get`

#### 3.1.1 Modificar `zabbix_api.py`

```python
# Agregar nuevo método a la clase ZabbixAPI

def get_items(self, hostids: list = None, itemids: list = None) -> list:
    """
    Obtiene items (métricas) de Zabbix.
    
    Args:
        hostids: Lista de IDs de hosts
        itemids: Lista de IDs de items
        
    Returns:
        Lista de items con información detallada
    """
    if not self.auth_token:
        raise Exception("No autenticado. Llame a login() primero.")
    
    params = {
        "output": ["itemid", "hostid", "name", "key_", "value_type", "units", "lastclock"],
        "selectTags": ["tag", "value"],
        "selectHosts": ["hostid", "name"]
    }
    
    if hostids:
        params["hostids"] = hostids
    if itemids:
        params["itemids"] = itemids
        
    return self._make_request("item.get", params)
```

#### 3.1.2 Integrar en `data_collector.py`

```python
# Agregar método a la clase DataCollector

def get_items_by_host(self, hostid: str) -> list:
    """
    Obtiene todos los items (métricas) de un host específico.
    
    Args:
        hostid: ID del host
        
    Returns:
        Lista de items del host
    """
    return self.zabbix.get_items(hostids=[hostid])

def get_all_items(self) -> list:
    """
    Obtiene todos los items de todos los hosts.
    
    Returns:
        Lista completa de items
    """
    hostgroups = self.get_all_hostgroups()
    all_items = []
    
    for group in hostgroups:
        hosts = self.get_hosts_by_group(group['groupid'])
        for host in hosts:
            items = self.get_items_by_host(host['hostid'])
            for item in items:
                item['host_name'] = host['name']
                item['group_name'] = group['name']
                all_items.append(item)
                
    return all_items
```

### 3.2 Agregar Nuevo Endpoint `trend.get`

#### 3.2.1 Modificar `zabbix_api.py`

```python
# Agregar método para tendencias
def get_trends(self, itemids: list = None, time_from: int = None, time_till: int = None) -> list:
    """
    Obtiene tendencias (datos históricos) de items.
    
    Args:
        itemids: Lista de IDs de items
        time_from: Timestamp de inicio
        time_till: Timestamp de fin
        
    Returns:
        Lista de tendencias
    """
    if not self.auth_token:
        raise Exception("No autenticado. Llame a login() primero.")
    
    params = {
        "output": ["trendid", "itemid", "clock", "value_avg", "value_min", "value_max"],
        "selectItems": ["itemid", "name", "key_"],
        "time_from": time_from,
        "time_till": time_till
    }
    
    if itemids:
        params["itemids"] = itemids
        
    return self._make_request("trend.get", params)
```

### 3.3 Agregar Nuevos Filtros por Tags

#### 3.3.1 Modificar `zabbix_api.py`

```python
def get_problems_by_tags(self, tags: list, time_from: int = None, time_till: int = None) -> list:
    """
    Obtiene problemas filtrados por tags específicos.
    
    Args:
        tags: Lista de diccionarios con formato {"tag": "tag_name", "value": "tag_value"}
        time_from: Timestamp de inicio
        time_till: Timestamp de fin
        
    Returns:
        Lista de problemas con tags específicos
    """
    if not self.auth_token:
        raise Exception("No autenticado. Llame a login() primero.")
    
    params = {
        "output": ["eventid", "name", "severity", "clock"],
        "selectHosts": ["hostid", "name"],
        "selectTags": ["tag", "value"],
        "tags": tags,
        "time_from": time_from,
        "time_till": time_till
    }
    
    return self._make_request("event.get", params)
```

#### 3.3.2 Modificar `data_collector.py`

```python
# Agregar método para filtrado por tags
def get_problems_by_environment_tags(self, tag_filters: list, time_from: int = None, time_till: int = None) -> list:
    """
    Obtiene problemas filtrados por tags de entorno específicos.
    
    Args:
        tag_filters: Lista de filtros de tags (ej: [{"tag": "entorno", "value": "producción"}])
        time_from: Timestamp de inicio
        time_till: Timestamp de fin
        
    Returns:
        Problemas filtrados por tags
    """
    # Usar el nuevo método de la API
    raw_problems = self.zabbix.get_problems_by_tags(tag_filters, time_from, time_till)
    return self._enrich_problems(raw_problems)
```

## 4. Incorporación de Nuevos Clientes

### 4.1 Guía Paso a Paso

#### 4.1.1 Agregar Nuevo Cliente a `clients.json`

```json
{
  "cliente_a": {
    "empresa": "Acme Corp S.A.",
    "logo_path": "assets/logos/acme.png",
    "zabbix_url": "http://192.168.1.23/zabbix/api_jsonrpc.php",
    "zabbix_user": "zabbix_reporter",
    "zabbix_pass": "A.bast2026"
  },
  "cliente_b": {
    "empresa": "Global Logistics S.L.",
    "logo_path": "assets/logos/global.png",
    "zabbix_url": "http://192.168.1.23/zabbix/api_jsonrpc.php",
    "zabbix_user": "reporter_b",
    "zabbix_pass": "password_b"
  },
  "nuevo_cliente": {
    "empresa": "Tech Innovations Inc.",
    "logo_path": "assets/logos/tech_innovations.png",
    "zabbix_url": "http://192.168.1.24/zabbix/api_jsonrpc.php",
    "zabbix_user": "reporter_nuevo",
    "zabbix_pass": "nueva_contraseña_segura"
  }
}
```

#### 4.1.2 Colocar Logotipo

```bash
# 1. Crear directorio si no existe
mkdir -p assets/logos

# 2. Colocar el logotipo (ejemplo: tech_innovations.png)
# Asegurarse de que el archivo esté en la raíz del proyecto

# 3. Verificar que el logotipo sea accesible
ls -la assets/logos/
# Debe mostrar: -rw-r--r-- 1 usuario grupo 245K Abr 08 20:07 tech_innovations.png

# 4. Probar nuevo cliente
python3 main.py --client nuevo_cliente --html informe_nuevo.html
```

### 4.2 Configurar Permisos de Logotipo

```bash
# Asegurarse de que el logotipo sea legible por el usuario que ejecuta el script
chmod 644 assets/logos/tech_innovations.png

# Si el script se ejecuta como root, puede necesitar permisos más permisivos
# chmod 664 assets/logos/tech_innovations.png
```

## 5. Ajustes de Envío y Destinatarios

### 5.1 Hacer Dinámicos los Destinatarios desde `clients.json`

#### 5.1.1 Modificar `enviar_reporte.sh`

```bash
#!/bin/bash

# ==============================================================================
# SCRIPT DE AUTOMATIZACIÓN Y ENVÍO DE INFORMES ZABBIX MULTI-CLIENTE
# ==============================================================================

# --- Configuración de Entorno ---
PROJ_DIR="/home/eramos/proyectos_git/Report_clientes"
PYTHON_BIN="/usr/bin/python3"
SCRIPT_NAME="main.py"

# --- Parámetros de Ejecución ---
CLIENTE="${1:-cliente_a}"  # Acepta el cliente por parámetro $1
HTML_REPORT="report_${CLIENTE}.html"

# --- Cargar destinatarios desde clients.json ---
# Extraer destinatarios del archivo de configuración
DESTINATARIOS=$(python3 -c "
import json
import sys
with open('clients.json', 'r') as f:
    clients = json.load(f)
if '$CLIENTE' in clients:
    cliente = clients['$CLIENTE']
    # Extraer emails del campo 'emails' si existe, o usar default
    emails = cliente.get('emails', ['admin@tudominio.com'])
    print('; '.join(emails))
else:
    print('admin@tudominio.com')
")

# --- Configurar asunto del correo ---
ASUNTO="[Zabbix] Informe de Estado y Alertas - ${CLIENTE^^}"

# --- Navegación al directorio de trabajo ---
cd "$PROJ_DIR" || { echo "Error: No se pudo acceder a $PROJ_DIR"; exit 1; }

echo "[$(date)] Generando informe para: $CLIENTE..."
echo "[$(date)] Enviando a: $DESTINATARIOS"

# 1. Ejecutar el script Python y capturar el resumen de consola
OUTPUT_TXT=$( $PYTHON_BIN $SCRIPT_NAME --client "$CLIENTE" --html "$HTML_REPORT" 2>&1 )
EXIT_CODE=$?

# 2. Validar que la ejecución de Python finalizó sin errores
if [ $EXIT_CODE -ne 0 ]; then
    echo "Error crítico durante la generación del informe para $CLIENTE:" >&2
    echo "$OUTPUT_TXT" >&2
    exit 1
fi

# 3. Validar existencia del fichero HTML generado
if [ -f "$HTML_REPORT" ]; then
    echo "[$(date)] Fichero $HTML_REPORT generado. Enviando correo..."
    
    # 4. Envío con Mutt (destinatarios dinámicos)
    echo "$OUTPUT_TXT" | mutt -s "$ASUNTO" -a "$HTML_REPORT" -- $DESTINATARIOS
    
    if [ $? -eq 0 ]; then
        echo "[$(date)] ¡Correo enviado con éxito a $DESTINATARIOS!"
    else
        echo "Error: Falló el envío del correo con mutt." >&2
        exit 1
    fi
else
    echo "Error: No se encontró el archivo adjunto $HTML_REPORT" >&2
    exit 1
fi
```

#### 5.1.2 Actualizar `clients.json` con Destinatarios

```json
{
  "cliente_a": {
    "empresa": "Acme Corp S.A.",
    "logo_path": "assets/logos/acme.png",
    "zabbix_url": "http://192.168.1.23/zabbix/api_jsonrpc.php",
    "zabbix_user": "zabbix_reporter",
    "zabbix_pass": "A.bast2026",
    "emails": ["gerente@acme.com", "admin@acme.com", "soporte@acme.com"]
  },
  "cliente_b": {
    "empresa": "Global Logistics S.L.",
    "logo_path": "assets/logos/global.png",
    "zabbix_url": "http://192.168.1.23/zabbix/api_jsonrpc.php",
    "zabbix_user": "reporter_b",
    "zabbix_pass": "password_b",
    "emails": ["director@global.com", "equipo@global.com"]
  }
}
```

### 5.2 Agregar Campo de Asunto Personalizado

```bash
# En enviar_reporte.sh, agregar campo asunto personalizado
ASUNTO="[Zabbix] ${CLIENTE^^} - Informe de Estado ${fecha_formateada}"

# O usar template desde clients.json
ASUNTO_TEMPLATE="${CLIENTE_CONFIG['asunto_template']}"
ASUNTO="$ASUNTO_TEMPLATE".replace("{empresa}", "{empresa}").replace("{fecha}", "$fecha")
```

## 6. Ejemplos de Personalización Avanzada

### 6.1 Agregar Sección GLPI Personalizada

```python
# En report_generator.py, método _get_glpi_links_section()

def _get_glpi_links_section(self) -> str:
    """Genera la sección de Enlaces GLPI con formato personalizado."""
    if not self.glpi_links:
        return '''
        <!-- ENLACES GLPI -->
        <div class="section">
            <div class="section-header">
                <h2>Enlaces GLPI</h2>
                <span class="badge">Sin tickets</span>
            </div>
            <div class="section-content">
                <div class="empty-state">
                    <p>No se encontraron problemas con el tag '__zbx_glpi_link'.</p>
                </div>
            </div>
        </div>'''
    
    # Agregar columna personalizada para prioridad
    rows = []
    for link in self.glpi_links:
        severity_class = self._get_severity_class(link.get('severity', ''))
        priority = link.get('priority', 'Media')  # Campo personalizado
        rows.append(f'''
        <tr>
            <td>{self._escape_html(link.get('ticket_id', ''))}</td>
            <td>{self._escape_html(link.get('title', ''))}</td>
            <td>{self._escape_html(link.get('host', ''))}</td>
            <td><span class="severity {severity_class}">{self._escape_html(link.get('severity', ''))}</span></td>
            <td><span class="priority-badge priority-{priority.lower()}">{priority}</span></td>
            <td><a href="{self._escape_html(link.get('url', '#'))}" target="_blank">Ver en GLPI</a></td>
        </tr>''')
    
    return f'''
    <!-- ENLACES GLPI -->
    <div class="section">
        <div class="section-header">
            <h2>Enlaces GLPI (Tag __zbx_glpi_link)</h2>
            <span class="badge">{len(self.glpi_links)} tickets</span>
        </div>
        <div class="section-content">
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Ticket ID</th>
                            <th>Título</th>
                            <th>Host</th>
                            <th>Severidad</th>
                            <th>Prioridad</th>
                            <th>Enlace</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows)}
                    </tbody>
                </table>
            </div>
        </div>
    </div>'''
```

### 6.2 Agregar Filtros de Tiempo Personalizados

```python
# En main.py, agregar nuevos argumentos CLI

def parse_args():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Generador de Informes Zabbix - Fase 10')
    parser.add_argument('--client', '-c', metavar='NOMBRE', help='Nombre del cliente (definido en clients.json)')
    parser.add_argument('--html', '-H', metavar='ARCHIVO', help='Guardar informe en archivo HTML')
    parser.add_argument('--no-console', '-n', action='store_true', help='No mostrar informe en consola')
    parser.add_argument('--url', '-u', help='URL del servidor Zabbix (ej: https://zabbix.example.com) - modo legacy')
    parser.add_argument('--user', '-U', help='Usuario de Zabbix - modo legacy')
    
    # Nuevos filtros de tiempo personalizados
    parser.add_argument('--periodo', choices=['hoy', 'semana', 'mes', 'trimestre'], 
                       help='Período predefinido: hoy, semana, mes, trimestre')
    parser.add_argument('--desde', help='Fecha/hora de inicio personalizada (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--hasta', help='Fecha/hora de fin personalizada (YYYY-MM-DD HH:MM:SS)')
    
    parser.add_argument('--time-from', help='Fecha/hora de inicio (YYYY-MM-DD HH:MM:SS o timestamp) - aplica a Resumen y Entornos', type=parse_time)
    parser.add_argument('--time-till', help='Fecha/hora de fin (YYYY-MM-DD HH:MM:SS o timestamp) - aplica a Resumen y Entornos', type=parse_time)
    return parser.parse_args()
```

```python
# En main.py, método main() para manejar nuevos filtros
def main():
    args = parse_args()
    
    # Calcular time_from/time_till basado en período o fechas personalizadas
    time_from = args.time_from
    time_till = args.time_till
    
    if args.periodo:
        # Calcular según período seleccionado
        now = datetime.now().timestamp()
        if args.periodo == 'hoy':
            time_from = now - (24 * 3600)  # Últimas 24 horas
        elif args.periodo == 'semana':
            time_from = now - (7 * 24 * 3600)  # Última semana
        elif args.periodo == 'mes':
            time_from = now - (30 * 24 * 3600)  # Último mes
        elif args.periodo == 'trimestre':
            time_from = now - (90 * 24 * 3600)  # Últimos 90 días
    
    # ... resto del código existente ...
```

## 7. Mantenimiento y Actualización de Personalizaciones

### 7.1 Verificar Personalizaciones Después de Actualizaciones

```bash
# 1. Verificar sintaxis de Python
python3 -m py_compile main.py
python3 -m py_compile zabbix_api.py
python3 -m py_compile data_collector.py
python3 -m py_compile report_generator.py

# 2. Verificar JSON
python3 -m json.tool clients.json > /dev/null && echo "clients.json es válido"

# 3. Probar script
chmod +x enviar_reporte.sh
./enviar_reporte.sh cliente_a
```

### 7.2 Documentar Personalizaciones

```bash
# Agregar notas de personalización a MEMORIA.md
# Ejemplo:

## Personalizaciones Realizadas

### 1. Extensión de API con item.get y trend.get
- **Archivo**: zabbix_api.py
- **Métodos añadidos**: get_items(), get_trends()
- **Uso**: Permite incluir métricas y tendencias en los informes

### 2. Filtros de destinatarios dinámicos
- **Archivo**: enviar_reporte.sh
- **Cambio**: Extraer emails desde clients.json
- **Beneficio**: Cada cliente puede tener diferentes destinatarios

### 3. Colores personalizados de severidad
- **Archivo**: report_generator.py
- **Cambio**: Modificar paleta de colores en _get_html_header()
- **Resultado**: Colores de informe personalizados para marca corporativa
```

## 8. Resumen de Comandos de Personalización Rápida

### 8.1 Modificar Colores

```bash
# Editar report_generator.py
nano report_generator.py
# Buscar .severity-disaster, .severity-info, etc.
```

### 8.2 Agregar Nuevo Cliente

```bash
# 1. Editar clients.json
nano clients.json
# 2. Agregar nuevo cliente
# 3. Colocar logotipo en assets/logos/
# 4. Probar: python3 main.py --client nuevo_cliente --html informe.html
```

### 8.3 Modificar Banner de Consola

```bash
# Editar enviar_reporte.sh
nano enviar_reporte.sh
# Personalizar sección de banner (líneas 98-130)
```

### 8.4 Agregar Nuevo Endpoint API

```bash
# 1. Editar zabbix_api.py
nano zabbix_api.py
# 2. Agregar nuevo método
# 3. Editar data_collector.py para integrar
# 4. Probar con Python
python3 -c "from zabbix_api import ZabbixAPI; api = ZabbixAPI('http://ejemplo.com'); print('API OK')"
```

### 8.5 Verificar Configuración

```bash
# Verificar estructura del proyecto
ls -la

# Verificar clientes.json
python3 -m json.tool clients.json

# Verificar sintaxis Python
python3 -m py_compile main.py data_collector.py zabbix_api.py report_generator.py

# Probar generación de informe
python3 main.py --client cliente_a --html prueba.html
```

---
*Guía de Personalización - Versión 0.16.0*
*Fecha: 2026-11-08*
*Autor: Ingeniero Lead - Sistema de Informes Zabbix*