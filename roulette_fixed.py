"""
Interactive Roulette Simulation App
Provides a visual interface for placing and evaluating roulette bets.
"""
from datetime import datetime
from typing import Dict, List, Tuple, Union

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import plotly.subplots as sp

# Import simulation module for roulette game
from utils.simulation import RouletteBet, RouletteSimulator
from utils.advanced_betting import AdvancedBettingAnalysis

# Initialize session state variables if not already set
if 'simulator' not in st.session_state:
    st.session_state.simulator = RouletteSimulator('European')
    st.session_state.simulator.initial_balance = 1000.0  # Set initial balance to track profit
    st.session_state.simulator.balance = 1000.0  # Start with $1000
    
    # Create an advanced betting analysis instance
    st.session_state.advanced_analysis = AdvancedBettingAnalysis()
    
    # Create a dataframe to track spin history
    st.session_state.spins_df = pd.DataFrame(
        columns=['number', 'color', 'parity', 'range', 'dozen', 'column', 'timestamp']
    )
    
    # Create a list to track win/loss history
    st.session_state.win_history = []
    
    # Create a dictionary to track strategy performance
    st.session_state.strategy_performance = {}
    
    # Initialize current bet amount (chip value)
    st.session_state.current_bet_amount = 5.0
    
    # Create a mock ML agent for recommendations
    from utils.agent import RLAgent
    st.session_state.agent = RLAgent()

def get_chip_color(value: float) -> str:
    """Get a color for a chip based on its value."""
    if value <= 1:
        return "white"
    elif value <= 5:
        return "red"
    elif value <= 25:
        return "green"
    elif value <= 100:
        return "black"
    else:
        return "purple"

def update_spins_df(number: Union[int, str], manually_added: bool = False):
    """Update the spins dataframe with a new result."""
    # Get properties for the number
    props = st.session_state.simulator.get_number_properties(number)
    
    # Create a new row with the spin result and current timestamp
    new_row = {
        'number': number,
        'color': props['color'],
        'parity': props['parity'],
        'range': props['range'],
        'dozen': props['dozen'],
        'column': props['column'],
        'timestamp': datetime.now(),
        'manually_added': manually_added
    }
    
    # Append the new row to the dataframe
    st.session_state.spins_df = pd.concat(
        [st.session_state.spins_df, pd.DataFrame([new_row])],
        ignore_index=True
    )
    
    # Update the agent with the new data
    if hasattr(st.session_state, 'agent'):
        # Record the new number - RLAgent doesn't have update method
        # so we simply add it to our tracking data
        pass

def spin_wheel():
    """Spin the roulette wheel and process results."""
    # Get the result of the spin
    result = st.session_state.simulator.spin()
    
    # Update the spins dataframe
    update_spins_df(result)
    
    # Get and store win/loss details
    details = st.session_state.simulator.get_last_result_details()
    
    # Track win/loss for analyzing strategy performance
    # Get the winnings directly from the details
    net_winnings = details.get('winnings', 0)
    
    # Record in session history
    st.session_state.win_history.append({
        'number': result,
        'winnings': net_winnings,
        'timestamp': datetime.now()
    })
    
    # Record strategy performance if agent recommendation was followed
    if hasattr(st.session_state, 'agent') and hasattr(st.session_state.agent, 'recent_recommendations'):
        # Get the most recent recommendation
        recent_recs = st.session_state.agent.recent_recommendations
        if recent_recs:
            # Simplified tracking for strategy performance
            # Since we don't have access to individual bet results in the current format
            # We'll track overall wins/losses for each strategy
            for strat_name, rec_details in recent_recs.items():
                if strat_name not in st.session_state.strategy_performance:
                    st.session_state.strategy_performance[strat_name] = {
                        'wins': 0, 'losses': 0, 'profit': 0
                    }
                
                # If we have a net win, count it as a win for the strategy
                if net_winnings > 0:
                    st.session_state.strategy_performance[strat_name]['wins'] += 1
                    st.session_state.strategy_performance[strat_name]['profit'] += net_winnings
                elif net_winnings < 0:
                    st.session_state.strategy_performance[strat_name]['losses'] += 1
                    st.session_state.strategy_performance[strat_name]['profit'] += net_winnings
    
    # Show the result
    return result

