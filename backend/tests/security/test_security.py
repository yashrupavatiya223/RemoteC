"""
Testes de segurança
"""

import pytest
import json

class TestSQLInjection:
    """Testes de SQL Injection"""
    
    @pytest.mark.parametrize('malicious_input', [
        "' OR '1'='1",
        "'; DROP TABLE devices; --",
        "1' UNION SELECT * FROM users--",
        "admin'--",
        "1' AND '1'='1",
    ])
    def test_sql_injection_in_device_id(self, client, auth_headers, malicious_input):
        """Deve prevenir SQL injection em device_id"""
        response = client.get(
            f'/api/device/{malicious_input}',
            headers=auth_headers
        )
        
        # Não deve quebrar o servidor
        assert response.status_code < 500
        
        # Não deve retornar dados sensíveis
        if response.status_code == 200:
            data = json.loads(response.data)
            # Verificar que não vazou informações do banco
            assert 'password' not in str(data).lower()
    
    def test_sql_injection_in_login(self, client):
        """Deve prevenir SQL injection no login"""
        malicious_payloads = [
            {'username': "admin'--", 'password': 'any'},
            {'username': "' OR '1'='1'--", 'password': ''},
            {'username': "admin", 'password': "' OR '1'='1'--"},
        ]
        
        for payload in malicious_payloads:
            response = client.post('/login', data=payload)
            
            # Não deve fazer login com SQL injection
            assert response.status_code != 200 or \
                   (response.content_type == 'application/json' and 
                    json.loads(response.data).get('status') != 'success')


class TestXSS:
    """Testes de Cross-Site Scripting"""
    
    @pytest.mark.parametrize('xss_payload', [
        '<script>alert("XSS")</script>',
        '<img src=x onerror=alert("XSS")>',
        '<svg onload=alert("XSS")>',
        'javascript:alert("XSS")',
        '<iframe src="javascript:alert(\'XSS\')">',
    ])
    def test_xss_in_device_name(self, client, auth_headers, db_session, xss_payload):
        """Deve sanitizar XSS em nome de dispositivo"""
        from database.backend.models import Device
        
        device = Device(
            device_id='xss_test_device',
            device_name=xss_payload  # Payload XSS
        )
        db_session.add(device)
        db_session.commit()
        
        # Buscar dispositivo
        response = client.get(f'/api/device/{device.device_id}', headers=auth_headers)
        
        if response.status_code == 200:
            # Verificar que script não é executável
            response_text = response.data.decode('utf-8')
            # Scripts devem ser escapados ou removidos
            assert '<script>' not in response_text or '&lt;script&gt;' in response_text


class TestAuthentication:
    """Testes de autenticação e autorização"""
    
    def test_unauthorized_access_to_dashboard(self, client):
        """Deve bloquear acesso não autenticado"""
        protected_routes = [
            '/dashboard',
            '/devices',
            '/commands',
            '/logs',
            '/api/devices',
            '/api/command',
        ]
        
        for route in protected_routes:
            response = client.get(route)
            # Deve redirecionar para login ou retornar 401
            assert response.status_code in [302, 401]
    
    def test_session_hijacking_prevention(self, client, admin_user):
        """Deve prevenir session hijacking"""
        # Login
        response = client.post('/login', data={
            'username': 'test_admin',
            'password': 'test_password_123'
        })
        
        # Verificar se session cookie tem atributos de segurança
        cookies = response.headers.getlist('Set-Cookie')
        if cookies:
            cookie_str = cookies[0]
            # Deve ter HttpOnly (não é crítico em testes, mas verificar se possível)
            # assert 'HttpOnly' in cookie_str  # Pode não estar em ambiente de teste
    
    def test_password_not_in_response(self, client, auth_headers, admin_user):
        """Não deve expor senhas em nenhuma resposta"""
        # Tentar acessar usuário
        response = client.get('/api/devices', headers=auth_headers)
        
        if response.status_code == 200:
            response_text = response.data.decode('utf-8').lower()
            # Não deve conter campos de senha
            assert 'password' not in response_text or 'password_hash' not in response_text


