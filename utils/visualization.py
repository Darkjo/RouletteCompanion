import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class RouletteVisualizer:
    """
    Class to create visualizations of roulette spin data.
    """
    
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
            
        # Get the last 20 spins or fewer if less data is available
        recent_spins = spins_df.sort_values(by='timestamp').tail(20).reset_index(drop=True)
        
        # Create a heatmap-like visual representation
        fig = go.Figure()
        
        # Add scatter plot for the spin results
        fig.add_trace(go.Scatter(
            x=list(range(len(recent_spins))),
            y=recent_spins['number'],
            mode='markers+lines',
            marker=dict(
                size=16,
                color=[self._get_color_for_number(num, color) 
                       for num, color in zip(recent_spins['number'], recent_spins['color'])],
                line=dict(width=2, color='black')
            ),
            text=recent_spins['number'],
            hovertemplate='Spin #%{x}<br>Number: %{text}<br>Time: %{customdata}',
            customdata=recent_spins['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        # Add a roulette wheel visualization at the bottom
        wheel_fig = self._create_roulette_wheel(recent_spins.iloc[-1]['number'], roulette_type)
        
        # Create a subplot with the main chart and the wheel
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            specs=[[{"type": "scatter"}], [{"type": "figure"}]]
        )
        
        # Add the scatter plot to the top subplot
        fig.add_trace(
            go.Scatter(
                x=list(range(len(recent_spins))),
                y=recent_spins['number'],
                mode='markers+lines',
                marker=dict(
                    size=20,
                    color=[self._get_color_for_number(num, color) 
                           for num, color in zip(recent_spins['number'], recent_spins['color'])],
                    line=dict(width=2, color='black')
                ),
                text=recent_spins['number'],
                hovertemplate='Spin #%{x}<br>Number: %{text}<br>Time: %{customdata}',
                customdata=recent_spins['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            ),
            row=1, col=1
        )
        
        # Add visual representation of the last result in the bottom subplot
        last_num = recent_spins.iloc[-1]['number']
        last_color = recent_spins.iloc[-1]['color']
        color_code = self._get_color_for_number(last_num, last_color)
        
        fig.add_trace(
            go.Scatter(
                x=[0],
                y=[0],
                mode='markers',
                marker=dict(
                    size=100,
                    color=color_code,
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
                int_num = int(num)
                red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
                if int_num in red_numbers:
                    colors.append('red')
                else:
                    colors.append('black')
        
        # Create the bar chart
        fig = go.Figure()
        
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
            
        # Filter out 0 and 00 (they're neither even nor odd)
        filtered_df = spins_df[spins_df['even_odd'] != 'none']
        
        if filtered_df.empty:
            # Return empty figure if all spins are 0 or 00
            fig = go.Figure()
            fig.update_layout(
                title="No even/odd data available (all spins are 0 or 00)"
            )
            return fig
            
        # Count occurrences of even and odd
        even_odd_counts = filtered_df['even_odd'].value_counts()
        
        # Create the pie chart
        fig = go.Figure(data=[go.Pie(
            labels=even_odd_counts.index,
            values=even_odd_counts.values,
            hole=.4,
            marker_colors=['lightblue', 'lightgreen']
        )])
        
        # Add history trend as a smaller chart
        # Get even/odd over time (last 20 spins or all if less)
        recent_spins = filtered_df.sort_values(by='timestamp').tail(20).reset_index()
        
        # Convert even/odd to 0/1 for easier plotting
        even_odd_numeric = [1 if val == 'even' else 0 for val in recent_spins['even_odd']]
        
        # Create a subplot with the pie chart and trend
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "pie"}, {"type": "scatter"}]]
        )
        
        # Add the pie chart
        fig.add_trace(
            go.Pie(
                labels=even_odd_counts.index,
                values=even_odd_counts.values,
                hole=.4,
                marker_colors=['royalblue', 'darkgreen'],
                textinfo='label+percent',
                insidetextorientation='radial'
            ),
            row=1, col=1
        )
        
        # Add the trend line
        fig.add_trace(
            go.Scatter(
                x=list(range(len(recent_spins))),
                y=even_odd_numeric,
                mode='lines+markers',
                line=dict(color='gray', width=2),
                marker=dict(
                    size=10,
                    color=['royalblue' if val == 1 else 'darkgreen' for val in even_odd_numeric]
                ),
                hovertemplate='Spin #%{x}<br>Result: %{text}<extra></extra>',
                text=recent_spins['even_odd']
            ),
            row=1, col=2
        )
        
        # Update yaxis to show categorical values
        fig.update_yaxes(
            tickmode='array',
            tickvals=[0, 1],
            ticktext=['Odd', 'Even'],
            row=1, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="Even/Odd Distribution Analysis",
            showlegend=False,
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        # Update axes for the trend subplot
        fig.update_xaxes(title_text="Recent Spins", row=1, col=2)
        
        return fig
    
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
            
        # Count occurrences of each color
        color_counts = spins_df['color'].value_counts()
        
        # Create the pie chart
        fig = go.Figure(data=[go.Pie(
            labels=color_counts.index,
            values=color_counts.values,
            hole=.4,
            marker_colors=['red', 'black', 'green']
        )])
        
        # Add history trend as a smaller chart (only for red and black)
        # Get color over time (last 20 spins or all if less)
        recent_spins = spins_df.sort_values(by='timestamp').tail(20).reset_index()
        
        # Create a subplot with the pie chart and trend
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "pie"}, {"type": "scatter"}]]
        )
        
        # Add the pie chart
        fig.add_trace(
            go.Pie(
                labels=color_counts.index,
                values=color_counts.values,
                hole=.4,
                marker_colors=['red', 'black', 'green'],
                textinfo='label+percent',
                insidetextorientation='radial'
            ),
            row=1, col=1
        )
        
        # Convert colors to numeric values for the trend line
        color_to_value = {'red': 1, 'black': 0, 'green': 0.5}
        color_numeric = [color_to_value[color] for color in recent_spins['color']]
        
        # Add the trend line
        fig.add_trace(
            go.Scatter(
                x=list(range(len(recent_spins))),
                y=color_numeric,
                mode='lines+markers',
                line=dict(color='gray', width=2),
                marker=dict(
                    size=10,
                    color=recent_spins['color']
                ),
                hovertemplate='Spin #%{x}<br>Color: %{text}<extra></extra>',
                text=recent_spins['color']
            ),
            row=1, col=2
        )
        
        # Update yaxis to show categorical values
        fig.update_yaxes(
            tickmode='array',
            tickvals=[0, 0.5, 1],
            ticktext=['Black', 'Green', 'Red'],
            row=1, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="Red/Black/Green Distribution Analysis",
            showlegend=False,
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        # Update axes for the trend subplot
        fig.update_xaxes(title_text="Recent Spins", row=1, col=2)
        
        return fig
    
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
            
        # Count occurrences of each dozen
        dozens_counts = spins_df['dozen'].value_counts()
        
        # Apply readable labels
        dozen_labels = {
            'first': '1-12 (First)',
            'second': '13-24 (Second)',
            'third': '25-36 (Third)',
            'none': '0/00'
        }
        
        # Create the bar chart
        fig = go.Figure(data=[go.Bar(
            x=[dozen_labels.get(dozen, dozen) for dozen in dozens_counts.index],
            y=dozens_counts.values,
            marker_color=['goldenrod', 'darkorange', 'firebrick', 'green'],
            hovertemplate='Dozen: %{x}<br>Count: %{y}<extra></extra>'
        )])
        
        # Calculate expected frequency for each category
        total_spins = len(spins_df)
        expected_dozen = total_spins * (12/37)  # Approximate for European roulette
        expected_zero = total_spins * (1/37)    # Approximate for European roulette
        
        # Add expected frequency lines
        dozen_keys = ['first', 'second', 'third', 'none']
        expected_values = [expected_dozen, expected_dozen, expected_dozen, expected_zero]
        
        # Only include dozens that exist in the data
        display_dozens = [dozen for dozen in dozen_keys if dozen in dozens_counts.index]
        display_expected = [
            expected_values[dozen_keys.index(dozen)] 
            for dozen in display_dozens
        ]
        
        fig.add_trace(go.Scatter(
            x=[dozen_labels.get(dozen, dozen) for dozen in display_dozens],
            y=display_expected,
            mode='lines+markers',
            marker=dict(color='rgba(100, 100, 100, 0.8)', size=8),
            line=dict(color='rgba(100, 100, 100, 0.5)', width=2, dash='dash'),
            name='Expected'
        ))
        
        # Update layout
        fig.update_layout(
            title_text="Dozens Distribution Analysis",
            xaxis_title="Dozen",
            yaxis_title="Count",
            showlegend=False,
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        return fig
    
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
            
        # Count occurrences of each column
        columns_counts = spins_df['column'].value_counts()
        
        # Apply readable labels
        column_labels = {
            'first': '1st Column (1,4,7,...,34)',
            'second': '2nd Column (2,5,8,...,35)',
            'third': '3rd Column (3,6,9,...,36)',
            'none': '0/00'
        }
        
        # Create the bar chart
        fig = go.Figure(data=[go.Bar(
            x=[column_labels.get(col, col) for col in columns_counts.index],
            y=columns_counts.values,
            marker_color=['purple', 'teal', 'orange', 'green'],
            hovertemplate='Column: %{x}<br>Count: %{y}<extra></extra>'
        )])
        
        # Calculate expected frequency for each category
        total_spins = len(spins_df)
        expected_column = total_spins * (12/37)  # Approximate for European roulette
        expected_zero = total_spins * (1/37)     # Approximate for European roulette
        
        # Add expected frequency lines
        column_keys = ['first', 'second', 'third', 'none']
        expected_values = [expected_column, expected_column, expected_column, expected_zero]
        
        # Only include columns that exist in the data
        display_columns = [col for col in column_keys if col in columns_counts.index]
        display_expected = [
            expected_values[column_keys.index(col)] 
            for col in display_columns
        ]
        
        fig.add_trace(go.Scatter(
            x=[column_labels.get(col, col) for col in display_columns],
            y=display_expected,
            mode='lines+markers',
            marker=dict(color='rgba(100, 100, 100, 0.8)', size=8),
            line=dict(color='rgba(100, 100, 100, 0.5)', width=2, dash='dash'),
            name='Expected'
        ))
        
        # Update layout
        fig.update_layout(
            title_text="Columns Distribution Analysis",
            xaxis_title="Column",
            yaxis_title="Count",
            showlegend=False,
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        return fig
    
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
            
        # Filter out 0 and 00 (they're neither high nor low)
        filtered_df = spins_df[spins_df['high_low'] != 'none']
        
        if filtered_df.empty:
            # Return empty figure if all spins are 0 or 00
            fig = go.Figure()
            fig.update_layout(
                title="No high/low data available (all spins are 0 or 00)"
            )
            return fig
            
        # Count occurrences of high and low
        high_low_counts = filtered_df['high_low'].value_counts()
        
        # Create the pie chart
        fig = go.Figure(data=[go.Pie(
            labels=high_low_counts.index,
            values=high_low_counts.values,
            hole=.4,
            marker_colors=['crimson', 'mediumblue']
        )])
        
        # Add history trend as a smaller chart
        # Get high/low over time (last 20 spins or all if less)
        recent_spins = filtered_df.sort_values(by='timestamp').tail(20).reset_index()
        
        # Convert high/low to 1/0 for easier plotting
        high_low_numeric = [1 if val == 'high' else 0 for val in recent_spins['high_low']]
        
        # Create a subplot with the pie chart and trend
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "pie"}, {"type": "scatter"}]]
        )
        
        # Add the pie chart
        fig.add_trace(
            go.Pie(
                labels=high_low_counts.index,
                values=high_low_counts.values,
                hole=.4,
                marker_colors=['crimson', 'mediumblue'],
                textinfo='label+percent',
                insidetextorientation='radial'
            ),
            row=1, col=1
        )
        
        # Add the trend line
        fig.add_trace(
            go.Scatter(
                x=list(range(len(recent_spins))),
                y=high_low_numeric,
                mode='lines+markers',
                line=dict(color='gray', width=2),
                marker=dict(
                    size=10,
                    color=['crimson' if val == 1 else 'mediumblue' for val in high_low_numeric]
                ),
                hovertemplate='Spin #%{x}<br>Result: %{text}<extra></extra>',
                text=recent_spins['high_low']
            ),
            row=1, col=2
        )
        
        # Update yaxis to show categorical values
        fig.update_yaxes(
            tickmode='array',
            tickvals=[0, 1],
            ticktext=['Low (1-18)', 'High (19-36)'],
            row=1, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="High/Low Distribution Analysis",
            showlegend=False,
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        # Update axes for the trend subplot
        fig.update_xaxes(title_text="Recent Spins", row=1, col=2)
        
        return fig
    
    def plot_actual_vs_expected(self, comparison_df):
        """
        Create a bar chart comparing actual vs expected occurrences.
        
        Args:
            comparison_df (pd.DataFrame): DataFrame with comparison data
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if comparison_df is None or comparison_df.empty:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No comparison data available"
            )
            return fig
            
        # Sort by number for better visualization
        try:
            comparison_df['sort_value'] = comparison_df['number'].apply(
                lambda x: -1 if x == '00' else int(x)
            )
            comparison_df = comparison_df.sort_values(by='sort_value')
        except:
            # Fallback if there's an issue with sorting
            pass
        
        # Create the bar chart
        fig = go.Figure()
        
        # Add actual occurrences
        fig.add_trace(go.Bar(
            x=comparison_df['number'],
            y=comparison_df['actual_count'],
            name='Actual',
            marker_color='royalblue',
            hovertemplate='Number: %{x}<br>Actual count: %{y}<extra></extra>'
        ))
        
        # Add expected occurrences
        fig.add_trace(go.Bar(
            x=comparison_df['number'],
            y=comparison_df['expected_count'],
            name='Expected',
            marker_color='lightgray',
            hovertemplate='Number: %{x}<br>Expected count: %{y:.1f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title_text="Actual vs Expected Occurrences",
            xaxis_title="Number",
            yaxis_title="Count",
            barmode='group',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        return fig
    
    def plot_deviations(self, deviation_df):
        """
        Create a bar chart showing deviations from expected values.
        
        Args:
            deviation_df (pd.DataFrame): DataFrame with deviation data
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if deviation_df is None or deviation_df.empty:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No deviation data available"
            )
            return fig
            
        # Sort by absolute deviation for better visualization
        deviation_df = deviation_df.sort_values(by='z_score', ascending=False)
        
        # Take top 10 deviations for clarity
        top_deviations = deviation_df.head(10)
        
        # Create the bar chart
        fig = go.Figure()
        
        # Add z-score bars
        fig.add_trace(go.Bar(
            x=top_deviations['number'],
            y=top_deviations['z_score'],
            marker_color=['red' if z > 0 else 'blue' for z in top_deviations['z_score']],
            hovertemplate=(
                'Number: %{x}<br>' +
                'Deviation: %{customdata[0]:.2f}<br>' +
                'Z-score: %{y:.2f}<br>' +
                'Actual: %{customdata[1]}<br>' +
                'Expected: %{customdata[2]:.1f}' +
                '<extra></extra>'
            ),
            customdata=top_deviations[['deviation', 'actual_count', 'expected_count']]
        ))
        
        # Add reference lines for statistical significance
        fig.add_shape(
            type='line',
            x0=-0.5,
            y0=1.96,
            x1=len(top_deviations) - 0.5,
            y1=1.96,
            line=dict(color='green', width=2, dash='dash'),
            name='95% Confidence'
        )
        
        fig.add_shape(
            type='line',
            x0=-0.5,
            y0=-1.96,
            x1=len(top_deviations) - 0.5,
            y1=-1.96,
            line=dict(color='green', width=2, dash='dash'),
            name='95% Confidence'
        )
        
        # Update layout
        fig.update_layout(
            title_text="Significant Deviations from Expected (Z-Score)",
            xaxis_title="Number",
            yaxis_title="Z-Score",
            showlegend=False,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        return fig
    
    def plot_bankroll_progression(self, bankroll_history):
        """
        Create a line chart showing the progression of the bankroll during simulation.
        
        Args:
            bankroll_history (list): List of bankroll values over time
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if not bankroll_history:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No bankroll data available"
            )
            return fig
            
        # Create the line chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=list(range(len(bankroll_history))),
            y=bankroll_history,
            mode='lines',
            line=dict(color='royalblue', width=3),
            fill='tozeroy',
            fillcolor='rgba(65, 105, 225, 0.2)',
            hovertemplate='Spin #%{x}<br>Bankroll: %{y:.2f} units<extra></extra>'
        ))
        
        # Add reference line for initial bankroll
        fig.add_shape(
            type='line',
            x0=0,
            y0=bankroll_history[0],
            x1=len(bankroll_history) - 1,
            y1=bankroll_history[0],
            line=dict(color='gray', width=2, dash='dash'),
            name='Initial Bankroll'
        )
        
        # Update layout
        fig.update_layout(
            title_text="Bankroll Progression During Simulation",
            xaxis_title="Spin Number",
            yaxis_title="Bankroll (units)",
            showlegend=False,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        return fig
    
    def _get_color_for_number(self, number, color):
        """
        Get the color code for a roulette number.
        
        Args:
            number (str): The roulette number
            color (str): The color property from the data
            
        Returns:
            str: Color code
        """
        if color == 'red':
            return 'red'
        elif color == 'black':
            return 'black'
        else:  # green for 0 and 00
            return 'green'
    
    def _create_roulette_wheel(self, last_number, roulette_type):
        """
        Create a simple visual representation of a roulette wheel with the last number highlighted.
        
        Args:
            last_number (str): The last spin result
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        # This is a simplified representation
        fig = go.Figure()
        
        # Define wheel segments
        segment_count = 37 if roulette_type == "European" else 38
        
        # Display the last number in the center of the wheel
        fig.add_trace(go.Scatter(
            x=[0],
            y=[0],
            mode='text',
            text=[last_number],
            textfont=dict(size=24, color='white'),
            hoverinfo='none'
        ))
        
        # Update layout
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, b=0, l=0, r=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-1, 1]
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-1, 1]
            )
        )
        
        return fig
