"""
Ultra-optimized OCR module for processing roulette history boards.
Completely refactored for maximum speed and minimal processing.
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cache of valid roulette numbers for fast validation
VALID_NUMBERS = set([str(i) for i in range(37)] + ["00"])

# Fixed OCR configuration for speed
FAST_CONFIG = '--oem 1 --psm 10 -c tessedit_char_whitelist=0123456789'

def rapid_process_board(image, rows=6, cols=8):
    """
    Ultra-optimized function for processing roulette history boards.
    Uses a single-pass grid approach with minimal processing.
    
    Args:
        image (PIL.Image): The image of the history board
        rows (int): Number of rows in the grid
        cols (int): Number of columns in the grid
        
    Returns:
        list: A list of tuples (number, confidence) for each detected number
    """
    try:
        # Convert to NumPy array
        np_image = np.array(image)
        
        # Convert to grayscale if needed
        if len(np_image.shape) == 3:
            # Process differently for color images (assumes red/white on black)
            # Single-step extraction of light colors (white and red)
            hsv = cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)
            mask = cv2.inRange(hsv, np.array([0, 0, 120]), np.array([180, 255, 255]))
            gray = mask
        else:
            # Already grayscale
            gray = np_image
        
        # Apply single threshold to entire image
        _, binary = cv2.threshold(gray, 45, 255, cv2.THRESH_BINARY)
        
        # Get dimensions
        height, width = binary.shape
        cell_height = height // rows
        cell_width = width // cols
        
        # Process grid quickly
        results = []
        
        for row in range(rows):
            for col in range(cols):
                # Extract cell directly
                y1 = row * cell_height
                y2 = y1 + cell_height
                x1 = col * cell_width
                x2 = x1 + cell_width
                
                cell = binary[y1:y2, x1:x2]
                
                # Skip obviously empty cells (saves OCR time)
                if np.mean(cell) < 5:
                    continue
                
                # Direct OCR - skip all preprocessing
                text = pytesseract.image_to_string(
                    cell,
                    config=FAST_CONFIG
                ).strip()
                
                # Fast text processing
                if text:
                    # Special case for "00"
                    if "00" in text:
                        results.append(("00", 0.8))
                        continue
                    
                    # Extract only digits
                    digits = ''.join(c for c in text if c.isdigit())
                    
                    if not digits:
                        continue
                    
                    # Fast validation with hashset
                    if digits in VALID_NUMBERS:
                        results.append((digits, 0.8))
                    elif len(digits) > 1:
                        # Handle common OCR errors
                        if digits[:2] in VALID_NUMBERS:
                            results.append((digits[:2], 0.7))
                        elif digits[0] in VALID_NUMBERS:
                            results.append((digits[0], 0.6))
        
        return results
    
    except Exception as e:
        logger.error(f"Error in rapid_process_board: {e}")
        return []

def process_image(image):
    """
    Process an image using multiple grid configurations to find the best match.
    Tries both 6x8 and 8x6 layouts which are common in roulette displays.
    
    Args:
        image (PIL.Image): Image to process
        
    Returns:
        list: A list of tuples (number, confidence) for each detected number
    """
    # Try 6x8 layout (common for digital boards)
    numbers = rapid_process_board(image, rows=6, cols=8)
    
    # If that doesn't find enough numbers, try 8x6 layout
    if len(numbers) < 10:
        alt_numbers = rapid_process_board(image, rows=8, cols=6)
        
        # Use whichever found more numbers
        if len(alt_numbers) > len(numbers):
            numbers = alt_numbers
    
    # Remove duplicates while preserving order
    seen = set()
    unique_results = []
    for num, conf in numbers:
        if num not in seen:
            seen.add(num)
            unique_results.append((num, conf))
    
    return unique_results