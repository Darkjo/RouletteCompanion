"""
Quick Input Panel for rapid entry of roulette spins
"""
import streamlit as st
from datetime import datetime
import random  # Import at the module level instead of repeatedly within functions

def create_quick_input_panel(current_roulette_type="European", on_result_callback=None):
    """
    Create a panel with clickable buttons for rapid spin entry.
    
    Args:
        current_roulette_type (str): Type of roulette - 'European' or 'American'
        on_result_callback (function): Callback function that receives the selected number
        
    Returns:
        None
    """
    st.subheader("Quick Input Panel")
    st.write("Click on any number to instantly record it as the latest spin result")
    
    # Define colors
    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    
    # Create a grid of buttons for all numbers
    st.write("**Single Numbers:**")
    
    # Green (0 and 00)
    zero_cols = st.columns(4 if current_roulette_type == "American" else 2)
    with zero_cols[0]:
        if st.button("0", key="quick_0", use_container_width=True, 
                    type="primary"):
            if on_result_callback:
                on_result_callback("0")
    
    if current_roulette_type == "American":
        with zero_cols[1]:
            if st.button("00", key="quick_00", use_container_width=True, 
                        type="primary"):
                if on_result_callback:
                    on_result_callback("00")
    
    # Numbers 1-36
    st.write("**Numbers 1-36:**")
    
    # Create a layout with multiple rows and 6 numbers per row
    for row in range(6):
        cols = st.columns(6)
        for col in range(6):
            number = row * 6 + col + 1
            is_red = number in red_numbers
            
            # Set button styling based on color
            button_type = "secondary"
            
            with cols[col]:
                if st.button(str(number), key=f"quick_{number}", 
                           use_container_width=True, 
                           type=button_type,
                           help=f"Click to record {number} ({'red' if is_red else 'black'})"):
                    if on_result_callback:
                        on_result_callback(str(number))
    
    # Group buttons
    st.write("**Quick Groups:**")
    
    # Row 1: Red/Black and Even/Odd
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔴 RED", key="quick_red", use_container_width=True):
            # Select a random red number
            selected = str(random.choice(red_numbers))
            if on_result_callback:
                on_result_callback(selected)
    
    with col2:
        if st.button("⚫ BLACK", key="quick_black", use_container_width=True):
            # Select a random black number
            black_numbers = [n for n in range(1, 37) if n not in red_numbers]
            selected = str(random.choice(black_numbers))
            if on_result_callback:
                on_result_callback(selected)
    
    with col3:
        if st.button("EVEN", key="quick_even", use_container_width=True):
            # Select a random even number
            selected = str(random.choice([n for n in range(2, 37, 2)]))
            if on_result_callback:
                on_result_callback(selected)
                
    with col4:
        if st.button("ODD", key="quick_odd", use_container_width=True):
            # Select a random odd number
            selected = str(random.choice([n for n in range(1, 37, 2)]))
            if on_result_callback:
                on_result_callback(selected)
    
    # Row 2: Dozens
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("1-12", key="quick_1st_dozen", use_container_width=True):
            # Select a random number from the first dozen
            selected = str(random.choice(range(1, 13)))
            if on_result_callback:
                on_result_callback(selected)
                
    with col2:
        if st.button("13-24", key="quick_2nd_dozen", use_container_width=True):
            # Select a random number from the second dozen
            selected = str(random.choice(range(13, 25)))
            if on_result_callback:
                on_result_callback(selected)
                
    with col3:
        if st.button("25-36", key="quick_3rd_dozen", use_container_width=True):
            # Select a random number from the third dozen
            selected = str(random.choice(range(25, 37)))
            if on_result_callback:
                on_result_callback(selected)
    
    # Row 3: Columns
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Column 1", key="quick_1st_col", use_container_width=True, 
                    help="1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34"):
            # Select a random number from the first column
            selected = str(random.choice([1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]))
            if on_result_callback:
                on_result_callback(selected)
                
    with col2:
        if st.button("Column 2", key="quick_2nd_col", use_container_width=True,
                    help="2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35"):
            # Select a random number from the second column
            selected = str(random.choice([2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]))
            if on_result_callback:
                on_result_callback(selected)
                
    with col3:
        if st.button("Column 3", key="quick_3rd_col", use_container_width=True,
                    help="3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36"):
            # Select a random number from the third column
            selected = str(random.choice([3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]))
            if on_result_callback:
                on_result_callback(selected)
                
    # Row 4: High/Low
    col1, col2 = st.columns(2)
    with col1:
        if st.button("LOW (1-18)", key="quick_low", use_container_width=True):
            # Select a random low number
            selected = str(random.choice(range(1, 19)))
            if on_result_callback:
                on_result_callback(selected)
                
    with col2:
        if st.button("HIGH (19-36)", key="quick_high", use_container_width=True):
            # Select a random high number
            selected = str(random.choice(range(19, 37)))
            if on_result_callback:
                on_result_callback(selected)
                
def add_floating_quick_input(session_name, roulette_data, roulette_type="European"):
    """
    Add a small panel that floats at the bottom of the screen for very quick input.
    
    Args:
        session_name (str): The session to add spins to
        roulette_data (RouletteData): The roulette data manager instance
        roulette_type (str): Type of roulette - 'European' or 'American'
    """
    with st.expander("Quick Input Panel (Click to expand)"):
        def on_quick_result(number):
            # Add the spin with current timestamp
            roulette_data.add_spin(
                session_name=session_name,
                number=number,
                timestamp=datetime.now()
            )
            
            # Store information about the last spin for display
            if "last_spin_time" not in st.session_state:
                st.session_state.last_spin_time = datetime.now()
                st.session_state.last_spin_number = number
                st.session_state.show_update_notification = True
            else:
                st.session_state.last_spin_time = datetime.now()
                st.session_state.last_spin_number = number
                st.session_state.show_update_notification = True
            
            # Show success message
            st.success(f"Added spin result: {number}")
            
            # Rerun to refresh the UI
            st.rerun()
            
        create_quick_input_panel(roulette_type, on_quick_result)