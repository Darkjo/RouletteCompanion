"""
DataFrame Converter Module
Provides utilities for handling and cleaning dataframes
"""

import pandas as pd
import numpy as np
from functools import wraps
from typing import Callable, Any, Dict


def with_clean_dataframe(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that ensures the dataframe is properly formatted before processing.
    
    Args:
        func (Callable): The function to decorate
        
    Returns:
        Callable: The decorated function
    """
    @wraps(func)
    def wrapper(self, df: pd.DataFrame, *args, **kwargs) -> Any:
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Ensure the dataframe has the expected columns
        required_columns = ['number', 'color', 'parity', 'range', 'dozen', 'column', 'timestamp']
        for col in required_columns:
            if col not in df.columns:
                if col == 'timestamp':
                    df[col] = pd.Timestamp.now()
                else:
                    df[col] = None
        
        # Convert 'number' column to string if it exists
        if 'number' in df.columns:
            df['number'] = df['number'].astype(str)
        
        # Call the original function with the cleaned dataframe
        return func(self, df, *args, **kwargs)
    
    return wrapper