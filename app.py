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
        df.columns = [c.strip() for c in df.columns] 
        return df
    except: return pd.DataFrame()

def load_data():
    target_file = next((f for f in POSSIBLE_SONG_FILES if os.path.exists(f)), None)
    if not target_file: return pd.DataFrame()
    try:
        df = pd.read_csv(target_file)
        for col in ['Body', 'Chords', 'Title', 'Artist', 'Book', 'Page', 'URL', 'Difficulty']:
            if col in df.columns: 
                df[col] = df[col].fillna("").astype(str)
                # Quick clean for lyrics
                if col == 'Body':
                    df[col] = df[col].str.replace("MOSELELE.CO.UK", "", case=False)
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
if 'random_active' not in st.session_state: st.session_state.random_active = False

def main():
    c_l, c_t = st.columns([1, 5])
    with c_l:
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=120)
    with c_t: st.title("Moselele song database")

    df = load_data()
    chord_lib = load_chord_library()
    
    # Identify the correct column for images
    path_col = None
    if not chord_lib.empty:
        if 'path' in chord_lib.columns:
            path_col = 'path'
        else:
            # Fallback search if 'path' isn't found for some reason
            for col in chord_lib.columns:
                if col.lower() in ['url', 'image', 'file']:
                    path_col = col
                    break

    if df.empty:
        st.warning("⚠️ Song database not found.")
        return

    # --- SIDEBAR ---
    if os.path.exists(LOGO_PATH): st.sidebar.image(LOGO_PATH, width=150)
    st.sidebar.header("Search & Filter")
    search_query = st.sidebar.text_input("Search", "", key="search_bar").lower()
    seasonal = st.sidebar.checkbox("Show Christmas Only")
    book_filter = st.sidebar.multiselect("Books", options=sorted(df['Book'].unique()) if 'Book' in df.columns else [])

    st.sidebar.divider()
    st.sidebar.subheader("Randomisers")
    r1, r2 = st.sidebar.columns(2)
    if r1.button("Pick 1"):
        st.session_state.random_active, st.session_state.rcount = True, 1
    if r2.button("Pick 10"):
        st.session_state.random_active, st.session_state.rcount = True, 10
    if st.sidebar.button("Clear Randomisers"):
        st.session_state.random_active = False
        st.rerun()

    # --- FILTERING ---
    f_df = df.copy()
    if seasonal and 'Book' in f_df.columns: 
        f_df = f_df[f_df['Book'].str.contains('Christmas|Winter', case=False)]
    if search_query:
        f_df = f_df[f_df['Title'].str.lower().str.contains(search_query) | 
                    f_df['Artist'].str.lower().str.contains(search_query) | 
                    f_df['Body'].str.lower().str.contains(search_query)]
    if book_filter: f_df = f_df[f_df['Book'].isin(book_filter)]

    if st.session_state.random_active:
        f_df = f_df.sample(n=min(getattr(st.session_state, 'rcount', 1), len(f_df)))
    elif not any([search_query, book_filter, seasonal]):
        f_df = f_df.sample(n=min(50, len(f_df)))

    st.write(f"Displaying **{len(f_df)}** songs")

    # --- MAIN LOOP ---
    for idx, song in f_df.iterrows():
        song_id = f"{song['Title']} ({song['Artist']})"
        prefix = "🎲 " if st.session_state.random_active else ""
        header = f"{prefix}{song['Title']} - {song['Artist']} | Book {song['Book']}, Page {song['Page']}"
        
        with st.expander(header):
            if not chord_lib.empty and song['Chords'].strip() and 'Chord Name' in chord_lib.columns:
                s_chords = [c.strip() for c in song['Chords'].split(',') if c.strip()]
                valid_imgs = []
                valid_caps = []
                
                for c_name in s_chords:
                    match = chord_lib[chord_lib['Chord Name'].str.lower() == c_name.lower()]
                    if not match.empty and path_col:
                        img_filename = str(match.iloc[0][path_col])
                        img_path = os.path.join(CHORD_IMG_DIR, img_filename)
                        if os.path.exists(img_path):
                            valid_imgs.append(img_path)
                            valid_caps.append(c_name)
                
                if valid_imgs:
                    st.image(valid_imgs, width=75, caption=valid_caps)
            
            if song['Body']:
                st.markdown(f'<div class="lyrics-box">{song["Body"].strip()}</div>', unsafe_allow_html=True)

        b1, b2, _ = st.columns([1.5, 1.5, 7])
        with b1:
            if st.button("➕ List", key=f"plist_{idx}"):
                if song_id not in st.session_state.playlist:
                    st.session_state.playlist.append(song_id)
                    st.toast(f"Added {song['Title']}")
        with b2:
            if song['URL']:
                st.markdown(f'<a href="{song["URL"]}" target="_blank" class="action-btn">📄 PDF</a>', unsafe_allow_html=True)

    if st.session_state.playlist:
        st.sidebar.divider()
        st.sidebar.subheader(f"Playlist ({len(st.session_state.playlist)})")
        for p in st.session_state.playlist: st.sidebar.caption(f"• {p}")
        if st.sidebar.button("Clear Playlist"):
            st.session_state.playlist = []
            st.rerun()

if __name__ == "__main__":
    main()