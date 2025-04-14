import pandas as pd
import numpy as np
import random

class BettingStrategist:
    """
    Class to provide betting suggestions based on roulette spin data.
    """
    
    def get_betting_suggestions(self, spins_df, strategy, roulette_type):
        """
        Generate betting suggestions based on the specified strategy.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            strategy (str): Betting strategy to use
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            dict: Dictionary with betting suggestions
        """
        if spins_df is None or spins_df.empty:
            return {}
            
        # Choose the appropriate strategy method
        if strategy == "Hot Numbers":
            return self._hot_numbers_strategy(spins_df, roulette_type)
        elif strategy == "Due Numbers":
            return self._due_numbers_strategy(spins_df, roulette_type)
        elif strategy == "Pattern Based":
            return self._pattern_based_strategy(spins_df)
        elif strategy == "Martingale":
            return self._martingale_strategy(spins_df)
        elif strategy == "D'Alembert":
            return self._dalembert_strategy(spins_df)
        elif strategy == "Fibonacci":
            return self._fibonacci_strategy(spins_df)
        else:
            return {}
    
    def _hot_numbers_strategy(self, spins_df, roulette_type, hot_count=5):
        """
        Generate betting suggestions based on the most frequent numbers.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            hot_count (int): Number of hot numbers to suggest
            
        Returns:
            dict: Betting suggestions
        """
        # Count occurrences of each number
        number_counts = spins_df['number'].value_counts()
        
        # Filter out numbers with at least one occurrence
        number_counts = number_counts[number_counts > 0]
        
        if number_counts.empty:
            return {}
            
        # Sort by frequency (descending)
        number_counts = number_counts.sort_values(ascending=False)
        
        # Get hot numbers
        hot_numbers = number_counts.head(hot_count).index.tolist()
        
        # Calculate probabilities
        total_spins = len(spins_df)
        hot_probs = {num: number_counts[num] / total_spins for num in hot_numbers}
        
        # Calculate expected value
        ev_single = {}
        for num in hot_numbers:
            prob = hot_probs[num]
            payout = 35
            house_edge = 1/37 if roulette_type == "European" else 2/38  # Simplified
            ev_single[num] = (prob * payout) - (1 - prob)
        
        # Find numbers with the best expected value
        best_numbers = sorted(ev_single.items(), key=lambda x: x[1], reverse=True)
        
        # Prepare suggestions
        suggestions = {
            "Straight Up Bets": [f"Number {num} (appeared {number_counts[num]} times, {number_counts[num]/total_spins:.1%})" 
                                for num in hot_numbers[:3]],
            "Split Bets": self._find_split_bets(hot_numbers),
            "Corner Bets": self._find_corner_bets(hot_numbers),
            "Strategy Explanation": "Bet on numbers that have appeared most frequently, with an emphasis on those with the highest occurrence rate."
        }
        
        return suggestions
    
    def _due_numbers_strategy(self, spins_df, roulette_type, due_count=5):
        """
        Generate betting suggestions based on numbers that are "due" to appear.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            due_count (int): Number of due numbers to suggest
            
        Returns:
            dict: Betting suggestions
        """
        # Count occurrences of each number
        number_counts = spins_df['number'].value_counts()
        
        # Generate all possible numbers based on roulette type
        all_numbers = [str(i) for i in range(37)]  # 0-36
        if roulette_type == "American":
            all_numbers.append("00")
            
        # Add missing numbers with count 0
        for num in all_numbers:
            if num not in number_counts:
                number_counts[num] = 0
                
        # Calculate "dueness" of each number
        recency = {}
        
        for num in all_numbers:
            # Find most recent occurrence
            for i, row in enumerate(spins_df.iterrows()):
                if row[1]['number'] == num:
                    recency[num] = i
                    break
            else:
                # If number never appeared, consider it very due (large value)
                recency[num] = len(spins_df) * 2
        
        # Sort by recency (most due first)
        recency_sorted = sorted(recency.items(), key=lambda x: x[1], reverse=True)
        
        # Get most due numbers
        due_numbers = [item[0] for item in recency_sorted[:due_count]]
        
        # Calculate "dueness" scores (normalized)
        max_recency = max(recency.values()) if recency else 1
        due_scores = {num: recency[num] / max_recency for num in due_numbers}
        
        # Prepare suggestions
        suggestions = {
            "Straight Up Bets": [f"Number {num} (last appeared {recency[num]} spins ago)" 
                                if recency[num] < len(spins_df) * 2 
                                else f"Number {num} (never appeared)" 
                                for num in due_numbers[:3]],
            "Split Bets": self._find_split_bets(due_numbers),
            "Strategy Explanation": "Bet on numbers that haven't appeared for the longest time, based on the principle of regression to the mean."
        }
        
        return suggestions
    
    def _pattern_based_strategy(self, spins_df):
        """
        Generate betting suggestions based on detected patterns.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            dict: Betting suggestions
        """
        if len(spins_df) < 10:  # Need sufficient data for pattern analysis
            return {
                "Message": "Insufficient data for pattern analysis. Need at least 10 spins."
            }
            
        # Analyze patterns in different properties
        number_pattern = self._detect_number_patterns(spins_df)
        color_pattern = self._detect_property_patterns(spins_df, 'color')
        even_odd_pattern = self._detect_property_patterns(spins_df, 'even_odd')
        high_low_pattern = self._detect_property_patterns(spins_df, 'high_low')
        
        # Prepare suggestions
        suggestions = {}
        
        if number_pattern:
            suggestions["Number Patterns"] = [
                f"Sequence detected: {' → '.join(number_pattern['pattern'])}",
                f"Predicted next number: {number_pattern['predicted']}"
            ]
            
        if color_pattern:
            suggestions["Color Patterns"] = [
                f"Sequence detected: {' → '.join(color_pattern['pattern'])}",
                f"Predicted next color: {color_pattern['predicted']}"
            ]
            
        if even_odd_pattern:
            suggestions["Even/Odd Patterns"] = [
                f"Sequence detected: {' → '.join(even_odd_pattern['pattern'])}",
                f"Predicted next: {even_odd_pattern['predicted']}"
            ]
            
        if high_low_pattern:
            suggestions["High/Low Patterns"] = [
                f"Sequence detected: {' → '.join(high_low_pattern['pattern'])}",
                f"Predicted next: {high_low_pattern['predicted']}"
            ]
            
        if not suggestions:
            suggestions["Message"] = "No significant patterns detected in the spin history."
            
        suggestions["Strategy Explanation"] = "Analyzes recent spin history to identify repeating patterns and predicts the next outcome based on those patterns."
            
        return suggestions
    
    def _martingale_strategy(self, spins_df):
        """
        Generate betting suggestions based on the Martingale strategy.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            dict: Betting suggestions
        """
        if spins_df.empty:
            return {}
            
        # Get the most recent spins
        recent_spins = spins_df.tail(10)
        
        # Check even/odd and red/black streaks in recent spins
        even_odd_list = recent_spins['even_odd'].tolist()
        color_list = recent_spins['color'].tolist()
        
        # Find the current streak for even/odd
        current_even_odd = None
        even_odd_streak = 0
        
        for val in reversed(even_odd_list):
            if val != 'none':
                if current_even_odd is None:
                    current_even_odd = val
                    even_odd_streak = 1
                elif val == current_even_odd:
                    even_odd_streak += 1
                else:
                    break
        
        # Find the current streak for red/black
        current_color = None
        color_streak = 0
        
        for val in reversed(color_list):
            if val != 'green':
                if current_color is None:
                    current_color = val
                    color_streak = 1
                elif val == current_color:
                    color_streak += 1
                else:
                    break
        
        # Prepare suggestions
        suggestions = {
            "Strategy Type": "Martingale (Progression System)",
            "Even/Odd Bet": f"Bet on {'odd' if current_even_odd == 'even' else 'even'}" if current_even_odd else "Bet on even",
            "Red/Black Bet": f"Bet on {'black' if current_color == 'red' else 'red'}" if current_color else "Bet on red",
            "Bet Structure": [
                f"If you lose, double your bet on the next spin",
                f"If you win, return to your original bet size"
            ],
            "Current Streak": [
                f"Even/Odd: {even_odd_streak} consecutive {current_even_odd}" if current_even_odd else "No even/odd streak",
                f"Color: {color_streak} consecutive {current_color}" if current_color else "No color streak"
            ],
            "Strategy Explanation": "The Martingale system involves doubling your bet after each loss, so when you eventually win, you recover all previous losses plus a profit equal to your original bet."
        }
        
        return suggestions
    
    def _dalembert_strategy(self, spins_df):
        """
        Generate betting suggestions based on the D'Alembert strategy.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            dict: Betting suggestions
        """
        if spins_df.empty:
            return {}
            
        # Get the most recent 5 spins for analysis
        recent_spins = spins_df.tail(5)
        
        # Analyze recent results for even/odd and red/black
        even_odd_counts = recent_spins['even_odd'].value_counts()
        color_counts = recent_spins['color'].value_counts()
        
        # Determine if there's a recent bias
        even_bias = even_odd_counts.get('even', 0) > even_odd_counts.get('odd', 0)
        red_bias = color_counts.get('red', 0) > color_counts.get('black', 0)
        
        # Get the last spin result
        last_spin = spins_df.iloc[-1] if not spins_df.empty else None
        
        # Prepare suggestions
        suggestions = {
            "Strategy Type": "D'Alembert (Progression System)",
            "Even/Odd Bet": f"Bet on {'odd' if even_bias else 'even'}",
            "Red/Black Bet": f"Bet on {'black' if red_bias else 'red'}",
            "Bet Structure": [
                "If you lose, increase your bet by one unit",
                "If you win, decrease your bet by one unit",
                "Starting bet size should be at least 2-3 units"
            ],
            "Strategy Explanation": "The D'Alembert system is a more conservative progression system than Martingale, where you increase your bet by one unit after a loss and decrease it by one unit after a win."
        }
        
        if last_spin is not None:
            suggestions["Last Spin Result"] = [
                f"Number: {last_spin['number']}",
                f"Color: {last_spin['color']}",
                f"Even/Odd: {last_spin['even_odd']}"
            ]
        
        return suggestions
    
    def _fibonacci_strategy(self, spins_df):
        """
        Generate betting suggestions based on the Fibonacci strategy.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            dict: Betting suggestions
        """
        if spins_df.empty:
            return {}
            
        # Generate Fibonacci sequence
        fibonacci = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
        
        # Analyze recent results for red/black and even/odd
        recent_spins = spins_df.tail(10)
        
        red_black_counts = recent_spins['color'].value_counts()
        even_odd_counts = recent_spins['even_odd'].value_counts()
        
        # Get the less frequent outcomes to bet on
        bet_color = 'red' if red_black_counts.get('red', 0) <= red_black_counts.get('black', 0) else 'black'
        bet_even_odd = 'even' if even_odd_counts.get('even', 0) <= even_odd_counts.get('odd', 0) else 'odd'
        
        # Prepare suggestions
        suggestions = {
            "Strategy Type": "Fibonacci (Progression System)",
            "Color Bet": f"Bet on {bet_color}",
            "Even/Odd Bet": f"Bet on {bet_even_odd}",
            "Bet Progression": f"Fibonacci sequence: {', '.join(map(str, fibonacci))}",
            "Bet Structure": [
                "Start with 1 unit at the beginning of the sequence",
                "If you lose, move one step forward in the sequence",
                "If you win, move two steps back in the sequence",
                "If you can't move back two steps, start again at the beginning"
            ],
            "Strategy Explanation": "The Fibonacci system uses the Fibonacci sequence to determine bet sizes. After a loss, move up one step; after a win, move back two steps. This creates a more gradual progression than the Martingale system."
        }
        
        return suggestions
    
    def _detect_number_patterns(self, spins_df):
        """
        Detect patterns in the sequence of numbers.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            dict or None: Detected pattern information
        """
        # Get the last several spins
        numbers = spins_df['number'].tail(20).tolist()
        
        # Look for repeating sequences of length 2-4
        for pattern_length in range(2, 5):
            if len(numbers) < pattern_length * 2:
                continue
                
            # Check if the most recent n numbers repeat elsewhere
            pattern = numbers[-pattern_length:]
            rest = numbers[:-pattern_length]
            
            # Look for the pattern in the rest of the sequence
            for i in range(len(rest) - pattern_length + 1):
                if rest[i:i+pattern_length] == pattern:
                    # Pattern found, predict the next number based on what followed
                    if i + pattern_length < len(rest):
                        return {
                            'pattern': pattern,
                            'predicted': rest[i+pattern_length]
                        }
        
        return None
    
    def _detect_property_patterns(self, spins_df, property_name):
        """
        Detect patterns in a specific property (color, even/odd, etc.).
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            property_name (str): Name of the property to analyze
            
        Returns:
            dict or None: Detected pattern information
        """
        # Get the property values for the last several spins
        values = spins_df[property_name].tail(30).tolist()
        
        # Filter out special values like 'none' (for 0 and 00)
        values = [v for v in values if v not in ['none', 'green']]
        
        if len(values) < 4:
            return None
            
        # Look for repeating patterns of length 2-4
        for pattern_length in range(2, 5):
            if len(values) < pattern_length * 2:
                continue
                
            # Check if the most recent n values repeat elsewhere
            pattern = values[-pattern_length:]
            rest = values[:-pattern_length]
            
            # Look for the pattern in the rest of the sequence
            for i in range(len(rest) - pattern_length + 1):
                if rest[i:i+pattern_length] == pattern:
                    # Pattern found, predict the next value based on what followed
                    if i + pattern_length < len(rest):
                        return {
                            'pattern': pattern,
                            'predicted': rest[i+pattern_length]
                        }
        
        return None
    
    def _find_split_bets(self, numbers):
        """
        Find advantageous split bets based on the given numbers.
        
        Args:
            numbers (list): List of roulette numbers
            
        Returns:
            list: Suggested split bets
        """
        split_bets = []
        number_pairs = {}
        
        # Convert string numbers to integers (except for '00')
        int_numbers = []
        for num in numbers:
            if num != '00':
                int_numbers.append(int(num))
        
        # Find adjacent numbers in the list
        for num in int_numbers:
            # Check if num+1 is in the list
            if num + 1 in int_numbers and num % 3 != 0:
                pair = (num, num + 1)
                number_pairs[pair] = 2
                
            # Check if num+3 is in the list (vertical split)
            if num + 3 in int_numbers and num <= 33:
                pair = (num, num + 3)
                number_pairs[pair] = 2
        
        # Sort by frequency and take top 2
        sorted_pairs = sorted(number_pairs.items(), key=lambda x: x[1], reverse=True)
        
        for (num1, num2), _ in sorted_pairs[:2]:
            split_bets.append(f"Split bet on {num1}/{num2}")
            
        if not split_bets:
            split_bets.append("No advantageous split bets identified")
            
        return split_bets
    
    def _find_corner_bets(self, numbers):
        """
        Find advantageous corner bets based on the given numbers.
        
        Args:
            numbers (list): List of roulette numbers
            
        Returns:
            list: Suggested corner bets
        """
        corner_bets = []
        
        # Convert string numbers to integers (except for '00')
        int_numbers = []
        for num in numbers:
            if num != '00':
                int_numbers.append(int(num))
        
        # Check for corners (groups of 4 adjacent numbers)
        corners = {}
        
        for num in int_numbers:
            # Skip numbers on the right edge of the layout
            if num % 3 == 0:
                continue
                
            # Skip numbers on the bottom row
            if num > 33:
                continue
                
            # Check if this number can form a corner with the numbers to its right and below
            corner = [num, num + 1, num + 3, num + 4]
            
            # Count how many of these numbers are in our list
            count = sum(1 for n in corner if n in int_numbers)
            
            if count >= 2:  # At least half of the corner numbers are in our list
                corners[tuple(corner)] = count
        
        # Sort by count and take top 2
        sorted_corners = sorted(corners.items(), key=lambda x: x[1], reverse=True)
        
        for corner, _ in sorted_corners[:2]:
            corner_list = '/'.join(map(str, corner))
            corner_bets.append(f"Corner bet on {corner_list}")
            
        if not corner_bets:
            corner_bets.append("No advantageous corner bets identified")
            
        return corner_bets
