import requests
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import json
import re
import time

# Configuration
SONG_DB_URL = "https://www.moselele.co.uk/?page_id=1062"
OUTPUT_FILE = "song_index.json"

def extract_pdf_data(pdf_content):
    """Extracts raw text body (preserving newlines) and identifies chords."""
    body_text = ""
    chords_found = set()
    valid_uke_chords = {
        "A", "Am", "A7", "Am7", "B", "Bb", "Bm", "B7", "C", "C7", "Cmaj7", "Cadd9",
        "D", "Dm", "D7", "E", "Em", "E7", "F", "Fmaj7", "G", "G7", "Gmaj7"
    }

    try:
        with fitz.open(stream=pdf_content, filetype="pdf") as doc:
            body_text = "".join([page.get_text() for page in doc])
            chord_pattern = r'\b[A-G][b#]?(?:m|maj|min|7|sus|add|dim)?[0-9]?\b'
            raw_matches = set(re.findall(chord_pattern, body_text))
            chords_found = raw_matches.intersection(valid_uke_chords)
    except Exception as e:
        pass # Handle empty or broken PDFs gracefully
        
    return body_text, sorted(list(chords_found))

def scrape_moselele():
    print("🚀 Starting Moselele Database Scraper...")
    
    # 1. Initialize the list AT THE START
    song_database = []
    
    try:
        response = requests.get(SONG_DB_URL, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to reach Moselele: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    
    if not table:
        print("❌ Could not find the song table.")
        return

    rows = table.find_all('tr')[1:] 

    print(f"📊 Found {len(rows)} songs. Starting scan...")

    for index, row in enumerate(rows):
        cols = row.find_all('td')
        if len(cols) >= 3:
            link_tag = cols[0].find('a', href=True)
            if not link_tag: continue
            
            title = link_tag.get_text(strip=True)
            url = link_tag['href']
            artist = cols[1].get_text(strip=True) or "Unknown"
            
            # Difficulty Logic
            diff_text = cols[2].get_text(strip=True)
            diff_match = re.search(r'\d', diff_text)
            difficulty = int(diff_match.group()) if diff_match else 3
            
            print(f"[{index+1}/{len(rows)}] Processing: {title}")
            try:
                time.sleep(0.1) # Polite delay
                pdf_req = requests.get(url, timeout=15)
                body, chords = extract_pdf_data(pdf_req.content)
            except:
                body, chords = "", []

            # Append to the list
            song_database.append({
                "title": title,
                "artist": artist,
                "difficulty": difficulty,
                "url": url,
                "chords": chords,
                "body": body 
            })

    # 2. Save the database
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(song_database, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ Success! {len(song_database)} songs saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_moselele()