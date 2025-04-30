"""
Real-time Adaptation Module
Provides utilities for adapting to real-time constraints in roulette betting.
"""

import time
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple, Callable


class RealTimeAdapter:
    """
    Adapts analysis to meet real-time constraints (8-second window between spins).
    Prioritizes computation based on time constraints and importance.
    """
    
    def __init__(self, time_limit: float = 8.0):
        """
        Initialize the real-time adapter.
        
        Args:
            time_limit (float): Maximum time allowed for computation in seconds
        """
        self.time_limit = time_limit
        self.start_time = 0
        self.current_priority = 0
        self.results_cache = {}
        
        # Initialize pattern tracking
        self.recent_spins = []
        self.pattern_memory = {}
    
    def start_timer(self):
        """Start the computation timer."""
        self.start_time = time.time()
        self.current_priority = 0
        self.results_cache = {}
    
    def time_remaining(self) -> float:
        """
        Calculate time remaining before the deadline.
        
        Returns:
            float: Seconds remaining before time limit is reached
        """
        elapsed = time.time() - self.start_time
        return max(0, self.time_limit - elapsed)
    
    def should_continue(self, min_priority: int = 0) -> bool:
        """
        Determine if computation should continue based on time and priority.
        
        Args:
            min_priority (int): Minimum priority level required to continue
            
        Returns:
            bool: True if computation should continue
        """
        if self.time_remaining() <= 0:
            return False
        return self.current_priority <= min_priority
    
    def adaptive_compute(self, function: Callable, *args, priority: int = 0, 
                         default_return: Any = None, **kwargs) -> Any:
        """
        Execute a function with time and priority constraints.
        
        Args:
            function (Callable): Function to execute
            *args: Arguments for the function
            priority (int): Priority level of the computation (0=highest)
            default_return (Any): Default value to return if time runs out
            **kwargs: Keyword arguments for the function
            
        Returns:
            Any: Result of the function or default value
        """
        # Check if we should execute this computation
        if not self.should_continue(priority):
            return default_return
        
        # Update current priority
        self.current_priority = priority
        
        # Cache key for the function call
        cache_key = (function.__name__, args, frozenset(kwargs.items()))
        
        # Check if result is cached
        if cache_key in self.results_cache:
            return self.results_cache[cache_key]
        
        # Execute function
        result = function(*args, **kwargs)
        
        # Cache result
        self.results_cache[cache_key] = result
        
        return result
        
    def add_spin(self, number):
        """
        Add a spin result to the recent history for pattern analysis.
        
        Args:
            number: The number that came up
        """
        # Convert to string for consistency
        number = str(number)
        
        # Add to recent spins
        self.recent_spins.append(number)
        
        # Keep only the last 20 spins
        if len(self.recent_spins) > 20:
            self.recent_spins.pop(0)
            
        # Update pattern memory
        if len(self.recent_spins) >= 3:
            # Look for patterns of length 2 and 3
            for pattern_length in [2, 3]:
                if len(self.recent_spins) >= pattern_length + 1:
                    # Get the last n+1 spins to check if pattern predicted outcome
                    recent = self.recent_spins[-(pattern_length+1):]
                    
                    # The pattern is all but the last number
                    pattern = tuple(recent[:-1])
                    outcome = recent[-1]
                    
                    # Create entry if this is a new pattern
                    if pattern not in self.pattern_memory:
                        self.pattern_memory[pattern] = {
                            'hits': 0,
                            'attempts': 0,
                            'outcomes': {}
                        }
                    
                    # Record if this pattern correctly predicted the outcome
                    if len(pattern) >= 2:
                        # Simple pattern check: if last number in pattern has correlation with outcome
                        if pattern[-1] == outcome:
                            self.pattern_memory[pattern]['hits'] += 1
                    
                    # Track total attempts with this pattern
                    self.pattern_memory[pattern]['attempts'] += 1
                    
                    # Record outcomes
                    if outcome not in self.pattern_memory[pattern]['outcomes']:
                        self.pattern_memory[pattern]['outcomes'][outcome] = 0
                    self.pattern_memory[pattern]['outcomes'][outcome] += 1
    
    def get_adaptation_recommendations(self, statistical_recommendations, roulette_type="European"):
        """
        Adapt the statistical recommendations based on real-time patterns.
        
        Args:
            statistical_recommendations (dict): Recommendations from statistical analysis
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            dict: Adapted recommendations
        """
        # Start with the statistical recommendations
        result = statistical_recommendations.copy()
        
        # If we don't have enough spins for pattern analysis, return statistical recommendations
        if len(self.recent_spins) < 5:
            return result
        
        # Look for strong patterns in the recent history
        for pattern, stats in self.pattern_memory.items():
            # Only consider patterns with sufficient attempts
            if stats['attempts'] >= 3:
                # Calculate hit rate
                hit_rate = stats['hits'] / stats['attempts'] if stats['attempts'] > 0 else 0
                
                # If this pattern has a good hit rate, use it to adjust recommendations
                if hit_rate > 0.6:
                    # Most recent spins that could match the pattern
                    recent = tuple(self.recent_spins[-len(pattern):])
                    
                    # If recent spins match this pattern...
                    if recent == pattern:
                        # Find most likely next number based on pattern outcomes
                        if stats['outcomes']:
                            # Get the most common outcome
                            most_common_outcome = max(stats['outcomes'].items(), key=lambda x: x[1])[0]
                            
                            # Add this as a high-confidence recommendation
                            result["pattern_based"] = {
                                "number": most_common_outcome,
                                "confidence": min(0.8, hit_rate + 0.1),
                                "explanation": f"Based on the pattern {pattern}, the next number is likely to be {most_common_outcome}"
                            }
                            
                            # Also add to single numbers with high confidence
                            result["single_numbers"].insert(0, {
                                "number": most_common_outcome,
                                "count": stats['outcomes'][most_common_outcome],
                                "frequency": f"{hit_rate:.1%}",
                                "deviation": hit_rate / (1/37 if roulette_type == 'European' else 1/38),
                                "confidence": min(0.8, hit_rate + 0.1)
                            })
        
        # Add confidence explanation
        result["confidence_explanation"] = f"Analysis based on {len(self.recent_spins)} recent spins with real-time pattern adaptation."
        
        return result