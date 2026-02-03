import requests
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import json
import re
import time
import urllib.parse

# Configuration
SONG_DB_URL = "https://www.moselele.co.uk/?page_id=1062"
OUTPUT_FILE = "song_index.json"

def extract_pdf_data(pdf_content):
    """
    Extracts raw text body (preserving newlines) and identifies ALL chords.
    No longer filters against a fixed 'valid ukulele chords' list.
    """
    body_text = ""
    chords_found = set()

    try:
        with fitz.open(stream=pdf_content, filetype="pdf") as doc:
            # Join text from all pages, preserving original layout/newlines
            body_text = "".join([page.get_text() for page in doc])
            
            # Identify chords based on standard patterns (Root + Accidental + Quality)
            # This regex captures roots A-G, #/b, and common qualities like m, maj, 7, sus, etc.
            chord_pattern = r'\b[A-G][b#]?(?:m|maj|min|7|sus|add|dim|aug)?[0-9]?\b'
            chords_found = set(re.findall(chord_pattern, body_text))
            
    except Exception:
        pass # Handle empty/broken PDFs
        
    return body_text, sorted(list(chords_found))

def get_with_retry(url, max_retries=3):
    """Download a URL with retry logic for spotty connections."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                return response
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                time.sleep(2)
    return None

def scrape_moselele():
    print("🚀 Starting Open-Chord Moselele Scraper...")
    song_database = []
    
    try:
        main_res = requests.get(SONG_DB_URL, timeout=15)
        soup = BeautifulSoup(main_res.text, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr')[1:] 
    except Exception as e:
        print(f"❌ Initial connection failed: {e}")
        return

    for index, row in enumerate(rows):
        cols = row.find_all('td')
        if len(cols) >= 3:
            link_tag = cols[0].find('a', href=True)
            if not link_tag: continue
            
            # Clean and normalize URL
            full_url = urllib.parse.urljoin(SONG_DB_URL, link_tag['href'])
            if not full_url.endswith('.pdf'): continue

            title = link_tag.get_text(strip=True)
            artist = cols[1].get_text(strip=True) or "Unknown"
            
            # Difficulty from table
            diff_text = cols[2].get_text(strip=True)
            diff_match = re.search(r'\d', diff_text)
            difficulty = int(diff_match.group()) if diff_match else 3
            
            print(f"[{index+1}/{len(rows)}] Indexing: {title}")
            
            pdf_res = get_with_retry(full_url)
            if pdf_res:
                body, chords = extract_pdf_data(pdf_res.content)
            else:
                body, chords = "", []

            song_database.append({
                "title": title,
                "artist": artist,
                "difficulty": difficulty,
                "url": full_url,
                "chords": chords,
                "body": body 
            })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(song_database, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ All set! Found {len(song_database)} songs with their full chord charts.")

if __name__ == "__main__":
    scrape_moselele()