def place_bet(bet_type, *args):
    """Place a bet of the specified type."""
    # Get current chip value from session state
    amount = st.session_state.current_bet_amount
    
    # Call the appropriate method of the simulator based on bet type
    if bet_type == 'straight':
        number = args[0]
        success = st.session_state.simulator.add_straight_bet(number, amount)
    elif bet_type == 'split':
        num1, num2 = args[0], args[1]
        success = st.session_state.simulator.add_split_bet(num1, num2, amount)
    elif bet_type == 'street':
        row = args[0]
        success = st.session_state.simulator.add_street_bet(row, amount)
    elif bet_type == 'corner':
        corner = args[0]
        success = st.session_state.simulator.add_corner_bet(corner, amount)
    elif bet_type == 'six_line':
        line = args[0]
        success = st.session_state.simulator.add_six_line_bet(line, amount)
    elif bet_type == 'top_line':
        success = st.session_state.simulator.add_top_line_bet(amount)
    elif bet_type == 'color':
        color = args[0]
        success = st.session_state.simulator.add_color_bet(color, amount)
    elif bet_type == 'parity':
        parity = args[0]
        success = st.session_state.simulator.add_parity_bet(parity, amount)
    elif bet_type == 'range':
        range_type = args[0]
        success = st.session_state.simulator.add_range_bet(range_type, amount)
    elif bet_type == 'dozen':
        dozen = args[0]
        success = st.session_state.simulator.add_dozen_bet(dozen, amount)
    elif bet_type == 'column':
        column = args[0]
        success = st.session_state.simulator.add_column_bet(column, amount)
    else:
        success = False
    
    return success

