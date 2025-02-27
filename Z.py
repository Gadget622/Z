import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import time
import threading
import csv
import pandas as pd
import subprocess
import platform
import sys

# Import helper for file operations
try:
    import file_helper
except ImportError:
    print("Error: file_helper.py module not found.")
    sys.exit(1)

# Import configuration from config module
try:
    from config import (
        DATA_CSV, TEMP_CSV, 
        PERIODIC_ENTRIES_ENABLED, PERIODIC_ENTRIES_INTERVAL,
        SLASH_PREFIX, SLASH_PREFIX_ALT, 
        TOKEN_PREFIX, TOKEN_PREFIX_ALT,
        ConfigError
    )
except ImportError as e:
    # Display error in a tkinter dialog
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    messagebox.showerror(
        "Configuration Error",
        f"Failed to import configuration module: {e}\n\nPlease ensure config.py exists in the application directory."
    )
    root.destroy()
    sys.exit(1)
except ConfigError as e:
    # Display the specific config error in a tkinter dialog
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    messagebox.showerror(
        "Configuration Error",
        f"{e}\n\nThe application will now prompt for the necessary information."
    )
    # Will handle by prompting user for configuration
    CONFIG_ERROR = str(e)
    root.deiconify()  # Show the root for user input
except Exception as e:
    # Any other unexpected error
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Unexpected Error",
        f"An unexpected error occurred while loading configuration: {e}"
    )
    root.destroy()
    sys.exit(1)

# Import command handler
try:
    from commands import CommandHandler
except ImportError:
    CommandHandler = None

