"""
File import functionality for roulette data
"""
import streamlit as st
import pandas as pd
from datetime import datetime

def create_file_importer():
    """
    Create a file import widget for roulette spins data.
    
    Returns:
        pd.DataFrame or None: Imported spin data or None if no import
    """
    st.subheader("Import Spin Data from File")
    
    st.write("""
    Upload a CSV or Excel file with your spin data. The file should have at least a 'number' column.
    Optionally, it can also have a 'timestamp' column.
    """)
    
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            # Determine file type by extension
            file_name = uploaded_file.name.lower()
            if file_name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:  # Excel
                df = pd.read_excel(uploaded_file)
            
            # Validate required columns
            if 'number' not in df.columns:
                st.error("The file must contain a 'number' column.")
                return None
            
            # If timestamp column doesn't exist, add it with current timestamp
            if 'timestamp' not in df.columns:
                df['timestamp'] = datetime.now()
            
            # Display preview
            st.subheader("Data Preview:")
            st.dataframe(df.head())
            
            if st.button("Import Data"):
                return df
                
        except Exception as e:
            st.error(f"Error importing file: {str(e)}")
    
    return None