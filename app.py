import streamlit as st
import pandas as pd
import os
import random

# --- CONFIGURATION ---
CSV_FILE = "moselele_songs_cleaned.csv"
LOGO_URL = "https://www.moselele.co.uk/wp-content/uploads/2016/04/moselele-logo-small.png"

def load_data():
    if not os.path.exists(CSV_FILE):
        st.error(f"❌ File not found: {CSV_FILE}")
        return pd.DataFrame()
    
    df = pd.read_csv(CSV_FILE)
    
    # Data Cleaning & Defaults
    df['Body'] = df['Body'].fillna("")
    df['Chords'] = df['Chords'].fillna("")
    df['Artist'] = df['Artist'].fillna("Unknown")
    df['Book'] = df['Book'].fillna("Other").astype(str)
    
    # Scale Difficulty to 5 (Divides original 10-point scale by 2)
    df['Difficulty_5'] = df['Difficulty'].apply(lambda x: min(5, round(x / 2)) if pd.notnull(x) else 3)
    
    return df

# --- PAGE CONFIG ---
st.set_page_config(page_title="Moselele Song Database", page_icon="🎼", layout="wide")

# Custom CSS for Monospaced Lyrics and UI
st.markdown("""
    <style>
    .lyrics-box {
        font-family: 'Courier New', Courier, monospace;
        white-space: pre-wrap;
        background-color: #ffffff;
        padding: 20px;
        border: 1px solid #ddd;
        border-radius: 8px;
        font-size: 15px;
        line-height: 1.2;
        color: #111;
    }
    .stExpander { border: 1px solid #e6e6e6; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE FOR PLAYLIST ---
if 'playlist' not in st.session_state:
    st.session_state.playlist = []

def main():
    # Header with Logo
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image(LOGO_URL, width=120)
    with col_title:
        st.title("Moselele song database")

    df = load_data()
    if df.empty: return

    # --- SIDEBAR SEARCH & FILTERS ---
    st.sidebar.image(LOGO_URL, width=100)
    st.sidebar.header("Search & Filter")
    
    search_query = st.sidebar.text_input("Song or Artist", "").lower()
    chord_query = st.sidebar.text_input("Contains Chords (e.g. G, C)", "").lower()
    
    # Seasonal Filter
    seasonal = st.sidebar.checkbox("Show Christmas/Seasonal Only")
    
    # Book Filter
    all_books = sorted(df['Book'].unique())
    book_filter = st.sidebar.multiselect("Books", options=all_books)

    # --- RANDOMIZER BUTTONS ---
    st.sidebar.divider()
    st.sidebar.subheader("Randomizers")
    col_r1, col_r2 = st.sidebar.columns(2)
    pick_1 = col_r1.button("Pick 1 Random")
    pick_10 = col_r2.button("Pick 10 Random")

    # --- FILTERING LOGIC ---
    filtered_df = df.copy()

    # Determine if we are in "Initial Load" state
    is_filtering = any([search_query, chord_query, book_filter, seasonal, pick_1, pick_10])

    if seasonal:
        filtered_df = filtered_df[filtered_df['Book'].str.contains('Christmas|Winter|Snow', case=False)]

    if search_query:
        filtered_df = filtered_df[
            (filtered_df['Title'].str.lower().str.contains(search_query)) |
            (filtered_df['Artist'].str.lower().str.contains(search_query))
        ]

    if chord_query:
        search_chords = [c.strip() for c in chord_query.split(',')]
        for sc in search_chords:
            filtered_df = filtered_df[filtered_df['Chords'].str.lower().str.contains(sc)]

    if book_filter:
        filtered_df = filtered_df[filtered_df['Book'].isin(book_filter)]

    # Apply Random Logic or Default 50 Random Load
    if pick_1:
        filtered_df = filtered_df.sample(1)
    elif pick_10:
        filtered_df = filtered_df.sample(min(10, len(filtered_df)))
    elif not is_filtering:
        # ON LOAD: Show 50 random songs ordered by difficulty
        filtered_df = filtered_df.sample(min(50, len(filtered_df))).sort_values('Difficulty_5')

    # --- PLAYLIST SIDEBAR ---
    st.sidebar.divider()
    st.sidebar.subheader(f"My Playlist ({len(st.session_state.playlist)})")
    if st.session_state.playlist:
        for p_song in st.session_state.playlist:
            st.sidebar.caption(f"• {p_song}")
        if st.sidebar.button("Clear Playlist"):
            st.session_state.playlist = []
            st.rerun()

    # --- MAIN DISPLAY ---
    st.write(f"Displaying **{len(filtered_df)}** songs")

    for _, song in filtered_df.iterrows():
        song_id = f"{song['Title']} ({song['Artist']})"
        
        with st.expander(f"{int(song['Difficulty_5'])}/5 | {song['Title']} - {song['Artist']}"):
            
            # Action Buttons & Meta
            c1, c2, c3 = st.columns([2, 2, 2])
            if c1.button("Add to Playlist", key=f"add_{song['Title']}"):
                if song_id not in st.session_state.playlist:
                    st.session_state.playlist.append(song_id)
                    st.toast(f"Added {song['Title']}")

            c2.write(f"**Book:** {song['Book']} | **Page:** {song['Page']}")
            c3.markdown(f"[View Original PDF]({song['URL']})")

            st.markdown(f"**Chords:** `{song['Chords']}`")

            # Lyrics Display
            if song['Body']:
                st.markdown(f'<div class="lyrics-box">{song["Body"]}</div>', unsafe_allow_html=True)
            else:
                st.warning("Lyrics could not be displayed.")

if __name__ == "__main__":
    main()