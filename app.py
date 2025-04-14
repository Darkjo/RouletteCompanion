import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import json

from utils.roulette_logic import RouletteGame
from utils.data_manager import DataManager
from utils.betting_strategies import BettingStrategies
from utils.visualization import Visualization

# Set page configuration
st.set_page_config(
    page_title="Roulette Tracker & Analyzer",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()

if 'current_session' not in st.session_state:
    st.session_state.current_session = None

if 'sessions' not in st.session_state:
    st.session_state.sessions = []

if 'roulette_type' not in st.session_state:
    st.session_state.roulette_type = "European"

# Main app title
st.title("🎰 Roulette Tracker & Analyzer")

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    # Roulette type selection
    roulette_type = st.radio(
        "Roulette Type",
        ["European", "American"],
        index=0 if st.session_state.roulette_type == "European" else 1
    )
    
    if roulette_type != st.session_state.roulette_type:
        st.session_state.roulette_type = roulette_type
        st.rerun()
    
    # Session management
    st.subheader("Session Management")
    session_action = st.radio("Session Action", ["Continue Current", "Start New", "Load Previous"])
    
    if session_action == "Start New":
        session_name = st.text_input("Session Name", f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        if st.button("Create New Session"):
            st.session_state.current_session = session_name
            if session_name not in st.session_state.sessions:
                st.session_state.sessions.append(session_name)
                st.session_state.data_manager.create_session(session_name, st.session_state.roulette_type)
            st.success(f"Created session: {session_name}")
            st.rerun()
    
    elif session_action == "Load Previous":
        if not st.session_state.sessions:
            st.warning("No saved sessions found.")
        else:
            selected_session = st.selectbox("Select Session", st.session_state.sessions)
            if st.button("Load Session"):
                st.session_state.current_session = selected_session
                st.success(f"Loaded session: {selected_session}")
                st.rerun()
    
    # Display current session
    if st.session_state.current_session:
        st.info(f"Current Session: {st.session_state.current_session}")
        # Show delete button
        if st.button("Delete Current Session"):
            if st.session_state.current_session in st.session_state.sessions:
                st.session_state.sessions.remove(st.session_state.current_session)
                st.session_state.data_manager.delete_session(st.session_state.current_session)
                st.session_state.current_session = None
                st.success("Session deleted")
                st.rerun()
    else:
        st.warning("No active session. Create or load a session to begin.")

# Main content
if st.session_state.current_session:
    tabs = st.tabs(["Spin Tracker", "Analysis", "Betting Suggestions", "History"])
    
    # Get session data
    session_data = st.session_state.data_manager.get_session_data(st.session_state.current_session)
    roulette_type = session_data.get('roulette_type', st.session_state.roulette_type)
    
    # Initialize roulette game with the correct type
    roulette_game = RouletteGame(roulette_type)
    
    # Initialize visualization
    viz = Visualization(roulette_game)
    
    # Initialize betting strategies
    betting_strategies = BettingStrategies(roulette_game)
    
    # Tab 1: Spin Tracker
    with tabs[0]:
        st.header("Record Spin Results")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Manual input section
            st.subheader("Manual Input")
            
            # Number input
            spin_result = st.number_input(
                "Enter Spin Result",
                min_value=0,
                max_value=36 if roulette_type == "European" else 37,  # 37 represents 00 in American
                value=0,
                help="Enter the number that came up in the spin (use 37 for 00 in American roulette)"
            )
            
            # Additional properties
            color = roulette_game.get_color(spin_result)
            is_even = roulette_game.is_even(spin_result)
            dozen = roulette_game.get_dozen(spin_result)
            column = roulette_game.get_column(spin_result)
            half = roulette_game.get_half(spin_result)
            
            st.write(f"**Color:** {color.upper()}")
            st.write(f"**Even/Odd:** {'EVEN' if is_even else 'ODD'}")
            st.write(f"**Dozen:** {dozen}")
            st.write(f"**Column:** {column}")
            st.write(f"**Half:** {half}")
            
            # Record spin button
            if st.button("Record Spin"):
                timestamp = datetime.now().isoformat()
                spin_data = {
                    "timestamp": timestamp,
                    "number": int(spin_result),
                    "color": color,
                    "is_even": is_even,
                    "dozen": dozen,
                    "column": column,
                    "half": half
                }
                
                st.session_state.data_manager.add_spin(st.session_state.current_session, spin_data)
                st.success(f"Recorded spin: {spin_result} ({color})")
                # Force refresh
                st.rerun()
        
        with col2:
            # Visual representation of the roulette wheel
            st.subheader("Roulette Wheel")
            
            # Use plotly for a visual representation of the wheel
            wheel_fig = viz.create_wheel_visualization(highlight_number=spin_result)
            st.plotly_chart(wheel_fig, use_container_width=True)
    
    # Tab 2: Analysis
    with tabs[1]:
        st.header("Spin Analysis")
        
        # Get spin history
        spin_history = st.session_state.data_manager.get_spin_history(st.session_state.current_session)
        
        if not spin_history:
            st.warning("No spin data recorded yet. Add spins in the Spin Tracker tab.")
        else:
            # Convert to DataFrame for analysis
            df = pd.DataFrame(spin_history)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Number Frequency")
                number_counts = df['number'].value_counts().reindex(range(37 if roulette_type == "European" else 38), fill_value=0)
                
                # Hot and cold numbers
                hot_numbers = number_counts.nlargest(5)
                cold_numbers = number_counts[number_counts > 0].nsmallest(5)
                
                st.markdown("##### Hot Numbers (Most Frequent)")
                for num, count in hot_numbers.items():
                    num_display = num if num != 37 else "00"
                    st.markdown(f"**{num_display}**: {count} times - {viz.get_colored_number_display(num)}")
                
                st.markdown("##### Cold Numbers (Least Frequent)")
                for num, count in cold_numbers.items():
                    num_display = num if num != 37 else "00"
                    st.markdown(f"**{num_display}**: {count} times - {viz.get_colored_number_display(num)}")
                
                # Frequency chart
                frequency_fig = px.bar(
                    x=[str(i) if i != 37 else "00" for i in range(38 if roulette_type == "American" else 37)],
                    y=number_counts,
                    title="Number Frequency",
                    labels={'x': 'Number', 'y': 'Frequency'}
                )
                st.plotly_chart(frequency_fig, use_container_width=True)
            
            with col2:
                st.subheader("Pattern Analysis")
                
                # Color distribution
                color_counts = df['color'].value_counts()
                color_fig = px.pie(
                    values=color_counts.values,
                    names=color_counts.index,
                    title="Color Distribution",
                    color=color_counts.index,
                    color_discrete_map={'red': 'red', 'black': 'black', 'green': 'green'}
                )
                st.plotly_chart(color_fig, use_container_width=True)
                
                # Even/Odd distribution
                even_odd_counts = df['is_even'].map({True: 'Even', False: 'Odd'}).value_counts()
                even_odd_fig = px.pie(
                    values=even_odd_counts.values,
                    names=even_odd_counts.index,
                    title="Even/Odd Distribution"
                )
                st.plotly_chart(even_odd_fig, use_container_width=True)
            
            # Additional statistical analysis
            st.subheader("Advanced Pattern Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Dozen distribution
                dozen_counts = df['dozen'].value_counts().sort_index()
                dozen_fig = px.bar(
                    x=dozen_counts.index,
                    y=dozen_counts.values,
                    title="Dozen Distribution",
                    labels={'x': 'Dozen', 'y': 'Count'}
                )
                st.plotly_chart(dozen_fig, use_container_width=True)
            
            with col2:
                # Column distribution
                column_counts = df['column'].value_counts().sort_index()
                column_fig = px.bar(
                    x=column_counts.index,
                    y=column_counts.values,
                    title="Column Distribution",
                    labels={'x': 'Column', 'y': 'Count'}
                )
                st.plotly_chart(column_fig, use_container_width=True)
            
            with col3:
                # Half distribution
                half_counts = df['half'].value_counts().sort_index()
                half_fig = px.bar(
                    x=half_counts.index,
                    y=half_counts.values,
                    title="Half Distribution",
                    labels={'x': 'Half', 'y': 'Count'}
                )
                st.plotly_chart(half_fig, use_container_width=True)
                
            # Sequential pattern analysis
            st.subheader("Sequential Pattern Analysis")
            
            # Calculate sequential patterns
            if len(df) >= 5:
                # Last 5 spins
                last_5_spins = df['number'].tail(5).tolist()
                st.write(f"Last 5 spins: {', '.join([str(n) if n != 37 else '00' for n in last_5_spins])}")
                
                # Check for repeating patterns
                repeating_patterns = viz.find_repeating_patterns(df['number'].tolist())
                if repeating_patterns:
                    st.markdown("##### Detected Repeating Patterns:")
                    for pattern, occurrences in repeating_patterns.items():
                        pattern_display = [str(n) if n != 37 else '00' for n in pattern]
                        st.write(f"Pattern `{' → '.join(pattern_display)}` has occurred {occurrences} times")
                else:
                    st.write("No significant repeating patterns detected.")
                
            else:
                st.info("Need at least 5 spins to analyze sequential patterns.")
                
            # Trend visualization
            st.subheader("Trend Visualization")
            
            if len(df) > 1:
                # Timeline of spins
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['spin_index'] = range(len(df))
                
                trend_fig = go.Figure()
                
                # Add points colored by color property
                for color in ['red', 'black', 'green']:
                    color_df = df[df['color'] == color]
                    trend_fig.add_trace(go.Scatter(
                        x=color_df['spin_index'],
                        y=color_df['number'],
                        mode='markers',
                        name=color.capitalize(),
                        marker=dict(color=color, size=10),
                        hovertemplate='Spin #%{x}<br>Number: %{y}'
                    ))
                
                trend_fig.update_layout(
                    title="Spin History Timeline",
                    xaxis_title="Spin Number",
                    yaxis_title="Result",
                    legend_title="Color"
                )
                
                st.plotly_chart(trend_fig, use_container_width=True)
                
                # Consecutive color runs
                color_runs = viz.analyze_color_runs(df['color'].tolist())
                
                st.markdown("##### Longest Color Runs:")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Longest Red Run", color_runs['red'])
                
                with col2:
                    st.metric("Longest Black Run", color_runs['black'])
                
                with col3:
                    st.metric("Longest Green Run", color_runs['green'])
            
            else:
                st.info("Need at least 2 spins to visualize trends.")
    
    # Tab 3: Betting Suggestions
    with tabs[2]:
        st.header("Betting Suggestions")
        
        spin_history = st.session_state.data_manager.get_spin_history(st.session_state.current_session)
        
        if not spin_history or len(spin_history) < 5:
            st.warning("Need at least 5 spins to generate meaningful betting suggestions.")
        else:
            df = pd.DataFrame(spin_history)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Strategy Selection")
                
                strategy = st.selectbox(
                    "Select Betting Strategy",
                    ["Pattern-Based", "Martingale", "D'Alembert", "Fibonacci", "Hot/Cold Numbers"],
                    help="Different strategies for placing bets"
                )
                
                risk_level = st.slider(
                    "Risk Level",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="1 = Conservative, 5 = Aggressive"
                )
                
                st.write("Strategy Description:")
                if strategy == "Pattern-Based":
                    st.info("Based on detected patterns in recent spin history.")
                elif strategy == "Martingale":
                    st.info("Double your bet after each loss, return to base bet after a win.")
                elif strategy == "D'Alembert":
                    st.info("Increase bet by one unit after a loss, decrease by one unit after a win.")
                elif strategy == "Fibonacci":
                    st.info("Follow the Fibonacci sequence for bet sizing after losses.")
                elif strategy == "Hot/Cold Numbers":
                    st.info("Bet on numbers that have been appearing frequently or rarely.")
                
                if st.button("Generate Suggestions"):
                    # Calculate suggestions based on the selected strategy
                    suggestions = betting_strategies.generate_suggestions(
                        df, 
                        strategy=strategy, 
                        risk_level=risk_level
                    )
                    
                    # Store in session state to display in the other column
                    st.session_state.current_suggestions = suggestions
                    st.rerun()
            
            with col2:
                st.subheader("Suggested Bets")
                
                if 'current_suggestions' in st.session_state and st.session_state.current_suggestions:
                    suggestions = st.session_state.current_suggestions
                    
                    st.markdown("##### Primary Bets:")
                    for bet in suggestions['primary_bets']:
                        st.markdown(f"- **{bet['type']}**: {bet['description']} (Confidence: {bet['confidence']}%)")
                    
                    st.markdown("##### Secondary Bets (Optional):")
                    for bet in suggestions['secondary_bets']:
                        st.markdown(f"- **{bet['type']}**: {bet['description']} (Confidence: {bet['confidence']}%)")
                    
                    st.markdown("##### Reasoning:")
                    st.write(suggestions['reasoning'])
                    
                    # Display warning about gambling
                    st.warning("""
                    **Disclaimer:** These suggestions are based on historical patterns only. 
                    Roulette is a game of chance with a guaranteed house edge. 
                    No betting system can guarantee profits in the long run.
                    """)
                else:
                    st.info("Select a strategy and click 'Generate Suggestions' to see betting recommendations.")
            
            # Strategy performance analysis if we have enough data
            if len(df) >= 20:  # Need a reasonable amount of historical data
                st.subheader("Historical Strategy Performance")
                
                # Simulated results using historical data
                simulation_results = betting_strategies.simulate_strategies(df['number'].tolist())
                
                # Create a performance chart
                performance_fig = go.Figure()
                
                for strategy_name, results in simulation_results.items():
                    performance_fig.add_trace(go.Scatter(
                        x=list(range(len(results))),
                        y=results,
                        mode='lines',
                        name=strategy_name
                    ))
                
                performance_fig.update_layout(
                    title="Simulated Strategy Performance",
                    xaxis_title="Spin Number",
                    yaxis_title="Cumulative Profit/Loss (Units)",
                    legend_title="Strategy"
                )
                
                st.plotly_chart(performance_fig, use_container_width=True)
                
                # Final performance metrics
                metrics_df = pd.DataFrame({
                    'Strategy': simulation_results.keys(),
                    'Final P/L': [results[-1] for results in simulation_results.values()],
                    'Max Profit': [max(results) for results in simulation_results.values()],
                    'Max Drawdown': [min(0, min(results)) for results in simulation_results.values()]
                })
                
                st.dataframe(metrics_df.set_index('Strategy'))
    
    # Tab 4: History
    with tabs[3]:
        st.header("Spin History")
        
        spin_history = st.session_state.data_manager.get_spin_history(st.session_state.current_session)
        
        if not spin_history:
            st.warning("No spin data recorded yet. Add spins in the Spin Tracker tab.")
        else:
            # Convert to DataFrame for display
            df = pd.DataFrame(spin_history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['formatted_time'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Create a clean display dataframe
            display_df = df[['formatted_time', 'number', 'color', 'is_even', 'dozen', 'column', 'half']].copy()
            display_df.columns = ['Timestamp', 'Number', 'Color', 'Is Even', 'Dozen', 'Column', 'Half']
            
            # Replace 37 with '00' for display
            display_df['Number'] = display_df['Number'].apply(lambda x: '00' if x == 37 else x)
            
            # Display the table
            st.dataframe(
                display_df.sort_values('Timestamp', ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
            # Option to export data
            if st.button("Export History as CSV"):
                csv = display_df.to_csv(index=False).encode('utf-8')
                session_name = st.session_state.current_session.replace(" ", "_")
                st.download_button(
                    "Download CSV File",
                    csv,
                    f"roulette_history_{session_name}.csv",
                    "text/csv",
                    key='download-csv'
                )
                
            # Clear history option
            if st.button("Clear Spin History"):
                st.session_state.data_manager.clear_spin_history(st.session_state.current_session)
                st.success("Spin history cleared successfully.")
                st.rerun()
else:
    # No active session - show welcome message
    st.info("👈 Create or load a session from the sidebar to start tracking your roulette spins.")
    
    st.markdown("""
    ## Welcome to the Roulette Tracker & Analyzer
    
    This application helps you:
    - Record and track roulette spin results
    - Analyze patterns and trends in the data
    - Get betting suggestions based on historical patterns
    - Track multiple betting sessions
    
    ### Features:
    - Support for both European and American roulette
    - Visual representation of spin history
    - Hot/cold number identification
    - Pattern detection and analysis
    - Multiple betting strategy suggestions
    
    To get started, create a new session from the sidebar.
    """)
