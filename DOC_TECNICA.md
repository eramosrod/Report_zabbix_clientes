# Documentación Técnica - Generador de Informes Zabbix Multi-Cliente

## 1. Arquitectura y Estructura del Proyecto

### 1.1 Flujo General del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  clients.json  │    │  assets/logos/  │    │  ~/.muttrc      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   enviar_reporte.sh  │    │  main.py        │    │  mutt (SMTP)    │
│  (Bash)          │    │  (Python)       │    │  (Office 365)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────┬───────────┘                       │
                     │                                   │
                     ▼                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                 Motor Zabbix API                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ zabbix_api.py   │  │ data_collector.py│  │ report_generator.py│ │
│  │ • ZabbixAPI     │  │ • DataCollector  │  │ • ReportGenerator │ │
│  │ • Autenticación │  │ • Recopilación   │  │ • HTML/Consola   │ │
│  │ • Peticiones    │  │ • Estructuración │  │ • Estilos Zabbix │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Descripción del Flujo

1. **Configuración Inicial**: `clients.json` define perfiles de clientes con credenciales Zabbix específicas
2. **Ejecución del Script**: `enviar_reporte.sh` invoca `main.py` con el cliente especificado
3. **Autenticación**: `ZabbixAPI` maneja la autenticación JSON-RPC con reintentos y manejo de errores
4. **Recopilación de Datos**: `DataCollector` obtiene HostGroups, problemas activos, histórico y eventos
5. **Estructuración**: Los datos se organizan en secciones para el informe (entornos, alertas, GLPI, alertas activas)
6. **Generación**: `ReportGenerator` crea salida HTML con colores oficiales de Zabbix y consola formateada
7. **Envío**: `mutt` envía correo con consola como cuerpo y HTML como adjunto

### 1.3 Estructura de Directorios

```
/proyectos_git/Report_clientes/
├── main.py                    # Punto de entrada principal
├── zabbix_api.py              # Cliente API de Zabbix
├── data_collector.py          # Recopilación y estructuración de datos
├── report_generator.py        # Generación de informes HTML/Consola
├── clients.json               # Configuración multi-tenant
├── requirements.txt           # Dependencias Python
├── assets/
│   └── logos/                 # Logotipos de clientes (PNG/JPG/SVG)
├── enviar_reporte.sh          # Script de automatización (fuera del repo)
├── MEMORIA.md                  # Especificaciones del proyecto
├── CHANGELOG.md               # Registro de cambios
├── report.html                # Informe HTML generado
├── report_cliente1.html       # Ejemplo de informe HTML
└── DOC_TECNICA.md             # Esta documentación (nueva)
└── GUIA_CUSTOMIZACION.md       # Guía de personalización (nueva)
```

## 2. Requisitos y Dependencias del Sistema

### 2.1 Requisitos de Linux

```bash
# Sistema operativo: Linux 7.2 (compatible con RHEL/Debian/Ubuntu)
# Python: 3.8 o superior

# Paquetes del sistema (para mutt y Python)
sudo apt-get update && sudo apt-get install -y python3 python3-pip mutt
# o en sistemas RHEL/CentOS:
sudo dnf install -y python3 python3-pip mutt

# Para entornos de producción, considera:
# - systemd para gestión de servicios
# - logrotate para rotación de logs
# - firewalld u otro firewall
```

### 2.2 Dependencias de Python

```json
{
  "dependencies": {
    "requests": ">=2.31.0"
  }
}
```

### 2.3 Variables de Entorno Requeridas

```bash
# Para ejecución manual (modo legacy)
export ZABBIX_URL="https://zabbix.example.com"
export ZABBIX_USER="usuario"
export ZABBIX_PASS="contraseña"

# Para modo multi-cliente, las credenciales están en clients.json
```

## 3. Paso a Paso de Instalación y Despliegue

### 3.1 Instalación Inicial

```bash
# 1. Clonar el repositorio
cd /ruta/proyecto/
# (suponiendo que el repo ya está clonado)

# 2. Instalar dependencias Python
pip3 install -r requirements.txt

# 3. Verificar estructura de directorios
ls -la assets/logos/
# Asegurarse de que los logotipos estén presentes

# 4. Configurar archivo .muttrc (ver sección 5)
```

### 3.2 Configuración de Directorios y Permisos

```bash
# Crear directorios necesarios (si no existen)
mkdir -p assets/logos

# Establecer permisos apropiados
chmod 755 assets/logos
# Los logotipos deben ser accesibles por el usuario que ejecuta el script
chmod 644 assets/logos/*.png

# Verificar que main.py sea ejecutable
chmod +x main.py
```

### 3.3 Configuración de Variables de Entorno

```bash
# Para ejecución manual (opcional)
export PYTHONPATH="/ruta/proyecto/Report_clientes:$PYTHONPATH"

# Para ejecución con clientes específicos
# Las credenciales están en clients.json, no se necesitan variables de entorno adicionales
```

## 4. Configuración de Identidades (`clients.json`)

