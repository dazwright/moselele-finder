import pandas as pd
import re
import csv

INPUT_FILE = "moselele_songs_updated.csv"
OUTPUT_FILE = "moselele_songs_cleaned.csv"

def clean_song_body(text):
    if not isinstance(text, str) or len(text) < 10:
        return text

    # 1. Clean up URLs first
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # 2. FIND THE CHORD SECTION
    # We look for "chords used" and any characters following it on the same line
    # then delete everything from the start of the string to that point.
    # The (?s) allows the dot to match newlines.
    cutoff_match = re.search(r'(?i)chords used.*?\n', text)
    
    if cutoff_match:
        # We take everything AFTER the end of the "chords used" line
        text = text[cutoff_match.end():]

    lines = text.splitlines()
    cleaned_lines = []
    
    # Metadata that might still exist between the "Chords used" line and the actual song
    ignore_keys = ['difficulty', 'artist', 'words & music', 'book', 'page', 'moselele']
    
    lyrics_started = False
    
    for line in lines:
        line_strip = line.strip()
        
        # Skip leading empty lines
        if not line_strip:
            if lyrics_started:
                cleaned_lines.append("")
            continue
            
        if not lyrics_started:
            # Check for actual song start: 
            # 1. Starts with [Chord]
            # 2. Is not a metadata line
            starts_with_chord = re.match(r'^\[[A-G]', line_strip)
            is_metadata = any(k in line_strip.lower() for k in ignore_keys)
            
            # If it's not metadata and it's not a single stray character, start the song
            if not is_metadata and len(line_strip) > 1:
                lyrics_started = True
                cleaned_lines.append(line_strip)
            else:
                continue 
        else:
            cleaned_lines.append(line_strip)

    return "\n".join(cleaned_lines).strip()

def process():
    print(f"🧹 Scrubbing Body column in {INPUT_FILE}...")
    # Read CSV, ensuring we target the right columns
    df = pd.read_csv(INPUT_FILE)

    if 'Body' in df.columns:
        # We apply the fix ONLY to the Body column
        df['Body'] = df['Body'].apply(clean_song_body)
        
        # Final safety check: remove any leftover "double newlines"
        df['Body'] = df['Body'].str.replace(r'\n{3,}', '\n\n', regex=True)
        
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
        print(f"✨ Success! Check the 'Body' column in {OUTPUT_FILE}")
    else:
        print("❌ Error: Could not find a column named 'Body'. Check your CSV headers.")

if __name__ == "__main__":
    process()