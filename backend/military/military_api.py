"""
Military API Routes - Rotas para funcionalidades militares avançadas
Sistema Argus - Nível Militar
"""

from flask import Blueprint, jsonify, request, session, render_template
from datetime import datetime, timedelta
import logging

from database.backend.models import db, Device, Command
from database.backend.models_military import (
    Operator, Campaign, CommandScript, GeoFence, ThreatIntelligence,
    Analytics, MapTrackingPoint
)
from backend.military.military_manager import MilitaryManager

logger = logging.getLogger(__name__)

# Criar Blueprint
military_bp = Blueprint('military', __name__, url_prefix='/api/military')

# Inicializar manager
military_manager = MilitaryManager()

def login_required(f):
    """Decorator para rotas que requerem autenticação"""
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def operator_required(f):
    """Decorator para rotas que requerem autenticação de operador"""
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-Operator-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        operator = Operator.query.filter_by(api_key=api_key, is_active=True).first()
        if not operator:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Adicionar operador ao request context
        request.operator = operator
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ====================== MULTI-TENANT ROUTES ======================

@military_bp.route('/operators', methods=['GET', 'POST'])
@login_required
def operators():
    """
    GET: Lista todos os operadores
    POST: Cria novo operador
    """
    if request.method == 'POST':
        try:
            data = request.json
            
            operator = military_manager.create_operator(
                name=data['name'],
                code_name=data['code_name'],
                organization=data.get('organization'),
                permission_level=data.get('permission_level', 1),
                max_devices=data.get('max_devices', 50)
            )
            
            return jsonify({
                'status': 'success',
                'operator': operator.to_dict(),
                'api_key': operator.api_key,
                'api_secret': operator.api_secret_plain  # Mostrar apenas na criação
            }), 201
            
        except Exception as e:
            logger.error(f"Erro ao criar operador: {e}")
            return jsonify({'error': str(e)}), 500
    
    else:  # GET
        try:
            operators_list = Operator.query.all()
            return jsonify([op.to_dict() for op in operators_list])
        except Exception as e:
            logger.error(f"Erro ao listar operadores: {e}")
            return jsonify({'error': str(e)}), 500

