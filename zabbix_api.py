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
                "value": 1
            },
            "only_true": True,
            "sortfield": "lastchange",
            "sortorder": "DESC"
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
        params = {
            "output": ["eventid", "name", "severity", "clock", "ns"],
            "selectHosts": ["hostid", "name"],
            "selectTags": ["tag", "value"],
            "value": 1,  # Solo problemas activos (1=problem, 0=ok)
            "sortfield": "clock",
            "sortorder": "DESC"
        }

        problems = self._make_request("event.get", params)
        
        # Enriquecer los problemas con información calculada
        enriched_problems = []
        now = datetime.now().timestamp()
        
        for problem in problems:
            # Obtener nombre del host (puede haber múltiples, tomar el primero)
            host_name = "Desconocido"
            if problem.get("hosts") and len(problem["hosts"]) > 0:
                host_name = problem["hosts"][0].get("name", "Desconocido")
            
            # Convertir severidad numérica a texto
            severity_num = int(problem.get("severity", 0))
            severity_text = self.SEVERITY_MAP.get(severity_num, f"Desconocido ({severity_num})")
            
            # Calcular duración
            clock = int(problem.get("clock", 0))
            duration_seconds = int(now - clock)
            duration_str = self._format_duration(duration_seconds)
            
            # Formatear tiempo de inicio
            time_str = datetime.fromtimestamp(clock).strftime('%Y-%m-%d %H:%M:%S')
            
            enriched_problems.append({
                "eventid": problem.get("eventid"),
                "time": time_str,
                "host": host_name,
                "severity": severity_text,
                "severity_num": severity_num,
                "description": problem.get("name", "Sin descripción"),
                "duration": duration_str,
                "duration_seconds": duration_seconds,
                "clock": clock
            })
        
        return enriched_problems

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
        params = {
            "output": ["eventid", "name", "severity", "clock", "ns"],
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
                    "selectHosts": ["hostid", "name"]
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

        return problems

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
                    "selectHosts": ["hostid", "name"]
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

        return problems

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
            "selectHosts": ["hostid", "name"],
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
        
        # Obtener triggers
        if events:
            triggerids = list(set([e["objectid"] for e in events]))
            # Consultar trigger.get
            triggers = self._make_request("trigger.get", {"triggerids": triggerids, "output": ["triggerid", "description", "priority"]})
            # Mapear triggers
            trigger_map = {t["triggerid"]: t for t in triggers}
            # Añadir triggers a los eventos
            for e in events:
                e["triggers"] = [trigger_map.get(e["objectid"])]
        
        return events