def create_roulette_board():
    """Create an interactive roulette board using native Streamlit components."""
    st.markdown("## Roulette Board")
    st.write("Select a chip amount in the sidebar and click on the board to place your bets:")
    
    # Standard roulette wheel - these numbers are red
    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    
    # Create a styling function for the number cells
    def get_number_style(num, is_zero=False):
        if is_zero:
            bg_color = "#008800"  # Green
            text_color = "white"
        elif num in red_numbers:
            bg_color = "#CC0000"  # Red
            text_color = "white"
        else:
            bg_color = "#000000"  # Black
            text_color = "white"
            
        # Check if there's a bet on this number
        has_bet = False
        bet_amount = ""
        for bet in st.session_state.simulator.active_bets:
            if num in bet.numbers and len(bet.numbers) == 1:
                has_bet = True
                bet_amount = str(bet.amount)
                break
                
        # Define the base style
        style = f"""
            background-color: {bg_color};
            color: {text_color};
            display: flex;
            justify-content: center;
            align-items: center;
            height: 50px;
            font-weight: bold;
            border-radius: 5px;
            text-align: center;
            cursor: pointer;
            position: relative;
        """
        
        # If there's a bet on this number, add a chip
        if has_bet:
            chip = f"""
            <div style="position: absolute; top: 5px; right: 5px; 
                    width: 20px; height: 20px; border-radius: 50%; 
                    background-color: white; color: black; 
                    display: flex; justify-content: center; align-items: center;
                    font-size: 10px; border: 2px dashed gold; font-weight: bold;">
                ${bet_amount}
            </div>
            """
        else:
            chip = ""
        
        return style, chip
    
    # Create the roulette board layout
    # Zero pocket
    zero_style, zero_chip = get_number_style(0, is_zero=True)
    
    # Create the main rows
    # This approach uses Streamlit's native components with HTML styling
    
    # Zero column
    zero_col, number_grid = st.columns([1, 11])
    
    with zero_col:
        # Create a full-height zero cell
        st.markdown(f"""
        <div style="{zero_style} height: 156px;">
            0
            {zero_chip}
        </div>
        """, unsafe_allow_html=True)
        
        # When clicked, place a bet on zero
        if st.button("Bet on 0", key="btn_zero", use_container_width=True, type="secondary"):
            place_bet('straight', 0)
            st.success("Bet placed on 0")
            st.rerun()
    
    # Main number grid (1-36)
    with number_grid:
        # Row 1 (numbers 1, 4, 7, ...)
        row1_cols = st.columns(12)
        for i, num in enumerate([n for n in range(1, 37, 3)]):
            style, chip = get_number_style(num)
            row1_cols[i].markdown(f"""
            <div style="{style}">
                {num}
                {chip}
            </div>
            """, unsafe_allow_html=True)
            
            # Add a button to place a bet
            if row1_cols[i].button(f"Bet", key=f"btn_{num}", use_container_width=True):
                place_bet('straight', num)
                st.success(f"Bet placed on {num}")
                st.rerun()
                
        # Row 2 (numbers 2, 5, 8, ...)
        row2_cols = st.columns(12)
        for i, num in enumerate([n for n in range(2, 37, 3)]):
            style, chip = get_number_style(num)
            row2_cols[i].markdown(f"""
            <div style="{style}">
                {num}
                {chip}
            </div>
            """, unsafe_allow_html=True)
            
            # Add a button to place a bet
            if row2_cols[i].button(f"Bet", key=f"btn_{num}", use_container_width=True):
                place_bet('straight', num)
                st.success(f"Bet placed on {num}")
                st.rerun()
                
        # Row 3 (numbers 3, 6, 9, ...)
        row3_cols = st.columns(12)
        for i, num in enumerate([n for n in range(3, 37, 3)]):
            style, chip = get_number_style(num)
            row3_cols[i].markdown(f"""
            <div style="{style}">
                {num}
                {chip}
            </div>
            """, unsafe_allow_html=True)
            
            # Add a button to place a bet
            if row3_cols[i].button(f"Bet", key=f"btn_{num}", use_container_width=True):
                place_bet('straight', num)
                st.success(f"Bet placed on {num}")
                st.rerun()
                
        # Column bets (2:1)
        col_bet_cols = st.columns(12)
        for i in range(3):
            with col_bet_cols[i*4 + 1]:
                if st.button(f"2:1 (col {i+1})", key=f"col_{i+1}", use_container_width=True):
                    place_bet('column', i+1)
                    st.success(f"Column bet placed on column {i+1}")
                    st.rerun()
    
    # Outside bets
    st.markdown("### Outside Bets")
    
    # Dozen bets
    dozen_cols = st.columns(3)
    for i in range(3):
        label = f"{i*12+1}-{i*12+12}"
        if dozen_cols[i].button(f"Dozen {i+1}: {label}", key=f"dozen_{i+1}", use_container_width=True):
            place_bet('dozen', i+1)
            st.success(f"Dozen bet placed on {label}")
            st.rerun()
    
    # Even money bets
    even_cols = st.columns(6)
    
    # Low/High
    if even_cols[0].button("1-18", key="low", use_container_width=True):
        place_bet('range', 'low')
        st.success("Bet placed on 1-18")
        st.rerun()
        
    if even_cols[5].button("19-36", key="high", use_container_width=True):
        place_bet('range', 'high')
        st.success("Bet placed on 19-36")
        st.rerun()
    
    # Even/Odd
    if even_cols[1].button("EVEN", key="even", use_container_width=True):
        place_bet('parity', 'even')
        st.success("Bet placed on EVEN")
        st.rerun()
        
    if even_cols[4].button("ODD", key="odd", use_container_width=True):
        place_bet('parity', 'odd')
        st.success("Bet placed on ODD")
        st.rerun()
    
    # Red/Black
    if even_cols[2].button("RED", key="red", use_container_width=True, type="primary"):
        place_bet('color', 'red')
        st.success("Bet placed on RED")
        st.rerun()
        
    if even_cols[3].button("BLACK", key="black", use_container_width=True):
        place_bet('color', 'black')
        st.success("Bet placed on BLACK")
        st.rerun()
    
    # Bet types legend
    st.markdown("""
    ### Bet Types and Payouts
    - **Straight Bet** (single number): 35 to 1
    - **Split Bet** (2 adjacent numbers): 17 to 1
    - **Street Bet** (3 numbers in a row): 11 to 1
    - **Corner Bet** (4 numbers in a square): 8 to 1
    - **Six Line** (6 numbers, two rows): 5 to 1
    - **Column/Dozen**: 2 to 1
    - **Red/Black, Odd/Even, 1-18/19-36**: 1 to 1
    """)
    
    # Clear bets button
    if st.button("Clear All Bets", key="clear_bets", type="secondary"):
        st.session_state.simulator.clear_bets()
        st.success("All bets cleared")
        st.rerun()

