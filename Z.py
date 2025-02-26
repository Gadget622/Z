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

# Import configuration from config module
try:
    from config import (
        DATA_CSV, TEMP_CSV, 
        PERIODIC_ENTRIES_ENABLED, PERIODIC_ENTRIES_INTERVAL,
        SLASH_PREFIX, SLASH_PREFIX_ALT, 
        TOKEN_PREFIX, TOKEN_PREFIX_ALT
    )
except ImportError:
    # Fallback defaults if config module is missing
    DATA_CSV = "Z data.csv"
    TEMP_CSV = "temp.csv"
    PERIODIC_ENTRIES_ENABLED = False
    PERIODIC_ENTRIES_INTERVAL = 5
    SLASH_PREFIX = "/"
    SLASH_PREFIX_ALT = "//"
    TOKEN_PREFIX = "$"
    TOKEN_PREFIX_ALT = "$$"

# Import command handler
try:
    from commands import CommandHandler
except ImportError:
    # Will handle this in __init__
    CommandHandler = None

class ZApp:
    def __init__(self):
        # "accesses or creates (if it doesn't already exist) a .txt file in the same directory called 'Z.txt'"
        # Updated to use CSV instead of TXT
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # CSV file for storing data
        self.csv_filename = os.path.join(script_dir, DATA_CSV)
        self.temp_csv_filename = os.path.join(script_dir, TEMP_CSV)
        
        # Create CSV file with headers if it doesn't exist
        if not os.path.exists(self.csv_filename):
            try:
                with open(self.csv_filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['timestamp', 'text'])
            except Exception as e:
                print(f"Could not create main CSV file: {e}")
                
        # Create temp CSV file with headers if it doesn't exist
        if not os.path.exists(self.temp_csv_filename):
            try:
                with open(self.temp_csv_filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['timestamp', 'text'])
            except Exception as e:
                print(f"Could not create temp CSV file: {e}")
            
        # "Perpetually have a prompt window open for the user outside of the terminal"
        self.root = tk.Tk()
        self.root.title("Z")
        
        # Configure window to be resizable
        self.root.resizable(True, True)
        
        # Configure grid weights to enable responsive resizing
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Create the input interface
        self.frame = ttk.Frame(self.root, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure frame grid weights
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        
        # "allows the user to input a token of arbitrary length from their keyboard"
        self.input_var = tk.StringVar()
        self.input_field = ttk.Entry(self.frame, textvariable=self.input_var)
        self.input_field.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.input_field.focus()
        
        # Add a feedback label for command results
        self.feedback_var = tk.StringVar()
        self.feedback_label = ttk.Label(self.frame, textvariable=self.feedback_var, foreground="blue")
        self.feedback_label.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Initialize periodic entries variable (hidden from UI)
        self.periodic_var = tk.BooleanVar(value=PERIODIC_ENTRIES_ENABLED)
        
        # Note: Settings frame and checkbox are hidden from UI
        # but the functionality remains in the code for future use
        
        # If periodic entries are enabled in config, start the thread
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
        
        # "When the user presses ENTER"
        self.root.bind('<Return>', self.handle_input)

    def get_timestamp(self):
        # "timestamp in the format specified"
        now = datetime.now()
        weekday = now.strftime("%a").upper()
        return now.strftime(f"%Y-%m-%d {weekday} %H:%M:%S.%f")[:-4]

    def handle_input(self, event=None):
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
        # "automatically add a newline character to the .txt file every five seconds"
        # Now adding empty entries to CSV instead of newlines to text file
        while not self.stop_thread.is_set():
            time.sleep(PERIODIC_ENTRIES_INTERVAL)  # Using interval from config
            
            if self.stop_thread.is_set():
                break
                
            # Add a timestamp with empty text
            timestamp = self.get_timestamp()
            self.write_to_csv(timestamp, "")
    
    def toggle_periodic_entries(self):
        """Toggle the periodic entries thread based on checkbox state"""
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
        Write an entry to the CSV file with error handling.
        Attempts to write to the main CSV first, falls back to temp CSV if needed.
        Also handles transferring data from temp to main when possible.
        """
        try:
            # First check if we have pending entries in temp.csv
            temp_entries = []
            if os.path.exists(self.temp_csv_filename):
                try:
                    # Check if temp file has content
                    temp_size = os.path.getsize(self.temp_csv_filename)
                    if temp_size > 10:  # More than just header
                        temp_df = pd.read_csv(self.temp_csv_filename)
                        if not temp_df.empty:
                            temp_entries = temp_df.values.tolist()
                except Exception:
                    # If we can't read temp file, just continue
                    pass
            
            # Try to write to main CSV
            with open(self.csv_filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # If we have temp entries, write them first
                if temp_entries:
                    for entry in temp_entries:
                        writer.writerow(entry)
                    
                    # Clear temp file
                    with open(self.temp_csv_filename, 'w', newline='') as temp_file:
                        temp_writer = csv.writer(temp_file)
                        temp_writer.writerow(['timestamp', 'text'])
                    
                    # Give feedback about recovery
                    self.feedback_var.set(f"Recovered {len(temp_entries)} entries from temporary storage")
                
                # Write the current entry
                writer.writerow([timestamp, text])
            
            # If we get here, writing to main CSV was successful
            return True
            
        except Exception as e:
            # If writing to main CSV fails, use temp CSV
            try:
                with open(self.temp_csv_filename, 'a', newline='') as temp_file:
                    temp_writer = csv.writer(temp_file)
                    temp_writer.writerow([timestamp, text])
                
                self.feedback_var.set("Entry saved to temporary storage (Z data.csv unavailable)")
                return False
                
            except Exception as e2:
                # Both files are inaccessible
                self.feedback_var.set("Warning: Could not save entry to any storage")
                return False

    def run(self):
        """Start the main event loop"""
        self.root.mainloop()

if __name__ == "__main__":
    import sys
    app = ZApp()
    app.run()