"""
Multiline Input Module

Handles multiline text input for the Z application as a model component.
"""

import os
import json


class MultilineHandler:
    """
    Handles multiline text input for the Z application.
    
    Features:
    - Command-based multiline mode toggle
    - Configurable number of lines
    - Option to preserve or flatten newlines when saving
    """
    
    def __init__(self, app):
        """
        Initialize the multiline handler.
        
        Args:
            app: The parent Z application
        """
        self.app = app
        
        # Load settings
        self.settings = self.load_settings()
        
        # Initialize multiline mode (off by default)
        self.active = False
        
        # Initialize buffer for multiline content
        self.buffer = []
    
    def load_settings(self):
        """
        Load multiline input settings from config file or use defaults.
        
        Returns:
            dict: Settings dictionary
        """
        default_settings = {
            "lines": 3,  # Visual representation only
            "preserve_newlines": False,
            "buffer_limit": 100  # Prevent excessive buffer growth
        }
        
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        settings_path = os.path.join(script_dir, "multiline_settings.json")
        
        # Try to load settings
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    loaded_settings = json.load(f)
                
                # Update default settings with loaded values
                default_settings.update(loaded_settings)
        except Exception as e:
            self.app.error_handler.log_error(f"Error loading multiline settings: {e}")
            
        return default_settings
    
    def save_settings(self):
        """Save current settings to the config file"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        settings_path = os.path.join(script_dir, "multiline_settings.json")
        
        try:
            with open(settings_path, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            self.app.error_handler.log_error(f"Error saving multiline settings: {e}")
    
    def is_active(self):
        """
        Check if multiline mode is active.
        
        Returns:
            bool: True if multiline mode is active
        """
        return self.active
    
    def toggle_active(self):
        """
        Toggle multiline mode.
        
        Returns:
            bool: New active state
        """
        self.active = not self.active
        
        # Clear buffer when deactivating
        if not self.active:
            self.buffer = []
        
        return self.active
    
    def add_to_buffer(self, text):
        """
        Add a line of text to the buffer.
        
        Args:
            text (str): Line of text to add
        """
        self.buffer.append(text)
        
        # Enforce buffer limit
        if len(self.buffer) > self.settings["buffer_limit"]:
            self.buffer = self.buffer[-self.settings["buffer_limit"]:]
    
    def get_buffer_content(self):
        """
        Get the current content of the buffer.
        
        Returns:
            str: Buffer content as a single string
        """
        if not self.buffer:
            return ""
        
        if self.settings["preserve_newlines"]:
            # Join with newlines
            return "\n".join(self.buffer)
        else:
            # Join with spaces
            return " ".join(self.buffer)
    
    def clear_buffer(self):
        """Clear the buffer."""
        self.buffer = []
    
    def submit_buffer(self):
        """
        Submit the buffer content.
        
        Returns:
            str: Buffer content or None if buffer is empty
        """
        if not self.buffer:
            return None
        
        content = self.get_buffer_content()
        
        # Process newlines based on settings
        if self.settings["preserve_newlines"]:
            # Replace newlines with a special token that can be stored in CSV
            # We'll use \\n as a token for newlines
            content = content.replace("\n", "\\n")
        
        # Record timestamp
        timestamp = self.app.data_manager.get_timestamp()
        
        # Write to CSV
        self.app.data_manager.write_entry(timestamp, content)
        
        # Clear the buffer
        self.clear_buffer()
        
        # Return the content for feedback
        return content
    
    def set_preserve_newlines(self, preserve):
        """
        Set the preserve_newlines setting.
        
        Args:
            preserve (bool): Whether to preserve newlines
        """
        self.settings["preserve_newlines"] = bool(preserve)
        self.save_settings()
    
    def set_lines(self, lines):
        """
        Set the number of lines for display purposes.
        
        Args:
            lines (int): Number of lines to display
        """
        try:
            lines = int(lines)
            if lines < 1:
                lines = 1
            elif lines > 20:
                lines = 20
            
            self.settings["lines"] = lines
            self.save_settings()
            return lines
        except ValueError:
            return self.settings["lines"]
    
    def render_multiline_text(self, text):
        """
        Render text that may contain preserved newlines.
        
        Args:
            text (str): Text that might contain encoded newlines
            
        Returns:
            str: Text with proper newlines for display
        """
        # Replace encoded newlines with actual newlines
        if "\\n" in text:
            return text.replace("\\n", "\n")
        return text
    
    def cmd_multiline(self, args):
        """
        Command to manage multiline input mode.
        
        Args:
            args (str): Command arguments
            
        Returns:
            str: Result message
        """
        # No arguments - toggle multiline mode
        if not args:
            mode = self.toggle_active()
            if mode:
                return "Multiline mode enabled. Enter text line by line. Use /ml submit to save or /ml cancel to discard."
            else:
                return "Multiline mode disabled."
        
        # Split arguments
        parts = args.split(None, 1)
        subcmd = parts[0].lower()
        subcmd_args = parts[1] if len(parts) > 1 else ""
        
        # Submit buffer
        if subcmd == "submit":
            if not self.is_active():
                return "Multiline mode is not active. Use /ml to enable it."
            
            content = self.submit_buffer()
            self.toggle_active()  # Disable multiline mode
            
            if content:
                return f"Submitted multiline content ({len(self.render_multiline_text(content).splitlines())} lines)"
            else:
                return "No content to submit."
        
        # Cancel and clear buffer
        elif subcmd == "cancel":
            if not self.is_active():
                return "Multiline mode is not active."
            
            self.clear_buffer()
            self.toggle_active()  # Disable multiline mode
            return "Multiline input canceled."
        
        # Show current buffer
        elif subcmd == "show":
            if not self.is_active():
                return "Multiline mode is not active. Use /ml to enable it."
            
            content = self.get_buffer_content()
            if content:
                return f"Current buffer:\n{self.render_multiline_text(content)}"
            else:
                return "Buffer is empty."
        
        # Set number of lines
        elif subcmd == "lines":
            try:
                lines = int(subcmd_args)
                new_lines = self.set_lines(lines)
                return f"Multiline lines set to {new_lines}."
            except ValueError:
                return f"Invalid line count. Current setting: {self.settings['lines']} lines."
        
        # Set preserve newlines setting
        elif subcmd == "preserve":
            value = subcmd_args.lower()
            
            if value in ["on", "true", "yes", "1"]:
                self.set_preserve_newlines(True)
                return "Newlines will be preserved in multiline input."
            elif value in ["off", "false", "no", "0"]:
                self.set_preserve_newlines(False)
                return "Newlines will be flattened to spaces in multiline input."
            else:
                current = "on" if self.settings["preserve_newlines"] else "off"
                return f"Invalid value. Use 'on' or 'off'. Current setting: {current}"
        
        # Show status
        elif subcmd == "status":
            mode = "active" if self.is_active() else "inactive"
            preserve = "preserved" if self.settings["preserve_newlines"] else "flattened to spaces"
            buffer_size = len(self.buffer)
            
            return f"Multiline mode is {mode}\n" + \
                   f"Lines: {self.settings['lines']}\n" + \
                   f"Newlines are {preserve}\n" + \
                   f"Buffer contains {buffer_size} lines"
        
        # Unknown subcommand
        else:
            return "Unknown multiline command. Available commands: submit, cancel, show, lines, preserve, status"