class ZApp:
    def __init__(self):
        # Set up root window
        self.root = tk.Tk()
        self.root.title("Z")
        
        # Configure window to be resizable
        self.root.resizable(True, True)
        
        # Handle config errors by prompting user
        if 'CONFIG_ERROR' in globals():
            self.handle_config_error(CONFIG_ERROR)
        
        # Get the directory where the script is located
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # CSV file for storing data
        self.csv_filename = os.path.join(self.script_dir, DATA_CSV)
        
        # Set up temporary directory
        self.temp_dir = file_helper.setup_temp_directory()
        
        # Instead of a single temp file, we'll generate temp files as needed
        self.current_temp_file = None
        
        # Configure grid weights to enable responsive resizing
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Create the input interface
        self.frame = ttk.Frame(self.root, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure frame grid weights
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        
        # Input field
        self.input_var = tk.StringVar()
        self.input_field = ttk.Entry(self.frame, textvariable=self.input_var)
        self.input_field.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.input_field.focus()
        
        # Add a feedback label for command results
        self.feedback_var = tk.StringVar()
        self.feedback_label = ttk.Label(self.frame, textvariable=self.feedback_var, foreground="blue")
        self.feedback_label.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Create CSV file with headers if it doesn't exist
        self.ensure_csv_exists()
        
        # Initialize periodic entries variable
        self.periodic_var = tk.BooleanVar(value=PERIODIC_ENTRIES_ENABLED)
        
        # If periodic entries are enabled, start the thread
        if PERIODIC_ENTRIES_ENABLED:
            self.stop_thread = threading.Event()
            self.newline_thread = threading.Thread(target=self.add_periodic_newlines, daemon=True)
            self.newline_thread.start()
        else:
            self.stop_thread = threading.Event()
            self.newline_thread = None
            
        # Set minimum window size
        self.root.minsize(300, 100)
        
        # Initialize command handler
        self.command_handler = CommandHandler(self) if CommandHandler else None
        
        # Bind enter key to handle input
        self.root.bind('<Return>', self.handle_input)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def handle_config_error(self, error_message):
        """Handle configuration errors by prompting the user for information"""
        self.root.title("Z - Configuration Setup")
        
        if "DATA_CSV" in error_message:
            # Prompt user for a data file name
            filename = file_helper.prompt_for_filename(
                self.root,
                "Data File Configuration",
                "Please enter a name for your data file:"
            )
            
            if filename is None:  # User canceled
                messagebox.showerror(
                    "Configuration Required",
                    "A data file name is required for the application to function."
                )
                self.root.quit()
                sys.exit(1)
            
            # Update global variable
            global DATA_CSV
            DATA_CSV = filename
            
            # Update config file
            success = file_helper.update_config_file("DATA_CSV", filename)
            if success:
                messagebox.showinfo(
                    "Configuration Updated",
                    f"Data file has been set to: {filename}"
                )
            else:
                messagebox.showwarning(
                    "Configuration Warning",
                    f"Data file will be set to {filename} for this session, but the configuration file could not be updated."
                )
    
    def ensure_csv_exists(self):
        """Ensure the CSV file exists with proper headers"""
        try:
            if not os.path.exists(self.csv_filename):
                with open(self.csv_filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['timestamp', 'text'])
        except Exception as e:
            messagebox.showwarning(
                "File Access Warning",
                f"Could not create or access the data file: {e}\n\nEntries will be saved to temporary files until this is resolved."
            )
    
    def get_timestamp(self):
        """Get formatted timestamp"""
        now = datetime.now()
        weekday = now.strftime("%a").upper()
        return now.strftime(f"%Y-%m-%d {weekday} %H:%M:%S.%f")[:-4]

    def handle_input(self, event=None):
        """Handle user input"""
        input_text = self.input_var.get().strip()
        
        if not input_text:
            self.clear_feedback()
            return
        
        # Record timestamp for all inputs
        timestamp = self.get_timestamp()
        
        # Check if the input is a slash command
        if input_text.startswith(SLASH_PREFIX):
            # Remove prefix (either / or //)
            if input_text.startswith(SLASH_PREFIX_ALT):
                cmd_text = input_text[len(SLASH_PREFIX_ALT):]
            else:
                cmd_text = input_text[len(SLASH_PREFIX):]
                
            # Handle slash command
            if self.command_handler:
                self.command_handler.process_slash_command(cmd_text, timestamp)
            else:
                self.feedback_var.set("Command system is unavailable")
        
        # Check if the input is a token command
        elif input_text.startswith(TOKEN_PREFIX):
            # Remove prefix (either $ or $$)
            if input_text.startswith(TOKEN_PREFIX_ALT):
                token_text = input_text[len(TOKEN_PREFIX_ALT):].strip()
            else:
                token_text = input_text[len(TOKEN_PREFIX):].strip()
                
            # Handle token command
            if self.command_handler:
                self.command_handler.process_token_command(token_text, timestamp)
            else:
                self.feedback_var.set("Command system is unavailable")
        
        else:
            # Regular input - store in CSV
            self.write_to_csv(timestamp, input_text)
            self.clear_feedback()
        
        # Clear the input field
        self.input_var.set("")
    
    def clear_feedback(self):
        """Clear the feedback label"""
        self.feedback_var.set("")
    
    def add_periodic_newlines(self):
        """Add periodic empty entries to the CSV"""
        while not self.stop_thread.is_set():
            time.sleep(PERIODIC_ENTRIES_INTERVAL)
            
            if self.stop_thread.is_set():
                break
                
            # Add a timestamp with empty text
            timestamp = self.get_timestamp()
            self.write_to_csv(timestamp, "")
    
    def toggle_periodic_entries(self):
        """Toggle the periodic entries thread"""
        if self.periodic_var.get():
            # Start the thread if it's not running
            if self.newline_thread is None or not self.newline_thread.is_alive():
                self.stop_thread.clear()
                self.newline_thread = threading.Thread(target=self.add_periodic_newlines, daemon=True)
                self.newline_thread.start()
                self.feedback_var.set("Periodic time entries enabled")
        else:
            # Stop the thread if it's running
            if self.newline_thread and self.newline_thread.is_alive():
                self.stop_thread.set()
                self.feedback_var.set("Periodic time entries disabled")
    
    def write_to_csv(self, timestamp, text):
        """
        Write an entry to the CSV file with enhanced error handling.
        Falls back to creating unique temporary files in the temp directory.
        """
        try:
            # First, try to recover any entries from temp files
            self.recover_temp_entries()
            
            # Try to write to main CSV
            with open(self.csv_filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([timestamp, text])
            
            # If we get here, writing was successful
            return True
            
        except Exception as e:
            # If writing to main CSV fails, use a unique temp file
            try:
                temp_filepath = file_helper.get_temp_filepath()
                
                with open(temp_filepath, 'w', newline='') as temp_file:
                    temp_writer = csv.writer(temp_file)
                    temp_writer.writerow(['timestamp', 'text'])  # Header
                    temp_writer.writerow([timestamp, text])
                
                self.feedback_var.set(f"Entry saved to temporary storage. Main file ({DATA_CSV}) is unavailable.")
                
                # Show a more detailed error message
                messagebox.showwarning(
                    "Data Storage Warning",
                    f"Could not write to the main data file: {e}\n\n"
                    f"Your entry has been saved to a temporary file in the 'temp' directory.\n"
                    f"The application will attempt to merge these files when the main file becomes available."
                )
                
                return False
                
            except Exception as e2:
                # Both main file and temp directory are inaccessible
                self.feedback_var.set("WARNING: Could not save entry to any storage location!")
                
                messagebox.showerror(
                    "Critical Storage Error",
                    f"Failed to write to both main and temporary storage: {e2}\n\n"
                    f"Your data could not be saved. Please check file permissions and disk space."
                )
                
                return False
    
    def recover_temp_entries(self):
        """
        Attempt to recover entries from temporary files in the temp directory
        and merge them into the main CSV file.
        """
        try:
            # Check if temp directory exists
            if not os.path.exists(self.temp_dir):
                return
            
            # Get all CSV files in the temp directory
            temp_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.csv')]
            
            if not temp_files:
                return
            
            # Keep track of the number of recovered entries
            total_recovered = 0
            recovered_files = 0
            
            # Process each temp file
            for temp_file in temp_files:
                temp_filepath = os.path.join(self.temp_dir, temp_file)
                
                try:
                    # Read the temp file
                    temp_df = pd.read_csv(temp_filepath)
                    
                    if temp_df.empty:
                        # Remove empty temp files
                        os.remove(temp_filepath)
                        continue
                    
                    # Write the entries to the main CSV
                    with open(self.csv_filename, 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        
                        for _, row in temp_df.iterrows():
                            writer.writerow([row['timestamp'], row['text']])
                            total_recovered += 1
                    
                    # Remove the temp file after successful recovery
                    os.remove(temp_filepath)
                    recovered_files += 1
                    
                except Exception:
                    # Skip files that can't be processed
                    continue
            
            # Show feedback if entries were recovered
            if total_recovered > 0:
                self.feedback_var.set(f"Recovered {total_recovered} entries from {recovered_files} temporary files")
                
        except Exception:
            # If recovery fails, just continue without error
            pass
    
    def on_close(self):
        """Handle window close event"""
        # Stop the periodic newline thread if running
        if self.newline_thread and self.newline_thread.is_alive():
            self.stop_thread.set()
            self.newline_thread.join(1.0)  # Wait up to 1 second for thread to finish
        
        # Try to recover any temp entries before closing
        try:
            self.recover_temp_entries()
        except:
            pass
        
        # Close the window
        self.root.destroy()
    
    def run(self):
        """Start the main event loop"""
        self.root.mainloop()

if __name__ == "__main__":
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