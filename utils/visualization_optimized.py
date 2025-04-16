import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class RouletteVisualizer:
    """
    Class to create visualizations of roulette spin data.
    Optimized to work with nested property dictionaries.
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
        
        # Extract properties from the nested dictionary structure
        numbers = recent_spins['number'].tolist()
        timestamps = recent_spins['timestamp']
        
        # Extract color information from properties
        colors = []
        for _, row in recent_spins.iterrows():
            if 'properties' in row and isinstance(row['properties'], dict):
                colors.append(row['properties'].get('color', 'black'))
            else:
                # Default to black if properties not available
                colors.append('black')
        
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
                    color=[self._get_color_for_number(num, color) 
                           for num, color in zip(numbers, colors)],
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
        
        # Extract parity from properties
        parity_values = []
        for _, row in spins_df.iterrows():
            if 'properties' in row and isinstance(row['properties'], dict):
                parity_values.append(row['properties'].get('parity', 'zero'))
            else:
                # Default if properties not available
                parity_values.append('zero')
        
        # Filter out zeros (they're neither even nor odd)
        parity_df = pd.DataFrame({'parity': parity_values})
        filtered_df = parity_df[parity_df['parity'] != 'zero']
        
        if filtered_df.empty:
            # Return empty figure if all spins are 0 or 00
            fig = go.Figure()
            fig.update_layout(
                title="No even/odd data available (all spins are 0 or 00)"
            )
            return fig
            
        # Count occurrences of even and odd
        even_odd_counts = filtered_df['parity'].value_counts()
        
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
        
        # Get recent spins for trend
        recent_values = parity_values[-20:] if len(parity_values) > 20 else parity_values
        
        # Convert even/odd to 0/1 for easier plotting
        even_odd_numeric = [1 if val == 'even' else 0 for val in recent_values if val != 'zero']
        recent_labels = [val for val in recent_values if val != 'zero']
        
        if even_odd_numeric:  # Only add if we have data
            # Add the trend line
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(even_odd_numeric))),
                    y=even_odd_numeric,
                    mode='lines+markers',
                    line=dict(color='gray', width=2),
                    marker=dict(
                        size=10,
                        color=['royalblue' if val == 1 else 'darkgreen' for val in even_odd_numeric]
                    ),
                    hovertemplate='Spin #%{x}<br>Result: %{text}<extra></extra>',
                    text=recent_labels
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
        
        # Extract color from properties
        color_values = []
        for _, row in spins_df.iterrows():
            if 'properties' in row and isinstance(row['properties'], dict):
                color_values.append(row['properties'].get('color', 'black'))
            else:
                # Default if properties not available
                color_values.append('black')
        
        # Count occurrences of each color
        color_counts = pd.Series(color_values).value_counts()
        
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
        
        # Get recent colors for trend
        recent_colors = color_values[-20:] if len(color_values) > 20 else color_values
        
        # Convert colors to numeric values for the trend line
        color_to_value = {'red': 1, 'black': 0, 'green': 0.5}
        color_numeric = [color_to_value.get(color, 0) for color in recent_colors]
        
        # Add the trend line
        fig.add_trace(
            go.Scatter(
                x=list(range(len(recent_colors))),
                y=color_numeric,
                mode='lines+markers',
                line=dict(color='gray', width=2),
                marker=dict(
                    size=10,
                    color=recent_colors
                ),
                hovertemplate='Spin #%{x}<br>Color: %{text}<extra></extra>',
                text=recent_colors
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
        
        # Extract dozen from properties
        dozen_values = []
        for _, row in spins_df.iterrows():
            if 'properties' in row and isinstance(row['properties'], dict):
                dozen_values.append(row['properties'].get('dozen', 'zero'))
            else:
                # Default if properties not available
                dozen_values.append('zero')
        
        # Count occurrences of each dozen
        dozens_counts = pd.Series(dozen_values).value_counts()
        
        # Apply readable labels
        dozen_labels = {
            'first': '1-12 (First)',
            'second': '13-24 (Second)',
            'third': '25-36 (Third)',
            'zero': '0/00'
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
        expected_values = []
        for dozen in dozens_counts.index:
            if dozen == 'zero':
                expected_values.append(expected_zero)
            else:
                expected_values.append(expected_dozen)
        
        fig.add_trace(go.Scatter(
            x=[dozen_labels.get(dozen, dozen) for dozen in dozens_counts.index],
            y=expected_values,
            mode='markers',
            marker=dict(size=12, color='blue', symbol='star'),
            name='Expected'
        ))
        
        # Update layout
        fig.update_layout(
            title_text="Dozens Distribution Analysis",
            xaxis_title="Dozen",
            yaxis_title="Count",
            showlegend=True,
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
        
        # Extract column from properties
        column_values = []
        for _, row in spins_df.iterrows():
            if 'properties' in row and isinstance(row['properties'], dict):
                column_values.append(row['properties'].get('column', 'zero'))
            else:
                # Default if properties not available
                column_values.append('zero')
        
        # Count occurrences of each column
        columns_counts = pd.Series(column_values).value_counts()
        
        # Apply readable labels
        column_labels = {
            'first': 'Column 1',
            'second': 'Column 2',
            'third': 'Column 3',
            'zero': '0/00'
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
        expected_values = []
        for col in columns_counts.index:
            if col == 'zero':
                expected_values.append(expected_zero)
            else:
                expected_values.append(expected_column)
        
        fig.add_trace(go.Scatter(
            x=[column_labels.get(col, col) for col in columns_counts.index],
            y=expected_values,
            mode='markers',
            marker=dict(size=12, color='blue', symbol='star'),
            name='Expected'
        ))
        
        # Update layout
        fig.update_layout(
            title_text="Columns Distribution Analysis",
            xaxis_title="Column",
            yaxis_title="Count",
            showlegend=True,
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
        
        # Extract range from properties
        range_values = []
        for _, row in spins_df.iterrows():
            if 'properties' in row and isinstance(row['properties'], dict):
                range_values.append(row['properties'].get('range', 'zero'))
            else:
                # Default if properties not available
                range_values.append('zero')
        
        # Filter out 0 and 00
        filtered_values = [val for val in range_values if val != 'zero']
        
        if not filtered_values:
            # Return empty figure if all spins are 0 or 00
            fig = go.Figure()
            fig.update_layout(
                title="No high/low data available (all spins are 0 or 00)"
            )
            return fig
            
        # Count occurrences of high and low
        high_low_counts = pd.Series(filtered_values).value_counts()
        
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
                marker_colors=['lightblue', 'darkblue'],
                textinfo='label+percent',
                insidetextorientation='radial'
            ),
            row=1, col=1
        )
        
        # Get recent values for trend (excluding zeros)
        recent_filtered = []
        recent_labels = []
        for val in range_values[-20:]:
            if val != 'zero':
                recent_filtered.append(val)
                recent_labels.append(val)
        
        if recent_filtered:  # Only add if we have data
            # Convert high/low to 0/1 for easier plotting
            high_low_numeric = [1 if val == 'high' else 0 for val in recent_filtered]
            
            # Add the trend line
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(recent_filtered))),
                    y=high_low_numeric,
                    mode='lines+markers',
                    line=dict(color='gray', width=2),
                    marker=dict(
                        size=10,
                        color=['darkblue' if val == 1 else 'lightblue' for val in high_low_numeric]
                    ),
                    hovertemplate='Spin #%{x}<br>Result: %{text}<extra></extra>',
                    text=recent_labels
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
    
    def _get_color_for_number(self, number, color_value):
        """
        Get the appropriate color for a number.
        
        Args:
            number (str or int): The roulette number
            color_value (str): The color value from properties
            
        Returns:
            str: CSS color value
        """
        if number == '0' or number == '00' or number == 0:
            return 'green'
        elif color_value == 'red':
            return 'red'
        else:
            return 'black'
            
    def plot_wheel_bias(self, bias_data, roulette_type):
        """
        Create a visual representation of wheel bias analysis.
        
        Args:
            bias_data (dict): Dictionary with bias data
            roulette_type (str): Type of roulette - 'European' or 'American'
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if not bias_data or not bias_data.get('numbers'):
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No bias data available"
            )
            return fig
            
        # Extract data
        numbers = bias_data['numbers']
        z_scores = bias_data['z_scores']
        expected = bias_data['expected']
        observed = bias_data['observed']
        
        # Create a subplot with two charts
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "bar"}, {"type": "scatter"}]],
            subplot_titles=["Frequency Deviation", "Statistical Significance (Z-Score)"]
        )
        
        # Add the frequency deviation chart (observed - expected)
        deviations = [obs - exp for obs, exp in zip(observed, expected)]
        
        # Determine colors based on whether number is above or below expected
        colors = ['green' if dev > 0 else 'red' for dev in deviations]
        
        fig.add_trace(
            go.Bar(
                x=numbers,
                y=deviations,
                marker_color=colors,
                hovertemplate='Number: %{x}<br>Deviation: %{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add the z-score scatter plot
        fig.add_trace(
            go.Scatter(
                x=numbers,
                y=z_scores,
                mode='markers',
                marker=dict(
                    size=12,
                    color=['red' if abs(z) > 1.96 else 'blue' for z in z_scores],
                    symbol=['star' if abs(z) > 1.96 else 'circle' for z in z_scores]
                ),
                hovertemplate='Number: %{x}<br>Z-Score: %{y:.2f}<extra></extra>'
            ),
            row=1, col=2
        )
        
        # Add a horizontal line at z=1.96 (95% confidence level)
        fig.add_shape(
            type="line",
            x0=min(numbers),
            y0=1.96,
            x1=max(numbers),
            y1=1.96,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            row=1, col=2
        )
        
        # Add a horizontal line at z=-1.96 (95% confidence level)
        fig.add_shape(
            type="line",
            x0=min(numbers),
            y0=-1.96,
            x1=max(numbers),
            y1=-1.96,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            row=1, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="Wheel Bias Analysis",
            showlegend=False,
            height=500,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        # Update axes
        fig.update_xaxes(title_text="Number", row=1, col=1)
        fig.update_yaxes(title_text="Deviation from Expected", row=1, col=1)
        
        fig.update_xaxes(title_text="Number", row=1, col=2)
        fig.update_yaxes(title_text="Z-Score (Significance)", row=1, col=2)
        
        return fig
    
    def plot_betting_strategy_heatmap(self, spins_df, roulette_type, bet_recommendations):
        """
        Create a heatmap visualization for betting strategy recommendations.
        
        Args:
            spins_df (pd.DataFrame): DataFrame with spin data
            roulette_type (str): Type of roulette - 'European' or 'American'
            bet_recommendations (dict): Dictionary with bet recommendations
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if spins_df is None or spins_df.empty or not bet_recommendations:
            # Return empty figure
            fig = go.Figure()
            fig.update_layout(
                title="No data available for strategy heatmap"
            )
            return fig
            
        # Extract number recommendations if available
        number_rec = bet_recommendations.get('numbers', [])
        
        # Create data for the heatmap
        all_numbers = [str(i) for i in range(37)]  # 0-36
        if roulette_type == "American":
            all_numbers.append("00")
            
        # Calculate confidence values for each number
        values = []
        for num in all_numbers:
            # Find this number in the recommendations
            found = False
            for rec in number_rec:
                if rec.get('number') == num:
                    values.append(rec.get('confidence', 0))
                    found = True
                    break
            
            if not found:
                values.append(0)
                
        # Create a dataframe for the heatmap
        heat_df = pd.DataFrame({
            'number': all_numbers,
            'confidence': values
        })
        
        # Sort numbers for better visualization
        try:
            heat_df['sort_value'] = heat_df['number'].apply(
                lambda x: -1 if x == '00' else int(x)
            )
            heat_df = heat_df.sort_values(by='sort_value')
        except:
            # Fallback if there's an issue with sorting
            pass
        
        # Get colors for each number for visual consistency
        colors = []
        for num in heat_df['number']:
            if num == '0' or num == '00':
                colors.append('green')
            else:
                int_num = int(num)
                red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
                if int_num in red_numbers:
                    colors.append('red')
                else:
                    colors.append('black')
        
        # Create the heatmap visualization
        fig = go.Figure()
        
        # Add bar chart for number recommendations
        fig.add_trace(go.Bar(
            x=heat_df['number'],
            y=heat_df['confidence'],
            marker_color=[self._get_color_for_confidence(val, col) 
                          for val, col in zip(heat_df['confidence'], colors)],
            hovertemplate='Number: %{x}<br>Confidence: %{y:.2f}<extra></extra>'
        ))
        
        # Add strategy recommendations as annotations
        strategy_rec = bet_recommendations.get('strategies', [])
        
        annotations = []
        for i, rec in enumerate(strategy_rec[:3]):  # Show top 3 strategies
            annotations.append(dict(
                x=len(heat_df) / 2,
                y=1.1 + (i * 0.1),
                xref="x",
                yref="paper",
                text=f"{rec.get('name', 'Strategy')}: {rec.get('confidence', 0):.2f}",
                showarrow=False,
                font=dict(
                    size=14,
                    color="black",
                    family="Arial"
                ),
                bgcolor="white",
                bordercolor="black",
                borderwidth=1,
                borderpad=4
            ))
        
        # Update layout
        fig.update_layout(
            title_text="Betting Strategy Recommendations",
            xaxis_title="Number",
            yaxis_title="Confidence Score",
            showlegend=False,
            margin=dict(t=75, b=50, l=50, r=50),
            annotations=annotations
        )
        
        return fig
    
    def _get_color_for_confidence(self, confidence, base_color):
        """
        Get a color based on confidence level, adjusting the base color.
        
        Args:
            confidence (float): Confidence value (0-1)
            base_color (str): Base color (red, black, green)
            
        Returns:
            str: Color for visualization
        """
        if base_color == 'red':
            # Adjust red intensity based on confidence
            intensity = min(255, 100 + int(155 * confidence))
            return f'rgb({intensity},0,0)'
        elif base_color == 'black':
            # Adjust darkness based on confidence
            intensity = max(0, 100 - int(100 * confidence))
            return f'rgb({intensity},{intensity},{intensity})'
        else:  # green
            # Adjust green intensity based on confidence
            intensity = min(255, 100 + int(155 * confidence))
            return f'rgb(0,{intensity},0)'