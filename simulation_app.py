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
    
    # Use simple HTML table approach to avoid comments showing up
    html_board = """
    <style>
        /* Table-based roulette styling */
        .roulette-table {
            border-collapse: collapse;
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
            background-color: #006400;
            color: white;
            font-family: sans-serif;
            border: 3px solid #333;
        }
        
        .zero-cell {
            background-color: #006400;
            text-align: center;
            font-weight: bold;
            width: 40px;
            border: 1px solid white;
            height: 120px;
        }
        
        .number-cell {
            width: 40px;
            height: 40px;
            text-align: center;
            font-weight: bold;
            border: 1px solid white;
        }
        
        .red-cell {
            background-color: #ff0000;
        }
        
        .black-cell {
            background-color: #000000;
        }
        
        .column-cell {
            background-color: #0066cc;
            text-align: center;
            border: 1px solid white;
            height: 30px;
        }
        
        .dozens-row td {
            background-color: #0066cc;
            text-align: center;
            border: 1px solid white;
            height: 40px;
        }
        
        .outside-row td {
            background-color: #333;
            text-align: center;
            border: 1px solid white;
            height: 40px;
        }
        
        .bet-legend {
            margin-top: 15px;
            background-color: rgba(0,0,0,0.5);
            padding: 10px;
            text-align: center;
            border-radius: 5px;
        }
        
        .chip {
            display: inline-block;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-left: 3px;
            line-height: 16px;
            font-size: 8px;
            text-align: center;
            background-color: white;
            color: black;
            border: 1px solid #333;
        }
    </style>
    
    <table class="roulette-table">
        <tr>
            <td rowspan="3" class="zero-cell">0</td>
    """
    
    # Add the first row - numbers 1, 4, 7, etc.
    html_board += "<tr>"
    for num in range(1, 37, 3):
        # Determine cell color (odd=red, even=black)
        color_class = "red-cell" if num % 2 == 1 else "black-cell"
        
        # Check if there's a bet on this number
        has_bet = False
        bet_amount = ""
        for bet in st.session_state.simulator.active_bets:
            if num in bet.numbers and len(bet.numbers) == 1:
                has_bet = True
                bet_amount = str(bet.amount)
                break
        
        # Add chip indicator if there's a bet
        if has_bet:
            html_board += f'<td class="number-cell {color_class}">{num}<span class="chip">${bet_amount}</span></td>'
        else:
            html_board += f'<td class="number-cell {color_class}">{num}</td>'
    
    # Add column bet cell
    html_board += '<td class="column-cell">2:1</td></tr>'
    
    # Add the second row - numbers 2, 5, 8, etc.
    html_board += "<tr>"
    for num in range(2, 37, 3):
        # Determine cell color (odd=red, even=black)
        color_class = "red-cell" if num % 2 == 1 else "black-cell"
        
        # Check if there's a bet on this number
        has_bet = False
        bet_amount = ""
        for bet in st.session_state.simulator.active_bets:
            if num in bet.numbers and len(bet.numbers) == 1:
                has_bet = True
                bet_amount = str(bet.amount)
                break
        
        # Add chip indicator if there's a bet
        if has_bet:
            html_board += f'<td class="number-cell {color_class}">{num}<span class="chip">${bet_amount}</span></td>'
        else:
            html_board += f'<td class="number-cell {color_class}">{num}</td>'
    
    # Add column bet cell
    html_board += '<td class="column-cell">2:1</td></tr>'
    
    # Add the third row - numbers 3, 6, 9, etc.
    html_board += "<tr>"
    for num in range(3, 37, 3):
        # Determine cell color (odd=red, even=black)
        color_class = "red-cell" if num % 2 == 1 else "black-cell"
        
        # Check if there's a bet on this number
        has_bet = False
        bet_amount = ""
        for bet in st.session_state.simulator.active_bets:
            if num in bet.numbers and len(bet.numbers) == 1:
                has_bet = True
                bet_amount = str(bet.amount)
                break
        
        # Add chip indicator if there's a bet
        if has_bet:
            html_board += f'<td class="number-cell {color_class}">{num}<span class="chip">${bet_amount}</span></td>'
        else:
            html_board += f'<td class="number-cell {color_class}">{num}</td>'
    
    # Add column bet cell
    html_board += '<td class="column-cell">2:1</td></tr>'
    
    # Add dozens row
    html_board += """
        <tr class="dozens-row">
            <td colspan="4">1st Dozen (1-12)</td>
            <td colspan="4">2nd Dozen (13-24)</td>
            <td colspan="4">3rd Dozen (25-36)</td>
            <td></td>
        </tr>
    """
    
    # Add outside bets rows (2 rows with 3 bets each)
    html_board += """
        <tr class="outside-row">
            <td colspan="2">1-18</td>
            <td colspan="2">EVEN</td>
            <td colspan="2">RED</td>
            <td colspan="2">BLACK</td>
            <td colspan="2">ODD</td>
            <td colspan="2">19-36</td>
            <td></td>
        </tr>
    """
    
    # Close the table and add bet legend
    html_board += """
    </table>
    
    <div class="bet-legend">
        <p><strong>Bet Types:</strong> A = Straight (35:1) | B = Split (17:1) | C = Street (11:1) | D = Corner (8:1) | E = Five Number (6:1)</p>
        <p>F = Six Line (5:1) | G/H = Column (2:1) | I = Dozen (2:1) | J/K = Even Money (1:1)</p>
    </div>
    """
    
    # Display the visual board
    st.markdown(html_board, unsafe_allow_html=True)
    
    # Horizontal line separator
    st.markdown("---")
    
    # Now create the actual betting interface
    st.write("## Place Your Bets")
    
    # Zero section for betting
    st.write("### Zero Section")
    zero_container = st.container()
    
    # Use a single row of columns for zero section
    zero_betting = st.columns(3)
    
    with zero_betting[0]:
        if st.button("Bet on 0", key="btn_0", use_container_width=True, 
                   help="Straight bet on 0"):
            place_bet('straight', 0)
    
    # Only show 00 option for American roulette
    with zero_betting[1]:
        if roulette_type == 'American':
            if st.button("Bet on 00", key="btn_00", use_container_width=True,
                       help="Straight bet on 00"):
                place_bet('straight', '00')
    
    with zero_betting[2]:
        if st.button("Top Line Bet", key="place_top_line", use_container_width=True,
                   help="Bet on 0, 00, 1, 2, 3 (pays 6:1)"):
            place_bet('top_line')
    
    # Straight number bets
    st.write("### Number Bets")
    
    # Display row 1 numbers (1-12)
    st.write("**Row 1:** 1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34")
    
    # Use buttons in groups to avoid nesting issues
    row1_betting = st.columns(4)
    
    with row1_betting[0]:
        if st.button("Bet on 1", key="btn_1", use_container_width=True):
            place_bet('straight', 1)
        if st.button("Bet on 4", key="btn_4", use_container_width=True):
            place_bet('straight', 4)
        if st.button("Bet on 7", key="btn_7", use_container_width=True):
            place_bet('straight', 7)
    
    with row1_betting[1]:
        if st.button("Bet on 10", key="btn_10", use_container_width=True):
            place_bet('straight', 10)
        if st.button("Bet on 13", key="btn_13", use_container_width=True):
            place_bet('straight', 13)
        if st.button("Bet on 16", key="btn_16", use_container_width=True):
            place_bet('straight', 16)
    
    with row1_betting[2]:
        if st.button("Bet on 19", key="btn_19", use_container_width=True):
            place_bet('straight', 19)
        if st.button("Bet on 22", key="btn_22", use_container_width=True):
            place_bet('straight', 22)
        if st.button("Bet on 25", key="btn_25", use_container_width=True):
            place_bet('straight', 25)
    
    with row1_betting[3]:
        if st.button("Bet on 28", key="btn_28", use_container_width=True):
            place_bet('straight', 28)
        if st.button("Bet on 31", key="btn_31", use_container_width=True):
            place_bet('straight', 31)
        if st.button("Bet on 34", key="btn_34", use_container_width=True):
            place_bet('straight', 34)
    
    # Display row 2 numbers (2-35)
    st.write("**Row 2:** 2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35")
    
    row2_betting = st.columns(4)
    
    with row2_betting[0]:
        if st.button("Bet on 2", key="btn_2", use_container_width=True):
            place_bet('straight', 2)
        if st.button("Bet on 5", key="btn_5", use_container_width=True):
            place_bet('straight', 5)
        if st.button("Bet on 8", key="btn_8", use_container_width=True):
            place_bet('straight', 8)
    
    with row2_betting[1]:
        if st.button("Bet on 11", key="btn_11", use_container_width=True):
            place_bet('straight', 11)
        if st.button("Bet on 14", key="btn_14", use_container_width=True):
            place_bet('straight', 14)
        if st.button("Bet on 17", key="btn_17", use_container_width=True):
            place_bet('straight', 17)
    
    with row2_betting[2]:
        if st.button("Bet on 20", key="btn_20", use_container_width=True):
            place_bet('straight', 20)
        if st.button("Bet on 23", key="btn_23", use_container_width=True):
            place_bet('straight', 23)
        if st.button("Bet on 26", key="btn_26", use_container_width=True):
            place_bet('straight', 26)
    
    with row2_betting[3]:
        if st.button("Bet on 29", key="btn_29", use_container_width=True):
            place_bet('straight', 29)
        if st.button("Bet on 32", key="btn_32", use_container_width=True):
            place_bet('straight', 32)
        if st.button("Bet on 35", key="btn_35", use_container_width=True):
            place_bet('straight', 35)
    
    # Display row 3 numbers (3-36)
    st.write("**Row 3:** 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36")
    
    row3_betting = st.columns(4)
    
    with row3_betting[0]:
        if st.button("Bet on 3", key="btn_3", use_container_width=True):
            place_bet('straight', 3)
        if st.button("Bet on 6", key="btn_6", use_container_width=True):
            place_bet('straight', 6)
        if st.button("Bet on 9", key="btn_9", use_container_width=True):
            place_bet('straight', 9)
    
    with row3_betting[1]:
        if st.button("Bet on 12", key="btn_12", use_container_width=True):
            place_bet('straight', 12)
        if st.button("Bet on 15", key="btn_15", use_container_width=True):
            place_bet('straight', 15)
        if st.button("Bet on 18", key="btn_18", use_container_width=True):
            place_bet('straight', 18)
    
    with row3_betting[2]:
        if st.button("Bet on 21", key="btn_21", use_container_width=True):
            place_bet('straight', 21)
        if st.button("Bet on 24", key="btn_24", use_container_width=True):
            place_bet('straight', 24)
        if st.button("Bet on 27", key="btn_27", use_container_width=True):
            place_bet('straight', 27)
    
    with row3_betting[3]:
        if st.button("Bet on 30", key="btn_30", use_container_width=True):
            place_bet('straight', 30)
        if st.button("Bet on 33", key="btn_33", use_container_width=True):
            place_bet('straight', 33)
        if st.button("Bet on 36", key="btn_36", use_container_width=True):
            place_bet('straight', 36)
    
    # Outside bets section
    st.write("### Outside Bets")
    
    # Create 3 rows of outside bets to avoid nesting
    outside_row1 = st.columns(3)
    
    with outside_row1[0]:
        st.write("**Red or Black (1:1)**")
        if st.button("Red", key="btn_red", use_container_width=True):
            place_bet('color', 'red')
        if st.button("Black", key="btn_black", use_container_width=True):
            place_bet('color', 'black')
    
    with outside_row1[1]:
        st.write("**Even or Odd (1:1)**")
        if st.button("Even", key="btn_even", use_container_width=True):
            place_bet('parity', 'even')
        if st.button("Odd", key="btn_odd", use_container_width=True):
            place_bet('parity', 'odd')
    
    with outside_row1[2]:
        st.write("**High or Low (1:1)**")
        if st.button("High (19-36)", key="btn_high", use_container_width=True):
            place_bet('range', 'high')
        if st.button("Low (1-18)", key="btn_low", use_container_width=True):
            place_bet('range', 'low')
    
    # Row for Dozens
    st.write("### Dozen Bets (2:1)")
    dozen_betting = st.columns(3)
    
    for idx, dozen in enumerate(["1st Dozen (1-12)", "2nd Dozen (13-24)", "3rd Dozen (25-36)"]):
        with dozen_betting[idx]:
            # Calculate the dozen range
            start_num = (idx * 12) + 1
            end_num = start_num + 11
            
            if st.button(dozen, key=f"btn_dozen_{idx+1}", use_container_width=True,
                       help=f"Dozen bet on {dozen} (pays 2:1)"):
                # Show the numbers this bet covers
                st.info(f"Dozen {idx+1} covers: {start_num}-{end_num}")
                place_bet('dozen', idx+1)
    
    # Row for Columns
    st.write("### Column Bets (2:1)")
    column_betting = st.columns(3)
    
    for idx, col_name in enumerate(["1st Column", "2nd Column", "3rd Column"]):
        with column_betting[idx]:
            # Calculate which numbers this column covers
            column_numbers = list(range(idx+1, 37, 3))
            column_numbers_str = ", ".join(str(n) for n in column_numbers)
            
            if st.button(col_name, key=f"btn_column_{idx+1}", use_container_width=True,
                       help=f"Column bet on {col_name} (pays 2:1)"):
                st.info(f"Column {idx+1} covers: {column_numbers_str}")
                place_bet('column', idx+1)
    
    # Special bets section
    st.write("### Special Bets")
    special_bets = st.columns(2)
    
    # Street bet
    with special_bets[0]:
        st.write("**Street Bet (11:1)**")
        street_row = st.number_input("Row number (1-12):", min_value=1, max_value=12, value=1, key="street_row")
        
        # Calculate the numbers in this street for preview
        start_number = (street_row - 1) * 3 + 1
        covered_numbers = [start_number, start_number + 1, start_number + 2]
        
        # Show the numbers this bet covers
        st.info(f"This bet covers: {', '.join(str(n) for n in covered_numbers)}")
        
        if st.button("Place Street Bet", key="place_street", use_container_width=True):
            place_bet('street', street_row)
    
    # Corner bet 
    with special_bets[1]:
        st.write("**Corner Bet (8:1)**")
        corner_num = st.number_input("Corner number (1-22):", min_value=1, max_value=22, value=1, key="corner_num")
        
        # Calculate the four corner numbers
        row = (corner_num - 1) // 11
        col = (corner_num - 1) % 11
        start_number = row * 3 + col + 1
        covered_numbers = [
            start_number, 
            start_number + 1, 
            start_number + 3, 
            start_number + 4
        ]
        
        # Show the numbers this bet covers
        st.info(f"This bet covers: {', '.join(str(n) for n in covered_numbers)}")
        
        if st.button("Place Corner Bet", key="place_corner", use_container_width=True):
            place_bet('corner', corner_num)
    
    # Six Line bet
    st.write("**Six Line Bet (5:1)**")
    line_num = st.number_input("Line number (1-11):", min_value=1, max_value=11, value=1, key="line_num")
    
    # Calculate the numbers in this line for preview
    start_number = (line_num - 1) * 3 + 1
    end_number = start_number + 5
    covered_numbers = list(range(start_number, end_number + 1))
    
    # Show the numbers this bet covers
    st.info(f"This bet covers: {', '.join(str(n) for n in covered_numbers)}")
    
    if st.button("Place Six Line Bet", key="place_six_line", use_container_width=True):
        place_bet('six_line', line_num)

