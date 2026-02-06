import streamlit as st
import pandas as pd
import os
import random
import re

# --- CONFIGURATION ---
CSV_FILE = "moselele_songs_cleaned.csv"
FAVICON_URL = "https://www.moselele.co.uk/wp-content/uploads/2015/11/moselele-icon-black.jpg"
LOGO_URL = "https://www.moselele.co.uk/wp-content/uploads/2013/08/moselele-logo-black_v_small.jpg"

def clean_stray_chars(text):
    """Removes single uppercase characters occurring before the first chord bracket."""
    if not text or '[' not in text:
        return text
    
    # Split text at the first bracket
    parts = text.split('[', 1)
    pre_chord = parts[0]
    post_chord = '[' + parts[1]
    
    # Remove single uppercase characters (e.g., 'A ', ' B ', 'C\n') from the pre-chord area
    # This regex looks for single capital letters surrounded by whitespace or start of string
    cleaned_pre = re.sub(r'(^|\s)[A-Z](\s|$)', r'\1\2', pre_chord).strip()
    
    # If the pre-chord area was just those characters, it will now be empty
    return (cleaned_pre + "\n" + post_chord).strip() if cleaned_pre else post_chord

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
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(CSV_FILE)
        # 1. Clean Body Text
        df['Body'] = df['Body'].fillna("").astype(str)
        df['Body'] = df['Body'].str.replace("MOSELELE.CO.UK", "", case=False, regex=False)
        df['Body'] = df['Body'].apply(clean_stray_chars)
        
        # 2. Standardize other columns
        df['Chords'] = df['Chords'].fillna("").astype(str)
        df['Artist'] = df['Artist'].fillna("Unknown").astype(str)
        df['Book'] = df['Book'].fillna("Other").astype(str)
        df['Page'] = df['Page'].fillna("NA").astype(str)
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
    div[data-testid="stVerticalBlock"] > div:has(button[kind="secondary"]) button {
        padding: 10px 5px !important;
        height: auto !important;
        min-height: 45px;
    }
    .stButton button { margin-top: 5px; width: 100%; height: 40px; }
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
        font-weight: 400;
    }
    .pdf-btn:hover { border-color: #ff4b4b; color: #ff4b4b; background-color: #fffafa; }
    </style>
""", unsafe_allow_html=True)

if 'playlist' not in st.session_state: st.session_state.playlist = []
if 'random_active' not in st.session_state: st.session_state.random_active = False

def main():
    col_logo, col_title = st.columns([1, 5])
    with col_logo: st.image(LOGO_URL, width=120)
    with col_title: st.title("Moselele song database")

    df = load_data()
    if df.empty:
        st.warning("No data found. Check if 'moselele_songs_cleaned.csv' is in the folder.")
        return

    # --- SIDEBAR ---
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.header("Search & Filter")
    
    search_query = st.sidebar.text_input("Search (Song, Artist, or Lyrics)", "", key="search_bar").lower()
    seasonal = st.sidebar.checkbox("Show Christmas/Seasonal Only")
    book_filter = st.sidebar.multiselect("Books", options=sorted(df['Book'].unique()))

    st.sidebar.divider()
    st.sidebar.subheader("Randomisers")
    col_r1, col_r2 = st.sidebar.columns(2)
    pick_1 = col_r1.button("Pick 1 Random")
    pick_10 = col_r2.button("Pick 10 Random")
    
    if st.sidebar.button("Clear Randomisers"):
        st.session_state.random_active = False
        st.rerun()

    # --- FILTERING LOGIC ---
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

    # --- RANDOM/DEFAULT LOGIC ---
    if pick_1 or pick_10:
        st.session_state.random_active = True
        count = 1 if pick_1 else 10
        filtered_df = filtered_df.sample(n=min(count, len(filtered_df)))
    elif not any([search_query, book_filter, seasonal]) and not st.session_state.random_active:
        filtered_df = df.sample(n=min(50, len(df))).sort_values('Difficulty_5')

    # --- PLAYLIST SIDEBAR ---
    st.sidebar.divider()
    st.sidebar.subheader(f"My Playlist ({len(st.session_state.playlist)})")
    for p_song in st.session_state.playlist:
        st.sidebar.caption(f"