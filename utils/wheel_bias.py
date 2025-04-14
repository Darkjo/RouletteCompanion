"""
Wheel Bias Detection Module

This module provides tools for analyzing and detecting potential biases in a roulette wheel
based on historical spin data. It implements several advanced statistical methods to
identify non-random patterns that may indicate physical imperfections in the wheel.
"""

import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
import math

class WheelBiasDetector:
    """
    Class to detect and analyze potential biases in a roulette wheel.
    """
    
    def __init__(self):
        """Initialize the wheel bias detector with standard wheel layouts."""
        # Define the standard layouts of European and American roulette wheels
        self.european_wheel_layout = [
            0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
        ]
        
        self.american_wheel_layout = [
            0, 28, 9, 26, 30, 11, 7, 20, 32, 17, 5, 22, 34, 15, 3, 24, 36, 13, 1, 00, 27, 10, 25, 29, 12, 8, 19, 31, 18, 6, 21, 33, 16, 4, 23, 35, 14, 2
        ]
        
        # Define diamond sectors (groups of 9 numbers) for European wheel
        self.diamond_sectors = {
            "Sector 1": [22, 18, 29, 7, 28, 12, 35, 3, 26],  # Centered around 0
            "Sector 2": [0, 32, 15, 19, 4, 21, 2, 25, 17],   # Centered around 26
            "Sector 3": [17, 34, 6, 27, 13, 36, 11, 30, 8],  # Centered around 13
            "Sector 4": [8, 23, 10, 5, 24, 16, 33, 1, 20]    # Centered around 5
        }
        
    def get_wheel_layout(self, roulette_type="European"):
        """
        Get the physical layout of numbers on the wheel.
        
        Args:
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            list: The layout of numbers on the wheel
        """
        if roulette_type.lower() == "american":
            return self.american_wheel_layout
        else:
            return self.european_wheel_layout
    
    def analyze_wheel_bias(self, spins_df, roulette_type="European", min_spins=300):
        """
        Perform a comprehensive analysis to detect potential wheel bias.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            min_spins (int): Minimum number of spins for reliable bias detection
            
        Returns:
            dict: Dictionary with bias analysis results
        """
        if len(spins_df) < min_spins:
            return {
                "status": "insufficient_data",
                "message": f"Need at least {min_spins} spins for reliable bias detection. Currently have {len(spins_df)} spins.",
                "recommendations": None,
                "confidence": 0.0
            }
        
        results = {}
        
        # 1. Perform chi-square goodness of fit test
        chi2_results = self.chi_square_analysis(spins_df, roulette_type)
        results["chi_square_test"] = chi2_results
        
        # 2. Analyze sector bias
        sector_bias = self.analyze_sector_bias(spins_df, roulette_type)
        results["sector_bias"] = sector_bias
        
        # 3. Analyze number frequency deviation
        frequency_deviation = self.analyze_frequency_deviation(spins_df, roulette_type)
        results["frequency_deviation"] = frequency_deviation
        
        # 4. Analyze neighbor patterns
        neighbor_patterns = self.analyze_neighbor_patterns(spins_df, roulette_type)
        results["neighbor_patterns"] = neighbor_patterns
        
        # 5. Calculate overall confidence in bias detection
        bias_confidence = self._calculate_bias_confidence(chi2_results, sector_bias, frequency_deviation)
        results["bias_confidence"] = bias_confidence
        
        # 6. Generate specific betting recommendations based on detected bias
        recommendations = self._generate_bias_recommendations(
            spins_df, 
            roulette_type, 
            chi2_results,
            sector_bias, 
            frequency_deviation, 
            neighbor_patterns,
            bias_confidence
        )
        results["recommendations"] = recommendations
        
        # Set overall status
        if bias_confidence > 0.7:
            results["status"] = "significant_bias_detected"
            results["message"] = "Significant wheel bias detected with high confidence."
        elif bias_confidence > 0.4:
            results["status"] = "potential_bias_detected"
            results["message"] = "Potential wheel bias detected with moderate confidence."
        else:
            results["status"] = "no_significant_bias"
            results["message"] = "No significant wheel bias detected based on current data."
        
        return results
    
    def chi_square_analysis(self, spins_df, roulette_type="European"):
        """
        Perform chi-square test to detect deviations from expected frequency.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            dict: Results of the chi-square analysis
        """
        # Count occurrences of each number
        number_counts = Counter(spins_df['number'].astype(str))
        
        # Expected probability for each number
        total_numbers = 37 if roulette_type.lower() == "european" else 38
        expected_probability = 1.0 / total_numbers
        
        # Expected count for each number with total spins
        total_spins = len(spins_df)
        expected_count = total_spins * expected_probability
        
        # Prepare observed and expected frequencies for chi-square test
        observed_values = []
        expected_values = []
        possible_numbers = [str(n) for n in range(37)]
        
        if roulette_type.lower() == "american":
            possible_numbers.append("00")
        
        for num in possible_numbers:
            observed_values.append(number_counts.get(num, 0))
            expected_values.append(expected_count)
        
        # Perform chi-square test
        chi2_stat, p_value = stats.chisquare(observed_values, expected_values)
        
        # Interpret results
        alpha = 0.05
        is_biased = p_value < alpha
        
        # Calculate deviation percentages for each number
        deviations = {}
        for i, num in enumerate(possible_numbers):
            deviation_pct = ((observed_values[i] - expected_values[i]) / expected_values[i]) * 100
            deviations[num] = deviation_pct
        
        # Sort deviations to find most extreme cases
        sorted_deviations = sorted(deviations.items(), key=lambda x: abs(x[1]), reverse=True)
        
        result = {
            "chi2_statistic": float(chi2_stat),
            "p_value": float(p_value),
            "is_biased": is_biased,
            "top_deviations": sorted_deviations[:5],
            "confidence": 1.0 - float(p_value) if is_biased else 0.0
        }
        
        return result
    
    def analyze_sector_bias(self, spins_df, roulette_type="European"):
        """
        Analyze the distribution of results across different sectors of the wheel.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            dict: Results of sector bias analysis
        """
        # Get wheel layout
        wheel_layout = self.get_wheel_layout(roulette_type)
        
        # Define quadrants (quarters of the wheel)
        quadrant_size = len(wheel_layout) // 4
        quadrants = {
            "Quadrant 1": wheel_layout[:quadrant_size],
            "Quadrant 2": wheel_layout[quadrant_size:quadrant_size*2],
            "Quadrant 3": wheel_layout[quadrant_size*2:quadrant_size*3],
            "Quadrant 4": wheel_layout[quadrant_size*3:]
        }
        
        # Count spins in each quadrant
        quadrant_counts = {q: 0 for q in quadrants}
        total_spins = 0
        
        for _, row in spins_df.iterrows():
            num = row['number']
            # Convert '00' to -1 for indexing purposes if American roulette
            if num == '00':
                num = -1
            else:
                num = int(num)
            
            for quadrant_name, quadrant_nums in quadrants.items():
                if num in quadrant_nums or (num == -1 and roulette_type.lower() == "american"):
                    quadrant_counts[quadrant_name] += 1
                    total_spins += 1
                    break
        
        # Expected count per quadrant (assuming uniform distribution)
        expected_count = total_spins / 4
        
        # Calculate deviations
        quadrant_deviations = {}
        for quadrant, count in quadrant_counts.items():
            deviation_pct = ((count - expected_count) / expected_count) * 100
            quadrant_deviations[quadrant] = {
                "count": count,
                "expected": expected_count,
                "deviation_pct": deviation_pct
            }
        
        # Perform chi-square test for quadrant distribution
        observed = list(quadrant_counts.values())
        expected = [expected_count] * 4
        chi2_stat, p_value = stats.chisquare(observed, expected)
        
        # Diamond sector analysis (for European wheel)
        diamond_analysis = None
        if roulette_type.lower() == "european":
            diamond_counts = {sector: 0 for sector in self.diamond_sectors}
            
            for _, row in spins_df.iterrows():
                num = row['number']
                if num == '00':
                    continue
                    
                num = int(num)
                for sector_name, sector_nums in self.diamond_sectors.items():
                    if num in sector_nums:
                        diamond_counts[sector_name] += 1
                        break
            
            # Expected count per diamond sector
            expected_diamond_count = total_spins / 4
            
            # Calculate deviations for diamond sectors
            diamond_deviations = {}
            for sector, count in diamond_counts.items():
                deviation_pct = ((count - expected_diamond_count) / expected_diamond_count) * 100
                diamond_deviations[sector] = {
                    "count": count,
                    "expected": expected_diamond_count,
                    "deviation_pct": deviation_pct
                }
            
            # Perform chi-square test for diamond sector distribution
            observed_diamond = list(diamond_counts.values())
            expected_diamond = [expected_diamond_count] * 4
            diamond_chi2_stat, diamond_p_value = stats.chisquare(observed_diamond, expected_diamond)
            
            diamond_analysis = {
                "sector_counts": diamond_counts,
                "sector_deviations": diamond_deviations,
                "chi2_statistic": float(diamond_chi2_stat),
                "p_value": float(diamond_p_value),
                "is_biased": diamond_p_value < 0.05
            }
        
        # Return the results
        return {
            "quadrant_counts": quadrant_counts,
            "quadrant_deviations": quadrant_deviations,
            "chi2_statistic": float(chi2_stat),
            "p_value": float(p_value),
            "is_biased": p_value < 0.05,
            "diamond_analysis": diamond_analysis,
            "confidence": 1.0 - float(p_value) if p_value < 0.05 else 0.0
        }
    
    def analyze_frequency_deviation(self, spins_df, roulette_type="European"):
        """
        Analyze individual number frequency deviations from expected values.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            dict: Results of frequency deviation analysis
        """
        # Count occurrences of each number
        number_counts = Counter(spins_df['number'].astype(str))
        
        # Expected probability for each number
        total_numbers = 37 if roulette_type.lower() == "european" else 38
        expected_probability = 1.0 / total_numbers
        
        # Expected count for each number with total spins
        total_spins = len(spins_df)
        expected_count = total_spins * expected_probability
        
        # Calculate deviation for each number
        deviations = {}
        for num, count in number_counts.items():
            deviation = count - expected_count
            deviation_pct = (deviation / expected_count) * 100
            std_error = math.sqrt(expected_count * expected_probability * (1 - expected_probability))
            z_score = deviation / std_error if std_error > 0 else 0
            
            # Calculate p-value for this deviation (two-tailed test)
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
            
            deviations[num] = {
                "count": count,
                "expected": expected_count,
                "deviation": deviation,
                "deviation_pct": deviation_pct,
                "z_score": z_score,
                "p_value": p_value,
                "is_significant": p_value < 0.05
            }
        
        # Sort by absolute z-score to find the most extreme deviations
        sorted_deviations = sorted(
            deviations.items(), 
            key=lambda x: abs(x[1]["z_score"]), 
            reverse=True
        )
        
        # Calculate the percentage of numbers showing significant deviation
        significant_count = sum(1 for _, v in deviations.items() if v["is_significant"])
        significant_percentage = (significant_count / len(deviations)) * 100 if deviations else 0
        
        # Overall bias estimate
        # If more than 15% of numbers show significant deviation, likely there is bias
        bias_confidence = min(1.0, significant_percentage / 15.0)
        
        return {
            "number_deviations": deviations,
            "top_deviations": sorted_deviations[:10],
            "significant_percentage": significant_percentage,
            "is_biased": significant_percentage > 15.0,
            "confidence": bias_confidence
        }
    
    def analyze_neighbor_patterns(self, spins_df, roulette_type="European"):
        """
        Analyze patterns between neighboring numbers on the wheel.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            dict: Results of neighbor pattern analysis
        """
        wheel_layout = self.get_wheel_layout(roulette_type)
        
        # Create a mapping of each number to its position on the wheel
        number_positions = {}
        for pos, num in enumerate(wheel_layout):
            number_positions[str(num)] = pos
        
        # If American, add '00'
        if roulette_type.lower() == "american":
            if "00" not in number_positions:
                # Find the position where 00 would be
                zero_pos = number_positions.get("0", 0)
                # In American wheel, 00 is often opposite to 0
                number_positions["00"] = (zero_pos + len(wheel_layout) // 2) % len(wheel_layout)
        
        # Get the sequence of numbers from spins
        spin_numbers = spins_df['number'].astype(str).tolist()
        
        # Analyze sequential spins for neighbor patterns
        transitions = defaultdict(int)
        
        for i in range(len(spin_numbers) - 1):
            current = spin_numbers[i]
            next_num = spin_numbers[i + 1]
            
            # Skip if either number is not in our mapping (shouldn't happen)
            if current not in number_positions or next_num not in number_positions:
                continue
            
            # Calculate the distance between the two numbers on the wheel
            pos1 = number_positions[current]
            pos2 = number_positions[next_num]
            
            # Calculate shortest distance around the wheel (clockwise or counterclockwise)
            wheel_size = len(wheel_layout)
            direct_distance = abs(pos1 - pos2)
            wheel_distance = min(direct_distance, wheel_size - direct_distance)
            
            # Record this distance
            transitions[wheel_distance] += 1
        
        # Calculate expected transition probabilities
        # In a random wheel, transitions should be uniformly distributed
        total_transitions = sum(transitions.values())
        wheel_size = len(wheel_layout)
        
        # Calculate expected counts for each distance
        # For a wheel of size N, the expected distribution of distances is:
        # Distance 1: 2/N (can go clockwise or counterclockwise)
        # Distance 2: 2/N
        # ...
        # Distance N/2: 1/N or 2/N (depending if N is even or odd)
        expected_transitions = {}
        max_distance = wheel_size // 2
        
        for distance in range(1, max_distance + 1):
            if distance == max_distance and wheel_size % 2 == 0:
                # For even-sized wheels, the maximum distance occurs only once
                expected_prob = 1.0 / wheel_size
            else:
                # All other distances can be reached clockwise or counterclockwise
                expected_prob = 2.0 / wheel_size
            
            expected_transitions[distance] = expected_prob * total_transitions
        
        # Compare observed to expected
        distance_analysis = {}
        for distance in range(1, max_distance + 1):
            observed = transitions.get(distance, 0)
            expected = expected_transitions.get(distance, 0)
            
            if expected > 0:
                deviation = observed - expected
                deviation_pct = (deviation / expected) * 100
                
                # Calculate statistical significance
                # Use chi-square test with 1 degree of freedom for each distance
                if observed > 0:  # Avoid division by zero
                    chi2 = ((observed - expected) ** 2) / expected
                    p_value = 1 - stats.chi2.cdf(chi2, 1)
                else:
                    chi2 = 0
                    p_value = 1.0
                
                distance_analysis[distance] = {
                    "observed": observed,
                    "expected": expected,
                    "deviation": deviation,
                    "deviation_pct": deviation_pct,
                    "chi2": chi2,
                    "p_value": p_value,
                    "is_significant": p_value < 0.05
                }
        
        # Check for overall pattern significance
        significant_distances = [d for d, analysis in distance_analysis.items() 
                               if analysis["is_significant"]]
        
        has_pattern = len(significant_distances) > 0
        
        # Calculate confidence based on the strongest pattern
        if has_pattern:
            # Use the smallest p-value as a confidence measure
            min_p_value = min(analysis["p_value"] for analysis in distance_analysis.values())
            confidence = 1.0 - min_p_value
        else:
            confidence = 0.0
        
        return {
            "transitions": dict(transitions),
            "distance_analysis": distance_analysis,
            "has_pattern": has_pattern,
            "significant_distances": significant_distances,
            "confidence": confidence
        }
    
    def _calculate_bias_confidence(self, chi2_results, sector_bias, frequency_deviation):
        """
        Calculate an overall confidence score for wheel bias detection.
        
        Args:
            chi2_results (dict): Results from chi-square analysis
            sector_bias (dict): Results from sector bias analysis
            frequency_deviation (dict): Results from frequency deviation analysis
            
        Returns:
            float: Overall confidence score (0-1)
        """
        # Weights for different analyses
        weights = {
            "chi_square": 0.3,
            "sector_bias": 0.3,
            "frequency_deviation": 0.4
        }
        
        # Calculate weighted confidence
        chi_square_confidence = chi2_results.get("confidence", 0)
        sector_confidence = sector_bias.get("confidence", 0)
        frequency_confidence = frequency_deviation.get("confidence", 0)
        
        overall_confidence = (
            weights["chi_square"] * chi_square_confidence +
            weights["sector_bias"] * sector_confidence +
            weights["frequency_deviation"] * frequency_confidence
        )
        
        return overall_confidence
    
    def _generate_bias_recommendations(self, spins_df, roulette_type, chi2_results, 
                                      sector_bias, frequency_deviation, neighbor_patterns,
                                      bias_confidence):
        """
        Generate betting recommendations based on detected wheel bias.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            chi2_results (dict): Results from chi-square analysis
            sector_bias (dict): Results from sector bias analysis
            frequency_deviation (dict): Results from frequency deviation analysis
            neighbor_patterns (dict): Results from neighbor pattern analysis
            bias_confidence (float): Overall bias confidence
            
        Returns:
            dict: Betting recommendations
        """
        recommendations = {
            "single_numbers": [],
            "sectors": [],
            "patterns": [],
            "overall_strategy": ""
        }
        
        # Only give recommendations if we have reasonable confidence
        if bias_confidence < 0.4:
            recommendations["overall_strategy"] = "No significant bias detected. Stick to standard betting strategies."
            return recommendations
        
        # 1. Recommend individual numbers with significant positive deviation
        if frequency_deviation["is_biased"]:
            biased_numbers = []
            
            for num, data in frequency_deviation["number_deviations"].items():
                if data["is_significant"] and data["deviation"] > 0:
                    confidence = 1.0 - data["p_value"]
                    biased_numbers.append({
                        "number": num,
                        "deviation_pct": data["deviation_pct"],
                        "confidence": confidence
                    })
            
            # Sort by confidence and take top 5
            biased_numbers = sorted(biased_numbers, key=lambda x: x["confidence"], reverse=True)[:5]
            recommendations["single_numbers"] = biased_numbers
        
        # 2. Recommend sectors with significant bias
        if sector_bias["is_biased"]:
            biased_sectors = []
            
            # Check quadrants
            for quadrant, data in sector_bias["quadrant_deviations"].items():
                if data["deviation_pct"] > 10:  # 10% threshold for recommendation
                    biased_sectors.append({
                        "sector": quadrant,
                        "deviation_pct": data["deviation_pct"],
                        "confidence": bias_confidence * 0.8  # Slightly lower confidence for sectors
                    })
            
            # Check diamond sectors for European wheel
            if sector_bias["diamond_analysis"] and roulette_type.lower() == "european":
                for sector, data in sector_bias["diamond_analysis"]["sector_deviations"].items():
                    if data["deviation_pct"] > 15:  # Higher threshold for diamond sectors
                        # Get the numbers in this sector
                        sector_numbers = self.diamond_sectors.get(sector, [])
                        
                        biased_sectors.append({
                            "sector": sector,
                            "numbers": sector_numbers,
                            "deviation_pct": data["deviation_pct"],
                            "confidence": bias_confidence * 0.85
                        })
            
            # Sort by deviation percentage
            biased_sectors = sorted(biased_sectors, key=lambda x: x["deviation_pct"], reverse=True)
            recommendations["sectors"] = biased_sectors
        
        # 3. Recommend based on neighbor patterns
        if neighbor_patterns["has_pattern"]:
            for distance in neighbor_patterns["significant_distances"]:
                data = neighbor_patterns["distance_analysis"][distance]
                
                if data["deviation"] > 0:  # Only recommend if more than expected
                    recommendations["patterns"].append({
                        "type": "neighbor_distance",
                        "distance": distance,
                        "deviation_pct": data["deviation_pct"],
                        "confidence": 1.0 - data["p_value"],
                        "description": f"Numbers separated by {distance} positions on the wheel appear more frequently than expected"
                    })
        
        # 4. Overall strategy recommendation based on confidence level
        if bias_confidence > 0.7:
            recommendations["overall_strategy"] = "Strong bias detected. Focus on the recommended numbers and sectors."
        elif bias_confidence > 0.5:
            recommendations["overall_strategy"] = "Moderate bias detected. Consider the recommended numbers but maintain reasonable bet sizes."
        else:
            recommendations["overall_strategy"] = "Slight bias detected. Use recommendations as supplementary to standard strategies."
        
        return recommendations