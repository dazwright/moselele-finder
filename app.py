import streamlit as st
import pandas as pd
import os
import re
from collections import Counter

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
        for col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
        return df
    except: return pd.DataFrame()

# --- PAGE CONFIG ---
st.set_page_config(page_title="Moselele Database", page_icon=FAVICON_PATH if os.path.exists(FAVICON_PATH) else "🎸", layout="wide")

st.markdown("""
    <style>
    .lyrics-box { white-space: pre-wrap; background-color: #fdfdfd; padding: 25px; border: 1px solid #eee; border-radius: 8px; font-size: 1.1rem; line-height: 1.6; color: #31333F; font-family: sans-serif; }
    .stExpander { border: 1px solid #e6e6e6; }
    .action-btn { text-decoration: none; color: #31333F !important; border: 1px solid #ccc; width: 100%; height: 38px; display: flex; align-items: center; justify-content: center; border-radius: 5px; font-size: 0.85rem; background-color: #fff; margin-top: 5px; }
    .stButton button { width: 100%; height: 38px; margin-top: 5px; }
    
    /* Tag Display Badges */
    .tag-display { display: inline-block; background: #e1f5fe; color: #01579b; padding: 2px 10px; border-radius: 5px; margin-right: 5px; font-size: 0.75rem; font-weight: bold; margin-bottom: 5px; }
    
    /* Clickable Tag Cloud Styling */
    div.stButton > button.tag-cloud-btn {
        background-color: #f0f2f6;
        color: #31333f;
        border: 1px solid #dcdde1;
        border-radius: 15px;
        padding: 0px 10px;
        height: 25px !important;
        width: auto !important;
        font-size: 0.75rem !important;
        margin: 2px !important;
        display: inline-block !important;
    }
    div.stButton > button.tag-cloud-btn:hover {
        border-color: #ff4b4b;
        color: #ff4b4b;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'playlist' not in st.session_state: st.session_state.playlist = []
if 'random_active' not in st.session_state: st.session_state.random_active = False
if 'active_tags' not in st.session_state: st.session_state.active_tags = []

def main():
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=120)
    with col_title: st.title("Moselele song database")

    df = load_data()
    chord_lib = load_chord_library()
    if df.empty: return

    # --- TAG PRE-PROCESSING ---
    all_tags = []
    if 'Tags' in df.columns:
        for val in df['Tags']:
            all_tags.extend([t.strip() for t in val.split(',') if t.strip()])
    
    tag_counts = Counter(all_tags)
    unique_tags = sorted(tag_counts.keys())

    # --- SIDEBAR ---
    if os.path.exists(LOGO_PATH): st.sidebar.image(LOGO_PATH, width=150)
    st.sidebar.header("Search & Filter")
    
    search_query = st.sidebar.text_input("Search", "", key="search_bar").lower()
    seasonal = st.sidebar.checkbox("Show Christmas/Seasonal Only")
    book_filter = st.sidebar.multiselect("Books", options=sorted(df['Book'].unique()))
    
    # Tag Filter (Populated by session state for interactivity)
    selected_tags = st.sidebar.multiselect("Active Tags", options=unique_tags, key="active_tags")

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

    # --- TAG CLOUD (Interactivity) ---
    st.sidebar.divider()
    st.sidebar.subheader("Interactive Tag Cloud")
    
    # Create small buttons for the tag cloud
    if tag_counts:
        # Sort by frequency for a better cloud feel
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Streamlit workaround for "flex-row" of buttons
        # We manually render buttons; if clicked, add to session_state.active_tags
        cols = st.sidebar.container()
        with cols:
            for tag, count in sorted_tags[:30]: # Limit to top 30 for sidebar neatness
                if st.button(f"{tag} ({count})", key=f"cloud_{tag}", help=f"Filter by {tag}"):
                    if tag not in st.session_state.active_tags:
                        st.session_state.active_tags.append(tag)
                        st.rerun()

    # --- FILTERING LOGIC ---
    f_df = df.copy()
    if seasonal:
        f_df = f_df[f_df['Book'].str.contains('Christmas|Winter', case=False) | f_df['Title'].str.contains('Christmas', case=False)]
    if search_query:
        f_df = f_df[f_df['Title'].str.lower().str.contains(search_query) | f_df['Artist'].str.lower().str.contains(search_query) | f_df['Body'].str.lower().str.contains(search_query)]
    if book_filter:
        f_df = f_df[f_df['Book'].isin(book_filter)]
    if selected_tags:
        f_df = f_df[f_df['Tags'].apply(lambda x: any(t in [s.strip() for s in x.split(',')] for t in selected_tags))]

    if st.session_state.random_active:
        f_df = f_df.sample(n=min(st.session_state.rcount, len(f_df)))
    elif not any([search_query, book_filter, selected_tags, seasonal]):
        f_df = f_df.sample(n=min(50, len(f_df)))

    # --- MAIN LOOP ---
    st.write(f"Displaying **{len(f_df)}** songs")
    for idx, song in f_df.iterrows():
        song_id = f"{song['Title']} ({song['Artist']})"
        prefix = "🎲 " if st.session_state.random_active else ""
        header = f"{prefix}{song['Title']} - {song['Artist']} | Difficulty {song['Difficulty']} | {song['Book']} | Page {song['Page']}"
        
        res_col, list_col, pdf_col = st.columns([7.5, 1.2, 1.2])
        with res_col:
            with st.expander(header):
                if song.get('Tags'):
                    tag_html = "".join([f'<span class="tag-display">{t.strip()}</span>' for t in song['Tags'].split(',') if t.strip()])
                    st.markdown(tag_html, unsafe_allow_html=True)

                chord_str = song.get('Chords', '').strip()
                if chord_str:
                    st.write(f"**Chords:** {chord_str}")
                    if not chord_lib.empty:
                        s_chords = [c.strip() for c in chord_str.split(',') if c.strip()]
                        valid_imgs, valid_caps = [], []
                        for c_name in s_chords:
                            match = chord_lib[chord_lib['Chord Name'].str.lower() == c_name.lower()]
                            if not match.empty:
                                img_path = os.path.join(CHORD_IMG_DIR, str(match.iloc[0]['Path']))
                                if os.path.exists(img_path):
                                    valid_imgs.append(img_path); valid_caps.append(c_name)
                        if valid_imgs: st.image(valid_imgs, width=75, caption=valid_caps)
                
                if song['Body']: st.markdown(f'<div class="lyrics-box">{song["Body"].strip()}</div>', unsafe_allow_html=True)

        with list_col:
            if st.button("➕ List", key=f"l_{idx}"):
                if song_id not in st.session_state.playlist:
                    st.session_state.playlist.append(song_id); st.toast(f"Added {song['Title']}")
        with pdf_col:
            if song.get('URL'): st.markdown(f'<a href="{song["URL"]}" target="_blank" class="action-btn">📄 PDF</a>', unsafe_allow_html=True)

    # --- PLAYLIST ---
    if st.session_state.playlist:
        st.sidebar.divider()
        st.sidebar.subheader(f"My Playlist ({len(st.session_state.playlist)})")
        for p in st.session_state.playlist: st.sidebar.caption(f"• {p}")
        if st.sidebar.button("Clear Playlist"):
            st.session_state.playlist = []; st.rerun()

if __name__ == "__main__":
    main()