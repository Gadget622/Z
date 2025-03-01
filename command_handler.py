"""
Command Handler Module

Handles command processing for the Z application.
This module separates command handling logic from the main UI code.
"""

import os
import sys
import subprocess
import pandas as pd
from datetime import datetime


class CommandHandler:
    """
    Handles parsing and execution of commands for the Z application.
    """
    
    def __init__(self, app):
        """
        Initialize the command handler.
        
        Args:
            app: The parent application that provides context (for feedback, etc.)
        """
        self.app = app
        
        # Dictionary of available slash commands
        self.slash_commands = {
            'help': self.cmd_help,
            'echo': self.cmd_echo,
            'list': self.cmd_list,
            'clear': self.cmd_clear,
            'os': self.cmd_os,
            'run': self.cmd_run,
            'exit': self.cmd_exit
        }
        
        # Dictionary of token commands ($ commands)
        self.token_commands = {
            'shopping list': self.token_shopping_list
        }
        
        # Add enhancement commands if available
        self.register_enhancement_commands()

    def handle_dir_command(self, args):
        """Handle directory tree related commands."""
        if not args:
            return "Available commands: clear, info, settings, scan, path <directory>"
        
        command = args[0].lower()
        
        if command == "path":
            if len(args) < 2:
                return "Usage: /dir path <directory_path>"
            new_path = " ".join(args[1:])
            if self.app.directory_tree and hasattr(self.app.directory_tree, 'set_root_path'):
                if self.app.directory_tree.set_root_path(new_path):
                    return f"Directory tree root changed to: {new_path}"
                return f"Failed to change directory to: {new_path}"
            return "Directory tree manager not available"
        
        elif command == "scan":
            if self.app.directory_tree:
                self.app.directory_tree.show_tree()
                return "Directory tree refreshed"
            return "Directory tree manager not available"
        
        elif command == "info":
            if self.app.directory_tree and hasattr(self.app.directory_tree, 'get_info'):
                return self.app.directory_tree.get_info()
            return "Directory tree manager not available"
        
        elif command == "settings":
            if self.app.directory_tree and hasattr(self.app.directory_tree, 'show_settings'):
                return self.app.directory_tree.show_settings()
            return "Directory tree manager not available"
        
        elif command == "clear":
            if self.app.directory_tree and hasattr(self.app.directory_tree, 'clear'):
                self.app.directory_tree.clear()
                return "Directory tree cleared"
            return "Directory tree manager not available"
        
        return f"Unknown directory command: {command}"

    def register_enhancement_commands(self):
        """Register commands from enhancement modules."""
        # Register directory tree commands
        if hasattr(self.app, 'directory_tree') and self.app.directory_tree:
            self.slash_commands['tree'] = self.app.directory_tree.cmd_tree
            self.slash_commands['dir'] = self.app.directory_tree.cmd_dir
            # Only register claude command if it's implemented
            if hasattr(self.app.directory_tree, 'cmd_claude'):
                self.slash_commands['claude'] = self.app.directory_tree.cmd_claude
        
        # Register checkbox commands
        if hasattr(self.app, 'checkbox_handler') and self.app.checkbox_handler:
            self.slash_commands['toggle'] = self.app.checkbox_handler.cmd_toggle
            self.slash_commands['todo'] = self.cmd_todo
            self.slash_commands['done'] = self.cmd_done
        
        # Register multiline commands
        if hasattr(self.app, 'multiline_handler') and self.app.multiline_handler:
            self.slash_commands['multiline'] = self.app.multiline_handler.cmd_multiline
            self.slash_commands['ml'] = self.app.multiline_handler.cmd_multiline  # Shorthand
        
        # Register word info commands
        if hasattr(self.app, 'word_info') and self.app.word_info:
            self.slash_commands['word'] = self.app.word_info.cmd_word
            self.slash_commands['words'] = self.app.word_info.cmd_words
    
    def process_slash_command(self, cmd_text, timestamp):
        """
        Process a slash command (commands that start with /).
        
        Args:
            cmd_text (str): The command text (without the slash)
            timestamp (str): The timestamp when the command was entered
        
        Returns:
            bool: True if command was processed successfully
        """
        # Split the command and arguments
        parts = cmd_text.split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in self.slash_commands:
            # Execute the command and get result
            result = self.slash_commands[cmd](args)
            
            # Display command result
            if result:
                self.app.gui_manager.set_feedback(result)
            else:
                self.app.gui_manager.clear_feedback()
                
            # Log command in CSV
            slash_csv_prefix = self.app.config.get("SLASH_CSV_PREFIX", "//")
            self.app.data_manager.write_entry(timestamp, f"{slash_csv_prefix}{cmd} {args}")
            return True
        else:
            self.app.gui_manager.set_feedback(f"Unknown command: {cmd}")
            return False
    
    def process_token_command(self, input_text, timestamp):
        """
        Process a token command (commands that start with $).
        
        Args:
            input_text (str): The command text (without the $)
            timestamp (str): The timestamp when the command was entered
            
        Returns:
            bool: True if a token command was processed
        """
        # Check if input text starts with any of the token commands
        for token, handler in self.token_commands.items():
            if input_text.startswith(token):
                # Extract the remainder after the token
                remainder = input_text[len(token):].strip()
                # Process the token command
                handler(remainder, timestamp)
                # Log the token command in CSV
                token_csv_prefix = self.app.config.get("TOKEN_CSV_PREFIX", "$")
                self.app.data_manager.write_entry(timestamp, f"{token_csv_prefix}{input_text}")
                return True
        
        # If no token matches, it's an unknown token command
        if input_text:
            first_word = input_text.split()[0]
            self.app.gui_manager.set_feedback(f"Unknown token command: ${first_word}")
            return False
        else:
            self.app.gui_manager.set_feedback("Token command requires a token")
            return False
    
    # ========== SLASH COMMANDS ==========
    
    def cmd_help(self, args):
        """Display available commands and their descriptions"""
        help_text = "Available commands:\n\n"
        
        # Core commands
        help_text += "--- Core Commands ---\n"
        help_text += "/help - Show this help message\n"
        help_text += "/echo [text] - Echo text back\n"
        help_text += "/list [n] - List the last n entries (default 5)\n"
        help_text += "/clear - Clear the feedback area\n"
        help_text += "/os [command] - Run OS command (use with caution)\n"
        help_text += "/run [file] - Execute a Python script\n"
        help_text += "/exit - Exit the application\n\n"
        
        # Checkbox commands
        if hasattr(self.app, 'checkbox_handler') and self.app.checkbox_handler:
            help_text += "--- Checkbox Commands ---\n"
            help_text += "/toggle <number> - Toggle checkbox by line number\n"
            help_text += "/toggle <pattern> - Toggle checkbox matching pattern\n"
            help_text += "/todo [text] - Create a new todo item\n"
            help_text += "/done [text] - Create a completed todo item\n\n"
        
        # Multiline commands
        if hasattr(self.app, 'multiline_handler') and self.app.multiline_handler:
            help_text += "--- Multiline Commands ---\n"
            help_text += "/multiline (or /ml) - Toggle multiline input mode\n"
            help_text += "/multiline lines [n] - Set number of lines (1-20)\n"
            help_text += "/multiline preserve [on|off] - Toggle preserving newlines\n\n"
        
        # Word info commands
        if hasattr(self.app, 'word_info') and self.app.word_info:
            help_text += "--- Word Info Commands ---\n"
            help_text += "/word <word> - Look up or add word information\n"
            help_text += "/words - List all words in database\n"
            help_text += "/words <pattern> - Search words by pattern\n\n"
        
        # Directory tree commands
        if hasattr(self.app, 'directory_tree') and self.app.directory_tree:
            help_text += "--- Directory Tree Commands ---\n"
            help_text += "/tree [path] - Generate directory tree\n"
            help_text += "/dir - Show directory cache status\n"
            help_text += "/dir scan [path] - Scan directory into cache\n"
            help_text += "/dir info [path] - Show info about a directory\n"
            help_text += "/dir clear - Clear directory cache\n"
            help_text += "/claude <directory> - Generate Claude Project\n\n"
        
        # Token commands
        help_text += "--- Token Commands ---\n"
        help_text += "$shopping list [items] - Add items to your shopping list\n"
        
        return help_text
    
    def cmd_echo(self, args):
        """Echo the arguments back to the user"""
        return args if args else "Echo what?"
    
    def cmd_list(self, args):
        """List the n most recent non-empty entries"""
        try:
            n = int(args) if args else 5
        except ValueError:
            return "Invalid number. Usage: /list [n]"
        
        try:
            df = pd.read_csv(self.app.data_manager.csv_filename)
            # Filter out empty entries
            df = df[df['text'].notna() & (df['text'] != '')]
            
            if df.empty:
                return "No entries found"
            
            # Get the last n entries
            recent = df.tail(n)
            
            result = "Recent entries:\n"
            for _, row in recent.iterrows():
                text = row['text']
                # Truncate long entries
                if len(text) > 50:
                    text = text[:47] + "..."
                result += f"- {text}\n"
            
            return result
        except Exception as e:
            return f"Error listing entries: {str(e)}"
    
    def cmd_clear(self, args):
        """Clear the feedback area"""
        self.app.gui_manager.clear_feedback()
        return None
    
    def cmd_os(self, args):
        """Run an operating system command (with caution)"""
        if not args:
            return "Usage: /os [command]"
        
        try:
            # Execute the command and capture output
            result = subprocess.run(
                args, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            output = result.stdout.strip()
            if not output and result.stderr:
                output = result.stderr.strip()
            
            return output if output else "Command executed (no output)"
        except subprocess.TimeoutExpired:
            return "Command timed out (5s limit)"
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def cmd_run(self, args):
        """Execute a Python script"""
        if not args:
            return "Usage: /run [filename.py]"
        
        script_path = args
        if not os.path.exists(script_path):
            # Try prepending the current directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, args)
            if not os.path.exists(script_path):
                return f"Script not found: {args}"
        
        try:
            # Execute the script as a subprocess
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout.strip()
            if not output and result.stderr:
                output = result.stderr.strip()
            
            return output if output else "Script executed (no output)"
        except subprocess.TimeoutExpired:
            return "Script execution timed out (10s limit)"
        except Exception as e:
            return f"Error executing script: {str(e)}"
    
    def cmd_exit(self, args):
        """Exit the application"""
        self.app.on_close()
        return None
    
    # ========== ENHANCEMENT COMMANDS ==========
    
    def cmd_todo(self, args):
        """Create a new todo item"""
        if not args:
            return "Usage: /todo [text] - Create a new todo item"
        
        # Create checkbox text
        checkbox_text = f"- [ ] {args}"
        
        # Get timestamp
        timestamp = self.app.data_manager.get_timestamp()
        
        # Save to CSV
        self.app.data_manager.write_entry(timestamp, checkbox_text)
        
        return f"Added todo item: {args}"
    
    def cmd_done(self, args):
        """Create a completed todo item"""
        if not args:
            return "Usage: /done [text] - Create a completed todo item"
        
        # Create checkbox text
        checkbox_text = f"- [x] {args}"
        
        # Get timestamp
        timestamp = self.app.data_manager.get_timestamp()
        
        # Save to CSV
        self.app.data_manager.write_entry(timestamp, checkbox_text)
        
        return f"Added completed item: {args}"
    
    # ========== TOKEN COMMANDS ==========
    
    def token_shopping_list(self, item_text, timestamp):
        """Add an item to the shopping list"""
        if not item_text:
            self.app.gui_manager.set_feedback("Please specify an item for your shopping list")
            return
            
        try:
            # Get the directory where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            shopping_list_path = os.path.join(script_dir, "shopping list.txt")
            
            # Append to the shopping list file
            with open(shopping_list_path, 'a') as f:
                f.write(f"{item_text}\n")
                
            self.app.gui_manager.set_feedback(f"Added to shopping list: {item_text}")
            
        except Exception as e:
            self.app.gui_manager.set_feedback(f"Error adding to shopping list: {str(e)}")