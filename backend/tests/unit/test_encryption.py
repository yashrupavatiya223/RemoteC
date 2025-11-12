"""
Testes unitários para módulo de criptografia
"""

import pytest
import json
from crypto.encryption import EncryptionUtils

class TestEncryptionBasics:
    """Testes básicos de criptografia/descriptografia"""
    
    def test_encrypt_decrypt_simple_string(self):
        """Deve criptografar e descriptografar string simples"""
        original = "Hello, Argus C2!"
        encrypted = EncryptionUtils.encrypt(original)
        decrypted = EncryptionUtils.decrypt(encrypted)
        
        assert decrypted == original
        assert encrypted != original
        assert len(encrypted) > len(original)
    
    def test_encrypt_decrypt_unicode(self):
        """Deve suportar caracteres unicode"""
        original = "Olá! 你好! مرحبا! 🚀"
        encrypted = EncryptionUtils.encrypt(original)
        decrypted = EncryptionUtils.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_different_output_each_time(self):
        """Deve gerar outputs diferentes para mesma entrada (IV aleatório)"""
        original = "Test message"
        encrypted1 = EncryptionUtils.encrypt(original)
        encrypted2 = EncryptionUtils.encrypt(original)
        
        # IVs diferentes = outputs diferentes
        assert encrypted1 != encrypted2
        
        # Mas ambos descriptografam para original
        assert EncryptionUtils.decrypt(encrypted1) == original
        assert EncryptionUtils.decrypt(encrypted2) == original
    
    def test_encrypt_empty_string(self):
        """Deve lidar com string vazia"""
        original = ""
        encrypted = EncryptionUtils.encrypt(original)
        decrypted = EncryptionUtils.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_long_string(self):
        """Deve lidar com strings longas"""
        original = "A" * 10000
        encrypted = EncryptionUtils.encrypt(original)
        decrypted = EncryptionUtils.decrypt(encrypted)
        
        assert decrypted == original
        assert len(decrypted) == 10000
    
    def test_decrypt_invalid_data_raises_error(self):
        """Deve lançar erro ao descriptografar dados inválidos"""
        with pytest.raises(Exception):
            EncryptionUtils.decrypt("invalid_base64_data")
    
    def test_decrypt_corrupted_data_raises_error(self):
        """Deve lançar erro se dados criptografados forem corrompidos"""
        original = "Test message"
        encrypted = EncryptionUtils.encrypt(original)
        
        # Corromper dados
        corrupted = encrypted[:-5] + "XXXXX"
        
        with pytest.raises(Exception):
            EncryptionUtils.decrypt(corrupted)


class TestEncryptionWithCustomKey:
    """Testes com chaves customizadas"""
    
    def test_encrypt_decrypt_with_custom_key(self):
        """Deve funcionar com chave customizada"""
        key = EncryptionUtils.string_to_key("my_custom_key_123")
        original = "Secret message"
        
        encrypted = EncryptionUtils.encrypt(original, key)
        decrypted = EncryptionUtils.decrypt(encrypted, key)
        
        assert decrypted == original
    
    def test_wrong_key_fails_decryption(self):
        """Deve falhar ao descriptografar com chave errada"""
        key1 = EncryptionUtils.string_to_key("key_1")
        key2 = EncryptionUtils.string_to_key("key_2")
        
        original = "Secret message"
        encrypted = EncryptionUtils.encrypt(original, key1)
        
        # Tentar descriptografar com chave errada
        with pytest.raises(Exception):
            EncryptionUtils.decrypt(encrypted, key2)
    
    def test_string_to_key_deterministic(self):
        """Deve gerar sempre a mesma chave para mesma string"""
        key1 = EncryptionUtils.string_to_key("test_key")
        key2 = EncryptionUtils.string_to_key("test_key")
        
        assert key1 == key2
        assert len(key1) == 32  # 256 bits
    
    def test_string_to_key_different_for_different_strings(self):
        """Deve gerar chaves diferentes para strings diferentes"""
        key1 = EncryptionUtils.string_to_key("key1")
        key2 = EncryptionUtils.string_to_key("key2")
        
        assert key1 != key2


