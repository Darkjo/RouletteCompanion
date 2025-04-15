"""
Specialized OCR module highly optimized for the specific format of the 
roulette history board with red and white numbers on black background.
This module is much faster than the general-purpose OCR.
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_roulette_board(image, rows=6, cols=8):
    """
    Process a roulette history board with a very specific layout
    of red and white numbers on a black background, arranged in 
    an 8x6 grid (8 columns, 6 rows).
    
    Extremely optimized for speed and accuracy for this exact format.
    
    Args:
        image (PIL.Image): Image of the history board
        rows (int): Number of rows in the grid
        cols (int): Number of columns in the grid
        
    Returns:
        list: Detected numbers as strings
    """
    try:
        # Convert to NumPy array
        np_image = np.array(image)
        
        # Check if image is colored
        if len(np_image.shape) == 3:
            # Extract color information - this is key for this specific board
            hsv = cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)
            
            # Create mask for red numbers (red appears in two HSV ranges)
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 100, 100])
            upper_red2 = np.array([180, 255, 255])
            
            red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            
            # Create mask for white numbers
            lower_white = np.array([0, 0, 150])
            upper_white = np.array([180, 30, 255])
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
            
            # Combine masks to extract all numbers
            combined_mask = cv2.bitwise_or(red_mask, white_mask)
            
            # Apply mask to extract only the number pixels
            numbers_only = cv2.bitwise_and(np_image, np_image, mask=combined_mask)
            
            # Convert to grayscale
            gray = cv2.cvtColor(numbers_only, cv2.COLOR_BGR2GRAY)
        else:
            gray = np_image
            
        # Get image dimensions and calculate cell sizes
        height, width = gray.shape
        cell_height = height // rows
        cell_width = width // cols
        
        # Prepare results list
        results = []
        
        # List of valid roulette numbers for validation
        valid_numbers = [str(i) for i in range(37)] + ["00"]
        
        # Process each cell in the grid
        for row in range(rows):
            for col in range(cols):
                # Calculate cell coordinates
                y1 = row * cell_height
                x1 = col * cell_width
                y2 = y1 + cell_height
                x2 = x1 + cell_width
                
                # Extract cell
                cell = gray[y1:y2, x1:x2]
                
                # Skip cells with low content
                if np.mean(cell) < 5:
                    continue
                
                # Apply threshold to make numbers stand out
                _, thresh = cv2.threshold(cell, 50, 255, cv2.THRESH_BINARY)
                
                # Convert to PIL for OCR
                cell_pil = Image.fromarray(thresh)
                
                # Try just one fast recognition mode
                try:
                    text = pytesseract.image_to_string(
                        cell_pil,
                        config="--oem 1 --psm 10 -c tessedit_char_whitelist=0123456789"
                    ).strip()
                    
                    # If we got text, clean it up
                    if text:
                        # Extract only digits
                        digits = ''.join(filter(str.isdigit, text))
                        
                        # Handle special case for "00"
                        if "00" in text:
                            number = "00"
                        elif digits:
                            number = digits
                            
                            # Validate multi-digit numbers
                            if len(digits) > 2:
                                if digits[:2] in valid_numbers:
                                    number = digits[:2]
                                elif digits[0] in valid_numbers:
                                    number = digits[0]
                            
                            # Validate the number
                            if number in valid_numbers:
                                results.append(number)
                                
                except Exception as e:
                    logger.debug(f"Error processing cell at ({row}, {col}): {e}")
                    continue
                    
        return results
        
    except Exception as e:
        logger.error(f"Error processing roulette board: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def process_image(image_path):
    """
    Process an image file containing a roulette history board.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        list: List of detected numbers
    """
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Try first with the specialized 8x6 grid layout
        numbers = process_roulette_board(image, rows=6, cols=8)
        
        # If that doesn't work well, try with 6x8 (transposed)
        if len(numbers) < 10:
            numbers = process_roulette_board(image, rows=8, cols=6)
            
        return numbers
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return []