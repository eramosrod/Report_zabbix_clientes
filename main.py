#!/usr/bin/env python3
"""
Módulo principal para generar informe de estado desde Zabbix.
Fase 1: Autenticación y obtención de HostGroups.
Fase 2: Obtención de alertas activas y hosts por grupo.
Fase 3: Consulta de problemas activos (event.get) con salida estructurada para informe.
Fase 4: Arquitectura modular de recopilación de datos y formateo para tablas de resumen.
Fase 5: Generación de informe visual (HTML) y vista de consola formateada.
Fase 8: Histórico de Alertas, Resumen agrupado y GLPI.
Fase 9: Histórico tipo Top Triggers con event.get (agrupado por Host + Trigger Name).
Fase 9.5: Paleta de colores oficial Zabbix y estados visuales de entornos.
Fase 9.6: Separación de fuentes de datos - Alertas Activas sin filtro temporal, Resumen y Entornos con filtro.
Fase 9.7: Simplificación tabla Entornos en HTML - 2 columnas (Nombre, Problemas) con colores dinámicos rojo/verde.
Fase 10: Gestión multi-cliente mediante archivo de configuración externo (clients.json) y almacenamiento local de logotipos.
"""

import sys
import argparse
import json
import os
from getpass import getpass
from datetime import datetime

# Importar módulos propios
from zabbix_api import ZabbixAPI
from data_collector import DataCollector
from report_generator import generate_report, ReportGenerator


def load_client_config(client_name: str) -> dict:
    """Carga la configuración del cliente desde clients.json."""
    config_path = os.path.join(os.path.dirname(__file__), 'clients.json')
    
    if not os.path.exists(config_path):
        print(f"Error: No se encuentra el archivo de configuración {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            clients = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: El archivo clients.json tiene formato inválido: {e}")
        sys.exit(1)
    
    if client_name not in clients:
        print(f"Error: Cliente '{client_name}' no encontrado en clients.json")
        print(f"Clientes disponibles: {', '.join(clients.keys())}")
        sys.exit(1)
    
    return clients[client_name]


def solicitar_credenciales() -> tuple:
    """Solicita al usuario las credenciales de acceso a Zabbix (modo legacy sin --client)."""
    print("=" * 60)
    print("  GENERADOR DE INFORMES ZABBIX")
    print("=" * 60)
    print()
    
    url = input("URL del servidor Zabbix (ej: https://zabbix.example.com): ").strip()
    if not url:
        print("Error: La URL es obligatoria.")
        sys.exit(1)
    
    username = input("Usuario: ").strip()
    if not username:
        print("Error: El usuario es obligatorio.")
        sys.exit(1)
    
    password = getpass("Contraseña: ")
    if not password:
        print("Error: La contraseña es obligatoria.")
        sys.exit(1)
    
    print()
    return url, username, password


def parse_time(time_str):
    """Convierte una cadena de tiempo a timestamp Unix."""
    if not time_str:
        return None
    try:
        # Intentar como timestamp Unix
        return int(time_str)
    except ValueError:
        # Intentar como formato YYYY-MM-DD HH:MM:SS
        try:
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            return int(dt.timestamp())
        except ValueError:
            raise argparse.ArgumentTypeError(f"Formato de tiempo inválido: {time_str}. Use YYYY-MM-DD HH:MM:SS o timestamp Unix.")

def parse_args():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Generador de Informes Zabbix - Fase 10')
    parser.add_argument('--client', '-c', metavar='NOMBRE', help='Nombre del cliente (definido en clients.json)')
    parser.add_argument('--html', '-H', metavar='ARCHIVO', help='Guardar informe en archivo HTML')
    parser.add_argument('--no-console', '-n', action='store_true', help='No mostrar informe en consola')
    parser.add_argument('--url', '-u', help='URL del servidor Zabbix (ej: https://zabbix.example.com) - modo legacy')
    parser.add_argument('--user', '-U', help='Usuario de Zabbix - modo legacy')
    parser.add_argument('--time-from', help='Fecha/hora de inicio (YYYY-MM-DD HH:MM:SS o timestamp) - aplica a Resumen y Entornos', type=parse_time)
    parser.add_argument('--time-till', help='Fecha/hora de fin (YYYY-MM-DD HH:MM:SS o timestamp) - aplica a Resumen y Entornos', type=parse_time)
    return parser.parse_args()


