"""
GUI Manager Module

Handles the graphical user interface for the Z application.
"""

import tkinter as tk
from tkinter import ttk


class GUIManager:
    """Manages the GUI for the Z application."""
    
    def __init__(self, app):
        """
        Initialize the GUI manager.
        
        Args:
            app: The Z application instance
        """
        self.app = app
        
        # Configure grid weights for main window
        app.root.grid_columnconfigure(1, weight=3)  # Main content area
        app.root.grid_columnconfigure(0, weight=1)  # Directory tree area
        app.root.grid_rowconfigure(0, weight=1)
        
        # Create the main frame for input/feedback
        self.frame = ttk.Frame(app.root, padding="10")
        self.frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure frame grid weights
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        
        # Input field
        self.input_var = tk.StringVar()
        self.input_field = ttk.Entry(self.frame, textvariable=self.input_var)
        self.input_field.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.input_field.focus()
        
        # Add a hint label for multiline mode
        self.multiline_hint_var = tk.StringVar()
        self.update_multiline_hint()
        self.multiline_hint = ttk.Label(
            self.frame,
            textvariable=self.multiline_hint_var,
            foreground="gray",
            font=("TkDefaultFont", 8)
        )
        self.multiline_hint.grid(row=2, column=0, padx=5, sticky="w")
        
        # Feedback label
        self.feedback_var = tk.StringVar()
        self.feedback_label = ttk.Label(self.frame, textvariable=self.feedback_var, foreground="blue")
        self.feedback_label.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Bind Enter key to handle input
        app.root.bind('<Return>', app.event_handler.handle_input)
        
        # Set up a periodic check for multiline mode
        self.check_multiline_mode()
    
    def update_multiline_hint(self):
        """Update the multiline mode hint."""
        if hasattr(self.app, 'multiline_handler') and self.app.multiline_handler:
            if self.app.multiline_handler.is_active():
                # Show multiline mode hint
                lines = self.app.multiline_handler.settings.get("lines", 3)
                buffer_size = len(self.app.multiline_handler.buffer)
                self.multiline_hint_var.set(
                    f"Multiline mode active ({buffer_size} lines) - "
                    f"Use /ml submit to save or /ml cancel to discard"
                )
            else:
                # Show command hint
                self.multiline_hint_var.set("Use /ml to enable multiline mode")
        else:
            # Clear the hint if multiline module not available
            self.multiline_hint_var.set("")
    
    def check_multiline_mode(self):
        """Periodically check multiline mode and update UI accordingly."""
        # Update the multiline hint
        self.update_multiline_hint()
        
        # Schedule next check
        self.app.root.after(1000, self.check_multiline_mode)
    
    def set_feedback(self, message):
        """
        Set the feedback message.
        
        Args:
            message (str): Feedback message to display
        """
        self.feedback_var.set(message)
    
    def clear_feedback(self):
        """Clear the feedback message."""
        self.feedback_var.set("")
    
    def get_input_text(self):
        """
        Get the current input text.
        
        Returns:
            str: Current input text
        """
        return self.input_var.get().strip()
    
    def clear_input(self):
        """Clear the input field."""
        self.input_var.set("")
    
    def focus_input(self):
        """Set focus to the input field."""
        self.input_field.focus()
    
    def update_window_title(self, title):
        """
        Update the main window title.
        
        Args:
            title (str): New window title
        """
        self.app.root.title(title)