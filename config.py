import json
import os
import sys
import tkinter as tk
from tkinter import messagebox

class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass

def load_config():
    """
    Load configuration from config.json.
    If the file doesn't exist, create it with default values.
    
    Returns:
        dict: Configuration dictionary
        
    Raises:
        ConfigError: If the config file cannot be loaded or created
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    
    # Default configuration
    default_config = {
        "files": {
            "DATA_CSV": "Z.csv",
            "TEMP_CSV": "temp.csv",
            "TEMP_TXT": "Z temp.txt"
        },
        "settings": {
            "TIME_INTERVAL": 10,
            "PERIODIC_ENTRIES_ENABLED": False,
            "PERIODIC_ENTRIES_INTERVAL": 5
        },
        "commands": {
            "SLASH_PREFIX": "/",
            "SLASH_PREFIX_ALT": "//",
            "SLASH_CSV_PREFIX": "//",
            "TOKEN_PREFIX": "$",
            "TOKEN_PREFIX_ALT": "$",
            "TOKEN_CSV_PREFIX": "$"
        }
    }
    
    # Check if config file exists
    if not os.path.exists(config_path):
        try:
            # Create default config file
            with open(config_path, 'w') as config_file:
                json.dump(default_config, config_file, indent=4)
            return default_config
        except Exception as e:
            raise ConfigError(f"Failed to create default configuration file: {e}")
    
    # Read existing config file
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        return config
    except Exception as e:
        raise ConfigError(f"Failed to load configuration file: {e}")

try:
    # Load configuration
    CONFIG = load_config()

    # Extract file paths
    DATA_CSV = CONFIG["files"]["DATA_CSV"]
    TEMP_CSV = CONFIG["files"]["TEMP_CSV"]
    TEMP_TXT = CONFIG["files"]["TEMP_TXT"]

    # Extract settings
    TIME_INTERVAL = CONFIG["settings"]["TIME_INTERVAL"]
    PERIODIC_ENTRIES_ENABLED = CONFIG["settings"]["PERIODIC_ENTRIES_ENABLED"]
    PERIODIC_ENTRIES_INTERVAL = CONFIG["settings"]["PERIODIC_ENTRIES_INTERVAL"]

    # Extract command prefixes
    SLASH_PREFIX = CONFIG["commands"]["SLASH_PREFIX"]
    SLASH_PREFIX_ALT = CONFIG["commands"]["SLASH_PREFIX_ALT"]
    SLASH_CSV_PREFIX = CONFIG["commands"]["SLASH_CSV_PREFIX"]
    TOKEN_PREFIX = CONFIG["commands"]["TOKEN_PREFIX"]
    TOKEN_PREFIX_ALT = CONFIG["commands"]["TOKEN_PREFIX_ALT"]
    TOKEN_CSV_PREFIX = CONFIG["commands"]["TOKEN_CSV_PREFIX"]
except (KeyError, ConfigError) as e:
    # Don't handle here - let the application handle it
    raise

# For compatibility with older code
def get_value(key, section="files", default=None):
    """
    Get a configuration value.
    
    Args:
        key (str): Configuration key
        section (str): Configuration section ("files" or "settings")
        default: Default value if key doesn't exist
        
    Returns:
        Value from configuration or default
        
    Raises:
        ConfigError: If the value doesn't exist and no default is provided
    """
    try:
        return CONFIG[section][key]
    except (KeyError, TypeError):
        if default is not None:
            return default
        raise ConfigError(f"Missing configuration: {section}.{key}")