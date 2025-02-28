"""
Config Manager Module

Handles loading, saving, and validating configuration for the Z application.
"""

import json
import os
import tkinter as tk
from tkinter import messagebox, simpledialog


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


def load_config(app=None):
    """
    Load configuration from config.json.
    If the file doesn't exist, create it with default values.
    
    Args:
        app: The Z application instance (optional)
        
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
            
            # Extract and return flat config
            return _extract_config(default_config)
        except Exception as e:
            raise ConfigError(f"Failed to create default configuration file: {e}")
    
    # Read existing config file
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        
        # Extract and return flat config
        return _extract_config(config)
    except Exception as e:
        raise ConfigError(f"Failed to load configuration file: {e}")


def _extract_config(config):
    """
    Extract configuration values into a flat dictionary.
    
    Args:
        config: The nested configuration dictionary
        
    Returns:
        dict: Flat configuration dictionary
    """
    flat_config = {}
    
    # Extract file paths
    for key, value in config.get("files", {}).items():
        flat_config[key] = value
    
    # Extract settings
    for key, value in config.get("settings", {}).items():
        flat_config[key] = value
    
    # Extract command prefixes
    for key, value in config.get("commands", {}).items():
        flat_config[key] = value
    
    return flat_config


def save_config(config):
    """
    Save configuration to config.json.
    
    Args:
        config: The flat configuration dictionary
        
    Returns:
        bool: True if successful, False otherwise
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    
    # Convert flat config back to nested structure
    nested_config = {
        "files": {},
        "settings": {},
        "commands": {}
    }
    
    # File keys
    file_keys = ["DATA_CSV", "TEMP_CSV", "TEMP_TXT"]
    for key in file_keys:
        if key in config:
            nested_config["files"][key] = config[key]
    
    # Settings keys
    settings_keys = ["TIME_INTERVAL", "PERIODIC_ENTRIES_ENABLED", "PERIODIC_ENTRIES_INTERVAL"]
    for key in settings_keys:
        if key in config:
            nested_config["settings"][key] = config[key]
    
    # Command keys
    command_keys = ["SLASH_PREFIX", "SLASH_PREFIX_ALT", "SLASH_CSV_PREFIX", 
                    "TOKEN_PREFIX", "TOKEN_PREFIX_ALT", "TOKEN_CSV_PREFIX"]
    for key in command_keys:
        if key in config:
            nested_config["commands"][key] = config[key]
    
    try:
        with open(config_path, 'w') as config_file:
            json.dump(nested_config, config_file, indent=4)
        return True
    except Exception:
        return False


def handle_config_error(app, error_message):
    """
    Handle configuration errors by prompting the user for information.
    
    Args:
        app: The Z application instance
        error_message: The error message
        
    Returns:
        dict: Updated configuration dictionary or None if error couldn't be resolved
    """
    # Import file_helper here to avoid circular imports
    try:
        import file_helper
    except ImportError:
        messagebox.showerror(
            "Module Error",
            "Failed to import file_helper module.\n\nPlease ensure file_helper.py exists in the application directory."
        )
        return None
    
    if "DATA_CSV" in error_message:
        # Prompt user for a data file name
        filename = file_helper.prompt_for_filename(
            app.root,
            "Data File Configuration",
            "Please enter a name for your data file:"
        )
        
        if filename is None:  # User canceled
            messagebox.showerror(
                "Configuration Required",
                "A data file name is required for the application to function."
            )
            return None
        
        # Update configuration
        app.config["DATA_CSV"] = filename
        
        # Update config file
        success = file_helper.update_config_file("DATA_CSV", filename)
        if success:
            messagebox.showinfo(
                "Configuration Updated",
                f"Data file has been set to: {filename}"
            )
        else:
            messagebox.showwarning(
                "Configuration Warning",
                f"Data file will be set to {filename} for this session, but the configuration file could not be updated."
            )
        
        return app.config
    
    # Handle other config errors as needed
    return None


def get_value(key, section="files", default=None):
    """
    Get a configuration value.
    
    Args:
        key (str): Configuration key
        section (str): Configuration section ("files", "settings", or "commands")
        default: Default value if key doesn't exist
        
    Returns:
        Value from configuration or default
        
    Raises:
        ConfigError: If the value doesn't exist and no default is provided
    """
    try:
        config = load_config()
        
        # For backwards compatibility, handle both flat and nested configs
        if key in config:
            return config[key]
        
        # If key not found and default provided, return default
        if default is not None:
            return default
        
        raise ConfigError(f"Missing configuration: {section}.{key}")
    except Exception as e:
        if default is not None:
            return default
        raise ConfigError(f"Error getting configuration value: {e}")