import os
import secrets
from datetime import timedelta

class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    JWT_EXPIRATION_DELTA = timedelta(hours=24)
    
    # API Keys for authentication
    API_KEYS = {
        'flutter_app': os.environ.get('FLUTTER_API_KEY', 'sabda_flutter_2025_secure_key'),
        'mobile_app': os.environ.get('MOBILE_API_KEY', 'sabda_mobile_2025_secure_key')
    }
    
    # Scraping configuration
    SCRAPING_DELAY_MIN = 2
    SCRAPING_DELAY_MAX = 5
    SCRAPING_TIMEOUT = 15

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    JWT_EXPIRATION_DELTA = timedelta(minutes=5)  # Shorter for testing

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
