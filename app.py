import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from utils.advanced_betting import AdvancedBettingAnalysis
from datetime import datetime, timedelta
import json
import os
import time

from utils.roulette_data_optimized import RouletteData  # Using optimized version
from utils.analysis import RouletteAnalyzer
from utils.betting_strategies import BettingStrategist
from utils.visualization_optimized import RouletteVisualizer  # Using optimized version
from utils.agent import RLAgent
from utils.performance_tracker import StrategyPerformanceTracker
from utils.strategies import StrategyEngine
from utils.strategy_selector import choose_strategy, get_bet_size_recommendation, get_strategy_description
from utils.file_import import create_file_importer
from utils.quick_input_optimized import add_floating_quick_input  # Using the optimized version
from utils.live_casino_input import create_live_casino_panel
from utils.wheel_bias import WheelBiasDetector
from utils.web_scraper import create_web_scraper_ui
from utils.dataframe_converter import clean_dataframe_for_analysis  # Import the new converter

# Set page configuration
st.set_page_config(
    page_title="Roulette Tracker and Analyzer",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'roulette_data' not in st.session_state:
    st.session_state.roulette_data = RouletteData()
    
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = RouletteAnalyzer()
    
if 'strategist' not in st.session_state:
    st.session_state.strategist = BettingStrategist()
    
if 'visualizer' not in st.session_state:
    st.session_state.visualizer = RouletteVisualizer()
    
# New components from ProjectR
if 'agent' not in st.session_state:
    st.session_state.agent = RLAgent()
    
if 'performance_tracker' not in st.session_state:
    st.session_state.performance_tracker = StrategyPerformanceTracker()
    
if 'strategy_engine' not in st.session_state:
    st.session_state.strategy_engine = StrategyEngine()
    
if 'wheel_bias_detector' not in st.session_state:
    st.session_state.wheel_bias_detector = WheelBiasDetector()
    
if 'advanced_betting' not in st.session_state:
    st.session_state.advanced_betting = AdvancedBettingAnalysis()
    
if 'bankroll' not in st.session_state:
    st.session_state.bankroll = 100.0
    
if 'current_session' not in st.session_state:
    st.session_state.current_session = "Default Session"
    
if 'sessions' not in st.session_state:
    st.session_state.sessions = ["Default Session"]
    
# Initialize fast_mode preference (default to True for 8-second window)
if 'fast_mode' not in st.session_state:
    st.session_state.fast_mode = True

# Application title
st.title("🎰 Roulette Tracker and Analyzer")

# Add a space for better UI layout
st.write("")

# Sidebar for settings and navigation
with st.sidebar:
    st.header("Settings")
    
    # Auto-save indicator
    st.success("✓ Auto-Save Enabled: Your data is automatically saved and will be preserved between sessions.")
    
    # Roulette type selection
    roulette_type = st.radio(
        "Select Roulette Type:",
        options=["European", "American"],
        index=0
    )
    
    # Bankroll management
    st.subheader("Bankroll Management")
    current_bankroll = st.number_input(
        "Current Bankroll ($):",
        min_value=10.0,
        max_value=10000.0,
        value=st.session_state.bankroll,
        step=10.0
    )
    
    # Update session state when bankroll changes
    if current_bankroll != st.session_state.bankroll:
        st.session_state.bankroll = current_bankroll
    
    # Display recommended bet size based on bankroll with explanation
    rec_bet_size = get_bet_size_recommendation(st.session_state.bankroll)
    
    with st.expander("💰 Adaptive Bankroll Strategy", expanded=True):
        st.markdown("""
        ### How Adaptive Bankroll Strategy Works
        
        The system automatically adjusts your recommended bet size based on your bankroll:
        
        | Bankroll Size | Bet Percentage | Explanation |
        |---------------|----------------|-------------|
        | Under $50     | Fixed $1.00    | Protection for small bankrolls |
        | $50-$99       | 2% of bankroll | Conservative approach for building up |
        | $100-$199     | 3% of bankroll | Balanced risk/reward ratio |
        | $200-$499     | 4% of bankroll | Moderate approach for growth |
        | $500+         | 5% of bankroll | Standard ratio for larger bankrolls |
        
        **Confidence Level Adjustments:**
        
        | Confidence | Adjustment | Example with $200 Bankroll |
        |------------|------------|----------------------------|
        | >75%       | +20%       | $8.00 → $9.60 |
        | 65-75%     | +10%       | $8.00 → $8.80 |
        | 40-65%     | No change  | $8.00 (standard) |
        | <40%       | -10%       | $8.00 → $7.20 |
        | Losing streak | -20%    | $8.00 → $6.40 |
        
        **Additional Adaptive Factors:**
        - Pattern recognition affects confidence scoring
        - Real-time adjustments based on recent results
        - Protection mechanisms during losing streaks
        
        _This adaptive strategy helps manage risk while maximizing potential returns._
        """)
    
    st.info(f"Recommended bet size: ${rec_bet_size:.2f}")
    
    # Session management
    st.subheader("Session Management")
    
    # Create a new session
    new_session_name = st.text_input("New Session Name")
    if st.button("Create Session") and new_session_name:
        if new_session_name not in st.session_state.sessions:
            st.session_state.sessions.append(new_session_name)
            st.session_state.current_session = new_session_name
            st.success(f"Created session: {new_session_name}")
            st.session_state.roulette_data.create_session(new_session_name, roulette_type)
        else:
            st.error("Session name already exists!")
    
    # Select an existing session
    st.session_state.current_session = st.selectbox(
        "Select Session:",
        options=st.session_state.sessions,
        index=st.session_state.sessions.index(st.session_state.current_session)
    )
    
    # Reset current session button with warning
    reset_col1, reset_col2 = st.columns([1, 1])
    with reset_col1:
        reset_session = st.button("🔄 Reset Session Data", type="primary", 
                                help="Clear all spin data for the current session")
    with reset_col2:
        confirm_reset = st.checkbox("Confirm Reset", 
                                  help="Check this to confirm you want to delete all data")
    
    if reset_session and confirm_reset:
        # Clear all spin history for the current session
        st.session_state.roulette_data.clear_spin_history(st.session_state.current_session)
        
        # Reset the agent's state as well
        if hasattr(st.session_state, "agent"):
            st.session_state.agent.reset()
            
        st.success(f"Reset complete! All data for '{st.session_state.current_session}' has been cleared.")
        # Force a rerun to refresh all displays
        st.rerun()
    
    # Delete the current session
    if st.button("Delete Current Session") and len(st.session_state.sessions) > 1:
        session_to_delete = st.session_state.current_session
        session_index = st.session_state.sessions.index(session_to_delete)
        st.session_state.sessions.remove(session_to_delete)
        st.session_state.current_session = st.session_state.sessions[0]
        st.session_state.roulette_data.delete_session(session_to_delete)
        st.success(f"Deleted session: {session_to_delete}")
        st.rerun()
    
    # Data management
    st.subheader("Data Management")
    
    st.info("💡 Note: Data is automatically saved after every change. Manual save/load is optional.")
    
    # Save data to file
    if st.button("Manual Save"):
        success = st.session_state.roulette_data.save_data()
        if success:
            st.success("Data saved successfully!")
        else:
            st.error("Failed to save data.")
    
    # Load data from file
    if st.button("Reload Data"):
        success = st.session_state.roulette_data.load_data()
        if success:
            # Update session list
            st.session_state.sessions = st.session_state.roulette_data.get_sessions()
            if st.session_state.sessions:
                st.session_state.current_session = st.session_state.sessions[0]
            else:
                st.session_state.sessions = ["Default Session"]
                st.session_state.current_session = "Default Session"
                st.session_state.roulette_data.create_session("Default Session", "European")
            st.success("Data loaded successfully!")
            st.rerun()
        else:
            st.error("No saved data found or error loading data.")

# Simplified UI with clearer navigation
st.title("🎰 Roulette Strategy Assistant")
current_roulette_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)

# Create a more intuitive three-column layout for the main dashboard
dashboard_col1, dashboard_col2, dashboard_col3 = st.columns([1, 2, 1])

with dashboard_col1:
    st.subheader("📊 Session Info")
    st.info(f"**Current Session:** {st.session_state.current_session}")
    st.info(f"**Roulette Type:** {current_roulette_type}")
    st.info(f"**Bankroll:** ${st.session_state.bankroll:.2f}")
    
    # Add quick input panel
    st.subheader("⚡ Quick Add")
    add_floating_quick_input(st.session_state.current_session, st.session_state.roulette_data, current_roulette_type)

with dashboard_col3:
    st.subheader("💡 Recommendations")
    
    # Get recommended bet size
    rec_bet_size = get_bet_size_recommendation(st.session_state.bankroll)
    st.metric("Recommended Bet", f"${rec_bet_size:.2f}")
    
    # Get recommended strategy based on current analysis
    raw_spins_df = st.session_state.roulette_data.get_session_data(st.session_state.current_session)
    # Clean the dataframe to extract properties (prevents unhashable type errors)
    spins_df = clean_dataframe_for_analysis(raw_spins_df)
    
    if spins_df is not None and not spins_df.empty and len(spins_df) > 10:
        rec_strategy = st.session_state.agent.get_recommendation(st.session_state.bankroll)
        st.success(f"Suggested Strategy: **{rec_strategy}**")
        
        with st.expander("Strategy Details"):
            st.write(get_strategy_description(rec_strategy))
    else:
        st.warning("Need more spins for strategy recommendations")

# Main navigation - simplify to 3 clear sections
main_tab1, main_tab2, main_tab3 = st.tabs(["💾 Data Management", "📈 Analysis", "🎲 Betting Strategies"])

