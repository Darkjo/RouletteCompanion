"""
Advanced Betting Analysis for Roulette
Implements sophisticated betting strategies and analysis including:
- Sector/Neighbors betting analysis
- Split/Corner bet opportunities
- Sleeper number detection
- Wheel heatmaps 
- Progression systems
- Pattern recognition
- Previous hit proximity analysis
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
import plotly.graph_objects as go
import plotly.express as px
from utils.dataframe_converter import with_clean_dataframe

# European wheel number sequence in physical order
EUROPEAN_WHEEL = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]

# American wheel number sequence in physical order
AMERICAN_WHEEL = [0, 28, 9, 26, 30, 11, 7, 20, 32, 17, 5, 22, 34, 15, 3, 24, 36, 13, 1, 00, 27, 10, 25, 29, 12, 8, 19, 31, 18, 6, 21, 33, 16, 4, 23, 35, 14, 2]

# Maps for red/black colors
RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

# Predefined sectors on European wheel
SECTORS = {
    "voisins_du_zero": [22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25],  # Neighbors of Zero
    "tiers_du_cylindre": [33, 16, 24, 5, 10, 23, 8, 30, 11, 36, 13, 27],  # Third of the Wheel
    "orphelins": [17, 34, 6, 1, 20, 14, 31, 9],  # Orphans
}

class AdvancedBettingAnalysis:
    """
    Analyzes roulette spin data for advanced betting strategies,
    focusing on methods that might reveal patterns or biases.
    """
    
    def __init__(self):
        """Initialize the advanced betting analysis system."""
        pass
        
    @with_clean_dataframe
    def get_sleeper_numbers(self, spins_df, roulette_type="European", 
                           min_absence_threshold=20) -> Dict:
        """
        Identify sleeper numbers (numbers that haven't appeared for an unusual time).
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            min_absence_threshold (int): Minimum number of spins to qualify as a sleeper
            
        Returns:
            dict: Dictionary with sleeper number analysis
        """
        if spins_df is None or len(spins_df) < 10:
            return {"sleepers": [], "explanation": "Not enough data (minimum 10 spins needed)"}
        
        total_spins = len(spins_df)
        
        # Create a set of all possible numbers based on roulette type
        all_numbers = set(str(i) for i in range(37))  # 0-36
        if roulette_type == "American":
            all_numbers.add("00")
            
        # Track the last occurrence of each number
        last_seen = {num: -1 for num in all_numbers}
        current_absence = {num: total_spins for num in all_numbers}
        
        # Process the spins in reverse order (oldest to newest)
        for idx, row in spins_df.iloc[::-1].iterrows():
            num = row['number']
            position = total_spins - spins_df.index.get_loc(idx) - 1
            
            if last_seen[num] == -1:
                last_seen[num] = position
                current_absence[num] = total_spins - position - 1
        
        # Expected average gap between appearances
        expected_gap = len(all_numbers)
        
        # Identify sleepers (numbers absent longer than threshold and expected)
        sleepers = []
        for num, absence in current_absence.items():
            if absence >= min_absence_threshold and absence > expected_gap:
                # Calculate how overdue the number is
                overdue_factor = absence / expected_gap
                
                # Create sleeper entry
                sleepers.append({
                    'number': num,
                    'spins_absent': absence,
                    'expected_gap': expected_gap,
                    'overdue_factor': round(overdue_factor, 2),
                    'last_position': last_seen[num] if last_seen[num] != -1 else "Never appeared"
                })
        
        # Sort by overdue factor (most overdue first)
        sleepers.sort(key=lambda x: x['overdue_factor'], reverse=True)
        
        return {
            "sleepers": sleepers,
            "explanation": f"Numbers absent for {min_absence_threshold}+ spins and longer than expected ({expected_gap} spins)."
        }
        
    @with_clean_dataframe
    def analyze_sectors(self, spins_df, roulette_type="European") -> Dict:
        """
        Analyze performance of predefined wheel sectors.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            dict: Dictionary with sector analysis
        """
        if spins_df is None or len(spins_df) < 10:
            return {"sectors": {}, "explanation": "Not enough data (minimum 10 spins needed)"}
        
        wheel = EUROPEAN_WHEEL if roulette_type == "European" else AMERICAN_WHEEL
        total_spins = len(spins_df)
        
        # Count occurrences in each sector
        sector_hits = {sector: 0 for sector in SECTORS}
        for idx, row in spins_df.iterrows():
            num_str = row['number']
            try:
                num = int(num_str) if num_str != "00" else -1
                
                # Check which sector(s) the number belongs to
                for sector, numbers in SECTORS.items():
                    if num in numbers:
                        sector_hits[sector] += 1
            except (ValueError, TypeError):
                # Skip invalid numbers
                continue
        
        # Calculate expected hits and deviations
        sector_analysis = {}
        for sector, hits in sector_hits.items():
            sector_size = len(SECTORS[sector])
            sector_probability = sector_size / (37 if roulette_type == "European" else 38)
            expected_hits = total_spins * sector_probability
            
            # Calculate deviation and z-score
            deviation = hits - expected_hits
            stddev = np.sqrt(expected_hits * (1 - sector_probability))
            z_score = deviation / stddev if stddev > 0 else 0
            
            # Determine if this sector is showing bias
            significance = abs(z_score) > 1.96  # 95% confidence level
            
            sector_analysis[sector] = {
                "numbers": SECTORS[sector],
                "hits": hits,
                "hit_percentage": round(100 * hits / total_spins, 2),
                "expected_hits": round(expected_hits, 2),
                "deviation": round(deviation, 2),
                "z_score": round(z_score, 2),
                "significant_bias": significance,
                "recommendation": "BET" if z_score > 1.0 else ("AVOID" if z_score < -1.0 else "NEUTRAL"),
                "confidence": min(0.95, max(0.5, 0.5 + abs(z_score) / 4))
            }
            
        return {
            "sectors": sector_analysis,
            "explanation": "Sector analysis based on physical wheel segments."
        }
        
    @with_clean_dataframe
    def find_split_corner_opportunities(self, spins_df, roulette_type="European") -> Dict:
        """
        Find opportunities for split bets (2 numbers) and corner bets (4 numbers)
        based on frequency analysis.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            dict: Dictionary with split and corner bet opportunities
        """
        if spins_df is None or len(spins_df) < 20:
            return {
                "split_opportunities": [],
                "corner_opportunities": [],
                "explanation": "Not enough data (minimum 20 spins needed)"
            }
            
        # Convert string numbers to integers for analysis
        numbers = []
        for num_str in spins_df['number']:
            try:
                if num_str == "00":
                    numbers.append(-1)  # Special code for 00
                else:
                    numbers.append(int(num_str))
            except (ValueError, TypeError):
                # Skip invalid entries
                continue
                
        # Get number frequencies
        number_counts = pd.Series(numbers).value_counts()
        total_spins = len(numbers)
        
        # Expected probability for single number
        expected_prob = 1 / (37 if roulette_type == "European" else 38)
        
        # Find hot numbers (appearing more than expected)
        hot_numbers = []
        for num, count in number_counts.items():
            if num < 0:  # Skip 00 for split/corner analysis
                continue
                
            observed_prob = count / total_spins
            if observed_prob > expected_prob * 1.3:  # At least 30% more frequent
                hot_numbers.append(num)
                
        # Define all valid splits (adjacent numbers on the table)
        valid_splits = []
        for row in range(1, 13):  # 12 rows on table
            for col in range(1, 3):  # 3 columns on table
                num = (row - 1) * 3 + col
                if num <= 36:  # Make sure we don't go beyond 36
                    # Horizontal split
                    if col < 3:
                        valid_splits.append((num, num + 1))
                    # Vertical split
                    if row < 12:
                        valid_splits.append((num, num + 3))
        
        # Define all valid corners (4 adjacent numbers on the table)
        valid_corners = []
        for row in range(1, 12):  # 11 rows (to stay within bounds for corners)
            for col in range(1, 3):  # 2 columns (to stay within bounds for corners)
                num = (row - 1) * 3 + col
                if num <= 33:  # Make sure the corner stays within bounds
                    valid_corners.append((num, num + 1, num + 3, num + 4))
        
        # Find promising splits
        split_opportunities = []
        for split in valid_splits:
            # Count how many hot numbers are in this split
            hot_count = sum(1 for num in split if num in hot_numbers)
            if hot_count > 0:
                # Calculate the combined probability
                combined_prob = sum(number_counts.get(num, 0) for num in split) / total_spins
                expected_split_prob = expected_prob * 2  # Two numbers
                
                if combined_prob > expected_split_prob * 1.2:  # At least 20% higher than expected
                    confidence = min(0.9, (combined_prob / expected_split_prob - 1) * 0.5)
                    split_opportunities.append({
                        'numbers': split,
                        'combined_hits': sum(number_counts.get(num, 0) for num in split),
                        'observed_probability': round(combined_prob, 4),
                        'expected_probability': round(expected_split_prob, 4),
                        'deviation_factor': round(combined_prob / expected_split_prob, 2),
                        'confidence': round(confidence, 2)
                    })
        
        # Find promising corners
        corner_opportunities = []
        for corner in valid_corners:
            # Count how many hot numbers are in this corner
            hot_count = sum(1 for num in corner if num in hot_numbers)
            if hot_count > 0:
                # Calculate the combined probability
                combined_prob = sum(number_counts.get(num, 0) for num in corner) / total_spins
                expected_corner_prob = expected_prob * 4  # Four numbers
                
                if combined_prob > expected_corner_prob * 1.2:  # At least 20% higher than expected
                    confidence = min(0.9, (combined_prob / expected_corner_prob - 1) * 0.5)
                    corner_opportunities.append({
                        'numbers': corner,
                        'combined_hits': sum(number_counts.get(num, 0) for num in corner),
                        'observed_probability': round(combined_prob, 4),
                        'expected_probability': round(expected_corner_prob, 4),
                        'deviation_factor': round(combined_prob / expected_corner_prob, 2),
                        'confidence': round(confidence, 2)
                    })
        
        # Sort by confidence
        split_opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        corner_opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            "split_opportunities": split_opportunities[:5],  # Top 5 splits
            "corner_opportunities": corner_opportunities[:5],  # Top 5 corners
            "explanation": "Based on numbers appearing more frequently than expected."
        }
        
    @with_clean_dataframe
    def proximity_analysis(self, spins_df, roulette_type="European") -> Dict:
        """
        Analyze if there's a correlation between numbers hitting based on their
        physical proximity on the wheel.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            dict: Dictionary with proximity analysis
        """
        if spins_df is None or len(spins_df) < 30:
            return {"proximity_patterns": [], "explanation": "Not enough data (minimum 30 spins needed)"}
        
        # Use the correct wheel layout
        wheel = EUROPEAN_WHEEL if roulette_type == "European" else AMERICAN_WHEEL
        wheel_map = {num: idx for idx, num in enumerate(wheel)}
        
        # Convert string numbers to integers
        numbers = []
        for num_str in spins_df['number']:
            try:
                if num_str == "00":
                    numbers.append(-1)  # Special code for double zero
                else:
                    numbers.append(int(num_str))
            except (ValueError, TypeError):
                continue
        
        # Skip if not enough valid numbers
        if len(numbers) < 30:
            return {"proximity_patterns": [], "explanation": "Not enough valid data points"}
        
        # Analyze transitions (distances between consecutive numbers on wheel)
        transitions = []
        for i in range(len(numbers) - 1):
            if numbers[i] >= 0 and numbers[i+1] >= 0:  # Skip transitions involving 00
                idx1 = wheel_map.get(numbers[i])
                idx2 = wheel_map.get(numbers[i+1])
                
                if idx1 is not None and idx2 is not None:
                    # Calculate shortest distance around the wheel
                    wheel_size = len(wheel)
                    distance = min((idx2 - idx1) % wheel_size, (idx1 - idx2) % wheel_size)
                    transitions.append(distance)
        
        # Create histogram of distances
        distance_counts = pd.Series(transitions).value_counts().sort_index()
        
        # Calculate expected distribution (uniform around the wheel)
        wheel_size = len(wheel)
        expected_counts = {}
        for distance in range(wheel_size // 2 + 1):
            # Each distance d has 2 possibilities except for max distance in odd-sized wheel
            if distance == 0:
                count = 1  # Only one way to get distance 0
            elif distance == wheel_size // 2 and wheel_size % 2 == 0:
                count = 1  # Only one way to get max distance in even-sized wheel
            else:
                count = 2  # Two ways to go around (clockwise/counterclockwise)
                
            expected_counts[distance] = count / wheel_size * len(transitions)
        
        # Find significant deviations
        significant_distances = []
        for distance, count in distance_counts.items():
            expected = expected_counts.get(distance, 0)
            if expected > 0:
                deviation = (count - expected) / np.sqrt(expected)
                if abs(deviation) > 1.5:  # Somewhat significant
                    # Find which numbers are this distance apart
                    examples = []
                    for i in range(len(wheel)):
                        j = (i + distance) % wheel_size
                        examples.append((wheel[i], wheel[j]))
                        if len(examples) >= 3:  # Just a few examples
                            break
                    
                    significant_distances.append({
                        'distance': distance,
                        'frequency': int(count),
                        'expected': round(expected, 2),
                        'deviation': round(deviation, 2),
                        'significance': "High" if abs(deviation) > 2 else "Medium",
                        'example_pairs': examples,
                        'suggests': "Proximity bias in wheel" if deviation > 0 else "Avoidance pattern in wheel"
                    })
        
        # Sort by significance of deviation
        significant_distances.sort(key=lambda x: abs(x['deviation']), reverse=True)
        
        return {
            "proximity_patterns": significant_distances,
            "explanation": "Analyzes if certain physical distances on wheel appear more than random"
        }
        
    @with_clean_dataframe
    def create_wheel_heatmap(self, spins_df, roulette_type="European"):
        """
        Generate a heatmap of the roulette wheel showing hot and cold spots.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure with the wheel heatmap
        """
        if spins_df is None or spins_df.empty:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No wheel data available"
            )
            return fig
        
        # Determine which wheel to use
        wheel = EUROPEAN_WHEEL if roulette_type == "European" else AMERICAN_WHEEL
        
        # Count occurrences of each number
        number_counts = {}
        total_spins = len(spins_df)
        
        for idx, row in spins_df.iterrows():
            num_str = row['number']
            try:
                if num_str == "00":
                    num = -1  # Special code for 00
                else:
                    num = int(num_str)
                
                if num in number_counts:
                    number_counts[num] += 1
                else:
                    number_counts[num] = 1
            except (ValueError, TypeError):
                continue
        
        # Calculate expected probability
        expected_prob = 1 / (37 if roulette_type == "European" else 38)
        expected_count = expected_prob * total_spins
        
        # Calculate deviation for each number
        wheel_data = []
        for num in wheel:
            count = number_counts.get(num, 0)
            deviation = (count - expected_count) / expected_count if expected_count > 0 else 0
            
            # Determine color (green for 0, red/black for others)
            if num == 0:
                color = 'green'
            elif num in RED_NUMBERS:
                color = 'red'
            else:
                color = 'black'
                
            wheel_data.append({
                'number': num,
                'count': count,
                'expected': expected_count,
                'deviation': deviation,
                'color': color
            })
        
        # Add 00 for American wheel
        if roulette_type == "American":
            count = number_counts.get(-1, 0)  # -1 is our code for 00
            deviation = (count - expected_count) / expected_count if expected_count > 0 else 0
            wheel_data.append({
                'number': '00',
                'count': count,
                'expected': expected_count,
                'deviation': deviation,
                'color': 'green'
            })
        
        # Create the wheel visualization
        fig = go.Figure()
        
        # Calculate positions for each number on a circle
        num_positions = len(wheel)
        theta = np.linspace(0, 2*np.pi, num_positions, endpoint=False)
        
        # Create data for the circle
        r = [1] * num_positions
        text = [str(data['number']) for data in wheel_data[:num_positions]]
        
        # Calculate marker colors based on deviation
        marker_colors = []
        for data in wheel_data[:num_positions]:
            # Base color from roulette
            base_color = data['color']
            
            # Adjust intensity based on deviation
            deviation = data['deviation']
            
            if base_color == 'red':
                if deviation > 0:
                    # Hot red (more intense)
                    intensity = min(255, 150 + int(105 * min(deviation * 2, 1)))
                    color = f'rgb({intensity},0,0)'
                else:
                    # Cold red (less intense)
                    intensity = max(50, 150 - int(100 * min(abs(deviation) * 2, 1)))
                    color = f'rgb({intensity},0,0)'
            elif base_color == 'black':
                if deviation > 0:
                    # Hot black (more like dark gray)
                    intensity = min(100, 30 + int(70 * min(deviation * 2, 1)))
                    color = f'rgb({intensity},{intensity},{intensity})'
                else:
                    # Cold black (more black)
                    intensity = max(0, 30 - int(30 * min(abs(deviation) * 2, 1)))
                    color = f'rgb({intensity},{intensity},{intensity})'
            else:  # Green
                if deviation > 0:
                    # Hot green (more intense)
                    intensity = min(255, 100 + int(155 * min(deviation * 2, 1)))
                    color = f'rgb(0,{intensity},0)'
                else:
                    # Cold green (less intense)
                    intensity = max(40, 100 - int(60 * min(abs(deviation) * 2, 1)))
                    color = f'rgb(0,{intensity},0)'
                    
            marker_colors.append(color)
        
        # Add the scatter plot representing wheel positions
        fig.add_trace(go.Scatterpolar(
            r=r,
            theta=theta * 180 / np.pi,  # Convert to degrees
            mode='markers+text',
            text=text,
            textfont=dict(color='white', size=12),
            marker=dict(
                size=40,
                color=marker_colors,
                symbol='circle',
                line=dict(color='white', width=1)
            ),
            hovertemplate='Number: %{text}<br>Count: %{customdata[0]}<br>Deviation: %{customdata[1]:.2f}%<extra></extra>',
            customdata=[[data['count'], data['deviation']*100] for data in wheel_data[:num_positions]]
        ))
        
        # Update layout for polar coordinates (wheel)
        fig.update_layout(
            title_text=f"{roulette_type} Roulette Wheel Heatmap",
            polar=dict(
                radialaxis=dict(visible=False, range=[0, 1.2]),
                angularaxis=dict(visible=True, showticklabels=False)
            ),
            showlegend=False,
            height=600,
            width=600,
            margin=dict(l=80, r=80, t=100, b=80)
        )
        
        return fig
        
    @with_clean_dataframe
    def get_progression_system_recommendation(self, spins_df, bankroll, 
                                             risk_tolerance="medium") -> Dict:
        """
        Recommend a betting progression system based on historical data.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            bankroll (float): Current bankroll amount
            risk_tolerance (str): Risk tolerance - 'low', 'medium', or 'high'
            
        Returns:
            dict: Dictionary with progression system recommendations
        """
        if spins_df is None or len(spins_df) < 20:
            return {"progression": None, "explanation": "Not enough data (minimum 20 spins needed)"}
        
        # Analyze win/loss patterns
        if 'result' in spins_df.columns:
            # If we have explicit win/loss data
            win_loss_sequence = spins_df['result'].tolist()
        else:
            # If not, we'll fabricate a sequence based on red/black betting as an example
            win_loss_sequence = []
            for num_str in spins_df['number']:
                try:
                    if num_str == "00" or num_str == "0":
                        win_loss_sequence.append("loss")
                    else:
                        num = int(num_str)
                        if num in RED_NUMBERS:
                            win_loss_sequence.append("win")  # Assuming betting on red
                        else:
                            win_loss_sequence.append("loss")
                except (ValueError, TypeError):
                    win_loss_sequence.append("loss")  # Default to loss for invalid entries
        
        # Calculate streak statistics
        max_winning_streak = 0
        max_losing_streak = 0
        current_winning_streak = 0
        current_losing_streak = 0
        
        for result in win_loss_sequence:
            if result == "win":
                current_winning_streak += 1
                current_losing_streak = 0
                max_winning_streak = max(max_winning_streak, current_winning_streak)
            else:
                current_losing_streak += 1
                current_winning_streak = 0
                max_losing_streak = max(max_losing_streak, current_losing_streak)
        
        # Calculate win rate
        win_count = win_loss_sequence.count("win")
        win_rate = win_count / len(win_loss_sequence) if win_loss_sequence else 0
        
        # Determine bankroll resilience
        # How many units in bankroll (assuming 1 unit = 1% of bankroll)
        bankroll_units = 100
        
        # Recommend progression systems based on characteristics
        systems = [
            {
                "name": "Martingale",
                "description": "Double bet after each loss, reset after win",
                "risk_level": "high",
                "win_streak_benefit": 0.2,
                "loss_streak_penalty": 0.9,
                "bankroll_requirement": 100,  # Units needed to withstand losses
                "best_for": "Short sessions with even-money bets",
                "implementation": "Start with base unit. After loss, bet 2x previous. After win, reset to base."
            },
            {
                "name": "D'Alembert",
                "description": "Add one unit after loss, subtract one after win",
                "risk_level": "medium",
                "win_streak_benefit": 0.4,
                "loss_streak_penalty": 0.6,
                "bankroll_requirement": 40,  # Units needed
                "best_for": "More stable progression with even-money bets",
                "implementation": "Start with base unit. After loss, add one unit. After win, subtract one unit."
            },
            {
                "name": "Fibonacci",
                "description": "Follow Fibonacci sequence after losses, move back two steps after win",
                "risk_level": "medium-high",
                "win_streak_benefit": 0.3,
                "loss_streak_penalty": 0.7,
                "bankroll_requirement": 70,  # Units needed
                "best_for": "Players who want slower progression than Martingale",
                "implementation": "Follow sequence: 1,1,2,3,5,8,13,21,... After loss, move forward. After win, move back two steps."
            },
            {
                "name": "Paroli",
                "description": "Progressive winning system - double after win, reset after loss",
                "risk_level": "medium",
                "win_streak_benefit": 0.8,
                "loss_streak_penalty": 0.2,
                "bankroll_requirement": 30,  # Units needed
                "best_for": "Capitalizing on winning streaks",
                "implementation": "Start with base unit. After win, double bet. Reset after loss or three consecutive wins."
            },
            {
                "name": "Oscar's Grind",
                "description": "Slow progression focused on winning one unit per series",
                "risk_level": "low",
                "win_streak_benefit": 0.5,
                "loss_streak_penalty": 0.3,
                "bankroll_requirement": 20,  # Units needed
                "best_for": "Conservative players with limited bankroll",
                "implementation": "Start with one unit. After win, increase one unit. Don't increase after loss. Series ends when profit is one unit."
            },
            {
                "name": "Flat Betting",
                "description": "Bet the same amount each spin",
                "risk_level": "low",
                "win_streak_benefit": 0.5,
                "loss_streak_penalty": 0.5,
                "bankroll_requirement": 10,  # Units needed
                "best_for": "Simplicity and bankroll preservation",
                "implementation": "Always bet the same amount regardless of wins or losses."
            }
        ]
        
        # Calculate scores for each system based on current conditions
        for system in systems:
            # Base score starts at 100
            score = 100
            
            # Adjust for risk tolerance
            if risk_tolerance == "low":
                if system["risk_level"] == "low":
                    score += 30
                elif system["risk_level"] == "medium":
                    score += 0
                else:
                    score -= 40
            elif risk_tolerance == "medium":
                if system["risk_level"] == "medium":
                    score += 20
                elif system["risk_level"] == "low":
                    score += 10
                elif system["risk_level"] == "medium-high":
                    score += 0
                else:
                    score -= 20
            else:  # high risk tolerance
                if system["risk_level"] == "high":
                    score += 30
                elif system["risk_level"] == "medium-high":
                    score += 20
                elif system["risk_level"] == "medium":
                    score += 10
                else:
                    score += 0
            
            # Adjust for win/loss patterns
            score += (win_rate - 0.5) * 100  # Adjust score based on win rate deviation from 50%
            
            # Adjust for streak characteristics
            score += max_winning_streak * system["win_streak_benefit"] * 10
            score -= max_losing_streak * system["loss_streak_penalty"] * 10
            
            # Adjust for bankroll adequacy
            bankroll_ratio = bankroll_units / system["bankroll_requirement"]
            if bankroll_ratio < 0.5:
                score -= 50  # Serious bankroll issue
            elif bankroll_ratio < 1:
                score -= 25  # Borderline bankroll
            else:
                score += min(25, (bankroll_ratio - 1) * 10)  # Bonus for excess bankroll
                
            # Store the score
            system["score"] = max(0, round(score, 1))
        
        # Sort by score
        systems.sort(key=lambda x: x["score"], reverse=True)
        
        # Return the top 3 recommendations
        return {
            "progression_systems": systems[:3],
            "win_rate": round(win_rate * 100, 1),
            "max_winning_streak": max_winning_streak,
            "max_losing_streak": max_losing_streak,
            "explanation": f"Based on {len(win_loss_sequence)} spins with {win_rate*100:.1f}% win rate."
        }
        
    @with_clean_dataframe
    def analyze_pattern_cycles(self, spins_df) -> Dict:
        """
        Analyze for repeating patterns or cycles in roulette outcomes.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            dict: Dictionary with pattern cycle analysis
        """
        if spins_df is None or len(spins_df) < 30:
            return {"patterns": [], "explanation": "Not enough data (minimum 30 spins needed)"}
        
        # Extract series data for different bet types
        sequences = {
            "red_black": [],
            "even_odd": [],
            "high_low": [],
            "dozens": [],
            "columns": []
        }
        
        for idx, row in spins_df.iterrows():
            num_str = row['number']
            try:
                if num_str == "00" or num_str == "0":
                    # Green number - not part of patterns
                    sequences["red_black"].append("green")
                    sequences["even_odd"].append("green")
                    sequences["high_low"].append("green")
                    sequences["dozens"].append("green")
                    sequences["columns"].append("green")
                else:
                    num = int(num_str)
                    
                    # Red/black
                    sequences["red_black"].append("red" if num in RED_NUMBERS else "black")
                    
                    # Even/odd
                    sequences["even_odd"].append("even" if num % 2 == 0 else "odd")
                    
                    # High/low
                    sequences["high_low"].append("high" if num >= 19 else "low")
                    
                    # Dozens
                    if 1 <= num <= 12:
                        sequences["dozens"].append("1st")
                    elif 13 <= num <= 24:
                        sequences["dozens"].append("2nd")
                    else:
                        sequences["dozens"].append("3rd")
                    
                    # Columns
                    if num % 3 == 1:
                        sequences["columns"].append("1st")
                    elif num % 3 == 2:
                        sequences["columns"].append("2nd")
                    elif num % 3 == 0:
                        sequences["columns"].append("3rd")
                    else:
                        sequences["columns"].append("none")  # Shouldn't happen
            except (ValueError, TypeError):
                # Fallback for any parsing issues
                for key in sequences:
                    sequences[key].append("unknown")
        
        # Look for repeating patterns in the sequences
        pattern_results = []
        
        for seq_type, sequence in sequences.items():
            # Skip if too many unknowns
            if sequence.count("unknown") > len(sequence) * 0.1:
                continue
                
            # Only analyze main values (skip green for red/black, etc.)
            if seq_type == "red_black":
                main_values = ["red", "black"]
            elif seq_type == "even_odd":
                main_values = ["even", "odd"]
            elif seq_type == "high_low":
                main_values = ["high", "low"]
            else:
                main_values = ["1st", "2nd", "3rd"]
            
            # Check for significant biases
            value_counts = {val: sequence.count(val) for val in main_values}
            total_main = sum(value_counts.values())
            
            if total_main == 0:
                continue
                
            # Expected counts
            expected = total_main / len(main_values)
            
            # Check if any values are appearing significantly more or less
            for val, count in value_counts.items():
                if count > 0:
                    deviation = (count - expected) / np.sqrt(expected)
                    if abs(deviation) > 1.96:  # 95% confidence level
                        pattern_results.append({
                            "type": seq_type,
                            "pattern": f"{val} appears {'more' if deviation > 0 else 'less'} than expected",
                            "value": val,
                            "count": count,
                            "expected": round(expected, 2),
                            "deviation": round(deviation, 2),
                            "significant": True,
                            "explanation": f"{val} has appeared {count} times ({count/total_main*100:.1f}%) vs expected {expected:.1f} times ({100/len(main_values):.1f}%)"
                        })
            
            # Check for alternating patterns
            for pattern_len in range(2, 5):  # Look for patterns of length 2, 3, and 4
                # Only check if we have enough data
                if len(sequence) < pattern_len * 5:
                    continue
                    
                # Look for repeating subsequences
                pattern_counts = {}
                for i in range(len(sequence) - pattern_len + 1):
                    pattern = tuple(sequence[i:i+pattern_len])
                    if all(val in main_values for val in pattern):  # Only patterns with main values
                        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
                
                # Find patterns that occur more often than expected
                for pattern, count in pattern_counts.items():
                    # Expected probability of this pattern
                    expected_prob = 1 / (len(main_values) ** pattern_len)
                    expected_count = expected_prob * (len(sequence) - pattern_len + 1)
                    
                    # Check if statistically significant
                    if count > 3 and count > expected_count * 1.5:
                        deviation = (count - expected_count) / np.sqrt(expected_count)
                        if deviation > 1.5:  # Somewhat significant
                            pattern_results.append({
                                "type": seq_type,
                                "pattern": "->".join(pattern),
                                "count": count,
                                "expected": round(expected_count, 2),
                                "deviation": round(deviation, 2),
                                "significant": deviation > 1.96,
                                "explanation": f"Pattern appears {count} times vs expected {expected_count:.1f}"
                            })
        
        # Sort by significance
        pattern_results.sort(key=lambda x: abs(x["deviation"]), reverse=True)
        
        return {
            "patterns": pattern_results[:10],  # Top 10 patterns
            "explanation": "Showing statistically significant patterns in roulette outcomes"
        }