def create_chip_selector():
    """Create a selector for betting chips."""
    st.write("### Select Chip")
    chip_cols = st.columns(9)
    
    chips = st.session_state.simulator.get_chip_options()
    
    for i, chip in enumerate(chips):
        chip_color = get_chip_color(chip)
        
        # Format the chip value
        if chip < 1:
            display_value = f"${chip:.2f}"
        else:
            display_value = f"${int(chip)}" if chip == int(chip) else f"${chip:.2f}"
        
        # Create a chip button with appropriate styling
        if chip_cols[i].button(
            display_value, 
            key=f"chip_{chip}",
            help=f"Select ${chip} chip",
            use_container_width=True,
            # Style based on whether this is the currently selected chip
            type="primary" if st.session_state.current_chip == chip else "secondary"
        ):
            st.session_state.current_chip = chip

def create_betting_controls():
    """Create controls for betting and spinning."""
    cols = st.columns([1, 1, 1, 1, 1])
    
    # Balance display
    cols[0].metric(
        "Balance", 
        f"${st.session_state.simulator.balance:.2f}", 
        f"{st.session_state.simulator.get_summary_stats()['net_profit']:.2f}"
    )
    
    # Current bets display
    total_bet = st.session_state.simulator.get_total_bet_amount()
    potential_win = st.session_state.simulator.get_potential_win()
    
    cols[1].metric("Total Bet", f"${total_bet:.2f}")
    cols[2].metric("Potential Win", f"${potential_win:.2f}" if potential_win > 0 else "$0.00")
    
    # Undo button - place directly in the column without nesting
    if cols[3].button("UNDO LAST BET", key="btn_undo_bet", use_container_width=True, 
                    type="secondary", help="Remove the last bet placed"):
        if st.session_state.simulator.undo_last_bet():
            st.success("Last bet removed!")
        else:
            st.warning("No bets to undo.")
    
    # Clear bets button - place directly in the main controls row
    if cols[4].button("CLEAR BETS", key="btn_clear_bets", use_container_width=True, 
                    type="secondary", help="Clear all active bets"):
        st.session_state.simulator.clear_bets()
        st.success("All bets cleared!")
    
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
    
    # Create two buttons - Spin or Enter Live Number
    spin_cols = st.columns(2)
    
    # Spin button
    if spin_cols[0].button("SPIN", key="btn_spin", use_container_width=True, type="primary"):
        spin_wheel()
    
    # Manual input for live casino numbers
    with spin_cols[1]:
        manual_num = st.text_input("Or enter live casino number:", key="manual_number", placeholder="Enter number (0-36 or 00)")
        if st.button("Add Result", key="btn_add_result", use_container_width=True):
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
    
    st.write("### Betting Recommendations")
    
    # Get recommendations from the agent
    recommendations = st.session_state.agent.get_specific_bet_recommendations(
        st.session_state.spins_df,
        st.session_state.simulator.roulette_type,
        st.session_state.simulator.balance
    )
    
    # Store recommendations for later evaluation
    st.session_state.last_recommendations = recommendations
    
    # Display recommendations with confidence scores
    rec_cols = st.columns(3)
    
    with rec_cols[0]:
        st.write("**Single Numbers**")
        if recommendations['single_numbers']:
            for num_rec in recommendations['single_numbers']:
                confidence = num_rec.get('confidence', 0)
                st.markdown(
                    f"<div style='display: flex; align-items: center;'>"
                    f"<span style='font-weight: bold; margin-right: 10px;'>Number {num_rec['number']}:</span>"
                    f"<div style='background: linear-gradient(to right, "
                    f"rgba(0,128,0,{confidence}) {int(confidence*100)}%, "
                    f"#f0f0f0 {int(confidence*100)}%); "
                    f"height: 20px; flex-grow: 1; border-radius: 5px;'></div>"
                    f"<span style='margin-left: 10px;'>{confidence:.2f}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.write("No single number recommendations")
    
    with rec_cols[1]:
        st.write("**Outside Bets**")
        for bet_type in ['red_black', 'even_odd', 'high_low']:
            if bet_type in recommendations and recommendations[bet_type].get('recommendation'):
                rec = recommendations[bet_type]
                confidence = rec.get('confidence', 0)
                bet_name = bet_type.replace('_', ' ').title()
                
                st.markdown(
                    f"<div style='display: flex; align-items: center;'>"
                    f"<span style='font-weight: bold; margin-right: 10px;'>{bet_name}:</span>"
                    f"<span style='margin-right: 10px;'>{rec['recommendation']}</span>"
                    f"<div style='background: linear-gradient(to right, "
                    f"rgba(0,128,0,{confidence}) {int(confidence*100)}%, "
                    f"#f0f0f0 {int(confidence*100)}%); "
                    f"height: 20px; flex-grow: 1; border-radius: 5px;'></div>"
                    f"<span style='margin-left: 10px;'>{confidence:.2f}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
    
    with rec_cols[2]:
        st.write("**Dozens & Columns**")
        for bet_type in ['dozens', 'columns']:
            if bet_type in recommendations and recommendations[bet_type].get('recommendation'):
                rec = recommendations[bet_type]
                confidence = rec.get('confidence', 0)
                bet_name = bet_type.title()
                
                st.markdown(
                    f"<div style='display: flex; align-items: center;'>"
                    f"<span style='font-weight: bold; margin-right: 10px;'>{bet_name}:</span>"
                    f"<span style='margin-right: 10px;'>{rec['recommendation']}</span>"
                    f"<div style='background: linear-gradient(to right, "
                    f"rgba(0,128,0,{confidence}) {int(confidence*100)}%, "
                    f"#f0f0f0 {int(confidence*100)}%); "
                    f"height: 20px; flex-grow: 1; border-radius: 5px;'></div>"
                    f"<span style='margin-left: 10px;'>{confidence:.2f}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

def create_strategy_performance_display():
    """Create a display for strategy performance."""
    if not st.session_state.strategy_performance:
        return
    
    st.write("### Strategy Performance")
    
    performance = []
    for strategy, stats in st.session_state.strategy_performance.items():
        total_bets = stats['wins'] + stats['losses']
        if total_bets > 0:
            win_rate = stats['wins'] / total_bets
            strategy_name = strategy.replace('_', ' ').title()
            performance.append({
                'Strategy': strategy_name,
                'Win Rate': win_rate,
                'Total Bets': total_bets,
                'Wins': stats['wins'],
                'Losses': stats['losses']
            })
    
    if performance:
        perf_df = pd.DataFrame(performance)
        
        # Sort by win rate
        perf_df = perf_df.sort_values(by='Win Rate', ascending=False)
        
        # Create a nice bar chart
        fig = px.bar(
            perf_df,
            x='Strategy',
            y='Win Rate',
            color='Win Rate',
            color_continuous_scale=['red', 'yellow', 'green'],
            text=perf_df['Win Rate'].apply(lambda x: f"{x:.1%}"),
            labels={'Win Rate': 'Win Rate', 'Strategy': 'Strategy'},
            height=300
        )
        
        fig.update_layout(
            xaxis_title='Strategy',
            yaxis_title='Win Rate',
            yaxis_tickformat='.0%',
            xaxis={'categoryorder': 'total descending'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display as a table too
        perf_df['Win Rate'] = perf_df['Win Rate'].apply(lambda x: f"{x:.1%}")
        st.dataframe(perf_df, use_container_width=True, hide_index=True)

def create_advanced_analysis():
    """Create a display for advanced betting analysis."""
    if st.session_state.spins_df.empty:
        st.info("Play more spins to see advanced analysis!")
        return
    
    st.write("### Advanced Betting Analysis")
    
    tabs = st.tabs(["Sleeper Numbers", "Sectors", "Split/Corner Opportunities", "Wheel Heatmap"])
    
    with tabs[0]:
        # Sleeper numbers analysis
        if len(st.session_state.spins_df) >= 10:
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
            else:
                st.info("No sleeper numbers detected yet.")
        else:
            st.info("Need at least 10 spins to find sleeper numbers.")
    
    with tabs[1]:
        # Sector analysis
        if len(st.session_state.spins_df) >= 20:
            sectors = st.session_state.advanced_analysis.analyze_sectors(
                st.session_state.spins_df,
                st.session_state.simulator.roulette_type
            )
            
            if sectors and 'hot_sectors' in sectors:
                st.write("Hot sectors on the wheel:")
                
                sector_data = []
                for sector in sectors['hot_sectors']:
                    sector_data.append({
                        'Sector': sector['name'],
                        'Hit Rate': sector['hit_rate'],
                        'Expected': sector['expected_rate'],
                        'Difference': sector['hit_rate'] - sector['expected_rate']
                    })
                
                sector_df = pd.DataFrame(sector_data)
                
                fig = px.bar(
                    sector_df,
                    x='Sector',
                    y='Difference',
                    color='Difference',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    labels={'Difference': 'Difference from Expected', 'Sector': 'Wheel Sector'},
                    height=300
                )
                
                fig.update_layout(
                    xaxis_title='Wheel Sector',
                    yaxis_title='Difference from Expected Rate',
                    yaxis_tickformat='.0%'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Format the dataframe for display
                sector_df['Hit Rate'] = sector_df['Hit Rate'].apply(lambda x: f"{x:.1%}")
                sector_df['Expected'] = sector_df['Expected'].apply(lambda x: f"{x:.1%}")
                sector_df['Difference'] = sector_df['Difference'].apply(lambda x: f"{x:+.1%}")
                
                st.dataframe(sector_df, use_container_width=True, hide_index=True)
            else:
                st.info("No significant sector patterns detected yet.")
        else:
            st.info("Need at least 20 spins for sector analysis.")
    
    with tabs[2]:
        # Split/corner opportunities
        if len(st.session_state.spins_df) >= 20:
            opportunities = st.session_state.advanced_analysis.find_split_corner_opportunities(
                st.session_state.spins_df,
                st.session_state.simulator.roulette_type
            )
            
            if opportunities:
                st.write("Potential betting opportunities:")
                
                if 'split_bets' in opportunities and opportunities['split_bets']:
                    st.write("**Split Bet Opportunities (pays 17:1)**")
                    split_cols = st.columns(min(4, len(opportunities['split_bets'])))
                    
                    for i, split in enumerate(opportunities['split_bets']):
                        numbers = split.get('numbers', [])
                        confidence = split.get('confidence', 0)
                        
                        if len(numbers) == 2:
                            split_cols[i].markdown(
                                f"<div style='text-align: center; font-weight: bold;'>"
                                f"{numbers[0]}-{numbers[1]}</div>"
                                f"<div style='background: linear-gradient(to right, "
                                f"rgba(0,128,0,{confidence}) {int(confidence*100)}%, "
                                f"#f0f0f0 {int(confidence*100)}%); "
                                f"height: 20px; border-radius: 5px; margin-bottom: 10px;'></div>"
                                f"<div style='text-align: center;'>Confidence: {confidence:.2f}</div>",
                                unsafe_allow_html=True
                            )
                
                if 'corner_bets' in opportunities and opportunities['corner_bets']:
                    st.write("**Corner Bet Opportunities (pays 8:1)**")
                    corner_cols = st.columns(min(3, len(opportunities['corner_bets'])))
                    
                    for i, corner in enumerate(opportunities['corner_bets']):
                        numbers = corner.get('numbers', [])
                        confidence = corner.get('confidence', 0)
                        
                        if len(numbers) == 4:
                            corner_cols[i].markdown(
                                f"<div style='text-align: center; font-weight: bold;'>"
                                f"{numbers[0]},{numbers[1]},{numbers[2]},{numbers[3]}</div>"
                                f"<div style='background: linear-gradient(to right, "
                                f"rgba(0,128,0,{confidence}) {int(confidence*100)}%, "
                                f"#f0f0f0 {int(confidence*100)}%); "
                                f"height: 20px; border-radius: 5px; margin-bottom: 10px;'></div>"
                                f"<div style='text-align: center;'>Confidence: {confidence:.2f}</div>",
                                unsafe_allow_html=True
                            )
            else:
                st.info("No significant opportunities detected yet.")
        else:
            st.info("Need at least 20 spins to find bet opportunities.")
    
    with tabs[3]:
        # Wheel heatmap
        if len(st.session_state.spins_df) >= 30:
            st.write("Roulette Wheel Heatmap (showing hot/cold areas)")
            
            heatmap = st.session_state.advanced_analysis.create_wheel_heatmap(
                st.session_state.spins_df,
                st.session_state.simulator.roulette_type
            )
            
            st.plotly_chart(heatmap, use_container_width=True)
        else:
            st.info("Need at least 30 spins to generate a wheel heatmap.")

def create_session_stats():
    """Create a display for session statistics."""
    if not st.session_state.win_history:
        return
    
    st.write("### Session Statistics")
    
    stats_cols = st.columns(5)
    
    # Get summary stats
    summary = st.session_state.simulator.get_summary_stats()
    win_history = st.session_state.win_history
    
    # Display metrics
    stats_cols[0].metric("Total Spins", summary['total_spins'])
    stats_cols[1].metric("Net Profit", f"${summary['net_profit']:.2f}")
    
    win_rate = summary['win_rate']
    stats_cols[2].metric("Win Rate", f"{win_rate:.1%}")
    
    # Find biggest win
    if win_history:
        biggest_win = max(win_history, key=lambda x: x['winnings'])
        stats_cols[3].metric("Biggest Win", f"${biggest_win['winnings']:.2f}", 
                           f"Number {biggest_win['number']}")
    
    # Most common result
    if summary['most_common_result'] is not None:
        stats_cols[4].metric("Most Common Number", str(summary['most_common_result']))
    
    # Create a balance history chart
    if len(win_history) > 1:
        # Calculate cumulative balance history
        initial_balance = 1000.0
        balance_history = [initial_balance]
        spin_numbers = [0]
        
        for i, result in enumerate(win_history):
            new_balance = balance_history[-1] + result['winnings'] - \
                         (result['bets_placed'] - result['bets_won']) * st.session_state.current_chip
            balance_history.append(new_balance)
            spin_numbers.append(i + 1)
        
        # Create the chart
        fig = go.Figure()
        
        # Add balance line
        fig.add_trace(go.Scatter(
            x=spin_numbers, 
            y=balance_history,
            mode='lines+markers',
            name='Balance',
            line=dict(color='blue', width=2),
            hovertemplate='Spin %{x}<br>Balance: $%{y:.2f}'
        ))
        
        # Add initial balance reference line
        fig.add_shape(
            type="line",
            x0=0,
            y0=initial_balance,
            x1=spin_numbers[-1],
            y1=initial_balance,
            line=dict(
                color="red",
                width=1,
                dash="dash",
            )
        )
        
        # Update layout
        fig.update_layout(
            title="Balance History",
            xaxis_title="Spin Number",
            yaxis_title="Balance ($)",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)

def main():
    """Main function to run the app."""
    st.title("🎰 Interactive Roulette Simulator")
    
    # Sidebar settings
    with st.sidebar:
        st.header("Settings")
        
        # Roulette type
        roulette_type = st.radio(
            "Roulette Type",
            ["European (Single Zero)", "American (Double Zero)"],
            index=0
        )
        
        # Set roulette type in simulator
        if roulette_type == "European (Single Zero)" and st.session_state.simulator.roulette_type != "European":
            st.session_state.simulator = RouletteSimulator(roulette_type="European")
        elif roulette_type == "American (Double Zero)" and st.session_state.simulator.roulette_type != "American":
            st.session_state.simulator = RouletteSimulator(roulette_type="American")
        
        # Balance settings
        st.header("Balance")
        starting_balance = st.number_input(
            "Starting Balance",
            min_value=0.0,
            max_value=10000.0,
            value=1000.0,
            step=100.0
        )
        
        # Set balance button
        if st.button("Set Balance"):
            st.session_state.simulator.set_balance(starting_balance)
        
        # Reset button
        if st.button("Reset Game", type="primary"):
            # Re-initialize simulator
            st.session_state.simulator = RouletteSimulator(
                roulette_type="European" if roulette_type == "European (Single Zero)" else "American"
            )
            st.session_state.simulator.set_balance(starting_balance)
            
            # Clear history
            st.session_state.spins_df = pd.DataFrame(columns=['number', 'color', 'parity', 'range', 'dozen', 'column', 'timestamp'])
            st.session_state.win_history = []
            st.session_state.strategy_performance = {}
            
            st.success("Game reset successfully!")
        
        # Show betting options info
        st.header("Betting Options")
        st.markdown("""
        ### Outside Bets
        1. **Dozen Bet** – Pays 2 to 1
        2. **Odd or Even** – Pays 1 to 1
        3. **Red or Black** – Pays 1 to 1
        4. **High or Low** – Pays 1 to 1
        5. **Column Bet** – Pays 2 to 1
        
        ### Inside Bets
        6. **Top Line Bet** (0, 00, 1, 2, 3) – Pays 6 to 1
        7. **Six Line Bet** (6 numbers) – Pays 5 to 1
        8. **Corner Bet** (4 numbers) – Pays 8 to 1
        9. **Street Bet** (3 numbers) – Pays 11 to 1
        10. **Split Bet** (2 numbers) – Pays 17 to 1
        11. **Straight Bet** (1 number) – Pays 35 to 1
        """)
    
    # Main area with tabs - simplified to focus on functionality
    main_tabs = st.tabs(["Roulette Table & Recommendations", "Analysis"])
    
    with main_tabs[0]:
        # Create two columns - 2/3 for table, 1/3 for recommendations
        table_rec_cols = st.columns([2, 1])
        
        with table_rec_cols[0]:
            # Betting controls
            create_betting_controls()
            
            # Chip selector
            create_chip_selector()
            
            # Roulette board
            create_roulette_board()
            
            # Spin history
            create_spin_history_display()
        
        with table_rec_cols[1]:
            # Agent recommendations directly on the table screen
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
                                if st.session_state.current_chip_value:
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
                                if st.session_state.current_chip_value:
                                    if bet_type == 'red_black':
                                        place_bet('color', recommendation.lower())
                                    elif bet_type == 'even_odd':
                                        place_bet('parity', recommendation.lower())
                                    elif bet_type == 'high_low':
                                        place_bet('range', recommendation.lower())
                                else:
                                    st.warning("Select a chip first")
    
    with main_tabs[1]:
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