"""
Roulette Simulation Module
Provides interactive simulation of roulette games with various betting options.
"""

import random
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Set, Union

class RouletteBet:
    """Class representing a roulette bet with type, amount, and covered numbers."""
    
    def __init__(self, bet_type: str, amount: float, numbers: List[Union[int, str]], name: str = None):
        """
        Initialize a roulette bet.
        
        Args:
            bet_type (str): The type of bet (e.g., 'straight', 'split', 'red', etc.)
            amount (float): The bet amount
            numbers (List[Union[int, str]]): List of numbers covered by the bet
            name (str, optional): Optional descriptive name for the bet
        """
        self.bet_type = bet_type
        self.amount = amount
        self.numbers = numbers
        self.name = name or bet_type
    
    def get_payout_multiplier(self) -> float:
        """
        Get the payout multiplier for this bet type.
        
        Returns:
            float: The payout multiplier
        """
        # Outside bets
        if self.bet_type in ['red', 'black', 'even', 'odd', 'high', 'low']:
            return 1.0  # 1:1 payout
        elif self.bet_type in ['column', 'dozen']:
            return 2.0  # 2:1 payout
        # Inside bets
        elif self.bet_type == 'top_line':
            return 6.0  # 6:1 payout
        elif self.bet_type == 'six_line':
            return 5.0  # 5:1 payout
        elif self.bet_type == 'corner':
            return 8.0  # 8:1 payout
        elif self.bet_type == 'street':
            return 11.0  # 11:1 payout
        elif self.bet_type == 'split':
            return 17.0  # 17:1 payout
        elif self.bet_type == 'straight':
            return 35.0  # 35:1 payout
        else:
            return 0.0  # Unknown bet type
    
    def get_winning_amount(self) -> float:
        """
        Calculate the winning amount including the original bet.
        
        Returns:
            float: The total amount received on a win
        """
        return self.amount + (self.amount * self.get_payout_multiplier())
    
    def get_probability(self, roulette_type: str = 'European') -> float:
        """
        Calculate the probability of winning this bet.
        
        Args:
            roulette_type (str): The roulette type ('European' or 'American')
            
        Returns:
            float: The probability of winning as a fraction (0-1)
        """
        # Total possible outcomes
        denominator = 37 if roulette_type == 'European' else 38
        
        # Number of winning outcomes
        numerator = len(self.numbers)
        
        return numerator / denominator

