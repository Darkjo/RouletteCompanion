"""
Utilities for converting nested dictionary data to flat dataframes.
This helps avoid the "unhashable type: 'dict'" error when working with pandas.
"""
import pandas as pd
import functools
import inspect

def extract_properties_to_columns(df):
    """
    Extract property values from nested dictionary into separate columns.
    This allows pandas to work with the data more effectively.
    
    Args:
        df (pd.DataFrame): DataFrame with nested 'properties' column
        
    Returns:
        pd.DataFrame: DataFrame with properties extracted to columns
    """
    if df is None or df.empty or 'properties' not in df.columns:
        return df
    
    # Create a copy to avoid modifying the original
    result_df = df.copy()
    
    # Extract common properties
    property_keys = ['color', 'parity', 'dozen', 'column', 'range']
    
    for key in property_keys:
        result_df[key] = result_df['properties'].apply(
            lambda props: props.get(key, 'unknown') if isinstance(props, dict) else 'unknown'
        )
    
    return result_df

def clean_dataframe_for_analysis(df):
    """
    Prepare a dataframe for analysis by extracting properties and 
    ensuring all columns have hashable values.
    
    Args:
        df (pd.DataFrame): DataFrame to clean
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    if df is None or df.empty:
        return df
    
    # First extract properties to columns
    result_df = extract_properties_to_columns(df)
    
    # Remove the original properties column to avoid unhashable values
    if 'properties' in result_df.columns:
        result_df = result_df.drop(columns=['properties'])
    
    return result_df

def with_clean_dataframe(func):
    """
    A decorator that automatically cleans any pandas DataFrame arguments
    before passing them to the decorated function.
    
    This is useful for methods that might receive DataFrames with nested dictionaries
    which can cause "unhashable type: 'dict'" errors.
    
    Args:
        func: The function to decorate
    
    Returns:
        The decorated function that automatically cleans DataFrames
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get the function's signature
        sig = inspect.signature(func)
        params = sig.parameters
        
        # Create a new list of args with cleaned DataFrames
        new_args = []
        for i, arg in enumerate(args):
            # Skip self/cls for methods
            if i == 0 and len(args) > 0 and inspect.ismethod(func):
                new_args.append(arg)
                continue
                
            # Check if the argument is a DataFrame
            if isinstance(arg, pd.DataFrame):
                new_args.append(clean_dataframe_for_analysis(arg))
            else:
                new_args.append(arg)
        
        # Create a new dict of kwargs with cleaned DataFrames
        new_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, pd.DataFrame):
                new_kwargs[key] = clean_dataframe_for_analysis(value)
            else:
                new_kwargs[key] = value
        
        # Call the original function with cleaned args
        return func(*new_args, **new_kwargs)
    
    return wrapper