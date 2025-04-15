import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import time

from utils.roulette_data import RouletteData
from utils.analysis import RouletteAnalyzer
from utils.betting_strategies import BettingStrategist
from utils.visualization import RouletteVisualizer
from utils.agent import RLAgent
from utils.performance_tracker import StrategyPerformanceTracker
from utils.strategies import StrategyEngine
from utils.strategy_selector import choose_strategy, get_bet_size_recommendation, get_strategy_description
from utils.file_import import create_file_importer
from utils.quick_input import add_floating_quick_input
from utils.live_casino_input import create_live_casino_panel
from utils.wheel_bias import WheelBiasDetector
from utils.web_scraper import create_web_scraper_ui

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
    
    # Display recommended bet size based on bankroll
    rec_bet_size = get_bet_size_recommendation(st.session_state.bankroll)
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

# Main content area with tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Spin Tracker", "Analysis", "Betting Suggestions", "Advanced Strategy Agent", "Statistics"])

# Add floating quick input panel at the bottom of the screen
current_roulette_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
add_floating_quick_input(st.session_state.current_session, st.session_state.roulette_data, current_roulette_type)

# Tab 1: Spin Tracker
with tab1:
    st.header(f"Spin Tracker - {st.session_state.current_session}")
    
    # Get current roulette type for this session
    current_roulette_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
    
    # Display current roulette type
    st.info(f"Current Roulette Type: {current_roulette_type}")
    
    # Input section for new spins with tabs for different input methods
    st.subheader("Record New Spin")
    
    data_input_tabs = st.tabs(["Manual Entry", "Live Casino Input", "Import from File", "Web Scraper"])
    
    with data_input_tabs[0]:
        # Traditional manual input
        col1, col2 = st.columns(2)
        
        with col1:
            # Input for spin number
            if current_roulette_type == "European":
                spin_number = st.number_input("Spin Result (0-36):", min_value=0, max_value=36, step=1)
            else:  # American
                spin_number = st.number_input("Spin Result (00, 0-36):", min_value=-1, max_value=36, step=1, 
                                            help="Enter -1 for '00' (American roulette)")
        
        with col2:
            # Add timestamp
            timestamp = st.date_input("Spin Date:", value=datetime.now().date())
            time_input = st.time_input("Spin Time:", value=datetime.now().time())
            
        # Combine date and time
        spin_timestamp = datetime.combine(timestamp, time_input)
        
        # Button to add the spin
        if st.button("Add Spin Result", key="manual_add_btn"):
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
    
    with data_input_tabs[1]:
        # Live Casino Input
        create_live_casino_panel(st.session_state.current_session, st.session_state.roulette_data, current_roulette_type)
    
    with data_input_tabs[2]:
        # Import from file
        imported_data = create_file_importer()
        
        if imported_data is not None:
            with st.spinner("Importing data..."):
                # Add each spin to the session
                for _, row in imported_data.iterrows():
                    number = row['number']
                    timestamp = row['timestamp'] if 'timestamp' in row else datetime.now()
                    
                    st.session_state.roulette_data.add_spin(
                        session_name=st.session_state.current_session,
                        number=str(number),
                        timestamp=timestamp
                    )
                
                st.success(f"Successfully imported {len(imported_data)} spins!")
                st.rerun()  # Refresh the page to show updated data
    
    with data_input_tabs[3]:
        # Web scraper for roulette data
        st.write("""
        Use the web scraper to import roulette spin data from websites.
        Enter the URL of a page containing roulette spin results.
        """)
        
        # Create the web scraper UI
        scraped_data = create_web_scraper_ui()
        
        if scraped_data is not None:
            with st.spinner("Importing scraped data..."):
                # Add each spin to the session
                for _, row in scraped_data.iterrows():
                    number = row['number']
                    timestamp = row['timestamp'] if 'timestamp' in row else datetime.now()
                    
                    st.session_state.roulette_data.add_spin(
                        session_name=st.session_state.current_session,
                        number=str(number),
                        timestamp=timestamp
                    )
                
                st.success(f"Successfully imported {len(scraped_data)} spins from web!")
                st.rerun()  # Refresh the page to show updated data
    
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
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No spins recorded in this session yet. Add some spins to get started!")

