import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURATION ---
POSSIBLE_SONG_FILES = ["moselele_songs_final_clean.csv", "moselele_songs_cleaned.csv", "moselele_songs.csv"]
CHORDS_LIB_FILE = "chords.csv"

FAVICON_URL = "https://www.moselele.co.uk/wp-content/uploads/2015/11/moselele-icon-black.jpg"
LOGO_URL = "https://www.moselele.co.uk/wp-content/uploads/2013/08/moselele-logo-black_v_small.jpg"

@st.cache_data
def load_chord_library():
    if not os.path.exists(CHORDS_LIB_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(CHORDS_LIB_FILE)
        df.columns = [c.strip() for c in df.columns]
        # Clean the Chord Name column to ensure matching works
        if 'Chord Name' in df.columns:
            df['Chord Name'] = df['Chord Name'].astype(str).str.strip()
        return df
    except:
        return pd.DataFrame()

def clean_difficulty(val):
    try:
        if pd.isna(val) or val == "" or str(val).strip().lower() == "na":
            return 0
        num_str = re.sub(r'\D', '', str(val))
        if num_str:
            score = int(num_str)
            if score > 5: return min(5, round(score / 2))
            return score
    except: pass
    return 0

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
        # Force all columns to strings and fill NAs to prevent rendering crashes
        for col in ['Body', 'Chords', 'Title', 'Artist', 'Book', 'Page', 'URL']:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
            else:
                df[col] = ""
        
        df['Difficulty_5'] = df['Difficulty'].apply(clean_difficulty)
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

# --- PAGE CONFIG ---
st.set_page_config(page_title="Moselele song database", page_icon=FAVICON_URL, layout="wide")

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
        color: #31333F;
        text-decoration: none;
        font-size: 14px;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

if 'playlist' not in st.session_state: st.session_state.playlist = []
if 'random_active' not in st.session_state: st.session_state.random_active = False

def main():
    col_logo, col_title = st.columns([1, 5])
    with col_logo: st.image(LOGO_URL, width=120)
    with col_title: st.title("Moselele song database")

    df = load_data()
    chord_lib = load_chord_library()
    
    if df.empty:
        st.warning(f"⚠️ Song database not found in: `{os.getcwd()}`")
        return

    # --- SIDEBAR ---
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.header("Search & Filter")
    search_query = st.sidebar.text_input("Search (Song, Artist, or Lyrics)", "", key="search_bar").lower()
    seasonal = st.sidebar.checkbox("Show Christmas/Seasonal Only")
    
    book_options = sorted([b for b in df['Book'].unique() if b != ""])
    book_filter = st.sidebar.multiselect("Books", options=book_options)

    st.sidebar.divider()
    st.sidebar.subheader("Randomisers")
    c_r1, c_r2 = st.sidebar.columns(2)
    if c_r1.button("Pick 1 Random"):
        st.session_state.random_active = True
        st.session_state.random_count = 1
    if c_r2.button("Pick 10 Random"):
        st.session_state.random_active = True
        st.session_state.random_count = 10
    
    if st.sidebar.button("Clear Randomisers"):
        st.session_state.random_active = False
        st.rerun()

    # --- FILTERING ---
    filtered_df = df.copy()
    if seasonal:
        filtered_df = filtered_df[filtered_df['Book'].str.contains('Christmas|Winter|Snow', case=False)]
    if search_query:
        filtered_df = filtered_df[
            (filtered_df['Title'].str.lower().str.contains(search_query)) |
            (filtered_df['Artist'].str.lower().str.contains(search_query)) |
            (filtered_df['Body'].str.lower().str.contains(search_query))
        ]
    if book_filter:
        filtered_df = filtered_df[filtered_df['Book'].isin(book_filter)]

    if st.session_state.random_active:
        count = getattr(st.session_state, 'random_count', 1)
        filtered_df = filtered_df.sample(n=min(count, len(filtered_df)))
    elif not any([search_query, book_filter, seasonal]):
        filtered_df = df.sample(n=min(50, len(df))).sort_values('Difficulty_5')

    # --- MAIN DISPLAY ---
    st.write(f"Displaying **{len(filtered_df)}** songs")

    for i, (idx, song) in enumerate(filtered_df.iterrows()):
        song_id = f"{song['Title']} ({song['Artist']})"
        diff_score = int(song['Difficulty_5'])
        diff_text = f"{diff_score}/5" if diff_score > 0 else "NA"
        prefix = "🎲 " if st.session_state.random_active else ""
        header = f"{prefix}{song['Title']} - {song['Artist']} | Difficulty: {diff_text} | Book {song['Book']}, Page {song['Page']}"
        
        col_exp, col_p, col_pdf = st.columns([7.5, 1.2, 1.2])
        
        with col_exp:
            with st.expander(header):
                st.write(f"**Chords:** {song['Chords']}")
                
                # --- CHORD DIAGRAM SECTION ---
                if not chord_lib.empty and song['Chords']:
                    song_chords = [c.strip() for c in song['Chords'].split(',') if c.strip()]
                    if song_chords:
                        # Draw diagrams in rows of 6
                        n_chords = len(song_chords)
                        cols = st.columns(min(n_chords, 6))
                        for c_idx, chord_name in enumerate(song_chords):
                            match = chord_lib[chord_lib['Chord Name'].str.lower() == chord_name.lower()]
                            if not match.empty:
                                img_url = str(match.iloc[0]['URL'])
                                with cols[c_idx % 6]:
                                    st.image(img_url, width=70, caption=chord_name)
                
                if song['Body']:
                    st.markdown(f'<div class="lyrics-box">{song["Body"].strip()}</div>', unsafe_allow_html=True)
        
        with col_p:
            if st.button("➕ List", key=f"plist_btn_{idx}_{i}"):
                if song_id not in st.session_state.playlist:
                    st.session_state.playlist.append(song_id)
                    st.toast(f"Added {song['Title']}")
        
        with col_pdf:
            if song['URL']:
                st.markdown(f'<a href="{song["URL"]}" target="_blank" class="pdf-btn">📄 PDF</a>', unsafe_allow_html=True)

    # --- PLAYLIST SIDEBAR (Bottom) ---
    if st.session_state.playlist:
        st.sidebar.divider()
        st.sidebar.subheader(f"My Playlist ({len(st.session_state.playlist)})")
        for p_song in st.session_state.playlist:
            st.sidebar.caption(f"• {p_song}")
        if st.sidebar.button("Clear Playlist"):
            st.session_state.playlist = []
            st.rerun()

if __name__ == "__main__":
    main()