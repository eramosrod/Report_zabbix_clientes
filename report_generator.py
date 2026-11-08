#!/usr/bin/env python3
"""
Módulo de generación de informes para Zabbix.
Fase 9: Histórico tipo Top Triggers con event.get (agrupado por Host + Trigger Name).
Fase 10: Gestión multi-cliente mediante archivo de configuración externo (clients.json) y almacenamiento local de logotipos.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import os


class ReportGenerator:
    """
    Generador de informes visuales a partir de los datos estructurados de DataCollector.
    Soporta salida HTML y vista de consola formateada.
    """
    
    def __init__(self, report_data: Dict[str, Any], time_from: int = None, time_till: int = None):
        """
        Inicializa el generador con los datos del informe.
        
        Args:
            report_data: Diccionario con la estructura completa del informe
                        (salida de DataCollector.get_complete_report_data())
            time_from: Timestamp de inicio (opcional)
            time_till: Timestamp de fin (opcional)
        """
        self.data = report_data
        self.time_from = time_from
        self.time_till = time_till
        self.timestamp = report_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.total_problems = report_data.get('total_problems', 0)
        self.total_active_problems = report_data.get('total_active_problems', 0)
        self.total_events = report_data.get('total_events', 0)
        self.total_hosts = report_data.get('total_hosts', 0)
        self.environments = report_data.get('environments', [])
        self.alerts_summary = report_data.get('alerts_summary', [])
        self.active_alerts = report_data.get('active_alerts', [])
        self.glpi_links = report_data.get('glpi_links', [])
        # Datos del cliente (Fase 10)
        self.client_name = report_data.get('client_name')
        self.client_empresa = report_data.get('client_empresa', 'Zabbix')
        self.client_logo_path = report_data.get('client_logo_path', '')
    
    def generate_html(self, output_path: Optional[str] = None) -> str:
        """
        Genera el informe completo en formato HTML.
        
        Args:
            output_path: Ruta opcional para guardar el archivo HTML
            
        Returns:
            Contenido HTML como string
        """
        html = self._build_html()
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✓ Informe HTML guardado en: {output_path}")
        
        return html
    
    def _build_html(self) -> str:
        """Construye el HTML completo del informe."""
        html_parts = [
            self._get_html_header(),
            self._get_banner_section(),
            self._get_environments_section(),
            self._get_alerts_summary_section(),
            self._get_glpi_links_section(),
            self._get_active_alerts_section(),
            self._get_html_footer()
        ]
        return '\n'.join(html_parts)
    
    def _get_html_header(self) -> str:
        """Retorna el header HTML con estilos CSS embebidos."""
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe de Estado Zabbix</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f6f9;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        /* Banner */
        .banner {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(30, 60, 114, 0.3);
        }
        .banner h1 {
            font-size: 2.2rem;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .banner .meta {
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
            font-size: 1rem;
            opacity: 0.9;
        }
        .banner .meta span {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        /* Section */
        .section {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 25px;
            overflow: hidden;
        }
        .section-header {
            background: #f8f9fa;
            padding: 18px 25px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .section-header h2 {
            font-size: 1.3rem;
            font-weight: 600;
            color: #1e3c72;
        }
        .section-header .badge {
            background: #1e3c72;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .section-content {
            padding: 25px;
        }
        /* Tables */
        .table-container {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
            white-space: nowrap;
            position: sticky;
            top: 0;
        }
        tr:hover td {
            background: #f8f9fa;
        }
        tr:last-child td {
            border-bottom: none;
        }
        /* Severity badges - Zabbix Official Color Palette */
        .severity {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .severity-disaster { background: #fdeaea; color: #E45959; }
        .severity-high { background: #fef0e0; color: #E97659; }
        .severity-average { background: #fff8e1; color: #FFA15C; }
        .severity-warning { background: #e8f4fd; color: #FFC859; }
        .severity-info { background: #e8f8f5; color: #7499FF; }
        .severity-notclassified { background: #f0f0f0; color: #7f8c8d; }
        /* Status badges */
        .status {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 0.78rem;
            font-weight: 600;
        }
        .status-problem { background: #fdeaea; color: #E45959; }
        .status-ok { background: #e8f8f5; color: #1abc9c; }
        /* Environment table - Simplified with dynamic colors */
        .env-row-has-alerts {
            background-color: #fdeaea;
        }
        .env-row-has-alerts td {
            color: #E45959;
        }
        .env-row-no-alerts {
            background-color: #e8f8f5;
        }
        .env-row-no-alerts td {
            color: #1abc9c;
        }
        .env-row-has-alerts:hover,
        .env-row-no-alerts:hover {
            opacity: 0.85;
        }
        /* Environment cards (legacy - kept for reference) */
        .env-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }
        .env-card {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        /* Environment card states based on active alerts */
        .env-card.has-alerts {
            border-left: 5px solid #E45959;
        }
        .env-card.no-alerts {
            border-left: 5px solid #1abc9c;
        }
        .env-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        }
        .env-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
            padding-bottom: 12px;
            border-bottom: 1px solid #e9ecef;
        }
        .env-card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1e3c72;
        }
        .env-card-title.has-alerts {
            color: #E45959;
        }
        .env-card-title.no-alerts {
            color: #1abc9c;
        }
        .env-card-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }
        .env-stat {
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .env-stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1e3c72;
        }
        .env-stat-label {
            font-size: 0.75rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .env-severity-breakdown {
            margin-top: 15px;
        }
        .env-severity-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            font-size: 0.85rem;
        }
        .env-severity-row .label {
            color: #6c757d;
        }
        .env-severity-row .value {
            font-weight: 600;
        }
        /* Footer */
        .footer {
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.85rem;
        }
        /* Empty state */
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #6c757d;
        }
        .empty-state svg {
            width: 64px;
            height: 64px;
            margin-bottom: 15px;
            opacity: 0.5;
        }
        /* Responsive */
        @media (max-width: 768px) {
            .container { padding: 15px; }
            .banner h1 { font-size: 1.6rem; }
            .section-content { padding: 15px; }
            th, td { padding: 10px 12px; font-size: 0.8rem; }
            .env-card-stats { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">'''
    
    def _get_banner_section(self) -> str:
        """Genera la sección del banner superior simplificada - solo título de la empresa."""
        # Logo del cliente si existe
        logo_html = ""
        if self.client_logo_path and os.path.exists(self.client_logo_path):
            # Convertir imagen a base64 para embeber en HTML
            import base64
            try:
                with open(self.client_logo_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                # Detectar tipo MIME por extensión
                ext = os.path.splitext(self.client_logo_path)[1].lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.svg': 'image/svg+xml',
                    '.webp': 'image/webp'
                }
                mime_type = mime_types.get(ext, 'image/png')
                logo_html = f'<img src="data:{mime_type};base64,{img_data}" alt="{self._escape_html(self.client_empresa)}" style="max-height: 60px; max-width: 200px; margin-right: 20px; vertical-align: middle;">'
            except Exception:
                logo_html = ""
        
        return f'''
        <!-- BANNER SUPERIOR -->
        <div class="banner">
            <div style="display: flex; align-items: center;">
                {logo_html}
                <h1 style="margin: 0;">Informe de Estado Zabbix - {self._escape_html(self.client_empresa)}</h1>
            </div>
        </div>'''
    
    def _get_environments_section(self) -> str:
        """Genera la sección de Estado de Entornos (HostGroups) - Tabla simplificada con colores dinámicos."""
        if not self.environments:
            return '''
        <!-- ESTADO DE ENTORNOS -->
        <div class="section">
            <div class="section-header">
                <h2>Estado de Entornos</h2>
                <span class="badge">0 entornos</span>
            </div>
            <div class="section-content">
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                    <p>No hay entornos (HostGroups) configurados en Zabbix.</p>
                </div>
            </div>
        </div>'''
        
        rows = []
        for env in self.environments:
            total_problems = env['total_problems']
            # Determine row color class based on problems count
            row_class = 'env-row-has-alerts' if total_problems > 0 else 'env-row-no-alerts'
            rows.append(f'''
            <tr class="{row_class}">
                <td>{self._escape_html(env['name'])}</td>
                <td style="text-align: right; font-weight: 600;">{total_problems}</td>
            </tr>''')
        
        return f'''
        <!-- ESTADO DE ENTORNOS -->
        <div class="section">
            <div class="section-header">
                <h2>Estado de Entornos (HostGroups)</h2>
                <span class="badge">{len(self.environments)} entornos</span>
            </div>
            <div class="section-content">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Nombre del Entorno</th>
                                <th style="text-align: right;">Número de Problemas</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(rows)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>'''
    
    def _get_alerts_summary_section(self) -> str:
        """Genera la sección de Resumen de Alertas (AGRUPADO con conteo)."""
        if not self.alerts_summary:
            return '''
        <!-- RESUMEN DE ALERTAS -->
        <div class="section">
            <div class="section-header">
                <h2>Resumen de Alertas</h2>
                <span class="badge">0 alertas</span>
            </div>
            <div class="section-content">
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <p>No hay alertas para mostrar en el resumen.</p>
                </div>
            </div>
        </div>'''
        
        rows = []
        total_occurrences = 0
        for alert in self.alerts_summary:
            severity_class = self._get_severity_class(alert['severidad'])
            count = alert.get('count', 1)
            total_occurrences += count
            rows.append(f'''
            <tr>
                <td>{self._escape_html(alert['host'])}</td>
                <td>{self._escape_html(alert['trigger_alerta'])}</td>
                <td><span class="severity {severity_class}">{self._escape_html(alert['severidad'])}</span></td>
                <td>{self._escape_html(alert['nombre_problema'])}</td>
                <td style="text-align: right; font-weight: 600;">{count}</td>
            </tr>''')
        
        return f'''
        <!-- RESUMEN DE ALERTAS -->
        <div class="section">
            <div class="section-header">
                <h2>Resumen de Alertas (Agrupado por problema)</h2>
                <span class="badge">{len(self.alerts_summary)} problemas únicos | {total_occurrences} ocurrencias totales</span>
            </div>
            <div class="section-content">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Host</th>
                                <th>Trigger / Alerta</th>
                                <th>Severidad</th>
                                <th>Nombre de problemas</th>
                                <th style="text-align: right;">Veces</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(rows)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>'''
    
    def _get_glpi_links_section(self) -> str:
        """Genera la sección de Enlaces GLPI (extraídos del tag __zbx_glpi_link)."""
        if not self.glpi_links:
            return '''
        <!-- ENLACES GLPI -->
        <div class="section">
            <div class="section-header">
                <h2>Enlaces GLPI</h2>
                <span class="badge">Sin enlaces</span>
            </div>
            <div class="section-content">
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                    <p>No se encontraron problemas con el tag '__zbx_glpi_link'.</p>
                </div>
            </div>
        </div>'''
        
        rows = []
        for link in self.glpi_links:
            severity_class = self._get_severity_class(link.get('severity', ''))
            rows.append(f'''
            <tr>
                <td>{self._escape_html(link.get('ticket_id', ''))}</td>
                <td>{self._escape_html(link.get('title', ''))}</td>
                <td>{self._escape_html(link.get('host', ''))}</td>
                <td><span class="severity {severity_class}">{self._escape_html(link.get('severity', ''))}</span></td>
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
    
    def _get_active_alerts_section(self) -> str:
        """Genera la sección de Alertas Activas (SOLO alertas activas actuales, SIN filtro temporal)."""
        if not self.active_alerts:
            return '''
        <!-- ALERTAS ACTIVAS -->
        <div class="section">
            <div class="section-header">
                <h2>Alertas Activas</h2>
                <span class="badge">0 alertas activas</span>
            </div>
            <div class="section-content">
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p>No hay alertas activas en el sistema.</p>
                </div>
            </div>
        </div>'''
        
        rows = []
        for alert in self.active_alerts:
            severity_class = self._get_severity_class(alert['severity'])
            status = alert.get('status', 'PROBLEM')
            status_class = 'status-problem' if status == 'PROBLEM' else 'status-ok'
            recovery = alert['recovery_time'] if alert['recovery_time'] else '—'
            rows.append(f'''
            <tr>
                <td>{self._escape_html(alert['time'])}</td>
                <td>{self._escape_html(recovery)}</td>
                <td><span class="status {status_class}">{self._escape_html(status)}</span></td>
                <td>{self._escape_html(alert['host'])}</td>
                <td><span class="severity {severity_class}">{self._escape_html(alert['severity'])}</span></td>
                <td>{self._escape_html(alert['trigger_problem'])}</td>
                <td>{self._escape_html(alert['duration'])}</td>
            </tr>''')
        
        return f'''
        <!-- ALERTAS ACTIVAS -->
        <div class="section">
            <div class="section-header">
                <h2>Alertas Activas</h2>
                <span class="badge">{len(self.active_alerts)} alertas activas actuales</span>
            </div>
            <div class="section-content">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Recovery Time</th>
                                <th>Status</th>
                                <th>Host</th>
                                <th>Severity</th>
                                <th>Trigger/Problem</th>
                                <th>Duration</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(rows)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>'''
    
    def _get_html_footer(self) -> str:
        """Retorna el footer HTML."""
        return '''
    </div>
    <div class="footer">
        <p>Informe generado automáticamente por Generador de Informes Zabbix v0.15.0</p>
        <p>Fase 10 - Gestión multi-cliente mediante clients.json y almacenamiento local de logotipos</p>
    </div>
</body>
</html>'''
    
    def _get_severity_class(self, severity: str) -> str:
        """Mapea severidad a clase CSS (nombres oficiales en inglés de Zabbix)."""
        severity_lower = severity.lower()
        if 'disaster' in severity_lower:
            return 'severity-disaster'
        elif 'high' in severity_lower:
            return 'severity-high'
        elif 'average' in severity_lower:
            return 'severity-average'
        elif 'warning' in severity_lower:
            return 'severity-warning'
        elif 'information' in severity_lower:
            return 'severity-info'
        else:
            return 'severity-notclassified'
    
    def _escape_html(self, text: str) -> str:
        """Escapa caracteres HTML especiales."""
        if not text:
            return ''
        s = str(text)
        s = s.replace('&', '&')
        s = s.replace('<', '<')
        s = s.replace('>', '>')
        s = s.replace('"', '"')
        s = s.replace("'", "'")
        return s
    
    def print_console_report(self) -> None:
        """
        Imprime el informe completo en consola con formato legible.
        """
        self._print_banner()
        self._print_environments_console()
        self._print_alerts_summary_console()
        self._print_glpi_links_console()
        self._print_active_alerts_console()
        self._print_footer_console()
    
    def _print_banner(self) -> None:
        """Imprime el banner en consola."""
        width = 100
        print("\n" + "=" * width)
        if self.client_name:
            print(f"  📊 INFORME DE ESTADO ZABBIX - {self.client_empresa.upper()}".center(width))
        else:
            print("  📊 INFORME DE ESTADO ZABBIX".center(width))
        print("=" * width)
        print(f"  🕐 Generado: {self.timestamp}")
        print(f"  🖥️  Total Hosts: {self.total_hosts}")
        print(f"  ⚠️  Problemas Totales (Histórico problem.get): {self.total_problems}")
        print(f"  📊 Eventos Totales (Histórico event.get - Top Triggers): {self.total_events}")
        print(f"  🔴 Problemas Activos (Actuales): {self.total_active_problems}")
        print(f"  🌍 Entornos (HostGroups): {len(self.environments)}")
        if self.client_name:
            print(f"  👤 Cliente: {self.client_empresa} ({self.client_name})")
            if self.client_logo_path:
                print(f"  🖼️  Logo: {self.client_logo_path}")
        
        # Mostrar intervalo de tiempo si está disponible
        if hasattr(self, 'time_from') and hasattr(self, 'time_till'):
            if self.time_from and self.time_till:
                from datetime import datetime
                time_from_str = datetime.fromtimestamp(self.time_from).strftime('%Y-%m-%d %H:%M:%S')
                time_till_str = datetime.fromtimestamp(self.time_till).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  ⏰ Intervalo (Resumen/Entornos): {time_from_str} - {time_till_str}")
            elif self.time_from or self.time_till:
                from datetime import datetime
                if self.time_from:
                    time_from_str = datetime.fromtimestamp(self.time_from).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  ⏰ Desde (Resumen/Entornos): {time_from_str}")
                if self.time_till:
                    time_till_str = datetime.fromtimestamp(self.time_till).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  ⏰ Hasta (Resumen/Entornos): {time_till_str}")
        
        print("=" * width + "\n")
    
    def _print_environments_console(self) -> None:
        """Imprime la sección de entornos en consola."""
        print("  📋 ESTADO DE ENTORNOS (HostGroups)")
        print("  " + "-" * 96)
        
        if not self.environments:
            print("  No hay entornos configurados.\n")
            return
        
        # Cabecera
        header = f"{'Entorno':<35} {'Hosts':>6} {'Problemas':>10} {'Disaster':>8} {'High':>6} {'Average':>8} {'Warning':>6} {'Info':>6}"
        print(f"  {header}")
        print("  " + "-" * 96)
        
        for env in self.environments:
            sev = env['problems_by_severity']
            row = f"{env['name'][:34]:<35} {env['total_hosts']:>6} {env['total_problems']:>10} "
            row += f"{sev['Disaster']:>8} {sev['High']:>6} {sev['Average']:>8} {sev['Warning']:>6} {sev['Information']:>6}"
            print(f"  {row}")
        
        print("  " + "-" * 96)
        
        # Totales
        total_hosts = sum(e['total_hosts'] for e in self.environments)
        total_problems = sum(e['total_problems'] for e in self.environments)
        total_disaster = sum(e['problems_by_severity']['Disaster'] for e in self.environments)
        total_high = sum(e['problems_by_severity']['High'] for e in self.environments)
        total_average = sum(e['problems_by_severity']['Average'] for e in self.environments)
        total_warning = sum(e['problems_by_severity']['Warning'] for e in self.environments)
        total_info = sum(e['problems_by_severity']['Information'] for e in self.environments)
        
        total_row = f"{'TOTAL':<35} {total_hosts:>6} {total_problems:>10} "
        total_row += f"{total_disaster:>8} {total_high:>6} {total_average:>8} {total_warning:>6} {total_info:>6}"
        print(f"  {total_row}")
        print("  " + "-" * 96 + "\n")
    
    def _print_alerts_summary_console(self) -> None:
        """Imprime el resumen de alertas en consola (AGRUPADO con conteo)."""
        print("  📋 RESUMEN DE ALERTAS (Agrupado por problema - Conteo de ocurrencias)")
        print("  " + "-" * 130)
        
        if not self.alerts_summary:
            print("  No hay alertas para mostrar en el resumen.\n")
            return
        
        col_host = 25
        col_trigger = 35
        col_severity = 12
        col_name = 35
        col_count = 8
        
        header = f"{'Host':<{col_host}} {'Trigger / Alerta':<{col_trigger}} {'Severidad':<{col_severity}} {'Nombre de problemas':<{col_name}} {'Veces':>{col_count}}"
        print(f"  {header}")
        print("  " + "-" * (col_host + col_trigger + col_severity + col_name + col_count + 4))
        
        total_occurrences = 0
        for alert in self.alerts_summary:
            host = alert['host'][:col_host-1] if len(alert['host']) > col_host else alert['host']
            trigger = alert['trigger_alerta'][:col_trigger-1] if len(alert['trigger_alerta']) > col_trigger else alert['trigger_alerta']
            severity = alert['severidad'][:col_severity-1] if len(alert['severidad']) > col_severity else alert['severidad']
            name = alert['nombre_problema'][:col_name-1] if len(alert['nombre_problema']) > col_name else alert['nombre_problema']
            count = alert.get('count', 1)
            total_occurrences += count
            
            row = f"{host:<{col_host}} {trigger:<{col_trigger}} {severity:<{col_severity}} {name:<{col_name}} {count:>{col_count}}"
            print(f"  {row}")
        
        print("  " + "-" * (col_host + col_trigger + col_severity + col_name + col_count + 4))
        print(f"  Total: {len(self.alerts_summary)} problema(s) único(s) | Total ocurrencias: {total_occurrences}\n")
    
    def _print_glpi_links_console(self) -> None:
        """Imprime los enlaces GLPI en consola (extraídos del tag __zbx_glpi_link)."""
        print("  🔗 ENLACES GLPI (Tag __zbx_glpi_link)")
        print("  " + "-" * 80)
        
        if not self.glpi_links:
            print("  No se encontraron problemas con el tag '__zbx_glpi_link'.\n")
            return
        
        for link in self.glpi_links:
            print(f"  • Ticket: {link.get('ticket_id', 'N/A')} - {link.get('title', 'Sin título')}")
            print(f"    Host: {link.get('host', 'N/A')} | Severidad: {link.get('severity', 'N/A')}")
            print(f"    URL: {link.get('url', 'N/A')}")
        print()
    
    def _print_active_alerts_console(self) -> None:
        """Imprime las alertas activas en consola (SOLO alertas activas actuales, SIN filtro temporal)."""
        print("  📋 ALERTAS ACTIVAS")
        print("  " + "-" * 150)
        
        if not self.active_alerts:
            print("  No hay alertas activas en el sistema.\n")
            return
        
        col_time = 19
        col_recovery = 19
        col_status = 10
        col_host = 25
        col_severity = 12
        col_trigger = 40
        col_duration = 12
        
        header = (f"{'Time':<{col_time}} {'Recovery Time':<{col_recovery}} {'Status':<{col_status}} "
                  f"{'Host':<{col_host}} {'Severity':<{col_severity}} {'Trigger/Problem':<{col_trigger}} {'Duration':<{col_duration}}")
        print(f"  {header}")
        print("  " + "-" * (col_time + col_recovery + col_status + col_host + col_severity + col_trigger + col_duration + 6))
        
        for alert in self.active_alerts:
            time_str = alert['time'][:col_time-1] if len(alert['time']) > col_time else alert['time']
            recovery = alert['recovery_time'][:col_recovery-1] if len(alert['recovery_time']) > col_recovery else alert['recovery_time']
            status = alert.get('status', 'PROBLEM')
            status = status[:col_status-1] if len(status) > col_status else status
            host = alert['host'][:col_host-1] if len(alert['host']) > col_host else alert['host']
            severity = alert['severity'][:col_severity-1] if len(alert['severity']) > col_severity else alert['severity']
            trigger = alert['trigger_problem'][:col_trigger-1] if len(alert['trigger_problem']) > col_trigger else alert['trigger_problem']
            duration = alert['duration'][:col_duration-1] if len(alert['duration']) > col_duration else alert['duration']
            
            row = (f"{time_str:<{col_time}} {recovery:<{col_recovery}} {status:<{col_status}} "
                   f"{host:<{col_host}} {severity:<{col_severity}} {trigger:<{col_trigger}} {duration:<{col_duration}}")
            print(f"  {row}")
        
        print("  " + "-" * (col_time + col_recovery + col_status + col_host + col_severity + col_trigger + col_duration + 6))
        print(f"  Total: {len(self.active_alerts)} alertas activas actuales\n")
    
    def _print_footer_console(self) -> None:
        """Imprime el pie del informe en consola."""
        print("  " + "=" * 100)
        print("  Informe generado automáticamente por Generador de Informes Zabbix v0.15.0")
        print("  Fase 10 - Gestión multi-cliente mediante clients.json y almacenamiento local de logotipos")
        print("  " + "=" * 100 + "\n")


def generate_report(report_data: Dict[str, Any], output_html: Optional[str] = None, console: bool = True, time_from: int = None, time_till: int = None) -> str:
    """
    Función de conveniencia para generar el informe.
    
    Args:
        report_data: Datos del informe desde DataCollector.get_complete_report_data()
        output_html: Ruta opcional para guardar HTML
        console: Si True, imprime también en consola
        time_from: Timestamp de inicio (opcional)
        time_till: Timestamp de fin (opcional)
        
    Returns:
        Contenido HTML generado
    """
    generator = ReportGenerator(report_data, time_from=time_from, time_till=time_till)
    
    if console:
        generator.print_console_report()
    
    html_content = generator.generate_html(output_html)
    
    return html_content


# Prueba independiente
if __name__ == "__main__":
    print("Módulo de generación de informes - Prueba independiente")
    print("Este módulo está diseñado para ser importado desde main.py")
    print("\nUso:")
    print("  from report_generator import generate_report, ReportGenerator")
    print("  html = generate_report(report_data, output_html='informe.html')")