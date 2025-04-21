import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.dataframe_converter import with_clean_dataframe

class RouletteVisualizer:
    """
    Class to create visualizations of roulette spin data.
    Optimized to work with nested property dictionaries.
    """
    
    @with_clean_dataframe
    def plot_recent_spins(self, spins_df, roulette_type):
        """
        Create a visual representation of recent spin results.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if spins_df is None or spins_df.empty:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No spin data available",
                xaxis_title="Spin number",
                yaxis_title="Result"
            )
            return fig
        
        # Additional implementation details here...
        return fig
    
    @with_clean_dataframe
    def plot_number_frequency(self, spins_df, roulette_type):
        """
        Create a bar chart showing the frequency of each number.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if spins_df is None or spins_df.empty:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No spin data available",
                xaxis_title="Number",
                yaxis_title="Frequency"
            )
            return fig
        
        # Additional implementation details here...
        return fig
    
    @with_clean_dataframe
    def plot_even_odd_distribution(self, spins_df):
        """
        Create a pie chart showing the distribution of even vs odd numbers.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if spins_df is None or spins_df.empty:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No spin data available"
            )
            return fig
        
        # Additional implementation details here...
        return fig
    
    @with_clean_dataframe
    def plot_red_black_distribution(self, spins_df):
        """
        Create a pie chart showing the distribution of red vs black numbers.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if spins_df is None or spins_df.empty:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No spin data available"
            )
            return fig
        
        # Additional implementation details here...
        return fig
    
    @with_clean_dataframe
    def plot_dozens_distribution(self, spins_df):
        """
        Create a bar chart showing the distribution of dozens.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if spins_df is None or spins_df.empty:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No spin data available"
            )
            return fig
        
        # Additional implementation details here...
        return fig
    
    @with_clean_dataframe
    def plot_columns_distribution(self, spins_df):
        """
        Create a bar chart showing the distribution of columns.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if spins_df is None or spins_df.empty:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No spin data available"
            )
            return fig
        
        # Additional implementation details here...
        return fig
    
    @with_clean_dataframe
    def plot_high_low_distribution(self, spins_df):
        """
        Create a pie chart showing the distribution of high vs low numbers.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if spins_df is None or spins_df.empty:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No spin data available"
            )
            return fig
        
        # Additional implementation details here...
        return fig
    
    @with_clean_dataframe
    def plot_betting_strategy_heatmap(self, strategies_data):
        """
        Create a heatmap visualization for betting strategy recommendations.
        
        Args:
            strategies_data (dict): Dictionary of strategies and their outcomes
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if not strategies_data:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No strategy data available"
            )
            return fig
        
        # Additional implementation details here...
        return fig
    
    def _get_color_for_number(self, number, color=None):
        """
        Get the color code for a roulette number.
        
        Args:
            number (str): Roulette number
            color (str, optional): Color if already known
            
        Returns:
            str: CSS color code
        """
        if color == 'red':
            return 'red'
        if color == 'black':
            return 'black'
        if color == 'green' or number == '0' or number == '00':
            return 'green'
        
        # Default fallback logic
        try:
            num = int(number)
            red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
            if num in red_numbers:
                return 'red'
            return 'black'
        except (ValueError, TypeError):
            return 'gray'  # Fallback color
    
    def _get_confidence_color(self, confidence):
        """
        Get a color based on confidence level.
        
        Args:
            confidence (float): Confidence value between 0 and 1
            
        Returns:
            str: CSS color code
        """
        if confidence < 0.3:
            # Red
            intensity = min(255, 100 + int(155 * (confidence / 0.3)))
            return f'rgb({intensity},0,0)'
        elif confidence < 0.7:
            # Yellow
            intensity = min(255, 100 + int(155 * ((confidence - 0.3) / 0.4)))
            return f'rgb({intensity},{intensity},0)'
        else:
            # Green
            intensity = min(255, 100 + int(155 * confidence))
            return f'rgb(0,{intensity},0)'
            
    @with_clean_dataframe
    def plot_actual_vs_expected(self, actual_vs_expected_df):
        """
        Create a visual comparison of actual vs expected frequencies.
        
        Args:
            actual_vs_expected_df (pd.DataFrame): DataFrame with comparison data
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if actual_vs_expected_df is None or actual_vs_expected_df.empty:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No comparison data available"
            )
            return fig
        
        # Additional implementation details here...
        return fig
        
    @with_clean_dataframe
    def plot_deviations(self, deviations_df):
        """
        Create a visualization of deviations from expected frequencies.
        
        Args:
            deviations_df (pd.DataFrame): DataFrame with deviation data
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if deviations_df is None or deviations_df.empty:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No deviation data available"
            )
            return fig
        
        # Additional implementation details here...
        return fig
        
    @with_clean_dataframe
    def plot_bankroll_progression(self, simulation_results):
        """
        Create a line chart showing the bankroll progression over time.
        
        Args:
            simulation_results (dict): Results of the simulation
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if not simulation_results or 'bankroll_history' not in simulation_results:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No simulation data available"
            )
            return fig
        
        # Additional implementation details here...
        return fig