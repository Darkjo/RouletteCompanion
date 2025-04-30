"""
Interactive Roulette Simulation App
Provides a visual interface for placing and evaluating roulette bets.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import random
import time
from PIL import Image
import os
import json
from typing import Dict, List, Tuple, Set, Union

from utils.simulation import RouletteSimulator, RouletteBet
from utils.agent import RLAgent
from utils.advanced_betting import AdvancedBettingAnalysis

# Set page config
st.set_page_config(
    page_title="Roulette Simulator",
    page_icon="🎰",
    layout="wide"
)

# Initialize session state
if 'simulator' not in st.session_state:
    st.session_state.simulator = RouletteSimulator()
if 'agent' not in st.session_state:
    st.session_state.agent = RLAgent()
if 'advanced_analysis' not in st.session_state:
    st.session_state.advanced_analysis = AdvancedBettingAnalysis()
if 'current_chip' not in st.session_state:
    st.session_state.current_chip = 1.0
if 'spins_df' not in st.session_state:
    st.session_state.spins_df = pd.DataFrame(columns=['number', 'color', 'parity', 'range', 'dozen', 'column', 'timestamp'])
if 'win_history' not in st.session_state:
    st.session_state.win_history = []
if 'strategy_performance' not in st.session_state:
    st.session_state.strategy_performance = {}

# Helper functions
def get_chip_color(value: float) -> str:
    """Get a color for a chip based on its value."""
    colors = {
        0.1: "#B0E0E6",    # Light blue
        0.5: "#FF7F50",     # Coral
        1: "#FFFFFF",       # White
        5: "#FF0000",       # Red
        10: "#0000FF",      # Blue
        25: "#008000",      # Green
        50: "#FFA500",      # Orange
        100: "#800080",     # Purple
        500: "#000000"      # Black
    }
    return colors.get(value, "#CCCCCC")

def update_spins_df(number: Union[int, str], manually_added: bool = False):
    """Update the spins dataframe with a new result."""
    props = st.session_state.simulator.get_number_properties(number)
    
    # Add row to DataFrame
    new_row = pd.DataFrame([{
        'number': str(number),
        'color': props['color'],
        'parity': props['parity'] if props['parity'] else 'none',
        'range': props['range'] if props['range'] else 'none',
        'dozen': props['dozen'] if props['dozen'] else 'none',
        'column': props['column'] if props['column'] else 'none',
        'timestamp': pd.Timestamp.now()
    }])
    
    st.session_state.spins_df = pd.concat([st.session_state.spins_df, new_row], ignore_index=True)
    
    # If this is a manually added number, check if there are active bets to settle
    if manually_added and st.session_state.simulator.active_bets:
        # Calculate winnings for the manual result
        winnings = 0
        won_bets = []
        lost_bets = []
        
        for bet in st.session_state.simulator.active_bets:
            if number in bet.numbers or str(number) in bet.numbers:
                # Bet wins
                winning_amount = bet.get_winning_amount()
                winnings += winning_amount
                won_bets.append(bet)
            else:
                # Bet loses
                lost_bets.append(bet)
        
        # Update balance
        st.session_state.simulator.balance += winnings
        
        # If balance is less than or equal to 0, set it to 0
        if st.session_state.simulator.balance <= 0:
            st.session_state.simulator.balance = 0
        
        # Store result in history
        st.session_state.simulator.spin_history.append({
            'result': number,
            'winnings': winnings,
            'won_bets': won_bets,
            'lost_bets': lost_bets
        })
        
        # Update win history
        st.session_state.win_history.append({
            'number': str(number),
            'winnings': winnings,
            'bets_placed': len(won_bets) + len(lost_bets),
            'bets_won': len(won_bets)
        })
        
        # Clear active bets for next round
        st.session_state.simulator.active_bets = []
        
        # Show result message
        if winnings > 0:
            st.success(f"You won ${winnings:.2f}! {len(won_bets)} bet(s) won.")
        else:
            st.warning(f"No winners this time. All {len(lost_bets)} bet(s) lost.")

def spin_wheel():
    """Spin the roulette wheel and process results."""
    if not st.session_state.simulator.active_bets:
        st.warning("Please place at least one bet first!")
        return
    
    # Spin the wheel
    result = st.session_state.simulator.spin()
    
    # Update spin history
    update_spins_df(result)
    
    # Get last result details
    last_result = st.session_state.simulator.get_last_result_details()
    
    # Update win history
    st.session_state.win_history.append({
        'number': str(result),
        'winnings': last_result['winnings'],
        'bets_placed': len(last_result['won_bets']) + len(last_result['lost_bets']),
        'bets_won': len(last_result['won_bets'])
    })
    
    # Update the agent's knowledge
    if hasattr(st.session_state, 'agent'):
        # Record if the agent's recommendation was followed
        last_recommendations = st.session_state.get('last_recommendations', {})
        for bet_type, bet_rec in last_recommendations.items():
            if bet_type == 'single_numbers' and bet_rec:
                for num_rec in bet_rec:
                    if str(num_rec.get('number')) == str(result):
                        st.session_state.agent.record_alignment(True)
                        break
                else:
                    st.session_state.agent.record_alignment(False)
            
            # Record bet result for strategy performance tracking
            if bet_type in ['red_black', 'even_odd', 'high_low', 'dozens', 'columns']:
                if bet_type not in st.session_state.strategy_performance:
                    st.session_state.strategy_performance[bet_type] = {'wins': 0, 'losses': 0}
                
                if bet_rec and bet_rec.get('recommendation'):
                    # Check if this strategy would have won
                    props = st.session_state.simulator.get_number_properties(result)
                    would_win = False
                    
                    if bet_type == 'red_black' and props['color'] == bet_rec.get('recommendation').lower():
                        would_win = True
                    elif bet_type == 'even_odd' and props['parity'] == bet_rec.get('recommendation').lower():
                        would_win = True
                    elif bet_type == 'high_low' and props['range'] == bet_rec.get('recommendation').lower():
                        would_win = True
                    elif bet_type == 'dozens':
                        recommended_dozen = bet_rec.get('recommendation')
                        if (recommended_dozen == '1st dozen' and props['dozen'] == 1 or
                            recommended_dozen == '2nd dozen' and props['dozen'] == 2 or
                            recommended_dozen == '3rd dozen' and props['dozen'] == 3):
                            would_win = True
                    elif bet_type == 'columns':
                        recommended_column = bet_rec.get('recommendation')
                        if (recommended_column == '1st column' and props['column'] == 1 or
                            recommended_column == '2nd column' and props['column'] == 2 or
                            recommended_column == '3rd column' and props['column'] == 3):
                            would_win = True
                    
                    # Update strategy performance stats
                    if would_win:
                        st.session_state.strategy_performance[bet_type]['wins'] += 1
                    else:
                        st.session_state.strategy_performance[bet_type]['losses'] += 1

def place_bet(bet_type, *args):
    """Place a bet of the specified type."""
    chip_value = st.session_state.current_chip
    bet_description = ""
    
    # Call the appropriate method based on bet type
    if bet_type == 'straight':
        number = args[0]
        success = st.session_state.simulator.add_straight_bet(number, chip_value)
        bet_description = f"straight bet on number {number}"
    elif bet_type == 'split':
        num1, num2 = args
        success = st.session_state.simulator.add_split_bet(num1, num2, chip_value)
        bet_description = f"split bet on numbers {num1} and {num2}"
    elif bet_type == 'street':
        row = args[0]
        success = st.session_state.simulator.add_street_bet(row, chip_value)
        bet_description = f"street bet on row {row}"
    elif bet_type == 'corner':
        corner = args[0]
        success = st.session_state.simulator.add_corner_bet(corner, chip_value)
        bet_description = f"corner bet on corner {corner}"
    elif bet_type == 'six_line':
        line = args[0]
        success = st.session_state.simulator.add_six_line_bet(line, chip_value)
        bet_description = f"six line bet on line {line}"
    elif bet_type == 'top_line':
        success = st.session_state.simulator.add_top_line_bet(chip_value)
        bet_description = "top line bet on 0, 00, 1, 2, 3"
    elif bet_type == 'color':
        color = args[0]
        success = st.session_state.simulator.add_color_bet(color, chip_value)
        bet_description = f"bet on {color}"
    elif bet_type == 'parity':
        parity = args[0]
        success = st.session_state.simulator.add_parity_bet(parity, chip_value)
        bet_description = f"bet on {parity} numbers"
    elif bet_type == 'range':
        range_type = args[0]
        success = st.session_state.simulator.add_range_bet(range_type, chip_value)
        bet_description = f"bet on {range_type} range"
    elif bet_type == 'dozen':
        dozen = args[0]
        success = st.session_state.simulator.add_dozen_bet(dozen, chip_value)
        bet_description = f"bet on {dozen}{'st' if dozen == 1 else 'nd' if dozen == 2 else 'rd'} dozen"
    elif bet_type == 'column':
        column = args[0]
        success = st.session_state.simulator.add_column_bet(column, chip_value)
        bet_description = f"bet on {column}{'st' if column == 1 else 'nd' if column == 2 else 'rd'} column"
    else:
        success = False
    
    if success:
        # Show a success message with bet details
        chip_display = f"${chip_value:.2f}" if chip_value < 1 or chip_value != int(chip_value) else f"${int(chip_value)}"
        st.success(f"Placed {chip_display} {bet_description}")
    else:
        st.warning(f"Couldn't place bet. Check your balance!")

def create_roulette_board():
    """Create an interactive roulette board."""
    simulator = st.session_state.simulator
    roulette_type = simulator.roulette_type
    
    # Main title
    st.write("## Roulette Board")
    
    # Create a fully interactive roulette board with clickable elements
    html_board = """
    <style>
        .roulette-board {
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #006400;
            border-radius: 10px;
            font-family: Arial, sans-serif;
            color: white;
            box-shadow: 0 0 15px rgba(0,0,0,0.5);
        }
        
        .board-grid {
            display: grid;
            grid-template-columns: 50px repeat(12, 1fr);
            grid-template-rows: repeat(3, 60px);
            gap: 3px;
            margin-bottom: 10px;
        }
        
        .number {
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            font-size: 18px;
            border-radius: 5px;
            cursor: pointer;
            position: relative;
            transition: transform 0.1s ease;
        }
        
        .number:hover {
            transform: scale(1.05);
            box-shadow: 0 0 5px rgba(255,255,255,0.5);
        }
        
        .red { background-color: #ff0000; }
        .black { background-color: #000; }
        .green { background-color: #006400; }
        
        .zero {
            grid-row: 1 / span 3;
            grid-column: 1;
            border-radius: 5px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            font-size: 20px;
            border: 1px solid white;
            cursor: pointer;
        }
        
        .zero:hover {
            background-color: #008800;
        }
        
        .column-bet {
            background-color: #0066cc;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            border-radius: 5px;
            cursor: pointer;
        }
        
        .column-bet:hover {
            background-color: #0088ff;
        }
        
        .outside-bets {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 5px;
            margin-bottom: 10px;
        }
        
        .dozen-bets {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 5px;
            margin-bottom: 10px;
        }
        
        .outside-bet, .dozen-bet {
            padding: 10px;
            text-align: center;
            background-color: #333;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        
        .outside-bet:hover, .dozen-bet:hover {
            background-color: #555;
        }
        
        .dozen-bet {
            background-color: #0066cc;
        }
        
        .chip {
            position: absolute;
            top: 5px;
            right: 5px;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            font-size: 10px;
            display: flex;
            justify-content: center;
            align-items: center;
            border: 2px dashed gold;
            background-color: white;
            color: black;
            font-weight: bold;
        }
        
        .bet-types {
            background-color: rgba(0, 0, 0, 0.5);
            padding: 10px;
            border-radius: 5px;
            margin-top: 15px;
            font-size: 12px;
            text-align: center;
        }
    </style>
    
    <div class="roulette-board">
        <div class="board-grid">
            <!-- Zero pocket -->
            <div class="zero green" onclick="placeBet('straight', 0)">0</div>
    """
    
    # Generate number cells for first row (1, 4, 7, etc.)
    for num in range(1, 37, 3):
        color = "red" if num % 2 == 1 else "black"
        
        # Check if there's a bet on this number
        has_bet = False
        bet_amount = ""
        for bet in st.session_state.simulator.active_bets:
            if num in bet.numbers and len(bet.numbers) == 1:
                has_bet = True
                bet_amount = str(bet.amount)
                break
        
        # Add cell with or without chip
        if has_bet:
            html_board += f"""
            <div class="number {color}" onclick="window.parent.postMessage({{type: 'bet_click', bet: 'straight', number: {num}}}, '*')">
                {num}
                <div class="chip">${bet_amount}</div>
            </div>
            """
        else:
            html_board += f"""
            <div class="number {color}" onclick="window.parent.postMessage({{type: 'bet_click', bet: 'straight', number: {num}}}, '*')">
                {num}
            </div>
            """
    
    # Add first column bet
    html_board += """
    <div class="column-bet" onclick="placeBet('column', 1)">2:1</div>
    """
    
    # Generate number cells for second row (2, 5, 8, etc.)
    for num in range(2, 37, 3):
        color = "red" if num % 2 == 1 else "black"
        
        # Check if there's a bet on this number
        has_bet = False
        bet_amount = ""
        for bet in st.session_state.simulator.active_bets:
            if num in bet.numbers and len(bet.numbers) == 1:
                has_bet = True
                bet_amount = str(bet.amount)
                break
        
        # Add cell with or without chip
        if has_bet:
            html_board += f"""
            <div class="number {color}" onclick="window.parent.postMessage({{type: 'bet_click', bet: 'straight', number: {num}}}, '*')">
                {num}
                <div class="chip">${bet_amount}</div>
            </div>
            """
        else:
            html_board += f"""
            <div class="number {color}" onclick="window.parent.postMessage({{type: 'bet_click', bet: 'straight', number: {num}}}, '*')">
                {num}
            </div>
            """
    
    # Add second column bet
    html_board += """
    <div class="column-bet" onclick="placeBet('column', 2)">2:1</div>
    """
    
    # Generate number cells for third row (3, 6, 9, etc.)
    for num in range(3, 37, 3):
        color = "red" if num % 2 == 1 else "black"
        
        # Check if there's a bet on this number
        has_bet = False
        bet_amount = ""
        for bet in st.session_state.simulator.active_bets:
            if num in bet.numbers and len(bet.numbers) == 1:
                has_bet = True
                bet_amount = str(bet.amount)
                break
        
        # Add cell with or without chip
        if has_bet:
            html_board += f"""
            <div class="number {color}" onclick="window.parent.postMessage({{type: 'bet_click', bet: 'straight', number: {num}}}, '*')">
                {num}
                <div class="chip">${bet_amount}</div>
            </div>
            """
        else:
            html_board += f"""
            <div class="number {color}" onclick="window.parent.postMessage({{type: 'bet_click', bet: 'straight', number: {num}}}, '*')">
                {num}
            </div>
            """
    
    # Add third column bet (moved to after the numbers 34, 35, 36)
    html_board += """
    <div class="column-bet" onclick="placeBet('column', 3)">2:1</div>
    """
    
    # Close the board grid
    html_board += """
        </div>
        
        <!-- Dozen bets -->
        <div class="dozen-bets">
            <div class="dozen-bet" onclick="placeBet('dozen', 1)">1st Dozen (1-12)</div>
            <div class="dozen-bet" onclick="placeBet('dozen', 2)">2nd Dozen (13-24)</div>
            <div class="dozen-bet" onclick="placeBet('dozen', 3)">3rd Dozen (25-36)</div>
        </div>
        
        <!-- Outside bets -->
        <div class="outside-bets">
            <div class="outside-bet" onclick="placeBet('range', 'low')">1-18</div>
            <div class="outside-bet" onclick="placeBet('parity', 'even')">EVEN</div>
            <div class="outside-bet" onclick="placeBet('color', 'red')">RED</div>
            <div class="outside-bet" onclick="placeBet('color', 'black')">BLACK</div>
            <div class="outside-bet" onclick="placeBet('parity', 'odd')">ODD</div>
            <div class="outside-bet" onclick="placeBet('range', 'high')">19-36</div>
        </div>
        
        <!-- Bet types legend -->
        <div class="bet-types">
            <p><strong>Bet Types:</strong> A = Straight (35:1) | B = Split (17:1) | C = Street (11:1) | D = Corner (8:1) | E = Five Number (6:1)</p>
            <p>F = Six Line (5:1) | G/H = Column (2:1) | I = Dozen (2:1) | J/K = Even Money (1:1)</p>
        </div>
    </div>
    
    <script>
        // Enhanced message handler with better debugging
        function placeBet(betType, number) {
            console.log('Sending bet to parent:', betType, number);
            
            try {
                // First try the standard postMessage approach
                window.parent.postMessage({
                    type: 'bet_click',
                    bet: betType,
                    number: number
                }, '*');
                
                // As a fallback, also manually create and submit a form
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = window.location.href;
                
                // Add hidden fields with the bet data
                const betTypeField = document.createElement('input');
                betTypeField.type = 'hidden';
                betTypeField.name = 'bet_type';
                betTypeField.value = betType;
                form.appendChild(betTypeField);
                
                const numberField = document.createElement('input');
                numberField.type = 'hidden';
                numberField.name = 'bet_number';
                numberField.value = number;
                form.appendChild(numberField);
                
                // Submit the form to reload the page with the bet
                document.body.appendChild(form);
                form.submit();
            } catch (e) {
                console.error('Error sending bet message:', e);
            }
        }
        
        // Update all onclick handlers to use our new function
        document.addEventListener('DOMContentLoaded', function() {
            // Get all elements with onclick handlers for betting
            const betElements = document.querySelectorAll('[onclick*="postMessage"]');
            
            // Replace their handlers with our new more robust function
            betElements.forEach(el => {
                const onclick = el.getAttribute('onclick');
                if (onclick) {
                    // Extract the bet type and number from the original handler
                    const matches = onclick.match(/bet:\s*'([^']+)'.*number:\s*([^,}]+)/);
                    if (matches && matches.length >= 3) {
                        const betType = matches[1];
                        const betNumber = matches[2];
                        
                        // Replace the handler with our new function
                        el.setAttribute('onclick', `placeBet('${betType}', ${betNumber})`);
                    }
                }
            });
        });
    </script>
    """
    
    # Register an event handler for board clicks using a custom component
    click_container = st.container()
    
    with click_container:
        # Create a custom component for handling click events
        # This uses Streamlit's component API directly
        st.markdown("""
        <script>
        // Setup a global event listener for messages from the board
        window.addEventListener('message', function(e) {
            if (e.data && e.data.type === 'bet_click') {
                // Log the click event
                console.log('Received bet click:', e.data);
                
                // Create a form to submit the data back to the server
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = window.location.href;
                
                // Add hidden fields with the bet data
                const betTypeField = document.createElement('input');
                betTypeField.type = 'hidden';
                betTypeField.name = 'bet_type';
                betTypeField.value = e.data.bet;
                form.appendChild(betTypeField);
                
                const numberField = document.createElement('input');
                numberField.type = 'hidden';
                numberField.name = 'bet_number';
                numberField.value = e.data.number;
                form.appendChild(numberField);
                
                // Submit the form to reload the page with the bet
                document.body.appendChild(form);
                form.submit();
            }
        });
        </script>
        """, unsafe_allow_html=True)
        
        # Store a hidden input for click parameter values
        bet_type = st.text_input("Bet Type", key="bet_type", value="", label_visibility="collapsed")
        bet_number = st.text_input("Bet Number", key="bet_number", value="", label_visibility="collapsed")
    
    # Create a callback for the interactive board
    interactive_board_handler = st.components.v1.html(html_board, height=600)
    
    # Process any clicks on the board (this happens on subsequent page loads)
    # Get form parameters from URL (Streamlit doesn't expose this directly, so we check session state)
    if 'bet_type' in st.session_state and st.session_state.bet_type:
        bet_type = st.session_state.bet_type
        number = st.session_state.bet_number
        
        # Place the bet based on the clicked element
        try:
            # For debugging in Streamlit console
            st.write(f"Debug - Received bet: type={bet_type}, number={number}")
            
            if bet_type == 'straight':
                place_bet('straight', int(number))
            elif bet_type == 'column':
                place_bet('column', int(number))
            elif bet_type == 'dozen':
                place_bet('dozen', int(number))
            elif bet_type == 'color':
                place_bet('color', number)
            elif bet_type == 'parity':
                place_bet('parity', number)
            elif bet_type == 'range':
                place_bet('range', number)
                
            # Clear the values after processing
            st.session_state.bet_type = ""
            st.session_state.bet_number = "" 
            
            # Success message
            st.success(f"Bet placed successfully!")
            
            # Force a rerun to update the UI with the new bet
            st.rerun()
        except Exception as e:
            st.error(f"Error processing bet: {str(e)}")

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
        spin_wheel()
    
    # Manual input for live casino numbers
    manual_num = spin_cols[1].text_input("", key="manual_number_top", 
                                        placeholder="Enter number (0-36 or 00)")
    if manual_num:
        # Validate the input
        valid_input = False
        if manual_num == "00":
            valid_input = True
        elif manual_num.isdigit() and 0 <= int(manual_num) <= 36:
            valid_input = True
        
        if valid_input:
            # Convert to correct type
            if manual_num == "00":
                result = "00"
            else:
                result = int(manual_num)
            
            # Update spin history with manual addition
            update_spins_df(result, manually_added=True)
        else:
            st.error("Invalid number. Enter 0-36 or 00.")
    
    # Row 2: Chip selection and control buttons
    top_row2 = st.columns([4, 1, 1])
    
    # Chip selection as buttons
    with top_row2[0]:
        chip_cols = st.columns(9)
        chip_values = [0.1, 0.5, 1, 5, 10, 25, 50, 100, 500]
        
        for i, value in enumerate(chip_values):
            # Format the display value
            display_value = f"${value:.1f}" if value < 1 else f"${int(value)}" if value == int(value) else f"${value:.1f}"
            
            # Create a button for each chip with visual indication of selection
            if chip_cols[i].button(
                display_value, 
                key=f"chip_btn_{value}",
                type="primary" if st.session_state.current_chip == value else "secondary",
                use_container_width=True
            ):
                st.session_state.current_chip = value
    
    # Undo and Clear buttons
    if top_row2[1].button("UNDO BET", key="btn_undo_bet_top", use_container_width=True, 
                    type="secondary", help="Remove the last bet placed"):
        if st.session_state.simulator.undo_last_bet():
            st.success("Last bet removed!")
        else:
            st.warning("No bets to undo.")
    
    if top_row2[2].button("CLEAR ALL", key="btn_clear_bets_top", use_container_width=True, 
                    type="secondary", help="Clear all active bets"):
        st.session_state.simulator.clear_bets()
        st.success("All bets cleared!")
    
    # Main area with tabs
    main_tabs = st.tabs(["Roulette Table", "Recommendations", "Analysis"])
    
    with main_tabs[0]:
        # Roulette board (includes chip selection)
        create_roulette_board()
        
        # Display active bets if there are any
        if st.session_state.simulator.active_bets:
            st.write("### Active Bets")
            
            # Create a table to display the active bets
            bet_data = []
            for bet in st.session_state.simulator.active_bets:
                # Format numbers for display
                numbers_str = ", ".join(str(n) for n in bet.numbers) if len(bet.numbers) <= 6 else f"{len(bet.numbers)} numbers"
                
                # Format bet type for display
                bet_type_display = bet.bet_type.replace('_', ' ').title()
                if bet.name:
                    bet_type_display = bet.name
                
                bet_data.append({
                    "Bet Type": bet_type_display,
                    "Amount": f"${bet.amount:.2f}",
                    "Covers": numbers_str,
                    "Payout": f"{bet.get_payout_multiplier()}:1",
                    "Win Amount": f"${bet.get_winning_amount():.2f}"
                })
            
            if bet_data:
                bet_df = pd.DataFrame(bet_data)
                st.dataframe(bet_df, use_container_width=True, hide_index=True)
        
        # No spin buttons here - they're now at the top of the page
        
        # Spin history
        create_spin_history_display()
    
    with main_tabs[1]:
        # Agent recommendations
        st.write("### Betting Recommendations")
        
        if not hasattr(st.session_state, 'agent') or st.session_state.spins_df.empty:
            st.info("Play more spins to get recommendations!")
        else:
            # Get recommendations from the agent
            recommendations = st.session_state.agent.get_specific_bet_recommendations(
                st.session_state.spins_df,
                st.session_state.simulator.roulette_type,
                st.session_state.simulator.balance
            )
            
            # Store recommendations for later evaluation
            st.session_state.last_recommendations = recommendations
            
            # Show recommendations with clear action buttons for quick betting
            st.write("**Single Numbers**")
            if recommendations['single_numbers']:
                for num_rec in recommendations['single_numbers']:
                    confidence = num_rec.get('confidence', 0)
                    number = num_rec['number']
                    
                    # Create a container for each recommendation with a bet button
                    num_cols = st.columns([3, 1])
                    
                    with num_cols[0]:
                        st.markdown(
                            f"<div style='display: flex; align-items: center;'>"
                            f"<span style='font-weight: bold; margin-right: 10px;'>Number {number}:</span>"
                            f"<div style='background: linear-gradient(to right, "
                            f"rgba(0,128,0,{confidence}) {int(confidence*100)}%, "
                            f"#f0f0f0 {int(confidence*100)}%); "
                            f"height: 20px; flex-grow: 1; border-radius: 5px;'></div>"
                            f"<span style='margin-left: 10px;'>{confidence:.2f}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    
                    # Add a button to place this bet
                    with num_cols[1]:
                        if st.button(f"Bet", key=f"bet_num_{number}"):
                            # Use current chip value to place this bet
                            if st.session_state.current_chip:
                                place_bet('straight', number)
                            else:
                                st.warning("Select a chip first")
            else:
                st.write("No single number recommendations")
            
            # Display outside bet recommendations
            st.write("**Outside Bets**")
            for bet_type in ['red_black', 'even_odd', 'high_low']:
                if bet_type in recommendations and recommendations[bet_type].get('recommendation'):
                    rec = recommendations[bet_type]
                    confidence = rec.get('confidence', 0)
                    recommendation = rec['recommendation']
                    bet_name = bet_type.replace('_', ' ').title()
                    
                    # Create a container with bet button
                    out_cols = st.columns([3, 1])
                    
                    with out_cols[0]:
                        st.markdown(
                            f"<div style='display: flex; align-items: center;'>"
                            f"<span style='font-weight: bold; margin-right: 10px;'>{bet_name}:</span>"
                            f"<span style='margin-right: 10px;'>{recommendation}</span>"
                            f"<div style='background: linear-gradient(to right, "
                            f"rgba(0,128,0,{confidence}) {int(confidence*100)}%, "
                            f"#f0f0f0 {int(confidence*100)}%); "
                            f"height: 20px; flex-grow: 1; border-radius: 5px;'></div>"
                            f"<span style='margin-left: 10px;'>{confidence:.2f}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    
                    # Add a button to place this bet
                    with out_cols[1]:
                        if st.button(f"Bet", key=f"bet_{bet_type}_{recommendation}"):
                            # Use current chip value to place this bet
                            if st.session_state.current_chip:
                                if bet_type == 'red_black':
                                    place_bet('color', recommendation.lower())
                                elif bet_type == 'even_odd':
                                    place_bet('parity', recommendation.lower())
                                elif bet_type == 'high_low':
                                    place_bet('range', recommendation.lower())
                            else:
                                st.warning("Select a chip first")
    
    with main_tabs[2]:
        # Create columns for stats
        analysis_cols = st.columns(2)
        
        with analysis_cols[0]:
            # Session stats - simplified
            create_session_stats()
        
        with analysis_cols[1]:
            # Advanced analysis components
            if len(st.session_state.spins_df) >= 10:
                st.write("### Wheel Sector Analysis")
                sector_analysis = st.session_state.advanced_analysis.analyze_sectors(
                    st.session_state.spins_df,
                    st.session_state.simulator.roulette_type
                )
                
                if sector_analysis and 'sectors' in sector_analysis:
                    sector_data = []
                    for sector in sector_analysis['sectors']:
                        sector_data.append({
                            'Sector': sector['name'],
                            'Frequency': f"{sector['frequency']:.1%}",
                            'Expected': f"{sector['expected']:.1%}",
                            'Difference': sector['frequency'] - sector['expected']
                        })
                    
                    if sector_data:
                        sector_df = pd.DataFrame(sector_data)
                        sector_df = sector_df.sort_values('Difference', ascending=False)
                        st.dataframe(sector_df, use_container_width=True, hide_index=True)
        
        # Display sleeper numbers as these are most useful
        if len(st.session_state.spins_df) >= 10:
            st.write("### Sleeper Numbers Analysis")
            sleepers = st.session_state.advanced_analysis.get_sleeper_numbers(
                st.session_state.spins_df,
                st.session_state.simulator.roulette_type
            )
            
            if sleepers and 'numbers' in sleepers:
                st.write("Numbers that haven't appeared for a while:")
                
                sleeper_cols = st.columns(min(5, len(sleepers['numbers'])))
                for i, sleeper in enumerate(sleepers['numbers']):
                    number = sleeper.get('number')
                    absence = sleeper.get('spins_absent', 0)
                    props = st.session_state.simulator.get_number_properties(int(number) if number.isdigit() else number)
                    color = props['color']
                    text_color = "white" if color in ['black', 'green'] else "black"
                    
                    sleeper_cols[i].markdown(
                        f"<div style='background-color: {color}; color: {text_color}; "
                        f"text-align: center; padding: 10px; border-radius: 50%; width: 100%; margin-bottom: 5px;'>"
                        f"{number}</div>"
                        f"<div style='text-align: center;'>Missing for {absence} spins</div>",
                        unsafe_allow_html=True
                    )

if __name__ == "__main__":
    main()