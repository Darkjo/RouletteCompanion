class RouletteGame:
    """
    Handles the logic and rules for roulette games.
    Supports both European and American roulette types.
    """
    
    def __init__(self, roulette_type="European"):
        """
        Initialize a roulette game with the specified type.
        
        Args:
            roulette_type (str): The type of roulette game ("European" or "American")
        """
        self.roulette_type = roulette_type
        
        # Define the numbers and their properties
        self.red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        self.black_numbers = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
        
        # Maximum number based on roulette type
        self.max_number = 36 if roulette_type == "European" else 37  # 37 represents 00 in American roulette
        
    def get_color(self, number):
        """
        Get the color of a roulette number.
        
        Args:
            number (int): The roulette number
            
        Returns:
            str: "red", "black", or "green" (for 0 and 00)
        """
        if number == 0 or number == 37:  # 0 or 00
            return "green"
        elif number in self.red_numbers:
            return "red"
        elif number in self.black_numbers:
            return "black"
        else:
            return "invalid"
    
    def is_even(self, number):
        """
        Check if a number is even.
        
        Args:
            number (int): The roulette number
            
        Returns:
            bool: True if even, False if odd or 0/00
        """
        if number == 0 or number == 37:  # 0 or 00
            return False
        return number % 2 == 0
    
    def get_dozen(self, number):
        """
        Get the dozen for a roulette number.
        
        Args:
            number (int): The roulette number
            
        Returns:
            int: 1, 2, 3 for the respective dozen, 0 for 0/00
        """
        if number == 0 or number == 37:  # 0 or 00
            return 0
        elif 1 <= number <= 12:
            return 1
        elif 13 <= number <= 24:
            return 2
        elif 25 <= number <= 36:
            return 3
        else:
            return 0
    
    def get_column(self, number):
        """
        Get the column for a roulette number.
        
        Args:
            number (int): The roulette number
            
        Returns:
            int: 1, 2, 3 for the respective column, 0 for 0/00
        """
        if number == 0 or number == 37:  # 0 or 00
            return 0
        
        # Column is determined by number % 3
        remainder = number % 3
        if remainder == 1:
            return 1
        elif remainder == 2:
            return 2
        else:  # remainder == 0
            return 3
    
    def get_half(self, number):
        """
        Get the half for a roulette number.
        
        Args:
            number (int): The roulette number
            
        Returns:
            int: 1 for 1-18, 2 for 19-36, 0 for 0/00
        """
        if number == 0 or number == 37:  # 0 or 00
            return 0
        elif 1 <= number <= 18:
            return 1
        elif 19 <= number <= 36:
            return 2
        else:
            return 0
    
    def get_all_numbers(self):
        """
        Get all possible numbers on the wheel.
        
        Returns:
            list: All the numbers on the wheel, including 0 and possibly 00
        """
        if self.roulette_type == "European":
            return list(range(37))  # 0-36
        else:  # American
            return list(range(37)) + [37]  # 0-36 plus 37 (which represents 00)
    
    def get_straight_up_payout(self):
        """
        Get the payout multiplier for a straight up bet (single number).
        
        Returns:
            int: The payout multiplier
        """
        return 35
    
    def get_split_payout(self):
        """
        Get the payout multiplier for a split bet (two adjacent numbers).
        
        Returns:
            int: The payout multiplier
        """
        return 17
    
    def get_street_payout(self):
        """
        Get the payout multiplier for a street bet (three numbers in a row).
        
        Returns:
            int: The payout multiplier
        """
        return 11
    
    def get_corner_payout(self):
        """
        Get the payout multiplier for a corner bet (four numbers in a square).
        
        Returns:
            int: The payout multiplier
        """
        return 8
    
    def get_line_payout(self):
        """
        Get the payout multiplier for a line bet (six numbers, two rows).
        
        Returns:
            int: The payout multiplier
        """
        return 5
    
    def get_dozen_payout(self):
        """
        Get the payout multiplier for a dozen bet.
        
        Returns:
            int: The payout multiplier
        """
        return 2
    
    def get_column_payout(self):
        """
        Get the payout multiplier for a column bet.
        
        Returns:
            int: The payout multiplier
        """
        return 2
    
    def get_even_money_payout(self):
        """
        Get the payout multiplier for even money bets (red/black, even/odd, 1-18/19-36).
        
        Returns:
            int: The payout multiplier
        """
        return 1
    
    def get_house_edge(self):
        """
        Calculate the house edge for this roulette type.
        
        Returns:
            float: The house edge as a percentage
        """
        if self.roulette_type == "European":
            return 100 * (1 / 37)  # About 2.7%
        else:  # American
            return 100 * (2 / 38)  # About 5.26%
    
    def format_number_display(self, number):
        """
        Format a number for display.
        
        Args:
            number (int): The roulette number
            
        Returns:
            str: Formatted number
        """
        if number == 37:
            return "00"
        return str(number)
