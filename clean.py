import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox

# Import configuration from config module
try:
    from config import DATA_CSV
except ImportError:
    # Fallback defaults if config module is missing
    DATA_CSV = "Z data.csv"

class ZCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Z Cleaner")
        self.root.geometry("400x300")
        
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
            text="This tool will remove all empty rows from the Z data.csv file.",
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
    
    def check_csv_exists(self):
        """Check if the CSV file exists and update UI accordingly"""
        if not os.path.exists(self.csv_filename):
            self.log_message(f"Error: CSV file not found at {self.csv_filename}")
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
            messagebox.showerror("Error", f"An error occurred while cleaning: {str(e)}")

def main():
    root = tk.Tk()
    app = ZCleanerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()