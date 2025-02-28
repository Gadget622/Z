"""
Checkbox Handler Module

Handles checkbox functionality for Z application.
Checkboxes are represented in text as:
- [ ] Unchecked item
- [x] or [X] Checked item
"""

import re
import pandas as pd


class CheckboxHandler:
    """Handles checkbox functionality for the Z application."""
    
    # Regular expressions for checkbox detection
    CHECKBOX_PATTERN = r'^\s*-\s*\[([ xX])\]\s*(.*?)$'
    
    def __init__(self, app):
        """
        Initialize the checkbox handler.
        
        Args:
            app: The parent Z application
        """
        self.app = app
        
        # Add toggle checkbox command to the command handler
        if hasattr(app, 'command_handler') and app.command_handler:
            app.command_handler.slash_commands['toggle'] = self.cmd_toggle
    
    def is_checkbox(self, text):
        """
        Check if the given text contains a checkbox.
        
        Args:
            text (str): The text to check
            
        Returns:
            bool: True if the text contains a checkbox
        """
        return bool(re.match(self.CHECKBOX_PATTERN, text))
    
    def get_checkbox_state(self, text):
        """
        Get the state of a checkbox in the text.
        
        Args:
            text (str): The text containing a checkbox
            
        Returns:
            tuple: (is_checked, content) or (None, None) if not a checkbox
        """
        match = re.match(self.CHECKBOX_PATTERN, text)
        if match:
            is_checked = match.group(1) in ['x', 'X']
            content = match.group(2)
            return is_checked, content
        return None, None
    
    def toggle_checkbox(self, text):
        """
        Toggle the state of a checkbox in the text.
        
        Args:
            text (str): The text containing a checkbox
            
        Returns:
            str: The text with the checkbox toggled
        """
        match = re.match(self.CHECKBOX_PATTERN, text)
        if not match:
            return text
            
        is_checked = match.group(1) in ['x', 'X']
        content = match.group(2)
        
        # Toggle the checkbox state
        new_mark = ' ' if is_checked else 'x'
        
        # Create the new checkbox text
        return f"- [{new_mark}] {content}"
    
    def format_checkbox_display(self, text):
        """
        Format a checkbox text for display, potentially with styling.
        
        Args:
            text (str): Text containing a checkbox
            
        Returns:
            str: Formatted text for display
        """
        is_checked, content = self.get_checkbox_state(text)
        if is_checked is None:
            return text
            
        # For now, just return the original text
        # In a GUI context, we could add styling here
        return text
    
    def cmd_toggle(self, args):
        """
        Command to toggle the state of checkboxes.
        
        Args:
            args (str): The command arguments - should be a line number or pattern
            
        Returns:
            str: Result message
        """
        try:
            # If args is a number, interpret as line number
            if args.isdigit():
                line_num = int(args)
                return self.toggle_by_line(line_num)
            
            # Otherwise, interpret as a search pattern
            elif args:
                return self.toggle_by_pattern(args)
            
            # No args, show usage
            else:
                return "Usage: /toggle <line_number> or /toggle <search_pattern>"
                
        except Exception as e:
            self.app.error_handler.log_error(f"Error toggling checkbox: {str(e)}")
            return f"Error toggling checkbox: {str(e)}"
    
    def toggle_by_line(self, line_num):
        """
        Toggle checkbox at the specified line number.
        
        Args:
            line_num (int): The line number (recent entries, 1-based)
            
        Returns:
            str: Result message
        """
        try:
            # Read the CSV file
            df = pd.read_csv(self.app.data_manager.csv_filename)
            
            # Check if the line number is valid
            if line_num <= 0 or line_num > len(df):
                return f"Invalid line number. There are {len(df)} entries."
            
            # Get the entry (1-based index to 0-based index)
            entry_idx = len(df) - line_num
            text = df.iloc[entry_idx]['text']
            
            # Check if the entry is a checkbox
            if not self.is_checkbox(text):
                return f"Entry #{line_num} is not a checkbox item."
            
            # Toggle the checkbox
            new_text = self.toggle_checkbox(text)
            
            # Update the entry
            df.at[entry_idx, 'text'] = new_text
            
            # Save the CSV
            df.to_csv(self.app.data_manager.csv_filename, index=False)
            
            # Get the state for the message
            is_checked, content = self.get_checkbox_state(new_text)
            state = "Checked" if is_checked else "Unchecked"
            
            return f"{state}: {content}"
            
        except Exception as e:
            self.app.error_handler.log_error(f"Error toggling checkbox by line: {str(e)}")
            return f"Error toggling checkbox by line: {str(e)}"
    
    def find_all_checkboxes(self):
        """
        Find all checkboxes in the database.
        
        Returns:
            list: List of checkbox entries with their indices
        """
        try:
            # Read the CSV file
            df = pd.read_csv(self.app.data_manager.csv_filename)
            
            # Find all checkboxes
            checkboxes = []
            
            for idx, row in df.iterrows():
                text = row['text']
                
                # Check if it's a checkbox
                if self.is_checkbox(text):
                    is_checked, content = self.get_checkbox_state(text)
                    checkboxes.append({
                        'index': idx,
                        'text': text,
                        'is_checked': is_checked,
                        'content': content,
                        'timestamp': row['timestamp']
                    })
            
            return checkboxes
            
        except Exception as e:
            self.app.error_handler.log_error(f"Error finding checkboxes: {str(e)}")
            return []
    
    def get_checkbox_summary(self):
        """
        Get a summary of checkbox status.
        
        Returns:
            dict: Summary information about checkboxes
        """
        checkboxes = self.find_all_checkboxes()
        
        if not checkboxes:
            return {
                'total': 0,
                'checked': 0,
                'unchecked': 0,
                'percentage': 0
            }
        
        checked = sum(1 for cb in checkboxes if cb['is_checked'])
        total = len(checkboxes)
        
        return {
            'total': total,
            'checked': checked,
            'unchecked': total - checked,
            'percentage': round(checked / total * 100, 1) if total > 0 else 0
        } 
    
    def toggle_by_pattern(self, pattern):
        """
        Toggle the most recent checkbox that matches the pattern.
        
        Args:
            pattern (str): The search pattern
            
        Returns:
            str: Result message
        """
        try:
            # Read the CSV file
            df = pd.read_csv(self.app.data_manager.csv_filename)
            
            # Find the most recent checkbox that matches the pattern
            found_idx = None
            found_text = None
            
            for idx, row in df[::-1].iterrows():  # Iterate from most recent
                text = row['text']
                
                # Check if it's a checkbox and matches the pattern
                is_checkbox = self.is_checkbox(text)
                if is_checkbox and pattern.lower() in text.lower():
                    found_idx = idx
                    found_text = text
                    break
            
            if found_idx is None:
                return f"No checkbox found matching '{pattern}'."
            
            # Toggle the checkbox
            new_text = self.toggle_checkbox(found_text)
            
            # Update the entry
            df.at[found_idx, 'text'] = new_text
            
            # Save the CSV
            df.to_csv(self.app.data_manager.csv_filename, index=False)
            
            # Get the state for the message
            is_checked, content = self.get_checkbox_state(new_text)
            state = "Checked" if is_checked else "Unchecked"
            
            return f"{state}: {content}"
            
        except Exception as e:
            self.app.error_handler.log_error(f"Error toggling checkbox by pattern: {str(e)}")
            return f"Error toggling checkbox by pattern: {str(e)}"