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
        # Initialize figure
        fig = go.Figure()
        
        if spins_df is None or spins_df.empty:
            # Return empty figure
            fig.update_layout(
                title="No spin data available"
            )
            return fig
        
        try:
            # Filter out 0 and 00
            filtered_df = spins_df[~spins_df['number'].isin(['0', '00'])]
            
            if filtered_df.empty:
                fig.add_trace(go.Pie(
                    labels=['No valid data'],
                    values=[1],
                    marker_colors=['lightgray']
                ))
                fig.update_layout(
                    title="No even/odd data available (only zeros)"
                )
                return fig
            
            # Calculate even/odd counts
            even_count = sum(1 for num in filtered_df['number'] if num.isdigit() and int(num) % 2 == 0)
            odd_count = sum(1 for num in filtered_df['number'] if num.isdigit() and int(num) % 2 == 1)
            
            # Calculate percentages
            total = even_count + odd_count
            even_pct = even_count / total * 100 if total > 0 else 0
            odd_pct = odd_count / total * 100 if total > 0 else 0
            
            # Create labels with percentages
            labels = [f'Even: {even_count} ({even_pct:.1f}%)', f'Odd: {odd_count} ({odd_pct:.1f}%)']
            
            # Create the pie chart
            fig.add_trace(go.Pie(
                labels=labels,
                values=[even_count, odd_count],
                marker_colors=['#3498db', '#e74c3c'],
                textinfo='label',
                hole=0.3
            ))
            
            # Update layout
            fig.update_layout(
                title="Even vs Odd Distribution",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
        except Exception as e:
            # Handle any errors gracefully
            fig.add_trace(go.Pie(
                labels=['Error'],
                values=[1],
                marker_colors=['lightgray']
            ))
            fig.update_layout(
                title=f"Error: {str(e)}"
            )
            
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
        # Initialize figure
        fig = go.Figure()
        
        if spins_df is None or spins_df.empty:
            # Return empty figure
            fig.update_layout(
                title="No spin data available"
            )
            return fig
        
        try:
            # Filter out green numbers (0 and 00)
            filtered_df = spins_df[~spins_df['number'].isin(['0', '00'])]
            
            if filtered_df.empty:
                fig.add_trace(go.Pie(
                    labels=['No valid data'],
                    values=[1],
                    marker_colors=['lightgray']
                ))
                fig.update_layout(
                    title="No red/black data available (only zeros)"
                )
                return fig
            
            # Define red numbers
            red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
            
            # Calculate red/black counts
            red_count = sum(1 for num in filtered_df['number'] 
                           if num.isdigit() and int(num) in red_numbers)
            black_count = len(filtered_df) - red_count
            
            # Calculate percentages
            total = red_count + black_count
            red_pct = red_count / total * 100 if total > 0 else 0
            black_pct = black_count / total * 100 if total > 0 else 0
            
            # Create labels with percentages
            labels = [f'Red: {red_count} ({red_pct:.1f}%)', f'Black: {black_count} ({black_pct:.1f}%)']
            
            # Create the pie chart
            fig.add_trace(go.Pie(
                labels=labels,
                values=[red_count, black_count],
                marker_colors=['#e74c3c', '#34495e'],
                textinfo='label',
                hole=0.3
            ))
            
            # Update layout
            fig.update_layout(
                title="Red vs Black Distribution",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
        except Exception as e:
            # Handle any errors gracefully
            fig.add_trace(go.Pie(
                labels=['Error'],
                values=[1],
                marker_colors=['lightgray']
            ))
            fig.update_layout(
                title=f"Error: {str(e)}"
            )
            
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
        # Initialize figure
        fig = go.Figure()
        
        if spins_df is None or spins_df.empty or not bet_recommendations:
            # Return empty figure
            fig.update_layout(
                title="No strategy data available",
                height=400,
                width=600
            )
            return fig
        
        # Extract key recommendation data for visualization
        strategies = []
        confidence_scores = []
        
        # Add single numbers with their confidence scores
        for num_rec in bet_recommendations.get('single_numbers', []):
            if 'number' in num_rec and 'confidence' in num_rec:
                strategies.append(f"Single: {num_rec['number']}")
                confidence_scores.append(num_rec['confidence'])
        
        # Add other bet types
        for bet_type in ['columns', 'dozens', 'red_black', 'even_odd', 'high_low']:
            if bet_type in bet_recommendations and bet_recommendations[bet_type].get('recommendation'):
                rec = bet_recommendations[bet_type]
                strategies.append(f"{bet_type.replace('_', ' ').title()}: {rec['recommendation']}")
                confidence_scores.append(rec['confidence'])
        
        # Create data for heatmap
        if strategies and confidence_scores:
            # Sort by confidence for better visualization
            sorted_indices = sorted(range(len(confidence_scores)), 
                                   key=lambda i: confidence_scores[i], 
                                   reverse=True)
            
            sorted_strategies = [strategies[i] for i in sorted_indices]
            sorted_scores = [confidence_scores[i] for i in sorted_indices]
            
            # Create a colorful heatmap
            fig.add_trace(go.Heatmap(
                z=[sorted_scores],
                y=['Confidence'],
                x=sorted_strategies,
                colorscale='Viridis',
                showscale=True,
                text=[[f"{score:.2f}" for score in sorted_scores]],
                texttemplate="%{text}",
                textfont={"size":12}
            ))
            
            # Update layout for better readability
            fig.update_layout(
                title="Betting Strategy Confidence Heatmap",
                xaxis_title="Strategy",
                yaxis_title="",
                height=300,
                margin=dict(l=60, r=30, t=50, b=80),
                xaxis=dict(tickangle=-45)
            )
        else:
            # No valid strategies to display
            fig.add_trace(go.Bar(
                x=["No strategies with confidence data"],
                y=[0],
                marker_color="lightgray"
            ))
            fig.update_layout(
                title="No strategy confidence data available",
                height=300
            )
        
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
        # Initialize figure
        fig = go.Figure()
        
        if actual_vs_expected_df is None or actual_vs_expected_df.empty:
            # Return empty figure
            fig.update_layout(
                title="No comparison data available"
            )
            return fig
        
        # Create a simple bar chart for actual vs expected comparison
        try:
            # If the dataframe has the right columns, create a proper comparison chart
            if 'number' in actual_vs_expected_df.columns and 'actual' in actual_vs_expected_df.columns and 'expected' in actual_vs_expected_df.columns:
                # Sort by number for better display
                df_sorted = actual_vs_expected_df.sort_values(by='number')
                
                # Add actual frequencies
                fig.add_trace(go.Bar(
                    x=df_sorted['number'],
                    y=df_sorted['actual'],
                    name='Actual',
                    marker_color='blue'
                ))
                
                # Add expected frequencies
                fig.add_trace(go.Bar(
                    x=df_sorted['number'],
                    y=df_sorted['expected'],
                    name='Expected',
                    marker_color='red'
                ))
                
                # Update layout
                fig.update_layout(
                    title='Actual vs Expected Frequencies',
                    xaxis_title='Number',
                    yaxis_title='Frequency',
                    barmode='group',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
            else:
                # If dataframe doesn't have expected columns, show a placeholder
                fig.add_trace(go.Bar(
                    x=["Data format not supported"],
                    y=[0],
                    marker_color="lightgray"
                ))
                fig.update_layout(
                    title="Could not create comparison - data format not supported"
                )
        except Exception as e:
            # Handle any errors gracefully
            fig.add_trace(go.Bar(
                x=["Error creating visualization"],
                y=[0],
                marker_color="lightgray"
            ))
            fig.update_layout(
                title=f"Error: {str(e)}"
            )
            
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
        # Initialize figure
        fig = go.Figure()
        
        if deviations_df is None or deviations_df.empty:
            # Return empty figure
            fig.update_layout(
                title="No deviation data available"
            )
            return fig
        
        # Create a visualization of deviations
        try:
            # If we have the expected columns, create a proper deviation chart
            if 'number' in deviations_df.columns and 'deviation' in deviations_df.columns:
                # Sort by number for better display
                df_sorted = deviations_df.sort_values(by='number')
                
                # Add deviation bars
                colors = ['red' if d > 0 else 'blue' for d in df_sorted['deviation']]
                
                fig.add_trace(go.Bar(
                    x=df_sorted['number'],
                    y=df_sorted['deviation'],
                    marker_color=colors,
                    hovertemplate='Number: %{x}<br>Deviation: %{y:.2f}<extra></extra>'
                ))
                
                # Add a reference line at y=0
                fig.add_shape(
                    type="line",
                    x0=0,
                    y0=0,
                    x1=1,
                    y1=0,
                    line=dict(
                        color="black",
                        width=2,
                        dash="dash",
                    ),
                    xref="paper",
                    yref="y"
                )
                
                # Update layout
                fig.update_layout(
                    title='Deviations from Expected Frequencies',
                    xaxis_title='Number',
                    yaxis_title='Deviation',
                    showlegend=False
                )
            else:
                # If the dataframe doesn't have the expected columns, show a placeholder
                fig.add_trace(go.Bar(
                    x=["Data format not supported"],
                    y=[0],
                    marker_color="lightgray"
                ))
                fig.update_layout(
                    title="Could not create deviation chart - data format not supported"
                )
        except Exception as e:
            # Handle any errors gracefully
            fig.add_trace(go.Bar(
                x=["Error creating visualization"],
                y=[0],
                marker_color="lightgray"
            ))
            fig.update_layout(
                title=f"Error: {str(e)}"
            )
            
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
        # Initialize figure
        fig = go.Figure()
        
        if not simulation_results or 'bankroll_history' not in simulation_results:
            # Return empty figure
            fig.update_layout(
                title="No simulation data available"
            )
            return fig
        
        try:
            # Extract bankroll history
            bankroll_history = simulation_results['bankroll_history']
            
            # Create x-axis values (spin numbers)
            spins = list(range(1, len(bankroll_history) + 1))
            
            # Create the line chart
            fig.add_trace(go.Scatter(
                x=spins,
                y=bankroll_history,
                mode='lines+markers',
                name='Bankroll',
                line=dict(color='green', width=2),
                marker=dict(size=6)
            ))
            
            # Add starting bankroll line
            if 'initial_bankroll' in simulation_results:
                initial_bankroll = simulation_results['initial_bankroll']
                fig.add_shape(
                    type="line",
                    x0=0,
                    y0=initial_bankroll,
                    x1=len(bankroll_history),
                    y1=initial_bankroll,
                    line=dict(
                        color="red",
                        width=1,
                        dash="dash",
                    ),
                )
                fig.add_annotation(
                    x=0,
                    y=initial_bankroll,
                    text="Initial Bankroll",
                    showarrow=False,
                    yshift=10,
                )
            
            # Update layout
            final_bankroll = bankroll_history[-1] if bankroll_history else 0
            initial = simulation_results.get('initial_bankroll', 0)
            profit_loss = final_bankroll - initial
            profit_loss_str = f"+{profit_loss:.2f}" if profit_loss >= 0 else f"{profit_loss:.2f}"
            
            fig.update_layout(
                title=f"Bankroll Progression: {profit_loss_str} ({len(bankroll_history)} spins)",
                xaxis_title="Spin Number",
                yaxis_title="Bankroll",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode="x unified"
            )
            
            # Add hoverable points
            fig.update_traces(
                hovertemplate='Spin: %{x}<br>Bankroll: %{y:.2f}<extra></extra>'
            )
            
        except Exception as e:
            # Handle any errors gracefully
            fig.add_trace(go.Scatter(
                x=[0, 1],
                y=[0, 0],
                mode='lines',
                line=dict(color='lightgray')
            ))
            fig.update_layout(
                title=f"Error plotting bankroll progression: {str(e)}"
            )
        
        return fig