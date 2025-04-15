import streamlit as st
from PIL import Image
import sys
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fast_ocr_test")

# Import the specialized fast grid OCR module
sys.path.insert(0, os.path.abspath('.'))
from utils.fast_grid_ocr import process_grid_history_board

def main():
    st.title("Fast Grid OCR Test for Roulette History Board")
    
    st.subheader("Testing with your history board image")
    
    # Load test image
    image_path = "test_images/roulette_history.png"
    if os.path.exists(image_path):
        image = Image.open(image_path)
        st.image(image, caption="Roulette History Board", width=600)
        
        # Process with optimized grid OCR
        with st.spinner("Processing image with fast OCR..."):
            start_time = time.time()
            
            # Define grid configurations to try
            grid_configs = [
                (10, 5),   # Default layout
                (5, 10),   # Rotated layout
                (8, 6),    # Alternative layout
                (12, 4),   # Wider layout
                (6, 8),    # Taller layout
            ]
            
            # Try all grid configurations and keep the one with most numbers
            all_results = []
            best_config = None
            most_numbers = 0
            
            for cols, rows in grid_configs:
                # Process with this grid configuration
                current_results = process_grid_history_board(image, expected_columns=cols, expected_rows=rows)
                
                # If this found more numbers, update the best config
                if len(current_results) > most_numbers:
                    most_numbers = len(current_results)
                    best_config = (cols, rows)
                    all_results = current_results
            
            # Now run with the best configuration
            if best_config:
                st.info(f"Best grid configuration: {best_config[0]}x{best_config[1]} (found {most_numbers} numbers)")
                results = all_results
            else:
                # Default configuration
                results = process_grid_history_board(image, expected_columns=10, expected_rows=5)
            
            processing_time = time.time() - start_time
        
        # Display timing
        st.success(f"✅ Processing completed in {processing_time:.2f} seconds")
        
        # Display results
        st.subheader("Detected Numbers")
        
        if results:
            # Create columns for displaying numbers
            col1, col2 = st.columns(2)
            
            # Sort by confidence (highest first)
            sorted_results = sorted(results, key=lambda x: -x[1])
            
            with col1:
                st.write("**Numbers Detected**")
                for i, (number, conf) in enumerate(sorted_results):
                    conf_pct = int(conf * 100)
                    st.write(f"{number} ({conf_pct}%)")
            
            with col2:
                # Count red and black numbers
                red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
                red_count = sum(1 for num, _ in results if num.isdigit() and int(num) in red_numbers)
                black_count = sum(1 for num, _ in results if num.isdigit() and int(num) > 0 and int(num) not in red_numbers)
                zero_count = sum(1 for num, _ in results if num in ["0", "00"])
                
                st.write("**Statistics**")
                st.write(f"Total numbers detected: **{len(results)}**")
                st.write(f"Red numbers: **{red_count}**")
                st.write(f"Black numbers: **{black_count}**")
                st.write(f"Zeros: **{zero_count}**")
            
            # Try different grid dimensions
            st.subheader("Grid Size Testing")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("Try different grid dimensions:")
                cols = st.slider("Number of Columns", min_value=5, max_value=15, value=10)
                rows = st.slider("Number of Rows", min_value=3, max_value=10, value=6)
                
                if st.button("Reprocess with New Grid Size"):
                    with st.spinner(f"Processing with {cols}x{rows} grid..."):
                        start_time = time.time()
                        new_results = process_grid_history_board(image, expected_columns=cols, expected_rows=rows)
                        new_processing_time = time.time() - start_time
                        
                        st.success(f"✅ Processing completed in {new_processing_time:.2f} seconds")
                        st.write(f"Numbers detected: **{len(new_results)}**")
                        
                        # Show detected numbers
                        number_list = [num for num, _ in new_results]
                        st.write(f"Detected: {', '.join(number_list)}")
            
            with col2:
                st.write("**Speed Optimization Tips**")
                st.write("""
                - Adjust grid dimensions to match the layout
                - For digital displays, use a uniform grid
                - For physical roulette tables, use more rows than columns
                - Processing time scales with image size and complexity
                """)
                
        else:
            st.error("No numbers were detected in the image.")
    else:
        st.error(f"Test image not found at {image_path}")
        
    st.subheader("Integration Options")
    st.write("""
    This fast OCR can be integrated into the main app in two ways:

    1. **Replace the existing OCR**: For pattern analysis using just numbers
    2. **Complementary mode**: Use this for history boards while keeping the general OCR for other inputs
    
    Which option would you prefer?
    """)

if __name__ == "__main__":
    main()