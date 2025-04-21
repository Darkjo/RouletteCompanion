import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
import collections
import functools

class RouletteAnalyzer:
    """
    Class to analyze roulette spin data and provide insights.
    """
    
    @functools.lru_cache(maxsize=16)
    def get_hot_cold_numbers(self, spins_df, roulette_type, hot_count=5, cold_count=5):
        """
        Get the most frequent (hot) and least frequent (cold) numbers.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            hot_count (int): Number of hot numbers to return
            cold_count (int): Number of cold numbers to return
            
        Returns:
            tuple: (hot_numbers_dict, cold_numbers_dict)
        """
        if spins_df is None or spins_df.empty:
            return {}, {}
            
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
                
        # Sort by count
        number_counts = number_counts.sort_values(ascending=False)
        
        # Get hot and cold numbers
        hot_numbers = number_counts.head(hot_count).to_dict()
        cold_numbers = number_counts.tail(cold_count).to_dict()
        
        return hot_numbers, cold_numbers
        
    def get_even_odd_trend(self, spins_df):
        """
        Analyze the trend of even vs odd numbers.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            dict: Results of the analysis
        """
        if spins_df is None or spins_df.empty:
            return {}
            
        # Filter out 0 and 00
        filtered_df = spins_df[~spins_df['number'].isin(['0', '00'])]
        
        if filtered_df.empty:
            return {}
            
        # Count even/odd occurrences
        even_odd_counts = filtered_df['even_odd'].value_counts()
        
        # Calculate percentages
        total = even_odd_counts.sum()
        even_pct = even_odd_counts.get('even', 0) / total * 100 if total else 0
        odd_pct = even_odd_counts.get('odd', 0) / total * 100 if total else 0
        
        # Check for streaks
        even_odd_list = filtered_df['even_odd'].tolist()
        max_even_streak = self._find_max_streak(even_odd_list, 'even')
        max_odd_streak = self._find_max_streak(even_odd_list, 'odd')
        
        # Calculate the expected probability
        expected_pct = 50.0
        
        # Determine if there's a bias
        threshold = 5.0  # 5% deviation threshold
        even_bias = abs(even_pct - expected_pct) > threshold
        odd_bias = abs(odd_pct - expected_pct) > threshold
        
        # Current trend (last 5 spins)
        recent_trend = filtered_df.tail(5)['even_odd'].value_counts()
        recent_even = recent_trend.get('even', 0)
        recent_odd = recent_trend.get('odd', 0)
        
        return {
            'even_count': even_odd_counts.get('even', 0),
            'odd_count': even_odd_counts.get('odd', 0),
            'even_percentage': even_pct,
            'odd_percentage': odd_pct,
            'max_even_streak': max_even_streak,
            'max_odd_streak': max_odd_streak,
            'even_bias': even_bias,
            'odd_bias': odd_bias,
            'recent_even': recent_even,
            'recent_odd': recent_odd
        }
    
    def get_red_black_trend(self, spins_df):
        """
        Analyze the trend of red vs black numbers.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            dict: Results of the analysis
        """
        if spins_df is None or spins_df.empty:
            return {}
            
        # Filter out green (0 and 00)
        filtered_df = spins_df[spins_df['color'] != 'green']
        
        if filtered_df.empty:
            return {}
            
        # Count red/black occurrences
        red_black_counts = filtered_df['color'].value_counts()
        
        # Calculate percentages
        total = red_black_counts.sum()
        red_pct = red_black_counts.get('red', 0) / total * 100 if total else 0
        black_pct = red_black_counts.get('black', 0) / total * 100 if total else 0
        
        # Check for streaks
        color_list = filtered_df['color'].tolist()
        max_red_streak = self._find_max_streak(color_list, 'red')
        max_black_streak = self._find_max_streak(color_list, 'black')
        
        # Calculate the expected probability
        expected_pct = 50.0
        
        # Determine if there's a bias
        threshold = 5.0  # 5% deviation threshold
        red_bias = abs(red_pct - expected_pct) > threshold
        black_bias = abs(black_pct - expected_pct) > threshold
        
        # Current trend (last 5 spins)
        recent_trend = filtered_df.tail(5)['color'].value_counts()
        recent_red = recent_trend.get('red', 0)
        recent_black = recent_trend.get('black', 0)
        
        return {
            'red_count': red_black_counts.get('red', 0),
            'black_count': red_black_counts.get('black', 0),
            'red_percentage': red_pct,
            'black_percentage': black_pct,
            'max_red_streak': max_red_streak,
            'max_black_streak': max_black_streak,
            'red_bias': red_bias,
            'black_bias': black_bias,
            'recent_red': recent_red,
            'recent_black': recent_black
        }
    
    def get_dozens_trend(self, spins_df):
        """
        Analyze the trend of dozens (1-12, 13-24, 25-36).
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            dict: Results of the analysis
        """
        if spins_df is None or spins_df.empty:
            return {}
            
        # Filter out 0 and 00
        filtered_df = spins_df[spins_df['dozen'] != 'none']
        
        if filtered_df.empty:
            return {}
            
        # Count dozens occurrences
        dozens_counts = filtered_df['dozen'].value_counts()
        
        # Calculate percentages
        total = dozens_counts.sum()
        first_pct = dozens_counts.get('first', 0) / total * 100 if total else 0
        second_pct = dozens_counts.get('second', 0) / total * 100 if total else 0
        third_pct = dozens_counts.get('third', 0) / total * 100 if total else 0
        
        # Check for streaks
        dozens_list = filtered_df['dozen'].tolist()
        max_first_streak = self._find_max_streak(dozens_list, 'first')
        max_second_streak = self._find_max_streak(dozens_list, 'second')
        max_third_streak = self._find_max_streak(dozens_list, 'third')
        
        # Calculate the expected probability
        expected_pct = 33.33
        
        # Determine if there's a bias
        threshold = 5.0  # 5% deviation threshold
        first_bias = abs(first_pct - expected_pct) > threshold
        second_bias = abs(second_pct - expected_pct) > threshold
        third_bias = abs(third_pct - expected_pct) > threshold
        
        # Current trend (last 5 spins)
        recent_trend = filtered_df.tail(5)['dozen'].value_counts()
        recent_first = recent_trend.get('first', 0)
        recent_second = recent_trend.get('second', 0)
        recent_third = recent_trend.get('third', 0)
        
        return {
            'first_dozen_count': dozens_counts.get('first', 0),
            'second_dozen_count': dozens_counts.get('second', 0),
            'third_dozen_count': dozens_counts.get('third', 0),
            'first_dozen_percentage': first_pct,
            'second_dozen_percentage': second_pct,
            'third_dozen_percentage': third_pct,
            'max_first_dozen_streak': max_first_streak,
            'max_second_dozen_streak': max_second_streak,
            'max_third_dozen_streak': max_third_streak,
            'first_dozen_bias': first_bias,
            'second_dozen_bias': second_bias,
            'third_dozen_bias': third_bias,
            'recent_first_dozen': recent_first,
            'recent_second_dozen': recent_second,
            'recent_third_dozen': recent_third
        }
    
    def get_columns_trend(self, spins_df):
        """
        Analyze the trend of columns.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            dict: Results of the analysis
        """
        if spins_df is None or spins_df.empty:
            return {}
            
        # Filter out 0 and 00
        filtered_df = spins_df[spins_df['column'] != 'none']
        
        if filtered_df.empty:
            return {}
            
        # Count columns occurrences
        columns_counts = filtered_df['column'].value_counts()
        
        # Calculate percentages
        total = columns_counts.sum()
        first_pct = columns_counts.get('first', 0) / total * 100 if total else 0
        second_pct = columns_counts.get('second', 0) / total * 100 if total else 0
        third_pct = columns_counts.get('third', 0) / total * 100 if total else 0
        
        # Check for streaks
        columns_list = filtered_df['column'].tolist()
        max_first_streak = self._find_max_streak(columns_list, 'first')
        max_second_streak = self._find_max_streak(columns_list, 'second')
        max_third_streak = self._find_max_streak(columns_list, 'third')
        
        # Calculate the expected probability
        expected_pct = 33.33
        
        # Determine if there's a bias
        threshold = 5.0  # 5% deviation threshold
        first_bias = abs(first_pct - expected_pct) > threshold
        second_bias = abs(second_pct - expected_pct) > threshold
        third_bias = abs(third_pct - expected_pct) > threshold
        
        # Current trend (last 5 spins)
        recent_trend = filtered_df.tail(5)['column'].value_counts()
        recent_first = recent_trend.get('first', 0)
        recent_second = recent_trend.get('second', 0)
        recent_third = recent_trend.get('third', 0)
        
        return {
            'first_column_count': columns_counts.get('first', 0),
            'second_column_count': columns_counts.get('second', 0),
            'third_column_count': columns_counts.get('third', 0),
            'first_column_percentage': first_pct,
            'second_column_percentage': second_pct,
            'third_column_percentage': third_pct,
            'max_first_column_streak': max_first_streak,
            'max_second_column_streak': max_second_streak,
            'max_third_column_streak': max_third_streak,
            'first_column_bias': first_bias,
            'second_column_bias': second_bias,
            'third_column_bias': third_bias,
            'recent_first_column': recent_first,
            'recent_second_column': recent_second,
            'recent_third_column': recent_third
        }
    
    def get_high_low_trend(self, spins_df):
        """
        Analyze the trend of high (19-36) vs low (1-18) numbers.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            dict: Results of the analysis
        """
        if spins_df is None or spins_df.empty:
            return {}
            
        # Filter out 0 and 00
        filtered_df = spins_df[spins_df['high_low'] != 'none']
        
        if filtered_df.empty:
            return {}
            
        # Count high/low occurrences
        high_low_counts = filtered_df['high_low'].value_counts()
        
        # Calculate percentages
        total = high_low_counts.sum()
        high_pct = high_low_counts.get('high', 0) / total * 100 if total else 0
        low_pct = high_low_counts.get('low', 0) / total * 100 if total else 0
        
        # Check for streaks
        high_low_list = filtered_df['high_low'].tolist()
        max_high_streak = self._find_max_streak(high_low_list, 'high')
        max_low_streak = self._find_max_streak(high_low_list, 'low')
        
        # Calculate the expected probability
        expected_pct = 50.0
        
        # Determine if there's a bias
        threshold = 5.0  # 5% deviation threshold
        high_bias = abs(high_pct - expected_pct) > threshold
        low_bias = abs(low_pct - expected_pct) > threshold
        
        # Current trend (last 5 spins)
        recent_trend = filtered_df.tail(5)['high_low'].value_counts()
        recent_high = recent_trend.get('high', 0)
        recent_low = recent_trend.get('low', 0)
        
        return {
            'high_count': high_low_counts.get('high', 0),
            'low_count': high_low_counts.get('low', 0),
            'high_percentage': high_pct,
            'low_percentage': low_pct,
            'max_high_streak': max_high_streak,
            'max_low_streak': max_low_streak,
            'high_bias': high_bias,
            'low_bias': low_bias,
            'recent_high': recent_high,
            'recent_low': recent_low
        }
    
    def find_repeating_patterns(self, spins_df, min_length=2, max_length=5):
        """
        Find repeating patterns in the spin history.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            min_length (int): Minimum pattern length to look for
            max_length (int): Maximum pattern length to look for
            
        Returns:
            list: List of detected patterns
        """
        if spins_df is None or spins_df.empty or len(spins_df) < min_length * 2:
            return []
            
        # Get the sequence of numbers
        numbers = spins_df['number'].tolist()
        
        # Find patterns
        patterns = []
        
        for pattern_length in range(min_length, min(max_length + 1, len(numbers) // 2 + 1)):
            pattern_counts = {}
            
            # Try all possible starting positions
            for i in range(len(numbers) - pattern_length + 1):
                pattern = tuple(numbers[i:i+pattern_length])
                
                if pattern in pattern_counts:
                    pattern_counts[pattern] += 1
                else:
                    pattern_counts[pattern] = 1
            
            # Keep patterns that appear more than once
            for pattern, count in pattern_counts.items():
                if count > 1:
                    patterns.append({
                        'pattern': pattern,
                        'count': count,
                        'length': pattern_length
                    })
        
        # Sort by count (most frequent first) and then by length (longest first)
        patterns.sort(key=lambda x: (-x['count'], -x['length']))
        
        # Limit to top 10 most significant patterns
        return patterns[:10]
    
    def get_session_duration(self, spins_df):
        """
        Calculate the duration of the session.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            str: Session duration in a human-readable format
        """
        if spins_df is None or spins_df.empty or len(spins_df) < 2:
            return "N/A"
            
        # Get the first and last timestamp
        first_spin = spins_df['timestamp'].min()
        last_spin = spins_df['timestamp'].max()
        
        # Calculate duration
        duration = last_spin - first_spin
        
        # Format duration in a human-readable format
        if duration.days > 0:
            return f"{duration.days} days, {duration.seconds // 3600} hours"
        elif duration.seconds // 3600 > 0:
            return f"{duration.seconds // 3600} hours, {(duration.seconds % 3600) // 60} minutes"
        else:
            return f"{(duration.seconds % 3600) // 60} minutes, {duration.seconds % 60} seconds"
    
    def compare_actual_vs_expected(self, spins_df, roulette_type):
        """
        Compare actual occurrence frequencies with expected probabilities.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            pd.DataFrame: DataFrame with comparison data
        """
        if spins_df is None or spins_df.empty:
            return pd.DataFrame()
            
        # Count occurrences of each number
        number_counts = spins_df['number'].value_counts()
        
        # Generate all possible numbers based on roulette type
        all_numbers = [str(i) for i in range(37)]  # 0-36
        if roulette_type == "American":
            all_numbers.append("00")
            
        # Calculate total number of spins
        total_spins = len(spins_df)
        
        # Calculate expected probability for each number
        num_numbers = 37 if roulette_type == "European" else 38
        expected_prob = 1 / num_numbers
        
        # Create comparison DataFrame
        comparison_data = []
        
        for num in all_numbers:
            actual_count = number_counts.get(num, 0)
            actual_prob = actual_count / total_spins if total_spins > 0 else 0
            expected_count = total_spins * expected_prob
            
            comparison_data.append({
                'number': num,
                'actual_count': actual_count,
                'expected_count': expected_count,
                'actual_probability': actual_prob,
                'expected_probability': expected_prob,
                'deviation': actual_count - expected_count
            })
            
        return pd.DataFrame(comparison_data)
    
    def calculate_deviation_from_expected(self, spins_df, roulette_type):
        """
        Calculate deviation of observed frequencies from expected values.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            pd.DataFrame: DataFrame with deviation data
        """
        comparison_df = self.compare_actual_vs_expected(spins_df, roulette_type)
        
        if comparison_df.empty:
            return pd.DataFrame()
            
        # Calculate percent deviation
        comparison_df['percent_deviation'] = (
            comparison_df['deviation'] / comparison_df['expected_count'] * 100
        ).fillna(0)
        
        # Calculate z-score (standardized deviation)
        comparison_df['z_score'] = (
            comparison_df['deviation'] / 
            np.sqrt(comparison_df['expected_count'] * 
                    (1 - comparison_df['expected_probability']))
        ).fillna(0)
        
        # Sort by absolute z-score (most significant deviations first)
        return comparison_df.sort_values(by='z_score', ascending=False)
    
    def chi_square_test(self, spins_df, roulette_type, alpha=0.05):
        """
        Perform a chi-square test to check if the spin distribution is random.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            alpha (float): Significance level
            
        Returns:
            tuple: (chi_square_value, p_value, is_random)
        """
        if spins_df is None or spins_df.empty:
            return 0, 1.0, True
            
        # Get actual vs expected comparison
        comparison_df = self.compare_actual_vs_expected(spins_df, roulette_type)
        
        if comparison_df.empty:
            return 0, 1.0, True
            
        # Extract observed and expected frequencies
        observed = comparison_df['actual_count'].values
        expected = comparison_df['expected_count'].values
        
        # Perform chi-square test
        chi2_stat, p_value = stats.chisquare(observed, expected)
        
        # Check if the distribution is random
        is_random = p_value > alpha
        
        return chi2_stat, p_value, is_random
    
    def simulate_betting(self, spins_df, betting_pattern, initial_bankroll, bet_size, roulette_type):
        """
        Simulate betting on the historical spin data.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            betting_pattern (str): Type of bet to simulate
            initial_bankroll (float): Starting bankroll
            bet_size (float): Size of each bet
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            dict: Results of the simulation
        """
        if spins_df is None or spins_df.empty:
            return {
                'final_bankroll': initial_bankroll,
                'win_rate': 0,
                'bankroll_history': [initial_bankroll]
            }
            
        # Set up the simulation
        bankroll = initial_bankroll
        bankroll_history = [bankroll]
        wins = 0
        losses = 0
        
        # Define payout ratios for different bet types
        payout_ratios = {
            'Red/Black': 1,
            'Even/Odd': 1,
            'High/Low': 1,
            'Dozens': 2,
            'Columns': 2,
            'Single Number': 35
        }
        
        # Simulate betting on each spin
        for _, spin in spins_df.iterrows():
            if bankroll < bet_size:
                # Bankrupt - stop simulation
                break
                
            # Place bet based on the selected pattern
            win = False
            
            if betting_pattern == 'Red/Black':
                # Bet on red (arbitrary choice)
                win = spin['color'] == 'red'
                
            elif betting_pattern == 'Even/Odd':
                # Bet on even (arbitrary choice)
                win = spin['even_odd'] == 'even'
                
            elif betting_pattern == 'High/Low':
                # Bet on high (arbitrary choice)
                win = spin['high_low'] == 'high'
                
            elif betting_pattern == 'Dozens':
                # Bet on first dozen (arbitrary choice)
                win = spin['dozen'] == 'first'
                
            elif betting_pattern == 'Columns':
                # Bet on first column (arbitrary choice)
                win = spin['column'] == 'first'
                
            elif betting_pattern == 'Single Number':
                # Bet on 17 (arbitrary choice)
                win = spin['number'] == '17'
            
            # Update bankroll
            if win:
                bankroll += bet_size * payout_ratios[betting_pattern]
                wins += 1
            else:
                bankroll -= bet_size
                losses += 1
                
            # Record bankroll
            bankroll_history.append(bankroll)
        
        # Calculate win rate
        total_bets = wins + losses
        win_rate = wins / total_bets if total_bets > 0 else 0
        
        return {
            'final_bankroll': bankroll,
            'win_rate': win_rate,
            'bankroll_history': bankroll_history
        }
    
    def _find_max_streak(self, sequence, value):
        """
        Find the maximum consecutive streak of a value in a sequence.
        
        Args:
            sequence (list): Sequence to analyze
            value: Value to look for
            
        Returns:
            int: Length of the maximum streak
        """
        if not sequence:
            return 0
            
        max_streak = 0
        current_streak = 0
        
        for item in sequence:
            if item == value:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
                
        return max_streak