def create_chip_selector():
    """Create a selector for betting chips."""
    # This function is integrated into create_roulette_board for better UI organization
    pass

def create_betting_controls():
    """Create controls for betting and spinning - now integrated into main layout."""
    pass

def create_spin_history_display():
    """Create a display for the spin history."""
    st.write("### Spin History")
    
    if not st.session_state.spins_df.empty:
        # Display the last 10 spins
        last_spins = st.session_state.spins_df.tail(20).copy()
        last_spins['timestamp'] = last_spins['timestamp'].dt.strftime('%H:%M:%S')
        
        # Create colored display for numbers
        cols = st.columns(min(20, len(last_spins)))
        for i, (_, spin) in enumerate(last_spins.iterrows()):
            color = spin['color']
            text_color = "white" if color in ['black', 'green'] else "black"
            
            cols[i].markdown(
                f"<div style='background-color: {color}; color: {text_color}; "
                f"text-align: center; padding: 10px; border-radius: 50%; width: 100%;'>"
                f"{spin['number']}</div>",
                unsafe_allow_html=True
            )

def create_recommendation_display():
    """Create a display for agent recommendations."""
    if not hasattr(st.session_state, 'agent') or st.session_state.spins_df.empty:
        st.info("Play more spins to get recommendations!")
        return
    
    # Display agent accuracy and recommendation summary
    st.write("### Agent Predictions")
    
    acc = st.session_state.agent.get_accuracy()
    st.progress(acc, text=f"Prediction Accuracy: {acc:.1%}")
    
    # Show recommendation for bet sizing
    bankroll = st.session_state.simulator.balance
    if bankroll > 0:
        bet_size_rec = st.session_state.agent.get_bet_size_recommendation(bankroll)
        st.write(f"**Recommended Bet Size:** ${bet_size_rec:.2f}")
    
    # Show winning streak or losing streak context
    losing_streak = st.session_state.agent.recent_losing_streak()
    if losing_streak > 3:
        st.warning(f"⚠️ Current losing streak: {losing_streak} spins")

def create_strategy_performance_display():
    """Create a display for strategy performance."""
    if not st.session_state.strategy_performance:
        st.info("Play more spins with recommendations to see strategy performance.")
        return
    
    st.write("### Strategy Performance")
    
    # Create a dataframe for strategy performance
    strat_data = []
    for strat_name, results in st.session_state.strategy_performance.items():
        wins = results.get('wins', 0)
        losses = results.get('losses', 0)
        total = wins + losses
        win_rate = wins / total if total > 0 else 0
        
        # Format strategy name for display
        display_name = strat_name.replace('_', ' ').title()
        
        strat_data.append({
            'Strategy': display_name,
            'Win Rate': f"{win_rate:.1%}",
            'Win/Loss': f"{wins}/{losses}",
            'Expected Value': f"{(win_rate * 2 - 1):.2f}"  # Simplified EV calc
        })
    
    if strat_data:
        strat_df = pd.DataFrame(strat_data)
        st.dataframe(strat_df, use_container_width=True, hide_index=True)

