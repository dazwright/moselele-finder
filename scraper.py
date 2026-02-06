import pandas as pd
import pdfplumber
import io
import time
import os
import re
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

INPUT_CSV = "moselele_songs.csv"
OUTPUT_CSV = "moselele_songs_updated.csv"

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Runs without opening a visible window
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def scrape_with_selenium(url, driver):
    try:
        # Use Selenium to 'visit' the PDF
        driver.get(url)
        time.sleep(3) # Give it time to load the PDF viewer
        
        # We use a trick to get the raw bytes from the browser's cache
        script = "var xhr = new XMLHttpRequest(); xhr.open('GET', window.location.href, false); xhr.overrideMimeType('text/plain; charset=x-user-defined'); xhr.send(null); return xhr.responseText;"
        response_text = driver.execute_script(script)
        
        # Convert response string to bytes
        pdf_bytes = bytes([ord(c) & 0xFF for c in response_text])
        
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            
        raw_matches = re.findall(r'\[(.*?)\]', text)
        chords = ", ".join(sorted(list(set([c.split('/')[0].replace('*','').strip() for c in raw_matches if len(c) < 10]))))
        
        return text.strip(), chords
    except Exception as e:
        return None, f"SELENIUM_ERROR: {str(e)[:20]}"

def main():
    source = OUTPUT_CSV if os.path.exists(OUTPUT_CSV) else INPUT_CSV
    df = pd.read_csv(source)
    
    driver = get_driver()
    total = len(df)
    
    print("🚦 Starting Selenium-powered Scrape...")
    
    try:
        for index, row in df.iterrows():
            if pd.notna(row.get('Body')) and len(str(row['Body'])) > 100:
                continue
            
            print(f"[{index+1}/{total}] Browser Fetch: {row['Title']} (Book {row.get('Book')})")
            lyrics, chords = scrape_with_selenium(row['URL'], driver)
            
            if lyrics:
                df.at[index, 'Body'] = lyrics
                df.at[index, 'Chords'] = chords
                print("   ✅ Success!")
            else:
                print(f"   ❌ {chords}")
                df.at[index, 'Body'] = f"FAILED: {chords}"

            if (index + 1) % 5 == 0:
                df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
            
    finally:
        driver.quit()
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)

if __name__ == "__main__":
    main()