class RouletteSimulator:
    """Class for simulating roulette games with various betting options."""
    
    def __init__(self, roulette_type: str = 'European'):
        """
        Initialize the roulette simulator.
        
        Args:
            roulette_type (str): The type of roulette ('European' or 'American')
        """
        self.roulette_type = roulette_type
        self.active_bets = []
        self.spin_history = []
        self.balance = 1000.0  # Default starting balance
        self.result = None
        
        # Define roulette wheel numbers
        if roulette_type == 'European':
            self.numbers = [0] + list(range(1, 37))
        else:  # American
            self.numbers = [0, '00'] + list(range(1, 37))
        
        # Define number properties
        self.red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        self.black_numbers = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
        
        # Create the dozens
        self.first_dozen = set(range(1, 13))
        self.second_dozen = set(range(13, 25))
        self.third_dozen = set(range(25, 37))
        
        # Create the columns
        self.first_column = {1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34}
        self.second_column = {2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35}
        self.third_column = {3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36}
    
    def set_balance(self, balance: float):
        """
        Set the player's balance.
        
        Args:
            balance (float): The new balance
        """
        self.balance = balance
    
    def clear_bets(self):
        """Clear all active bets."""
        # Refund all bet amounts back to balance
        for bet in self.active_bets:
            self.balance += bet.amount
        # Clear the active bets list
        self.active_bets = []
        
    def undo_last_bet(self):
        """Remove the most recently placed bet and refund the bet amount."""
        if not self.active_bets:
            return False
            
        # Get the last bet
        last_bet = self.active_bets.pop()
        
        # Refund the bet amount
        self.balance += last_bet.amount
        
        return True
    
    def add_straight_bet(self, number: Union[int, str], amount: float) -> bool:
        """
        Add a straight bet on a single number.
        
        Args:
            number (Union[int, str]): The number to bet on
            amount (float): The bet amount
            
        Returns:
            bool: True if the bet was added successfully
        """
        if amount > self.balance:
            return False
            
        bet = RouletteBet(
            bet_type='straight',
            amount=amount,
            numbers=[number],
            name=f'Straight bet on {number}'
        )
        self.active_bets.append(bet)
        self.balance -= amount
        return True
    
    def add_split_bet(self, number1: int, number2: int, amount: float) -> bool:
        """
        Add a split bet on two adjacent numbers.
        
        Args:
            number1 (int): First number
            number2 (int): Second number
            amount (float): The bet amount
            
        Returns:
            bool: True if the bet was added successfully
        """
        if amount > self.balance:
            return False
            
        bet = RouletteBet(
            bet_type='split',
            amount=amount,
            numbers=[number1, number2],
            name=f'Split bet on {number1}/{number2}'
        )
        self.active_bets.append(bet)
        self.balance -= amount
        return True
    
    def add_street_bet(self, row: int, amount: float) -> bool:
        """
        Add a street bet on three numbers in a row.
        
        Args:
            row (int): The row number (1-12)
            amount (float): The bet amount
            
        Returns:
            bool: True if the bet was added successfully
        """
        if amount > self.balance or row < 1 or row > 12:
            return False
            
        # Calculate the three numbers in the row
        start_number = (row - 1) * 3 + 1
        numbers = [start_number, start_number + 1, start_number + 2]
        
        bet = RouletteBet(
            bet_type='street',
            amount=amount,
            numbers=numbers,
            name=f'Street bet on {numbers[0]}-{numbers[-1]}'
        )
        self.active_bets.append(bet)
        self.balance -= amount
        return True
    
    def add_corner_bet(self, corner: int, amount: float) -> bool:
        """
        Add a corner bet on four numbers.
        
        Args:
            corner (int): The corner number (1-22)
            amount (float): The bet amount
            
        Returns:
            bool: True if the bet was added successfully
        """
        if amount > self.balance or corner < 1 or corner > 22:
            return False
            
        # Calculate row and column
        row = (corner - 1) // 11
        col = (corner - 1) % 11
        
        # Calculate the four corner numbers
        start_number = row * 3 + col + 1
        numbers = [
            start_number, 
            start_number + 1, 
            start_number + 3, 
            start_number + 4
        ]
        
        bet = RouletteBet(
            bet_type='corner',
            amount=amount,
            numbers=numbers,
            name=f'Corner bet on {numbers[0]},{numbers[1]},{numbers[2]},{numbers[3]}'
        )
        self.active_bets.append(bet)
        self.balance -= amount
        return True
    
    def add_six_line_bet(self, line: int, amount: float) -> bool:
        """
        Add a six line bet on six numbers across two rows.
        
        Args:
            line (int): The line number (1-11)
            amount (float): The bet amount
            
        Returns:
            bool: True if the bet was added successfully
        """
        if amount > self.balance or line < 1 or line > 11:
            return False
            
        # Calculate the six numbers in the two rows
        start_number = (line - 1) * 3 + 1
        numbers = [
            start_number, start_number + 1, start_number + 2,
            start_number + 3, start_number + 4, start_number + 5
        ]
        
        bet = RouletteBet(
            bet_type='six_line',
            amount=amount,
            numbers=numbers,
            name=f'Six line bet on {numbers[0]}-{numbers[-1]}'
        )
        self.active_bets.append(bet)
        self.balance -= amount
        return True
    
    def add_top_line_bet(self, amount: float) -> bool:
        """
        Add a top line bet on 0, 00, 1, 2, 3.
        
        Args:
            amount (float): The bet amount
            
        Returns:
            bool: True if the bet was added successfully
        """
        if amount > self.balance:
            return False
            
        if self.roulette_type == 'European':
            numbers = [0, 1, 2, 3]
            name = 'First four bet on 0,1,2,3'
        else:  # American
            numbers = [0, '00', 1, 2, 3]
            name = 'Top line bet on 0,00,1,2,3'
            
        bet = RouletteBet(
            bet_type='top_line',
            amount=amount,
            numbers=numbers,
            name=name
        )
        self.active_bets.append(bet)
        self.balance -= amount
        return True
    
    def add_color_bet(self, color: str, amount: float) -> bool:
        """
        Add a bet on red or black.
        
        Args:
            color (str): The color to bet on ('red' or 'black')
            amount (float): The bet amount
            
        Returns:
            bool: True if the bet was added successfully
        """
        if amount > self.balance or color not in ['red', 'black']:
            return False
            
        numbers = list(self.red_numbers) if color == 'red' else list(self.black_numbers)
        
        bet = RouletteBet(
            bet_type=color,
            amount=amount,
            numbers=numbers,
            name=f'{color.capitalize()} bet'
        )
        self.active_bets.append(bet)
        self.balance -= amount
        return True
    
    def add_parity_bet(self, parity: str, amount: float) -> bool:
        """
        Add a bet on even or odd.
        
        Args:
            parity (str): The parity to bet on ('even' or 'odd')
            amount (float): The bet amount
            
        Returns:
            bool: True if the bet was added successfully
        """
        if amount > self.balance or parity not in ['even', 'odd']:
            return False
            
        if parity == 'even':
            numbers = [n for n in range(2, 37, 2)]
        else:  # odd
            numbers = [n for n in range(1, 37, 2)]
        
        bet = RouletteBet(
            bet_type=parity,
            amount=amount,
            numbers=numbers,
            name=f'{parity.capitalize()} bet'
        )
        self.active_bets.append(bet)
        self.balance -= amount
        return True
    
    def add_range_bet(self, range_type: str, amount: float) -> bool:
        """
        Add a bet on high or low numbers.
        
        Args:
            range_type (str): The range to bet on ('high' or 'low')
            amount (float): The bet amount
            
        Returns:
            bool: True if the bet was added successfully
        """
        if amount > self.balance or range_type not in ['high', 'low']:
            return False
            
        if range_type == 'high':
            numbers = list(range(19, 37))
        else:  # low
            numbers = list(range(1, 19))
        
        bet = RouletteBet(
            bet_type=range_type,
            amount=amount,
            numbers=numbers,
            name=f'{range_type.capitalize()} bet ({"19-36" if range_type == "high" else "1-18"})'
        )
        self.active_bets.append(bet)
        self.balance -= amount
        return True
    
    def add_dozen_bet(self, dozen: int, amount: float) -> bool:
        """
        Add a bet on a dozen (1-12, 13-24, 25-36).
        
        Args:
            dozen (int): The dozen to bet on (1, 2, or 3)
            amount (float): The bet amount
            
        Returns:
            bool: True if the bet was added successfully
        """
        if amount > self.balance or dozen < 1 or dozen > 3:
            return False
            
        if dozen == 1:
            numbers = list(self.first_dozen)
            name = '1st dozen (1-12)'
        elif dozen == 2:
            numbers = list(self.second_dozen)
            name = '2nd dozen (13-24)'
        else:  # dozen == 3
            numbers = list(self.third_dozen)
            name = '3rd dozen (25-36)'
        
        bet = RouletteBet(
            bet_type='dozen',
            amount=amount,
            numbers=numbers,
            name=f'Dozen bet on {name}'
        )
        self.active_bets.append(bet)
        self.balance -= amount
        return True
    
    def add_column_bet(self, column: int, amount: float) -> bool:
        """
        Add a bet on a column.
        
        Args:
            column (int): The column to bet on (1, 2, or 3)
            amount (float): The bet amount
            
        Returns:
            bool: True if the bet was added successfully
        """
        if amount > self.balance or column < 1 or column > 3:
            return False
            
        if column == 1:
            numbers = list(self.first_column)
            name = '1st column'
        elif column == 2:
            numbers = list(self.second_column)
            name = '2nd column'
        else:  # column == 3
            numbers = list(self.third_column)
            name = '3rd column'
        
        bet = RouletteBet(
            bet_type='column',
            amount=amount,
            numbers=numbers,
            name=f'Column bet on {name}'
        )
        self.active_bets.append(bet)
        self.balance -= amount
        return True
    
    def get_total_bet_amount(self) -> float:
        """
        Get the total amount of all active bets.
        
        Returns:
            float: The total bet amount
        """
        return sum(bet.amount for bet in self.active_bets)
    
    def get_potential_win(self) -> float:
        """
        Calculate the potential maximum win amount (not accounting for overlap).
        
        Returns:
            float: The maximum potential win
        """
        return max([bet.get_winning_amount() for bet in self.active_bets]) if self.active_bets else 0
    
    def spin(self) -> Union[int, str]:
        """
        Spin the roulette wheel and process the results.
        
        Returns:
            Union[int, str]: The result of the spin
        """
        # Spin the wheel
        self.result = random.choice(self.numbers)
        
        # Process bets
        winnings = 0.0
        won_bets = []
        lost_bets = []
        
        for bet in self.active_bets:
            if self.result in bet.numbers:
                # Bet wins
                win_amount = bet.get_winning_amount()
                winnings += win_amount
                won_bets.append((bet, win_amount))
            else:
                # Bet loses
                lost_bets.append(bet)
        
        # Update balance
        self.balance += winnings
        
        # If balance is less than or equal to 0, set it to 0
        if self.balance <= 0:
            self.balance = 0
        
        # Store result in history
        self.spin_history.append({
            'result': self.result,
            'winnings': winnings,
            'won_bets': won_bets,
            'lost_bets': lost_bets
        })
        
        # Clear active bets for next round
        self.active_bets = []
        
        return self.result
    
    def get_chip_options(self) -> List[float]:
        """
        Get the available chip denominations.
        
        Returns:
            List[float]: List of chip denominations
        """
        return [0.10, 0.50, 1.0, 5.0, 10.0, 25.0, 50.0, 100.0, 500.0]
    
    def get_roulette_layout(self) -> List[List[Union[int, str]]]:
        """
        Get the layout of the roulette table.
        
        Returns:
            List[List[Union[int, str]]]: 2D representation of the roulette table
        """
        if self.roulette_type == 'European':
            return [
                [0],
                [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
                [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
                [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
            ]
        else:  # American
            return [
                [0, '00'],
                [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
                [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
                [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
            ]
    
    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics about the simulation.
        
        Returns:
            Dict: Dictionary with summary statistics
        """
        if not self.spin_history:
            return {
                'total_spins': 0,
                'net_profit': 0,
                'win_rate': 0,
                'most_common_result': None,
                'biggest_win': 0
            }
        
        total_spins = len(self.spin_history)
        starting_balance = 1000.0  # Default starting balance
        net_profit = self.balance - starting_balance
        
        # Calculate win rate
        spins_with_wins = sum(1 for spin in self.spin_history if spin['winnings'] > 0)
        win_rate = spins_with_wins / total_spins if total_spins > 0 else 0
        
        # Find most common result
        results = [spin['result'] for spin in self.spin_history]
        most_common = max(set(results), key=results.count) if results else None
        
        # Find biggest win
        biggest_win = max((spin['winnings'] for spin in self.spin_history), default=0)
        
        return {
            'total_spins': total_spins,
            'net_profit': net_profit,
            'win_rate': win_rate,
            'most_common_result': most_common,
            'biggest_win': biggest_win
        }
    
    def get_last_result_details(self) -> Dict:
        """
        Get details about the last spin result.
        
        Returns:
            Dict: Dictionary with details about the last spin
        """
        if not self.spin_history:
            return {
                'result': None,
                'winnings': 0,
                'won_bets': [],
                'lost_bets': []
            }
        
        return self.spin_history[-1]
    
    def get_number_properties(self, number: Union[int, str]) -> Dict:
        """
        Get properties of a roulette number.
        
        Args:
            number (Union[int, str]): The roulette number
            
        Returns:
            Dict: Dictionary with number properties
        """
        # Handle 0 and 00
        if number == 0 or number == '00':
            return {
                'color': 'green',
                'parity': None,
                'range': None,
                'dozen': None,
                'column': None
            }
        
        # Ensure number is an integer
        num = int(number)
        
        return {
            'color': 'red' if num in self.red_numbers else 'black',
            'parity': 'even' if num % 2 == 0 else 'odd',
            'range': 'high' if num >= 19 else 'low',
            'dozen': 1 if num in self.first_dozen else (2 if num in self.second_dozen else 3),
            'column': 1 if num in self.first_column else (2 if num in self.second_column else 3)
        }