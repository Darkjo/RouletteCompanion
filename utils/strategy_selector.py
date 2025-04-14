"""
Strategy Selector for Roulette Betting
Based on the implementation from ProjectR
"""

def choose_strategy(bankroll, history, accuracy=None):
    """
    Choose a betting strategy based on current bankroll, spin history, and agent accuracy.
    
    Args:
        bankroll (float): Current bankroll amount
        history (list): List of recent spin results
        accuracy (float, optional): Agent prediction accuracy
        
    Returns:
        str: Recommended strategy name
    """
    if accuracy is not None:
        if accuracy > 0.65 and bankroll > 150:
            return "Paroli"
        elif bankroll < 50:
            return "Flat"
        elif len(history) >= 5 and accuracy < 0.5:
            return "D'Alembert"
        else:
            return "Fibonacci"
    else:
        # Decision without accuracy information
        if bankroll < 30:
            return "Flat"  # Protect small bankrolls
        elif bankroll > 200:
            return "Martingale"  # Higher risk with larger bankroll
        elif _detect_alternating_pattern(history):
            return "Paroli"  # Capitalize on potential winning streaks
        else:
            return "D'Alembert"  # Safe middle-ground choice

def get_bet_size_recommendation(bankroll, risk_level="medium"):
    """
    Recommend an appropriate bet size based on bankroll and risk tolerance.
    
    Args:
        bankroll (float): Current bankroll amount
        risk_level (str): Risk tolerance level - "low", "medium", or "high"
        
    Returns:
        float: Recommended bet size
    """
    # Base percentages for different risk levels
    risk_percentages = {
        "low": 0.01,      # 1% of bankroll
        "medium": 0.025,  # 2.5% of bankroll
        "high": 0.05      # 5% of bankroll
    }
    
    # Get percentage based on risk level, default to medium
    percentage = risk_percentages.get(risk_level.lower(), 0.025)
    
    # Calculate recommended bet size with minimum and maximum constraints
    bet_size = bankroll * percentage
    
    # Enforce minimum and maximum bet sizes
    bet_size = max(1.0, bet_size)  # Minimum bet is 1.0
    bet_size = min(bet_size, bankroll * 0.1)  # Maximum is 10% of bankroll
    
    # Round to nearest 0.5 unit for convenience
    bet_size = round(bet_size * 2) / 2
    
    return bet_size

def _detect_alternating_pattern(history, min_length=4):
    """
    Detect if there's an alternating win/loss pattern in the history.
    
    Args:
        history (list): List of recent results
        min_length (int): Minimum sequence length to consider
        
    Returns:
        bool: True if an alternating pattern is detected
    """
    if not history or len(history) < min_length:
        return False
        
    # Check for alternating pattern
    alternating = True
    for i in range(len(history) - 1):
        if history[i] == history[i + 1]:
            alternating = False
            break
            
    return alternating

def get_strategy_description(strategy_name):
    """
    Get a description of a betting strategy.
    
    Args:
        strategy_name (str): Name of the strategy
        
    Returns:
        dict: Strategy description details
    """
    descriptions = {
        "Flat": {
            "description": "Always bet the same amount regardless of wins or losses.",
            "risk_level": "Low",
            "complexity": "Simple",
            "bankroll_impact": "Very safe, preserves bankroll",
            "best_for": "Beginners, small bankrolls, or conservative play",
            "worst_for": "Recovering from losses or capitalizing on winning streaks"
        },
        "Martingale": {
            "description": "Double your bet after each loss, return to base bet after a win.",
            "risk_level": "Very High",
            "complexity": "Simple",
            "bankroll_impact": "Can deplete bankroll quickly during losing streaks",
            "best_for": "Even-money bets with a large bankroll",
            "worst_for": "Limited bankrolls or tables with betting limits"
        },
        "Paroli": {
            "description": "Double your bet after each win (up to three consecutive wins), return to base bet after a loss.",
            "risk_level": "Medium",
            "complexity": "Simple",
            "bankroll_impact": "Can increase winnings during hot streaks",
            "best_for": "Capitalizing on winning streaks",
            "worst_for": "Long losing streaks or choppy results"
        },
        "Fibonacci": {
            "description": "Progress through the Fibonacci sequence after losses, move back two steps after a win.",
            "risk_level": "Medium",
            "complexity": "Medium",
            "bankroll_impact": "More moderate progression than Martingale",
            "best_for": "Players who want a systematic approach with less risk than Martingale",
            "worst_for": "Very long losing streaks"
        },
        "D'Alembert": {
            "description": "Increase bet by one unit after a loss, decrease by one unit after a win.",
            "risk_level": "Medium-Low",
            "complexity": "Simple",
            "bankroll_impact": "Slower increases than Martingale, more sustainable",
            "best_for": "Cautious players who still want a progressive system",
            "worst_for": "Recovering quickly from deep losses"
        },
        "Labouchere": {
            "description": "Use a sequence of numbers where you bet the sum of the first and last, adding to the sequence after losses and removing after wins.",
            "risk_level": "High",
            "complexity": "Complex",
            "bankroll_impact": "Variable based on the sequence used",
            "best_for": "Experienced players who enjoy complex systems",
            "worst_for": "Beginners or those looking for simplicity"
        }
    }
    
    return descriptions.get(strategy_name, {
        "description": "Strategy details not available",
        "risk_level": "Unknown",
        "complexity": "Unknown",
        "bankroll_impact": "Unknown",
        "best_for": "Unknown",
        "worst_for": "Unknown"
    })