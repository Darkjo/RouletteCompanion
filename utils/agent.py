"""
RL Agent for Roulette Strategy Recommendation
Based on the implementation from ProjectR
"""

import random
from collections import defaultdict

class RLAgent:
    """
    Reinforcement Learning Agent for roulette strategy recommendations.
    Tracks performance and provides strategy suggestions based on accuracy and bankroll.
    """
    def __init__(self):
        self.history = []  # Track past spins and context
        self.accuracy = 0.5
        self.alignments = []
        self.performance_log = []  # [(number, strategy, win, payout)]

    def record_alignment(self, success: bool):
        """
        Record if a prediction was successful.
        
        Args:
            success (bool): Whether the prediction was successful
        """
        self.alignments.append(success)
        if len(self.alignments) > 50:
            self.alignments.pop(0)
        self.accuracy = sum(self.alignments) / len(self.alignments) if self.alignments else 0.5

    def record_result(self, number, strategy, win, payout):
        """
        Record the result of a betting round.
        
        Args:
            number (str or int): The number that came up
            strategy (str): The strategy used
            win (bool): Whether the bet won
            payout (float): The payout amount (negative for losses)
        """
        self.performance_log.append({
            'number': number,
            'strategy': strategy,
            'win': win,
            'payout': payout
        })
        if len(self.performance_log) > 100:
            self.performance_log.pop(0)
        self.record_alignment(win)

    def get_accuracy(self) -> float:
        """
        Get the current prediction accuracy.
        
        Returns:
            float: Accuracy as a fraction (0-1)
        """
        return round(self.accuracy, 2)

    def get_recommendation(self, bankroll, confidence=None):
        """
        Suggest strategy based on accuracy, bankroll, and (optionally) prediction confidence.
        
        Args:
            bankroll (float): Current bankroll amount
            confidence (float, optional): Confidence in the current prediction
            
        Returns:
            str: Recommended strategy name
        """
        if confidence is not None:
            if confidence >= 0.7 and bankroll > 150 and self.accuracy > 0.6:
                return "Martingale"
            elif confidence <= 0.4 or bankroll < 50:
                return "Flat"
            elif self.recent_losing_streak() >= 3:
                return "Fibonacci"
            return "Paroli"
        else:
            # fallback if confidence is not provided
            if self.accuracy > 0.65 and bankroll > 150:
                return "Martingale"
            elif self.accuracy < 0.4 or bankroll < 50:
                return "Flat"
            elif self.recent_losing_streak() >= 3:
                return "Fibonacci"
            return "D'Alembert" if bankroll < 100 else "Paroli"

    def get_bet_size_recommendation(self, bankroll):
        """
        Recommend bet size based on bankroll.
        
        Args:
            bankroll (float): Current bankroll amount
            
        Returns:
            float: Recommended bet size
        """
        # Conservative bet sizing - between 1-5% of bankroll
        if bankroll < 50:
            return 1.0  # Minimum bet to protect bankroll
        elif bankroll < 100:
            return round(bankroll * 0.02, 1)  # 2% of bankroll
        elif bankroll < 200:
            return round(bankroll * 0.03, 1)  # 3% of bankroll
        elif bankroll < 500:
            return round(bankroll * 0.04, 1)  # 4% of bankroll
        else:
            return round(bankroll * 0.05, 1)  # 5% of bankroll

    def recent_losing_streak(self):
        """
        Calculate the current consecutive losing streak.
        
        Returns:
            int: Length of the current losing streak
        """
        streak = 0
        for result in reversed(self.alignments):
            if result is False:
                streak += 1
            else:
                break
        return streak

    def reset(self):
        """Reset the agent's state."""
        self.history.clear()
        self.alignments.clear()
        self.performance_log.clear()
        self.accuracy = 0.5

    def get_summary(self):
        """
        Get a summary of the agent's performance.
        
        Returns:
            list: Summary statistics for each strategy
        """
        summary = defaultdict(lambda: {"wins": 0, "losses": 0, "profit": 0})
        for entry in self.performance_log:
            strat = entry['strategy']
            summary[strat]['profit'] += entry['payout']
            if entry['win']:
                summary[strat]['wins'] += 1
            else:
                summary[strat]['losses'] += 1

        summary_list = []
        for strat, data in summary.items():
            total = data['wins'] + data['losses']
            win_rate = round(100 * data['wins'] / total, 2) if total else 0
            summary_list.append({
                'strategy': strat,
                'wins': data['wins'],
                'losses': data['losses'],
                'profit': round(data['profit'], 2),
                'win_rate': win_rate
            })
        return summary_list