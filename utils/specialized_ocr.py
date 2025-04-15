"""
Ultra-optimized OCR module for the specific format of roulette history boards
with red and white numbers on black background. This version uses minimal
processing for maximum speed.
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cache of valid roulette numbers for faster validation
VALID_NUMBERS = set([str(i) for i in range(37)] + ["00"])

# Tesseract configuration - using the fastest engine and mode
TESSERACT_CONFIG = "--oem 1 --psm 10 -c tessedit_char_whitelist=0123456789"

def process_roulette_board(image, rows=6, cols=8):
    """
    Process a roulette history board with a very specific layout
    of red and white numbers on a black background.
    
    Ultra-optimized for speed.
    
    Args:
        image (PIL.Image): Image of the history board
        rows (int): Number of rows in the grid
        cols (int): Number of columns in the grid
        
    Returns:
        list: Detected numbers as strings
    """
    try:
        # Convert to NumPy array once
        np_image = np.array(image)
        
        # Check if image is colored - use optimized path for each
        if len(np_image.shape) == 3:
            # Fast color-based preprocessing
            hsv = cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)
            
            # Single-pass mask creation for both red and white numbers
            # Expanded ranges to ensure we catch all numbers
            mask = cv2.inRange(hsv, np.array([0, 0, 150]), np.array([180, 255, 255]))
            
            # Apply threshold directly to mask instead of doing bitwise operations
            gray = mask
        else:
            # For grayscale images, just use directly
            gray = np_image
            
        # Calculate grid dimensions once
        height, width = gray.shape
        cell_height = height // rows
        cell_width = width // cols
        
        # Preallocate results list for slight performance gain
        results = []
        
        # Process grid in one pass
        for row in range(rows):
            for col in range(cols):
                # Extract cell with minimal operations
                y1 = row * cell_height
                y2 = y1 + cell_height
                x1 = col * cell_width
                x2 = x1 + cell_width
                
                cell = gray[y1:y2, x1:x2]
                
                # Skip empty cells quickly
                if np.mean(cell) < 5:
                    continue
                
                # Apply binary threshold - simple and fast
                _, cell = cv2.threshold(cell, 45, 255, cv2.THRESH_BINARY)
                
                # Directly use pytesseract without converting to PIL
                # This was a slowdown in testing
                text = pytesseract.image_to_string(
                    cell,
                    config=TESSERACT_CONFIG
                ).strip()
                
                # Fast text processing
                if text:
                    # Handle common cases quickly
                    if text == "00":
                        results.append("00")
                        continue
                        
                    # Filter to just digits
                    digits = ''.join(c for c in text if c.isdigit())
                    
                    if not digits:
                        continue
                        
                    # Fast number validation
                    if digits in VALID_NUMBERS:
                        results.append(digits)
                    elif len(digits) > 1:
                        # Handle common misreads
                        if digits[:2] in VALID_NUMBERS:
                            results.append(digits[:2])
                        elif digits[0] in VALID_NUMBERS:
                            results.append(digits[0])
                    
        return results
        
    except Exception as e:
        logger.error(f"Error processing roulette board: {e}")
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