"""
Performance Tracker for Roulette Strategy Performance
Based on the implementation from ProjectR
"""

class StrategyPerformanceTracker:
    """
    Tracks and analyzes the performance of different betting strategies.
    """
    def __init__(self):
        self.stats = {}  # Strategy statistics
        self.session_history = []  # Track all betting sessions

    def update(self, strategy, win, profit, bet_amount=None):
        """
        Update statistics for a strategy after a bet.
        
        Args:
            strategy (str): The strategy name
            win (bool): Whether the bet won
            profit (float): The profit/loss from this bet
            bet_amount (float, optional): The amount that was bet
        """
        if strategy not in self.stats:
            self.stats[strategy] = {
                "wins": 0, 
                "losses": 0, 
                "profit": 0.0,
                "total_bets": 0,
                "max_win": 0,
                "max_loss": 0,
                "total_bet_amount": 0
            }
        
        self.stats[strategy]["total_bets"] += 1
        
        if win:
            self.stats[strategy]["wins"] += 1
            self.stats[strategy]["max_win"] = max(profit, self.stats[strategy]["max_win"])
        else:
            self.stats[strategy]["losses"] += 1
            self.stats[strategy]["max_loss"] = min(profit, self.stats[strategy]["max_loss"])
        
        self.stats[strategy]["profit"] += profit
        
        if bet_amount is not None:
            self.stats[strategy]["total_bet_amount"] += bet_amount
        
        # Record session history
        self.session_history.append({
            "strategy": strategy,
            "win": win,
            "profit": profit,
            "bet_amount": bet_amount
        })

    def get_summary(self):
        """
        Get a summary of performance for all strategies.
        
        Returns:
            list: List of dictionaries with strategy performance stats
        """
        summary = []
        for strategy, data in self.stats.items():
            total = data["wins"] + data["losses"]
            win_rate = (data["wins"] / total * 100) if total > 0 else 0
            roi = (data["profit"] / data["total_bet_amount"] * 100) if data["total_bet_amount"] > 0 else 0
            
            summary.append({
                "strategy": strategy,
                "wins": data["wins"],
                "losses": data["losses"],
                "total_bets": data["total_bets"],
                "profit": round(data["profit"], 2),
                "win_rate": round(win_rate, 2),
                "max_win": round(data["max_win"], 2),
                "max_loss": round(data["max_loss"], 2),
                "roi": round(roi, 2)
            })
        return summary

    def get_strategy_performance(self, strategy):
        """
        Get detailed performance data for a specific strategy.
        
        Args:
            strategy (str): The strategy name
            
        Returns:
            dict: Performance metrics for the strategy
        """
        if strategy not in self.stats:
            return None
        
        data = self.stats[strategy]
        total = data["wins"] + data["losses"]
        
        return {
            "strategy": strategy,
            "wins": data["wins"],
            "losses": data["losses"],
            "total_bets": data["total_bets"],
            "profit": round(data["profit"], 2),
            "win_rate": round((data["wins"] / total * 100) if total > 0 else 0, 2),
            "max_win": round(data["max_win"], 2),
            "max_loss": round(data["max_loss"], 2),
            "average_profit_per_bet": round(data["profit"] / total if total > 0 else 0, 2)
        }

    def get_session_history(self, limit=None):
        """
        Get the session betting history.
        
        Args:
            limit (int, optional): Number of recent sessions to return
            
        Returns:
            list: List of session entries
        """
        if limit is None:
            return self.session_history
        return self.session_history[-limit:]

    def reset(self):
        """Reset all tracking data."""
        self.stats.clear()
        self.session_history.clear()