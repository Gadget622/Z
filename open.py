import pandas as pd
import os
from datetime import datetime

# Import configuration from config module
try:
    from config import DATA_CSV, TEMP_TXT, TIME_INTERVAL
except ImportError:
    # Fallback defaults if config module is missing
    DATA_CSV = "Z data.csv"
    TEMP_TXT = "Z temp.txt"
    TIME_INTERVAL = 10

def generate_temp_file(csv_filename=DATA_CSV, output_filename=TEMP_TXT, time_interval=TIME_INTERVAL):
    """
    Generate a temporary text file from CSV data, adding newlines based on the time difference
    between timestamps.
    
    Parameters:
    - csv_filename: Name of the CSV file containing timestamp and text data
    - output_filename: Name of the output text file
    - time_interval: Time interval in seconds for adding newlines between entries (default: 10 seconds)
    """
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, csv_filename)
    output_path = os.path.join(script_dir, output_filename)
    
    # Check if CSV file exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_filename}' not found.")
        return
    
    # Read CSV file using pandas
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Filter out rows with empty text
    df = df[df['text'].notna() & (df['text'] != '')]
    
    if df.empty:
        print("No text entries found in the CSV file.")
        with open(output_path, 'w') as f:
            pass  # Create empty file
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
    
    # Process the entries and create the temp file
    # "for a configurable length of time (10 seconds by default), for however many whole multiples of ten 
    # two timestamps are separated, include one enter between the two pieces of text in the outputted text document"
    with open(output_path, 'w') as f:
        prev_time = None
        
        for i, row in df.iterrows():
            text = row['text']
            curr_time = row['datetime']
            
            # Skip entries with invalid timestamps
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

if __name__ == "__main__":
    # Default parameters
    generate_temp_file()
    
    # You can also call it with custom parameters:
    # generate_temp_file(csv_filename="custom.csv", output_filename="custom.txt", time_interval=20)