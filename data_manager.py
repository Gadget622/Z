"""
Data Manager Module

Handles all data operations for the Z application.
"""

import os
import csv
import pandas as pd
from datetime import datetime


class DataManager:
    """Manages data operations for the Z application."""
    
    def __init__(self, app):
        """
        Initialize the data manager.
        
        Args:
            app: The Z application instance
        """
        self.app = app
        
        # Get the directory where the script is located
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # CSV file for storing data
        self.csv_filename = os.path.join(self.script_dir, app.config.get("DATA_CSV", "Z.csv"))
        
        # Set up temporary directory
        self.setup_temp_directory()
        
        # Ensure CSV file exists
        self.ensure_csv_exists()
    
    def setup_temp_directory(self):
        """Create a temporary directory for backup and recovery files."""
        self.temp_dir = os.path.join(self.script_dir, "temp")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def ensure_csv_exists(self):
        """Ensure the CSV file exists with proper headers."""
        try:
            if not os.path.exists(self.csv_filename):
                with open(self.csv_filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['timestamp', 'text'])
        except Exception as e:
            self.app.gui_manager.set_feedback(f"Could not create or access the data file: {e}")
            self.app.error_handler.log_error(f"Data file creation error: {e}")
    
    def get_timestamp(self):
        """
        Get formatted timestamp.
        
        Returns:
            str: Formatted timestamp
        """
        now = datetime.now()
        weekday = now.strftime("%a").upper()
        return now.strftime(f"%Y-%m-%d {weekday} %H:%M:%S.%f")[:-4]
    
    def write_entry(self, timestamp, text):
        """
        Write an entry to the CSV file.
        
        Args:
            timestamp (str): Entry timestamp
            text (str): Entry text
            
        Returns:
            bool: True if successful, False otherwise
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
            self.app.error_handler.log_error(f"Error writing to CSV: {e}")
            
            # If writing to main CSV fails, use a unique temp file
            try:
                temp_filepath = self.get_temp_filepath()
                
                with open(temp_filepath, 'w', newline='') as temp_file:
                    temp_writer = csv.writer(temp_file)
                    temp_writer.writerow(['timestamp', 'text'])  # Header
                    temp_writer.writerow([timestamp, text])
                
                self.app.gui_manager.set_feedback(
                    f"Entry saved to temporary storage. Main file ({self.app.config.get('DATA_CSV')}) is unavailable."
                )
                
                return False
                
            except Exception as e2:
                # Both main file and temp directory are inaccessible
                self.app.gui_manager.set_feedback("WARNING: Could not save entry to any storage location!")
                self.app.error_handler.log_error(f"Critical storage error: {e2}")
                return False
    
    def recover_temp_entries(self):
        """
        Attempt to recover entries from temporary files and merge them into the main CSV file.
        
        Returns:
            int: Number of recovered entries
        """
        try:
            # Check if temp directory exists
            if not os.path.exists(self.temp_dir):
                return 0
            
            # Get all CSV files in the temp directory
            temp_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.csv')]
            
            if not temp_files:
                return 0
            
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
                    
                except Exception as e:
                    # Skip files that can't be processed
                    self.app.error_handler.log_error(f"Error recovering temp file {temp_file}: {e}")
                    continue
            
            # Show feedback if entries were recovered
            if total_recovered > 0:
                self.app.gui_manager.set_feedback(
                    f"Recovered {total_recovered} entries from {recovered_files} temporary files"
                )
            
            return total_recovered
                
        except Exception as e:
            # If recovery fails, log error and continue
            self.app.error_handler.log_error(f"Error in recovery process: {e}")
            return 0
    
    def get_temp_filepath(self):
        """
        Generate a path for a temporary file.
        
        Returns:
            str: Path to a new temporary file
        """
        # Generate unique filename based on timestamp
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"temp_{timestamp}.csv"
        
        return os.path.join(self.temp_dir, filename)
    
    def read_entries(self, count=None, filter_func=None):
        """
        Read entries from the CSV file.
        
        Args:
            count (int, optional): Maximum number of entries to return
            filter_func (function, optional): Function to filter entries
            
        Returns:
            list: List of entry dictionaries
        """
        try:
            if not os.path.exists(self.csv_filename):
                return []
            
            # Read CSV into pandas DataFrame
            df = pd.read_csv(self.csv_filename)
            
            # Apply filter if provided
            if filter_func:
                df = df[df.apply(filter_func, axis=1)]
            
            # Convert to list of dictionaries
            entries = df.to_dict('records')
            
            # Limit entries if count provided
            if count and count > 0:
                entries = entries[-count:]
            
            return entries
        
        except Exception as e:
            self.app.error_handler.log_error(f"Error reading entries: {e}")
            return []
    
    def update_entry(self, index, new_text):
        """
        Update an entry in the CSV file.
        
        Args:
            index (int): Index of the entry to update
            new_text (str): New text for the entry
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read the CSV file
            df = pd.read_csv(self.csv_filename)
            
            # Check if index is valid
            if index < 0 or index >= len(df):
                return False
            
            # Update the entry
            df.at[index, 'text'] = new_text
            
            # Write back to CSV
            df.to_csv(self.csv_filename, index=False)
            
            return True
        
        except Exception as e:
            self.app.error_handler.log_error(f"Error updating entry: {e}")
            return False
    
    def delete_entry(self, index):
        """
        Delete an entry from the CSV file.
        
        Args:
            index (int): Index of the entry to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read the CSV file
            df = pd.read_csv(self.csv_filename)
            
            # Check if index is valid
            if index < 0 or index >= len(df):
                return False
            
            # Delete the entry
            df = df.drop(index)
            
            # Reset the index
            df = df.reset_index(drop=True)
            
            # Write back to CSV
            df.to_csv(self.csv_filename, index=False)
            
            return True
        
        except Exception as e:
            self.app.error_handler.log_error(f"Error deleting entry: {e}")
            return False
    
    def search_entries(self, query):
        """
        Search entries for a query string.
        
        Args:
            query (str): Search query
            
        Returns:
            list: List of matching entry dictionaries
        """
        try:
            # Read all entries
            entries = self.read_entries()
            
            # Filter entries containing the query
            matches = [entry for entry in entries if query.lower() in entry['text'].lower()]
            
            return matches
        
        except Exception as e:
            self.app.error_handler.log_error(f"Error searching entries: {e}")
            return []