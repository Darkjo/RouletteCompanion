"""
Web Scraper for Roulette Data
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
    try:
        st.info(f"Attempting to scrape data from: {url}")
        
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded:
            # Extract text content
            text = trafilatura.extract(downloaded)
            
            if text:
                st.success("Successfully extracted content from the website")
                st.write("Processing data...")
                
                # Process the extracted text to find roulette numbers
                # This is a simple implementation and may need customization based on the website structure
                numbers = process_text_for_numbers(text)
                
                if numbers:
                    # Create DataFrame with numbers and current timestamp
                    df = pd.DataFrame({
                        'number': numbers,
                        'timestamp': [datetime.now()] * len(numbers)
                    })
                    
                    return df
                else:
                    st.error("Could not find roulette numbers in the extracted content")
            else:
                st.error("Failed to extract meaningful content from the website")
        else:
            st.error("Failed to download content from the provided URL")
    
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
    # This is a simple implementation that looks for patterns that might be roulette numbers
    # Look for single or double digits (0-36) and possibly "00"
    potential_numbers = []
    
    # Look for "Spin result: X" or "Number: X" patterns
    spin_pattern = re.compile(r'(?:spin|result|number)\s*:?\s*(\d{1,2}|00)', re.IGNORECASE)
    matches = spin_pattern.findall(text)
    potential_numbers.extend(matches)
    
    # Also look for isolated numbers that might be roulette results
    # This is more prone to false positives but might catch some results
    number_pattern = re.compile(r'\b(0|00|[1-9]|[12][0-9]|3[0-6])\b')
    matches = number_pattern.findall(text)
    potential_numbers.extend(matches)
    
    # Remove duplicates but maintain order
    processed_numbers = []
    for num in potential_numbers:
        if num not in processed_numbers:
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
    Note: Web scraping may not work on all websites and the results may vary.
    """)
    
    url = st.text_input("Website URL:", placeholder="https://example.com/roulette-results")
    
    if st.button("Scrape Data", key="scrape_btn"):
        if url:
            # Show a spinner while scraping
            with st.spinner("Scraping data..."):
                df = scrape_roulette_data(url)
                
                if df is not None and not df.empty:
                    st.subheader("Scraped Data Preview")
                    st.dataframe(df)
                    
                    # Allow user to confirm import
                    if st.button("Import Scraped Data", key="confirm_scrape"):
                        return df
                
                return None
        else:
            st.error("Please enter a valid URL")
    
    return None