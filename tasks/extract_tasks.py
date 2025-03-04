"""
Extract Tasks Script

This script extracts rows from Z.csv based on task and completion status.
"""

import os
import sys
import pandas as pd
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration from config module if available
try:
    from config import DATA_CSV
except ImportError:
    # Default if config module is missing
    DATA_CSV = "Z.csv"

def extract_tasks(input_filename=None, output_filename=None, filter_completed=False, only_completed=False):
    """
    Extract tasks from Z.csv to a separate file.
    
    Args:
        input_filename (str, optional): Source CSV file
        output_filename (str, optional): Destination CSV file
        filter_completed (bool): Whether to include completion status in filtering
        only_completed (bool): When filter_completed is True, whether to get only completed tasks
        
    Returns:
        str: Success/error message
    """
    try:
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Default input filename
        if input_filename is None:
            input_filename = DATA_CSV
        
        # Default output filename
        if output_filename is None:
            if only_completed and filter_completed:
                output_filename = "completed_tasks.csv"
            elif filter_completed and not only_completed:
                output_filename = "pending_tasks.csv"
            else:
                output_filename = "tasks.csv"
        
        # Full paths
        input_path = os.path.join(script_dir, input_filename)
        output_path = os.path.join(script_dir, output_filename)
        
        # Check if input file exists
        if not os.path.exists(input_path):
            return f"Error: File '{input_filename}' not found"
        
        # Read the CSV file
        df = pd.read_csv(input_path)
        
        # Check if required columns exist
        if 'task' not in df.columns:
            return f"Error: No 'task' column found in '{input_filename}'"
        
        # Filter rows where task is explicitly 1
        # This will handle various data types and exclude null/empty values
        tasks_df = df[df['task'].notna() & (df['task'].astype(str) == '1')]
        
        # Apply completed filter if requested
        if filter_completed and 'completed' in df.columns:
            if only_completed:
                # Get only completed tasks
                tasks_df = tasks_df[tasks_df['completed'].notna() & (tasks_df['completed'].astype(str) == '1')]
                filter_description = "completed "
            else:
                # Get only non-completed tasks
                tasks_df = tasks_df[~(tasks_df['completed'].notna() & (tasks_df['completed'].astype(str) == '1'))]
                filter_description = "pending "
        else:
            filter_description = ""
        
        # Check if any tasks were found
        if tasks_df.empty:
            return f"No {filter_description}tasks found in '{input_filename}'"
        
        # Save to output file
        tasks_df.to_csv(output_path, index=False)
        
        return f"Successfully extracted {len(tasks_df)} {filter_description}tasks to '{output_filename}'"
        
    except Exception as e:
        return f"Error extracting tasks: {str(e)}"