### 4.1 Estructura del Archivo

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
  }
}
```

### 4.2 Explicación de Campos

- **empresa**: Nombre legal del cliente (aparece en el banner del informe)
- **logo_path**: Ruta relativa desde la raíz del proyecto al archivo de imagen del logotipo
- **zabbix_url**: URL base del servidor Zabbix (incluye `/api_jsonrpc.php`)
- **zabbix_user**: Usuario específico de Zabbix para este cliente
- **zabbix_pass**: Contraseña para el usuario Zabbix

### 4.3 Cómo Zabbix Aísla los Entornos

Cada cliente tiene credenciales Zabbix únicas, lo que permite:

1. **Aislamiento de Datos**: El usuario Zabbix solo puede ver los hosts y grupos asignados a ese cliente
2. **Seguridad por Cliente**: Las credenciales nunca se comparten entre clientes
3. **Personalización**: Cada informe muestra el logotipo y nombre de empresa del cliente
4. **Escalabilidad**: Agregar nuevos clientes solo requiere entradas en `clients.json`

## 5. Configuración del Motor de Envío de Correo (`~/.muttrc`)

### 5.1 Configuración Completa para Office 365

```text
# ==============================================================================
# CONFIGURACIÓN SMTP DE MUTT (OUTLOOK / OFFICE 365)
# ==============================================================================

# 1. Identidad del Remitente
set from = "tu-correo-de-outlook@live.com"
set realname = "Sistema de Informes Zabbix"

# 2. Servidor SMTP y Credenciales
# Nota: Si tu usuario contiene el carácter '@', debes codificarlo como '%40'
set smtp_url = "smtp://tu-correo-de-outlook%40live.com:TU_CONTRASEÑA@smtp.office365.com:587/"
set smtp_pass = "TU_CONTRASEÑA_O_APP_PASSWORD"

# 3. Seguridad y Protocolos
set ssl_starttls = yes
set ssl_force_tls = yes

# 4. Ajustes para Ejecución Desatendida (Scripts / Cron)
set envelope_from = yes
set use_from = yes
set beep = no
set wait_key = no
```

### 5.2 Configuración de Contraseñas de Aplicación (2FA)

Si el correo tiene autenticación en dos pasos:

1. Inicia sesión en tu cuenta de Office 365
2. Ve a: Seguridad > Contraseñas de aplicación
3. Genera una nueva contraseña para "Aplicaciones menos seguras"
4. Copia la contraseña generada (ej: `Abc123!@#`) y colócala en `smtp_pass`

### 5.3 Protección del Archivo de Configuración

```bash
# Asegurarse de que solo el propietario pueda leer el archivo
chmod 600 ~/.muttrc

# Verificar permisos
ls -la ~/.muttrc
# Debe mostrar: -rw------- 1 usuario grupo 123 Abr 08 20:06 .muttrc
```

## 6. Comandos de Ejecución y Pruebas

### 6.1 Pruebas Manuales en Terminal

#### 6.1.1 Generar Informe para un Cliente Específico

```bash
# Generar informe HTML para cliente_a
python3 main.py --client cliente_a --html informe_cliente_a.html

# Generar informe solo HTML (sin consola)
python3 main.py --client cliente_a --html informe_cliente_a.html --no-console

# Generar informe con rango de tiempo personalizado
python3 main.py --client cliente_a --html informe_cliente_a.html \
  --time-from "2026-11-01 00:00:00" --time-till "2026-11-08 23:59:59"
```

#### 6.1.2 Modo Legacy (sin clientes)

```bash
# Modo interactivo (solicita credenciales)
python3 main.py

# Modo no interactivo con argumentos
python3 main.py --url "https://zabbix.example.com" --user "admin" --html informe.html
```

### 6.2 Ejecución del Script Bash

```bash
# Ejecutar script de envío (requiere .muttrc configurado)
./enviar_reporte.sh cliente_a

# Con cliente específico por parámetro
./enviar_reporte.sh cliente_b

# Con destino de correo personalizado (modificar enviar_reporte.sh)
./enviar_reporte.sh cliente_a
```

### 6.3 Verificación del Informe Generado

```bash
# Verificar archivo HTML
ls -la report_cliente_a.html
# Debe mostrar: -rw-r--r-- 1 usuario grupo 2.5M Abr 08 20:06 report_cliente_a.html

# Abrir en navegador (opcional)
# xdg-open report_cliente_a.html

# Verificar contenido
head -20 report_cliente_a.html
# Debe mostrar: <!DOCTYPE html> y banner con Acme Corp S.A.
```

## 7. Automatización con Cron

### 7.1 Sintaxis de Tareas Programadas

