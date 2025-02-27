import re
import os
import csv
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import sys

# Import helper for file operations
try:
    import file_helper
except ImportError:
    # Display error in a tkinter dialog
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Module Error",
        "Failed to import file_helper module.\n\nPlease ensure file_helper.py exists in the application directory."
    )
    root.destroy()
    sys.exit(1)

# Import configuration from config module
try:
    from config import DATA_CSV, ConfigError
except ImportError:
    # Display error in a tkinter dialog
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Configuration Error",
        "Failed to import configuration module.\n\nPlease ensure config.py exists in the application directory."
    )
    root.destroy()
    sys.exit(1)
except ConfigError as e:
    # Display the specific config error in a tkinter dialog
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Configuration Error",
        f"{e}\n\nThe application will now prompt for the necessary information."
    )
    # Will handle by prompting user for configuration
    CONFIG_ERROR = str(e)
    root.deiconify()  # Show the root for user input

class ZImporter:
    def __init__(self, root):
        self.root = root
        self.root.title("Z Import Tool")
        self.root.geometry("500x300")
        
        # Handle config errors by prompting user if needed
        if 'CONFIG_ERROR' in globals():
            self.handle_config_error(CONFIG_ERROR)
        
        # Configure the grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)
        
        # Get the directory where the script is located
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # File selection
        self.file_frame = ttk.Frame(root, padding="10")
        self.file_frame.grid(row=0, column=0, sticky="ew")
        
        self.file_label = ttk.Label(self.file_frame, text="No file selected")
        self.file_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.browse_button = ttk.Button(self.file_frame, text="Browse...", command=self.browse_file)
        self.browse_button.pack(side=tk.RIGHT)
        
        # Sort option
        self.sort_frame = ttk.Frame(root, padding="10")
        self.sort_frame.grid(row=1, column=0, sticky="ew")
        
        self.sort_var = tk.BooleanVar(value=True)
        self.sort_check = ttk.Checkbutton(
            self.sort_frame, 
            text="Sort entries by timestamp",
            variable=self.sort_var
        )
        self.sort_check.pack(side=tk.LEFT)
        
        # Status display
        self.status_frame = ttk.Frame(root, padding="10")
        self.status_frame.grid(row=2, column=0, sticky="ew")
        
        self.status_label = ttk.Label(self.status_frame, text="Ready to import")
        self.status_label.pack(side=tk.LEFT)
        
        # Log display
        self.log_frame = ttk.Frame(root, padding="10")
        self.log_frame.grid(row=3, column=0, sticky="nsew")
        
        self.log_text = tk.Text(self.log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Import button
        self.import_button = ttk.Button(
            root, 
            text="Import", 
            command=self.import_data,
            state=tk.DISABLED
        )
        self.import_button.grid(row=4, column=0, pady=10)
        
        # File path
        self.file_path = None
        
    def handle_config_error(self, error_message):
        """Handle configuration errors by prompting the user for information"""
        self.root.title("Z Importer - Configuration Setup")
        
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
        
    def browse_file(self):
        """Open file dialog to select a text file"""
        file_path = filedialog.askopenfilename(
            title="Select Text File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            self.file_path = file_path
            self.file_label.config(text=os.path.basename(file_path))
            self.import_button.config(state=tk.NORMAL)
            self.log("File selected: " + file_path)
    
    def log(self, message):
        """Add message to log display"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
    
    def import_data(self):
        """Process the selected file and import data to CSV"""
        if not self.file_path:
            return
        
        try:
            # Get the output CSV path
            csv_filename = os.path.join(self.script_dir, DATA_CSV)
            
            # Check if CSV exists, create it if not
            csv_exists = os.path.exists(csv_filename)
            if not csv_exists:
                try:
                    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['timestamp', 'text'])
                    self.log(f"Created new CSV file: {DATA_CSV}")
                    csv_exists = True
                except Exception as e:
                    self.log(f"Error creating CSV file: {str(e)}")
                    
                    # Handle file creation error
                    response = messagebox.askquestion(
                        "File Creation Error",
                        f"Could not create file {DATA_CSV}: {e}\n\nWould you like to specify a different filename?",
                        icon='warning'
                    )
                    
                    if response == 'yes':
                        new_filename = file_helper.prompt_for_filename(
                            self.root,
                            "Select New Data File",
                            "Please enter a name for your data file:"
                        )
                        
                        if new_filename:
                            # Update global variable
                            global DATA_CSV
                            DATA_CSV = new_filename
                            
                            # Update config file
                            file_helper.update_config_file("DATA_CSV", new_filename)
                            
                            # Update csv_filename
                            csv_filename = os.path.join(self.script_dir, new_filename)
                            
                            # Try to create the new file
                            try:
                                with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerow(['timestamp', 'text'])
                                
                                self.log(f"Created new CSV file: {new_filename}")
                                csv_exists = True
                            except Exception as e2:
                                self.log(f"Error creating new CSV file: {str(e2)}")
                                return
                        else:
                            # User canceled
                            return
                    else:
                        # User chose not to specify new filename
                        return
            
            # Read the text file
            self.log(f"Reading input file: {self.file_path}")
            with open(self.file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Parse lines using regex
            # Format: 2025-02-22 SAT 18:21:52.25 ~ text content
            pattern = r'^(\d{4}-\d{2}-\d{2}\s+[A-Z]{3}\s+\d{2}:\d{2}:\d{2}\.\d{2})\s+~\s+(.+)$'
            
            entries = []
            skipped = 0
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                    
                match = re.match(pattern, line)
                if match:
                    timestamp = match.group(1)
                    text = match.group(2)
                    entries.append([timestamp, text])
                    self.log(f"Line {line_num}: Parsed successfully")
                else:
                    skipped += 1
                    self.log(f"Line {line_num}: Invalid format, skipped")
            
            if not entries:
                messagebox.showwarning("No Valid Entries", "No valid entries found in the file.")
                return
            
            # Process entries based on sort option
            valid_count = len(entries)
            self.log(f"Found {valid_count} valid entries to import")
            
            # Create a temp directory for backups
            temp_dir = file_helper.setup_temp_directory()
            
            # Sort entries if option is selected
            sort_entries = self.sort_var.get()
            if sort_entries:
                self.log("Sorting entries by timestamp...")
                
                try:
                    # If CSV already exists, read it first
                    if csv_exists:
                        try:
                            # Create a backup of the original file
                            backup_filename = os.path.join(temp_dir, f"backup_{DATA_CSV}_{file_helper.generate_temp_filename()}")
                            import shutil
                            shutil.copy2(csv_filename, backup_filename)
                            self.log(f"Created backup at: {backup_filename}")
                            
                            # Read existing file
                            df_existing = pd.read_csv(csv_filename)
                            
                            # Convert entries to DataFrame
                            df_new = pd.DataFrame(entries, columns=['timestamp', 'text'])
                            
                            # Combine existing and new data
                            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                            
                            # Sort by timestamp
                            df_combined = df_combined.sort_values('timestamp')
                            
                            # Write back to CSV
                            df_combined.to_csv(csv_filename, index=False)
                            
                            self.log(f"Added {len(entries)} entries to existing CSV file")
                            self.log(f"Total entries after import: {len(df_combined)}")
                            
                        except Exception as e:
                            self.log(f"Error processing existing CSV: {str(e)}")
                            
                            # Try to use a temp file if the main file is inaccessible
                            temp_filepath = os.path.join(temp_dir, file_helper.generate_temp_filename())
                            
                            df_new = pd.DataFrame(entries, columns=['timestamp', 'text'])
                            df_new = df_new.sort_values('timestamp')
                            df_new.to_csv(temp_filepath, index=False)
                            
                            self.log(f"Could not update main CSV file. Data saved to: {temp_filepath}")
                            messagebox.showwarning(
                                "Import Warning",
                                f"Could not update the main CSV file ({DATA_CSV}). Your imported data has been saved to a temporary file."
                            )
                            return
                    else:
                        # If CSV doesn't exist or couldn't be read, create new
                        entries.sort(key=lambda x: x[0])  # Sort by timestamp
                        
                        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow(['timestamp', 'text'])  # Header
                            writer.writerows(entries)
                        
                        self.log(f"Created new CSV file with {len(entries)} sorted entries")
                except Exception as e:
                    self.log(f"Error during import: {str(e)}")
                    
                    # Save to temp file as last resort
                    temp_filepath = os.path.join(temp_dir, file_helper.generate_temp_filename())
                    
                    try:
                        with open(temp_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow(['timestamp', 'text'])  # Header
                            writer.writerows(sorted(entries, key=lambda x: x[0]))
                        
                        self.log(f"Error importing to main file. Data saved to: {temp_filepath}")
                        messagebox.showwarning(
                            "Import Warning",
                            f"An error occurred during import: {e}\n\nYour data has been saved to a temporary file."
                        )
                    except Exception as e2:
                        self.log(f"Critical error: {str(e2)}")
                        messagebox.showerror(
                            "Critical Error",
                            f"Failed to save data to any location: {e2}\n\nYour data could not be imported."
                        )
                    return
            else:
                # Append to existing or create new without sorting
                try:
                    mode = 'a' if csv_exists else 'w'
                    with open(csv_filename, mode, newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        
                        # Write header if new file
                        if not csv_exists:
                            writer.writerow(['timestamp', 'text'])
                            
                        writer.writerows(entries)
                    
                    self.log(f"Added {len(entries)} entries to CSV (unsorted)")
                except Exception as e:
                    self.log(f"Error during import: {str(e)}")
                    
                    # Save to temp file as last resort
                    temp_filepath = os.path.join(temp_dir, file_helper.generate_temp_filename())
                    
                    try:
                        with open(temp_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow(['timestamp', 'text'])  # Header
                            writer.writerows(entries)
                        
                        self.log(f"Error importing to main file. Data saved to: {temp_filepath}")
                        messagebox.showwarning(
                            "Import Warning",
                            f"An error occurred during import: {e}\n\nYour data has been saved to a temporary file."
                        )
                    except Exception as e2:
                        self.log(f"Critical error: {str(e2)}")
                        messagebox.showerror(
                            "Critical Error",
                            f"Failed to save data to any location: {e2}\n\nYour data could not be imported."
                        )
                    return
            
            # Update status
            self.status_label.config(text=f"Imported {valid_count} entries ({skipped} skipped)")
            
            messagebox.showinfo(
                "Import Complete", 
                f"Successfully imported {valid_count} entries to {DATA_CSV}"
            )
            
        except Exception as e:
            self.log(f"Unexpected error: {str(e)}")
            messagebox.showerror("Import Error", str(e))

def main():
    try:
        root = tk.Tk()
        app = ZImporter(root)
        root.mainloop()
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