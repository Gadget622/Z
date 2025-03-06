"""
Directory Tree Module

Manages directory tree structure for the Z application.
Features:
- Generate tree representation of directories
- Memory management (limit directory size)
- Store file contents for quick access
- Display total sizes for all directories and files
- Save tree output to txt directory
"""

import os
import re
import json
import shutil
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class DirectoryTreeManager:
    """
    Manages a tree structure of directories and files for Z application.
    """
    
    def __init__(self, app):
        """
        Initialize the directory tree manager.
        
        Args:
            app: The parent Z application
        """
        self.app = app
        
        # Get the directory where the script is located
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load settings
        self.settings = self.load_settings()
        
        # Initialize directory structure cache
        self.dir_cache = self.load_dir_cache()
        
        # Add directory tree commands to command handler
        if hasattr(app, 'command_handler') and app.command_handler:
            app.command_handler.slash_commands['tree'] = self.cmd_tree
            app.command_handler.slash_commands['dir'] = self.cmd_dir
            
            # Only register claude command if it's implemented
            if hasattr(self, 'cmd_claude'):
                app.command_handler.slash_commands['claude'] = self.cmd_claude
    
    def show_tree(self):
        """Display the directory tree in the GUI."""
        try:
            # Generate tree starting from script directory
            tree_output = self.generate_tree(self.script_dir)
            
            # Create or update tree display
            if not hasattr(self, 'tree_display'):
                # Create tree frame
                self.tree_frame = ttk.Frame(self.app.root)
                self.tree_frame.grid(row=0, column=0, sticky='nsew')
                
                # Create scrollbar
                scrollbar = ttk.Scrollbar(self.tree_frame)
                scrollbar.grid(row=0, column=1, sticky='ns')
                
                # Create tree display
                self.tree_display = tk.Text(self.tree_frame, 
                                        width=40, 
                                        height=30,
                                        font=('Courier', 10),
                                        yscrollcommand=scrollbar.set)
                self.tree_display.grid(row=0, column=0, sticky='nsew')
                
                # Configure scrollbar
                scrollbar.config(command=self.tree_display.yview)
                
                # Configure grid weights for tree frame
                self.tree_frame.grid_columnconfigure(0, weight=1)
                self.tree_frame.grid_rowconfigure(0, weight=1)
            
            # Update tree content
            self.tree_display.delete('1.0', tk.END)
            self.tree_display.insert('1.0', tree_output)
            
            self.app.error_handler.log_info("Directory tree displayed successfully")
            
        except Exception as e:
            self.app.error_handler.log_error(f"Error displaying tree: {e}")
            messagebox.showerror("Error", f"Failed to display directory tree: {e}")

    def load_settings(self):
        """
        Load directory tree settings from config file or use defaults.
        
        Returns:
            dict: Settings dictionary
        """
        default_settings = {
            "max_dir_size": 1048576,  # 1 MB maximum directory size
            "scan_depth": 3,          # Maximum depth for tree generation
            "file_extensions": [".py", ".txt", ".md", ".csv", ".json", ".html", ".css", ".js"],
            "exclude_dirs": ["__pycache__", ".git", ".venv", "venv", "node_modules"],
            "exclude_files": [".gitignore", ".DS_Store", "Thumbs.db"],
            "last_scanned": None,     # Timestamp of last scan
            "save_to_txt_dir": True   # Default to saving tree output to txt directory
        }
        
        # Try to load settings from JSON
        settings_path = os.path.join(self.script_dir, "tree_settings.json")
        
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    loaded_settings = json.load(f)
                
                # Update default settings with loaded values
                default_settings.update(loaded_settings)
        except Exception as e:
            if hasattr(self, 'app') and hasattr(self.app, 'error_handler'):
                self.app.error_handler.log_error(f"Error loading tree settings: {e}")
            
        return default_settings
    
    def save_settings(self):
        """Save current settings to the config file"""
        settings_path = os.path.join(self.script_dir, "tree_settings.json")
        
        try:
            with open(settings_path, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            self.app.error_handler.log_error(f"Error saving tree settings: {e}")
    
    def cmd_tree(self, args):
        """
        Command to generate and display a directory tree.
        
        Args:
            args (str): Optional path and flags
            
        Returns:
            str: Generated tree or error message
        """
        # Check for special save flag
        save_flag = False
        path = args
        
        if args and "--save" in args:
            save_flag = True
            path = args.replace("--save", "").strip()
        
        # Handle special cases like ".." for parent directory
        if path == "..":
            path = os.path.dirname(self.script_dir)
        elif path == ".":
            path = self.script_dir
        elif not path:
            path = self.script_dir
        
        # Clean path and handle relative paths
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(self.script_dir, path))
        
        # Check if the path exists
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
        
        # Check if it's a directory
        if not os.path.isdir(path):
            return f"Error: '{path}' is not a directory."
        
        # Generate the tree
        try:
            tree_output = self.generate_tree(path)
            
            # Update the timestamp of the last scan
            self.settings["last_scanned"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_settings()
            
            # Save tree output to txt directory if enabled in settings or flag is set
            if save_flag or self.settings.get("save_to_txt_dir", True):
                success, message = self.save_tree_to_txt(tree_output, path)
                if success:
                    tree_output += "\n" + message
                else:
                    tree_output += "\n" + message
            
            return tree_output
        except Exception as e:
            self.app.error_handler.log_error(f"Error generating tree: {e}")
            return f"Error generating tree: {str(e)}"
    
    def save_tree_to_txt(self, tree_output, path):
        """
        Save tree output to a file in the txt directory.
        
        Args:
            tree_output (str): The tree output to save
            path (str): The directory path that was scanned
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Create txt directory if it doesn't exist
            txt_dir = os.path.join(self.script_dir, "txt")
            os.makedirs(txt_dir, exist_ok=True)
            
            # Generate filename based on the directory name and timestamp
            dir_name = os.path.basename(path)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tree_{dir_name}_{timestamp}.txt"
            file_path = os.path.join(txt_dir, filename)
            
            # Save tree output to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(tree_output)
            
            return True, f"Tree output saved to: txt/{filename}"
        except Exception as e:
            self.app.error_handler.log_error(f"Error saving tree output: {e}")
            return False, f"Error saving tree output: {str(e)}"
    
    def cmd_dir(self, args):
        """
        Command to show directory information and manage the tree.
        
        Args:
            args (str): Options for directory management
            
        Returns:
            str: Result message
        """
        if not args:
            # Show directory tree cache status
            return self.show_cache_status()
        
        # Parse arguments
        parts = args.split(None, 1)
        option = parts[0].lower()
        option_args = parts[1] if len(parts) > 1 else ""
        
        # Handle different options
        if option == "clear":
            # Clear the cache
            self.dir_cache = {}
            self.save_dir_cache()
            return "Directory tree cache cleared."
            
        elif option == "info":
            # Show info about a specific directory
            path = option_args or self.script_dir
            return self.show_dir_info(path)
            
        elif option == "settings":
            # Show or modify settings
            return self.handle_settings(option_args)
            
        elif option == "scan":
            # Scan directories and update cache
            path = option_args or self.script_dir
            return self.scan_directories(path)

        elif option == "path":
            # Change the root directory for the tree
            if not option_args:
                return "Please specify a directory path"
            
            new_path = option_args
            
            # Handle special cases like ".." for parent directory
            if new_path == "..":
                new_path = os.path.dirname(self.script_dir)
            elif new_path == ".":
                new_path = self.script_dir
            
            # Check if this is an absolute or relative path
            if not os.path.isabs(new_path):
                new_path = os.path.abspath(os.path.join(self.script_dir, new_path))
            
            if self.set_root_path(new_path):
                return f"Directory tree root changed to: {new_path}"
            return f"Failed to change directory to: {new_path}"
            
        else:
            return f"Unknown option: {option}\nAvailable options: clear, info, settings, scan, path"
    
    def generate_tree(self, root_path, depth=0):
        """
        Generate a tree representation of the directory structure.
        
        Args:
            root_path (str): The root directory to start from
            depth (int): Current depth in the tree
            
        Returns:
            str: Text representation of the directory tree
        """
        if depth > self.settings["scan_depth"]:
            return "    " * depth + "...\n"
        
        # Check if this directory should be excluded
        if os.path.basename(root_path) in self.settings["exclude_dirs"]:
            return ""
        
        output = ""
        
        # Start with the root directory
        if depth == 0:
            output = f"{os.path.basename(root_path)}/\n"
            
            # Calculate directory size
            dir_size = self.get_directory_size(root_path)
            
            # Add size information
            output += f"Total size: {self.format_size(dir_size)}\n"
            
            # Update the cache
            self.update_dir_cache(root_path, dir_size)
        
        try:
            # Get list of items in the directory
            items = os.listdir(root_path)
            
            # Sort items: directories first, then files
            dirs = []
            files = []
            
            for item in items:
                item_path = os.path.join(root_path, item)
                
                # Skip excluded items
                if (os.path.isdir(item_path) and item in self.settings["exclude_dirs"]) or \
                   (os.path.isfile(item_path) and item in self.settings["exclude_files"]):
                    continue
                
                # Add to appropriate list
                if os.path.isdir(item_path):
                    dirs.append(item)
                else:
                    # Only include files with specified extensions
                    ext = os.path.splitext(item)[1].lower()
                    if not self.settings["file_extensions"] or ext in self.settings["file_extensions"]:
                        files.append(item)
            
            # Process directories
            for i, d in enumerate(sorted(dirs)):
                # Calculate directory size
                dir_path = os.path.join(root_path, d)
                dir_size = self.get_directory_size(dir_path)
                
                # Use different symbols for the last item
                is_last = (i == len(dirs) - 1 and not files)
                prefix = "└── " if is_last else "├── "
                
                # Add the directory to the output with size information
                output += "    " * depth + prefix + d + "/ " + f"({self.format_size(dir_size)})\n"
                
                # Add subdirectories (with proper indentation)
                sub_prefix = "    " if is_last else "│   "
                sub_output = self.generate_tree(dir_path, depth + 1)
                
                # Properly indent the sub-directory output
                sub_lines = sub_output.splitlines()
                for line in sub_lines:
                    if line:
                        output += "    " * depth + sub_prefix + line + "\n"
            
            # Process files
            for i, f in enumerate(sorted(files)):
                is_last = (i == len(files) - 1)
                prefix = "└── " if is_last else "├── "
                
                # Get file size
                file_path = os.path.join(root_path, f)
                file_size = os.path.getsize(file_path)
                
                # Add the file to the output
                output += "    " * depth + prefix + f + f" ({self.format_size(file_size)})\n"
                
                # Store file contents in cache if it's small enough
                if file_size <= 102400:  # 100 KB limit for caching file contents
                    try:
                        # Read text files only
                        ext = os.path.splitext(f)[1].lower()
                        if ext in [".py", ".txt", ".md", ".csv", ".json", ".html", ".js", ".css"]:
                            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                                content = file.read()
                                self.update_file_cache(file_path, content)
                    except Exception as e:
                        # Skip files that can't be read
                        self.app.error_handler.log_error(f"Error reading file {file_path}: {e}")
            
            return output
            
        except PermissionError:
            return "    " * depth + "[Permission denied]\n"
        except Exception as e:
            self.app.error_handler.log_error(f"Error generating tree for {root_path}: {e}")
            return "    " * depth + f"[Error: {str(e)}]\n"
    
    def get_directory_size(self, path):
        """
        Calculate the total size of a directory.
        
        Args:
            path (str): Directory path
            
        Returns:
            int: Total size in bytes
        """
        total_size = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                # Remove excluded directories
                for exclude_dir in self.settings["exclude_dirs"]:
                    if exclude_dir in dirnames:
                        dirnames.remove(exclude_dir)
                
                # Add size of all files in the directory
                for f in filenames:
                    # Skip excluded files
                    if f in self.settings["exclude_files"]:
                        continue
                        
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp) and os.path.isfile(fp):
                        total_size += os.path.getsize(fp)
        except Exception as e:
            self.app.error_handler.log_error(f"Error calculating directory size for {path}: {e}")
            
        return total_size
    
    def format_size(self, size_bytes):
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes (int): Size in bytes
            
        Returns:
            str: Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def update_dir_cache(self, dir_path, size):
        """
        Update the directory cache with size information.
        
        Args:
            dir_path (str): Directory path
            size (int): Directory size in bytes
        """
        self.dir_cache[dir_path] = {
            "size": size,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files": self.dir_cache.get(dir_path, {}).get("files", {})
        }
        
        # Save the updated cache
        self.save_dir_cache()
    
    def update_file_cache(self, file_path, content):
        """
        Update the file cache with content.
        
        Args:
            file_path (str): File path
            content (str): File content
        """
        dir_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        
        # Initialize directory entry if needed
        if dir_path not in self.dir_cache:
            self.dir_cache[dir_path] = {
                "size": 0,
                "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "files": {}
            }
        
        # Update file entry
        self.dir_cache[dir_path]["files"][file_name] = {
            "size": len(content),
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save the updated cache
        self.save_dir_cache()

            
    def save_dir_cache(self):
        """Save the directory cache to a file"""
        # Create private directory
        private_dir = self.ensure_private_dir()
        cache_path = os.path.join(private_dir, "dir_cache.json")
        
        try:
            simplified_cache = {}
            
            for dir_path, dir_info in self.dir_cache.items():
                simplified_cache[dir_path] = {
                    "size": dir_info["size"],
                    "last_updated": dir_info["last_updated"],
                    "files": {}
                }
                
                for file_name, file_info in dir_info.get("files", {}).items():
                    # Store metadata but not content
                    simplified_cache[dir_path]["files"][file_name] = {
                        "size": file_info.get("size", 0),
                        "last_updated": file_info.get("last_updated", "")
                    }
        
            with open(cache_path, 'w') as f:
                json.dump(simplified_cache, f, indent=4)
        except Exception as e:
            self.app.error_handler.log_error(f"Error saving directory cache: {e}")

    def load_dir_cache(self):
        """Load the directory cache from file."""
        # Create private directory
        private_dir = self.ensure_private_dir()
        cache_path = os.path.join(private_dir, "dir_cache.json")
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.app.error_handler.log_error(f"Error loading directory cache: {e}")
        
        return {}
    
    def set_root_path(self, new_path):
        """Change the root path for directory scanning."""
        if os.path.exists(new_path) and os.path.isdir(new_path):
            self.script_dir = os.path.abspath(new_path)
            self.show_tree()  # Refresh the tree with new path
            self.app.error_handler.log_info(f"Directory tree root changed to: {new_path}")
            return True
        else:
            self.app.error_handler.log_error(f"Invalid directory path: {new_path}")
            return False
    
    def handle_settings(self, args):
        """
        Handle directory tree settings.
        
        Args:
            args (str): Setting arguments
            
        Returns:
            str: Result message
        """
        if not args:
            # Show current settings
            output = "Directory Tree Settings:\n\n"
            output += f"Maximum directory size: {self.format_size(self.settings['max_dir_size'])}\n"
            output += f"Scan depth: {self.settings['scan_depth']}\n"
            output += f"File extensions: {', '.join(self.settings['file_extensions'])}\n"
            output += f"Excluded directories: {', '.join(self.settings['exclude_dirs'])}\n"
            output += f"Excluded files: {', '.join(self.settings['exclude_files'])}\n"
            output += f"Save to txt directory: {'Enabled' if self.settings.get('save_to_txt_dir', True) else 'Disabled'}\n"
            
            return output
        
        # Parse setting command
        parts = args.split(None, 1)
        setting = parts[0].lower()
        value = parts[1] if len(parts) > 1 else ""
        
        # Handle different settings
        if setting == "depth":
            try:
                depth = int(value)
                if depth < 1:
                    return "Error: Depth must be at least 1."
                
                self.settings["scan_depth"] = depth
                self.save_settings()
                return f"Scan depth set to {depth}."
            except ValueError:
                return "Error: Invalid depth value."

        elif setting == "savetotxt":
            value_lower = value.lower()
            if value_lower in ["on", "true", "yes", "1"]:
                self.settings["save_to_txt_dir"] = True
                self.save_settings()
                return "Tree output will be saved to txt directory."
            elif value_lower in ["off", "false", "no", "0"]:
                self.settings["save_to_txt_dir"] = False
                self.save_settings()
                return "Tree output will not be saved to txt directory."
            else:
                return "Invalid value. Use 'on' or 'off'."
        
        elif setting == "maxsize":
            try:
                # Parse size string (e.g., "1MB", "500KB")
                size_match = re.match(r"(\d+)\s*([KMG]?B)?", value, re.IGNORECASE)
                if not size_match:
                    return "Error: Invalid size format. Use format like '1MB' or '500KB'."
                
                size_value = int(size_match.group(1))
                size_unit = size_match.group(2).upper() if size_match.group(2) else "B"
                
                # Convert to bytes
                if size_unit == "KB":
                    size_bytes = size_value * 1024
                elif size_unit == "MB":
                    size_bytes = size_value * 1024 * 1024
                elif size_unit == "GB":
                    size_bytes = size_value * 1024 * 1024 * 1024
                else:
                    size_bytes = size_value
                
                self.settings["max_dir_size"] = size_bytes
                self.save_settings()
                return f"Maximum directory size set to {self.format_size(size_bytes)}."
            except Exception:
                return "Error: Invalid size value."
        
        elif setting == "extensions":
            # Parse extensions list
            extensions = [ext.strip() for ext in value.split(",") if ext.strip()]
            
            # Ensure all extensions start with a dot
            extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions]
            
            self.settings["file_extensions"] = extensions
            self.save_settings()
            return f"File extensions set to: {', '.join(extensions)}"
        
        elif setting == "exclude":
            # Parse exclusion list
            items = [item.strip() for item in value.split(",") if item.strip()]
            
            # Check if directories or files
            if len(parts) > 2 and parts[1].lower() == "dirs":
                self.settings["exclude_dirs"] = items
                self.save_settings()
                return f"Excluded directories set to: {', '.join(items)}"
            else:
                self.settings["exclude_files"] = items
                self.save_settings()
                return f"Excluded files set to: {', '.join(items)}"
        
        else:
            return f"Unknown setting: {setting}\nAvailable settings: depth, maxsize, extensions, exclude, savetotxt"

    def show_cache_status(self):
        """
        Show the status of the directory cache.
        
        Returns:
            str: Status message
        """
        if not self.dir_cache:
            return "Directory cache is empty. Use '/dir scan' to populate it."
        
        # Calculate total cached size
        total_size = 0
        total_files = 0
        dir_count = len(self.dir_cache)
        
        for dir_path, dir_info in self.dir_cache.items():
            total_size += dir_info["size"]
            total_files += len(dir_info.get("files", {}))
        
        # Format the output
        output = "Directory Cache Status:\n\n"
        output += f"Directories: {dir_count}\n"
        output += f"Cached files: {total_files}\n"
        output += f"Total size: {self.format_size(total_size)}\n"
        output += f"Last scan: {self.settings['last_scanned'] or 'Never'}\n\n"
        
        # Show top 5 largest directories
        output += "Largest directories:\n"
        sorted_dirs = sorted(self.dir_cache.items(), key=lambda x: x[1]["size"], reverse=True)
        
        for i, (dir_path, dir_info) in enumerate(sorted_dirs[:5], 1):
            output += f"{i}. {os.path.basename(dir_path)} ({self.format_size(dir_info['size'])})\n"
        
        return output
    
    def show_dir_info(self, path):
        """
        Show information about a specific directory.
        
        Args:
            path (str): Directory path
            
        Returns:
            str: Information message
        """
        # Clean path and handle relative paths
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(self.script_dir, path))
        
        # Check if the path exists
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
        
        # Check if it's a directory
        if not os.path.isdir(path):
            return f"Error: '{path}' is not a directory."
        
        # Check if the directory is in the cache
        if path not in self.dir_cache:
            return f"Directory '{path}' is not in the cache. Use '/dir scan {path}' to add it."
        
        # Get directory info
        dir_info = self.dir_cache[path]
        
        # Format the output
        output = f"Directory: {path}\n\n"
        output += f"Size: {self.format_size(dir_info['size'])}\n"
        output += f"Last updated: {dir_info['last_updated']}\n"
        output += f"Cached files: {len(dir_info.get('files', {}))}\n\n"
        
        # List cached files
        if dir_info.get("files"):
            output += "Cached files:\n"
            
            for file_name, file_info in sorted(dir_info["files"].items()):
                output += f"- {file_name} ({self.format_size(file_info.get('size', 0))})\n"
        
        return output
        
    def scan_directories(self, path):
        """
        Scan directories and update the cache.
        
        Args:
            path (str): Directory path to scan
            
        Returns:
            str: Result message
        """
        # Clean path and handle relative paths
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(self.script_dir, path))
        
        # Check if the path exists
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
        
        # Check if it's a directory
        if not os.path.isdir(path):
            return f"Error: '{path}' is not a directory."
        
        # Start scanning
        self.app.gui_manager.set_feedback(f"Scanning directory: {path}...")
        
        try:
            # Generate tree (this also updates the cache)
            self.generate_tree(path)
            
            # Update scan timestamp
            self.settings["last_scanned"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_settings()
            
            return f"Scan complete for '{path}'."
        except Exception as e:
            self.app.error_handler.log_error(f"Error scanning directory: {e}")
            return f"Error scanning directory: {str(e)}"
        
    def ensure_private_dir(self):
        """Create the private directory if it doesn't exist."""
        private_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "private")
        os.makedirs(private_dir, exist_ok=True)
        return private_dir
    
