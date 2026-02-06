import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURATION ---
POSSIBLE_SONG_FILES = ["moselele_songs_final_clean.csv", "moselele_songs_cleaned.csv", "moselele_songs.csv"]
CHORDS_LIB_FILE = "chords.csv"
CHORD_IMG_DIR = "chord_images"
MEDIA_DIR = "media"

FAVICON_PATH = os.path.join(MEDIA_DIR, "moselele-icon-black.jpg")
LOGO_PATH = os.path.join(MEDIA_DIR, "moselele-logo-black_v_small.jpg")

@st.cache_data
def load_chord_library():
    if not os.path.exists(CHORDS_LIB_FILE): return pd.DataFrame()
    try:
        df = pd.read_csv(CHORDS_LIB_FILE)
        # Clean headers
        df.columns = [c.strip() for c in df.columns]
        # Force these columns to strings to prevent errors
        for col in ['Chord Name', 'Path']:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()
        return df
    except: return pd.DataFrame()

def load_data():
    target_file = next((f for f in POSSIBLE_SONG_FILES if os.path.exists(f)), None)
    if not target_file: return pd.DataFrame()
    try:
        df = pd.read_csv(target_file)
        df.columns = [c.strip() for c in df.columns]
        # Clean and standardize song data
        for col in df.columns:
            df[col] = df[col].fillna("").astype(str)
        return df
    except: return pd.DataFrame()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Moselele song database", 
    page_icon=FAVICON_PATH if os.path.exists(FAVICON_PATH) else "🎸", 
    layout="wide"
)

st.markdown("""
    <style>
    .lyrics-box {
        white-space: pre-wrap; background-color: #fdfdfd; padding: 25px;
        border: 1px solid #eee; border-radius: 8px; font-size: 1.1rem;
        line-height: 1.6; color: #31333F; font-family: sans-serif;
    }
    .stExpander { border: 1px solid #e6e6e6; margin-bottom: 5px; }
    .action-btn {
        text-decoration: none; color: #31333F !important; border: 1px solid #ccc;
        padding: 5px 15px; border-radius: 5px; font-size: 0.85rem; background-color: #fff;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

if 'playlist' not in st.session_state: st.session_state.playlist = []

def main():
    # Logo and Title
    c_l, c_t = st.columns([1, 5])
    with c_l:
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=120)
    with c_t: st.title("Moselele song database")

    df = load_data()
    chord_lib = load_chord_library()
    
    if df.empty:
        st.warning("⚠️ Song database not found.")
        return

    # --- SIDEBAR ---
    if os.path.exists(LOGO_PATH): st.sidebar.image(LOGO_PATH, width=150)
    search_query = st.sidebar.text_input("Search", "", key="search_bar").lower()
    book_filter = st.sidebar.multiselect("Books", options=sorted(df['Book'].unique()) if 'Book' in df.columns else [])

    # --- FILTERING ---
    f_df = df.copy()
    if search_query:
        f_df = f_df[f_df['Title'].str.lower().str.contains(search_query) | 
                    f_df['Artist'].str.lower().str.contains(search_query) | 
                    f_df['Body'].str.lower().str.contains(search_query)]
    if book_filter: f_df = f_df[f_df['Book'].isin(book_filter)]

    # Default view if no search
    if not any([search_query, book_filter]):
        f_df = f_df.sample(n=min(50, len(f_df)))

    st.write(f"Displaying **{len(f_df)}** songs")

    # --- MAIN LOOP ---
    for idx, song in f_df.iterrows():
        song_id = f"{song['Title']} ({song['Artist']})"
        header = f"{song['Title']} - {song['Artist']} | Book {song['Book']}"
        
        with st.expander(header):
            # 1. Display Chords Text from column "Chords"
            chord_str = song.get('Chords', '').strip()
            if chord_str:
                st.write(f"**Chords in this song:** {chord_str}")
                
                # 2. Chord Diagrams Logic
                if not chord_lib.empty and 'Chord Name' in chord_lib.columns and 'Path' in chord_lib.columns:
                    # Split comma-separated list from songs CSV
                    s_chords = [c.strip() for c in chord_str.split(',') if c.strip()]
                    valid_imgs = []
                    valid_caps = []
                    
                    for c_name in s_chords:
                        # Match song chord against "Chord Name" column in chords CSV
                        match = chord_lib[chord_lib['Chord Name'].str.lower() == c_name.lower()]
                        if not match.empty:
                            # Get filename from "Path" column
                            img_filename = str(match.iloc[0]['Path'])
                            img_path = os.path.join(CHORD_IMG_DIR, img_filename)
                            
                            if os.path.exists(img_path):
                                valid_imgs.append(img_path)
                                valid_caps.append(c_name)
                    
                    if valid_imgs:
                        st.image(valid_imgs, width=75, caption=valid_caps)
            
            # 3. Lyrics
            if song['Body']:
                st.markdown(f'<div class="lyrics-box">{song["Body"].strip()}</div>', unsafe_allow_html=True)

        # 4. Buttons
        b1, b2, _ = st.columns([1.5, 1.5, 7])
        with b1:
            if st.button("➕ List", key=f"plist_{idx}"):
                if song_id not in st.session_state.playlist:
                    st.session_state.playlist.append(song_id)
                    st.toast(f"Added {song['Title']}")
        with b2:
            if song.get('URL'):
                st.markdown(f'<a href="{song["URL"]}" target="_blank" class="action-btn">📄 PDF</a>', unsafe_allow_html=True)

    # --- PLAYLIST SIDEBAR ---
    if st.session_state.playlist:
        st.sidebar.divider()
        st.sidebar.subheader(f"Playlist ({len(st.session_state.playlist)})")
        for p in st.session_state.playlist: st.sidebar.caption(f"• {p}")
        if st.sidebar.button("Clear Playlist"):
            st.session_state.playlist = []
            st.rerun()

if __name__ == "__main__":
    main()