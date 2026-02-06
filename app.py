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
        st.error(f"❌ File not found: {CSV_FILE}")
        return pd.DataFrame()
    df = pd.read_csv(CSV_FILE)
    df['Body'] = df['Body'].fillna("").astype(str)
    df['Body'] = df['Body'].str.replace("MOSELELE.CO.UK", "", case=False, regex=False)
    df['Chords'] = df['Chords'].fillna("").astype(str)
    df['Artist'] = df['Artist'].fillna("Unknown").astype(str)
    df['Book'] = df['Book'].fillna("Other").astype(str)
    df['Page'] = df['Page'].fillna("NA").astype(str)
    df['Difficulty_5'] = df['Difficulty'].apply(clean_difficulty)
    return df

# --- PAGE CONFIG ---
st.set_page_config(page_title="Moselele song database", page_icon=FAVICON_URL, layout="wide")

# Custom CSS for spacing and button alignment
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
    
    /* Randomiser Button Spacing (Sidebar) */
    div[data-testid="stVerticalBlock"] > div:has(button[kind="secondary"]) button {
        padding: 10px 5px !important;
        height: auto !important;
        min-height: 45px;
    }

    /* Result Row Buttons */
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

# --- SESSION STATE ---
if 'playlist' not in st.session_state: st.session_state.playlist = []
if 'random_active' not in st.session_state: st.session_state.random_active = False

def main():
    col_logo, col_title = st.columns([1, 5])
    with col_logo: st.image(LOGO_URL, width=120)
    with col_title: st.title("Moselele song database")

    df = load_data()
    if df.empty: return

    # --- SIDEBAR ---
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.header("Search & Filter")
    
    # Removed chord_query box here
    search_query = st.sidebar.text_input("Search (Song, Artist, or Lyrics)", "").lower()
    seasonal = st.sidebar.checkbox("Show Christmas/Seasonal Only")
    book_filter = st.sidebar.multiselect("Books", options=sorted(df['Book'].unique()))

    st.sidebar.divider()
    st.sidebar.subheader("Randomisers")
    col_r1, col_r2 = st.sidebar.columns(2)
    pick_1 = col_r1.button("Pick 1 Random")
    pick_10 = col_r2.button("Pick 10 Random")
    
    if st.sidebar.button("Clear Randomisers"):
        st.session_state.random_active = False