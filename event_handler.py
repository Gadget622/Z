"""
Event Handler Module

Handles user interface events for the Z application.
"""


class EventHandler:
    """Handles events from the user interface."""
    
    def __init__(self, app):
        """
        Initialize the event handler.
        
        Args:
            app: The Z application instance
        """
        self.app = app
    
    def handle_input(self, event=None):
        """
        Handle user input from the input field.
        
        Args:
            event: The event that triggered this handler (optional)
        """
        # Get input text
        input_text = self.app.gui_manager.get_input_text()
        
        if not input_text:
            self.app.gui_manager.clear_feedback()
            return
        
        # Record timestamp for all inputs
        timestamp = self.app.data_manager.get_timestamp()
        
        # Check if multiline mode is active (handle differently)
        if hasattr(self.app, 'multiline_handler') and self.app.multiline_handler and self.app.multiline_handler.is_active():
            # If in multiline mode, add to buffer and don't process until submission
            self.app.multiline_handler.add_to_buffer(input_text)
            self.app.gui_manager.clear_input()
            return
        
        # Store the original input for potential recovery
        original_input = input_text
        
        # Get command prefixes from config
        slash_prefix = self.app.config.get("SLASH_PREFIX", "/")
        slash_prefix_alt = self.app.config.get("SLASH_PREFIX_ALT", "//")
        token_prefix = self.app.config.get("TOKEN_PREFIX", "$")
        token_prefix_alt = self.app.config.get("TOKEN_PREFIX_ALT", "$")
        
        # Check if the input is a slash command
        if input_text.startswith(slash_prefix):
            # Remove prefix (either / or //)
            if input_text.startswith(slash_prefix_alt):
                cmd_text = input_text[len(slash_prefix_alt):]
            else:
                cmd_text = input_text[len(slash_prefix):]
                
            # Check if this is a tree command with special path like ".."
            # which needs special handling to prevent disappearing input
            if cmd_text.startswith("tree") and (".." in cmd_text or "." in cmd_text):
                try:
                    # Process the command and get result
                    if self.app.command_handler:
                        result = self.app.command_handler.process_slash_command(cmd_text, timestamp)
                        
                        # If command failed, restore input
                        if not result:
                            self.app.gui_manager.set_input_text(original_input)
                            return
                    else:
                        self.app.gui_manager.set_feedback("Command system is unavailable")
                        self.app.gui_manager.set_input_text(original_input)
                        return
                except Exception as e:
                    # If an error occurred, restore input and show error
                    self.app.error_handler.log_error(f"Error processing tree command: {e}")
                    self.app.gui_manager.set_feedback(f"Error processing command: {str(e)}")
                    self.app.gui_manager.set_input_text(original_input)
                    return
            else:
                # Handle normal slash command
                if self.app.command_handler:
                    self.app.command_handler.process_slash_command(cmd_text, timestamp)
                else:
                    self.app.gui_manager.set_feedback("Command system is unavailable")
        
        # Check if the input is a token command
        elif input_text.startswith(token_prefix):
            # Remove prefix (either $ or $$)
            if input_text.startswith(token_prefix_alt):
                token_text = input_text[len(token_prefix_alt):].strip()
            else:
                token_text = input_text[len(token_prefix):].strip()
                
            # Handle token command
            if self.app.command_handler:
                self.app.command_handler.process_token_command(token_text, timestamp)
            else:
                self.app.gui_manager.set_feedback("Command system is unavailable")
        
        # Check if input is a checkbox and checkbox handler is available
        elif hasattr(self.app, 'checkbox_handler') and self.app.checkbox_handler and self.app.checkbox_handler.is_checkbox(input_text):
            # Store checkbox in CSV
            self.app.data_manager.write_entry(timestamp, input_text)
            
            # Show feedback
            is_checked, content = self.app.checkbox_handler.get_checkbox_state(input_text)
            state = "Checked" if is_checked else "Unchecked"
            self.app.gui_manager.set_feedback(f"Added {state} item: {content}")
        
        else:
            # Regular input - store in CSV
            self.app.data_manager.write_entry(timestamp, input_text)
            self.app.gui_manager.clear_feedback()
        
        # Clear the input field (if we got this far, all went well)
        self.app.gui_manager.clear_input()
        self.app.gui_manager.focus_input()