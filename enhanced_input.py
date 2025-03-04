"""
Enhanced Input Module

Provides a multi-field input interface for the Z application with:
- Multiple configurable input fields
- Checkbox activation for each field
- Column selection via dropdown menus
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import os
import csv

class EnhancedInputPanel:
    """Manages a configurable multi-field input panel for Z application."""
    
    def __init__(self, app):
        """
        Initialize the enhanced input panel.
        
        Args:
            app: The parent Z application
        """
        self.app = app
        
        # Configuration
        self.num_fields = 5  # Default number of input fields
        self.fields = []  # Will store references to all field components
        
        # Get available columns from CSV
        self.columns = self.get_available_columns()
        
        # Create the input panel
        self.create_input_panel()
        
        # Replace default input controls with our enhanced panel
        self.replace_default_input()
        
        # Initialize dropdown options
        self.update_dropdown_options()
    
    def get_available_columns(self):
        """
        Get available columns from the CSV file.
        
        Returns:
            list: List of column names
        """
        columns = ['text']  # Default if CSV doesn't exist
        
        try:
            # Check if CSV file exists
            if os.path.exists(self.app.data_manager.csv_filename):
                # Read CSV
                df = pd.read_csv(self.app.data_manager.csv_filename)
                # Get column names (excluding timestamp)
                columns = [col for col in df.columns if col != 'timestamp']
        except Exception as e:
            self.app.error_handler.log_error(f"Error getting columns: {e}")
        
        return columns
    
    def create_input_panel(self):
        """Create the enhanced input panel with multiple fields."""
        # Main frame for the input panel
        self.frame = ttk.Frame(self.app.root)
        
        # For each field, create a row with checkbox, dropdown, and input
        for i in range(self.num_fields):
            field_frame = ttk.Frame(self.frame)
            field_frame.pack(fill=tk.X, pady=2)
            
            # Checkbox to activate field
            active_var = tk.BooleanVar(value=True if i == 0 else False)
            checkbox = ttk.Checkbutton(field_frame, variable=active_var)
            checkbox.pack(side=tk.LEFT, padx=5)
            
            # Dropdown for column selection
            column_var = tk.StringVar(value='text' if i == 0 else '')
            dropdown = ttk.Combobox(field_frame, textvariable=column_var, width=15)
            dropdown['values'] = self.columns
            dropdown.pack(side=tk.LEFT, padx=5)
            
            # Input field
            input_var = tk.StringVar()
            entry = ttk.Entry(field_frame, textvariable=input_var, width=40)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            # Store all components for this field
            field_data = {
                'active_var': active_var,
                'column_var': column_var,
                'input_var': input_var,
                'checkbox': checkbox,
                'dropdown': dropdown,
                'entry': entry,
                'frame': field_frame,
                'index': i  # Store the index for reference
            }
            
            self.fields.append(field_data)
            
            # Fix for lambda scoping issue - use a function to create proper bindings
            def create_bindings(field_index):
                self.fields[field_index]['dropdown'].bind('<<ComboboxSelected>>', 
                                                          lambda event, idx=field_index: self.on_dropdown_changed(idx))
                self.fields[field_index]['checkbox'].config(command=lambda idx=field_index: self.on_checkbox_toggled(idx))
            
            create_bindings(i)
        
        # Add Submit button
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.submit_button = ttk.Button(
            button_frame,
            text="Submit",
            command=self.submit_entry
        )
        self.submit_button.pack(side=tk.LEFT, padx=5)
        
        # Add New Column button
        self.new_column_button = ttk.Button(
            button_frame,
            text="New Column",
            command=self.create_new_column
        )
        self.new_column_button.pack(side=tk.LEFT, padx=5)
    
    def on_dropdown_changed(self, field_index):
        """Handle dropdown selection change."""
        self.update_dropdown_options()
    
    def on_checkbox_toggled(self, field_index):
        """
        Handle checkbox toggle.
        Prevent activating a field if its column is already active in another field.
        """
        field = self.fields[field_index]
        is_active = field['active_var'].get()
        column = field['column_var'].get()
        
        # If trying to activate and column is selected
        if is_active and column:
            # Check if this column is active in any other field
            for i, other_field in enumerate(self.fields):
                if i != field_index and other_field['active_var'].get() and other_field['column_var'].get() == column:
                    # Column already active elsewhere - prevent activation
                    field['active_var'].set(False)
                    self.app.gui_manager.set_feedback(f"Column '{column}' is already active in another field")
                    return
        
        # Update dropdown options
        self.update_dropdown_options()
    
    def replace_default_input(self):
        """Replace the default input controls with our enhanced panel."""
        # Hide the original input field and related controls
        if hasattr(self.app.gui_manager, 'input_field'):
            self.app.gui_manager.input_field.grid_remove()
        
        if hasattr(self.app.gui_manager, 'feedback_label'):
            self.app.gui_manager.feedback_label.grid_remove()
        
        # Place our frame in the main window
        self.frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Bind Enter key to submit
        for field in self.fields:
            field['entry'].bind('<Return>', lambda event: self.submit_entry())
    
    def update_dropdown_options(self):
        """
        Update dropdown options to prevent duplicate active columns.
        Inactive fields don't restrict column selection.
        """
        # Get all active selected columns
        active_columns = {}  # Use a dictionary to track {column_name: field_index}
        
        for field in self.fields:
            if field['active_var'].get() and field['column_var'].get():
                column = field['column_var'].get()
                active_columns[column] = field['index']
        
        # Update each dropdown
        for field in self.fields:
            current_selection = field['column_var'].get()
            is_active = field['active_var'].get()
            field_index = field['index']
            
            # Calculate available columns
            if is_active:
                # For active fields: all columns except those selected in other active fields
                available = []
                for col in self.columns:
                    # Include if:
                    # 1. It's the current selection for this field, OR
                    # 2. It's not selected in any other active field
                    if col == current_selection or col not in active_columns or active_columns[col] == field_index:
                        available.append(col)
            else:
                # For inactive fields: all columns are available
                available = self.columns
            
            # Update the dropdown values
            field['dropdown']['values'] = available
            
            # If current selection is no longer valid (shouldn't happen with this logic), clear it
            if current_selection and current_selection not in available:
                field['column_var'].set('')

    def submit_entry(self):
        """Submit the entry with all active fields."""
        # Collect data from active fields
        data = {}
        
        for field in self.fields:
            if field['active_var'].get():
                column = field['column_var'].get()
                value = field['input_var'].get()
                
                if column and value:
                    data[column] = value
        
        if not data:
            self.app.gui_manager.set_feedback("No data to submit")
            return
        
        # Get timestamp
        timestamp = self.app.data_manager.get_timestamp()
        
        # Add timestamp to data
        data['timestamp'] = timestamp
        
        # Write to CSV using metadata approach
        self.app.data_manager.write_entry_with_metadata(timestamp, data.get('text', ''), data)
        
        # Clear input fields
        for field in self.fields:
            field['input_var'].set('')
        
        # Focus the first active field
        for field in self.fields:
            if field['active_var'].get():
                field['entry'].focus()
                break
        
        # Show feedback
        columns = [k for k in data.keys() if k != 'timestamp']
        self.app.gui_manager.set_feedback(f"Added entry with columns: {', '.join(columns)}")
    
    def create_new_column(self):
        """Create a new column in the CSV file."""
        # Create a simple dialog to get the column name
        dialog = tk.Toplevel(self.app.root)
        dialog.title("New Column")
        dialog.geometry("300x100")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # Configure dialog
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        dialog.rowconfigure(1, weight=1)
        
        # Add a label and entry field
        ttk.Label(dialog, text="Enter new column name:").grid(
            row=0, column=0, padx=10, pady=(10, 0), sticky="w"
        )
        
        column_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=column_var, width=30)
        entry.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="ew")
        entry.focus_set()
        
        # Function to add the column
        def add_column():
            column_name = column_var.get().strip()
            
            if not column_name:
                self.app.gui_manager.set_feedback("Column name cannot be empty")
                return
            
            # Check if column already exists
            if column_name in self.columns or column_name == 'timestamp':
                self.app.gui_manager.set_feedback(f"Column '{column_name}' already exists")
                return
            
            # Add the column to the CSV
            try:
                if os.path.exists(self.app.data_manager.csv_filename):
                    df = pd.read_csv(self.app.data_manager.csv_filename)
                    
                    # Add new column
                    df[column_name] = None
                    
                    # Save back to CSV
                    df.to_csv(self.app.data_manager.csv_filename, index=False)
                    
                    # Update columns list
                    self.columns = self.get_available_columns()
                    
                    # Update dropdowns
                    self.update_dropdown_options()
                    
                    self.app.gui_manager.set_feedback(f"Added new column: {column_name}")
                else:
                    self.app.gui_manager.set_feedback("Cannot add column: CSV file does not exist")
            except Exception as e:
                self.app.error_handler.log_error(f"Error adding column: {e}")
                self.app.gui_manager.set_feedback(f"Error adding column: {str(e)}")
            
            dialog.destroy()
        
        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Add", command=add_column).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to add_column
        entry.bind('<Return>', lambda event: add_column())
        
        # Center the dialog on the parent window
        dialog.update_idletasks()
        x = self.app.root.winfo_x() + (self.app.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.app.root.winfo_y() + (self.app.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")