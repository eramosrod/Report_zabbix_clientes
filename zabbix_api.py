#!/usr/bin/env python3
"""
Módulo de cliente para la API JSON-RPC de Zabbix.
Separado para evitar importaciones circulares.
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional


class ZabbixAPI:
    """Cliente para interactuar con la API JSON-RPC de Zabbix."""
    
    # Mapeo de severidades de Zabbix (nombres oficiales en inglés)
    SEVERITY_MAP = {
        0: "Not classified",
        1: "Information",
        2: "Warning",
        3: "Average",
        4: "High",
        5: "Disaster"
    }
    
    # Macros comunes de Zabbix que se pueden resolver
    COMMON_MACROS = {
        '{HOST.NAME}': 'host_name',
        '{HOST.HOST}': 'host_host',
        '{HOST.IP}': 'host_ip',
        '{HOST.DNS}': 'host_dns',
        '{HOST.CONN}': 'host_conn',
        '{HOST.PORT}': 'host_port',
        '{ITEM.NAME}': 'item_name',
        '{ITEM.KEY}': 'item_key',
        '{ITEM.VALUE}': 'item_value',
        '{ITEM.LASTVALUE}': 'item_lastvalue',
        '{TRIGGER.NAME}': 'trigger_name',
        '{TRIGGER.DESCRIPTION}': 'trigger_description',
        '{TRIGGER.STATUS}': 'trigger_status',
        '{TRIGGER.SEVERITY}': 'trigger_severity',
        '{TRIGGER.PRIORITY}': 'trigger_priority',
        '{TRIGGER.URL}': 'trigger_url',
        '{EVENT.ID}': 'event_id',
        '{EVENT.TIME}': 'event_time',
        '{EVENT.DATE}': 'event_date',
        '{EVENT.NAME}': 'event_name',
        '{EVENT.OPDATA}': 'event_opdata',
        '{EVENT.VALUE}': 'event_value',
        '{EVENT.STATUS}': 'event_status',
        '{EVENT.RECOVERY.ID}': 'event_recovery_id',
        '{EVENT.RECOVERY.TIME}': 'event_recovery_time',
        '{EVENT.RECOVERY.DATE}': 'event_recovery_date',
        '{EVENT.RECOVERY.VALUE}': 'event_recovery_value',
        '{EVENT.RECOVERY.STATUS}': 'event_recovery_status',
    }
    
    def __init__(self, url: str, timeout: int = 30, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Inicializa el cliente de la API de Zabbix.
        
        Args:
            url: URL base del servidor Zabbix (ej: https://zabbix.example.com)
            timeout: Timeout en segundos para las peticiones HTTP
            max_retries: Número máximo de reintentos para errores transitorios
            retry_delay: Delay base en segundos entre reintentos (backoff exponencial)
        """
        # Asegurar que la URL termine en /api_jsonrpc.php
        if not url.endswith('/api_jsonrpc.php'):
            url = url.rstrip('/') + '/api_jsonrpc.php'
        self.url = url
        self.auth_token = None
        self.request_id = 0
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def _make_request(self, method: str, params: dict) -> dict:
        """
        Realiza una petición JSON-RPC a la API de Zabbix con reintentos y manejo robusto de errores.
        
        Args:
            method: Método de la API (ej: 'user.login', 'hostgroup.get')
            params: Parámetros del método
            
        Returns:
            Respuesta de la API como diccionario
            
        Raises:
            Exception: Si hay error en la petición o en la respuesta tras agotar reintentos
        """
        self.request_id += 1
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }
        
        headers = {
            "Content-Type": "application/json-rpc"
        }
        
        if self.auth_token and method != "user.login":
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(self.url, json=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                
                # Verificar respuesta vacía
                if not response.content:
                    raise Exception("Respuesta vacía del servidor")
                
                result = response.json()
                
                # Verificar estructura de respuesta JSON-RPC
                if not isinstance(result, dict):
                    raise Exception(f"Respuesta inválida: se esperaba objeto JSON, recibido {type(result).__name__}")
                
                if "error" in result:
                    error_msg = result['error'].get('message', 'Desconocido')
                    error_data = result['error'].get('data', '')
                    error_code = result['error'].get('code', -32603)
                    
                    # Errores que no deberían reintentarse (errores de autenticación, parámetros inválidos, etc.)
                    if error_code in (-32600, -32601, -32602, -32603) or "auth" in error_msg.lower() or "login" in error_msg.lower() or "permission" in error_msg.lower():
                        raise Exception(f"Error API Zabbix: {error_msg} - {error_data}")
                    
                    # Para otros errores, permitir reintento
                    raise Exception(f"Error API Zabbix: {error_msg} - {error_data}")
                
                # Verificar que existe el campo result
                if "result" not in result:
                    raise Exception("Respuesta API inválida: falta campo 'result'")
                
                return result.get("result")
                
            except requests.exceptions.Timeout:
                last_exception = Exception(f"Timeout ({self.timeout}s) en petición a {method}")
            except requests.exceptions.ConnectionError as e:
                last_exception = Exception(f"Error de conexión: {str(e)}")
            except requests.exceptions.RequestException as e:
                last_exception = Exception(f"Error de petición HTTP: {str(e)}")
            except json.JSONDecodeError as e:
                last_exception = Exception(f"Respuesta inválida del servidor (no es JSON válido): {str(e)}")
            except Exception as e:
                # Re-lanzar errores que no son transitorios (autenticación, parámetros, etc.)
                if "Error API Zabbix" in str(e) or "Respuesta inválida" in str(e) or "Respuesta vacía" in str(e) or "falta campo" in str(e):
                    raise
                last_exception = e
            
            # Si no es el último intento, esperar antes de reintentar
            if attempt < self.max_retries:
                wait_time = self.retry_delay * (2 ** attempt)  # Backoff exponencial
                time.sleep(wait_time)
        
        # Si llegamos aquí, se agotaron los reintentos
        raise Exception(f"Falló tras {self.max_retries + 1} intentos: {str(last_exception)}")
    
    def login(self, username: str, password: str) -> str:
        """
        Autentica al usuario y obtiene el token de sesión.
        """
        # Intentar con parámetros para Zabbix 6.0+ (username) y legacy (user)
        for param_name in ["username", "user"]:
            params = {
                param_name: username,
                "password": password
            }
            
            try:
                self.auth_token = self._make_request("user.login", params)
                print(f"  ✓ Autenticación exitosa usando parámetro '{param_name}'")
                return self.auth_token
            except Exception as e:
                error_msg = str(e).lower()
                # Si es error de credenciales, probar el siguiente formato
                if "invalid" in error_msg or "incorrect" in error_msg or "login" in error_msg or "password" in error_msg:
                    continue
                # Si es otro error (conexión, etc.), relanzar
                raise
        
        # Si llegamos aquí, ninguno de los formatos funcionó
        raise Exception("Error de autenticación: usuario o contraseña incorrectos.")
    
    def get_hostgroups(self) -> list:
        """Obtiene la lista de grupos de hosts."""
        if not self.auth_token:
            raise Exception("No autenticado. Llame a login() primero.")
        
        params = {
            "output": ["groupid", "name"],
            "sortfield": "name"
        }
        
        return self._make_request("hostgroup.get", params)

    def get_active_alerts(self) -> list:
        """
        Obtiene los problemas activos (triggers con valor 1).
        Método legacy mantenido por compatibilidad.
        """
        if not self.auth_token:
            raise Exception("No autenticado. Llame a login() primero.")

        params = {
            "output": ["triggerid", "description", "priority", "lastchange"],
            "filter": {
                "value": 1,
                "status": 0          # Solo triggers habilitados (0=habilitado, 1=deshabilitado)
            },
            "only_true": True,
            "sortfield": "lastchange",
            "sortorder": "DESC",
            "monitored": True        # Solo triggers monitorizados (excluye deshabilitados)
        }

        return self._make_request("trigger.get", params)

    def get_active_problems(self) -> List[Dict[str, Any]]:
        """
        Obtiene los problemas activos usando event.get (compatible con más versiones de Zabbix).
        event.get soporta selectHosts para obtener información del host directamente.
        
        Returns:
            Lista de problemas con información enriquecida: host, severidad, duración, etc.
        """
        if not self.auth_token:
            raise Exception("No autenticado. Llame a login() primero.")

        # Usar event.get en lugar de problem.get para compatibilidad con selectHosts
        # value=1 significa problemas activos (no resueltos)
        # Filtrar: solo triggers habilitados (status=0) y hosts monitorizados (monitored=true)
        # NOTA: expandDescription NO es válido en event.get en versiones recientes de Zabbix
        # Las macros se resolverán manualmente si es necesario
        params = {
            "output": ["eventid", "name", "severity", "clock", "ns"],
            "selectHosts": ["hostid", "name", "status"],
            "selectTags": ["tag", "value"],
            "value": 1,  # Solo problemas activos (1=problem, 0=ok)
            "sortfield": "clock",
            "sortorder": "DESC"
        }

        problems = self._make_request("event.get", params)
        
        # Filtrar problemas de hosts deshabilitados (status=1)
        host_filtered = []
        for problem in problems:
            hosts = problem.get("hosts", [])
            # Verificar que al menos un host esté habilitado (status=0)
            # El campo status puede venir como string "0"/"1" o no venir (default 0=habilitado)
            host_enabled = True
            for h in hosts:
                if str(h.get("status", "0")) != "0":
                    host_enabled = False
                    break
            
            if host_enabled:
                host_filtered.append(problem)
        
        # Filtrar problemas de triggers deshabilitados
        # Obtener triggerids de los problemas filtrados por host
        if host_filtered:
            # Para obtener el trigger status, necesitamos consultar trigger.get
            # Los problemas de event.get no incluyen directamente el trigger status
            # Usamos objectid como triggerid (en event.get para triggers, objectid = triggerid)
            triggerids = list(set([p.get("objectid") for p in host_filtered if p.get("objectid")]))
            if triggerids:
                triggers = self._make_request("trigger.get", {
                    "triggerids": triggerids,
                    "output": ["triggerid", "status"]
                })
                trigger_status_map = {t["triggerid"]: str(t.get("status", "0")) for t in triggers}
                
                # Filtrar solo triggers habilitados (status=0)
                filtered_problems = []
                for problem in host_filtered:
                    triggerid = problem.get("objectid")
                    trigger_status = trigger_status_map.get(triggerid, "0")
                    
                    if triggerid and trigger_status == "0":
                        filtered_problems.append(problem)
                    elif not triggerid:
                        # Si no hay triggerid, mantener el problema (no se puede verificar)
                        filtered_problems.append(problem)
            else:
                filtered_problems = host_filtered
        else:
            filtered_problems = []
        
        return filtered_problems

    def _format_duration(self, seconds: int) -> str:
        """Formatea una duración en segundos a formato legible (días, horas, minutos)."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h"

    def resolve_macros(self, text: str, host_info: Dict[str, Any] = None, trigger_info: Dict[str, Any] = None,
                       item_info: Dict[str, Any] = None, event_info: Dict[str, Any] = None) -> str:
        """
        Resuelve macros de Zabbix en un texto dado.
        
        Args:
            text: Texto que puede contener macros de Zabbix
            host_info: Información del host (name, host, ip, dns, port)
            trigger_info: Información del trigger (description, priority, status, url)
            item_info: Información del item (name, key, lastvalue)
            event_info: Información del evento (eventid, clock, name, value, etc.)
            
        Returns:
            Texto con macros resueltas
        """
        if not text:
            return text
            
        result = text
        
        # Resolver macros de host
        if host_info:
            result = result.replace('{HOST.NAME}', host_info.get('name', ''))
            result = result.replace('{HOST.HOST}', host_info.get('host', ''))
            result = result.replace('{HOST.IP}', host_info.get('ip', ''))
            result = result.replace('{HOST.DNS}', host_info.get('dns', ''))
            result = result.replace('{HOST.CONN}', host_info.get('conn', ''))
            result = result.replace('{HOST.PORT}', str(host_info.get('port', '')))
        
        # Resolver macros de trigger
        if trigger_info:
            result = result.replace('{TRIGGER.NAME}', trigger_info.get('description', ''))
            result = result.replace('{TRIGGER.DESCRIPTION}', trigger_info.get('description', ''))
            result = result.replace('{TRIGGER.STATUS}', str(trigger_info.get('status', '')))
            result = result.replace('{TRIGGER.SEVERITY}', str(trigger_info.get('priority', '')))
            result = result.replace('{TRIGGER.PRIORITY}', str(trigger_info.get('priority', '')))
            result = result.replace('{TRIGGER.URL}', trigger_info.get('url', ''))
        
        # Resolver macros de item
        if item_info:
            result = result.replace('{ITEM.NAME}', item_info.get('name', ''))
            result = result.replace('{ITEM.KEY}', item_info.get('key_', ''))
            result = result.replace('{ITEM.VALUE}', str(item_info.get('lastvalue', '')))
            result = result.replace('{ITEM.LASTVALUE}', str(item_info.get('lastvalue', '')))
        
        # Resolver macros de evento
        if event_info:
            result = result.replace('{EVENT.ID}', str(event_info.get('eventid', '')))
            result = result.replace('{EVENT.NAME}', event_info.get('name', ''))
            result = result.replace('{EVENT.OPDATA}', event_info.get('opdata', ''))
            result = result.replace('{EVENT.VALUE}', str(event_info.get('value', '')))
            result = result.replace('{EVENT.STATUS}', str(event_info.get('value', '')))
            # Formatear tiempo si está disponible
            if 'clock' in event_info:
                from datetime import datetime
                dt = datetime.fromtimestamp(int(event_info['clock']))
                result = result.replace('{EVENT.TIME}', dt.strftime('%H:%M:%S'))
                result = result.replace('{EVENT.DATE}', dt.strftime('%Y-%m-%d'))
        
        return result

    def get_active_problems_raw(self, time_from: int = None, time_till: int = None) -> List[Dict[str, Any]]:
        """
        Obtiene los problemas ACTIVOS ACTUALES usando problem.get SIN enriquecer.
        Devuelve los datos crudos de la API para uso interno (ej. agrupación por hostgroup).
        NOTA: problem.get devuelve SOLO problemas actualmente activos (no resueltos).
        
        Returns:
            Lista de problemas crudos con campos: eventid, name, severity, clock, ns, hosts, tags
        """
        if not self.auth_token:
            raise Exception("No autenticado. Llame a login() primero.")

        # Usar problem.get para obtener SOLO problemas actualmente activos
        # problem.get NO soporta selectHosts en algunas versiones de Zabbix
        # problem.get solo soporta sortfield: "eventid"
        # NOTA: expandDescription NO es válido en problem.get en versiones recientes de Zabbix
        # Las macros se resolverán manualmente si es necesario
        params = {
            "output": ["eventid", "name", "severity", "clock", "ns", "objectid"],
            "selectTags": ["tag", "value"],
            "sortfield": "eventid",
            "sortorder": "DESC"
        }
        
        if time_from:
            params["time_from"] = time_from
        if time_till:
            params["time_till"] = time_till

        problems = self._make_request("problem.get", params)
        
        # Obtener información de hosts usando event.get con los eventids
        # event.get SÍ soporta selectHosts
        if problems:
            eventids = [p["eventid"] for p in problems]
            # Consultar en lotes para evitar límites de la API
            batch_size = 500
            all_events = []
            
            for i in range(0, len(eventids), batch_size):
                batch = eventids[i:i + batch_size]
                event_params = {
                    "eventids": batch,
                    "output": ["eventid"],
                    "selectHosts": ["hostid", "name", "status"]
                }
                events = self._make_request("event.get", event_params)
                all_events.extend(events)
            
            # Crear mapa eventid -> hosts
            event_hosts_map = {}
            for event in all_events:
                event_hosts_map[event["eventid"]] = event.get("hosts", [])
            
            # Enriquecer problemas con información de hosts
            for problem in problems:
                eventid = problem["eventid"]
                if eventid in event_hosts_map:
                    problem["hosts"] = event_hosts_map[eventid]
                else:
                    problem["hosts"] = []

        # Filtrar problemas de hosts deshabilitados (status=1)
        host_filtered = []
        for problem in problems:
            hosts = problem.get("hosts", [])
            # Verificar que al menos un host esté habilitado (status=0)
            # El campo status puede venir como string "0"/"1" o no venir (default 0=habilitado)
            host_enabled = True
            for h in hosts:
                if str(h.get("status", "0")) != "0":
                    host_enabled = False
                    break
            
            if host_enabled:
                host_filtered.append(problem)
        
        # Filtrar problemas de triggers deshabilitados
        # Obtener triggerids de los problemas filtrados por host
        if host_filtered:
            # Para obtener el trigger status, necesitamos consultar trigger.get
            # Los problemas de problem.get no incluyen directamente el trigger status
            # Usamos objectid como triggerid (en problem.get para triggers, objectid = triggerid)
            triggerids = list(set([p.get("objectid") for p in host_filtered if p.get("objectid")]))
            if triggerids:
                triggers = self._make_request("trigger.get", {
                    "triggerids": triggerids,
                    "output": ["triggerid", "status"]
                })
                trigger_status_map = {t["triggerid"]: str(t.get("status", "0")) for t in triggers}
                
                # Filtrar solo triggers habilitados (status=0)
                filtered_problems = []
                for problem in host_filtered:
                    triggerid = problem.get("objectid")
                    trigger_status = trigger_status_map.get(triggerid, "0")
                    
                    if triggerid and trigger_status == "0":
                        filtered_problems.append(problem)
                    elif not triggerid:
                        # Si no hay triggerid, mantener el problema (no se puede verificar)
                        filtered_problems.append(problem)
            else:
                filtered_problems = host_filtered
        else:
            filtered_problems = []
        
        return filtered_problems

    def get_problems_history(self, time_from: int = None, time_till: int = None, limit: int = 10000) -> List[Dict[str, Any]]:
        """
        Obtiene el histórico de problemas (resueltos y activos) usando problem.get.
        Incluye problemas resueltos para tener el histórico completo necesario para el informe.
        
        NOTA: problem.get no soporta selectHosts en algunas versiones de Zabbix.
        Para obtener los nombres de hosts, hacemos una segunda consulta con event.get
        usando los eventids obtenidos.
        
        Args:
            time_from: Timestamp de inicio (opcional, por defecto últimos 30 días)
            time_till: Timestamp de fin (opcional, por defecto ahora)
            limit: Límite máximo de problemas a retornar (por defecto 10000 para histórico completo)
             
        Returns:
            Lista de problemas con información: eventid, name, severity, clock, ns, hosts, tags, r_eventid
        """
        if not self.auth_token:
            raise Exception("No autenticado. Llame a login() primero.")

        # Por defecto, últimos 30 días
        if time_from is None:
            time_from = int((datetime.now().timestamp()) - (30 * 24 * 3600))
        if time_till is None:
            time_till = int(datetime.now().timestamp())

        # Paso 1: Obtener problemas históricos con problem.get (incluye r_eventid para resueltos)
        # problem.get NO soporta selectHosts en algunas versiones
        # Añadimos 'limit' para asegurar que se obtenga el histórico completo (evita límite por defecto de la API)
        # No usamos 'recent' para no filtrar solo problemas recientes
        # NOTA: expandDescription NO es válido en problem.get en versiones recientes de Zabbix
        # Las macros se resolverán manualmente si es necesario
        params = {
            "output": ["eventid", "name", "severity", "clock", "ns"],
            "selectTags": ["tag", "value"],
            "selectSuppressionData": ["suppress_until"],
            "time_from": time_from,
            "time_till": time_till,
            "limit": limit,
            "sortfield": "eventid",
            "sortorder": "DESC"
        }

        problems = self._make_request("problem.get", params)
        
        # Paso 2: Obtener información de hosts usando event.get con los eventids
        # event.get SÍ soporta selectHosts
        if problems:
            eventids = [p["eventid"] for p in problems]
            # Consultar en lotes para evitar límites de la API
            batch_size = 500
            all_events = []
            
            for i in range(0, len(eventids), batch_size):
                batch = eventids[i:i + batch_size]
                event_params = {
                    "eventids": batch,
                    "output": ["eventid"],
                    "selectHosts": ["hostid", "name", "status"]
                }
                events = self._make_request("event.get", event_params)
                all_events.extend(events)
            
            # Crear mapa eventid -> hosts
            event_hosts_map = {}
            for event in all_events:
                event_hosts_map[event["eventid"]] = event.get("hosts", [])
            
            # Enriquecer problemas con información de hosts
            for problem in problems:
                eventid = problem["eventid"]
                if eventid in event_hosts_map:
                    problem["hosts"] = event_hosts_map[eventid]
                else:
                    problem["hosts"] = []

        # Filtrar problemas de hosts deshabilitados (status=1)
        host_filtered = []
        for problem in problems:
            hosts = problem.get("hosts", [])
            # Verificar que al menos un host esté habilitado (status=0)
            # El campo status puede venir como string "0"/"1" o no venir (default 0=habilitado)
            host_enabled = any(str(h.get("status", "0")) == "0" for h in hosts)
            if host_enabled:
                host_filtered.append(problem)
        
        # Filtrar problemas de triggers deshabilitados
        # Obtener triggerids de los problemas filtrados por host
        if host_filtered:
            # Para obtener el trigger status, necesitamos consultar trigger.get
            # Los problemas de problem.get no incluyen directamente el trigger status
            # Usamos objectid como triggerid (en problem.get para triggers, objectid = triggerid)
            triggerids = list(set([p.get("objectid") for p in host_filtered if p.get("objectid")]))
            if triggerids:
                triggers = self._make_request("trigger.get", {
                    "triggerids": triggerids,
                    "output": ["triggerid", "status"]
                })
                trigger_status_map = {t["triggerid"]: str(t.get("status", "0")) for t in triggers}
                
                # Filtrar solo triggers habilitados (status=0)
                filtered_problems = []
                for problem in host_filtered:
                    triggerid = problem.get("objectid")
                    if triggerid and trigger_status_map.get(triggerid, "0") == "0":
                        filtered_problems.append(problem)
                    elif not triggerid:
                        # Si no hay triggerid, mantener el problema (no se puede verificar)
                        filtered_problems.append(problem)
            else:
                filtered_problems = host_filtered
        else:
            filtered_problems = []
        
        return filtered_problems

    def get_hosts_by_group(self, groupid: str) -> list:
        """
        Obtiene los hosts de un grupo específico.
        """
        if not self.auth_token:
            raise Exception("No autenticado. Llame a login() primero.")

        params = {
            "groupids": groupid,
            "output": ["hostid", "name"]
        }

        return self._make_request("host.get", params)

    def get_events_history(self, time_from: int = None, time_till: int = None, limit: int = 10000) -> List[Dict[str, Any]]:
        """
        Obtiene el histórico de eventos de triggers (tipo Top Triggers de Zabbix) usando event.get.
        Este método replica la consulta del informe "Top Triggers" de Zabbix para obtener
        un recuento exacto y agrupado de las alertas por Host y Nombre de Trigger.
        
        Parámetros clave:
        - source: 0 (eventos de disparadores/triggers)
        - object: 0 (triggers)
        - value: 1 (solo eventos de creación de problemas, para contar cada vez que salta la alerta)
        - time_from: Timestamp hacia atrás en el tiempo (por defecto últimos 30 días)
        - selectHosts: ["hostid", "name"] para obtener el nombre del host
        - NOTA: expandDescription NO es válido en event.get en versiones recientes de Zabbix
        - Las macros se resolverán manualmente si es necesario
        
        Args:
            time_from: Timestamp de inicio (opcional, por defecto últimos 30 días)
            time_till: Timestamp de fin (opcional, por defecto ahora)
            limit: Límite máximo de eventos a retornar (por defecto 10000)
             
        Returns:
            Lista de eventos con información: eventid, clock, ns, hosts, triggers
        """
        if not self.auth_token:
            raise Exception("No autenticado. Llame a login() primero.")

        # Por defecto, últimos 30 días
        if time_from is None:
            time_from = int((datetime.now().timestamp()) - (30 * 24 * 3600))
        if time_till is None:
            time_till = int(datetime.now().timestamp())

        params = {
            "output": ["eventid", "clock", "ns", "objectid"],
            "selectHosts": ["hostid", "name", "status"],
            "source": 0,      # 0 = eventos de triggers
            "object": 0,      # 0 = triggers
            "value": 1,       # 1 = creación de problema (para contar cada salto de alerta)
            "time_from": time_from,
            "time_till": time_till,
            "limit": limit,
            "sortfield": "clock",
            "sortorder": "DESC"
        }

        events = self._make_request("event.get", params)
        
        # Filtrar eventos de hosts deshabilitados (status=1)
        filtered_events = []
        for event in events:
            hosts = event.get("hosts", [])
            # Verificar que al menos un host esté habilitado (status=0)
            # El campo status puede venir como string "0"/"1" o no venir (default 0=habilitado)
            host_enabled = any(str(h.get("status", "0")) == "0" for h in hosts)
            if host_enabled:
                filtered_events.append(event)
        
        # Obtener triggers con información de status para filtrar triggers deshabilitados
        final_events = []
        if filtered_events:
            triggerids = list(set([e["objectid"] for e in filtered_events]))
            # Consultar trigger.get con status para filtrar triggers deshabilitados
            triggers = self._make_request("trigger.get", {
                "triggerids": triggerids,
                "output": ["triggerid", "description", "priority", "status"]
            })
            # Mapear triggers
            trigger_map = {t["triggerid"]: t for t in triggers}
            # Añadir triggers a los eventos y filtrar triggers deshabilitados (status=1)
            for e in filtered_events:
                trigger = trigger_map.get(e["objectid"])
                if trigger and str(trigger.get("status", "0")) == "0":  # Solo triggers habilitados (0=habilitado, 1=deshabilitado)
                    e["triggers"] = [trigger]
                    final_events.append(e)
        
        return final_events