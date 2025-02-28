"""
Error Handler Module

Handles error logging and user notification for the Z application.
"""

import os
import sys
import traceback
import logging
from datetime import datetime
import tkinter as tk
from tkinter import messagebox


class ErrorHandler:
    """Handles errors and exceptions for the Z application."""
    
    def __init__(self):
        """Initialize the error handler."""
        # Set up logging
        self.setup_logging()
    
    def setup_logging(self):
        """Set up the logging system."""
        # Create logs directory if it doesn't exist
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(script_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create log file name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(logs_dir, f"z_app_{timestamp}.log")
        
        # Configure logging
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add console handler for debugging
        console = logging.StreamHandler()
        console.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
    
    def log_error(self, message, exc_info=None):
        """
        Log an error message.
        
        Args:
            message (str): Error message
            exc_info (Exception, optional): Exception object
        """
        if exc_info:
            logging.error(message, exc_info=exc_info)
        else:
            logging.error(message)
    
    def log_warning(self, message):
        """
        Log a warning message.
        
        Args:
            message (str): Warning message
        """
        logging.warning(message)
    
    def log_info(self, message):
        """
        Log an info message.
        
        Args:
            message (str): Info message
        """
        logging.info(message)
    
    def handle_exception(self, exception, context=None):
        """
        Handle an exception by logging it and showing a message to the user.
        
        Args:
            exception (Exception): The exception to handle
            context (str, optional): Context information about where the exception occurred
        """
        # Format the error message
        error_message = f"{type(exception).__name__}: {str(exception)}"
        if context:
            error_message = f"{context}: {error_message}"
        
        # Log the exception
        self.log_error(error_message, exc_info=exception)
        
        # Show error message to user
        try:
            messagebox.showerror(
                "Error",
                f"An error occurred: {error_message}\n\nThe error has been logged."
            )
        except Exception:
            # If messagebox fails, print to console
            print(f"ERROR: {error_message}")
    
    def handle_critical_error(self, message):
        """
        Handle a critical error that requires the application to exit.
        
        Args:
            message (str): Error message
        """
        # Log the critical error
        self.log_error(f"CRITICAL ERROR: {message}")
        
        # Show error message to user
        try:
            messagebox.showerror(
                "Critical Error",
                f"{message}\n\nThe application will now close."
            )
        except Exception:
            # If messagebox fails, print to console
            print(f"CRITICAL ERROR: {message}")
        
        # Exit the application
        sys.exit(1)
    
    def install_global_exception_handler(self):
        """Install a global exception handler to catch unhandled exceptions."""
        def global_exception_handler(exctype, value, tb):
            """Global exception handler function."""
            # Format traceback
            traceback_str = ''.join(traceback.format_tb(tb))
            
            # Log the exception
            self.log_error(
                f"Unhandled exception: {exctype.__name__}: {value}\n{traceback_str}"
            )
            
            # Show error message to user
            try:
                messagebox.showerror(
                    "Unhandled Error",
                    f"An unhandled error occurred: {exctype.__name__}: {value}\n\n"
                    "The error has been logged."
                )
            except Exception:
                # If messagebox fails, print to console
                print(f"UNHANDLED ERROR: {exctype.__name__}: {value}")
                print(traceback_str)
            
            # Call the original exception handler
            sys.__excepthook__(exctype, value, tb)
        
        # Set the global exception handler
        sys.excepthook = global_exception_handler