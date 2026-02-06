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
        for col in ['Body', 'Chords', 'Title', 'Artist', 'Book', 'Page', 'URL']:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
        df['Difficulty_5'] = df['Difficulty'].apply(clean_difficulty)
        return df
    except:
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
        color: #31333F !important;
        text-decoration: none !important;
        font-size: 14px;
        margin-top: 5px;
    }
    /* Simple flexbox for chords to avoid nested column crashes */
    .chord-row {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin-bottom: 15px;
    }
    .chord-card {
        text-align: center;
        width: 70px;
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
        st.warning(f"⚠️ Song database not found.")
        return

    # --- SIDEBAR ---
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.header("Search & Filter")
    search_query = st.sidebar.text_input("Search", "", key="search_bar").lower()
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
        
        # Use simple columns for the result row
        row_cols = st.columns([7.5, 1.2, 1.2])
        
        with row_cols[0]:
            with st.expander(header):
                if song['Chords'].strip():
                    st.write(f"**Chords:** {song['Chords']}")
                    
                    if not chord_lib.empty:
                        s_chords = [c.strip() for c in song['Chords'].split(',') if c.strip()]
                        if s_chords:
                            # Using a horizontal container instead of nested st.columns
                            with st.container():
                                chord_display_cols = st.columns(min(len(s_chords), 8))
                                for c_idx, c_name in enumerate(s_chords):
                                    match = chord_lib[chord_lib['Chord Name'].str.lower() == c_name.lower()]
                                    if not match.empty:
                                        with chord_display_cols[c_idx % 8]:
                                            st.image(str(match.iloc[0]['URL']), width=65)
                                            st.caption(c_name)
                
                if song['Body']:
                    st.markdown(f'<div class="lyrics-box">{song["Body"].strip()}</div>', unsafe_allow_html=True)

        with row_cols[1]:
            if st.button("➕ List", key=f"lbtn_{idx}_{i}"):
                if song_id not in st.session_state.playlist:
                    st.session_state.playlist.append(song_id)
                    st.toast(f"Added {song['Title']}")

        with row_cols[2]:
            if song['URL']:
                st.markdown(f'<a href="{song["URL"]}" target="_blank" class="pdf-btn">📄 PDF</a>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()