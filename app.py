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
from utils.agent import RLAgent
from utils.performance_tracker import StrategyPerformanceTracker
from utils.strategies import StrategyEngine
from utils.strategy_selector import choose_strategy, get_bet_size_recommendation, get_strategy_description
from utils.wheel_input import create_roulette_wheel_input, create_file_importer
from utils.quick_input import add_floating_quick_input
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
    
if 'bankroll' not in st.session_state:
    st.session_state.bankroll = 100.0
    
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
    
    data_input_tabs = st.tabs(["Visual Wheel Input", "Manual Entry", "Import from File", "Web Scraper"])
    
    with data_input_tabs[0]:
        # Visual wheel input
        st.write("Use the visual roulette wheel to select a number:")
        selected_number = create_roulette_wheel_input(current_roulette_type)
        
        if selected_number:
            col1, col2 = st.columns(2)
            
            with col1:
                # Use current time by default
                use_current_time = st.checkbox("Use current time", value=True)
            
            with col2:
                # Add button to confirm the selection
                add_selected = st.button("Add Selected Number")
            
            if add_selected:
                # Timestamp handling
                if use_current_time:
                    spin_timestamp = datetime.now()
                else:
                    # Add timestamp selection if not using current time
                    st.write("Select date and time:")
                    timestamp = st.date_input("Spin Date:", value=datetime.now().date())
                    time_input = st.time_input("Spin Time:", value=datetime.now().time())
                    spin_timestamp = datetime.combine(timestamp, time_input)
                
                # Add spin to current session
                st.session_state.roulette_data.add_spin(
                    session_name=st.session_state.current_session,
                    number=selected_number,
                    timestamp=spin_timestamp
                )
                
                st.success(f"Added spin result: {selected_number}")
                st.rerun()  # Refresh the page to show updated data
    
    with data_input_tabs[1]:
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

# Tab 4: Advanced Strategy Agent
with tab4:
    st.header(f"Advanced Strategy Agent - {st.session_state.current_session}")
    
    # Get data for current session
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
        specific_recommendations = st.session_state.agent.get_specific_bet_recommendations(
            spins_df, 
            current_roulette_type, 
            st.session_state.bankroll
        )
        
        # Display recommendation confidence explanation
        st.info(specific_recommendations["confidence_explanation"])
        
        if specific_recommendations.get("highest_confidence", 0) > 0:
            st.success(f"Recommended bet size: ${specific_recommendations.get('recommended_bet_size', 0):.2f}")
        
        # Create tabs for different bet types
        bet_tabs = st.tabs(["Numbers", "Split Bets", "Columns/Dozens", "Even Money Bets"])
        
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
                    counts = dozen_data["counts"]
                    for dozen_name, count in counts.items():
                        st.markdown(f"{dozen_name}: {count} spins")
                    confidence = dozen_data['confidence'] * 100
                    st.progress(dozen_data['confidence'], text=f"Confidence: {confidence:.0f}%")
                else:
                    st.write("No statistically significant dozen bias detected.")
        
        with bet_tabs[3]:
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
            
            # Display simulation results
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
