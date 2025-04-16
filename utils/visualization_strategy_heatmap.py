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
    import plotly.graph_objects as go
    import pandas as pd
    
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
        marker_color=[_get_color_for_confidence(val, col) 
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

def _get_color_for_confidence(confidence, base_color):
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