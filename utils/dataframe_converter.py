"""
Utilities for converting nested dictionary data to flat dataframes.
This helps avoid the "unhashable type: 'dict'" error when working with pandas.
"""
import pandas as pd

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