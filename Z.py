"""
Z Application - Main Module

This is the main entry point for the Z application, a Zettelkasten note-taking system.
This module coordinates the different components and provides the main application window.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import time
import threading

try:
    from tasks import TaskManager, TaskListDisplay
except ImportError:
    # TaskManager and TaskListDisplay are optional
    TaskManager = None
    TaskListDisplay = None

# Import core modules with better error handling
try:
    from . import config_manager
    from . import data_manager
    from . import gui_manager
    from . import command_handler
    from . import event_handler
    from . import error_handler
    from .config_manager import load_config
except ImportError:
    try:
        import config_manager
        import data_manager
        import gui_manager
        import command_handler
        import event_handler
        import error_handler
        from config_manager import load_config
    except ImportError as e:
        print(f"Error importing core modules: {e}")
        print("Please ensure all required modules are available.")
        sys.exit(1)
class ZApp:
    """Main Z application class that coordinates all components."""
    
    def __init__(self):
        """Initialize the Z application."""
        try:
            # Set up error handling first
            self.error_handler = error_handler.ErrorHandler()
            
            # Initialize event handler early
            self.event_handler = event_handler.EventHandler(self)
            self.error_handler.log_info("Event handler initialized successfully")
            
            # Initialize the root window
            self.root = tk.Tk()
            self.root.title("Z Enhanced")
            self.root.resizable(True, True)
            
            # Load configuration
            self.config = load_config(self)
            
            # Set up the application directory
            self.script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Initialize data manager
            self.data_manager = data_manager.DataManager(self)
            
            # Initialize GUI
            self.gui_manager = gui_manager.GUIManager(self)
            
            # Initialize command handler
            self.command_handler = command_handler.CommandHandler(self)
            
            # Initialize enhancement modules last
            self.initialize_enhancements()
            
            # Set up periodic entries if enabled
            self.setup_periodic_entries()
            
            # Set up window close event
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
            
            # Set minimum window size
            self.root.minsize(300, 100)
            
        except Exception as e:
            self.error_handler.handle_critical_error(f"Error initializing application: {e}")
    
    def initialize_enhancements(self):
        """Initialize enhancement modules if available."""
        # Initialize enhanced input panel
        self.enhanced_input = None
        try:
            from enhanced_input import EnhancedInputPanel
            self.enhanced_input = EnhancedInputPanel(self)
            self.error_handler.log_info("Enhanced input panel initialized")
        except ImportError:
            self.error_handler.log_info("Enhanced input panel not available")
            
        # Initialize task manager - should be initialized AFTER gui_manager
        self.task_manager = None
        try:
            from tasks import TaskManager
            self.task_manager = TaskManager(self)
            self.error_handler.log_info("Task manager initialized")
        except ImportError:
            self.error_handler.log_info("Task manager not available")
        
        # Add task list display AFTER task_manager initialization
        self.task_list_display = None
        try:
            if self.task_manager:  # Only initialize if task_manager is available
                from tasks import TaskListDisplay
                self.task_list_display = TaskListDisplay(self)
                self.error_handler.log_info("Task list display initialized")
        except ImportError:
            self.error_handler.log_info("Task list display not available")

        # Initialize checkbox handler
        self.checkbox_handler = None
        try:
            from checkbox_handler import CheckboxHandler
            self.checkbox_handler = CheckboxHandler(self)
            self.error_handler.log_info("Checkbox handler initialized")
        except ImportError:
            self.error_handler.log_info("Checkbox handler not available")
        
        # Initialize multiline input handler
        self.multiline_handler = None
        try:
            from multiline_input import MultilineHandler
            self.multiline_handler = MultilineHandler(self)
            self.error_handler.log_info("Multiline handler initialized")
        except ImportError:
            self.error_handler.log_info("Multiline handler not available")
        
        # Initialize word info collector
        self.word_info = None
        try:
            from word_info import WordInfoCollector
            self.word_info = WordInfoCollector(self)
            self.error_handler.log_info("Word info collector initialized")
        except ImportError:
            self.error_handler.log_info("Word info collector not available")
        
        # Initialize directory tree manager
        self.directory_tree = None
        try:
            from directory_tree import DirectoryTreeManager
            self.directory_tree = DirectoryTreeManager(self)
            self.error_handler.log_info("Directory tree manager initialized")
            self.directory_tree.show_tree()
        except ImportError:
            self.error_handler.log_info("Directory tree manager not available")
    
    def setup_periodic_entries(self):
        """Set up periodic entries thread if enabled in config."""
        if self.config.get("PERIODIC_ENTRIES_ENABLED", False):
            self.stop_thread = threading.Event()
            self.periodic_interval = self.config.get("PERIODIC_ENTRIES_INTERVAL", 5)
            self.newline_thread = threading.Thread(target=self.add_periodic_newlines, daemon=True)
            self.newline_thread.start()
        else:
            self.stop_thread = threading.Event()
            self.newline_thread = None
    
    def add_periodic_newlines(self):
        """Add periodic empty entries to the database."""
        while not self.stop_thread.is_set():
            time.sleep(self.periodic_interval)
            
            if self.stop_thread.is_set():
                break
                
            # Add a timestamp with empty text
            timestamp = self.data_manager.get_timestamp()
            self.data_manager.write_entry(timestamp, "")
    
    def toggle_periodic_entries(self, enabled=None):
        """Toggle the periodic entries feature."""
        if enabled is None:
            enabled = not self.config.get("PERIODIC_ENTRIES_ENABLED", False)
        
        # Update config
        self.config["PERIODIC_ENTRIES_ENABLED"] = enabled
        config_manager.save_config(self.config)
        
        # Update thread
        if enabled:
            if self.newline_thread is None or not self.newline_thread.is_alive():
                self.stop_thread.clear()
                self.periodic_interval = self.config.get("PERIODIC_ENTRIES_INTERVAL", 5)
                self.newline_thread = threading.Thread(target=self.add_periodic_newlines, daemon=True)
                self.newline_thread.start()
                self.gui_manager.set_feedback("Periodic time entries enabled")
        else:
            if self.newline_thread and self.newline_thread.is_alive():
                self.stop_thread.set()
                self.gui_manager.set_feedback("Periodic time entries disabled")
    
    def on_close(self):
        """Handle application close event."""
        # Stop the periodic newline thread if running
        if self.newline_thread and self.newline_thread.is_alive():
            self.stop_thread.set()
            self.newline_thread.join(1.0)  # Wait up to 1 second for thread to finish
        
        # Try to recover any temp entries before closing
        try:
            self.data_manager.recover_temp_entries()
        except Exception:
            pass
        
        # Close the window
        self.root.destroy()
    
    def run(self):
        """Start the main event loop."""
        try:
            self.root.mainloop()
        except Exception as e:
            self.error_handler.handle_critical_error(f"Unexpected error in main loop: {e}")


def main():
    """Main function to start the Z application."""
    try:
        app = ZApp()
        app.run()
    except Exception as e:
        # Last resort error handling
        try:
            messagebox.showerror(
                "Critical Error",
                f"An unexpected error occurred: {e}\n\nThe application will now close."
            )
        except:
            print(f"Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()