class TestHashAndIntegrity:
    """Testes de hash SHA-256 e verificação de integridade"""
    
    def test_sha256_hash(self):
        """Deve calcular hash SHA-256 corretamente"""
        data = "Test data"
        hash_value = EncryptionUtils.sha256(data)
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 = 64 caracteres hex
    
    def test_sha256_deterministic(self):
        """Deve gerar sempre o mesmo hash para mesmos dados"""
        data = "Test data"
        hash1 = EncryptionUtils.sha256(data)
        hash2 = EncryptionUtils.sha256(data)
        
        assert hash1 == hash2
    
    def test_sha256_different_for_different_data(self):
        """Deve gerar hashes diferentes para dados diferentes"""
        hash1 = EncryptionUtils.sha256("data1")
        hash2 = EncryptionUtils.sha256("data2")
        
        assert hash1 != hash2
    
    def test_verify_integrity_success(self):
        """Deve verificar integridade de dados corretos"""
        data = "Test data"
        hash_value = EncryptionUtils.sha256(data)
        
        assert EncryptionUtils.verify_integrity(data, hash_value) is True
    
    def test_verify_integrity_failure(self):
        """Deve detectar dados corrompidos"""
        data = "Test data"
        hash_value = EncryptionUtils.sha256(data)
        
        corrupted_data = "Test datx"  # Um caractere diferente
        
        assert EncryptionUtils.verify_integrity(corrupted_data, hash_value) is False


class TestJSONEncryption:
    """Testes de criptografia de objetos JSON"""
    
    def test_encrypt_decrypt_json_dict(self):
        """Deve criptografar e descriptografar dicionário"""
        original_dict = {
            'device_id': 'test_001',
            'command': 'get_location',
            'timestamp': 1234567890,
            'nested': {
                'key': 'value'
            }
        }
        
        encrypted = EncryptionUtils.encrypt_json(original_dict)
        decrypted = EncryptionUtils.decrypt_json(encrypted)
        
        assert decrypted == original_dict
    
    def test_encrypt_json_with_unicode(self):
        """Deve suportar unicode em JSON"""
        original_dict = {
            'message': 'Olá mundo! 🚀',
            'user': 'José'
        }
        
        encrypted = EncryptionUtils.encrypt_json(original_dict)
        decrypted = EncryptionUtils.decrypt_json(encrypted)
        
        assert decrypted == original_dict
    
    def test_encrypt_json_with_custom_key(self):
        """Deve funcionar com chave customizada em JSON"""
        key = EncryptionUtils.string_to_key("json_key")
        original_dict = {'test': 'data'}
        
        encrypted = EncryptionUtils.encrypt_json(original_dict, key)
        decrypted = EncryptionUtils.decrypt_json(encrypted, key)
        
        assert decrypted == original_dict


class TestKeyGeneration:
    """Testes de geração de chaves"""
    
    def test_generate_key_correct_size(self):
        """Deve gerar chave do tamanho correto"""
        key = EncryptionUtils.generate_key()
        
        assert len(key) == 32  # 256 bits
    
    def test_generate_key_random(self):
        """Deve gerar chaves aleatórias diferentes"""
        key1 = EncryptionUtils.generate_key()
        key2 = EncryptionUtils.generate_key()
        
        assert key1 != key2
    
    def test_key_to_base64_conversion(self):
        """Deve converter chave para base64 e vice-versa"""
        original_key = EncryptionUtils.generate_key()
        
        base64_key = EncryptionUtils.key_to_base64(original_key)
        restored_key = EncryptionUtils.base64_to_key(base64_key)
        
        assert original_key == restored_key


class TestEdgeCases:
    """Testes de casos extremos"""
    
    def test_encrypt_special_characters(self):
        """Deve lidar com caracteres especiais"""
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        encrypted = EncryptionUtils.encrypt(special_chars)
        decrypted = EncryptionUtils.decrypt(encrypted)
        
        assert decrypted == special_chars
    
    def test_encrypt_newlines_and_tabs(self):
        """Deve preservar newlines e tabs"""
        original = "Line 1\nLine 2\tTabbed"
        encrypted = EncryptionUtils.encrypt(original)
        decrypted = EncryptionUtils.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_json_with_null_values(self):
        """Deve lidar com valores null em JSON"""
        original_dict = {
            'key1': 'value1',
            'key2': None,
            'key3': []
        }
        
        encrypted = EncryptionUtils.encrypt_json(original_dict)
        decrypted = EncryptionUtils.decrypt_json(encrypted)
        
        assert decrypted == original_dict

