"""
RL Agent for Roulette Strategy Recommendation
Based on the implementation from ProjectR

Performance optimizations added:
- Caching for expensive calculations
- Progress indicators for long-running operations
- Batch processing for large datasets
"""

import random
import pandas as pd
import streamlit as st
from collections import defaultdict
from time import time

class RLAgent:
    """
    Reinforcement Learning Agent for roulette strategy recommendations.
    Tracks performance and provides strategy suggestions based on accuracy and bankroll.
    
    Performance optimizations:
    - Uses Streamlit caching to avoid redundant calculations
    - Shows progress bars for time-consuming operations
    - Processes large datasets in batches for improved responsiveness
    """
    def __init__(self):
        self.history = []  # Track past spins and context
        self.accuracy = 0.5
        self.alignments = []
        self.performance_log = []  # [(number, strategy, win, payout)]
        self._last_cached_time = time()  # Track when caches were last updated

    def record_alignment(self, success: bool):
        """
        Record if a prediction was successful.
        
        Args:
            success (bool): Whether the prediction was successful
        """
        self.alignments.append(success)
        if len(self.alignments) > 50:
            self.alignments.pop(0)
        self.accuracy = sum(self.alignments) / len(self.alignments) if self.alignments else 0.5

    def record_result(self, number, strategy, win, payout):
        """
        Record the result of a betting round.
        
        Args:
            number (str or int): The number that came up
            strategy (str): The strategy used
            win (bool): Whether the bet won
            payout (float): The payout amount (negative for losses)
        """
        self.performance_log.append({
            'number': number,
            'strategy': strategy,
            'win': win,
            'payout': payout
        })
        if len(self.performance_log) > 100:
            self.performance_log.pop(0)
        self.record_alignment(win)

    def get_accuracy(self) -> float:
        """
        Get the current prediction accuracy.
        
        Returns:
            float: Accuracy as a fraction (0-1)
        """
        return round(self.accuracy, 2)

    def get_recommendation(self, bankroll, confidence=None):
        """
        Suggest strategy based on accuracy, bankroll, and (optionally) prediction confidence.
        
        Args:
            bankroll (float): Current bankroll amount
            confidence (float, optional): Confidence in the current prediction
            
        Returns:
            str: Recommended strategy name
        """
        if confidence is not None:
            if confidence >= 0.7 and bankroll > 150 and self.accuracy > 0.6:
                return "Martingale"
            elif confidence <= 0.4 or bankroll < 50:
                return "Flat"
            elif self.recent_losing_streak() >= 3:
                return "Fibonacci"
            return "Paroli"
        else:
            # fallback if confidence is not provided
            if self.accuracy > 0.65 and bankroll > 150:
                return "Martingale"
            elif self.accuracy < 0.4 or bankroll < 50:
                return "Flat"
            elif self.recent_losing_streak() >= 3:
                return "Fibonacci"
            return "D'Alembert" if bankroll < 100 else "Paroli"

    def get_bet_size_recommendation(self, bankroll):
        """
        Recommend bet size based on bankroll.
        
        Args:
            bankroll (float): Current bankroll amount
            
        Returns:
            float: Recommended bet size
        """
        # Conservative bet sizing - between 1-5% of bankroll
        if bankroll < 50:
            return 1.0  # Minimum bet to protect bankroll
        elif bankroll < 100:
            return round(bankroll * 0.02, 1)  # 2% of bankroll
        elif bankroll < 200:
            return round(bankroll * 0.03, 1)  # 3% of bankroll
        elif bankroll < 500:
            return round(bankroll * 0.04, 1)  # 4% of bankroll
        else:
            return round(bankroll * 0.05, 1)  # 5% of bankroll

    def recent_losing_streak(self):
        """
        Calculate the current consecutive losing streak.
        
        Returns:
            int: Length of the current losing streak
        """
        streak = 0
        for result in reversed(self.alignments):
            if result is False:
                streak += 1
            else:
                break
        return streak

    def reset(self):
        """Reset the agent's state."""
        self.history.clear()
        self.alignments.clear()
        self.performance_log.clear()
        self.accuracy = 0.5

    @st.cache_data(ttl=60)  # Cache for 60 seconds
    def get_cached_summary(_self):
        """
        Cached version of get_summary to avoid redundant calculations.
        The TTL of 60 seconds ensures the cache is refreshed periodically.
        The leading underscore in _self is required for Streamlit caching to work,
        as RLAgent objects are not hashable.
        
        Returns:
            list: Summary statistics for each strategy
        """
        return _self._calculate_summary()
    
    def get_summary(self):
        """
        Get a summary of the agent's performance.
        Uses caching for better performance.
        
        Returns:
            list: Summary statistics for each strategy
        """
        # If we haven't updated for a while, use the cached version
        # This prevents repeated calculations when viewing the same data
        return self.get_cached_summary()
    
    def _calculate_summary(self):
        """
        Internal method to calculate summary statistics.
        
        Returns:
            list: Summary statistics for each strategy
        """
        summary = defaultdict(lambda: {"wins": 0, "losses": 0, "profit": 0})
        
        # Process in batches for better performance with large logs
        batch_size = 20
        log_length = len(self.performance_log)
        
        # Initialize progress bar variable
        progress_bar = None
        
        # Show progress bar if processing a large number of entries
        if log_length > 50:
            progress_bar = st.progress(0)
        
        for i in range(0, log_length, batch_size):
            # Process a batch of entries
            end_idx = min(i + batch_size, log_length)
            batch = self.performance_log[i:end_idx]
            
            for entry in batch:
                strat = entry['strategy']
                summary[strat]['profit'] += entry['payout']
                if entry['win']:
                    summary[strat]['wins'] += 1
                else:
                    summary[strat]['losses'] += 1
            
            # Update progress bar if we're showing one
            if progress_bar is not None:
                progress_bar.progress(min(end_idx / log_length, 1.0))
        
        # Clear progress bar if shown
        if progress_bar is not None:
            progress_bar.empty()

        summary_list = []
        for strat, data in summary.items():
            total = data['wins'] + data['losses']
            win_rate = round(100 * data['wins'] / total, 2) if total else 0
            summary_list.append({
                'strategy': strat,
                'wins': data['wins'],
                'losses': data['losses'],
                'profit': round(data['profit'], 2),
                'win_rate': win_rate
            })
        return summary_list
        
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_cached_bet_recommendations(_self, spins_df, roulette_type, bankroll):
        """
        Cached version of get_specific_bet_recommendations.
        The leading underscore in _self is required for Streamlit caching to work,
        as RLAgent objects are not hashable.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            bankroll (float): Current bankroll amount
            
        Returns:
            dict: Detailed recommendations with confidence scores
        """
        # Create a hash of the dataframe to use as part of the cache key
        # This ensures we recompute if the data changes
        return _self._calculate_bet_recommendations(spins_df, roulette_type, bankroll)
    
    def get_specific_bet_recommendations(self, spins_df, roulette_type, bankroll):
        """
        Provide specific number and bet recommendations based on statistical analysis.
        Uses caching and shows progress indicators for large datasets.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            bankroll (float): Current bankroll amount
            
        Returns:
            dict: Detailed recommendations with confidence scores
        """
        # Use cached version
        return self.get_cached_bet_recommendations(spins_df, roulette_type, bankroll)
        
    def _calculate_bet_recommendations(self, spins_df, roulette_type, bankroll):
        """
        Internal method to calculate bet recommendations with progress indicators.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            bankroll (float): Current bankroll amount
            
        Returns:
            dict: Detailed recommendations with confidence scores
        """
        if spins_df is None or len(spins_df) < 10:
            return {
                "single_numbers": [],
                "columns": {"recommendation": None, "confidence": 0},
                "dozens": {"recommendation": None, "confidence": 0},
                "red_black": {"recommendation": None, "confidence": 0},
                "even_odd": {"recommendation": None, "confidence": 0},
                "high_low": {"recommendation": None, "confidence": 0},
                "split_bets": [],
                "confidence_explanation": "Not enough data for reliable recommendations (minimum 10 spins needed)"
            }
            
        # Initialize result structure
        result = {
            "single_numbers": [],
            "columns": {"recommendation": None, "confidence": 0},
            "dozens": {"recommendation": None, "confidence": 0},
            "red_black": {"recommendation": None, "confidence": 0},
            "even_odd": {"recommendation": None, "confidence": 0},
            "high_low": {"recommendation": None, "confidence": 0},
            "split_bets": [],
            "confidence_explanation": ""
        }
        
        # Define colors for roulette numbers
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        
        # 1. Single Numbers Analysis
        # Get the frequency of each number
        number_counts = spins_df['number'].value_counts()
        total_spins = len(spins_df)
        
        # For European roulette, expected probability is 1/37, for American 1/38
        expected_prob = 1/37 if roulette_type == "European" else 1/38
        
        # Find numbers that appear more frequently than expected
        hot_numbers = []
        
        # Show progress indicator for large datasets
        progress_bar = None
        if len(number_counts) > 30:
            progress_bar = st.progress(0)
            st.caption("Analyzing number frequencies...")
            
        # Process in batches for better performance
        items = list(number_counts.items())
        batch_size = 10
        
        for i in range(0, len(items), batch_size):
            # Process a batch of numbers
            end_idx = min(i + batch_size, len(items))
            batch = items[i:end_idx]
            
            for num, count in batch:
                # Skip 0 and 00 for simplicity
                if num in ['0', '00']: 
                    continue
                    
                observed_prob = count / total_spins
                deviation = observed_prob / expected_prob
                
                # Consider as "hot" if it appears at least 1.5x more than expected
                if deviation >= 1.5:
                    confidence = min(0.9, (deviation - 1) * 0.5)  # Cap confidence at 90%
                    hot_numbers.append({
                        'number': num,
                        'count': count,
                        'frequency': f"{round(observed_prob * 100, 1)}%",
                        'deviation': round(deviation, 2),
                        'confidence': round(confidence, 2)
                    })
            
            # Update progress bar if we're showing one
            if progress_bar is not None:
                progress_bar.progress(min(end_idx / len(items), 1.0))
        
        # Clear progress bar if shown
        if progress_bar is not None:
            progress_bar.empty()
        
        # Sort by deviation and take top 3
        hot_numbers = sorted(hot_numbers, key=lambda x: x['deviation'], reverse=True)[:3]
        result["single_numbers"] = hot_numbers
        
        # 2. Column Analysis
        col1_count = sum(1 for num in spins_df['number'] if num.isdigit() and int(num) % 3 == 1)
        col2_count = sum(1 for num in spins_df['number'] if num.isdigit() and int(num) % 3 == 2)
        col3_count = sum(1 for num in spins_df['number'] if num.isdigit() and int(num) % 3 == 0 and int(num) > 0)
        
        column_counts = {
            "1st column": col1_count,
            "2nd column": col2_count,
            "3rd column": col3_count
        }
        
        # Find the column with highest frequency
        best_column = max(column_counts, key=column_counts.get)
        max_count = column_counts[best_column]
        
        # Calculate confidence based on deviation from expected
        total_column_spins = col1_count + col2_count + col3_count
        expected_col_count = total_column_spins / 3
        
        if total_column_spins > 0:
            column_deviation = max_count / expected_col_count
            column_confidence = min(0.9, (column_deviation - 1) * 1.5)
            
            # Only recommend if confidence is above threshold
            if column_confidence > 0.2:
                result["columns"] = {
                    "recommendation": best_column,
                    "counts": column_counts,
                    "confidence": round(column_confidence, 2)
                }
        
        # 3. Dozen Analysis
        first_dozen = sum(1 for num in spins_df['number'] if num.isdigit() and 1 <= int(num) <= 12)
        second_dozen = sum(1 for num in spins_df['number'] if num.isdigit() and 13 <= int(num) <= 24)
        third_dozen = sum(1 for num in spins_df['number'] if num.isdigit() and 25 <= int(num) <= 36)
        
        dozen_counts = {
            "1st dozen (1-12)": first_dozen,
            "2nd dozen (13-24)": second_dozen,
            "3rd dozen (25-36)": third_dozen
        }
        
        best_dozen = max(dozen_counts, key=dozen_counts.get)
        max_dozen_count = dozen_counts[best_dozen]
        
        total_dozen_spins = first_dozen + second_dozen + third_dozen
        expected_dozen_count = total_dozen_spins / 3
        
        if total_dozen_spins > 0:
            dozen_deviation = max_dozen_count / expected_dozen_count
            dozen_confidence = min(0.9, (dozen_deviation - 1) * 1.5)
            
            if dozen_confidence > 0.2:
                result["dozens"] = {
                    "recommendation": best_dozen,
                    "counts": dozen_counts,
                    "confidence": round(dozen_confidence, 2)
                }
        
        # 4. Red/Black Analysis
        red_count = sum(1 for num in spins_df['number'] if num.isdigit() and int(num) in red_numbers)
        black_count = sum(1 for num in spins_df['number'] if num.isdigit() and int(num) > 0 and int(num) not in red_numbers)
        
        color_counts = {"red": red_count, "black": black_count}
        best_color = max(color_counts, key=color_counts.get)
        max_color_count = color_counts[best_color]
        
        total_color_spins = red_count + black_count
        expected_color_count = total_color_spins / 2
        
        if total_color_spins > 0:
            color_deviation = max_color_count / expected_color_count
            color_confidence = min(0.8, (color_deviation - 1) * 2.0)
            
            if color_confidence > 0.15:
                result["red_black"] = {
                    "recommendation": best_color,
                    "counts": color_counts,
                    "confidence": round(color_confidence, 2)
                }
        
        # 5. Even/Odd Analysis
        even_count = sum(1 for num in spins_df['number'] if num.isdigit() and int(num) > 0 and int(num) % 2 == 0)
        odd_count = sum(1 for num in spins_df['number'] if num.isdigit() and int(num) > 0 and int(num) % 2 == 1)
        
        even_odd_counts = {"even": even_count, "odd": odd_count}
        best_parity = max(even_odd_counts, key=even_odd_counts.get)
        max_parity_count = even_odd_counts[best_parity]
        
        total_parity_spins = even_count + odd_count
        expected_parity_count = total_parity_spins / 2
        
        if total_parity_spins > 0:
            parity_deviation = max_parity_count / expected_parity_count
            parity_confidence = min(0.8, (parity_deviation - 1) * 2.0)
            
            if parity_confidence > 0.15:
                result["even_odd"] = {
                    "recommendation": best_parity,
                    "counts": even_odd_counts,
                    "confidence": round(parity_confidence, 2)
                }
        
        # 6. High/Low Analysis
        low_count = sum(1 for num in spins_df['number'] if num.isdigit() and 1 <= int(num) <= 18)
        high_count = sum(1 for num in spins_df['number'] if num.isdigit() and 19 <= int(num) <= 36)
        
        high_low_counts = {"low (1-18)": low_count, "high (19-36)": high_count}
        best_range = max(high_low_counts, key=high_low_counts.get)
        max_range_count = high_low_counts[best_range]
        
        total_range_spins = low_count + high_count
        expected_range_count = total_range_spins / 2
        
        if total_range_spins > 0:
            range_deviation = max_range_count / expected_range_count
            range_confidence = min(0.8, (range_deviation - 1) * 2.0)
            
            if range_confidence > 0.15:
                result["high_low"] = {
                    "recommendation": best_range,
                    "counts": high_low_counts,
                    "confidence": round(range_confidence, 2)
                }
        
        # 7. Split Bet Analysis
        if hot_numbers:
            # Find potential split bets using hot numbers
            split_bets = []
            
            # Show progress for split bet analysis if there are a lot of hot numbers
            split_progress = None
            if len(hot_numbers) >= 3:
                split_progress = st.progress(0)
                st.caption("Analyzing split bet opportunities...")
            
            for i, hot_num_data in enumerate(hot_numbers):
                hot_num = int(hot_num_data['number'])
                # Find adjacent numbers on the roulette layout
                # This is a simplified approach - actual adjacency depends on roulette wheel layout
                adjacent_numbers = self._get_adjacent_numbers(hot_num)
                
                for adj_num in adjacent_numbers:
                    adj_count = number_counts.get(str(adj_num), 0)
                    if adj_count > 0:
                        combined_frequency = (hot_num_data['count'] + adj_count) / total_spins
                        # Expected frequency for 2 numbers
                        expected_split_freq = expected_prob * 2
                        split_deviation = combined_frequency / expected_split_freq
                        
                        if split_deviation > 1.3:
                            split_confidence = min(0.85, (split_deviation - 1) * 0.7)
                            split_bets.append({
                                'numbers': f"{hot_num}/{adj_num}",
                                'combined_count': hot_num_data['count'] + adj_count,
                                'deviation': round(split_deviation, 2),
                                'confidence': round(split_confidence, 2)
                            })
                
                # Update progress if shown
                if split_progress is not None:
                    split_progress.progress(min((i+1) / len(hot_numbers), 1.0))
            
            # Clear progress if shown
            if split_progress is not None:
                split_progress.empty()
            
            # Sort by deviation and take top 2
            split_bets = sorted(split_bets, key=lambda x: x['deviation'], reverse=True)[:2]
            result["split_bets"] = split_bets
            
        # 8. Corner Bet Analysis
        if hot_numbers:
            corner_bets = self._find_corner_bets(hot_numbers, number_counts, total_spins, expected_prob)
            if corner_bets:
                result["corner_bets"] = corner_bets
        
        # Add explanation based on amount of data
        if total_spins < 20:
            result["confidence_explanation"] = "Limited data available (fewer than 20 spins). Recommendations are not highly reliable."
        elif total_spins < 50:
            result["confidence_explanation"] = "Moderate amount of data (fewer than 50 spins). Recommendations have medium reliability."
        else:
            result["confidence_explanation"] = "Good data sample size. Recommendations have higher reliability, but remember that roulette remains a game of chance."
        
        # Include recommendation for bet sizing based on bankroll and confidence
        highest_confidence = max(
            [result["columns"]["confidence"] if result["columns"]["recommendation"] else 0,
             result["dozens"]["confidence"] if result["dozens"]["recommendation"] else 0,
             result["red_black"]["confidence"] if result["red_black"]["recommendation"] else 0,
             result["even_odd"]["confidence"] if result["even_odd"]["recommendation"] else 0,
             result["high_low"]["confidence"] if result["high_low"]["recommendation"] else 0,
             *[num["confidence"] for num in result["single_numbers"]],
             *[split["confidence"] for split in result["split_bets"]],
             0]  # Include 0 to avoid empty list
        )
        
        bet_size = self.get_bet_size_recommendation(bankroll)
        
        # Adjust bet size based on confidence
        if highest_confidence > 0.6:
            # Slightly increase bet for high confidence
            bet_size = round(bet_size * 1.2, 1)
        elif highest_confidence < 0.3:
            # Reduce bet for low confidence
            bet_size = round(bet_size * 0.8, 1)
            
        result["recommended_bet_size"] = bet_size
        result["highest_confidence"] = round(highest_confidence, 2)
        
        return result
        
    def _get_adjacent_numbers(self, number):
        """
        Get adjacent numbers on a standard roulette layout for split betting.
        
        Args:
            number (int): The central number
            
        Returns:
            list: Adjacent numbers for potential split bets
        """
        # Edge cases
        if number == 0:
            return [1, 2, 3]
        
        # Special cases for numbers on the edges
        if number % 3 == 1:  # Left column: 1, 4, 7, 10, etc.
            if number == 1:
                return [2, 4]
            elif number == 34:
                return [31, 35]
            else:
                return [number+1, number-3, number+3]
        elif number % 3 == 0:  # Right column: 3, 6, 9, 12, etc.
            if number == 3:
                return [2, 6]
            elif number == 36:
                return [33, 35]
            else:
                return [number-1, number-3, number+3]
        else:  # Middle column: 2, 5, 8, 11, etc.
            if number == 2:
                return [1, 3, 5]
            elif number == 35:
                return [32, 34, 36]
            else:
                return [number-1, number+1, number-3, number+3]
                
    def _find_corner_bets(self, hot_numbers, number_counts, total_spins, expected_prob):
        """
        Find potential corner bets (4 numbers in a square) based on hot numbers.
        
        Args:
            hot_numbers (list): List of dictionaries containing hot number data
            number_counts (Series): Frequency counts of all numbers
            total_spins (int): Total number of spins
            expected_prob (float): Expected probability for a single number
            
        Returns:
            list: List of potential corner bet recommendations
        """
        if not hot_numbers:
            return []
        
        # Extract just the numbers from the hot_numbers list
        hot_nums = [int(n['number']) for n in hot_numbers if str(n['number']).isdigit()]
        
        # Dictionary to map hot numbers to their confidence scores
        confidence_map = {int(n['number']): n['confidence'] for n in hot_numbers if str(n['number']).isdigit()}
        
        # Define all valid corner bets on a standard roulette table
        # Each corner is defined by its top-left number, and includes that number plus the 3 adjacent numbers
        all_corners = []
        
        # Generate all possible corner bets (except those involving 0)
        for row in range(1, 12):  # 12 rows on standard layout
            for col in range(1, 3):  # 2 columns (since we're defining by top-left corner)
                base_num = (row - 1) * 3 + col
                if base_num <= 34:  # Ensure we don't go past 36
                    corner = [base_num, base_num + 1, base_num + 3, base_num + 4]
                    all_corners.append(corner)
        
        # Find corners containing at least 1 hot number
        potential_corners = []
        
        for corner in all_corners:
            # Count how many numbers in this corner are hot
            hot_matches = [num for num in corner if num in hot_nums]
            
            if hot_matches:  # At least 1 number in the corner is hot
                # Calculate combined frequency of all 4 numbers
                combined_count = sum(number_counts.get(str(num), 0) for num in corner)
                combined_frequency = combined_count / total_spins
                
                # Expected frequency for 4 numbers
                expected_corner_freq = expected_prob * 4
                corner_deviation = combined_frequency / expected_corner_freq
                
                if corner_deviation > 1.2:  # Threshold for recommendation
                    # Calculate confidence based on deviation and number of hot matches
                    base_confidence = min(0.8, (corner_deviation - 1) * 0.8)
                    
                    # Bonus confidence if multiple hot numbers in corner
                    hot_bonus = len(hot_matches) * 0.05
                    
                    # Additional bonus for high-confidence hot numbers
                    confidence_bonus = sum(confidence_map.get(num, 0) for num in hot_matches) / 10
                    
                    final_confidence = min(0.9, base_confidence + hot_bonus + confidence_bonus)
                    
                    potential_corners.append({
                        'numbers': f"{corner[0]}/{corner[1]}/{corner[2]}/{corner[3]}",
                        'combined_count': combined_count,
                        'hot_matches': len(hot_matches),
                        'deviation': round(corner_deviation, 2),
                        'confidence': round(final_confidence, 2)
                    })
        
        # Sort by confidence, then by deviation
        sorted_corners = sorted(
            potential_corners,
            key=lambda x: (x['confidence'], x['deviation']),
            reverse=True
        )
        
        # Return top 3 corners
        return sorted_corners[:3]