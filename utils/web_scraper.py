"""
Web Scraper for Roulette Data
Extracts roulette spin results from websites using trafilatura for content extraction
and regex patterns for number identification.
"""
import streamlit as st
import trafilatura
import re
import pandas as pd
from datetime import datetime

def scrape_roulette_data(url):
    """
    Scrape roulette spin data from a website.
    
    Args:
        url (str): URL of the website to scrape
        
    Returns:
        pd.DataFrame or None: DataFrame with spin data or None if scraping failed
    """
    if not url:
        st.error("Please provide a valid URL")
        return None
        
    # Ensure URL has http/https prefix
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        st.info(f"Added https prefix to URL: {url}")
    
    try:
        st.info(f"Attempting to scrape data from: {url}")
        
        # Send a request to the website with timeout
        downloaded = trafilatura.fetch_url(url, timeout=10)
        
        if downloaded:
            # Extract text content with settings for better extraction
            text = trafilatura.extract(
                downloaded,
                include_tables=True,
                include_links=False,
                include_images=False,
                favor_precision=True
            )
            
            if text:
                st.success("Successfully extracted content from the website")
                
                # Show a small preview of the extracted text
                max_preview_len = 300
                preview = text[:max_preview_len] + "..." if len(text) > max_preview_len else text
                with st.expander("Preview of extracted content"):
                    st.text(preview)
                
                st.write("Processing data to find roulette numbers...")
                
                # Process the extracted text to find roulette numbers
                numbers = process_text_for_numbers(text)
                
                if numbers:
                    st.success(f"Found {len(numbers)} potential roulette numbers")
                    
                    # Create DataFrame with numbers and current timestamp
                    df = pd.DataFrame({
                        'number': numbers,
                        'timestamp': [datetime.now()] * len(numbers)
                    })
                    
                    return df
                else:
                    st.error("Could not find any valid roulette numbers in the extracted content")
            else:
                st.error("Failed to extract meaningful content from the website")
        else:
            st.error("Failed to download content from the provided URL. The site might be blocking scrapers or require authentication.")
    
    except Exception as e:
        st.error(f"An error occurred while scraping: {str(e)}")
    
    return None

def process_text_for_numbers(text):
    """
    Process text content to extract roulette numbers.
    
    Args:
        text (str): Text content extracted from website
        
    Returns:
        list: List of extracted numbers
    """
    if not text:
        return []
        
    potential_numbers = []
    
    # Pattern 1: Look for "Spin result: X" or "Number: X" patterns (higher confidence)
    spin_pattern = re.compile(r'(?:spin|result|number|outcome|ball)\s*:?\s*(\d{1,2}|00)', re.IGNORECASE)
    matches = spin_pattern.findall(text)
    potential_numbers.extend(matches)
    
    # Pattern 2: Look for table formats with numbers (medium confidence)
    table_pattern = re.compile(r'[\|\s]+(0|00|[1-9]|[12][0-9]|3[0-6])[\|\s]+')
    matches = table_pattern.findall(text)
    potential_numbers.extend(matches)
    
    # Pattern 3: Look for isolated numbers that might be roulette results (lower confidence)
    # Only use this if we didn't find anything with the higher confidence patterns
    if not potential_numbers:
        number_pattern = re.compile(r'\b(0|00|[1-9]|[12][0-9]|3[0-6])\b')
        matches = number_pattern.findall(text)
        potential_numbers.extend(matches)
    
    # Remove duplicates but maintain order
    processed_numbers = []
    for num in potential_numbers:
        if num not in processed_numbers and (num == '00' or 0 <= int(num) <= 36):
            processed_numbers.append(num)
    
    return processed_numbers

def create_web_scraper_ui():
    """
    Create a UI for the web scraper functionality.
    
    Returns:
        pd.DataFrame or None: DataFrame with scraped data or None if no scraping was done
    """
    st.subheader("Import Data from Website")
    
    st.write("""
    Enter the URL of a website that contains roulette spin results.
    The scraper will attempt to extract numbers that appear to be roulette results.
    """)
    
    with st.expander("Tips for better results", expanded=False):
        st.markdown("""
        - Use sites specifically dedicated to roulette results
        - URLs for recent roulette game statistics work best
        - The scraper works best on sites with clear, structured data
        - Historical results pages typically contain more data to extract
        - You can edit the extracted numbers before importing them
        """)
    
    # URL input with example
    url = st.text_input(
        "Website URL:", 
        placeholder="https://example.com/roulette-results",
        help="Enter the full URL including http:// or https://"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        scrape_btn = st.button("📥 Scrape Data", key="scrape_btn", use_container_width=True)
    
    if scrape_btn and url:
        # Show a spinner while scraping
        with st.spinner("Scraping data... This may take a few seconds"):
            df = scrape_roulette_data(url)
            
            if df is not None and not df.empty:
                # Create a container for the results
                result_container = st.container()
                
                with result_container:
                    st.subheader("📋 Scraped Data Preview")
                    
                    # Allow editing the data before importing
                    st.write("Review and edit the data before importing:")
                    
                    # Convert to a format that can be edited
                    edited_df = st.data_editor(
                        df,
                        num_rows="dynamic",
                        key="scraped_data_editor",
                        use_container_width=True,
                        column_config={
                            "number": st.column_config.TextColumn(
                                "Number",
                                help="The roulette number (0-36 or 00)",
                                required=True,
                            ),
                            "timestamp": st.column_config.DatetimeColumn(
                                "Timestamp",
                                help="When the spin occurred",
                                format="D MMM YYYY, h:mm a",
                            ),
                        },
                    )
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if st.button("✅ Import Edited Data", key="confirm_scrape", use_container_width=True):
                            # Validate the numbers before returning
                            valid_numbers = []
                            for idx, row in edited_df.iterrows():
                                num = row['number']
                                if num == '00' or (num.isdigit() and 0 <= int(num) <= 36):
                                    valid_numbers.append(idx)
                                    
                            if valid_numbers:
                                return edited_df.iloc[valid_numbers]
                            else:
                                st.error("No valid roulette numbers found in the edited data")
                    
                    with col2:
                        if st.button("🔄 Start Over", key="start_over", use_container_width=True):
                            st.rerun()
            
            return None
    elif scrape_btn:
        st.error("Please enter a valid URL")
    
    return None