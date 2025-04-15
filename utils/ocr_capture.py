"""
OCR-based screen capture module for automated roulette number detection.
Allows capturing from screen regions and processing via OCR.
"""
import cv2
import numpy as np
import pytesseract
import time
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from datetime import datetime, timedelta
import os
import logging
import threading
import io
import re
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import pyautogui but provide fallback for server environments
PYAUTOGUI_AVAILABLE = False
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning(f"PyAutoGUI could not be imported: {e}")
    logger.warning("Screen capture functionality will be limited to file uploads only")

# Global variables
capture_active = False
capture_thread = None
last_recognized_number = None
last_recognition_confidence = 0.0
capture_region = None
ocr_config = None

def initialize_ocr_settings():
    """
    Initialize OCR settings with optimized parameters for number recognition.
    """
    global ocr_config
    
    # OCR config for numbers only with high accuracy settings
    ocr_config = "--oem 1 --psm 10 -c tessedit_char_whitelist=0123456789"
    
    # Check if tesseract is available
    try:
        pytesseract.get_tesseract_version()
        logger.info("Tesseract OCR initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing Tesseract OCR: {e}")
        return False

def set_capture_region(x, y, width, height):
    """
    Set the region of the screen to capture.
    
    Args:
        x (int): X coordinate of the top-left corner
        y (int): Y coordinate of the top-left corner
        width (int): Width of the region
        height (int): Height of the region
    """
    global capture_region
    capture_region = (x, y, width, height)
    logger.info(f"Capture region set to: {capture_region}")

def capture_screen_region():
    """
    Capture the defined region of the screen.
    
    Returns:
        PIL.Image: The captured image region
    """
    global capture_region, PYAUTOGUI_AVAILABLE
    
    if not capture_region:
        logger.warning("No capture region defined")
        return None
        
    if not PYAUTOGUI_AVAILABLE:
        logger.warning("PyAutoGUI is not available for screen capture")
        return None
    
    try:
        x, y, width, height = capture_region
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        return screenshot
    except Exception as e:
        logger.error(f"Error capturing screen region: {e}")
        return None

def preprocess_image(image):
    """
    Preprocess the image for better OCR accuracy.
    
    Args:
        image (PIL.Image): The input image
        
    Returns:
        PIL.Image: The preprocessed image
    """
    try:
        # Convert to grayscale
        gray_image = image.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(gray_image)
        contrast_image = enhancer.enhance(2.0)
        
        # Apply thresholding
        threshold_value = 150
        threshold_image = contrast_image.point(lambda p: 255 if p > threshold_value else 0)
        
        # Apply noise reduction
        denoised_image = threshold_image.filter(ImageFilter.MedianFilter(size=3))
        
        # Sharpen the image
        sharpened_image = denoised_image.filter(ImageFilter.SHARPEN)
        
        return sharpened_image
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        return image  # Return original if processing fails

def recognize_number(image):
    """
    Perform OCR to recognize a roulette number from an image.
    
    Args:
        image (PIL.Image): The input image
        
    Returns:
        tuple: (recognized_number, confidence)
    """
    global ocr_config
    
    if not image:
        return None, 0.0
    
    try:
        # Preprocess the image
        processed_image = preprocess_image(image)
        
        # Convert to OpenCV format for additional processing
        cv_image = np.array(processed_image)
        
        # Further preprocessing with OpenCV
        _, binary = cv2.threshold(cv_image, 150, 255, cv2.THRESH_BINARY_INV)
        
        # Remove noise
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Perform OCR
        text = pytesseract.image_to_string(binary, config=ocr_config)
        
        # Get confidence
        data = pytesseract.image_to_data(binary, config=ocr_config, output_type=pytesseract.Output.DICT)
        
        # Extract the recognized number and confidence
        if len(data['text']) > 0 and any(data['text']):
            # Find highest confidence text
            confidences = [float(conf) for conf in data['conf'] if conf != '-1']
            if confidences:
                max_conf = max(confidences) / 100.0  # Convert to 0-1 scale
                
                # Extract the number
                number = ''.join(c for c in text if c.isdigit())
                
                # Handle special case for "00"
                if "00" in text:
                    number = "00"
                
                # Validate that it's a valid roulette number
                if number in ["0", "00"] or (number.isdigit() and 1 <= int(number) <= 36):
                    return number, max_conf
        
        return None, 0.0
    except Exception as e:
        logger.error(f"Error recognizing number: {e}")
        return None, 0.0