# Tab 1: Simplified Data Management
with main_tab1:
    st.header("Data Management")
    
    # Simplified input options
    input_method = st.radio(
        "Choose Input Method:",
        ["Manual Entry", "OCR/Camera", "Import From File", "Live Casino"],
        horizontal=True,
        help="Select how you want to enter spin data"
    )

    # Create a clean divider
    st.divider()
    
    # Display different input methods based on selection
    if input_method == "Manual Entry":
        # Traditional manual input with bigger, clearer UI
        st.subheader("📝 Manual Entry")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Input for spin number with clearer labels
            if current_roulette_type == "European":
                spin_number = st.number_input("Spin Result (0-36):", 
                                           min_value=0, max_value=36, step=1,
                                           help="Enter the number that came up on the wheel")
            else:  # American
                spin_number = st.number_input("Spin Result (00, 0-36):", 
                                           min_value=-1, max_value=36, step=1,
                                           help="Enter -1 for '00' (American roulette)")
        
        with col2:
            # Simplified timestamp - just use current time by default
            use_custom_time = st.checkbox("Use custom time?", value=False)
            
            if use_custom_time:
                timestamp = st.date_input("Date:", value=datetime.now().date())
                time_input = st.time_input("Time:", value=datetime.now().time())
                spin_timestamp = datetime.combine(timestamp, time_input)
            else:
                spin_timestamp = datetime.now()
        
        # Button to add the spin
        if st.button("➕ Add Spin Result", key="manual_add_btn", use_container_width=True):
            # Convert -1 to '00' for American roulette
            display_number = '00' if spin_number == -1 else str(spin_number)
            
            # Add spin to current session
            st.session_state.roulette_data.add_spin(
                session_name=st.session_state.current_session,
                number=display_number,
                timestamp=spin_timestamp
            )
            
            st.success(f"Added spin result: {display_number}")
            st.rerun()  # Refresh the page to show updated data
    
    elif input_method == "OCR/Camera":
        # OCR-based capture with simpler UI
        st.subheader("📷 OCR/Camera Input")
        
        # Create tabs for different OCR methods
        ocr_tabs = st.tabs(["Upload Image", "Camera Capture", "Screen Capture"])
        
        with ocr_tabs[0]:
            st.write("Upload a photo of a roulette number or history board:")
            
            # Create tabs for single number and history board
            img_type = st.radio("Select image type:", 
                             ["Single Number", "History Board"],
                             horizontal=True)
            
            uploaded_file = st.file_uploader(
                "Upload image:", 
                type=["png", "jpg", "jpeg"],
                key="ocr_upload"
            )
            
            if uploaded_file is not None:
                # Process the uploaded image
                from utils.ocr_capture import recognize_number, batch_process_history_board, validate_roulette_number
                from PIL import Image
                
                image = Image.open(uploaded_file)
                
                # Display the image
                st.image(image, caption="Uploaded Image", width=300)
                
                if img_type == "Single Number":
                    # Process with OCR for single number
                    number, confidence = recognize_number(image)
                    
                    if number and confidence > 0.5:
                        st.success(f"✅ Recognized number: {number} (confidence: {confidence:.2f})")
                        
                        # Add button to confirm and add this number
                        if st.button("Add This Number", type="primary", key="add_ocr_single"):
                            st.session_state.roulette_data.add_spin(
                                session_name=st.session_state.current_session,
                                number=number,
                                timestamp=datetime.now()
                            )
                            st.success(f"✅ Added {number} to session {st.session_state.current_session}")
                            st.rerun()
                    else:
                        st.error("❌ Could not recognize a valid roulette number in this image.")
                
                else:  # History Board
                    # Add options for processing methods with Fast as default for better performance
                    ocr_method = st.radio(
                        "Choose processing method:",
                        ["Ultra Fast (Maximum speed)", "Fast (Balanced)", "Standard (Most accurate)"],
                        index=0, # Default to Ultra Fast
                        horizontal=True,
                        help="Ultra Fast works best with digital displays, Fast is for most boards, Standard for unusual layouts"
                    )
                    
                    # Add batch processing button
                    if st.button("Process History Board", type="primary", key="process_history"):
                        with st.spinner("Processing roulette history board..."):
                            start_time = time.time()
                            
                            if ocr_method == "Ultra Fast (Maximum speed)":
                                # Import our ultra-optimized OCR module
                                try:
                                    from utils.optimized_ocr import process_image
                                    # Process with the ultra-fast method
                                    numbers = process_image(image)
                                    processing_time = time.time() - start_time
                                    st.success(f"Ultra-fast processing completed in {processing_time:.2f} seconds")
                                except ImportError:
                                    st.warning("Ultra-fast module not available, falling back to Fast mode")
                                    from utils.specialized_ocr import process_roulette_board
                                    number_list = process_roulette_board(image, rows=6, cols=8)
                                    numbers = [(num, 0.8) for num in number_list]
                                    processing_time = time.time() - start_time
                                    st.info(f"Fast processing completed in {processing_time:.2f} seconds")
                                    
                            elif ocr_method == "Fast (Balanced)":
                                # Use the specialized OCR module
                                try:
                                    from utils.specialized_ocr import process_roulette_board
                                    # Process with the specialized method
                                    number_list = process_roulette_board(image, rows=6, cols=8)
                                    if len(number_list) < 10:
                                        # If that didn't find many numbers, try other layout
                                        number_list = process_roulette_board(image, rows=8, cols=6)
                                    
                                    # Convert to the expected format
                                    numbers = [(num, 0.8) for num in number_list]
                                    processing_time = time.time() - start_time
                                    st.info(f"Fast processing completed in {processing_time:.2f} seconds")
                                except ImportError:
                                    st.warning("Fast processing module not available, using standard method")
                                    numbers = batch_process_history_board(image)
                                    processing_time = time.time() - start_time
                                    st.info(f"Standard processing completed in {processing_time:.2f} seconds")
                            else:
                                # Use the standard full-featured method
                                numbers = batch_process_history_board(image)
                                processing_time = time.time() - start_time
                                st.info(f"Standard processing completed in {processing_time:.2f} seconds")
                            
                            if numbers and len(numbers) > 0:
                                # Display the recognized numbers
                                st.success(f"✅ Recognized {len(numbers)} numbers from the history board!")
                                
                                # Create a dataframe to display the results
                                import pandas as pd
                                results_df = pd.DataFrame(numbers, columns=["Number", "Confidence"])
                                st.dataframe(results_df)
                                
                                # Option to add all numbers
                                reverse_order = st.checkbox("Reverse the order (oldest to newest)", value=False)
                                
                                if st.button("Add All Numbers", type="primary", key="add_all_history"):
                                    # Process in the selected order
                                    process_list = list(numbers)
                                    if reverse_order:
                                        process_list.reverse()
                                    
                                    # Add each number to the session
                                    added_count = 0
                                    for num, conf in process_list:
                                        if validate_roulette_number(num):
                                            st.session_state.roulette_data.add_spin(
                                                session_name=st.session_state.current_session,
                                                number=num,
                                                timestamp=datetime.now() - timedelta(seconds=(added_count*10))
                                            )
                                            added_count += 1
                                    
                                    st.success(f"✅ Added {added_count} numbers to session {st.session_state.current_session}")
                                    st.rerun()
                            else:
                                st.error("❌ Could not recognize any valid roulette numbers in this image.")
        
        with ocr_tabs[1]:
            st.write("Use your device camera to capture roulette numbers:")
            
            # Add button to activate camera only when user wants it
            if "show_camera" not in st.session_state:
                st.session_state.show_camera = False
                
            if st.button("📷 Activate Camera", use_container_width=True):
                st.session_state.show_camera = True
                
            # Only show camera input when the button is clicked
            if st.session_state.show_camera:
                # Upload from camera option
                camera_file = st.camera_input("Take a photo of the roulette number")
                
                if camera_file is not None:
                    # Process the uploaded image
                    from utils.ocr_capture import recognize_number
                    from PIL import Image
                    
                    image = Image.open(camera_file)
                    
                    # Display the image
                    st.image(image, caption="Captured Image", width=300)
                    
                    # Process with OCR
                    number, confidence = recognize_number(image)
                    
                    if number and confidence > 0.5:
                        st.success(f"✅ Recognized number: {number} (confidence: {confidence:.2f})")
                        
                        # Add large, touchscreen-friendly button
                        if st.button("ADD THIS NUMBER", type="primary", key="add_camera", use_container_width=True):
                            st.session_state.roulette_data.add_spin(
                                session_name=st.session_state.current_session,
                                number=number,
                                timestamp=datetime.now()
                            )
                            st.success(f"✅ Added {number} to session {st.session_state.current_session}")
                            st.rerun()
                    else:
                        st.error("❌ Could not recognize a valid roulette number in this image.")
            else:
                st.info("Click 'Activate Camera' button above when you're ready to take a photo")
                
        with ocr_tabs[2]:
            st.warning("Screen capture is not available in this environment.")
            st.info("Please use the Upload Image or Camera options instead.")
    
    elif input_method == "Import From File":
        st.subheader("📁 Import From File")
        
        # Import from file with clearer instructions
        st.write("""
        ### Import Roulette Data from CSV or Excel Files
        
        You can import spin data from CSV or Excel files. The file should have at least one column named 'number' 
        containing the roulette numbers (0, 00, 1-36).
        
        **Optional columns:**
        - 'timestamp': Date and time of each spin
        """)
        
        imported_data = create_file_importer()
        
        if imported_data is not None:
            with st.spinner("Importing data..."):
                # Show preview of the data
                st.write("Data Preview:")
                st.dataframe(imported_data.head())
                
                # Confirm import
                if st.button("Confirm Import", type="primary"):
                    # Add each spin to the session
                    for _, row in imported_data.iterrows():
                        number = row['number']
                        timestamp = row['timestamp'] if 'timestamp' in row else datetime.now()
                        
                        st.session_state.roulette_data.add_spin(
                            session_name=st.session_state.current_session,
                            number=str(number),
                            timestamp=timestamp
                        )
                    
                    st.success(f"✅ Successfully imported {len(imported_data)} spins!")
                    st.rerun()  # Refresh the page to show updated data
    
    elif input_method == "Live Casino":
        st.subheader("🎲 Live Casino Input")
        
        # Add live casino with clearer instructions
        st.write("""
        ### Live Casino Input Tools
        
        This mode provides specialized tools for tracking spins while playing at a live casino, 
        either online or in-person.
        """)
        
        # Create the live casino panel
        create_live_casino_panel(st.session_state.current_session, st.session_state.roulette_data, current_roulette_type)
    
    # Display the current session's spin history
    st.subheader("Spin History")
    
    spins_df = st.session_state.roulette_data.get_session_data(st.session_state.current_session)
    
    if spins_df is not None and not spins_df.empty:
        # Button to remove the last spin
        if st.button("Remove Last Spin") and len(spins_df) > 0:
            st.session_state.roulette_data.remove_last_spin(st.session_state.current_session)
            st.success("Last spin removed.")
            st.rerun()
        
        # Display recent spins
        st.dataframe(spins_df.sort_values(by='timestamp', ascending=False).head(10))
        
        # Visual representation of recent spins
        st.subheader("Recent Spins Visualization")
        fig = st.session_state.visualizer.plot_recent_spins(spins_df, current_roulette_type)
        st.plotly_chart(fig, use_container_width=True, key="recent_spins_chart")
    else:
        st.info("No spins recorded in this session yet. Add some spins to get started!")

# Tab 2: Analysis
with main_tab2:
    st.header("Data Analysis")
    
    # Get data for current session
    spins_df = st.session_state.roulette_data.get_session_data(st.session_state.current_session)
    
    if spins_df is not None and not spins_df.empty:
        # Analysis options
        analysis_option = st.selectbox(
            "Select Analysis Type:",
            ["Number Frequency", "Even/Odd Distribution", "Red/Black Distribution", 
             "Dozens Distribution", "Columns Distribution", "High/Low Distribution",
             "Wheel Bias Detection"]
        )
        
        # Perform the selected analysis
        if analysis_option == "Number Frequency":
            st.subheader("Number Frequency Analysis")
            fig = st.session_state.visualizer.plot_number_frequency(spins_df, 
                                                                   st.session_state.roulette_data.get_session_type(st.session_state.current_session))
            st.plotly_chart(fig, use_container_width=True, key="number_frequency_chart")
            
            # Display hot and cold numbers
            hot_numbers, cold_numbers = st.session_state.analyzer.get_hot_cold_numbers(spins_df, 
                                                                                      st.session_state.roulette_data.get_session_type(st.session_state.current_session))
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Hot Numbers (Most Frequent)")
                st.write(hot_numbers)
            
            with col2:
                st.subheader("Cold Numbers (Least Frequent)")
                st.write(cold_numbers)
        
        elif analysis_option == "Even/Odd Distribution":
            st.subheader("Even/Odd Distribution Analysis")
            fig = st.session_state.visualizer.plot_even_odd_distribution(spins_df)
            st.plotly_chart(fig, use_container_width=True, key="even_odd_chart")
            
            # Display even/odd trend
            even_odd_trend = st.session_state.analyzer.get_even_odd_trend(spins_df)
            st.subheader("Even/Odd Trend Analysis")
            st.write(even_odd_trend)
        
        elif analysis_option == "Red/Black Distribution":
            st.subheader("Red/Black Distribution Analysis")
            fig = st.session_state.visualizer.plot_red_black_distribution(spins_df)
            st.plotly_chart(fig, use_container_width=True, key="red_black_chart")
            
            # Display red/black trend
            red_black_trend = st.session_state.analyzer.get_red_black_trend(spins_df)
            st.subheader("Red/Black Trend Analysis")
            st.write(red_black_trend)
        
        elif analysis_option == "Dozens Distribution":
            st.subheader("Dozens Distribution Analysis")
            fig = st.session_state.visualizer.plot_dozens_distribution(spins_df)
            st.plotly_chart(fig, use_container_width=True, key="dozens_chart")
            
            # Display dozens trend
            dozens_trend = st.session_state.analyzer.get_dozens_trend(spins_df)
            st.subheader("Dozens Trend Analysis")
            st.write(dozens_trend)
        
        elif analysis_option == "Columns Distribution":
            st.subheader("Columns Distribution Analysis")
            fig = st.session_state.visualizer.plot_columns_distribution(spins_df)
            st.plotly_chart(fig, use_container_width=True, key="columns_chart")
            
            # Display columns trend
            columns_trend = st.session_state.analyzer.get_columns_trend(spins_df)
            st.subheader("Columns Trend Analysis")
            st.write(columns_trend)
        
        elif analysis_option == "High/Low Distribution":
            st.subheader("High/Low Distribution Analysis")
            fig = st.session_state.visualizer.plot_high_low_distribution(spins_df)
            st.plotly_chart(fig, use_container_width=True, key="high_low_chart")
            
            # Display high/low trend
            high_low_trend = st.session_state.analyzer.get_high_low_trend(spins_df)
            st.subheader("High/Low Trend Analysis")
            st.write(high_low_trend)
            
        elif analysis_option == "Wheel Bias Detection":
            st.subheader("Wheel Bias Detection Analysis (Fast Mode)")
            
            # Get current roulette type
            current_roulette_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
            
            # Display information about the minimum spins required
            st.info("**Wheel Bias Detection** requires at least 300 spins for reliable results.")
            
            # Show current spin count
            st.write(f"Current number of spins: **{len(spins_df)}**")
            
            if len(spins_df) < 50:
                st.warning("You need more spins for any meaningful bias detection. Please add at least 50 spins to see preliminary results.")
            else:
                # Perform the wheel bias analysis 
                bias_results = st.session_state.wheel_bias_detector.analyze_wheel_bias(
                    spins_df, 
                    current_roulette_type,
                    min_spins=50
                )
                
                # Display the results
                st.write("### Bias Detection Results")
                
                # Status and confidence
                status_color = "red" if bias_results["status"] == "significant_bias_detected" else \
                              "orange" if bias_results["status"] == "potential_bias_detected" else "green"
                
                st.write(f"**Status:** <span style='color:{status_color}'>{bias_results['status'].replace('_', ' ').title()}</span>", unsafe_allow_html=True)
                st.write(f"**Overall Confidence:** {bias_results['bias_confidence']:.2%}")
                st.write(f"**Message:** {bias_results['message']}")
                
                # Betting recommendations based on detected bias
                if bias_results["bias_confidence"] > 0.1:  # Show recommendations if there's at least some confidence
                    st.write("### Betting Recommendations Based on Wheel Bias")
                    
                    recommendations = bias_results["recommendations"]
                    
                    # Display single number recommendations only (simplified for performance)
                    if recommendations["single_numbers"]:
                        st.write("#### Top Recommended Numbers:")
                        # Limit to top 3 for better performance
                        for num_data in recommendations["single_numbers"][:3]:
                            st.write(f"Number {num_data['number']}: {num_data['deviation_pct']:.1f}% deviation, {num_data['confidence']:.2%} confidence")
                    
                    # Display overall strategy recommendation
                    st.write("#### Overall Strategy:")
                    st.write(recommendations["overall_strategy"])
                else:
                    st.info("No significant bias detected to generate betting recommendations.")
        
        # Pattern detection
        st.subheader("Pattern Detection")
        repeating_patterns = st.session_state.analyzer.find_repeating_patterns(spins_df)
        
        if repeating_patterns:
            st.write("Detected repeating patterns:")
            for pattern in repeating_patterns:
                st.write(f"Pattern: {pattern['pattern']}, Occurrences: {pattern['count']}")
        else:
            st.info("No significant repeating patterns detected.")
    
    else:
        st.info("No spin data available for analysis. Please add spins in the Spin Tracker tab.")