def create_advanced_analysis():
    """Create a display for advanced betting analysis."""
    if len(st.session_state.spins_df) < 10:
        st.info("Need at least 10 spins for advanced analysis.")
        return
    
    # Get analysis from the advanced analysis module
    sleepers = st.session_state.advanced_analysis.get_sleeper_numbers(
        st.session_state.spins_df,
        st.session_state.simulator.roulette_type
    )
    
    if sleepers and 'numbers' in sleepers and sleepers['numbers']:
        st.write("### Sleeper Numbers")
        
        # Display sleeper numbers in a horizontal layout
        cols = st.columns(min(5, len(sleepers['numbers'])))
        
        for i, sleeper in enumerate(sleepers['numbers']):
            if i < len(cols):  # Ensure we don't exceed available columns
                number = sleeper.get('number')
                absence = sleeper.get('spins_absent', 0)
                
                # Get the color for this number for visual display
                props = st.session_state.simulator.get_number_properties(
                    int(number) if str(number).isdigit() else number
                )
                color = props['color']
                text_color = "white" if color in ['black', 'green'] else "black"
                
                # Create a circular display for the number
                cols[i].markdown(
                    f"<div style='background-color: {color}; color: {text_color}; "
                    f"text-align: center; padding: 15px; border-radius: 50%; "
                    f"width: 80%; margin: 0 auto;'>{number}</div>",
                    unsafe_allow_html=True
                )
                cols[i].write(f"Missing: {absence} spins", unsafe_allow_html=True)

