"""
Phishing Module - Sistema completo de phishing
Sistema Argus - Nível Militar
"""

from .phishing_manager import PhishingManager
from .phishing_api import phishing_bp, register_phishing_routes

__all__ = ['PhishingManager', 'phishing_bp', 'register_phishing_routes']