# Tab 3: Betting Strategies
with main_tab3:
    st.header("Betting Strategies")
    
    # Get data for current session
    spins_df = st.session_state.roulette_data.get_session_data(st.session_state.current_session)
    
    if spins_df is not None and not spins_df.empty:
        # Betting strategy selection
        st.subheader("Select Betting Strategy")
        strategy = st.selectbox(
            "Strategy:",
            ["Hot Numbers", "Due Numbers", "Pattern Based", "Martingale", "D'Alembert", "Fibonacci"]
        )
        
        # Get current roulette type
        current_roulette_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
        
        # Generate betting suggestions based on selected strategy
        suggestions = st.session_state.strategist.get_betting_suggestions(
            spins_df, 
            strategy, 
            current_roulette_type
        )
        
        # Display suggestions
        st.subheader("Suggested Bets:")
        
        if suggestions:
            for category, bets in suggestions.items():
                st.write(f"**{category}:**")
                if isinstance(bets, list):
                    for bet in bets:
                        st.write(f"- {bet}")
                else:
                    st.write(f"- {bets}")
        else:
            st.info("Not enough data to generate reliable betting suggestions.")
        
        # Strategy explanation
        st.subheader("Strategy Explanation")
        
        if strategy == "Hot Numbers":
            st.write("""
            **Hot Numbers Strategy** focuses on betting on numbers that have appeared most frequently in recent spins. 
            The theory is that certain numbers may be "hot" due to subtle biases in the wheel or ball.
            
            **Pros:**
            - Can capitalize on physical biases if they exist
            - Simple to understand and implement
            
            **Cons:**
            - Past results don't guarantee future outcomes
            - No mathematical edge in the long run on a fair wheel
            """)
        
        elif strategy == "Due Numbers":
            st.write("""
            **Due Numbers Strategy** (also called the Law of Averages) assumes that numbers that haven't appeared for a long time are "due" to appear soon.
            
            **Pros:**
            - Can capitalize on the regression to the mean phenomenon
            - Provides a structured approach to number selection
            
            **Cons:**
            - Suffers from the gambler's fallacy - past results don't influence future spins
            - No mathematical advantage in the long run
            """)
        
        elif strategy == "Pattern Based":
            st.write("""
            **Pattern Based Strategy** looks for repeating sequences or patterns in the spin history and bets based on expected continuations.
            
            **Pros:**
            - May identify actual biases if they exist
            - More sophisticated than simpler strategies
            
            **Cons:**
            - Patterns in truly random events are usually coincidental
            - Complex to implement correctly
            """)
        
        elif strategy == "Martingale":
            st.write("""
            **Martingale Strategy** involves doubling your bet after each loss, so that the first win recovers all previous losses plus a profit equal to the original stake.
            
            **Pros:**
            - Simple to understand and implement
            - Can work in the short term with even-money bets
            
            **Cons:**
            - Requires large bankroll for sustained losing streaks
            - Table limits eventually prevent doubling
            - Long-term expected value remains negative
            """)
        
        elif strategy == "D'Alembert":
            st.write("""
            **D'Alembert Strategy** is a more conservative progression system where you increase your bet by one unit after a loss and decrease it by one unit after a win.
            
            **Pros:**
            - Less aggressive than Martingale
            - Smaller bankroll requirements
            
            **Cons:**
            - Slower recovery from losses
            - Still has a negative expected value long-term
            """)
        
        elif strategy == "Fibonacci":
            st.write("""
            **Fibonacci Strategy** uses the Fibonacci sequence to determine bet sizes, increasing bets in the Fibonacci pattern after losses and moving back two steps after wins.
            
            **Pros:**
            - More measured progression than Martingale
            - Based on a natural mathematical sequence
            
            **Cons:**
            - Can still lead to high bets after a losing streak
            - Negative expected value in the long run
            """)
    
    else:
        st.info("No spin data available for betting suggestions. Please add spins in the Spin Tracker tab.")

