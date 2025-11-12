"""
Configuração pytest para testes do Argus C2
"""

import pytest
import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from config import TestingConfig
from database.backend.database_manager import DatabaseManager, db
from database.backend.models import User, Device, Command

@pytest.fixture(scope='session')
def app():
    """Cria app Flask para testes"""
    app = Flask(__name__)
    app.config.from_object(TestingConfig)
    
    # Inicializar database manager
    db_manager = DatabaseManager(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """Cliente de teste Flask"""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    """Sessão de banco limpa para cada teste"""
    with app.app_context():
        # Limpar todas as tabelas
        Device.query.delete()
        Command.query.delete()
        User.query.delete()
        db.session.commit()
        
        yield db.session
        
        # Limpar após teste
        db.session.rollback()

@pytest.fixture
def admin_user(db_session):
    """Cria usuário admin para testes"""
    user = User(
        username='test_admin',
        email='admin@test.local',
        role='admin'
    )
    user.set_password('test_password_123')
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_device(db_session):
    """Cria dispositivo de teste"""
    device = Device(
        device_id='test_device_001',
        device_name='Test Device',
        model='Test Model',
        manufacturer='Test Manufacturer',
        android_version='13',
        api_level=33,
        status='online',
        battery_level=80.0,
        is_charging=False
    )
    db_session.add(device)
    db_session.commit()
    return device

@pytest.fixture
def auth_headers(admin_user, client):
    """Headers de autenticação para testes"""
    # Login
    response = client.post('/login', data={
        'username': 'test_admin',
        'password': 'test_password_123'
    })
    
    # Retornar headers com session cookie
    return {'Cookie': response.headers.get('Set-Cookie')}

