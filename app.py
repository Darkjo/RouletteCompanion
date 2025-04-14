import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os

from utils.roulette_data import RouletteData
from utils.analysis import RouletteAnalyzer
from utils.betting_strategies import BettingStrategist
from utils.visualization import RouletteVisualizer

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
    
if 'current_session' not in st.session_state:
    st.session_state.current_session = "Default Session"
    
if 'sessions' not in st.session_state:
    st.session_state.sessions = ["Default Session"]

# Application title
st.title("🎰 Roulette Tracker and Analyzer")

# Sidebar for settings and navigation
with st.sidebar:
    st.header("Settings")
    
    # Roulette type selection
    roulette_type = st.radio(
        "Select Roulette Type:",
        options=["European", "American"],
        index=0
    )
    
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
    
    # Save data to file
    if st.button("Save All Data"):
        success = st.session_state.roulette_data.save_data()
        if success:
            st.success("Data saved successfully!")
        else:
            st.error("Failed to save data.")
    
    # Load data from file
    if st.button("Load Data"):
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
tab1, tab2, tab3, tab4 = st.tabs(["Spin Tracker", "Analysis", "Betting Suggestions", "Statistics"])

# Tab 1: Spin Tracker
with tab1:
    st.header(f"Spin Tracker - {st.session_state.current_session}")
    
    # Get current roulette type for this session
    current_roulette_type = st.session_state.roulette_data.get_session_type(st.session_state.current_session)
    
    # Display current roulette type
    st.info(f"Current Roulette Type: {current_roulette_type}")
    
    # Input section for new spins
    st.subheader("Record New Spin")
    
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
    if st.button("Add Spin Result"):
        # Convert -1 to '00' for American roulette
        display_number = '00' if spin_number == -1 else str(spin_number)
        
        # Add spin to current session
        st.session_state.roulette_data.add_spin(
            session_name=st.session_state.current_session,
            number=display_number,
            timestamp=spin_timestamp
        )
        
        st.success(f"Added spin result: {display_number}")
    
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
             "Dozens Distribution", "Columns Distribution", "High/Low Distribution"]
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

# Tab 4: Statistics
with tab4:
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
        
        if st.button("Run Simulation"):
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
