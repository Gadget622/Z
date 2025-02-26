import re
import os
import csv
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

# Import configuration from config module
try:
    from config import DATA_CSV
except ImportError:
    # Fallback defaults if config module is missing
    DATA_CSV = "Z data.csv"

class ZImporter:
    def __init__(self, root):
        self.root = root
        self.root.title("Z Import Tool")
        self.root.geometry("500x300")
        
        # Configure the grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)
        
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
            # Get the directory of the script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            csv_filename = os.path.join(script_dir, DATA_CSV)
            
            # Check if CSV exists, create it if not
            csv_exists = os.path.exists(csv_filename)
            
            # Read the text file
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
                
            # Sort entries if option is selected
            sort_entries = self.sort_var.get()
            if sort_entries:
                self.log("Sorting entries by timestamp...")
                
                # If CSV already exists, read it first
                if csv_exists:
                    try:
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
                        # Fallback to creating new file
                        csv_exists = False
                
                # If CSV doesn't exist or couldn't be read, create new
                if not csv_exists:
                    entries.sort(key=lambda x: x[0])  # Sort by timestamp
                    
                    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['timestamp', 'text'])  # Header
                        writer.writerows(entries)
                    
                    self.log(f"Created new CSV file with {len(entries)} sorted entries")
            else:
                # Append to existing or create new without sorting
                mode = 'a' if csv_exists else 'w'
                with open(csv_filename, mode, newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header if new file
                    if not csv_exists:
                        writer.writerow(['timestamp', 'text'])
                        
                    writer.writerows(entries)
                
                self.log(f"Added {len(entries)} entries to CSV (unsorted)")
            
            # Update status
            valid_count = len(entries)
            self.status_label.config(text=f"Imported {valid_count} entries ({skipped} skipped)")
            
            messagebox.showinfo("Import Complete", 
                            f"Successfully imported {valid_count} entries to Z data.csv")
            
        except Exception as e:
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Import Error", str(e))

def main():
    root = tk.Tk()
    app = ZImporter(root)
    root.mainloop()

if __name__ == "__main__":
    main()