```cron
# ==============================================================================
# TAREAS PROGRAMADAS PARA INFORMES ZABBIX SEMANALES
# ==============================================================================

# Cliente A - Lunes a las 08:00 AM
0 8 * * 1 /ruta/proyecto/Report_clientes/enviar_reporte.sh cliente_a >> /ruta/proyecto/Report_clientes/cron.log 2>&1

# Cliente B - Lunes a las 08:15 AM  
15 8 * * 1 /ruta/proyecto/Report_clientes/enviar_reporte.sh cliente_b >> /ruta/proyecto/Report_clientes/cron.log 2>&1

# Ejemplo adicional: Todos los días a las 18:00 para clientes específicos
0 18 * * * /ruta/proyecto/Report_clientes/enviar_reporte.sh cliente_a >> /ruta/proyecto/Report_clientes/cron.log 2>&1
```

### 7.2 Creación del Archivo de Log

```bash
# Crear archivo de log vacío
touch /ruta/proyecto/Report_clientes/cron.log

# Establecer permisos
chmod 644 /ruta/proyecto/Report_clientes/cron.log

# Verificar que cron lo pueda escribir
ls -la /ruta/proyecto/Report_clientes/cron.log
```

### 7.3 Verificación de Cron

```bash
# Editar crontab (ejecutar como el usuario que ejecutará los informes)
crontab -e

# Verificar tareas programadas
 crontab -l

# Verificar logs (después de algunas ejecuciones)
tail -f /ruta/proyecto/Report_clientes/cron.log
```

### 7.4 Comandos Útiles de Cron

```bash
# Listar todas las tareas programadas
 crontab -l

# Editar tareas programadas
 crontab -e

# Desactivar temporalmente una tarea
# Comentar la línea con # al principio

# Activar una tarea desactivada
# Eliminar # del principio de la línea

# Verificar sintaxis de crontab
crontab -l | crontab -
```

## 8. Resolución de Problemas Comunes

### 8.1 Errores Comunes y Soluciones

| Síntoma | Causa | Solución |
|---------|-------|----------|
| "Error: Cliente 'cliente_x' no encontrado" | Nombre de cliente incorrecto | Verificar clientes disponibles en clients.json |
| "Error: No se encuentra el archivo de configuración" | clients.json no existe | Verificar que el archivo esté en la raíz del proyecto |
| "Error de conexión a Zabbix" | URL o credenciales incorrectas | Verificar zabbix_url, zabbix_user, zabbix_pass |
| "Error de autenticación" | Usuario/contraseña incorrectos | Verificar credenciales en clients.json |
| "mutt: no se puede enviar correo" | .muttrc mal configurado | Verificar smtp_url, smtp_pass, permisos |

### 8.2 Comandos de Diagnóstico

```bash
# Verificar estructura del proyecto
ls -la /ruta/proyecto/Report_clientes

# Verificar clientes.json
python3 -m json.tool clients.json

# Probar conexión a Zabbix (modo cliente)
python3 main.py --client cliente_a --no-console

# Verificar .muttrc
mutt -D

# Probar envío de correo (sin adjunto)
echo "Prueba desde mutt" | mutt -s "Prueba" tu-correo@ejemplo.com
```

## 9. Mantenimiento y Actualizaciones

### 9.1 Agregar Nuevo Cliente

```bash
# 1. Agregar entrada a clients.json
# Editar clients.json y agregar nuevo cliente

# 2. Colocar logotipo
# Colocar archivo PNG/JPG en assets/logos/
# Actualizar logo_path en clients.json

# 3. Probar nuevo cliente
python3 main.py --client nuevo_cliente --html informe_nuevo.html
```

### 9.2 Actualizar Dependencias

```bash
# Actualizar pip
pip3 install --upgrade requests

# Verificar versiones
pip3 freeze | grep requests
```

### 9.3 Respaldar Configuración

```bash
# Respaldar archivos clave
cp clients.json clients.json.backup.$(date +%Y%m%d_%H%M%S)
cp ~/.muttrc ~/.muttrc.backup.$(date +%Y%m%d_%H%M%S)

# Verificar respaldos
ls -la *.backup*
```

## 10. Documentación de Referencia Rápida

### 10.1 Comandos Más Usados

```bash
# Generar informe para cliente específico
python3 main.py --client cliente_a --html informe.html

# Enviar informe automáticamente
./enviar_reporte.sh cliente_a

# Verificar tareas programadas
 crontab -l

# Revisar logs de cron
tail -f cron.log

# Limpiar informes HTML antiguos (opcional)
rm -f report_*.html
```

### 10.2 Archivos Clave

- **main.py**: Punto de entrada principal
- **clients.json**: Configuración multi-tenant
- **assets/logos/**: Imágenes de clientes
- **~/.muttrc**: Configuración de correo
- **enviar_reporte.sh**: Script de automatización
- **cron.log**: Log de ejecuciones programadas

### 10.3 Contacto y Soporte

Para problemas:
1. Verificar logs (`cron.log`, salida de terminal)
2. Verificar configuración (`.muttrc`, `clients.json`)
3. Probar manualmente con `python3 main.py --client cliente_a`
4. Verificar conectividad de red a Zabbix y servidor de correo

---
*Documentación generada automáticamente - Versión 0.16.0*
*Fecha: 2026-11-08*
