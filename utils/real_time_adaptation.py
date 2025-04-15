"""
Real-Time Adaptation Module

This module provides real-time adaptation of betting recommendations based on
the most recent spin results. It detects short-term patterns and biases that
may not be apparent in the full dataset analysis.
"""

import numpy as np
import pandas as pd
from collections import deque, Counter
import math
from scipy import stats


class RealTimeAdapter:
    """
    Class for real-time adaptation of betting strategies and recommendations.
    Detects short-term patterns and adjusts recommendations accordingly.
    """
    
    def __init__(self, window_size=20, min_confidence=0.65):
        """
        Initialize the real-time adapter.
        
        Args:
            window_size (int): Number of most recent spins to consider for short-term patterns
            min_confidence (float): Minimum confidence threshold for recommendations
        """
        self.window_size = window_size
        self.min_confidence = min_confidence
        self.recent_spins = deque(maxlen=window_size)
        self.last_recommendation = None
        
        # Roulette wheel properties
        self.red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        self.black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        
        # European wheel layout (clockwise)
        self.european_wheel = [
            0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10,
            5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
        ]
        
        # American wheel layout (clockwise)
        self.american_wheel = [
            0, 28, 9, 26, 30, 11, 7, 20, 32, 17, 5, 22, 34, 15, 3, 24, 36, 13, 1,
            "00", 27, 10, 25, 29, 12, 8, 19, 31, 18, 6, 21, 33, 16, 4, 23, 35, 14, 2
        ]
        
        # Strategy adaptation weights
        self.strategy_weights = {
            "short_term_frequency": 0.35,
            "runs_streaks": 0.25,
            "recent_sector_bias": 0.25,
            "dealer_signature": 0.15
        }
        
        # Initialize pattern detectors
        self.pattern_memory = {}  # Store detected patterns and their prediction accuracy
    
    def add_spin(self, number, timestamp=None):
        """
        Add a new spin to the real-time tracking window.
        
        Args:
            number (str): The number that came up (including '0' and '00')
            timestamp (datetime, optional): When the spin occurred
        """
        self.recent_spins.append({
            'number': str(number),
            'timestamp': timestamp
        })
        
        # Update pattern detection after adding new spin
        self._update_pattern_detection()
    
    def _get_spin_properties(self, number):
        """
        Get properties of a number (color, even/odd, etc.).
        
        Args:
            number (str): The roulette number
            
        Returns:
            dict: Properties of the number
        """
        if number in ('0', '00'):
            return {
                'number': number,
                'color': 'green',
                'parity': None,
                'dozen': None,
                'column': None,
                'half': None
            }
        
        num = int(number)
        return {
            'number': number,
            'color': 'red' if num in self.red_numbers else 'black',
            'parity': 'even' if num % 2 == 0 else 'odd',
            'dozen': 1 if 1 <= num <= 12 else 2 if 13 <= num <= 24 else 3,
            'column': (num - 1) % 3 + 1,
            'half': 'low' if 1 <= num <= 18 else 'high'
        }
    
    def _update_pattern_detection(self):
        """Update pattern detection based on recent spins."""
        if len(self.recent_spins) < 5:  # Need at least 5 spins to detect patterns
            return
        
        # Extract just the numbers for sequence analysis
        numbers = [spin['number'] for spin in self.recent_spins]
        
        # Look for repeating sequences of length 2-4
        for seq_len in range(2, 5):
            if len(numbers) >= seq_len * 2:  # Need at least two sequences to compare
                self._detect_repeating_sequences(numbers, seq_len)
        
        # Update run/streak detection
        self._detect_property_runs(numbers)
    
    def _detect_repeating_sequences(self, numbers, seq_len):
        """
        Detect repeating sequences of specific length in recent spins.
        
        Args:
            numbers (list): List of spin numbers
            seq_len (int): Length of sequence to detect
        """
        # Check last sequence
        last_seq = tuple(numbers[-seq_len:])
        
        # Look for this sequence in earlier spins
        for i in range(len(numbers) - seq_len * 2 + 1):
            seq = tuple(numbers[i:i+seq_len])
            if seq == last_seq:
                # Found a match, record the sequence and what came next
                next_pos = i + seq_len
                if next_pos < len(numbers) - seq_len:  # If we have data on what came next
                    next_num = numbers[next_pos]
                    
                    # Update pattern memory
                    if seq not in self.pattern_memory:
                        self.pattern_memory[seq] = {'predictions': Counter(), 'hits': 0, 'misses': 0}
                    
                    self.pattern_memory[seq]['predictions'][next_num] += 1
    
    def _detect_property_runs(self, numbers):
        """
        Detect runs/streaks of properties (color, parity, etc.).
        
        Args:
            numbers (list): List of spin numbers
        """
        # Convert to properties
        properties = [self._get_spin_properties(num) for num in numbers]
        
        # Check for streaks in each property
        for prop in ['color', 'parity', 'dozen', 'column', 'half']:
            # Skip green (0, 00) for properties
            values = [p[prop] for p in properties if p[prop] is not None]
            if not values:
                continue
                
            # Check current streak
            current_val = values[-1]
            streak_length = 1
            
            # Count backward to find streak length
            for i in range(len(values) - 2, -1, -1):
                if values[i] == current_val:
                    streak_length += 1
                else:
                    break
            
            # Record notable streaks (4+ in a row)
            if streak_length >= 4:
                streak_key = f"{prop}_{current_val}_{streak_length}"
                if streak_key not in self.pattern_memory:
                    self.pattern_memory[streak_key] = {
                        'property': prop,
                        'value': current_val,
                        'length': streak_length,
                        'detection_time': len(self.recent_spins)
                    }
    
    def get_adaptation_recommendations(self, global_recommendations, roulette_type="European"):
        """
        Generate adapted recommendations based on recent spin patterns.
        
        Args:
            global_recommendations (dict): Base recommendations from the overall analysis
            roulette_type (str): Type of roulette wheel
            
        Returns:
            dict: Adapted recommendations
        """
        if len(self.recent_spins) < self.window_size // 2:
            # Not enough data for reliable adaptation
            # Return the original recommendations with added explanation
            result = global_recommendations.copy()
            result['adapted'] = False
            result['message'] = f"Need more spins for real-time adaptation (minimum {self.window_size // 2} recent spins)."
            result['confidence_explanation'] = "Using statistical analysis only. Real-time adaptation requires more recent spins."
            return result
        
        # Extract numbers for analysis
        numbers = [spin['number'] for spin in self.recent_spins]
        
        # 1. Short-term frequency analysis
        frequency_recommendations = self._analyze_short_term_frequency(numbers, roulette_type)
        
        # 2. Runs/streaks analysis
        streak_recommendations = self._analyze_runs_and_streaks(numbers)
        
        # 3. Recent sector bias analysis
        sector_recommendations = self._analyze_recent_sector_bias(numbers, roulette_type)
        
        # 4. Dealer signature analysis (if available)
        dealer_recommendations = self._analyze_dealer_signature(numbers, roulette_type)
        
        # Combine recommendations with weighting
        adapted_recommendations = self._combine_recommendations(
            global_recommendations,
            frequency_recommendations,
            streak_recommendations,
            sector_recommendations,
            dealer_recommendations
        )
        
        # Instead of nesting recommendations, merge them with our adaptation data
        result = adapted_recommendations['recommendations'].copy()
        
        # Add the adaptation metadata
        result['adapted'] = True
        result['message'] = "Recommendations adapted based on recent spins and detected patterns."
        result['confidence_explanation'] = "Recommendations are enhanced with real-time adaptation from recent spins."
        result['adaptation_confidence'] = adapted_recommendations['confidence']
        
        return result
    
    def _analyze_short_term_frequency(self, numbers, roulette_type):
        """
        Analyze short-term frequency bias in recent spins.
        
        Args:
            numbers (list): List of spin numbers
            roulette_type (str): Type of roulette wheel
            
        Returns:
            dict: Short-term frequency recommendations
        """
        # Count occurrences
        number_counts = Counter(numbers)
        
        # Expected probability for each number
        total_numbers = 37 if roulette_type.lower() == "european" else 38
        expected_probability = 1.0 / total_numbers
        
        # Expected count for each number
        total_spins = len(numbers)
        expected_count = total_spins * expected_probability
        
        # Find numbers that appear more than expected
        hot_numbers = []
        for num, count in number_counts.items():
            if num in ('0', '00'):
                continue  # Skip zero for simplicity
                
            if count > expected_count:
                # Calculate binomial probability for significance
                prob = stats.binom.pmf(count, total_spins, expected_probability)
                confidence = 1 - prob
                
                if confidence > self.min_confidence:
                    hot_numbers.append({
                        'number': num,
                        'count': count,
                        'expected': expected_count,
                        'deviation_pct': ((count - expected_count) / expected_count) * 100,
                        'confidence': confidence
                    })
        
        # Sort by confidence
        hot_numbers = sorted(hot_numbers, key=lambda x: x['confidence'], reverse=True)
        
        return {
            'hot_numbers': hot_numbers,
            'confidence': max([n['confidence'] for n in hot_numbers]) if hot_numbers else 0
        }
    
    def _analyze_runs_and_streaks(self, numbers):
        """
        Analyze runs and streaks in properties (color, parity, etc.).
        
        Args:
            numbers (list): List of spin numbers
            
        Returns:
            dict: Streak-based recommendations
        """
        # Convert to properties
        properties = [self._get_spin_properties(num) for num in numbers]
        
        # Check for property streaks
        streak_recommendations = []
        
        for prop in ['color', 'parity', 'dozen', 'column', 'half']:
            # Get streak lengths for each property value
            values = [p[prop] for p in properties if p[prop] is not None]
            if not values:
                continue
            
            # Check if current streak is long enough to be significant
            current_val = values[-1]
            streak_length = 1
            
            for i in range(len(values) - 2, -1, -1):
                if values[i] == current_val:
                    streak_length += 1
                else:
                    break
            
            # Only consider significant streaks
            if streak_length >= 4:
                # Calculate probability of this streak by chance
                prob = (1/2 if prop in ['color', 'parity', 'half'] else 
                        1/3 if prop in ['dozen', 'column'] else 0)
                
                if prob > 0:
                    # Probability of streak_length or more consecutive outcomes
                    p_value = (prob ** streak_length)
                    confidence = 1 - p_value
                    
                    if confidence > self.min_confidence:
                        # Two possible strategies: follow the streak or bet on its end
                        follow_confidence = confidence * 0.4  # Less confidence in continuation
                        reversal_confidence = confidence * 0.6  # More confidence in eventual reversal
                        
                        streak_recommendations.append({
                            'property': prop,
                            'value': current_val,
                            'streak_length': streak_length,
                            'follow': {
                                'recommendation': f"Continue betting on {prop}={current_val}",
                                'confidence': follow_confidence
                            },
                            'reverse': {
                                'recommendation': f"Bet against {prop}={current_val} (streak likely to end)",
                                'confidence': reversal_confidence
                            }
                        })
        
        # Sort by confidence of the reversal strategy (usually more reliable)
        streak_recommendations = sorted(
            streak_recommendations, 
            key=lambda x: x['reverse']['confidence'], 
            reverse=True
        )
        
        max_confidence = max([s['reverse']['confidence'] for s in streak_recommendations]) if streak_recommendations else 0
        
        return {
            'streaks': streak_recommendations,
            'confidence': max_confidence
        }
    
    def _analyze_recent_sector_bias(self, numbers, roulette_type):
        """
        Analyze bias in wheel sectors based on recent spins.
        
        Args:
            numbers (list): List of spin numbers
            roulette_type (str): Type of roulette wheel
            
        Returns:
            dict: Sector bias recommendations
        """
        # Choose the appropriate wheel layout
        wheel = self.european_wheel if roulette_type.lower() == "european" else self.american_wheel
        
        # Create a mapping of numbers to their positions
        position_map = {str(num): pos for pos, num in enumerate(wheel)}
        
        # Define sectors (8 equal sections around the wheel)
        sector_size = len(wheel) // 8
        sectors = {}
        
        for i in range(8):
            start_pos = i * sector_size
            end_pos = start_pos + sector_size - 1
            if end_pos >= len(wheel):
                end_pos = len(wheel) - 1
            
            sector_numbers = [wheel[pos] for pos in range(start_pos, end_pos + 1)]
            sectors[f"Sector_{i+1}"] = [str(num) for num in sector_numbers]
        
        # Count occurrences in each sector
        sector_counts = {sector: 0 for sector in sectors}
        
        for num in numbers:
            for sector, sector_nums in sectors.items():
                if num in sector_nums:
                    sector_counts[sector] += 1
                    break
        
        # Expected counts
        total_spins = len(numbers)
        expected_count = total_spins / 8  # Equal distribution across 8 sectors
        
        # Find biased sectors
        biased_sectors = []
        for sector, count in sector_counts.items():
            if count > expected_count:
                deviation = count - expected_count
                deviation_pct = (deviation / expected_count) * 100
                
                # Calculate statistical significance (chi-square with 1 df)
                chi2 = ((count - expected_count) ** 2) / expected_count
                p_value = 1 - stats.chi2.cdf(chi2, 1)
                confidence = 1 - p_value
                
                if confidence > self.min_confidence:
                    biased_sectors.append({
                        'sector': sector,
                        'numbers': sectors[sector],
                        'count': count,
                        'expected': expected_count,
                        'deviation_pct': deviation_pct,
                        'confidence': confidence
                    })
        
        # Sort by confidence
        biased_sectors = sorted(biased_sectors, key=lambda x: x['confidence'], reverse=True)
        
        return {
            'sectors': biased_sectors,
            'confidence': max([s['confidence'] for s in biased_sectors]) if biased_sectors else 0
        }
    
    def _analyze_dealer_signature(self, numbers, roulette_type):
        """
        Analyze potential dealer signature patterns in release and drop zones.
        This is more speculative but can provide additional insights.
        
        Args:
            numbers (list): List of spin numbers
            roulette_type (str): Type of roulette wheel
            
        Returns:
            dict: Dealer signature recommendations
        """
        # This is a simplified version of dealer signature analysis
        # In real applications, this would require physical observations
        # of the dealer's behavior and ball drop zones
        
        # For demonstration, we'll check for clustering in specific wheel regions
        wheel = self.european_wheel if roulette_type.lower() == "european" else self.american_wheel
        
        # Create number to position mapping
        position_map = {str(num): pos for pos, num in enumerate(wheel)}
        
        # Convert numbers to positions
        positions = []
        for num in numbers:
            if num in position_map:
                positions.append(position_map[num])
        
        if not positions:
            return {'confidence': 0, 'clusters': []}
        
        # Calculate circular distance between consecutive positions
        distances = []
        for i in range(len(positions) - 1):
            pos1 = positions[i]
            pos2 = positions[i + 1]
            
            wheel_size = len(wheel)
            direct_distance = abs(pos1 - pos2)
            circular_distance = min(direct_distance, wheel_size - direct_distance)
            
            distances.append(circular_distance)
        
        # Check if distances are more clustered than expected by chance
        if not distances:
            return {'confidence': 0, 'clusters': []}
        
        # Calculate variance of distances - lower variance suggests dealer signature
        mean_distance = sum(distances) / len(distances)
        variance = sum((d - mean_distance) ** 2 for d in distances) / len(distances)
        
        # Expected variance for random distribution
        expected_variance = (len(wheel) ** 2) / 12  # Approximation
        
        # If variance is significantly lower than expected, there might be a dealer signature
        variance_ratio = variance / expected_variance
        
        # Calculate confidence
        if variance_ratio < 0.7:  # Threshold for significance
            confidence = (0.7 - variance_ratio) / 0.7  # Scale to 0-1
            
            # Identify potential drop zones
            clusters = self._identify_position_clusters(positions, wheel_size=len(wheel))
            
            return {
                'confidence': confidence,
                'variance_ratio': variance_ratio,
                'clusters': clusters
            }
        
        return {'confidence': 0, 'clusters': []}
    
    def _identify_position_clusters(self, positions, wheel_size, cluster_width=6):
        """
        Identify clusters of positions on the wheel that may indicate drop zones.
        
        Args:
            positions (list): List of wheel positions
            wheel_size (int): Total positions on the wheel
            cluster_width (int): Width of cluster window to consider
            
        Returns:
            list: Potential drop zone clusters
        """
        # Count positions within sliding windows around the wheel
        window_counts = []
        
        for center in range(wheel_size):
            # Define a window centered at this position
            window = [(center + i) % wheel_size for i in range(-cluster_width//2, cluster_width//2 + 1)]
            count = sum(1 for pos in positions if pos in window)
            window_counts.append((center, count))
        
        # Expected count in each window by chance
        expected_count = len(positions) * (cluster_width / wheel_size)
        
        # Find windows with significantly higher counts
        clusters = []
        for center, count in window_counts:
            if count > expected_count * 1.5:  # At least 50% more than expected
                deviation_pct = ((count - expected_count) / expected_count) * 100
                confidence = min(deviation_pct / 100, 0.95)  # Cap at 95%
                
                window = [(center + i) % wheel_size for i in range(-cluster_width//2, cluster_width//2 + 1)]
                numbers = [str(self.european_wheel[pos]) if pos < len(self.european_wheel) else str(self.american_wheel[pos]) 
                           for pos in window]
                
                clusters.append({
                    'center': center,
                    'numbers': numbers,
                    'count': count,
                    'expected': expected_count,
                    'deviation_pct': deviation_pct,
                    'confidence': confidence
                })
        
        # Sort by confidence
        return sorted(clusters, key=lambda x: x['confidence'], reverse=True)
    
    def _combine_recommendations(self, global_recommendations, frequency_rec, streak_rec, 
                               sector_rec, dealer_rec):
        """
        Combine different recommendation sources with appropriate weighting.
        
        Args:
            global_recommendations (dict): Base recommendations from overall analysis
            frequency_rec (dict): Short-term frequency recommendations
            streak_rec (dict): Streak-based recommendations
            sector_rec (dict): Sector bias recommendations
            dealer_rec (dict): Dealer signature recommendations
            
        Returns:
            dict: Combined recommendations
        """
        # Create adapted recommendations object
        adapted_recs = {
            'single_numbers': [],
            'sectors': [],
            'patterns': [],
            'special_bets': [],
            'overall_strategy': ""
        }
        
        # Calculate overall adaptation confidence
        adaptation_confidence = (
            self.strategy_weights["short_term_frequency"] * frequency_rec["confidence"] +
            self.strategy_weights["runs_streaks"] * streak_rec["confidence"] +
            self.strategy_weights["recent_sector_bias"] * sector_rec["confidence"] +
            self.strategy_weights["dealer_signature"] * dealer_rec["confidence"]
        )
        
        # If adaptation confidence is too low, use global recommendations
        if adaptation_confidence < 0.4:
            # Return the original recommendations with our message
            result = global_recommendations.copy()
            result['adapted'] = False
            result['adaptation_confidence'] = adaptation_confidence
            result['message'] = "Real-time adaptation confidence too low, using base recommendations."
            result['confidence_explanation'] = "Using statistical analysis with minimal adaptation."
            return result
        
        # 1. Combine single number recommendations
        number_recs = []
        
        # Add frequency-based recommendations
        for num_data in frequency_rec.get('hot_numbers', []):
            number_recs.append({
                'number': num_data['number'],
                'confidence': num_data['confidence'],
                'source': 'frequency',
                'message': f"Hot in recent spins ({num_data['count']} occurrences)"
            })
        
        # Add sector-based numbers
        for sector_data in sector_rec.get('sectors', []):
            for num in sector_data['numbers']:
                if num not in ('0', '00'):  # Skip zeros
                    number_recs.append({
                        'number': num,
                        'confidence': sector_data['confidence'] * 0.8,  # Lower confidence for individual numbers
                        'source': 'sector',
                        'message': f"In hot sector {sector_data['sector']}"
                    })
        
        # Add dealer signature numbers if available
        for cluster in dealer_rec.get('clusters', []):
            for num in cluster['numbers']:
                if num not in ('0', '00'):  # Skip zeros
                    number_recs.append({
                        'number': num,
                        'confidence': cluster['confidence'] * 0.7,  # Lower confidence (speculative)
                        'source': 'dealer',
                        'message': f"In potential drop zone (dealer signature)"
                    })
        
        # Combine and deduplicate number recommendations
        number_map = {}
        for rec in number_recs:
            num = rec['number']
            if num not in number_map or rec['confidence'] > number_map[num]['confidence']:
                number_map[num] = rec
        
        # Sort by confidence and take top recommendations
        sorted_numbers = sorted(number_map.values(), key=lambda x: x['confidence'], reverse=True)
        adapted_recs['single_numbers'] = sorted_numbers[:5]  # Limit to top 5
        
        # 2. Handle streak/run recommendations
        for streak_data in streak_rec.get('streaks', []):
            # Usually prefer reversal for long streaks
            strategy = 'reverse' if streak_data['streak_length'] >= 6 else 'follow'
            
            adapted_recs['patterns'].append({
                'type': 'streak',
                'property': streak_data['property'],
                'value': streak_data['value'],
                'length': streak_data['streak_length'],
                'strategy': strategy,
                'confidence': streak_data[strategy]['confidence'],
                'recommendation': streak_data[strategy]['recommendation']
            })
        
        # 3. Add sector recommendations
        for sector_data in sector_rec.get('sectors', []):
            adapted_recs['sectors'].append({
                'name': sector_data['sector'],
                'numbers': sector_data['numbers'],
                'confidence': sector_data['confidence'],
                'message': f"Bias detected: {sector_data['deviation_pct']:.1f}% above expected"
            })
        
        # 4. Create overall strategy message
        strategy_components = []
        
        # Add number strategy if we have good single numbers
        if adapted_recs['single_numbers'] and adapted_recs['single_numbers'][0]['confidence'] > 0.7:
            top_numbers = [n['number'] for n in adapted_recs['single_numbers'][:3]]
            strategy_components.append(f"Focus on numbers {', '.join(top_numbers)}")
        
        # Add pattern strategy if applicable
        if adapted_recs['patterns']:
            top_pattern = adapted_recs['patterns'][0]
            if top_pattern['type'] == 'streak':
                if top_pattern['strategy'] == 'follow':
                    strategy_components.append(
                        f"Continue betting on {top_pattern['property']}={top_pattern['value']} " 
                        f"(streak of {top_pattern['length']})"
                    )
                else:
                    strategy_components.append(
                        f"Bet against {top_pattern['property']}={top_pattern['value']} " 
                        f"(streak of {top_pattern['length']} likely to end)"
                    )
        
        # Add sector strategy if applicable
        if adapted_recs['sectors'] and adapted_recs['sectors'][0]['confidence'] > 0.65:
            strategy_components.append(
                f"Focus on the {adapted_recs['sectors'][0]['name']} area of the wheel"
            )
        
        # Combine strategy components
        if strategy_components:
            adapted_recs['overall_strategy'] = "Real-time adaptation strategy: " + ". ".join(strategy_components)
        else:
            adapted_recs['overall_strategy'] = "No strong real-time patterns detected. Use base recommendations."
        
        return {
            'confidence': adaptation_confidence,
            'recommendations': adapted_recs,
            'message': "Recommendations adapted based on real-time patterns."
        }