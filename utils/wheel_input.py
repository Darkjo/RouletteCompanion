"""
Visual Roulette Wheel Input Component
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random  # Import random here instead of importing in multiple functions

def create_roulette_wheel_input(roulette_type="European"):
    """
    Create a visual roulette wheel for input.
    
    Args:
        roulette_type (str): Type of roulette - 'European' or 'American'
        
    Returns:
        str or None: Selected number or None if no selection was made
    """
    # Define wheel numbers and colors
    if roulette_type == "European":
        wheel_numbers = [
            '0', '32', '15', '19', '4', '21', '2', '25', '17', '34', '6', 
            '27', '13', '36', '11', '30', '8', '23', '10', '5', '24', '16', 
            '33', '1', '20', '14', '31', '9', '22', '18', '29', '7', '28', 
            '12', '35', '3', '26'
        ]
    else:  # American
        wheel_numbers = [
            '0', '28', '9', '26', '30', '11', '7', '20', '32', '17', '5', 
            '22', '34', '15', '3', '24', '36', '13', '1', '00', '27', '10', 
            '25', '29', '12', '8', '19', '31', '18', '6', '21', '33', '16', 
            '4', '23', '35', '14', '2'
        ]
    
    # Define colors for each number
    colors = {}
    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    for num in wheel_numbers:
        if num == '0' or num == '00':
            colors[num] = 'green'
        elif int(num) in red_numbers:
            colors[num] = 'red'
        else:
            colors[num] = 'black'
    
    # Create visual wheel with three tabs: Wheel, Quick Bets, and Manual Entry
    tab1, tab2, tab3 = st.tabs(["Visual Wheel", "Quick Picks", "Manual Entry"])
    
    selected_number = None
    
    with tab1:
        st.write("Click on the wheel sector to select a number:")
        
        # Create a circular layout
        num_sectors = len(wheel_numbers)
        angles = np.linspace(0, 2*np.pi, num_sectors, endpoint=False)
        
        # Create a polar chart for the wheel
        fig = go.Figure()
        
        # Add sectors
        for i, (num, angle) in enumerate(zip(wheel_numbers, angles)):
            # Add sector as marker
            next_angle = angles[(i+1) % num_sectors]
            angle_range = np.linspace(angle, next_angle, 20)
            fig.add_trace(go.Scatterpolar(
                r=[0.9] * len(angle_range),
                theta=np.degrees(angle_range),
                mode='lines',
                fill='toself',
                fillcolor=colors[num],
                line=dict(color='white', width=1),
                name=num,
                hoverinfo='name'
            ))
            
            # Add number labels
            mid_angle = (angle + next_angle) / 2
            fig.add_trace(go.Scatterpolar(
                r=[0.7],
                theta=[np.degrees(mid_angle)],
                mode='text',
                text=[num],
                textfont=dict(color='white', size=12),
                hoverinfo='skip',
                name=''
            ))
        
        # Update layout for nice wheel appearance
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=False),
                angularaxis=dict(visible=False)
            ),
            showlegend=False,
            margin=dict(t=0, b=0, l=0, r=0),
            height=600,
            width=600
        )
        
        # Use Streamlit's experimental plotly events to capture clicks
        # Since this isn't supported directly, we'll use a workaround with buttons
        st.plotly_chart(fig)
        
        # Create a grid of buttons for number selection
        st.subheader("Select a number:")
        
        # Create a grid layout of numbers
        cols = st.columns(6)
        for i, num in enumerate(sorted(wheel_numbers, key=lambda x: int(0 if x == '00' else x))):
            col_idx = i % 6
            if cols[col_idx].button(
                num, 
                key=f"wheel_btn_{num}",
                use_container_width=True,
                type="primary" if colors[num] == "green" else "secondary"
            ):
                selected_number = num
    
    with tab2:
        st.write("Quick selection options:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔴 Red Number", use_container_width=True):
                # Select a random red number
                red_nums = [str(num) for num in red_numbers]
                selected_number = random.choice(red_nums)
            
            if st.button("⚫ Black Number", use_container_width=True):
                # Select a random black number
                black_nums = [n for n in wheel_numbers if n != '0' and n != '00' and n not in [str(num) for num in red_numbers]]
                selected_number = random.choice(black_nums)
            
            if st.button("Even Number", use_container_width=True):
                # Select a random even number
                even_nums = [str(num) for num in range(2, 37, 2)]
                selected_number = random.choice(even_nums)
                
        with col2:
            if st.button("Odd Number", use_container_width=True):
                # Select a random odd number
                odd_nums = [str(num) for num in range(1, 37, 2)]
                selected_number = random.choice(odd_nums)
            
            if st.button("Green (0)", use_container_width=True):
                selected_number = '0'
                
            if roulette_type == "American":
                if st.button("Green (00)", use_container_width=True):
                    selected_number = '00'
        
        # Quick number groups
        st.subheader("Number Groups:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("1-12 (First Dozen)", use_container_width=True):
                first_dozen = [str(num) for num in range(1, 13)]
                selected_number = random.choice(first_dozen)
                
        with col2:
            if st.button("13-24 (Second Dozen)", use_container_width=True):
                second_dozen = [str(num) for num in range(13, 25)]
                selected_number = random.choice(second_dozen)
                
        with col3:
            if st.button("25-36 (Third Dozen)", use_container_width=True):
                third_dozen = [str(num) for num in range(25, 37)]
                selected_number = random.choice(third_dozen)
                
    with tab3:
        st.write("Enter the spin result manually:")
        
        if roulette_type == "European":
            manual_num = st.number_input("Spin Result (0-36):", min_value=-1, max_value=36, step=1, value=-1)
            if manual_num >= 0:
                selected_number = str(manual_num)
        else:  # American
            manual_options = ["Select"] + ["00"] + [str(i) for i in range(37)]
            manual_selection = st.selectbox("Spin Result:", manual_options)
            if manual_selection != "Select":
                selected_number = manual_selection
                
    # Display the selected number if any
    if selected_number:
        color = colors.get(selected_number, 'green')
        st.success(f"Selected number: {selected_number} ({color})")
    
    return selected_number

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