def create_session_stats():
    """Create a display for session statistics."""
    st.write("### Session Stats")
    
    # Get basic stats
    stats = st.session_state.simulator.get_summary_stats()
    
    # Create two columns for the stats
    stat_cols = st.columns(2)
    
    with stat_cols[0]:
        st.metric("Initial Balance", f"${st.session_state.simulator.initial_balance:.2f}")
        st.metric("Bets Placed", stats['bets_placed'])
        st.metric("Bet Win Rate", f"{stats['win_rate']:.1%}")
    
    with stat_cols[1]:
        st.metric("Net Profit", f"${stats['net_profit']:.2f}")
        st.metric("Total Wagered", f"${stats['total_wagered']:.2f}")
        st.metric("Return on Investment", f"{stats['roi']:.1%}")
    
    # Show recent results
    if st.session_state.win_history:
        # Calculate a 5-spin moving average for winnings
        win_df = pd.DataFrame(st.session_state.win_history)
        
        # Show only if we have enough data
        if len(win_df) >= 5:
            win_df['rolling_win'] = win_df['winnings'].rolling(window=5).mean()
            
            # Plot the rolling average
            fig = px.line(
                win_df.tail(20), 
                y='rolling_win',
                title="5-Spin Moving Average Profit/Loss",
                labels={'index': 'Spin', 'rolling_win': 'Avg. Profit/Loss ($)'},
            )
            
            # Add a horizontal line at y=0
            fig.add_hline(y=0, line_dash="dash", line_color="red")
            
            # Make the plot more compact
            fig.update_layout(
                height=250,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            
            st.plotly_chart(fig, use_container_width=True)

def main():
    """Main function to run the app."""
    st.title("🎰 Interactive Roulette Simulator")
    
    # Sidebar settings
    with st.sidebar:
        st.write("## Settings")
        
        # Roulette type selection
        roulette_type = st.radio(
            "Roulette Type",
            options=["European", "American"],
            index=0 if st.session_state.simulator.roulette_type == "European" else 1
        )
        
        # Update roulette type if changed
        if roulette_type != st.session_state.simulator.roulette_type:
            st.session_state.simulator.roulette_type = roulette_type
        
        # Bankroll settings
        st.write("## Bankroll")
        
        # Allow setting balance with a slider
        balance = st.number_input(
            "Balance",
            min_value=0.0,
            max_value=10000.0,
            value=st.session_state.simulator.balance,
            step=10.0,
            format="%.2f"
        )
        
        # Update balance if changed
        if balance != st.session_state.simulator.balance:
            st.session_state.simulator.balance = balance
        
        # Reset option
        if st.button("Reset Session", type="primary"):
            st.session_state.simulator.reset()
            
            # Also reset the agent
            if hasattr(st.session_state, 'agent'):
                st.session_state.agent.reset()
            
            # Reset the spin history
            st.session_state.spins_df = pd.DataFrame(
                columns=['number', 'color', 'parity', 'range', 'dozen', 'column', 'timestamp']
            )
            st.session_state.win_history = []
            st.session_state.strategy_performance = {}
            
            st.success("Session has been reset!")
            st.rerun()
        
        # Information section
        st.write("## How To Play")
        st.markdown("""
        1. **Set your bankroll** using the slider above
        2. **Select chips** to use for betting
        3. **Place bets** by clicking on the roulette board
        4. **Spin the wheel** to see if you win
        5. **Try different strategies** with agent recommendations

        **Bet Types and Payouts:**
        1. **Red/Black, Odd/Even, High/Low** – Pays 1 to 1
        2. **Dozen/Column Bets** – Pays 2 to 1
        3. **Six Line** (6 numbers) – Pays 5 to 1
        4. **Top Line** (0, 00, 1, 2, 3) – Pays 6 to 1
        5. **Corner Bet** (4 numbers) – Pays 8 to 1
        6. **Street Bet** (3 numbers) – Pays 11 to 1
        7. **Split Bet** (2 numbers) – Pays 17 to 1
        8. **Straight Bet** (1 number) – Pays 35 to 1
        """)
    
    # Display balance, controls, and bet info at the top
    # Row 1: Balance, Bet Info, and Spin
    top_row1 = st.columns([2, 2, 2, 3])
    
    # Balance display
    top_row1[0].metric(
        "Balance", 
        f"${st.session_state.simulator.balance:.2f}", 
        f"{st.session_state.simulator.get_summary_stats()['net_profit']:.2f}"
    )
    
    # Current bets display
    total_bet = st.session_state.simulator.get_total_bet_amount()
    potential_win = st.session_state.simulator.get_potential_win()
    
    top_row1[1].metric("Total Bet", f"${total_bet:.2f}")
    top_row1[2].metric("Potential Win", f"${potential_win:.2f}" if potential_win > 0 else "$0.00")
    
    # Spin button and manual input
    spin_cols = top_row1[3].columns([1, 2])
    if spin_cols[0].button("SPIN", key="btn_spin_top", use_container_width=True, type="primary"):
        try:
            result = spin_wheel()
            st.success(f"Spin result: {result}")
            # No rerun needed - let the page update naturally
        except Exception as e:
            st.error(f"Error during spin: {str(e)}")
    
    # Manual input for live casino numbers
    manual_num = spin_cols[1].text_input("", key="manual_number_top", 
                                       placeholder="Enter number to add...")
    if manual_num:
        try:
            # Try to convert to integer
            num = int(manual_num)
            # Validate the number is on the wheel
            if (num >= 0 and num <= 36) or (num == 00 and st.session_state.simulator.roulette_type == "American"):
                update_spins_df(num, manually_added=True)
                st.success(f"Added number {num} to history!")
                st.rerun()
            else:
                st.error("Invalid roulette number!")
        except ValueError:
            st.error("Please enter a valid number!")
    
    # Row 2: Chip Selection
    top_row2 = st.columns([1, 5])
    
    # Chip selection
    top_row2[0].write("**Chip:**")
    chip_options = st.session_state.simulator.get_chip_options()
    chip_cols = top_row2[1].columns(len(chip_options))
    
    for i, value in enumerate(chip_options):
        chip_color = get_chip_color(value)
        if chip_cols[i].button(
            f"${value}",
            key=f"chip_{value}",
            use_container_width=True,
            type="primary" if st.session_state.current_bet_amount == value else "secondary"
        ):
            st.session_state.current_bet_amount = value
            st.rerun()
    
    # Create tabs for main game vs analysis
    tab1, tab2, tab3 = st.tabs(["Game", "Recommendations", "Analysis"])
    
    with tab1:
        # Create the roulette board
        create_roulette_board()
        
        # Show spin history
        create_spin_history_display()
        
        # Basic session stats
        create_session_stats()
    
    with tab2:
        # Recommendations from agent based on history
        create_recommendation_display()
        
        # Strategy performance
        create_strategy_performance_display()
        
        # If we have enough spins, show specific bet recommendations
        if hasattr(st.session_state, 'agent') and len(st.session_state.spins_df) >= 5:
            st.write("### Specific Bet Recommendations")
            
            recommendations = st.session_state.agent.get_specific_bet_recommendations(
                st.session_state.spins_df
            )
            
            rec_cols = st.columns(3)
            
            if recommendations.get('number_bet'):
                rec = recommendations['number_bet']
                props = st.session_state.simulator.get_number_properties(rec['number'])
                color = props['color']
                text_color = "white" if color in ['black', 'green'] else "black"
                
                with rec_cols[0]:
                    st.markdown(
                        f"<div style='background-color: {color}; color: {text_color}; "
                        f"text-align: center; padding: 15px; margin-bottom: 10px; "
                        f"border-radius: 50%; width: 50px; height: 50px; line-height: 50px; "
                        f"margin: 0 auto;'>{rec['number']}</div>",
                        unsafe_allow_html=True
                    )
                    
                    st.write(f"**Straight Bet**<br>Confidence: {rec['confidence']:.1%}", unsafe_allow_html=True)
                    
                    if st.button("Place Number Bet", key="rec_number_bet"):
                        place_bet('straight', rec['number'])
                        st.rerun()
            
            if recommendations.get('color_bet'):
                rec = recommendations['color_bet']
                color = rec['color']
                text_color = "white" if color == 'black' else "black"
                
                with rec_cols[1]:
                    st.markdown(
                        f"<div style='background-color: {color}; color: {text_color}; "
                        f"text-align: center; padding: 15px; margin-bottom: 10px; "
                        f"border-radius: 5px; width: 100px; "
                        f"margin: 0 auto;'>{color.upper()}</div>",
                        unsafe_allow_html=True
                    )
                    
                    st.write(f"**Color Bet**<br>Confidence: {rec['confidence']:.1%}", unsafe_allow_html=True)
                    
                    if st.button("Place Color Bet", key="rec_color_bet"):
                        place_bet('color', rec['color'])
                        st.rerun()
            
            if recommendations.get('dozen_bet'):
                rec = recommendations['dozen_bet']
                dozen = rec['dozen']
                
                with rec_cols[2]:
                    st.markdown(
                        f"<div style='background-color: #0066cc; color: white; "
                        f"text-align: center; padding: 15px; margin-bottom: 10px; "
                        f"border-radius: 5px; width: 100px; "
                        f"margin: 0 auto;'>Dozen {dozen}</div>",
                        unsafe_allow_html=True
                    )
                    
                    st.write(f"**Dozen Bet**<br>Confidence: {rec['confidence']:.1%}", unsafe_allow_html=True)
                    
                    if st.button("Place Dozen Bet", key="rec_dozen_bet"):
                        place_bet('dozen', dozen)
                        st.rerun()
    
    with tab3:
        # Advanced pattern analysis
        create_advanced_analysis()
        
        # Show full statistics
        if not st.session_state.spins_df.empty:
            st.write("### Number Distribution")
            
            # Create a count of number occurrences
            number_counts = st.session_state.spins_df['number'].value_counts().reset_index()
            number_counts.columns = ['number', 'count']
            
            # Sort by number
            number_counts = number_counts.sort_values('number')
            
            # Create a bar chart
            fig = px.bar(
                number_counts,
                x='number',
                y='count',
                color='count',
                labels={'number': 'Roulette Number', 'count': 'Frequency'},
                title="Number Frequency Distribution"
            )
            
            # Add a horizontal line at the expected frequency
            expected_freq = len(st.session_state.spins_df) / 37  # (or 38 for American roulette)
            fig.add_hline(
                y=expected_freq,
                line_dash="dash",
                line_color="red",
                annotation_text="Expected"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show frequency distribution charts for various bet types
            col1, col2 = st.columns(2)
            
            with col1:
                # Red/Black distribution
                color_counts = st.session_state.spins_df['color'].value_counts()
                
                # Create pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=color_counts.index,
                    values=color_counts.values,
                    hole=.4,
                    marker=dict(colors=['red', 'black', 'green'])
                )])
                
                fig.update_layout(title_text="Color Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Odd/Even distribution
                parity_counts = st.session_state.spins_df['parity'].value_counts()
                
                # Create pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=parity_counts.index,
                    values=parity_counts.values,
                    hole=.4
                )])
                
                fig.update_layout(title_text="Odd/Even Distribution")
                st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()