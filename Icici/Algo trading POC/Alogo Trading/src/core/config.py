"""
Configuration management for the trading platform.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """
    Centralized configuration management for the trading platform.
    """
    
    _instance = None
    _config_data: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def load(cls, config_path: Path):
        """Load configuration from a file."""
        try:
            if not config_path.exists():
                logger.warning(f"Config file not found: {config_path}")
                cls._load_defaults()
                return
            
            with open(config_path, 'r') as file:
                if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                    cls._config_data = yaml.safe_load(file)
                elif config_path.suffix.lower() == '.json':
                    cls._config_data = json.load(file)
                else:
                    raise ValueError(f"Unsupported config file format: {config_path.suffix}")
            
            # Override with environment variables
            cls._load_environment_overrides()
            
            logger.info(f"Configuration loaded from: {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            cls._load_defaults()
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split('.')
        value = cls._config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    @classmethod
    def set(cls, key: str, value: Any):
        """Set a configuration value using dot notation."""
        keys = key.split('.')
        config = cls._config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """Get all configuration data."""
        return cls._config_data.copy()
    
    @classmethod
    def _load_defaults(cls):
        """Load default configuration values."""
        cls._config_data = {
            'broker': {
                'name': 'icici_breeze',
                'paper_trading': True,
                'api_key': '',
                'api_secret': '',
                'session_token': ''
            },
            'data': {
                'provider': 'icici_breeze',
                'historical_data_source': 'icici_breeze'
            },
            'risk': {
                'max_position_size': 100000,
                'max_daily_loss': 10000,
                'max_open_positions': 10,
                'position_size_percent': 0.02
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/trading.log',
                'max_file_size': 10485760,  # 10MB
                'backup_count': 5
            },
            'strategies': {
                'default_strategy': 'moving_average',
                'strategy_params': {
                    'moving_average': {
                        'short_window': 20,
                        'long_window': 50,
                        'symbols': ['NIFTY', 'BANKNIFTY']
                    }
                }
            }
        }
        
        logger.info("Default configuration loaded")
    
    @classmethod
    def _load_environment_overrides(cls):
        """Load configuration overrides from environment variables."""
        env_mappings = {
            'ICICI_API_KEY': 'broker.api_key',
            'ICICI_API_SECRET': 'broker.api_secret',
            'ICICI_SESSION_TOKEN': 'broker.session_token',
            'PAPER_TRADING': 'broker.paper_trading',
            'LOG_LEVEL': 'logging.level',
            'MAX_POSITION_SIZE': 'risk.max_position_size',
            'MAX_DAILY_LOSS': 'risk.max_daily_loss'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert boolean strings
                if env_value.lower() in ('true', 'false'):
                    env_value = env_value.lower() == 'true'
                # Convert numeric strings
                elif env_value.isdigit():
                    env_value = int(env_value)
                elif env_value.replace('.', '').isdigit():
                    env_value = float(env_value)
                
                cls.set(config_key, env_value)
                logger.debug(f"Environment override: {config_key} = {env_value}")


# Create a singleton instance
config = Config()