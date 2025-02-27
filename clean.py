import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
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

class ZCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Z Cleaner")
        self.root.geometry("400x300")
        
        # Handle config errors by prompting user if needed
        if 'CONFIG_ERROR' in globals():
            self.handle_config_error(CONFIG_ERROR)
        
        # Get the directory where the script is located
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.csv_filename = os.path.join(self.script_dir, DATA_CSV)
        
        # Main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and description
        title_label = ttk.Label(
            main_frame, 
            text="Z CSV Cleaner",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        desc_label = ttk.Label(
            main_frame,
            text=f"This tool will remove all empty rows from the {DATA_CSV} file.",
            wraplength=350
        )
        desc_label.pack(pady=(0, 20))
        
        # Status display
        self.status_frame = ttk.LabelFrame(main_frame, text="Status", padding=10)
        self.status_frame.pack(fill=tk.X, pady=10)
        
        self.status_text = tk.Text(self.status_frame, height=6, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.analyze_button = ttk.Button(
            button_frame,
            text="Analyze CSV",
            command=self.analyze_csv
        )
        self.analyze_button.pack(side=tk.LEFT, padx=5)
        
        self.clean_button = ttk.Button(
            button_frame,
            text="Clean CSV",
            command=self.clean_csv,
            state=tk.DISABLED
        )
        self.clean_button.pack(side=tk.LEFT, padx=5)
        
        # Add backup option
        self.backup_var = tk.BooleanVar(value=True)
        self.backup_check = ttk.Checkbutton(
            main_frame,
            text="Create backup before cleaning",
            variable=self.backup_var
        )
        self.backup_check.pack(anchor=tk.W, pady=5)
        
        # Statistics
        self.stats = {
            "total": 0,
            "empty": 0
        }
        
        # Initial setup
        self.check_csv_exists()
    
    def handle_config_error(self, error_message):
        """Handle configuration errors by prompting the user for information"""
        self.root.title("Z Cleaner - Configuration Setup")
        
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
    
    def check_csv_exists(self):
        """Check if the CSV file exists and update UI accordingly"""
        if not os.path.exists(self.csv_filename):
            self.log_message(f"Error: CSV file not found at {self.csv_filename}")
            self.log_message("Please create the file or specify a new filename.")
            
            # Prompt user to create a new file or specify a different one
            response = messagebox.askquestion(
                "File Not Found",
                f"The data file '{DATA_CSV}' was not found.\nWould you like to create it now?",
                icon='warning'
            )
            
            if response == 'yes':
                try:
                    # Create empty CSV with headers
                    with open(self.csv_filename, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['timestamp', 'text'])
                    
                    self.log_message(f"Created new CSV file: {DATA_CSV}")
                    return True
                except Exception as e:
                    self.log_message(f"Error creating CSV file: {str(e)}")
                    
                    # If creation fails, ask user for a new filename
                    messagebox.showerror(
                        "File Creation Error",
                        f"Could not create file: {e}\n\nPlease select a different filename."
                    )
                    
                    # Prompt for new filename
                    new_filename = file_helper.prompt_for_filename(
                        self.root,
                        "Select New Data File",
                        "Please enter a name for your data file:"
                    )
                    
                    if new_filename:
                        # Update global and instance variables
                        global DATA_CSV
                        DATA_CSV = new_filename
                        self.csv_filename = os.path.join(self.script_dir, new_filename)
                        
                        # Update config file
                        file_helper.update_config_file("DATA_CSV", new_filename)
                        
                        # Try to create the new file
                        try:
                            with open(self.csv_filename, 'w', newline='') as csvfile:
                                writer = csv.writer(csvfile)
                                writer.writerow(['timestamp', 'text'])
                            
                            self.log_message(f"Created new CSV file: {new_filename}")
                            return True
                        except Exception as e2:
                            self.log_message(f"Error creating new CSV file: {str(e2)}")
                            self.analyze_button.config(state=tk.DISABLED)
                            return False
                    else:
                        # User canceled
                        self.analyze_button.config(state=tk.DISABLED)
                        return False
            else:
                # User chose not to create a file
                self.analyze_button.config(state=tk.DISABLED)
                return False
        
        return True
    
    def log_message(self, message):
        """Add a message to the status text box"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
    
    def analyze_csv(self):
        """Analyze the CSV file and count empty rows"""
        if not self.check_csv_exists():
            return
        
        try:
            # Clear the status
            self.status_text.delete(1.0, tk.END)
            self.log_message("Analyzing CSV file...")
            
            # Read the CSV
            df = pd.read_csv(self.csv_filename)
            
            # Count total rows
            total_rows = len(df)
            
            # Count empty rows (where text is empty or NaN)
            empty_rows = df['text'].isna().sum() + (df['text'] == '').sum()
            
            # Update stats
            self.stats["total"] = total_rows
            self.stats["empty"] = empty_rows
            
            # Show results
            self.log_message(f"Total rows: {total_rows}")
            self.log_message(f"Empty rows: {empty_rows}")
            self.log_message(f"Non-empty rows: {total_rows - empty_rows}")
            
            if empty_rows > 0:
                self.log_message("\nReady to clean. Click 'Clean CSV' to remove empty rows.")
                self.clean_button.config(state=tk.NORMAL)
            else:
                self.log_message("\nNo empty rows found. No cleaning needed.")
                self.clean_button.config(state=tk.DISABLED)
                
        except Exception as e:
            self.log_message(f"Error analyzing CSV: {str(e)}")
            
            # More detailed error handling
            if "No such file or directory" in str(e):
                self.log_message("The CSV file no longer exists or was moved.")
                self.check_csv_exists()  # Re-check and possibly recreate
            elif "Permission denied" in str(e):
                self.log_message("Permission denied when trying to access the file.")
                messagebox.showwarning(
                    "Permission Error",
                    f"Cannot access {DATA_CSV}. The file may be in use by another program or you don't have permission to access it."
                )
            else:
                # Generic error handling
                messagebox.showerror("Analysis Error", f"An error occurred while analyzing the CSV: {e}")
            
            self.clean_button.config(state=tk.DISABLED)
    
    def clean_csv(self):
        """Remove empty rows from the CSV file"""
        if not self.check_csv_exists():
            return
            
        try:
            # Create backup if option is selected
            if self.backup_var.get():
                backup_filename = f"{self.csv_filename}.backup"
                import shutil
                shutil.copy2(self.csv_filename, backup_filename)
                self.log_message(f"Backup created: {os.path.basename(backup_filename)}")
            
            # Read the CSV
            df = pd.read_csv(self.csv_filename)
            
            # Record the original row count
            original_count = len(df)
            
            # Filter out empty rows
            df_cleaned = df[df['text'].notna() & (df['text'] != '')]
            
            # Count rows removed
            rows_removed = original_count - len(df_cleaned)
            
            # Save the cleaned DataFrame back to the CSV
            df_cleaned.to_csv(self.csv_filename, index=False)
            
            # Show results
            self.log_message(f"Cleaning complete. Removed {rows_removed} empty rows.")
            self.log_message(f"CSV file now has {len(df_cleaned)} rows.")
            
            # Disable the clean button (need to analyze again before cleaning)
            self.clean_button.config(state=tk.DISABLED)
            
            # Show success message
            messagebox.showinfo(
                "Cleaning Complete", 
                f"Successfully removed {rows_removed} empty rows from the CSV file."
            )
            
        except Exception as e:
            self.log_message(f"Error cleaning CSV: {str(e)}")
            
            # More detailed error handling
            if "Permission denied" in str(e):
                messagebox.showwarning(
                    "Permission Error",
                    f"Cannot modify {DATA_CSV}. The file may be in use by another program or you don't have permission to modify it."
                )
            else:
                messagebox.showerror("Cleaning Error", f"An error occurred while cleaning: {str(e)}")

def main():
    try:
        root = tk.Tk()
        app = ZCleanerApp(root)
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
    import csv
    main()