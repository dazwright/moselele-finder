import requests
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import json
import re
import time

# Configuration
SONG_DB_URL = "https://www.moselele.co.uk/?page_id=1062"
OUTPUT_FILE = "song_index.json"

def extract_chords(pdf_content):
    """Scans PDF binary content for common ukulele chord patterns."""
    try:
        with fitz.open(stream=pdf_content, filetype="pdf") as doc:
            # We only need the first page usually for the chord list
            text = doc[0].get_text()
            
            # Regex for chords: Looking for A-G with variations like m, 7, maj
            chord_pattern = r'\b[A-G][b#]?(?:m|maj|min|7|sus|add|dim)?[0-9]?\b'
            found = set(re.findall(chord_pattern, text))
            
            # Common Uke Chords to filter out noise (like 'A' used as a word)
            valid_set = {"A", "Am", "A7", "B", "Bb", "Bm", "C", "C7", "Cmaj7", 
                         "D", "Dm", "D7", "E", "Em", "E7", "F", "G", "G7"}
            return sorted(list(found.intersection(valid_set)))
    except Exception:
        return []

def scrape_moselele():
    print("🚀 Starting Moselele Scraper...")
    response = requests.get(SONG_DB_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Target the song table
    table = soup.find('table')
    if not table:
        print("❌ Error: Could not find the song table on the page.")
        return
    
    rows = table.find_all('tr')[1:] # Skip header
    song_database = []

    print(f"📊 Found {len(rows)} potential songs. Analyzing...")

    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 3:
            link_tag = cols[0].find('a', href=True)
            if not link_tag: continue
            
            title = link_tag.get_text(strip=True)
            url = link_tag['href']
            artist = cols[1].get_text(strip=True) or "Unknown"
            
            # Clean up difficulty (extract digit)
            diff_raw = cols[2].get_text(strip=True)
            difficulty = int(re.search(r'\d', diff_raw).group()) if re.search(r'\d', diff_raw) else 3
            
            # PDF Chord Extraction
            print(f"  🔍 Extracting chords for: {title}")
            try:
                # Small delay to be polite to the server
                time.sleep(0.1) 
                pdf_req = requests.get(url, timeout=10)
                chords = extract_chords(pdf_req.content)
            except:
                chords = []

            song_database.append({
                "title": title,
                "artist": artist,
                "difficulty": difficulty,
                "chords": chords,
                "url": url
            })

    # Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(song_database, f, indent=4)
    
    print(f"\n✅ Success! {len(song_database)} songs saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_moselele()