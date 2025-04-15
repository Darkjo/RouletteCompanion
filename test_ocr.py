import streamlit as st
from PIL import Image
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ocr_test")

# Import the OCR module
sys.path.insert(0, os.path.abspath('.'))
from utils.ocr_capture import batch_process_history_board, initialize_ocr_settings

def main():
    st.title("OCR Test for Roulette History Board")
    
    # Initialize OCR
    initialize_ocr_settings()
    
    st.subheader("Testing with sample image")
    
    # Load test image
    image_path = "test_images/roulette_history.png"
    if os.path.exists(image_path):
        image = Image.open(image_path)
        st.image(image, caption="Roulette History Board", width=600)
        
        # Process with batch OCR
        with st.spinner("Processing image with OCR..."):
            results = batch_process_history_board(image)
        
        # Display results
        st.subheader("Detected Numbers")
        
        if results:
            # Create three columns
            col1, col2, col3 = st.columns(3)
            
            # Sort by confidence (highest first)
            sorted_results = sorted(results, key=lambda x: -x[1])
            
            # Split into columns
            items_per_column = len(sorted_results) // 3 + (1 if len(sorted_results) % 3 > 0 else 0)
            
            # First column
            with col1:
                st.write("**High Confidence**")
                for i, (number, conf) in enumerate(sorted_results[:items_per_column]):
                    conf_pct = int(conf * 100)
                    st.write(f"{number} ({conf_pct}%)")
            
            # Second column
            with col2:
                st.write("**Medium Confidence**")
                for i, (number, conf) in enumerate(sorted_results[items_per_column:2*items_per_column]):
                    conf_pct = int(conf * 100)
                    st.write(f"{number} ({conf_pct}%)")
            
            # Third column (remainder)
            with col3:
                st.write("**Lower Confidence**")
                for i, (number, conf) in enumerate(sorted_results[2*items_per_column:]):
                    conf_pct = int(conf * 100)
                    st.write(f"{number} ({conf_pct}%)")
            
            # Summary
            st.subheader("Summary")
            st.write(f"Total numbers detected: {len(results)}")
            
            # List unique numbers
            unique_numbers = sorted(list(set([num for num, _ in results])))
            st.write(f"Unique numbers detected: {', '.join(unique_numbers)}")
            
            # Show numbers by confidence
            high_conf = [num for num, conf in results if conf > 0.8]
            medium_conf = [num for num, conf in results if 0.6 <= conf <= 0.8]
            low_conf = [num for num, conf in results if conf < 0.6]
            
            st.write(f"High confidence detections: {len(high_conf)}")
            st.write(f"Medium confidence detections: {len(medium_conf)}")
            st.write(f"Low confidence detections: {len(low_conf)}")
            
        else:
            st.error("No numbers were detected in the image. Try adjusting the image or OCR parameters.")
    else:
        st.error(f"Test image not found at {image_path}")

if __name__ == "__main__":
    main()