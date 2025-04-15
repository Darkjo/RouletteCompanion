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
        # Enhance contrast and apply preprocessing
        enhancer = ImageEnhance.Contrast(image)
        enhanced_image = enhancer.enhance(1.8)  # Increase contrast
        
        # Convert to NumPy array for OpenCV processing
        np_image = np.array(enhanced_image)
        
        # Check if image is colored and use color-based segmentation
        if len(np_image.shape) == 3:
            # Extract red numbers (specific to this history board)
            # Convert to HSV color space
            hsv = cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)
            
            # Define range for red color
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 100, 100])
            upper_red2 = np.array([180, 255, 255])
            
            # Create masks for red regions
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = mask1 + mask2
            
            # Extract white text (for black/white numbers)
            # Define range for white color
            lower_white = np.array([0, 0, 180])
            upper_white = np.array([255, 30, 255])
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
            
            # Combine masks
            combined_mask = cv2.bitwise_or(red_mask, white_mask)
            
            # Apply mask
            highlighted = cv2.bitwise_and(np_image, np_image, mask=combined_mask)
            
            # Convert to grayscale
            gray_image = cv2.cvtColor(highlighted, cv2.COLOR_RGB2GRAY)
        else:
            gray_image = np_image
            
        # Apply adaptive thresholding to handle varying lighting conditions
        binary = cv2.adaptiveThreshold(
            gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
            
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
                
                # Extract the cell from both grayscale and binary versions
                cell_gray = gray_image[y1:y2, x1:x2]
                cell_binary = binary[y1:y2, x1:x2]
                
                # Skip empty cells
                if cell_gray.size == 0:
                    continue
                
                # Skip cells with very little variation (likely empty)
                if np.std(cell_gray) < 10:
                    continue
                
                # Try both regular threshold and adaptive threshold
                # This helps with both bright and dark numbers
                _, thresh1 = cv2.threshold(cell_gray, 120, 255, cv2.THRESH_BINARY)
                _, thresh2 = cv2.threshold(cell_gray, 120, 255, cv2.THRESH_BINARY_INV)
                
                # Resize cell for better OCR (2x larger)
                h, w = cell_gray.shape
                resized = cv2.resize(cell_gray, (w*2, h*2), interpolation=cv2.INTER_CUBIC)
                
                # Prepare different versions for OCR
                versions = [
                    Image.fromarray(cell_gray),      # Original grayscale
                    Image.fromarray(cell_binary),    # Binary
                    Image.fromarray(thresh1),        # Threshold normal
                    Image.fromarray(thresh2),        # Threshold inverted
                    Image.fromarray(resized)         # Resized
                ]
                
                # Try all versions until we get a valid number
                for i, cell_pil in enumerate(versions):
                    try:
                        # Multiple OCR configurations for better coverage
                        configs = [
                            "--oem 1 --psm 10 -c tessedit_char_whitelist=0123456789",
                            "--oem 3 --psm 10 -c tessedit_char_whitelist=0123456789",
                            "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789",
                        ]
                        
                        # Try all OCR configs
                        for config in configs:
                            text = pytesseract.image_to_string(cell_pil, config=config).strip()
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
                                        else:
                                            for digit in number:
                                                if validate_roulette_number(digit):
                                                    # Found a valid single digit
                                                    number = digit
                                                    break
                                    
                                    # Validate the number
                                    if validate_roulette_number(number):
                                        # Get confidence score (based on version used)
                                        # Earlier versions and configs get higher confidence
                                        base_confidence = 0.85 - (i * 0.05) - (configs.index(config) * 0.03)
                                        
                                        # Higher confidence for single digits (less chance of error)
                                        if len(number) == 1:
                                            confidence = min(0.95, base_confidence + 0.05)
                                        else:
                                            confidence = base_confidence
                                            
                                        # Add to results
                                        results.append((number, confidence))
                                        logger.debug(f"Detected {number} at position ({row}, {col}) with confidence {confidence}")
                                        
                                        # We found a valid number, no need to try more versions
                                        raise StopIteration
                    except StopIteration:
                        break
                    except Exception as e:
                        logger.debug(f"Error with version {i} at ({row}, {col}): {e}")
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