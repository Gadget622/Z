import os
import re
import time
import json
from datetime import datetime
import tkinter as tk
from tkinter import simpledialog, messagebox

# Windows disallowed characters in filenames
INVALID_CHARS = r'[<>:"/\\|?*]'

def validate_filename(filename):
    """
    Validates if a filename is legal according to Windows OS restrictions.
    
    Args:
        filename (str): The filename to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check for empty filename
    if not filename or filename.strip() == '':
        return False, "Filename cannot be empty."
    
    # Check if filename has extension
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    # Check for invalid characters
    if re.search(INVALID_CHARS, filename):
        return False, f"Filename contains invalid characters. Do not use: < > : \" / \\ | ? *"
    
    # Check for reserved names
    reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", 
                     "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", 
                     "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
    
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        return False, f"'{name_without_ext}' is a reserved name and cannot be used."
    
    # Check length
    if len(filename) > 255:
        return False, "Filename is too long. Maximum length is 255 characters."
    
    return True, filename

def prompt_for_filename(parent, title="Enter Filename", message="Please enter a name for the CSV file:"):
    """
    Prompts the user to enter a valid filename.
    
    Args:
        parent: The parent window
        title (str): Dialog title
        message (str): Message to display
        
    Returns:
        str or None: Valid filename with .csv extension or None if canceled
    """
    while True:
        filename = simpledialog.askstring(title, message, parent=parent)
        
        if filename is None:  # User canceled
            return None
        
        valid, result = validate_filename(filename)
        if valid:
            return result
        else:
            messagebox.showerror("Invalid Filename", result, parent=parent)

def update_config_file(key, value, section="files"):
    """
    Updates the config.json file with a new value.
    
    Args:
        key (str): The key to update
        value (str): The new value
        section (str): The section in the config file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config.json")
        
        # Read existing config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update value
        config[section][key] = value
        
        # Write back to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        return True
    except Exception as e:
        print(f"Error updating config file: {e}")
        return False

def setup_temp_directory():
    """
    Creates a temp directory if it doesn't exist.
    
    Returns:
        str: Path to the temp directory
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(script_dir, "temp")
    
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    return temp_dir

def generate_temp_filename():
    """
    Generates a unique filename based on current timestamp.
    
    Returns:
        str: Unique filename
    """
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")[:-4]  # Keep only centiseconds
    return f"temp_{timestamp}.csv"

def get_temp_filepath():
    """
    Returns a full path to a new temporary file.
    
    Returns:
        str: Full path to a temporary file
    """
    temp_dir = setup_temp_directory()
    temp_filename = generate_temp_filename()
    return os.path.join(temp_dir, temp_filename)