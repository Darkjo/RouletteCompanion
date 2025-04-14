import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

class RouletteData:
    """
    Class to handle roulette data storage, retrieval, and manipulation.
    """
    def __init__(self):
        # Initialize with empty sessions dictionary
        self.sessions = {}
        self.session_types = {}
        self.data_file = "roulette_data.json"
        
    def create_session(self, session_name, roulette_type):
        """
        Create a new session with the specified name and roulette type.
        
        Args:
            session_name (str): Name of the session
            roulette_type (str): Type of roulette - 'European' or 'American'
        """
        if session_name not in self.sessions:
            self.sessions[session_name] = []
            self.session_types[session_name] = roulette_type
            return True
        return False
    
    def delete_session(self, session_name):
        """
        Delete a session by name.
        
        Args:
            session_name (str): Name of the session to delete
        """
        if session_name in self.sessions:
            del self.sessions[session_name]
            del self.session_types[session_name]
            return True
        return False
    
    def add_spin(self, session_name, number, timestamp=None):
        """
        Add a spin result to a session.
        
        Args:
            session_name (str): Name of the session
            number (str or int): The number that came up (0, 00, 1-36)
            timestamp (datetime, optional): Timestamp of the spin. Defaults to current time.
        """
        if session_name not in self.sessions:
            self.create_session(session_name, "European")
            
        if timestamp is None:
            timestamp = datetime.now()
            
        # Convert number to string if it's not already
        number = str(number)
        
        # Add the spin to the session
        spin_data = {
            "number": number,
            "timestamp": timestamp.isoformat(),
            "properties": self._get_number_properties(number)
        }
        
        self.sessions[session_name].append(spin_data)
        return True
    
    def remove_last_spin(self, session_name):
        """
        Remove the last spin from a session.
        
        Args:
            session_name (str): Name of the session
        """
        if session_name in self.sessions and self.sessions[session_name]:
            self.sessions[session_name].pop()
            return True
        return False
    
    def get_session_data(self, session_name):
        """
        Get a DataFrame of the spin data for a session.
        
        Args:
            session_name (str): Name of the session
            
        Returns:
            pd.DataFrame: DataFrame with spin data or None if session doesn't exist
        """
        if session_name not in self.sessions:
            return None
            
        if not self.sessions[session_name]:
            return pd.DataFrame(columns=["number", "timestamp", "color", "even_odd", "high_low", "dozen", "column"])
            
        # Convert the session data to a DataFrame
        spins = []
        for spin in self.sessions[session_name]:
            spin_dict = {
                "number": spin["number"],
                "timestamp": datetime.fromisoformat(spin["timestamp"]),
                "color": spin["properties"]["color"],
                "even_odd": spin["properties"]["even_odd"],
                "high_low": spin["properties"]["high_low"],
                "dozen": spin["properties"]["dozen"],
                "column": spin["properties"]["column"]
            }
            spins.append(spin_dict)
            
        return pd.DataFrame(spins)
    
    def get_session_type(self, session_name):
        """
        Get the roulette type for a session.
        
        Args:
            session_name (str): Name of the session
            
        Returns:
            str: 'European' or 'American'
        """
        if session_name in self.session_types:
            return self.session_types[session_name]
        return "European"  # Default to European
    
    def get_sessions(self):
        """
        Get a list of all session names.
        
        Returns:
            list: List of session names
        """
        return list(self.sessions.keys())
    
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
                return False
                
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                
            self.sessions = data.get("sessions", {})
            self.session_types = data.get("session_types", {})
            
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def _get_number_properties(self, number):
        """
        Calculate properties of a roulette number.
        
        Args:
            number (str): The roulette number
            
        Returns:
            dict: Properties of the number
        """
        # Convert number to string if it's not already
        number = str(number)
        
        # Define properties
        properties = {}
        
        # Zero and double zero are special cases
        if number == '0' or number == '00':
            properties["color"] = "green"
            properties["even_odd"] = "none"
            properties["high_low"] = "none"
            properties["dozen"] = "none"
            properties["column"] = "none"
            return properties
        
        # Convert to integer for other calculations
        num = int(number)
        
        # Determine color (red or black)
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        properties["color"] = "red" if num in red_numbers else "black"
        
        # Even or odd
        properties["even_odd"] = "even" if num % 2 == 0 else "odd"
        
        # High (19-36) or low (1-18)
        properties["high_low"] = "high" if num >= 19 else "low"
        
        # Determine dozen (1-12, 13-24, 25-36)
        if 1 <= num <= 12:
            properties["dozen"] = "first"
        elif 13 <= num <= 24:
            properties["dozen"] = "second"
        else:
            properties["dozen"] = "third"
        
        # Determine column
        if num % 3 == 1:
            properties["column"] = "first"
        elif num % 3 == 2:
            properties["column"] = "second"
        else:  # num % 3 == 0
            properties["column"] = "third"
        
        return properties
