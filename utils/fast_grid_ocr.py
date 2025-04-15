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
    # Specialized for the exact format in the test image which has red/white numbers on black background
    try:
        # Increase brightness a bit before contrast to help with dark numbers
        brightness_enhancer = ImageEnhance.Brightness(image)
        brightened_image = brightness_enhancer.enhance(1.2)  # Slight brightness increase
        
        # Simple contrast enhancement - faster
        contrast_enhancer = ImageEnhance.Contrast(brightened_image)
        enhanced_image = contrast_enhancer.enhance(1.8)  # Increase contrast
        
        # Convert to NumPy array for OpenCV processing
        np_image = np.array(enhanced_image)
        
        # Convert to grayscale
        if len(np_image.shape) == 3:
            gray_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
        else:
            gray_image = np_image
        
        # Apply TWO different thresholds for better chance of catching numbers
        # This helps with both black-on-white and white-on-black numbers
        _, binary1 = cv2.threshold(gray_image, 120, 255, cv2.THRESH_BINARY)
        _, binary2 = cv2.threshold(gray_image, 120, 255, cv2.THRESH_BINARY_INV)
            
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
        
        # Results list with duplicates allowed for now
        results = []
        
        # Generate all potential numbers to check against (improves validation)
        valid_numbers = [str(n) for n in range(0, 37)] + ["00"]
        
        # Calculate slight overlap to catch numbers on cell boundaries
        overlap = 2
        
        # Process each cell in the grid - simplified approach with overlapping cells
        for row in range(expected_rows):
            for col in range(expected_columns):
                # Calculate cell coordinates with overlap
                x1 = max(0, col * cell_width - overlap)
                y1 = max(0, row * cell_height - overlap)
                x2 = min(width, (col + 1) * cell_width + overlap)
                y2 = min(height, (row + 1) * cell_height + overlap)
                
                # Skip cells that would be too small
                if x2 - x1 < 5 or y2 - y1 < 5:
                    continue
                
                # Extract the cells from both binary versions
                cell1 = binary1[y1:y2, x1:x2]
                cell2 = binary2[y1:y2, x1:x2]
                
                # Skip empty cells
                if cell1.size == 0:
                    continue
                
                # Try both thresholded versions
                for cell, version in [(cell1, 'normal'), (cell2, 'inverted')]:
                    # Skip cells with very little variation (likely empty)
                    if np.std(cell) < 8:  # Lowered threshold to catch more cells
                        continue
                    
                    # Convert to PIL for OCR
                    cell_pil = Image.fromarray(cell)
                    
                    # Try with two different OCR configs for better coverage
                    configs = [
                        "--oem 1 --psm 10 -c tessedit_char_whitelist=0123456789",  # Single digit mode
                        "--oem 1 --psm 7 -c tessedit_char_whitelist=0123456789"    # Single line mode
                    ]
                    
                    for config in configs:
                        try:
                            text = pytesseract.image_to_string(cell_pil, config=config).strip()
                            
                            if text:
                                # Extract digits
                                digits = ''.join(c for c in text if c.isdigit())
                                
                                # Handle special case for "00"
                                if "00" in text:
                                    number = "00"
                                elif digits:
                                    number = digits
                                    
                                    # Validate multi-digit numbers
                                    if len(number) > 2:
                                        if number[:2] in valid_numbers:
                                            number = number[:2]
                                        elif number[0] in valid_numbers:
                                            number = number[0]
                                else:
                                    continue
                                    
                                # Quick validation check
                                if number in valid_numbers:
                                    confidence = 0.8
                                    results.append((number, confidence))
                                    # Once we find a valid number in this cell, move to the next cell
                                    break
                                    
                        except Exception as e:
                            logger.debug(f"Error processing cell at ({row}, {col}) with config {config}: {e}")
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