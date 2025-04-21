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
        # Initialize fig variable to avoid UnboundLocalError
        fig = go.Figure()
        
        if spins_df is None or spins_df.empty:
            # Return empty figure
            fig.update_layout(
                title="No spin data available",
                xaxis_title="Spin number",
                yaxis_title="Result"
            )
            return fig
            
        # Get the last 20 spins or fewer if less data is available
        recent_spins = spins_df.sort_values(by='timestamp').tail(20).reset_index(drop=True)
        
        # Extract number and timestamp information
        numbers = recent_spins['number'].tolist()
        timestamps = recent_spins['timestamp']
        
        # Get colors for numbers
        colors = []
        for num in numbers:
            if num == '0' or num == '00':
                colors.append('green')
            else:
                try:
                    int_num = int(num)
                    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
                    if int_num in red_numbers:
                        colors.append('red')
                    else:
                        colors.append('black')
                except ValueError:
                    colors.append('gray')
        
        # Create a subplot with the main chart and the wheel
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            specs=[[{"type": "scatter"}], [{"type": "scatter"}]]
        )
        
        # Add the scatter plot to the top subplot
        fig.add_trace(
            go.Scatter(
                x=list(range(len(recent_spins))),
                y=numbers,
                mode='markers+lines',
                marker=dict(
                    size=20,
                    color=colors,
                    line=dict(width=2, color='black')
                ),
                text=numbers,
                hovertemplate='Spin #%{x}<br>Number: %{text}<br>Time: %{customdata}',
                customdata=timestamps.dt.strftime('%Y-%m-%d %H:%M:%S')
            ),
            row=1, col=1
        )
        
        # Add visual representation of the last result in the bottom subplot
        if len(recent_spins) > 0:
            last_num = numbers[-1]
            last_color = colors[-1]
            
            fig.add_trace(
                go.Scatter(
                    x=[0],
                    y=[0],
                    mode='markers',
                    marker=dict(
                        size=100,
                        color=last_color,
                        line=dict(width=2, color='black')
                    ),
                    text=[f"Last spin: {last_num}"],
                    hoverinfo='text'
                ),
                row=2, col=1
            )
        
        # Update layout
        fig.update_layout(
            title_text="Recent Spin Results",
            showlegend=False,
            height=600,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        # Update axes
        fig.update_xaxes(title_text="Spin Number", row=1, col=1)
        fig.update_yaxes(title_text="Result", row=1, col=1)
        
        # Hide axis in the wheel subplot
        fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, row=2, col=1)
        fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False, row=2, col=1)
        
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
        # Initialize fig variable to avoid UnboundLocalError
        fig = go.Figure()
        
        if spins_df is None or spins_df.empty:
            # Return empty figure
            fig.update_layout(
                title="No spin data available",
                xaxis_title="Number",
                yaxis_title="Frequency"
            )
            return fig
            
        # Count occurrences of each number
        number_counts = spins_df['number'].value_counts().reset_index()
        number_counts.columns = ['number', 'count']
        
        # Get all possible numbers based on roulette type
        all_numbers = [str(i) for i in range(37)]  # 0-36
        if roulette_type == "American":
            all_numbers.append("00")
            
        # Make sure all numbers are in the dataframe
        for num in all_numbers:
            if num not in number_counts['number'].values:
                number_counts = pd.concat([
                    number_counts, 
                    pd.DataFrame({'number': [num], 'count': [0]})
                ], ignore_index=True)
        
        # Sort numbers for better visualization
        try:
            number_counts['sort_value'] = number_counts['number'].apply(
                lambda x: -1 if x == '00' else int(x)
            )
            number_counts = number_counts.sort_values(by='sort_value')
        except:
            # Fallback if there's an issue with sorting
            pass
        
        # Get colors for each number
        colors = []
        for num in number_counts['number']:
            if num == '0' or num == '00':
                colors.append('green')
            else:
                try:
                    int_num = int(num)
                    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
                    if int_num in red_numbers:
                        colors.append('red')
                    else:
                        colors.append('black')
                except ValueError:
                    colors.append('gray')
        
        # Create the bar chart
        fig.add_trace(go.Bar(
            x=number_counts['number'],
            y=number_counts['count'],
            marker_color=colors,
            hovertemplate='Number: %{x}<br>Count: %{y}<extra></extra>'
        ))
        
        # Calculate expected frequency
        total_spins = len(spins_df)
        expected_freq = total_spins / len(all_numbers)
        
        # Add a line for the expected frequency
        fig.add_trace(go.Scatter(
            x=number_counts['number'],
            y=[expected_freq] * len(number_counts),
            mode='lines',
            line=dict(color='rgba(100, 100, 100, 0.5)', width=2, dash='dash'),
            name='Expected'
        ))
        
        # Update layout
        fig.update_layout(
            title_text="Number Frequency Analysis",
            xaxis_title="Number",
            yaxis_title="Frequency",
            showlegend=False,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
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