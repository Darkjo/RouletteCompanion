"""
Betting Strategies for Roulette
Based on the implementation from ProjectR
"""

class BaseStrategy:
    """Base class for all betting strategies."""
    def __init__(self, base_bet=1.0):
        self.base_bet = base_bet
        self.current_bet = self.base_bet

    def next_bet(self, win: bool) -> float:
        """
        Calculate the next bet amount based on the result of the current bet.
        
        Args:
            win (bool): Whether the current bet won
            
        Returns:
            float: The amount to bet next
        """
        raise NotImplementedError("Must be implemented in subclass")

    def reset(self):
        """Reset the strategy to its initial state."""
        self.current_bet = self.base_bet


class FlatStrategy(BaseStrategy):
    """
    Flat betting - always bet the same amount.
    Low risk, low reward. Good for preserving bankroll.
    """
    def next_bet(self, win: bool) -> float:
        return self.base_bet


class MartingaleStrategy(BaseStrategy):
    """
    Double the bet after each loss, return to base bet after a win.
    High risk, medium reward. Can lead to rapid bankruptcy with losing streaks.
    """
    def next_bet(self, win: bool) -> float:
        if win:
            self.current_bet = self.base_bet
        else:
            self.current_bet *= 2
        return self.current_bet


class ParoliStrategy(BaseStrategy):
    """
    Double the bet after each win, up to 3 wins in a row.
    Medium risk, high reward. Capitalizes on winning streaks.
    """
    def __init__(self, base_bet=1.0):
        super().__init__(base_bet)
        self.wins = 0

    def next_bet(self, win: bool) -> float:
        if win:
            self.wins += 1
            if self.wins >= 3:
                self.current_bet = self.base_bet
                self.wins = 0
            else:
                self.current_bet *= 2
        else:
            self.current_bet = self.base_bet
            self.wins = 0
        return self.current_bet


class FibonacciStrategy(BaseStrategy):
    """
    Increase bet based on Fibonacci sequence after losses.
    Medium risk, medium reward. More gradual progression than Martingale.
    """
    def __init__(self, base_bet=1.0):
        super().__init__(base_bet)
        self.sequence = [1, 1]
        self.index = 0

    def next_bet(self, win: bool) -> float:
        if win:
            self.index = max(0, self.index - 2)
        else:
            if self.index >= len(self.sequence) - 1:
                self.sequence.append(self.sequence[-1] + self.sequence[-2])
            self.index += 1
        self.current_bet = self.base_bet * self.sequence[self.index]
        return self.current_bet

    def reset(self):
        super().reset()
        self.sequence = [1, 1]
        self.index = 0


class DAlembertStrategy(BaseStrategy):
    """
    Add one unit after a loss, subtract one unit after a win.
    Medium-low risk, medium-low reward. More conservative than Martingale.
    """
    def next_bet(self, win: bool) -> float:
        if win:
            self.current_bet = max(self.base_bet, self.current_bet - self.base_bet)
        else:
            self.current_bet += self.base_bet
        return self.current_bet


class LabouchereStrategy(BaseStrategy):
    """
    Bet the sum of first and last numbers in a sequence, cross them off after a win,
    add the sum to the end after a loss.
    High risk, high reward. Complex but can yield good results with the right sequence.
    """
    def __init__(self, base_bet=1.0):
        super().__init__(base_bet)
        self.sequence = [1, 2, 3, 4]

    def next_bet(self, win: bool) -> float:
        if len(self.sequence) == 0:
            self.sequence = [1, 2, 3, 4]  # Reset if sequence is exhausted
            
        if win:
            if len(self.sequence) > 1:
                self.sequence = self.sequence[1:-1]  # Remove first and last
            else:
                self.sequence = []  # Clear sequence if only one number left
        else:
            # Add the sum of first and last to the end
            if len(self.sequence) >= 1:
                self.sequence.append(self.sequence[0] + (self.sequence[-1] if len(self.sequence) > 1 else 0))
        
        if len(self.sequence) >= 2:
            self.current_bet = self.base_bet * (self.sequence[0] + self.sequence[-1])
        elif len(self.sequence) == 1:
            self.current_bet = self.base_bet * self.sequence[0]
        else:
            self.current_bet = self.base_bet  # Default to base bet if sequence is empty
            
        return self.current_bet

    def reset(self):
        super().reset()
        self.sequence = [1, 2, 3, 4]