# Add Advanced Strategy section to the Betting Strategies tab
with main_tab3:
    # Create tabs for different strategy sections
    strategy_tab1, strategy_tab2, strategy_tab3, strategy_tab4, strategy_tab5 = st.tabs([
        "🧠 Strategy Agent", 
        "🎯 Advanced Betting", 
        "🔄 Progression Systems",
        "🗺️ Wheel Visualization",
        "💰 Bet Simulator"
    ])
    
    with strategy_tab1:
        st.subheader("🧠 Advanced Strategy Agent")
    
    # Get the latest data for current session (force refresh)
    spins_df = st.session_state.roulette_data.get_session_data(st.session_state.current_session)
    current_roulette_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
    
    if spins_df is not None and not spins_df.empty:
        st.write("""
        The Advanced Strategy Agent uses reinforcement learning to analyze your spin data 
        and recommend optimal betting strategies based on your bankroll and the patterns detected.
        
        **✨ Adaptive Strategy Features:**
        * Automatically adjusts bet size based on your current bankroll
        * Adapts strategy based on detected patterns in spin history
        * Adjusts confidence levels using real-time statistical analysis
        * Protects your bankroll during losing streaks
        * Optimizes bet sizing for different confidence levels
        
        The system continuously learns from your results and updates its recommendations
        to maximize your potential returns while managing risk appropriately.
        """)
        
        # Display current bankroll and agent accuracy
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Bankroll", f"${st.session_state.bankroll:.2f}")
        with col2:
            st.metric("Agent Accuracy", f"{st.session_state.agent.get_accuracy() * 100:.1f}%")
        with col3:
            # Keep this simple metric
            st.metric("Recommended Strategy", st.session_state.agent.get_recommendation(st.session_state.bankroll))
        
        # Streamlined recommendation section
        st.subheader("📊 Strategy Recommendation")
        
        # Get agent recommendation (stored in variables for reuse)
        strategy_name = st.session_state.agent.get_recommendation(st.session_state.bankroll)
        recommended_bet = st.session_state.agent.get_bet_size_recommendation(st.session_state.bankroll)
        
        # Create two columns for the layout
        rec_col1, rec_col2 = st.columns([2, 3])
        
        with rec_col1:
            # Display the compact recommendation box
            st.info(f"Based on your current bankroll (${st.session_state.bankroll:.2f}):")
            st.markdown(f"**Strategy:** {strategy_name}")
            st.markdown(f"**Bet Size:** ${recommended_bet:.2f}")
        
        with rec_col2:
            # Get bet recommendations for visualization
            bet_recommendations = st.session_state.agent.get_specific_bet_recommendations(
                spins_df,
                current_roulette_type,
                st.session_state.bankroll
            )
            
            # Personalized Betting Strategy Heatmap
            heatmap_fig = st.session_state.visualizer.plot_betting_strategy_heatmap(
                spins_df,
                current_roulette_type,
                bet_recommendations
            )
            st.plotly_chart(heatmap_fig, use_container_width=True, key="betting_strategy_heatmap")
        
        # Real-Time Adaptation Metrics Section
        st.subheader("🔄 Real-Time Adaptation Metrics")
        
        # Calculate adaptation metrics
        if hasattr(st.session_state.agent, 'real_time_adapter') and len(st.session_state.agent.real_time_adapter.recent_spins) > 0:
            recent_count = len(st.session_state.agent.real_time_adapter.recent_spins)
            adaptation_confidence = min(0.95, recent_count / 20)  # Max out at 95% with 20+ spins
            
            # Create metrics for adaptation state
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Recent Spins Analyzed", f"{recent_count}")
            with col2:
                st.metric("Adaptation State", 
                         "Fully Adapted" if recent_count >= 20 else 
                         "Adapting" if recent_count >= 10 else "Initial Phase")
            with col3:
                st.metric("Adaptation Confidence", f"{adaptation_confidence * 100:.1f}%")
            
            # Display adaptation insights
            if recent_count >= 5:
                # Get recent numbers
                recent_numbers = [spin['number'] for spin in st.session_state.agent.real_time_adapter.recent_spins]
                
                # Calculate some basic statistics
                number_counts = {}
                for num in recent_numbers:
                    if num in number_counts:
                        number_counts[num] += 1
                    else:
                        number_counts[num] = 1
                
                sorted_numbers = sorted(number_counts.items(), key=lambda x: x[1], reverse=True)
                
                # Create an expander for detailed adaptation information
                with st.expander("View Real-Time Adaptation Details"):
                    st.write("### Recent Pattern Analysis")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("#### Recently Active Numbers")
                        for num, count in sorted_numbers[:3]:  # Top 3 active numbers
                            st.write(f"- Number **{num}** appeared **{count}** times")
                    
                    with col2:
                        # Calculate property frequencies
                        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
                        colors = {"red": 0, "black": 0, "green": 0}
                        for num in recent_numbers:
                            if num in ('0', '00'):
                                colors["green"] += 1
                            elif int(num) in red_numbers:
                                colors["red"] += 1
                            else:
                                colors["black"] += 1
                        
                        st.write("#### Color Distribution")
                        for color, count in colors.items():
                            if count > 0:
                                st.write(f"- **{color.capitalize()}**: {count} spins ({count/len(recent_numbers)*100:.1f}%)")
                    
                    # Show streak information
                    st.write("### Current Streaks")
                    
                    # Detect color streaks
                    if len(recent_numbers) >= 3:
                        current_streak = 1
                        last_num = recent_numbers[-1]
                        if last_num not in ('0', '00'):
                            current_property = "red" if int(last_num) in red_numbers else "black" 
                            for i in range(len(recent_numbers)-2, -1, -1):
                                num = recent_numbers[i]
                                if num not in ('0', '00'):
                                    prop = "red" if int(num) in red_numbers else "black"
                                    if prop == current_property:
                                        current_streak += 1
                                    else:
                                        break
                        
                            if current_streak >= 3:
                                st.write(f"🔥 **{current_property.capitalize()} streak**: {current_streak} spins")
                                if current_streak >= 6:
                                    st.write("💡 **Recommendation**: Consider betting against this streak continuing")
                                else:
                                    st.write("💡 **Recommendation**: This streak may continue for 1-2 more spins")
            else:
                st.info("Add more spins to see real-time adaptation metrics. At least 5 spins are needed for basic adaptation, and 20+ for optimal performance.")
        else:
            st.info("No spins recorded yet. Add spins to activate real-time adaptation.")
        
        # Add note about fast mode for 8-second window
        if len(spins_df) > 20:
            st.markdown("""
            **Quick Analysis Timer**: Roulette tables typically give you about 8 seconds between spins to place bets. 
            Use the Fast Analysis mode below for quicker recommendations.
            """)
            col1, col2 = st.columns([1, 2])
            with col1:
                st.session_state.fast_mode = st.toggle("Fast Analysis Mode (8-sec)", 
                                                           value=st.session_state.fast_mode,
                                                           help="Enable for quick analysis suitable for live casino play.")
            with col2:
                if st.session_state.fast_mode:
                    st.info("⚡ Fast mode enabled: Analysis optimized for 8-second decision window")
                else:
                    st.info("🔍 Comprehensive mode: Analysis may take longer but provides deeper insights")
        
        # Get and display strategy details
        strategy_details = get_strategy_description(strategy_name)
        if strategy_details:
            st.subheader("Strategy Details")
            st.markdown(f"**Description:** {strategy_details.get('description', 'N/A')}")
            st.markdown(f"**Risk Level:** {strategy_details.get('risk_level', 'N/A')}")
            st.markdown(f"**Complexity:** {strategy_details.get('complexity', 'N/A')}")
            st.markdown(f"**Bankroll Impact:** {strategy_details.get('bankroll_impact', 'N/A')}")
            st.markdown(f"**Best For:** {strategy_details.get('best_for', 'N/A')}")
            st.markdown(f"**Worst For:** {strategy_details.get('worst_for', 'N/A')}")
        
        # New section for specific bet recommendations based on statistical analysis
        st.subheader("Statistical Bet Recommendations")
        st.write("""
        Below are specific betting recommendations based on statistical analysis 
        of your spin history. Each recommendation includes a confidence score 
        indicating how strongly the pattern deviates from random expectation.
        """)
        
        # Get specific bet recommendations
        # Show a progress bar while analysis is running
        with st.spinner("Analyzing spin patterns..."):
            progress_bar = st.progress(0, text="Starting analysis...")
            
            # Create a timer to update the progress bar
            if st.session_state.fast_mode:
                # Fast mode: update progress bar to simulate 8-second window
                import time
                start_time = time.time()
                max_time = 8.0  # Maximum time in seconds
                
                # Function to update progress bar
                def update_progress():
                    elapsed = time.time() - start_time
                    progress = min(elapsed / max_time, 0.99)  # Cap at 99% until complete
                    progress_bar.progress(progress, text=f"Analyzing spin patterns... {int(progress * 100)}%")
                    return progress < 0.99
                
                # Start analysis with progress updates
                while update_progress():
                    pass  # Removed animation delay
                    # Break early if we're past 7.5 seconds to avoid hitting the limit
                    if time.time() - start_time > 7.5:
                        break
            
            # Get the recommendations from the agent
            specific_recommendations = st.session_state.agent.get_specific_bet_recommendations(
                spins_df, 
                current_roulette_type, 
                st.session_state.bankroll
            )
            
            # Complete the progress bar
            progress_bar.progress(1.0, text="Analysis complete!")
            # Removed animation delay
            progress_bar.empty()  # Remove the progress bar
        
        # Add smooth loading animation for recommendation results
        with st.spinner("Preparing recommendation display..."):
            # Create a container for the animated results
            results_container = st.container()
            
            # Display recommendation confidence explanation with animation
            with results_container:
                # Add a beginner-friendly confidence explanation section
                with st.expander("🔍 Understanding Confidence Scores (Click to expand)", expanded=True):
                    st.markdown("""
                    ### What do Confidence Scores Mean?
                    
                    Confidence scores tell you how strongly the system believes in its recommendations:
                    
                    | Confidence Level | What It Means | Recommended Action |
                    |------------------|---------------|-------------------|
                    | **90-100%** | **Very Strong** | Consider these bets a top priority |
                    | **75-89%** | **Strong** | Worth serious consideration |
                    | **60-74%** | **Moderate** | Potentially valuable patterns detected |
                    | **40-59%** | **Fair** | Some indication of a pattern |
                    | **Below 40%** | **Weak** | Not enough evidence to recommend |
                    
                    **Key Points:**
                    - Higher confidence means a stronger statistical pattern was detected
                    - Even high confidence doesn't guarantee wins (it's still gambling!)
                    - Confidence is based on how much a pattern deviates from random chance
                    - More data (more spins) generally leads to more reliable confidence scores
                    
                    Remember: No betting system can beat the house edge in the long run. Use responsibly!
                    """)
                
                # Display explanation if available, or adaptation message
                if "confidence_explanation" in specific_recommendations:
                    st.info(specific_recommendations["confidence_explanation"])
                elif "message" in specific_recommendations:
                    st.info(specific_recommendations["message"])
                else:
                    st.info("Analysis complete. Review the recommendations above.")
                
                # Display a clear summary of all recommendations at the top with animation
                st.subheader("💰 Quick Recommendation Summary")
                
                # Create placeholder for animated content
                summary_placeholder = st.empty()
                
                # Create a container for animated content
                with summary_placeholder.container():
                    # Create summary card with all recommendations (will be displayed with animation)
                    summary_cols = st.columns(2)
                    
                    # Removed animation delay
                    
                    # First, calculate all confidence values and find highest confidence recommendation
                    highest_confidence = 0
                    best_bet_type = "None"
                    best_bet_value = "None"
                    
                    # Check all bet types and find the one with highest confidence
                    if specific_recommendations["red_black"]["recommendation"]:
                        conf = specific_recommendations["red_black"]["confidence"]
                        if conf > highest_confidence:
                            highest_confidence = conf
                            best_bet_type = "Color"
                            best_bet_value = specific_recommendations["red_black"]["recommendation"].upper()
                    
                    if specific_recommendations["even_odd"]["recommendation"]:
                        conf = specific_recommendations["even_odd"]["confidence"]
                        if conf > highest_confidence:
                            highest_confidence = conf
                            best_bet_type = "Parity"
                            best_bet_value = specific_recommendations["even_odd"]["recommendation"].upper()
                    
                    if specific_recommendations["high_low"]["recommendation"]:
                        conf = specific_recommendations["high_low"]["confidence"]
                        if conf > highest_confidence:
                            highest_confidence = conf
                            best_bet_type = "Range"
                            best_bet_value = specific_recommendations["high_low"]["recommendation"].upper()
                    
                    if specific_recommendations["columns"]["recommendation"]:
                        conf = specific_recommendations["columns"]["confidence"]
                        if conf > highest_confidence:
                            highest_confidence = conf
                            best_bet_type = "Column"
                            best_bet_value = specific_recommendations["columns"]["recommendation"].upper()
                    
                    if specific_recommendations["dozens"]["recommendation"]:
                        conf = specific_recommendations["dozens"]["confidence"]
                        if conf > highest_confidence:
                            highest_confidence = conf
                            best_bet_type = "Dozen"
                            best_bet_value = specific_recommendations["dozens"]["recommendation"].upper()
                    
                    # Animate first column appearance
                    with summary_cols[0]:
                        st.markdown("### Best Bets")
                        
                        # Add top recommended bets with subtle animations
                        st.markdown("#### Top Recommended Bets:")
                        
                        # Start with the overall best recommendation
                        if highest_confidence > 0:
                            st.markdown(f"**{best_bet_type}:** {best_bet_value} (Confidence: {highest_confidence*100:.0f}%)")
                        
                        # Add single numbers
                        if specific_recommendations["single_numbers"]:
                            # Removed animation delay
                            numbers_str = ", ".join([n["number"] for n in specific_recommendations["single_numbers"][:2]])
                            st.markdown(f"**Numbers:** {numbers_str}")
                        
                        # Add split bets
                        if specific_recommendations["split_bets"]:
                            # Removed animation delay
                            splits_str = ", ".join([s["numbers"] for s in specific_recommendations["split_bets"][:2]])
                            st.markdown(f"**Split Bets:** {splits_str}")
                        
                        # Add corner bets
                        if "corner_bets" in specific_recommendations and specific_recommendations["corner_bets"]:
                            # Removed animation delay
                            corners_str = ", ".join([c["numbers"] for c in specific_recommendations["corner_bets"][:1]])
                            st.markdown(f"**Corner Bets:** {corners_str}")
                        
                        # Add street bets (3 consecutive numbers in a row)
                        # Since we don't have explicit street bet analysis, we'll derive it from hot numbers
                        if specific_recommendations["single_numbers"]:
                            # Get hot numbers and their confidence scores
                            hot_nums = [int(n["number"]) for n in specific_recommendations["single_numbers"] if str(n["number"]).isdigit()]
                            hot_num_confidence = {int(n["number"]): n["confidence"] for n in specific_recommendations["single_numbers"] if str(n["number"]).isdigit()}
                            
                            # Track streets that contain hot numbers
                            streets = []
                            street_scores = {}
                            
                            # Check each hot number
                            for num in hot_nums:
                                # Find which street this number belongs to
                                row = (num - 1) // 3
                                street_start = row * 3 + 1
                                street = f"{street_start}-{street_start+1}-{street_start+2}"
                                
                                # Add street if not already in list
                                if street not in streets:
                                    streets.append(street)
                                    # Initialize score with the confidence of the hot number
                                    street_scores[street] = hot_num_confidence[num]
                                else:
                                    # Increase score if another hot number is in the same street
                                    street_scores[street] += hot_num_confidence[num]
                            
                            # Sort streets by their scores (higher confidence first)
                            sorted_streets = sorted(streets, key=lambda s: street_scores[s], reverse=True)
                            
                            if sorted_streets:
                                # Removed animation delay
                                # Show up to 2 streets, prioritizing those with higher scores
                                streets_str = ", ".join(sorted_streets[:2])
                                st.markdown(f"**Street Bets:** {streets_str}")
                    
                    # Animate second column with a slight delay
                    with summary_cols[1]:
                        # Removed animation delay
                        st.markdown("### Bet Details")
                        
                        # Display recommended bet size
                        if specific_recommendations.get("highest_confidence", 0) > 0:
                            st.success(f"Recommended bet size: ${specific_recommendations.get('recommended_bet_size', 0):.2f}")
                        
                        # Show all the even money bets
                        st.markdown("#### Even Money Bets:")
                        
                        if specific_recommendations["red_black"]["recommendation"]:
                            # Removed animation delay
                            st.markdown(f"**Color:** {specific_recommendations['red_black']['recommendation'].upper()}")
                        
                        if specific_recommendations["even_odd"]["recommendation"]:
                            # Removed animation delay
                            st.markdown(f"**Parity:** {specific_recommendations['even_odd']['recommendation'].upper()}")
                        
                        if specific_recommendations["high_low"]["recommendation"]:
                            # Removed animation delay
                            st.markdown(f"**Range:** {specific_recommendations['high_low']['recommendation'].upper()}")
                        
                        # Show all the column/dozen bets
                        # Removed animation delay
                        st.markdown("#### Column/Dozen Bets:")
                        
                        if specific_recommendations["columns"]["recommendation"]:
                            st.markdown(f"**Column:** {specific_recommendations['columns']['recommendation']}")
                        
                        if specific_recommendations["dozens"]["recommendation"]:
                            dozen_rec = specific_recommendations['dozens']['recommendation']
                            st.markdown(f"**Dozen:** {dozen_rec}")
                            # Display pattern info if available
                            if "pattern_info" in specific_recommendations['dozens'] and specific_recommendations['dozens']['pattern_info']:
                                st.markdown(f"*{specific_recommendations['dozens']['pattern_info']}*")
                            
                        # Indicate if using fast mode
                        # Removed animation delay
                        st.markdown("---")
                        if st.session_state.fast_mode:
                            st.caption("⚡ Analysis completed in fast mode for 8-second window")
                        else:
                            st.caption("🔍 Comprehensive analysis mode")
        
        # Create animated display of tabs section
        with st.spinner("Loading detailed recommendations..."):
            # Removed animation delay
            
            # Add an informational message to introduce the detailed tabs
            st.info("Explore detailed betting recommendations in the tabs below")
            
            # Create tabs for different bet types with a visual transition
            bet_tabs = st.tabs(["Numbers", "Split Bets", "Corner Bets", "Columns/Dozens", "Even Money Bets"])
        
        with bet_tabs[0]:
            st.subheader("🎯 Single Number Bets")
            if specific_recommendations["single_numbers"]:
                for num_data in specific_recommendations["single_numbers"]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Number {num_data['number']}** - Appeared {num_data['count']} times ({num_data['frequency']})")
                        st.markdown(f"Deviation from expected: {num_data['deviation']}x")
                    with col2:
                        # Display confidence as progress bar
                        confidence = num_data['confidence'] * 100
                        st.progress(num_data['confidence'], text=f"Confidence: {confidence:.0f}%")
            else:
                st.write("No statistically significant hot numbers detected in your data.")
        
        with bet_tabs[1]:
            st.subheader("🔀 Split Bet Recommendations")
            if specific_recommendations["split_bets"]:
                for split_data in specific_recommendations["split_bets"]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Split {split_data['numbers']}** - Combined occurrences: {split_data['combined_count']}")
                        st.markdown(f"Deviation from expected: {split_data['deviation']}x")
                    with col2:
                        # Display confidence as progress bar
                        confidence = split_data['confidence'] * 100
                        st.progress(split_data['confidence'], text=f"Confidence: {confidence:.0f}%")
            else:
                st.write("No statistically significant split bets detected in your data.")
        
        with bet_tabs[2]:
            st.subheader("🔳 Corner Bet Recommendations")
            if "corner_bets" in specific_recommendations and specific_recommendations["corner_bets"]:
                for corner_data in specific_recommendations["corner_bets"]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Corner {corner_data['numbers']}** - Combined occurrences: {corner_data['combined_count']}")
                        st.markdown(f"Deviation from expected: {corner_data['deviation']}x")
                        if 'hot_matches' in corner_data:
                            st.markdown(f"Hot numbers in this corner: {corner_data['hot_matches']}")
                    with col2:
                        # Display confidence as progress bar
                        confidence = corner_data['confidence'] * 100
                        st.progress(corner_data['confidence'], text=f"Confidence: {confidence:.0f}%")
            else:
                st.write("No statistically significant corner bets detected in your data.")
        
        with bet_tabs[3]:
            st.subheader("🎯 Column and Dozen Bets")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### Column Bets")
                if specific_recommendations["columns"]["recommendation"]:
                    col_data = specific_recommendations["columns"]
                    st.markdown(f"**Recommendation: {col_data['recommendation']}**")
                    counts = col_data["counts"]
                    for col_name, count in counts.items():
                        st.markdown(f"{col_name}: {count} spins")
                    confidence = col_data['confidence'] * 100
                    st.progress(col_data['confidence'], text=f"Confidence: {confidence:.0f}%")
                else:
                    st.write("No statistically significant column bias detected.")
            
            with col2:
                st.markdown("##### Dozen Bets")
                if specific_recommendations["dozens"]["recommendation"]:
                    dozen_data = specific_recommendations["dozens"]
                    st.markdown(f"**Recommendation: {dozen_data['recommendation']}**")
                    
                    # Display counts
                    counts = dozen_data["counts"]
                    for dozen_name, count in counts.items():
                        st.markdown(f"{dozen_name}: {count} spins")
                    
                    # Display enhanced pattern information if available
                    if "pattern_detected" in dozen_data and dozen_data["pattern_detected"]:
                        st.markdown("##### Pattern Detected:")
                        st.markdown(f"_{dozen_data['pattern_info']}_")
                    
                    # Display recent hot/cold dozen information if available
                    if "recent_hot" in dozen_data:
                        st.markdown(f"**Recently Hot:** {dozen_data['recent_hot']}")
                    if "recent_cold" in dozen_data:
                        st.markdown(f"**Recently Cold:** {dozen_data['recent_cold']}")
                    
                    # Show confidence with visual indicator
                    confidence = dozen_data['confidence'] * 100
                    st.progress(dozen_data['confidence'], text=f"Confidence: {confidence:.0f}%")
                else:
                    st.write("No statistically significant dozen bias detected.")
        
        with bet_tabs[4]:
            st.subheader("💰 Even Money Bets")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("##### Red/Black")
                if specific_recommendations["red_black"]["recommendation"]:
                    color_data = specific_recommendations["red_black"]
                    st.markdown(f"**Recommendation: {color_data['recommendation']}**")
                    counts = color_data["counts"]
                    for color, count in counts.items():
                        st.markdown(f"{color.capitalize()}: {count} spins")
                    confidence = color_data['confidence'] * 100
                    st.progress(color_data['confidence'], text=f"Confidence: {confidence:.0f}%")
                else:
                    st.write("No significant color bias detected.")
                    
            with col2:
                st.markdown("##### Even/Odd")
                if specific_recommendations["even_odd"]["recommendation"]:
                    parity_data = specific_recommendations["even_odd"]
                    st.markdown(f"**Recommendation: {parity_data['recommendation']}**")
                    counts = parity_data["counts"]
                    for parity, count in counts.items():
                        st.markdown(f"{parity.capitalize()}: {count} spins")
                    confidence = parity_data['confidence'] * 100
                    st.progress(parity_data['confidence'], text=f"Confidence: {confidence:.0f}%")
                else:
                    st.write("No significant even/odd bias detected.")
                    
            with col3:
                st.markdown("##### High/Low")
                if specific_recommendations["high_low"]["recommendation"]:
                    range_data = specific_recommendations["high_low"]
                    st.markdown(f"**Recommendation: {range_data['recommendation']}**")
                    counts = range_data["counts"]
                    for range_name, count in counts.items():
                        st.markdown(f"{range_name.capitalize()}: {count} spins")
                    confidence = range_data['confidence'] * 100
                    st.progress(range_data['confidence'], text=f"Confidence: {confidence:.0f}%")
                else:
                    st.write("No significant high/low bias detected.")
        
        # Simulation section
        st.subheader("Strategy Simulation")
        
        # Get available strategies
        available_strategies = st.session_state.strategy_engine.get_strategy_names()
        
        # Allow user to select strategy for simulation
        sim_strategy = st.selectbox("Select Strategy to Simulate:", available_strategies)
        
        # Simulation parameters
        col1, col2 = st.columns(2)
        with col1:
            sim_bankroll = st.number_input("Starting Bankroll:", 
                                          min_value=10.0, 
                                          max_value=10000.0, 
                                          value=st.session_state.bankroll,
                                          step=10.0)
        with col2:
            bet_size = st.number_input("Base Bet Size:", 
                                     min_value=0.10, 
                                     max_value=sim_bankroll/10,  # Max 10% of bankroll
                                     value=recommended_bet,
                                     step=0.10)
        
        # Bet type selection for simulation
        bet_type = st.selectbox("Select Bet Type:", 
                              ["red", "black", "even", "odd", "high", "low", 
                               "dozen:first", "dozen:second", "dozen:third", 
                               "column:first", "column:second", "column:third"])
        
        # Parse bet type and value
        if ":" in bet_type:
            bet_type_main, bet_value = bet_type.split(":")
        else:
            bet_type_main, bet_value = bet_type, None
        
        # Run simulation button
        if st.button("Run Simulation"):
            # Reset the strategy and performance tracker
            st.session_state.strategy_engine.reset_strategy(sim_strategy)
            
            # Get the spin data as a list of numbers
            spin_numbers = spins_df['number'].tolist()
            
            # Set up simulation variables
            current_bankroll = sim_bankroll
            results = []
            win_count = 0
            loss_count = 0
            
            # Set the base bet for the selected strategy
            st.session_state.strategy_engine.set_base_bet(sim_strategy, bet_size)
            
            # Run through the simulation
            for i, number in enumerate(spin_numbers):
                # Get the current bet amount
                current_bet = st.session_state.strategy_engine.get_bet_amount(
                    sim_strategy, 
                    i > 0 and results[-1]['win'] if results else False
                )
                
                # Adjust if bet is more than current bankroll
                current_bet = min(current_bet, current_bankroll)
                
                # Evaluate the bet
                win, payout_multiple = st.session_state.strategy_engine.evaluate_bet(
                    bet_type_main, 
                    bet_value, 
                    number
                )
                
                # Calculate profit/loss
                profit = current_bet * payout_multiple if win else -current_bet
                
                # Update bankroll
                current_bankroll += profit
                
                # Track wins/losses
                if win:
                    win_count += 1
                else:
                    loss_count += 1
                
                # Record result
                results.append({
                    'spin': i + 1,
                    'number': number,
                    'bet_amount': current_bet,
                    'win': win,
                    'profit': profit,
                    'bankroll': current_bankroll
                })
                
                # Record in agent and performance tracker
                st.session_state.agent.record_result(number, sim_strategy, win, profit)
                st.session_state.performance_tracker.update(
                    sim_strategy, 
                    win, 
                    profit, 
                    current_bet
                )
                
                # Break if bankrupt
                if current_bankroll <= 0:
                    break
            
            # Display simulation results with animated appearance
            with st.spinner("Generating simulation results..."):
                # Removed animation delay
                st.success("Simulation completed successfully!")
                st.subheader("Simulation Results")
            
            # Key metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Final Bankroll", f"${current_bankroll:.2f}", 
                        f"{(current_bankroll - sim_bankroll):.2f}")
            with col2:
                total_spins = win_count + loss_count
                win_rate = (win_count / total_spins * 100) if total_spins > 0 else 0
                st.metric("Win Rate", f"{win_rate:.1f}%")
            with col3:
                roi = ((current_bankroll - sim_bankroll) / sim_bankroll * 100) if sim_bankroll > 0 else 0
                st.metric("ROI", f"{roi:.1f}%")
            
            # Results table
            st.subheader("Detailed Results")
            results_df = pd.DataFrame(results)
            st.dataframe(results_df)
            
            # Bankroll chart
            st.subheader("Bankroll Progression")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=results_df['spin'], 
                y=results_df['bankroll'],
                mode='lines+markers',
                name='Bankroll',
                line=dict(color='blue', width=2)
            ))
            fig.update_layout(
                title="Bankroll Progression During Simulation",
                xaxis_title="Spin Number",
                yaxis_title="Bankroll ($)",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True, key="bankroll_progression_chart")
            
            # Update agent recommendation
            st.subheader("Updated Agent Recommendation")
            new_strategy = st.session_state.agent.get_recommendation(current_bankroll)
            st.info(f"Based on the simulation results, the agent now recommends the {new_strategy} strategy.")
    else:
        st.info("No spin data available for strategy agent. Please add spins in the Spin Tracker tab.")

