"""
Live Casino Input methods for fast data entry from physical or online casinos
"""
import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
import time

def create_live_casino_panel(session_name, roulette_data, roulette_type="European"):
    """
    Create a specialized panel for recording spins from a live casino setting.
    
    Args:
        session_name (str): The name of the current session
        roulette_data: The roulette data instance to store spins
        roulette_type (str): Type of roulette - 'European' or 'American'
    """
    st.subheader("🎰 Live Casino Input")
    
    # Create tabs for different input methods
    input_tabs = st.tabs(["Numeric Pad", "Recent Numbers", "Last Calls"])
    
    with input_tabs[0]:
        create_numeric_pad(session_name, roulette_data)
    
    with input_tabs[1]:
        create_recent_numbers_tracker(session_name, roulette_data, roulette_type)
    
    with input_tabs[2]:
        create_last_calls_tracker(session_name, roulette_data, roulette_type)

def create_numeric_pad(session_name, roulette_data):
    """
    Create a numeric keypad for quick number entry.
    
    Args:
        session_name (str): The name of the current session
        roulette_data: The roulette data instance to store spins
    """
    st.write("Enter numbers using the keypad:")
    
    # Create a text input for displaying the current number
    if "numeric_buffer" not in st.session_state:
        st.session_state.numeric_buffer = ""
    
    # Display the current buffer
    number_display = st.empty()
    number_display.markdown(f"## Current Entry: {st.session_state.numeric_buffer}")
    
    # Create 4 rows of buttons
    # Row 1: 7, 8, 9
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("7", key="num_7", use_container_width=True):
            st.session_state.numeric_buffer += "7"
    with col2:
        if st.button("8", key="num_8", use_container_width=True):
            st.session_state.numeric_buffer += "8"
    with col3:
        if st.button("9", key="num_9", use_container_width=True):
            st.session_state.numeric_buffer += "9"
    
    # Row 2: 4, 5, 6
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("4", key="num_4", use_container_width=True):
            st.session_state.numeric_buffer += "4"
    with col2:
        if st.button("5", key="num_5", use_container_width=True):
            st.session_state.numeric_buffer += "5"
    with col3:
        if st.button("6", key="num_6", use_container_width=True):
            st.session_state.numeric_buffer += "6"
    
    # Row 3: 1, 2, 3
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("1", key="num_1", use_container_width=True):
            st.session_state.numeric_buffer += "1"
    with col2:
        if st.button("2", key="num_2", use_container_width=True):
            st.session_state.numeric_buffer += "2"
    with col3:
        if st.button("3", key="num_3", use_container_width=True):
            st.session_state.numeric_buffer += "3"
    
    # Row 4: 0, 00, Clear
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("0", key="num_0", use_container_width=True):
            st.session_state.numeric_buffer += "0"
    with col2:
        if st.button("00", key="num_00", use_container_width=True):
            st.session_state.numeric_buffer = "00"
    with col3:
        if st.button("Clear", key="num_clear", use_container_width=True):
            st.session_state.numeric_buffer = ""
    
    # Add number or submit
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit", key="num_submit", use_container_width=True, type="primary"):
            if st.session_state.numeric_buffer:
                # Validate the entry first
                number = st.session_state.numeric_buffer
                is_valid = False
                
                if number == "0" or number == "00":
                    is_valid = True
                elif number.isdigit() and 1 <= int(number) <= 36:
                    is_valid = True
                
                if is_valid:
                    # Add the number to the session
                    roulette_data.add_spin(
                        session_name=session_name,
                        number=number,
                        timestamp=datetime.now()
                    )
                    success_msg = st.success(f"✅ Added {number}")
                    st.session_state.numeric_buffer = ""
                    time.sleep(1)
                    success_msg.empty()
                else:
                    # Show error message for invalid entry
                    error_msg = st.error(f"❌ Invalid number: {number}")
                    time.sleep(1)
                    error_msg.empty()

