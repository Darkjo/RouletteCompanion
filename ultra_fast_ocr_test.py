import streamlit as st
from PIL import Image
import sys
import os
import time

# Import the specialized OCR module
sys.path.insert(0, os.path.abspath('.'))
from utils.specialized_ocr import process_roulette_board, process_image

def main():
    st.title("Ultra-Fast Specialized OCR")
    st.write("Optimized for the exact roulette board layout with red/white numbers on black background")
    
    # Load the test image
    image_path = "test_images/roulette_history.png"
    if os.path.exists(image_path):
        image = Image.open(image_path)
        st.image(image, caption="Roulette History Board", width=600)
        
        # Process the image
        with st.spinner("Processing with ultra-fast OCR..."):
            start_time = time.time()
            
            # Process with the specialized layout
            numbers = process_roulette_board(image, rows=6, cols=8)
            
            processing_time = time.time() - start_time
        
        # Display results
        st.success(f"✅ Processing completed in {processing_time:.2f} seconds")
        
        if numbers:
            # Create columns for display
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Detected Numbers")
                st.write(", ".join(numbers))
                st.write(f"Total detected: **{len(numbers)}**")
            
            with col2:
                # Count red and black numbers
                red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
                red_count = sum(1 for num in numbers if num.isdigit() and int(num) in red_numbers)
                black_count = sum(1 for num in numbers if num.isdigit() and int(num) > 0 and int(num) not in red_numbers)
                zero_count = sum(1 for num in numbers if num in ["0", "00"])
                
                st.subheader("Statistics")
                st.write(f"Red numbers: **{red_count}**")
                st.write(f"Black numbers: **{black_count}**")
                st.write(f"Zeros: **{zero_count}**")
            
            # Compare different layouts
            st.subheader("Try Different Layouts")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Try 6x8 Layout (6 rows, 8 columns)"):
                    with st.spinner("Processing with 6x8 layout..."):
                        start = time.time()
                        nums = process_roulette_board(image, rows=6, cols=8)
                        elapsed = time.time() - start
                        st.success(f"Detected {len(nums)} numbers in {elapsed:.2f} seconds")
                        st.write(", ".join(nums))
                        
                if st.button("Try 8x6 Layout (8 rows, 6 columns)"):
                    with st.spinner("Processing with 8x6 layout..."):
                        start = time.time()
                        nums = process_roulette_board(image, rows=8, cols=6)
                        elapsed = time.time() - start
                        st.success(f"Detected {len(nums)} numbers in {elapsed:.2f} seconds")
                        st.write(", ".join(nums))
            
            with col2:
                st.markdown("""
                **Tips for Optimal Results:**
                - Make sure the image shows the complete board
                - Higher resolution images work better
                - Try both 6x8 and 8x6 layouts to see which works best
                - This algorithm is highly specialized for this specific board layout
                """)
        else:
            st.error("No numbers were detected in the image.")
    else:
        st.error(f"Test image not found at {image_path}")

if __name__ == "__main__":
    main()