# Statistics Section
# Add Statistics section to the Analysis tab
with main_tab2:
    st.subheader("📊 Session Statistics")
    
    # Get data for current session
    spins_df = st.session_state.roulette_data.get_session_data(st.session_state.current_session)
    
    if spins_df is not None and not spins_df.empty:
        # Overall session statistics
        st.subheader("Session Overview")
        
        # Create three columns for key stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Spins", len(spins_df))
        
        with col2:
            session_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
            st.metric("Roulette Type", session_type)
        
        with col3:
            duration = st.session_state.analyzer.get_session_duration(spins_df)
            st.metric("Session Duration", duration)
        
        # Display probability-related statistics
        st.subheader("Probability Analysis")
        
        # Create tabs for different probability analysis views
        prob_tab1, prob_tab2, prob_tab3 = st.tabs(["Actual vs Expected", "Deviation Analysis", "Chi-Square Test"])
        
        with prob_tab1:
            st.write("### Actual vs Expected Occurrences")
            
            # Get actual vs expected comparison
            comparison_df = st.session_state.analyzer.compare_actual_vs_expected(
                spins_df, 
                st.session_state.roulette_data.get_session_type(st.session_state.current_session)
            )
            
            st.dataframe(comparison_df)
            
            # Visualize the comparison
            fig = st.session_state.visualizer.plot_actual_vs_expected(comparison_df)
            st.plotly_chart(fig, use_container_width=True, key="actual_vs_expected_chart")
        
        with prob_tab2:
            st.write("### Deviation from Expected")
            
            # Calculate and display deviation
            deviation_df = st.session_state.analyzer.calculate_deviation_from_expected(
                spins_df, 
                st.session_state.roulette_data.get_session_type(st.session_state.current_session)
            )
            
            st.dataframe(deviation_df)
            
            # Visualize deviations
            fig = st.session_state.visualizer.plot_deviations(deviation_df)
            st.plotly_chart(fig, use_container_width=True, key="deviations_chart")
        
        with prob_tab3:
            st.write("### Randomness Test (Chi-Square)")
            
            # Perform chi-square test for randomness
            chi_square_result, p_value, is_random = st.session_state.analyzer.chi_square_test(
                spins_df, 
                st.session_state.roulette_data.get_session_type(st.session_state.current_session)
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Chi-Square Value", f"{chi_square_result:.2f}")
            
            with col2:
                st.metric("p-value", f"{p_value:.4f}")
            
            if is_random:
                st.success("The spin results appear to be random (failed to reject null hypothesis).")
            else:
                st.warning("The spin results show some non-random patterns (rejected null hypothesis).")
            
            st.write("""
            **Note:** Chi-square test compares the observed frequency distribution with the expected frequency distribution
            for a fair roulette wheel. A low p-value (typically < 0.05) suggests the distribution is not random.
            """)
        
        # Win-loss simulation based on common betting patterns
        st.subheader("Win/Loss Simulation")
        
        betting_pattern = st.selectbox(
            "Select a betting pattern to simulate:",
            ["Red/Black", "Even/Odd", "High/Low", "Dozens", "Columns", "Single Number"]
        )
        
        bankroll = st.number_input("Initial bankroll (units):", min_value=10.0, value=100.0, step=10.0)
        bet_size = st.number_input("Bet size (units):", min_value=0.10, value=1.0, step=0.10)
        
        if st.button("Run Pattern Simulation"):
            results = st.session_state.analyzer.simulate_betting(
                spins_df, 
                betting_pattern, 
                bankroll, 
                bet_size,
                st.session_state.roulette_data.get_session_type(st.session_state.current_session)
            )
            
            # Display simulation results
            st.write(f"### Simulation Results for {betting_pattern} Betting")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Final Bankroll", f"{results['final_bankroll']:.2f} units")
            
            with col2:
                profit_loss = results['final_bankroll'] - bankroll
                st.metric("Profit/Loss", f"{profit_loss:.2f} units", delta=f"{profit_loss:.2f}")
            
            with col3:
                win_rate = results['win_rate'] * 100
                st.metric("Win Rate", f"{win_rate:.1f}%")
            
            # Plot bankroll progression
            fig = st.session_state.visualizer.plot_bankroll_progression(results['bankroll_history'])
            st.plotly_chart(fig, use_container_width=True, key="winloss_simulation_chart")
    
    else:
        st.info("No spin data available for statistics. Please add spins in the Spin Tracker tab.")
        
    # Advanced Betting Tab
    with strategy_tab2:
        st.subheader("🎯 Advanced Betting Analysis")
        
        st.write("""
        This section provides sophisticated betting analysis that goes beyond basic strategies, 
        looking for patterns based on wheel physics, sector betting, and advanced statistical models.
        """)
        
        # Check if we have spin data
        spins_df = clean_dataframe_for_analysis(st.session_state.roulette_data.get_session_data(st.session_state.current_session))
        current_roulette_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
        
        if spins_df is not None and not spins_df.empty and len(spins_df) >= 20:
            # Create tabs for different advanced betting analyses
            advanced_tabs = st.tabs([
                "Sector Betting", 
                "Split & Corner Bets",
                "Sleeper Numbers",
                "Wheel Bias"
            ])
            
            # Sector Betting Analysis
            with advanced_tabs[0]:
                st.subheader("🔄 Sector Betting Analysis")
                
                st.write("""
                Sector betting focuses on groups of numbers based on their physical arrangement 
                on the roulette wheel rather than their position on the betting table.
                
                This approach can help identify wheel bias or physical imperfections that may
                cause certain sectors to come up more frequently.
                """)
                
                # Get sector analysis
                sector_analysis = st.session_state.advanced_betting.analyze_sectors(
                    spins_df, current_roulette_type
                )
                
                if sector_analysis and "sectors" in sector_analysis:
                    sectors = sector_analysis["sectors"]
                    if sectors:
                        # Create metrics for each sector
                        st.subheader("Wheel Sector Performance")
                        
                        sector_cols = st.columns(3)
                        for i, (sector_name, data) in enumerate(sectors.items()):
                            with sector_cols[i % 3]:
                                # Format sector name for display
                                display_name = sector_name.replace("_", " ").title()
                                
                                # Calculate hit percentage and expected percentage
                                hit_pct = data.get("hit_percentage", 0)
                                expected_pct = (len(data.get("numbers", [])) / (37 if current_roulette_type == "European" else 38)) * 100
                                
                                # Calculate delta
                                delta = hit_pct - expected_pct
                                
                                # Display metric with delta
                                st.metric(
                                    f"{display_name}",
                                    f"{hit_pct:.1f}%",
                                    f"{delta:.1f}%" if abs(delta) > 1.0 else "Normal",
                                    delta_color="normal" if abs(delta) <= 1.0 else "off" if delta < 0 else "inverse"
                                )
                                
                                # Show recommendation
                                recommendation = data.get("recommendation", "NEUTRAL")
                                if recommendation == "BET":
                                    st.success(f"✅ Recommended: **{delta:.1f}%** above expected")
                                elif recommendation == "AVOID":
                                    st.error(f"❌ Avoid: **{abs(delta):.1f}%** below expected")
                                else:
                                    st.info("✓ Normal performance")
                        
                        # Create detailed table of sector statistics
                        st.subheader("Detailed Sector Statistics")
                        
                        # Prepare data for the table
                        sector_stats = []
                        for sector_name, data in sectors.items():
                            sector_stats.append({
                                "Sector": sector_name.replace("_", " ").title(),
                                "Numbers": ", ".join(str(n) for n in data.get("numbers", [])[:8]) + 
                                           ("..." if len(data.get("numbers", [])) > 8 else ""),
                                "Count": data.get("hits", 0),
                                "Hit %": f"{data.get('hit_percentage', 0):.1f}%",
                                "Expected %": f"{(len(data.get('numbers', [])) / (37 if current_roulette_type == 'European' else 38)) * 100:.1f}%",
                                "Deviation": f"{data.get('deviation', 0):.2f}",
                                "Significant": "Yes" if data.get("significant_bias", False) else "No",
                                "Recommendation": data.get("recommendation", "NEUTRAL")
                            })
                        
                        # Convert to DataFrame for display
                        sector_df = pd.DataFrame(sector_stats)
                        st.dataframe(sector_df, use_container_width=True)
                        
                        # Show the top recommendation
                        best_sector = None
                        best_confidence = 0
                        for sector_name, data in sectors.items():
                            if data.get("recommendation", "") == "BET" and data.get("confidence", 0) > best_confidence:
                                best_sector = sector_name
                                best_confidence = data.get("confidence", 0)
                        
                        if best_sector:
                            st.success(f"### Top Recommendation: Bet on {best_sector.replace('_', ' ').title()}")
                            st.write(f"Confidence: {best_confidence * 100:.1f}%")
                            
                            # Show the specific numbers in this sector
                            numbers = sectors[best_sector].get("numbers", [])
                            if numbers:
                                number_str = ", ".join(str(n) for n in sorted(numbers))
                                st.write(f"Numbers in this sector: {number_str}")
                    else:
                        st.info("No significant sector patterns detected in your data.")
                else:
                    st.warning("Unable to perform sector analysis. Please ensure you have sufficient spin data.")
            
            # Split & Corner Bets Analysis
            with advanced_tabs[1]:
                st.subheader("🎲 Split & Corner Bet Opportunities")
                
                st.write("""
                Split bets (two adjacent numbers) and corner bets (four numbers in a square)
                can offer better payouts than outside bets while still providing better odds than 
                single number bets.
                
                This analysis identifies which split and corner bets show statistical bias
                based on your spin history.
                """)
                
                # Get split and corner analysis
                bet_opportunities = st.session_state.advanced_betting.find_split_corner_opportunities(
                    spins_df, current_roulette_type
                )
                
                if bet_opportunities:
                    # Display split bet opportunities
                    if "split_opportunities" in bet_opportunities and bet_opportunities["split_opportunities"]:
                        st.subheader("Split Bet Opportunities (Pays 17:1)")
                        
                        # Create a clean table of opportunities
                        split_data = []
                        for opp in bet_opportunities["split_opportunities"]:
                            split_data.append({
                                "Numbers": " & ".join(str(n) for n in opp.get("numbers", [])),
                                "Hit Count": opp.get("combined_hits", 0),
                                "Observed %": f"{opp.get('observed_probability', 0) * 100:.2f}%",
                                "Expected %": f"{opp.get('expected_probability', 0) * 100:.2f}%",
                                "Deviation": f"{opp.get('deviation_factor', 1):.2f}x",
                                "Confidence": f"{opp.get('confidence', 0) * 100:.1f}%"
                            })
                        
                        # Display as DataFrame
                        split_df = pd.DataFrame(split_data)
                        st.dataframe(split_df, use_container_width=True)
                        
                        # Show the top split bet recommendation
                        if split_data:
                            top_split = bet_opportunities["split_opportunities"][0]
                            numbers = top_split.get("numbers", [])
                            confidence = top_split.get("confidence", 0)
                            
                            if numbers and confidence > 0.2:
                                st.success(f"### Top Split Bet: {' & '.join(str(n) for n in numbers)}")
                                st.write(f"Confidence: {confidence * 100:.1f}%")
                                st.write(f"This split appears {top_split.get('deviation_factor', 1):.2f}x more often than expected")
                    else:
                        st.info("No significant split bet opportunities detected.")
                    
                    # Display corner bet opportunities
                    if "corner_opportunities" in bet_opportunities and bet_opportunities["corner_opportunities"]:
                        st.subheader("Corner Bet Opportunities (Pays 8:1)")
                        
                        # Create a clean table of opportunities
                        corner_data = []
                        for opp in bet_opportunities["corner_opportunities"]:
                            corner_data.append({
                                "Numbers": ", ".join(str(n) for n in opp.get("numbers", [])),
                                "Hit Count": opp.get("combined_hits", 0),
                                "Observed %": f"{opp.get('observed_probability', 0) * 100:.2f}%",
                                "Expected %": f"{opp.get('expected_probability', 0) * 100:.2f}%",
                                "Deviation": f"{opp.get('deviation_factor', 1):.2f}x",
                                "Confidence": f"{opp.get('confidence', 0) * 100:.1f}%"
                            })
                        
                        # Display as DataFrame
                        corner_df = pd.DataFrame(corner_data)
                        st.dataframe(corner_df, use_container_width=True)
                        
                        # Show the top corner bet recommendation
                        if corner_data:
                            top_corner = bet_opportunities["corner_opportunities"][0]
                            numbers = top_corner.get("numbers", [])
                            confidence = top_corner.get("confidence", 0)
                            
                            if numbers and confidence > 0.2:
                                st.success(f"### Top Corner Bet: {', '.join(str(n) for n in numbers)}")
                                st.write(f"Confidence: {confidence * 100:.1f}%")
                                st.write(f"This corner appears {top_corner.get('deviation_factor', 1):.2f}x more often than expected")
                    else:
                        st.info("No significant corner bet opportunities detected.")
                else:
                    st.warning("Unable to analyze split and corner bets. Please ensure you have sufficient spin data.")
            
            # Sleeper Numbers Analysis
            with advanced_tabs[2]:
                st.subheader("💤 Sleeper Number Analysis")
                
                st.write("""
                Sleeper numbers are those that haven't appeared for a statistically unusual period.
                While every spin is independent, tracking sleepers can help identify potential biases
                in the wheel or unusual patterns.
                """)
                
                # Controls for sleeper analysis
                col1, col2 = st.columns(2)
                with col1:
                    min_absence = st.slider("Minimum Spins Absent", 10, 50, 20, 
                                           help="Minimum number of spins a number must be absent to be considered a sleeper")
                
                # Get sleeper analysis
                sleeper_analysis = st.session_state.advanced_betting.get_sleeper_numbers(
                    spins_df, current_roulette_type, min_absence_threshold=min_absence
                )
                
                if sleeper_analysis and "sleepers" in sleeper_analysis:
                    sleepers = sleeper_analysis["sleepers"]
                    if sleepers:
                        # Show sleeper metrics
                        st.subheader("Top Sleeper Numbers")
                        
                        # Create metrics for top sleepers
                        sleeper_cols = st.columns(min(3, len(sleepers)))
                        for i, sleeper in enumerate(sleepers[:3]):
                            with sleeper_cols[i]:
                                number = sleeper.get("number", "")
                                absent = sleeper.get("spins_absent", 0)
                                expected = sleeper.get("expected_gap", 0)
                                overdue = sleeper.get("overdue_factor", 0)
                                
                                st.metric(
                                    f"Number {number}",
                                    f"{absent} spins",
                                    f"{overdue:.1f}x overdue"
                                )
                        
                        # Create detailed table of sleepers
                        st.subheader("All Sleeper Numbers")
                        
                        # Prepare data for the table
                        sleeper_data = []
                        for sleeper in sleepers:
                            sleeper_data.append({
                                "Number": sleeper.get("number", ""),
                                "Spins Absent": sleeper.get("spins_absent", 0),
                                "Expected Gap": f"{sleeper.get('expected_gap', 0):.1f} spins",
                                "Overdue Factor": f"{sleeper.get('overdue_factor', 0):.2f}x",
                                "Last Seen": sleeper.get("last_position", "Unknown")
                            })
                        
                        # Convert to DataFrame for display
                        sleeper_df = pd.DataFrame(sleeper_data)
                        st.dataframe(sleeper_df, use_container_width=True)
                        
                        # Show betting recommendations for sleepers
                        st.subheader("Sleeper Betting Strategy")
                        
                        if len(sleepers) >= 3:
                            # Calculate optimal coverage based on overdue factors
                            total_overdue = sum(s.get("overdue_factor", 0) for s in sleepers)
                            allocations = []
                            
                            for sleeper in sleepers:
                                number = sleeper.get("number", "")
                                overdue = sleeper.get("overdue_factor", 0)
                                weight = overdue / total_overdue if total_overdue > 0 else 0
                                allocations.append({
                                    "number": number,
                                    "weight": weight,
                                    "overdue": overdue
                                })
                            
                            # Sort by weight
                            allocations.sort(key=lambda x: x["weight"], reverse=True)
                            
                            # Show allocation recommendation
                            st.write("""
                            **Betting Strategy for Sleeper Numbers:**
                            
                            If you want to bet on sleeper numbers, consider allocating your bet amount
                            according to how overdue each number is. Here's a suggested allocation:
                            """)
                            
                            # Display as a progress bar
                            for alloc in allocations[:5]:  # Top 5
                                number = alloc["number"]
                                weight = alloc["weight"]
                                pct = weight * 100
                                
                                st.write(f"Number **{number}**: {pct:.1f}% of your sleeper number bet")
                                st.progress(weight)
                            
                            # Warning about gambler's fallacy
                            st.warning("""
                            **Note**: Be aware of the Gambler's Fallacy. Each spin is independent,
                            and previous results don't influence future spins on a fair wheel.
                            This strategy is best used only when you suspect physical wheel bias.
                            """)
                        else:
                            st.info("No significant sleeper numbers detected with current threshold.")
                    else:
                        st.info(f"No numbers have been absent for {min_absence} or more spins.")
                else:
                    st.warning("Unable to perform sleeper analysis. Please ensure you have sufficient spin data.")
                    
            # Wheel Bias Analysis
            with advanced_tabs[3]:
                st.subheader("🎡 Wheel Bias Heatmap")
                
                st.write("""
                This visualization shows the physical roulette wheel layout with colors indicating
                which numbers are appearing more frequently (hot) or less frequently (cold) than expected.
                
                A properly balanced wheel should show a mostly uniform distribution over time.
                Persistent patterns may indicate physical bias in the wheel.
                """)
                
                # Generate wheel heatmap
                heatmap_fig = st.session_state.advanced_betting.create_wheel_heatmap(
                    spins_df, current_roulette_type
                )
                
                # Display the heatmap
                st.plotly_chart(heatmap_fig, use_container_width=True, key="wheel_bias_heatmap")
                
                # Proximity analysis
                st.subheader("Physical Proximity Analysis")
                
                st.write("""
                This analysis examines if there are patterns in the physical distance between
                consecutive numbers on the wheel. In a truly random wheel, there should be
                no correlation between consecutive spins.
                """)
                
                # Get proximity analysis
                proximity_analysis = st.session_state.advanced_betting.proximity_analysis(
                    spins_df, current_roulette_type
                )
                
                if proximity_analysis and "proximity_patterns" in proximity_analysis:
                    patterns = proximity_analysis["proximity_patterns"]
                    if patterns:
                        # Show proximity metrics
                        st.subheader("Physical Wheel Distance Patterns")
                        
                        # Create table of patterns
                        pattern_data = []
                        for pattern in patterns:
                            pattern_data.append({
                                "Distance": pattern.get("distance", 0),
                                "Observed": pattern.get("frequency", 0),
                                "Expected": f"{pattern.get('expected', 0):.1f}",
                                "Deviation": f"{pattern.get('deviation', 0):.2f}",
                                "Significance": pattern.get("significance", "Low"),
                                "Suggests": pattern.get("suggests", "Unknown")
                            })
                        
                        # Convert to DataFrame for display
                        pattern_df = pd.DataFrame(pattern_data)
                        st.dataframe(pattern_df, use_container_width=True)
                        
                        # Show the most significant pattern
                        if patterns:
                            top_pattern = patterns[0]
                            distance = top_pattern.get("distance", 0)
                            suggests = top_pattern.get("suggests", "")
                            
                            st.write(f"### Most Significant Pattern: Distance {distance}")
                            st.write(f"This pattern {suggests}")
                            
                            # Show example pairs
                            examples = top_pattern.get("example_pairs", [])
                            if examples:
                                st.write("Example number pairs at this distance:")
                                for pair in examples:
                                    st.write(f"- {pair[0]} and {pair[1]}")
                    else:
                        st.info("No significant proximity patterns detected.")
                else:
                    st.warning("Unable to perform proximity analysis. Please ensure you have sufficient spin data.")
        else:
            st.warning("Need at least 20 spins for advanced betting analysis. Please add more spins in the Data Management tab.")
    
    # Progression Systems Tab
    with strategy_tab3:
        st.subheader("🔄 Betting Progression Systems")
        
        st.write("""
        Progression systems adjust your bet size based on previous results.
        While they can't overcome the house edge, they can help manage your bankroll
        and potentially maximize wins during hot streaks.
        """)
        
        # Check if we have spin data
        spins_df = clean_dataframe_for_analysis(st.session_state.roulette_data.get_session_data(st.session_state.current_session))
        
        if spins_df is not None and not spins_df.empty and len(spins_df) >= 20:
            # Risk tolerance selection
            risk_tolerance = st.select_slider(
                "Risk Tolerance",
                options=["low", "medium", "high"],
                value="medium",
                help="Higher risk tolerance means more aggressive betting progressions"
            )
            
            # Get progression system recommendations
            progression_rec = st.session_state.advanced_betting.get_progression_system_recommendation(
                spins_df, st.session_state.bankroll, risk_tolerance
            )
            
            if progression_rec and "progression_systems" in progression_rec:
                systems = progression_rec["progression_systems"]
                if systems:
                    # Show the top recommended system
                    top_system = systems[0]
                    st.success(f"### Top Recommendation: {top_system.get('name', '')}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("System Score", f"{top_system.get('score', 0):.1f}/100")
                    with col2:
                        st.metric("Risk Level", top_system.get('risk_level', 'Unknown'))
                    
                    # Description and implementation
                    st.subheader("How It Works")
                    st.write(top_system.get("description", ""))
                    
                    st.subheader("Implementation")
                    st.write(top_system.get("implementation", ""))
                    
                    st.subheader("Best For")
                    st.write(top_system.get("best_for", ""))
                    
                    # Show all recommended systems
                    st.subheader("All Recommended Systems")
                    
                    # Create table data
                    system_data = []
                    for system in systems:
                        system_data.append({
                            "System": system.get("name", ""),
                            "Score": f"{system.get('score', 0):.1f}/100",
                            "Risk Level": system.get("risk_level", ""),
                            "Bankroll Req.": f"{system.get('bankroll_requirement', 0)} units",
                            "Best For": system.get("best_for", "")
                        })
                    
                    # Convert to DataFrame
                    system_df = pd.DataFrame(system_data)
                    st.dataframe(system_df, use_container_width=True)
                    
                    # Session statistics
                    st.subheader("Current Session Statistics")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Win Rate", f"{progression_rec.get('win_rate', 0):.1f}%")
                    with col2:
                        st.metric("Max Win Streak", progression_rec.get("max_winning_streak", 0))
                    with col3:
                        st.metric("Max Loss Streak", progression_rec.get("max_losing_streak", 0))
                else:
                    st.info("No progression systems could be recommended based on your data.")
            else:
                st.warning("Unable to generate progression recommendations. Please ensure you have sufficient spin data.")
        else:
            st.warning("Need at least 20 spins for progression analysis. Please add more spins in the Data Management tab.")
    
    # Wheel Visualization Tab
    with strategy_tab4:
        st.subheader("🗺️ Wheel Visualization")
        
        st.write("""
        This section provides a visual representation of the roulette wheel and spin results,
        allowing you to see patterns that might not be apparent in numerical data.
        """)
        
        # Check if we have spin data
        spins_df = clean_dataframe_for_analysis(st.session_state.roulette_data.get_session_data(st.session_state.current_session))
        current_roulette_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
        
        if spins_df is not None and not spins_df.empty:
            # Create wheel heatmap visualization
            wheel_fig = st.session_state.advanced_betting.create_wheel_heatmap(
                spins_df, current_roulette_type
            )
            
            # Display the wheel visualization
            st.plotly_chart(wheel_fig, use_container_width=True, key="wheel_visualization")
            
            # Pattern cycle analysis
            st.subheader("Pattern Cycle Analysis")
            
            pattern_analysis = st.session_state.advanced_betting.analyze_pattern_cycles(spins_df)
            
            if pattern_analysis and "patterns" in pattern_analysis:
                patterns = pattern_analysis["patterns"]
                if patterns:
                    # Show pattern data
                    pattern_data = []
                    for pattern in patterns:
                        pattern_data.append({
                            "Type": pattern.get("type", "").replace("_", "/").title(),
                            "Pattern": pattern.get("pattern", ""),
                            "Count": pattern.get("count", 0),
                            "Expected": f"{pattern.get('expected', 0):.1f}",
                            "Deviation": f"{pattern.get('deviation', 0):.2f}",
                            "Significant": "Yes" if pattern.get("significant", False) else "No"
                        })
                    
                    # Convert to DataFrame
                    pattern_df = pd.DataFrame(pattern_data)
                    st.dataframe(pattern_df, use_container_width=True)
                    
                    # Show the most significant pattern
                    if patterns:
                        top_pattern = patterns[0]
                        
                        st.success(f"### Most Significant Pattern: {top_pattern.get('pattern', '')}")
                        st.write(f"Type: {top_pattern.get('type', '').replace('_', '/').title()}")
                        st.write(top_pattern.get('explanation', ''))
                else:
                    st.info("No significant pattern cycles detected in your data.")
            else:
                st.warning("Unable to perform pattern analysis. Please ensure you have sufficient spin data.")
        else:
            st.warning("Need spin data for wheel visualization. Please add spins in the Data Management tab.")
            
    # Bet Simulator Tab
    with strategy_tab5:
        st.subheader("💰 Bet Simulator")
        
        st.write("""
        This interactive simulator lets you place different types of bets and see how they would affect your bankroll.
        The agent will track your wins and losses and adjust its recommendations based on your betting history.
        """)
        
        # Initialize bet simulator state variables if they don't exist
        if 'bet_simulator_bankroll' not in st.session_state:
            st.session_state.bet_simulator_bankroll = st.session_state.bankroll
            
        if 'bet_history' not in st.session_state:
            st.session_state.bet_history = []
            
        # Display current bankroll and controls
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            current_simulator_bankroll = st.number_input(
                "Simulator Bankroll ($)", 
                min_value=5.0, 
                value=st.session_state.bet_simulator_bankroll,
                step=5.0
            )
            st.session_state.bet_simulator_bankroll = current_simulator_bankroll
            
        with col2:
            reset_btn = st.button("Reset Bankroll to $100")
            if reset_btn:
                st.session_state.bet_simulator_bankroll = 100.0
                st.session_state.bet_history = []
                st.rerun()
                
        with col3:
            if st.button("Get Agent Recommendations", help="Use agent to analyze bet history and provide recommendations"):
                # Only provide recommendations if we have betting history
                if len(st.session_state.bet_history) > 0:
                    # Process bet history to train the agent
                    for bet in st.session_state.bet_history:
                        # Update agent with bet results if not already recorded
                        if 'processed_by_agent' not in bet or not bet['processed_by_agent']:
                            st.session_state.agent.record_result(
                                bet['spin_result'], 
                                bet['bet_type'], 
                                bet['won'], 
                                bet['amount'] * bet['payout_multiplier'] if bet['won'] else -bet['amount']
                            )
                            bet['processed_by_agent'] = True
                    st.success("Agent updated with your betting history!")
                    st.rerun()
                else:
                    st.info("Place some bets first to get recommendations.")
                
        # Display spins data if available
        spins_df = st.session_state.roulette_data.get_session_data(st.session_state.current_session)
        current_roulette_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
        
        # Add quick input panel for spins
        import random
        from datetime import datetime
        
        spin_input_expander = st.expander("Quick Spin Input", expanded=False)
        with spin_input_expander:
            st.write("Add new spins directly from the Bet Simulator tab:")
            
            def on_spin_added(number):
                # Add the spin with current timestamp
                st.session_state.roulette_data.add_spin(
                    session_name=st.session_state.current_session,
                    number=number,
                    timestamp=datetime.now()
                )
                st.success(f"✅ Added spin: {number}")
                st.rerun()
            
            # Create simplified quick input panel
            tabs = st.tabs(["Number Grid", "Quick Numbers"])
            
            with tabs[0]:
                # Green (0 and 00)
                zero_row = st.columns([1, 1, 6] if current_roulette_type == "American" else [1, 7])
                with zero_row[0]:
                    if st.button("0", key="simulator_0", use_container_width=True, type="primary"):
                        on_spin_added("0")
                
                if current_roulette_type == "American":
                    with zero_row[1]:
                        if st.button("00", key="simulator_00", use_container_width=True, type="primary"):
                            on_spin_added("00")
                
                # Numbers 1-36 in standard layout (3 rows of 12 numbers)
                st.write("**Row 1 (1-12)**")
                cols = st.columns(12)
                for i in range(12):
                    number = i + 1
                    with cols[i]:
                        if st.button(str(number), key=f"simulator_{number}", use_container_width=True):
                            on_spin_added(str(number))
                
                st.write("**Row 2 (13-24)**")
                cols = st.columns(12)
                for i in range(12):
                    number = i + 13
                    with cols[i]:
                        if st.button(str(number), key=f"simulator_{number}", use_container_width=True):
                            on_spin_added(str(number))
                
                st.write("**Row 3 (25-36)**")
                cols = st.columns(12)
                for i in range(12):
                    number = i + 25
                    with cols[i]:
                        if st.button(str(number), key=f"simulator_{number}", use_container_width=True):
                            on_spin_added(str(number))
            
            with tabs[1]:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Red", key="simulator_red", use_container_width=True):
                        on_spin_added(str(random.choice([1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36])))
                    if st.button("Odd", key="simulator_odd", use_container_width=True):
                        on_spin_added(str(random.choice(range(1, 37, 2))))
                with col2:
                    if st.button("Black", key="simulator_black", use_container_width=True):
                        on_spin_added(str(random.choice([2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35])))
                    if st.button("Even", key="simulator_even", use_container_width=True):
                        on_spin_added(str(random.choice(range(2, 37, 2))))
        
        if spins_df is not None and not spins_df.empty:
            # Get the most recent spin for simulation
            latest_spin = spins_df.iloc[0]['number'] if not spins_df.empty else None
            
            # Create betting interface
            st.subheader("Place Your Bet")
            
            # Create columns for different bet types
            bet_col1, bet_col2 = st.columns(2)
            
            with bet_col1:
                bet_type = st.radio(
                    "Bet Type",
                    ["Straight (Single Number)", 
                     "Red/Black", 
                     "Even/Odd", 
                     "1-18/19-36",
                     "Dozen (1-12, 13-24, 25-36)",
                     "Column",
                     "Split (Two Numbers)",
                     "Street (Three Numbers)",
                     "Corner (Four Numbers)",
                     "Six Line",
                     "Zero/Double Zero"]
                )
                
                # Set bet options based on selected type
                if bet_type == "Straight (Single Number)":
                    # For single number bets
                    specific_bet = st.number_input(
                        "Number to Bet On", 
                        min_value=0, 
                        max_value=36, 
                        value=0
                    )
                    payout_multiplier = 35
                    
                elif bet_type == "Red/Black":
                    # For red/black bets
                    specific_bet = st.radio(
                        "Choose Color",
                        ["Red", "Black"]
                    )
                    payout_multiplier = 1
                    
                elif bet_type == "Even/Odd":
                    # For even/odd bets
                    specific_bet = st.radio(
                        "Choose Parity",
                        ["Even", "Odd"]
                    )
                    payout_multiplier = 1
                    
                elif bet_type == "1-18/19-36":
                    # For high/low bets
                    specific_bet = st.radio(
                        "Choose Range",
                        ["1-18 (Low)", "19-36 (High)"]
                    )
                    payout_multiplier = 1
                    
                elif bet_type == "Dozen (1-12, 13-24, 25-36)":
                    # For dozen bets
                    specific_bet = st.radio(
                        "Choose Dozen",
                        ["1st Dozen (1-12)", "2nd Dozen (13-24)", "3rd Dozen (25-36)"]
                    )
                    payout_multiplier = 2
                    
                elif bet_type == "Column":
                    # For column bets
                    specific_bet = st.radio(
                        "Choose Column",
                        ["1st Column (1,4,7,...,34)", "2nd Column (2,5,8,...,35)", "3rd Column (3,6,9,...,36)"]
                    )
                    payout_multiplier = 2
                    
                elif bet_type == "Split (Two Numbers)":
                    # For split bets
                    st.write("Choose two adjacent numbers")
                    split_num1 = st.number_input("First Number", min_value=1, max_value=36, value=1)
                    split_num2 = st.number_input("Second Number", min_value=1, max_value=36, value=2)
                    specific_bet = f"{split_num1}/{split_num2}"
                    payout_multiplier = 17
                    
                elif bet_type == "Street (Three Numbers)":
                    # For street bets (3 numbers in a row)
                    first_num = st.number_input("First number in row", min_value=1, max_value=34, value=1, step=3) 
                    street_numbers = [first_num, first_num+1, first_num+2]
                    specific_bet = f"{first_num},{first_num+1},{first_num+2}"
                    payout_multiplier = 11
                    
                elif bet_type == "Corner (Four Numbers)":
                    # For corner bets (4 numbers in a square)
                    corner_num = st.number_input("Lower-left corner number", min_value=1, max_value=32, value=1)
                    if corner_num % 3 == 0:  # Can't be rightmost column
                        st.error("Cannot select rightmost column number. Please choose another number.")
                        corner_num = corner_num - 1
                    corner_numbers = [corner_num, corner_num+1, corner_num+3, corner_num+4]
                    specific_bet = f"{corner_num},{corner_num+1},{corner_num+3},{corner_num+4}"
                    payout_multiplier = 8
                    
                elif bet_type == "Six Line":
                    # For six line bets (two adjacent rows)
                    first_num = st.number_input("First number in first row", min_value=1, max_value=31, value=1, step=3)
                    six_line_numbers = [first_num, first_num+1, first_num+2, first_num+3, first_num+4, first_num+5]
                    specific_bet = f"{first_num}-{first_num+5}"
                    payout_multiplier = 5
                    
                elif bet_type == "Zero/Double Zero":
                    # For zero bets
                    if current_roulette_type == "American":
                        specific_bet = st.radio(
                            "Choose Zero Type",
                            ["0", "00"]
                        )
                    else:
                        specific_bet = "0"
                        st.info("European roulette only has a single zero (0).")
                    payout_multiplier = 35
                
            with bet_col2:
                # Bet amount
                bet_amount = st.number_input(
                    "Bet Amount ($)", 
                    min_value=0.10, 
                    max_value=float(st.session_state.bet_simulator_bankroll), 
                    value=min(5.0, float(st.session_state.bet_simulator_bankroll)),
                    step=0.10
                )
                
                # Calculate potential win
                potential_win = bet_amount * payout_multiplier
                
                # Show payout information
                st.info(f"Payout: {payout_multiplier}:1")
                st.success(f"Potential Win: ${potential_win:.2f}")
                
                # Show current spin
                st.subheader("Current Spin")
                if latest_spin is not None:
                    # Display the number with a colored background
                    num = latest_spin
                    try:
                        # Format 0 and 00 properly
                        if num == "0" or num == "00":
                            bg_color = "green"
                            text_color = "white"
                        # Format normal numbers
                        elif int(num) in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]:
                            bg_color = "red"
                            text_color = "white"
                        else:
                            bg_color = "black"
                            text_color = "white"
                        
                        st.markdown(
                            f'<div style="background-color:{bg_color}; color:{text_color}; padding:10px; '
                            f'border-radius:50%; width:60px; height:60px; text-align:center; line-height:40px; '
                            f'font-size:24px; display:flex; align-items:center; justify-content:center;">{num}</div>',
                            unsafe_allow_html=True
                        )
                    except ValueError:
                        st.write(f"Last Spin: {num}")
                else:
                    st.write("No spin data available")
                
                # Place bet button
                if st.button("Place Bet"):
                    # Check if we have enough in bankroll
                    if bet_amount <= st.session_state.bet_simulator_bankroll and latest_spin is not None:
                        # Determine if bet won
                        won = False
                        
                        # Check different bet types
                        if bet_type == "Straight (Single Number)":
                            won = str(specific_bet) == latest_spin
                            
                        elif bet_type == "Red/Black":
                            red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
                            try:
                                num = int(latest_spin)
                                if specific_bet == "Red":
                                    won = num in red_numbers
                                else:  # Black
                                    won = num not in red_numbers and num != 0 and num != 00
                            except ValueError:
                                # Handle 00
                                won = False  # Neither red nor black
                            
                        elif bet_type == "Even/Odd":
                            try:
                                num = int(latest_spin)
                                if specific_bet == "Even":
                                    won = num != 0 and num % 2 == 0
                                else:  # Odd
                                    won = num % 2 == 1
                            except ValueError:
                                # Handle 00
                                won = False  # Neither even nor odd
                            
                        elif bet_type == "1-18/19-36":
                            try:
                                num = int(latest_spin)
                                if specific_bet == "1-18 (Low)":
                                    won = 1 <= num <= 18
                                else:  # 19-36 (High)
                                    won = 19 <= num <= 36
                            except ValueError:
                                # Handle 00
                                won = False
                            
                        elif bet_type == "Dozen (1-12, 13-24, 25-36)":
                            try:
                                num = int(latest_spin)
                                if specific_bet == "1st Dozen (1-12)":
                                    won = 1 <= num <= 12
                                elif specific_bet == "2nd Dozen (13-24)":
                                    won = 13 <= num <= 24
                                else:  # 3rd Dozen
                                    won = 25 <= num <= 36
                            except ValueError:
                                # Handle 00
                                won = False
                            
                        elif bet_type == "Column":
                            try:
                                num = int(latest_spin)
                                if specific_bet == "1st Column (1,4,7,...,34)":
                                    won = num % 3 == 1
                                elif specific_bet == "2nd Column (2,5,8,...,35)":
                                    won = num % 3 == 2
                                else:  # 3rd Column
                                    won = num % 3 == 0 and num != 0
                            except ValueError:
                                # Handle 00
                                won = False
                            
                        elif bet_type == "Split (Two Numbers)":
                            try:
                                split_numbers = [int(n) for n in specific_bet.split('/')]
                                won = int(latest_spin) in split_numbers
                            except ValueError:
                                # Handle 00 or conversion error
                                won = False
                            
                        elif bet_type == "Street (Three Numbers)":
                            try:
                                street_numbers = [int(n) for n in specific_bet.split(',')]
                                won = int(latest_spin) in street_numbers
                            except ValueError:
                                # Handle 00 or conversion error
                                won = False
                            
                        elif bet_type == "Corner (Four Numbers)":
                            try:
                                corner_numbers = [int(n) for n in specific_bet.split(',')]
                                won = int(latest_spin) in corner_numbers
                            except ValueError:
                                # Handle 00 or conversion error
                                won = False
                            
                        elif bet_type == "Six Line":
                            try:
                                first, last = map(int, specific_bet.split('-'))
                                six_line_numbers = list(range(first, last + 1))
                                won = int(latest_spin) in six_line_numbers
                            except ValueError:
                                # Handle 00 or conversion error
                                won = False
                            
                        elif bet_type == "Zero/Double Zero":
                            won = specific_bet == latest_spin
                        
                        # Calculate winnings or losses
                        if won:
                            winnings = bet_amount * payout_multiplier
                            st.session_state.bet_simulator_bankroll += winnings
                            st.success(f"🎉 You won ${winnings:.2f}!")
                            
                            # Record win for agent learning
                            st.session_state.agent.record_result(
                                latest_spin, bet_type, True, winnings
                            )
                        else:
                            st.session_state.bet_simulator_bankroll -= bet_amount
                            st.error(f"❌ You lost ${bet_amount:.2f}")
                            
                            # Record loss for agent learning
                            st.session_state.agent.record_result(
                                latest_spin, bet_type, False, -bet_amount
                            )
                        
                        # Record in bet history
                        st.session_state.bet_history.append({
                            'bet_type': bet_type,
                            'specific_bet': specific_bet,
                            'amount': bet_amount,
                            'spin_result': latest_spin,
                            'won': won,
                            'payout_multiplier': payout_multiplier,
                            'bankroll_after': st.session_state.bet_simulator_bankroll
                        })
                        
                        # Update main bankroll to match simulator if requested
                        if st.session_state.bet_simulator_bankroll != st.session_state.bankroll:
                            st.session_state.bankroll = st.session_state.bet_simulator_bankroll
                            
                        # Rerun to update the UI
                        st.rerun()
                    else:
                        if latest_spin is None:
                            st.error("No spin data available. Please add spins in the Data Management tab.")
                        else:
                            st.error("Insufficient funds for this bet.")
            
            # Display bet history
            if len(st.session_state.bet_history) > 0:
                st.subheader("Betting History")
                
                # Create DataFrame from bet history
                history_df = pd.DataFrame(st.session_state.bet_history)
                
                # Calculate win rate
                win_rate = history_df['won'].mean() * 100
                
                # Calculate profit/loss
                initial_bankroll = 100.0  # Assuming starting bankroll was 100
                total_profit = st.session_state.bet_simulator_bankroll - initial_bankroll
                
                # Show metrics
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                with metric_col1:
                    st.metric("Total Bets", len(st.session_state.bet_history))
                with metric_col2:
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                with metric_col3:
                    st.metric("Profit/Loss", f"${total_profit:.2f}", delta=f"{total_profit:.2f}")
                
                # Show recent bets
                st.write("Recent Bets")
                recent_history = history_df.tail(5).sort_index(ascending=False).reset_index(drop=True)
                
                # Format the data for display
                display_history = recent_history[['bet_type', 'specific_bet', 'amount', 'spin_result', 'won', 'bankroll_after']].copy()
                display_history['won'] = display_history['won'].apply(lambda x: "✅ Won" if x else "❌ Lost")
                display_history['amount'] = display_history['amount'].apply(lambda x: f"${x:.2f}")
                display_history['bankroll_after'] = display_history['bankroll_after'].apply(lambda x: f"${x:.2f}")
                
                # Rename columns for better display
                display_history.columns = ['Bet Type', 'Selection', 'Amount', 'Result', 'Outcome', 'Bankroll After']
                
                # Display as a table
                st.dataframe(display_history, use_container_width=True)
                
                # Agent Recommendation Based on Betting History
                st.subheader("Agent Recommendation")
                
                # Get agent recommendation
                strategy_name = st.session_state.agent.get_recommendation(st.session_state.bet_simulator_bankroll)
                recommended_bet = st.session_state.agent.get_bet_size_recommendation(st.session_state.bet_simulator_bankroll)
                
                # Agent assessment
                losing_streak = st.session_state.agent.recent_losing_streak()
                
                recommendation_text = f"""
                Based on your betting history and current bankroll (${st.session_state.bet_simulator_bankroll:.2f}), 
                the agent recommends the following strategy:
                
                **Strategy:** {strategy_name}
                **Suggested Bet Size:** ${recommended_bet:.2f}
                """
                
                if losing_streak >= 3:
                    recommendation_text += f"\n\n⚠️ **Warning:** You're currently on a {losing_streak} bet losing streak. Consider lowering your bet size or taking a break."
                
                st.info(recommendation_text)
                
                # Advanced recommendations
                detailed_rec_expander = st.expander("Detailed Betting Recommendations", expanded=False)
                with detailed_rec_expander:
                    if spins_df is not None and not spins_df.empty and len(spins_df) >= 5:
                        # Get recommendations using the agent
                        bet_recommendations = st.session_state.agent.get_specific_bet_recommendations(
                            spins_df, 
                            current_roulette_type, 
                            st.session_state.bet_simulator_bankroll,
                            fast_mode=True
                        )
                        
                        if bet_recommendations:
                            # Display agent accuracy
                            accuracy = st.session_state.agent.get_accuracy() * 100
                            st.metric(
                                "Agent Prediction Accuracy",
                                f"{accuracy:.1f}%",
                                help="Higher accuracy means more reliable recommendations"
                            )
                            
                            # Display top number recommendations
                            if "hot_numbers" in bet_recommendations and bet_recommendations["hot_numbers"]:
                                st.write("**Top Number Recommendations:**")
                                hot_cols = st.columns(min(5, len(bet_recommendations["hot_numbers"])))
                                for i, hot_num in enumerate(bet_recommendations["hot_numbers"][:5]):
                                    with hot_cols[i]:
                                        num = hot_num["number"]
                                        confidence = hot_num["confidence"] * 100
                                        st.metric(
                                            f"Number {num}",
                                            f"{confidence:.1f}%",
                                            help=f"Expected to hit with {confidence:.1f}% confidence"
                                        )
                            
                            # Display pattern recommendations
                            if "pattern_recommendations" in bet_recommendations:
                                pattern_recs = bet_recommendations["pattern_recommendations"]
                                if pattern_recs:
                                    st.write("**Pattern Recommendations:**")
                                    
                                    # Create table for pattern recommendations
                                    pattern_data = []
                                    for pattern, data in pattern_recs.items():
                                        if data["confidence"] > 0.1:
                                            pattern_display = pattern.replace("_", " ").title()
                                            pattern_data.append({
                                                "Pattern": pattern_display,
                                                "Confidence": f"{data['confidence'] * 100:.1f}%",
                                                "Expected Value": f"{data['expected_value']:.2f}",
                                                "Recommendation": "Bet" if data['confidence'] > 0.5 else "Avoid" if data['confidence'] < 0.3 else "Neutral"
                                            })
                                    
                                    if pattern_data:
                                        pattern_df = pd.DataFrame(pattern_data)
                                        st.dataframe(pattern_df, use_container_width=True)
                                        
                                        # Show best pattern
                                        best_pattern = max(pattern_recs.items(), key=lambda x: x[1]["confidence"])
                                        if best_pattern[1]["confidence"] > 0.4:
                                            best_pattern_name = best_pattern[0].replace("_", " ").title()
                                            st.success(f"**Best betting pattern:** {best_pattern_name} with {best_pattern[1]['confidence'] * 100:.1f}% confidence")
                                    else:
                                        st.info("No significant patterns detected")
                                else:
                                    st.info("No pattern recommendations available yet")
                        else:
                            st.warning("Unable to generate detailed recommendations with the current data")
                    else:
                        st.warning("Need more spin data for detailed recommendations (minimum 5 spins)")
                
        else:
            st.warning("Need spin data for bet simulation. Please add spins in the Data Management tab.")