def main():
    """Función principal del programa - Fase 10: Gestión multi-cliente."""
    args = parse_args()
    
    # Variables para datos del cliente
    client_data = None
    client_name = None
    
    try:
        # Determinar modo de operación: --client o modo legacy
        if args.client:
            # Modo multi-cliente: cargar configuración desde clients.json
            client_data = load_client_config(args.client)
            client_name = args.client
            url = client_data['zabbix_url']
            username = client_data['zabbix_user']
            password = client_data['zabbix_pass']
            empresa = client_data['empresa']
            logo_path = client_data.get('logo_path', '')
            
            print("=" * 60)
            print(f"  GENERADOR DE INFORMES ZABBIX - Cliente: {empresa}")
            print("=" * 60)
            print()
            print(f"✓ Configuración cargada para cliente: {client_name}")
            print(f"  Empresa: {empresa}")
            print(f"  URL Zabbix: {url}")
            print(f"  Usuario: {username}")
            if logo_path:
                print(f"  Logo: {logo_path}")
            print()
        else:
            # Modo legacy: solicitar credenciales interactivamente o por args
            if args.url and args.user:
                url = args.url
                username = args.user
                password = getpass("Contraseña: ")
                if not password:
                    print("Error: La contraseña es obligatoria.")
                    sys.exit(1)
                print()
            else:
                url, username, password = solicitar_credenciales()
            
            empresa = "Zabbix"
            logo_path = ""
        
        # Crear cliente API
        zabbix = ZabbixAPI(url)
        
        # Autenticar
        print("Autenticando en Zabbix...")
        token = zabbix.login(username, password)
        print(f"✓ Autenticación exitosa.")
        print()
        
        # Crear colector de datos (arquitectura modular Fase 4)
        collector = DataCollector(zabbix)
        
        # Obtener HostGroups
        print("Consultando grupos de hosts (HostGroups)...")
        hostgroups = collector.get_all_hostgroups()
        print(f"✓ Se encontraron {len(hostgroups)} grupos de hosts.")
        print()
        
        # Obtener problemas activos (para tabla de Alertas Activas - SIN filtro temporal)
        print("Consultando problemas activos actuales (event.get - SIN filtro temporal)...")
        active_problems = collector.get_active_problems()
        print(f"✓ Se encontraron {len(active_problems)} problemas activos actuales.")
        print()
        
        # Obtener histórico completo de problemas (problem.get) - para Resumen de Alertas y GLPI (CON filtro temporal)
        print("Consultando histórico de problemas (problem.get - CON filtro temporal)...")
        history_problems = collector.get_problems_history(time_from=args.time_from, time_till=args.time_till, limit=10000)
        print(f"✓ Se encontraron {len(history_problems)} problemas en histórico (activos + resueltos).")
        print()
        
        # Obtener histórico de eventos de triggers (event.get tipo Top Triggers) - para Resumen de Alertas (CON filtro temporal)
        print("Consultando histórico de eventos de triggers (event.get - tipo Top Triggers - CON filtro temporal)...")
        history_events = collector.get_events_history(time_from=args.time_from, time_till=args.time_till, limit=10000)
        print(f"✓ Se encontraron {len(history_events)} eventos de triggers en histórico.")
        print()
        
        # ============================================================
        # FASE 9.6: SEPARACIÓN DE FUENTES DE DATOS
        # ============================================================
        
        # 1. Estado de Entornos (agrupado por HostGroups - CON filtro temporal)
        print("Generando resumen por entornos (HostGroups - CON filtro temporal)...")
        environment_summary = collector.get_environment_summary(time_from=args.time_from, time_till=args.time_till)
        
        # 2. Resumen de Alertas (AGRUPADO ESTRICTO por Host + Trigger Name - CON filtro temporal)
        print("Generando tabla de Resumen de Alertas (agrupado por Host + Trigger Name - tipo Top Triggers - CON filtro temporal)...")
        alerts_summary = collector.format_events_for_summary_table(history_events)
        
        # 3. Alertas Activas (SOLO alertas activas actuales - SIN filtro temporal)
        print("Generando tabla de Alertas Activas (SOLO alertas activas actuales - SIN filtro temporal)...")
        active_alerts = collector.format_problems_for_active_alerts_table(active_problems)
        
        # 4. Datos completos para el informe (incluye GLPI links)
        print("Generando estructura completa de datos para informe...")
        complete_report = collector.get_complete_report_data(time_from=args.time_from, time_till=args.time_till, limit=10000)
        print(f"✓ Estructura de informe generada:")
        print(f"  Timestamp: {complete_report['timestamp']}")
        print(f"  Entornos: {len(complete_report['environments'])}")
        print(f"  Problemas totales (histórico problem.get - CON filtro): {complete_report['total_problems']}")
        print(f"  Problemas activos (actuales - SIN filtro): {complete_report['total_active_problems']}")
        print(f"  Eventos totales (histórico event.get - Top Triggers - CON filtro): {complete_report['total_events']}")
        print(f"  Alertas en resumen (agrupadas por Host+Trigger): {len(complete_report['alerts_summary'])}")
        print(f"  Alertas activas en tabla: {len(complete_report['active_alerts'])}")
        print(f"  Enlaces GLPI: {len(complete_report['glpi_links'])}")
        print()
        
        # Añadir datos del cliente al informe para el banner
        complete_report['client_name'] = client_name
        complete_report['client_empresa'] = empresa
        complete_report['client_logo_path'] = logo_path
        
        # ============================================================
        # FASE 10: GENERACIÓN DE INFORME VISUAL (HTML + CONSOLA)
        # ============================================================
        print("=" * 60)
        print("  FASE 10: GENERACIÓN DE INFORME VISUAL")
        print("=" * 60)
        
        # Generar informe en consola (por defecto)
        if not args.no_console:
            print("\n📋 Mostrando informe en consola...\n")
            generate_report(complete_report, output_html=None, console=True, time_from=args.time_from, time_till=args.time_till)
        
        # Generar archivo HTML si se solicita
        if args.html:
            print(f"\n💾 Generando archivo HTML: {args.html}...")
            generate_report(complete_report, output_html=args.html, console=False, time_from=args.time_from, time_till=args.time_till)
            print(f"✓ Informe HTML guardado correctamente en: {args.html}")
        elif not args.no_console:
            print("\n💡 Usa --html archivo.html para guardar el informe en formato HTML")
        
        print()
        print("✓ Fase 10 completada correctamente - Gestión multi-cliente con clients.json y logotipos locales.")
        
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