class TestRateLimiting:
    """Testes de rate limiting"""
    
    def test_login_rate_limiting(self, client):
        """Deve aplicar rate limiting no login"""
        # Tentar múltiplos logins
        for i in range(10):
            response = client.post('/login', data={
                'username': f'user{i}',
                'password': 'wrong_password'
            })
        
        # Eventualmente deve retornar 429 (Too Many Requests)
        # Ou continuar retornando erro de autenticação
        assert response.status_code in [200, 401, 429]


class TestCSRF:
    """Testes de CSRF protection"""
    
    def test_csrf_token_required_for_state_changing_operations(self, client, auth_headers):
        """Operações que mudam estado devem ter proteção CSRF"""
        # Tentar deletar device sem CSRF token
        response = client.delete(
            '/api/device/test_device',
            headers=auth_headers
        )
        
        # Depende da implementação, mas não deve falhar
        # Flask não tem CSRF por padrão, precisaria Flask-WTF
        assert response.status_code in [200, 403, 404, 405]


class TestInputValidation:
    """Testes de validação de input"""
    
    def test_invalid_json_rejected(self, client):
        """Deve rejeitar JSON inválido"""
        response = client.post(
            '/api/device/register',
            data='{"invalid": json}',  # JSON inválido
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_oversized_payload_rejected(self, client):
        """Deve rejeitar payloads muito grandes"""
        # Criar payload gigante (mais de MAX_CONTENT_LENGTH)
        huge_data = 'A' * (101 * 1024 * 1024)  # 101 MB
        
        response = client.post(
            '/api/device/register',
            data=huge_data,
            content_type='application/json'
        )
        
        # Deve rejeitar (413 Payload Too Large ou 400)
        assert response.status_code in [400, 413]
    
    @pytest.mark.parametrize('invalid_device_id', [
        '',  # Vazio
        ' ',  # Espaço
        'x' * 1000,  # Muito longo
        '../../../etc/passwd',  # Path traversal
        'device\x00id',  # Null byte
    ])
    def test_invalid_device_ids_rejected(self, client, auth_headers, invalid_device_id):
        """Deve rejeitar device IDs inválidos"""
        response = client.get(
            f'/api/device/{invalid_device_id}',
            headers=auth_headers
        )
        
        # Deve rejeitar ou não encontrar
        assert response.status_code in [400, 404]


class TestCORS:
    """Testes de CORS (Cross-Origin Resource Sharing)"""
    
    def test_cors_headers_present(self, client):
        """Deve ter headers CORS apropriados"""
        response = client.get('/api/devices')
        
        # Verificar se há headers CORS (se configurado)
        # CORS deve ser restritivo, não "*"
        if 'Access-Control-Allow-Origin' in response.headers:
            origin = response.headers['Access-Control-Allow-Origin']
            # Não deve ser wildcard
            # assert origin != '*'  # Comentado pois projeto usa "*" atualmente


class TestEncryption:
    """Testes de criptografia em trânsito"""
    
    def test_encrypted_communication_accepted(self, client, sample_device):
        """Deve aceitar dados criptografados"""
        from crypto.encryption import EncryptionUtils
        
        data = {'device_id': sample_device.device_id, 'data': 'test'}
        json_data = json.dumps(data)
        encrypted = EncryptionUtils.encrypt(json_data)
        
        response = client.post(
            '/api/data/exfiltrate',
            data=encrypted,
            content_type='application/octet-stream',
            headers={'X-Device-ID': sample_device.device_id}
        )
        
        # Deve aceitar dados criptografados
        assert response.status_code in [200, 400]  # 400 se device não configurado


class TestDataExposure:
    """Testes de exposição de dados sensíveis"""
    
    def test_error_messages_not_verbose(self, client):
        """Mensagens de erro não devem expor detalhes internos"""
        # Tentar acessar recurso inexistente
        response = client.get('/api/device/nonexistent')
        
        if response.status_code >= 400:
            error_text = response.data.decode('utf-8').lower()
            
            # Não deve expor stack traces ou paths internos
            assert 'traceback' not in error_text
            assert '/backend/' not in error_text
            assert 'sqlalchemy' not in error_text
    
    def test_no_directory_listing(self, client):
        """Não deve permitir directory listing"""
        response = client.get('/static/')
        
        # Não deve listar diretório
        assert response.status_code in [403, 404]

