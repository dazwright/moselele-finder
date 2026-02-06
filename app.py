import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURATION ---
POSSIBLE_SONG_FILES = ["moselele_songs_final_clean.csv", "moselele_songs_cleaned.csv", "moselele_songs.csv"]
CHORDS_LIB_FILE = "chords.csv"
CHORD_IMG_DIR = "chord_images"
MEDIA_DIR = "media"

# Local Media Paths
FAVICON_PATH = os.path.join(MEDIA_DIR, "moselele-icon-black.jpg")
LOGO_PATH = os.path.join(MEDIA_DIR, "moselele-logo-black_v_small.jpg")

@st.cache_data
def load_chord_library():
    if not os.path.exists(CHORDS_LIB_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(CHORDS_LIB_FILE)
        df.columns = [c.strip() for c in df.columns]
        if 'Chord Name' in df.columns:
            df['Chord Name'] = df['Chord Name'].astype(str).str.strip()
        return df
    except:
        return pd.DataFrame()

def load_data():
    target_file = None
    for f in POSSIBLE_SONG_FILES:
        if os.path.exists(f):
            target_file = f
            break
    if not target_file:
        return pd.DataFrame()
    try:
        df = pd.read_csv(target_file)
        # Standardizing text columns
        for col in ['Body', 'Chords', 'Title', 'Artist', 'Book', 'Page', 'URL']:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
        # Parse Difficulty
        df['Difficulty_5'] = df['Difficulty'].apply(lambda x: min(5, round(float(re.sub(r'\D', '', str(x)))/2)) if re.sub(r'\D', '', str(x)) else 0)
        return df
    except:
        return pd.DataFrame()

# --- PAGE CONFIG ---
# Note: Page icon can take a local file path
st.set_page_config(
    page_title="Moselele song database", 
    page_icon=FAVICON_PATH if os.path.exists(FAVICON_PATH) else "🎸", 
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .lyrics-box {
        white-space: pre-wrap;
        background-color: #fdfdfd;
        padding: 25px;
        border: 1px solid #eee;
        border-radius: 8px;
        font-size: 1.1rem;
        line-height: 1.6;
        color: #31333F;
        font-family: sans-serif;
    }
    .stExpander { border: 1px solid #e6e6e6; margin-bottom: 0px; }
    .pdf-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 40px;
        border-radius: 8px;
        border: 1px solid #ccc;
        background-color: white;
        color: #31333F !important;
        text-decoration: none !important;
        font-size: 14px;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

if 'playlist' not in st.session_state: st.session_state.playlist = []
if 'random_active' not in st.session_state: st.session_state.random_active = False

def main():
    # Header Section
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=120)
    with col_title:
        st.title("Moselele song database")

    df = load_data()
    chord_lib = load_chord_library()
    
    if df.empty:
        st.warning(f"⚠️ Song database not found. Looking in: `{os.getcwd()}`")
        return

    # --- SIDEBAR ---
    st.sidebar.image(LOGO_PATH, width=150) if os.path.exists(LOGO_PATH) else None
    st.sidebar.header("Search & Filter")
    search_query = st.sidebar.text_input("Search (Song, Artist, or Lyrics)", "", key="search_bar").lower()
    seasonal = st.sidebar.checkbox("Show Christmas Only")
    book_filter = st.sidebar.multiselect("Books", options=sorted(df['Book'].unique()))

    st.sidebar.divider()
    st.sidebar.subheader("Randomisers")
    c_r1, c_r2 = st.sidebar.columns(2)
    if c_r1.button("Pick 1"):
        st.session_state.random_active, st.session_state.rcount = True, 1
    if c_r2.button("Pick 10"):
        st.session_state.random_active, st.session_state.rcount = True, 10
    
    if st.sidebar.button("Clear Randomisers"):
        st.session_state.random_active = False
        st.rerun()

    # --- FILTERING ---
    f_df = df.copy()
    if seasonal: f_df = f_df[f_df['Book'].str.contains('Christmas|Winter', case=False)]
    if search_query:
        f_df = f_df[f_df['Title'].str.lower().str.contains(search_query) | 
                    f_df['Artist'].str.lower().str.contains(search_query) | 
                    f_df['Body'].str.lower().str.contains(search_query)]
    if book_filter: f_df = f_df[f_df['Book'].isin(book_filter)]

    if st.session_state.random_active:
        f_df = f_df.sample(n=min(getattr(st.session_state, 'rcount', 1), len(f_df)))
    elif not any([search_query, book_filter, seasonal]):
        f_df = f_df.sample(n=min(50, len(f_df))).sort_values('Difficulty_5')

    # --- MAIN DISPLAY ---
    st.write(f"Displaying **{len(f_df)}** songs")

    for i, (idx, song) in enumerate(f_df.iterrows()):
        song_id = f"{song['Title']} ({song['Artist']})"
        d_val = int(song['Difficulty_5'])
        d_text = f"{d_val}/5" if d_val > 0 else "NA"
        prefix = "🎲 " if st.session_state.random_active else ""
        header = f"{prefix}{song['Title']} - {song['Artist']} | {d_text} | Book {song['Book']}, Page {song['Page']}"
        
        row_cols = st.columns([7.5, 1.2, 1.2])
        
        with row_cols[0]:
            with st.expander(header):
                # Local Chord Image Logic
                if not chord_lib.empty and song['Chords'].strip():
                    s_chords = [c.strip() for c in song['Chords'].split(',') if c.strip()]
                    
                    chord_imgs = []
                    chord_captions = []
                    for c_name in s_chords:
                        match = chord_lib[chord_lib['Chord Name'].str.lower() == c_name.lower()]
                        if not match.empty:
                            img_file = str(match.iloc[0]['URL'])
                            img_full_path = os.path.join(CHORD_IMG_DIR, img_file)
                            if os.path.exists(img_full_path):
                                chord_imgs.append(img_full_path)
                                chord_captions.append(c_name)
                    
                    if chord_imgs:
                        st.image(chord_imgs, width=70, caption=chord_captions)
                
                if song['Body']:
                    st.markdown(f'<div class="lyrics-box">{song["Body"].strip()}</div>', unsafe_allow_html=True)

        with row_cols[1]:
            if st.button("➕ List", key=f"btn_l_{idx}_{i}"):
                if song_id not in st.session_state.playlist:
                    st.session_state.playlist.append(song_id)
                    st.toast(f"Added {song['Title']}")

        with row_cols[2]:
            if song['URL']:
                st.markdown(f'<a href="{song["URL"]}" target="_blank" class="pdf-btn">📄 PDF</a>', unsafe_allow_html=True)

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