@military_bp.route('/operators/<int:operator_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def operator_detail(operator_id):
    """
    GET: Detalhes do operador
    PUT: Atualiza operador
    DELETE: Remove operador
    """
    operator = Operator.query.get(operator_id)
    if not operator:
        return jsonify({'error': 'Operator not found'}), 404
    
    if request.method == 'GET':
        return jsonify(operator.to_dict())
    
    elif request.method == 'PUT':
        try:
            data = request.json
            
            if 'name' in data:
                operator.name = data['name']
            if 'organization' in data:
                operator.organization = data['organization']
            if 'permission_level' in data:
                operator.permission_level = data['permission_level']
            if 'max_devices' in data:
                operator.max_devices = data['max_devices']
            if 'is_active' in data:
                operator.is_active = data['is_active']
            
            db.session.commit()
            return jsonify({'status': 'success', 'operator': operator.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar operador: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(operator)
            db.session.commit()
            return jsonify({'status': 'success'})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao deletar operador: {e}")
            return jsonify({'error': str(e)}), 500

@military_bp.route('/campaigns', methods=['GET', 'POST'])
@login_required
def campaigns():
    """
    GET: Lista campanhas
    POST: Cria nova campanha
    """
    if request.method == 'POST':
        try:
            data = request.json
            
            campaign = military_manager.create_campaign(
                operator_id=data['operator_id'],
                name=data['name'],
                code_name=data['code_name'],
                description=data.get('description'),
                priority=data.get('priority', 'normal')
            )
            
            return jsonify({
                'status': 'success',
                'campaign': campaign.to_dict()
            }), 201
            
        except Exception as e:
            logger.error(f"Erro ao criar campanha: {e}")
            return jsonify({'error': str(e)}), 500
    
    else:  # GET
        try:
            operator_id = request.args.get('operator_id', type=int)
            
            query = Campaign.query
            if operator_id:
                query = query.filter_by(operator_id=operator_id)
            
            campaigns_list = query.all()
            return jsonify([c.to_dict() for c in campaigns_list])
            
        except Exception as e:
            logger.error(f"Erro ao listar campanhas: {e}")
            return jsonify({'error': str(e)}), 500

@military_bp.route('/campaigns/<int:campaign_id>/assign_device', methods=['POST'])
@login_required
def assign_device_to_campaign(campaign_id):
    """Atribui dispositivo a campanha"""
    try:
        data = request.json
        device_id = data['device_id']
        role = data.get('role')
        
        device_campaign = military_manager.assign_device_to_campaign(
            device_id=device_id,
            campaign_id=campaign_id,
            role=role
        )
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Erro ao atribuir dispositivo: {e}")
        return jsonify({'error': str(e)}), 500

# ====================== COMMAND SCRIPTING ROUTES ======================

@military_bp.route('/scripts', methods=['GET', 'POST'])
@login_required
def command_scripts():
    """
    GET: Lista scripts de comandos
    POST: Cria novo script
    """
    if request.method == 'POST':
        try:
            data = request.json
            
            script = military_manager.create_command_script(
                name=data['name'],
                script_steps=data['script_steps'],
                campaign_id=data.get('campaign_id'),
                description=data.get('description'),
                repeat_count=data.get('repeat_count', 1),
                repeat_interval=data.get('repeat_interval', 0)
            )
            
            return jsonify({
                'status': 'success',
                'script': script.to_dict()
            }), 201
            
        except Exception as e:
            logger.error(f"Erro ao criar script: {e}")
            return jsonify({'error': str(e)}), 500
    
    else:  # GET
        try:
            campaign_id = request.args.get('campaign_id', type=int)
            
            query = CommandScript.query
            if campaign_id:
                query = query.filter_by(campaign_id=campaign_id)
            
            scripts = query.all()
            return jsonify([s.to_dict() for s in scripts])
            
        except Exception as e:
            logger.error(f"Erro ao listar scripts: {e}")
            return jsonify({'error': str(e)}), 500

@military_bp.route('/scripts/<script_id>/execute', methods=['POST'])
@login_required
def execute_script(script_id):
    """Executa script em dispositivo"""
    try:
        data = request.json
        device_id = data['device_id']
        
        execution = military_manager.execute_script(
            script_id=script_id,
            device_id=device_id
        )
        
        return jsonify({
            'status': 'success',
            'execution': execution.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Erro ao executar script: {e}")
        return jsonify({'error': str(e)}), 500

@military_bp.route('/scripts/executions/<execution_id>', methods=['GET'])
@login_required
def script_execution_status(execution_id):
    """Status de execução de script"""
    try:
        execution = military_manager.get_script_execution_status(execution_id)
        
        if not execution:
            return jsonify({'error': 'Execution not found'}), 404
        
        return jsonify(execution.to_dict())
        
    except Exception as e:
        logger.error(f"Erro ao buscar status de execução: {e}")
        return jsonify({'error': str(e)}), 500

# ====================== GEO-FENCING ROUTES ======================

@military_bp.route('/geofences', methods=['GET', 'POST'])
@login_required
def geofences():
    """
    GET: Lista geo-fences
    POST: Cria nova geo-fence
    """
    if request.method == 'POST':
        try:
            data = request.json
            
            geofence = military_manager.create_geofence(
                name=data['name'],
                center_lat=data['center_latitude'],
                center_lon=data['center_longitude'],
                radius_meters=data['radius_meters'],
                campaign_id=data.get('campaign_id'),
                trigger_on_enter=data.get('trigger_on_enter', True),
                trigger_on_exit=data.get('trigger_on_exit', False),
                action_commands=data.get('action_commands')
            )
            
            return jsonify({
                'status': 'success',
                'geofence': geofence.to_dict()
            }), 201
            
        except Exception as e:
            logger.error(f"Erro ao criar geo-fence: {e}")
            return jsonify({'error': str(e)}), 500
    
    else:  # GET
        try:
            campaign_id = request.args.get('campaign_id', type=int)
            
            query = GeoFence.query
            if campaign_id:
                query = query.filter_by(campaign_id=campaign_id)
            
            geofences_list = query.all()
            return jsonify([g.to_dict() for g in geofences_list])
            
        except Exception as e:
            logger.error(f"Erro ao listar geo-fences: {e}")
            return jsonify({'error': str(e)}), 500

# ====================== THREAT INTELLIGENCE ROUTES ======================

@military_bp.route('/intelligence', methods=['GET'])
@login_required
def threat_intelligence():
    """Lista inteligência coletada"""
    try:
        operator_id = request.args.get('operator_id', type=int)
        intel_type = request.args.get('type')
        actionable_only = request.args.get('actionable', 'false').lower() == 'true'
        
        if actionable_only:
            intelligence = military_manager.get_actionable_intelligence(
                operator_id=operator_id,
                intel_type=intel_type
            )
        else:
            query = ThreatIntelligence.query
            if intel_type:
                query = query.filter_by(intel_type=intel_type)
            intelligence = query.order_by(ThreatIntelligence.detected_at.desc()).limit(100).all()
        
        return jsonify([i.to_dict() for i in intelligence])
        
    except Exception as e:
        logger.error(f"Erro ao buscar intelligence: {e}")
        return jsonify({'error': str(e)}), 500

@military_bp.route('/intelligence/<intelligence_id>/mark_processed', methods=['POST'])
@login_required
def mark_intelligence_processed(intelligence_id):
    """Marca inteligência como processada"""
    try:
        intel = ThreatIntelligence.query.filter_by(intelligence_id=intelligence_id).first()
        
        if not intel:
            return jsonify({'error': 'Intelligence not found'}), 404
        
        intel.is_processed = True
        
        # Adicionar notas se fornecidas
        data = request.json or {}
        if 'notes' in data:
            intel.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao marcar intelligence: {e}")
        return jsonify({'error': str(e)}), 500

# ====================== REAL-TIME MAP ROUTES ======================

@military_bp.route('/map/live', methods=['GET'])
@login_required
def live_map_data():
    """Retorna posições atuais de todos os dispositivos para mapa em tempo real"""
    try:
        operator_id = request.args.get('operator_id', type=int)
        
        positions = military_manager.get_current_device_positions(operator_id=operator_id)
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'device_count': len(positions),
            'positions': positions
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar posições de mapa: {e}")
        return jsonify({'error': str(e)}), 500

@military_bp.route('/map/tracking/<int:device_id>', methods=['POST'])
def update_device_tracking(device_id):
    """
    Endpoint para dispositivos atualizarem posição no mapa
    (Chamado pelo AdaptiveNetworkManager)
    """
    try:
        data = request.json
        
        point = military_manager.update_map_tracking(
            device_id=device_id,
            latitude=data['latitude'],
            longitude=data['longitude'],
            accuracy=data.get('accuracy'),
            battery_level=data.get('battery_level'),
            speed=data.get('speed')
        )
        
        # Verificar geo-fences
        triggers = military_manager.check_geofence_triggers(
            device_id=device_id,
            latitude=data['latitude'],
            longitude=data['longitude']
        )
        
        return jsonify({
            'status': 'success',
            'triggers_fired': len(triggers)
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar tracking: {e}")
        return jsonify({'error': str(e)}), 500

# ====================== ANALYTICS & METRICS ROUTES ======================

@military_bp.route('/analytics/dashboard', methods=['GET'])
@login_required
def analytics_dashboard():
    """Retorna analytics agregados para dashboard"""
    try:
        operator_id = request.args.get('operator_id', type=int)
        
        analytics = military_manager.get_dashboard_analytics(operator_id=operator_id)
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Erro ao gerar analytics: {e}")
        return jsonify({'error': str(e)}), 500

@military_bp.route('/analytics/metrics', methods=['GET'])
@login_required
def metrics_timeseries():
    """Retorna série temporal de métricas para gráficos"""
    try:
        metric_type = request.args.get('type', 'device_count')
        hours = request.args.get('hours', 24, type=int)
        operator_id = request.args.get('operator_id', type=int)
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        metrics = military_manager.get_metrics_timeseries(
            metric_type=metric_type,
            start_time=start_time,
            operator_id=operator_id
        )
        
        return jsonify([m.to_dict() for m in metrics])
        
    except Exception as e:
        logger.error(f"Erro ao buscar métricas: {e}")
        return jsonify({'error': str(e)}), 500

@military_bp.route('/analytics/export/prometheus', methods=['GET'])
def export_prometheus():
    """
    Exporta métricas no formato Prometheus
    Para integração com Grafana
    """
    try:
        # Buscar estatísticas atuais
        total_devices = Device.query.count()
        online_devices = Device.query.filter_by(status='online').count()
        
        total_commands = Command.query.count()
        successful_commands = Command.query.filter_by(status='executed').count()
        
        # Formato Prometheus
        metrics = [
            f"# HELP argus_devices_total Total number of devices",
            f"# TYPE argus_devices_total gauge",
            f"argus_devices_total {total_devices}",
            "",
            f"# HELP argus_devices_online Number of online devices",
            f"# TYPE argus_devices_online gauge",
            f"argus_devices_online {online_devices}",
            "",
            f"# HELP argus_commands_total Total number of commands",
            f"# TYPE argus_commands_total counter",
            f"argus_commands_total {total_commands}",
            "",
            f"# HELP argus_commands_successful Number of successful commands",
            f"# TYPE argus_commands_successful counter",
            f"argus_commands_successful {successful_commands}",
            ""
        ]
        
        return "\n".join(metrics), 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        logger.error(f"Erro ao exportar Prometheus: {e}")
        return str(e), 500

# ====================== TEMPLATE ROUTES ======================

@military_bp.route('/map', methods=['GET'])
@login_required
def map_view():
    """Renderiza página de mapa em tempo real"""
    return render_template('military/map.html')

@military_bp.route('/operators/dashboard', methods=['GET'])
@login_required
def operators_dashboard():
    """Dashboard de operadores"""
    return render_template('military/operators.html')

@military_bp.route('/campaigns/dashboard', methods=['GET'])
@login_required
def campaigns_dashboard():
    """Dashboard de campanhas"""
    return render_template('military/campaigns.html')

@military_bp.route('/intelligence/dashboard', methods=['GET'])
@login_required
def intelligence_dashboard():
    """Dashboard de threat intelligence"""
    return render_template('military/intelligence.html')

def register_military_routes(app):
    """Registra rotas militares na aplicação Flask"""
    app.register_blueprint(military_bp)
    logger.info("Rotas militares registradas com sucesso")

