#!/usr/bin/env python3
"""
Módulo de recopilación y estructuración de datos para informes Zabbix.
Fase 8: Histórico de Alertas, Resumen agrupado y GLPI.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
from zabbix_api import ZabbixAPI


class DataCollector:
    """
    Clase responsable de la recopilación y estructuración de datos desde Zabbix.
    Agrupa la lógica de obtención de HostGroups, hosts, problemas y su asociación.
    """
    
    def __init__(self, zabbix_api: ZabbixAPI):
        """
        Inicializa el colector de datos.
        
        Args:
            zabbix_api: Instancia autenticada de ZabbixAPI
        """
        self.zabbix = zabbix_api
        self._hostgroups_cache: Optional[List[Dict]] = None
        self._hosts_by_group_cache: Dict[str, List[Dict]] = {}
        self._problems_cache: Optional[List[Dict]] = None
        self._problems_history_cache: Optional[List[Dict]] = None
    
    def get_all_hostgroups(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los grupos de hosts (HostGroups) ordenados alfabéticamente.
        Usa caché para evitar consultas repetidas.
        
        Returns:
            Lista de diccionarios con groupid y name
        """
        if self._hostgroups_cache is None:
            self._hostgroups_cache = self.zabbix.get_hostgroups()
        return self._hostgroups_cache
    
    def get_hosts_by_group(self, groupid: str) -> List[Dict[str, Any]]:
        """
        Obtiene los hosts de un grupo específico.
        Usa caché para evitar consultas repetidas.
        
        Args:
            groupid: ID del grupo de hosts
            
        Returns:
            Lista de diccionarios con hostid y name
        """
        if groupid not in self._hosts_by_group_cache:
            self._hosts_by_group_cache[groupid] = self.zabbix.get_hosts_by_group(groupid)
        return self._hosts_by_group_cache[groupid]
    
    def get_all_hosts_by_group(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Obtiene todos los hosts agrupados por su grupo de hosts.
        
        Returns:
            Diccionario con groupid como clave y lista de hosts como valor
        """
        hostgroups = self.get_all_hostgroups()
        result = {}
        for group in hostgroups:
            groupid = group['groupid']
            result[groupid] = self.get_hosts_by_group(groupid)
        return result
    
    def get_active_problems(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los problemas activos enriquecidos.
        NO aplica filtro temporal - muestra todas las alertas activas actuales del sistema.
        Usa caché para evitar consultas repetidas.
        
        Returns:
            Lista de problemas con información enriquecida (incluye status, recovery_time, is_resolved)
        """
        if self._problems_cache is None:
            raw_problems = self.zabbix.get_active_problems_raw()
            self._problems_cache = self._enrich_problems(raw_problems)
        return self._problems_cache

    def get_problems_history(self, time_from: int = None, time_till: int = None, limit: int = 10000) -> List[Dict[str, Any]]:
        """
        Obtiene el histórico completo de problemas (activos + resueltos) enriquecidos.
        Usa caché para evitar consultas repetidas si no hay filtros temporales.
        
        Args:
            time_from: Timestamp de inicio (opcional)
            time_till: Timestamp de fin (opcional)
            limit: Límite máximo de problemas a retornar (por defecto 10000 para histórico completo)
        
        Returns:
            Lista de problemas con información enriquecida (incluye r_eventid para resueltos)
        """
        # Si hay filtros, no usar caché
        if time_from or time_till:
            raw_problems = self.zabbix.get_problems_history(time_from=time_from, time_till=time_till, limit=limit)
            return self._enrich_problems(raw_problems)
            
        if self._problems_history_cache is None:
            raw_problems = self.zabbix.get_problems_history(limit=limit)
            self._problems_history_cache = self._enrich_problems(raw_problems)
        return self._problems_history_cache

    def get_events_history(self, time_from: int = None, time_till: int = None, limit: int = 10000) -> List[Dict[str, Any]]:
        """
        Obtiene el histórico de eventos de triggers (tipo Top Triggers de Zabbix) usando event.get.
        Este método replica la consulta del informe "Top Triggers" de Zabbix para obtener
        un recuento exacto y agrupado de las alertas por Host y Nombre de Trigger.
        
        Args:
            time_from: Timestamp de inicio (opcional)
            time_till: Timestamp de fin (opcional)
            limit: Límite máximo de eventos a retornar (por defecto 10000)
        
        Returns:
            Lista de eventos enriquecidos con host, trigger, severidad, etc.
        """
        # Si hay filtros, no usar caché
        if time_from or time_till:
            raw_events = self.zabbix.get_events_history(time_from=time_from, time_till=time_till, limit=limit)
            return self._enrich_events(raw_events)
            
        if not hasattr(self, '_events_history_cache'):
            self._events_history_cache = None
            
        if self._events_history_cache is None:
            raw_events = self.zabbix.get_events_history(limit=limit)
            self._events_history_cache = self._enrich_events(raw_events)
        return self._events_history_cache

    def _enrich_events(self, raw_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enriquece una lista de eventos crudos de event.get con información calculada.
        Los eventos de event.get tienen estructura diferente: hosts[] y triggers[]
        
        Args:
            raw_events: Lista de eventos crudos de event.get
            
        Returns:
            Lista de eventos enriquecidos
        """
        enriched_events = []
        now = datetime.now().timestamp()
        
        for event in raw_events:
            # Obtener información del host (del campo hosts[])
            host_info = {}
            host_name = "Desconocido"
            if event.get("hosts") and len(event["hosts"]) > 0:
                host = event["hosts"][0]
                host_name = host.get("name", "Desconocido")
                host_info = {
                    'name': host.get('name', ''),
                    'host': host.get('host', ''),
                    'ip': host.get('ip', ''),
                    'dns': host.get('dns', ''),
                    'port': host.get('port', ''),
                }
            
            # Obtener información del trigger (del campo triggers[])
            trigger_info = {}
            trigger_description = "Sin descripción"
            trigger_priority = 0
            if event.get("triggers") and len(event["triggers"]) > 0:
                trigger = event["triggers"][0]
                trigger_description = trigger.get("description", "Sin descripción")
                trigger_priority = int(trigger.get("priority", 0))
                trigger_info = {
                    'description': trigger.get('description', ''),
                    'priority': trigger.get('priority', 0),
                    'status': trigger.get('status', 0),
                    'url': trigger.get('url', ''),
                }
            
            # Resolver macros en la descripción del trigger
            resolved_description = self.zabbix.resolve_macros(
                trigger_description,
                host_info=host_info,
                trigger_info=trigger_info
            )
            
            # Convertir severidad numérica a texto (usando priority del trigger)
            severity_text = self.zabbix.SEVERITY_MAP.get(trigger_priority, f"Desconocido ({trigger_priority})")
            
            # Calcular duración
            clock = int(event.get("clock", 0))
            duration_seconds = int(now - clock)
            duration_str = self.zabbix._format_duration(duration_seconds)
            
            # Formatear tiempo de inicio
            time_str = datetime.fromtimestamp(clock).strftime('%Y-%m-%d %H:%M:%S')
            
            # Los eventos con value=1 son siempre de creación de problema (no resueltos en este contexto)
            # Para el histórico tipo Top Triggers, cada evento es una ocurrencia
            status = 'EVENT'  # Cada evento es una ocurrencia individual
            
            enriched_events.append({
                "eventid": event.get("eventid"),
                "time": time_str,
                "host": host_name,
                "severity": severity_text,
                "severity_num": trigger_priority,
                "description": resolved_description,  # Nombre del trigger con macros resueltas
                "duration": duration_str,
                "duration_seconds": duration_seconds,
                "clock": clock,
                "status": status,
                "trigger_description": resolved_description,
                "trigger_priority": trigger_priority
            })
        
        return enriched_events

    def _enrich_problems(self, raw_problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enriquece una lista de problemas crudos de la API con información calculada.
        
        Args:
            raw_problems: Lista de problemas crudos de event.get o problem.get
            
        Returns:
            Lista de problemas enriquecidos
        """
        enriched_problems = []
        now = datetime.now().timestamp()
        
        for problem in raw_problems:
            # Obtener información del host (puede haber múltiples, tomar el primero)
            # NOTA: problem.get no devuelve 'hosts' en algunas versiones de Zabbix
            host_info = {}
            host_name = "Desconocido"
            if problem.get("hosts") and len(problem["hosts"]) > 0:
                host = problem["hosts"][0]
                host_name = host.get("name", "Desconocido")
                host_info = {
                    'name': host.get('name', ''),
                    'host': host.get('host', ''),
                    'ip': host.get('ip', ''),
                    'dns': host.get('dns', ''),
                    'port': host.get('port', ''),
                }
            elif problem.get("host") and problem["host"].get("name"):
                # Algunas versiones pueden devolver host directamente
                host = problem["host"]
                host_name = host.get("name", "Desconocido")
                host_info = {
                    'name': host.get('name', ''),
                    'host': host.get('host', ''),
                    'ip': host.get('ip', ''),
                    'dns': host.get('dns', ''),
                    'port': host.get('port', ''),
                }
            
            # Convertir severidad numérica a texto
            severity_num = int(problem.get("severity", 0))
            severity_text = self.zabbix.SEVERITY_MAP.get(severity_num, f"Desconocido ({severity_num})")
            
            # Calcular duración
            clock = int(problem.get("clock", 0))
            duration_seconds = int(now - clock)
            duration_str = self.zabbix._format_duration(duration_seconds)
            
            # Formatear tiempo de inicio
            time_str = datetime.fromtimestamp(clock).strftime('%Y-%m-%d %H:%M:%S')
            
            # Determinar si está resuelto (tiene r_eventid)
            is_resolved = 'r_eventid' in problem and problem['r_eventid']
            status = 'OK' if is_resolved else 'PROBLEM'
            
            # Recovery time si está resuelto
            recovery_time = ''
            if is_resolved and problem.get('r_eventid'):
                # El r_eventid es el eventid del evento de resolución
                # Para obtener el clock de resolución necesitaríamos otra consulta
                # Por ahora dejamos vacío o usamos el clock del problema si no hay más info
                recovery_time = 'Resuelto'
            
            # Extraer tags
            tags = {}
            if problem.get("tags"):
                for tag in problem["tags"]:
                    tags[tag.get("tag", "")] = tag.get("value", "")
            
            # Resolver macros en el nombre del problema
            problem_name = problem.get("name", "Sin descripción")
            resolved_name = self.zabbix.resolve_macros(
                problem_name,
                host_info=host_info,
                event_info={
                    'eventid': problem.get('eventid'),
                    'clock': clock,
                    'name': problem_name,
                    'value': problem.get('value', 1),
                }
            )
            
            enriched_problems.append({
                "eventid": problem.get("eventid"),
                "time": time_str,
                "host": host_name,
                "severity": severity_text,
                "severity_num": severity_num,
                "description": resolved_name,  # Nombre del problema con macros resueltas
                "duration": duration_str,
                "duration_seconds": duration_seconds,
                "clock": clock,
                "status": status,
                "is_resolved": is_resolved,
                "recovery_time": recovery_time,
                "tags": tags,
                "r_eventid": problem.get("r_eventid")
            })
        
        return enriched_problems
    
    def get_hostgroup_map(self) -> Dict[str, str]:
        """
        Crea un mapa de hostid -> groupid para asociación rápida.
        Un host puede pertenecer a múltiples grupos; se asocia al primero encontrado.
        
        Returns:
            Diccionario hostid -> groupid
        """
        hostgroup_map = {}
        all_hosts_by_group = self.get_all_hosts_by_group()
        
        for groupid, hosts in all_hosts_by_group.items():
            for host in hosts:
                hostid = host['hostid']
                # Solo asignar si no tiene grupo asignado (primer grupo encontrado)
                if hostid not in hostgroup_map:
                    hostgroup_map[hostid] = groupid
        
        return hostgroup_map
    
    def group_problems_by_hostgroup(self, time_from: int = None, time_till: int = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Agrupa los problemas activos por grupo de hosts (entorno).
        
        Returns:
            Diccionario con groupid como clave y lista de problemas como valor.
            Incluye clave especial 'sin_grupo' para problemas sin hostgroup asociado.
        """
        # Obtener problemas originales de la API (con campo 'hosts') para asociación correcta
        # Usamos el cliente Zabbix directamente para obtener los problemas sin enriquecer
        raw_problems = self.zabbix.get_active_problems_raw(time_from=time_from, time_till=time_till)
        hostgroup_map = self.get_hostgroup_map()
        hostgroups = self.get_all_hostgroups()
        
        # Crear mapa de groupid -> nombre del grupo para referencia
        groupid_to_name = {g['groupid']: g['name'] for g in hostgroups}
        
        # Inicializar estructura de resultado con todos los grupos
        result = {group['groupid']: [] for group in hostgroups}
        result['sin_grupo'] = []  # Para problemas sin grupo asociado
        
        for problem in raw_problems:
            # El problema tiene hosts asociados (del selectHosts en event.get)
            problem_hosts = problem.get('hosts', [])
            
            if problem_hosts:
                # Tomar el primer host del problema
                hostid = problem_hosts[0].get('hostid')
                groupid = hostgroup_map.get(hostid)
                
                if groupid and groupid in result:
                    result[groupid].append(problem)
                else:
                    result['sin_grupo'].append(problem)
            else:
                result['sin_grupo'].append(problem)
        
        return result
    
    def get_environment_summary(self, time_from: int = None, time_till: int = None) -> List[Dict[str, Any]]:
        """
        Genera un resumen por entorno (HostGroup) para la tabla de "Estado Entornos".
        
        Returns:
            Lista de diccionarios con resumen por entorno:
            - groupid, name, total_hosts, total_problems, problems_by_severity
        """
        hostgroups = self.get_all_hostgroups()
        problems_by_group = self.group_problems_by_hostgroup(time_from=time_from, time_till=time_till)
        all_hosts_by_group = self.get_all_hosts_by_group()
        
        summary = []
        
        for group in hostgroups:
            groupid = group['groupid']
            group_name = group['name']
            hosts = all_hosts_by_group.get(groupid, [])
            raw_problems = problems_by_group.get(groupid, [])
            
            # Contar problemas por severidad (convertir severidad numérica a texto)
            severity_counts = {
                'Disaster': 0,
                'High': 0,
                'Average': 0,
                'Warning': 0,
                'Information': 0,
                'Not classified': 0
            }
            
            for problem in raw_problems:
                severity_num = int(problem.get('severity', 0))
                severity_text = self.zabbix.SEVERITY_MAP.get(severity_num, 'Not classified')
                if severity_text in severity_counts:
                    severity_counts[severity_text] += 1
                else:
                    severity_counts['Not classified'] += 1
            
            summary.append({
                'groupid': groupid,
                'name': group_name,
                'total_hosts': len(hosts),
                'total_problems': len(raw_problems),
                'problems_by_severity': severity_counts,
                'hosts': hosts,
                'problems': raw_problems
            })
        
        # Ordenar por total de problemas descendente, luego por nombre
        summary.sort(key=lambda x: (-x['total_problems'], x['name']))
        
        return summary
    
    def format_problems_for_summary_table(self, problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formatea una lista de problemas para la tabla de "Resumen de Alertas".
        AGRUPADO: Realiza un recuento por nombre/descripción del problema indicando
        cuántas veces ha saltado/ocurrido en total (considerando histórico + activo).
        
        Args:
            problems: Lista de problemas enriquecidos (salida de get_problems_history)
            
        Returns:
            Lista de diccionarios formateados para la tabla AGRUPADA:
            - host, trigger_alerta, severidad, nombre_problema, count
        """
        # Agrupar por nombre de problema (description) y host
        grouped = defaultdict(lambda: {
            'host': '',
            'trigger_alerta': '',
            'severidad': '',
            'nombre_problema': '',
            'count': 0,
            'severity_num': 0,
            'latest_time': '',
            'latest_clock': 0
        })
        
        for problem in problems:
            key = (problem.get('host', 'Desconocido'), problem.get('description', 'Sin descripción'))
            group = grouped[key]
            
            if group['count'] == 0:
                group['host'] = problem.get('host', 'Desconocido')
                group['trigger_alerta'] = problem.get('description', 'Sin descripción')
                group['severidad'] = problem.get('severity', 'Not classified')
                group['nombre_problema'] = problem.get('description', 'Sin descripción')
                group['severity_num'] = problem.get('severity_num', 0)
                group['latest_time'] = problem.get('time', '')
                group['latest_clock'] = problem.get('clock', 0)
            else:
                # Mantener el más reciente
                if problem.get('clock', 0) > group['latest_clock']:
                    group['latest_time'] = problem.get('time', '')
                    group['latest_clock'] = problem.get('clock', 0)
            
            group['count'] += 1
        
        # Convertir a lista y ordenar por count descendente, luego por tiempo descendente
        formatted = list(grouped.values())
        formatted.sort(key=lambda x: (-x['count'], -x['latest_clock']))
        
        # Eliminar campos internos
        for item in formatted:
            item.pop('severity_num', None)
            item.pop('latest_time', None)
            item.pop('latest_clock', None)
        
        return formatted

    def format_events_for_summary_table(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formatea una lista de eventos (de event.get tipo Top Triggers) para la tabla de "Resumen de Alertas".
        AGRUPADO ESTRICTO: Realiza un recuento por Host + Nombre del Trigger (trigger_description),
        sumando el recuento total de ocurrencias históricas (cada evento value=1 es una ocurrencia).
        
        Args:
            events: Lista de eventos enriquecidos (salida de get_events_history)
            
        Returns:
            Lista de diccionarios formateados para la tabla AGRUPADA:
            - host, trigger_alerta, severidad, nombre_problema, count
        """
        # Agrupar por Host + Nombre del Trigger (trigger_description)
        grouped = defaultdict(lambda: {
            'host': '',
            'trigger_alerta': '',
            'severidad': '',
            'nombre_problema': '',
            'count': 0,
            'severity_num': 0,
            'latest_time': '',
            'latest_clock': 0
        })
        
        for event in events:
            # Clave de agrupación: Host + Trigger Description (nombre del trigger)
            key = (event.get('host', 'Desconocido'), event.get('trigger_description', 'Sin descripción'))
            group = grouped[key]
            
            if group['count'] == 0:
                group['host'] = event.get('host', 'Desconocido')
                group['trigger_alerta'] = event.get('trigger_description', 'Sin descripción')
                group['severidad'] = event.get('severity', 'Not classified')
                group['nombre_problema'] = event.get('trigger_description', 'Sin descripción')
                group['severity_num'] = event.get('severity_num', 0)
                group['latest_time'] = event.get('time', '')
                group['latest_clock'] = event.get('clock', 0)
            else:
                # Mantener el más reciente
                if event.get('clock', 0) > group['latest_clock']:
                    group['latest_time'] = event.get('time', '')
                    group['latest_clock'] = event.get('clock', 0)
            
            group['count'] += 1
        
        # Convertir a lista y ordenar por count descendente, luego por tiempo descendente
        formatted = list(grouped.values())
        formatted.sort(key=lambda x: (-x['count'], -x['latest_clock']))
        
        # Eliminar campos internos
        for item in formatted:
            item.pop('severity_num', None)
            item.pop('latest_time', None)
            item.pop('latest_clock', None)
        
        return formatted

    def get_glpi_links(self, problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extrae los enlaces GLPI de los problemas que tengan el tag '__zbx_glpi_link'.
        
        Args:
            problems: Lista de problemas enriquecidos (con campo 'tags')
            
        Returns:
            Lista de diccionarios con ticket_id, title, url, status
        """
        glpi_links = []
        
        for problem in problems:
            tags = problem.get('tags', {})
            glpi_link = tags.get('__zbx_glpi_link', '')
            
            if glpi_link:
                # El valor del tag puede ser una URL completa o un ID de ticket
                # Intentar extraer ticket_id si es una URL de GLPI
                ticket_id = glpi_link
                title = problem.get('description', 'Sin descripción')
                url = glpi_link
                status = 'Abierto' if not problem.get('is_resolved', False) else 'Resuelto'
                
                # Si es una URL, intentar extraer el ID del ticket
                if glpi_link.startswith('http'):
                    # Patrones comunes: /front/ticket.form.php?id=123 o /tickets/123
                    import re
                    match = re.search(r'[?&]id=(\d+)', glpi_link)
                    if match:
                        ticket_id = match.group(1)
                    else:
                        match = re.search(r'/tickets?/(\d+)', glpi_link)
                        if match:
                            ticket_id = match.group(1)
                
                glpi_links.append({
                    'ticket_id': ticket_id,
                    'title': title,
                    'url': url,
                    'status': status,
                    'host': problem.get('host', 'Desconocido'),
                    'severity': problem.get('severity', 'Not classified'),
                    'eventid': problem.get('eventid')
                })
        
        return glpi_links
    
    def format_problems_for_active_alerts_table(self, problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formatea una lista de problemas para la tabla de "Alertas Activas" (tabla temporal).
        Incluye tanto problemas activos como resueltos (histórico).
        
        Args:
            problems: Lista de problemas enriquecidos (con campos status, recovery_time, is_resolved)
            
        Returns:
            Lista de diccionarios formateados para la tabla temporal:
            - time, recovery_time, status, host, severity, trigger_problem, duration
        """
        formatted = []
        
        for problem in problems:
            formatted.append({
                'time': problem.get('time', ''),
                'recovery_time': problem.get('recovery_time', ''),
                'status': problem.get('status', 'PROBLEM'),
                'host': problem.get('host', 'Desconocido'),
                'severity': problem.get('severity', 'Not classified'),
                'trigger_problem': problem.get('description', 'Sin descripción'),
                'duration': problem.get('duration', ''),
                'eventid': problem.get('eventid'),
                'clock': problem.get('clock', 0)
            })
        
        # Ordenar por tiempo descendente (más recientes primero)
        formatted.sort(key=lambda x: x['clock'], reverse=True)
        
        return formatted
    
    def get_complete_report_data(self, time_from: int = None, time_till: int = None, limit: int = 10000) -> Dict[str, Any]:
        """
        Obtiene todos los datos estructurados necesarios para generar el informe completo.
        
        Args:
            time_from: Timestamp de inicio (opcional)
            time_till: Timestamp de fin (opcional)
            limit: Límite máximo de problemas históricos a retornar (por defecto 10000)
        
        Returns:
            Diccionario con todas las secciones del informe:
            - environments: Resumen por entorno (Estado Entornos) - CON filtro temporal
            - alerts_summary: Datos para Resumen de Alertas (AGRUPADO por Host + Trigger Name - tipo Top Triggers) - CON filtro temporal
            - active_alerts: Datos para Alertas Activas (SOLO alertas activas actuales, SIN filtro temporal)
            - glpi_links: Enlaces GLPI extraídos del tag __zbx_glpi_link
            - timestamp: Timestamp de generación
            - total_problems: Total global de problemas (histórico + activo) - CON filtro temporal
            - total_active_problems: Total de problemas activos únicamente (SIN filtro temporal)
            - total_events: Total de eventos de triggers (tipo Top Triggers) - CON filtro temporal
        """
        # Estado de Entornos y Resumen de Alertas: CON filtro temporal
        environment_summary = self.get_environment_summary(time_from=time_from, time_till=time_till)
        
        # Obtener histórico completo de problemas (activos + resueltos) - para Resumen de Alertas y GLPI
        all_problems_history = self.get_problems_history(time_from=time_from, time_till=time_till, limit=limit)
        
        # Obtener histórico de eventos de triggers (tipo Top Triggers de Zabbix) - para Resumen de Alertas agrupado
        all_events_history = self.get_events_history(time_from=time_from, time_till=time_till, limit=limit)
        
        # Obtener SOLO problemas activos actuales - SIN filtro temporal (para tabla de Alertas Activas)
        active_problems = self.get_active_problems()
        
        # Formatear para las diferentes tablas
        # Resumen de Alertas: usar eventos (event.get) para replicar Top Triggers - agrupado por Host + Trigger Name
        alerts_summary_data = self.format_events_for_summary_table(all_events_history)
        # Tabla temporal (Alertas Activas): usar SOLO problemas activos actuales (SIN filtro temporal)
        active_alerts_data = self.format_problems_for_active_alerts_table(active_problems)
        
        # Extraer enlaces GLPI del histórico de problemas (CON filtro temporal)
        glpi_links = self.get_glpi_links(all_problems_history)
        
        # Calcular totales globales
        total_problems = len(all_problems_history)
        total_active_problems = len(active_problems)
        total_events = len(all_events_history)
        total_hosts = sum(env['total_hosts'] for env in environment_summary)
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_problems': total_problems,
            'total_active_problems': total_active_problems,
            'total_events': total_events,
            'total_hosts': total_hosts,
            'environments': environment_summary,
            'alerts_summary': alerts_summary_data,
            'active_alerts': active_alerts_data,
            'glpi_links': glpi_links
        }
    
    def clear_cache(self) -> None:
        """Limpia todas las cachés internas."""
        self._hostgroups_cache = None
        self._hosts_by_group_cache = {}
        self._problems_cache = None
        self._problems_history_cache = None
        self._events_history_cache = None


def print_environment_summary(environments: List[Dict[str, Any]]) -> None:
    """
    Imprime un resumen tabular de los entornos (Estado Entornos).
    
    Args:
        environments: Lista de resúmenes de entorno desde get_environment_summary()
    """
    if not environments:
        print("  No hay entornos configurados.")
        return
    
    print("\n" + "=" * 100)
    print("  ESTADO DE ENTORNOS (HostGroups)")
    print("=" * 100)
    
    # Cabecera
    header = f"{'Entorno':<35} {'Hosts':>6} {'Problemas':>10} {'Disaster':>8} {'High':>6} {'Average':>8} {'Warning':>6} {'Info':>6}"
    separator = "-" * 100
    
    print(separator)
    print(header)
    print(separator)
    
    for env in environments:
        sev = env['problems_by_severity']
        row = f"{env['name'][:34]:<35} {env['total_hosts']:>6} {env['total_problems']:>10} "
        row += f"{sev['Disaster']:>8} {sev['High']:>6} {sev['Average']:>8} {sev['Warning']:>6} {sev['Information']:>6}"
        print(row)
    
    print(separator)
    
    # Totales
    total_hosts = sum(e['total_hosts'] for e in environments)
    total_problems = sum(e['total_problems'] for e in environments)
    total_disaster = sum(e['problems_by_severity']['Disaster'] for e in environments)
    total_high = sum(e['problems_by_severity']['High'] for e in environments)
    total_average = sum(e['problems_by_severity']['Average'] for e in environments)
    total_warning = sum(e['problems_by_severity']['Warning'] for e in environments)
    total_info = sum(e['problems_by_severity']['Information'] for e in environments)
    
    total_row = f"{'TOTAL':<35} {total_hosts:>6} {total_problems:>10} "
    total_row += f"{total_disaster:>8} {total_high:>6} {total_average:>8} {total_warning:>6} {total_info:>6}"
    print(total_row)
    print(separator)


def print_alerts_summary_table(alerts: List[Dict[str, Any]]) -> None:
    """
    Imprime la tabla de Resumen de Alertas (AGRUPADA con conteo).
    
    Args:
        alerts: Lista formateada desde format_problems_for_summary_table() con campo 'count'
    """
    if not alerts:
        print("\n  No hay alertas para mostrar en el resumen.")
        return
    
    print("\n" + "=" * 130)
    print("  RESUMEN DE ALERTAS (Agrupado por problema - Conteo de ocurrencias)")
    print("=" * 130)
    
    col_host = 25
    col_trigger = 35
    col_severity = 12
    col_name = 35
    col_count = 8
    
    header = f"{'Host':<{col_host}} {'Trigger / Alerta':<{col_trigger}} {'Severidad':<{col_severity}} {'Nombre de problemas':<{col_name}} {'Veces':>{col_count}}"
    separator = "-" * (col_host + col_trigger + col_severity + col_name + col_count + 4)
    
    print(separator)
    print(header)
    print(separator)
    
    for alert in alerts:
        host = alert['host'][:col_host-1] if len(alert['host']) > col_host else alert['host']
        trigger = alert['trigger_alerta'][:col_trigger-1] if len(alert['trigger_alerta']) > col_trigger else alert['trigger_alerta']
        severity = alert['severidad'][:col_severity-1] if len(alert['severidad']) > col_severity else alert['severidad']
        name = alert['nombre_problema'][:col_name-1] if len(alert['nombre_problema']) > col_name else alert['nombre_problema']
        count = alert.get('count', 1)
        
        row = f"{host:<{col_host}} {trigger:<{col_trigger}} {severity:<{col_severity}} {name:<{col_name}} {count:>{col_count}}"
        print(row)
    
    print(separator)
    print(f"Total: {len(alerts)} problema(s) único(s) | Total ocurrencias: {sum(a.get('count', 1) for a in alerts)}")


def print_active_alerts_table(alerts: List[Dict[str, Any]]) -> None:
    """
    Imprime la tabla de Alertas (Tabla Temporal - Histórico + Activas).
    
    Args:
        alerts: Lista formateada desde format_problems_for_active_alerts_table() con campos status, recovery_time
    """
    if not alerts:
        print("\n  No hay alertas para mostrar.")
        return
    
    print("\n" + "=" * 150)
    print("  ALERTAS (Tabla Temporal - Histórico + Activas)")
    print("=" * 150)
    
    col_time = 19
    col_recovery = 19
    col_status = 10
    col_host = 25
    col_severity = 12
    col_trigger = 40
    col_duration = 12
    
    header = (f"{'Time':<{col_time}} {'Recovery Time':<{col_recovery}} {'Status':<{col_status}} "
              f"{'Host':<{col_host}} {'Severity':<{col_severity}} {'Trigger/Problem':<{col_trigger}} {'Duration':<{col_duration}}")
    separator = "-" * (col_time + col_recovery + col_status + col_host + col_severity + col_trigger + col_duration + 6)
    
    print(separator)
    print(header)
    print(separator)
    
    for alert in alerts:
        time_str = alert['time'][:col_time-1] if len(alert['time']) > col_time else alert['time']
        recovery = alert['recovery_time'][:col_recovery-1] if len(alert['recovery_time']) > col_recovery else alert['recovery_time']
        status = alert['status'][:col_status-1] if len(alert['status']) > col_status else alert['status']
        host = alert['host'][:col_host-1] if len(alert['host']) > col_host else alert['host']
        severity = alert['severity'][:col_severity-1] if len(alert['severity']) > col_severity else alert['severity']
        trigger = alert['trigger_problem'][:col_trigger-1] if len(alert['trigger_problem']) > col_trigger else alert['trigger_problem']
        duration = alert['duration'][:col_duration-1] if len(alert['duration']) > col_duration else alert['duration']
        
        row = (f"{time_str:<{col_time}} {recovery:<{col_recovery}} {status:<{col_status}} "
               f"{host:<{col_host}} {severity:<{col_severity}} {trigger:<{col_trigger}} {duration:<{col_duration}}")
        print(row)
    
    print(separator)
    active_count = sum(1 for a in alerts if a.get('status') == 'PROBLEM')
    resolved_count = sum(1 for a in alerts if a.get('status') == 'OK')
    print(f"Total: {len(alerts)} alerta(s) | Activas: {active_count} | Resueltas: {resolved_count}")


# Función de prueba independiente
if __name__ == "__main__":
    print("Módulo de recopilación de datos - Prueba independiente")
    print("Este módulo está diseñado para ser importado desde main.py")