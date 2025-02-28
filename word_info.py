"""
Word Information Module

Collects and manages information about words including:
- Definitions
- Synonyms
- Antonyms
- Etymology
"""

import os
import re
import json
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time


class WordInfoCollector:
    """
    Module for collecting word information in the Z application.
    """
    
    def __init__(self, app):
        """
        Initialize the word information collector.
        
        Args:
            app: The parent Z application
        """
        self.app = app
        
        # Get the directory where the script is located
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # File to store word information
        self.words_file = os.path.join(self.script_dir, "word_info.json")
        
        # Initialize word data
        self.word_data = self.load_word_data()
        
        # Add word info commands to command handler
        if hasattr(app, 'command_handler') and app.command_handler:
            app.command_handler.slash_commands['word'] = self.cmd_word
            app.command_handler.slash_commands['words'] = self.cmd_words
    
    def load_word_data(self):
        """
        Load word information from JSON file.
        
        Returns:
            dict: Word information dictionary
        """
        if os.path.exists(self.words_file):
            try:
                with open(self.words_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.app.error_handler.log_error(f"Error loading word data: {e}")
        
        # Return an empty dict if file doesn't exist or loading fails
        return {}
    
    def save_word_data(self):
        """Save word information to JSON file"""
        try:
            with open(self.words_file, 'w', encoding='utf-8') as f:
                json.dump(self.word_data, f, indent=4, sort_keys=True)
        except Exception as e:
            self.app.error_handler.log_error(f"Error saving word data: {e}")
    
    def cmd_word(self, args):
        """
        Command to look up or add word information.
        
        Args:
            args (str): The word to look up or add
            
        Returns:
            str: Result message
        """
        if not args:
            return "Usage: /word <word> - Look up or add word information"
        
        # Get the word (first argument) and any options
        parts = args.strip().split(None, 1)
        word = parts[0].lower()
        options = parts[1] if len(parts) > 1 else ""
        
        # Check if the word exists in our data
        if word in self.word_data:
            # Word exists, show its information
            return self.format_word_info(word)
        else:
            # Word doesn't exist, start a background lookup
            self.app.gui_manager.set_feedback(f"Looking up information for '{word}'...")
            
            # Start a background thread to fetch word information
            thread = threading.Thread(
                target=self.fetch_word_info,
                args=(word,),
                daemon=True
            )
            thread.start()
            
            return None  # Don't return a message, the thread will update feedback
    
    def cmd_words(self, args):
        """
        Command to list or search words in the database.
        
        Args:
            args (str): Optional search pattern
            
        Returns:
            str: Result message with list of words
        """
        # If no words in database, show a message
        if not self.word_data:
            return "No words in database. Use /word <word> to add words."
        
        # If args provided, use as search pattern
        if args:
            pattern = args.lower()
            matching_words = [word for word in self.word_data if pattern in word]
            
            if not matching_words:
                return f"No words found matching '{pattern}'."
                
            word_count = len(matching_words)
            words_list = ", ".join(sorted(matching_words)[:20])
            
            if word_count > 20:
                return f"Found {word_count} words matching '{pattern}' (showing first 20):\n{words_list}"
            else:
                return f"Found {word_count} words matching '{pattern}':\n{words_list}"
        
        # No args, list all words
        word_count = len(self.word_data)
        words_list = ", ".join(sorted(self.word_data.keys())[:20])
        
        if word_count > 20:
            return f"Word database contains {word_count} words (showing first 20):\n{words_list}"
        else:
            return f"Word database contains {word_count} words:\n{words_list}"
    
    def fetch_word_info(self, word):
        """
        Fetch information for a word from various sources.
        This runs in a background thread.
        
        Args:
            word (str): The word to look up
        """
        word_info = {
            "synonyms": [],
            "antonyms": [],
            "definitions": [],
            "etymology": ""
        }
        
        success = False
        
        try:
            # Try to fetch from a dictionary API
            # For this example, we'll use a mock implementation
            # In a real implementation, you would use actual API calls
            
            # Simulate API delay
            time.sleep(1.5)
            
            # Mock data for demonstration
            if len(word) > 2:  # Simple check to avoid very short words
                success = True
                
                # Simulate data based on the word
                word_info["synonyms"] = self.mock_synonyms(word)
                word_info["antonyms"] = self.mock_antonyms(word)
                word_info["definitions"] = self.mock_definitions(word)
                word_info["etymology"] = self.mock_etymology(word)
        
        except Exception as e:
            # Update feedback with error
            self.app.gui_manager.set_feedback(f"Error fetching info for '{word}': {str(e)}")
            self.app.error_handler.log_error(f"Error fetching word info: {e}")
            return
        
        # If we got any data, save it
        if success:
            self.word_data[word] = word_info
            self.save_word_data()
            
            # Update the feedback with a success message
            self.app.gui_manager.set_feedback(f"Added information for '{word}'")
        else:
            self.app.gui_manager.set_feedback(f"Could not find information for '{word}'")
    
    def format_word_info(self, word):
        """
        Format word information for display.
        
        Args:
            word (str): The word to format
            
        Returns:
            str: Formatted word information
        """
        if word not in self.word_data:
            return f"No information found for '{word}'."
        
        info = self.word_data[word]
        result = f"Information for '{word}':\n\n"
        
        # Add definitions
        if info["definitions"]:
            result += "Definitions:\n"
            for i, definition in enumerate(info["definitions"], 1):
                result += f"{i}. {definition}\n"
            result += "\n"
        
        # Add synonyms
        if info["synonyms"]:
            result += f"Synonyms: {', '.join(info['synonyms'])}\n\n"
        
        # Add antonyms
        if info["antonyms"]:
            result += f"Antonyms: {', '.join(info['antonyms'])}\n\n"
        
        # Add etymology
        if info["etymology"]:
            result += f"Etymology: {info['etymology']}\n"
        
        return result
    
    def add_word(self, word, data):
        """
        Add or update a word in the database.
        
        Args:
            word (str): The word to add or update
            data (dict): The word information
            
        Returns:
            bool: True if successful
        """
        if not word or not isinstance(data, dict):
            return False
        
        # Ensure required fields
        required_fields = ["synonyms", "antonyms", "definitions", "etymology"]
        for field in required_fields:
            if field not in data:
                data[field] = [] if field != "etymology" else ""
        
        # Update the word data
        self.word_data[word.lower()] = data
        
        # Save the updated data
        self.save_word_data()
        
        return True
    
    def show_word_editor(self, word=None):
        """
        Show a dialog to add or edit word information.
        
        Args:
            word (str, optional): The word to edit, or None to add a new word
        """
        # Create a new toplevel window
        editor = tk.Toplevel(self.app.root)
        editor.title("Word Information Editor")
        editor.geometry("500x400")
        editor.transient(self.app.root)
        editor.grab_set()
        
        # Configure grid
        editor.columnconfigure(0, weight=0)
        editor.columnconfigure(1, weight=1)
        for i in range(6):
            editor.rowconfigure(i, weight=0)
        editor.rowconfigure(3, weight=1)  # Definitions gets extra space
        
        # Word entry
        ttk.Label(editor, text="Word:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        word_var = tk.StringVar(value=word if word else "")
        word_entry = ttk.Entry(editor, textvariable=word_var)
        word_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        
        # Synonyms
        ttk.Label(editor, text="Synonyms:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        synonyms_var = tk.StringVar(value=", ".join(self.word_data.get(word, {}).get("synonyms", [])) if word else "")
        synonyms_entry = ttk.Entry(editor, textvariable=synonyms_var)
        synonyms_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        # Antonyms
        ttk.Label(editor, text="Antonyms:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        antonyms_var = tk.StringVar(value=", ".join(self.word_data.get(word, {}).get("antonyms", [])) if word else "")
        antonyms_entry = ttk.Entry(editor, textvariable=antonyms_var)
        antonyms_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        # Definitions (Text for multiple lines)
        ttk.Label(editor, text="Definitions:").grid(row=3, column=0, sticky="nw", padx=10, pady=5)
        definitions_text = tk.Text(editor, height=6, width=40)
        definitions_text.grid(row=3, column=1, sticky="nsew", padx=10, pady=5)
        
        # Add a scrollbar for definitions
        def_scrollbar = ttk.Scrollbar(editor, command=definitions_text.yview)
        def_scrollbar.grid(row=3, column=2, sticky="ns", pady=5)
        definitions_text.config(yscrollcommand=def_scrollbar.set)
        
        # Insert existing definitions if editing a word
        if word and word in self.word_data:
            definitions = self.word_data[word].get("definitions", [])
            definitions_text.insert("1.0", "\n".join(definitions))
        
        # Etymology
        ttk.Label(editor, text="Etymology:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        etymology_var = tk.StringVar(value=self.word_data.get(word, {}).get("etymology", "") if word else "")
        etymology_entry = ttk.Entry(editor, textvariable=etymology_var)
        etymology_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(editor)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        
        # Save button
        def save_word_data():
            # Get the word
            word_text = word_var.get().strip().lower()
            if not word_text:
                messagebox.showerror("Error", "Please enter a word", parent=editor)
                return
            
            # Build the data
            word_data = {
                "synonyms": [s.strip() for s in synonyms_var.get().split(",") if s.strip()],
                "antonyms": [a.strip() for a in antonyms_var.get().split(",") if a.strip()],
                "definitions": [d for d in definitions_text.get("1.0", "end-1c").splitlines() if d.strip()],
                "etymology": etymology_var.get().strip()
            }
            
            # Add or update the word
            if self.add_word(word_text, word_data):
                self.app.gui_manager.set_feedback(f"Saved information for '{word_text}'")
                editor.destroy()
            else:
                messagebox.showerror("Error", "Failed to save word data", parent=editor)
        
        save_button = ttk.Button(buttons_frame, text="Save", command=save_word_data)
        save_button.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        # Cancel button
        cancel_button = ttk.Button(buttons_frame, text="Cancel", command=editor.destroy)
        cancel_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Focus the word entry if adding a new word, otherwise the first input field
        if not word:
            word_entry.focus()
        else:
            synonyms_entry.focus()
    
    # Mock data methods for demonstration (these would be replaced with real API calls)
    def mock_synonyms(self, word):
        """Generate mock synonyms for demonstration"""
        word_length = len(word)
        common_words = ["happy", "sad", "big", "small", "fast", "slow", "good", "bad", "hot", "cold"]
        
        if word in common_words:
            # Return known synonyms for common words
            synonyms_map = {
                "happy": ["joyful", "cheerful", "content", "pleased", "delighted"],
                "sad": ["unhappy", "sorrowful", "dejected", "gloomy", "downcast"],
                "big": ["large", "huge", "enormous", "substantial", "great"],
                "small": ["little", "tiny", "miniature", "compact", "diminutive"],
                "fast": ["quick", "speedy", "swift", "rapid", "hasty"],
                "slow": ["sluggish", "leisurely", "unhurried", "gradual", "plodding"],
                "good": ["excellent", "fine", "superior", "quality", "satisfactory"],
                "bad": ["poor", "inferior", "substandard", "inadequate", "deficient"],
                "hot": ["warm", "boiling", "scorching", "burning", "fiery"],
                "cold": ["cool", "chilly", "frigid", "icy", "frosty"]
            }
            return synonyms_map.get(word, [])
        
        # Generate random synonyms based on word characteristics
        return [f"{word[0]}{word[1:]}{chr(97 + (ord(word[0]) - 97 + i) % 26)}" for i in range(min(5, word_length))]
    
    def mock_antonyms(self, word):
        """Generate mock antonyms for demonstration"""
        common_words = ["happy", "sad", "big", "small", "fast", "slow", "good", "bad", "hot", "cold"]
        
        if word in common_words:
            # Return known antonyms for common words
            antonyms_map = {
                "happy": ["sad", "unhappy", "miserable", "depressed", "gloomy"],
                "sad": ["happy", "joyful", "cheerful", "glad", "delighted"],
                "big": ["small", "little", "tiny", "compact", "miniature"],
                "small": ["big", "large", "huge", "enormous", "gigantic"],
                "fast": ["slow", "sluggish", "leisurely", "unhurried", "gradual"],
                "slow": ["fast", "quick", "speedy", "swift", "rapid"],
                "good": ["bad", "poor", "inferior", "substandard", "inadequate"],
                "bad": ["good", "excellent", "superior", "quality", "fine"],
                "hot": ["cold", "cool", "chilly", "freezing", "icy"],
                "cold": ["hot", "warm", "heated", "boiling", "burning"]
            }
            return antonyms_map.get(word, [])
        
        # Generate a simple opposite by reversing letters or adding "not-"
        if len(word) > 3:
            return [f"not-{word}", word[::-1]]
        return []
    
    def mock_definitions(self, word):
        """Generate mock definitions for demonstration"""
        common_words = ["happy", "sad", "big", "small", "fast", "slow", "good", "bad", "hot", "cold"]
        
        if word in common_words:
            # Return known definitions for common words
            definitions_map = {
                "happy": [
                    "Feeling or showing pleasure or contentment.",
                    "Fortunate and convenient."
                ],
                "sad": [
                    "Feeling or showing sorrow; unhappy.",
                    "Causing or characterized by sorrow or regret."
                ],
                "big": [
                    "Of considerable size, extent, or intensity.",
                    "Of considerable importance or seriousness."
                ],
                "small": [
                    "Of a size that is less than normal or usual.",
                    "Limited in quantity."
                ],
                "fast": [
                    "Moving or capable of moving at high speed.",
                    "Firm or fixed in position."
                ],
                "slow": [
                    "Moving or operating at a low speed.",
                    "Taking a long time to perform a specified action."
                ],
                "good": [
                    "To be desired or approved of.",
                    "Having the qualities required for a particular role."
                ],
                "bad": [
                    "Of poor quality or a low standard.",
                    "Not such as to be hoped for or desired; unpleasant or unwelcome."
                ],
                "hot": [
                    "Having a high degree of heat or a high temperature.",
                    "Spicy or pungent in taste."
                ],
                "cold": [
                    "Of or at a low or relatively low temperature.",
                    "Lacking affection or warmth of feeling; unemotional."
                ]
            }
            return definitions_map.get(word, [])
        
        # Generate some placeholder definitions
        return [
            f"The state or quality of being {word}.",
            f"One who or that which is characterized by {word}ness."
        ]
    
    def mock_etymology(self, word):
        """Generate mock etymology for demonstration"""
        common_words = ["happy", "sad", "big", "small", "fast", "slow", "good", "bad", "hot", "cold"]
        
        if word in common_words:
            # Return known etymologies for common words
            etymology_map = {
                "happy": "From Middle English happy, from hap (chance, fortune) + -y (suffix forming adjectives).",
                "sad": "From Old English sæd (sated, tired), from Proto-Germanic *sadaz.",
                "big": "Possibly from Norwegian dialect bugge (important man).",
                "small": "From Old English smæl, from Proto-Germanic *smalaz.",
                "fast": "From Old English fæst (firmly fixed, steadfast), from Proto-Germanic *fastuz.",
                "slow": "From Old English slaw, from Proto-Germanic *slæwaz.",
                "good": "From Old English gōd, from Proto-Germanic *gōdaz.",
                "bad": "Origin uncertain, possibly from Old English bæddel (hermaphrodite).",
                "hot": "From Old English hāt, from Proto-Germanic *haitaz.",
                "cold": "From Old English cald, ceald, from Proto-Germanic *kaldaz."
            }
            return etymology_map.get(word, "")
        
        # Generate a simple placeholder etymology
        vowels = "aeiou"
        if any(v in word for v in vowels):
            return f"From Old English {word[0]}æ{word[1:]} or Latin {word}us."
        else:
            return f"Origin uncertain, possibly from Proto-Germanic *{word}az."