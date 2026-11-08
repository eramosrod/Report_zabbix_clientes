# Guía de Configuración y Automatización de Envíos de Correo para Informes Zabbix

Este documento describe el procedimiento paso a paso para configurar el envío automático de informes ejecutivos de Zabbix (cuerpo en texto plano con el resumen de la consola y adjunto HTML con la imagen de marca del cliente) mediante **mutt**, **Bash** y **Cron**.

## 1. Requisitos Previos e Instalación

Para que el envío funcione de manera ligera y directa contra el servidor SMTP (sin necesidad de configurar un MTA complejo como Postfix o Sendmail), utilizaremos **`mutt`**.

### Instalación de Mutt

En tu servidor Linux (RHEL/Debian/Ubuntu), instala el paquete `mutt`:

```bash
# En sistemas basados en Debian/Ubuntu:
sudo apt-get update && sudo apt-get install -y mutt

# En sistemas basados en RHEL/CentOS/Rocky Linux:
sudo dnf install -y mutt
```

## 2. Configuración del Perfil SMTP de Envío (`~/.muttrc`)

Mutt permite autenticarse directamente con el servidor de correo saliente. Crearemos o editaremos el archivo de configuración en el directorio personal del usuario que ejecutará el script (`~/.muttrc`).

### Paso A: Crear el archivo `.muttrc`

```bash
nano ~/.muttrc
```

### Paso B: Insertar la configuración (Ejemplo para Outlook / Office 365)

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

> **Importante (Autenticación de 2 Factores / 2FA):**
> Si tu cuenta de correo tiene habilitada la autenticación en dos pasos (2FA), no utilices la contraseña habitual de tu cuenta. Genera una **Contraseña de Aplicación** (*App Password*) desde el portal de seguridad de tu proveedor de correo y colócala en `smtp_pass`.

### Paso C: Proteger el archivo de configuración

Dado que `.muttrc` contiene credenciales, ajusta sus permisos para que solo el propietario pueda leerlo:

```bash
chmod 600 ~/.muttrc
```

## 3. Implementación del Script de Control en Bash (`enviar_reporte.sh`)

Este script se encarga de llamar a `main.py` para el cliente especificado, capturar la salida en consola para usarla como cuerpo del correo, y adjuntar la versión HTML formateada.

### Paso A: Crear el archivo `enviar_reporte.sh`

Ubicación recomendada: `/ruta/al/proyecto/enviar_reporte.sh`

```bash
#!/bin/bash

# ==============================================================================
# SCRIPT DE AUTOMATIZACIÓN Y ENVÍO DE INFORMES ZABBIX MULTI-CLIENTE
# ==============================================================================

# --- Configuración de Entorno ---
PROJ_DIR="/ruta/al/proyecto"
PYTHON_BIN="/usr/bin/python3"
SCRIPT_NAME="main.py"

# --- Parámetros de Ejecución ---
CLIENTE="${1:-cliente_a}"  # Acepta el cliente por parámetro $1 (por defecto: cliente_a)
HTML_REPORT="report_${CLIENTE}.html"
DESTINATARIO="admin@tudominio.com"
ASUNTO="[Zabbix] Informe de Estado y Alertas - ${CLIENTE^^}"

# --- Navegación al directorio de trabajo ---
cd "$PROJ_DIR" || { echo "Error: No se pudo acceder a $PROJ_DIR"; exit 1; }

echo "[$(date)] Generando informe para: $CLIENTE..."

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
    
    # 4. Envío con Mutt
    # -s : Asunto
    # -a : Archivo adjunto (HTML)
    # -- : Separa las opciones del destinatario
    echo "$OUTPUT_TXT" | mutt -s "$ASUNTO" -a "$HTML_REPORT" -- "$DESTINATARIO"
    
    if [ $? -eq 0 ]; then
        echo "[$(date)] ¡Correo enviado con éxito a $DESTINATARIO!"
    else
        echo "Error: Falló el envío del correo con mutt." >&2
        exit 1
    fi
else
    echo "Error: No se encontró el archivo adjunto $HTML_REPORT" >&2
    exit 1
fi
```

### Paso B: Asignar permisos de ejecución

```bash
chmod +x /ruta/al/proyecto/enviar_reporte.sh
```

## 4. Prueba Manual de Funcionamiento

Antes de programarlo en el sistema, ejecuta el script de forma manual para verificar el envío:

```bash
/ruta/al/proyecto/enviar_reporte.sh cliente_a
```

Comprueba en el buzón de correo de destino que:

1. El remitente corresponda a la cuenta configurada en `.muttrc`.
2. El cuerpo del correo contenga la tabla y datos resumidos impresos por la consola.
3. El archivo adjunto `report_cliente_a.html` se pueda descargar y abra con la cabecera limpia, logotipos y estilos oficiales.

## 5. Automatización mediante Cron

Para programar el envío periódico y desatendido:

1. Abre el programador de tareas para tu usuario:

   ```bash
   crontab -e
   ```

2. Añade las tareas programadas deseadas (ejemplo: **Todos los lunes a las 08:00 AM**):

   ```cron
   # --- Envío de Informes Semanales Zabbix ---
   # Cliente A (Lunes 08:00 AM)
   0 8 * * 1 /ruta/al/proyecto/enviar_reporte.sh cliente_a >> /ruta/al/proyecto/cron.log 2>&1
   
   # Cliente B (Lunes 08:15 AM)
   15 8 * * 1 /ruta/al/proyecto/enviar_reporte.sh cliente_b >> /ruta/al/proyecto/cron.log 2>&1
   ```

3. Guarda y cierra el archivo (`:wq` en Vim o `Ctrl+O` / `Ctrl+X` en Nano).

## 6. Diagnóstico y Monitoreo

* **Logs de Cron:** Revisa el fichero `cron.log` generado para confirmar que las ejecuciones automáticas se realizan sin fallos:

  ```bash
  cat /ruta/al/proyecto/cron.log
  ```

* **Ficheros temporales:** Si deseas limpiar los informes HTML generados tras el envío, puedes añadir `rm "$HTML_REPORT"` al final del script `enviar_reporte.sh`.