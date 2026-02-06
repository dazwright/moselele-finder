import streamlit as st
import pandas as pd
import os
import random
import re

# --- CONFIGURATION ---
CSV_FILE = "moselele_songs_cleaned.csv"
FAVICON_URL = "https://www.moselele.co.uk/wp-content/uploads/2015/11/moselele-icon-black.jpg"
LOGO_URL = "https://www.moselele.co.uk/wp-content/uploads/2013/08/moselele-logo-black_v_small.jpg"

def clean_difficulty(val):
    """Extracts numbers from messy strings and scales them to 5."""
    try:
        if pd.isna(val) or val == "" or str(val).strip().lower() == "na":
            return 0
        num_str = re.sub(r'\D', '', str(val))
        if num_str:
            score = int(num_str)
            # If original was 1-10, scale to 1-5. If already 1-5, keep it.
            if score > 5:
                return min(5, round(score / 2))
            return score
    except:
        pass
    return 0

def load_data():
    if not os.path.exists(CSV_FILE):
        st.error(f"❌ File not found: {CSV_FILE}")
        return pd.DataFrame()
    
    df = pd.read_csv(CSV_FILE)
    
    # 1. Standardize Text Columns
    df['Body'] = df['Body'].fillna("").astype(str)
    df['Body'] = df['Body'].str.replace("MOSELELE.CO.UK", "", case=False, regex=False)
    df['Chords'] = df['Chords'].fillna("").astype(str)
    df['Artist'] = df['Artist'].fillna("Unknown").astype(str)
    df['Book'] = df['Book'].fillna("Other").astype(str)
    df['Page'] = df['Page'].fillna("NA").astype(str)
    
    # 2. Difficulty Scaling
    df['Difficulty_5'] = df['Difficulty'].apply(clean_difficulty)
    
    return df

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
    .stExpander { border: 1px solid #e6e6e6; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

if 'playlist' not in st.session_state:
    st.session_state.playlist = []

def main():
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image(LOGO_URL, width=120)
    with col_title:
        st.title("Moselele song database")

    df = load_data()
    if df.empty: return

    # --- SIDEBAR ---
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.header("Search & Filter")
    
    search_query = st.sidebar.text_input("Search (Song, Artist, or Lyrics)", "").lower()
    chord_query = st.sidebar.text_input("Contains Chords (e.g. G, C)", "").lower()
    seasonal = st.sidebar.checkbox("Show Christmas/Seasonal Only")
    
    all_books = sorted(df['Book'].unique())
    book_filter = st.sidebar.multiselect("Books", options=all_books)

    st.sidebar.divider()
    st.sidebar.subheader("Randomizers")
    col_r1, col_r2 = st.sidebar.columns(2)
    pick_1 = col_r1.button("Pick 1 Random")
    pick_10 = col_r2.button("Pick 10 Random")

    # --- FILTERING ---
    filtered_df = df.copy()
    is_filtering = any([search_query, chord_query, book_filter, seasonal, pick_1, pick_10])

    if seasonal:
        filtered_df = filtered_df[filtered_df['Book'].str.contains('Christmas|Winter|Snow', case=False)]

    if search_query:
        filtered_df = filtered_df[
            (filtered_df['Title'].str.lower().str.contains(search_query)) |
            (filtered_df['Artist'].str.lower().str.contains(search_query)) |
            (filtered_df['Body'].str.lower().str.contains(search_query))
        ]

    if chord_query:
        search_chords = [c.strip() for c in chord_query.split(',')]
        for sc in search_chords:
            filtered_df = filtered_df[filtered_df['Chords'].str.lower().str.contains(sc)]

    if book_filter:
        filtered_df = filtered_df[filtered_df['Book'].isin(book_filter)]

    # Initial Load or Random Picks
    if pick_1:
        filtered_df = filtered_df.sample(1)
    elif pick_10:
        filtered_df = filtered_df.sample(min(10, len(filtered_df)))
    elif not is_filtering:
        # Load 50 random and sort by difficulty (Ascending: easiest first)
        filtered_df = filtered_df.sample(min(50, len(filtered_df))).sort_values('Difficulty_5', ascending=True)

    # --- PLAYLIST ---
    st.sidebar.divider()
    st.sidebar.subheader(f"My Playlist ({len(st.session_state.playlist)})")
    if st.session_state.playlist:
        for p_song in st.session_state.playlist:
            st.sidebar.caption(f"• {p_song}")
        if st.sidebar.button("Clear Playlist"):
            st.session_state.playlist = []
            st.rerun()

    # --- DISPLAY ---
    st.write(f"Displaying **{len(filtered_df)}** songs")

    for _, song in filtered_df.iterrows():
        song_id = f"{song['Title']} ({song['Artist']})"
        
        # Difficulty logic
        diff_score = int(song['Difficulty_5'])
        diff_display = f"Difficulty: {diff_score}/5" if diff_score > 0 else "Difficulty: NA"
        
        # EXPLICIT HEADER FORMAT: Title - Artist | Difficulty | Book & Page
        header_text = f"{song['Title']} - {song['Artist']} | {diff_display} | Book {song['Book']}, Page {song['Page']}"
        
        with st.expander(header_text):
            c1, c2, c3 = st.columns([2, 2, 2])
            
            if c1.button("Add to Playlist", key=f"add_{song['Title']}"):
                if song_id not in st.session_state.playlist:
                    st.session_state.playlist.append(song_id)
                    st.toast(f"Added {song['Title']}")

            c2.markdown(f"**Chords:** `{song['Chords']}`")
            c3.markdown(f"[View Original PDF]({song['URL']})")

            if song['Body']:
                st.markdown(f'<div class="lyrics-box">{song["Body"].strip()}</div>', unsafe_allow_html=True)
            else:
                st.warning("Lyrics could not be displayed.")

if __name__ == "__main__":
    main()