import pandas as pd
import os
import sys
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog

# Import helper for file operations
try:
    import file_helper
except ImportError:
    # Can't use tkinter if running as a script, so just print error
    print("Error: file_helper.py module not found.")
    sys.exit(1)

# Import configuration from config module
try:
    from config import DATA_CSV, TEMP_TXT, TIME_INTERVAL, ConfigError
except ImportError:
    print("Error: config.py module not found.")
    sys.exit(1)
except ConfigError as e:
    # Handle config error when running as a script
    print(f"Configuration error: {e}")
    
    # Try to handle this with a GUI if possible
    try:
        root = tk.Tk()
        root.withdraw()
        
        if "DATA_CSV" in str(e):
            # Ask user for a data filename
            filename = file_helper.prompt_for_filename(
                root,
                "Data File Configuration",
                "Please enter a name for your data file:"
            )
            
            if filename:
                # Update global variable for this session
                DATA_CSV = filename  # This is now a local assignment first
                globals()['DATA_CSV'] = filename  # This updates the global variable
                
                # Try to update the config file
                file_helper.update_config_file("DATA_CSV", filename)
                print(f"Set data file to: {filename}")
            else:
                print("No filename provided. Exiting.")
                root.destroy()
                sys.exit(1)
        
        if "TEMP_TXT" in str(e):
            # Default to a reasonable value
            TEMP_TXT = "Z temp.txt"
            print(f"Using default temp file: {TEMP_TXT}")
        
        if "TIME_INTERVAL" in str(e):
            # Default to 10 seconds
            TIME_INTERVAL = 10
            print(f"Using default time interval: {TIME_INTERVAL} seconds")
        
        root.destroy()
    except:
        print("Please run the main Z application to configure the system.")
        sys.exit(1)

def generate_temp_file(csv_filename=None, output_filename=None, time_interval=None):
    """
    Generate a temporary text file from CSV data, adding newlines based on the time difference
    between timestamps.
    
    Parameters:
    - csv_filename: Name of the CSV file containing timestamp and text data
    - output_filename: Name of the output text file
    - time_interval: Time interval in seconds for adding newlines between entries
    
    Returns:
    - bool: True if successful, False otherwise
    - str: Path to the output file or error message
    """
    """
    Generate a temporary text file from CSV data, adding newlines based on the time difference
    between timestamps.
    
    Parameters:
    - csv_filename: Name of the CSV file containing timestamp and text data
    - output_filename: Name of the output text file
    - time_interval: Time interval in seconds for adding newlines between entries
    """
    # Use parameters or defaults from config
    csv_filename = csv_filename or DATA_CSV
    output_filename = output_filename or TEMP_TXT
    time_interval = time_interval or TIME_INTERVAL
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, csv_filename)
    output_path = os.path.join(script_dir, output_filename)
    
    # Check if CSV file exists
    if not os.path.exists(csv_path):
        error_msg = f"Error: CSV file '{csv_filename}' not found."
        print(error_msg)
        
        # Create a popup if run from GUI
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("File Not Found", error_msg)
            root.destroy()
        except:
            pass
        
        return
    
    # Read CSV file using pandas
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        error_msg = f"Error reading CSV file: {e}"
        print(error_msg)
        
        # Create a popup if run from GUI
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Read Error", error_msg)
            root.destroy()
        except:
            pass
        
        return
    
    # Create temp directory for potential backups
    temp_dir = file_helper.setup_temp_directory()
    
    # Create backup of original file
    try:
        import shutil
        backup_filename = os.path.join(temp_dir, f"backup_{os.path.basename(csv_path)}_{file_helper.generate_temp_filename()}")
        shutil.copy2(csv_path, backup_filename)
        print(f"Created backup at: {backup_filename}")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")
    
    # Filter out rows with empty text
    df = df[df['text'].notna() & (df['text'] != '')]
    
    if df.empty:
        print("No text entries found in the CSV file.")
        try:
            with open(output_path, 'w') as f:
                pass  # Create empty file
            print(f"Created empty output file: {output_filename}")
        except Exception as e:
            print(f"Error creating output file: {e}")
        return
    
    # Parse timestamps
    def parse_timestamp(ts_str):
        try:
            # Format: "2025-02-24 MON 14:30:45.123"
            # Remove weekday abbreviation
            parts = ts_str.split()
            date_part = parts[0]
            time_part = parts[2]
            # Parse as datetime
            return datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S.%f")
        except Exception:
            # Return None if parsing fails
            return None
    
    df['datetime'] = df['timestamp'].apply(parse_timestamp)
    
    # Remove rows with invalid timestamps
    df = df[df['datetime'].notna()]
    
    if df.empty:
        print("No valid timestamps found in the CSV file.")
        try:
            with open(output_path, 'w') as f:
                pass  # Create empty file
            print(f"Created empty output file: {output_filename}")
        except Exception as e:
            print(f"Error creating output file: {e}")
        return
    
    # Process the entries and create the temp file
    # "for a configurable length of time (10 seconds by default), for however many whole multiples of ten 
    # two timestamps are separated, include one enter between the two pieces of text in the outputted text document"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            prev_time = None
            
            for i, row in df.iterrows():
                text = row['text']
                curr_time = row['datetime']
                
                # Skip entries with invalid timestamps (should be filtered out already)
                if curr_time is None:
                    continue
                
                # Add newlines based on time difference
                if prev_time is not None:
                    time_diff = (curr_time - prev_time).total_seconds()
                    newlines = int(time_diff // time_interval)
                    f.write('\n' * newlines)
                
                # Write the text
                f.write(text)
                prev_time = curr_time
        
        print(f"Successfully created '{output_filename}'")
        
        # Show success message if run from GUI
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("Success", f"Successfully created '{output_filename}'")
            root.destroy()
        except:
            pass
            
    except Exception as e:
        error_msg = f"Error writing output file: {e}"
        print(error_msg)
        
        # Try writing to a temporary file instead if the main file fails
        try:
            temp_output_path = os.path.join(temp_dir, f"temp_output_{file_helper.generate_temp_filename()}.txt")
            
            with open(temp_output_path, 'w', encoding='utf-8') as f:
                prev_time = None
                
                for i, row in df.iterrows():
                    text = row['text']
                    curr_time = row['datetime']
                    
                    if curr_time is None:
                        continue
                    
                    if prev_time is not None:
                        time_diff = (curr_time - prev_time).total_seconds()
                        newlines = int(time_diff // time_interval)
                        f.write('\n' * newlines)
                    
                    f.write(text)
                    prev_time = curr_time
            
            print(f"Saved output to temporary file: {temp_output_path}")
            
            # Show warning message if run from GUI
            try:
                root = tk.Tk()
                root.withdraw()
                messagebox.showwarning(
                    "File Access Warning",
                    f"Could not write to '{output_filename}'. Output saved to: {temp_output_path}"
                )
                root.destroy()
            except:
                pass
                
        except Exception as e2:
            print(f"Critical error: Could not write to any output file: {e2}")
            
            # Show error message if run from GUI
            try:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror(
                    "Critical Error",
                    f"Failed to create output file in any location: {e2}"
                )
                root.destroy()
            except:
                pass