def create_recent_numbers_tracker(session_name, roulette_data, roulette_type="European"):
    """
    Create a panel showing recently seen numbers that can be quickly added.
    Good for when you see what numbers have been coming up but haven't been tracking.
    
    Args:
        session_name (str): The name of the current session
        roulette_data: The roulette data instance to store spins
        roulette_type (str): Type of roulette - 'European' or 'American'
    """
    st.write("Click on numbers you've recently seen to add them to your session:")
    
    # Define colors for the numbers
    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    
    # Numbers grid - arranged in a layout closer to what you'd see on a physical wheel
    # First row - 0 and 00 (if American)
    cols = st.columns(2)
    with cols[0]:
        if st.button("0", key="recent_0", use_container_width=True, type="primary"):
            add_spin_to_session(session_name, roulette_data, "0")
    
    if roulette_type == "American":
        with cols[1]:
            if st.button("00", key="recent_00", use_container_width=True, type="primary"):
                add_spin_to_session(session_name, roulette_data, "00")
    
    # Create a 6x6 grid of numbers
    for row in range(0, 6):
        cols = st.columns(6)
        for col in range(0, 6):
            num = row * 6 + col + 1
            is_red = num in red_numbers
            button_color = "♦️" if is_red else "♠️"
            
            with cols[col]:
                if st.button(f"{button_color} {num}", key=f"recent_{num}", use_container_width=True):
                    add_spin_to_session(session_name, roulette_data, str(num))

def create_last_calls_tracker(session_name, roulette_data, roulette_type="European"):
    """
    Create a panel for last call announcements often made in casinos.
    Useful for European casinos that announce "les voisins", "orphelins", etc.
    
    Args:
        session_name (str): The name of the current session
        roulette_data: The roulette data instance to store spins
        roulette_type (str): Type of roulette - 'European' or 'American'
    """
    st.write("Casino Last Calls - Click on the section announced by the dealer:")
    
    # Define section groups on a European wheel
    voisins_du_zero = [22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25]
    tier_du_cylindre = [27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33]
    orphelins = [1, 20, 14, 31, 9, 17, 34, 6]
    
    # Create buttons for each section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Voisins du Zero", key="last_voisins", help="0, 2, 3, 4, 7, 12, 15, 18, 19, 21, 22, 25, 26, 28, 29, 32, 35", use_container_width=True):
            import random
            number = random.choice(voisins_du_zero)
            add_spin_to_session(session_name, roulette_data, str(number))
    
    with col2:
        if st.button("Tier du Cylindre", key="last_tier", help="5, 8, 10, 11, 13, 16, 23, 24, 27, 30, 33, 36", use_container_width=True):
            import random
            number = random.choice(tier_du_cylindre)
            add_spin_to_session(session_name, roulette_data, str(number))
    
    with col3:
        if st.button("Orphelins", key="last_orphelins", help="1, 6, 9, 14, 17, 20, 31, 34", use_container_width=True):
            import random
            number = random.choice(orphelins)
            add_spin_to_session(session_name, roulette_data, str(number))
    
    # American roulette has different sections
    if roulette_type == "American":
        st.write("American Roulette Sections:")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("0-00-1-2-3 (Top Line)", key="last_topline", use_container_width=True):
                import random
                number = random.choice(["0", "00", "1", "2", "3"])
                add_spin_to_session(session_name, roulette_data, number)
        
        with col2:
            if st.button("Adjacent Numbers", key="last_adjacent", use_container_width=True):
                # Simulate randomly selecting adjacent numbers on an American wheel
                import random
                groups = [
                    ["00", "27", "10"], ["10", "27", "25"], ["25", "27", "13"], ["13", "27", "36"],
                    ["36", "11", "30"], ["30", "11", "8"], ["8", "11", "23"], ["23", "10", "5"],
                    ["5", "10", "24"], ["24", "16", "33"], ["33", "1", "20"], ["20", "1", "14"],
                    ["14", "31", "9"], ["9", "31", "22"], ["22", "18", "29"], ["29", "18", "7"],
                    ["7", "18", "28"], ["28", "12", "35"], ["35", "12", "3"], ["3", "12", "26"],
                    ["26", "0", "32"], ["32", "0", "15"], ["15", "19", "4"], ["4", "19", "21"],
                    ["21", "2", "25"], ["25", "2", "17"], ["17", "2", "34"], ["34", "6", "17"]
                ]
                group = random.choice(groups)
                number = random.choice(group)
                add_spin_to_session(session_name, roulette_data, number)

def add_spin_to_session(session_name, roulette_data, number):
    """
    Add a spin to the session and show a success message.
    
    Args:
        session_name (str): The name of the current session
        roulette_data: The roulette data instance to store spins
        number (str): The number to add
    """
    # Add the spin with current timestamp
    roulette_data.add_spin(
        session_name=session_name,
        number=number,
        timestamp=datetime.now()
    )
    
    # Show success message
    success = st.success(f"✅ Added spin result: {number}")
    time.sleep(1)
    success.empty()
    
    # Rerun to refresh the UI
    st.rerun()