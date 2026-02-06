import streamlit as st
import pandas as pd
import os

# --- CONFIGURATION ---
CSV_FILE = "moselele_songs_cleaned.csv"

def load_data():
    if not os.path.exists(CSV_FILE):
        st.error(f"❌ File not found: {CSV_FILE}. Please ensure your cleaned CSV is in the same folder.")
        return pd.DataFrame()
    
    # Load the CSV
    df = pd.read_csv(CSV_FILE)
    
    # Fill empty values to prevent search errors
    df['Body'] = df['Body'].fillna("")
    df['Chords'] = df['Chords'].fillna("")
    df['Artist'] = df['Artist'].fillna("Unknown")
    
    return df

# --- PAGE CONFIG ---
st.set_page_config(page_title="Moselele Songbook Explorer", layout="wide")

st.markdown("""
    <style>
    .song-container {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ddd;
    }
    .lyrics-box {
        font-family: 'Courier New', Courier, monospace;
        white-space: pre-wrap;
        background-color: #ffffff;
        padding: 15px;
        border: 1px solid #eee;
        border-radius: 5px;
        font-size: 16px;
        line-height: 1.2;
    }
    </style>
""", unsafe_allow_html=True)

# --- APP LOGIC ---
def main():
    st.title("🎸 Moselele Songbook Explorer")
    
    df = load_data()
    if df.empty:
        return

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Search & Filter")
    
    search_query = st.sidebar.text_input("Search Title or Artist", "").lower()
    
    chord_filter = st.sidebar.text_input("Filter by Chords (e.g. G, C, D)", "").lower()
    
    unique_books = sorted(df['Book'].unique().astype(str))
    book_filter = st.sidebar.multiselect("Filter by Book", options=unique_books)

    # --- FILTERING LOGIC ---
    filtered_df = df.copy()

    if search_query:
        filtered_df = filtered_df[
            (filtered_df['Title'].str.lower().str.contains(search_query)) |
            (filtered_df['Artist'].str.lower().str.contains(search_query))
        ]

    if chord_filter:
        # Split search into individual chords
        search_chords = [c.strip() for c in chord_filter.split(',')]
        for sc in search_chords:
            filtered_df = filtered_df[filtered_df['Chords'].str.lower().str.contains(sc)]

    if book_filter:
        filtered_df = filtered_df[filtered_df['Book'].astype(str).isin(book_filter)]

    # --- DISPLAY RESULTS ---
    st.write(f"Showing **{len(filtered_df)}** songs")

    if len(filtered_df) == 0:
        st.warning("No songs found matching those filters.")
    else:
        for _, song in filtered_df.iterrows():
            with st.expander(f"{song['Title']} - {song['Artist']} (Book {song['Book']}, Page {song['Page']})"):
                
                # Metadata Row
                col1, col2, col3 = st.columns(3)
                col1.metric("Difficulty", f"{int(song['Difficulty'])}/10" if pd.notnull(song['Difficulty']) else "N/A")
                col2.write(f"**Chords Used:** \n`{song['Chords']}`")
                col3.write(f"[Open Original PDF]({song['URL']})")

                # The Lyrics/Body Section
                if song['Body']:
                    st.markdown(f'<div class="lyrics-box">{song["Body"]}</div>', unsafe_allow_html=True)
                else:
                    st.info("No lyrics available for this song.")

if __name__ == "__main__":
    main()