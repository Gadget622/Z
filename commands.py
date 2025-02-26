import os
import sys
import subprocess
import pandas as pd
from datetime import datetime

# Import config for command prefixes
try:
    from config import SLASH_PREFIX, SLASH_PREFIX_ALT, SLASH_CSV_PREFIX, TOKEN_PREFIX, TOKEN_PREFIX_ALT, TOKEN_CSV_PREFIX
except ImportError:
    # Default values if config module is missing
    SLASH_PREFIX = "/"
    SLASH_PREFIX_ALT = "//"
    SLASH_CSV_PREFIX = "//"
    TOKEN_PREFIX = "$"
    TOKEN_PREFIX_ALT = "$"
    TOKEN_CSV_PREFIX = "$"

class CommandHandler:
    """
    Handles parsing and execution of commands for the Z application.
    This class separates command handling logic from the main UI code.
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
                self.app.feedback_var.set(result)
            else:
                self.app.clear_feedback()
                
            # Log command in CSV
            self.app.write_to_csv(timestamp, f"{SLASH_CSV_PREFIX}{cmd} {args}")
            return True
        else:
            self.app.feedback_var.set(f"Unknown command: {cmd}")
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
                self.app.write_to_csv(timestamp, f"{TOKEN_CSV_PREFIX}{input_text}")
                return True
        
        # If no token matches, it's an unknown token command
        if input_text:
            first_word = input_text.split()[0]
            self.app.feedback_var.set(f"Unknown token command: ${first_word}")
            return False
        else:
            self.app.feedback_var.set("Token command requires a token")
            return False
    
    # ========== SLASH COMMANDS ==========
    
    def cmd_help(self, args):
        """Display available commands and their descriptions"""
        help_text = "Available commands:\n"
        help_text += "/help or //help - Show this help message\n"
        help_text += "/echo or //echo [text] - Echo text back\n"
        help_text += "/list or //list [n] - List the last n entries (default 5)\n"
        help_text += "/clear or //clear - Clear the feedback area\n"
        help_text += "/os or //os [command] - Run OS command (use with caution)\n"
        help_text += "/run or //run [file] - Execute a Python script\n"
        help_text += "/exit or //exit - Exit the application\n\n"
        
        help_text += "Token commands:\n"
        help_text += "$shopping list or $shopping list [items] - Add items to your shopping list"
        
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
            df = pd.read_csv(self.app.csv_filename)
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
        self.app.clear_feedback()
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
        self.app.root.quit()
        return None
    
    # ========== TOKEN COMMANDS ==========
    
    def token_shopping_list(self, item_text, timestamp):
        """Add an item to the shopping list"""
        if not item_text:
            self.app.feedback_var.set("Please specify an item for your shopping list")
            return
            
        try:
            # Get the directory where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            shopping_list_path = os.path.join(script_dir, "shopping list.txt")
            
            # Append to the shopping list file
            with open(shopping_list_path, 'a') as f:
                f.write(f"{item_text}\n")
                
            self.app.feedback_var.set(f"Added to shopping list: {item_text}")
            
        except Exception as e:
            self.app.feedback_var.set(f"Error adding to shopping list: {str(e)}")