"""
Military Module - Funcionalidades Militares Avançadas
Sistema Argus - Nível Militar
"""

from .military_manager import MilitaryManager
from .military_api import military_bp, register_military_routes

__all__ = ['MilitaryManager', 'military_bp', 'register_military_routes']

