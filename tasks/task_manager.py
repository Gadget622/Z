"""
Task Manager Module

Handles task management functionality for the Z application.
Tasks are marked by integer flags in the CSV data (0 or 1).
"""

import os
import csv
import pandas as pd
import tkinter as tk
from tkinter import ttk

class TaskManager:
    """Manages task functionality for the Z application."""
    
    def __init__(self, app):
        """
        Initialize the task manager.
        
        Args:
            app: The parent Z application
        """
        self.app = app
        
        # Ensure task column exists in the CSV
        self.ensure_columns()
        
        # Add the task indicator and button to the GUI
        self.add_task_controls()
        
        # Bind to the input field directly
        self.app.gui_manager.input_field.bind('<Return>', self.handle_enter, add='+')
    
    def ensure_columns(self):
        """Ensure task and completed columns exist in the CSV file."""
        try:
            # Check if CSV file exists
            if not os.path.exists(self.app.data_manager.csv_filename):
                return
            
            # Read the CSV file
            df = pd.read_csv(self.app.data_manager.csv_filename)
            
            # Check if 'task' column exists
            if 'task' not in df.columns:
                # Add the task column header without setting values (they'll remain empty/null)
                df['task'] = None
                self.app.error_handler.log_info("Added 'task' column to CSV file")
            
            # Check if 'completed' column exists
            if 'completed' not in df.columns:
                # Add the completed column header without setting values
                df['completed'] = None
                self.app.error_handler.log_info("Added 'completed' column to CSV file")
            
            # If there are existing float values, convert them to integers for storage efficiency
            if 'task' in df.columns:
                # Convert NaN to None, floats to integers
                df['task'] = df['task'].apply(lambda x: int(x) if pd.notnull(x) else None)
            
            if 'completed' in df.columns:
                # Convert NaN to None, floats to integers
                df['completed'] = df['completed'].apply(lambda x: int(x) if pd.notnull(x) else None)
            
            # Write back to CSV if changes were made
            df.to_csv(self.app.data_manager.csv_filename, index=False)
                
        except Exception as e:
            self.app.error_handler.log_error(f"Error ensuring columns: {e}")
    
    def add_task_controls(self):
        """Add task and completed controls to the GUI."""
        # Create a frame for the task elements
        self.task_frame = ttk.Frame(self.app.gui_manager.frame)
        self.task_frame.grid(row=0, column=1, padx=5, pady=5, sticky="e")
        
        # Create task checkbox
        self.task_var = tk.IntVar(value=0)  # Use IntVar for direct 0/1 values
        self.task_label = ttk.Label(self.task_frame, text="Task:")
        self.task_label.pack(side=tk.LEFT, padx=(0, 5))
        self.task_checkbox = ttk.Checkbutton(
            self.task_frame,
            variable=self.task_var,
            style='Circle.TCheckbutton'  # Will create this style to make it circular
        )
        self.task_checkbox.pack(side=tk.LEFT, padx=(0, 10))
        
        # Create completed checkbox
        self.completed_var = tk.IntVar(value=0)  # Use IntVar for direct 0/1 values
        self.completed_label = ttk.Label(self.task_frame, text="Completed:")
        self.completed_label.pack(side=tk.LEFT, padx=(0, 5))
        self.completed_checkbox = ttk.Checkbutton(
            self.task_frame,
            variable=self.completed_var,
            style='Circle.TCheckbutton'
        )
        self.completed_checkbox.pack(side=tk.LEFT)
        
        # Try to create a circular style for the checkboxes
        try:
            style = ttk.Style()
            # Note: Making a truly circular checkbox requires custom styling 
            # that may vary by platform. This is a basic approximation.
            style.configure('Circle.TCheckbutton', background='white')
        except Exception as e:
            self.app.error_handler.log_error(f"Error styling checkboxes: {e}")
            
        # Add a submit button as backup
        self.submit_button = ttk.Button(
            self.task_frame,
            text="Submit",
            command=self.submit_entry
        )
        self.submit_button.pack(side=tk.RIGHT, padx=(10, 0))
    
    def handle_enter(self, event):
        """Handle Enter key press in the input field."""
        # Get input text
        input_text = self.app.gui_manager.get_input_text()
        
        if not input_text:
            return
        
        # Check if this is a command - if so, let the normal handler deal with it
        slash_prefix = self.app.config.get("SLASH_PREFIX", "/")
        token_prefix = self.app.config.get("TOKEN_PREFIX", "$")
        
        if input_text.startswith(slash_prefix) or input_text.startswith(token_prefix):
            # Don't interrupt command processing
            return
        
        # If it's multiline mode, let that handle it
        if hasattr(self.app, 'multiline_handler') and self.app.multiline_handler and self.app.multiline_handler.is_active():
            return
            
        # For regular text, use our custom handling
        self.submit_entry()
        
        # Prevent the default handler from running
        return "break"
    
    def submit_entry(self):
        """Submit the current input with task and completed flags."""
        # Get input text
        input_text = self.app.gui_manager.get_input_text()
        
        if not input_text:
            self.app.gui_manager.set_feedback("Please enter some text first")
            return
        
        # Get task and completed values - integers (0 or 1)
        task_value = self.task_var.get()
        completed_value = self.completed_var.get()
        
        # Get timestamp
        timestamp = self.app.data_manager.get_timestamp()
        
        # Write directly to CSV
        self.write_to_csv(timestamp, input_text, task_value, completed_value)
        
        # Clear input
        self.app.gui_manager.clear_input()
        
        # Set feedback
        feedback = "Added"
        if task_value == 1:
            feedback += " as task"
        if completed_value == 1:
            feedback += " (completed)"
        feedback += f": {input_text}"
        
        self.app.gui_manager.set_feedback(feedback)
    
    def write_to_csv(self, timestamp, text, task_value, completed_value):
        """
        Write directly to the CSV file using integers for task flags.
        
        Args:
            timestamp (str): Entry timestamp
            text (str): Entry text
            task_value (int): Task flag (0 or 1)
            completed_value (int): Completed flag (0 or 1)
        """
        try:
            # Ensure CSV exists
            if not os.path.exists(self.app.data_manager.csv_filename):
                with open(self.app.data_manager.csv_filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['timestamp', 'text', 'task', 'completed'])
            
            # Ensure our columns exist
            try:
                df = pd.read_csv(self.app.data_manager.csv_filename)
                columns_changed = False
                
                if 'task' not in df.columns:
                    df['task'] = None
                    columns_changed = True
                
                if 'completed' not in df.columns:
                    df['completed'] = None
                    columns_changed = True
                
                if columns_changed:
                    df.to_csv(self.app.data_manager.csv_filename, index=False)
                    
            except Exception as e:
                self.app.error_handler.log_error(f"Error checking columns: {e}")
            
            # Now write our row with integer values
            with open(self.app.data_manager.csv_filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([timestamp, text, int(task_value), int(completed_value)])
                
            self.app.error_handler.log_info(f"Added entry with task={task_value}, completed={completed_value}")
        
        except Exception as e:
            self.app.error_handler.log_error(f"Error writing to CSV: {e}")
            # Try using the app's data manager as fallback
            try:
                self.app.data_manager.write_entry(timestamp, text)
                self.app.error_handler.log_warning("Wrote entry without task data due to error")
            except Exception:
                self.app.error_handler.log_error("Complete failure to write entry")