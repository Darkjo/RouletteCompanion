import json
import os
from datetime import datetime

class DataManager:
    """
    Handles data storage and retrieval for the roulette tracker application.
    Manages session data and spin history.
    """
    
    def __init__(self):
        """
        Initialize the data manager with in-memory session data storage.
        """
        self.sessions = {}
    
    def create_session(self, session_name, roulette_type="European"):
        """
        Create a new roulette tracking session.
        
        Args:
            session_name (str): The name of the session
            roulette_type (str): The type of roulette ("European" or "American")
        """
        if session_name not in self.sessions:
            self.sessions[session_name] = {
                'created_at': datetime.now().isoformat(),
                'roulette_type': roulette_type,
                'spins': []
            }
    
    def get_session_data(self, session_name):
        """
        Get the data for a specific session.
        
        Args:
            session_name (str): The name of the session
            
        Returns:
            dict: The session data or empty dict if not found
        """
        if session_name in self.sessions:
            return self.sessions[session_name]
        return {}
    
    def add_spin(self, session_name, spin_data):
        """
        Add a spin result to a session.
        
        Args:
            session_name (str): The name of the session
            spin_data (dict): The spin result data
        """
        if session_name in self.sessions:
            self.sessions[session_name]['spins'].append(spin_data)
    
    def get_spin_history(self, session_name):
        """
        Get the spin history for a session.
        
        Args:
            session_name (str): The name of the session
            
        Returns:
            list: The list of spin results
        """
        if session_name in self.sessions:
            return self.sessions[session_name]['spins']
        return []
    
    def clear_spin_history(self, session_name):
        """
        Clear the spin history for a session.
        
        Args:
            session_name (str): The name of the session
        """
        if session_name in self.sessions:
            self.sessions[session_name]['spins'] = []
    
    def delete_session(self, session_name):
        """
        Delete a session.
        
        Args:
            session_name (str): The name of the session
        """
        if session_name in self.sessions:
            del self.sessions[session_name]
    
    def get_all_sessions(self):
        """
        Get a list of all session names.
        
        Returns:
            list: List of session names
        """
        return list(self.sessions.keys())
    
    def export_session_data(self, session_name):
        """
        Export session data to JSON format.
        
        Args:
            session_name (str): The name of the session
            
        Returns:
            str: JSON string of the session data
        """
        if session_name in self.sessions:
            return json.dumps(self.sessions[session_name], indent=2)
        return "{}"
    
    def import_session_data(self, session_name, json_data):
        """
        Import session data from JSON format.
        
        Args:
            session_name (str): The name for the imported session
            json_data (str): JSON string containing session data
        """
        try:
            data = json.loads(json_data)
            self.sessions[session_name] = data
            return True
        except json.JSONDecodeError:
            return False