class TaskExtractorApp:
    """GUI application for extracting tasks from Z.csv"""
    
    def __init__(self, root):
        """Initialize the task extractor app"""
        self.root = root
        root.title("Z Task Extractor")
        root.geometry("450x300")
        
        # Main frame
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Extract Tasks from Z.csv", font=("Helvetica", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Input file frame
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        input_label = tk.Label(input_frame, text="Input file:", width=10, anchor="w")
        input_label.pack(side=tk.LEFT)
        
        self.input_var = tk.StringVar(value=DATA_CSV)
        input_entry = tk.Entry(input_frame, textvariable=self.input_var)
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        input_button = tk.Button(input_frame, text="Browse", command=self.browse_input)
        input_button.pack(side=tk.RIGHT)
        
        # Output file frame
        output_frame = tk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        output_label = tk.Label(output_frame, text="Output file:", width=10, anchor="w")
        output_label.pack(side=tk.LEFT)
        
        self.output_var = tk.StringVar(value="tasks.csv")
        output_entry = tk.Entry(output_frame, textvariable=self.output_var)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        output_button = tk.Button(output_frame, text="Browse", command=self.browse_output)
        output_button.pack(side=tk.RIGHT)
        
        # Filter options frame
        filter_frame = tk.LabelFrame(main_frame, text="Filter Options", padx=10, pady=10)
        filter_frame.pack(fill=tk.X, pady=10)
        
        # Filter by completion status
        self.filter_completed_var = tk.BooleanVar(value=False)
        filter_completed_check = ttk.Checkbutton(
            filter_frame, 
            text="Filter by completion status",
            variable=self.filter_completed_var,
            command=self.toggle_completion_options
        )
        filter_completed_check.pack(anchor=tk.W)
        
        # Completion filter options
        self.completion_option_frame = ttk.Frame(filter_frame)
        self.completion_option_frame.pack(fill=tk.X, padx=20, pady=(5, 0))
        
        self.completion_option_var = tk.StringVar(value="pending")
        pending_radio = ttk.Radiobutton(
            self.completion_option_frame,
            text="Only pending tasks",
            variable=self.completion_option_var,
            value="pending",
            state=tk.DISABLED
        )
        pending_radio.pack(anchor=tk.W)
        
        self.completed_radio = ttk.Radiobutton(
            self.completion_option_frame,
            text="Only completed tasks",
            variable=self.completion_option_var,
            value="completed",
            state=tk.DISABLED
        )
        self.completed_radio.pack(anchor=tk.W)
        
        # Store radiobutton references
        self.option_buttons = [pending_radio, self.completed_radio]
        
        # Extract button
        extract_button = tk.Button(main_frame, text="Extract Tasks", command=self.extract)
        extract_button.pack(pady=10)
        
        # Status label
        self.status_var = tk.StringVar()
        status_label = tk.Label(main_frame, textvariable=self.status_var, wraplength=400)
        status_label.pack(pady=5)
    
    def toggle_completion_options(self):
        """Enable/disable completion filter options"""
        if self.filter_completed_var.get():
            state = tk.NORMAL
        else:
            state = tk.DISABLED
        
        for button in self.option_buttons:
            button.configure(state=state)
    
    def browse_input(self):
        """Open file dialog to select input CSV file"""
        filename = filedialog.askopenfilename(
            initialdir=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            title="Select input CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.input_var.set(os.path.basename(filename))
    
    def browse_output(self):
        """Open file dialog to select output CSV file"""
        filename = filedialog.asksaveasfilename(
            initialdir=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            title="Select output CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            defaultextension=".csv"
        )
        if filename:
            self.output_var.set(os.path.basename(filename))
    
    def extract(self):
            """Extract tasks from input file to output file"""
            # Get filter options
            filter_completed = self.filter_completed_var.get()
            only_completed = self.completion_option_var.get() == "completed" if filter_completed else False
            
            # Update output filename based on filter if user hasn't changed it
            if self.output_var.get() == "tasks.csv":
                if filter_completed:
                    if only_completed:
                        self.output_var.set("completed_tasks.csv")
                    else:
                        self.output_var.set("pending_tasks.csv")
            
            # Extract tasks
            result = extract_tasks(
                self.input_var.get(), 
                self.output_var.get(),
                filter_completed,
                only_completed
            )
            
            self.status_var.set(result)
            
            # Show message box with result
            if result.startswith("Error:") or result.startswith("No"):
                messagebox.showerror("Extract Result", result)
            else:
                messagebox.showinfo("Extract Result", result)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Usage: python -m tasks.extract_tasks [input_file] [output_file] [options]")
            print("  input_file: CSV file to extract tasks from (default: Z.csv)")
            print("  output_file: CSV file to write tasks to (default: tasks.csv)")
            print("Options:")
            print("  --pending: Extract only pending tasks")
            print("  --completed: Extract only completed tasks")
            return
        
        # Get input and output filenames
        input_file = sys.argv[1] if len(sys.argv) > 1 else None
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        # Parse options
        filter_completed = False
        only_completed = False
        
        for arg in sys.argv[1:]:
            if arg == "--pending":
                filter_completed = True
                only_completed = False
            elif arg == "--completed":
                filter_completed = True
                only_completed = True
        
        # Extract tasks
        result = extract_tasks(input_file, output_file, filter_completed, only_completed)
        print(result)
    else:
        # GUI mode
        root = tk.Tk()
        app = TaskExtractorApp(root)
        root.mainloop()

if __name__ == "__main__":
    main()