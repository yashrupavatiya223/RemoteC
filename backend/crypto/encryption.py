"""
Utilitários de criptografia AES-256 para servidor Python
Compatível com EncryptionUtils.java do Android
"""

import base64
import hashlib
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os

class EncryptionUtils:
    """Classe para criptografia/descriptografia AES-256"""
    
    ALGORITHM = 'AES'
    KEY_SIZE = 32  # 256 bits
    IV_SIZE = 16   # 128 bits
    BLOCK_SIZE = 128  # AES block size in bits
    
    # Chave padrão (deve ser alterada em produção)
    DEFAULT_KEY = "argus_encryption_key_2024_change_me"
    
    @staticmethod
    def string_to_key(key_string):
        """Converte string para chave AES usando SHA-256"""
        return hashlib.sha256(key_string.encode('utf-8')).digest()
    
    @staticmethod
    def generate_iv():
        """Gera IV (Initialization Vector) aleatório"""
        return os.urandom(EncryptionUtils.IV_SIZE)
    
    @staticmethod
    def encrypt(data, secret_key=None):
        """
        Criptografa dados usando AES-256-CBC
        
        Args:
            data (str): Dados para criptografar
            secret_key (bytes): Chave secreta (opcional, usa DEFAULT_KEY se None)
            
        Returns:
            str: String Base64 com IV + dados criptografados
        """
        if secret_key is None:
            secret_key = EncryptionUtils.string_to_key(EncryptionUtils.DEFAULT_KEY)
        
        # Gerar IV
        iv = EncryptionUtils.generate_iv()
        
        # Criar cifra
        cipher = Cipher(
            algorithms.AES(secret_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Adicionar padding PKCS7
        padder = padding.PKCS7(EncryptionUtils.BLOCK_SIZE).padder()
        padded_data = padder.update(data.encode('utf-8')) + padder.finalize()
        
        # Criptografar
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combinar IV + dados criptografados
        combined = iv + encrypted
        
        # Retornar como Base64
        return base64.b64encode(combined).decode('utf-8')
    
    @staticmethod
    def decrypt(encrypted_data, secret_key=None):
        """
        Descriptografa dados usando AES-256-CBC
        
        Args:
            encrypted_data (str): String Base64 com IV + dados criptografados
            secret_key (bytes): Chave secreta (opcional, usa DEFAULT_KEY se None)
            
        Returns:
            str: Dados descriptografados
        """
        if secret_key is None:
            secret_key = EncryptionUtils.string_to_key(EncryptionUtils.DEFAULT_KEY)
        
        # Decodificar Base64
        combined = base64.b64decode(encrypted_data)
        
        # Separar IV e dados criptografados
        iv = combined[:EncryptionUtils.IV_SIZE]
        encrypted = combined[EncryptionUtils.IV_SIZE:]
        
        # Criar cifra
        cipher = Cipher(
            algorithms.AES(secret_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Descriptografar
        padded_data = decryptor.update(encrypted) + decryptor.finalize()
        
        # Remover padding PKCS7
        unpadder = padding.PKCS7(EncryptionUtils.BLOCK_SIZE).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data.decode('utf-8')
    
    @staticmethod
    def sha256(data):
        """Calcula hash SHA-256"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def verify_integrity(data, hash_value):
        """Verifica integridade dos dados"""
        calculated = EncryptionUtils.sha256(data)
        return calculated == hash_value
    
    @staticmethod
    def encrypt_json(data_dict, secret_key=None):
        """
        Criptografa objeto Python para JSON
        
        Args:
            data_dict (dict): Dicionário para criptografar
            secret_key (bytes): Chave secreta (opcional)
            
        Returns:
            str: JSON criptografado em Base64
        """
        json_str = json.dumps(data_dict, ensure_ascii=False)
        return EncryptionUtils.encrypt(json_str, secret_key)
    
    @staticmethod
    def decrypt_json(encrypted_json, secret_key=None):
        """
        Descriptografa JSON criptografado
        
        Args:
            encrypted_json (str): JSON criptografado em Base64
            secret_key (bytes): Chave secreta (opcional)
            
        Returns:
            dict: Dicionário descriptografado
        """
        decrypted_str = EncryptionUtils.decrypt(encrypted_json, secret_key)
        return json.loads(decrypted_str)
    
    @staticmethod
    def generate_key():
        """Gera chave AES-256 aleatória"""
        return os.urandom(EncryptionUtils.KEY_SIZE)
    
    @staticmethod
    def key_to_base64(key):
        """Converte chave para Base64"""
        return base64.b64encode(key).decode('utf-8')
    
    @staticmethod
    def base64_to_key(key_b64):
        """Converte Base64 para chave"""
        return base64.b64decode(key_b64)


# Funções de conveniência
def encrypt_message(message, key=None):
    """Criptografa mensagem simples"""
    return EncryptionUtils.encrypt(message, key)

def decrypt_message(encrypted_message, key=None):
    """Descriptografa mensagem simples"""
    return EncryptionUtils.decrypt(encrypted_message, key)

def encrypt_payload(payload_dict, key=None):
    """Criptografa payload dict para transmissão"""
    return EncryptionUtils.encrypt_json(payload_dict, key)

def decrypt_payload(encrypted_payload, key=None):
    """Descriptografa payload recebido"""
    return EncryptionUtils.decrypt_json(encrypted_payload, key)


# Teste de compatibilidade
if __name__ == '__main__':
    print("=== Teste de Criptografia ===")
    
    # Teste básico
    original = "Hello, Argus C2!"
    print(f"Original: {original}")
    
    encrypted = EncryptionUtils.encrypt(original)
    print(f"Encrypted: {encrypted}")
    
    decrypted = EncryptionUtils.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")
    
    print(f"Match: {original == decrypted}")
    
    # Teste JSON
    print("\n=== Teste JSON ===")
    data = {
        'device_id': 'test_device_001',
        'command': 'get_location',
        'timestamp': '2024-10-23T12:00:00'
    }
    print(f"Original: {data}")
    
    encrypted_json = EncryptionUtils.encrypt_json(data)
    print(f"Encrypted JSON: {encrypted_json}")
    
    decrypted_json = EncryptionUtils.decrypt_json(encrypted_json)
    print(f"Decrypted JSON: {decrypted_json}")
    
    print(f"Match: {data == decrypted_json}")
    
    # Teste Hash
    print("\n=== Teste Hash ===")
    hash_value = EncryptionUtils.sha256(original)
    print(f"SHA-256: {hash_value}")
    print(f"Integrity OK: {EncryptionUtils.verify_integrity(original, hash_value)}")




