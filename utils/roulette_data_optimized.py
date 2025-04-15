"""
Optimized version of RouletteData class with performance improvements
for adding data more efficiently.
"""
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import time

class RouletteData:
    """
    Class to handle roulette data storage, retrieval, and manipulation.
    Optimized for better performance when adding multiple spins.
    
    Features:
    - Batch saving with configurable auto-save intervals
    - Optimized data structures for faster access
    - Improved performance for high-frequency updates
    """
    def __init__(self):
        # Initialize with empty sessions dictionary
        self.sessions = {}
        self.session_types = {}
        self.data_file = "roulette_data.json"
        
        # For optimization - only save after a certain number of updates
        self.changes_since_save = 0
        self.auto_save_threshold = 5  # Save after every 5 changes
        self.last_save_time = time.time()
        self.save_interval = 5  # Save at least every 5 seconds
        
        # Cache for common properties to avoid recalculation
        self._property_cache = {}
        
        # Pre-compute number properties
        self._precompute_properties()
        
        # Automatically load saved data on initialization
        self.load_data()
        
    def _precompute_properties(self):
        """
        Pre-compute properties for all possible roulette numbers
        to avoid recalculation every time a spin is added.
        """
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        
        # Regular numbers 0-36
        for i in range(37):
            num_str = str(i)
            properties = {}
            
            # Color (red, black, green)
            if i == 0:
                properties["color"] = "green"
            elif i in red_numbers:
                properties["color"] = "red"
            else:
                properties["color"] = "black"
                
            # Even/odd
            if i == 0:
                properties["parity"] = "zero"
            elif i % 2 == 0:
                properties["parity"] = "even"
            else:
                properties["parity"] = "odd"
                
            # Dozen (1-12, 13-24, 25-36)
            if i == 0:
                properties["dozen"] = "zero"
            elif i <= 12:
                properties["dozen"] = "first"
            elif i <= 24:
                properties["dozen"] = "second"
            else:
                properties["dozen"] = "third"
                
            # Column
            if i == 0:
                properties["column"] = "zero"
            elif i % 3 == 1:
                properties["column"] = "first"
            elif i % 3 == 2:
                properties["column"] = "second"
            elif i % 3 == 0:
                properties["column"] = "third"
                
            # High/low
            if i == 0:
                properties["range"] = "zero"
            elif i <= 18:
                properties["range"] = "low"
            else:
                properties["range"] = "high"
                
            # Store in cache
            self._property_cache[num_str] = properties
            
        # Handle 00 for American roulette
        properties = {
            "color": "green",
            "parity": "zero",
            "dozen": "zero",
            "column": "zero",
            "range": "zero"
        }
        self._property_cache["00"] = properties
        
    def create_session(self, session_name, roulette_type):
        """
        Create a new session with the specified name and roulette type.
        
        Args:
            session_name (str): Name of the session
            roulette_type (str): Type of roulette - 'European' or 'American'
        """
        self.sessions[session_name] = []
        self.session_types[session_name] = roulette_type
        
        # Mark as changed and check for auto-save
        self._mark_changed()
        
    def add_spin(self, session_name, number, timestamp=None):
        """
        Add a spin result to a session with improved performance.
        
        Args:
            session_name (str): Name of the session
            number (str or int): The number that came up (0, 00, 1-36)
            timestamp (datetime, optional): Timestamp of the spin. Defaults to current time.
            
        Returns:
            bool: True if successful
        """
        # Create session if it doesn't exist
        if session_name not in self.sessions:
            self.create_session(session_name, "European")
            
        # Use current time if no timestamp provided
        if timestamp is None:
            timestamp = datetime.now()
            
        # Convert number to string if it's not already
        number = str(number)
        
        # Get number properties from pre-computed cache (faster)
        properties = self._property_cache.get(number, self._get_number_properties(number))
        
        # Add the spin to the session
        spin_data = {
            "number": number,
            "timestamp": timestamp.isoformat(),
            "properties": properties
        }
        
        # Add to session data
        self.sessions[session_name].append(spin_data)
        
        # Mark as changed and check for auto-save
        self._mark_changed()
        
        return True
    
    def _mark_changed(self):
        """
        Mark data as changed and trigger auto-save based on threshold or time interval.
        This improves performance by batching saves instead of saving after every change.
        """
        self.changes_since_save += 1
        current_time = time.time()
        
        # Save if we've hit the threshold or time interval
        if (self.changes_since_save >= self.auto_save_threshold or 
            current_time - self.last_save_time >= self.save_interval):
            self.save_data()
            self.changes_since_save = 0
            self.last_save_time = current_time
    
    def _get_number_properties(self, number):
        """
        Get properties of a roulette number.
        Used as a fallback if not in cache or for custom numbers.
        
        Args:
            number (str): The roulette number
            
        Returns:
            dict: Properties of the number
        """
        # Define properties for each number
        properties = {}
        
        # Convert number to int for comparison
        try:
            num = int(number)
        except ValueError:
            if number == "00":
                num = -1  # Special case for 00
            else:
                num = 0  # Default to 0 for invalid numbers
        
        # Color (red, black, green)
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        if num == 0 or num == -1:  # 0 or 00
            properties["color"] = "green"
        elif num in red_numbers:
            properties["color"] = "red"
        else:
            properties["color"] = "black"
            
        # Even/odd
        if num == 0 or num == -1:  # 0 or 00
            properties["parity"] = "zero"
        elif num % 2 == 0:
            properties["parity"] = "even"
        else:
            properties["parity"] = "odd"
            
        # Dozen (1-12, 13-24, 25-36)
        if num == 0 or num == -1:  # 0 or 00
            properties["dozen"] = "zero"
        elif num <= 12:
            properties["dozen"] = "first"
        elif num <= 24:
            properties["dozen"] = "second"
        else:
            properties["dozen"] = "third"
            
        # Column
        if num == 0 or num == -1:  # 0 or 00
            properties["column"] = "zero"
        elif num % 3 == 1:
            properties["column"] = "first"
        elif num % 3 == 2:
            properties["column"] = "second"
        elif num % 3 == 0:
            properties["column"] = "third"
            
        # High/low
        if num == 0 or num == -1:  # 0 or 00
            properties["range"] = "zero"
        elif num <= 18:
            properties["range"] = "low"
        else:
            properties["range"] = "high"
            
        return properties
    
    def get_session_data(self, session_name):
        """
        Get spin data for a session as a pandas DataFrame.
        
        Args:
            session_name (str): Name of the session
            
        Returns:
            pandas.DataFrame: DataFrame with spin data
        """
        if session_name not in self.sessions:
            return None
            
        # Convert the session data to a DataFrame
        df = pd.DataFrame(self.sessions[session_name])
        
        # Convert timestamp strings to datetime objects
        if not df.empty and 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        return df
    
    def get_session_type(self, session_name):
        """
        Get the type of roulette for a session.
        
        Args:
            session_name (str): Name of the session
            
        Returns:
            str: Type of roulette - 'European' or 'American'
        """
        return self.session_types.get(session_name, "European")
    
    def get_sessions(self):
        """
        Get a list of all session names.
        
        Returns:
            list: List of session names
        """
        return list(self.sessions.keys())
    
    def clear_spin_history(self, session_name):
        """
        Clear all spin history for a session.
        
        Args:
            session_name (str): Name of the session
        """
        if session_name in self.sessions:
            # Keep the session but clear all spins
            self.sessions[session_name] = []
            
            # Ensure data is saved
            self.save_data()
    
    def delete_session(self, session_name):
        """
        Delete a session entirely.
        
        Args:
            session_name (str): Name of the session
        """
        if session_name in self.sessions:
            # Remove the session
            del self.sessions[session_name]
            del self.session_types[session_name]
            
            # Ensure data is saved
            self.save_data()
    
    def remove_last_spin(self, session_name):
        """
        Remove the last spin from a session.
        
        Args:
            session_name (str): Name of the session
        """
        if session_name in self.sessions and self.sessions[session_name]:
            # Remove the last spin
            self.sessions[session_name].pop()
            
            # Mark as changed and check for auto-save
            self._mark_changed()
    
    def save_data(self):
        """
        Save all session data to a JSON file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert data to serializable format
            data = {
                "sessions": self.sessions,
                "session_types": self.session_types
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f)
            
            # Reset the changes counter and update last save time
            self.changes_since_save = 0
            self.last_save_time = time.time()
                
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def load_data(self):
        """
        Load session data from a JSON file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.data_file):
                # No existing data file, start fresh
                return False
                
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                
            # Update session data
            self.sessions = data.get("sessions", {})
            self.session_types = data.get("session_types", {})
            
            # Reset the changes counter
            self.changes_since_save = 0
            self.last_save_time = time.time()
                
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            # Start fresh with empty data on error
            self.sessions = {}
            self.session_types = {}
            return False