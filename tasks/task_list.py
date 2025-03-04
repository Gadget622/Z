"""
Task List Module

Displays a list of uncompleted tasks in the Z application.
Uses integer values (0 or 1) for task flags for efficiency.
"""

import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox

class TaskListDisplay:
    """Component for displaying uncompleted tasks."""
    
    def __init__(self, app):
        """
        Initialize the task list display.
        
        Args:
            app: The parent Z application
        """
        self.app = app
        
        # Store task data
        self.tasks_df = None
        self.task_indices = []
        
        # Create task list frame
        self.create_task_list()
        
        # Initial load of tasks
        self.refresh_tasks()
        
        # Set up periodic refresh
        self.setup_auto_refresh()
    
    def create_task_list(self):
        """Create the task list display frame."""
        # Create main frame
        self.frame = ttk.LabelFrame(self.app.root, text="To-Do List")
        self.frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        
        # Configure grid weights
        self.app.root.grid_rowconfigure(1, weight=1)
        
        # Create task list as a Treeview (better for selection)
        self.task_tree = ttk.Treeview(self.frame, columns=("text", "timestamp"), show="headings")
        self.task_tree.heading("text", text="Task")
        self.task_tree.heading("timestamp", text="Added On")
        self.task_tree.column("text", width=300)
        self.task_tree.column("timestamp", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.frame, command=self.task_tree.yview)
        self.task_tree.config(yscrollcommand=scrollbar.set)
        
        # Button frame for actions
        self.button_frame = ttk.Frame(self.frame)
        
        # Complete button
        self.complete_button = ttk.Button(
            self.button_frame,
            text="Mark Completed",
            command=self.mark_selected_completed
        )
        self.complete_button.pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        self.refresh_button = ttk.Button(
            self.button_frame,
            text="Refresh",
            command=self.refresh_tasks
        )
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Place components
        self.task_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.button_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="w")
        
        # Configure grid weights for frame
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
    
    def setup_auto_refresh(self):
        """Set up periodic refresh of the task list."""
        # Refresh every 5 seconds
        self.app.root.after(5000, self.auto_refresh)
    
    def auto_refresh(self):
        """Automatically refresh the task list periodically."""
        self.refresh_tasks()
        # Schedule next refresh
        self.app.root.after(5000, self.auto_refresh)
    
    def refresh_tasks(self):
        """Load and display uncompleted tasks."""
        try:
            # Clear the task tree
            for item in self.task_tree.get_children():
                self.task_tree.delete(item)
            
            # Reset stored data
            self.task_indices = []
            
            # Check if CSV file exists
            if not os.path.exists(self.app.data_manager.csv_filename):
                self.app.error_handler.log_info("CSV file not found during task refresh")
                return
            
            # Read the CSV file
            df = pd.read_csv(self.app.data_manager.csv_filename)
            
            # Check if task and completed columns exist
            if 'task' not in df.columns or 'completed' not in df.columns:
                self.app.error_handler.log_info("Task or completed columns not found")
                return
            
            # Convert values to integers to handle mixed data types in CSV
            try:
                # Convert task column to numeric, coercing errors to NaN
                df['task'] = pd.to_numeric(df['task'], errors='coerce')
                
                # Convert completed column to numeric, coercing errors to NaN
                df['completed'] = pd.to_numeric(df['completed'], errors='coerce')
                
                # Filter for task=1 and (completed is not 1)
                # This works with integers (1), floats (1.0), or strings ('1') in the CSV
                mask = (df['task'] == 1) & ((df['completed'] != 1) | df['completed'].isna())
                
                # Apply the mask
                self.tasks_df = df[mask].copy()
                
                # Log for debugging
                self.app.error_handler.log_info(f"Found {len(self.tasks_df)} uncompleted tasks")
                
            except Exception as e:
                self.app.error_handler.log_error(f"Error filtering tasks: {e}")
                return
            
            # Check if any tasks were found
            if self.tasks_df.empty:
                self.app.error_handler.log_info("No uncompleted tasks found")
                return
            
            # Add tasks to the treeview
            for idx, row in self.tasks_df.iterrows():
                text = row['text']
                timestamp = row['timestamp']
                
                # Insert into treeview
                self.task_tree.insert("", "end", values=(text, timestamp))
                
                # Store the original dataframe index
                self.task_indices.append(idx)
            
        except Exception as e:
            self.app.error_handler.log_error(f"Error refreshing tasks: {e}")
    
    def mark_selected_completed(self):
        """Mark the selected task as completed."""
        # Get selected item
        selected_item = self.task_tree.selection()
        if not selected_item:
            messagebox.showinfo("No Selection", "Please select a task to mark as completed.")
            return
        
        try:
            # Get the index of the selected item in our list
            selected_idx = self.task_tree.index(selected_item[0])
            
            # Get the original dataframe index
            df_idx = self.task_indices[selected_idx]
            
            # Read the CSV file
            df = pd.read_csv(self.app.data_manager.csv_filename)
            
            # Store task text for feedback
            task_text = df.at[df_idx, 'text']
            
            # Update the completed status - use integer 1 (most efficient)
            df.at[df_idx, 'completed'] = 1
            
            # Write back to CSV
            df.to_csv(self.app.data_manager.csv_filename, index=False)
            
            # Remove from treeview
            self.task_tree.delete(selected_item[0])
            
            # Log and notify
            self.app.error_handler.log_info(f"Marked task as completed: {task_text}")
            self.app.gui_manager.set_feedback(f"Marked task as completed: {task_text}")
            
            # Update task list
            self.refresh_tasks()
            
        except Exception as e:
            self.app.error_handler.log_error(f"Error marking task as completed: {e}")
            messagebox.showerror("Error", f"Failed to mark task as completed: {str(e)}")