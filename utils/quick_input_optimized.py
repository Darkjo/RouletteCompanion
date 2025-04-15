"""
Optimized Quick Input Panel for rapid entry of roulette spins
With performance improvements for faster response time.
"""
import streamlit as st
from datetime import datetime
import random

# Pre-define common number groups as tuples for better memory efficiency
RED_NUMBERS = (1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36)
BLACK_NUMBERS = (2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35)
EVEN_NUMBERS = tuple(range(2, 37, 2))
ODD_NUMBERS = tuple(range(1, 37, 2))
LOW_NUMBERS = tuple(range(1, 19))
HIGH_NUMBERS = tuple(range(19, 37))
FIRST_DOZEN = tuple(range(1, 13))
SECOND_DOZEN = tuple(range(13, 25))
THIRD_DOZEN = tuple(range(25, 37))
FIRST_COLUMN = (1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34)
SECOND_COLUMN = (2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35)
THIRD_COLUMN = (3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36)

def create_quick_input_panel(current_roulette_type="European", on_result_callback=None):
    """
    Create a panel with clickable buttons for rapid spin entry.
    Optimized for performance.
    
    Args:
        current_roulette_type (str): Type of roulette - 'European' or 'American'
        on_result_callback (function): Callback function that receives the selected number
        
    Returns:
        None
    """
    st.write("Click any number to record it")
    
    # Green (0 and 00) - Simplify by using fewer UI elements
    zero_row = st.columns([1, 1, 3, 3] if current_roulette_type == "American" else [1, 7])
    with zero_row[0]:
        if st.button("0", key="quick_0", use_container_width=True, type="primary"):
            if on_result_callback:
                on_result_callback("0")
    
    if current_roulette_type == "American":
        with zero_row[1]:
            if st.button("00", key="quick_00", use_container_width=True, type="primary"):
                if on_result_callback:
                    on_result_callback("00")
    
    # Numbers 1-36 - Optimize layout to fit more numbers per row for fewer UI elements
    cols_per_row = 6
    for row in range(6):
        cols = st.columns(cols_per_row)
        for col in range(cols_per_row):
            number = row * cols_per_row + col + 1
            with cols[col]:
                if st.button(str(number), key=f"quick_{number}", use_container_width=True):
                    if on_result_callback:
                        on_result_callback(str(number))
    
    # Group buttons - Optimize to use fewer expanders and collapse common elements
    with st.expander("Group Buttons", expanded=False):
        # Use a more compact layout
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔴 RED", key="quick_red", use_container_width=True):
                on_result_callback(str(random.choice(RED_NUMBERS)))
            
            if st.button("EVEN", key="quick_even", use_container_width=True):
                on_result_callback(str(random.choice(EVEN_NUMBERS)))
                
            if st.button("1-12", key="quick_1st_dozen", use_container_width=True):
                on_result_callback(str(random.choice(FIRST_DOZEN)))
                
            if st.button("13-24", key="quick_2nd_dozen", use_container_width=True):
                on_result_callback(str(random.choice(SECOND_DOZEN)))
                
            if st.button("LOW (1-18)", key="quick_low", use_container_width=True):
                on_result_callback(str(random.choice(LOW_NUMBERS)))
                
        with col2:
            if st.button("⚫ BLACK", key="quick_black", use_container_width=True):
                on_result_callback(str(random.choice(BLACK_NUMBERS)))
            
            if st.button("ODD", key="quick_odd", use_container_width=True):
                on_result_callback(str(random.choice(ODD_NUMBERS)))
                
            if st.button("25-36", key="quick_3rd_dozen", use_container_width=True):
                on_result_callback(str(random.choice(THIRD_DOZEN)))
                
            if st.button("COLUMNS", key="quick_columns", use_container_width=True):
                # Combine all columns into one button to reduce UI elements
                column_sets = [FIRST_COLUMN, SECOND_COLUMN, THIRD_COLUMN]
                selected_column = random.choice(column_sets)
                on_result_callback(str(random.choice(selected_column)))
                
            if st.button("HIGH (19-36)", key="quick_high", use_container_width=True):
                on_result_callback(str(random.choice(HIGH_NUMBERS)))

def add_floating_quick_input(session_name, roulette_data, roulette_type):
    """
    Add a floating quick input panel with efficient data entry options.
    Optimized for performance with fewer UI elements and streamlined code.
    
    Args:
        session_name (str): Current session name
        roulette_data (RouletteData): RouletteData object for adding spins
        roulette_type (str): Type of roulette - 'European' or 'American'
        
    Returns:
        None
    """
    # Optimized, simpler callback function
    def on_number_selected(number):
        roulette_data.add_spin(
            session_name=session_name,
            number=number,
            timestamp=datetime.now()
        )
        st.success(f"✅ Added {number}")
        st.rerun()
        
    # Create a tabbed interface with fewer overall widgets
    input_tabs = st.tabs(["Number Grid", "Quick Lists", "Random"])
    
    with input_tabs[0]:
        # Use the optimized quick input panel
        create_quick_input_panel(roulette_type, on_number_selected)
    
    with input_tabs[1]:
        # Option to quickly add from predefined groups
        st.write("Add from Quick Lists")
        
        # Pre-defined groups dictionary for faster lookup
        groups = {
            "Red": RED_NUMBERS,
            "Black": BLACK_NUMBERS,
            "Even": EVEN_NUMBERS,
            "Odd": ODD_NUMBERS,
            "Low (1-18)": LOW_NUMBERS,
            "High (19-36)": HIGH_NUMBERS
        }
        
        # Simplified group selector with fewer options and horizontal layout
        group_type = st.radio(
            "Select Group:",
            list(groups.keys()),
            horizontal=True
        )
        
        # Get the selected group
        numbers_to_show = groups[group_type]
            
        # Display the selected group as buttons - more compact layout
        cols_per_row = 6
        for i in range(0, len(numbers_to_show), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(numbers_to_show):
                    num = numbers_to_show[i + j]
                    with cols[j]:
                        if st.button(f"{num}", key=f"group_{num}"):
                            on_number_selected(str(num))
    
    with input_tabs[2]:
        # Ultra-simplified random generator with minimal options
        col1, col2 = st.columns(2)
        
        with col1:
            num_spins = st.number_input("Spins:", min_value=1, max_value=20, value=5)
        
        with col2:
            include_zeros = st.checkbox("Include zeros", value=True)
        
        if st.button("Generate Random", use_container_width=True):
            # Prepare possible numbers once - not in the loop
            if roulette_type == "European":
                possible_nums = [str(i) for i in range(37)]  # 0-36
            else:  # American
                possible_nums = ["00"] + [str(i) for i in range(37)]  # 00, 0-36
                
            if not include_zeros:
                possible_nums = [n for n in possible_nums if n != "0" and n != "00"]
            
            # Batch process all spins at once
            with st.spinner(f"Adding {num_spins} random spins..."):
                # Generate all random choices at once
                selected_numbers = [random.choice(possible_nums) for _ in range(num_spins)]
                
                # Add all spins in one batch
                for number in selected_numbers:
                    roulette_data.add_spin(
                        session_name=session_name,
                        number=number,
                        timestamp=datetime.now()
                    )
                    
                st.success(f"✅ Added {num_spins} spins")
                st.rerun()