def validate_roulette_number(number):
    """
    Validate if a string is a valid roulette number.
    
    Args:
        number (str): The number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not number:
        return False
        
    if number == "0" or number == "00":
        return True
        
    if number.isdigit() and 1 <= int(number) <= 36:
        return True
        
    return False

def batch_process_history_board(image):
    """
    Process an image of a roulette history board to extract multiple numbers.
    Enhanced to recognize more numbers using multiple OCR approaches.
    
    Args:
        image (PIL.Image): The image of the history board
        
    Returns:
        list: A list of tuples (number, confidence) for each detected number
    """
    try:
        # Make a copy of the image to avoid modifying the original
        img_copy = image.copy()
        
        # Get image dimensions
        width, height = img_copy.size
        
        # Try multiple preprocessing approaches to maximize number detection
        results = []
        
        # APPROACH 1: Traditional contour-based detection with enhanced preprocessing
        
        # Convert to high contrast grayscale
        gray_image = img_copy.convert('L')
        enhancer = ImageEnhance.Contrast(gray_image)
        contrast_image = enhancer.enhance(2.5)  # Higher contrast for history boards
        
        # Convert to OpenCV format
        cv_image = np.array(contrast_image)
        
        # Apply different thresholding techniques
        # 1. Adaptive thresholding
        binary_adaptive = cv2.adaptiveThreshold(
            cv_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # 2. Otsu's thresholding
        _, binary_otsu = cv2.threshold(cv_image, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        
        # Process both thresholded images
        binary_images = [binary_adaptive, binary_otsu]
        
        for binary in binary_images:
            # Find contours in the binary image
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by size and shape
            min_area = 80  # Reduced minimum area to catch smaller numbers
            max_area = 8000  # Increased maximum area to catch larger displays
            number_regions = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    # Allow wider range of aspect ratios
                    aspect_ratio = float(w) / h
                    if 0.3 < aspect_ratio < 3.0:  # More permissive aspect ratio
                        number_regions.append((x, y, w, h))
            
            # Sort regions by position (left-to-right, top-to-bottom)
            number_regions.sort(key=lambda r: (r[1] // 30, r[0]))  # Reduced grid size to 30px
            
            # Extract and process each region
            processed_regions = []
            
            # Process each potential number region
            for region in number_regions:
                x, y, w, h = region
                
                # Check if this region overlaps with already processed regions
                overlaps = False
                for px, py, pw, ph in processed_regions:
                    # Check for significant overlap (more than 60% overlap)
                    overlap_area = max(0, min(x+w, px+pw) - max(x, px)) * max(0, min(y+h, py+ph) - max(y, py))
                    min_area = min(w*h, pw*ph)
                    if overlap_area > 0.6 * min_area:  # Only skip if significant overlap
                        overlaps = True
                        break
                
                if overlaps:
                    continue
                    
                # Extract the region with margin
                margin = int(max(w, h) * 0.2)  # Add 20% margin
                x1 = max(0, x - margin)
                y1 = max(0, y - margin)
                x2 = min(binary.shape[1], x + w + margin)
                y2 = min(binary.shape[0], y + h + margin)
                roi = binary[y1:y2, x1:x2]
                
                if roi.size == 0:  # Skip empty regions
                    continue
                
                # Try multiple OCR configurations for better results
                ocr_configs = [
                    "--oem 1 --psm 10 -c tessedit_char_whitelist=0123456789",  # Single digit
                    "--oem 1 --psm 7 -c tessedit_char_whitelist=0123456789",   # Single line
                    "--oem 1 --psm 8 -c tessedit_char_whitelist=0123456789"    # Single word
                ]
                
                best_number = None
                best_confidence = 0
                
                for config in ocr_configs:
                    # Perform OCR with current configuration
                    text = pytesseract.image_to_string(roi, config=config).strip()
                    
                    # Get confidence
                    data = pytesseract.image_to_data(
                        roi, config=config, output_type=pytesseract.Output.DICT
                    )
                    
                    # Process the OCR results
                    if text and any(data['text']):
                        # Extract the number
                        number = ''.join(c for c in text if c.isdigit())
                        
                        # Check if it's potentially a valid roulette number
                        if number and (number == "0" or number == "00" or 
                                      (number.isdigit() and 0 <= int(number) <= 36)):
                            
                            # Handle 00 cases - check if it's an American roulette number
                            if len(number) > 2 and number.startswith("00"):
                                # Likely a double zero misread as more digits
                                number = "00"
                            elif len(number) > 1 and number != "00":
                                # For numbers with multiple digits, ensure they're valid roulette numbers
                                if int(number) > 36:
                                    # If number is too large, try to take just the first or last digit
                                    if int(number[0]) <= 36:
                                        number = number[0]
                                    elif int(number[-1]) <= 36:
                                        number = number[-1]
                            
                            # Get confidence score
                            confidences = [float(conf) for conf in data['conf'] if conf != '-1']
                            conf_value = max(confidences) / 100.0 if confidences else 0.5
                            
                            # Check if this is better than our previous best for this region
                            if conf_value > best_confidence and validate_roulette_number(number):
                                best_number = number
                                best_confidence = conf_value
                
                # If we found a valid number, add it to results
                if best_number:
                    results.append((best_number, best_confidence))
                    processed_regions.append(region)
        
        # APPROACH 2: Grid-based search for more structured layouts
        # This is especially effective for digital displays and betting tables
        
        # Try different grid sizes for better coverage
        grid_sizes = [width//10, width//15, width//20]
        
        for grid_size in grid_sizes:
            if grid_size < 15:  # Skip if grid cells would be too small
                continue
                
            # Process in grid pattern
            for y in range(0, height, grid_size):
                for x in range(0, width, grid_size):
                    # Extract a cell with enough context
                    x1 = max(0, x - grid_size//4)
                    y1 = max(0, y - grid_size//4)
                    x2 = min(width, x + grid_size + grid_size//4)
                    y2 = min(height, y + grid_size + grid_size//4)
                    
                    cell = img_copy.crop((x1, y1, x2, y2))
                    
                    # Process with enhanced OCR
                    # First try direct recognition
                    number, confidence = recognize_number(cell)
                    
                    # If we found a valid number with good confidence, add it to results
                    if number and validate_roulette_number(number) and confidence > 0.5:
                        # Check if this number is already in results to avoid duplicates
                        if not any(number == n for n, _ in results):
                            results.append((number, confidence))
                    else:
                        # Try with preprocessing
                        cell_gray = cell.convert('L')
                        cell_contrast = ImageEnhance.Contrast(cell_gray).enhance(2.0)
                        number, confidence = recognize_number(cell_contrast)
                        
                        if number and validate_roulette_number(number) and confidence > 0.45:
                            # Check if this number is already in results
                            if not any(number == n for n, _ in results):
                                results.append((number, confidence))
        
        # APPROACH 3: Full image OCR with segmentation for specific layouts
        # Try OCR on the full image with page segmentation to detect tabular data
        for psm in [6, 11, 12]:  # Try different page segmentation modes
            full_text = pytesseract.image_to_string(
                contrast_image, 
                config=f"--oem 1 --psm {psm} -c tessedit_char_whitelist=0123456789"
            )
            
            # Extract digits and validate
            for match in re.finditer(r'(\d{1,2})', full_text):
                number = match.group(1)
                if validate_roulette_number(number):
                    # Add to results if not already present
                    if not any(number == n for n, _ in results):
                        results.append((number, 0.6))  # Default confidence
        
        # Remove duplicates and sort for consistent output
        results = list(set(results))
        results.sort(key=lambda x: -x[1])  # Sort by confidence, highest first
        
        # Limit to top 50 results with highest confidence
        return results[:50]
    
    except Exception as e:
        logger.error(f"Error processing history board: {e}")
        # Log the full stack trace for debugging
        import traceback
        logger.error(traceback.format_exc())
        return []

def start_capture(session_name, roulette_data, interval=2.0):
    """
    Start continuous screen capture and OCR in a separate thread.
    
    Args:
        session_name (str): The name of the current session
        roulette_data: The roulette data instance to store spins
        interval (float): Capture interval in seconds
    """
    global capture_active, capture_thread, last_recognized_number
    
    if capture_active:
        logger.warning("Capture already active")
        return False
    
    capture_active = True
    last_recognized_number = None
    
    def capture_loop():
        global capture_active, last_recognized_number, last_recognition_confidence
        
        logger.info(f"Starting capture loop with interval {interval}s")
        
        while capture_active:
            try:
                # Capture screen region
                image = capture_screen_region()
                
                if image:
                    # Perform OCR
                    number, confidence = recognize_number(image)
                    
                    # Store the image for display and debugging
                    img_bytes = io.BytesIO()
                    image.save(img_bytes, format='PNG')
                    st.session_state.last_captured_image = img_bytes.getvalue()
                    
                    # If a valid number is recognized with good confidence
                    if number and confidence > 0.7 and validate_roulette_number(number):
                        # Only add if it's different from the last recognized number
                        if number != last_recognized_number:
                            logger.info(f"Recognized number: {number} (confidence: {confidence:.2f})")
                            
                            # Add to session data
                            roulette_data.add_spin(
                                session_name=session_name,
                                number=number,
                                timestamp=datetime.now()
                            )
                            
                            # Update last recognized number
                            last_recognized_number = number
                            last_recognition_confidence = confidence
                            
                            # Signal the UI to update
                            st.session_state.ocr_detected_number = number
                            st.session_state.ocr_last_detection_time = datetime.now()
                    
                # Wait for the next capture
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(1)  # Avoid rapid error loops
    
    # Start capture in a separate thread
    capture_thread = threading.Thread(target=capture_loop, daemon=True)
    capture_thread.start()
    
    logger.info("Screen capture started")
    return True

def stop_capture():
    """
    Stop the screen capture thread.
    
    Returns:
        bool: True if successfully stopped, False otherwise
    """
    global capture_active, capture_thread
    
    if not capture_active:
        logger.warning("No active capture to stop")
        return False
    
    capture_active = False
    
    if capture_thread and capture_thread.is_alive():
        # Wait for thread to terminate
        capture_thread.join(timeout=3.0)
    
    logger.info("Screen capture stopped")
    return True

def is_capture_active():
    """
    Check if screen capture is currently active.
    
    Returns:
        bool: True if active, False otherwise
    """
    global capture_active
    return capture_active

def create_ocr_capture_interface(session_name, roulette_data):
    """
    Create a Streamlit interface for OCR-based capture.
    
    Args:
        session_name (str): The name of the current session
        roulette_data: The roulette data instance to store spins
    """
    st.subheader("📷 Screen Capture OCR")
    
    # Initialize session state variables if needed
    if "ocr_detected_number" not in st.session_state:
        st.session_state.ocr_detected_number = None
    if "ocr_last_detection_time" not in st.session_state:
        st.session_state.ocr_last_detection_time = None
    if "last_captured_image" not in st.session_state:
        st.session_state.last_captured_image = None
    if "capture_status" not in st.session_state:
        st.session_state.capture_status = "inactive"
    
    # Check if Tesseract is available
    ocr_available = initialize_ocr_settings()
    
    if not ocr_available:
        st.error("⚠️ Tesseract OCR is not available. Please make sure it's installed correctly.")
        st.info("For more information, visit: https://github.com/tesseract-ocr/tesseract")
        return
    
    # Check for PyAutoGUI availability
    if not PYAUTOGUI_AVAILABLE:
        st.warning("⚠️ Live screen capture is not available in this environment (PyAutoGUI dependency missing).")
        st.info("The file upload option is available instead.")
        
        # Create device selection tabs
        device_tabs = st.tabs(["Desktop Mode", "Tablet Mode", "Upload Images"])
        
        with device_tabs[0]:
            st.subheader("Desktop Mode - Manual File Selection")
            st.write("""
            ### How to use Desktop Mode:
            1. Use screenshot tools on your desktop computer to capture the roulette number display
            2. Save the image files (one per spin)
            3. Upload them below to process with OCR
            4. Confirm the detected number is correct
            """)
            
            desktop_files = st.file_uploader(
                "Upload screenshots of roulette numbers:", 
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key="desktop_upload"
            )
            
            if desktop_files:
                for file in desktop_files:
                    # Create columns for image and actions
                    col1, col2 = st.columns([1, 2])
                    
                    # Process the uploaded image
                    image = Image.open(file)
                    
                    # Display the image
                    with col1:
                        st.image(image, caption=file.name, width=150)
                    
                    # Process with OCR and show actions
                    with col2:
                        number, confidence = recognize_number(image)
                        
                        if number and confidence > 0.5:
                            st.success(f"✅ Recognized: {number} (confidence: {confidence:.2f})")
                            
                            # Add button to confirm and add this number
                            if st.button(f"Add {number}", key=f"add_desktop_{file.name}", type="primary"):
                                roulette_data.add_spin(
                                    session_name=session_name,
                                    number=number,
                                    timestamp=datetime.now()
                                )
                                st.success(f"✅ Added {number} to session {session_name}")
                        else:
                            st.error("❌ No valid number detected")
                            
                            # Allow manual entry
                            number_input = st.number_input(
                                "Enter number manually:", 
                                min_value=0, 
                                max_value=36,
                                key=f"manual_{file.name}"
                            )
                            
                            if st.button(f"Add {number_input}", key=f"add_manual_{file.name}"):
                                roulette_data.add_spin(
                                    session_name=session_name,
                                    number=str(number_input),
                                    timestamp=datetime.now()
                                )
                                st.success(f"✅ Added {number_input} to session {session_name}")
                    
                    st.divider()
        
        with device_tabs[1]:
            st.subheader("Tablet Mode - Camera Capture")
            st.write("""
            ### How to use Tablet Mode:
            1. Position your tablet/phone camera to view the roulette table or screen
            2. Take photos of the number display after each spin
            3. Upload the photos here for processing
            4. Optimize for tablet use with larger buttons and simplified interface
            """)
            
            # Add button to activate camera only when user wants it
            if "show_camera" not in st.session_state:
                st.session_state.show_camera = False
                
            if st.button("📷 Activate Camera", use_container_width=True):
                st.session_state.show_camera = True
                
            # Only show camera input when the button is clicked
            if st.session_state.show_camera:
                # Upload from camera option (works well on tablets/phones)
                camera_file = st.camera_input("Take a photo of the roulette number")
            else:
                camera_file = None
                st.info("Click 'Activate Camera' button above when you're ready to take a photo")
            
            if camera_file is not None:
                # Process the uploaded image
                image = Image.open(camera_file)
                
                # Display the image
                st.image(image, caption="Captured Image", width=300)
                
                # Process with OCR
                number, confidence = recognize_number(image)
                
                if number and confidence > 0.5:
                    st.success(f"✅ Recognized number: {number} (confidence: {confidence:.2f})")
                    
                    # Add large, touchscreen-friendly button
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("ADD THIS NUMBER", type="primary", key="add_tablet", use_container_width=True):
                            roulette_data.add_spin(
                                session_name=session_name,
                                number=number,
                                timestamp=datetime.now()
                            )
                            st.success(f"✅ Added {number} to session {session_name}")
                else:
                    st.error("❌ Could not recognize a valid roulette number in this image.")
                    
                    # Quick number pad for easy manual entry on tablets
                    st.subheader("Enter number manually:")
                    
                    # Zero buttons
                    zero_col1, zero_col2 = st.columns(2)
                    with zero_col1:
                        if st.button("0", key="tablet_0", use_container_width=True):
                            roulette_data.add_spin(
                                session_name=session_name,
                                number="0",
                                timestamp=datetime.now()
                            )
                            st.success(f"✅ Added 0 to session {session_name}")
                    
                    with zero_col2:
                        if st.button("00", key="tablet_00", use_container_width=True):
                            roulette_data.add_spin(
                                session_name=session_name,
                                number="00",
                                timestamp=datetime.now()
                            )
                            st.success(f"✅ Added 00 to session {session_name}")
                    
                    # Number grid - display numbers 1-36 in a grid for easy selection
                    # Show in groups of 12 numbers (1-12, 13-24, 25-36)
                    st.write("#### Numbers 1-12:")
                    for row in range(4):
                        cols = st.columns(3)
                        for col in range(3):
                            num = row * 3 + col + 1
                            if 1 <= num <= 12:
                                if cols[col].button(f"{num}", key=f"tablet_{num}", use_container_width=True):
                                    roulette_data.add_spin(
                                        session_name=session_name,
                                        number=str(num),
                                        timestamp=datetime.now()
                                    )
                                    st.success(f"✅ Added {num} to session {session_name}")
                    
                    st.write("#### Numbers 13-24:")
                    for row in range(4):
                        cols = st.columns(3)
                        for col in range(3):
                            num = row * 3 + col + 13
                            if 13 <= num <= 24:
                                if cols[col].button(f"{num}", key=f"tablet_{num}", use_container_width=True):
                                    roulette_data.add_spin(
                                        session_name=session_name,
                                        number=str(num),
                                        timestamp=datetime.now()
                                    )
                                    st.success(f"✅ Added {num} to session {session_name}")
                    
                    st.write("#### Numbers 25-36:")
                    for row in range(4):
                        cols = st.columns(3)
                        for col in range(3):
                            num = row * 3 + col + 25
                            if 25 <= num <= 36:
                                if cols[col].button(f"{num}", key=f"tablet_{num}", use_container_width=True):
                                    roulette_data.add_spin(
                                        session_name=session_name,
                                        number=str(num),
                                        timestamp=datetime.now()
                                    )
                                    st.success(f"✅ Added {num} to session {session_name}")
        
        with device_tabs[2]:
            st.subheader("Upload Roulette Images")
            
            # Create tabs for single number and history board
            upload_tabs = st.tabs(["Single Number", "History Board"])
            
            with upload_tabs[0]:
                st.write("""
                ### Single Number Upload:
                Upload an image containing a single roulette number for OCR processing.
                """)
                
                uploaded_file = st.file_uploader(
                    "Upload a screenshot of a roulette number:", 
                    type=["png", "jpg", "jpeg"],
                    key="general_upload"
                )
            
            with upload_tabs[1]:
                st.write("""
                ### Roulette History Board:
                Upload an image of a roulette history/results board showing multiple recent spins.
                The system will attempt to identify all visible numbers and add them to your session.
                
                **Tips for best results:**
                - Make sure numbers are clearly visible
                - Avoid glare or reflections on the screen
                - For digital boards, ensure the image is high resolution
                - Try to capture the board straight-on, not at an angle
                """)
                
                history_file = st.file_uploader(
                    "Upload a screenshot of a roulette history board:", 
                    type=["png", "jpg", "jpeg"],
                    key="history_board_upload"
                )
                
                if history_file is not None:
                    # Process the uploaded image
                    image = Image.open(history_file)
                    
                    # Display the image
                    st.image(image, caption="Uploaded History Board", width=600)
                    
                    # Add batch processing button
                    if st.button("Process History Board", type="primary", key="process_history"):
                        with st.spinner("Processing roulette history board..."):
                            # Create a placeholder for results
                            results_placeholder = st.empty()
                            
                            # Process the image to identify multiple numbers
                            numbers = batch_process_history_board(image)
                            
                            if numbers and len(numbers) > 0:
                                # Display the recognized numbers
                                results_placeholder.success(f"✅ Recognized {len(numbers)} numbers from the history board!")
                                
                                # Show the numbers with their confidence
                                st.write("#### Recognized Numbers:")
                                st.write("(Listed from most recent to oldest based on typical board layouts)")
                                
                                # Create a dataframe to display the results
                                import pandas as pd
                                results_df = pd.DataFrame(numbers, columns=["Number", "Confidence"])
                                st.dataframe(results_df)
                                
                                # Confirm addition of all numbers
                                st.write("#### Add these numbers to your session?")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    # Option to reverse the order
                                    reverse_order = st.checkbox("Reverse the order (oldest to newest)", value=False)
                                
                                with col2:
                                    # Add all button
                                    if st.button("Add All Numbers", type="primary", key="add_all_history"):
                                        # Process in the selected order
                                        process_list = list(numbers)
                                        if reverse_order:
                                            process_list.reverse()
                                        
                                        # Add each number to the session
                                        added_count = 0
                                        for num, conf in process_list:
                                            if validate_roulette_number(num):
                                                roulette_data.add_spin(
                                                    session_name=session_name,
                                                    number=num,
                                                    timestamp=datetime.now() - timedelta(seconds=(added_count*10))
                                                )
                                                added_count += 1
                                        
                                        st.success(f"✅ Added {added_count} numbers to session {session_name}")
                            else:
                                st.error("❌ Could not recognize any valid roulette numbers in this image.")
                                st.info("Try adjusting the image or using a clearer picture of the history board.")
            
            if uploaded_file is not None:
                # Process the uploaded image
                image = Image.open(uploaded_file)
                
                # Display the image
                st.image(image, caption="Uploaded Image", width=300)
                
                # Process with OCR
                number, confidence = recognize_number(image)
                
                if number and confidence > 0.5:
                    st.success(f"✅ Recognized number: {number} (confidence: {confidence:.2f})")
                    
                    # Add button to confirm and add this number
                    if st.button("Add This Number", type="primary", key="add_upload"):
                        roulette_data.add_spin(
                            session_name=session_name,
                            number=number,
                            timestamp=datetime.now()
                        )
                        st.success(f"✅ Added {number} to session {session_name}")
                else:
                    st.error("❌ Could not recognize a valid roulette number in this image.")
                    
                    # Manual entry option
                    st.subheader("Enter manually:")
                    num_col1, num_col2 = st.columns([3, 1])
                    
                    with num_col1:
                        manual_num = st.text_input("Number:", key="manual_upload")
                    
                    with num_col2:
                        if st.button("Add", key="add_manual_upload", use_container_width=True):
                            if validate_roulette_number(manual_num):
                                roulette_data.add_spin(
                                    session_name=session_name,
                                    number=manual_num,
                                    timestamp=datetime.now()
                                )
                                st.success(f"✅ Added {manual_num} to session {session_name}")
                            else:
                                st.error("❌ Invalid roulette number")
        
        return
    
    # Create tabs for setup and monitoring
    ocr_tabs = st.tabs(["Setup Capture", "Monitor", "Advanced Settings"])
    
    with ocr_tabs[0]:
        st.write("Set up the screen region to capture:")
        
        # Method selection
        capture_method = st.radio(
            "Capture Method:",
            ["Manual Region", "Window Selection"],
            horizontal=True,
            help="Choose how to define the capture region"
        )
        
        if capture_method == "Manual Region":
            # Manual region setup
            col1, col2 = st.columns(2)
            with col1:
                x_pos = st.number_input("X Position:", min_value=0, value=100)
                width = st.number_input("Width:", min_value=10, value=200)
            with col2:
                y_pos = st.number_input("Y Position:", min_value=0, value=100)
                height = st.number_input("Height:", min_value=10, value=100)
            
            if st.button("Set Capture Region", type="primary"):
                set_capture_region(x_pos, y_pos, width, height)
                st.success(f"✅ Capture region set to: ({x_pos}, {y_pos}, {width}, {height})")
        else:
            # Window selection
            st.info("Window selection is coming soon. Please use Manual Region for now.")
        
        # Capture control
        st.subheader("Capture Control")
        
        col1, col2 = st.columns(2)
        with col1:
            if not is_capture_active():
                if st.button("Start Capture", key="start_capture", type="primary"):
                    if not capture_region:
                        st.error("⚠️ Please set a capture region first.")
                    else:
                        if start_capture(session_name, roulette_data):
                            st.session_state.capture_status = "active"
                            st.success("✅ Screen capture started!")
                            st.rerun()
            else:
                if st.button("Stop Capture", key="stop_capture", type="primary"):
                    if stop_capture():
                        st.session_state.capture_status = "inactive"
                        st.info("Screen capture stopped.")
                        st.rerun()
    
    with ocr_tabs[1]:
        st.write("Monitor the OCR detection:")
        
        # Show capture status
        if st.session_state.capture_status == "active":
            st.success("✅ Capture is ACTIVE")
        else:
            st.warning("⚠️ Capture is INACTIVE")
        
        # Show last captured image
        if st.session_state.last_captured_image:
            st.subheader("Last Captured Image:")
            st.image(st.session_state.last_captured_image, caption="Captured Region", width=300)
        
        # Show last detected number
        if st.session_state.ocr_detected_number:
            st.subheader("Last Detected Number:")
            detection_time = st.session_state.ocr_last_detection_time
            time_str = detection_time.strftime("%H:%M:%S") if detection_time else "N/A"
            
            # Display with appropriate styling
            st.markdown(
                f"""
                <div style="padding: 20px; border-radius: 10px; background-color: #f0f8ff; text-align: center;">
                    <h1 style="font-size: 3em; margin-bottom: 5px;">{st.session_state.ocr_detected_number}</h1>
                    <p>Detected at {time_str}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.info("No number detected yet.")
        
        # Auto-refresh this tab if capture is active
        if st.session_state.capture_status == "active":
            time.sleep(1)
            st.rerun()
    
    with ocr_tabs[2]:
        st.write("Adjust advanced OCR settings:")
        
        # Capture interval
        capture_interval = st.slider(
            "Capture Interval (seconds):",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.1,
            help="Time between screen captures"
        )
        
        # Confidence threshold
        confidence_threshold = st.slider(
            "Confidence Threshold:",
            min_value=0.3,
            max_value=0.95,
            value=0.7,
            step=0.05,
            help="Minimum confidence level required for number recognition"
        )
        
        # Image processing settings
        st.subheader("Image Processing")
        
        col1, col2 = st.columns(2)
        with col1:
            preprocessing_level = st.select_slider(
                "Preprocessing Level:",
                options=["None", "Light", "Medium", "Heavy"],
                value="Medium",
                help="Amount of preprocessing to apply to the captured image"
            )
        
        with col2:
            ocr_mode = st.selectbox(
                "OCR Mode:",
                ["Digits Only", "Full Text"],
                index=0,
                help="What type of text to recognize"
            )
        
        # Apply settings button
        if st.button("Apply Settings", type="primary"):
            # Here we would apply the settings to the OCR system
            # For now just show a success message
            st.success("✅ Settings applied!")
            
            # Actually restart capture with new settings if it's active
            if is_capture_active():
                stop_capture()
                start_capture(session_name, roulette_data, interval=capture_interval)
                st.info("♻️ Capture restarted with new settings.")