# Tab 2: Analysis
with tab2:
    st.header(f"Analysis - {st.session_state.current_session}")
    
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
            st.plotly_chart(fig, use_container_width=True)
            
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
            st.plotly_chart(fig, use_container_width=True)
            
            # Display even/odd trend
            even_odd_trend = st.session_state.analyzer.get_even_odd_trend(spins_df)
            st.subheader("Even/Odd Trend Analysis")
            st.write(even_odd_trend)
        
        elif analysis_option == "Red/Black Distribution":
            st.subheader("Red/Black Distribution Analysis")
            fig = st.session_state.visualizer.plot_red_black_distribution(spins_df)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display red/black trend
            red_black_trend = st.session_state.analyzer.get_red_black_trend(spins_df)
            st.subheader("Red/Black Trend Analysis")
            st.write(red_black_trend)
        
        elif analysis_option == "Dozens Distribution":
            st.subheader("Dozens Distribution Analysis")
            fig = st.session_state.visualizer.plot_dozens_distribution(spins_df)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display dozens trend
            dozens_trend = st.session_state.analyzer.get_dozens_trend(spins_df)
            st.subheader("Dozens Trend Analysis")
            st.write(dozens_trend)
        
        elif analysis_option == "Columns Distribution":
            st.subheader("Columns Distribution Analysis")
            fig = st.session_state.visualizer.plot_columns_distribution(spins_df)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display columns trend
            columns_trend = st.session_state.analyzer.get_columns_trend(spins_df)
            st.subheader("Columns Trend Analysis")
            st.write(columns_trend)
        
        elif analysis_option == "High/Low Distribution":
            st.subheader("High/Low Distribution Analysis")
            fig = st.session_state.visualizer.plot_high_low_distribution(spins_df)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display high/low trend
            high_low_trend = st.session_state.analyzer.get_high_low_trend(spins_df)
            st.subheader("High/Low Trend Analysis")
            st.write(high_low_trend)
            
        elif analysis_option == "Wheel Bias Detection":
            st.subheader("Wheel Bias Detection Analysis")
            
            # Get current roulette type
            current_roulette_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
            
            # Display information about the minimum spins required
            st.info("**Wheel Bias Detection** requires at least 300 spins for reliable results. More spins provide more accurate analysis.")
            
            # Show current spin count
            st.write(f"Current number of spins: **{len(spins_df)}**")
            
            if len(spins_df) < 50:
                st.warning("You need more spins for any meaningful bias detection. Please add at least 50 spins to see preliminary results.")
            else:
                # Perform the wheel bias analysis
                bias_results = st.session_state.wheel_bias_detector.analyze_wheel_bias(
                    spins_df, 
                    current_roulette_type,
                    min_spins=50  # Lowered for demo, but will show confidence appropriately
                )
                
                # Display the results
                st.write("### Bias Detection Results")
                
                # Status and confidence
                status_color = "red" if bias_results["status"] == "significant_bias_detected" else \
                              "orange" if bias_results["status"] == "potential_bias_detected" else "green"
                
                st.write(f"**Status:** <span style='color:{status_color}'>{bias_results['status'].replace('_', ' ').title()}</span>", unsafe_allow_html=True)
                st.write(f"**Overall Confidence:** {bias_results['bias_confidence']:.2%}")
                st.write(f"**Message:** {bias_results['message']}")
                
                # Chi-square test results
                with st.expander("Chi-Square Test Results"):
                    chi2_results = bias_results["chi_square_test"]
                    st.write(f"Chi-square statistic: {chi2_results['chi2_statistic']:.2f}")
                    st.write(f"P-value: {chi2_results['p_value']:.6f}")
                    st.write(f"Is wheel biased (statistical): {'Yes' if chi2_results['is_biased'] else 'No'}")
                    
                    st.write("### Top Number Deviations")
                    for num, dev in chi2_results['top_deviations']:
                        deviation_color = "red" if abs(dev) > 100 else "orange" if abs(dev) > 50 else "black"
                        st.write(f"Number {num}: <span style='color:{deviation_color}'>{dev:.1f}%</span> from expected", unsafe_allow_html=True)
                
                # Sector bias results
                with st.expander("Sector Bias Analysis"):
                    sector_bias = bias_results["sector_bias"]
                    st.write(f"Quadrant analysis p-value: {sector_bias['p_value']:.6f}")
                    st.write(f"Is sector biased: {'Yes' if sector_bias['is_biased'] else 'No'}")
                    
                    st.write("### Quadrant Deviations")
                    for quadrant, data in sector_bias['quadrant_deviations'].items():
                        st.write(f"{quadrant}: {data['deviation_pct']:.1f}% from expected")
                    
                    # Show diamond analysis for European wheels
                    if sector_bias["diamond_analysis"]:
                        st.write("### Diamond Sector Analysis")
                        diamond = sector_bias["diamond_analysis"]
                        st.write(f"Diamond sector p-value: {diamond['p_value']:.6f}")
                        st.write(f"Is diamond sector biased: {'Yes' if diamond['is_biased'] else 'No'}")
                        
                        for sector, data in diamond['sector_deviations'].items():
                            st.write(f"{sector}: {data['deviation_pct']:.1f}% from expected")
                
                # Frequency deviation details
                with st.expander("Number Frequency Analysis"):
                    freq = bias_results["frequency_deviation"]
                    st.write(f"Significant deviations: {freq['significant_percentage']:.1f}% of numbers")
                    st.write(f"Is frequency biased: {'Yes' if freq['is_biased'] else 'No'}")
                    
                    st.write("### Top Individual Number Deviations")
                    for num, data in freq['top_deviations'][:10]:
                        sig_text = " (Statistically Significant)" if data['is_significant'] else ""
                        st.write(f"Number {num}: {data['deviation_pct']:.1f}% from expected, Z-score: {data['z_score']:.2f}{sig_text}")
                
                # Neighbor pattern analysis
                with st.expander("Neighbor Pattern Analysis"):
                    neighbors = bias_results["neighbor_patterns"]
                    st.write(f"Has neighbor patterns: {'Yes' if neighbors['has_pattern'] else 'No'}")
                    
                    if neighbors['has_pattern']:
                        st.write("### Significant Distance Patterns")
                        for distance in neighbors['significant_distances']:
                            data = neighbors['distance_analysis'][distance]
                            st.write(f"Distance {distance}: {data['deviation_pct']:.1f}% from expected, p-value: {data['p_value']:.6f}")
                    else:
                        st.write("No significant neighbor patterns detected.")
                
                # Betting recommendations based on detected bias
                if bias_results["bias_confidence"] > 0.1:  # Show recommendations if there's at least some confidence
                    st.write("### Betting Recommendations Based on Wheel Bias")
                    
                    recommendations = bias_results["recommendations"]
                    
                    # Display single number recommendations
                    if recommendations["single_numbers"]:
                        st.write("#### Recommended Single Numbers:")
                        for num_data in recommendations["single_numbers"]:
                            st.write(f"Number {num_data['number']}: {num_data['deviation_pct']:.1f}% deviation, {num_data['confidence']:.2%} confidence")
                    
                    # Display sector recommendations
                    if recommendations["sectors"]:
                        st.write("#### Recommended Sectors:")
                        for sector_data in recommendations["sectors"]:
                            if "numbers" in sector_data:
                                st.write(f"{sector_data['sector']}: {sector_data['deviation_pct']:.1f}% deviation, {sector_data['confidence']:.2%} confidence")
                                st.write(f"   Numbers: {', '.join(map(str, sector_data['numbers']))}")
                            else:
                                st.write(f"{sector_data['sector']}: {sector_data['deviation_pct']:.1f}% deviation, {sector_data['confidence']:.2%} confidence")
                    
                    # Display pattern recommendations
                    if recommendations["patterns"]:
                        st.write("#### Recommended Pattern Strategies:")
                        for pattern_data in recommendations["patterns"]:
                            st.write(f"{pattern_data['description']}: {pattern_data['deviation_pct']:.1f}% deviation, {pattern_data['confidence']:.2%} confidence")
                    
                    # Display overall strategy recommendation
                    st.write("#### Overall Strategy Recommendation:")
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

