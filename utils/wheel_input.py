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
        st.write("Select a number from the roulette wheel:")
        
        # Create a more reliable visual representation using a grid layout
        st.write("### Roulette Wheel Layout")
        
        # Display a more aesthetic header explaining the wheel
        st.markdown("""
        <style>
        .wheel-header {
            background-color: #1E1E1E;
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="wheel-header">
            <h4 style="color: white; margin: 0;">🎰 Standard {0} Roulette Wheel 🎰</h4>
        </div>
        """.format(roulette_type), unsafe_allow_html=True)
        
        # Create a visual grid representation of the wheel
        # We'll arrange the numbers in concentric circular patterns
        
        # For European wheel
        if roulette_type == "European":
            # Green (0) in the center
            center_col = st.columns(3)
            with center_col[1]:
                if st.button("0", key="wheel_center_0", 
                            use_container_width=True,
                            type="primary"):
                    selected_number = "0"
            
            # First inner circle (red and black alternating)
            st.write("##### Inner Circle")
            inner_cols = st.columns(6)
            inner_numbers = ["32", "15", "19", "4", "21", "2"]
            for i, num in enumerate(inner_numbers):
                button_type = "primary" if colors[num] == "green" else "secondary"
                button_color = "red" if int(num) in red_numbers else "black"
                with inner_cols[i]:
                    if st.button(f"{num} ({button_color})", key=f"wheel_inner_{num}", 
                               use_container_width=True,
                               type=button_type):
                        selected_number = num
            
            # Second circle
            st.write("##### Middle Circle")
            middle_cols1 = st.columns(6)
            middle_numbers1 = ["25", "17", "34", "6", "27", "13"]
            for i, num in enumerate(middle_numbers1):
                button_type = "primary" if colors[num] == "green" else "secondary"
                button_color = "red" if int(num) in red_numbers else "black"
                with middle_cols1[i]:
                    if st.button(f"{num} ({button_color})", key=f"wheel_middle1_{num}", 
                               use_container_width=True,
                               type=button_type):
                        selected_number = num
            
            middle_cols2 = st.columns(6)
            middle_numbers2 = ["36", "11", "30", "8", "23", "10"]
            for i, num in enumerate(middle_numbers2):
                button_type = "primary" if colors[num] == "green" else "secondary"
                button_color = "red" if int(num) in red_numbers else "black"
                with middle_cols2[i]:
                    if st.button(f"{num} ({button_color})", key=f"wheel_middle2_{num}", 
                               use_container_width=True,
                               type=button_type):
                        selected_number = num
            
            # Outer circle
            st.write("##### Outer Circle")
            outer_cols1 = st.columns(6)
            outer_numbers1 = ["5", "24", "16", "33", "1", "20"]
            for i, num in enumerate(outer_numbers1):
                button_type = "primary" if colors[num] == "green" else "secondary"
                button_color = "red" if int(num) in red_numbers else "black"
                with outer_cols1[i]:
                    if st.button(f"{num} ({button_color})", key=f"wheel_outer1_{num}", 
                               use_container_width=True,
                               type=button_type):
                        selected_number = num
            
            outer_cols2 = st.columns(6)
            outer_numbers2 = ["14", "31", "9", "22", "18", "29"]
            for i, num in enumerate(outer_numbers2):
                button_type = "primary" if colors[num] == "green" else "secondary"
                button_color = "red" if int(num) in red_numbers else "black"
                with outer_cols2[i]:
                    if st.button(f"{num} ({button_color})", key=f"wheel_outer2_{num}", 
                               use_container_width=True,
                               type=button_type):
                        selected_number = num
            
            outer_cols3 = st.columns(6)
            outer_numbers3 = ["7", "28", "12", "35", "3", "26"]
            for i, num in enumerate(outer_numbers3):
                button_type = "primary" if colors[num] == "green" else "secondary"
                button_color = "red" if int(num) in red_numbers else "black"
                with outer_cols3[i]:
                    if st.button(f"{num} ({button_color})", key=f"wheel_outer3_{num}", 
                               use_container_width=True,
                               type=button_type):
                        selected_number = num
                        
        # For American wheel
        else:
            # Green (0 and 00) in the center
            center_cols = st.columns(4)
            with center_cols[1]:
                if st.button("0", key="wheel_center_0", 
                           use_container_width=True,
                           type="primary"):
                    selected_number = "0"
            with center_cols[2]:
                if st.button("00", key="wheel_center_00", 
                           use_container_width=True,
                           type="primary"):
                    selected_number = "00"
            
            # Create rows of numbers for American wheel layout
            st.write("##### First Row")
            row1_cols = st.columns(6)
            row1_numbers = ["28", "9", "26", "30", "11", "7"]
            for i, num in enumerate(row1_numbers):
                button_type = "primary" if colors[num] == "green" else "secondary"
                button_color = "red" if int(num) in red_numbers else "black"
                with row1_cols[i]:
                    if st.button(f"{num} ({button_color})", key=f"wheel_row1_{num}", 
                               use_container_width=True,
                               type=button_type):
                        selected_number = num
            
            st.write("##### Second Row")
            row2_cols = st.columns(6)
            row2_numbers = ["20", "32", "17", "5", "22", "34"]
            for i, num in enumerate(row2_numbers):
                button_type = "primary" if colors[num] == "green" else "secondary"
                button_color = "red" if int(num) in red_numbers else "black"
                with row2_cols[i]:
                    if st.button(f"{num} ({button_color})", key=f"wheel_row2_{num}", 
                               use_container_width=True,
                               type=button_type):
                        selected_number = num
            
            st.write("##### Third Row")
            row3_cols = st.columns(6)
            row3_numbers = ["15", "3", "24", "36", "13", "1"]
            for i, num in enumerate(row3_numbers):
                button_type = "primary" if colors[num] == "green" else "secondary"
                button_color = "red" if int(num) in red_numbers else "black"
                with row3_cols[i]:
                    if st.button(f"{num} ({button_color})", key=f"wheel_row3_{num}", 
                               use_container_width=True,
                               type=button_type):
                        selected_number = num
            
            st.write("##### Fourth Row")
            row4_cols = st.columns(6)
            row4_numbers = ["27", "10", "25", "29", "12", "8"]
            for i, num in enumerate(row4_numbers):
                button_type = "primary" if colors[num] == "green" else "secondary"
                button_color = "red" if int(num) in red_numbers else "black"
                with row4_cols[i]:
                    if st.button(f"{num} ({button_color})", key=f"wheel_row4_{num}", 
                               use_container_width=True,
                               type=button_type):
                        selected_number = num
            
            st.write("##### Fifth Row")
            row5_cols = st.columns(6)
            row5_numbers = ["19", "31", "18", "6", "21", "33"]
            for i, num in enumerate(row5_numbers):
                button_type = "primary" if colors[num] == "green" else "secondary"
                button_color = "red" if int(num) in red_numbers else "black"
                with row5_cols[i]:
                    if st.button(f"{num} ({button_color})", key=f"wheel_row5_{num}", 
                               use_container_width=True,
                               type=button_type):
                        selected_number = num
            
            st.write("##### Sixth Row")
            row6_cols = st.columns(6)
            row6_numbers = ["16", "4", "23", "35", "14", "2"]
            for i, num in enumerate(row6_numbers):
                button_type = "primary" if colors[num] == "green" else "secondary"
                button_color = "red" if int(num) in red_numbers else "black"
                with row6_cols[i]:
                    if st.button(f"{num} ({button_color})", key=f"wheel_row6_{num}", 
                               use_container_width=True,
                               type=button_type):
                        selected_number = num
        
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