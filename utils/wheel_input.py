"""
Roulette Number Input Component
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import random

def create_roulette_wheel_input(roulette_type="European"):
    """
    Create a simplified roulette input interface.
    
    Args:
        roulette_type (str): Type of roulette - 'European' or 'American'
        
    Returns:
        str or None: Selected number or None if no selection was made
    """
    # Define wheel numbers and colors
    if roulette_type == "European":
        max_number = 36
        has_double_zero = False
    else:  # American
        max_number = 36
        has_double_zero = True
    
    # Define colors for roulette numbers
    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    
    # Create input tabs
    tab1, tab2, tab3 = st.tabs(["Roulette Table", "Quick Picks", "Manual Entry"])
    
    selected_number = None
    
    # Tab 1: Roulette Table representation
    with tab1:
        st.write("#### Select a number from the roulette table:")
        
        # Style the layout to look more like a roulette table
        st.markdown("""
        <style>
        .roulette-table {
            background-color: #0D4C27;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create the zero section
        st.markdown('<div class="roulette-table">', unsafe_allow_html=True)
        
        # Handle zero(s) differently based on roulette type
        if has_double_zero:
            # For American roulette with 0 and 00
            zero_cols = st.columns([1, 2, 1])
            with zero_cols[1]:
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("0", key="table_0", use_container_width=True, 
                               type="primary", help="Green - 0"):
                        selected_number = "0"
                
                with col2:
                    if st.button("00", key="table_00", use_container_width=True, 
                               type="primary", help="Green - 00"):
                        selected_number = "00"
        else:
            # For European roulette with just 0
            zero_cols = st.columns([1, 2, 1])
            with zero_cols[1]:
                if st.button("0", key="table_0", use_container_width=True, 
                           type="primary", help="Green - 0"):
                    selected_number = "0"
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Create the main number grid (3 rows x 12 columns)
        st.markdown('<div class="roulette-table">', unsafe_allow_html=True)
        
        # Create 3 rows of numbers
        for row in range(3):
            cols = st.columns(12)
            for col in range(12):
                num = str(col * 3 + row + 1)
                is_red = (col * 3 + row + 1) in red_numbers
                
                with cols[col]:
                    if st.button(
                        num, 
                        key=f"table_{num}", 
                        use_container_width=True,
                        type="secondary",
                        help=f"{'Red' if is_red else 'Black'} - {num}"
                    ):
                        selected_number = num
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add betting options section
        st.write("#### Betting Options:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Dozens:**")
            if st.button("1st Dozen (1-12)", key="dozen_1", use_container_width=True):
                selected_number = str(random.randint(1, 12))
                
            if st.button("2nd Dozen (13-24)", key="dozen_2", use_container_width=True):
                selected_number = str(random.randint(13, 24))
                
            if st.button("3rd Dozen (25-36)", key="dozen_3", use_container_width=True):
                selected_number = str(random.randint(25, 36))
        
        with col2:
            st.write("**Columns:**")
            if st.button("1st Column (1,4,7...)", key="col_1", use_container_width=True):
                selected_number = str(random.choice([1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]))
                
            if st.button("2nd Column (2,5,8...)", key="col_2", use_container_width=True):
                selected_number = str(random.choice([2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]))
                
            if st.button("3rd Column (3,6,9...)", key="col_3", use_container_width=True):
                selected_number = str(random.choice([3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]))
                
        with col3:
            st.write("**Even/Odd & Colors:**")
            if st.button("🔴 Red", key="bet_red", use_container_width=True):
                selected_number = str(random.choice(red_numbers))
                
            if st.button("⚫ Black", key="bet_black", use_container_width=True):
                black_numbers = [n for n in range(1, 37) if n not in red_numbers]
                selected_number = str(random.choice(black_numbers))
                
            odd_even_cols = st.columns(2)
            if odd_even_cols[0].button("Even", key="bet_even", use_container_width=True):
                selected_number = str(random.choice(range(2, 37, 2)))
                
            if odd_even_cols[1].button("Odd", key="bet_odd", use_container_width=True):
                selected_number = str(random.choice(range(1, 37, 2)))
    
    # Tab 2: Quick Picks
    with tab2:
        st.write("#### Quick selection options:")
        
        # Random number picker
        st.write("**Random Number Selection:**")
        if st.button("🎲 Random Number", key="random_number", use_container_width=True):
            # Include 0 and 00 (if American) in the possibilities
            possible_nums = list(range(max_number + 1))
            if has_double_zero:
                # Use -1 to represent 00 (for random selection purposes)
                possible_nums.append(-1)
                
            selected = random.choice(possible_nums)
            if selected == -1:
                selected_number = "00"
            else:
                selected_number = str(selected)
        
        # Hot and cold numbers (simulated for demo)
        st.write("**Hot and Cold Numbers:**")
        cols = st.columns(2)
        
        with cols[0]:
            st.write("**Hot Numbers (most frequent):**")
            # Simulated hot numbers
            hot_nums = [7, 17, 23, 24, 32]
            hot_cols = st.columns(5)
            for i, num in enumerate(hot_nums):
                if hot_cols[i].button(str(num), key=f"hot_{num}", use_container_width=True):
                    selected_number = str(num)
        
        with cols[1]:
            st.write("**Cold Numbers (least frequent):**")
            # Simulated cold numbers
            cold_nums = [6, 13, 27, 33, 34]
            cold_cols = st.columns(5)
            for i, num in enumerate(cold_nums):
                if cold_cols[i].button(str(num), key=f"cold_{num}", use_container_width=True):
                    selected_number = str(num)
        
        # Number patterns
        st.write("**Number Patterns:**")
        pattern_cols = st.columns(3)
        
        with pattern_cols[0]:
            if st.button("Low (1-18)", key="pattern_low", use_container_width=True):
                selected_number = str(random.randint(1, 18))
                
        with pattern_cols[1]:
            if st.button("Middle (13-24)", key="pattern_mid", use_container_width=True):
                selected_number = str(random.randint(13, 24))
                
        with pattern_cols[2]:
            if st.button("High (19-36)", key="pattern_high", use_container_width=True):
                selected_number = str(random.randint(19, 36))
    
    # Tab 3: Manual Entry
    with tab3:
        st.write("#### Enter the spin result manually:")
        
        method = st.radio("Input Method:", ["Number Picker", "Direct Entry"])
        
        if method == "Number Picker":
            if roulette_type == "European":
                manual_options = ["Select"] + [str(i) for i in range(max_number + 1)]
                manual_selection = st.selectbox("Select Number:", manual_options)
                if manual_selection != "Select":
                    selected_number = manual_selection
            else:  # American
                manual_options = ["Select"] + ["00"] + [str(i) for i in range(max_number + 1)]
                manual_selection = st.selectbox("Select Number:", manual_options)
                if manual_selection != "Select":
                    selected_number = manual_selection
        else:  # Direct Entry
            if roulette_type == "European":
                manual_num = st.number_input("Enter Number (0-36):", min_value=-1, max_value=max_number, step=1, value=-1)
                if manual_num >= 0:
                    selected_number = str(manual_num)
            else:  # American
                col1, col2 = st.columns(2)
                with col1:
                    manual_num = st.number_input("Enter Number (0-36):", min_value=-1, max_value=max_number, step=1, value=-1)
                    if manual_num >= 0:
                        selected_number = str(manual_num)
                with col2:
                    if st.button("00", key="manual_00", use_container_width=True):
                        selected_number = "00"
    
    # Display the selected number with appropriate color
    if selected_number:
        if selected_number == "0" or selected_number == "00":
            color = "green"
        elif int(selected_number) in red_numbers:
            color = "red"
        else:
            color = "black"
            
        # Provide visual feedback for the selected number
        st.markdown(f"""
        <div style="padding: 10px; background-color: #f0f0f0; border-radius: 5px; margin-top: 15px;">
            <h3 style="text-align: center; margin: 0;">Selected Number: 
                <span style="color: {color}; font-weight: bold;">{selected_number}</span>
            </h3>
        </div>
        """, unsafe_allow_html=True)
    
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