# Tab 3: Betting Suggestions
with tab3:
    st.header(f"Betting Suggestions - {st.session_state.current_session}")
    
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

# Tab 4: Advanced Strategy Agent
with tab4:
    st.header(f"Advanced Strategy Agent - {st.session_state.current_session}")
    
    # Add a sample data generator for testing the recommendation system
    with st.expander("Test Data Generator (For Development)"):
        st.write("""
        This section allows you to generate sample spin data to test the recommendation system.
        You can quickly add different patterns of numbers to see how the system responds.
        """)
        
        test_data_type = st.selectbox(
            "Select Test Data Pattern",
            ["Random Data", "Red Bias", "Black Bias", "Even Bias", "Odd Bias", 
             "First Dozen Bias", "Single Number Bias", "Alternating Colors", "Consecutive Numbers"]
        )
        
        sample_size = st.slider("Number of Spins to Generate", 10, 200, 50)
        
        if st.button("Generate Test Data"):
            # Get current roulette type
            current_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
            
            # Clear existing data
            st.session_state.roulette_data.clear_spin_history(st.session_state.current_session)
            
            # Define roulette wheel properties
            red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
            black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
            all_numbers = list(range(1, 37))
            if current_type == "American":
                all_numbers.extend([0, 0])  # 0 and 00
            else:
                all_numbers.append(0)  # Just 0 for European
            
            # Generate spins based on selected pattern
            import random
            import datetime
            
            test_spins = []
            timestamp = datetime.datetime.now() - datetime.timedelta(minutes=sample_size)
            
            for i in range(sample_size):
                # Increment timestamp for each spin
                timestamp += datetime.timedelta(minutes=1)
                
                # Select number based on pattern
                if test_data_type == "Random Data":
                    number = random.choice(all_numbers)
                elif test_data_type == "Red Bias":
                    # 70% chance of red, 30% chance of others
                    if random.random() < 0.7:
                        number = random.choice(red_numbers)
                    else:
                        number = random.choice([n for n in all_numbers if n not in red_numbers])
                elif test_data_type == "Black Bias":
                    # 70% chance of black, 30% chance of others
                    if random.random() < 0.7:
                        number = random.choice(black_numbers)
                    else:
                        number = random.choice([n for n in all_numbers if n not in black_numbers])
                elif test_data_type == "Even Bias":
                    # 70% chance of even, 30% chance of odd or zero
                    if random.random() < 0.7:
                        number = random.choice([n for n in all_numbers if n > 0 and n % 2 == 0])
                    else:
                        number = random.choice([n for n in all_numbers if n == 0 or n % 2 == 1])
                elif test_data_type == "Odd Bias":
                    # 70% chance of odd, 30% chance of even or zero
                    if random.random() < 0.7:
                        number = random.choice([n for n in all_numbers if n > 0 and n % 2 == 1])
                    else:
                        number = random.choice([n for n in all_numbers if n == 0 or n % 2 == 0])
                elif test_data_type == "First Dozen Bias":
                    # 70% chance of 1-12, 30% chance of others
                    if random.random() < 0.7:
                        number = random.choice(range(1, 13))
                    else:
                        number = random.choice([n for n in all_numbers if n == 0 or n > 12])
                elif test_data_type == "Single Number Bias":
                    # 30% chance of number 17, 70% chance of others
                    if random.random() < 0.3:
                        number = 17
                    else:
                        number = random.choice([n for n in all_numbers if n != 17])
                elif test_data_type == "Alternating Colors":
                    # Alternate between red and black
                    if i % 2 == 0:
                        number = random.choice(red_numbers)
                    else:
                        number = random.choice(black_numbers)
                elif test_data_type == "Consecutive Numbers":
                    # Series of consecutive numbers that repeats
                    number = (i % 36) + 1
                else:
                    number = random.choice(all_numbers)
                
                # Convert to string (0 and 00 handling)
                if number == 0 and current_type == "American" and random.random() < 0.5:
                    number_str = "00"
                else:
                    number_str = str(number)
                
                # Add spin to test data
                st.session_state.roulette_data.add_spin(
                    st.session_state.current_session, 
                    number_str,
                    timestamp
                )
            
            st.success(f"Generated {sample_size} spins with {test_data_type} pattern for testing!")
    
    # Get the latest data for current session (force refresh)
    spins_df = st.session_state.roulette_data.get_session_data(st.session_state.current_session)
    current_roulette_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
    
    if spins_df is not None and not spins_df.empty:
        st.write("""
        The Advanced Strategy Agent uses reinforcement learning to analyze your spin data 
        and recommend optimal betting strategies based on your bankroll and the patterns detected.
        """)
        
        # Display current bankroll and agent accuracy
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Bankroll", f"${st.session_state.bankroll:.2f}")
        with col2:
            st.metric("Agent Accuracy", f"{st.session_state.agent.get_accuracy() * 100:.1f}%")
        with col3:
            st.metric("Recommended Strategy", st.session_state.agent.get_recommendation(st.session_state.bankroll))
        
        # Agent recommendation section
        st.subheader("Agent Strategy Recommendation")
        
        # Get agent recommendation
        strategy_name = st.session_state.agent.get_recommendation(st.session_state.bankroll)
        recommended_bet = st.session_state.agent.get_bet_size_recommendation(st.session_state.bankroll)
        
        # Display the recommendation
        st.info(f"Based on your current bankroll (${st.session_state.bankroll:.2f}) and historical data, the agent recommends:")
        st.markdown(f"**Strategy:** {strategy_name}")
        st.markdown(f"**Bet Size:** ${recommended_bet:.2f}")
        
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
                    time.sleep(0.1)  # Update every 100ms
                    # Break early if we're past 7.5 seconds to avoid hitting the limit
                    if time.time() - start_time > 7.5:
                        break
            
            # Pass the fast_mode parameter from session state to the analysis
            specific_recommendations = st.session_state.agent.get_specific_bet_recommendations(
                spins_df, 
                current_roulette_type, 
                st.session_state.bankroll,
                st.session_state.fast_mode
            )
            
            # Complete the progress bar
            progress_bar.progress(1.0, text="Analysis complete!")
            time.sleep(0.5)  # Give a moment to see the completed progress
            progress_bar.empty()  # Remove the progress bar
        
        # Add smooth loading animation for recommendation results
        with st.spinner("Preparing recommendation display..."):
            # Create a container for the animated results
            results_container = st.container()
            
            # Display recommendation confidence explanation with animation
            with results_container:
                # Add a small delay to create smooth transition effect
                time.sleep(0.3)
                st.info(specific_recommendations["confidence_explanation"])
                
                # Display a clear summary of all recommendations at the top with animation
                st.subheader("💰 Quick Recommendation Summary")
                
                # Create placeholder for animated content
                summary_placeholder = st.empty()
                
                # Create a container for animated content
                with summary_placeholder.container():
                    # Create summary card with all recommendations (will be displayed with animation)
                    summary_cols = st.columns(2)
                    
                    # Add small delay for smooth appearance
                    time.sleep(0.2)
                    
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
                            time.sleep(0.1)  # Subtle delay for animation
                            numbers_str = ", ".join([n["number"] for n in specific_recommendations["single_numbers"][:2]])
                            st.markdown(f"**Numbers:** {numbers_str}")
                        
                        # Add split bets
                        if specific_recommendations["split_bets"]:
                            time.sleep(0.1)  # Subtle delay for animation
                            splits_str = ", ".join([s["numbers"] for s in specific_recommendations["split_bets"][:2]])
                            st.markdown(f"**Split Bets:** {splits_str}")
                        
                        # Add corner bets
                        if "corner_bets" in specific_recommendations and specific_recommendations["corner_bets"]:
                            time.sleep(0.1)  # Subtle delay for animation
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
                                time.sleep(0.1)  # Subtle delay for animation
                                # Show up to 2 streets, prioritizing those with higher scores
                                streets_str = ", ".join(sorted_streets[:2])
                                st.markdown(f"**Street Bets:** {streets_str}")
                    
                    # Animate second column with a slight delay
                    with summary_cols[1]:
                        # Add small delay for second column appearance
                        time.sleep(0.3)
                        st.markdown("### Bet Details")
                        
                        # Display recommended bet size
                        if specific_recommendations.get("highest_confidence", 0) > 0:
                            st.success(f"Recommended bet size: ${specific_recommendations.get('recommended_bet_size', 0):.2f}")
                        
                        # Show all the even money bets
                        st.markdown("#### Even Money Bets:")
                        
                        if specific_recommendations["red_black"]["recommendation"]:
                            time.sleep(0.05)  # Subtle animation delay
                            st.markdown(f"**Color:** {specific_recommendations['red_black']['recommendation'].upper()}")
                        
                        if specific_recommendations["even_odd"]["recommendation"]:
                            time.sleep(0.05)  # Subtle animation delay
                            st.markdown(f"**Parity:** {specific_recommendations['even_odd']['recommendation'].upper()}")
                        
                        if specific_recommendations["high_low"]["recommendation"]:
                            time.sleep(0.05)  # Subtle animation delay
                            st.markdown(f"**Range:** {specific_recommendations['high_low']['recommendation'].upper()}")
                        
                        # Show all the column/dozen bets
                        time.sleep(0.1)  # Slightly longer delay between sections
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
                        time.sleep(0.1)  # Final animation delay
                        st.markdown("---")
                        if st.session_state.fast_mode:
                            st.caption("⚡ Analysis completed in fast mode for 8-second window")
                        else:
                            st.caption("🔍 Comprehensive analysis mode")
        
        # Create animated display of tabs section
        with st.spinner("Loading detailed recommendations..."):
            # Add a slight delay before showing the detailed tabs for a smoother transition
            time.sleep(0.4)
            
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
                                     min_value=1.0, 
                                     max_value=sim_bankroll/10,  # Max 10% of bankroll
                                     value=recommended_bet,
                                     step=1.0)
        
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
                time.sleep(0.5)  # Add a brief delay for animation effect
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
            st.plotly_chart(fig, use_container_width=True)
            
            # Update agent recommendation
            st.subheader("Updated Agent Recommendation")
            new_strategy = st.session_state.agent.get_recommendation(current_bankroll)
            st.info(f"Based on the simulation results, the agent now recommends the {new_strategy} strategy.")
    else:
        st.info("No spin data available for strategy agent. Please add spins in the Spin Tracker tab.")

# Tab 5: Statistics
with tab5:
    st.header(f"Statistics - {st.session_state.current_session}")
    
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
            st.plotly_chart(fig, use_container_width=True)
        
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
            st.plotly_chart(fig, use_container_width=True)
        
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
        
        bankroll = st.number_input("Initial bankroll (units):", min_value=10, value=100, step=10)
        bet_size = st.number_input("Bet size (units):", min_value=1, value=1, step=1)
        
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
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No spin data available for statistics. Please add spins in the Spin Tracker tab.")