class StrategyEngine:
    """
    Engine to manage and apply different betting strategies.
    """
    def __init__(self):
        self.strategies = {
            "Flat": FlatStrategy(),
            "Martingale": MartingaleStrategy(),
            "Paroli": ParoliStrategy(),
            "Fibonacci": FibonacciStrategy(),
            "D'Alembert": DAlembertStrategy(),
            "Labouchere": LabouchereStrategy(),
        }

    def evaluate_bet(self, bet_type, bet_value, result_number):
        """
        Evaluate whether a bet won based on the roulette result.
        
        Args:
            bet_type (str): Type of bet (e.g., 'number', 'red', 'even')
            bet_value: The specific value bet on
            result_number (int or str): The number that came up
            
        Returns:
            tuple: (bool indicating win/loss, payout multiplier)
        """
        # Convert result to int for numerical comparisons if it's not "00"
        result = result_number
        if result != "00" and isinstance(result, str):
            result = int(result)
            
        # Define roulette number properties
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        
        # Handle different bet types
        if bet_type == "number":
            if str(bet_value) == str(result_number):
                return True, 35  # 35:1 payout for single number
            return False, 0
            
        elif bet_type == "red":
            if isinstance(result, int) and result in red_numbers:
                return True, 1  # 1:1 payout
            return False, 0
            
        elif bet_type == "black":
            if isinstance(result, int) and result in black_numbers:
                return True, 1  # 1:1 payout
            return False, 0
            
        elif bet_type == "even":
            if isinstance(result, int) and result % 2 == 0 and result != 0:
                return True, 1  # 1:1 payout
            return False, 0
            
        elif bet_type == "odd":
            if isinstance(result, int) and result % 2 == 1:
                return True, 1  # 1:1 payout
            return False, 0
            
        elif bet_type == "low":
            if isinstance(result, int) and 1 <= result <= 18:
                return True, 1  # 1:1 payout
            return False, 0
            
        elif bet_type == "high":
            if isinstance(result, int) and 19 <= result <= 36:
                return True, 1  # 1:1 payout
            return False, 0
            
        elif bet_type == "dozen":
            if not isinstance(result, int) or result == 0:
                return False, 0
                
            if bet_value == "first" and 1 <= result <= 12:
                return True, 2  # 2:1 payout
            elif bet_value == "second" and 13 <= result <= 24:
                return True, 2  # 2:1 payout
            elif bet_value == "third" and 25 <= result <= 36:
                return True, 2  # 2:1 payout
            return False, 0
            
        elif bet_type == "column":
            if not isinstance(result, int) or result == 0:
                return False, 0
                
            if bet_value == "first" and result % 3 == 1:
                return True, 2  # 2:1 payout
            elif bet_value == "second" and result % 3 == 2:
                return True, 2  # 2:1 payout
            elif bet_value == "third" and result % 3 == 0:
                return True, 2  # 2:1 payout
            return False, 0
            
        # Handle unknown bet types
        return False, 0

    def get_bet_amount(self, strategy_name: str, win: bool) -> float:
        """
        Get the next bet amount for a strategy.
        
        Args:
            strategy_name (str): Name of the strategy
            win (bool): Whether the last bet won
            
        Returns:
            float: The next bet amount
        """
        if strategy_name in self.strategies:
            return self.strategies[strategy_name].next_bet(win)
        return 1.0  # Default to 1.0 for unknown strategies

    def set_base_bet(self, strategy_name: str, base_bet: float):
        """
        Set the base bet amount for a strategy.
        
        Args:
            strategy_name (str): Name of the strategy
            base_bet (float): The base bet amount
        """
        if strategy_name in self.strategies:
            self.strategies[strategy_name].base_bet = base_bet
            self.strategies[strategy_name].reset()

    def reset_strategy(self, strategy_name: str):
        """
        Reset a strategy to its initial state.
        
        Args:
            strategy_name (str): Name of the strategy
        """
        if strategy_name in self.strategies:
            self.strategies[strategy_name].reset()

    def get_strategy_names(self):
        """
        Get a list of all available strategy names.
        
        Returns:
            list: List of strategy names
        """
        return list(self.strategies.keys())