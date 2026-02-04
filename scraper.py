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

def extract_pdf_body(pdf_content):
    """
    Extracts raw text from PDF bytes, preserving layout.
    """
    body_text = ""
    try:
        with fitz.open(stream=pdf_content, filetype="pdf") as doc:
            # Join text from all pages
            body_text = "".join([page.get_text() for page in doc])
    except Exception:
        pass # Return empty string if PDF is unreadable
    return body_text

def scrape_moselele():
    print("🚀 Starting Full Scraper (Table Metadata + PDF Lyrics)...")
    song_database = []
    
    try:
        main_res = requests.get(SONG_DB_URL, timeout=15)
        soup = BeautifulSoup(main_res.text, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr')[1:] # Skip header
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    total = len(rows)
    for index, row in enumerate(rows):
        cols = row.find_all('td')
        if len(cols) >= 3:
            link_tag = cols[0].find('a', href=True)
            if not link_tag: continue
            
            # 1. Extract Website Metadata
            title = link_tag.get_text(strip=True)
            artist = cols[1].get_text(strip=True)
            meta_text = cols[2].get_text(strip=True)
            
            # Regex for Book, Page, and Difficulty
            diff_match = re.search(r'Difficulty\s*(\d+)', meta_text, re.I)
            book_match = re.search(r'Book\s*(\d+)', meta_text, re.I)
            page_match = re.search(r'Page\s*(\d+)', meta_text, re.I)
            
            full_url = urllib.parse.urljoin(SONG_DB_URL, link_tag['href'])
            
            print(f"[{index+1}/{total}] Processing: {title}")
            
            # 2. Extract PDF Body (The Lyrics)
            pdf_body = ""
            if full_url.endswith('.pdf'):
                try:
                    pdf_res = requests.get(full_url, timeout=10)
                    if pdf_res.status_code == 200:
                        pdf_body = extract_pdf_body(pdf_res.content)
                except Exception as e:
                    print(f"   ⚠️ Could not download PDF for {title}")

            # 3. Combine everything
            song_database.append({
                "title": title,
                "artist": artist,
                "difficulty": int(diff_match.group(1)) if diff_match else 3,
                "book": int(book_match.group(1)) if book_match else "N/A",
                "page": int(page_match.group(1)) if page_match else "N/A",
                "url": full_url,
                "body": pdf_body  # Now correctly populated
            })
            
            # Tiny sleep to be polite to the server
            time.sleep(0.1)

    # Save the complete database
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(song_database, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ Done! {len(song_database)} songs indexed with metadata and lyrics.")

if __name__ == "__main__":
    scrape_moselele()