"""
Fast OCR module specifically optimized for grid-based roulette history boards.
This specialized module is much faster than the general-purpose OCR for structured layouts.
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OCR configuration for digits only
OCR_CONFIG = "--oem 1 --psm 10 -c tessedit_char_whitelist=0123456789"

def validate_roulette_number(number):
    """
    Validate if a string is a valid roulette number.
    """
    if not number:
        return False
    
    if number == "0" or number == "00":
        return True
    
    if number.isdigit() and 1 <= int(number) <= 36:
        return True
    
    return False

def process_grid_history_board(image, expected_columns=10, expected_rows=5):
    """
    Fast processing for grid-based history boards with uniform cell sizes.
    This is optimized for the specific layout seen in most digital roulette history displays.
    
    Args:
        image (PIL.Image): The image of the history board
        expected_columns (int): Expected number of columns in the grid
        expected_rows (int): Expected number of rows in the grid
        
    Returns:
        list: A list of tuples (number, confidence) for each detected number
    """
    try:
        # Convert to NumPy array for OpenCV processing
        np_image = np.array(image)
        
        # Check if image is colored and convert to grayscale if needed
        if len(np_image.shape) == 3:
            gray_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
        else:
            gray_image = np_image
            
        # Get image dimensions
        height, width = gray_image.shape
        
        # Calculate approximate cell dimensions
        cell_width = width // expected_columns
        cell_height = height // expected_rows
        
        # Define a minimum cell size to avoid processing tiny regions
        if cell_width < 8:
            cell_width = 8
        if cell_height < 10:
            cell_height = 10
        
        logger.info(f"Processing grid with cell size: {cell_width}x{cell_height}")
        
        # Results list
        results = []
        
        # Process each cell in the grid
        for row in range(expected_rows):
            for col in range(expected_columns):
                # Calculate cell coordinates
                x1 = col * cell_width
                y1 = row * cell_height
                x2 = min(x1 + cell_width, width)
                y2 = min(y1 + cell_height, height)
                
                # Skip cells that would be too small
                if x2 - x1 < 5 or y2 - y1 < 5:
                    continue
                
                # Extract the cell
                cell = gray_image[y1:y2, x1:x2]
                
                # Skip empty cells
                if cell.size == 0 or np.mean(cell) < 5 or np.mean(cell) > 250:
                    continue
                
                # Threshold to make digits stand out
                _, binary = cv2.threshold(cell, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                
                # Convert back to PIL for OCR
                cell_pil = Image.fromarray(binary)
                
                # Perform OCR
                try:
                    text = pytesseract.image_to_string(cell_pil, config=OCR_CONFIG).strip()
                    if text:
                        # Extract the number
                        digits = ''.join(c for c in text if c.isdigit())
                        
                        # Handle special case for "00"
                        if "00" in text:
                            number = "00"
                        elif digits:
                            number = digits
                            
                            # Handle multi-digit numbers that might be invalid
                            if len(number) > 2 and not validate_roulette_number(number):
                                # Try just the first and second characters
                                first_two = number[:2]
                                if validate_roulette_number(first_two):
                                    number = first_two
                                # Or just the first digit
                                elif validate_roulette_number(number[0]):
                                    number = number[0]
                                # Or single digits anywhere in the string
                                for digit in number:
                                    if validate_roulette_number(digit):
                                        # Found a valid single digit
                                        number = digit
                                        break
                        else:
                            continue  # No digits found
                            
                        # Validate the number
                        if validate_roulette_number(number):
                            # Get confidence score (simplified, just based on OCR clarity)
                            confidence = 0.75  # Default confidence
                            
                            # Higher confidence for single digits (less chance of error)
                            if len(number) == 1:
                                confidence = 0.85
                                
                            # Add to results
                            results.append((number, confidence))
                            logger.debug(f"Detected {number} at position ({row}, {col}) with confidence {confidence}")
                            
                except Exception as e:
                    logger.debug(f"Error processing cell at ({row}, {col}): {e}")
                    continue
        
        # Remove duplicates and return
        unique_results = []
        seen_numbers = set()
        
        for number, confidence in results:
            if number not in seen_numbers:
                seen_numbers.add(number)
                unique_results.append((number, confidence))
        
        return unique_results
    
    except Exception as e:
        logger.error(f"Error in grid processing: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def optimized_process_image(image_path):
    """
    Process an image file with the optimized grid method.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        list: List of detected numbers with confidence scores
    """
    try:
        # Load the image
        image = Image.open(image_path)
        
        # Process with the grid method
        results = process_grid_history_board(image)
        
        return results
    
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return []